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
"""The neural synthesizer driver's chunking and rate mapping, with NVDA stubbed."""

import builtins
import importlib.util
import sys
import types
import unittest
from pathlib import Path

DRIVER_PATH = Path(__file__).parent.parent / "addon" / "synthDrivers" / "greekMathVoice.py"
_MISSING = object()


class Command:
	"""Stand-in for NVDA's speech command classes."""

	def __init__(self, **attributes):
		self.__dict__.update(attributes)


class BreakCommand(Command):
	pass


class IndexCommand(Command):
	pass


class LangChangeCommand(Command):
	pass


class RateCommand(Command):
	def isDefault(self):
		return getattr(self, "default", False)


def loadDriver():
	"""Import the driver module against stubbed NVDA packages."""
	saved = {}
	for name in ("addonHandler", "nvwave", "synthDriverHandler", "logHandler", "speech", "speech.commands"):
		saved[name] = sys.modules.get(name, _MISSING)

	addonHandler = types.ModuleType("addonHandler")
	addonHandler.initTranslation = lambda: None

	class FakeWavePlayer:
		created = []

		def __init__(self, *args, **kwargs):
			self.args = args
			self.kwargs = kwargs
			self.fed = []
			self.stopped = False
			self.idled = False
			FakeWavePlayer.created.append(self)

		def feed(self, data, onDone=None):
			self.fed.append(data)
			if onDone:
				onDone()

		def stop(self):
			self.stopped = True

		def idle(self):
			self.idled = True

	nvwave = types.ModuleType("nvwave")
	nvwave.WavePlayer = FakeWavePlayer

	class StubSetting:
		def __init__(self, *args, **kwargs):
			pass

	class StubSynthDriver:
		VoiceSetting = staticmethod(lambda *a, **k: StubSetting())
		RateSetting = staticmethod(lambda *a, **k: StubSetting())
		RateBoostSetting = staticmethod(lambda *a, **k: StubSetting())
		VolumeSetting = staticmethod(lambda *a, **k: StubSetting())

		def __init__(self):
			pass

		def terminate(self):
			pass

	class StubNotification:
		def __init__(self):
			self.calls = []

		def notify(self, **kwargs):
			self.calls.append(kwargs)

	synthDriverHandler = types.ModuleType("synthDriverHandler")
	synthDriverHandler.SynthDriver = StubSynthDriver
	synthDriverHandler.VoiceInfo = lambda *args, **kwargs: types.SimpleNamespace(id=args[0], displayName=args[1], language=args[2] if len(args) > 2 else None)
	synthDriverHandler.synthIndexReached = StubNotification()
	synthDriverHandler.synthDoneSpeaking = StubNotification()

	logHandler = types.ModuleType("logHandler")
	logHandler.log = types.SimpleNamespace(error=lambda *a, **k: None, warning=lambda *a, **k: None)

	speech = types.ModuleType("speech")
	commands = types.ModuleType("speech.commands")
	commands.BreakCommand = BreakCommand
	commands.IndexCommand = IndexCommand
	commands.LangChangeCommand = LangChangeCommand
	commands.RateCommand = RateCommand
	speech.commands = commands

	sys.modules.update(
		{
			"addonHandler": addonHandler,
			"nvwave": nvwave,
			"synthDriverHandler": synthDriverHandler,
			"logHandler": logHandler,
			"speech": speech,
			"speech.commands": commands,
		}
	)
	savedTranslation = getattr(builtins, "_", _MISSING)
	builtins._ = lambda message: message
	try:
		spec = importlib.util.spec_from_file_location("greekMathVoiceUnderTest", DRIVER_PATH)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module
	finally:
		for name, value in saved.items():
			if value is _MISSING:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value
		if savedTranslation is _MISSING:
			del builtins._
		else:
			builtins._ = savedTranslation


def setUpModule():
	raise unittest.SkipTest("Neural voices synthesizer driver commented out for future releases")


class TestDriverImports(unittest.TestCase):
	def test_the_driver_module_loads(self):
		# Guards against a typo in the driver only being found on Windows.
		self.assertTrue(hasattr(loadDriver(), "SynthDriver"))


