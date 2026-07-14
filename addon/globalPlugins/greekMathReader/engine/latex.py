# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# SPDX-License-Identifier: GPL-2.0-only
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

"""LaTeX math → MathNode tree, for reading LaTeX aloud in Greek.

Pure Python (no NVDA imports). The output is the *same* MathNode tree that
``parser.parse_mathml`` produces, so the existing Greek speech rules in
``speech.py`` and the navigation in ``interaction.py`` work unchanged — this
module is only a second front end that reaches the same tree.

Scope is the common math subset students meet: fractions, roots, super/sub
scripts, big operators with bounds, Greek letters, named functions, delimiters,
matrices, accents (vec/hat/bar/dot), binomials and the usual relations and
operators. Unknown commands degrade gracefully: they are spoken by their name
(without the backslash) rather than dropped, so nothing is silently lost.
"""

import re

from .parser import MathNode, _group_fences, _reindex, _simplify

__all__ = ["latex_to_tree", "LatexParseError", "looks_like_latex", "strip_math_delimiters"]


class LatexParseError(Exception):
	"""Raised when a LaTeX string cannot be turned into a tree."""


# ---------------------------------------------------------------------------
# Command → Unicode tables (kept as data so terminology review stays easy).
# ---------------------------------------------------------------------------

_GREEK = {
	"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
	"varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
	"iota": "ι", "kappa": "κ", "varkappa": "ϰ", "lambda": "λ", "mu": "μ",
	"nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π", "varpi": "ϖ",
	"rho": "ρ", "varrho": "ϱ", "sigma": "σ", "varsigma": "ς", "tau": "τ",
	"upsilon": "υ", "phi": "φ", "varphi": "ϕ", "chi": "χ", "psi": "ψ", "omega": "ω",
	"Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
	"Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}

# Symbols that become a single <mo> (or <mi> for letterlike) operator token.
_SYMBOLS = {
	"times": "×", "cdot": "⋅", "div": "÷", "pm": "±", "mp": "∓",
	"ast": "*", "star": "⋆", "circ": "∘", "bullet": "•",
	"leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠",
	"ll": "≪", "gg": "≫", "approx": "≈", "cong": "≅", "equiv": "≡",
	"sim": "∼", "simeq": "≃", "propto": "∝", "asymp": "≍", "doteq": "≐",
	"prec": "≺", "succ": "≻", "preceq": "⪯", "succeq": "⪰",
	"lesssim": "≲", "gtrsim": "≳",
	"to": "→", "rightarrow": "→", "leftarrow": "←", "leftrightarrow": "↔",
	"Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔", "iff": "⇔",
	"implies": "⇒", "mapsto": "↦", "longrightarrow": "⟶",
	"rightleftharpoons": "⇌",
	"in": "∈", "notin": "∉", "ni": "∋",
	"subset": "⊂", "subseteq": "⊆", "subsetneq": "⊊",
	"supset": "⊃", "supseteq": "⊇",
	"cup": "∪", "cap": "∩", "setminus": "∖",
	"emptyset": "∅", "varnothing": "∅",
	"forall": "∀", "exists": "∃", "nexists": "∄",
	"land": "∧", "wedge": "∧", "lor": "∨", "vee": "∨", "neg": "¬", "lnot": "¬",
	"oplus": "⊕", "otimes": "⊗", "ominus": "⊖", "odot": "⊙",
	"infty": "∞", "partial": "∂", "nabla": "∇",
	"angle": "∠", "perp": "⊥", "parallel": "∥", "triangle": "△",
	"cdots": "⋯", "ldots": "…", "dots": "…", "vdots": "⋮", "ddots": "⋱",
	"therefore": "∴", "because": "∵",
	"mid": "∣", "nmid": "∤",
	"Re": "ℜ", "Im": "ℑ", "aleph": "ℵ", "hbar": "ℏ", "ell": "ℓ",
	"degree": "°", "prime": "′",
	"coloneqq": "≔", "coloneq": "≔", "triangleq": "≜",
}

_NUMBER_SETS = {
	"mathbb{R}": "ℝ", "mathbb{Z}": "ℤ", "mathbb{Q}": "ℚ",
	"mathbb{N}": "ℕ", "mathbb{C}": "ℂ", "mathbb{P}": "ℙ",
	"R": "ℝ", "Z": "ℤ", "Q": "ℚ", "N": "ℕ", "C": "ℂ",
}

# Functions rendered upright; become an <mi> whose text triggers speech naming.
_FUNCTIONS = {
	"sin", "cos", "tan", "cot", "sec", "csc",
	"arcsin", "arccos", "arctan",
	"sinh", "cosh", "tanh", "coth",
	"log", "ln", "lg", "exp",
	"lim", "limsup", "liminf", "max", "min", "sup", "inf", "arg",
	"det", "dim", "ker", "gcd", "lcm", "rank", "tr", "deg", "hom",
	"Pr", "Var", "Cov", "Re", "Im",
}

_BIG_OPERATORS = {
	"sum": "∑", "prod": "∏", "coprod": "∐",
	"int": "∫", "iint": "∬", "iiint": "∭", "oint": "∮",
	"bigcup": "⋃", "bigcap": "⋂", "bigoplus": "⨁", "bigotimes": "⨂",
}

_ACCENTS = {
	"vec": "→", "hat": "^", "bar": "¯", "overline": "¯",
	"dot": "˙", "ddot": "¨", "tilde": "~", "widehat": "^", "widetilde": "~",
}

_OPEN_DELIMS = {"(": "(", "[": "[", "\\{": "{", "\\langle": "⟨", "\\lfloor": "⌊", "\\lceil": "⌈", "|": "|", "\\|": "‖", "\\lvert": "|", "\\lVert": "‖"}
_CLOSE_DELIMS = {")": ")", "]": "]", "\\}": "}", "\\rangle": "⟩", "\\rfloor": "⌋", "\\rceil": "⌉", "|": "|", "\\|": "‖", "\\rvert": "|", "\\rVert": "‖"}

_MATRIX_FENCES = {
	"pmatrix": ("(", ")"), "bmatrix": ("[", "]"), "Bmatrix": ("{", "}"),
	"vmatrix": ("|", "|"), "Vmatrix": ("‖", "‖"), "matrix": ("", ""),
}


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
	r"""
	  (?P<rowbreak>\\\\)               # \\ row separator (must precede command)
	| (?P<command>\\[A-Za-z]+\*?)      # \frac, \alpha, \left …
	| (?P<escaped>\\[^A-Za-z])         # \{ \} \| \, \; \  (escaped char)
	| (?P<number>[0-9]+(?:\.[0-9]+)?)  # 3, 3.14
	| (?P<space>\s+)
	| (?P<char>.)                      # any single character
	""",
	re.VERBOSE | re.DOTALL,
)


