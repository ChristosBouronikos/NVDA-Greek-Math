# -*- coding: utf-8 -*-
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""Δοκιμές του αναγνώστη LaTeX: LaTeX → ελληνική εκφώνηση.

Εκτέλεση:  python3 -m unittest discover tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import (  # noqa: E402
	LatexParseError,
	ReadingConfig,
	SMART,
	TERSE,
	VERBOSE,
	looks_like_latex,
	speak_latex,
	strip_math_delimiters,
	tokens_to_text,
)


def spoken(latex, verbosity=SMART):
	return tokens_to_text(speak_latex(latex, ReadingConfig(verbosity=verbosity)))


class TestLatexBasics(unittest.TestCase):
	def test_addition(self):
		self.assertEqual(spoken("2 + 3 = 5"), "2 συν 3 ίσον 5")

	def test_latin_letters(self):
		self.assertEqual(spoken("x + y"), "χι συν ψι")

	def test_greek_letters(self):
		self.assertEqual(spoken(r"\alpha + \beta"), "άλφα συν βήτα")

	def test_unary_minus(self):
		self.assertEqual(spoken("-x"), "μείον χι")

	def test_times(self):
		self.assertEqual(spoken(r"2 \times 3"), "2 επί 3")

	def test_decimal_comma(self):
		self.assertEqual(spoken("3.14"), "3,14")


class TestLatexPowersAndScripts(unittest.TestCase):
	def test_square(self):
		self.assertEqual(spoken("x^2"), "χι στο τετράγωνο")

	def test_pythagorean(self):
		self.assertEqual(spoken("a^2 + b^2"), "α στο τετράγωνο συν μπε στο τετράγωνο")

	def test_braced_exponent(self):
		self.assertEqual(spoken("x^{n+1}"), "χι υψωμένο σε νι συν 1")

	def test_subscript(self):
		self.assertEqual(spoken("x_1"), "χι 1")

	def test_sub_and_sup(self):
		self.assertEqual(spoken("x_1^2"), "χι 1 στο τετράγωνο")

	def test_prime(self):
		self.assertEqual(spoken("f'"), "εφ τόνος")


class TestLatexFractionsAndRoots(unittest.TestCase):
	def test_named_fraction(self):
		self.assertEqual(spoken(r"\frac{3}{4}"), "τρία τέταρτα")

	def test_symbolic_fraction(self):
		self.assertEqual(spoken(r"\frac{\alpha}{\beta}"), "άλφα διά βήτα")

	def test_complex_fraction(self):
		self.assertEqual(
			spoken(r"\frac{x^2 + 1}{x - 1}"),
			"κλάσμα με αριθμητή χι στο τετράγωνο συν 1, και παρονομαστή χι πλην 1, τέλος κλάσματος",
		)

	def test_sqrt(self):
		self.assertEqual(spoken(r"\sqrt{2}"), "τετραγωνική ρίζα του 2")

	def test_cube_root(self):
		self.assertEqual(spoken(r"\sqrt[3]{8}"), "κυβική ρίζα του 8")

	def test_binomial(self):
		self.assertEqual(spoken(r"\binom{n}{k}"), "παρένθεση συνδυασμοί νι ανά κάπα κλείνει η παρένθεση")


class TestLatexFunctions(unittest.TestCase):
	def test_sin(self):
		self.assertEqual(spoken(r"\sin x"), "ημίτονο χι")

	def test_ln(self):
		self.assertEqual(spoken(r"\ln x"), "φυσικός λογάριθμος χι")

	def test_function_call(self):
		self.assertEqual(spoken("f(x)"), "εφ του χι")


class TestLatexBigOperators(unittest.TestCase):
	def test_definite_integral(self):
		self.assertEqual(
			spoken(r"\int_0^1 x^2 dx"),
			"ολοκλήρωμα από 0 έως 1 του χι στο τετράγωνο ντε χι",
		)

	def test_sum_with_bounds(self):
		self.assertEqual(
			spoken(r"\sum_{n=1}^{\infty} \frac{1}{n^2}"),
			"άθροισμα για νι από 1 έως άπειρο του 1 διά νι στο τετράγωνο",
		)

	def test_limit(self):
		self.assertEqual(
			spoken(r"\lim_{x \to 0} \frac{\sin x}{x}"),
			"όριο καθώς το χι τείνει στο 0 του ημίτονο χι διά χι",
		)


