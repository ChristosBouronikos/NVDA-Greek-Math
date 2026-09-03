# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 3 or later.
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

"""Greek math speech engine: pure Python, no NVDA dependencies.

Public API:
	parse_mathml(mathml)           -> MathNode tree
	speak_mathml(mathml, config)   -> list of speech tokens (str | Pause)
	latex_to_tree(latex)           -> MathNode tree (LaTeX front end)
	speak_latex(latex, config)     -> tokens for a LaTeX string
	speak_node(node, config)       -> tokens for a subtree (used by navigation)
	tokens_to_text(tokens)         -> plain-text preview (tests, clipboard)
	role_description(node)         -> Greek position label for navigation
"""

from .latex import (
	LatexParseError,
	latex_to_tree,
	looks_like_latex,
	strip_math_delimiters,
)
from .parser import MathMLParseError, MathNode, mathnode_to_mathml, parse_mathml
from .semantics import (
	EngineDiagnostics,
	SemanticNode,
	get_last_engine_diagnostics,
	interpret_latex,
	interpret_mathml,
	interpret_node,
	interpret_unicodemath,
	reset_engine_diagnostics,
	semantic_navigation_children,
)
from .speech import (
	MEDIUM,
	LONG,
	Language,
	NavigationMark,
	Pause,
	Prosody,
	ReadingConfig,
	SHORT,
	SMART,
	TERSE,
	VERBOSE,
	is_simple,
	enrich_speech,
	role_description,
	speak_mathml,
	speak_node,
	tokens_to_text,
)
from .terminology_el import PROFILES, SCHOOL, STANDARD, TERMINOLOGY_VERSION, UNIVERSITY
from .unicodemath import (
	detect_math_format,
	UnicodeMathParseError,
	looks_like_unicodemath,
	unicodemath_to_latex,
	unicodemath_to_tree,
)


def speak_latex(latex, config=None):
	"""LaTeX math string → list of Greek speech tokens (str | Pause)."""
	reset_engine_diagnostics()
	return speak_node(latex_to_tree(latex), config)


def speak_unicodemath(source, config=None):
	"""Microsoft UnicodeMath string → list of Greek speech tokens."""
	reset_engine_diagnostics()
	return speak_node(unicodemath_to_tree(source), config)


__all__ = [
	"detect_math_format",
	"LatexParseError",
	"MathMLParseError",
	"MathNode",
	"SemanticNode",
	"EngineDiagnostics",
	"Language",
	"NavigationMark",
	"Pause",
	"Prosody",
	"ReadingConfig",
	"SHORT",
	"MEDIUM",
	"LONG",
	"TERSE",
	"SMART",
	"VERBOSE",
	"STANDARD",
	"SCHOOL",
	"UNIVERSITY",
	"PROFILES",
	"TERMINOLOGY_VERSION",
	"is_simple",
	"enrich_speech",
	"latex_to_tree",
	"looks_like_latex",
	"looks_like_unicodemath",
	"mathnode_to_mathml",
	"parse_mathml",
	"interpret_node",
	"interpret_mathml",
	"interpret_latex",
	"interpret_unicodemath",
	"semantic_navigation_children",
	"role_description",
	"speak_latex",
	"speak_mathml",
	"speak_node",
	"speak_unicodemath",
	"strip_math_delimiters",
	"tokens_to_text",
	"UnicodeMathParseError",
	"unicodemath_to_latex",
	"unicodemath_to_tree",
	"get_last_engine_diagnostics",
]
