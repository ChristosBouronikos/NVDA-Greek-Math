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

"""Settings panel for the Greek Math Reader add-on."""

import json

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
					# Translators: Explains the read-only health check and explicit repair.
					label=_(
						"The health check reports settings that can block Greek math. "
						"Use Repair to change them explicitly."
					),
			)
		)
		from . import getHealthCheck

		health = getHealthCheck()
		self.healthStatus = helper.addItem(
			wx.StaticText(
				self,
				label=_("Health check: ready") if health["healthy"] else _("Health check: repair recommended"),
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

		self.terminologyProfileChoice = helper.addLabeledControl(
			_("Greek &terminology profile:"),
			wx.Choice,
			choices=[
				_("Standard (default)"),
				_("School"),
				_("University"),
			],
		)
		profile = section.get("terminologyProfile", "standard")
		self.terminologyProfileChoice.SetSelection(
			{"standard": 0, "school": 1, "university": 2}.get(profile, 0)
		)

		self.domainHintChoice = helper.addLabeledControl(
			_("Notation &context:"),
			wx.Choice,
			choices=[
				_("Automatic"), _("General mathematics"), _("Geometry"),
				_("Probability and statistics"), _("Linear algebra"),
				_("Vector calculus"), _("Physics"), _("Quantum physics"),
				_("Abstract algebra"),
			],
		)
		self._domainValues = (
			"auto", "general_math", "geometry", "probability_statistics",
			"linear_algebra", "vector_calculus", "physics", "quantum_physics", "algebra",
		)
		try:
			domainIndex = self._domainValues.index(section.get("domainHint", "auto"))
		except ValueError:
			domainIndex = 0
		self.domainHintChoice.SetSelection(domainIndex)

		self.relativeRateControl = helper.addLabeledControl(
			_("Relative math speech &rate (percent):"),
			wx.SpinCtrl,
			min=1,
			max=100,
			initial=int(section.get("relativeRate", 100)),
		)
		self.pauseFactorControl = helper.addLabeledControl(
			_("Math &pause factor:"),
			wx.SpinCtrl,
			min=0,
			max=100,
			initial=int(section.get("pauseFactor", 50)),
		)

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

		self.autoMathCatCheckbox = helper.addItem(
			wx.CheckBox(
				self,
				label=_("Use the installed MathCAT Greek backend automatically when available"),
			)
		)
		self.autoMathCatCheckbox.SetValue(bool(section.get("autoMathCatBackend", True)))

		try:
			self._terminologyOverrides = json.loads(section.get("terminologyOverrides", "{}"))
		except (TypeError, ValueError):
			self._terminologyOverrides = {}
		if not isinstance(self._terminologyOverrides, dict):
			self._terminologyOverrides = {}

		self.importTerminologyButton = helper.addItem(
			wx.Button(self, label=_("&Import personal terminology..."))
		)
		self.importTerminologyButton.Bind(wx.EVT_BUTTON, self.onImportTerminology)
		self.exportTerminologyButton = helper.addItem(
			wx.Button(self, label=_("E&xport personal terminology..."))
		)
		self.exportTerminologyButton.Bind(wx.EVT_BUTTON, self.onExportTerminology)
		self.clearTerminologyButton = helper.addItem(
			wx.Button(self, label=_("&Clear personal terminology"))
		)
		self.clearTerminologyButton.Bind(wx.EVT_BUTTON, self.onClearTerminology)
		self.resetTerminologyChoice = helper.addLabeledControl(
			_("Personal term to &reset:"),
			wx.Choice,
			choices=[],
		)
		self.resetSelectedTerminologyButton = helper.addItem(
			wx.Button(self, label=_("Reset &selected personal term"))
		)
		self.resetSelectedTerminologyButton.Bind(wx.EVT_BUTTON, self.onResetSelectedTerminology)
		self._refreshTerminologyChoices()

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
		self.repairButton = helper.addItem(
			wx.Button(self, label=_("&Repair required NVDA settings"))
		)
		self.repairButton.Bind(wx.EVT_BUTTON, self.onRepair)

		self.copyDiagnosticsButton = helper.addItem(
			# Translators: Copies exact add-on, provider, equation exposure, and voice details.
			wx.Button(self, label=_("&Copy diagnostics"))
		)
		self.copyDiagnosticsButton.Bind(wx.EVT_BUTTON, self.onCopyDiagnostics)

	def onTestSpeech(self, event):
		from . import speakSelfTest

		speakSelfTest()

	def _refreshTerminologyChoices(self):
		concepts = sorted(self._terminologyOverrides)
		self.resetTerminologyChoice.Set(concepts or [_('(no personal terms)')])
		self.resetTerminologyChoice.SetSelection(0)
		self.resetSelectedTerminologyButton.Enable(bool(concepts))

	def onImportTerminology(self, event):
		from .engine.terminology_el import validate_overrides

		dialog = wx.FileDialog(
			self,
			message=_("Import personal Greek math terminology"),
			wildcard=_("JSON files (*.json)|*.json"),
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		)
		try:
			if dialog.ShowModal() != wx.ID_OK:
				return
			with open(dialog.GetPath(), "r", encoding="utf-8") as source:
				loaded = json.load(source)
			accepted, rejected = validate_overrides(loaded)
			if rejected:
				ui.message(_("The terminology file contains invalid or unknown concept identifiers"))
				return
			self._terminologyOverrides = accepted
			self._refreshTerminologyChoices()
			ui.message(_("Personal terminology imported"))
		except (OSError, ValueError):
			ui.message(_("Could not import the terminology file"))
		finally:
			dialog.Destroy()

	def onExportTerminology(self, event):
		dialog = wx.FileDialog(
			self,
			message=_("Export personal Greek math terminology"),
			defaultFile="greek-math-terminology.json",
			wildcard=_("JSON files (*.json)|*.json"),
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
		)
		try:
			if dialog.ShowModal() != wx.ID_OK:
				return
			with open(dialog.GetPath(), "w", encoding="utf-8") as destination:
				json.dump(self._terminologyOverrides, destination, ensure_ascii=False, indent=2, sort_keys=True)
			ui.message(_("Personal terminology exported"))
		except OSError:
			ui.message(_("Could not export the terminology file"))
		finally:
			dialog.Destroy()

	def onClearTerminology(self, event):
		self._terminologyOverrides = {}
		self._refreshTerminologyChoices()
		ui.message(_("Personal terminology cleared"))

	def onResetSelectedTerminology(self, event):
		from .engine.terminology_el import reset_override

		concept = self.resetTerminologyChoice.GetStringSelection()
		self._terminologyOverrides, removed, _rejected = reset_override(
			self._terminologyOverrides,
			concept,
		)
		self._refreshTerminologyChoices()
		if removed:
			ui.message(_("Selected personal terminology reset"))
		else:
			ui.message(_("No personal terminology selected"))

	def onReset(self, event):
		from . import resetRecommendedDefaults

		resetRecommendedDefaults()
		self.verbosityChoice.SetSelection(1)
		self.decimalCommaCheckbox.SetValue(True)
		self.unconfirmedBackupCheckbox.SetValue(True)
		self.terminologyProfileChoice.SetSelection(0)
		self.domainHintChoice.SetSelection(0)
		self.relativeRateControl.SetValue(100)
		self.pauseFactorControl.SetValue(50)
		self.autoMathCatCheckbox.SetValue(True)
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

	def onRepair(self, event):
		from . import repairRequiredNvdaSettings

		repairRequiredNvdaSettings()
		self.healthStatus.SetLabel(_("Health check: ready"))
		ui.message(_("Required NVDA settings repaired"))

	def onSave(self):
		section = config.conf["greekMathReader"]
		section["enabled"] = True
		section["verbosity"] = self.verbosityChoice.GetSelection()
		section["decimalComma"] = self.decimalCommaCheckbox.GetValue()
		section["translateUnconfirmedWordMath"] = self.unconfirmedBackupCheckbox.GetValue()
		section["terminologyProfile"] = ("standard", "school", "university")[
			self.terminologyProfileChoice.GetSelection()
		]
		section["domainHint"] = self._domainValues[self.domainHintChoice.GetSelection()]
		section["relativeRate"] = self.relativeRateControl.GetValue()
		section["pauseFactor"] = self.pauseFactorControl.GetValue()
		section["autoMathCatBackend"] = self.autoMathCatCheckbox.GetValue()
		section["terminologyOverrides"] = json.dumps(
			self._terminologyOverrides,
			ensure_ascii=False,
			sort_keys=True,
		)
		section["forceGreekLanguage"] = True
		# Reassert ownership whenever this panel is saved. This also repairs a
		# provider slot that changed while the dialog was open.
		from . import applyProviderRegistration

		applyProviderRegistration()