def _tokenize(source):
	tokens = []
	for match in _TOKEN_RE.finditer(source):
		kind = match.lastgroup
		value = match.group()
		if kind == "space":
			continue
		tokens.append((kind, value))
	return tokens


# ---------------------------------------------------------------------------
# Parser: recursive descent over the token stream.
# ---------------------------------------------------------------------------


class _Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		self.pos = 0

	# -- token helpers -------------------------------------------------

	def _peek(self):
		return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

	def _next(self):
		token = self._peek()
		self.pos += 1
		return token

	def _at_end(self):
		return self.pos >= len(self.tokens)

	# -- entry point ---------------------------------------------------

	def parse(self):
		children = self._parse_sequence(stop_chars=set())
		root = MathNode("math")
		for child in children:
			root.append(child)
		return root

	# -- sequences and scripts ----------------------------------------

	def _parse_sequence(self, stop_chars, stop_commands=frozenset()):
		"""Parse atoms until a stop char/command (consumed by the caller)."""
		out = []
		while not self._at_end():
			kind, value = self._peek()
			if kind == "char" and value in stop_chars:
				break
			if kind == "command" and value[1:] in stop_commands:
				break
			if kind == "char" and value == "&":
				break  # handled by matrix/row parser
			if kind == "rowbreak":
				break
			atom = self._parse_atom()
			if atom is None:
				break
			atom = self._attach_scripts(atom)
			out.append(atom)
		return out

	def _attach_scripts(self, base):
		"""Fold trailing ^{…} and _{…} into msup / msub / msubsup."""
		sub = None
		sup = None
		while True:
			kind, value = self._peek()
			if kind == "char" and value == "^" and sup is None:
				self._next()
				sup = self._parse_group_or_atom()
			elif kind == "char" and value == "_" and sub is None:
				self._next()
				sub = self._parse_group_or_atom()
			else:
				break
		# Limit-style operators put their bounds *under/over*, not as scripts, so
		# that the Greek "όριο καθώς το … τείνει στο …" rule in speech.py fires.
		under_over = base.tag == "mi" and base.text in ("lim", "limsup", "liminf")
		if sub is not None and sup is not None:
			node = MathNode("munderover" if under_over else "msubsup")
			node.append(base)
			node.append(sub)
			node.append(sup)
			return node
		if sub is not None:
			node = MathNode("munder" if under_over else "msub")
			node.append(base)
			node.append(sub)
			return node
		if sup is not None:
			node = MathNode("msup")
			node.append(base)
			node.append(sup)
			return node
		return base

	def _parse_group_or_atom(self):
		"""A braced group {…} or a single atom (for scripts, \\frac args …)."""
		kind, value = self._peek()
		if kind == "char" and value == "{":
			self._next()
			children = self._parse_sequence(stop_chars={"}"})
			self._expect_char("}")
			return _wrap(children)
		atom = self._parse_atom()
		if atom is None:
			return MathNode("mrow")
		return self._attach_scripts_shallow(atom)

	def _attach_scripts_shallow(self, atom):
		# A single script argument like x^2^3 is unusual; keep it simple.
		return atom

	def _expect_char(self, char):
		kind, value = self._peek()
		if kind == "char" and value == char:
			self._next()
			return
		# Tolerate missing close brace rather than failing the whole read.

	# -- atoms ---------------------------------------------------------

	def _parse_atom(self):
		kind, value = self._next()
		if kind is None:
			return None
		if kind == "number":
			return MathNode("mn", text=value)
		if kind == "command":
			return self._parse_command(value[1:], value)
		if kind == "escaped":
			return self._parse_escaped(value)
		if kind == "char":
			return self._parse_char(value)
		return None

	def _parse_char(self, ch):
		if ch == "{":
			children = self._parse_sequence(stop_chars={"}"})
			self._expect_char("}")
			return _wrap(children)
		if ch in "+-*/=<>":
			return MathNode("mo", text=_CHAR_OPERATORS.get(ch, ch))
		if ch in ",;.":
			return MathNode("mo", text=ch)
		if ch in "()[]|":
			return MathNode("mo", text=ch)
		if ch == "'":
			return MathNode("mo", text="′")
		if ch == "!":
			return MathNode("mo", text="!")
		if ch.isalpha():
			return MathNode("mi", text=ch)
		if ch.isspace():
			return MathNode("mrow")
		return MathNode("mo", text=ch)

	def _parse_escaped(self, value):
		ch = value[1]
		if ch in "{}":
			return MathNode("mo", text=ch)
		if ch == "|":
			return MathNode("mo", text="‖")
		if ch in " ,;!":
			return MathNode("mrow")  # spacing commands: no speech
		return MathNode("mo", text=ch)

	# -- commands ------------------------------------------------------

	def _parse_command(self, name, raw):
		if name in _GREEK:
			return MathNode("mi", text=_GREEK[name])
		if name in _NUMBER_SETS:
			return MathNode("mi", text=_NUMBER_SETS[name])
		if name in _SYMBOLS:
			return MathNode("mo", text=_SYMBOLS[name])
		if name in _FUNCTIONS:
			return MathNode("mi", text=name)
		if name in _BIG_OPERATORS:
			return MathNode("mo", text=_BIG_OPERATORS[name])
		if name in _ACCENTS:
			return self._parse_accent(name)
		if name == "frac" or name == "dfrac" or name == "tfrac":
			return self._parse_frac()
		if name == "binom" or name == "dbinom":
			return self._parse_binom()
		if name == "sqrt":
			return self._parse_sqrt()
		if name == "left":
			return self._parse_delimited()
		if name == "right":
			# A stray \right with no matching \left: skip its delimiter.
			self._next()
			return MathNode("mrow")
		if name == "operatorname":
			arg = self._parse_group_or_atom()
			return MathNode("mi", text=arg.token_text())
		if name in ("mathbb", "mathbf", "mathrm", "mathcal", "mathit", "text", "mathsf", "boldsymbol"):
			return self._parse_font(name)
		if name == "begin":
			return self._parse_environment()
		if name in ("cdot", "cdots"):
			return MathNode("mo", text=_SYMBOLS.get(name, "⋅"))
		if name in ("quad", "qquad", ",", ";", "!", " "):
			return MathNode("mrow")  # spacing
		# Unknown command: speak its name verbatim (mtext avoids the letter-by-
		# letter reading that mi applies to multi-letter identifiers).
		return MathNode("mtext", text=name)

	def _parse_font(self, name):
		arg = self._parse_group_or_atom()
		if name == "mathbb":
			text = arg.token_text()
			if text in _NUMBER_SETS:
				return MathNode("mi", text=_NUMBER_SETS[text])
		if name == "text":
			return MathNode("mtext", text=arg.token_text())
		if name == "mathrm":
			for node in arg.iter():
				if node.tag == "mi":
					node.attrib["mathvariant"] = "normal"
		# For other fonts, keep the content as-is (styling is irrelevant to speech).
		return arg

	def _parse_accent(self, name):
		arg = self._parse_group_or_atom()
		node = MathNode("mover")
		node.append(arg)
		node.append(MathNode("mo", text=_ACCENTS[name]))
		return node

	def _parse_frac(self):
		numerator = self._parse_group_or_atom()
		denominator = self._parse_group_or_atom()
		node = MathNode("mfrac")
		node.append(numerator)
		node.append(denominator)
		return node

	def _parse_binom(self):
		top = self._parse_group_or_atom()
		bottom = self._parse_group_or_atom()
		frac = MathNode("mfrac", {"linethickness": "0"})
		frac.append(top)
		frac.append(bottom)
		row = MathNode("mrow")
		row.append(MathNode("mo", text="("))
		row.append(frac)
		row.append(MathNode("mo", text=")"))
		return row

	def _parse_sqrt(self):
		# Optional index: \sqrt[3]{x}
		kind, value = self._peek()
		index = None
		if kind == "char" and value == "[":
			self._next()
			index_children = self._parse_sequence(stop_chars={"]"})
			self._expect_char("]")
			index = _wrap(index_children)
		radicand = self._parse_group_or_atom()
		if index is not None:
			node = MathNode("mroot")
			node.append(radicand)
			node.append(index)
			return node
		node = MathNode("msqrt")
		if radicand.tag == "mrow":
			for child in list(radicand.children):
				node.append(child)
		else:
			node.append(radicand)
		return node

	def _parse_delimited(self):
		open_delim = self._read_delimiter()
		inner = self._parse_sequence(stop_chars=set(), stop_commands={"right"})
		# consume the \right
		kind, value = self._peek()
		close_delim = ")"
		if kind == "command" and value == "\\right":
			self._next()
			close_delim = self._read_delimiter(closing=True)
		row = MathNode("mrow")
		if open_delim:
			row.append(MathNode("mo", text=open_delim))
		for child in inner:
			row.append(child)
		if close_delim:
			row.append(MathNode("mo", text=close_delim))
		return row

	def _read_delimiter(self, closing=False):
		kind, value = self._next()
		if kind is None:
			return ")" if closing else "("
		if kind == "command":
			table = _CLOSE_DELIMS if closing else _OPEN_DELIMS
			return table.get(value, "")
		if value == ".":
			return ""  # \left. and \right. are invisible delimiters
		table = _CLOSE_DELIMS if closing else _OPEN_DELIMS
		return table.get(value, value)

	def _parse_environment(self):
		name_group = self._parse_group_or_atom()
		env = name_group.token_text().strip("*")
		if env in _MATRIX_FENCES or env in ("array", "cases", "aligned", "align", "align*"):
			return self._parse_matrix(env)
		# Unknown environment: read its body, stop at \end.
		body = self._parse_sequence(stop_chars=set(), stop_commands={"end"})
		self._consume_end()
		return _wrap(body)

	def _parse_matrix(self, env):
		rows = self._parse_rows()
		self._consume_end()
		table = MathNode("mtable")
		for row_cells in rows:
			tr = MathNode("mtr")
			for cell in row_cells:
				td = MathNode("mtd")
				for child in cell:
					td.append(child)
				tr.append(td)
			table.append(tr)
		if env in ("cases",):
			row = MathNode("mrow")
			row.append(MathNode("mo", text="{"))
			row.append(table)
			return row
		fences = _MATRIX_FENCES.get(env)
		if fences and fences[0]:
			row = MathNode("mrow")
			row.append(MathNode("mo", text=fences[0]))
			row.append(table)
			row.append(MathNode("mo", text=fences[1]))
			return row
		return table

	def _parse_rows(self):
		rows = []
		cells = [[]]
		while not self._at_end():
			kind, value = self._peek()
			if kind == "command" and value == "\\end":
				break
			if kind == "command" and value[1:] == "end":
				break
			if kind == "char" and value == "&":
				self._next()
				cells.append([])
				continue
			if kind == "rowbreak":
				self._next()
				rows.append(cells)
				cells = [[]]
				continue
			atom = self._parse_atom()
			if atom is None:
				break
			atom = self._attach_scripts(atom)
			cells[-1].append(atom)
		if any(cell for cell in cells):
			rows.append(cells)
		return rows

	def _consume_end(self):
		kind, value = self._peek()
		if kind == "command" and value == "\\end":
			self._next()
			self._parse_group_or_atom()  # discard environment name


