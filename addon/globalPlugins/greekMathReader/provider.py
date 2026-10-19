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

import json
import re

import addonHandler
import config
import mathPres
from logHandler import log
from speech.commands import BreakCommand, LangChangeCommand

try:
	from speech.commands import RateCommand
except ImportError:  # NVDA versions without relative-rate speech commands.
	RateCommand = None

from .backend import automaticBackend
from .engine import (
	MathMLParseError,
	Language,
	NavigationMark,
	Pause,
	Prosody,
	ReadingConfig,
	enrich_speech,
	get_last_engine_diagnostics,
	normalize_equation_boundary,
	speak_mathml,
)
from .engine.terminology_el import validate_overrides

addonHandler.initTranslation()

GREEK_LOCALE = "el_GR"

# Speech-only pronunciation overrides.
#
# Several Greek letter names are two-character monosyllables (ψι, χι, φι …).
# The Windows OneCore Greek voice (Microsoft Stefanos) tends to *spell* such a
# short, unaccented token letter by letter — "ψι" comes out as "ψι γιώτα"
# (psi + iota) instead of the single syllable "psi". Adding the tonos accent
# forces the synthesizer to read each as one word.
#
# This map is applied ONLY to the speech sequence handed to NVDA. The engine's
# own tokens stay unaccented, so the clipboard reading (Ctrl+C in interaction
# mode), the unit tests and any future braille keep the orthographically
# correct monosyllabic spelling. "σε" is deliberately excluded because it also
# occurs as the Greek preposition "σε" inside "υψωμένο σε" (raised to).
SPEECH_PRONUNCIATION = {
	"βε": "βέ", "ζε": "ζέ", "ζι": "ζί", "μι": "μί", "νι": "νί",
	"ξι": "ξί", "ου": "ού", "πι": "πί", "ρο": "ρό", "σι": "σί",
	"φι": "φί", "χι": "χί", "ψι": "ψί",
}
_PRONUNCIATION_RE = re.compile(
	r"\b(" + "|".join(re.escape(word) for word in SPEECH_PRONUNCIATION) + r")\b"
)


def _applyPronunciation(text):
	"""Respell short Greek letter names so the synthesizer speaks them as words."""
	return _PRONUNCIATION_RE.sub(lambda match: SPEECH_PRONUNCIATION[match.group(1)], text)


def getReadingConfig(section=None):
	"""Build an engine ReadingConfig from the current NVDA configuration."""
	section = config.conf["greekMathReader"] if section is None else section
	overrides = section.get("terminologyOverrides", "{}")
	if isinstance(overrides, str):
		try:
			overrides = json.loads(overrides)
		except (TypeError, ValueError):
			overrides = {}
	if not isinstance(overrides, dict):
		overrides = {}
	overrides, _rejected = validate_overrides(overrides)
	profiles = section.get("symbolPronunciations", "{}")
	try:
		profiles = json.loads(profiles) if isinstance(profiles, str) else profiles
	except (TypeError, ValueError):
		profiles = {}
	pronunciations = profiles.get(section.get("pronunciationCourse", "Default"), {}) if isinstance(profiles, dict) else {}
	return ReadingConfig(
		announce_capitals=bool(section.get("announceCapitals", False)),
		symbol_pronunciations=pronunciations,
		gradient_name=section.get("gradientName", "ανάδελτα"),
		explain_composition=bool(section.get("explainComposition", False)),
		matrix_reading=section.get("matrixReading", "whole"),
		matrix_positions=bool(section.get("matrixPositions", False)),
		boundary_sound=int(section.get("boundarySound", 100)),
		verbosity=int(section["verbosity"]),
		decimal_comma=bool(section["decimalComma"]),
		decimal_digits=bool(section.get("decimalDigits", False)),
		terminology_profile=section.get("terminologyProfile", "standard"),
		domain_hint=section.get("domainHint", "auto"),
		relative_rate=int(section.get("relativeRate", 100)),
		pause_factor=int(section.get("pauseFactor", 50)),
		terminology_overrides=overrides,
		latin_literal=section.get("latinLetterMode", "greek_school") == "literal",
	)


def isAutoLanguageSwitchingEnabled():
	"""Whether NVDA honours LangChangeCommand in speech sequences.

	NVDA silently drops every LangChangeCommand when the user has disabled
	"Automatic language switching" in its speech settings, in which case the
	Greek language tag this add-on emits can never reach the synthesizer.
	"""
	try:
		return bool(config.conf["speech"]["autoLanguageSwitching"])
	except KeyError:
		return True


_warnedLanguageSwitchingOffForSynths = set()
_warnedGreekVoiceUnavailableForSynths = set()