class TestChunking(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		# staticmethod: a bare function on a class would be bound as a method.
		cls.split = staticmethod(loadDriver().splitIntoChunks)

	def test_a_sentence_is_one_chunk(self):
		self.assertEqual(self.split("ένα συν δύο"), ["ένα συν δύο"])

	def test_sentences_are_split_so_speech_can_start_sooner(self):
		self.assertEqual(len(self.split("Πρώτη πρόταση. Δεύτερη πρόταση.")), 2)

	def test_a_decimal_point_does_not_split_a_number(self):
		# A split here would be heard as a pause in the middle of a figure.
		self.assertEqual(self.split("η τιμή 3.14 είναι"), ["η τιμή 3.14 είναι"])

	def test_a_ratio_is_not_split(self):
		self.assertEqual(self.split("λόγος 2:3 τέλος"), ["λόγος 2:3 τέλος"])

	def test_the_greek_question_mark_ends_a_chunk(self):
		# U+037E, which Greek text uses where English writes "?".
		self.assertEqual(len(self.split("Τι είναι αυτό; Και μετά;")), 2)

	def test_the_ano_teleia_ends_a_chunk(self):
		self.assertEqual(len(self.split("πρώτο μέρος· δεύτερο μέρος·")), 2)

	def test_very_long_text_without_punctuation_is_still_broken_up(self):
		text = " ".join(["λέξη"] * 200)
		self.assertGreater(len(self.split(text)), 1)

	def test_whitespace_only_text_produces_nothing(self):
		self.assertEqual(self.split("   \n  "), [])


class TestRateMapping(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.module = loadDriver()

	def _speedAt(self, rate, boost=False):
		driver = self.module.SynthDriver.__new__(self.module.SynthDriver)
		driver._rate = rate
		driver._rateBoost = boost
		return driver._speed

	def test_the_middle_of_the_scale_is_the_model_s_natural_pace(self):
		self.assertAlmostEqual(self._speedAt(50), 1.0)

	def test_the_scale_is_monotonic(self):
		speeds = [self._speedAt(rate) for rate in (0, 25, 50, 75, 100)]
		self.assertEqual(speeds, sorted(speeds))

	def test_the_rate_boost_speeds_speech_up_further(self):
		self.assertGreater(self._speedAt(100, boost=True), self._speedAt(100))

	def test_speed_stays_within_a_range_the_model_can_render(self):
		for rate in (0, 100):
			for boost in (False, True):
				self.assertGreaterEqual(self._speedAt(rate, boost), 0.3)
				self.assertLessEqual(self._speedAt(rate, boost), 6.0)


class TestProsodyMultiplier(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.multiplier = staticmethod(loadDriver()._prosodyMultiplier)

	def test_a_relative_rate_command_is_honoured(self):
		self.assertAlmostEqual(self.multiplier(RateCommand(multiplier=1.5)), 1.5)

	def test_a_default_command_leaves_the_rate_alone(self):
		self.assertAlmostEqual(self.multiplier(RateCommand(multiplier=2.0, default=True)), 1.0)

	def test_a_nonsensical_multiplier_is_ignored_rather_than_silencing_speech(self):
		self.assertAlmostEqual(self.multiplier(RateCommand(multiplier=0)), 1.0)
		self.assertAlmostEqual(self.multiplier(RateCommand(multiplier=None)), 1.0)


class TestDriverDescription(unittest.TestCase):
	def test_driver_description_matches_requested_display_name(self):
		module = loadDriver()
		self.assertEqual(module.SynthDriver.description, "Neural Voices - by Bouronikos hristos")


class TestPlayerCreation(unittest.TestCase):
	def setUp(self):
		self.module = loadDriver()
		self.driver = self.module.SynthDriver.__new__(self.module.SynthDriver)
		self.driver._player = None

	def test_ensure_player_creates_wave_player_with_mono_and_valid_rate(self):
		player = self.driver._ensurePlayer(16000)
		self.assertIsNotNone(player)
		self.assertEqual(player.kwargs.get("channels"), 1)
		self.assertEqual(player.kwargs.get("samplesPerSec"), 16000)
		self.assertEqual(player.kwargs.get("bitsPerSample"), 16)

	def test_ensure_player_defaults_to_16000_when_rate_is_zero(self):
		player = self.driver._ensurePlayer(0)
		self.assertEqual(player.kwargs.get("samplesPerSec"), 16000)

	def test_close_player_stops_player_and_clears_reference(self):
		player = self.driver._ensurePlayer(16000)
		self.driver._closePlayer()
		self.assertTrue(player.stopped)
		self.assertIsNone(self.driver._player)


class TestAvailableVoices(unittest.TestCase):
	def test_available_voices_returns_ordered_dict(self):
		from collections import OrderedDict
		module = loadDriver()
		driver = module.SynthDriver.__new__(module.SynthDriver)
		voice_stub = types.SimpleNamespace(id="piper-el-rapunzelina", label="Rapunzelina", languages=["el"])
		driver._manager = types.SimpleNamespace(installedVoices=lambda: [voice_stub])
		voices = driver._get_availableVoices()
		self.assertIsInstance(voices, OrderedDict)
		self.assertIn("piper-el-rapunzelina", voices)
		self.assertEqual(voices["piper-el-rapunzelina"].displayName, "Rapunzelina")


class TestSpeechLifecycle(unittest.TestCase):
	def setUp(self):
		import threading

		self.module = loadDriver()
		self.driver = self.module.SynthDriver.__new__(self.module.SynthDriver)
		self.driver._player = None
		self.driver._engine = types.SimpleNamespace(sampleRate=16000, synthesize=lambda *a, **k: b"\x00" * 32)
		self.driver._rate = 50
		self.driver._rateBoost = False
		self.driver._volume = 100
		self.driver._generation = 1
		self.driver._lock = threading.Lock()

	def test_handle_done_calls_idle_and_notifies_synth_done_speaking(self):
		self.module.synthDoneSpeaking.calls = []
		player = self.driver._ensurePlayer(16000)
		self.driver._handle("done", None, "", 1.0, 1)
		self.assertTrue(player.idled)
		self.assertEqual(len(self.module.synthDoneSpeaking.calls), 1)

	def test_handle_speak_feeds_synthesized_audio_to_player(self):
		player = self.driver._ensurePlayer(16000)
		self.driver._handle("speak", "ένα συν δύο", "", 1.0, 1)
		self.assertEqual(len(player.fed), 1)
		self.assertEqual(player.fed[0], b"\x00" * 32)

	def test_handle_speak_error_does_not_call_synth_done_speaking_prematurely(self):
		self.module.synthDoneSpeaking.calls = []
		self.driver._engine.synthesize = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthesis failed"))
		with self.assertRaises(RuntimeError):
			self.driver._handle("speak", "ένα", "", 1.0, 1)
		# _handle does not notify on speak error, _run handles queue and notifies on done
		self.assertEqual(len(self.module.synthDoneSpeaking.calls), 0)

	def test_run_processes_queue_cleanly(self):
		import queue
		self.module.synthDoneSpeaking.calls = []
		self.driver._queue = queue.Queue()
		self.driver._queue.put((1, "speak", "ένα", "", 1.0))
		self.driver._queue.put((1, "done", None, "", 1.0))
		self.driver._queue.put(None)
		self.driver._run()
		self.assertEqual(len(self.module.synthDoneSpeaking.calls), 1)
		self.assertIsNotNone(self.driver._player)
		self.assertTrue(self.driver._player.idled)

	def test_run_with_speak_error_notifies_done_exactly_once(self):
		import queue
		self.module.synthDoneSpeaking.calls = []
		self.driver._engine.synthesize = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthesis failed"))
		self.driver._queue = queue.Queue()
		self.driver._queue.put((1, "speak", "ένα", "", 1.0))
		self.driver._queue.put((1, "done", None, "", 1.0))
		self.driver._queue.put(None)
		self.driver._run()
		# Exactly one notification from done, no duplicate from speak failure
		self.assertEqual(len(self.module.synthDoneSpeaking.calls), 1)


if __name__ == "__main__":
	unittest.main()
