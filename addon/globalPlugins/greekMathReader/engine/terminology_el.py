# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
"""Versioned, reviewable Greek terminology for semantic mathematics.

The legacy symbol tables remain the lossless character-level fallback.  This
registry is keyed by *meaning*, not glyph, so ambiguous notation can be spoken
only after the semantic interpreter has identified a concept.
"""

TERMINOLOGY_VERSION = "2026.08.2"

STANDARD = "standard"
SCHOOL = "school"
UNIVERSITY = "university"
PROFILES = (STANDARD, SCHOOL, UNIVERSITY)


def _entry(standard, school=None, university=None, **metadata):
	forms = {
		STANDARD: standard,
		SCHOOL: school or standard,
		UNIVERSITY: university or standard,
	}
	reviewed = bool(metadata.pop("reviewed", False))
	return {
		"forms": forms,
		"grammaticalGender": metadata.pop("gender", "not-applicable"),
		"caseForms": metadata.pop("case_forms", {}),
		"numberForms": metadata.pop("number_forms", {}),
		"pronunciationOverride": metadata.pop("pronunciation", None),
		"mathcatHead": metadata.pop("mathcat_head", None),
		"localFixity": metadata.pop("local_fixity", "function"),
		"reviewStatus": "reviewed" if reviewed else "source-checked-pending-expert-review",
		"reviewed": reviewed,
		**metadata,
	}


