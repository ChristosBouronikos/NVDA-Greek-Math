# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Golden tests for the conservative semantic layer and Greek terminology."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import (  # noqa: E402
	Language,
	NavigationMark,
	Prosody,
	ReadingConfig,
	enrich_speech,
	get_last_engine_diagnostics,
	interpret_mathml,
	mathnode_to_mathml,
	parse_mathml,
	semantic_navigation_children,
	speak_mathml,
	tokens_to_text,
)
from engine.terminology_el import (  # noqa: E402
	SEMANTIC_MODULES,
	TERMS,
	reset_override,
	terminology_record,
	validate_overrides,
)


def spoken(mathml, **config):
	return tokens_to_text(speak_mathml(mathml, ReadingConfig(**config)))


class TestSemanticPrecedence(unittest.TestCase):
	def test_author_intent_overrides_ambiguous_presentation(self):
		mathml = '<math intent="transpose($a)"><mi arg="a">A</mi><mo>†</mo></math>'
		self.assertEqual(spoken(mathml), "ανάστροφος του άλφα")
		self.assertEqual(interpret_mathml(mathml).confidence, "author")

	def test_invalid_intent_falls_back_without_losing_content(self):
		mathml = '<math intent="not valid("><mi>x</mi><mo>+</mo><mn>1</mn></math>'
		self.assertEqual(spoken(mathml), "χι συν 1")
		self.assertIn("invalid-intent:not valid(", get_last_engine_diagnostics()["fallbacks"])

	def test_unsupported_intent_falls_back_without_losing_content(self):
		mathml = '<math intent="author-private"><mi>x</mi></math>'
		self.assertEqual(spoken(mathml), "χι")
		self.assertIn("unsupported-intent:author-private", get_last_engine_diagnostics()["fallbacks"])

	def test_unknown_symbols_are_literal_and_diagnostic(self):
		self.assertEqual(spoken("<math><mo>⧖</mo><mi>fooBar</mi></math>"), "⧖ fooBar")
		diagnostics = get_last_engine_diagnostics()
		self.assertIn("operator:⧖", diagnostics["unknown"])
		self.assertIn("identifier:fooBar", diagnostics["unknown"])


class TestLinearAlgebraAndVectorCalculus(unittest.TestCase):
	def test_adjoint_is_not_read_as_a_religious_symbol(self):
		self.assertEqual(
			spoken("<math><msup><mi>A</mi><mo>†</mo></msup></math>"),
			"συζυγής ανάστροφος του άλφα",
		)
		self.assertEqual(
			spoken(
				"<math><msup><mi>A</mi><mo>†</mo></msup></math>",
				terminology_profile="university",
			),
			"προσαρτημένος τελεστής του άλφα",
		)

	def test_quantum_profile_uses_hermitian_adjoint(self):
		self.assertEqual(
			spoken("<math><msup><mi>A</mi><mo>†</mo></msup></math>", domain_hint="quantum_physics"),
			"ερμιτιανός συζυγής του άλφα",
		)

	def test_gradient_divergence_curl_and_laplacian(self):
		cases = {
			"<math><mo>∇</mo><mi>f</mi></math>": "βαθμίδα του εφ",
			"<math><mo>∇</mo><mo>·</mo><mi>F</mi></math>": "απόκλιση του εφ",
			"<math><mo>∇</mo><mo>×</mo><mi>F</mi></math>": "στροβιλισμός του εφ",
			"<math><msup><mo>∇</mo><mn>2</mn></msup><mi>f</mi></math>": "λαπλασιανή του εφ",
		}
		for mathml, expected in cases.items():
			with self.subTest(expected=expected):
				self.assertEqual(spoken(mathml), expected)
		self.assertEqual(
			spoken("<math><mo>∇</mo><mi>f</mi></math>", terminology_profile="school"),
			"κλίση του εφ",
		)

	def test_scalar_multiplication_is_not_guessed_as_dot_product(self):
		self.assertEqual(spoken("<math><mi>a</mi><mo>·</mo><mi>b</mi></math>"), "α επί μπε")

	def test_vector_styling_enables_dot_product(self):
		mathml = '<math><mi mathvariant="bold">a</mi><mo>·</mo><mi mathvariant="bold">b</mi></math>'
		self.assertEqual(spoken(mathml), "εσωτερικό γινόμενο α με μπε")

	def test_cross_and_exterior_products_are_not_conflated(self):
		cross = '<math intent="cross-product($a,$b)"><mi arg="a">a</mi><mi arg="b">b</mi></math>'
		exterior = '<math intent="exterior-product($a,$b)"><mi arg="a">a</mi><mi arg="b">b</mi></math>'
		self.assertEqual(spoken(cross), "διανυσματικό γινόμενο α με μπε")
		self.assertEqual(spoken(exterior), "εξωτερικό γινόμενο α με μπε")


