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

"""Settings panel for the Greek Math Reader add-on."""

import addonHandler
import config
import gui
import ui
import wx
from gui.settingsDialogs import SettingsPanel

addonHandler.initTranslation()


class GreekMathSettingsPanel(SettingsPanel):
	# Translators: Title of the add-on settings panel.
	title = _("Greek Math Reader")

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		section = config.conf["greekMathReader"]

		helper.addItem(
			wx.StaticText(
				self,
					# Translators: Explains why Greek does not appear in NVDA's built-in Math language list.
					label=_(
						"NVDA 2026.1.1 has no Automatic choice under Math; English is the "
						"normal MathCAT default. Greek Math Reader bypasses that language box."
					),
			)
		)

		helper.addItem(
			wx.StaticText(
				self,
					# Translators: Lists the NVDA settings automatically enforced by this add-on.
					label=_(
						"Required NVDA settings are enforced automatically: Automatic "
						"language switching is on, native Word/Outlook math is off, and "
						"Word UI Automation is Always."
					),
			)
		)

		helper.addItem(
			wx.StaticText(
				self,
				# Translators: Status shown because the add-on no longer permits another speech reader.
				label=_(
					"Greek Math Reader is the exclusive speech and interaction reader "
					"while it is installed."
				),
			)
		)

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

		self.unconfirmedBackupCheckbox = helper.addItem(
			# Translators: Label of a checkbox enabling the backup translation of
			# English math speech in Word when no equation can be confirmed.
			wx.CheckBox(
				self,
				label=_(
					"&Backup mode: translate English math speech in Word and Outlook "
					"even when the equation cannot be confirmed"
				),
			)
		)
		self.unconfirmedBackupCheckbox.SetValue(bool(section["translateUnconfirmedWordMath"]))

		self.testSpeechButton = helper.addItem(
			# Translators: Button that directly speaks a sample equation using the add-on's Greek engine.
			wx.Button(self, label=_("&Test Greek math speech"))
		)
		self.testSpeechButton.Bind(wx.EVT_BUTTON, self.onTestSpeech)

		self.resetButton = helper.addItem(
			# Translators: Resets add-on settings and repairs all exclusive provider hooks.
			wx.Button(self, label=_("&Reset settings and repair Greek math"))
		)
		self.resetButton.Bind(wx.EVT_BUTTON, self.onReset)

		self.copyDiagnosticsButton = helper.addItem(
			# Translators: Copies exact add-on, provider, equation exposure, and voice details.
			wx.Button(self, label=_("&Copy diagnostics"))
		)
		self.copyDiagnosticsButton.Bind(wx.EVT_BUTTON, self.onCopyDiagnostics)

	def onTestSpeech(self, event):
		from . import speakSelfTest

		speakSelfTest()

	def onReset(self, event):
		from . import resetRecommendedDefaults

		resetRecommendedDefaults()
		self.verbosityChoice.SetSelection(1)
		self.decimalCommaCheckbox.SetValue(True)
		self.unconfirmedBackupCheckbox.SetValue(True)
		# Translators: Announced after reset; Word must recreate its accessibility objects.
		ui.message(
			_(
				"Greek Math Reader reset and repaired. Restart NVDA and Microsoft Word "
				"before testing Word equations."
			)
		)

	def onCopyDiagnostics(self, event):
		from . import copyDiagnostics

		if copyDiagnostics():
			# Translators: Announced after a diagnostic report is placed on the clipboard.
			ui.message(_("Greek Math Reader diagnostics copied"))
		else:
			# Translators: Announced if the diagnostic report could not be copied.
			ui.message(_("Could not copy Greek Math Reader diagnostics"))

	def onSave(self):
		section = config.conf["greekMathReader"]
		section["enabled"] = True
		section["verbosity"] = self.verbosityChoice.GetSelection()
		section["decimalComma"] = self.decimalCommaCheckbox.GetValue()
		section["translateUnconfirmedWordMath"] = self.unconfirmedBackupCheckbox.GetValue()
		section["forceGreekLanguage"] = True
		# Reassert ownership whenever this panel is saved. This also repairs a
		# provider slot that changed while the dialog was open.
		from . import applyProviderRegistration

		applyProviderRegistration()