# ``source`` is deliberately a short source family rather than a URL.  The
# terminology review document records the exact edition/page used at sign-off.
TERMS = {
	"power": _entry(
		"δύναμη",
		domain="arithmetic_algebra",
		source="Greek school books",
		reviewed=True,
	),
	"transpose": _entry(
		"ανάστροφος του",
		domain="linear_algebra",
		source="Greek school books / Kallipos",
		reviewed=True,
	),
	"adjoint": _entry(
		"συζυγής ανάστροφος του",
		university="προσαρτημένος τελεστής του",
		domain="linear_algebra",
		source="Kallipos",
		reviewed=False,
	),
	"quantum_adjoint": _entry(
		"ερμιτιανός συζυγής του",
		domain="quantum_physics",
		source="Kallipos",
		reviewed=False,
	),
	"gradient": _entry(
		"βαθμίδα του",
		school="κλίση του",
		domain="vector_calculus",
		source="Kallipos",
		reviewed=False,
	),
	"divergence": _entry(
		"απόκλιση του",
		domain="vector_calculus",
		source="Kallipos",
		reviewed=False,
	),
	"curl": _entry(
		"στροβιλισμός του",
		domain="vector_calculus",
		source="Kallipos",
		reviewed=False,
	),
	"laplacian": _entry(
		"λαπλασιανή του",
		domain="differential_equations",
		source="Kallipos",
		reviewed=False,
	),
	"expectation": _entry(
		"αναμενόμενη τιμή του",
		school="μέση τιμή του",
		domain="probability_statistics",
		source="Greek school books / Kallipos",
		reviewed=False,
	),
	"conditional_expectation": _entry(
		"δεσμευμένη αναμενόμενη τιμή του",
		school="δεσμευμένη μέση τιμή του",
		domain="probability_statistics",
		source="Kallipos",
		reviewed=False,
	),
	"probability": _entry(
		"πιθανότητα του",
		domain="probability_statistics",
		source="Greek school books",
		reviewed=True,
	),
	"variance": _entry(
		"διακύμανση του",
		domain="probability_statistics",
		source="Greek school books / Kallipos",
		reviewed=True,
	),
	"covariance": _entry(
		"συνδιακύμανση των",
		domain="probability_statistics",
		source="Kallipos",
		reviewed=False,
	),
	"standard_deviation": _entry(
		"τυπική απόκλιση του",
		domain="probability_statistics",
		source="Greek school books / Kallipos",
		reviewed=True,
	),
	"braket": _entry(
		"εσωτερικό γινόμενο",
		university="μπρα-κετ",
		domain="quantum_physics",
		source="Kallipos",
		reviewed=False,
	),
	"matrix_element": _entry(
		"στοιχείο πίνακα",
		university="στοιχείο μήτρας",
		domain="quantum_physics",
		source="Kallipos",
		reviewed=False,
	),
	"bra": _entry(
		"μπρα",
		domain="quantum_physics",
		source="Kallipos",
		reviewed=False,
	),
	"ket": _entry(
		"κετ",
		domain="quantum_physics",
		source="Kallipos",
		reviewed=False,
	),
	"commutator": _entry(
		"μεταθέτης των",
		domain="algebra_quantum",
		source="Kallipos",
		reviewed=False,
	),
	"anticommutator": _entry(
		"αντιμεταθέτης των",
		domain="algebra_quantum",
		source="Kallipos",
		reviewed=False,
	),
	"dot_product": _entry(
		"εσωτερικό γινόμενο",
		domain="linear_algebra_physics",
		source="Greek school books / Kallipos",
		reviewed=True,
	),
	"cross_product": _entry(
		"διανυσματικό γινόμενο",
		domain="linear_algebra_physics",
		source="Kallipos",
		reviewed=False,
	),
	"exterior_product": _entry(
		"εξωτερικό γινόμενο",
		domain="multilinear_algebra_differential_geometry",
		source="Kallipos",
		reviewed=False,
	),
	"tensor_product": _entry(
		"τανυστικό γινόμενο",
		domain="multilinear_algebra",
		source="Kallipos",
		reviewed=True,
	),
	"evaluation": _entry(
		"αποτίμηση του",
		domain="calculus",
		source="Kallipos",
		reviewed=False,
	),
	"absolute_value": _entry(
		"απόλυτη τιμή του",
		domain="arithmetic_analysis",
		source="Greek school books",
		reviewed=True,
	),
	"norm": _entry(
		"νόρμα του",
		domain="analysis_linear_algebra",
		source="Kallipos",
		reviewed=True,
	),
	"cardinality": _entry(
		"πληθάριθμος του",
		domain="set_theory",
		source="Greek school books / Kallipos",
		reviewed=True,
	),
	"coordinate": _entry(
		"σημείο με συντεταγμένες",
		domain="geometry",
		source="Greek school books",
		reviewed=True,
	),
	"interval": _entry(
		"διάστημα",
		domain="analysis",
		source="Greek school books",
		reviewed=True,
	),
	"open_interval": _entry(
		"ανοιχτό διάστημα",
		domain="analysis",
		source="Greek school books",
		reviewed=True,
	),
	"closed_interval": _entry(
		"κλειστό διάστημα",
		domain="analysis",
		source="Greek school books",
		reviewed=True,
	),
	"open_closed_interval": _entry(
		"διάστημα ανοιχτό αριστερά κλειστό δεξιά",
		domain="analysis",
		source="Greek school books",
		reviewed=True,
	),
	"closed_open_interval": _entry(
		"διάστημα κλειστό αριστερά ανοιχτό δεξιά",
		domain="analysis",
		source="Greek school books",
		reviewed=True,
	),
	"directional_derivative": _entry(
		"παράγωγος κατά την κατεύθυνση",
		domain="calculus",
		source="Kallipos",
	),
	"ordinary_derivative": _entry(
		"παράγωγος του",
		domain="calculus",
		source="Greek school books / Kallipos",
	),
	"partial_derivative": _entry(
		"μερική παράγωγος του",
		domain="calculus_differential_equations",
		source="Kallipos",
	),
	"material_derivative": _entry(
		"υλική παράγωγος του",
		domain="continuum_mechanics",
		source="Kallipos",
	),
	"line_integral": _entry(
		"επικαμπύλιο ολοκλήρωμα του",
		domain="vector_calculus",
		source="Kallipos",
	),
	"surface_integral": _entry(
		"επιφανειακό ολοκλήρωμα του",
		domain="vector_calculus",
		source="Kallipos",
	),
	"multiple_integral": _entry(
		"πολλαπλό ολοκλήρωμα του",
		domain="multivariable_calculus",
		source="Kallipos",
	),
	"asymptotic_equivalence": _entry(
		"είναι ασυμπτωτικά ισοδύναμο με",
		domain="analysis",
		source="Kallipos",
		local_fixity="infix",
	),
	"jacobian": _entry(
		"ιακωβιανός πίνακας του",
		domain="multivariable_calculus",
		source="Kallipos",
	),
	"hessian": _entry(
		"εσσιανός πίνακας του",
		domain="multivariable_calculus",
		source="Kallipos",
	),
	"fourier_transform": _entry(
		"μετασχηματισμός Φουριέ του",
		domain="analysis_physics",
		source="Kallipos",
	),
	"laplace_transform": _entry(
		"μετασχηματισμός Λαπλάς του",
		domain="analysis_differential_equations",
		source="Kallipos",
	),
	"hamiltonian": _entry(
		"χαμιλτονιανός τελεστής",
		domain="mechanics_quantum",
		source="Kallipos",
	),
	"lagrangian": _entry(
		"λαγκρανζιανή συνάρτηση",
		domain="analytical_mechanics",
		source="Kallipos",
	),
	"four_vector": _entry(
		"τετραδιάνυσμα",
		domain="relativity",
		source="Kallipos",
	),
	"metric_tensor": _entry(
		"μετρικός τανυστής",
		domain="relativity_differential_geometry",
		source="Kallipos",
	),
	"eigenvalue": _entry(
		"ιδιοτιμή του",
		domain="linear_algebra",
		source="Kallipos",
	),
	"eigenvector": _entry(
		"ιδιοδιάνυσμα του",
		domain="linear_algebra",
		source="Kallipos",
	),
	"quadratic_form": _entry(
		"τετραγωνική μορφή του",
		domain="linear_algebra",
		source="Kallipos",
	),
	"identity_matrix": _entry(
		"μοναδιαίος πίνακας τάξης",
		domain="linear_algebra",
		source="Kallipos",
	),
	"diagonal_matrix": _entry(
		"διαγώνιος πίνακας του",
		domain="linear_algebra",
		source="Kallipos",
	),
	"block_matrix": _entry(
		"πίνακας κατά μπλοκ",
		domain="linear_algebra",
		source="Greek academic usage; citation pending",
	),
	"augmented_matrix": _entry(
		"επαυξημένος πίνακας",
		domain="linear_algebra",
		source="Kallipos",
	),
	"boundary_condition": _entry(
		"συνοριακή συνθήκη",
		domain="differential_equations",
		source="Kallipos",
	),
	"initial_condition": _entry(
		"αρχική συνθήκη",
		domain="differential_equations",
		source="Kallipos",
	),
	"confidence_interval": _entry(
		"διάστημα εμπιστοσύνης",
		domain="probability_statistics",
		source="Kallipos",
	),
	"estimator": _entry(
		"εκτιμητής του",
		domain="probability_statistics",
		source="Kallipos",
	),
	"hypothesis_test": _entry(
		"έλεγχος υπόθεσης",
		domain="probability_statistics",
		source="Kallipos",
	),
	"stochastic_process": _entry(
		"στοχαστική διαδικασία",
		university="στοχαστική ανέλιξη",
		domain="probability_statistics",
		source="Kallipos",
	),
	"position_vector": _entry(
		"διάνυσμα θέσης",
		domain="classical_mechanics",
		source="Kallipos",
	),
	"velocity": _entry(
		"ταχύτητα",
		domain="classical_mechanics",
		source="Greek school books / Kallipos",
	),
	"acceleration": _entry(
		"επιτάχυνση",
		domain="classical_mechanics",
		source="Greek school books / Kallipos",
	),
	"momentum": _entry(
		"ορμή",
		domain="classical_mechanics",
		source="Greek school books / Kallipos",
	),
	"angular_momentum": _entry(
		"στροφορμή",
		domain="classical_mechanics_quantum",
		source="Kallipos",
	),
	"torque": _entry(
		"ροπή",
		domain="classical_mechanics",
		source="Greek school books / Kallipos",
	),
	"electric_field": _entry(
		"ηλεκτρικό πεδίο",
		domain="electromagnetism",
		source="Greek school books / Kallipos",
	),
	"magnetic_field": _entry(
		"μαγνητικό πεδίο",
		domain="electromagnetism",
		source="Greek school books / Kallipos",
	),
	"wavefunction": _entry(
		"κυματοσυνάρτηση",
		domain="quantum_physics",
		source="Kallipos",
	),
	"quantum_operator": _entry(
		"κβαντικός τελεστής",
		domain="quantum_physics",
		source="Kallipos",
	),
	"entropy": _entry(
		"εντροπία",
		domain="thermodynamics_statistical_mechanics",
		source="Kallipos",
	),
	"partition_function": _entry(
		"συνάρτηση επιμερισμού",
		domain="statistical_mechanics",
		source="Greek academic usage; citation pending",
	),
	"proper_time": _entry(
		"ιδιοχρόνος",
		domain="relativity",
		source="Kallipos",
	),
	"covariant_index": _entry(
		"συναλλοίωτος δείκτης του",
		domain="relativity_differential_geometry",
		source="Kallipos",
	),
	"contravariant_index": _entry(
		"ανταλλοίωτος δείκτης του",
		domain="relativity_differential_geometry",
		source="Kallipos",
	),
	"four_momentum": _entry(
		"τετραορμή",
		domain="relativity_particle_physics",
		source="Kallipos",
	),
	"group": _entry(
		"ομάδα",
		domain="abstract_algebra",
		source="Greek academic usage; citation pending",
	),
	"ring": _entry(
		"δακτύλιος",
		domain="abstract_algebra",
		source="Greek academic usage; citation pending",
	),
	"field_structure": _entry(
		"σώμα",
		domain="abstract_algebra",
		source="Greek academic usage; citation pending",
	),
	"ideal": _entry(
		"ιδεώδες",
		domain="commutative_algebra",
		source="Greek academic usage; citation pending",
	),
	"topological_space": _entry(
		"τοπολογικός χώρος",
		domain="topology",
		source="Greek academic usage; citation pending",
	),
	"open_set": _entry(
		"ανοιχτό σύνολο",
		domain="topology",
		source="Greek academic usage; citation pending",
	),
	"measure": _entry(
		"μέτρο του",
		domain="measure_theory",
		source="Greek academic usage; citation pending",
	),
	"bounded_operator": _entry(
		"φραγμένος τελεστής",
		domain="functional_analysis",
		source="Greek academic usage; citation pending",
	),
	"manifold": _entry(
		"πολλαπλότητα",
		domain="differential_geometry",
		source="Greek academic usage; citation pending",
	),
	"differential_form": _entry(
		"διαφορική μορφή",
		domain="differential_geometry",
		source="Greek academic usage; citation pending",
	),
	"morphism": _entry(
		"μορφισμός",
		domain="category_theory",
		source="Greek academic usage; citation pending",
	),
	"generalized_function": _entry(
		"γενικευμένη συνάρτηση",
		domain="distribution_theory",
		source="Greek academic usage; citation pending",
	),
	"stochastic_integral": _entry(
		"στοχαστικό ολοκλήρωμα του",
		domain="stochastic_calculus",
		source="Greek academic usage; citation pending",
	),
	"semantic_entailment": _entry(
		"συνεπάγεται σημασιολογικά",
		domain="mathematical_logic",
		source="Greek academic usage; citation pending",
		local_fixity="infix",
	),
	"independence": _entry(
		"ανεξάρτητο από",
		domain="probability_statistics",
		source="Kallipos",
	),
}