class TestProbabilityAndQuantum(unittest.TestCase):
	def test_expectation_profiles_preserve_meaning(self):
		mathml = "<math><mi>E</mi><mrow><mo>[</mo><mi>X</mi><mo>]</mo></mrow></math>"
		self.assertEqual(spoken(mathml), "αναμενόμενη τιμή του χι")
		self.assertEqual(spoken(mathml, terminology_profile="school"), "μέση τιμή του χι")

	def test_parenthesized_statistics_use_semantic_connectors(self):
		mathml = (
			"<math><mi>Cov</mi><mrow><mo>(</mo><mi>X</mi><mo>,</mo>"
			"<mi>Y</mi><mo>)</mo></mrow></math>"
		)
		self.assertEqual(spoken(mathml), "συνδιακύμανση των χι και ψι")

	def test_conditional_expectation_intent(self):
		mathml = (
			'<math intent="conditional-expectation($x,$y)">'
			'<mi arg="x">X</mi><mo>|</mo><mi arg="y">Y</mi></math>'
		)
		self.assertEqual(spoken(mathml), "δεσμευμένη αναμενόμενη τιμή του χι δεδομένου του ψι")

	def test_independence_symbol(self):
		self.assertEqual(spoken("<math><mi>X</mi><mo>⫫</mo><mi>Y</mi></math>"), "χι ανεξάρτητο από ψι")

	def test_bra_ket_and_matrix_element(self):
		self.assertEqual(
			spoken("<math><mo>⟨</mo><mi>ψ</mi><mo>|</mo><mi>φ</mi><mo>⟩</mo></math>"),
			"εσωτερικό γινόμενο ψι με φι",
		)
		self.assertEqual(
			spoken("<math><mo>⟨</mo><mi>ψ</mi><mo>|</mo><mi>A</mi><mo>|</mo><mi>φ</mi><mo>⟩</mo></math>"),
			"στοιχείο πίνακα με μπρα ψι άλφα κετ φι",
		)
		self.assertEqual(
			spoken(
				"<math><mo>⟨</mo><mi>ψ</mi><mo>|</mo><mi>A</mi><mo>|</mo><mi>φ</mi><mo>⟩</mo></math>",
				terminology_profile="university",
			),
			"στοιχείο μήτρας με μπρα ψι άλφα κετ φι",
		)

	def test_commutator_requires_domain_context(self):
		mathml = "<math><mo>[</mo><mi>A</mi><mo>,</mo><mi>B</mi><mo>]</mo></math>"
		self.assertEqual(spoken(mathml), "αγκύλη άλφα κόμμα βήτα κλείνει η αγκύλη")
		self.assertEqual(
			spoken(mathml, domain_hint="quantum_physics"),
			"μεταθέτης των άλφα και βήτα",
		)


class TestAdvancedAuthorIntent(unittest.TestCase):
	def test_analysis_and_physics_concepts(self):
		cases = {
			"jacobian": "ιακωβιανός πίνακας του εφ",
			"hessian": "εσσιανός πίνακας του εφ",
			"fourier-transform": "μετασχηματισμός Φουριέ του εφ",
			"laplace-transform": "μετασχηματισμός Λαπλάς του εφ",
			"material-derivative": "υλική παράγωγος του εφ",
			"hamiltonian": "χαμιλτονιανός τελεστής ήτα",
			"metric-tensor": "μετρικός τανυστής ζε",
		}
		for intent, expected in cases.items():
			mathml = f'<math intent="{intent}($x)"><mi arg="x">{"H" if intent == "hamiltonian" else "g" if intent == "metric-tensor" else "f"}</mi></math>'
			with self.subTest(intent=intent):
				self.assertEqual(spoken(mathml), expected)

	def test_directional_derivative_keeps_direction_and_operand(self):
		mathml = (
			'<math intent="directional-derivative($f,$v)">'
			'<mi arg="f">f</mi><mi arg="v">v</mi></math>'
		)
		self.assertEqual(spoken(mathml), "παράγωγος κατά την κατεύθυνση βε του εφ")

	def test_evaluated_antiderivative_keeps_expression_and_bounds(self):
		mathml = (
			'<math intent="evaluation($f,$a,$b)">'
			'<mi arg="f">F</mi><mn arg="a">0</mn><mn arg="b">1</mn></math>'
		)
		self.assertEqual(spoken(mathml), "αποτίμηση του εφ από 0 έως 1")

	def test_university_core_intent_vocabulary(self):
		cases = {
			"eigenvalue": "ιδιοτιμή του άλφα",
			"boundary-condition": "συνοριακή συνθήκη άλφα",
			"confidence-interval": "διάστημα εμπιστοσύνης άλφα",
			"stochastic-process": "στοχαστική διαδικασία άλφα",
		}
		for intent, expected in cases.items():
			with self.subTest(intent=intent):
				self.assertEqual(spoken(f'<math intent="{intent}($x)"><mi arg="x">A</mi></math>'), expected)
		self.assertEqual(
			spoken(
				'<math intent="stochastic-process($x)"><mi arg="x">A</mi></math>',
				terminology_profile="university",
			),
			"στοχαστική ανέλιξη άλφα",
		)

	def test_physics_intent_vocabulary(self):
		cases = {
			"angular-momentum": "στροφορμή άλφα",
			"electric-field": "ηλεκτρικό πεδίο άλφα",
			"wavefunction": "κυματοσυνάρτηση άλφα",
			"proper-time": "ιδιοχρόνος άλφα",
		}
		for intent, expected in cases.items():
			with self.subTest(intent=intent):
				self.assertEqual(spoken(f'<math intent="{intent}($x)"><mi arg="x">A</mi></math>'), expected)

	def test_specialist_intents_are_explicit_and_lossless(self):
		cases = {
			"topological-space": "τοπολογικός χώρος άλφα",
			"bounded-operator": "φραγμένος τελεστής άλφα",
			"differential-form": "διαφορική μορφή άλφα",
			"stochastic-integral": "στοχαστικό ολοκλήρωμα του άλφα",
		}
		for intent, expected in cases.items():
			with self.subTest(intent=intent):
				self.assertEqual(spoken(f'<math intent="{intent}($x)"><mi arg="x">A</mi></math>'), expected)

	def test_relation_intent_uses_natural_infix_order(self):
		mathml = (
			'<math intent="asymptotic-equivalence($f,$g)">'
			'<mi arg="f">f</mi><mi arg="g">g</mi></math>'
		)
		self.assertEqual(spoken(mathml), "εφ είναι ασυμπτωτικά ισοδύναμο με ζε")

	def test_preview_modules_cannot_be_mistaken_for_stable(self):
		self.assertEqual(SEMANTIC_MODULES["foundation"]["status"], "stable-existing")
		for module in ("university_core", "physics", "specialist"):
			self.assertEqual(SEMANTIC_MODULES[module]["status"], "preview")


