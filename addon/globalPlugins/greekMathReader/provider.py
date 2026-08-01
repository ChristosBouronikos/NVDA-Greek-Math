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


def getReadingConfig():
	"""Build an engine ReadingConfig from the current NVDA configuration."""
	section = config.conf["greekMathReader"]
	overrides = section.get("terminologyOverrides", "{}")
	if isinstance(overrides, str):
		try:
			overrides = json.loads(overrides)
		except (TypeError, ValueError):
			overrides = {}
	if not isinstance(overrides, dict):
		overrides = {}
	overrides, _rejected = validate_overrides(overrides)
	return ReadingConfig(
		verbosity=int(section["verbosity"]),
		decimal_comma=bool(section["decimalComma"]),
		terminology_profile=section.get("terminologyProfile", "standard"),
		domain_hint=section.get("domainHint", "auto"),
		relative_rate=int(section.get("relativeRate", 100)),
		pause_factor=int(section.get("pauseFactor", 50)),
		terminology_overrides=overrides,
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


_hasWarnedLanguageSwitchingOff = False
_hasWarnedGreekVoiceUnavailable = False


def getGreekVoiceSupport():
	"""Return whether the current synthesizer can switch to a Greek voice.

	``None`` means the capability could not be queried (for example during
	startup or in the platform-independent test suite).
	"""
	try:
		import synthDriverHandler

		synth = synthDriverHandler.getSynth()
		if synth is None:
			return None
		return bool(synth.languageIsSupported(GREEK_LOCALE))
	except Exception:
		return None


def tokensToSpeechSequence(tokens):
	"""Convert engine tokens (str | Pause) to an NVDA speech sequence."""
	global _hasWarnedLanguageSwitchingOff, _hasWarnedGreekVoiceUnavailable
	sequence = []
	forceGreek = bool(config.conf["greekMathReader"]["forceGreekLanguage"])
	if forceGreek and not isAutoLanguageSwitchingEnabled() and not _hasWarnedLanguageSwitchingOff:
		log.warning(
			"Greek Math Reader: NVDA's 'Automatic language switching' speech "
			"setting is disabled, so the Greek language tag on math speech is "
			"discarded and the current voice reads it with its own language. "
			"Enable it in NVDA menu -> Preferences -> Settings -> Speech."
		)
		_hasWarnedLanguageSwitchingOff = True
	greekVoiceSupport = getGreekVoiceSupport()
	if forceGreek and greekVoiceSupport is False and not _hasWarnedGreekVoiceUnavailable:
		log.warning(
			"Greek Math Reader: the current synthesizer has no installed Greek "
			"voice (el_GR); Greek text will be pronounced by the current voice"
		)
		_hasWarnedGreekVoiceUnavailable = True
	richTokens = list(tokens)
	if not any(isinstance(token, Language) for token in richTokens):
		richTokens = enrich_speech(richTokens, getReadingConfig())
	for token in richTokens:
		if isinstance(token, Pause):
			sequence.append(BreakCommand(time=token.ms))
		elif isinstance(token, Language):
			if forceGreek:
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
		if automaticBackend.usingMathCat:
			try:
				sequence = automaticBackend.getSpeechForMathMl(mathMl)
				if sequence is not None:
					self.lastBackend = "mathcat-el"
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
			return tokensToSpeechSequence(tokens)
		except MathMLParseError as error:
			log.error(f"Greek Math Reader: invalid MathML: {error}\n{mathMl}")
			# Translators: Spoken when the MathML markup of an equation cannot be parsed.
			return [_("Invalid mathematical content")]
		except Exception:
			log.exception(f"Greek Math Reader: error speaking MathML:\n{mathMl}")
			# Translators: Spoken when an unexpected error occurs while reading an equation.
			return [_("Error reading mathematical content")]

	def interactWithMathMl(self, mathMl):
		if automaticBackend.usingMathCat:
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