def getGreekVoiceSupport():
	"""Return whether the current synthesizer advertises a Greek voice.

	Inventory support does not prove voice switching or successful audio.

	``None`` means the capability could not be queried (for example during
	startup or in the platform-independent test suite).
	"""
	try:
		import synthDriverHandler

		synth = synthDriverHandler.getSynth()
		if synth is None:
			return None
		checker = getattr(synth, "languageIsSupported", None)
		if callable(checker):
			return bool(checker(GREEK_LOCALE))
		# NVDA 2024.x drivers do not all expose languageIsSupported. Query
		# public voice metadata instead, independent of the driver/architecture.
		languages = getattr(synth, "availableLanguages", None)
		if languages is None:
			voices = getattr(synth, "availableVoices", None)
			if voices is None:
				return None
			languages = [getattr(voice, "language", None) for voice in voices.values()]
		return any(
			isinstance(language, str) and language.lower().replace("-", "_").split("_")[0] == "el"
			for language in languages
		)
	except Exception:
		return None


def tokensToSpeechSequence(tokens, readingConfig=None):
	"""Convert engine tokens (str | Pause) to an NVDA speech sequence."""
	tokens = [
		normalize_equation_boundary(token) if isinstance(token, str) else token
		for token in tokens
	]
	sequence = []
	forceGreek = bool(config.conf["greekMathReader"]["forceGreekLanguage"])
	try:
		import synthDriverHandler
		synth = synthDriverHandler.getSynth()
		warningKey = (id(synth), getattr(synth, "name", None), str(getattr(synth, "voice", None)))
	except Exception:
		warningKey = None
	if forceGreek and not isAutoLanguageSwitchingEnabled() and warningKey not in _warnedLanguageSwitchingOffForSynths:
		log.warning(
			"Greek Math Reader: NVDA's 'Automatic language switching' speech "
			"setting is disabled, so the Greek language tag on math speech is "
			"discarded and the current voice reads it with its own language. "
			"Enable it in NVDA menu -> Preferences -> Settings -> Speech."
		)
		_warnedLanguageSwitchingOffForSynths.add(warningKey)
	greekVoiceSupport = getGreekVoiceSupport()
	if forceGreek and greekVoiceSupport is False and warningKey not in _warnedGreekVoiceUnavailableForSynths:
		log.warning(
			"Greek Math Reader: the current synthesizer has no installed Greek "
			"voice (el_GR); select or install a Greek voice for this synthesizer. "
			"Unsupported Greek language commands will not be sent."
		)
		_warnedGreekVoiceUnavailableForSynths.add(warningKey)
	richTokens = list(tokens)
	if not any(isinstance(token, Language) for token in richTokens):
		richTokens = enrich_speech(richTokens, readingConfig or getReadingConfig())
	for token in richTokens:
		if isinstance(token, Pause):
			sequence.append(BreakCommand(time=token.ms))
		elif isinstance(token, Language):
			if forceGreek and greekVoiceSupport is not False:
				locale = GREEK_LOCALE if token.locale else None
				sequence.append(LangChangeCommand(locale))
		elif isinstance(token, Prosody):
			if RateCommand is not None:
				sequence.append(RateCommand(multiplier=token.relative_rate / 100.0))
		elif isinstance(token, NavigationMark):
			continue
		elif isinstance(token, str):
			sequence.append(_applyPronunciation(token))
		else:
			sequence.append(token)
	return sequence


# Only the most recently read expression is retained, in memory, for Settings.
# Previews never overwrite this record or trigger provider repair.
lastReading = None


def rememberReading(source, inputFormat, sequence, backend="local", section=None):
	global lastReading
	try:
		import synthDriverHandler
		synth = synthDriverHandler.getSynth()
	except Exception:
		synth = None
	try:
		# NVDA's AggregatedSection iterates keys but has no keys() method.
		# dict(section) treats those strings as key/value pairs and raises.
		# Its public items() API works for both NVDA sections and plain dicts.
		section = dict((config.conf["greekMathReader"] if section is None else section).items())
		lastReading = {
			"expression": source, "format": inputFormat,
			"actualSpeech": " ".join(item for item in sequence if isinstance(item, str)), "backend": backend,
			"preset": section.get("terminologyProfile", "standard"),
			"context": section.get("domainHint", "auto"),
			"voice": str(getattr(synth, "voice", "unavailable")),
			"synthesizer": str(getattr(synth, "name", "unavailable")),
			"settings": section,
		}
	except Exception as error:
		# This optional Settings record must never prevent speech, including
		# the error announcement produced when equation rendering itself fails.
		lastReading = None
		log.warning(f"Greek Math Reader: could not record last reading; speech continues: {error!r}")


def _localPreferencesRequired(mathMl=""):
	settings = getReadingConfig()
	# MathCAT's delegate has no contract for these local pronunciation/navigation options.
	return (re.search(r"∇|&#(?:8711|x2207);|&(?:nabla|Del);|grad|quotient[-_]group", mathMl, re.I) is not None
		or settings.announce_capitals or settings.symbol_pronunciations
		or settings.explain_composition or settings.matrix_reading != "whole"
		or settings.matrix_positions or settings.boundary_sound != 100
		or settings.gradient_name != "ανάδελτα" or settings.decimal_digits
		or settings.verbosity != 1 or not settings.decimal_comma
		or settings.terminology_profile != "standard" or settings.domain_hint != "auto"
		or settings.terminology_overrides
		or settings.latin_literal or settings.relative_rate != 100 or settings.pause_factor != 50)


