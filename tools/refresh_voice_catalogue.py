#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Regenerate ``neural/catalogue.json``.

The add-on refuses to install any runtime wheel or voice model whose SHA-256 is
not pinned in that file, so every download URL here must carry a digest that was
actually observed rather than copied from a web page.

PyPI publishes digests in its JSON API, so runtime wheels cost one API call.
GitHub release assets do not, so each voice archive is streamed once and hashed
without being kept on disk.

Usage:
    python3 tools/refresh_voice_catalogue.py            # runtime + all voices
    python3 tools/refresh_voice_catalogue.py --runtime  # runtime wheels only
    python3 tools/refresh_voice_catalogue.py --voice piper-el-int8
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "addon" / "globalPlugins" / "greekMathReader" / "neural" / "catalogue.json"

SCHEMA_VERSION = 1

# Pinned so a rebuild of the catalogue cannot silently move users to a runtime
# that has not been tested against the NVDA versions in the manifest.
RUNTIME_VERSION = "1.13.7"

# ``sherpa_onnx`` holds the CPython-ABI bindings, ``sherpa_onnx_core`` the much
# larger native libraries. Both are needed; only the first is ABI-specific.
RUNTIME_PACKAGES = ("sherpa-onnx", "sherpa-onnx-core")

GITHUB_TTS_MODELS = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"

# Human-authored metadata. Sizes and digests are filled in by this script.
#
# ``licenseAcceptance`` marks weights whose licence imposes conditions on
# downstream recipients. Those cannot be redistributed inside a GPL-3.0-or-later
# add-on, so the user has to fetch them and accept the terms personally.
VOICES = [
	{
		"id": "piper-el-int8",
		"archive": "vits-piper-el_GR-rapunzelina-low-int8.tar.bz2",
		"family": "vits",
		"languages": ["el"],
		"label": "Rapunzelina (Greek, Piper, compact)",
		"licenseId": "CC0-1.0",
		"licenseName": "CC0 1.0 (public domain)",
		"licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
		"licenseAcceptance": False,
		"recommended": True,
		"notes": (
			"Quantised build of the only public-domain neural Greek voice. "
			"Trained on about four hours of single-speaker audiobook speech "
			"(CSS10 Greek), fine-tuned from a US English voice, 16 kHz."
		),
	},
	{
		"id": "piper-el-fp16",
		"archive": "vits-piper-el_GR-rapunzelina-low-fp16.tar.bz2",
		"family": "vits",
		"languages": ["el"],
		"label": "Rapunzelina (Greek, Piper, balanced)",
		"licenseId": "CC0-1.0",
		"licenseName": "CC0 1.0 (public domain)",
		"licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
		"licenseAcceptance": False,
		"recommended": False,
		"notes": "Half-precision build of the same voice. Larger download, slightly cleaner output.",
	},
	{
		"id": "piper-el-full",
		"archive": "vits-piper-el_GR-rapunzelina-low.tar.bz2",
		"family": "vits",
		"languages": ["el"],
		"label": "Rapunzelina (Greek, Piper, full precision)",
		"licenseId": "CC0-1.0",
		"licenseName": "CC0 1.0 (public domain)",
		"licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
		"licenseAcceptance": False,
		"recommended": False,
		"notes": "Unquantised build. Highest fidelity of the three, slowest to synthesise.",
	},
	{
		"id": "mimic3-el",
		"archive": "vits-mimic3-el_GR-rapunzelina_low.tar.bz2",
		"family": "vits",
		"languages": ["el"],
		"label": "Rapunzelina (Greek, Mimic 3)",
		"licenseId": "CC0-1.0",
		"licenseName": "CC0 1.0 (public domain)",
		"licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
		"licenseAcceptance": False,
		"recommended": False,
		"notes": (
			"Independent Mimic 3 training of the same public-domain corpus. "
			"Worth comparing against the Piper builds; the two differ audibly."
		),
	},
	{
		"id": "supertonic-3",
		"archive": "sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2",
		"family": "supertonic",
		"languages": ["el", "en", "de", "fr", "es", "it", "pt", "ru", "zh", "ja", "ko"],
		"label": "Supertonic 3 (multilingual, includes Greek)",
		"licenseId": "OpenRAIL-M",
		"licenseName": "BigScience Open RAIL-M",
		"licenseUrl": "https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE",
		"licenseAcceptance": True,
		"recommended": False,
		"notes": (
			"Modern multilingual model, markedly newer than the Piper voices. "
			"Its licence adds use restrictions that must be passed to anyone you "
			"redistribute it to, so this add-on cannot ship it - you download it "
			"yourself after accepting the terms."
		),
	},
	{
		"id": "kokoro-multi-int8",
		"archive": "kokoro-int8-multi-lang-v1_1.tar.bz2",
		"family": "kokoro",
		"languages": ["en", "es", "fr", "hi", "it", "ja", "pt", "zh"],
		"label": "Kokoro v1.1 (multilingual, no Greek)",
		"licenseId": "Apache-2.0",
		"licenseName": "Apache 2.0",
		"licenseUrl": "https://huggingface.co/hexgrad/Kokoro-82M",
		"licenseAcceptance": False,
		"recommended": False,
		"notes": (
			"Does NOT speak Greek. Offered for users who also read English or "
			"another supported language and want one neural voice for that."
		),
	},
]


