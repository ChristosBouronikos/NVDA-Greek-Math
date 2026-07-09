# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.

"""Greek math speech engine: pure Python, no NVDA dependencies.

Public API:
	parse_mathml(mathml)           -> MathNode tree
	speak_mathml(mathml, config)   -> list of speech tokens (str | Pause)
	speak_node(node, config)       -> tokens for a subtree (used by navigation)
	tokens_to_text(tokens)         -> plain-text preview (tests, clipboard)
	role_description(node)         -> Greek position label for navigation
"""

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

__all__ = [
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
	"parse_mathml",
	"role_description",
	"speak_mathml",
	"speak_node",
	"tokens_to_text",
]
