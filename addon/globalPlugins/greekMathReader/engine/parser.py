# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# See the file COPYING.txt for more details.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

"""MathML parser: turns MathML markup into a navigable tree of MathNode objects.

This module is pure Python (stdlib only) and must never import NVDA modules,
so that the whole speech engine can be unit-tested outside NVDA.
"""

import re
import unicodedata
from html.entities import html5 as HTML5_ENTITIES
from xml.etree import ElementTree

# Named MathML/HTML entities commonly found in real-world MathML.
# XML parsers only know &amp; &lt; &gt; &quot; &apos;, so the rest are
# replaced with their Unicode characters before parsing.
NAMED_ENTITIES = {
	# Invisible operators
	"ApplyFunction": "⁡", "af": "⁡",
	"InvisibleTimes": "⁢", "it": "⁢",
	"InvisibleComma": "⁣", "ic": "⁣",
	# Common operators and relations
	"PlusMinus": "±", "pm": "±", "plusmn": "±",
	"MinusPlus": "∓", "mp": "∓",
	"times": "×", "divide": "÷", "div": "÷",
	"minus": "−", "cdot": "⋅", "sdot": "⋅",
	"middot": "·", "centerdot": "·",
	"ne": "≠", "NotEqual": "≠",
	"le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
	"ll": "≪", "gg": "≫",
	"approx": "≈", "cong": "≅", "equiv": "≡",
	"prop": "∝", "propto": "∝",
	"sim": "∼", "simeq": "≃",
	"lt": "<", "gt": ">",
	# Arrows
	"rarr": "→", "rightarrow": "→", "RightArrow": "→",
	"larr": "←", "leftarrow": "←",
	"harr": "↔", "uarr": "↑", "darr": "↓",
	"rArr": "⇒", "Implies": "⇒", "DoubleRightArrow": "⇒",
	"lArr": "⇐", "hArr": "⇔", "iff": "⇔",
	"mapsto": "↦", "map": "↦",
	"to": "→",
	# Calculus / analysis
	"int": "∫", "Integral": "∫",
	"sum": "∑", "Sum": "∑", "prod": "∏", "Product": "∏",
	"infin": "∞", "infty": "∞",
	"part": "∂", "PartialD": "∂", "pd": "∂",
	"nabla": "∇", "Del": "∇",
	"prime": "′", "Prime": "″", "tprime": "‴",
	"dd": "ⅆ", "DifferentialD": "ⅆ",
	"ee": "ⅇ", "ExponentialE": "ⅇ",
	"ii": "ⅈ", "ImaginaryI": "ⅈ",
	# Roots and misc
	"radic": "√", "Sqrt": "√",
	"deg": "°", "degree": "°",
	"percnt": "%", "permil": "‰",
	"hellip": "…", "ctdot": "⋯", "dtdot": "⋱", "vellip": "⋮",
	"mldr": "…",
	# Sets and logic
	"isin": "∈", "Element": "∈", "isinv": "∈", "in": "∈",
	"notin": "∉", "NotElement": "∉",
	"ni": "∋", "sub": "⊂", "subset": "⊂",
	"sube": "⊆", "subseteq": "⊆", "subsetneq": "⊊",
	"sup": "⊃", "supset": "⊃", "supe": "⊇", "supseteq": "⊇",
	"cup": "∪", "cap": "∩",
	"empty": "∅", "emptyset": "∅", "emptyv": "∅",
	"setminus": "∖", "ssetmn": "∖",
	"forall": "∀", "ForAll": "∀",
	"exist": "∃", "Exists": "∃", "nexist": "∄",
	"and": "∧", "wedge": "∧", "or": "∨", "vee": "∨",
	"not": "¬",
	# Geometry
	"ang": "∠", "angle": "∠",
	"perp": "⊥", "par": "∥", "parallel": "∥",
	"tri": "△", "triangle": "△",
	# Number sets (double-struck)
	"naturals": "ℕ", "integers": "ℤ", "rationals": "ℚ",
	"reals": "ℝ", "complexes": "ℂ",
	"Ropf": "ℝ", "Zopf": "ℤ", "Nopf": "ℕ", "Qopf": "ℚ", "Copf": "ℂ",
	# Greek letters (lowercase and uppercase)
	"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
	"epsilon": "ε", "epsi": "ε", "varepsilon": "ε",
	"zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
	"iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ",
	"nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π",
	"rho": "ρ", "sigma": "σ", "sigmaf": "ς", "varsigma": "ς",
	"tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "ϕ",
	"chi": "χ", "psi": "ψ", "omega": "ω",
	"Alpha": "Α", "Beta": "Β", "Gamma": "Γ", "Delta": "Δ",
	"Epsilon": "Ε", "Zeta": "Ζ", "Eta": "Η", "Theta": "Θ",
	"Iota": "Ι", "Kappa": "Κ", "Lambda": "Λ", "Mu": "Μ",
	"Nu": "Ν", "Xi": "Ξ", "Omicron": "Ο", "Pi": "Π",
	"Rho": "Ρ", "Sigma": "Σ", "Tau": "Τ", "Upsilon": "Υ",
	"Phi": "Φ", "Chi": "Χ", "Psi": "Ψ", "Omega": "Ω",
	# Spaces and layout
	"nbsp": " ", "ensp": " ", "emsp": " ", "thinsp": " ",
	"ThinSpace": " ", "MediumSpace": " ", "ZeroWidthSpace": "​",
	"NoBreak": "⁠", "shy": "­",
	# Floor / ceiling
	"lfloor": "⌊", "rfloor": "⌋", "lceil": "⌈", "rceil": "⌉",
	# Brackets
	"lang": "⟨", "rang": "⟩", "LeftAngleBracket": "⟨",
	"RightAngleBracket": "⟩",
	"Vert": "‖", "Verbar": "‖",
	"vert": "|", "VerticalBar": "∣", "mid": "∣",
	"lbrace": "{", "rbrace": "}", "lbrack": "[", "rbrack": "]",
	# Misc
	"real": "ℜ", "image": "ℑ", "wp": "℘",
	"aleph": "ℵ", "hbar": "ℏ", "ell": "ℓ",
	"oplus": "⊕", "otimes": "⊗", "ominus": "⊖",
	"circ": "∘", "compfn": "∘", "SmallCircle": "∘",
	"bull": "•", "star": "⋆", "ast": "*",
	"dagger": "†", "Dagger": "‡",
	"there4": "∴", "Therefore": "∴", "because": "∵", "Because": "∵",
	# Additional relations
	"leqslant": "⩽", "geqslant": "⩾",
	"nle": "≰", "nge": "≱", "nlt": "≮", "ngt": "≯",
	"nleq": "≰", "ngeq": "≱", "nless": "≮", "ngtr": "≯",
	"prec": "≺", "succ": "≻", "preceq": "⪯", "succeq": "⪰",
	"nequiv": "≢", "NotCongruent": "≢",
	"asymp": "≍", "doteq": "≐",
	# Additional operators and dots
	"cdots": "⋯", "ldots": "…", "ddots": "⋱", "vdots": "⋮",
	"ominus": "⊖", "odot": "⊙", "oslash": "⊘",
	"bigcup": "⋃", "bigcap": "⋂", "coprod": "∐",
	"boxplus": "⊞", "boxtimes": "⊠",
	# Long arrows and equilibrium
	"longrightarrow": "⟶", "Longrightarrow": "⟹", "Longleftrightarrow": "⟺",
	"rightleftharpoons": "⇌", "Equilibrium": "⇌",
	"uArr": "⇑", "dArr": "⇓",
	# Greek variant letters
	"thetasym": "ϑ", "upsih": "ϒ", "piv": "ϖ",
	"kappav": "ϰ", "rhov": "ϱ", "sigmav2": "ς",
	# Letterlike and misc
	"Re2": "ℜ", "Im2": "ℑ", "micro": "µ", "euro": "€", "pound": "£",
	"comp": "∁", "complement": "∁",
	"measuredangle": "∡", "angmsd": "∡", "sphericalangle": "∢", "angsph": "∢",
	"increment": "∆", "Laplacetrf": "ℒ",
	"planckh": "ℎ", "plankv": "ℏ",
	"frac12": "½", "frac13": "⅓", "frac23": "⅔", "frac14": "¼", "frac34": "¾",
	"half": "½",
	"sup2": "²", "sup3": "³", "sup1": "¹",
	# Brackets and bars (LaTeX-style names emitted by some generators)
	"langle": "⟨", "rangle": "⟩",
	"lVert": "‖", "rVert": "‖", "lvert": "|", "rvert": "|",
	"lbrace": "{", "rbrace": "}",
	# Logic and definition
	"land": "∧", "lor": "∨", "lnot": "¬",
	"implies": "⇒", "impliedby": "⇐", "iff2": "⇔",
	"models": "⊨", "vdash": "⊢", "top": "⊤", "bot": "⊥",
	"coloneq": "≔", "coloneqq": "≔", "Coloneqq": "≔", "eqcolon": "≕",
	"colon": ":",
	# Analysis and letters
	"partial": "∂", "hslash": "ℏ", "varnothing": "∅",
	"varpi": "ϖ", "varkappa": "ϰ", "varrho": "ϱ",
	"digamma": "ϝ",
	"nparallel": "∦", "parallel2": "∥",
	# Multiple integrals and vector operators
	"iint": "∬", "iiint": "∭", "oint": "∮", "oiint": "∯",
	"bigoplus": "⨁", "bigotimes": "⨂",
	# Ordering and approx
	"lesssim": "≲", "gtrsim": "≳", "approxeq": "≈",
	"triangleq": "≜", "eqdef": "≜",
}

