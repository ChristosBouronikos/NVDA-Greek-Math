# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Capability-gated MathCAT Greek backend selection."""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from backend import AutomaticMathBackend  # noqa: E402


class FakeMathCat:
	def __init__(self, languages):
		self.languages = languages
		self.preferences = []
		self.requests = []

	def GetSupportedLanguages(self):
		return self.languages

	def SetPreference(self, name, value):
		self.preferences.append((name, value))

	def getSpeechForMathMl(self, mathml):
		self.requests.append(mathml)
		return ["MathCAT Greek"]


class TestAutomaticMathBackend(unittest.TestCase):
	def test_uses_mathcat_only_when_greek_is_advertised(self):
		delegate = FakeMathCat(["en", "el", "sv"])
		backend = AutomaticMathBackend()
		self.assertTrue(backend.configure(delegate))
		self.assertTrue(backend.usingMathCat)
		self.assertEqual(backend.getSpeechForMathMl("<math/>"), ["MathCAT Greek"])
		self.assertIn(("Language", "el"), delegate.preferences)

	def test_non_greek_mathcat_falls_back_locally(self):
		backend = AutomaticMathBackend()
		self.assertFalse(backend.configure(FakeMathCat(["en", "fr"])))
		self.assertFalse(backend.usingMathCat)
		self.assertEqual(backend.diagnostics()["backend"], "local")

	def test_disabled_adapter_never_probes_or_delegates(self):
		backend = AutomaticMathBackend()
		self.assertFalse(backend.configure(FakeMathCat(["el"]), enabled=False))
		self.assertIsNone(backend.getSpeechForMathMl("<math/>"))
		self.assertIn("disabled", backend.diagnostics()["detail"].lower())

	def test_unrelated_greek_module_cannot_enable_english_delegate(self):
		delegate = FakeMathCat(["en"])
		module = types.ModuleType("MathCAT")
		module.GetSupportedLanguages = lambda: ["el"]
		module.SetPreference = lambda name, value: None
		backend = AutomaticMathBackend()
		with patch.dict(sys.modules, {"MathCAT": module}):
			self.assertFalse(backend.configure(delegate))
		self.assertIsNone(backend.getSpeechForMathMl("<math/>"))
		self.assertEqual(delegate.preferences, [])
		self.assertEqual(delegate.requests, [])

	def test_delegate_cannot_borrow_unrelated_language_setter(self):
		delegate = FakeMathCat(["el"])
		delegate.SetPreference = None
		module = types.ModuleType("MathCAT")
		module.SetPreference = lambda name, value: None
		with patch.dict(sys.modules, {"MathCAT": module}):
			self.assertFalse(AutomaticMathBackend().configure(delegate))

	def test_language_is_reselected_before_every_speech_request(self):
		class ResettingMathCat(FakeMathCat):
			language = "en"

			def SetPreference(self, name, value):
				self.language = value
				super().SetPreference(name, value)

			def getSpeechForMathMl(self, mathml):
				language = self.language
				self.language = "en"
				return [language]

		delegate = ResettingMathCat(["el"])
		backend = AutomaticMathBackend()
		self.assertTrue(backend.configure(delegate))
		delegate.language = "en"
		self.assertEqual(backend.getSpeechForMathMl("<math/>"), ["el"])
		self.assertEqual(backend.getSpeechForMathMl("<math/>"), ["el"])

	def test_language_selection_failure_stops_delegation(self):
		delegate = FakeMathCat(["el"])
		backend = AutomaticMathBackend()
		self.assertTrue(backend.configure(delegate))
		delegate.SetPreference = lambda name, value: False
		self.assertIsNone(backend.getSpeechForMathMl("<math/>"))
		self.assertFalse(backend.usingMathCat)
		self.assertEqual(delegate.requests, [])

	def test_rejected_language_selection_does_not_enable_delegate(self):
		delegate = FakeMathCat(["el"])
		delegate.SetPreference = lambda name, value: False
		self.assertFalse(AutomaticMathBackend().configure(delegate))


if __name__ == "__main__":
	unittest.main()
