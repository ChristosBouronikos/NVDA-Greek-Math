# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""Tests for the real provider's NVDA speech-sequence adaptation."""

import builtins
import importlib.util
import sys
import types
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"
PACKAGE_NAME = "greekMathReaderProviderSpeechTest"
_MISSING = object()


class TestProviderSpeechSequence(unittest.TestCase):
	def setUp(self):
		self.savedModules = {}
		self.savedTranslation = getattr(builtins, "_", _MISSING)
		builtins._ = lambda message: message

		addonHandler = types.ModuleType("addonHandler")
		addonHandler.initTranslation = lambda: None

		config = types.ModuleType("config")
		config.conf = {
			"greekMathReader": {
				"verbosity": 1,
				"decimalComma": True,
				"forceGreekLanguage": True,
			},
			"speech": {"autoLanguageSwitching": True},
		}

		mathPres = types.ModuleType("mathPres")
		mathPres.MathPresentationProvider = object

		class FakeLog:
			def __init__(log):
				log.warnings = []

			def warning(log, message):
				log.warnings.append(message)

			def info(log, message):
				pass

			def error(log, message):
				pass

			def exception(log, message):
				pass

		logHandler = types.ModuleType("logHandler")
		logHandler.log = self.log = FakeLog()

		commands = types.ModuleType("speech.commands")

		class BreakCommand:
			def __init__(command, time=0):
				command.time = time

		class LangChangeCommand:
			def __init__(command, lang):
				command.lang = lang

		commands.BreakCommand = BreakCommand
		commands.LangChangeCommand = LangChangeCommand
		speech = types.ModuleType("speech")
		speech.__path__ = []

		self.synth = types.SimpleNamespace(languageIsSupported=lambda language: True)
		synthDriverHandler = types.ModuleType("synthDriverHandler")
		synthDriverHandler.getSynth = lambda: self.synth

		package = types.ModuleType(PACKAGE_NAME)
		package.__path__ = [str(PACKAGE_DIR)]

		stubs = {
			"addonHandler": addonHandler,
			"config": config,
			"mathPres": mathPres,
			"logHandler": logHandler,
			"speech": speech,
			"speech.commands": commands,
			"synthDriverHandler": synthDriverHandler,
			PACKAGE_NAME: package,
		}
		for name, module in stubs.items():
			self.savedModules[name] = sys.modules.get(name, _MISSING)
			sys.modules[name] = module

		spec = importlib.util.spec_from_file_location(
			f"{PACKAGE_NAME}.provider",
			PACKAGE_DIR / "provider.py",
		)
		self.provider = importlib.util.module_from_spec(spec)
		self.savedModules[spec.name] = sys.modules.get(spec.name, _MISSING)
		sys.modules[spec.name] = self.provider
		spec.loader.exec_module(self.provider)
		self.commands = commands

	def tearDown(self):
		for name, previous in self.savedModules.items():
			if previous is _MISSING:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = previous
		if self.savedTranslation is _MISSING:
			del builtins._
		else:
			builtins._ = self.savedTranslation

	def test_sequence_uses_explicit_greek_locale(self):
		# The speech sequence accents short letter names so the synthesizer reads
		# them as one word: "χι" is spoken (and asserted) as "χί". The engine's
		# own tokens stay unaccented for the clipboard and the tests.
		sequence = self.provider.tokensToSpeechSequence(["χι"])

		self.assertIsInstance(sequence[0], self.commands.LangChangeCommand)
		self.assertEqual(sequence[0].lang, "el_GR")
		self.assertEqual(sequence[1], "χί")
		self.assertIsNone(sequence[-1].lang)

	def test_short_letter_names_are_accented_for_speech(self):
		sequence = self.provider.tokensToSpeechSequence(["ψι", "στο τετράγωνο", "συν", "ρο"])
		spoken = [item for item in sequence if isinstance(item, str)]
		self.assertEqual(spoken, ["ψί", "στο τετράγωνο", "συν", "ρό"])

	def test_preposition_se_is_not_respelled(self):
		# "σε" (raised to) must stay the preposition, not become the letter name.
		sequence = self.provider.tokensToSpeechSequence(["χι", "υψωμένο σε", "ψι"])
		spoken = [item for item in sequence if isinstance(item, str)]
		self.assertEqual(spoken, ["χί", "υψωμένο σε", "ψί"])

	def test_missing_greek_voice_is_logged_once(self):
		self.synth.languageIsSupported = lambda language: False

		self.provider.tokensToSpeechSequence(["χι"])
		self.provider.tokensToSpeechSequence(["ψι"])

		matching = [message for message in self.log.warnings if "no installed Greek voice" in message]
		self.assertEqual(len(matching), 1)


if __name__ == "__main__":
	unittest.main()