_ENTITY_RE = re.compile(r"&(#x?[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);")
_XML_PREDEFINED = {"amp", "lt", "gt", "quot", "apos"}

# Tags that are purely presentational wrappers: treated as transparent rows.
_TRANSPARENT_TAGS = {"mstyle", "mpadded", "menclose_ignore", "mprescripts_ignore"}

# Tags whose content is invisible or irrelevant to speech.
_SKIPPED_TAGS = {"mspace", "mphantom", "maligngroup", "malignmark", "annotation", "annotation-xml"}


class MathMLParseError(Exception):
	"""Raised when MathML markup cannot be parsed."""


class MathNode:
	"""A node in the parsed MathML tree.

	Keeps parent links and child indexes so that the interactive navigation
	mode can walk the tree in every direction.
	"""

	__slots__ = ("tag", "attrib", "text", "children", "parent", "index")

	def __init__(self, tag, attrib=None, text="", parent=None):
		self.tag = tag
		self.attrib = attrib or {}
		self.text = text
		self.children = []
		self.parent = parent
		self.index = 0  # position among siblings

	def append(self, child):
		child.parent = self
		child.index = len(self.children)
		self.children.append(child)

	@property
	def is_token(self):
		return self.tag in ("mi", "mn", "mo", "mtext", "ms")

	@property
	def is_leaf(self):
		return not self.children

	def child(self, i):
		return self.children[i] if 0 <= i < len(self.children) else None

	def next_sibling(self):
		if self.parent is None:
			return None
		return self.parent.child(self.index + 1)

	def previous_sibling(self):
		if self.parent is None:
			return None
		return self.parent.child(self.index - 1)

	def iter(self):
		yield self
		for child in self.children:
			yield from child.iter()

	def token_text(self):
		"""Concatenated text of all token descendants (for pattern matching)."""
		if self.is_token:
			return self.text
		return "".join(child.token_text() for child in self.children)

	def __repr__(self):
		if self.is_token:
			return f"<{self.tag} {self.text!r}>"
		return f"<{self.tag} [{len(self.children)}]>"