def _fetch_json(url):
	with urllib.request.urlopen(url, timeout=60) as response:
		return json.load(response)


def build_runtime():
	"""Collect pinned wheel URLs and digests straight from the PyPI API.

	``sherpa_onnx`` wheels are CPython-ABI specific (cp311-win32, cp313-win_amd64
	...), while ``sherpa_onnx_core`` ships one ``py3-none`` wheel per architecture.
	They are kept in separate maps because a running NVDA needs one of each and
	they are keyed differently.
	"""
	bindings = {}
	core = {}
	for package in RUNTIME_PACKAGES:
		data = _fetch_json(f"https://pypi.org/pypi/{package}/json")
		files = data["releases"].get(RUNTIME_VERSION)
		if not files:
			raise SystemExit(f"{package} has no release {RUNTIME_VERSION}")
		for entry in files:
			name = entry["filename"]
			if not name.endswith(".whl") or "win" not in name:
				continue
			# name-version-pytag-abitag-platform.whl
			parts = name[: -len(".whl")].split("-")
			pyTag, abiTag, platform = parts[-3], parts[-2], parts[-1]
			record = {
				"filename": name,
				"url": entry["url"],
				"size": entry["size"],
				"sha256": entry["digests"]["sha256"],
			}
			if abiTag == "none":
				core[platform] = record
			else:
				bindings[f"{pyTag}-{platform}"] = record
	return {
		"package": "sherpa-onnx",
		"version": RUNTIME_VERSION,
		"license": "Apache-2.0",
		"licenseUrl": "https://github.com/k2-fsa/sherpa-onnx/blob/master/LICENSE",
		"bindings": bindings,
		"core": core,
	}


def hash_asset(url):
	"""Stream a release asset and return (size, sha256) without storing it."""
	digest = hashlib.sha256()
	total = 0
	with urllib.request.urlopen(url, timeout=300) as response:
		while True:
			chunk = response.read(1024 * 256)
			if not chunk:
				break
			total += len(chunk)
			digest.update(chunk)
	return total, digest.hexdigest()


def build_voices(previous, only=None):
	known = {voice["id"]: voice for voice in previous.get("voices", [])}
	result = []
	for voice in VOICES:
		entry = dict(voice)
		url = GITHUB_TTS_MODELS + voice["archive"]
		entry["url"] = url
		cached = known.get(voice["id"])
		if only and voice["id"] not in only and cached and cached.get("sha256"):
			entry["size"] = cached["size"]
			entry["sha256"] = cached["sha256"]
			result.append(entry)
			continue
		print(f"hashing {voice['archive']} ...", flush=True)
		size, digest = hash_asset(url)
		entry["size"] = size
		entry["sha256"] = digest
		print(f"  {size / 1e6:.1f} MB  sha256={digest}", flush=True)
		result.append(entry)
	return result


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--runtime", action="store_true", help="refresh runtime wheels only")
	parser.add_argument("--voice", action="append", help="refresh only these voice ids")
	args = parser.parse_args()

	previous = {}
	if OUTPUT.exists():
		previous = json.loads(OUTPUT.read_text(encoding="utf-8"))

	catalogue = {
		"schemaVersion": SCHEMA_VERSION,
		"runtime": build_runtime(),
		"voices": previous.get("voices", []) if args.runtime else build_voices(previous, args.voice),
	}
	OUTPUT.parent.mkdir(parents=True, exist_ok=True)
	OUTPUT.write_text(json.dumps(catalogue, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	print(f"wrote {OUTPUT.relative_to(ROOT)}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
