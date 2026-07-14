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

"""Interactive navigation of math expressions.

Entered with NVDA+Alt+M (NVDA's standard "interact with math" command).
Arrow keys walk the expression tree:
	down  — into the current part (e.g. into the numerator)
	up    — out to the containing part
	left/right — previous/next sibling part
	home  — back to the whole expression
	space — repeat the current part
	escape — exit interaction (handled by the base class)
"""

import addonHandler
import api
import mathPres
import speech
import tones
import ui
from scriptHandler import script

from .engine import parse_mathml, role_description, speak_node
from .provider import getReadingConfig, tokensToSpeechSequence

addonHandler.initTranslation()


class GreekMathInteraction(mathPres.MathInteractionNVDAObject):
	"""Tree-walking interaction for a math expression, announced in Greek."""

	def __init__(self, provider=None, mathMl=None, tree=None):
		super().__init__(provider=provider, mathMl=mathMl)
		self.tree = tree if tree is not None else parse_mathml(mathMl)
		# Ξεκινάμε από το πρώτο ουσιαστικό επίπεδο κάτω από το <math>.
		self.pointer = self.tree.children[0] if len(self.tree.children) == 1 else self.tree

	def event_gainFocus(self):
		# Translators: Announced when entering math interaction mode.
		ui.message(_("Math interaction. Use the arrow keys to explore, escape to exit."))
		self._speakPointer(includeRole=False)

	def _speakPointer(self, includeRole=True):
		tokens = []
		if includeRole:
			role = role_description(self.pointer)
			if role:
				tokens.append(role + ":")
		tokens.extend(speak_node(self.pointer, getReadingConfig()))
		speech.speak(tokensToSpeechSequence(tokens))

	def _move(self, target, edgeMessage):
		if target is None:
			tones.beep(200, 60)
			ui.message(edgeMessage)
			return
		self.pointer = target
		self._speakPointer()

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move into the current part of the expression"),
		gesture="kb:downArrow",
	)
	def script_moveIn(self, gesture):
		children = self.pointer.children
		# Translators: Announced when the current math part has no inner parts.
		self._move(children[0] if children else None, _("No inner parts"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move out to the containing part of the expression"),
		gesture="kb:upArrow",
	)
	def script_moveOut(self, gesture):
		parent = self.pointer.parent
		# Translators: Announced when already at the outermost math part.
		self._move(parent, _("At the outermost level"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move to the next part of the expression"),
		gesture="kb:rightArrow",
	)
	def script_moveNext(self, gesture):
		# Translators: Announced when there is no next math part.
		self._move(self.pointer.next_sibling(), _("End"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move to the previous part of the expression"),
		gesture="kb:leftArrow",
	)
	def script_movePrevious(self, gesture):
		# Translators: Announced when there is no previous math part.
		self._move(self.pointer.previous_sibling(), _("Start"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Return to the whole expression"),
		gesture="kb:home",
	)
	def script_moveToRoot(self, gesture):
		self.pointer = self.tree.children[0] if len(self.tree.children) == 1 else self.tree
		self._speakPointer(includeRole=False)

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Repeat the current part of the expression"),
		gesture="kb:space",
	)
	def script_repeat(self, gesture):
		self._speakPointer()

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Copy the Greek reading of the expression to the clipboard"),
		gesture="kb:control+c",
	)
	def script_copyReading(self, gesture):
		from .engine import tokens_to_text

		text = tokens_to_text(speak_node(self.pointer, getReadingConfig()))
		if api.copyToClip(text):
			# Translators: Announced when the reading of the expression was copied.
			ui.message(_("Copied"))
