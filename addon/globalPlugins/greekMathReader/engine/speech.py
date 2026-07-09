# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.

"""Μετατροπή δέντρου MathML σε ελληνική εκφώνηση.

Pure Python (χωρίς εξαρτήσεις NVDA). Η έξοδος είναι λίστα από tokens:
strings και αντικείμενα Pause. Το επίπεδο NVDA τα μετατρέπει σε
speech sequence με BreakCommand.
"""

import re

from . import grammar_el as grammar
from . import symbols_el as symbols
from .parser import MathNode, parse_mathml  # noqa: F401 (re-exported for convenience)

# Επίπεδα λεπτομέρειας εκφώνησης
TERSE = 0    # σύντομη: "χι τετράγωνο", ελάχιστες δομικές αναγγελίες
SMART = 1    # έξυπνη: δομικές αναγγελίες μόνο όταν χρειάζονται (προεπιλογή)
VERBOSE = 2  # αναλυτική: πλήρεις αναγγελίες αρχής/τέλους δομών


class Pause(object):
	"""Παύση στην εκφώνηση, σε χιλιοστά του δευτερολέπτου (ενδεικτικά)."""

	__slots__ = ("ms",)

	def __init__(self, ms):
		self.ms = ms

	def __repr__(self):
		return f"<Pause {self.ms}>"

	def __eq__(self, other):
		return isinstance(other, Pause) and other.ms == self.ms


SHORT = 100
MEDIUM = 250
LONG = 450


class ReadingConfig(object):
	"""Ρυθμίσεις ανάγνωσης. Κρατιέται απλό ώστε να αποθηκεύεται εύκολα στο config του NVDA."""

	def __init__(self, verbosity=SMART, decimal_comma=True, announce_capitals=False):
		self.verbosity = verbosity
		self.decimal_comma = decimal_comma
		self.announce_capitals = announce_capitals


_PRIMES = {"′": 1, "″": 2, "‴": 3, "⁗": 4, "'": 1, "’": 1}
_ACCENTS_OVER = {
	"¯": "παύλα", "‾": "παύλα", "ˉ": "παύλα", "̄": "παύλα", "̅": "παύλα", "−": "παύλα", "-": "παύλα", "_": "παύλα",
	"→": "διάνυσμα", "⃗": "διάνυσμα", "⇀": "διάνυσμα",
	"^": "καπέλο", "ˆ": "καπέλο", "̂": "καπέλο",
	"~": "περισπωμένη", "˜": "περισπωμένη", "̃": "περισπωμένη",
	"˙": "τελεία", "̇": "τελεία", ".": "τελεία",
	"¨": "δύο τελείες", "̈": "δύο τελείες",
	"⏜": "τόξο", "⌢": "τόξο",
}
_BIG_OPERATOR_CHARS = set(symbols.BIG_OPERATORS)
_SUM_LIKE = {"∑", "∏", "⋃", "⋂", "⨁", "⨂"}
_INTEGRAL_CHARS = {"∫", "∬", "∭", "∮", "∯"}
_RELATION_CHARS = set(symbols.RELATIONS) | {"⇒", "⇔", "→", "↦"}
_DIFFERENTIAL_RE = re.compile(r"^[dⅆ∂](\d*)(.*)$", re.DOTALL)
_TRAILING_SUPERSCRIPTS_RE = re.compile(r"^([\d.,]+)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)$")
_SUPERSCRIPT_TRANS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def is_simple(node):
	"""Απλή παράσταση: εκφωνείται χωρίς δομικές αναγγελίες (π.χ. "2χι", "ν+1")."""
	if node.is_token:
		return True
	if node.tag in ("msub", "msup"):
		base, script = node.child(0), node.child(1)
		return base is not None and script is not None and base.is_token and script.is_token
	if node.tag == "mrow":
		if node.attrib.get("_fenced"):
			return False
		if len(node.children) > 4:
			return False
		return all(child.is_token for child in node.children)
	return False


def role_description(node):
	"""Ελληνική περιγραφή της θέσης ενός κόμβου μέσα στον γονέα του (για πλοήγηση)."""
	parent = node.parent
	if parent is None:
		return None
	i = node.index
	tag = parent.tag
	if tag == "mfrac":
		return "αριθμητής" if i == 0 else "παρονομαστής"
	if tag == "msup":
		return "βάση" if i == 0 else "εκθέτης"
	if tag == "msub":
		return "βάση" if i == 0 else "δείκτης"
	if tag == "msubsup":
		return ("βάση", "κάτω όριο", "πάνω όριο")[i] if i < 3 else None
	if tag == "munderover":
		return ("βάση", "κάτω όριο", "πάνω όριο")[i] if i < 3 else None
	if tag == "munder":
		return "βάση" if i == 0 else "κάτω σύμβολο"
	if tag == "mover":
		return "βάση" if i == 0 else "πάνω σύμβολο"
	if tag == "mroot":
		return "υπόρριζο" if i == 0 else "τάξη ρίζας"
	if tag == "msqrt":
		return "υπόρριζο"
	if tag == "mtr":
		return f"στήλη {i + 1}"
	if tag == "mtable":
		return f"γραμμή {i + 1}"
	return None