class GreekMathProvider(mathPres.MathPresentationProvider):
	"""Speaks MathML in Greek and provides interactive navigation."""
	_hasLoggedFirstSpeech = False
	speechRequestCount = 0
	lastInputDiagnostic = "No MathML received."
	lastEngineDiagnostic = "No local-engine speech has been generated."
	lastBackend = "local"

	def configureMathCatDelegate(self, delegate=None):
		section = config.conf["greekMathReader"]
		return automaticBackend.configure(
			delegate,
			enabled=bool(section.get("autoMathCatBackend", True)),
		)

	@property
	def usingMathCatBackend(self):
		return automaticBackend.usingMathCat

	def getSpeechForMathMl(self, mathMl):
		self.speechRequestCount += 1
		if automaticBackend.usingMathCat and not _localPreferencesRequired(mathMl):
			try:
				sequence = automaticBackend.getSpeechForMathMl(mathMl)
				if sequence is not None:
					if config.conf["greekMathReader"]["forceGreekLanguage"]:
						# Keep delegate language resets from overriding our scoped Greek tag.
						sequence = [item for item in sequence if not isinstance(item, LangChangeCommand)]
					sequence = tokensToSpeechSequence(sequence)
					if not any(isinstance(item, str) and item.strip() for item in sequence):
						raise ValueError("MathCAT returned no speakable text")
					self.lastBackend = "mathcat-el"
					rememberReading(mathMl, "mathml", sequence, "mathcat-el")
					return sequence
			except Exception:
				log.exception("Greek Math Reader: MathCAT Greek backend failed; using local engine")
			automaticBackend.configure(None, enabled=False)
		mathMlText = mathMl if isinstance(mathMl, str) else repr(mathMl)
		preview = re.sub(r"\s+", " ", mathMlText).strip()
		if len(preview) > 220:
			preview = preview[:217] + "..."
		lowerMathMl = mathMlText.lower()
		structuralTagPattern = r"<(?:\w+:)?(?:mfrac|msup|msub|msubsup|mroot|msqrt|mtable|munderover|mover|munder)\b"
		textOnly = bool(re.search(r"<(?:\w+:)?mtext\b", lowerMathMl)) and not bool(
			re.search(structuralTagPattern, lowerMathMl)
		)
		self.lastInputDiagnostic = (
			f"length={len(mathMlText)}; textOnlyOrAltText={textOnly}; preview={preview!r}"
		)
		if not self._hasLoggedFirstSpeech:
			log.info(
				"Greek Math Reader: received MathML for Greek speech; "
				+ self.lastInputDiagnostic
			)
			self._hasLoggedFirstSpeech = True
		try:
			tokens = speak_mathml(mathMl, getReadingConfig())
			self.lastBackend = "local"
			self.lastEngineDiagnostic = repr(get_last_engine_diagnostics())
			sequence = tokensToSpeechSequence(tokens)
			if not any(isinstance(item, str) and item.strip() for item in sequence):
				log.warning("Greek Math Reader: equation produced no speakable text; " + self.lastInputDiagnostic)
				sequence = tokensToSpeechSequence(["Δεν υπάρχει διαθέσιμο μαθηματικό περιεχόμενο για ανάγνωση."])
			rememberReading(mathMl, "mathml", sequence)
			return sequence
		except MathMLParseError as error:
			log.error(f"Greek Math Reader: invalid MathML: {error}\n{mathMl}")
			# Translators: Spoken when the MathML markup of an equation cannot be parsed.
			sequence = [_("Invalid mathematical content")]
			rememberReading(mathMl, "mathml", sequence)
			return sequence
		except Exception:
			log.exception(f"Greek Math Reader: error speaking MathML:\n{mathMl}")
			# Translators: Spoken when an unexpected error occurs while reading an equation.
			sequence = [_("Error reading mathematical content")]
			rememberReading(mathMl, "mathml", sequence)
			return sequence

	def interactWithMathMl(self, mathMl):
		if automaticBackend.usingMathCat and not _localPreferencesRequired(mathMl):
			interaction = getattr(automaticBackend.delegate, "interactWithMathMl", None)
			if callable(interaction):
				try:
					return interaction(mathMl)
				except Exception:
					log.exception("Greek Math Reader: MathCAT Greek interaction failed; using local navigation")
		# Imported lazily: interaction pulls in wx/NVDAObjects, which must not
		# load during add-on import.
		from .interaction import GreekMathInteraction

		try:
			interaction = GreekMathInteraction(provider=self, mathMl=mathMl)
		except MathMLParseError as error:
			import ui

			log.error(f"Greek Math Reader: invalid MathML: {error}\n{mathMl}")
			# Translators: Spoken when the MathML markup of an equation cannot be parsed.
			ui.message(_("Invalid mathematical content"))
			return
		interaction.setFocus()