class TestContentMathMLAndRichSpeech(unittest.TestCase):
	def test_semantic_navigation_exposes_operands_not_punctuation(self):
		tree = parse_mathml(
			"<math><mi>E</mi><mrow><mo>[</mo><mi>X</mi><mo>|</mo><mi>Y</mi><mo>]</mo></mrow></math>"
		)
		children = semantic_navigation_children(tree)
		self.assertEqual([child.token_text() for child in children], ["X", "Y"])

	def test_content_mathml_apply(self):
		mathml = "<math><apply><plus/><ci>x</ci><cn>2</cn></apply></math>"
		self.assertEqual(spoken(mathml), "χι συν 2")

	def test_content_mathml_interval(self):
		mathml = '<math><interval closure="open-closed"><cn>0</cn><cn>1</cn></interval></math>'
		self.assertEqual(spoken(mathml), "διάστημα ανοιχτό αριστερά κλειστό δεξιά από 0 έως 1")

	def test_mathml_source_serialization(self):
		tree = parse_mathml("<math><mfrac><mn>1</mn><mi>x</mi></mfrac></math>")
		source = mathnode_to_mathml(tree.children[0])
		self.assertIn("<mfrac>", source)
		self.assertIn('xmlns="http://www.w3.org/1998/Math/MathML"', source)

	def test_rich_speech_contains_language_rate_and_mark(self):
		rich = enrich_speech(["χι"], ReadingConfig(relative_rate=80), mark="node-1")
		self.assertIsInstance(rich[0], Language)
		self.assertTrue(any(isinstance(token, Prosody) and token.relative_rate == 80 for token in rich))
		self.assertTrue(any(isinstance(token, NavigationMark) and token.name == "node-1" for token in rich))

	def test_terminology_records_have_review_metadata(self):
		for concept in TERMS:
			record = terminology_record(concept)
			with self.subTest(concept=concept):
				self.assertEqual(record["conceptId"], concept)
				self.assertIn("grammaticalGender", record)
				self.assertIn("caseForms", record)
				self.assertIn("numberForms", record)
				self.assertIn("pronunciationOverride", record)
				self.assertIn("reviewStatus", record)
				self.assertTrue(record["domain"])
				self.assertTrue(record["source"])

	def test_override_validation_and_use(self):
		accepted, rejected = validate_overrides({"gradient": "διανυσματική κλίση του", "made_up": "λάθος"})
		self.assertEqual(accepted, {"gradient": "διανυσματική κλίση του"})
		self.assertEqual(rejected, ["made_up"])
		mathml = "<math><mo>∇</mo><mi>f</mi></math>"
		self.assertEqual(
			spoken(mathml, terminology_overrides=accepted),
			"διανυσματική κλίση του εφ",
		)

	def test_one_personal_override_can_be_reset(self):
		overrides = {"gradient": "διανυσματική κλίση του", "variance": "διασπορά του"}
		remaining, removed, rejected = reset_override(overrides, "gradient")
		self.assertTrue(removed)
		self.assertEqual(rejected, [])
		self.assertEqual(remaining, {"variance": "διασπορά του"})


if __name__ == "__main__":
	unittest.main()
