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
"""Tests for the real provider's NVDA speech-sequence adaptation."""

import builtins
import importlib.util
import sys
import types
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"
PACKAGE_NAME = "greekMathReaderProviderSpeechTest"
_MISSING = object()


class NVDAStyleConfigSection:
	"""Match AggregatedSection's items API without a dict keys() method.

	A plain dict fixture concealed the 2.5.0 last-reading speech regression.
	"""
	def __init__(self, values):
		self.values = dict(values)

	def __iter__(self):
		return iter(self.values)

	def __getitem__(self, key):
		return self.values[key]

	def __setitem__(self, key, value):
		self.values[key] = value

	def get(self, key, default=None):
		return self.values.get(key, default)

	def items(self):
		return self.values.items()

	def update(self, *args, **kwargs):
		self.values.update(*args, **kwargs)

	def copy(self):
		return dict(self.items())

	def __eq__(self, other):
		return hasattr(other, "items") and dict(self.items()) == dict(other.items())


class TestProviderSpeechSequence(unittest.TestCase):
	def setUp(self):
		self.savedModules = {}
		self.savedTranslation = getattr(builtins, "_", _MISSING)
		builtins._ = lambda message: message

		addonHandler = types.ModuleType("addonHandler")
		addonHandler.initTranslation = lambda: None

		config = types.ModuleType("config")
		config.conf = {
			"greekMathReader": NVDAStyleConfigSection({
				"verbosity": 1,
				"decimalComma": True,
				"forceGreekLanguage": True,
			}),
			"speech": {"autoLanguageSwitching": True},
		}
		self.config = config.conf

		mathPres = types.ModuleType("mathPres")
		mathPres.MathPresentationProvider = object

		class FakeLog:
			def __init__(log):
				log.warnings = []

			def warning(log, message):
				log.warnings.append(message)

			def info(log, message):
				pass

			def error(log, message):
				pass

			def exception(log, message):
				pass

		logHandler = types.ModuleType("logHandler")
		logHandler.log = self.log = FakeLog()

		commands = types.ModuleType("speech.commands")

		class BreakCommand:
			def __init__(command, time=0):
				command.time = time

		class LangChangeCommand:
			def __init__(command, lang):
				command.lang = lang

		class RateCommand:
			def __init__(command, multiplier=1.0):
				command.multiplier = multiplier

		commands.BreakCommand = BreakCommand
		commands.LangChangeCommand = LangChangeCommand
		commands.RateCommand = RateCommand
		speech = types.ModuleType("speech")
		speech.__path__ = []

		self.synth = types.SimpleNamespace(languageIsSupported=lambda language: True)
		synthDriverHandler = types.ModuleType("synthDriverHandler")
		synthDriverHandler.getSynth = lambda: self.synth

		package = types.ModuleType(PACKAGE_NAME)
		package.__path__ = [str(PACKAGE_DIR)]

		stubs = {
			"addonHandler": addonHandler,
			"config": config,
			"mathPres": mathPres,
			"logHandler": logHandler,
			"speech": speech,
			"speech.commands": commands,
			"synthDriverHandler": synthDriverHandler,
			PACKAGE_NAME: package,
		}
		for name, module in stubs.items():
			self.savedModules[name] = sys.modules.get(name, _MISSING)
			sys.modules[name] = module

		spec = importlib.util.spec_from_file_location(
			f"{PACKAGE_NAME}.provider",
			PACKAGE_DIR / "provider.py",
		)
		self.provider = importlib.util.module_from_spec(spec)
		self.savedModules[spec.name] = sys.modules.get(spec.name, _MISSING)
		sys.modules[spec.name] = self.provider
		spec.loader.exec_module(self.provider)
		self.commands = commands
		self.provider.automaticBackend = type(self.provider.automaticBackend)()

	def tearDown(self):
		for name, previous in self.savedModules.items():
			if previous is _MISSING:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = previous
		if self.savedTranslation is _MISSING:
			del builtins._
		else:
			builtins._ = self.savedTranslation

	def test_nvda_config_contract_does_not_support_direct_dict_conversion(self):
		section = self.config["greekMathReader"]
		self.assertFalse(hasattr(section, "keys"))
		with self.assertRaises(ValueError):
			dict(section)
		self.assertEqual(dict(section.items())["verbosity"], 1)

	def test_last_reading_works_with_nvda_configuration_section(self):
		self.provider.automaticBackend.configure(None, enabled=False)
		source = "<math><mn>3</mn><mo>+</mo><mn>5</mn></math>"
		sequence = self.provider.GreekMathProvider().getSpeechForMathMl(source)
		self.assertEqual(" ".join(item for item in sequence if isinstance(item, str)), "3 συν 5")
		self.assertEqual(self.provider.lastReading["actualSpeech"], "3 συν 5")
		self.assertEqual(self.provider.lastReading["settings"], dict(self.config["greekMathReader"].items()))

	def test_optional_reading_record_failure_cannot_suppress_equation_or_error_speech(self):
		self.provider.automaticBackend.configure(None, enabled=False)
		class BrokenSnapshot(NVDAStyleConfigSection):
			def items(self):
				raise RuntimeError("Configuration snapshot unavailable")
		self.config["greekMathReader"] = BrokenSnapshot(dict(self.config["greekMathReader"].items()))
		provider = self.provider.GreekMathProvider()
		for source in ("<math><mn>3</mn><mo>+</mo><mn>5</mn></math>", "<math><"):
			with self.subTest(source=source):
				sequence = provider.getSpeechForMathMl(source)
				self.assertTrue(any(isinstance(item, str) and item.strip() for item in sequence))
				self.assertIsNone(self.provider.lastReading)

	def test_decimal_digit_preference_reaches_speech(self):
		self.config["greekMathReader"]["decimalDigits"] = True
		sequence = self.provider.GreekMathProvider().getSpeechForMathMl(
			'<math><mn>1.025</mn><mo>+</mo><mi>G</mi></math>'
		)
		self.assertEqual(
			" ".join(item for item in sequence if isinstance(item, str)),
			"ένα κόμμα μηδέν δύο πέντε συν τζί",
		)

	def test_flat_equation_output_contains_words_not_suppressible_punctuation(self):
		self.provider.automaticBackend.configure(None, enabled=False)
		for tag in ("mtext", "mi", "mn"):
			with self.subTest(tag=tag):
				sequence = self.provider.GreekMathProvider().getSpeechForMathMl(
					f"<math><{tag}>3+5=8</{tag}></math>"
				)
				self.assertEqual(
					" ".join(item for item in sequence if isinstance(item, str)),
					"3 συν 5 ίσον 8",
				)
				self.assertEqual(sequence[0].lang, "el_GR")
				self.assertIsNone(sequence[-1].lang)

	def test_greek_voice_metadata_supports_driver_names_and_locale_variants(self):
		# API contract checks, not execution of the Windows synthesizers.
		for name, locale in (("espeak", "el"), ("oneCore", "el-GR"), ("sapi5", "el_GR"), ("sapi5_32", "el")):
			with self.subTest(driver=name):
				self.synth = types.SimpleNamespace(name=name, availableLanguages={"en_US", locale})
				self.assertTrue(self.provider.getGreekVoiceSupport())

	def test_older_driver_voice_metadata_fallback(self):
		self.synth = types.SimpleNamespace(availableVoices={
			"greek": types.SimpleNamespace(language="el-GR"),
		})
		self.assertTrue(self.provider.getGreekVoiceSupport())
		self.synth.availableVoices = {"english": types.SimpleNamespace(language="en_US")}
		self.assertFalse(self.provider.getGreekVoiceSupport())
		self.synth = types.SimpleNamespace()
		self.assertIsNone(self.provider.getGreekVoiceSupport())

	def test_empty_local_math_has_spoken_explanation_not_silence(self):
		self.provider.automaticBackend.configure(None, enabled=False)
		sequence = self.provider.GreekMathProvider().getSpeechForMathMl("<math/>")
		self.assertTrue(any(isinstance(item, str) and item.strip() for item in sequence))
		self.assertIn("Δεν υπάρχει", " ".join(item for item in sequence if isinstance(item, str)))
		self.assertEqual(sequence[0].lang, "el_GR")

	def test_empty_delegate_falls_back_to_local_equation(self):
		for empty in ([], ["  "], [self.commands.BreakCommand(time=100)]):
			with self.subTest(empty=empty):
				self._configureDelegate(empty)
				provider = self.provider.GreekMathProvider()
				sequence = provider.getSpeechForMathMl("<math><mn>3</mn><mo>+</mo><mn>5</mn></math>")
				self.assertEqual(provider.lastBackend, "local")
				self.assertEqual(" ".join(item for item in sequence if isinstance(item, str)), "3 συν 5")

	def test_sequence_uses_explicit_greek_locale(self):
		# The speech sequence accents short letter names so the synthesizer reads
		# them as one word: "χι" is spoken (and asserted) as "χί". The engine's
		# own tokens stay unaccented for the clipboard and the tests.
		sequence = self.provider.tokensToSpeechSequence(["χι"])

		self.assertIsInstance(sequence[0], self.commands.LangChangeCommand)
		self.assertEqual(sequence[0].lang, "el_GR")
		self.assertEqual(sequence[1], "χί")
		self.assertIsNone(sequence[-1].lang)

	def test_short_letter_names_are_accented_for_speech(self):
		sequence = self.provider.tokensToSpeechSequence(["ψι", "στο τετράγωνο", "συν", "ρο"])
		spoken = [item for item in sequence if isinstance(item, str)]
		self.assertEqual(spoken, ["ψί", "στο τετράγωνο", "συν", "ρό"])

	def test_relative_math_rate_has_scoped_start_and_reset(self):
		self.config["greekMathReader"]["relativeRate"] = 80
		sequence = self.provider.tokensToSpeechSequence(["χι"])
		rates = [item.multiplier for item in sequence if isinstance(item, self.commands.RateCommand)]
		self.assertEqual(rates, [0.8, 1.0])

	def test_preposition_se_is_not_respelled(self):
		# "σε" (raised to) must stay the preposition, not become the letter name.
		sequence = self.provider.tokensToSpeechSequence(["χι", "υψωμένο σε", "ψι"])
		spoken = [item for item in sequence if isinstance(item, str)]
		self.assertEqual(spoken, ["χί", "υψωμένο σε", "ψί"])

	def test_missing_greek_voice_is_logged_once(self):
		self.synth.languageIsSupported = lambda language: False

		self.provider.tokensToSpeechSequence(["χι"])
		self.provider.tokensToSpeechSequence(["ψι"])

		matching = [message for message in self.log.warnings if "no installed Greek voice" in message]
		self.assertEqual(len(matching), 1)

	def test_missing_greek_voice_does_not_receive_unsupported_language_commands(self):
		self.synth.languageIsSupported = lambda language: False
		sequence = self.provider.tokensToSpeechSequence(["συν"])
		self.assertEqual([item for item in sequence if isinstance(item, str)], ["συν"])
		self.assertFalse(any(isinstance(item, self.commands.LangChangeCommand) for item in sequence))

	def test_changing_synthesizer_allows_a_new_missing_voice_warning(self):
		self.synth = types.SimpleNamespace(name="sapi5", voice="english64", languageIsSupported=lambda language: False)
		self.provider.tokensToSpeechSequence(["συν"])
		self.synth = types.SimpleNamespace(name="sapi5_32", voice="english32", languageIsSupported=lambda language: False)
		self.provider.tokensToSpeechSequence(["συν"])
		self.assertEqual(len([message for message in self.log.warnings if "no installed Greek voice" in message]), 2)

	def _configureDelegate(self, sequence):
		requests = []

		def getSpeech(mathMl):
			requests.append(mathMl)
			return sequence

		delegate = types.SimpleNamespace(
			GetSupportedLanguages=lambda: ["el"],
			SetPreference=lambda name, value: None,
			getSpeechForMathMl=getSpeech,
		)
		self.assertTrue(self.provider.GreekMathProvider().configureMathCatDelegate(delegate))
		return delegate, requests

	def test_delegate_speech_gets_scoped_greek_and_pronunciation(self):
		pause = self.commands.BreakCommand(time=100)
		self._configureDelegate([
			self.commands.LangChangeCommand("en_US"), "χι", pause,
			self.commands.LangChangeCommand(None), "συν ψι",
		])
		provider = self.provider.GreekMathProvider()
		sequence = provider.getSpeechForMathMl("<math><mi>x</mi></math>")
		self.assertEqual(provider.lastBackend, "mathcat-el")
		self.assertEqual([item for item in sequence if isinstance(item, str)], ["χί", "συν ψί"])
		self.assertEqual(
			[item.lang for item in sequence if isinstance(item, self.commands.LangChangeCommand)],
			["el_GR", None],
		)
		self.assertIs(sequence[2], pause)
		self.assertIsNone(sequence[-1].lang)
		self.assertEqual(self.provider.lastReading["actualSpeech"], "χί συν ψί")

	def test_delegate_preserves_language_commands_when_forcing_is_disabled(self):
		self.config["greekMathReader"]["forceGreekLanguage"] = False
		language = self.commands.LangChangeCommand("el_GR")
		self._configureDelegate([language, "χι"])
		sequence = self.provider.GreekMathProvider().getSpeechForMathMl("<math/>")
		self.assertEqual(sequence, [language, "χί"])

	def test_local_preferences_bypass_delegate(self):
		preferences = (
			("verbosity", 0), ("verbosity", 2), ("decimalComma", False),
			("terminologyProfile", "school"), ("terminologyProfile", "university"),
			("domainHint", "quantum_physics"),
			("terminologyOverrides", '{"power": "δοκιμή"}'),
		)
		defaults = dict(self.config["greekMathReader"].items())
		for setting, value in preferences:
			with self.subTest(setting=setting, value=value):
				self.config["greekMathReader"] = NVDAStyleConfigSection(dict(defaults, **{setting: value}))
				_delegate, requests = self._configureDelegate(["English delegate speech"])
				provider = self.provider.GreekMathProvider()
				sequence = provider.getSpeechForMathMl('<math><mi>x</mi><mo>+</mo><mn>1</mn></math>')
				self.assertEqual(requests, [])
				self.assertEqual(provider.lastBackend, "local")
				self.assertEqual([item for item in sequence if isinstance(item, str)], ["χί", "συν", "1"])

	def test_language_reselection_failure_uses_local_greek_operators(self):
		delegate, requests = self._configureDelegate(["English delegate speech"])
		delegate.SetPreference = lambda name, value: False
		provider = self.provider.GreekMathProvider()
		sequence = provider.getSpeechForMathMl(
			'<math><mi>x</mi><mo>+</mo><mn>1</mn><mo>−</mo><mi>ψ</mi></math>'
		)
		self.assertEqual(requests, [])
		self.assertEqual(provider.lastBackend, "local")
		self.assertEqual(
			[item for item in sequence if isinstance(item, str)],
			["χί", "συν", "1", "πλην", "ψί"],
		)


if __name__ == "__main__":
	unittest.main()
