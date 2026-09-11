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

"""Loading the downloaded runtime and turning text into PCM audio.

The runtime is imported from the user's configuration directory rather than from
site-packages, so this module owns the ``sys.path`` juggling and keeps it in one
place. Only the non-streaming ``generate`` call is used: its ``samples`` come
back as a plain list of floats, whereas the streaming callback hands over a
NumPy array, and NVDA does not ship NumPy.

No NVDA imports; ``sherpa_onnx`` is injectable so the conversion and
configuration logic can be tested against a stub.
"""

import array
import os
import sys

from . import layout

#: NVDA speech output is mono; sherpa-onnx voices are single-channel too.
CHANNELS = 1

#: Samples come back as floats in [-1, 1] and NVDA's wave player wants 16-bit.
_FULL_SCALE = 32767


#: Kept alive so Windows does not remove the directories from the search path
#: on garbage collection.
_DLL_HANDLES = []


class EngineError(Exception):
	"""The runtime could not be loaded or the voice could not be spoken."""


def importSherpaOnnx(runtimeDirectory):
	"""Import ``sherpa_onnx`` from a downloaded runtime directory.

	The package is loaded once per NVDA session; a second call with a different
	directory returns the already-imported module rather than trying to swap a
	native extension that is still loaded.
	"""
	existing = sys.modules.get("sherpa_onnx")
	if existing is not None:
		return existing
	if not os.path.isdir(runtimeDirectory):
		raise EngineError("speech runtime is not installed: {0}".format(runtimeDirectory))
	# The bindings' .pyd sits beside the DLLs it needs. Python 3.8+ no longer
	# searches PATH for extension dependencies, so name the directory explicitly.
	libraryPath = os.path.join(runtimeDirectory, "sherpa_onnx", "lib")
	addDllDirectory = getattr(os, "add_dll_directory", None)
	for candidate in (libraryPath, os.path.join(runtimeDirectory, "sherpa_onnx"), runtimeDirectory):
		if os.path.isdir(candidate):
			if addDllDirectory is not None:
				try:
					_DLL_HANDLES.append(addDllDirectory(candidate))
				except OSError:
					pass
			try:
				import ctypes

				ctypes.windll.kernel32.SetDllDirectoryW(candidate)
			except Exception:
				pass
	if os.path.isdir(libraryPath):
		os.environ["PATH"] = libraryPath + os.pathsep + os.environ.get("PATH", "")
		for dllName in ("onnxruntime.dll", "sherpa-onnx-c-api.dll", "sherpa-onnx-core.dll"):
			dllPath = os.path.join(libraryPath, dllName)
			if os.path.isfile(dllPath):
				try:
					import ctypes

					ctypes.CDLL(dllPath)
				except Exception:
					pass
	if runtimeDirectory not in sys.path:
		sys.path.insert(0, runtimeDirectory)
	try:
		import sherpa_onnx
	except Exception as error:
		raise EngineError("could not load the speech runtime: {0}".format(error))
	return sherpa_onnx


def _toPcm16(samples, volume=1.0):
	"""Convert sherpa-onnx float samples to little-endian 16-bit PCM bytes."""
	scale = _FULL_SCALE * max(0.0, min(1.0, volume))
	block = array.array("h")
	block.extend(int(max(-1.0, min(1.0, sample)) * scale) for sample in samples)
	if sys.byteorder != "little":
		block.byteswap()
	return block.tobytes()


class SpeechEngine:
	"""One loaded neural voice."""

	def __init__(self, runtimeDirectory, voiceDirectory, family, numThreads=1, sherpa=None):
		self._runtimeDirectory = runtimeDirectory
		self._voiceDirectory = voiceDirectory
		self._family = family
		self._numThreads = max(1, int(numThreads))
		self._sherpa = sherpa
		self._tts = None
		self._sampleRate = 0

	@property
	def sampleRate(self):
		return self._sampleRate

	@property
	def family(self):
		return self._family

	def _buildConfig(self, sherpa, arguments):
		"""Assemble the family-specific model configuration."""
		modelKwargs = {"provider": "cpu", "debug": False, "num_threads": self._numThreads}
		cleanArgs = {k: v for k, v in arguments.items() if v}
		if self._family == "vits":
			modelKwargs["vits"] = sherpa.OfflineTtsVitsModelConfig(**cleanArgs)
		elif self._family == "kokoro":
			modelKwargs["kokoro"] = sherpa.OfflineTtsKokoroModelConfig(**cleanArgs)
		elif self._family == "supertonic":
			modelKwargs["supertonic"] = sherpa.OfflineTtsSupertonicModelConfig(**cleanArgs)
		else:
			raise EngineError("unsupported model family: {0}".format(self._family))
		return sherpa.OfflineTtsConfig(
			model=sherpa.OfflineTtsModelConfig(**modelKwargs),
			# One sentence per generate() call: the driver already splits the
			# utterance, and batching whole paragraphs would delay first audio.
			max_num_sentences=1,
		)

	def load(self):
		"""Load the model. Safe to call repeatedly."""
		if self._tts is not None:
			return
		sherpa = self._sherpa or importSherpaOnnx(self._runtimeDirectory)
		self._sherpa = sherpa
		try:
			arguments = layout.describe(self._family, self._voiceDirectory)
		except layout.LayoutError as error:
			raise EngineError(str(error))
		config = self._buildConfig(sherpa, arguments)
		if hasattr(config, "validate") and not config.validate():
			raise EngineError("the downloaded voice failed the runtime's own validation")
		try:
			self._tts = sherpa.OfflineTts(config)
		except Exception as error:
			raise EngineError("could not load the voice: {0}".format(error))
		self._sampleRate = int(getattr(self._tts, "sample_rate", 0))

	def _generationConfig(self, speed, speakerId, language):
		"""Build a GenerationConfig, or None if this runtime predates it."""
		factory = getattr(self._sherpa, "GenerationConfig", None)
		if factory is None:
			return None
		generation = factory()
		generation.sid = int(speakerId)
		generation.speed = float(speed)
		if language and hasattr(generation, "extra"):
			# Supertonic selects its language here; VITS voices are monolingual
			# and ignore it.
			try:
				generation.extra["lang"] = language
			except Exception:
				pass
		return generation

	def synthesize(self, text, speed=1.0, speakerId=0, language=None, volume=1.0):
		"""Return 16-bit PCM bytes for ``text``, or ``b""`` when it is silent."""
		if self._tts is None:
			self.load()
		if not text or not text.strip():
			return b""
		generation = self._generationConfig(speed, speakerId, language)
		audio = None
		if generation is not None:
			try:
				audio = self._tts.generate(text, generation)
			except Exception:
				audio = None
		if audio is None:
			try:
				audio = self._tts.generate(text, sid=int(speakerId), speed=float(speed))
			except TypeError:
				try:
					audio = self._tts.generate(text)
				except Exception as error:
					raise EngineError("speech generation failed: {0}".format(error))
			except Exception as error:
				raise EngineError("speech generation failed: {0}".format(error))
		samples = getattr(audio, "samples", None) or []
		sampleRate = int(getattr(audio, "sample_rate", 0)) or int(getattr(self._tts, "sample_rate", 0))
		if sampleRate:
			self._sampleRate = sampleRate
		return _toPcm16(samples, volume)

	def close(self):
		"""Release the loaded model."""
		self._tts = None
