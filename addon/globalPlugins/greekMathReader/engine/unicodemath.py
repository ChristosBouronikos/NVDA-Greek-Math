# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Microsoft UnicodeMath front end.

UnicodeMath deliberately resembles linear mathematical notation.  This module
normalizes its distinctive Unicode operators and grouped constructs into the
existing LaTeX front end, which guarantees that all inputs reach the same
``MathNode`` and semantic pipelines.
"""

import re
import unicodedata

from .latex import LatexParseError, latex_to_tree

__all__ = [
	"detect_math_format",
	"UnicodeMathParseError",
	"looks_like_unicodemath",
	"unicodemath_to_latex",
	"unicodemath_to_tree",
]


class UnicodeMathParseError(LatexParseError):
	pass


_COMMANDS = {
	"∑": r"\sum ", "∏": r"\prod ", "∐": r"\coprod ",
	"∫": r"\int ", "∬": r"\iint ", "∭": r"\iiint ", "∮": r"\oint ",
	"∞": r"\infty ", "∂": r"\partial ", "∇": r"\nabla ",
	"→": r"\to ", "↦": r"\mapsto ", "⇒": r"\Rightarrow ", "⇔": r"\Leftrightarrow ",
	"≤": r"\leq ", "≥": r"\geq ", "≠": r"\neq ", "≈": r"\approx ",
	"∈": r"\in ", "∉": r"\notin ", "⊂": r"\subset ", "⊆": r"\subseteq ",
	"∪": r"\cup ", "∩": r"\cap ", "∅": r"\emptyset ",
	"∀": r"\forall ", "∃": r"\exists ", "¬": r"\neg ", "∧": r"\land ", "∨": r"\lor ",
	"⊗": r"\otimes ", "⊕": r"\oplus ", "⊥": r"\perp ", "∥": r"\parallel ",
	"×": r"\times ", "⋅": r"\cdot ", "·": r"\cdot ", "±": r"\pm ",
	"ℏ": r"\hbar ", "ℜ": r"\Re ", "ℑ": r"\Im ", "†": r"\dagger ",
}

_SUPERSCRIPTS = str.maketrans({
	"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
	"⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
	"⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")", "ⁿ": "n",
})
_SUBSCRIPTS = str.maketrans({
	"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
	"₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
	"₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
	"ₐ": "a", "ₑ": "e", "ₕ": "h", "ᵢ": "i", "ⱼ": "j", "ₖ": "k",
	"ₗ": "l", "ₘ": "m", "ₙ": "n", "ₒ": "o", "ₚ": "p", "ᵣ": "r",
	"ₛ": "s", "ₜ": "t", "ᵤ": "u", "ᵥ": "v", "ₓ": "x",
})
_SUPER_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ"
_SUB_CHARS = "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"

_HINT_RE = re.compile(
	r"[√∛∜∑∏∫∬∭∮∞∂∇ℏ≤≥≠∈⊆⊗†■]|"
	rf"[{re.escape(_SUPER_CHARS + _SUB_CHARS)}]|"
	r"[A-Za-zΑ-Ωα-ω0-9)][_^][({A-Za-zΑ-Ωα-ω0-9]"
)


def looks_like_unicodemath(text):
	if not text or "\\" in text:
		return False
	return bool(_HINT_RE.search(text))


def detect_math_format(text):
	"""Return ``latex``, ``unicodemath`` or ``None`` without guessing prose.

	The syntaxes overlap for expressions such as ``x^2``.  Those are called
	LaTeX for compatibility; UnicodeMath is announced only when the input has a
	distinctive Unicode or Word-linear construct.
	"""
	if not text or not text.strip():
		return None
	text = text.strip()
	from .latex import looks_like_latex

	if "\\" in text or text.startswith("$"):
		return "latex" if looks_like_latex(text) else None
	distinctive = re.search(
		r"[√∛∜∑∏∫∬∭∮∞∂∇ℏ≤≥≠∈⊆⊗†‡■]"
		+ rf"|[{re.escape(_SUPER_CHARS + _SUB_CHARS)}]",
		text,
	)
	if distinctive and looks_like_unicodemath(text):
		return "unicodemath"
	return "latex" if looks_like_latex(text) else None


def _balanced_group(source, start):
	opening = source[start]
	closing = {"(": ")", "[": "]", "{": "}"}.get(opening)
	if closing is None:
		return None
	depth = 0
	for index in range(start, len(source)):
		char = source[index]
		if char == opening:
			depth += 1
		elif char == closing:
			depth -= 1
			if depth == 0:
				return source[start + 1:index], index + 1
	return None


def _convert_roots(source):
	out = []
	i = 0
	while i < len(source):
		char = source[i]
		if char not in ("√", "∛", "∜"):
			out.append(char)
			i += 1
			continue
		index = "" if char == "√" else ("3" if char == "∛" else "4")
		j = i + 1
		while j < len(source) and source[j].isspace():
			j += 1
		if j < len(source) and source[j] in "([{":
			group = _balanced_group(source, j)
			if group is not None:
				body, end = group
				out.append(r"\sqrt" + (f"[{index}]" if index else "") + "{" + _convert_roots(body) + "}")
				i = end
				continue
		if j < len(source):
			out.append(r"\sqrt" + (f"[{index}]" if index else "") + "{" + source[j] + "}")
			i = j + 1
			continue
		out.append("root")
		i += 1
	return "".join(out)


def _convert_scripts(source):
	def superscript(match):
		return "^{" + match.group(0).translate(_SUPERSCRIPTS) + "}"

	def subscript(match):
		return "_{" + match.group(0).translate(_SUBSCRIPTS) + "}"

	source = re.sub(f"[{re.escape(_SUPER_CHARS)}]+", superscript, source)
	return re.sub(f"[{re.escape(_SUB_CHARS)}]+", subscript, source)


def _convert_matrices(source):
	"""Convert Word's ``■(a&b@c&d)`` linear matrix notation."""
	out = []
	i = 0
	while i < len(source):
		if source[i] != "■" or i + 1 >= len(source) or source[i + 1] != "(":
			out.append(source[i])
			i += 1
			continue
		group = _balanced_group(source, i + 1)
		if group is None:
			out.append("matrix")
			i += 1
			continue
		body, end = group
		body = body.replace("@", r"\\")
		out.append(r"\begin{pmatrix}" + body + r"\end{pmatrix}")
		i = end
	return "".join(out)


