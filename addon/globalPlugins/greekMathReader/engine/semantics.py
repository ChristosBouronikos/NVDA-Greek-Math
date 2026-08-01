# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
"""Semantic interpretation shared by MathML, LaTeX and UnicodeMath.

The interpreter is intentionally conservative.  It recognizes a meaning only
when author intent, a distinctive structure, or strong local context supports
it.  Everything else remains a syntax node and receives the engine's existing
lossless structural reading.
"""

import re

from .parser import MathNode, parse_mathml
from .terminology_el import INTENT_ALIASES, TERMINOLOGY_VERSION


class SemanticNode:
	"""Canonical, input-independent mathematical meaning.

	``arguments`` contain source ``MathNode`` objects for recognized concepts or
	child ``SemanticNode`` objects in a complete interpreted tree.  Keeping the
	source nodes lets the established structural speaker render each operand.
	"""

	__slots__ = ("concept", "arguments", "attributes", "source", "confidence")

	def __init__(self, concept, arguments=(), attributes=None, source=None, confidence="certain"):
		self.concept = concept
		self.arguments = tuple(arguments)
		self.attributes = attributes or {}
		self.source = source
		self.confidence = confidence

	def __repr__(self):
		return f"<SemanticNode {self.concept!r} [{len(self.arguments)}] {self.confidence}>"


class EngineDiagnostics:
	__slots__ = ("unknown", "fallbacks", "recognized", "terminologyVersion")

	def __init__(self):
		self.unknown = []
		self.fallbacks = []
		self.recognized = []
		self.terminologyVersion = TERMINOLOGY_VERSION

	def as_dict(self):
		return {
			"terminologyVersion": self.terminologyVersion,
			"recognized": list(self.recognized),
			"fallbacks": list(self.fallbacks),
			"unknown": list(self.unknown),
		}


_last_diagnostics = EngineDiagnostics()


def reset_engine_diagnostics():
	global _last_diagnostics
	_last_diagnostics = EngineDiagnostics()
	return _last_diagnostics


def get_last_engine_diagnostics():
	return _last_diagnostics.as_dict()


def record_unknown(value, role="symbol"):
	item = f"{role}:{value}"
	if item not in _last_diagnostics.unknown:
		_last_diagnostics.unknown.append(item)


def record_fallback(value):
	if value not in _last_diagnostics.fallbacks:
		_last_diagnostics.fallbacks.append(value)


_INTENT_APPLICATION_RE = re.compile(
	r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*(?::[A-Za-z][A-Za-z0-9_-]*\s*)*"
	r"(?:\((.*)\))?\s*$",
	re.DOTALL,
)
_INTENT_REFERENCE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_.-]*)")


def _descendant_with_arg(node, name):
	for descendant in node.iter():
		if descendant is not node and descendant.attrib.get("arg") == name:
			return descendant
	return None


def _intent_semantic(node):
	intent = node.attrib.get("intent", "")
	if not intent or intent.lstrip().startswith(":"):
		return None
	match = _INTENT_APPLICATION_RE.match(intent)
	if not match:
		record_fallback(f"invalid-intent:{intent}")
		return None
	name = match.group(1).replace("_", "-").replace(".", "-").lower()
	concept = INTENT_ALIASES.get(name)
	if concept is None:
		record_fallback(f"unsupported-intent:{name}")
		return None
	arguments = []
	for reference in _INTENT_REFERENCE_RE.findall(match.group(2) or ""):
		target = _descendant_with_arg(node, reference)
		if target is None:
			record_fallback(f"missing-intent-argument:{reference}")
			return None
		arguments.append(target)
	if not arguments:
		arguments = list(node.children)
	if concept in ("braket", "matrix_element") and len(arguments) == 1:
		target = arguments[0]
		parts = _split(target.children, ("|", "∣")) if target.tag == "mrow" else []
		if len(parts) in (2, 3) and all(parts):
			arguments = [_wrap(part) for part in parts]
	return SemanticNode(
		concept,
		arguments,
		{"intent": intent},
		node,
		confidence="author",
	)


def _fence_parts(node):
	if node.tag not in ("math", "mrow") or len(node.children) < 2:
		return None
	first, last = node.children[0], node.children[-1]
	if first.tag != "mo" or last.tag != "mo":
		return None
	pairs = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "|": "|", "‖": "‖"}
	if pairs.get(first.text) != last.text:
		return None
	return first.text, last.text, node.children[1:-1]


def _split(nodes, separators):
	parts = [[]]
	for child in nodes:
		if child.tag == "mo" and child.text in separators:
			parts.append([])
		else:
			parts[-1].append(child)
	return parts


def _wrap(nodes):
	if len(nodes) == 1:
		return nodes[0]
	row = MathNode("mrow")
	for child in nodes:
		row.append(_clone_math_node(child))
	return row


def _clone_math_node(node):
	copy = MathNode(node.tag, dict(node.attrib), node.text)
	for child in node.children:
		copy.append(_clone_math_node(child))
	return copy


def _is_vector(node):
	if node is None:
		return False
	if node.tag == "mover":
		over = node.child(1)
		return over is not None and over.token_text().strip() in ("→", "⃗", "⇀")
	return node.attrib.get("mathvariant") in ("bold", "bold-italic")


def _domain(config):
	return getattr(config, "domain_hint", "auto") if config is not None else "auto"