class MathSpeaker(object):
	"""Μετατρέπει MathNode δέντρα σε ελληνικά speech tokens."""

	def __init__(self, config=None):
		self.config = config or ReadingConfig()

	# ------------------------------------------------------------------
	# Δημόσια διεπαφή
	# ------------------------------------------------------------------

	def speak(self, node):
		tokens = self._node(node)
		return _clean_tokens(tokens)

	# ------------------------------------------------------------------
	# Κεντρικός διεκπεραιωτής
	# ------------------------------------------------------------------

	def _node(self, node):
		handler = getattr(self, f"_speak_{node.tag}", None)
		if handler is not None:
			return handler(node)
		# Άγνωστη ετικέτα: διάβασε τα παιδιά της στη σειρά.
		return self._sequence(node.children)

	def _sequence(self, children):
		"""Εκφώνηση ακολουθίας αδελφών κόμβων (περιεχόμενο mrow)."""
		out = []
		i = 0
		# Μοτίβο ορισμού συνάρτησης: f : A → B
		fn_def = self._function_definition(children)
		if fn_def is not None:
			return fn_def
		while i < len(children):
			child = children[i]
			# Αόρατοι τελεστές
			if child.tag == "mo" and child.text in symbols.INVISIBLE_CHARS:
				if child.text == symbols.INVISIBLE_PLUS:
					out.append("και")
				# εφαρμογή συνάρτησης/αόρατος πολλαπλασιασμός: σιωπή
				i += 1
				continue
			# Μεγάλοι τελεστές: ολοκληρώματα, αθροίσματα, γινόμενα
			big = self._big_operator(child)
			if big is not None:
				out.extend(big)
				if self._has_operand_after(children, i):
					out.append("του")
				i += 1
				continue
			# Όριο: lim με κάτω δείκτη
			lim = self._limit(child)
			if lim is not None:
				out.extend(lim)
				if self._has_operand_after(children, i):
					out.append("του")
				i += 1
				continue
			# Σύστημα/κλάδοι: άγκιστρο ακολουθούμενο από πίνακα
			if (
				child.tag == "mo" and child.text == "{"
				and i + 1 < len(children) and children[i + 1].tag == "mtable"
			):
				out.extend(self._cases(children[i + 1]))
				i += 2
				continue
			# Συνάρτηση με παρενθέσεις: f(x), ημ(χ) — προσθέτουμε "του".
			# Ο αόρατος τελεστής εφαρμογής (U+2061) μπορεί να μεσολαβεί.
			if self._is_function_atom(child):
				j = i + 1
				if (
					j < len(children)
					and children[j].tag == "mo"
					and children[j].text == symbols.INVISIBLE_APPLY
				):
					j += 1
				if j < len(children) and self._is_paren_group(children[j]):
					out.extend(self._node(child))
					out.append("του")
					out.extend(self._fenced_content_or_group(children[j]))
					i = j + 1
					continue
			# Δυαδικό/μοναδιαίο πλην
			if child.tag == "mo" and child.text in ("−", "-"):
				if self._is_unary_context(children, i):
					out.append("μείον")
				else:
					out.append("πλην")
				i += 1
				continue
			# ":" — "προς" σε αναλογίες (το "τέτοιο ώστε" δίνεται μέσα σε σύνολα)
			if child.tag == "mo" and child.text in (":", "∶"):
				out.append("προς")
				i += 1
				continue
			out.extend(self._node(child))
			i += 1
		return out

	def _has_operand_after(self, children, i):
		for sibling in children[i + 1:]:
			if sibling.tag == "mo":
				if sibling.text in symbols.INVISIBLE_CHARS:
					continue
				return sibling.text not in _RELATION_CHARS
			return True
		return False

	def _is_unary_context(self, children, i):
		if i == 0:
			return True
		prev = children[i - 1]
		if prev.tag == "mo":
			if prev.text in symbols.INVISIBLE_CHARS:
				return self._is_unary_context(children, i - 1)
			if prev.text in symbols.FENCES_OPEN:
				return True
			if prev.text in _RELATION_CHARS or symbols.symbol_reading(prev.text):
				return prev.text not in ("!",)
		return False

	def _function_definition(self, children):
		"""f : A → B  →  'συνάρτηση εφ από το Α στο Β'."""
		if len(children) < 5:
			return None
		first = children[0]
		if not (first.tag == "mi" and len(first.text) <= 3):
			return None
		if not (children[1].tag == "mo" and children[1].text in (":", "∶")):
			return None
		arrow_index = None
		for i, child in enumerate(children[2:], start=2):
			if child.tag == "mo" and child.text in ("→", "⟶", "↦"):
				arrow_index = i
				break
		if arrow_index is None or arrow_index == 2 or arrow_index == len(children) - 1:
			return None
		out = ["συνάρτηση"]
		out.extend(self._node(first))
		out.append("από το")
		out.extend(self._sequence(children[2:arrow_index]))
		out.append("στο")
		out.extend(self._sequence(children[arrow_index + 1:]))
		return out

	# ------------------------------------------------------------------
	# Κόμβοι-σύμβολα (tokens)
	# ------------------------------------------------------------------

	def _number_set_phrase(self, node, phrase):
		"""Αποφυγή διπλού άρθρου: "ανήκει στο το σύνολο…" → "ανήκει στο σύνολο…"."""
		prev = node.previous_sibling()
		if prev is not None and prev.tag == "mo":
			reading = symbols.symbol_reading(prev.text) or ""
			if reading.endswith(("στο", "του", " το")) and phrase.startswith("το "):
				return phrase[3:]
		return phrase

	def _speak_mi(self, node):
		text = node.text
		if not text:
			return []
		if text in symbols.NUMBER_SETS:
			if self.config.verbosity == TERSE:
				return [symbols.NUMBER_SETS_TERSE[text]]
			return [self._number_set_phrase(node, symbols.NUMBER_SETS[text])]
		if text in symbols.FUNCTION_NAMES and len(text) > 1:
			return [symbols.FUNCTION_NAMES[text]]
		if len(text) == 1:
			reading = symbols.letter_reading(
				text, verbose=(self.config.verbosity == VERBOSE or self.config.announce_capitals)
			)
			if reading:
				return [reading]
			symbol = symbols.symbol_reading(text)
			if symbol:
				return [symbol]
			return [text]
		# Πολυγράμματο mi: όνομα συνάρτησης, ελληνική λέξη, ή γράμμα-γράμμα
		if text in symbols.FUNCTION_NAMES:
			return [symbols.FUNCTION_NAMES[text]]
		if re.fullmatch(r"[A-Za-zΑ-ΩΆ-Ώ]{2,4}", text):
			# Πιθανό ευθύγραμμο τμήμα/σχήμα (ΑΒ, ΑΒΓ): γράμμα-γράμμα.
			readings = [symbols.letter_reading(c) or c for c in text]
			return [" ".join(readings)]
		return [text]

	def _speak_mn(self, node):
		text = node.text
		# Έτοιμοι χαρακτήρες κλασμάτων κ.λπ. μέσα σε mn: ½ → "ένα δεύτερο"
		symbol = symbols.symbol_reading(text)
		if symbol:
			return [symbol]
		# Αριθμός με χαρακτήρες εκθέτη μέσα στο κείμενο: "10²" → "10 στο τετράγωνο"
		match = _TRAILING_SUPERSCRIPTS_RE.match(text)
		if match:
			base_text, sup_chars = match.group(1), match.group(2)
			power = grammar.power_reading(sup_chars.translate(_SUPERSCRIPT_TRANS))
			if power:
				if self.config.decimal_comma:
					base_text = grammar.normalize_number(base_text)
				return [base_text, power]
		if self.config.decimal_comma:
			text = grammar.normalize_number(text)
		return [text] if text else []

	def _speak_mo(self, node):
		text = node.text
		if not text or text in symbols.INVISIBLE_CHARS:
			return []
		if text in ("−", "-"):
			return ["πλην"]
		if text in symbols.FENCES_OPEN and node.parent and node.index == 0:
			return [symbols.FENCES_OPEN[text]]
		if text in symbols.FENCES_CLOSE and node.parent and node.index == len(node.parent.children) - 1:
			return [symbols.FENCES_CLOSE[text]]
		reading = symbols.symbol_reading(text)
		if reading:
			return [reading]
		if text in symbols.FENCES_OPEN:
			return [symbols.FENCES_OPEN[text]]
		if text in symbols.FENCES_CLOSE:
			return [symbols.FENCES_CLOSE[text]]
		letter = symbols.letter_reading(text)
		if letter:
			return [letter]
		return [text]

	def _speak_mtext(self, node):
		return [node.text] if node.text else []

	def _speak_ms(self, node):
		return [node.text] if node.text else []

	def _speak_math(self, node):
		return self._sequence(node.children)

	# ------------------------------------------------------------------
	# mrow και ομάδες με σύμβολα ομαδοποίησης
	# ------------------------------------------------------------------

	def _speak_mrow(self, node):
		fence_info = self._fence_info(node)
		if fence_info is not None:
			return self._speak_fenced(node, *fence_info)
		return self._sequence(node.children)

	def _fence_info(self, node):
		"""(open_char, close_char, inner_children) αν ο κόμβος είναι ομάδα με fences."""
		kids = node.children
		if len(kids) < 2:
			return None
		first, last = kids[0], kids[-1]
		if not (first.tag == "mo" and last.tag == "mo"):
			return None
		if first.text in symbols.MATCHING_FENCE and symbols.MATCHING_FENCE[first.text] == last.text:
			return (first.text, last.text, kids[1:-1])
		return None

	def _is_paren_group(self, node):
		info = self._fence_info(node) if node.tag == "mrow" else None
		return info is not None and info[0] == "("

	def _fenced_content_or_group(self, node):
		"""Ορίσματα συνάρτησης: χωρίς αναγγελία παρένθεσης όταν είναι απλά."""
		info = self._fence_info(node)
		if info is None:
			return self._node(node)
		_, _, inner = info
		if self._all_simple(inner):
			return self._arguments(inner)
		return self._node(node)

	def _arguments(self, inner):
		out = []
		for child in inner:
			if child.tag == "mo" and child.text in (",", symbols.INVISIBLE_COMMA):
				out.append(Pause(SHORT))
				out.append("κόμμα")
			else:
				out.extend(self._node(child))
		return out

	def _all_simple(self, nodes):
		return all(
			is_simple(n) or (n.tag == "mo" and (n.text == "," or n.text in symbols.INVISIBLE_CHARS))
			for n in nodes
		)

	def _speak_fenced(self, node, open_char, close_char, inner):
		verbosity = self.config.verbosity
		# Πίνακες, ορίζουσες, διανύσματα
		if len(inner) == 1 and inner[0].tag == "mtable":
			return self._table_with_fences(inner[0], open_char)
		# Απόλυτη τιμή
		if open_char == "|":
			out = ["απόλυτη τιμή του" if verbosity != TERSE else "απόλυτο"]
			out.extend(self._sequence(inner))
			if not self._all_simple(inner):
				out.append(Pause(SHORT))
				out.append("τέλος απόλυτης τιμής")
			return out
		# Νόρμα
		if open_char == "‖":
			out = ["νόρμα του"]
			out.extend(self._sequence(inner))
			if not self._all_simple(inner):
				out.append(Pause(SHORT))
				out.append("τέλος νόρμας")
			return out
		# Ακέραιο μέρος
		if open_char == "⌊":
			out = ["ακέραιο μέρος του"]
			out.extend(self._sequence(inner))
			out.append(Pause(SHORT))
			out.append("τέλος ακέραιου μέρους")
			return out
		if open_char == "⌈":
			out = ["άνω ακέραιο μέρος του"]
			out.extend(self._sequence(inner))
			out.append(Pause(SHORT))
			out.append("τέλος άνω ακέραιου μέρους")
			return out
		# Σύνολο σε άγκιστρα
		if open_char == "{":
			return self._set_notation(inner)
		# Διαστήματα: [α, β] και μικτά
		interval = self._interval(node, open_char, close_char, inner)
		if interval is not None:
			return interval
		# Γενική παρένθεση/αγκύλη
		out = [symbols.FENCES_OPEN.get(open_char, open_char)]
		out.extend(self._sequence(inner))
		out.append(Pause(SHORT))
		out.append(symbols.FENCES_CLOSE.get(close_char, close_char))
		return out

	def _split_top_level(self, inner, separators=(",",)):
		parts = [[]]
		for child in inner:
			if child.tag == "mo" and child.text in separators:
				parts.append([])
			else:
				parts[-1].append(child)
		return parts

	def _interval(self, node, open_char, close_char, inner):
		if open_char not in "([" or close_char not in ")]":
			return None
		parts = self._split_top_level(inner)
		if len(parts) != 2 or not parts[0] or not parts[1]:
			return None
		# Η (α, β) διαβάζεται ως διάστημα μόνο όταν προηγείται "ανήκει" (∈)
		# — αλλιώς είναι διατεταγμένο ζεύγος/σημείο και μένει γενική παρένθεση.
		if open_char == "(" and close_char == ")":
			prev = node.previous_sibling()
			if not (prev is not None and prev.tag == "mo" and prev.text in ("∈", "∉", "⊂", "⊆", "=")):
				return None
			kind = "ανοιχτό διάστημα"
		elif open_char == "[" and close_char == "]":
			kind = "κλειστό διάστημα"
		elif open_char == "[" and close_char == ")":
			kind = "διάστημα κλειστό αριστερά ανοιχτό δεξιά"
		else:
			kind = "διάστημα ανοιχτό αριστερά κλειστό δεξιά"
		out = [kind, "από"]
		out.extend(self._sequence(parts[0]))
		out.append("έως")
		out.extend(self._sequence(parts[1]))
		return out

	def _set_notation(self, inner):
		# {α, β, γ} → "το σύνολο με στοιχεία ..." | {x : P(x)} → "το σύνολο των x τέτοιων ώστε ..."
		separator_index = None
		for i, child in enumerate(inner):
			if child.tag == "mo" and child.text in (":", "∣", "|", "∶"):
				separator_index = i
				break
		if separator_index is not None:
			out = ["το σύνολο των"]
			out.extend(self._sequence(inner[:separator_index]))
			out.append("τέτοιων ώστε")
			out.extend(self._sequence(inner[separator_index + 1:]))
			return out
		out = ["σύνολο με στοιχεία"]
		out.extend(self._arguments(inner))
		if self.config.verbosity == VERBOSE:
			out.append(Pause(SHORT))
			out.append("τέλος συνόλου")
		return out

	# ------------------------------------------------------------------
	# Κλάσματα (και παράγωγοι, διωνυμικοί συντελεστές)
	# ------------------------------------------------------------------

	def _speak_mfrac(self, node):
		numerator, denominator = node.child(0), node.child(1)
		if numerator is None or denominator is None:
			return self._sequence(node.children)
		verbosity = self.config.verbosity
		# Διωνυμικός συντελεστής: mfrac με linethickness=0
		thickness = node.attrib.get("linethickness", "").strip()
		if thickness in ("0", "0px", "0pt", "0em"):
			out = ["συνδυασμοί"]
			out.extend(self._operand(numerator))
			out.append("ανά")
			out.extend(self._operand(denominator))
			return out
		# Παράγωγος κατά Leibniz: dy/dx, d²y/dx², ∂f/∂x
		derivative = self._derivative(numerator, denominator)
		if derivative is not None:
			return derivative
		# Αριθμητικό κλάσμα με φυσικό όνομα: 3/4 "τρία τέταρτα"
		if verbosity != VERBOSE and numerator.tag == "mn" and denominator.tag == "mn":
			named = grammar.numeric_fraction_reading(numerator.text, denominator.text)
			if named:
				return [named]
		simple = is_simple(numerator) and is_simple(denominator)
		if simple and verbosity != VERBOSE:
			out = []
			out.extend(self._operand(numerator))
			out.append("διά")
			out.extend(self._operand(denominator))
			return out
		if verbosity == TERSE:
			out = ["κλάσμα"]
			out.extend(self._node(numerator))
			out.append("διά")
			out.extend(self._node(denominator))
			out.append(Pause(SHORT))
			out.append("τέλος κλάσματος")
			return out
		out = ["κλάσμα με αριθμητή"]
		out.extend(self._node(numerator))
		out.append(Pause(MEDIUM))
		out.append("και παρονομαστή")
		out.extend(self._node(denominator))
		out.append(Pause(MEDIUM))
		out.append("τέλος κλάσματος")
		return out

	def _derivative(self, numerator, denominator):
		num_text = numerator.token_text().replace(" ", "")
		den_text = denominator.token_text().replace(" ", "")
		num_match = _DIFFERENTIAL_RE.match(num_text)
		den_match = _DIFFERENTIAL_RE.match(den_text)
		if not num_match or not den_match:
			return None
		if not (num_text[0] in "dⅆ∂" and den_text[0] in "dⅆ∂"):
			return None
		partial = num_text[0] == "∂" or den_text[0] == "∂"
		order_text = num_match.group(1) or "1"
		function_part = num_match.group(2)
		# Ο παρονομαστής πρέπει να είναι d + μεταβλητή (+ εκθέτης τάξης)
		den_body = den_match.group(2)
		den_vars = re.findall(r"[^\dⅆd∂]", den_body)
		if not den_vars:
			return None
		order = grammar.derivative_order_reading(order_text) or "παράγωγος"
		if partial:
			order = order.replace("παράγωγος", "μερική παράγωγος")
		out = [order]
		if function_part:
			out.append("του")
			readings = [symbols.letter_reading(c) or c for c in function_part]
			out.append(" ".join(readings))
		out.append("ως προς")
		var_readings = [symbols.letter_reading(c) or c for c in den_vars]
		out.append(" και ".join(var_readings) if len(var_readings) > 1 else var_readings[0])
		return out

	def _operand(self, node):
		"""Εκφώνηση τελεστέου, με παρένθεση γύρω από σύνθετα σε αναλυτική εκφώνηση."""
		return self._node(node)

	# ------------------------------------------------------------------
	# Ρίζες
	# ------------------------------------------------------------------

	def _speak_msqrt(self, node):
		inner = node.children
		verbosity = self.config.verbosity
		simple = self._all_simple(inner)
		if verbosity == TERSE and simple:
			out = ["ρίζα"]
			out.extend(self._sequence(inner))
			return out
		out = ["τετραγωνική ρίζα του"]
		out.extend(self._sequence(inner))
		if not simple or verbosity == VERBOSE:
			out.append(Pause(SHORT))
			out.append("τέλος ρίζας")
		return out

	def _speak_mroot(self, node):
		base, index = node.child(0), node.child(1)
		if base is None or index is None:
			return self._sequence(node.children)
		reading = grammar.root_reading(index.token_text())
		if reading is None:
			out = ["ρίζα τάξης"]
			out.extend(self._node(index))
			out.append("του")
		else:
			out = [reading, "του"]
		out.extend(self._node(base))
		if not is_simple(base) or self.config.verbosity == VERBOSE:
			out.append(Pause(SHORT))
			out.append("τέλος ρίζας")
		return out

	# ------------------------------------------------------------------
	# Εκθέτες, δείκτες
	# ------------------------------------------------------------------

	def _speak_msup(self, node):
		base, exponent = node.child(0), node.child(1)
		if base is None or exponent is None:
			return self._sequence(node.children)
		exp_text = exponent.token_text().strip()
		# Μοίρες: 30°
		if exp_text in ("∘", "°"):
			out = self._node(base)
			out.append("μοίρες")
			return out
		# Σύνολα αριθμών με πρόσημο ή δύναμη: ℝ⁺, ℤ*, ℝ²
		if base.is_token and base.text in symbols.NUMBER_SETS:
			if exp_text in symbols.NUMBER_SET_SIGNS:
				adjective = symbols.NUMBER_SET_SIGNS[exp_text]
				phrase = symbols.NUMBER_SETS[base.text].replace("των ", f"των {adjective} ", 1)
				return [self._number_set_phrase(node, phrase)]
			power = grammar.power_reading(exp_text) if is_simple(exponent) else None
			if power is not None:
				# ℝ² "ρο στο τετράγωνο", ℝⁿ "ρο στη νιοστή" — με το όνομα του γράμματος.
				letter = symbols.NUMBER_SETS_TERSE[base.text].split()[0]
				return [letter, power]
		# Τόνοι: σε αριθμούς είναι λεπτά της μοίρας (30° 15′), αλλού παράγωγοι (f′)
		total_primes = sum(_PRIMES.get(c, 0) for c in exp_text)
		if exp_text and all(c in _PRIMES for c in exp_text):
			out = self._node(base)
			if base.tag == "mn" and total_primes in (1, 2):
				out.append("πρώτα λεπτά" if total_primes == 1 else "δεύτερα λεπτά")
			else:
				out.append(grammar.PRIME_READINGS.get(total_primes, f"{total_primes} τόνοι"))
			return out
		# Ανάστροφος πίνακας: A^T
		if exp_text in ("T", "t", "⊤") and base.tag == "mi" and base.text.isupper():
			out = ["ανάστροφος του"]
			out.extend(self._node(base))
			return out
		# Συζυγής μιγαδικός: z*
		if exp_text in ("*", "∗") :
			out = ["συζυγής του"]
			out.extend(self._node(base))
			return out
		# Αντίστροφη συνάρτηση: f⁻¹, sin⁻¹ (τόξο ημιτόνου)
		if exp_text in ("-1", "−1") and self._is_function_atom(base):
			if base.tag == "mi" and base.text in symbols.INVERSE_TRIG:
				return [symbols.INVERSE_TRIG[base.text]]
			out = ["αντίστροφη της"]
			out.extend(self._node(base))
			return out
		# Απλή δύναμη: στο τετράγωνο, στον κύβο, στην νιοστή…
		power = grammar.power_reading(exp_text) if is_simple(exponent) else None
		out = self._node(base)
		if power is not None:
			out.append(power)
			return out
		out.append("υψωμένο σε")
		if is_simple(exponent):
			out.extend(self._node(exponent))
		else:
			out.append(Pause(SHORT))
			out.extend(self._node(exponent))
			out.append(Pause(SHORT))
			out.append("τέλος εκθέτη")
		return out

	def _is_function_atom(self, node):
		if node.tag == "mi":
			if len(node.text) > 1 and node.text in symbols.FUNCTION_NAMES:
				return True
			if node.text in ("f", "g", "h", "φ", "ψ", "σ"):
				return True
		if node.tag in ("msub", "msup"):
			base = node.child(0)
			return base is not None and self._is_function_atom(base)
		return False

	def _speak_msub(self, node):
		base, subscript = node.child(0), node.child(1)
		if base is None or subscript is None:
			return self._sequence(node.children)
		# Λογάριθμος με βάση: log₂
		if base.tag == "mi" and base.text in ("log", "lg"):
			out = ["λογάριθμος με βάση"]
			out.extend(self._node(subscript))
			return out
		out = self._node(base)
		if self.config.verbosity == VERBOSE:
			out.append(grammar.SUBSCRIPT_WORD)
			out.extend(self._node(subscript))
			if not is_simple(subscript):
				out.append(Pause(SHORT))
				out.append(grammar.SUBSCRIPT_END_WORD)
			return out
		if is_simple(subscript):
			out.extend(self._node(subscript))
			return out
		out.append(grammar.SUBSCRIPT_WORD)
		out.extend(self._node(subscript))
		out.append(Pause(SHORT))
		out.append(grammar.SUBSCRIPT_END_WORD)
		return out

	def _speak_msubsup(self, node):
		base, sub, sup = node.child(0), node.child(1), node.child(2)
		if base is None or sub is None or sup is None:
			return self._sequence(node.children)
		if base.tag == "mo" and base.text in _INTEGRAL_CHARS:
			out = [symbols.BIG_OPERATORS[base.text], "από"]
			out.extend(self._node(sub))
			out.append("έως")
			out.extend(self._node(sup))
			return out
		if base.tag == "mo" and base.text in _SUM_LIKE:
			return self._sum_like(base, sub, sup)
		# Γενική περίπτωση: πρώτα ο δείκτης, μετά ο εκθέτης: x₁²
		sub_node = MathNode("msub")
		sub_node.append(_clone(base))
		sub_node.append(_clone(sub))
		out = self._speak_msub(sub_node)
		power = grammar.power_reading(sup.token_text().strip()) if is_simple(sup) else None
		if power is not None:
			out.append(power)
		else:
			out.append("υψωμένο σε")
			out.extend(self._node(sup))
		return out

	# ------------------------------------------------------------------
	# Μεγάλοι τελεστές, όρια, πάνω/κάτω σύμβολα
	# ------------------------------------------------------------------

	def _big_operator(self, node):
		"""Αναγνώριση ∫/∑/∏ κ.λπ. ως msubsup/munderover/σκέτο mo."""
		if node.tag == "mo" and node.text in _BIG_OPERATOR_CHARS:
			return [symbols.BIG_OPERATORS[node.text]]
		if node.tag in ("msubsup", "munderover"):
			base = node.child(0)
			if base is not None and base.tag == "mo" and base.text in _BIG_OPERATOR_CHARS:
				sub, sup = node.child(1), node.child(2)
				if base.text in _INTEGRAL_CHARS:
					out = [symbols.BIG_OPERATORS[base.text], "από"]
					out.extend(self._node(sub))
					out.append("έως")
					out.extend(self._node(sup))
					return out
				return self._sum_like(base, sub, sup)
		if node.tag == "munder":
			base = node.child(0)
			if base is not None and base.tag == "mo" and base.text in _BIG_OPERATOR_CHARS:
				out = [symbols.BIG_OPERATORS[base.text], "για"]
				out.extend(self._under_condition(node.child(1)))
				return out
		return None

	def _sum_like(self, base, sub, sup):
		out = [symbols.BIG_OPERATORS[base.text], "για"]
		out.extend(self._under_condition(sub))
		if sup is not None and sup.tag != "none":
			out.append("έως")
			out.extend(self._node(sup))
		return out

	def _under_condition(self, under):
		"""Κάτω όριο αθροίσματος: 'n=1' → 'νι από 1'."""
		if under is None:
			return []
		if under.tag == "mrow":
			parts = self._split_top_level(under.children, separators=("=",))
			if len(parts) == 2 and parts[0] and parts[1]:
				out = []
				out.extend(self._sequence(parts[0]))
				out.append("από")
				out.extend(self._sequence(parts[1]))
				return out
		return self._node(under)

	def _limit(self, node):
		if node.tag != "munder":
			return None
		base, under = node.child(0), node.child(1)
		if base is None or under is None:
			return None
		if not (base.tag in ("mi", "mo") and base.text in ("lim", "limsup", "liminf")):
			return None
		out = [symbols.FUNCTION_NAMES.get(base.text, "όριο"), "καθώς το"]
		if under.tag == "mrow":
			arrow_split = self._split_top_level(under.children, separators=("→", "⟶"))
			if len(arrow_split) == 2 and arrow_split[0] and arrow_split[1]:
				out.extend(self._sequence(arrow_split[0]))
				out.append("τείνει στο")
				out.extend(self._speak_limit_target(arrow_split[1]))
				return out
		out.extend(self._node(under))
		return out

	def _speak_limit_target(self, nodes):
		# 0⁺ → "μηδέν από δεξιά", 0⁻ → "μηδέν από αριστερά"
		if len(nodes) == 1 and nodes[0].tag == "msup":
			base, sup = nodes[0].child(0), nodes[0].child(1)
			sign = sup.token_text().strip() if sup is not None else ""
			if sign in ("+",):
				out = self._node(base)
				out.append("από δεξιά")
				return out
			if sign in ("−", "-"):
				out = self._node(base)
				out.append("από αριστερά")
				return out
		return self._sequence(nodes)

	def _speak_munder(self, node):
		limit = self._limit(node)
		if limit is not None:
			return limit
		big = self._big_operator(node)
		if big is not None:
			return big
		base, under = node.child(0), node.child(1)
		if base is None or under is None:
			return self._sequence(node.children)
		out = self._node(base)
		out.append("με κάτω")
		out.extend(self._node(under))
		return out

	def _speak_mover(self, node):
		base, over = node.child(0), node.child(1)
		if base is None or over is None:
			return self._sequence(node.children)
		accent = _ACCENTS_OVER.get(over.token_text().strip())
		# Περιοδικός δεκαδικός: 0,3̄ → "3 περιοδικό"
		if accent == "παύλα" and base.tag == "mn":
			out = self._node(base)
			out.append("περιοδικό")
			return out
		if accent == "διάνυσμα":
			out = ["διάνυσμα"]
			out.extend(self._node(base))
			return out
		if accent == "τόξο":
			out = ["τόξο"]
			out.extend(self._node(base))
			return out
		if accent is not None:
			out = self._node(base)
			out.append(accent)
			return out
		out = self._node(base)
		out.append("με πάνω")
		out.extend(self._node(over))
		return out

	def _speak_munderover(self, node):
		big = self._big_operator(node)
		if big is not None:
			return big
		base, under, over = node.child(0), node.child(1), node.child(2)
		if base is None or under is None or over is None:
			return self._sequence(node.children)
		out = self._node(base)
		out.append("με κάτω")
		out.extend(self._node(under))
		out.append("και πάνω")
		out.extend(self._node(over))
		return out

	# ------------------------------------------------------------------
	# Πίνακες, ορίζουσες, συστήματα
	# ------------------------------------------------------------------

	def _table_dimensions(self, table):
		rows = [child for child in table.children if child.tag in ("mtr", "mlabeledtr")]
		max_columns = 0
		for row in rows:
			cells = [c for c in row.children if c.tag == "mtd"]
			max_columns = max(max_columns, len(cells))
		return rows, max_columns

	def _table_with_fences(self, table, open_char):
		rows, columns = self._table_dimensions(table)
		row_count = len(rows)
		if open_char == "|":
			kind, end = "ορίζουσα", "τέλος ορίζουσας"
		elif open_char == "‖":
			kind, end = "νόρμα πίνακα", "τέλος νόρμας"
		elif open_char == "{":
			return self._cases(table)
		else:
			if row_count == 1 or columns == 1:
				return self._vector(rows, columns)
			kind, end = "πίνακας", "τέλος πίνακα"
		out = [kind, f"{row_count} επί {columns}", Pause(MEDIUM)]
		out.extend(self._table_rows(rows))
		out.append(Pause(SHORT))
		out.append(end)
		return out

	def _vector(self, rows, columns):
		count = max(len(rows), columns)
		orientation = "γραμμή" if len(rows) == 1 else "στήλη"
		out = [f"διάνυσμα {orientation} με {count} στοιχεία", Pause(MEDIUM)]
		first = True
		for row in rows:
			for cell in row.children:
				if cell.tag != "mtd":
					continue
				if not first:
					out.append(Pause(MEDIUM))
				out.extend(self._sequence(cell.children))
				first = False
		out.append(Pause(SHORT))
		out.append("τέλος διανύσματος")
		return out

	def _table_rows(self, rows):
		out = []
		verbosity = self.config.verbosity
		for r, row in enumerate(rows, start=1):
			if r > 1:
				out.append(Pause(LONG))
			out.append(f"γραμμή {r}:")
			cells = [c for c in row.children if c.tag == "mtd"]
			for c, cell in enumerate(cells, start=1):
				if c > 1:
					out.append(Pause(MEDIUM))
				if verbosity == VERBOSE:
					out.append(f"στήλη {c}:")
				out.extend(self._sequence(cell.children))
		return out

	def _cases(self, table):
		rows, _ = self._table_dimensions(table)
		is_system = any(
			any(char in row.token_text() for char in "=<>≤≥")
			for row in rows
		)
		if is_system:
			label, item = f"σύστημα {len(rows)} εξισώσεων", "εξίσωση"
		else:
			label, item = f"{len(rows)} περιπτώσεις", "περίπτωση"
		out = [label, Pause(MEDIUM)]
		for r, row in enumerate(rows, start=1):
			if r > 1:
				out.append(Pause(LONG))
			out.append(f"{item} {r}:")
			cells = [c for c in row.children if c.tag == "mtd"]
			for c, cell in enumerate(cells):
				if c > 0:
					out.append(Pause(MEDIUM))
				out.extend(self._sequence(cell.children))
		out.append(Pause(SHORT))
		out.append("τέλος" if not is_system else "τέλος συστήματος")
		return out

	def _speak_mtable(self, node):
		# Πίνακας χωρίς σύμβολα ομαδοποίησης: πολύγραμμες εξισώσεις.
		rows, _ = self._table_dimensions(node)
		out = []
		for r, row in enumerate(rows, start=1):
			if r > 1:
				out.append(Pause(LONG))
			if self.config.verbosity == VERBOSE:
				out.append(f"γραμμή {r}:")
			for cell in row.children:
				if cell.tag == "mtd":
					out.extend(self._sequence(cell.children))
					out.append(Pause(SHORT))
		return out

	def _speak_mtr(self, node):
		out = []
		for cell in node.children:
			out.extend(self._node(cell))
			out.append(Pause(SHORT))
		return out

	def _speak_mtd(self, node):
		return self._sequence(node.children)

	# ------------------------------------------------------------------
	# Λοιπές δομές
	# ------------------------------------------------------------------

	def _speak_mmultiscripts(self, node):
		children = node.children
		if not children:
			return []
		base = children[0]
		post = []
		pre = []
		target = post
		i = 1
		while i < len(children):
			child = children[i]
			if child.tag == "mprescripts":
				target = pre
				i += 1
				continue
			pair = (child, children[i + 1] if i + 1 < len(children) else None)
			target.append(pair)
			i += 2
		out = []
		for sub, sup in pre:
			if sup is not None and sup.tag != "none":
				out.append("προεκθέτης")
				out.extend(self._node(sup))
			if sub is not None and sub.tag != "none":
				out.append("προδείκτης")
				out.extend(self._node(sub))
		out.extend(self._node(base))
		for sub, sup in post:
			if sub is not None and sub.tag != "none":
				out.append(grammar.SUBSCRIPT_WORD)
				out.extend(self._node(sub))
			if sup is not None and sup.tag != "none":
				power = grammar.power_reading(sup.token_text().strip())
				if power:
					out.append(power)
				else:
					out.append("υψωμένο σε")
					out.extend(self._node(sup))
		return out

	def _speak_menclose(self, node):
		notation = node.attrib.get("notation", "longdiv").split()
		labels = {
			"box": "σε πλαίσιο",
			"circle": "σε κύκλο",
			"roundedbox": "σε πλαίσιο",
			"updiagonalstrike": "διαγραμμένο",
			"downdiagonalstrike": "διαγραμμένο",
			"horizontalstrike": "διαγραμμένο",
			"verticalstrike": "διαγραμμένο",
			"radical": "ρίζα",
			"longdiv": "διαίρεση",
			"actuarial": "ασφαλιστικός συμβολισμός",
			"top": "με πάνω γραμμή",
			"bottom": "με κάτω γραμμή",
			"left": "με αριστερή γραμμή",
			"right": "με δεξιά γραμμή",
		}
		spoken = [labels[n] for n in notation if n in labels]
		out = []
		out.extend(spoken)
		out.extend(self._sequence(node.children))
		return out

	def _speak_merror(self, node):
		return self._sequence(node.children)

	def _speak_none(self, node):
		return []

	def _speak_mprescripts(self, node):
		return []


