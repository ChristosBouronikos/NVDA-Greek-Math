# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 3 or later.
# See the file COPYING.txt for more details.
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

"""An optional neural synthesizer, listed beside eSpeak NG and Windows OneCore.

This driver only appears usable once the user has downloaded a runtime and at
least one voice from the add-on's settings; ``check`` reports False until then,
so NVDA never offers a synthesizer that cannot speak.

Speech is synthesised on a worker thread one sentence at a time and fed to
NVDA's wave player as it is produced. Generating a whole utterance before
playing any of it would put the model's full synthesis time in front of the
first word, which is the difference between a usable and an unusable screen
reader.
"""

from collections import OrderedDict
import os
import queue
import sys
import threading

import addonHandler
import nvwave
import synthDriverHandler
from logHandler import log
from speech.commands import BreakCommand, IndexCommand, LangChangeCommand, RateCommand
from synthDriverHandler import SynthDriver, VoiceInfo, synthDoneSpeaking, synthIndexReached

addonHandler.initTranslation()


def _importManager():
	"""Import the voice manager from the add-on's global plugin package."""
	try:
		from globalPlugins.greekMathReader.neural.manager import VoiceManager

		return VoiceManager
	except ImportError:
		pass
	try:
		from greekMathReader.neural.manager import VoiceManager

		return VoiceManager
	except ImportError:
		pass
	addonRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	for candidate in (
		os.path.join(addonRoot, "globalPlugins", "greekMathReader"),
		os.path.join(addonRoot, "globalPlugins"),
		addonRoot,
	):
		if candidate not in sys.path:
			sys.path.insert(0, candidate)
	try:
		from neural.manager import VoiceManager

		return VoiceManager
	except ImportError:
		from greekMathReader.neural.manager import VoiceManager

		return VoiceManager


#: Break commands shorter than this are not worth a separate silence buffer.
_MIN_BREAK_MS = 10

#: NVDA's wave player reports a buffer as done once it has been played, so an
#: index rides on a buffer this short. Inaudible, but reliably scheduled.
_INDEX_TICK_MS = 2

_CHANNELS = 1
_BITS_PER_SAMPLE = 16


def _prosodyMultiplier(command):
	"""Return the speed factor a relative prosody command asks for."""
	try:
		if command.isDefault():
			return 1.0
	except Exception:
		pass
	multiplier = getattr(command, "multiplier", None)
	try:
		multiplier = float(multiplier)
	except (TypeError, ValueError):
		return 1.0
	return multiplier if multiplier > 0 else 1.0

#: Sentence ends. Both semicolons are deliberate: ASCII ";" and U+037E, the
#: Greek question mark. "·" is the Greek ano teleia.
_CHUNK_TERMINATORS = ".;!?:;·\n"

#: Longest chunk synthesised in one call when no terminator is found.
_MAX_CHUNK_CHARACTERS = 200


def splitIntoChunks(text, limit=_MAX_CHUNK_CHARACTERS):
	"""Split ``text`` into sentence-sized pieces for incremental synthesis.

	A terminator only ends a chunk when whitespace or the end of the text
	follows it, so "3.14" and "2:3" are not torn in half; a decimal point spoken
	mid-number would otherwise become a chunk boundary and be heard as a pause
	in the middle of a figure.
	"""
	chunks = []
	current = ""
	length = len(text)
	for position, character in enumerate(text):
		current += character
		atEnd = position + 1 >= length
		endsWord = atEnd or text[position + 1].isspace()
		if character in _CHUNK_TERMINATORS and endsWord and len(current.strip()) > 1:
			chunks.append(current)
			current = ""
		elif len(current) >= limit and character.isspace():
			chunks.append(current)
			current = ""
	if current.strip():
		chunks.append(current)
	return [chunk for chunk in chunks if chunk.strip()]