# Modules are explicit release units. Dictionary coverage makes a concept
# available only through author intent; it does not make the module stable.
SEMANTIC_MODULES = {
	"foundation": {"status": "stable-existing", "concepts": (
		"power", "absolute_value", "coordinate", "interval", "open_interval",
		"closed_interval", "open_closed_interval", "closed_open_interval",
	)},
	"university_core": {"status": "preview", "concepts": (
		"ordinary_derivative", "partial_derivative", "directional_derivative",
		"material_derivative", "line_integral", "surface_integral", "multiple_integral",
		"asymptotic_equivalence", "jacobian", "hessian", "eigenvalue", "eigenvector",
		"quadratic_form", "identity_matrix", "diagonal_matrix", "block_matrix",
		"augmented_matrix", "boundary_condition", "initial_condition",
		"confidence_interval", "estimator", "hypothesis_test", "stochastic_process",
	)},
	"physics": {"status": "preview", "concepts": (
		"position_vector", "velocity", "acceleration", "momentum", "angular_momentum",
		"torque", "electric_field", "magnetic_field", "wavefunction", "quantum_operator",
		"entropy", "partition_function", "proper_time", "covariant_index",
		"contravariant_index", "four_vector", "four_momentum", "metric_tensor",
	)},
	"specialist": {"status": "preview", "concepts": (
		"group", "ring", "field_structure", "ideal", "topological_space", "open_set",
		"measure", "bounded_operator", "manifold", "differential_form", "morphism",
		"generalized_function", "stochastic_integral", "semantic_entailment",
	)},
}


