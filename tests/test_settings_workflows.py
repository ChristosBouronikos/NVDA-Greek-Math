# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Exercise Settings actions with NVDA/wx adapters; never launch real mail or audio."""
import copy
import importlib.util
import json
import sys
import types
import unittest
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch

import test_provider_speech as fixture


class Control:
	def __init__(self, *args, **kwargs):
		self.value = kwargs.get("initial", kwargs.get("value", ""))
		self.choices = list(kwargs.get("choices", []))
		self.selection = -1
		self.label = kwargs.get("label", "")
		self.enabled = True
		self.modal = 0
	def Bind(self, *args, **kwargs): pass
	def SetValue(self, value): self.value = value
	def ChangeValue(self, value): self.value = value
	def GetValue(self): return self.value
	def SetSelection(self, value): self.selection = value
	def GetSelection(self): return self.selection
	def GetStringSelection(self): return self.choices[self.selection] if self.selection >= 0 else ""
	def SetStringSelection(self, value): self.selection = self.choices.index(value)
	def Set(self, values):
		self.choices = list(values)
		self.selection = -1
	def Enable(self, enabled): self.enabled = enabled
	def SetLabel(self, label): self.label = label
	def Add(self, *args, **kwargs): pass
	def SetSizer(self, *args): pass
	def SetupScrolling(self, **kwargs): pass
	def SetMinSize(self, *args): pass
	def Wrap(self, *args): pass
	def CreateButtonSizer(self, *args): return Control()
	def EndModal(self, result): self.modal = result
	def ShowModal(self): return self.modal
	def AddPage(self, *args, **kwargs): pass
	def __enter__(self): return self
	def __exit__(self, *args): pass


class Helper:
	def __init__(self, parent, sizer=None): pass
	def addItem(self, item): return item
	def addLabeledControl(self, label, cls, **kwargs): return cls(label=label, **kwargs)