class SynthDriver(synthDriverHandler.SynthDriver):
	name = "greekMathVoice"
	# Translators: The name of this synthesizer in NVDA's synthesizer list.
	description = _("Neural Voices - by Bouronikos hristos")

	supportedSettings = (
		SynthDriver.VoiceSetting(),
		SynthDriver.RateSetting(),
		SynthDriver.RateBoostSetting(),
		SynthDriver.VolumeSetting(),
	)
	supportedCommands = {IndexCommand, BreakCommand, LangChangeCommand, RateCommand}
	supportedNotifications = {synthIndexReached, synthDoneSpeaking}

	@classmethod
	def check(cls):
		"""Only offer this synthesizer when it is enabled and usable.

		NVDA calls this to decide whether to list the synthesizer at all, so it
		has to stay quiet and quick: a user who never enables neural voices
		should not see an entry that cannot speak.
		"""
		try:
			import config

			if not config.conf["greekMathReader"]["neuralVoicesEnabled"]:
				return False
		except Exception:
			# The add-on section may not exist yet during early NVDA startup.
			return False
		try:
			manager = _importManager()()
			ready = manager.isReady()
			if not ready:
				log.debug(
					"greekMathVoice: check() returned False — "
					"runtimeInstalled=%s, installedVoices=%s, configPath=%r, platform=%r",
					manager.isRuntimeInstalled(),
					[v.id for v in manager.installedVoices()],
					manager.configPath,
					manager.platformKey,
				)
			return ready
		except Exception:
			log.debugWarning("greekMathVoice: check() failed", exc_info=True)
			return False

	def __init__(self):
		super().__init__()
		self._manager = _importManager()()
		self._engine = None
		self._rate = 50
		self._rateBoost = False
		self._volume = 100
		self._language = ""
		self._voiceId = ""
		self._player = None
		self._queue = queue.Queue()
		# Bumped on cancel so audio queued for a superseded utterance is dropped
		# instead of being played after the user has moved on.
		self._generation = 0
		self._lock = threading.Lock()
		self._thread = threading.Thread(target=self._run, name="greekMathVoice", daemon=True)
		self._thread.start()
		voices = self._manager.installedVoices()
		if not voices:
			raise RuntimeError("no neural voice has been downloaded")
		self.voice = voices[0].id

	# -- settings ------------------------------------------------------------

	def _get_availableVoices(self):
		voices = OrderedDict()
		for voice in self._manager.installedVoices():
			language = voice.languages[0] if voice.languages else None
			voices[voice.id] = VoiceInfo(voice.id, voice.label, language)
		return voices

	def _get_voice(self):
		return self._voiceId

	def _set_voice(self, value):
		if value == self._voiceId:
			return
		installed = {voice.id for voice in self._manager.installedVoices()}
		if value not in installed:
			return
		self.cancel()
		with self._lock:
			if self._engine is not None:
				try:
					self._engine.close()
				except Exception:
					pass
			self._engine = None
			self._voiceId = value
			self._closePlayer()

	def _get_rate(self):
		return self._rate

	def _set_rate(self, value):
		self._rate = max(0, min(100, int(value)))

	def _get_rateBoost(self):
		return self._rateBoost

	def _set_rateBoost(self, value):
		self._rateBoost = bool(value)

	def _get_volume(self):
		return self._volume

	def _set_volume(self, value):
		self._volume = max(0, min(100, int(value)))

	@property
	def _speed(self):
		"""Map NVDA's 0-100 rate onto the model's speed multiplier.

		50 is the model's natural pace, so the scale is deliberately asymmetric:
		below 50 it slows towards half speed, above 50 it accelerates towards
		2.5x, and the rate boost extends that for users who read very fast.
		"""
		if self._rate <= 50:
			speed = 0.5 + (self._rate / 50.0) * 0.5
		else:
			speed = 1.0 + ((self._rate - 50) / 50.0) * 1.5
		if self._rateBoost:
			speed *= 1.8
		return max(0.3, min(6.0, speed))

	# -- speech --------------------------------------------------------------

	def _ensureEngine(self):
		if self._engine is not None:
			return self._engine
		self._engine = self._manager.createEngine(self._voiceId)
		return self._engine

	def _ensurePlayer(self, sampleRate):
		"""Create the wave player, tolerating NVDA's changing signature.

		``WavePlayer`` gained and lost keyword arguments across the NVDA range
		this add-on supports, so the keyword form is tried first and the
		positional form is used as a fallback.
		"""
		if self._player is not None:
			return self._player
		rate = int(sampleRate) if sampleRate else 16000
		try:
			self._player = nvwave.WavePlayer(
				channels=_CHANNELS, samplesPerSec=rate, bitsPerSample=_BITS_PER_SAMPLE
			)
		except TypeError:
			self._player = nvwave.WavePlayer(_CHANNELS, rate, _BITS_PER_SAMPLE)
		return self._player

	def _closePlayer(self):
		if self._player is None:
			return
		try:
			self._player.stop()
		except Exception:
			pass
		self._player = None

	def speak(self, speechSequence):
		"""Queue an utterance, preserving the indexes NVDA asked us to report."""
		with self._lock:
			generation = self._generation
		language = self._language
		# The add-on's own math speech asks for a relative rate, so honour a
		# RateCommand for the rest of the utterance rather than dropping it.
		multiplier = 1.0
		text = ""

		def flush():
			nonlocal text
			for chunk in splitIntoChunks(text):
				self._queue.put((generation, "speak", chunk, language, multiplier))
			text = ""

		for item in speechSequence:
			if isinstance(item, str):
				text += item
			elif isinstance(item, IndexCommand):
				flush()
				self._queue.put((generation, "index", item.index, language, multiplier))
			elif isinstance(item, BreakCommand):
				flush()
				if item.time >= _MIN_BREAK_MS:
					self._queue.put((generation, "break", item.time, language, multiplier))
			elif isinstance(item, RateCommand):
				flush()
				multiplier = _prosodyMultiplier(item)
			elif isinstance(item, LangChangeCommand):
				flush()
				# Multilingual models pick their language per utterance; the
				# add-on's own math speech relies on this to stay Greek.
				language = (item.lang or "").split("_")[0].split("-")[0].lower()
		flush()
		self._queue.put((generation, "done", None, language, multiplier))

	def _run(self):
		while True:
			item = self._queue.get()
			if item is None:
				return
			generation, kind, payload, language, multiplier = item
			with self._lock:
				if generation != self._generation:
					continue
			try:
				self._handle(kind, payload, language, multiplier, generation)
			except Exception:
				log.error("greekMathVoice: could not speak", exc_info=True)
				if kind == "done":
					synthDoneSpeaking.notify(synth=self)

	def _handle(self, kind, payload, language, multiplier, generation):
		if kind == "done":
			try:
				player = self._player
				if player is not None:
					# Block until the queued audio has actually been heard, so NVDA
					# is not told the utterance finished while it is still playing.
					player.idle()
			except Exception:
				log.debugWarning("greekMathVoice: error idling player", exc_info=True)
			finally:
				synthDoneSpeaking.notify(synth=self)
			return
		if kind == "index":
			self._notifyIndexAfterQueuedAudio(payload)
			return
		if kind == "break":
			try:
				engine = self._ensureEngine()
				rate = getattr(engine, "sampleRate", 0) or 16000
				self._ensurePlayer(rate).feed(self._silence(rate, payload))
			except Exception:
				log.error("greekMathVoice: break failed", exc_info=True)
			return
		engine = self._ensureEngine()
		audio = engine.synthesize(
			payload,
			speed=self._speed * multiplier,
			language=language or None,
			volume=self._volume / 100.0,
		)
		with self._lock:
			if generation != self._generation:
				return
		if not audio:
			return
		rate = getattr(engine, "sampleRate", 0) or 16000
		self._ensurePlayer(rate).feed(audio)

	@staticmethod
	def _silence(sampleRate, milliseconds):
		frames = int(sampleRate * milliseconds / 1000.0)
		return b"\0" * (frames * (_BITS_PER_SAMPLE // 8))

	def _notifyIndexAfterQueuedAudio(self, index):
		"""Report an index once the audio queued before it has been played.

		The notification is hung off a very short silent buffer rather than an
		empty one: an empty buffer is not necessarily scheduled, and NVDA relies
		on these callbacks to keep the caret and braille in step with speech.
		"""
		player = self._player
		engine = self._engine
		rate = getattr(engine, "sampleRate", 0) or 16000
		if player is None or engine is None:
			synthIndexReached.notify(synth=self, index=index)
			return
		try:
			player.feed(
				self._silence(rate, _INDEX_TICK_MS),
				onDone=lambda index=index: synthIndexReached.notify(synth=self, index=index),
			)
		except Exception:
			synthIndexReached.notify(synth=self, index=index)

	def cancel(self):
		with self._lock:
			self._generation += 1
		while True:
			try:
				self._queue.get_nowait()
			except queue.Empty:
				break
		player = self._player
		if player is not None:
			try:
				player.stop()
			except Exception:
				pass

	def pause(self, switch):
		player = self._player
		if player is not None:
			try:
				player.pause(switch)
			except Exception:
				pass

	def terminate(self):
		self.cancel()
		self._queue.put(None)
		with self._lock:
			if self._engine is not None:
				try:
					self._engine.close()
				except Exception:
					pass
				self._engine = None
		self._closePlayer()
		super().terminate()
