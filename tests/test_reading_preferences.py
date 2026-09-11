# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Behavioral coverage for user-facing reading preferences."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon/globalPlugins/greekMathReader"))
from engine import ReadingConfig, speak_mathml, speak_latex, tokens_to_text, Pause
from engine.symbols_el import validate_pronunciations

MATRIX = '<math><mrow><mo>[</mo><mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>0</mn></mtd></mtr><mtr><mtd><mn>3</mn></mtd><mtd><mn>2</mn></mtd></mtr></mtable><mo>]</mo></mrow></math>'


def reading(source, **settings):
	return tokens_to_text(speak_mathml(source, ReadingConfig(**settings)))


class TestReadingPreferences(unittest.TestCase):
	def test_capitals_across_identifier_paths(self):
		for source in ('<mi>G</mi>', '<mo>G</mo>', '<mi>𝐆</mi>'):
			self.assertEqual(reading('<math>'+source+'</math>', announce_capitals=True), 'κεφαλαίο τζί')
		self.assertEqual(reading('<math><mi>AB</mi></math>', announce_capitals=True), 'κεφαλαίο έι κεφαλαίο μπί')
		self.assertEqual(reading('<math><mi>ABCDEFG</mi></math>', announce_capitals=True).count('κεφαλαίο'), 7)
		self.assertEqual(reading('<math><mi>AgΓγ</mi></math>', announce_capitals=True), 'κεφαλαίο έι τζί κεφαλαίο γάμα γάμα')
		self.assertEqual(reading('<math><mi>G</mi></math>'), 'τζί')

	def test_capitals_and_literal_mode(self):
		self.assertEqual(reading('<math><mi>AB</mi><mo>+</mo><mi>g</mi></math>', announce_capitals=True, latin_literal=True), 'κεφαλαίο A κεφαλαίο B συν g')
		self.assertEqual(reading('<math><mo>G</mo></math>', announce_capitals=True, latin_literal=True), 'κεφαλαίο G')
		self.assertEqual(reading('<math><mi>Γγ</mi></math>', announce_capitals=True, latin_literal=True), 'κεφαλαίο γάμα γάμα')

	def test_greek_alpha_and_latin_a_remain_distinct(self):
		self.assertEqual(reading('<math><mi>α</mi><mo>+</mo><mi>a</mi><mo>+</mo><mi>A</mi></math>'), 'άλφα συν έι συν έι')
		self.assertEqual(reading('<math><mi>A</mi></math>', announce_capitals=True), 'κεφαλαίο έι')

	def test_custom_names_distinguish_symbols_and_preserve_prose(self):
		names = {'G': 'λατινικό μεγάλο', 'g': 'λατινικό μικρό', 'Γ': 'ελληνικό μεγάλο', 'γ': 'ελληνικό μικρό', 'c': 'σί'}
		self.assertEqual(reading('<math><mi>GgΓγ</mi><mi>c</mi><mtext>σε και τζί</mtext></math>', symbol_pronunciations=names), 'λατινικό μεγάλο λατινικό μικρό ελληνικό μεγάλο ελληνικό μικρό σί σε και τζί')
		self.assertEqual(reading('<math><msup><mi>c</mi><mi>z</mi></msup></math>', symbol_pronunciations=names), 'σί υψωμένο σε ζήτα')
		self.assertEqual(reading('<math><mi>G</mi></math>', symbol_pronunciations=names, latin_literal=True, announce_capitals=True), 'κεφαλαίο λατινικό μεγάλο')

	def test_custom_name_reaches_tensor_and_derivative(self):
		names = {'G': 'τζι δοκιμή', 'X': 'εξ δοκιμή'}
		self.assertIn('κεφαλαίο τζι δοκιμή', reading('<math><msub><mi>G</mi><mi>μν</mi></msub></math>', symbol_pronunciations=names))
		self.assertIn('κεφαλαίο εξ δοκιμή', tokens_to_text(speak_latex(r'\frac{d}{dX}', ReadingConfig(symbol_pronunciations=names, announce_capitals=True))))

	def test_invalid_names_do_not_become_text_replacements(self):
		self.assertEqual(validate_pronunciations({'σε': 'wrong', 'G': '', 'g': 'bad\nname', 'Γ': 'x'*101, 'c': 'σί'}), {'c': 'σί'})
		self.assertEqual(validate_pronunciations([]), {})

	def test_gradient_preference_and_distinct_vector_operators(self):
		for name in ('ανάδελτα', 'κλίση'):
			for source in ('<mo>∇</mo>', '<mi>∇</mi>', '<mi>grad</mi>'):
				self.assertEqual(reading('<math>'+source+'</math>', gradient_name=name), name)
			self.assertEqual(reading('<math><mo>∇</mo><mi>f</mi></math>', gradient_name=name), name+' του εφ')
			self.assertEqual(reading('<math><mi>grad</mi><mo>(</mo><mi>f</mi><mo>)</mo></math>', gradient_name=name), name+' του εφ')
			self.assertEqual(reading('<math><mo>∇</mo><mo>×</mo><mi>F</mi></math>', gradient_name=name), 'στροβιλισμός του εφ')

	def test_composition_explanation_is_optional(self):
		self.assertEqual(tokens_to_text(speak_latex(r'f\circ g')), 'εφ σύνθεση τζί')
		self.assertEqual(tokens_to_text(speak_latex(r'f\circ g', ReadingConfig(explain_composition=True))), 'σύνθεση της εφ με τη τζί: πρώτα εφαρμόζεται η τζί και μετά η εφ')
		self.assertEqual(tokens_to_text(speak_latex('f(g(x))', ReadingConfig(explain_composition=True))), 'εφ του παρένθεση τζί του χι κλείνει η παρένθεση')
		self.assertNotIn('πρώτα', tokens_to_text(speak_latex(r'3\circ4', ReadingConfig(explain_composition=True))))

	def test_quotient_requires_author_identification_even_in_algebra(self):
		for domain in ('auto', 'algebra'):
			self.assertEqual(tokens_to_text(speak_latex('G/H', ReadingConfig(domain_hint=domain))), 'τζί διά έιτς')
		self.assertEqual(reading('<math intent="quotient-group($g,$h)"><mi arg="g">G</mi><mo>/</mo><mi arg="h">H</mi></math>'), 'ομάδα πηλίκο της τζί ως προς την έιτς')
		self.assertNotIn('ομάδα πηλίκο', reading('<math intent="quotient-group($g)"><mi arg="g">G</mi><mo>/</mo><mi>H</mi></math>'))

	def test_matrix_default_and_zero_entries(self):
		self.assertEqual(reading(MATRIX), 'πίνακας 2 επί 2, γραμμή 1: 1, 0, γραμμή 2: 3, 2 τέλος πίνακα')
		for mode in ('whole', 'rows', 'columns'):
			self.assertIn('0', reading(MATRIX, matrix_reading=mode))
		self.assertEqual(reading(MATRIX, matrix_reading='rows'), reading(MATRIX))
		columns = reading(MATRIX, matrix_reading='columns')
		self.assertLess(columns.index('3'), columns.index('στήλη 2'))
		self.assertIn('στήλη 2: 0', columns)
		self.assertIn('στήλη 2:', reading(MATRIX, matrix_positions=True))

	def test_dimensions_mode_announces_exploration(self):
		self.assertEqual(reading(MATRIX, matrix_reading='explore'), 'πίνακας 2 επί 2, χρησιμοποιήστε την αλληλεπίδραση μαθηματικών για εξερεύνηση των στοιχείων')
		self.assertNotIn('εξερεύνηση', reading('<math><mo>{</mo><mtable><mtr><mtd><mi>x</mi></mtd><mtd><mi>x</mi><mo>&gt;</mo><mn>0</mn></mtd></mtr></mtable></math>', matrix_reading='explore'))

	def test_pause_scaling(self):
		standard = [t.ms for t in speak_mathml(MATRIX) if isinstance(t, Pause)]
		for factor, scale in ((0, 0), (50, 1), (100, 2)):
			actual = [t.ms for t in speak_mathml(MATRIX, ReadingConfig(pause_factor=factor)) if isinstance(t, Pause)]
			self.assertEqual(actual, [value*scale for value in standard])