def _clone(node):
	"""Ρηχή αντιγραφή υποδέντρου (για εσωτερική αναδιάταξη στο msubsup)."""
	copy = MathNode(node.tag, dict(node.attrib), node.text)
	for child in node.children:
		copy.append(_clone(child))
	return copy


def _clean_tokens(tokens):
	"""Καθάρισμα: κενές συμβολοσειρές και διαδοχικές παύσεις συγχωνεύονται."""
	out = []
	for token in tokens:
		if isinstance(token, str):
			token = token.strip()
			if not token:
				continue
			out.append(token)
		elif isinstance(token, Pause):
			if out and isinstance(out[-1], Pause):
				out[-1] = Pause(max(out[-1].ms, token.ms))
			elif out:
				out.append(token)
	while out and isinstance(out[-1], Pause):
		out.pop()
	return out


def speak_node(node, config=None):
	"""Εκφώνηση ενός κόμβου του δέντρου (χρησιμοποιείται και στην πλοήγηση)."""
	return MathSpeaker(config).speak(node)


def speak_mathml(mathml, config=None):
	"""MathML → λίστα ελληνικών speech tokens."""
	tree = parse_mathml(mathml)
	return speak_node(tree, config)


def tokens_to_text(tokens):
	"""Μετατροπή tokens σε απλό κείμενο (για δοκιμές και προεπισκόπηση)."""
	parts = []
	for token in tokens:
		if isinstance(token, Pause):
			if token.ms >= MEDIUM and parts:
				parts[-1] = parts[-1] + ","
		else:
			parts.append(token)
	return " ".join(parts)