def _convert_grouped_fractions(source):
	# Word commonly linearizes a built-up fraction as ``(a+b)/(c+d)``.  Repeat
	# from the inside out; plain a/b remains a compact spoken division.
	pattern = re.compile(r"\(([^()]*)\)\s*/\s*\(([^()]*)\)")
	previous = None
	while previous != source:
		previous = source
		source = pattern.sub(lambda m: r"\frac{" + m.group(1) + "}{" + m.group(2) + "}", source)
	return source


def _convert_parenthesized_scripts(source):
	"""UnicodeMath uses ``_(...)``/``^(...)`` where TeX uses braces."""
	pattern = re.compile(r"([_^])\(([^()]*)\)")
	previous = None
	while previous != source:
		previous = source
		source = pattern.sub(lambda match: match.group(1) + "{" + match.group(2) + "}", source)
	return source


def _convert_postfix_dagger(source):
	# Dagger is overwhelmingly a postfix adjoint in UnicodeMath.  An author can
	# still request a literal dagger with an explicit \dagger command in LaTeX.
	return re.sub(r"(?<=[A-Za-zΑ-Ωα-ω0-9)\]])[†‡]", lambda match: "^{" + _COMMANDS[match.group(0)].strip() + "}", source)


def _mark_function_names(source):
	r"""Σημείωσε τα ονόματα συναρτήσεων ώστε να μείνουν ενιαία σύμβολα.

	Η γραμμική μορφή γράφει «sin(x)» χωρίς ανάστροφη κάθετο, οπότε ο αναλυτής
	LaTeX το έσπαγε σε τρία γράμματα και εκφωνούνταν «ες ι νι» αντί για
	«ημίτονο». Το \mathrm{} κρατά το όνομα ενιαίο και καλύπτει και την ελληνική
	σχολική γραφή (ημ, συν, εφ), για την οποία δεν υπάρχει εντολή LaTeX.

	Απαιτείται ανοιχτή παρένθεση, ώστε το «5 min» να παραμείνει «λεπτά». Για τα
	ονόματα που είναι ταυτόχρονα και μονάδες χρησιμοποιείται η εντολή LaTeX
	(\min), επειδή το \mathrm{min} θα διαβαζόταν ως μονάδα χρόνου.
	"""
	from .symbols_el import FUNCTION_NAMES, UNITS

	for name in sorted(FUNCTION_NAMES, key=len, reverse=True):
		pattern = re.compile(
			rf"(?<![A-Za-zΑ-Ωα-ω\\]){re.escape(name)}(?=\s*\()"
		)

		def replacement(match, name=name):
			prefix = source[:match.start()].rstrip()
			if prefix and prefix[-1].isdigit():
				return match.group(0)
			if name in UNITS:
				return "\\" + name
			return r"\mathrm{" + name + "}"

		source = pattern.sub(replacement, source)
	return source


