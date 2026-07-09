# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.

"""Settings panel for the Greek Math Reader add-on."""

import addonHandler
import config
import gui
import wx
from gui.settingsDialogs import SettingsPanel

addonHandler.initTranslation()


class GreekMathSettingsPanel(SettingsPanel):
	# Translators: Title of the add-on settings panel.
	title = _("Greek Math Reader")

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		section = config.conf["greekMathReader"]

		self.enabledCheckbox = helper.addItem(
			# Translators: Label of a checkbox in the settings panel.
			wx.CheckBox(self, label=_("&Read mathematics in Greek (replaces the default math reader)"))
		)
		self.enabledCheckbox.SetValue(bool(section["enabled"]))

		self.verbosityChoice = helper.addLabeledControl(
			# Translators: Label of a combo box in the settings panel.
			_("Speech &verbosity:"),
			wx.Choice,
			choices=[
				# Translators: A verbosity level: minimal structural announcements.
				_("Terse (chi square)"),
				# Translators: A verbosity level: announcements only for complex structures.
				_("Smart — recommended (announces structure only when needed)"),
				# Translators: A verbosity level: full structural announcements.
				_("Verbose (full begin and end announcements)"),
			],
		)
		self.verbosityChoice.SetSelection(int(section["verbosity"]))

		self.decimalCommaCheckbox = helper.addItem(
			# Translators: Label of a checkbox in the settings panel.
			wx.CheckBox(self, label=_("Read the decimal &point as a Greek decimal comma (3.14 as 3,14)"))
		)
		self.decimalCommaCheckbox.SetValue(bool(section["decimalComma"]))

		self.forceGreekCheckbox = helper.addItem(
			# Translators: Label of a checkbox in the settings panel.
			wx.CheckBox(self, label=_("Switch the synthesizer &language to Greek while reading math"))
		)
		self.forceGreekCheckbox.SetValue(bool(section["forceGreekLanguage"]))

	def onSave(self):
		section = config.conf["greekMathReader"]
		wasEnabled = bool(section["enabled"])
		section["enabled"] = self.enabledCheckbox.GetValue()
		section["verbosity"] = self.verbosityChoice.GetSelection()
		section["decimalComma"] = self.decimalCommaCheckbox.GetValue()
		section["forceGreekLanguage"] = self.forceGreekCheckbox.GetValue()
		if wasEnabled != section["enabled"]:
			from . import applyProviderRegistration

			applyProviderRegistration()
