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

"""Optional neural speech support for the Greek Math Reader add-on.

The add-on speaks through whatever synthesizer NVDA is set to. This package adds
an *optional* synthesizer of its own, which appears in NVDA's own synthesizer
list once the user downloads a runtime and at least one voice from the add-on's
settings. Nothing here runs, and nothing is downloaded, unless the user asks.
"""

from . import catalogue, installer, layout, paths, platforms, synthesis  # noqa: F401

__all__ = ["catalogue", "installer", "layout", "paths", "platforms", "synthesis"]
