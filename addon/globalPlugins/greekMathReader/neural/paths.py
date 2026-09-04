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

"""Filesystem layout for the optional neural speech runtime and voices.

Everything downloaded at the user's request lives under the NVDA *configuration*
directory, never under the add-on directory: NVDA replaces the add-on directory
wholesale on update, which would silently discard a few hundred megabytes the
user chose to download.

This module deliberately imports nothing from NVDA so it can be unit-tested on
any platform; callers pass the configuration path in.
"""

import os

#: Directory created under the NVDA configuration directory.
ROOT_DIRNAME = "greekMathReader"
NEURAL_DIRNAME = "neural"

#: Written into a voice or runtime directory once extraction has fully
#: succeeded. Its absence marks a partial download that must be discarded.
COMPLETION_MARKER = ".installed"


def neuralRoot(configPath):
	"""Return the directory holding every downloaded runtime and voice."""
	return os.path.join(configPath, ROOT_DIRNAME, NEURAL_DIRNAME)


def runtimeDir(configPath, platformKey):
	"""Return the directory for one platform's speech runtime.

	The platform key is part of the path because a single configuration
	directory can be shared between a 32-bit and a 64-bit NVDA (for example
	during an upgrade from 2025.x to 2026.1), and their binaries must not
	overwrite each other.
	"""
	return os.path.join(neuralRoot(configPath), "runtime", platformKey)


def voiceDir(configPath, voiceId):
	"""Return the directory holding one downloaded voice model."""
	return os.path.join(neuralRoot(configPath), "voices", voiceId)


def isComplete(directory):
	"""Whether ``directory`` holds a fully extracted download."""
	return os.path.isfile(os.path.join(directory, COMPLETION_MARKER))


def markComplete(directory):
	"""Record that ``directory`` was extracted successfully."""
	with open(os.path.join(directory, COMPLETION_MARKER), "w", encoding="utf-8") as marker:
		marker.write("ok\n")


def installedVoiceIds(configPath):
	"""Return the ids of every voice that finished downloading, sorted."""
	base = os.path.join(neuralRoot(configPath), "voices")
	try:
		entries = os.listdir(base)
	except OSError:
		return []
	return sorted(name for name in entries if isComplete(os.path.join(base, name)))
