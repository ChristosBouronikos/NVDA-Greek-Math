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

"""NVDA math presentation provider backed by the Greek speech engine."""

"""Local preview and report helpers, independent of NVDA settings mutation."""

import json
from urllib.parse import urlencode, quote

from .engine import speak_mathml, speak_latex, speak_unicodemath

PREVIEW_EXAMPLES = (
	("Capitals and letters", '<math><mi>G</mi><mo>+</mo><mi>g</mi><mo>+</mo><mi>Γ</mi><mo>+</mo><mi>γ</mi><mo>+</mo><mi>AB</mi></math>'),
	("Fractions and pauses", '<math><mfrac><mi>a</mi><mi>b</mi></mfrac><mi>c</mi></math>'),
	("Tensor indices", '<math><msubsup><mi>T</mi><mi>μ</mi><mi>ν</mi></msubsup></math>'),
	("Matrix including zeros", '<math><mrow><mo>[</mo><mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>0</mn></mtd></mtr><mtr><mtd><mn>0</mn></mtd><mtd><mn>2</mn></mtd></mtr></mtable><mo>]</mo></mrow></math>'),
	("Unknown symbol", '<math><mi>🜁</mi><mo>+</mo><mi>x</mi></math>'),
	("Composition and gradient", '<math><mrow><mi>f</mi><mo>∘</mo><mi>g</mi></mrow><mo>;</mo><mrow><mo>∇</mo><mi>f</mi></mrow></math>'),
)


def preview_tokens(source, input_format, reading_config):
	reader = {"mathml": speak_mathml, "latex": speak_latex, "unicodemath": speak_unicodemath}[input_format]
	return reader(source, reading_config)


def reading_report(reading, expected="", notes=""):
	return "\n".join((
		"Greek Math Reader — reading problem", "",
		"Expression:", reading["expression"], "",
		"Actual speech:", reading["actualSpeech"], "",
		"Expected speech:", expected, "", "User notes:", notes, "",
		"Format: " + reading["format"], "Preset: " + reading["preset"],
		"Context: " + reading["context"], "Backend: " + reading["backend"],
		"Voice: " + reading["voice"], "Synthesizer: " + reading["synthesizer"],
		"Settings at the time of reading:",
		json.dumps(reading["settings"], ensure_ascii=False, indent=2, sort_keys=True),
	))


def report_mailto(report):
	return "mailto:cbouronikos@uth.gr?" + urlencode({
		"subject": "Greek Math Reader: reading problem", "body": report,
	}, quote_via=quote)