class TestLatexDelimitersAndMatrices(unittest.TestCase):
	def test_left_right_parens(self):
		self.assertEqual(
			spoken(r"\left( x + 1 \right)"),
			"παρένθεση χι συν 1 κλείνει η παρένθεση",
		)

	def test_absolute_value(self):
		self.assertEqual(spoken(r"\left| x \right|"), "απόλυτη τιμή του χι")

	def test_pmatrix(self):
		self.assertEqual(
			spoken(r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}"),
			"πίνακας 2 επί 2, γραμμή 1: 1, 2, γραμμή 2: 3, 4 τέλος πίνακα",
		)

	def test_determinant(self):
		self.assertEqual(
			spoken(r"\begin{vmatrix} a & b \\ c & d \end{vmatrix}"),
			"ορίζουσα 2 επί 2, γραμμή 1: α, μπε, γραμμή 2: σε, ντε τέλος ορίζουσας",
		)


class TestLatexAccentsAndSymbols(unittest.TestCase):
	def test_vector(self):
		self.assertEqual(spoken(r"\vec{v}"), "διάνυσμα βε")

	def test_bar(self):
		self.assertEqual(spoken(r"\bar{x}"), "μέσος όρος του χι")

	def test_complex_conjugate(self):
		self.assertEqual(spoken(r"\bar{z}"), "συζυγής του ζήτα")

	def test_number_set(self):
		self.assertEqual(
			spoken(r"x \in \mathbb{R}"),
			"χι ανήκει στο σύνολο των πραγματικών αριθμών",
		)

	def test_infinity(self):
		self.assertEqual(spoken(r"\infty"), "άπειρο")

	def test_unknown_command_spoken_by_name(self):
		# Άγνωστη εντολή: εκφωνείται με το όνομά της αντί να χαθεί σιωπηλά.
		self.assertEqual(spoken(r"\foo"), "foo")


class TestLatexExpandedVocabulary(unittest.TestCase):
	def test_conditional_probability(self):
		self.assertEqual(
			spoken(r"P(A\mid B)"),
			"πιθανότητα του άλφα δεδομένου του βήτα",
		)

	def test_expected_value_and_variance(self):
		self.assertEqual(
			spoken(r"E(X)+\operatorname{Var}(X)"),
			"μέση τιμή του χι συν διακύμανση του χι",
		)

	def test_real_and_imaginary_parts(self):
		self.assertEqual(
			spoken(r"\Re(z)+\Im(z)"),
			"πραγματικό μέρος του ζήτα συν φανταστικό μέρος του ζήτα",
		)

	def test_trace_and_rank(self):
		self.assertEqual(
			spoken(r"\tr(A)+\rank(A)"),
			"ίχνος του άλφα συν βαθμός του άλφα",
		)

	def test_complex_modulus(self):
		self.assertEqual(spoken(r"\left|z\right|"), "μέτρο του ζήτα")

	def test_delta_change(self):
		self.assertEqual(spoken(r"\Delta x"), "μεταβολή του χι")

	def test_si_unit_fraction(self):
		self.assertEqual(
			spoken(r"3\frac{\mathrm{m}}{\mathrm{s}^2}"),
			"3 μέτρα ανά δευτερόλεπτο στο τετράγωνο",
		)

	def test_scientific_notation(self):
		self.assertEqual(
			spoken(r"6.02\times10^{23}"),
			"6,02 επί 10 στην εικοστή τρίτη",
		)


class TestLatexDelimiterStripping(unittest.TestCase):
	def test_dollar(self):
		self.assertEqual(spoken(r"$x^2$"), "χι στο τετράγωνο")

	def test_display(self):
		self.assertEqual(spoken(r"\[ x^2 \]"), "χι στο τετράγωνο")

	def test_paren_delims(self):
		self.assertEqual(spoken(r"\(x^2\)"), "χι στο τετράγωνο")

	def test_strip_helper(self):
		self.assertEqual(strip_math_delimiters(r"$x^2$"), "x^2")
		self.assertEqual(strip_math_delimiters(r"\[a\]"), "a")

	def test_empty_raises(self):
		with self.assertRaises(LatexParseError):
			speak_latex("   ")


class TestLooksLikeLatex(unittest.TestCase):
	def test_positive(self):
		self.assertTrue(looks_like_latex(r"\frac{1}{2}"))
		self.assertTrue(looks_like_latex("x^2"))
		self.assertTrue(looks_like_latex("$x$"))
		self.assertTrue(looks_like_latex("x + 1"))

	def test_negative(self):
		self.assertFalse(looks_like_latex("just some words"))
		self.assertFalse(looks_like_latex(""))


if __name__ == "__main__":
	unittest.main()
