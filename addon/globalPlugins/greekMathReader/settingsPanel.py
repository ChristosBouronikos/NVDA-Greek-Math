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
		section = config.conf["greekMathReader"]

		hasNotebook = hasattr(wx, "Notebook") and hasattr(wx, "Panel")
		if hasNotebook:
			self.notebook = wx.Notebook(self)
			settingsSizer.Add(self.notebook, proportion=1, flag=wx.EXPAND)

			def createTabPage(title):
				page = wx.Panel(self.notebook)
				sizer = wx.BoxSizer(wx.VERTICAL)
				page.SetSizer(sizer)
				self.notebook.AddPage(page, title)
				return gui.guiHelper.BoxSizerHelper(page, sizer=sizer), page

			generalHelper, tabGeneral = createTabPage(_("General"))
			mathHelper, tabMath = createTabPage(_("Math & Notation"))
			navHelper, tabNav = createTabPage(_("Matrices & Navigation"))
			previewHelper, tabPreview = createTabPage(_("Rate & Preview"))
			termsHelper, tabTerms = createTabPage(_("Symbols & Terminology"))
			voicesHelper, tabVoices = createTabPage(_("Voices & Tools"))
		else:
			self.notebook = None
			generalHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
			mathHelper = navHelper = previewHelper = termsHelper = voicesHelper = generalHelper
			tabGeneral = tabMath = tabNav = tabPreview = tabTerms = tabVoices = self

		# =========================================================================
		# Tab 1: General & Speech Behavior
		# =========================================================================
		generalHelper.addItem(
			wx.StaticText(
				tabGeneral,
				# Translators: Explains why Greek does not appear in NVDA's built-in Math language list.
				label=_(
					"NVDA 2026.1.1 has no Automatic choice under Math; English is the "
					"normal MathCAT default. Greek Math Reader bypasses that language box."
				),
			)
		)

		generalHelper.addItem(
			wx.StaticText(
				tabGeneral,
				# Translators: Explains the read-only health check and explicit repair.
				label=_(
					"The health check reports settings that can block Greek math. "
					"Use Repair under Voices & Tools to change them explicitly."
				),
			)
		)
		from . import getHealthCheck

		health = getHealthCheck()
		self.healthStatus = generalHelper.addItem(
			wx.StaticText(
				tabGeneral,
				label=_("Health check: ready") if health["healthy"] else _("Health check: repair recommended"),
			)
		)

		generalHelper.addItem(
			wx.StaticText(
				tabGeneral,
				# Translators: Status shown because the add-on no longer permits another speech reader.
				label=_(
					"Greek Math Reader is the exclusive speech and interaction reader "
					"while it is installed."
				),
			)
		)

		self.verbosityChoice = generalHelper.addLabeledControl(
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

		self.announceCapitalsCheckbox = generalHelper.addItem(
			wx.CheckBox(tabGeneral, label=_("Announce capital letters independently of verbosity"))
		)
		self.announceCapitalsCheckbox.SetValue(bool(section.get("announceCapitals", False)))

		self.unconfirmedBackupCheckbox = generalHelper.addItem(
			# Translators: Label of a checkbox enabling the backup translation of
			# English math speech in Word when no equation can be confirmed.
			wx.CheckBox(
				tabGeneral,
				label=_(
					"&Backup mode: translate English math speech in Word and Outlook "
					"even when the equation cannot be confirmed"
				),
			)
		)
		self.unconfirmedBackupCheckbox.SetValue(bool(section["translateUnconfirmedWordMath"]))

		self.autoMathCatCheckbox = generalHelper.addItem(
			wx.CheckBox(
				tabGeneral,
				label=_("Use the installed MathCAT Greek backend automatically when available"),
			)
		)
		self.autoMathCatCheckbox.SetValue(bool(section.get("autoMathCatBackend", True)))

		# =========================================================================
		# Tab 2: Mathematics & Notation
		# =========================================================================
		self.terminologyProfileChoice = mathHelper.addLabeledControl(
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

		self.domainHintChoice = mathHelper.addLabeledControl(
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

		self.decimalCommaCheckbox = mathHelper.addItem(
			# Translators: Label of a checkbox in the settings panel.
			wx.CheckBox(tabMath, label=_("Read the decimal &point as a Greek decimal comma (3.14 as 3,14)"))
		)
		self.decimalCommaCheckbox.SetValue(bool(section["decimalComma"]))

		self.decimalDigitsCheckbox = mathHelper.addItem(
			wx.CheckBox(tabMath, label=_("Read decimal digits &individually"))
		)
		self.decimalDigitsCheckbox.SetValue(bool(section.get("decimalDigits", False)))

		self.latinLiteralCheckbox = mathHelper.addItem(
			# Translators: Label of a checkbox in the settings panel.
			wx.CheckBox(
				tabMath,
				label=_("Read Latin letters in formulas as literal &English letters"),
			)
		)
		self.latinLiteralCheckbox.SetValue(section.get("latinLetterMode", "greek_school") == "literal")

		self.gradientChoice = mathHelper.addLabeledControl(
			_("Name for ∇ and grad (gradient):"),
			wx.Choice,
			choices=["ανάδελτα", "κλίση"],
		)
		self.gradientChoice.SetSelection(1 if section.get("gradientName") == "κλίση" else 0)
		mathHelper.addItem(
			wx.StaticText(tabMath, label=_("A course-specific custom name for ∇ takes precedence over this choice."))
		)

		self.compositionCheckbox = mathHelper.addItem(
			wx.CheckBox(tabMath, label=_("Explain function composition (apply the right function first)"))
		)
		self.compositionCheckbox.SetValue(bool(section.get("explainComposition", False)))

		# =========================================================================
		# Tab 3: Matrices & Navigation
		# =========================================================================
		self.matrixChoice = navHelper.addLabeledControl(
			_("Matrix reading:"),
			wx.Choice,
			choices=[
				_("Whole matrix (current reading — default)"),
				_("Dimensions, then explore cells"),
				_("Read by rows"),
				_("Read by columns"),
			],
		)
		self._matrixValues = ("whole", "explore", "rows", "columns")
		self.matrixChoice.SetSelection(self._matrixValues.index(section.get("matrixReading", "whole")))

		self.matrixPositionsCheckbox = navHelper.addItem(
			wx.CheckBox(tabNav, label=_("Announce matrix cell positions"))
		)
		self.matrixPositionsCheckbox.SetValue(bool(section.get("matrixPositions", False)))

		navHelper.addItem(
			wx.StaticText(
				tabNav,
				label=_(
					"In matrix interaction: R reads the current row, C reads the current column, "
					"Control+arrows move between cells. Zero entries are read."
				),
			)
		)

		self.boundarySoundControl = navHelper.addLabeledControl(
			_("Navigation boundary sound (% of current volume, 0 = off):"),
			wx.SpinCtrl,
			min=0,
			max=100,
			initial=int(section.get("boundarySound", 100)),
		)
		self.boundarySampleButton = navHelper.addItem(
			wx.Button(tabNav, label=_("Listen to boundary sound"))
		)
		self.boundarySampleButton.Bind(wx.EVT_BUTTON, self.onBoundarySample)

		# =========================================================================
		# Tab 4: Speech Rate, Pauses & Preview
		# =========================================================================
		self.relativeRateControl = previewHelper.addLabeledControl(
			_("Math speech rate (% of normal NVDA speech, 100 = normal):"),
			wx.SpinCtrl,
			min=1,
			max=100,
			initial=int(section.get("relativeRate", 100)),
		)
		self.pauseFactorControl = previewHelper.addLabeledControl(
			_("Math pauses (% of standard breaks: 0 = none, 100 = normal, 200 = double):"),
			wx.SpinCtrl,
			min=0,
			max=200,
			initial=2 * int(section.get("pauseFactor", 50)),
		)

		from .settingsSupport import PREVIEW_EXAMPLES

		previewHelper.addItem(
			wx.StaticText(
				tabPreview,
				label=_(
					"Preview uses unsaved choices in the local Greek engine and does not run Repair. "
					"Read an expression before opening Settings to preview it here."
				),
			)
		)
		self.exampleChoice = previewHelper.addLabeledControl(
			_("Preview example:"),
			wx.Choice,
			choices=[_(label) for label, source in PREVIEW_EXAMPLES],
		)
		self.exampleChoice.SetSelection(0)
		self.previewTranscript = previewHelper.addLabeledControl(
			_("Preview transcript:"),
			wx.TextCtrl,
			style=wx.TE_MULTILINE | wx.TE_READONLY,
			size=(-1, 90),
		)
		self.previewStatus = previewHelper.addItem(wx.StaticText(tabPreview, label=""))
		self.testSpeechButton = previewHelper.addItem(
			# Translators: Button that directly speaks a sample equation using the add-on's Greek engine.
			wx.Button(tabPreview, label=_("Listen to example (including rate and pauses)"))
		)
		self.testSpeechButton.Bind(wx.EVT_BUTTON, self.onTestSpeech)
		self.currentSpeechButton = previewHelper.addItem(
			wx.Button(tabPreview, label=_("Listen to current expression"))
		)
		self.currentSpeechButton.Bind(wx.EVT_BUTTON, self.onCurrentSpeech)

		# =========================================================================
		# Tab 5: Symbols & Terminology
		# =========================================================================
		from .engine.symbols_el import validate_pronunciations

		try:
			profiles = json.loads(section.get("symbolPronunciations", "{}"))
		except (TypeError, ValueError):
			profiles = {}
		self._pronunciationProfiles = (
			{
				name: validate_pronunciations(values)
				for name, values in profiles.items()
				if isinstance(name, str) and name.strip()
			}
			if isinstance(profiles, dict)
			else {}
		)
		self._pronunciationCourse = section.get("pronunciationCourse", "Default")
		self._pronunciationProfiles.setdefault(self._pronunciationCourse, {})

		self.symbolEditorButton = termsHelper.addItem(
			wx.Button(tabTerms, label=_("Symbol pronunciations and ambiguous symbols..."))
		)
		self.symbolEditorButton.Bind(wx.EVT_BUTTON, self.onSymbolEditor)

		try:
			self._terminologyOverrides = json.loads(section.get("terminologyOverrides", "{}"))
		except (TypeError, ValueError):
			self._terminologyOverrides = {}
		if not isinstance(self._terminologyOverrides, dict):
			self._terminologyOverrides = {}

		self.importTerminologyButton = termsHelper.addItem(
			wx.Button(tabTerms, label=_("&Import personal terminology..."))
		)
		self.importTerminologyButton.Bind(wx.EVT_BUTTON, self.onImportTerminology)
		self.exportTerminologyButton = termsHelper.addItem(
			wx.Button(tabTerms, label=_("E&xport personal terminology..."))
		)
		self.exportTerminologyButton.Bind(wx.EVT_BUTTON, self.onExportTerminology)
		self.clearTerminologyButton = termsHelper.addItem(
			wx.Button(tabTerms, label=_("&Clear personal terminology"))
		)
		self.clearTerminologyButton.Bind(wx.EVT_BUTTON, self.onClearTerminology)
		self.resetTerminologyChoice = termsHelper.addLabeledControl(
			_("Personal term to &reset:"),
			wx.Choice,
			choices=[],
		)
		self.resetSelectedTerminologyButton = termsHelper.addItem(
			wx.Button(tabTerms, label=_("Reset &selected personal term"))
		)
		self.resetSelectedTerminologyButton.Bind(wx.EVT_BUTTON, self.onResetSelectedTerminology)
		self._refreshTerminologyChoices()

		# =========================================================================
		# Tab 6: Voices & Tools
		# =========================================================================
		# --- Section: Neural Voices (Deferred / commented out for future releases) ---
		# voicesHelper.addItem(
		# 	wx.StaticText(
		# 		tabVoices,
		# 		# Translators: Introduces the optional downloadable neural voices.
		# 		label=_(
		# 			"Optional offline neural voices: replace the voice for all of NVDA, "
		# 			"not just maths. Downloaded only on demand."
		# 		),
		# 	)
		# )
		# self.neuralVoicesCheckbox = voicesHelper.addItem(
		# 	wx.CheckBox(
		# 		tabVoices,
		# 		# Translators: Master switch for the optional downloadable neural voices.
		# 		label=_("&Offer downloadable neural voices in NVDA's synthesizer list"),
		# 	)
		# )
		# self.neuralVoicesCheckbox.SetValue(bool(section.get("neuralVoicesEnabled", False)))
		# self.neuralVoicesCheckbox.Bind(wx.EVT_CHECKBOX, self.onNeuralVoicesToggle)
		#
		# self.manageVoicesButton = voicesHelper.addItem(
		# 			# Translators: Opens the dialog that downloads and removes neural voices.
		# 	wx.Button(tabVoices, label=_("&Manage neural voices..."))
		# )
		# self.manageVoicesButton.Bind(wx.EVT_BUTTON, self.onManageVoices)

		# --- Section: Windows OneCore Voices ---
		voicesHelper.addItem(
			wx.StaticText(
				tabVoices,
				label=_(
					"Windows OneCore voices include Microsoft Stefanos and additional downloadable language packages. "
					"Use Windows Settings to download and install more Greek voice options."
				),
			)
		)
		self.downloadOneCoreButton = voicesHelper.addItem(
			wx.Button(tabVoices, label=_("&Download more Greek voices for Windows OneCore..."))
		)
		self.downloadOneCoreButton.Bind(wx.EVT_BUTTON, self.onDownloadOneCore)

		# --- Section: Nuance Vocalizer Expressive ---
		voicesHelper.addItem(
			wx.StaticText(
				tabVoices,
				label=_(
					"Nuance Vocalizer Expressive provides high-quality Greek voices (Melina and Nikos). "
					"Download the driver and voice packages from Tiflotecnia, then install them via Add-on Store."
				),
			)
		)
		self.downloadVocalizerButton = voicesHelper.addItem(
			wx.Button(tabVoices, label=_("&Download Vocalizer Expressive (Melina / Nikos)..."))
		)
		self.downloadVocalizerButton.Bind(wx.EVT_BUTTON, self.onDownloadVocalizer)

		# --- Section: Maintenance & Diagnostics ---
		voicesHelper.addItem(
			wx.StaticText(
				tabVoices,
				label=_("Maintenance and problem diagnostics:"),
			)
		)
		self.repairButton = voicesHelper.addItem(
			wx.Button(tabVoices, label=_("&Repair required NVDA settings"))
		)
		self.repairButton.Bind(wx.EVT_BUTTON, self.onRepair)

		self.resetButton = voicesHelper.addItem(
			# Translators: Resets add-on settings and repairs all exclusive provider hooks.
			wx.Button(tabVoices, label=_("&Reset settings and repair Greek math"))
		)
		self.resetButton.Bind(wx.EVT_BUTTON, self.onReset)

		self.copyDiagnosticsButton = voicesHelper.addItem(
			# Translators: Copies exact add-on, provider, equation exposure, and voice details.
			wx.Button(tabVoices, label=_("&Copy diagnostics"))
		)
		self.copyDiagnosticsButton.Bind(wx.EVT_BUTTON, self.onCopyDiagnostics)

		# Keep reporting at the end of Settings, after all preferences and tools.
		self.reportProblemButton = voicesHelper.addItem(
			wx.Button(tabVoices, label=_("Report a reading problem / email the maintainer..."))
		)
		self.reportProblemButton.Bind(wx.EVT_BUTTON, self.onReportProblem)

	# Preserved for future releases:
	# def onNeuralVoicesToggle(self, event):
	# 	config.conf["greekMathReader"]["neuralVoicesEnabled"] = self.neuralVoicesCheckbox.GetValue()

	def onDownloadOneCore(self, event):
		"""Open Windows Speech Settings to download and install more Greek voice packages."""
		ui.message(
			_(
				"Opening Windows Speech Settings... Select 'Add voices' under 'Manage voices' "
				"to download more Greek voice options."
			)
		)
		try:
			import os

			if hasattr(os, "startfile"):
				os.startfile("ms-settings:speech")
			else:
				import webbrowser

				webbrowser.open("ms-settings:speech")
		except Exception:
			try:
				import webbrowser

				webbrowser.open("ms-settings:speech")
			except Exception:
				pass

	def onDownloadVocalizer(self, event):
		"""Open the official Vocalizer Expressive downloads page in the browser."""
		url = "https://www.tiflotecnia.net/en/downloads.htm"
		ui.message(_("Opening Vocalizer Expressive download page in your browser..."))
		try:
			import webbrowser

			webbrowser.open(url)
		except Exception:
			try:
				wx.LaunchDefaultBrowser(url)
			except Exception:
				pass

	# Preserved for future releases:
	# def onManageVoices(self, event):
	# 	"""Open the voice manager, enabling the feature first if needed.
	#
	# 	Downloading a voice is pointless while the synthesizer stays hidden from
	# 	NVDA's list, so opening the manager ticks the option. It is saved
	# 	immediately so the newly downloaded voice is available in NVDA's Speech
	# 	settings without requiring an extra dialog save cycle.
	# 	"""
	# 	self.neuralVoicesCheckbox.SetValue(True)
	# 	config.conf["greekMathReader"]["neuralVoicesEnabled"] = True
	# 	try:
	# 		from .neuralVoicesDialog import NeuralVoicesDialog
	# 	except ImportError:
	# 		# Translators: Shown if the neural voice component is unavailable.
	# 		ui.message(_("The neural voice manager could not be opened"))
	# 		return
	# 	with NeuralVoicesDialog(self) as dialog:
	# 		dialog.ShowModal()
	# 	self.neuralVoicesCheckbox.SetValue(bool(config.conf["greekMathReader"].get("neuralVoicesEnabled", True)))

	def _pendingSection(self):
		section = dict(config.conf["greekMathReader"])
		section.update({
			"verbosity": self.verbosityChoice.GetSelection(),
			"announceCapitals": self.announceCapitalsCheckbox.GetValue(),
			"decimalComma": self.decimalCommaCheckbox.GetValue(),
			"decimalDigits": self.decimalDigitsCheckbox.GetValue(),
			"latinLetterMode": "literal" if self.latinLiteralCheckbox.GetValue() else "greek_school",
			"terminologyProfile": ("standard", "school", "university")[self.terminologyProfileChoice.GetSelection()],
			"domainHint": self._domainValues[self.domainHintChoice.GetSelection()],
			"relativeRate": self.relativeRateControl.GetValue(),
			"pauseFactor": round(self.pauseFactorControl.GetValue() / 2),
			"gradientName": ("ανάδελτα", "κλίση")[self.gradientChoice.GetSelection()],
			"explainComposition": self.compositionCheckbox.GetValue(),
			"matrixReading": self._matrixValues[self.matrixChoice.GetSelection()],
			"matrixPositions": self.matrixPositionsCheckbox.GetValue(),
			"boundarySound": self.boundarySoundControl.GetValue(),
			"symbolPronunciations": json.dumps(self._pronunciationProfiles, ensure_ascii=False),
			"pronunciationCourse": self._pronunciationCourse,
			"terminologyOverrides": json.dumps(self._terminologyOverrides, ensure_ascii=False),
		})
		return section

	def onSymbolEditor(self, event):
		from .provider import getReadingConfig
		from .readingSettingsDialogs import PronunciationDialog
		with PronunciationDialog(self, self._pronunciationProfiles, self._pronunciationCourse,
			getReadingConfig(self._pendingSection())) as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				self._pronunciationProfiles = dialog.profiles
				self._pronunciationCourse = dialog.course

	def _preview(self, source, inputFormat):
		import speech
		from .provider import getReadingConfig, tokensToSpeechSequence
		from .settingsSupport import preview_tokens
		from .engine import MathMLParseError, LatexParseError, UnicodeMathParseError, get_last_engine_diagnostics
		try:
			readingConfig = getReadingConfig(self._pendingSection())
			tokens = preview_tokens(source, inputFormat, readingConfig)
			sequence = tokensToSpeechSequence(tokens, readingConfig)
		except (MathMLParseError, LatexParseError, UnicodeMathParseError, KeyError):
			self.previewTranscript.ChangeValue(_("Could not preview this expression"))
			self.previewStatus.SetLabel("")
			ui.message(_("Could not preview this expression"))
			return
		self.previewTranscript.ChangeValue(" ".join(item for item in sequence if isinstance(item, str)))
		unknown = get_last_engine_diagnostics()["unknown"]
		self.previewStatus.SetLabel(_("Unknown symbols or identifiers: {symbols}").format(
			symbols=", ".join(item.split(":", 1)[-1] for item in unknown)) if unknown else "")
		speech.speak(sequence)

	def onTestSpeech(self, event):
		from .settingsSupport import PREVIEW_EXAMPLES
		self._preview(PREVIEW_EXAMPLES[self.exampleChoice.GetSelection()][1], "mathml")

	def onCurrentSpeech(self, event):
		from .provider import lastReading
		if lastReading is None:
			ui.message(_("Read an expression first, then reopen Settings."))
			return
		self._preview(lastReading["expression"], lastReading["format"])

	def onBoundarySample(self, event):
		import tones
		volume = round(self.boundarySoundControl.GetValue() / 2)
		if volume:
			tones.beep(200, 60, left=volume, right=volume)
		else:
			ui.message(_("Boundary sound is off"))

	def onReportProblem(self, event):
		from .provider import lastReading
		from .readingSettingsDialogs import ReadingReportDialog
		if lastReading is None:
			ui.message(_("Read the problem expression first, then reopen Settings."))
			return
		with ReadingReportDialog(self, lastReading) as dialog:
			dialog.ShowModal()

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
		self.decimalDigitsCheckbox.SetValue(False)
		self.latinLiteralCheckbox.SetValue(False)
		self.unconfirmedBackupCheckbox.SetValue(True)
		self.terminologyProfileChoice.SetSelection(0)
		self.domainHintChoice.SetSelection(0)
		self.relativeRateControl.SetValue(100)
		self.pauseFactorControl.SetValue(100)
		self.announceCapitalsCheckbox.SetValue(False)
		self.gradientChoice.SetSelection(0)
		self.compositionCheckbox.SetValue(False)
		self.matrixChoice.SetSelection(0)
		self.matrixPositionsCheckbox.SetValue(False)
		self.boundarySoundControl.SetValue(100)
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
		# Save the same reading preferences used by pending previews.
		for key, value in self._pendingSection().items():
			section[key] = value
		section["enabled"] = True
		section["translateUnconfirmedWordMath"] = self.unconfirmedBackupCheckbox.GetValue()
		# Neural voices disabled; preserved for future releases
		# section["neuralVoicesEnabled"] = self.neuralVoicesCheckbox.GetValue()
		section["neuralVoicesEnabled"] = False
		# Reassert ownership whenever this panel is saved. This also repairs a
		# provider slot that changed while the dialog was open.
		from . import applyProviderRegistration

		applyProviderRegistration()
