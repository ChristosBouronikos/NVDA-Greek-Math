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

"""Ελληνική γραμματική για μαθηματική εκφώνηση: δυνάμεις, ρίζες, τακτικά
αριθμητικά, κλασματικά ονόματα, παράγωγοι.

Όπως και το symbols_el.py, το αρχείο αυτό περιέχει ΜΟΝΟ δεδομένα ορολογίας
και απλές συναρτήσεις επιλογής, ώστε η αναθεώρηση να είναι εύκολη.
"""

# ---------------------------------------------------------------------------
# Θηλυκά τακτικά αριθμητικά 1–99: πρώτη, δεύτερη, …, εικοστή πρώτη, …
# Χρησιμοποιούνται για δυνάμεις (ενν. "δύναμη"), ρίζες και τάξεις παραγώγων.
# ---------------------------------------------------------------------------

# ΠΡΟΣ ΑΝΑΘΕΩΡΗΣΗ: χρησιμοποιείται η σύγχρονη μορφή "τέταρτη"·
# στην παραδοσιακή υπαγόρευση ακούγεται και "στην τετάρτην/τετάρτη".
_ORDINAL_UNITS_F = {
	1: "πρώτη", 2: "δεύτερη", 3: "τρίτη", 4: "τέταρτη", 5: "πέμπτη",
	6: "έκτη", 7: "έβδομη", 8: "όγδοη", 9: "ένατη",
}

_ORDINAL_TEENS_F = {
	10: "δέκατη", 11: "ενδέκατη", 12: "δωδέκατη",
}

_ORDINAL_TENS_F = {
	20: "εικοστή", 30: "τριακοστή", 40: "τεσσαρακοστή", 50: "πεντηκοστή",
	60: "εξηκοστή", 70: "εβδομηκοστή", 80: "ογδοηκοστή", 90: "ενενηκοστή",
}


def feminine_ordinal(value):
	"""Θηλυκό τακτικό για 1–99: 4 → 'τέταρτη', 21 → 'εικοστή πρώτη'. None εκτός ορίων."""
	if value in _ORDINAL_UNITS_F:
		return _ORDINAL_UNITS_F[value]
	if value in _ORDINAL_TEENS_F:
		return _ORDINAL_TEENS_F[value]
	if 13 <= value <= 19:
		return f"δέκατη {_ORDINAL_UNITS_F[value - 10]}"
	if value in _ORDINAL_TENS_F:
		return _ORDINAL_TENS_F[value]
	if 21 <= value <= 99 and value % 10 != 0:
		return f"{_ORDINAL_TENS_F[value // 10 * 10]} {_ORDINAL_UNITS_F[value % 10]}"
	return None


# Το τελικό ν του άρθρου: "στην" πριν από φωνήεν ή κ, π, τ, ξ, ψ — αλλιώς "στη".
_KEEPS_FINAL_N = set("αάεέηήιίϊΐοόυύϋΰωώκπτξψ")


def _stin(word):
	return "στην" if word and word[0].lower() in _KEEPS_FINAL_N else "στη"


# ---------------------------------------------------------------------------
# Δυνάμεις: "χι στο τετράγωνο", "χι στον κύβο", "χι στην τετάρτη", …
# ---------------------------------------------------------------------------

POWER_SPECIAL = {
	2: "στο τετράγωνο",
	3: "στον κύβο",
}

# Μεταβλητοί εκθέτες που έχουν καθιερωμένη ανάγνωση: x^ν "χι στη νιοστή".
POWER_VARIABLE = {
	"n": "στη νιοστή",
	"ν": "στη νιοστή",
	"k": "στην κάπα",
	"κ": "στην κάπα",
	"m": "στη μι",
	"μ": "στη μι",
}


def power_reading(exponent_text):
	"""Επιστρέφει την εκφώνηση εκθέτη για απλούς εκθέτες, αλλιώς None.

	"2" → "στο τετράγωνο", "5" → "στην πέμπτη", "21" → "στην εικοστή πρώτη",
	"ν" → "στη νιοστή".
	"""
	text = exponent_text.strip().replace("−", "-")
	if text in POWER_VARIABLE:
		return POWER_VARIABLE[text]
	try:
		value = int(text)
	except ValueError:
		return None
	if value in POWER_SPECIAL:
		return POWER_SPECIAL[value]
	ordinal = feminine_ordinal(value)
	if ordinal:
		return f"{_stin(ordinal)} {ordinal}"
	if value < 0:
		return f"στη δύναμη μείον {-value}"
	return f"στη δύναμη {value}"


# ---------------------------------------------------------------------------
# Ρίζες: τετραγωνική, κυβική, τετάρτη, νιοστή, τάξης κάπα
# ---------------------------------------------------------------------------

ROOT_SPECIAL = {
	2: "τετραγωνική ρίζα",
	3: "κυβική ρίζα",
}

ROOT_VARIABLE = {
	"n": "νιοστή ρίζα",
	"ν": "νιοστή ρίζα",
	"k": "ρίζα τάξης κάπα",
	"κ": "ρίζα τάξης κάπα",
	"m": "ρίζα τάξης μι",
	"μ": "ρίζα τάξης μι",
}


