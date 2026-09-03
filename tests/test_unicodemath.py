# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""UnicodeMath input and cross-format semantic parity tests."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import (  # noqa: E402
	detect_math_format,
	speak_latex,
	speak_mathml,
	speak_unicodemath,
	tokens_to_text,
	unicodemath_to_latex,
)


class TestUnicodeMath(unittest.TestCase):
	def spoken(self, source):
		return tokens_to_text(speak_unicodemath(source))

	def test_detection_prefers_distinctive_syntax(self):
		self.assertEqual(detect_math_format("x²+1"), "unicodemath")
		self.assertEqual(detect_math_format("■(1&2@3&4)"), "unicodemath")
		self.assertEqual(detect_math_format(r"\frac{1}{2}"), "latex")
		self.assertEqual(detect_math_format("x^2"), "latex")
		self.assertIsNone(detect_math_format("just some words"))

	def test_scripts_roots_and_large_operators(self):
		self.assertEqual(self.spoken("x²+1"), "χι στο τετράγωνο συν 1")
		self.assertEqual(self.spoken("√(x+1)"), "τετραγωνική ρίζα του χι συν 1")
		self.assertEqual(
			self.spoken("∑_(n=1)^∞ 1/n²"),
			"άθροισμα για νι από 1 έως άπειρο του 1 διά νι στο τετράγωνο",
		)

	def test_word_linear_matrix(self):
		self.assertEqual(
			self.spoken("■(1&2@3&4)"),
			"πίνακας 2 επί 2, γραμμή 1: 1, 2, γραμμή 2: 3, 4 τέλος πίνακα",
		)

	def test_adjoint_and_compound_si_units(self):
		self.assertEqual(self.spoken("A†"), "συζυγής ανάστροφος του άλφα")
		self.assertEqual(self.spoken("1 m/s"), "1 μέτρο ανά δευτερόλεπτο")
		self.assertEqual(self.spoken("2 m/s"), "2 μέτρα ανά δευτερόλεπτο")
		self.assertEqual(
			self.spoken("3 kg·m/s²"),
			"3 κιλά επί μέτρο ανά δευτερόλεπτο στο τετράγωνο",
		)
		self.assertEqual(
			self.spoken("1 kg·m/s²"),
			"1 κιλό επί μέτρο ανά δευτερόλεπτο στο τετράγωνο",
		)

	def test_conversion_is_auditable(self):
		self.assertEqual(unicodemath_to_latex("x²+1"), "x^{2}+1")
		self.assertIn(r"\begin{pmatrix}", unicodemath_to_latex("■(1&2@3&4)"))


class TestCrossFormatParity(unittest.TestCase):
	def assertSpeechParity(self, mathml, latex, unicodemath):
		readings = {
			tokens_to_text(speak_mathml(mathml)),
			tokens_to_text(speak_latex(latex)),
			tokens_to_text(speak_unicodemath(unicodemath)),
		}
		self.assertEqual(len(readings), 1, readings)

	def test_square(self):
		self.assertSpeechParity(
			"<math><msup><mi>x</mi><mn>2</mn></msup></math>",
			"x^2",
			"x²",
		)

	def test_adjoint(self):
		self.assertSpeechParity(
			"<math><msup><mi>A</mi><mo>†</mo></msup></math>",
			r"A^\dagger",
			"A†",
		)

	def test_sum(self):
		self.assertSpeechParity(
			"<math><munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><mo>∞</mo></munderover><mfrac><mn>1</mn><msup><mi>n</mi><mn>2</mn></msup></mfrac></math>",
			r"\sum_{n=1}^{\infty}\frac{1}{n^2}",
			"∑_(n=1)^∞ 1/n²",
		)


if __name__ == "__main__":
	unittest.main()