# MathCAT intent mappings distinguish operator fixity from the words used to
# speak a concept.  All other registry concepts are function-like.  Keeping
# this here makes the upstream rule export use the same semantic vocabulary as
# the local engine instead of growing a second handwritten dictionary.
MATHCAT_INFIX_CONCEPTS = {
	"dot_product",
	"cross_product",
	"exterior_product",
	"tensor_product",
	"independence",
	"asymptotic_equivalence",
	"semantic_entailment",
}


INTENT_ALIASES = {
	"power": "power",
	"transpose": "transpose",
	"adjoint": "adjoint",
	"quantum-adjoint": "quantum_adjoint",
	"conjugate-transpose": "adjoint",
	"expectation": "expectation",
	"expected-value": "expectation",
	"conditional-expectation": "conditional_expectation",
	"probability": "probability",
	"variance": "variance",
	"covariance": "covariance",
	"standard-deviation": "standard_deviation",
	"gradient": "gradient",
	"divergence": "divergence",
	"curl": "curl",
	"laplacian": "laplacian",
	"inner-product": "braket",
	"braket": "braket",
	"matrix-element": "matrix_element",
	"bra": "bra",
	"ket": "ket",
	"commutator": "commutator",
	"anticommutator": "anticommutator",
	"dot-product": "dot_product",
	"cross-product": "cross_product",
	"exterior-product": "exterior_product",
	"wedge-product": "exterior_product",
	"tensor-product": "tensor_product",
	"evaluation": "evaluation",
	"norm": "norm",
	"absolute-value": "absolute_value",
	"cardinality": "cardinality",
	"coordinate": "coordinate",
	"point": "coordinate",
	"interval": "interval",
	"open-interval": "open_interval",
	"closed-interval": "closed_interval",
	"open-closed-interval": "open_closed_interval",
	"closed-open-interval": "closed_open_interval",
	"directional-derivative": "directional_derivative",
	"material-derivative": "material_derivative",
	"jacobian": "jacobian",
	"hessian": "hessian",
	"fourier-transform": "fourier_transform",
	"laplace-transform": "laplace_transform",
	"hamiltonian": "hamiltonian",
	"lagrangian": "lagrangian",
	"four-vector": "four_vector",
	"metric-tensor": "metric_tensor",
	"independence": "independence",
}