def _replace_entities(mathml):
	def repl(match):
		name = match.group(1)
		if name.startswith("#"):
			return match.group(0)  # numeric refs are valid XML, keep them
		if name in _XML_PREDEFINED:
			return match.group(0)
		char = NAMED_ENTITIES.get(name)
		if char is not None:
			return char
		# The project dictionary covers common MathML entities. Fall back to the
		# standard HTML5 entity table so uncommon but valid mathematical symbols
		# keep their meaning instead of being silently removed from the formula.
		# Look up the complete name, including its semicolon. html.unescape is
		# deliberately permissive and could partially decode an invalid name such
		# as ``&notAMathEntity;`` as the valid ``&not;`` prefix.
		return HTML5_ENTITIES.get(f"{name};", match.group(0))
	return _ENTITY_RE.sub(repl, mathml)


_MML_TAG_PREFIX_RE = re.compile(r"<(/?)mml:", re.IGNORECASE)


def _strip_mml_tag_prefix(mathml):
	"""Accept fragments with ``mml:`` tags even when the prefix is unbound."""
	return _MML_TAG_PREFIX_RE.sub(r"<\1", mathml)


def _strip_ns(tag):
	return tag.rsplit("}", 1)[-1].lower()


_WS_RE = re.compile(r"\s+")

# Script/fraktur letterlike symbols folded to their base letter for speech.
# Deliberately NOT folded: ℝ ℤ ℚ ℕ ℂ ℙ (number sets), ℜ ℑ (real/imaginary
# part), ℓ ℏ ℘ ℵ (have their own readings in symbols_el).
_LETTERLIKE_MAP = {
	"ℎ": "h", "ℯ": "e", "ℊ": "g", "ℴ": "o",
	"ℐ": "I", "ℒ": "L", "ℛ": "R", "ℬ": "B",
	"ℰ": "E", "ℱ": "F", "ℳ": "M", "ℋ": "H",
	"ℭ": "C", "ℨ": "Z", "ⅅ": "D",
}


