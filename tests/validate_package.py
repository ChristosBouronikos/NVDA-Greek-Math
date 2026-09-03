#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Optional support: https://paypal.me/christosbouronikos

"""Validate the release bundle's Store-facing metadata and structure."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


EXPECTED_MANIFEST_LINES = {
	"name = greekMathReader",
	'summary = "Greek Math Reader"',
	'author = "Bouronikos Christos <chrisbouronikos@gmail.com>"',
	"url = https://github.com/ChristosBouronikos/NVDA-Greek-Math",
	"version = 2.1.0-dev",
	"minimumNVDAVersion = 2024.1.0",
	"lastTestedNVDAVersion = 2026.1.1",
	"updateChannel = dev",
}

# Required in the shipped package by the GPL-3.0 section 7(b) term in LICENSE.md.
ATTRIBUTION_NOTICE = (
	"NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)"
)

REQUIRED_FILES = {
	"LICENSE.md",
	"doc/el/readme.html",
	"doc/en/readme.html",
	"globalPlugins/greekMathReader/__init__.py",
	"locale/el/LC_MESSAGES/nvda.mo",
	"locale/el/manifest.ini",
	"manifest.ini",
}


def validate(path: Path) -> None:
	if path.suffix != ".nvda-addon":
		raise AssertionError(f"release filename must end in .nvda-addon: {path.name}")
	with zipfile.ZipFile(path) as bundle:
		names = set(bundle.namelist())
		missing = REQUIRED_FILES - names
		if missing:
			raise AssertionError(f"package is missing required files: {sorted(missing)}")
		if "globalPlugins/__init__.py" in names:
			raise AssertionError("unused globalPlugins/__init__.py must not be packaged")
		if any(name.startswith("appModules/") for name in names):
			raise AssertionError("this add-on must not contain an appModules package")
		for name in names:
			if "__pycache__" in name or name.endswith((".pyc", ".po", ".pot")):
				raise AssertionError(f"generated/source-only file must not be packaged: {name}")
		manifest = bundle.read("manifest.ini").decode("utf-8")
		missing_lines = EXPECTED_MANIFEST_LINES - set(manifest.splitlines())
		if missing_lines:
			raise AssertionError(f"manifest mismatch: {sorted(missing_lines)}")
		terms = bundle.read("LICENSE.md").decode("utf-8")
		if "GNU GENERAL PUBLIC LICENSE" not in terms or "Version 3" not in terms:
			raise AssertionError("LICENSE.md is missing the complete GNU GPL version 3 text")
		if ATTRIBUTION_NOTICE not in terms:
			raise AssertionError("LICENSE.md is missing the required attribution notice")
		for doc in ("doc/en/readme.html", "doc/el/readme.html"):
			if ATTRIBUTION_NOTICE not in bundle.read(doc).decode("utf-8"):
				raise AssertionError(f"{doc} is missing the required attribution notice")


if __name__ == "__main__":
	package = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("greekMathReader-2.1.0-dev.nvda-addon")
	validate(package)
	print(f"Store package validation passed: {package}")
