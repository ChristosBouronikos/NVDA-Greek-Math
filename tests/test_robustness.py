# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Generated invariants for lossless and non-English structural speech."""

import random
import string
import sys
import unittest
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import get_last_engine_diagnostics, speak_mathml, tokens_to_text  # noqa: E402


class TestGeneratedLosslessProperties(unittest.TestCase):
	def test_generated_unknown_operators_are_never_silent(self):
		randomizer = random.Random(20260801)
		unknown = ("⧖", "⧗", "⟑", "⟒", "⌁", "⦿")
		for _index in range(100):
			operator = randomizer.choice(unknown)
			identifier = "q" + "".join(randomizer.choice(string.ascii_lowercase) for _ in range(5))
			mathml = f"<math><mi>{identifier}</mi><mo>{escape(operator)}</mo><mn>7</mn></math>"
			reading = tokens_to_text(speak_mathml(mathml))
			self.assertIn(identifier, reading)
			self.assertIn(operator, reading)
			diagnostics = get_last_engine_diagnostics()
			self.assertIn(f"operator:{operator}", diagnostics["unknown"])

	def test_generated_unknown_wrappers_preserve_descendants(self):
		for depth in range(1, 25):
			content = "<mi>x</mi>"
			for index in range(depth):
				content = f"<authorNotation{index}>{content}</authorNotation{index}>"
			reading = tokens_to_text(speak_mathml(f"<math>{content}</math>"))
			self.assertEqual(reading, "χι")
			self.assertIn(
				f"unsupported-construct:authornotation{depth - 1}",
				get_last_engine_diagnostics()["fallbacks"],
			)

	def test_short_unknown_identifier_is_spoken_and_diagnostic(self):
		reading = tokens_to_text(speak_mathml("<math><mi>qfoo</mi></math>"))
		self.assertEqual(reading, "κου εφ ο ο")
		diagnostics = get_last_engine_diagnostics()
		self.assertIn("identifier:qfoo", diagnostics["unknown"])
		self.assertIn("multi-letter-identifier-spelled:qfoo", diagnostics["fallbacks"])

	def test_structural_math_does_not_leak_english_reader_words(self):
		mathml = (
			"<math><mfrac><mrow><msup><mi>x</mi><mn>2</mn></msup><mo>+</mo><mn>1</mn></mrow>"
			"<mrow><mi>x</mi><mo>−</mo><mn>1</mn></mrow></mfrac></math>"
		)
		reading = tokens_to_text(speak_mathml(mathml)).lower()
		for english in ("fraction", "numerator", "denominator", "squared", "plus", "minus", "end"):
			self.assertNotIn(english, reading)

	def test_empty_unknown_nodes_do_not_crash_following_content(self):
		reading = tokens_to_text(speak_mathml("<math><unknown/><mi>x</mi><merror/><mn>2</mn></math>"))
		self.assertEqual(reading, "χι 2")


if __name__ == "__main__":
	unittest.main()