def _operator_sequence(node, config):
	if node.tag not in ("math", "mrow"):
		return None
	kids = node.children
	if len(kids) < 2:
		return None

	# ∇f, ∇·F, ∇×F and ∇²f have distinctive operator syntax.
	first = kids[0]
	if first.tag == "mo" and first.text == "∇":
		if len(kids) >= 3 and kids[1].tag == "mo" and kids[1].text in ("·", "⋅", "∙"):
			return SemanticNode("divergence", [_wrap(kids[2:])], source=node)
		if len(kids) >= 3 and kids[1].tag == "mo" and kids[1].text in ("×", "⨯"):
			return SemanticNode("curl", [_wrap(kids[2:])], source=node)
		return SemanticNode("gradient", [_wrap(kids[1:])], source=node)
	if first.tag == "msup":
		base, exponent = first.child(0), first.child(1)
		if base is not None and base.tag == "mo" and base.text == "∇" and exponent is not None and exponent.token_text() == "2":
			return SemanticNode("laplacian", [_wrap(kids[1:])], source=node)

	# E[X], P(A), Var(X), Cov(X,Y). Treat both conventional fence styles as
	# the same function semantics so connectors and multiple arguments agree.
	if len(kids) == 2 and first.tag == "mi":
		fence = _fence_parts(kids[1])
		if fence is not None and (
			fence[0] == "["
			or (fence[0] == "(" and first.text not in ("E", "ℰ", "𝔼"))
		):
			inner = fence[2]
			function_concepts = {
				"E": "expectation", "ℰ": "expectation", "𝔼": "expectation",
				"P": "probability", "Pr": "probability",
				"Var": "variance", "var": "variance",
				"Cov": "covariance", "cov": "covariance",
				"SD": "standard_deviation", "Std": "standard_deviation",
			}
			concept = function_concepts.get(first.text)
			if concept:
				parts = _split(inner, (",", "|", "∣"))
				return SemanticNode(concept, [_wrap(part) for part in parts if part], source=node)

	# Dot/cross products are semantic only when vector styling or a physics
	# context makes the meaning stronger than ordinary multiplication.
	if len(kids) == 3 and kids[1].tag == "mo":
		operator = kids[1].text
		if operator == "⫫":
			return SemanticNode("independence", [kids[0], kids[2]], source=node)
		vector_context = _is_vector(kids[0]) or _is_vector(kids[2]) or _domain(config) in (
			"physics", "quantum_physics", "vector_calculus",
		)
		if vector_context and operator in ("·", "⋅", "∙"):
			return SemanticNode("dot_product", [kids[0], kids[2]], source=node)
		if vector_context and operator in ("×", "⨯"):
			return SemanticNode("cross_product", [kids[0], kids[2]], source=node)
	return None


def _fenced_semantic(node, config):
	fence = _fence_parts(node)
	if fence is None:
		return None
	open_char, _close_char, inner = fence
	if open_char == "⟨":
		parts = _split(inner, ("|", "∣"))
		if len(parts) == 2 and all(parts):
			return SemanticNode("braket", [_wrap(part) for part in parts], source=node)
		if len(parts) == 3 and all(parts):
			return SemanticNode("matrix_element", [_wrap(part) for part in parts], source=node)
	if open_char == "[" and _domain(config) in ("quantum_physics", "algebra"):
		parts = _split(inner, (",",))
		if len(parts) == 2 and all(parts):
			return SemanticNode("commutator", [_wrap(part) for part in parts], source=node, confidence="context")
	if open_char == "{" and _domain(config) == "quantum_physics":
		parts = _split(inner, (",",))
		if len(parts) == 2 and all(parts):
			return SemanticNode("anticommutator", [_wrap(part) for part in parts], source=node, confidence="context")
	return None


def recognize_semantic(node, config=None):
	"""Return a recognized semantic concept for ``node``, or ``None``."""
	intent = _intent_semantic(node)
	if intent is not None:
		_last_diagnostics.recognized.append(f"{intent.concept}:author")
		return intent

	if node.tag == "msup":
		base, exponent = node.child(0), node.child(1)
		if exponent is not None and exponent.token_text().strip() in ("†", "‡"):
			concept = "quantum_adjoint" if _domain(config) == "quantum_physics" else "adjoint"
			semantic = SemanticNode(concept, [base] if base is not None else [], source=node)
			_last_diagnostics.recognized.append(f"{concept}:structure")
			return semantic

	semantic = _operator_sequence(node, config) or _fenced_semantic(node, config)
	if semantic is not None:
		_last_diagnostics.recognized.append(f"{semantic.concept}:{semantic.confidence}")
	return semantic


def semantic_navigation_children(node, config=None):
	"""Return semantic operands when known, otherwise the syntax children."""
	semantic = recognize_semantic(node, config)
	if semantic is None:
		return list(node.children)
	arguments = [argument for argument in semantic.arguments if isinstance(argument, MathNode)]
	return arguments or list(node.children)


def interpret_node(node, config=None):
	"""Build a complete canonical tree while preserving unknown syntax nodes."""
	recognized = recognize_semantic(node, config)
	if recognized is not None:
		return recognized
	return SemanticNode(
		f"syntax:{node.tag}",
		[interpret_node(child, config) for child in node.children],
		{"text": node.text, **dict(node.attrib)},
		node,
		confidence="structural",
	)


def interpret_mathml(mathml, config=None):
	reset_engine_diagnostics()
	return interpret_node(parse_mathml(mathml), config)


def interpret_latex(latex, config=None):
	from .latex import latex_to_tree

	reset_engine_diagnostics()
	return interpret_node(latex_to_tree(latex), config)


def interpret_unicodemath(source, config=None):
	from .unicodemath import unicodemath_to_tree

	reset_engine_diagnostics()
	return interpret_node(unicodemath_to_tree(source), config)
