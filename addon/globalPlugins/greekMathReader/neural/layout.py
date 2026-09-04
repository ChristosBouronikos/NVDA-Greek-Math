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

"""Locating the model files inside a downloaded voice directory.

Each archive in the catalogue unpacks to a single top-level directory whose name
varies with the model and its release date, and the file layout differs per
model family. This module turns "the directory the user downloaded" into "the
arguments sherpa-onnx needs", without hard-coding release-dated directory names.

No NVDA and no sherpa-onnx imports, so layout detection is unit-testable against
directory trees built in a temporary folder.
"""

import os

#: Espeak phoneme data shipped inside VITS and Kokoro archives.
_ESPEAK_DATA = "espeak-ng-data"

#: Supertonic splits one voice across several fixed-name graphs.
_SUPERTONIC_FILES = {
	"duration_predictor": ("duration_predictor",),
	"text_encoder": ("text_encoder",),
	"vector_estimator": ("vector_estimator",),
	"vocoder": ("vocoder",),
}


class LayoutError(Exception):
	"""A downloaded voice directory does not look like the expected family."""


def modelRoot(directory):
	"""Return the directory actually holding the model files.

	Archives unpack to one nested directory; if that is what we find, descend
	into it. A voice re-extracted flat still works.
	"""
	if not os.path.isdir(directory):
		raise LayoutError("no such directory: {0}".format(directory))
	entries = [name for name in os.listdir(directory) if not name.startswith(".")]
	files = [name for name in entries if os.path.isfile(os.path.join(directory, name))]
	subdirectories = [name for name in entries if os.path.isdir(os.path.join(directory, name))]
	if not files and len(subdirectories) == 1:
		return os.path.join(directory, subdirectories[0])
	return directory


def _find(root, predicate):
	for name in sorted(os.listdir(root)):
		if predicate(name):
			return os.path.join(root, name)
	return ""


def _optional(root, name):
	path = os.path.join(root, name)
	return path if os.path.exists(path) else ""


def describeVits(root):
	"""Return the VITS/Piper arguments found in ``root``."""
	model = _find(root, lambda name: name.endswith(".onnx"))
	if not model:
		raise LayoutError("no .onnx model in {0}".format(root))
	tokens = _optional(root, "tokens.txt")
	if not tokens:
		raise LayoutError("no tokens.txt in {0}".format(root))
	return {
		"model": model,
		"tokens": tokens,
		"data_dir": _optional(root, _ESPEAK_DATA),
		"lexicon": _optional(root, "lexicon.txt"),
	}


def describeKokoro(root):
	"""Return the Kokoro arguments found in ``root``."""
	model = _find(root, lambda name: name.endswith(".onnx"))
	if not model:
		raise LayoutError("no .onnx model in {0}".format(root))
	voices = _find(root, lambda name: name.startswith("voices") and name.endswith(".bin"))
	if not voices:
		raise LayoutError("no voices.bin in {0}".format(root))
	return {
		"model": model,
		"voices": voices,
		"tokens": _optional(root, "tokens.txt"),
		"data_dir": _optional(root, _ESPEAK_DATA),
		"lexicon": _find(root, lambda name: name.startswith("lexicon") and name.endswith(".txt")),
	}


def describeSupertonic(root):
	"""Return the Supertonic arguments found in ``root``.

	The four graphs are matched by prefix so that quantised releases
	(``vocoder.int8.onnx``) and float releases (``vocoder.onnx``) both resolve.
	"""
	found = {}
	for key, prefixes in _SUPERTONIC_FILES.items():
		path = _find(
			root,
			lambda name, prefixes=prefixes: name.endswith(".onnx") and name.startswith(prefixes),
		)
		if not path:
			raise LayoutError("no {0} graph in {1}".format(key, root))
		found[key] = path
	for key, filename in (("tts_json", "tts.json"), ("unicode_indexer", "unicode_indexer.bin"), ("voice_style", "voice.bin")):
		path = _optional(root, filename)
		if not path:
			raise LayoutError("no {0} in {1}".format(filename, root))
		found[key] = path
	return found


#: Family name in the catalogue -> the function describing that layout.
DESCRIBERS = {
	"vits": describeVits,
	"kokoro": describeKokoro,
	"supertonic": describeSupertonic,
}


def describe(family, directory):
	"""Return the sherpa-onnx arguments for a downloaded voice."""
	describer = DESCRIBERS.get(family)
	if describer is None:
		raise LayoutError("unsupported model family: {0}".format(family))
	return describer(modelRoot(directory))
