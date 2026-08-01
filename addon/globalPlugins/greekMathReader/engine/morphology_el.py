# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
"""Small, deterministic Greek morphology helpers for mathematical speech.

The renderer does not infer mathematical meaning.  It receives a resolved
concept and selects agreement forms, so terminology profiles cannot change the
semantics of an expression.
"""


ARTICLES = {
	("masculine", "nominative", "singular"): "ο",
	("feminine", "nominative", "singular"): "η",
	("neuter", "nominative", "singular"): "το",
	("masculine", "genitive", "singular"): "του",
	("feminine", "genitive", "singular"): "της",
	("neuter", "genitive", "singular"): "του",
	("masculine", "accusative", "singular"): "τον",
	("feminine", "accusative", "singular"): "την",
	("neuter", "accusative", "singular"): "το",
	("masculine", "nominative", "plural"): "οι",
	("feminine", "nominative", "plural"): "οι",
	("neuter", "nominative", "plural"): "τα",
	("masculine", "genitive", "plural"): "των",
	("feminine", "genitive", "plural"): "των",
	("neuter", "genitive", "plural"): "των",
	("masculine", "accusative", "plural"): "τους",
	("feminine", "accusative", "plural"): "τις",
	("neuter", "accusative", "plural"): "τα",
}


def grammatical_number(count):
	"""Return singular only for exactly plus or minus one."""
	try:
		return "singular" if abs(float(count)) == 1 else "plural"
	except (TypeError, ValueError):
		return "plural"


def counted_form(singular, plural, count):
	return singular if grammatical_number(count) == "singular" else plural


def article(gender, case="nominative", number="singular"):
	return ARTICLES.get((gender, case, number), "")


def with_preposition(preposition, gender, case="accusative", number="singular"):
	"""Join a mathematical connector with its agreeing definite article."""
	selected = article(gender, case, number)
	return " ".join(part for part in (preposition, selected) if part)


def join_arguments(readings, connector="και"):
	readings = [reading for reading in readings if reading]
	if len(readings) < 2:
		return " ".join(readings)
	return ", ".join(readings[:-1]) + " " + connector + " " + readings[-1]