# Every canonical concept has a predictable MathML intent spelling. Explicit
# aliases above remain for authoring conventions such as ``expected-value``.
for _concept in TERMS:
	INTENT_ALIASES.setdefault(_concept.replace("_", "-"), _concept)


def normalize_profile(profile):
	return profile if profile in PROFILES else STANDARD


def term(concept, profile=STANDARD, overrides=None):
	"""Return the reviewed spoken head for a semantic concept.

	Overrides are keyed by stable concept id.  Empty/non-string values are
	ignored so a damaged user dictionary cannot make mathematics disappear.
	"""
	if overrides:
		value = overrides.get(concept)
		if isinstance(value, str) and value.strip():
			return value.strip()
	entry = TERMS.get(concept)
	if entry is None:
		return concept.replace("_", " ")
	return entry["forms"][normalize_profile(profile)]


def terminology_record(concept):
	record = TERMS.get(concept)
	return {"conceptId": concept, **record} if record is not None else None


def mathcat_intent_record(concept):
	"""Return a review-labelled MathCAT intent mapping candidate."""
	record = terminology_record(concept)
	if record is None:
		return None
	head = record.get("mathcatHead") or record["forms"][STANDARD]
	for connector in (" του", " των"):
		if head.endswith(connector):
			head = head[:-len(connector)]
			break
	return {
		"name": concept.replace("_", "-"),
		"fixity": "infix" if concept in MATHCAT_INFIX_CONCEPTS else "function",
		"head": head,
		"reviewStatus": record["reviewStatus"],
	}


def validate_overrides(overrides):
	"""Return ``(accepted, rejectedIds)`` for a personal terminology map."""
	if not isinstance(overrides, dict):
		return {}, ["<root>"]
	accepted = {}
	rejected = []
	for concept, value in overrides.items():
		if (
			concept not in TERMS
			or not isinstance(value, str)
			or not value.strip()
			or len(value.strip()) > 160
			or any(ord(char) < 32 for char in value)
		):
			rejected.append(str(concept))
			continue
		accepted[concept] = value.strip()
	return accepted, rejected


def reset_override(overrides, concept):
	"""Return a validated copy without one personal concept override."""
	accepted, rejected = validate_overrides(overrides)
	removed = concept in accepted
	accepted.pop(concept, None)
	return accepted, removed, rejected
