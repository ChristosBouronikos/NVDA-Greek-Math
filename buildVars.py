# Build customizations for the Greek Math Reader NVDA add-on.
# SPDX-License-Identifier: GPL-2.0-only
# Change this file instead of sconstruct or manifest files, whenever possible.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries

# Since some strings in `addon_info` are translatable,
# we need to include them in the .po files.
# Gettext recognizes only strings given as parameters to the `_` function.
# To avoid initializing translations in this module we simply import a "fake" `_` function
# which returns whatever is given to it as an argument.
from site_scons.site_tools.NVDATool.utils import _


# Add-on information variables
addon_info = AddonInfo(
	# add-on Name/identifier, internal for NVDA
	addon_name="greekMathReader",
	# Add-on summary/title, usually the user visible name of the add-on
	# Translators: Summary/title for this add-on
	# to be shown on installation and add-on information found in add-on store
	addon_summary=_("Greek Math Reader"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-on store
	addon_description=_(
		"""Reads mathematical content (MathML) aloud in natural Greek, following the dictation
conventions used in Greek schools and universities.
Supports school and university mathematics, statistics, SI physics units, fractions,
powers, roots, integrals, limits, derivatives, matrices, probability, and LaTeX input.
Includes interactive navigation to explore complex expressions part by part,
and three verbosity levels (terse, smart, verbose)."""
	),
	# version
	addon_version="2.0.0",
	# Brief changelog for this version
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_(
		"""Version 2.0.0: reliable Greek reading of Word equations (structured OMath transform with an English backup), Greek LaTeX reading with NVDA+Alt+L, expanded school/university/statistics/physics vocabulary, clearer pronunciation of short Greek letter names, and Greek equation-boundary announcements."""
	),
	# Author(s)
	addon_author="Bouronikos Christos <chrisbouronikos@gmail.com>",
	# URL for the add-on documentation support
	addon_url="https://github.com/ChristosBouronikos/NVDA-Greek-Math",
	# URL for the add-on repository where the source code can be found
	addon_sourceURL="https://github.com/ChristosBouronikos/NVDA-Greek-Math",
	# Documentation file name
	addon_docFileName="readme.html",
	# Minimum NVDA version supported (e.g. "2019.3.0", minor version is optional)
	addon_minimumNVDAVersion="2024.1.0",
	# Last NVDA version supported/tested (e.g. "2024.4.0", ideally more recent than minimum version)
	addon_lastTestedNVDAVersion="2026.1.1",
	# Add-on update channel (default is None, denoting stable releases,
	# and for development releases, use "dev".)
	# Do not change unless you know what you are doing!
	addon_updateChannel=None,
	# SPDX identifier: GPL-2.0-only. This is compatible with NVDA's GPL-2.0-or-later license.
	addon_license="GPL-2.0-only",
	# URL for the license document the ad-on is licensed under
	addon_licenseURL="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
)

# Define the python files that are the sources of your add-on.
pythonSources = [
	"addon/globalPlugins/greekMathReader/*.py",
	"addon/globalPlugins/greekMathReader/engine/*.py",
]

# Files that contain strings for translation. Usually your python sources
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles: list[str] = [
	".DS_Store",
	"**/.DS_Store",
	"*.pyc",
	"**/*.pyc",
	"**/__pycache__/*",
	"**/*.po",
	"**/*.pot",
]

# Base language for the NVDA add-on
# The add-on UI messages are authored in English and translated to Greek (el);
# the math speech output itself is always Greek and lives in the engine data modules.
baseLanguage: str = "en"

# Markdown extensions for add-on documentation
markdownExtensions: list[str] = ["markdown.extensions.tables"]

# Custom braille translation tables (none in v1; Greek math braille is planned for v2)
brailleTables: BrailleTables = {}

# Custom speech symbol dictionaries (math symbols are handled by the engine, not NVDA symbol dics)
symbolDictionaries: SymbolDictionaries = {}
