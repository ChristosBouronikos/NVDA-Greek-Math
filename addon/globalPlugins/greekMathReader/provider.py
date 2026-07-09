# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.

"""NVDA math presentation provider backed by the Greek speech engine."""

import addonHandler
import config
import mathPres
from logHandler import log
from speech.commands import BreakCommand, LangChangeCommand

from .engine import MathMLParseError, Pause, ReadingConfig, speak_mathml

addonHandler.initTranslation()


def getReadingConfig():
	"""Build an engine ReadingConfig from the current NVDA configuration."""
	section = config.conf["greekMathReader"]
	return ReadingConfig(
		verbosity=int(section["verbosity"]),
		decimal_comma=bool(section["decimalComma"]),
	)


def tokensToSpeechSequence(tokens):
	"""Convert engine tokens (str | Pause) to an NVDA speech sequence."""
	sequence = []
	forceGreek = bool(config.conf["greekMathReader"]["forceGreekLanguage"])
	if forceGreek:
		sequence.append(LangChangeCommand("el"))
	for token in tokens:
		if isinstance(token, Pause):
			sequence.append(BreakCommand(time=token.ms))
		else:
			sequence.append(token)
	if forceGreek:
		sequence.append(LangChangeCommand(None))
	return sequence


class GreekMathProvider(mathPres.MathPresentationProvider):
	"""Speaks MathML in Greek and provides interactive navigation."""

	def getSpeechForMathMl(self, mathMl):
		try:
			tokens = speak_mathml(mathMl, getReadingConfig())
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
