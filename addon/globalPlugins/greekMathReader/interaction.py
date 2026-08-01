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
	end   — last child of the current part
	backspace — return through navigation history
	control+arrows — move between table cells
	space — repeat the current part
	p     — announce position
	control+shift+c — copy structural MathML source
	escape — exit interaction (handled by the base class)
"""

import addonHandler
import api
import mathPres
import speech
import tones
import ui
from scriptHandler import script

from .engine import (
	mathnode_to_mathml,
	parse_mathml,
	role_description,
	semantic_navigation_children,
	speak_node,
)
from .provider import getReadingConfig, tokensToSpeechSequence

addonHandler.initTranslation()


class GreekMathInteraction(mathPres.MathInteractionNVDAObject):
	"""Tree-walking interaction for a math expression, announced in Greek."""

	def __init__(self, provider=None, mathMl=None, tree=None):
		super().__init__(provider=provider, mathMl=mathMl)
		self.tree = tree if tree is not None else parse_mathml(mathMl)
		# Ξεκινάμε από το πρώτο ουσιαστικό επίπεδο κάτω από το <math>.
		self.pointer = self.tree.children[0] if len(self.tree.children) == 1 else self.tree
		self._history = []
		self._semanticParents = {}
		self._semanticSiblingGroups = {}

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

	def _move(self, target, edgeMessage, remember=True):
		if target is None:
			tones.beep(200, 60)
			ui.message(edgeMessage)
			return
		if remember and target is not self.pointer:
			self._history.append(self.pointer)
		self.pointer = target
		self._speakPointer()

	def _root(self):
		return self.tree.children[0] if len(self.tree.children) == 1 else self.tree

	def _navigationChildren(self, node):
		children = semantic_navigation_children(node, getReadingConfig())
		if children != list(node.children):
			group = tuple(children)
			for child in children:
				self._semanticParents[id(child)] = node
				self._semanticSiblingGroups[id(child)] = group
		return children

	def _navigationParent(self, node):
		return self._semanticParents.get(id(node), node.parent)

	def _navigationSibling(self, offset):
		group = self._semanticSiblingGroups.get(id(self.pointer))
		if group is None:
			return self.pointer.previous_sibling() if offset < 0 else self.pointer.next_sibling()
		try:
			index = group.index(self.pointer) + offset
		except ValueError:
			return None
		return group[index] if 0 <= index < len(group) else None

	def _tablePosition(self):
		cell = self.pointer
		while cell is not None and cell.tag != "mtd":
			cell = cell.parent
		if cell is None or cell.parent is None or cell.parent.tag != "mtr":
			return None
		row = cell.parent
		table = row.parent
		if table is None or table.tag != "mtable":
			return None
		return table, row.index, cell.index

	def _moveTable(self, rowOffset, columnOffset):
		position = self._tablePosition()
		if position is None:
			self._move(None, _("Not in a table cell"))
			return
		table, rowIndex, columnIndex = position
		targetRow = table.child(rowIndex + rowOffset)
		targetCell = targetRow.child(columnIndex + columnOffset) if targetRow is not None else None
		self._move(targetCell, _("No table cell in that direction"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move into the current part of the expression"),
		gesture="kb:downArrow",
	)
	def script_moveIn(self, gesture):
		children = self._navigationChildren(self.pointer)
		# Translators: Announced when the current math part has no inner parts.
		self._move(children[0] if children else None, _("No inner parts"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move out to the containing part of the expression"),
		gesture="kb:upArrow",
	)
	def script_moveOut(self, gesture):
		parent = self._navigationParent(self.pointer)
		# Translators: Announced when already at the outermost math part.
		self._move(parent, _("At the outermost level"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move to the next part of the expression"),
		gesture="kb:rightArrow",
	)
	def script_moveNext(self, gesture):
		# Translators: Announced when there is no next math part.
		self._move(self._navigationSibling(1), _("End"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Move to the previous part of the expression"),
		gesture="kb:leftArrow",
	)
	def script_movePrevious(self, gesture):
		# Translators: Announced when there is no previous math part.
		self._move(self._navigationSibling(-1), _("Start"))

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Return to the whole expression"),
		gesture="kb:home",
	)
	def script_moveToRoot(self, gesture):
		target = self._root()
		if target is not self.pointer:
			self._history.append(self.pointer)
		self.pointer = target
		self._speakPointer(includeRole=False)

	@script(
		description=_("Move to the last inner part of the expression"),
		gesture="kb:end",
	)
	def script_moveToEnd(self, gesture):
		children = self._navigationChildren(self.pointer)
		self._move(children[-1] if children else None, _("No inner parts"))

	@script(
		description=_("Return to the previous navigation position"),
		gesture="kb:backspace",
	)
	def script_moveBack(self, gesture):
		if not self._history:
			self._move(None, _("No previous navigation position"))
			return
		self.pointer = self._history.pop()
		self._speakPointer()

	@script(description=_("Move to the table cell on the left"), gesture="kb:control+leftArrow")
	def script_tableLeft(self, gesture):
		self._moveTable(0, -1)

	@script(description=_("Move to the table cell on the right"), gesture="kb:control+rightArrow")
	def script_tableRight(self, gesture):
		self._moveTable(0, 1)

	@script(description=_("Move to the table cell above"), gesture="kb:control+upArrow")
	def script_tableUp(self, gesture):
		self._moveTable(-1, 0)

	@script(description=_("Move to the table cell below"), gesture="kb:control+downArrow")
	def script_tableDown(self, gesture):
		self._moveTable(1, 0)

	@script(
		# Translators: Describes a command in math interaction mode.
		description=_("Repeat the current part of the expression"),
		gesture="kb:space",
	)
	def script_repeat(self, gesture):
		self._speakPointer()

	@script(
		description=_("Announce the current position in the expression"),
		gesture="kb:p",
	)
	def script_reportPosition(self, gesture):
		tablePosition = self._tablePosition()
		if tablePosition is not None:
			_table, rowIndex, columnIndex = tablePosition
			ui.message(_("Row {row}, column {column}").format(
				row=rowIndex + 1,
				column=columnIndex + 1,
			))
			return
		parent = self._navigationParent(self.pointer)
		if parent is None:
			ui.message(_("Whole expression"))
			return
		group = self._semanticSiblingGroups.get(id(self.pointer))
		if group is not None:
			position = group.index(self.pointer) + 1
			total = len(group)
		else:
			position = self.pointer.index + 1
			total = len(parent.children)
		ui.message(_("Part {position} of {total}").format(position=position, total=total))

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

	@script(
		description=_("Copy the current expression as MathML source"),
		gesture="kb:control+shift+c",
	)
	def script_copySource(self, gesture):
		if api.copyToClip(mathnode_to_mathml(self.pointer)):
			ui.message(_("MathML source copied"))
