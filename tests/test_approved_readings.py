# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Approved readings and explicit exclusions from the 2026-09-08 request."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon/globalPlugins/greekMathReader"))
from engine import ReadingConfig, speak_latex, speak_mathml, speak_unicodemath, tokens_to_text, parse_mathml, semantic_navigation_children


def latex(source, **options):
	return tokens_to_text(speak_latex(source, ReadingConfig(**options)))


def mathml(source, **options):
	return tokens_to_text(speak_mathml(source, ReadingConfig(**options)))


class TestApprovedReadings(unittest.TestCase):
	def test_g_pronunciation_without_changing_function_structure(self):
		self.assertEqual(latex('f(g(x))'), 'εφ του παρένθεση τζί του χι κλείνει η παρένθεση')
		self.assertEqual(latex('G+g'), 'τζί συν τζί')
		self.assertEqual(latex('G+g', latin_literal=True), 'G συν g')

	def test_selected_symbol_and_relation_readings(self):
		self.assertEqual(latex(r'a\le b'), 'έι μικρότερο ή ίσο του μπί')
		self.assertEqual(latex(r'\alpha\le b'), 'άλφα μικρότερο ή ίσο του μπί')
		self.assertEqual(latex(r'a\ne b'), 'έι διάφορο του μπί')
		self.assertEqual(latex(r'a\approx b'), 'έι περίπου ίσο με μπί')
		self.assertEqual(latex(r'A\subseteq B'), 'έι υποσύνολο ή ίσο με μπί')
		self.assertEqual(latex(r'\forall x'), 'για κάθε χι')
		self.assertEqual(latex(r'\partial'), 'σύμβολο μερικής παραγώγου')
		self.assertEqual(latex(r'\frac{\partial f}{\partial x}'), 'μερική παράγωγος του εφ ως προς χι')
		self.assertEqual(latex('*'), 'αστερίσκος')
		self.assertEqual(latex(r'\ast'), 'αστερίσκος')
		self.assertEqual(latex('a*b'), 'έι επί μπί')

	def test_selected_contextual_readings(self):
		self.assertEqual(latex(r'\int f(x)\,dx'), 'ολοκλήρωμα της εφ του χι ως προς χ')
		self.assertEqual(latex(r'\int f(y)\,dy'), 'ολοκλήρωμα της εφ του γουάι ως προς γουάι')
		self.assertEqual(latex(r'\int f(z)\,dz'), 'ολοκλήρωμα της εφ του ζήτα ως προς ζήτα')
		self.assertEqual(latex(r'\iint f(x,y)dxdy'), 'διπλό ολοκλήρωμα της εφ του χι κόμμα γουάι ως προς χ και γουάι')
		self.assertEqual(latex(r'\langle u,v\rangle'), 'γωνιακή αγκύλη γιού κόμμα βί κλείνει η γωνιακή αγκύλη')
		self.assertEqual(latex(r'\langle u,v\rangle', domain_hint='linear_algebra'), 'εσωτερικό γινόμενο γιού με βί')
		self.assertEqual(latex(r'A^*'), 'συζυγής του έι')
		self.assertEqual(mathml('<math><msup><mi intent=":matrix">A</mi><mo>*</mo></msup></math>'), 'συζυγής ανάστροφος του πίνακα έι')
		self.assertEqual(latex(r'i^2=-1'), 'άι στο τετράγωνο ίσον μείον ένα')
		self.assertEqual(latex(r'e^{i\pi}+1=0'), 'ί υψωμένο σε άι επί πι συν ένα ίσον μηδέν')
		self.assertEqual(latex(r'R^\rho_{\sigma\mu\nu}'), 'κεφαλαίο άρ με κάτω δείκτες σίγμα μι νι και άνω δείκτη ρο')
		self.assertEqual(latex(r'R_{\mu\nu}'), 'κεφαλαίο άρ με κάτω δείκτες μι νι')
		self.assertEqual(latex(r'g_{\mu\nu}'), 'τζί με κάτω δείκτες μι νι')
		self.assertEqual(latex(r'\mathbb R^n'), 'πραγματικός χώρος νι διαστάσεων')
		self.assertEqual(latex(r'e+i+\epsilon+\iota'), 'ί συν άι συν έψιλον συν γιώτα')

	def test_fraction_followed_by_factor_has_boundary(self):
		self.assertEqual(latex(r'\frac{a}{b}c'), 'κλάσμα με αριθμητή έι, και παρονομαστή μπί, τέλος κλάσματος επί σί')
		self.assertEqual(latex(r'\frac{a}{b}+c'), 'έι διά μπί συν σί')
		self.assertEqual(latex(r'\frac{3}{4}'), 'τρία τέταρτα')

	def test_decimal_digits_are_optional(self):
		self.assertEqual(latex('1.025'), '1,025')
		self.assertEqual(latex('1.025', decimal_digits=True), 'ένα κόμμα μηδέν δύο πέντε')
		self.assertEqual(latex('12.03', decimal_digits=True), '12 κόμμα μηδέν τρία')

	def test_point_definition_in_geometry(self):
		self.assertEqual(latex('P=(a,b)', domain_hint='geometry'), 'το σημείο πι έχει συντεταγμένες έι και μπί')
		self.assertIn('ανοιχτό διάστημα', latex('P=(a,b)'))
		self.assertIn('ανοιχτό διάστημα', latex(r'x\in(a,b)', domain_hint='geometry'))

	def test_modular_congruence(self):
		for source in (r'a\equiv b\pmod{n}', r'a\equiv b\pmod n'):
			self.assertEqual(latex(source), 'έι ισότιμο με μπί μόντουλο νι')
		self.assertEqual(latex(r'a\equiv b'), 'έι ταυτίζεται με μπί')

	def test_evaluation_bounds(self):
		self.assertEqual(latex(r'\left.f(x)\right|_a^b'), 'εφ του χι, υπολογισμένο από έι έως μπί')
		self.assertEqual(latex(r'\left|x\right|'), 'απόλυτη τιμή του χι')

	def test_scalar_products_in_all_domains(self):
		for domain in ('auto', 'physics', 'vector_calculus', 'quantum_physics'):
			for op in (r'\times', r'\cdot'):
				self.assertEqual(latex('3'+op+'4', domain_hint=domain), '3 επί 4')
		self.assertEqual(latex(r'a\times b', domain_hint='physics'), 'διανυσματικό γινόμενο έι με μπί')

	def test_tensor_indices_and_true_powers(self):
		self.assertEqual(latex(r'T_\mu^\nu'), 'κεφαλαίο ταυ με κάτω δείκτη μι και άνω δείκτη νι')
		self.assertEqual(latex(r'G_{\mu\nu}'), 'κεφαλαίο τζί με κάτω δείκτες μι νι')
		self.assertEqual(latex(r'\Gamma^\rho_{\mu\nu}'), 'κεφαλαίο γάμα με άνω δείκτη ρο και κάτω δείκτες μι νι')
		self.assertEqual(latex('c^4'), 'σί στην τέταρτη')
		self.assertEqual(latex('x_1^2'), 'χι 1 στο τετράγωνο')
		self.assertEqual(latex(r'T_\mu^2'), 'ταυ μι στο τετράγωνο')

	def test_piecewise_values_and_conditions(self):
		self.assertEqual(latex(r'\begin{cases}x & x>0 \\ 0 & x\leq0\end{cases}'),
		 'δύο περιπτώσεις: χι όταν χι μεγαλύτερο του μηδενός, μηδέν όταν χι μικρότερο ή ίσο του μηδενός')
		self.assertIn('σύστημα 2 εξισώσεων', latex(r'\begin{cases}x+y=3 \\ x-y=1\end{cases}'))

	def test_initial_condition_requires_identification(self):
		self.assertEqual(mathml('<math intent="initial-condition($condition)"><mrow arg="condition"><mi>y</mi><mo>(</mo><mn>0</mn><mo>)</mo><mo>=</mo><mn>1</mn></mrow></math>'),
		 'αρχική συνθήκη: γουάι του μηδενός ίσον ένα')
		self.assertEqual(latex('y(0)=1'), 'γουάι παρένθεση 0 κλείνει η παρένθεση ίσον 1')

	def test_expectation_profiles_and_overrides(self):
		for profile, head in [('standard', 'αναμενόμενη τιμή του'), ('university', 'αναμενόμενη τιμή του'), ('school', 'μέση τιμή του')]:
			for source in ['E(X)', 'E[X]']:
				self.assertEqual(latex(source, terminology_profile=profile), head+' χι')
		self.assertEqual(latex('E(X)', terminology_overrides={'expectation':'προσδοκία του'}), 'προσδοκία του χι')

	def test_normal_distribution_in_statistics(self):
		self.assertEqual(latex(r'X\sim N(\mu,\sigma^2)', domain_hint='probability_statistics'),
		 'κεφαλαίο χι ακολουθεί κανονική κατανομή με μέση τιμή μι και διακύμανση σίγμα στο τετράγωνο')
		self.assertIn('όμοιο με', latex(r'X\sim N(\mu,\sigma^2)'))

	def test_gamma_function(self):
		self.assertEqual(latex(r'\Gamma(z)'), 'συνάρτηση γάμα του ζήτα')
		self.assertEqual(latex(r'\Gamma'), 'γάμα')

	def test_fourier_requires_identification(self):
		self.assertEqual(mathml('<math intent="fourier-transform($f)"><mrow arg="f"><mi>f</mi><mo>(</mo><mi>t</mi><mo>)</mo></mrow></math>'),
		 'μετασχηματισμός Φουριέ της εφ του ταυ')
		self.assertNotIn('Φουριέ', latex(r'\mathcal F\{f(t)\}'))

	def test_classical_hamiltonian_requires_identification(self):
		self.assertEqual(mathml('<math intent="classical-hamiltonian($q,$p)"><mi arg="q">q</mi><mi arg="p">p</mi></math>'),
		 'χαμιλτονιανή συνάρτηση των κιού και πί')
		self.assertEqual(latex('H(q,p)'), 'έιτς παρένθεση κιού κόμμα πι κλείνει η παρένθεση')

	def test_newton_equation_symbolic_reading(self):
		self.assertEqual(latex('F=ma'), 'κεφαλαίο εφ ίσον μι επί έι')
		self.assertEqual(latex('F=mb'), 'εφ ίσον μι μπί')

	def test_matrix_references_without_changing_dagger(self):
		self.assertEqual(latex('A^T'), 'ανάστροφος του πίνακα έι')
		self.assertEqual(latex(r'\det(A)'), 'ορίζουσα του πίνακα έι')
		self.assertEqual(latex('A^{-1}'), 'αντίστροφος πίνακας έι')
		self.assertEqual(latex(r'a^\dagger'), 'συζυγής ανάστροφος του έι')
		self.assertEqual(latex(r'a^\dagger', domain_hint='quantum_physics'), 'ερμιτιανός συζυγής του έι')

	def test_dirac_delta_requires_identification(self):
		self.assertEqual(mathml('<math intent="dirac-delta($x)"><mi arg="x">x</mi></math>'), 'δέλτα του Ντιράκ στο χι')
		self.assertEqual(latex(r'\delta(x)'), 'δέλτα παρένθεση χι κλείνει η παρένθεση')

	def test_unapproved_examples_keep_their_existing_readings(self):
		cases = {
		 r'\operatorname{sinc}(x)': 'συνάρτηση συγχρονισμού του χι',
		 r'\Delta f': 'μεταβολή του εφ',
		 r'f*g': 'εφ επί τζί',
		 r'G/H': 'τζί διά έιτς',
		 r'\operatorname{Tr}_B(\rho)': 'ίχνος μπί του ρο',
		 r'\delta(x)': 'δέλτα παρένθεση χι κλείνει η παρένθεση',
		}
		for source, expected in cases.items():
			with self.subTest(source=source):
				self.assertEqual(latex(source), expected)

	def test_fraction_boundary_keeps_derivative_operator(self):
		self.assertEqual(latex(r'\frac{d}{dx}f(x)'), 'παράγωγος ως προς χι εφ του χι')
		self.assertEqual(mathml('<math><mfrac><mi>a</mi><mi>b</mi></mfrac><mo>⁢</mo><mi>c</mi></math>'),
		 'κλάσμα με αριθμητή έι, και παρονομαστή μπί, τέλος κλάσματος επί σί')

	def test_decimal_digits_preserve_grouped_numbers(self):
		self.assertEqual(mathml('<math><mn>1.234.567</mn></math>', decimal_digits=True), '1.234.567')
		self.assertEqual(latex('1.025', decimal_digits=True, decimal_comma=False), 'ένα τελεία μηδέν δύο πέντε')

	def test_nested_annotations_keep_identified_meaning(self):
		self.assertEqual(mathml('<math><mrow intent="dirac-delta($x)"><mi arg="x">x</mi></mrow></math>'), 'δέλτα του Ντιράκ στο χι')
		self.assertEqual(mathml('<math intent="gamma-function($z)"><mi arg="z">z</mi></math>'), 'συνάρτηση γάμα του ζήτα')

	def test_incomplete_approved_intents_preserve_operands(self):
		for name in ('dirac-delta', 'fourier-transform', 'classical-hamiltonian', 'normal-distribution', 'point-definition', 'modular-congruence', 'evaluation'):
			source = f'<math intent="{name}($x,$y,$z,$w)"><mi arg="x">x</mi><mi arg="y">y</mi><mi arg="z">z</mi><mi arg="w">w</mi></math>'
			self.assertEqual(mathml(source), 'χι γουάι ζήτα ντάμπλιου')

	def test_evaluation_in_mathml_with_bounds_on_bar(self):
		self.assertEqual(mathml('<math><mi>f</mi><mo>(</mo><mi>x</mi><mo>)</mo><msubsup><mo>|</mo><mi>a</mi><mi>b</mi></msubsup></math>'),
		 'εφ του χι, υπολογισμένο από έι έως μπί')
		self.assertNotIn('υπολογισμένο', latex(r'\left|x\right|_a^b'))

	def test_tensor_multiscripts_and_combined_index_tokens(self):
		self.assertEqual(mathml('<math><mmultiscripts><mi>T</mi><mi>μ</mi><mi>ν</mi></mmultiscripts></math>'),
		 'κεφαλαίο ταυ με κάτω δείκτη μι και άνω δείκτη νι')
		self.assertEqual(mathml('<math><msub><mi>G</mi><mi>μν</mi></msub></math>'), 'κεφαλαίο τζί με κάτω δείκτες μι νι')
		self.assertEqual(mathml('<math><mmultiscripts><mi>Γ</mi><none/><mi>ρ</mi><mi>μ</mi><none/><mi>ν</mi><none/></mmultiscripts></math>'),
		 'κεφαλαίο γάμα με άνω δείκτη ρο και κάτω δείκτες μι νι')

	def test_tensor_unicodemath_matches_latex(self):
		for source, tex in [('T_μ^ν', r'T_\mu^\nu'), ('G_(μν)', r'G_{\mu\nu}'), ('Γ_(μν)^ρ', r'\Gamma^\rho_{\mu\nu}')]:
			self.assertEqual(tokens_to_text(speak_unicodemath(source)), latex(tex))

	def test_expectation_and_gamma_inside_larger_expressions(self):
		self.assertEqual(latex('E(X)+E[X]'), 'αναμενόμενη τιμή του χι συν αναμενόμενη τιμή του χι')
		self.assertEqual(latex(r'\Gamma(z)+\Gamma(w)'), 'συνάρτηση γάμα του ζήτα συν συνάρτηση γάμα του ντάμπλιου')
		self.assertEqual(mathml('<math><mi>E</mi><mo>⁡</mo><mo>(</mo><mi>X</mi><mo>|</mo><mi>Y</mi><mo>)</mo></math>'),
		 'αναμενόμενη τιμή του χι δεδομένου του γουάι')

	def test_initial_condition_preserves_decimal_values(self):
		self.assertEqual(mathml('<math intent="initial-condition($c)"><mrow arg="c"><mi>y</mi><mo>(</mo><mn>0.5</mn><mo>)</mo><mo>=</mo><mn>1.0</mn></mrow></math>'),
		 'αρχική συνθήκη: γουάι του 0,5 ίσον 1,0')

	def test_normal_distribution_identification_and_malformed_input(self):
		self.assertEqual(mathml('<math intent="normal-distribution($x,$mean,$variance)"><mi arg="x">X</mi><mi arg="mean">μ</mi><msup arg="variance"><mi>σ</mi><mn>2</mn></msup></math>'),
		 'κεφαλαίο χι ακολουθεί κανονική κατανομή με μέση τιμή μι και διακύμανση σίγμα στο τετράγωνο')
		self.assertTrue(mathml('<math><mi>X</mi><mo>∼</mo><mi>N</mi><mo>(</mo><mi>μ</mi><mo>,</mo><msup><mi>σ</mi></msup><mo>)</mo></math>', domain_hint='probability_statistics'))

	def test_identified_operands_remain_navigable(self):
		tree = parse_mathml('<math intent="classical-hamiltonian($q,$p)"><mi arg="q">q</mi><mi arg="p">p</mi></math>')
		self.assertEqual([n.text for n in semantic_navigation_children(tree)], ['q', 'p'])
