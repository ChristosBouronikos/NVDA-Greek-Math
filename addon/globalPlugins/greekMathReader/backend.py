# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
"""Automatic local/MathCAT speech backend selection.

MathCAT versions embedded in NVDA expose capability APIs through slightly
different Python layers.  Detection is deliberately defensive: delegation is
enabled only when Greek is explicitly advertised and the language can be set.
"""

import importlib
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
				function("Language", "el")
				return True
			except Exception:
				continue
	for name in ("setLanguage", "set_language"):
		function = getattr(owner, name, None)
		if callable(function):
			try:
				function("el")
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
		owners = []
		if delegate is not None:
			owners.extend((delegate, type(delegate)))
		for module_name in ("mathPres.MathCAT.MathCAT", "libmathcat_py", "MathCAT"):
			try:
				owners.append(importlib.import_module(module_name))
			except (ImportError, AttributeError):
				continue
		languages = set()
		for owner in owners:
			languages.update(_call_capability(owner))
		greek = any(code == "el" or code.startswith("el-") for code in languages)
		if not greek:
			self.detail = "MathCAT does not advertise an el language pack; using the local engine."
			return False
		language_set = any(_set_language(owner) for owner in owners)
		if not language_set:
			self.detail = "MathCAT advertises Greek but its language could not be selected safely."
			return False
		if delegate is None or not callable(getattr(delegate, "getSpeechForMathMl", None)):
			self.detail = "MathCAT Greek is available but no NVDA speech delegate is active."
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
		return self.delegate.getSpeechForMathMl(mathMl)

	def diagnostics(self):
		return {
			"backend": self.backendName,
			"detail": self.detail,
		}


automaticBackend = AutomaticMathBackend()

