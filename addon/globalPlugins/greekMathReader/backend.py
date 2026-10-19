# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Automatic local/MathCAT speech backend selection.

MathCAT versions embedded in NVDA expose capability APIs through slightly
different Python layers.  Detection is deliberately defensive: delegation is
enabled only when Greek is explicitly advertised and the language can be set.
"""

import re


def _language_codes(value):
	if isinstance(value, tuple) and value:
		# Rust/Python wrappers sometimes return ``(value, errorCode)``.
		value = value[0]
	if isinstance(value, str):
		return {part.lower().replace("_", "-") for part in re.findall(r"[A-Za-z]{2,3}(?:[-_][A-Za-z]{2,4})?", value)}
	if isinstance(value, (list, tuple, set)):
		return {str(part).lower().replace("_", "-") for part in value}
	return set()


def _call_capability(owner):
	for name in ("GetSupportedLanguages", "getSupportedLanguages", "get_supported_languages"):
		function = getattr(owner, name, None)
		if callable(function):
			try:
				return _language_codes(function())
			except Exception:
				continue
	return set()


def _set_language(owner):
	for name in ("SetPreference", "setPreference", "set_preference"):
		function = getattr(owner, name, None)
		if callable(function):
			try:
				if function("Language", "el") is not False:
					return True
			except Exception:
				continue
	for name in ("setLanguage", "set_language"):
		function = getattr(owner, name, None)
		if callable(function):
			try:
				if function("el") is not False:
					return True
			except Exception:
				continue
	return False


class AutomaticMathBackend:
	def __init__(self):
		self.delegate = None
		self.backendName = "local"
		self.detail = "MathCAT Greek capability has not been detected."

	def configure(self, delegate=None, enabled=True):
		self.delegate = None
		self.backendName = "local"
		if not enabled:
			self.detail = "Automatic MathCAT delegation is disabled."
			return False
		if delegate is None or not callable(getattr(delegate, "getSpeechForMathMl", None)):
			self.detail = "No NVDA speech delegate is active; using the local engine."
			return False
		# Capability and language selection must belong to the provider that will
		# speak. An unrelated installed MathCAT module proves nothing about it.
		languages = _call_capability(delegate)
		greek = any(code == "el" or code.startswith("el-") for code in languages)
		if not greek:
			self.detail = "MathCAT does not advertise an el language pack; using the local engine."
			return False
		if not _set_language(delegate):
			self.detail = "MathCAT advertises Greek but its language could not be selected safely."
			return False
		self.delegate = delegate
		self.backendName = "mathcat-el"
		self.detail = "Using the installed MathCAT Greek language pack."
		return True

	@property
	def usingMathCat(self):
		return self.delegate is not None and self.backendName == "mathcat-el"

	def getSpeechForMathMl(self, mathMl):
		if not self.usingMathCat:
			return None
		# Another math reader or synthesizer change may have reset the language.
		if not _set_language(self.delegate):
			self.delegate = None
			self.backendName = "local"
			self.detail = "MathCAT Greek could not be reselected; using the local engine."
			return None
		return self.delegate.getSpeechForMathMl(mathMl)

	def diagnostics(self):
		return {
			"backend": self.backendName,
			"detail": self.detail,
		}


automaticBackend = AutomaticMathBackend()