def _mark_unambiguous_units(source):
	from .symbols_el import UNITS

	for unit in sorted(UNITS, key=len, reverse=True):
		pattern = re.compile(rf"(?<![A-Za-zΑ-Ωα-ω]){re.escape(unit)}(?![A-Za-zΑ-Ωα-ω])")

		def replacement(match):
			prefix = source[:match.start()].rstrip()
			if not prefix:
				return match.group(0)
			if prefix[-1].isdigit():
				return r"\mathrm{" + match.group(0) + "}"
			if prefix[-1] not in "/·⋅×*⁢":
				return match.group(0)
			# Ο τελεστής από μόνος του δεν κάνει μονάδα το σύμβολο: στο «x/L»
			# ο αριθμητής είναι μεταβλητή, άρα το L είναι «λάμδα» και όχι
			# «λίτρα». Το ίδιο ισχύει για «P/V», «n/N», «y/K». Απαιτείται ο
			# προηγούμενος όρος να είναι και αυτός μονάδα, όπως στο «m/s».
			before = prefix[:-1].rstrip()
			marked = re.search(r"\\mathrm\{([^{}]+)\}$", before)
			if marked is not None:
				return (
					r"\mathrm{" + match.group(0) + "}"
					if marked.group(1) in UNITS
					else match.group(0)
				)
			token = re.search(r"[A-Za-zΑ-Ωα-ω]+$", before)
			if token is not None and token.group(0) in UNITS:
				return r"\mathrm{" + match.group(0) + "}"
			return match.group(0)

		source = pattern.sub(replacement, source)
	return source


def _convert_compound_unit_fractions(source):
	from .symbols_el import UNITS

	units = sorted(UNITS, key=len, reverse=True)
	unit_alt = "(?:" + "|".join(re.escape(unit) for unit in units) + ")"
	factor = unit_alt + r"(?:\^\{[^{}]+\})?"
	expression = factor + r"(?:[·⋅×*]" + factor + r")*"
	pattern = re.compile(
		rf"(?<![A-Za-zΑ-Ωα-ω])({expression})\s*/\s*({expression})(?![A-Za-zΑ-Ωα-ω])"
	)
	unit_re = re.compile(unit_alt)

	def marked(text):
		return unit_re.sub(lambda match: r"\mathrm{" + match.group(0) + "}", text)

	return pattern.sub(lambda match: r"\frac{" + marked(match.group(1)) + "}{" + marked(match.group(2)) + "}", source)


def unicodemath_to_latex(source):
	if source is None or not source.strip():
		raise UnicodeMathParseError("empty UnicodeMath input")
	# Fold only Unicode Mathematical Alphanumeric Symbols.  Whole-string NFKC
	# would destroy meaningful superscript/subscript characters before the
	# script conversion below sees them.
	text = "".join(
		unicodedata.normalize("NFKC", char)
		if "\U0001D400" <= char <= "\U0001D7FF"
		else char
		for char in source.strip()
	)
	text = _convert_matrices(text)
	text = _convert_roots(text)
	text = _convert_scripts(text)
	text = _convert_parenthesized_scripts(text)
	text = _convert_grouped_fractions(text)
	text = _convert_postfix_dagger(text)
	text = _mark_function_names(text)
	text = _convert_compound_unit_fractions(text)
	text = _mark_unambiguous_units(text)
	return "".join(_COMMANDS.get(char, char) for char in text)


def unicodemath_to_tree(source):
	try:
		return latex_to_tree(unicodemath_to_latex(source))
	except LatexParseError as error:
		raise UnicodeMathParseError(str(error)) from error
