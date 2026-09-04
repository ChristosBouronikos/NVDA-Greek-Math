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

"""Which prebuilt speech runtime matches the interpreter NVDA is running.

NVDA changed architecture and interpreter mid-way through the version range this
add-on supports: 2024.1 through 2025.x are 32-bit CPython 3.11, while 2026.1 is
64-bit CPython 3.13. A downloaded binary extension has to match both, so the
wheel is selected from the running interpreter rather than from the NVDA version.

Kept free of NVDA imports so the selection logic can be unit-tested.
"""

import sys
import sysconfig

#: Platform tags used by Windows CPython wheels.
_PLATFORM_ALIASES = {
	"win-amd64": "win_amd64",
	"win-arm64": "win_arm64",
	"win32": "win32",
}


def pythonTag(versionInfo=None):
	"""Return the CPython ABI tag, for example ``cp311``."""
	info = versionInfo or sys.version_info
	return "cp{0}{1}".format(info[0], info[1])


def platformTag(name=None):
	"""Return the wheel platform tag, for example ``win32`` or ``win_amd64``."""
	raw = name if name is not None else sysconfig.get_platform()
	return _PLATFORM_ALIASES.get(raw, raw.replace("-", "_"))


def platformKey(versionInfo=None, name=None):
	"""Return the combined key naming a runtime build, ``cp311-win32``."""
	return "{0}-{1}".format(pythonTag(versionInfo), platformTag(name))


def isSupportedPlatform(name=None):
	"""Whether the running platform is one the prebuilt runtimes cover."""
	return platformTag(name) in _PLATFORM_ALIASES.values()
