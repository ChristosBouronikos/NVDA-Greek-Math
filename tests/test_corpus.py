# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""Smoke tests for representative MathJax, Word UIA, and MathType MathML shapes."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import speak_mathml, tokens_to_text  # noqa: E402


CORPUS_DIR = Path(__file__).parent / "corpus"
GREEK_TEXT_RE = re.compile(r"[Α-Ωα-ωάέήίόύώϊϋΐΰ]")


class TestRealWorldMathMLCorpus(unittest.TestCase):
	def test_every_sample_produces_greek_speech(self):
		samples = sorted(CORPUS_DIR.glob("*.mathml"))
		self.assertGreaterEqual(len(samples), 3)
		for sample in samples:
			with self.subTest(sample=sample.name):
				mathml = sample.read_text(encoding="utf-8")
				reading = tokens_to_text(speak_mathml(mathml))
				self.assertTrue(reading.strip())
				self.assertRegex(reading, GREEK_TEXT_RE)


if __name__ == "__main__":
	unittest.main()