def _normalize_token_char(char):
	"""Fold Unicode math alphanumerics (𝑥, 𝐀, 𝟑, 𝛂…) to their base characters.

	MathML from Word (OMML export) and many generators uses the Mathematical
	Alphanumeric Symbols block (U+1D400–U+1D7FF) for italic/bold letters; NFKC
	maps each to its plain Latin/Greek/digit equivalent. Only this block is
	folded so that letterlike symbols with dedicated readings (ℝ, ℜ, ℓ…) are
	left untouched.
	"""
	if "\U0001D400" <= char <= "\U0001D7FF":
		return unicodedata.normalize("NFKC", char)
	return _LETTERLIKE_MAP.get(char, char)


def _clean_text(text):
	if not text:
		return ""
	text = "".join(_normalize_token_char(c) for c in text)
	return _WS_RE.sub(" ", text).strip()


def _convert(element, parent):
	"""Convert an ElementTree element into MathNode children of `parent`."""
	tag = _strip_ns(element.tag)

	if tag in _SKIPPED_TAGS:
		return

	if tag == "semantics":
		# Prefer the presentation child. Some conversion pipelines put presentation
		# MathML only inside annotation-xml, which must not be discarded.
		for child in element:
			if _strip_ns(child.tag) not in ("annotation", "annotation-xml"):
				_convert(child, parent)
				return
		for child in element:
			if _strip_ns(child.tag) != "annotation-xml":
				continue
			encoding = child.attrib.get("encoding", "").lower()
			if "mathml-presentation" not in encoding and "presentation" not in encoding:
				continue
			for presentation_child in child:
				_convert(presentation_child, parent)
			return
		return

	if tag == "maction":
		# MathML counts maction choices from one. Invalid or absent selections
		# intentionally fall back to the first child, which is the MathML default.
		children = list(element)
		if children:
			try:
				selection = int(element.attrib.get("selection", "1"))
			except ValueError:
				selection = 1
			selected = children[selection - 1] if 1 <= selection <= len(children) else children[0]
			_convert(selected, parent)
		return

	if tag in ("mstyle", "mpadded", "none"):
		if tag == "none":
			node = MathNode("none", dict(element.attrib))
			parent.append(node)
			return
		# Transparent wrappers become mrows so downstream rules see one shape.
		tag = "mrow"

	if tag == "mfenced":
		# Normalize deprecated mfenced into an explicit mrow with mo fences,
		# so that fence handling lives in exactly one place downstream.
		node = MathNode("mrow", {"_from_mfenced": "1"}, parent=parent)
		open_fence = element.attrib.get("open", "(")
		close_fence = element.attrib.get("close", ")")
		# An empty separators attribute deliberately means no separators; when a
		# shorter non-empty list is provided, MathML repeats its last separator.
		separators = element.attrib.get("separators", ",").replace(" ", "")
		if open_fence:
			node.append(MathNode("mo", {"fence": "true"}, open_fence))
		children = list(element)
		for i, child in enumerate(children):
			_convert(child, node)
			if i < len(children) - 1 and separators:
				sep = separators[min(i, len(separators) - 1)]
				node.append(MathNode("mo", {"separator": "true"}, sep))
		if close_fence:
			node.append(MathNode("mo", {"fence": "true"}, close_fence))
		parent.append(node)
		return

	node = MathNode(tag, dict(element.attrib))
	if tag in ("mi", "mn", "mo", "mtext", "ms", "annotation"):
		node.text = _clean_text("".join(element.itertext()))
	else:
		for child in element:
			_convert(child, node)
	parent.append(node)


def _simplify(node):
	"""Collapse redundant wrappers: an mrow with a single child becomes that child.

	This is done bottom-up and keeps parent/index links consistent.
	"""
	new_children = []
	for child in node.children:
		simplified = _simplify(child)
		new_children.append(simplified)
	node.children = []
	for child in new_children:
		node.append(child)
	if node.tag == "mrow" and len(node.children) == 1 and node.parent is not None:
		only = node.children[0]
		return only
	return node


# Fence characters used to build explicit groups out of flat mo sequences.
_OPEN_FENCES = "([{⟨⌊⌈"
_CLOSE_FENCES = ")]}⟩⌋⌉"
_AMBIGUOUS_FENCES = "|‖"
_FENCE_MATCH = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "⌊": "⌋", "⌈": "⌉"}