def root_reading(index_text):
	"""'3' → 'κυβική ρίζα', '12' → 'δωδέκατη ρίζα', 'ν' → 'νιοστή ρίζα', αλλιώς None."""
	text = index_text.strip()
	if text in ROOT_VARIABLE:
		return ROOT_VARIABLE[text]
	try:
		value = int(text)
	except ValueError:
		return None
	if value in ROOT_SPECIAL:
		return ROOT_SPECIAL[value]
	ordinal = feminine_ordinal(value)
	if ordinal:
		return f"{ordinal} ρίζα"
	return f"ρίζα τάξης {value}"


# ---------------------------------------------------------------------------
# Παράγωγοι: τόνοι και τάξη παραγώγου
# ---------------------------------------------------------------------------

PRIME_READINGS = {
	1: "τόνος",
	2: "δύο τόνοι",
	3: "τρεις τόνοι",
	4: "τέσσερις τόνοι",
}

DERIVATIVE_ORDER_VARIABLE = {
	"n": "νιοστή παράγωγος",
	"ν": "νιοστή παράγωγος",
	"k": "παράγωγος τάξης κάπα",
	"κ": "παράγωγος τάξης κάπα",
}


def derivative_order_reading(order_text):
	"""'1' → 'παράγωγος', '2' → 'δεύτερη παράγωγος', '11' → 'ενδέκατη παράγωγος'."""
	text = order_text.strip()
	if text in DERIVATIVE_ORDER_VARIABLE:
		return DERIVATIVE_ORDER_VARIABLE[text]
	try:
		value = int(text)
	except ValueError:
		return None
	if value == 1:
		return "παράγωγος"
	ordinal = feminine_ordinal(value)
	if ordinal:
		return f"{ordinal} παράγωγος"
	return f"παράγωγος τάξης {value}"


# ---------------------------------------------------------------------------
# Αριθμητικά κλάσματα με "όνομα": 1/2 "ένα δεύτερο", 3/4 "τρία τέταρτα"
# ---------------------------------------------------------------------------

# Αριθμητής (απόλυτη τιμή) ως λέξη — μόνο για μικρά κλασματικά ονόματα.
_NUMERATOR_WORDS = {
	1: "ένα", 2: "δύο", 3: "τρία", 4: "τέσσερα", 5: "πέντε",
	6: "έξι", 7: "επτά", 8: "οκτώ", 9: "εννέα",
}

# Ονόματα παρονομαστών: ενικός/πληθυντικός.
_DENOMINATOR_NAMES = {
	2: ("δεύτερο", "δεύτερα"),
	3: ("τρίτο", "τρίτα"),
	4: ("τέταρτο", "τέταρτα"),
	5: ("πέμπτο", "πέμπτα"),
	6: ("έκτο", "έκτα"),
	7: ("έβδομο", "έβδομα"),
	8: ("όγδοο", "όγδοα"),
	9: ("ένατο", "ένατα"),
	10: ("δέκατο", "δέκατα"),
	100: ("εκατοστό", "εκατοστά"),
	1000: ("χιλιοστό", "χιλιοστά"),
}

# Ειδική περίπτωση: 1/2 συχνά διαβάζεται "μισό".
HALF_READING = "ένα δεύτερο"


def numeric_fraction_reading(numerator_text, denominator_text):
	"""'3', '4' → 'τρία τέταρτα', '23', '100' → '23 εκατοστά'.

	None αν δεν υπάρχει φυσικό όνομα για τον παρονομαστή.
	"""
	try:
		numerator = int(numerator_text.strip())
		denominator = int(denominator_text.strip())
	except ValueError:
		return None
	if numerator < 1 or numerator > 999:
		return None
	if denominator not in _DENOMINATOR_NAMES:
		return None
	if numerator == 1 and denominator == 2:
		return HALF_READING
	singular, plural = _DENOMINATOR_NAMES[denominator]
	word = _NUMERATOR_WORDS.get(numerator, str(numerator))
	return f"{word} {singular if numerator == 1 else plural}"


# ---------------------------------------------------------------------------
# Δείκτες: x₁ "χι ένα" — οι αριθμοί μένουν ως ψηφία (τα διαβάζει η σύνθεση
# φωνής)· εδώ ορίζεται μόνο το πρόθεμα της αναλυτικής εκφώνησης.
# ---------------------------------------------------------------------------

SUBSCRIPT_WORD = "δείκτης"           # αναλυτικά: "χι δείκτης ένα"
SUBSCRIPT_END_WORD = "τέλος δείκτη"  # για σύνθετους δείκτες

# ---------------------------------------------------------------------------
# Δεκαδικοί: το ελληνικό δεκαδικό σύμβολο είναι το κόμμα.
# Το "3.14" κανονικοποιείται σε "3,14" ώστε η ελληνική σύνθεση φωνής
# να το εκφωνήσει "τρία κόμμα δεκατέσσερα".
# ---------------------------------------------------------------------------


def normalize_number(text):
	"""Κανονικοποίηση αριθμού για ελληνική εκφώνηση (τελεία → κόμμα)."""
	stripped = text.strip()
	if not stripped:
		return stripped
	# Μετατροπή δεκαδικής τελείας σε κόμμα μόνο για απλά δεκαδικά (3.14),
	# όχι για αριθμούς με χιλιαδικούς διαχωριστές (1.234.567).
	if stripped.count(".") == 1 and "," not in stripped:
		integer_part, _, decimal_part = stripped.partition(".")
		if integer_part.lstrip("+-").isdigit() and decimal_part.isdigit():
			return f"{integer_part},{decimal_part}"
	return stripped
