# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# Optional support: https://paypal.me/christosbouronikos

"""Greek Math Reader: reads MathML in natural Greek.

Registers a math presentation provider for speech and interaction,
leaving braille to whichever provider was active before (MathCAT in
NVDA 2026.1+, MathPlayer or none in older versions).
"""

import addonHandler
import config
import globalPluginHandler
import gui
import mathPres
import ui
from logHandler import log
from scriptHandler import script

from .provider import GreekMathProvider

addonHandler.initTranslation()

CONFIG_SPEC = {
	"enabled": "boolean(default=True)",
	"verbosity": "integer(default=1, min=0, max=2)",
	"decimalComma": "boolean(default=True)",
	"forceGreekLanguage": "boolean(default=True)",
}

config.conf.spec["greekMathReader"] = CONFIG_SPEC

# NVDA keeps one global provider per presentation mode. Keep the providers we
# displaced so disabling this add-on restores exactly the previous behaviour.
_provider = None
_previousSpeechProvider = None
_previousInteractionProvider = None
_registered = False


def _register():
	"""Install one shared provider for speech and interaction.

	The provider object is intentionally reused across enable/disable cycles;
	only NVDA's global slots are changed. This avoids repeatedly constructing
	stateful NVDA objects while still preserving whatever provider was active
	immediately before this add-on was enabled.
	"""
	global _provider, _previousSpeechProvider, _previousInteractionProvider, _registered
	if _registered:
		return
	if _provider is None:
		_provider = GreekMathProvider()
	_previousSpeechProvider = mathPres.speechProvider
	_previousInteractionProvider = mathPres.interactionProvider
	mathPres.registerProvider(_provider, speech=True, interaction=True)
	_registered = True
	log.info("Greek Math Reader: provider registered")


def _unregister():
	"""Restore provider slots still owned by this add-on and release our state.

	Another add-on may replace either slot after ours is registered. We must not
	overwrite that newer provider, but we must *always* clear ``_registered``;
	otherwise a later re-enable would incorrectly believe this provider was
	already active.
	"""
	global _registered, _previousSpeechProvider, _previousInteractionProvider
	if not _registered:
		return
	# There is no official unregister API; restore what was there before us,
	# but only if we are still the active provider (another add-on may have
	# replaced us in the meantime).
	if mathPres.speechProvider is _provider:
		mathPres.speechProvider = _previousSpeechProvider
	if mathPres.interactionProvider is _provider:
		mathPres.interactionProvider = _previousInteractionProvider
	_registered = False
	# The next registration must snapshot the providers active at that time,
	# rather than accidentally retaining providers from an earlier cycle.
	_previousSpeechProvider = None
	_previousInteractionProvider = None
	log.info("Greek Math Reader: provider unregistered")


def applyProviderRegistration():
	"""Register or unregister the provider according to the current config."""
	if config.conf["greekMathReader"]["enabled"]:
		_register()
	else:
		_unregister()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		from .settingsPanel import GreekMathSettingsPanel

		self._settingsPanel = GreekMathSettingsPanel
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(GreekMathSettingsPanel)
		applyProviderRegistration()

	def terminate(self):
		_unregister()
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(self._settingsPanel)
		except ValueError:
			pass
		super().terminate()

	@script(
		# Translators: Describes the toggle command in the input gestures dialog.
		description=_("Toggles reading mathematics in Greek on or off"),
		# Translators: Category of the add-on's commands in the input gestures dialog.
		category=_("Greek Math Reader"),
		gesture="kb:NVDA+alt+g",
	)
	def script_toggleGreekMath(self, gesture):
		enabled = not config.conf["greekMathReader"]["enabled"]
		config.conf["greekMathReader"]["enabled"] = enabled
		applyProviderRegistration()
		if enabled:
			# Translators: Announced when Greek math reading is turned on.
			ui.message(_("Greek math reading on"))
		else:
			# Translators: Announced when Greek math reading is turned off.
			ui.message(_("Greek math reading off"))
