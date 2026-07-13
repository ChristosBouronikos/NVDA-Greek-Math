# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""Integration-style tests for the add-on's NVDA provider registration."""

import builtins
import importlib.util
import sys
import types
import unittest
from pathlib import Path


ADDON_PACKAGE_DIR = (
	Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"
)
PACKAGE_NAME = "greekMathReaderRegistrationTest"
_MISSING = object()


class _FakeConfig(dict):
	def __init__(self):
		super().__init__(
			greekMathReader={
				"enabled": True,
				"verbosity": 1,
				"decimalComma": True,
				"forceGreekLanguage": True,
			},
			UIA={"allowInMSWord": 0},
		)
		self.spec = {}


class _FakeMathPres(types.ModuleType):
	def __init__(self):
		super().__init__("mathPres")
		self.__path__ = []
		self.speechProvider = object()
		self.brailleProvider = object()
		self.interactionProvider = object()
		self.initializeCalls = 0
		self.terminateCalls = 0

	def registerProvider(self, provider, speech=False, braille=False, interaction=False):
		if speech:
			self.speechProvider = provider
		if interaction:
			self.interactionProvider = provider
		if braille:
			self.brailleProvider = provider

	def initialize(self):
		self.initializeCalls += 1

	def terminate(self):
		self.terminateCalls += 1
		self.speechProvider = None
		self.brailleProvider = None
		self.interactionProvider = None

	def getMathMlFromTextInfo(self, info):
		return getattr(info, "mathMl", None)


class _FakeLog:
	def __init__(self):
		self.infoMessages = []
		self.warningMessages = []
		self.exceptionMessages = []

	def info(self, message):
		self.infoMessages.append(message)

	def warning(self, message):
		self.warningMessages.append(message)

	def exception(self, message):
		self.exceptionMessages.append(message)


