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

"""Editable course pronunciation choices and user-reviewed local reports."""

import copy
import os
import unicodedata
from xml.sax.saxutils import escape

import addonHandler
import api
import gui
import speech
import ui
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .engine import speak_mathml
from .engine.symbols_el import (ALL_SYMBOLS, GREEK_LETTERS, GREEK_CAPITALS,
	LATIN_LETTERS, LATIN_CAPITALS, AMBIGUOUS_PRONUNCIATIONS,
	letter_reading, validate_pronunciations)
from .provider import tokensToSpeechSequence
from .settingsSupport import reading_report, report_mailto

addonHandler.initTranslation()


class PronunciationDialog(wx.Dialog):
	def __init__(self, parent, profiles, course, readingConfig):
		super().__init__(parent, title=_("Symbol pronunciations by course"), size=(650, 650), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.profiles = copy.deepcopy(profiles)
		self.course = course
		self.profiles.setdefault(course, {})
		self.readingConfig = readingConfig
		self._symbol = None
		sizer = wx.BoxSizer(wx.VERTICAL)
		body = ScrolledPanel(self)
		contentSizer = wx.BoxSizer(wx.VERTICAL)
		helper = gui.guiHelper.BoxSizerHelper(body, sizer=contentSizer)
		note = helper.addItem(wx.StaticText(body, label=_("Pronunciations change symbol names only. Mathematical meanings and Greek prose stay separate. Custom names also apply in literal-letter mode.")))
		note.Wrap(580)
		self.courses = helper.addLabeledControl(_("Course:"), wx.Choice, choices=sorted(self.profiles))
		self.courses.SetStringSelection(course)
		self.courses.Bind(wx.EVT_CHOICE, self.onCourse)
		add = helper.addItem(wx.Button(body, label=_("New course...")))
		add.Bind(wx.EVT_BUTTON, self.onNewCourse)
		self.search = helper.addLabeledControl(_("Search symbol or name:"), wx.TextCtrl)
		self.ambiguous = helper.addItem(wx.CheckBox(body, label=_("Show ambiguous symbols only")))
		self.symbols = helper.addLabeledControl(_("Symbol (Latin and Greek letters are distinct):"), wx.ListBox, choices=[])
		self.name = helper.addLabeledControl(_("Spoken name (editable suggestions):"), wx.ComboBox, choices=[])
		self.search.Bind(wx.EVT_TEXT, self.onFilter)
		self.ambiguous.Bind(wx.EVT_CHECKBOX, self.onFilter)
		self.symbols.Bind(wx.EVT_LISTBOX, self.onSymbol)
		for label, handler in ((_("Listen to symbol"), self.onListen), (_("Reset selected symbol"), self.onReset)):
			button = helper.addItem(wx.Button(body, label=label))
			button.Bind(wx.EVT_BUTTON, handler)
		body.SetSizer(contentSizer)
		body.SetupScrolling(scroll_x=False)
		sizer.Add(body, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
		self.SetSizer(sizer)
		self.SetMinSize((600, 450))
		self.onFilter(None)

	def _defaultName(self):
		if self._symbol == "∇":
			return self.readingConfig.gradient_name
		return (letter_reading(self._symbol, latin_literal=self.readingConfig.latin_literal)
			or ALL_SYMBOLS.get(self._symbol)
			or next(iter(AMBIGUOUS_PRONUNCIATIONS.get(self._symbol, ())), ""))

	def _storeEdit(self):
		if self._symbol is None or self.name.GetValue() == self._initialName:
			return True
		accepted = validate_pronunciations({self._symbol: self.name.GetValue()})
		if not accepted:
			ui.message(_("Enter a spoken name of 1 to 100 characters without line breaks."))
			return False
		self.profiles[self.course].update(accepted)
		self._initialName = self.name.GetValue()
		return True

	def onFilter(self, event):
		if not self._storeEdit():
			return
		query = self.search.GetValue().strip()
		allSymbols = set(ALL_SYMBOLS) | set(AMBIGUOUS_PRONUNCIATIONS) | set(GREEK_LETTERS) | set(GREEK_CAPITALS) | set(LATIN_LETTERS) | set(LATIN_CAPITALS)
		pool = set(AMBIGUOUS_PRONUNCIATIONS) if self.ambiguous.GetValue() else allSymbols
		labels = {symbol: f"{symbol} — {unicodedata.name(symbol, '')} — {letter_reading(symbol) or ALL_SYMBOLS.get(symbol, '')}"
			for symbol in pool if len(symbol) == 1}
		# A one-character search is exact, preserving G/g and Γ/γ distinctions.
		self._visible = sorted(symbol for symbol, label in labels.items()
			if not query or (symbol == query if len(query) == 1 else query.casefold() in label.casefold()))
		self.symbols.Set([labels[symbol] for symbol in self._visible])
		self._symbol = None
		if self._visible:
			self.symbols.SetSelection(0)
		self.onSymbol(None)

	def onSymbol(self, event):
		if not self._storeEdit():
			return
		index = self.symbols.GetSelection()
		self._symbol = self._visible[index] if index != wx.NOT_FOUND else None
		choices = AMBIGUOUS_PRONUNCIATIONS.get(self._symbol, ())
		self.name.Set(list(choices))
		default = self._defaultName()
		self._initialName = self.profiles[self.course].get(self._symbol, default)
		self.name.SetValue(self._initialName)

	def onCourse(self, event):
		if not self._storeEdit():
			self.courses.SetStringSelection(self.course)
			return
		self.course = self.courses.GetStringSelection()
		self._symbol = None
		self.onSymbol(None)

	def onNewCourse(self, event):
		if not self._storeEdit():
			return
		with wx.TextEntryDialog(self, _("Course name:"), _("New course")) as dialog:
			if dialog.ShowModal() != wx.ID_OK:
				return
			name = dialog.GetValue().strip()
		if not name or len(name) > 80 or any(ord(c) < 32 for c in name):
			ui.message(_("Enter a course name of 1 to 80 characters."))
			return
		self.profiles.setdefault(name, {})
		self.courses.Set(sorted(self.profiles))
		self.courses.SetStringSelection(name)
		self.onCourse(None)

	def onListen(self, event):
		if self._symbol is None:
			return
		values = validate_pronunciations({self._symbol: self.name.GetValue()})
		if not values:
			ui.message(_("Enter a spoken name of 1 to 100 characters without line breaks."))
			return
		settings = copy.copy(self.readingConfig)
		settings.symbol_pronunciations = values
		source = '<math><mi>' + escape(self._symbol) + '</mi></math>'
		speech.speak(tokensToSpeechSequence(speak_mathml(source, settings), settings))

	def onReset(self, event):
		if self._symbol is not None:
			self.profiles[self.course].pop(self._symbol, None)
			self._initialName = self._defaultName()
			self.name.SetValue(self._initialName)

	def onOK(self, event):
		if self._storeEdit():
			self.EndModal(wx.ID_OK)


class ReadingReportDialog(wx.Dialog):
	def __init__(self, parent, reading):
		super().__init__(parent, title=_("Report a reading problem"), size=(700, 650), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.reading = copy.deepcopy(reading)
		sizer = wx.BoxSizer(wx.VERTICAL)
		body = ScrolledPanel(self)
		contentSizer = wx.BoxSizer(wx.VERTICAL)
		helper = gui.guiHelper.BoxSizerHelper(body, sizer=contentSizer)
		note = helper.addItem(wx.StaticText(body, label=_("Review the expression and log below. Email opens a draft to cbouronikos@uth.gr in your mail app; you decide when to send it.")))
		note.Wrap(580)
		self.expected = helper.addLabeledControl(_("Expected speech:"), wx.TextCtrl, style=wx.TE_MULTILINE)
		self.notes = helper.addLabeledControl(_("Your message:"), wx.TextCtrl, style=wx.TE_MULTILINE)
		self.report = helper.addLabeledControl(_("Local report:"), wx.TextCtrl, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 250))
		self.expected.Bind(wx.EVT_TEXT, self.onUpdate)
		self.notes.Bind(wx.EVT_TEXT, self.onUpdate)
		for label, handler in ((_("Copy report"), self.onCopy), (_("Save report..."), self.onSave), (_("Open email draft"), self.onEmail)):
			button = helper.addItem(wx.Button(body, label=label))
			button.Bind(wx.EVT_BUTTON, handler)
		body.SetSizer(contentSizer)
		body.SetupScrolling(scroll_x=False)
		sizer.Add(body, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		sizer.Add(self.CreateButtonSizer(wx.CLOSE), flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
		self.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_CLOSE), id=wx.ID_CLOSE)
		self.SetSizer(sizer)
		self.SetMinSize((600, 450))
		self.onUpdate(None)

	def onUpdate(self, event):
		self.report.ChangeValue(reading_report(self.reading, self.expected.GetValue(), self.notes.GetValue()))

	def onCopy(self, event):
		ui.message(_("Copied") if api.copyToClip(self.report.GetValue()) else _("Could not copy the report"))

	def onSave(self, event):
		with wx.FileDialog(self, _("Save reading report"), defaultFile="greek-math-reading-report.txt",
			wildcard=_("Text files (*.txt)|*.txt"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
			if dialog.ShowModal() != wx.ID_OK:
				return
			try:
				with open(dialog.GetPath(), "w", encoding="utf-8") as destination:
					destination.write(self.report.GetValue())
			except OSError:
				ui.message(_("Could not save the report"))

	def onEmail(self, event):
		report = self.report.GetValue()
		url = report_mailto(report)
		if len(url) > 1800:
			# Windows mail handlers impose differing URL limits. Never truncate a log.
			if not api.copyToClip(report):
				ui.message(_("Could not copy the report. Save it and attach it to your email."))
				return
			url = report_mailto(_("Please paste the copied reading report here. You can add your own message before sending."))
			ui.message(_("The full report is copied. Paste it into the email draft with Control+V; you can add your own message."))
		try:
			os.startfile(url)
		except (OSError, AttributeError):
			ui.message(_("Could not open a mail app. Copy or save the report and email it to cbouronikos@uth.gr."))