class TestSettingsWorkflows(unittest.TestCase):
	def setUp(self):
		self.fixture = fixture.TestProviderSpeechSequence()
		self.fixture.setUp()
		self.provider = self.fixture.provider
		self.config = self.fixture.config["greekMathReader"]
		self.config.update({"translateUnconfirmedWordMath": True, "verbosity": 1, "pauseFactor": 50})
		self.audio = []
		self.beeps = []
		self.messages = []
		self.clipboard = []
		self.repairs = []
		sys.modules['speech'].speak = self.audio.append
		self.wx = types.ModuleType('wx')
		for name in ('Dialog', 'TextCtrl', 'CheckBox', 'Choice', 'SpinCtrl', 'StaticText', 'Button', 'ListBox', 'ComboBox', 'BoxSizer', 'Notebook', 'Panel'):
			setattr(self.wx, name, Control)
		for name in ('EVT_BUTTON', 'EVT_CHOICE', 'EVT_TEXT', 'EVT_CHECKBOX', 'EVT_LISTBOX', 'TE_MULTILINE', 'TE_READONLY', 'VERTICAL', 'ALL', 'ALIGN_RIGHT', 'OK', 'CANCEL', 'CLOSE', 'EXPAND', 'DEFAULT_DIALOG_STYLE', 'RESIZE_BORDER'):
			setattr(self.wx, name, 1)
		self.wx.NOT_FOUND = -1
		self.wx.ID_OK = 10
		self.wx.ID_CLOSE = 11
		gui = types.ModuleType('gui')
		gui.guiHelper = types.SimpleNamespace(BoxSizerHelper=Helper)
		settings = types.ModuleType('gui.settingsDialogs')
		settings.SettingsPanel = Control
		self._stub('wx', self.wx)
		self._stub('wx.lib', types.ModuleType('wx.lib'))
		self._stub('wx.lib.scrolledpanel', types.SimpleNamespace(ScrolledPanel=Control))
		self._stub('gui', gui)
		self._stub('gui.settingsDialogs', settings)
		self._stub('ui', types.SimpleNamespace(message=self.messages.append))
		self._stub('api', types.SimpleNamespace(copyToClip=lambda text: self.clipboard.append(text) or True))
		self._stub('tones', types.SimpleNamespace(beep=lambda *args, **kwargs: self.beeps.append((args, kwargs))))
		self._stub('scriptHandler', types.SimpleNamespace(script=lambda **kwargs: lambda function: function))
		sys.modules['mathPres'].MathInteractionNVDAObject = Control
		package = sys.modules[fixture.PACKAGE_NAME]
		package.getHealthCheck = lambda: {"healthy": True}
		package.applyProviderRegistration = lambda: self.repairs.append('save')
		self.panelModule = self._load('settingsPanel')
		self.support = self._load('settingsSupport')
		self.dialogs = self._load('readingSettingsDialogs')
		self.panel = self.panelModule.GreekMathSettingsPanel()
		self.panel.makeSettings(Control())

	def _stub(self, name, module):
		if name not in self.fixture.savedModules:
			self.fixture.savedModules[name] = sys.modules.get(name, fixture._MISSING)
		sys.modules[name] = module

	def _load(self, name):
		fullName = fixture.PACKAGE_NAME + '.' + name
		spec = importlib.util.spec_from_file_location(fullName, fixture.PACKAGE_DIR / (name+'.py'))
		module = importlib.util.module_from_spec(spec)
		self._stub(fullName, module)
		spec.loader.exec_module(module)
		return module

	def tearDown(self):
		self.fixture.tearDown()

	def _read(self):
		self.provider.GreekMathProvider().getSpeechForMathMl('<math><mi>G</mi><mo>+</mo><mi>g</mi></math>')
		return copy.deepcopy(self.provider.lastReading)

	def test_unsaved_preview_uses_capitals_course_rate_and_pauses(self):
		original = copy.deepcopy(self.config)
		last = self._read()
		self.panel.announceCapitalsCheckbox.SetValue(True)
		self.panel.relativeRateControl.SetValue(80)
		self.panel.pauseFactorControl.SetValue(200)
		self.panel._pronunciationCourse = 'Physics'
		self.panel._pronunciationProfiles['Physics'] = {'G': 'δοκιμή'}
		self.panel.onCurrentSpeech(None)
		self.assertIn('κεφαλαίο δοκιμή', self.panel.previewTranscript.GetValue())
		self.assertEqual([v.multiplier for v in self.audio[-1] if isinstance(v, self.fixture.commands.RateCommand)], [0.8, 1.0])
		self.panel.exampleChoice.SetSelection(1)
		self.panel.onTestSpeech(None)
		settings = self.provider.getReadingConfig(self.panel._pendingSection())
		self.assertEqual(settings.pause_factor, 100)
		self.assertTrue(any(isinstance(v, self.fixture.commands.BreakCommand) and v.time > 0 for v in self.audio[-1]))
		self.assertEqual(self.provider.lastReading, last)
		self.assertEqual(self.config, original)
		self.assertEqual(self.repairs, [])

	def test_save_persists_new_controls_and_default_pause_scale(self):
		self.assertEqual(self.panel.pauseFactorControl.GetValue(), 100)
		self.assertEqual(self.panel.matrixChoice.GetSelection(), 0)
		self.panel.announceCapitalsCheckbox.SetValue(True)
		self.panel.matrixChoice.SetSelection(3)
		self.panel.pauseFactorControl.SetValue(0)
		self.panel.compositionCheckbox.SetValue(True)
		self.panel.gradientChoice.SetSelection(1)
		self.panel.onSave()
		settings = self.provider.getReadingConfig()
		self.assertTrue(settings.announce_capitals)
		self.assertEqual(settings.matrix_reading, 'columns')
		self.assertEqual(settings.pause_factor, 0)
		self.assertEqual(settings.gradient_name, 'κλίση')
		self.assertTrue(settings.explain_composition)

	@unittest.skip("Neural voices scratched from settings; preserved for future releases")
	def test_closing_voice_manager_then_saving_enables_the_synthesizer(self):
		dialogModule = types.ModuleType(fixture.PACKAGE_NAME + '.neuralVoicesDialog')
		dialogModule.NeuralVoicesDialog = Control
		self._stub(fixture.PACKAGE_NAME + '.neuralVoicesDialog', dialogModule)
		self.config['neuralVoicesEnabled'] = False
		self.panel.neuralVoicesCheckbox.SetValue(False)
		self.panel.onManageVoices(None)
		# Immediately enabled so user doesn't have to save before seeing synthesizer
		self.assertTrue(self.config['neuralVoicesEnabled'])
		self.panel.onSave()
		self.assertTrue(self.config['neuralVoicesEnabled'])

	@unittest.skip("Neural voices scratched from settings; preserved for future releases")
	def test_neural_voices_checkbox_toggle_immediately_updates_config(self):
		self.config['neuralVoicesEnabled'] = False
		self.panel.neuralVoicesCheckbox.SetValue(True)
		self.panel.onNeuralVoicesToggle(None)
		self.assertTrue(self.config['neuralVoicesEnabled'])
		self.panel.neuralVoicesCheckbox.SetValue(False)
		self.panel.onNeuralVoicesToggle(None)
		self.assertFalse(self.config['neuralVoicesEnabled'])

	def test_preview_examples_and_missing_current(self):
		for index in range(len(self.support.PREVIEW_EXAMPLES)):
			self.panel.exampleChoice.SetSelection(index)
			self.panel.onTestSpeech(None)
			self.assertTrue(self.panel.previewTranscript.GetValue())
		self.assertIsNone(self.provider.lastReading)
		self.panel.onCurrentSpeech(None)
		self.assertIn('Read an expression first', self.messages[-1])

	def test_symbol_editor_distinguishes_case_reset_and_cancel(self):
		profiles = {'Default': {}, 'Physics': {'G': 'δοκιμή'}}
		dialog = self.dialogs.PronunciationDialog(Control(), profiles, 'Default', self.provider.getReadingConfig())
		dialog.search.SetValue('G')
		dialog.onFilter(None)
		self.assertEqual(dialog._visible, ['G'])
		dialog.name.SetValue('τζι μεγάλο')
		dialog.search.SetValue('g')
		dialog.onFilter(None)
		self.assertEqual(dialog.profiles['Default'], {'G': 'τζι μεγάλο'})
		self.assertEqual(dialog._visible, ['g'])
		dialog.courses.SetStringSelection('Physics')
		dialog.onCourse(None)
		dialog.search.SetValue('G')
		dialog.onFilter(None)
		self.assertEqual(dialog.name.GetValue(), 'δοκιμή')
		dialog.onReset(None)
		dialog.onOK(None)
		self.assertEqual(dialog.profiles['Physics'], {})
		self.assertEqual(profiles, {'Default': {}, 'Physics': {'G': 'δοκιμή'}})

	def test_report_captures_original_speech_and_encodes_email(self):
		reading = self._read()
		self.config['verbosity'] = 2
		report = self.support.reading_report(reading, 'αναμενόμενο & κείμενο', 'λεπτομέρειες')
		self.assertIn('τζί συν τζί', report)
		self.assertIn('"verbosity": 1', report)
		url = self.support.report_mailto(report)
		self.assertEqual(urlsplit(url).path, 'cbouronikos@uth.gr')
		self.assertEqual(parse_qs(urlsplit(url).query)['body'], [report])
		self.assertEqual(set(parse_qs(urlsplit(url).query)), {'body', 'subject'})

	def test_invalid_expression_can_be_reported(self):
		source = '<math><mfrac>'
		sequence = self.provider.GreekMathProvider().getSpeechForMathMl(source)
		self.assertEqual(sequence, ['Invalid mathematical content'])
		self.assertEqual(self.provider.lastReading['expression'], source)
		self.assertEqual(self.provider.lastReading['actualSpeech'], sequence[0])

	def test_email_opens_draft_and_keeps_full_long_report(self):
		dialog = self.dialogs.ReadingReportDialog(Control(), self._read())
		dialog.expected.SetValue('σωστή εκφώνηση')
		dialog.notes.SetValue('σημείωση ' * 2000)
		dialog.onUpdate(None)
		opened = []
		with patch.object(self.dialogs, 'os', types.SimpleNamespace(startfile=opened.append)):
			dialog.onEmail(None)
		self.assertEqual(self.clipboard[-1], dialog.report.GetValue())
		self.assertEqual(len(opened), 1)
		self.assertTrue(opened[0].startswith('mailto:cbouronikos@uth.gr?'))
		self.assertLess(len(opened[0]), 1800)
		self.assertIn('Paste it', self.messages[-1])

	def test_short_email_includes_full_body_and_missing_mail_app_is_handled(self):
		dialog = self.dialogs.ReadingReportDialog(Control(), self._read())
		dialog.report.SetValue('δοκιμή & αναφορά')
		opened = []
		with patch.object(self.dialogs, 'os', types.SimpleNamespace(startfile=opened.append)):
			dialog.onEmail(None)
		self.assertEqual(parse_qs(urlsplit(opened[0]).query)['body'], ['δοκιμή & αναφορά'])
		self.assertEqual(self.clipboard, [])
		def missing_app(url):
			raise OSError('no handler')
		with patch.object(self.dialogs, 'os', types.SimpleNamespace(startfile=missing_app)):
			dialog.onEmail(None)
		self.assertIn('Could not open a mail app', self.messages[-1])

	def test_local_backend_used_for_unsupported_preferences(self):
		self.assertFalse(self.provider._localPreferencesRequired('<math><mi>x</mi></math>'))
		self.config['announceCapitals'] = True
		self.assertTrue(self.provider._localPreferencesRequired())
		self.config['announceCapitals'] = False
		self.assertTrue(self.provider._localPreferencesRequired('<math><mo>∇</mo><mi>f</mi></math>'))

	def test_matrix_navigation_rows_columns_positions_and_boundary_volume(self):
		module = self._load('interaction')
		source = self.support.PREVIEW_EXAMPLES[3][1]
		interaction = module.GreekMathInteraction(mathMl=source)
		self.config['matrixReading'] = 'explore'
		interaction.script_moveIn(None)
		self.assertEqual(interaction.pointer.tag, 'mtd')
		self.config['matrixPositions'] = True
		interaction.script_tableRight(None)
		self.assertIn('γραμμή 1, στήλη 2:', self.audio[-1])
		self.assertIn('0', self.audio[-1])
		interaction.script_readColumn(None)
		spoken = [item for item in self.audio[-1] if isinstance(item, str)]
		self.assertIn('0', spoken)
		self.assertIn('2', spoken)
		interaction.script_readRow(None)
		self.assertIn('1', self.audio[-1])
		self.assertIn('0', self.audio[-1])
		interaction.script_tableRight(None)
		self.assertEqual(self.beeps[-1], ((200, 60), {'left': 50, 'right': 50}))
		self.config['boundarySound'] = 0
		before = len(self.beeps)
		interaction.script_tableRight(None)
		self.assertEqual(len(self.beeps), before)

	def test_vocalizer_download_button_opens_browser_and_notifies(self):
		opened = []
		with patch('webbrowser.open', opened.append):
			self.panel.onDownloadVocalizer(None)
		self.assertEqual(opened, ['https://www.tiflotecnia.net/en/downloads.htm'])
		self.assertIn('Opening Vocalizer Expressive download page', self.messages[-1])

	def test_onecore_download_button_opens_settings_and_notifies(self):
		opened = []
		with patch('webbrowser.open', opened.append):
			self.panel.onDownloadOneCore(None)
		self.assertEqual(opened, ['ms-settings:speech'])
		self.assertIn('Opening Windows Speech Settings', self.messages[-1])

	def test_settings_panel_tabs_and_controls_exist(self):
		self.assertIsNotNone(self.panel.notebook)
		self.assertIsNotNone(self.panel.verbosityChoice)
		self.assertIsNotNone(self.panel.announceCapitalsCheckbox)
		self.assertIsNotNone(self.panel.terminologyProfileChoice)
		self.assertIsNotNone(self.panel.domainHintChoice)
		self.assertIsNotNone(self.panel.matrixChoice)
		self.assertIsNotNone(self.panel.relativeRateControl)
		self.assertIsNotNone(self.panel.pauseFactorControl)
		self.assertIsNotNone(self.panel.symbolEditorButton)
		self.assertFalse(hasattr(self.panel, "neuralVoicesCheckbox"))
		self.assertFalse(hasattr(self.panel, "manageVoicesButton"))
		self.assertIsNotNone(self.panel.downloadOneCoreButton)
		self.assertIsNotNone(self.panel.downloadVocalizerButton)
