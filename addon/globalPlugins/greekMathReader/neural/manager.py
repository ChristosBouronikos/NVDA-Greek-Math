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

"""What is installed, and installing what is not.

This is the single entry point used by both the settings panel and the
synthesizer driver, so that "is a neural voice usable right now?" has exactly one
answer in the add-on.

The configuration directory is passed in rather than imported, which keeps the
whole class testable; ``defaultConfigPath`` resolves it from NVDA when running
inside NVDA.
"""

import os
import shutil

from . import catalogue as catalogueModule
from . import installer, paths, platforms
from .engine import SpeechEngine


def defaultConfigPath():
	"""Return NVDA's configuration directory, or ``""`` outside NVDA."""
	try:
		import globalVars

		return globalVars.appArgs.configPath or ""
	except Exception:
		return ""


class VoiceManager:
	"""Tracks and installs the optional speech runtime and voices."""

	def __init__(self, configPath=None, catalogue=None):
		self.configPath = configPath if configPath is not None else defaultConfigPath()
		self._catalogue = catalogue
		self._lastError = ""

	@property
	def catalogue(self):
		if self._catalogue is None:
			self._catalogue = catalogueModule.loadCatalogue()
		return self._catalogue

	@property
	def lastError(self):
		return self._lastError

	@property
	def platformKey(self):
		return platforms.platformKey()

	@property
	def runtimeDirectory(self):
		return paths.runtimeDir(self.configPath, self.platformKey)

	def voiceDirectory(self, voiceId):
		return paths.voiceDir(self.configPath, voiceId)

	# -- state ---------------------------------------------------------------

	def isPlatformSupported(self):
		"""Whether a prebuilt runtime exists for this NVDA build."""
		return bool(self.catalogue.runtimeDownloads())

	def isRuntimeInstalled(self):
		return bool(self.configPath) and paths.isComplete(self.runtimeDirectory)

	def isVoiceInstalled(self, voiceId):
		return bool(self.configPath) and paths.isComplete(self.voiceDirectory(voiceId))

	def installedVoices(self):
		"""Catalogue entries for every fully downloaded voice."""
		if not self.configPath:
			return []
		installed = set(paths.installedVoiceIds(self.configPath))
		return [voice for voice in self.catalogue.voices if voice.id in installed]

	def isReady(self):
		"""Whether at least one voice can actually be spoken right now."""
		return self.isRuntimeInstalled() and bool(self.installedVoices())

	def diagnostics(self):
		"""A short, log-safe summary of the neural speech state."""
		return {
			"platform": self.platformKey,
			"platformSupported": self.isPlatformSupported(),
			"runtimeInstalled": self.isRuntimeInstalled(),
			"installedVoices": [voice.id for voice in self.installedVoices()],
			"lastError": self._lastError,
		}

	# -- installation --------------------------------------------------------

	def installRuntime(self, progress=None, opener=None):
		"""Download the speech runtime for this NVDA build."""
		downloads = self.catalogue.runtimeDownloads()
		if not downloads:
			self._lastError = "No speech runtime is published for {0}.".format(self.platformKey)
			return False
		return self._install(downloads, self.runtimeDirectory, installer.extractZip, progress, opener)

	def installVoice(self, voiceId, progress=None, opener=None):
		"""Download one voice model."""
		voice = self.catalogue.voice(voiceId)
		if voice is None:
			self._lastError = "Unknown voice: {0}".format(voiceId)
			return False
		return self._install(
			[voice.download], self.voiceDirectory(voiceId), installer.extractTar, progress, opener
		)

	def _install(self, downloads, destination, extractor, progress, opener):
		if not self.configPath:
			self._lastError = "NVDA's configuration directory could not be located."
			return False
		try:
			installer.installArchives(
				downloads, destination, extractor, opener=opener, progress=progress
			)
			paths.markComplete(destination)
		except installer.InstallError as error:
			self._lastError = str(error)
			return False
		except Exception as error:
			self._lastError = "unexpected failure: {0}".format(error)
			return False
		self._lastError = ""
		return True

	def removeVoice(self, voiceId):
		"""Delete a downloaded voice, freeing its disk space."""
		directory = self.voiceDirectory(voiceId)
		if not os.path.isdir(directory):
			return True
		try:
			shutil.rmtree(directory)
		except OSError as error:
			self._lastError = str(error)
			return False
		return True

	def diskUsage(self):
		"""Total bytes occupied by everything downloaded so far."""
		total = 0
		for root, _dirs, files in os.walk(paths.neuralRoot(self.configPath)):
			for name in files:
				try:
					total += os.path.getsize(os.path.join(root, name))
				except OSError:
					continue
		return total

	# -- speaking ------------------------------------------------------------

	def createEngine(self, voiceId, numThreads=1):
		"""Build a loaded ``SpeechEngine`` for an installed voice."""
		voice = self.catalogue.voice(voiceId)
		if voice is None:
			raise KeyError(voiceId)
		engine = SpeechEngine(
			self.runtimeDirectory, self.voiceDirectory(voiceId), voice.family, numThreads=numThreads
		)
		engine.load()
		return engine