_CHAR_OPERATORS = {"*": "⋅"}


def _wrap(children):
	"""Wrap a list of nodes: single child returns bare, else an mrow."""
	if len(children) == 1:
		return children[0]
	node = MathNode("mrow")
	for child in children:
		node.append(child)
	return node


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_MATH_DELIMITERS = (
	(r"\[", r"\]"),
	(r"\(", r"\)"),
	("$$", "$$"),
	("$", "$"),
)


def strip_math_delimiters(text):
	"""Remove surrounding $…$, $$…$$, \\(…\\) or \\[…\\] if present."""
	stripped = text.strip()
	for open_delim, close_delim in _MATH_DELIMITERS:
		if stripped.startswith(open_delim) and stripped.endswith(close_delim) and len(stripped) > len(open_delim) + len(close_delim) - 1:
			return stripped[len(open_delim):len(stripped) - len(close_delim)].strip()
	return stripped


_LATEX_HINT_RE = re.compile(
	r"\\[A-Za-z]+|[\^_]|\\[\[\(]|\$|"
	r"[A-Za-zΑ-Ωα-ω0-9]\s*[+\-*/=<>]\s*[A-Za-zΑ-Ωα-ω0-9]"
)


def looks_like_latex(text):
	"""Heuristic: does this string look like LaTeX math rather than plain text?"""
	if not text:
		return False
	return bool(_LATEX_HINT_RE.search(text))


def latex_to_tree(source):
	"""Parse a LaTeX math string into a MathNode tree rooted at <math>.

	Raises LatexParseError on empty input.
	"""
	if source is None or not source.strip():
		raise LatexParseError("empty LaTeX input")
	body = strip_math_delimiters(source)
	tokens = _tokenize(body)
	tree = _Parser(tokens).parse()
	# Run the same normalization the MathML front end uses, so that the speech
	# rules see one consistent tree shape regardless of input format.
	_reindex(tree)
	tree = _simplify(tree)
	_reindex(tree)
	_group_fences(tree)
	_reindex(tree)
	return tree
