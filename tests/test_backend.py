# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
"""Capability-gated MathCAT Greek backend selection."""

import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
	unittest.main()
