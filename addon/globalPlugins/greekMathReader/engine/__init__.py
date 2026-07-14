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
from .parser import MathMLParseError, MathNode, parse_mathml
from .speech import (
	MEDIUM,
	LONG,
	Pause,
	ReadingConfig,
	SHORT,
	SMART,
	TERSE,
	VERBOSE,
	is_simple,
	role_description,
	speak_mathml,
	speak_node,
	tokens_to_text,
)


def speak_latex(latex, config=None):
	"""LaTeX math string → list of Greek speech tokens (str | Pause)."""
	return speak_node(latex_to_tree(latex), config)


__all__ = [
	"LatexParseError",
	"MathMLParseError",
	"MathNode",
	"Pause",
	"ReadingConfig",
	"SHORT",
	"MEDIUM",
	"LONG",
	"TERSE",
	"SMART",
	"VERBOSE",
	"is_simple",
	"latex_to_tree",
	"looks_like_latex",
	"parse_mathml",
	"role_description",
	"speak_latex",
	"speak_mathml",
	"speak_node",
	"strip_math_delimiters",
	"tokens_to_text",
]