def _is_fence_mo(node, chars):
	return node.tag == "mo" and node.text in chars


def _group_fences(node):
	"""Wrap fence-delimited ranges of children into explicit mrow groups.

	Browsers often emit flat rows like <mrow><mi>f</mi><mo>(</mo><mi>x</mi>
	<mo>)</mo></mrow>. This pass turns the "( x )" range into a nested mrow
	marked with _fenced, so speech rules and navigation treat parenthesized
	content as one unit. Runs bottom-up; repeats until no more groups form.
	"""
	for child in node.children:
		_group_fences(child)
	if node.tag in ("mtd", "mtr", "mtable"):
		pass  # table cells still benefit; fall through
	changed = True
	while changed:
		changed = False
		# Exact wrap: first child opens, last child closes with the matching fence.
		kids = node.children
		if (
			len(kids) >= 2
			and _is_fence_mo(kids[0], _OPEN_FENCES + _AMBIGUOUS_FENCES)
			and _is_fence_mo(kids[-1], _CLOSE_FENCES + _AMBIGUOUS_FENCES)
			and _fences_match(kids[0].text, kids[-1].text)
			and _is_balanced_between(kids, 1, len(kids) - 1)
		):
			node.attrib["_fenced"] = "1"
			break
		match = _find_fence_range(kids)
		if match:
			start, end = match
			group = MathNode("mrow", {"_fenced": "1"})
			for taken in kids[start:end + 1]:
				group.append(taken)
			node.children[start:end + 1] = [group]
			group.parent = node
			_reindex(node)
			changed = True


def _fences_match(open_char, close_char):
	if open_char in _FENCE_MATCH:
		return _FENCE_MATCH[open_char] == close_char
	if open_char in _AMBIGUOUS_FENCES:
		return open_char == close_char
	return False


def _is_balanced_between(kids, start, end):
	"""True if no unmatched hard fence lies strictly between start and end."""
	depth = 0
	for i in range(start, end):
		child = kids[i]
		if _is_fence_mo(child, _OPEN_FENCES):
			depth += 1
		elif _is_fence_mo(child, _CLOSE_FENCES):
			depth -= 1
			if depth < 0:
				return False
	return depth == 0


def _find_fence_range(kids):
	"""Find the innermost complete fence pair among children; None if none."""
	stack = []
	ambiguous_open = None
	for i, child in enumerate(kids):
		if _is_fence_mo(child, _OPEN_FENCES):
			stack.append((i, child.text))
		elif _is_fence_mo(child, _CLOSE_FENCES):
			if stack and _FENCE_MATCH.get(stack[-1][1]) == child.text:
				start, _ = stack.pop()
				if start == 0 and i == len(kids) - 1:
					return None  # exact wrap is handled by the caller
				return (start, i)
			# Unmatched close fence: ignore.
		elif _is_fence_mo(child, _AMBIGUOUS_FENCES) and not stack:
			if ambiguous_open is None:
				ambiguous_open = (i, child.text)
			elif ambiguous_open[1] == child.text:
				start = ambiguous_open[0]
				if start == 0 and i == len(kids) - 1:
					return None
				return (start, i)
	return None


def parse_mathml(mathml):
	"""Parse a MathML string into a MathNode tree rooted at the <math> element.

	Raises MathMLParseError on malformed input.
	"""
	if not mathml or not mathml.strip():
		raise MathMLParseError("empty MathML input")
	prepared = _strip_mml_tag_prefix(_replace_entities(mathml))
	# Strip anything before the opening <math> tag (some sources prepend XML decls).
	start = prepared.find("<math")
	if start > 0:
		prepared = prepared[start:]
	try:
		root_element = ElementTree.fromstring(prepared)
	except ElementTree.ParseError as error:
		raise MathMLParseError(str(error)) from error
	if _strip_ns(root_element.tag) != "math":
		# Tolerate fragments by wrapping them.
		wrapper = MathNode("math")
		_convert(root_element, wrapper)
		root = wrapper
	else:
		root = MathNode("math", dict(root_element.attrib))
		for child in root_element:
			_convert(child, root)
	# Remove redundant presentation-only wrappers while retaining the ``math``
	# root. The stable root gives interactive navigation one predictable outer
	# level even when a producer wraps its entire expression in a single mrow.
	root = _simplify(root)
	_reindex(root)
	_group_fences(root)
	_reindex(root)
	return root


def _reindex(node):
	for i, child in enumerate(node.children):
		child.parent = node
		child.index = i
		_reindex(child)
