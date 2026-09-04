# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 3 or later.
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""The optional neural voices must not disturb the existing Greek math reading.

The add-on's established behaviour - reading mathematics through whatever
synthesizer NVDA is already set to - is finished work. These tests exist so that
the optional neural speech stays strictly additive: off unless asked for, unable
to reach the reading engine, and inert at NVDA startup.
"""

import ast
import re
import sys
import types
import unittest
from pathlib import Path

ADDON = Path(__file__).parent.parent / "addon"
PLUGIN = ADDON / "globalPlugins" / "greekMathReader"
NEURAL = PLUGIN / "neural"
DRIVER = ADDON / "synthDrivers" / "greekMathVoice.py"

sys.path.insert(0, str(PLUGIN))
sys.path.insert(0, str(Path(__file__).parent))

from test_synth_driver import loadDriver  # noqa: E402

#: The reading path as it stood before neural speech was added. Nothing in the
#: neural feature may import any of it.
READING_MODULES = (
	"engine",
	"provider",
	"interaction",
	"backend",
	"speech",
	"parser",
	"symbols_el",
	"grammar_el",
	"terminology_el",
	"semantics",
	"latex",
	"unicodemath",
	"morphology_el",
)

#: Settings that existed before this feature. Their defaults must not drift.
ESTABLISHED_DEFAULTS = {
	"enabled": "boolean(default=True)",
	"verbosity": "integer(default=1, min=0, max=2)",
	"decimalComma": "boolean(default=True)",
	"forceGreekLanguage": "boolean(default=True)",
	"terminologyProfile": "option('standard', 'school', 'university', default='standard')",
	"latinLetterMode": "option('greek_school', 'literal', default='greek_school')",
	"relativeRate": "integer(default=100, min=1, max=100)",
	"pauseFactor": "integer(default=50, min=0, max=100)",
	"autoMathCatBackend": "boolean(default=True)",
	"terminologyOverrides": "string(default='{}')",
	"translateUnconfirmedWordMath": "boolean(default=True)",
}


def _configSpec():
	"""Read CONFIG_SPEC out of the plugin without importing NVDA."""
	tree = ast.parse((PLUGIN / "__init__.py").read_text(encoding="utf-8"))
	for node in tree.body:
		if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CONFIG_SPEC":
			return {
				key.value: value.value
				for key, value in zip(node.value.keys, node.value.values)
			}
	raise AssertionError("CONFIG_SPEC not found")


class TestExistingBehaviourIsUntouched(unittest.TestCase):
	def test_every_established_setting_keeps_its_default(self):
		# A changed default here would silently alter how maths is read.
		spec = _configSpec()
		for key, expected in ESTABLISHED_DEFAULTS.items():
			self.assertEqual(spec.get(key), expected, msg=key)

	def test_neural_speech_is_off_until_the_user_asks(self):
		self.assertEqual(_configSpec()["neuralVoicesEnabled"], "boolean(default=False)")

	def test_the_reading_engine_has_no_knowledge_of_neural_speech(self):
		# The engine must stay a pure, NVDA-free Greek reader.
		for path in sorted((PLUGIN / "engine").glob("*.py")):
			source = path.read_text(encoding="utf-8")
			self.assertNotIn("neural", source, msg=path.name)

	def test_the_provider_and_interaction_layers_are_unaware_of_neural_speech(self):
		for name in ("provider.py", "interaction.py", "backend.py"):
			source = (PLUGIN / name).read_text(encoding="utf-8")
			self.assertNotIn("neural", source, msg=name)


class TestNeuralCodeCannotReachTheReadingPath(unittest.TestCase):
	def _imports(self, path):
		"""Names imported from outside the neural package.

		``from . import layout`` is a sibling inside ``neural/`` and is ignored;
		``from ..engine import ...`` climbs out into the reading path and is
		exactly what these tests are looking for.
		"""
		tree = ast.parse(path.read_text(encoding="utf-8"))
		names = set()
		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				names.update(alias.name.split(".")[0] for alias in node.names)
			elif isinstance(node, ast.ImportFrom):
				if node.level == 1:
					continue
				if node.module:
					names.add(node.module.split(".")[0])
				names.update(alias.name for alias in node.names)
		return names

	def test_no_neural_module_imports_the_reading_engine(self):
		# One-way dependency: neural speech may not influence how maths is read.
		for path in sorted(NEURAL.glob("*.py")):
			imported = self._imports(path)
			for forbidden in READING_MODULES:
				self.assertNotIn(forbidden, imported, msg="{0} imports {1}".format(path.name, forbidden))

	def test_the_neural_package_imports_nothing_from_nvda(self):
		# It has to stay unit-testable off Windows, like the engine.
		nvdaModules = {"config", "gui", "wx", "ui", "speech", "nvwave", "addonHandler", "api"}
		for path in sorted(NEURAL.glob("*.py")):
			if path.name == "manager.py":
				# manager.py reaches globalVars lazily, inside a guarded function.
				continue
			self.assertFalse(
				self._imports(path) & nvdaModules,
				msg="{0} imports {1}".format(path.name, self._imports(path) & nvdaModules),
			)

	def test_the_manager_only_touches_nvda_lazily(self):
		source = (NEURAL / "manager.py").read_text(encoding="utf-8")
		# globalVars must be imported inside a function, never at module level.
		moduleLevel = [
			line for line in source.splitlines() if re.match(r"^(import|from)\s", line)
		]
		self.assertFalse([line for line in moduleLevel if "globalVars" in line])


class TestDriverIsInertUntilEnabled(unittest.TestCase):
	def setUp(self):
		self.module = loadDriver()

	def _check(self, enabled, spec=True):
		saved = sys.modules.get("config")
		stub = types.ModuleType("config")
		if spec:
			stub.conf = {"greekMathReader": {"neuralVoicesEnabled": enabled}}
		else:
			stub.conf = {}
		sys.modules["config"] = stub
		try:
			return self.module.SynthDriver.check()
		finally:
			if saved is None:
				sys.modules.pop("config", None)
			else:
				sys.modules["config"] = saved

	def test_the_synthesizer_is_not_offered_while_the_option_is_off(self):
		self.assertFalse(self._check(False))

	def test_a_configuration_without_the_add_on_section_is_survived(self):
		# check() runs during NVDA startup, possibly before the plugin registers
		# its spec. It must report False rather than raise.
		self.assertFalse(self._check(True, spec=False))

	def test_nothing_is_loaded_while_the_option_is_off(self):
		"""The disabled path must not import the plugin or read the disk."""
		def explode():
			raise AssertionError("the voice manager must not be imported when disabled")

		original = self.module._importManager
		self.module._importManager = explode
		try:
			self.assertFalse(self._check(False))
		finally:
			self.module._importManager = original

	def test_the_driver_declares_itself_as_a_separate_synthesizer(self):
		# It is an alternative to OneCore/eSpeak, not a replacement for the
		# add-on's math provider, so it must not collide with NVDA's own names.
		self.assertEqual(self.module.SynthDriver.name, "greekMathVoice")
		self.assertNotIn(self.module.SynthDriver.name, ("espeak", "oneCore", "sapi5", "silence"))


class TestPackagingKeepsTheAddonSmall(unittest.TestCase):
	def test_no_model_or_binary_is_bundled(self):
		# The runtime and voices are downloaded on request; shipping them would
		# push a 166 KB add-on past 80 MB for users who never enable this.
		heavy = [
			path.name
			for path in ADDON.rglob("*")
			if path.is_file() and path.suffix in (".onnx", ".whl", ".dll", ".pyd", ".bz2")
		]
		self.assertEqual(heavy, [])


if __name__ == "__main__":
	unittest.main()