class TestProviderRegistration(unittest.TestCase):
	def setUp(self):
		self._savedModules = {}
		self._savedTranslation = getattr(builtins, "_", _MISSING)
		builtins._ = lambda message: message

		self.config = _FakeConfig()
		self.mathPres = _FakeMathPres()
		self.log = _FakeLog()
		self.originalMathCatCalls = []
		testCase = self

		class FakeMathCAT:
			def getSpeechForMathMl(instance, mathMl):
				testCase.originalMathCatCalls.append(mathMl)
				return ["English MathCAT speech"]

		self.MathCAT = FakeMathCAT
		mathPresMathCatPackage = types.ModuleType("mathPres.MathCAT")
		mathPresMathCatPackage.__path__ = []
		mathPresMathCatModule = types.ModuleType("mathPres.MathCAT.MathCAT")
		mathPresMathCatModule.MathCAT = FakeMathCAT

		addonHandler = types.ModuleType("addonHandler")
		addonHandler.initTranslation = lambda: None
		api = types.ModuleType("api")
		api.getFocusObject = lambda: None

		config = types.ModuleType("config")
		config.conf = self.config

		core = types.ModuleType("core")
		core.isMainThread = lambda: True
		self.callLaterHandles = []

		class CallLaterHandle:
			def __init__(handle, callback, args, kwargs):
				handle.callback = callback
				handle.args = args
				handle.kwargs = kwargs
				handle.stopped = False

			def Stop(handle):
				handle.stopped = True

			def run(handle):
				if not handle.stopped:
					handle.callback(*handle.args, **handle.kwargs)

		def callLater(delay, callback, *args, **kwargs):
			handle = CallLaterHandle(callback, args, kwargs)
			self.callLaterHandles.append(handle)
			return handle

		core.callLater = callLater

		globalPluginHandler = types.ModuleType("globalPluginHandler")

		class GlobalPluginBase:
			def __init__(self):
				pass

			def terminate(self):
				pass

		globalPluginHandler.GlobalPlugin = GlobalPluginBase

		gui = types.ModuleType("gui")

		class NVDASettingsDialog:
			categoryClasses = []

		gui.settingsDialogs = types.SimpleNamespace(NVDASettingsDialog=NVDASettingsDialog)

		ui = types.ModuleType("ui")
		ui.messages = []
		ui.message = ui.messages.append

		class FakeSpeechFilter:
			def __init__(filterInstance):
				filterInstance._handlers = []

			@property
			def handlers(filterInstance):
				return iter(filterInstance._handlers)

			def register(filterInstance, handler):
				if handler not in filterInstance._handlers:
					filterInstance._handlers.append(handler)

			def unregister(filterInstance, handler):
				try:
					filterInstance._handlers.remove(handler)
				except ValueError:
					return False
				return True

			def moveToEnd(filterInstance, handler, last=False):
				if handler not in filterInstance._handlers:
					return False
				filterInstance._handlers.remove(handler)
				if last:
					filterInstance._handlers.append(handler)
				else:
					filterInstance._handlers.insert(0, handler)
				return True

			def apply(filterInstance, value):
				for handler in list(filterInstance._handlers):
					value = handler(value)
				return value

		filterSpeechSequence = FakeSpeechFilter()
		speechExtensions = types.ModuleType("speech.extensions")
		speechExtensions.filter_speechSequence = filterSpeechSequence

		speech = types.ModuleType("speech")
		speech.__path__ = []
		speech.spokenSequences = []

		def speak(sequence, *args, **kwargs):
			speech.spokenSequences.append(filterSpeechSequence.apply(sequence))

		speech.speak = speak
		speech.filter_speechSequence = filterSpeechSequence
		self.originalObjectSpeechCalls = []

		def getObjectSpeech(obj, *args, **kwargs):
			self.originalObjectSpeechCalls.append(obj)
			if getattr(obj, "belowLockScreen", False):
				return []
			return ["English accessible math"]

		speech.getObjectSpeech = getObjectSpeech
		self.originalTextInfoSpeechCalls = []

		def getTextInfoSpeech(
			info,
			useCache=True,
			formatConfig=None,
			unit=None,
			reason="query",
			_prefixSpeechCommand=None,
			onlyInitialFields=False,
			suppressBlanks=False,
		):
			self.originalTextInfoSpeechCalls.append((info, unit, reason))
			if reason == "onlyCache":
				return False
			yield [getattr(info, "nativeSpeech", "χ squared plus 1")]
			return True

		def addMathForTextInfo(sequence, info, field):
			sequence.append("English MathCAT speech")

		speech.getTextInfoSpeech = getTextInfoSpeech
		speechCore = types.ModuleType("speech.speech")
		speechCore.getObjectSpeech = getObjectSpeech
		speechCore.getTextInfoSpeech = getTextInfoSpeech
		speechCore._extendSpeechSequence_addMathForTextInfo = addMathForTextInfo
		speechCore.speak = speak
		speech.speech = speechCore
		self.speech = speech
		self.speechCore = speechCore

		controlTypes = types.ModuleType("controlTypes")
		controlTypes.Role = types.SimpleNamespace(MATH="math")
		controlTypes.OutputReason = types.SimpleNamespace(
			QUERY="query",
			ONLYCACHE="onlyCache",
			CARET="caret",
		)
		self.controlTypes = controlTypes
		utils = types.ModuleType("utils")
		utils.__path__ = []
		security = types.ModuleType("utils.security")
		security.objectBelowLockScreenAndWindowsIsLocked = lambda obj: bool(
			getattr(obj, "belowLockScreen", False)
		)

		textInfos = types.ModuleType("textInfos")
		textInfos.UNIT_CHARACTER = "character"
		textInfos.UNIT_WORD = "word"
		textInfos.POSITION_CARET = "caret"
		textInfos.POSITION_SELECTION = "selection"

		logHandler = types.ModuleType("logHandler")
		logHandler.log = self.log

		scriptHandler = types.ModuleType("scriptHandler")

		def script(**kwargs):
			return lambda function: function

		scriptHandler.script = script
		scriptHandler.repeatCount = 0
		scriptHandler.getLastScriptRepeatCount = lambda: scriptHandler.repeatCount
		self.scriptHandler = scriptHandler

		provider = types.ModuleType(f"{PACKAGE_NAME}.provider")

		class GreekMathProvider:
			def getSpeechForMathMl(self, mathMl):
				self.lastMathMl = mathMl
				return ["χι στο τετράγωνο συν 1"]

		provider.GreekMathProvider = GreekMathProvider
		provider.getGreekVoiceSupport = lambda: None
		provider.tokensToSpeechSequence = lambda tokens: tokens
		settingsPanel = types.ModuleType(f"{PACKAGE_NAME}.settingsPanel")

		class GreekMathSettingsPanel:
			pass

		settingsPanel.GreekMathSettingsPanel = GreekMathSettingsPanel

		stubs = {
			"addonHandler": addonHandler,
			"api": api,
			"config": config,
			"core": core,
			"globalPluginHandler": globalPluginHandler,
			"gui": gui,
			"mathPres": self.mathPres,
			"mathPres.MathCAT": mathPresMathCatPackage,
			"mathPres.MathCAT.MathCAT": mathPresMathCatModule,
			"speech": speech,
			"speech.speech": speechCore,
			"speech.extensions": speechExtensions,
			"controlTypes": controlTypes,
			"utils": utils,
			"utils.security": security,
			"textInfos": textInfos,
			"ui": ui,
			"logHandler": logHandler,
			"scriptHandler": scriptHandler,
			f"{PACKAGE_NAME}.provider": provider,
			f"{PACKAGE_NAME}.settingsPanel": settingsPanel,
		}
		for name, module in stubs.items():
			self._savedModules[name] = sys.modules.get(name, _MISSING)
			sys.modules[name] = module

		spec = importlib.util.spec_from_file_location(
			PACKAGE_NAME,
			ADDON_PACKAGE_DIR / "__init__.py",
			submodule_search_locations=[str(ADDON_PACKAGE_DIR)],
		)
		self.module = importlib.util.module_from_spec(spec)
		self._savedModules[PACKAGE_NAME] = sys.modules.get(PACKAGE_NAME, _MISSING)
		sys.modules[PACKAGE_NAME] = self.module
		spec.loader.exec_module(self.module)

	def tearDown(self):
		for name, previous in self._savedModules.items():
			if previous is _MISSING:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = previous
		if self._savedTranslation is _MISSING:
			del builtins._
		else:
			builtins._ = self._savedTranslation

	def test_register_and_unregister_restore_previous_providers(self):
		previousSpeech = self.mathPres.speechProvider
		previousInteraction = self.mathPres.interactionProvider

		self.module._register()

		self.assertTrue(self.module.isProviderActive())
		self.module._unregister()
		self.assertIs(self.mathPres.speechProvider, previousSpeech)
		self.assertIs(self.mathPres.interactionProvider, previousInteraction)

	def test_register_recovers_after_slots_are_replaced(self):
		originalSpeech = self.mathPres.speechProvider
		originalInteraction = self.mathPres.interactionProvider
		self.module._register()
		replacementSpeech = object()
		replacementInteraction = object()
		self.mathPres.speechProvider = replacementSpeech
		self.mathPres.interactionProvider = replacementInteraction

		self.module._register()

		self.assertTrue(self.module.isProviderActive())
		self.assertIn(
			"Greek Math Reader: provider was replaced; registration recovered",
			self.log.warningMessages,
		)
		self.module._unregister()
		self.assertIs(self.mathPres.speechProvider, originalSpeech)
		self.assertIs(self.mathPres.interactionProvider, originalInteraction)

	def test_focus_event_recovers_provider_and_continues_event_chain(self):
		self.module._register()
		self.mathPres.speechProvider = object()
		self.mathPres.interactionProvider = object()
		nextCalls = []
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.event_gainFocus(None, lambda: nextCalls.append(True))

		self.assertTrue(self.module.isProviderActive())
		self.assertEqual(nextCalls, [True])

	def test_focus_event_forces_exclusive_even_if_legacy_setting_is_false(self):
		self.config["greekMathReader"]["enabled"] = False
		replacementSpeech = object()
		replacementInteraction = object()
		self.mathPres.speechProvider = replacementSpeech
		self.mathPres.interactionProvider = replacementInteraction
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.event_gainFocus(None, lambda: None)

		self.assertTrue(self.module.isProviderActive())
		self.assertTrue(self.config["greekMathReader"]["enabled"])

	def test_self_test_speaks_known_greek_without_document_math(self):
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertEqual(self.speech.spokenSequences, [["χι στο τετράγωνο συν 1"]])
		self.assertIn("<msup>", self.module._provider.lastMathMl)
		self.assertTrue(self.module.isProviderActive())

	def test_self_test_forces_auto_language_switching_on(self):
		self.config["speech"] = {"autoLanguageSwitching": False}
		self.module._register()
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertTrue(self.config["speech"]["autoLanguageSwitching"])
		self.assertEqual(ui.messages, [])

	def test_self_test_does_not_warn_when_auto_language_switching_is_on(self):
		self.config["speech"] = {"autoLanguageSwitching": True}
		self.module._register()
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertEqual(ui.messages, [])

	def test_self_test_announces_recovery_from_another_math_reader(self):
		# setUp leaves a foreign provider in the speech slot; the self-test
		# reclaims it and must say so.
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertEqual(len(ui.messages), 1)
		self.assertIn("has been restored", ui.messages[0])
		self.assertTrue(self.module.isProviderActive())

	def test_self_test_ignores_stale_disabled_setting_and_restores_exclusive_reader(self):
		self.config["greekMathReader"]["enabled"] = False
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertTrue(self.config["greekMathReader"]["enabled"])
		self.assertTrue(self.module.isProviderActive())
		self.assertIn("has been restored", ui.messages[0])

	def test_self_test_forces_word_native_math_off(self):
		self.config["math"] = {"other": {"useWordNativeMath": True}}
		self.module._register()
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertFalse(self.config["math"]["other"]["useWordNativeMath"])
		self.assertEqual(ui.messages, [])

	def test_self_test_quiet_when_word_native_math_is_disabled(self):
		self.config["math"] = {"other": {"useWordNativeMath": False}}
		self.module._register()
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertEqual(ui.messages, [])

	def test_self_test_warns_when_synth_has_no_greek_voice(self):
		self.config["speech"] = {"autoLanguageSwitching": True}
		self.module.getGreekVoiceSupport = lambda: False
		self.module._register()
		ui = sys.modules["ui"]
		plugin = object.__new__(self.module.GlobalPlugin)

		plugin.script_testGreekMath(None)

		self.assertEqual(len(ui.messages), 1)
		self.assertIn("no Greek voice installed", ui.messages[0])

	def test_delayed_startup_registration_recovers_from_later_addon(self):
		plugin = self.module.GlobalPlugin()
		self.assertEqual(len(self.callLaterHandles), 1)
		self.mathPres.speechProvider = object()
		self.mathPres.interactionProvider = object()

		self.callLaterHandles[0].run()

		self.assertTrue(self.module.isProviderActive())
		self.assertIsNone(plugin._lateRegistration)
		self.assertIsNotNone(plugin._providerWatchdog)

	def test_watchdog_recovers_provider_without_a_focus_event(self):
		plugin = self.module.GlobalPlugin()
		self.callLaterHandles[0].run()
		watchdog = plugin._providerWatchdog
		self.mathPres.speechProvider = object()
		self.mathPres.interactionProvider = object()

		watchdog.run()

		self.assertTrue(self.module.isProviderActive())
		self.assertIsNotNone(plugin._providerWatchdog)

	def test_mathcat_speech_is_redirected_and_restored(self):
		plugin = self.module.GlobalPlugin()
		mathCat = self.MathCAT()
		mathMl = "<math><mi>x</mi></math>"

		self.assertEqual(
			mathCat.getSpeechForMathMl(mathMl),
			["χι στο τετράγωνο συν 1"],
		)
		self.assertEqual(self.originalMathCatCalls, [])

		plugin.terminate()
		self.assertEqual(mathCat.getSpeechForMathMl(mathMl), ["English MathCAT speech"])
		self.assertEqual(self.originalMathCatCalls, [mathMl])

	def test_mathcat_fallback_ignores_stale_disabled_setting(self):
		plugin = self.module.GlobalPlugin()
		self.config["greekMathReader"]["enabled"] = False
		mathMl = "<math><mi>x</mi></math>"

		self.assertEqual(
			self.MathCAT().getSpeechForMathMl(mathMl),
			["χι στο τετράγωνο συν 1"],
		)
		self.assertEqual(self.originalMathCatCalls, [])
		plugin.terminate()

	def test_exclusive_guard_blocks_foreign_speech_and_interaction_but_allows_braille(self):
		plugin = self.module.GlobalPlugin()
		foreign = object()

		self.mathPres.registerProvider(foreign, speech=True, braille=True, interaction=True)

		self.assertTrue(self.module.isProviderActive())
		self.assertIs(self.mathPres.brailleProvider, foreign)
		plugin.terminate()

	def test_mathpres_terminate_immediately_reasserts_exclusive_provider(self):
		plugin = self.module.GlobalPlugin()

		self.mathPres.terminate()

		self.assertEqual(self.mathPres.terminateCalls, 1)
		self.assertTrue(self.module.isProviderActive())
		plugin.terminate()

	def test_reset_restores_recommended_settings_and_all_routing(self):
		self.config["greekMathReader"].update(
			enabled=False,
			verbosity=2,
			decimalComma=False,
			forceGreekLanguage=False,
		)
		self.config["speech"] = {"autoLanguageSwitching": False}
		self.config["math"] = {"other": {"useWordNativeMath": True}}

		self.module.resetRecommendedDefaults()

		self.assertEqual(self.config["greekMathReader"]["verbosity"], 1)
		self.assertTrue(self.config["greekMathReader"]["decimalComma"])
		self.assertTrue(self.config["greekMathReader"]["enabled"])
		self.assertTrue(self.config["greekMathReader"]["forceGreekLanguage"])
		self.assertTrue(self.config["speech"]["autoLanguageSwitching"])
		self.assertFalse(self.config["math"]["other"]["useWordNativeMath"])
		self.assertEqual(self.config["UIA"]["allowInMSWord"], 3)
		self.assertTrue(self.module.isProviderActive())
		self.module._removeMathPresGuards()
		self.module._removeMathCatSpeechFallback()
		self.module._unregister()

	def test_math_object_with_mathml_bypasses_english_accessible_name(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			role=self.controlTypes.Role.MATH,
			mathMl="<math><mi>x</mi></math>",
			name="x squared",
			_hasNavigableText=True,
			appModule=types.SimpleNamespace(appName="browser"),
		)

		sequence = self.speechCore.getObjectSpeech(obj)

		self.assertEqual(sequence, ["χι στο τετράγωνο συν 1"])
		self.assertEqual(self.originalObjectSpeechCalls, [])
		plugin.terminate()

	def test_math_object_without_mathml_keeps_application_fallback(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			role=self.controlTypes.Role.MATH,
			name="x squared",
			_hasNavigableText=True,
			appModule=types.SimpleNamespace(appName="browser"),
		)

		sequence = self.speechCore.getObjectSpeech(obj)

		self.assertEqual(sequence, ["English accessible math"])
		self.assertEqual(self.originalObjectSpeechCalls, [obj])
		plugin.terminate()

	def test_math_object_hook_preserves_lock_screen_security(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			role=self.controlTypes.Role.MATH,
			mathMl="<math><mi>x</mi></math>",
			belowLockScreen=True,
		)

		sequence = self.speechCore.getObjectSpeech(obj)

		self.assertEqual(sequence, [])
		self.assertEqual(self.originalObjectSpeechCalls, [obj])
		plugin.terminate()

	def test_math_object_hook_delegates_only_cache_requests(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			role=self.controlTypes.Role.MATH,
			mathMl="<math><mi>x</mi></math>",
		)

		sequence = self.speechCore.getObjectSpeech(
			obj,
			reason=self.controlTypes.OutputReason.ONLYCACHE,
		)

		self.assertEqual(sequence, ["English accessible math"])
		self.assertEqual(self.originalObjectSpeechCalls, [obj])
		plugin.terminate()

	def test_word_character_speech_replaces_native_english_text_with_mathml(self):
		plugin = self.module.GlobalPlugin()
		wordInfoClass = type("WordDocumentTextInfo", (), {})
		wordInfoClass.__module__ = "NVDAObjects.UIA.wordDocument"
		info = wordInfoClass()
		info.obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(
				appName="winword",
				productName="Microsoft Office Word",
				productVersion="16.0.19000",
			),
		)
		info.mathMl = "<math><msup><mi>χ</mi><mn>2</mn></msup><mo>+</mo><mn>1</mn></math>"

		sequences = list(
			self.speechCore.getTextInfoSpeech(
				info,
				unit="character",
				reason="caret",
			)
		)

		self.assertEqual(sequences, [["χι στο τετράγωνο συν 1"]])
		self.assertEqual(
			self.originalTextInfoSpeechCalls,
			[(info, "character", "onlyCache")],
		)
		plugin.terminate()

	def test_textinfo_math_appender_uses_greek_provider_directly(self):
		plugin = self.module.GlobalPlugin()
		info = types.SimpleNamespace(getMathMl=lambda field: "<math><mi>χ</mi></math>")
		sequence = []

		self.speechCore._extendSpeechSequence_addMathForTextInfo(sequence, info, {})

		self.assertEqual(sequence, ["χι στο τετράγωνο συν 1"])
		plugin.terminate()

	def test_word_character_speech_translates_native_terms_when_mathml_is_absent(self):
		plugin = self.module.GlobalPlugin()
		wordInfoClass = type("WordDocumentTextInfo", (), {})
		wordInfoClass.__module__ = "NVDAObjects.UIA.wordDocument"
		info = wordInfoClass()
		info.obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(appName="winword"),
			WinwordSelectionObject=None,
		)
		originalGetWordComMathContext = self.module._getWordComMathContext
		self.module._getWordComMathContext = lambda obj, **kwargs: (None, True)

		try:
			sequences = list(
				self.speechCore.getTextInfoSpeech(
					info,
					unit="character",
					reason="caret",
				)
			)
		finally:
			self.module._getWordComMathContext = originalGetWordComMathContext

		self.assertEqual(sequences, [["χ στο τετράγωνο συν 1"]])
		plugin.terminate()

	def test_word_prose_with_math_words_is_never_translated(self):
		plugin = self.module.GlobalPlugin()
		wordInfoClass = type("WordDocumentTextInfo", (), {})
		wordInfoClass.__module__ = "NVDAObjects.UIA.wordDocument"
		info = wordInfoClass()
		info.nativeSpeech = "Use plus and times in this paragraph"
		info.obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(appName="winword"),
			WinwordSelectionObject=None,
		)

		sequences = list(
			self.speechCore.getTextInfoSpeech(
				info,
				unit="character",
				reason="caret",
			)
		)

		self.assertEqual(sequences, [["Use plus and times in this paragraph"]])
		plugin.terminate()

	def test_confirmed_word_math_notification_never_falls_through_in_english(self):
		plugin = self.module.GlobalPlugin()
		wordInfoClass = type("WordDocumentTextInfo", (), {})
		wordInfoClass.__module__ = "NVDAObjects.UIA.wordDocument"
		info = wordInfoClass()
		obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(appName="winword"),
			WinwordSelectionObject=object(),
			makeTextInfo=lambda position: info,
		)
		info.obj = obj
		originalGetWordComMathContext = self.module._getWordComMathContext
		self.module._getWordComMathContext = lambda candidate, **kwargs: (None, True)
		api = sys.modules["api"]
		originalGetFocusObject = api.getFocusObject
		api.getFocusObject = lambda: obj
		nextCalls = []

		try:
			plugin.event_UIA_notification(
				obj,
				lambda: nextCalls.append(True),
				displayString="χ squared plus 1",
				activityId="WordEquation",
			)
		finally:
			self.module._getWordComMathContext = originalGetWordComMathContext
			api.getFocusObject = originalGetFocusObject

		self.assertEqual(nextCalls, [])
		self.assertEqual(self.speech.spokenSequences, [["χι στο τετράγωνο συν 1"]])
		self.assertIn("<mtext>χ squared plus 1</mtext>", self.module._provider.lastMathMl)
		plugin.terminate()

	def test_final_speech_filter_catches_word_line_route_and_preserves_commands(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(appName="winword"),
			belowLockScreen=False,
		)
		api = sys.modules["api"]
		originalGetFocusObject = api.getFocusObject
		api.getFocusObject = lambda: obj
		originalGetWordMathContext = self.module._getWordMathContextAtCaret
		self.module._getWordMathContextAtCaret = lambda candidate, **kwargs: (None, True)
		callback = object()
		endUtterance = object()

		try:
			self.speech.speak([callback, "χ squared plus 1", endUtterance])
		finally:
			self.module._getWordMathContextAtCaret = originalGetWordMathContext
			api.getFocusObject = originalGetFocusObject

		spoken = self.speech.spokenSequences[-1]
		self.assertIs(spoken[0], callback)
		self.assertEqual(spoken[1], "χι στο τετράγωνο συν 1")
		self.assertIs(spoken[2], endUtterance)
		self.assertEqual(self.module._finalWordSpeechReplacementCount, 1)
		plugin.terminate()

	def test_final_speech_filter_rejects_ordinary_word_prose_inside_equation(self):
		plugin = self.module.GlobalPlugin()
		obj = types.SimpleNamespace(
			appModule=types.SimpleNamespace(appName="winword"),
			belowLockScreen=False,
		)
		api = sys.modules["api"]
		originalGetFocusObject = api.getFocusObject
		api.getFocusObject = lambda: obj
		originalGetWordMathContext = self.module._getWordMathContextAtCaret
		self.module._getWordMathContextAtCaret = lambda candidate, **kwargs: (None, True)

		try:
			self.speech.speak(["Use plus to add values"])
		finally:
			self.module._getWordMathContextAtCaret = originalGetWordMathContext
			api.getFocusObject = originalGetFocusObject

		self.assertEqual(self.speech.spokenSequences[-1], ["Use plus to add values"])
		plugin.terminate()

	def test_repeated_latex_command_enters_interaction(self):
		plugin = object.__new__(self.module.GlobalPlugin)
		calls = []
		plugin._readLatex = lambda interact=False: calls.append(interact)

		plugin.script_readLatex(None)
		self.scriptHandler.repeatCount = 1
		plugin.script_readLatex(None)

		self.assertEqual(calls, [False, True])


if __name__ == "__main__":
	unittest.main()
