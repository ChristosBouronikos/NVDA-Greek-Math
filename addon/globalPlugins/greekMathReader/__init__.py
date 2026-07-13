# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 2.
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos

"""Greek Math Reader: reads MathML in natural Greek.

Installs itself as NVDA's exclusive math speech and interaction provider.
Braille remains with NVDA's built-in provider.
"""

import addonHandler
import config
import core
import globalPluginHandler
import gui
import mathPres
import ui
from logHandler import log
from scriptHandler import script

from .provider import GreekMathProvider, getGreekVoiceSupport, tokensToSpeechSequence

addonHandler.initTranslation()

ADDON_VERSION = "2.0.0"
BUILD_ID = "20260713-v2-release-r8"
_WORD_UIA_ALWAYS = 3

CONFIG_SPEC = {
	# Kept only to migrate old configurations. While the add-on is installed,
	# speech and interaction are always enabled and exclusive.
	"enabled": "boolean(default=True)",
	"verbosity": "integer(default=1, min=0, max=2)",
	"decimalComma": "boolean(default=True)",
	"forceGreekLanguage": "boolean(default=True)",
	# Backup mode: translate Word/Outlook speech that clearly reads as English
	# math even when no native OMath or UIA math field confirms an equation
	# (COM unavailable, protected view, Outlook reading pane and similar).
	"translateUnconfirmedWordMath": "boolean(default=True)",
}

config.conf.spec["greekMathReader"] = CONFIG_SPEC

# NVDA keeps one global provider per presentation mode. Keep the providers we
# displaced so unloading/uninstalling restores exactly the previous behaviour.
_provider = None
_previousSpeechProvider = None
_previousInteractionProvider = None
_registered = False
_mathCatClass = None
_originalMathCatSpeech = None
_mathCatSpeechFallback = None
_hasLoggedMathCatFallback = False
_exclusiveModeActive = False
_originalRegisterProvider = None
_originalMathPresInitialize = None
_originalMathPresTerminate = None
_registerProviderGuard = None
_mathPresInitializeGuard = None
_mathPresTerminateGuard = None
_hasLoggedBlockedProvider = False
_speechCoreModule = None
_speechPublicModule = None
_originalGetObjectSpeech = None
_originalPublicGetObjectSpeech = None
_mathObjectSpeechHook = None
_hasLoggedMathObjectRoute = False
_hasLoggedMathObjectWithoutMathMl = False
_lastMathObjectDiagnostic = "No math object has been encountered since NVDA started."
_textSpeechCoreModule = None
_textSpeechPublicModule = None
_originalGetTextInfoSpeech = None
_originalPublicGetTextInfoSpeech = None
_textInfoSpeechHook = None
_originalAddMathForTextInfo = None
_addMathForTextInfoHook = None
_hasLoggedWordTextInfoRoute = False
_hasLoggedWordNativeTranslation = False
_lastWordTextInfoDiagnostic = "No Word equation text range has been encountered since NVDA started."
_lastWordNotificationDiagnostic = "No Word math notification has been encountered since NVDA started."
_finalSpeechFilterExtension = None
_finalWordSpeechFilter = None
_hasLoggedFinalWordSpeechRoute = False
_finalWordSpeechFilterActive = False
_finalWordSpeechInvocationCount = 0
_finalWordSpeechCandidateCount = 0
_finalWordSpeechReplacementCount = 0
_lastWordFinalSpeechDiagnostic = "No final Word speech sequence has been intercepted since NVDA started."
_lastWordComDiagnostic = "Word OMath fallback has not been attempted since NVDA started."
_ommlStylesheetDom = None
_ommlStylesheetPath = None
_lastOmmlSourceDigest = None
_lastOmmlStylesheetPath = None
_lastOmmlResult = None
_PROVIDER_WATCHDOG_INTERVAL_MS = 500
_SELF_TEST_MATHML = (
	"<math xmlns='http://www.w3.org/1998/Math/MathML'>"
	"<msup><mi>x</mi><mn>2</mn></msup><mo>+</mo><mn>1</mn>"
	"</math>"
)


def _clearWordOmmlCaches():
	"""Release cached Office COM DOMs and equation data."""
	global _ommlStylesheetDom, _ommlStylesheetPath
	global _lastOmmlSourceDigest, _lastOmmlStylesheetPath, _lastOmmlResult
	_ommlStylesheetDom = None
	_ommlStylesheetPath = None
	_lastOmmlSourceDigest = None
	_lastOmmlStylesheetPath = None
	_lastOmmlResult = None


def _getMathMlFromObject(obj):
	"""Return usable MathML exposed by an NVDA math object, if available."""
	try:
		mathMl = obj.mathMl
	except Exception:
		return None
	return mathMl if isinstance(mathMl, str) and mathMl.strip() else None


def _describeMathObject(obj, mathMl):
	"""Record enough object detail to distinguish MathML from English ARIA text."""
	global _lastMathObjectDiagnostic
	try:
		appModule = getattr(obj, "appModule", None)
	except Exception:
		appModule = None
	try:
		name = getattr(obj, "name", None)
	except Exception as error:
		name = f"<unavailable: {error!r}>"
	try:
		role = getattr(obj, "role", None)
	except Exception as error:
		role = f"<unavailable: {error!r}>"
	try:
		hasNavigableText = getattr(obj, "_hasNavigableText", None)
	except Exception as error:
		hasNavigableText = f"<unavailable: {error!r}>"
	if isinstance(name, str) and len(name) > 180:
		name = name[:177] + "..."
	_lastMathObjectDiagnostic = (
		f"app={getattr(appModule, 'appName', None)!r}; "
		f"class={type(obj).__module__}.{type(obj).__name__}; "
		f"role={role!r}; "
		f"hasNavigableText={hasNavigableText!r}; "
		f"mathMlAvailable={mathMl is not None}; "
		f"mathMlLength={len(mathMl) if mathMl is not None else 0}; "
		f"accessibleName={name!r}"
	)


def _installMathObjectSpeechHook():
	"""Force math objects with MathML through the Greek provider.

	NVDA 2026.1.1 normally invokes the registered provider, but a Role.MATH
	object which advertises navigable text takes the generic text path first.
	That can speak an English MathJax/ARIA name and skip the provider entirely.
	This narrow hook affects only Role.MATH objects that expose real MathML.
	"""
	global _speechCoreModule, _speechPublicModule
	global _originalGetObjectSpeech, _originalPublicGetObjectSpeech
	global _mathObjectSpeechHook, _hasLoggedMathObjectRoute
	global _hasLoggedMathObjectWithoutMathMl
	try:
		import controlTypes
		import speech
		from speech import speech as speechCore
		from utils.security import objectBelowLockScreenAndWindowsIsLocked
	except (ImportError, AttributeError):
		objectBelowLockScreenAndWindowsIsLocked = None
		try:
			import controlTypes
			import speech
			from speech import speech as speechCore
		except (ImportError, AttributeError):
			return False

	if _mathObjectSpeechHook is not None:
		repaired = False
		if speechCore.getObjectSpeech is not _mathObjectSpeechHook:
			speechCore.getObjectSpeech = _mathObjectSpeechHook
			repaired = True
		if speech.getObjectSpeech is not _mathObjectSpeechHook:
			speech.getObjectSpeech = _mathObjectSpeechHook
			repaired = True
		if repaired:
			log.warning("Greek Math Reader: repaired forced math-object speech route")
		return True

	original = speechCore.getObjectSpeech
	originalPublic = speech.getObjectSpeech

	def getObjectSpeech(obj, *args, **kwargs):
		global _hasLoggedMathObjectRoute, _hasLoggedMathObjectWithoutMathMl
		reason = kwargs.get("reason")
		if reason is None and args:
			reason = args[0]
		if reason is None:
			reason = controlTypes.OutputReason.QUERY
		if (
			objectBelowLockScreenAndWindowsIsLocked is not None
			and objectBelowLockScreenAndWindowsIsLocked(obj)
		):
			return original(obj, *args, **kwargs)
		if reason == controlTypes.OutputReason.ONLYCACHE:
			return original(obj, *args, **kwargs)
		if _exclusiveModeActive and getattr(obj, "role", None) == controlTypes.Role.MATH:
			mathMl = _getMathMlFromObject(obj)
			_describeMathObject(obj, mathMl)
			if mathMl is not None:
				if _provider is None:
					_register()
				if not _hasLoggedMathObjectRoute:
					log.info(
						"Greek Math Reader: forcing Role.MATH object through Greek speech; "
						+ _lastMathObjectDiagnostic
					)
					_hasLoggedMathObjectRoute = True
				sequence = []
				prefix = kwargs.get("_prefixSpeechCommand")
				if prefix is None and len(args) >= 2:
					prefix = args[1]
				if prefix is not None:
					sequence.append(prefix)
				sequence.extend(_provider.getSpeechForMathMl(mathMl))
				return sequence
			if not _hasLoggedMathObjectWithoutMathMl:
				log.warning(
					"Greek Math Reader: math object exposes no MathML; NVDA can only read "
					"the application's accessible text; " + _lastMathObjectDiagnostic
				)
				_hasLoggedMathObjectWithoutMathMl = True
		return original(obj, *args, **kwargs)

	getObjectSpeech._greekMathReaderMathObjectRoute = True
	_speechCoreModule = speechCore
	_speechPublicModule = speech
	_originalGetObjectSpeech = original
	_originalPublicGetObjectSpeech = originalPublic
	_mathObjectSpeechHook = getObjectSpeech
	speechCore.getObjectSpeech = getObjectSpeech
	speech.getObjectSpeech = getObjectSpeech
	log.info("Greek Math Reader: forced math-object speech route installed")
	return True


def _removeMathObjectSpeechHook():
	"""Restore the exact speech functions displaced by our narrow object hook."""
	global _speechCoreModule, _speechPublicModule
	global _originalGetObjectSpeech, _originalPublicGetObjectSpeech, _mathObjectSpeechHook
	if _speechCoreModule is not None and _speechCoreModule.getObjectSpeech is _mathObjectSpeechHook:
		_speechCoreModule.getObjectSpeech = _originalGetObjectSpeech
	if _speechPublicModule is not None and _speechPublicModule.getObjectSpeech is _mathObjectSpeechHook:
		_speechPublicModule.getObjectSpeech = _originalPublicGetObjectSpeech
	_speechCoreModule = None
	_speechPublicModule = None
	_originalGetObjectSpeech = None
	_originalPublicGetObjectSpeech = None
	_mathObjectSpeechHook = None


def _iterWordObjectCandidates(*seeds, includeFocus=False):
	"""Yield bounded Word/Outlook NVDA objects hidden behind document proxies."""
	queue = [seed for seed in seeds if seed is not None]
	if includeFocus:
		try:
			import api

			queue.append(api.getFocusObject())
			queue.extend(api.getFocusAncestors())
		except Exception:
			pass
	seen = set()
	while queue and len(seen) < 40:
		candidate = queue.pop(0)
		if candidate is None or id(candidate) in seen:
			continue
		seen.add(id(candidate))
		try:
			root = candidate.rootNVDAObject
		except Exception:
			root = None
		if root is not None and root is not candidate:
			queue.append(root)
		try:
			treeRoot = candidate.treeInterceptor.rootNVDAObject
		except Exception:
			treeRoot = None
		if treeRoot is not None and treeRoot is not candidate:
			queue.append(treeRoot)
		try:
			appName = getattr(candidate.appModule, "appName", None)
		except Exception:
			appName = None
		if appName in ("winword", "outlook"):
			yield candidate


def _getWordObjectFromTextInfo(info):
	"""Resolve a real Word object from UIA/browse-mode TextInfo wrappers."""
	seeds = []
	try:
		seeds.append(info.obj)
	except Exception:
		pass
	try:
		seeds.append(info.innerTextInfo.obj)
	except Exception:
		pass
	for candidate in _iterWordObjectCandidates(*seeds):
		return candidate
	# RootProxyTextInfo variants can hide every useful relation; the active
	# focus is a safe final identity source while speech is generated.
	for candidate in _iterWordObjectCandidates(*seeds, includeFocus=True):
		return candidate
	return None


def _isWordTextInfo(info):
	"""Return whether a TextInfo belongs to a Word or Outlook document."""
	return _getWordObjectFromTextInfo(info) is not None


def _iterWordOMaths(collection):
	"""Yield Word OMath COM objects from a one-based read-only collection."""
	try:
		count = min(int(collection.Count), 500)
	except Exception:
		return
	for index in range(1, count + 1):
		try:
			yield collection.Item(index)
		except Exception:
			continue


def _findContainingWordOMath(obj, allowAdjacentEnd=False):
	"""Find the smallest native Word equation containing the current selection."""
	global _lastWordComDiagnostic
	try:
		selection = obj.WinwordSelectionObject
		caretRange = selection.Range.Duplicate
	except Exception as error:
		_lastWordComDiagnostic = f"COM unavailable: {error!r}"
		return None
	try:
		caretStart = int(caretRange.Start)
		caretEnd = int(caretRange.End)
	except Exception as error:
		_lastWordComDiagnostic = f"could not read Word selection range: {error!r}"
		return None

	def rangeDetails(omath):
		try:
			rangeObj = omath.Range
			start = int(rangeObj.Start)
			end = int(rangeObj.End)
		except Exception:
			return None
		return start, end, omath

	def rank(omath, start, end):
		try:
			nestingLevel = int(omath.NestingLevel)
		except Exception:
			nestingLevel = 1_000_000
		# Prefer the outermost equation.  A Word selection may expose both a
		# complete OMath and an argument-level nested OMath at the same caret.
		return nestingLevel, -(end - start), omath

	def contains(omath):
		details = rangeDetails(omath)
		if details is None:
			return None
		start, end, omath = details
		if caretStart == caretEnd:
			inside = start <= caretStart < end
			if allowAdjacentEnd and start < end and end == caretStart:
				# A UIA notification can arrive just after Word placed the caret
				# at the equation's exclusive end.  This option is deliberately
				# reserved for that notification path, never ordinary prose.
				inside = True
		else:
			inside = start < caretEnd and caretStart < end
		return rank(omath, start, end) if inside else None

	matches = []
	for owner in (selection, caretRange):
		try:
			collection = owner.OMaths
		except Exception:
			continue
		for omath in _iterWordOMaths(collection):
			# Word's Selection/Range.OMaths collection reports an equation even
			# when the collapsed caret merely *touches* its exclusive end — that
			# is, when the caret is really on the first character AFTER the
			# equation. Containment is therefore enforced here too; otherwise
			# character navigation right after an equation speaks the whole
			# equation instead of the character. The notification and final
			# speech filter paths opt into end-adjacency via allowAdjacentEnd.
			match = contains(omath)
			if match is not None:
				matches.append(match)
	if not matches:
		if not allowAdjacentEnd:
			_lastWordComDiagnostic = (
				f"no containing native OMath; selectionStart={caretStart}; "
				f"selectionEnd={caretEnd}"
			)
			return None
		try:
			probeRange = caretRange.Duplicate
			# wdParagraph = 4. Expanding a duplicate Range does not move the
			# selection or modify the document.
			probeRange.Expand(4)
			collection = probeRange.OMaths
		except Exception as error:
			_lastWordComDiagnostic = f"could not inspect surrounding Word paragraph: {error!r}"
			return None
		for omath in _iterWordOMaths(collection):
			match = contains(omath)
			if match is not None:
				matches.append(match)
	if not matches:
		_lastWordComDiagnostic = (
			f"no containing native OMath; selectionStart={caretStart}; selectionEnd={caretEnd}"
		)
		return None
	matches.sort(key=lambda item: (item[0], item[1]))
	bestNestingLevel, negativeLength, bestOMath = matches[0]
	_lastWordComDiagnostic = (
		f"native OMath found; selectionStart={caretStart}; selectionEnd={caretEnd}; "
		f"equationLength={-negativeLength}; nestingLevel={bestNestingLevel}"
	)
	return bestOMath


def _loadOmmlStylesheet(obj):
	"""Load Office's own OMML-to-MathML stylesheet into a hardened MSXML DOM."""
	global _ommlStylesheetDom, _ommlStylesheetPath, _lastWordComDiagnostic
	try:
		import os
		from comtypes.client import CreateObject

		application = obj.WinwordApplicationObject
		officePath = application.Path
		xslPath = os.path.join(officePath, "OMML2MML.XSL")
	except Exception as error:
		_lastWordComDiagnostic += f"; could not locate Office OMML2MML.XSL: {error!r}"
		return None
	if _ommlStylesheetDom is not None and _ommlStylesheetPath == xslPath:
		return _ommlStylesheetDom
	if not os.path.isfile(xslPath):
		_lastWordComDiagnostic += f"; Office OMML2MML.XSL missing at {xslPath!r}"
		return None
	try:
		stylesheet = CreateObject("Msxml2.DOMDocument.6.0")
		setattr(stylesheet, "async", False)
		stylesheet.validateOnParse = False
		stylesheet.resolveExternals = False
		try:
			stylesheet.setProperty("ProhibitDTD", True)
		except Exception:
			pass
		for propertyName in ("AllowXsltScript", "AllowDocumentFunction"):
			try:
				stylesheet.setProperty(propertyName, False)
			except Exception:
				pass
		if not stylesheet.load(xslPath):
			reason = getattr(getattr(stylesheet, "parseError", None), "reason", "unknown error")
			_lastWordComDiagnostic += f"; could not load OMML stylesheet: {reason}"
			return None
	except Exception as error:
		_lastWordComDiagnostic += f"; could not initialize MSXML transform: {error!r}"
		return None
	_ommlStylesheetDom = stylesheet
	_ommlStylesheetPath = xslPath
	return stylesheet


def _transformWordOmmlToMathMl(obj, wordOpenXml):
	"""Extract an OMML equation from Flat OPC and transform it in memory."""
	global _lastWordComDiagnostic
	global _lastOmmlSourceDigest, _lastOmmlStylesheetPath, _lastOmmlResult
	if not isinstance(wordOpenXml, str) or not wordOpenXml.strip():
		_lastWordComDiagnostic += "; WordOpenXML was empty"
		return None
	if len(wordOpenXml) > 2_000_000:
		_lastWordComDiagnostic += f"; WordOpenXML too large ({len(wordOpenXml)} characters)"
		return None
	from hashlib import sha256

	sourceDigest = sha256(wordOpenXml.encode("utf-8", errors="surrogatepass")).digest()
	stylesheet = _loadOmmlStylesheet(obj)
	if stylesheet is None:
		return None
	if (
		sourceDigest == _lastOmmlSourceDigest
		and _ommlStylesheetPath == _lastOmmlStylesheetPath
		and _lastOmmlResult is not None
	):
		_lastWordComDiagnostic += "; reused cached OMML transform"
		return _lastOmmlResult
	try:
		from xml.etree import ElementTree

		root = ElementTree.fromstring(wordOpenXml)
		mathNamespace = "http://schemas.openxmlformats.org/officeDocument/2006/math"
		omml = root.find(f".//{{{mathNamespace}}}oMath")
		if omml is None and root.tag in (
			f"{{{mathNamespace}}}oMath",
			f"{{{mathNamespace}}}oMathPara",
		):
			omml = root
		if omml is None:
			_lastWordComDiagnostic += "; WordOpenXML contained no OMML equation"
			return None
		ommlXml = ElementTree.tostring(omml, encoding="unicode")
	except Exception as error:
		_lastWordComDiagnostic += f"; could not parse WordOpenXML: {error!r}"
		return None
	try:
		from comtypes.client import CreateObject

		source = CreateObject("Msxml2.DOMDocument.6.0")
		setattr(source, "async", False)
		source.validateOnParse = False
		source.resolveExternals = False
		try:
			source.setProperty("ProhibitDTD", True)
		except Exception:
			pass
		for propertyName in ("AllowXsltScript", "AllowDocumentFunction"):
			try:
				source.setProperty(propertyName, False)
			except Exception:
				pass
		if not source.loadXML(ommlXml):
			reason = getattr(getattr(source, "parseError", None), "reason", "unknown error")
			_lastWordComDiagnostic += f"; MSXML rejected OMML: {reason}"
			return None
		mathMl = source.transformNode(stylesheet)
	except Exception as error:
		_lastWordComDiagnostic += f"; OMML transform failed: {error!r}"
		return None
	if not isinstance(mathMl, str) or not mathMl.strip():
		_lastWordComDiagnostic += "; OMML transform returned no content"
		return None
	# Office's stylesheet can return sibling presentation elements rather than
	# a <math> document element. Strip its declaration and wrap that fragment.
	try:
		import re
		from xml.etree import ElementTree

		mathMl = re.sub(r"^\s*<\?xml[^>]*\?>", "", mathMl, count=1).strip()
		try:
			transformedRoot = ElementTree.fromstring(mathMl)
			rootLocalName = transformedRoot.tag.rsplit("}", 1)[-1].split(":")[-1]
		except ElementTree.ParseError:
			rootLocalName = None
		if rootLocalName != "math":
			mathMl = (
				"<math xmlns='http://www.w3.org/1998/Math/MathML'>"
				+ mathMl
				+ "</math>"
			)
		ElementTree.fromstring(mathMl)
	except Exception as error:
		_lastWordComDiagnostic += f"; transformed MathML was invalid: {error!r}"
		return None
	_lastOmmlSourceDigest = sourceDigest
	_lastOmmlStylesheetPath = _ommlStylesheetPath
	_lastOmmlResult = mathMl
	_lastWordComDiagnostic += f"; transformed to MathML ({len(mathMl)} characters)"
	return mathMl


def _getMathMlFromWordOMath(obj, omath):
	"""Transform one already-located native Word OMath without modifying it."""
	try:
		wordOpenXml = omath.Range.WordOpenXML
	except Exception as error:
		global _lastWordComDiagnostic
		_lastWordComDiagnostic += f"; could not read OMath WordOpenXML: {error!r}"
		return None
	return _transformWordOmmlToMathMl(obj, wordOpenXml)


def _getWordComMathContext(obj, allowAdjacentEnd=False):
	"""Return ``(MathML, insideNativeOMath)`` for Word's current selection."""
	omath = _findContainingWordOMath(obj, allowAdjacentEnd=allowAdjacentEnd)
	if omath is None:
		return None, False
	return _getMathMlFromWordOMath(obj, omath), True


def _textInfoHasMathControl(info):
	"""Detect an enclosing Role.MATH field even when its MathML lookup fails."""
	try:
		import controlTypes
		import textInfos

		probe = info.copy()
		probe.expand(textInfos.UNIT_CHARACTER)
		fields = probe.getTextWithFields()
	except Exception:
		return False
	for item in fields:
		if getattr(item, "command", None) != "controlStart":
			continue
		field = getattr(item, "field", None)
		if not hasattr(field, "get"):
			continue
		if field.get("role") == controlTypes.Role.MATH or field.get("mathml"):
			return True
	return False


def _getMathContextFromTextInfo(info, allowWordCom=False):
	"""Return ``(MathML, independentlyConfirmedMath)`` without speaking."""
	try:
		mathMl = mathPres.getMathMlFromTextInfo(info)
	except Exception:
		mathMl = None
	if isinstance(mathMl, str) and mathMl.strip():
		return mathMl, True
	hasMathControl = _textInfoHasMathControl(info)
	wordObj = _getWordObjectFromTextInfo(info) if allowWordCom else None
	if wordObj is not None:
		try:
			comMathMl, insideOMath = _getWordComMathContext(wordObj)
			if comMathMl is not None:
				return comMathMl, True
			return None, hasMathControl or insideOMath
		except Exception:
			log.exception("Greek Math Reader: unexpected Word OMath fallback failure")
	return None, hasMathControl


def _getMathMlFromTextInfo(info, allowWordCom=False):
	"""Return MathML enclosing a TextInfo; COM is opt-in for caret-aligned calls."""
	return _getMathContextFromTextInfo(info, allowWordCom=allowWordCom)[0]


def _describeWordTextInfo(info, mathMl, unit, reason, confirmedMath):
	"""Record the Word caret route which supplied MathML instead of native text."""
	global _lastWordTextInfoDiagnostic
	obj = _getWordObjectFromTextInfo(info)
	appModule = getattr(obj, "appModule", None) if obj is not None else None
	_lastWordTextInfoDiagnostic = (
		f"app={getattr(appModule, 'appName', None)!r}; "
		f"officeProduct={getattr(appModule, 'productName', None)!r}; "
		f"officeVersion={getattr(appModule, 'productVersion', None)!r}; "
		f"objectClass={type(obj).__module__}.{type(obj).__name__}; "
		f"textInfoClass={type(info).__module__}.{type(info).__name__}; "
		f"unit={unit!r}; reason={reason!r}; "
		f"confirmedMath={confirmedMath}; "
		f"mathMlAvailable={mathMl is not None}; "
		f"mathMlLength={len(mathMl) if mathMl is not None else 0}"
	)


def _installMathTextInfoSpeechHooks():
	"""Replace Word's English linear equation stream with the enclosing MathML.

	Word keeps focus on its document rather than on a Role.MATH object. During
	character and word movement NVDA requests ``extraDetail`` and deliberately
	uses Word's inner speakable text (for example ``x squared plus 1``), bypassing
	the normal math provider. This generator hook preserves NVDA's field cache but
	yields only this add-on's Greek rendering whenever Word exposes MathML.
	"""
	global _textSpeechCoreModule, _textSpeechPublicModule
	global _originalGetTextInfoSpeech, _originalPublicGetTextInfoSpeech
	global _textInfoSpeechHook, _originalAddMathForTextInfo, _addMathForTextInfoHook
	global _hasLoggedWordTextInfoRoute
	try:
		import controlTypes
		import speech
		import textInfos
		from speech import speech as speechCore
	except (ImportError, AttributeError):
		return False

	if not all(
		callable(value)
		for value in (
			getattr(speechCore, "getTextInfoSpeech", None),
			getattr(speech, "getTextInfoSpeech", None),
			getattr(speechCore, "_extendSpeechSequence_addMathForTextInfo", None),
		)
	):
		return False

	if _textInfoSpeechHook is not None:
		repaired = False
		if speechCore.getTextInfoSpeech is not _textInfoSpeechHook:
			speechCore.getTextInfoSpeech = _textInfoSpeechHook
			repaired = True
		if speech.getTextInfoSpeech is not _textInfoSpeechHook:
			speech.getTextInfoSpeech = _textInfoSpeechHook
			repaired = True
		if speechCore._extendSpeechSequence_addMathForTextInfo is not _addMathForTextInfoHook:
			speechCore._extendSpeechSequence_addMathForTextInfo = _addMathForTextInfoHook
			repaired = True
		if repaired:
			log.warning("Greek Math Reader: repaired forced Word TextInfo math route")
		return True

	originalGetTextInfoSpeech = speechCore.getTextInfoSpeech
	originalPublicGetTextInfoSpeech = speech.getTextInfoSpeech
	originalAddMathForTextInfo = speechCore._extendSpeechSequence_addMathForTextInfo
	forcedUnits = {textInfos.UNIT_CHARACTER, textInfos.UNIT_WORD}

	def getTextInfoSpeech(
		info,
		useCache=True,
		formatConfig=None,
		unit=None,
		reason=controlTypes.OutputReason.QUERY,
		_prefixSpeechCommand=None,
		onlyInitialFields=False,
		suppressBlanks=False,
	):
		global _hasLoggedWordTextInfoRoute, _hasLoggedWordNativeTranslation
		if _exclusiveModeActive and _isWordTextInfo(info):
			# Make the provider visible before Word decides whether to retain its
			# native English content for ordinary line and say-all speech.
			if _provider is None or mathPres.speechProvider is not _provider:
				_register()
			if unit not in forcedUnits:
				# Record routes such as current-line reading even though their final
				# speech is handled by the last-mile Word safeguard below.
				observedMathMl, observedConfirmedMath = _getMathContextFromTextInfo(
					info,
					allowWordCom=False,
				)
				_describeWordTextInfo(
					info,
					observedMathMl,
					unit,
					reason,
					observedConfirmedMath,
				)
			if (
				unit in forcedUnits
				and reason != controlTypes.OutputReason.ONLYCACHE
				and not onlyInitialFields
			):
				mathMl, confirmedMath = _getMathContextFromTextInfo(
					info,
					allowWordCom=reason == controlTypes.OutputReason.CARET,
				)
				_describeWordTextInfo(info, mathMl, unit, reason, confirmedMath)
				if mathMl is not None:
					# Let NVDA update its control-field cache, but discard Word's
					# native x-squared English speech sequence.
					try:
						cacheGenerator = originalGetTextInfoSpeech(
							info,
							useCache,
							formatConfig,
							unit,
							controlTypes.OutputReason.ONLYCACHE,
							None,
							onlyInitialFields,
							suppressBlanks,
						)
						for _unusedSequence in cacheGenerator:
							pass
					except Exception:
						log.exception("Greek Math Reader: could not update Word TextInfo speech cache")
					if not _hasLoggedWordTextInfoRoute:
						log.info(
							"Greek Math Reader: replaced Word's native English equation text "
							"with Greek MathML speech; " + _lastWordTextInfoDiagnostic
						)
						_hasLoggedWordTextInfoRoute = True
					sequence = []
					if _prefixSpeechCommand is not None:
						sequence.append(_prefixSpeechCommand)
					sequence.extend(_provider.getSpeechForMathMl(mathMl))
					if sequence:
						yield sequence
						return True
					return False
				if not confirmedMath:
					return (yield from originalGetTextInfoSpeech(
						info,
						useCache,
						formatConfig,
						unit,
						reason,
						_prefixSpeechCommand,
						onlyInitialFields,
						suppressBlanks,
					))
				# Last-resort defence for legacy/secured Word environments where
				# neither UIA nor the read-only OMath fallback yields structure.
				# An enclosing math control/OMath has already independently
				# confirmed the context, so ordinary Word prose is never translated.
				originalGenerator = originalGetTextInfoSpeech(
					info,
					useCache,
					formatConfig,
					unit,
					reason,
					_prefixSpeechCommand,
					onlyInitialFields,
					suppressBlanks,
				)
				while True:
					try:
						wordSequence = next(originalGenerator)
					except StopIteration as finished:
						return finished.value
					normalizedSequence, changed = _normalizeWordNativeSpeechSequence(wordSequence)
					if changed:
						if not _hasLoggedWordNativeTranslation:
							log.warning(
								"Greek Math Reader: Word exposed no equation structure; "
								"translated its explicit English math vocabulary as a fallback"
							)
							_hasLoggedWordNativeTranslation = True
						yield tokensToSpeechSequence(normalizedSequence)
					else:
						yield wordSequence
		return (yield from originalGetTextInfoSpeech(
			info,
			useCache,
			formatConfig,
			unit,
			reason,
			_prefixSpeechCommand,
			onlyInitialFields,
			suppressBlanks,
		))

	def addMathForTextInfo(speechSequence, info, field):
		if _exclusiveModeActive:
			try:
				mathMl = info.getMathMl(field)
			except (NotImplementedError, LookupError):
				mathMl = None
			except Exception:
				mathMl = None
			if isinstance(mathMl, str) and mathMl.strip():
				if _provider is None:
					_register()
				speechSequence.extend(_provider.getSpeechForMathMl(mathMl))
				return
		return originalAddMathForTextInfo(speechSequence, info, field)

	getTextInfoSpeech._greekMathReaderWordTextInfoRoute = True
	addMathForTextInfo._greekMathReaderTextInfoMathAppender = True
	_textSpeechCoreModule = speechCore
	_textSpeechPublicModule = speech
	_originalGetTextInfoSpeech = originalGetTextInfoSpeech
	_originalPublicGetTextInfoSpeech = originalPublicGetTextInfoSpeech
	_textInfoSpeechHook = getTextInfoSpeech
	_originalAddMathForTextInfo = originalAddMathForTextInfo
	_addMathForTextInfoHook = addMathForTextInfo
	speechCore.getTextInfoSpeech = getTextInfoSpeech
	speech.getTextInfoSpeech = getTextInfoSpeech
	speechCore._extendSpeechSequence_addMathForTextInfo = addMathForTextInfo
	log.info("Greek Math Reader: forced Word TextInfo math route installed")
	return True


def _removeMathTextInfoSpeechHooks():
	"""Restore the exact TextInfo functions displaced by this add-on."""
	global _textSpeechCoreModule, _textSpeechPublicModule
	global _originalGetTextInfoSpeech, _originalPublicGetTextInfoSpeech
	global _textInfoSpeechHook, _originalAddMathForTextInfo, _addMathForTextInfoHook
	if (
		_textSpeechCoreModule is not None
		and _textSpeechCoreModule.getTextInfoSpeech is _textInfoSpeechHook
	):
		_textSpeechCoreModule.getTextInfoSpeech = _originalGetTextInfoSpeech
	if (
		_textSpeechPublicModule is not None
		and _textSpeechPublicModule.getTextInfoSpeech is _textInfoSpeechHook
	):
		_textSpeechPublicModule.getTextInfoSpeech = _originalPublicGetTextInfoSpeech
	if (
		_textSpeechCoreModule is not None
		and getattr(_textSpeechCoreModule, "_extendSpeechSequence_addMathForTextInfo", None)
		is _addMathForTextInfoHook
	):
		_textSpeechCoreModule._extendSpeechSequence_addMathForTextInfo = _originalAddMathForTextInfo
	_textSpeechCoreModule = None
	_textSpeechPublicModule = None
	_originalGetTextInfoSpeech = None
	_originalPublicGetTextInfoSpeech = None
	_textInfoSpeechHook = None
	_originalAddMathForTextInfo = None
	_addMathForTextInfoHook = None


def _redirectStaleMathCatInteraction(obj):
	"""Replace an already-focused MathCAT navigator with Greek interaction."""
	try:
		from mathPres.MathCAT.MathCAT import MathCATInteraction
	except (ImportError, AttributeError):
		return False
	if not isinstance(obj, MathCATInteraction):
		return False
	mathMl = getattr(obj, "initMathML", None)
	if not isinstance(mathMl, str) or not mathMl.strip():
		return False
	if _provider is None:
		_register()
	log.warning("Greek Math Reader: replacing stale English MathCAT interaction")
	_provider.interactWithMathMl(mathMl)
	return True


def _installMathCatSpeechFallback():
	"""Make the built-in MathCAT provider delegate speech to this add-on.

	The normal and documented integration is ``mathPres.speechProvider``. Some
	NVDA/application transitions can nevertheless leave an already-created
	MathCAT object on the effective speech path after this add-on registered.
	Hooking the built-in provider is a deliberately narrow safety net: it changes
	only MathCAT speech, only while this global plugin is loaded, and is restored
	exactly when the global plugin terminates.
	"""
	global _mathCatClass, _originalMathCatSpeech, _mathCatSpeechFallback
	try:
		from mathPres.MathCAT.MathCAT import MathCAT
	except (ImportError, AttributeError):
		return False
	if _mathCatSpeechFallback is not None and _mathCatClass is MathCAT:
		if MathCAT.getSpeechForMathMl is not _mathCatSpeechFallback:
			MathCAT.getSpeechForMathMl = _mathCatSpeechFallback
			log.warning("Greek Math Reader: repaired MathCAT speech fallback")
		return True
	if _mathCatSpeechFallback is not None:
		_removeMathCatSpeechFallback()
	original = MathCAT.getSpeechForMathMl
	if getattr(original, "_greekMathReaderFallback", False):
		# A previous instance has not finished unloading yet. Do not wrap it twice.
		return False

	def getSpeechForMathMl(mathCatInstance, mathMl):
		global _hasLoggedMathCatFallback
		if _exclusiveModeActive:
			if not _hasLoggedMathCatFallback:
				log.warning(
					"Greek Math Reader: MathCAT received the speech request; "
					"redirecting it to the Greek provider"
				)
				_hasLoggedMathCatFallback = True
			if _provider is None:
				_register()
			return _provider.getSpeechForMathMl(mathMl)
		return original(mathCatInstance, mathMl)

	getSpeechForMathMl._greekMathReaderFallback = True
	_mathCatClass = MathCAT
	_originalMathCatSpeech = original
	_mathCatSpeechFallback = getSpeechForMathMl
	MathCAT.getSpeechForMathMl = getSpeechForMathMl
	log.info("Greek Math Reader: MathCAT speech fallback installed")
	return True


def _removeMathCatSpeechFallback():
	"""Restore MathCAT's exact original speech method if our hook still owns it."""
	global _mathCatClass, _originalMathCatSpeech, _mathCatSpeechFallback
	if (
		_mathCatClass is not None
		and _mathCatSpeechFallback is not None
		and _mathCatClass.getSpeechForMathMl is _mathCatSpeechFallback
	):
		_mathCatClass.getSpeechForMathMl = _originalMathCatSpeech
	_mathCatClass = None
	_originalMathCatSpeech = None
	_mathCatSpeechFallback = None


def _installMathPresGuards():
	"""Prevent NVDA or later add-ons from replacing Greek math speech.

	This protects all three official mutation paths in ``mathPres``:
	``registerProvider``, ``initialize`` and ``terminate``. Foreign providers may
	still register braille, but speech and interaction remain exclusively Greek.
	"""
	global _exclusiveModeActive
	global _originalRegisterProvider, _originalMathPresInitialize, _originalMathPresTerminate
	global _registerProviderGuard, _mathPresInitializeGuard, _mathPresTerminateGuard
	if _registerProviderGuard is not None:
		_exclusiveModeActive = True
		repaired = False
		if mathPres.registerProvider is not _registerProviderGuard:
			mathPres.registerProvider = _registerProviderGuard
			repaired = True
		if (
			_mathPresInitializeGuard is not None
			and getattr(mathPres, "initialize", None) is not _mathPresInitializeGuard
		):
			mathPres.initialize = _mathPresInitializeGuard
			repaired = True
		if (
			_mathPresTerminateGuard is not None
			and getattr(mathPres, "terminate", None) is not _mathPresTerminateGuard
		):
			mathPres.terminate = _mathPresTerminateGuard
			repaired = True
		if repaired:
			log.warning("Greek Math Reader: repaired exclusive math provider guards")
		return

	originalRegister = mathPres.registerProvider
	originalInitialize = getattr(mathPres, "initialize", None)
	originalTerminate = getattr(mathPres, "terminate", None)

	def registerProvider(provider, speech=False, braille=False, interaction=False):
		global _hasLoggedBlockedProvider
		if _exclusiveModeActive and provider is not _provider:
			if (speech or interaction) and not _hasLoggedBlockedProvider:
				log.warning(
					"Greek Math Reader: blocked another provider from replacing "
					"exclusive Greek math speech or interaction"
				)
				_hasLoggedBlockedProvider = True
			return originalRegister(
				provider,
				speech=False,
				braille=braille,
				interaction=False,
			)
		return originalRegister(
			provider,
			speech=speech,
			braille=braille,
			interaction=interaction,
		)

	if callable(originalInitialize):
		def initialize():
			result = originalInitialize()
			if _exclusiveModeActive:
				_register()
			return result
	else:
		initialize = None

	if callable(originalTerminate):
		def terminate():
			result = originalTerminate()
			if _exclusiveModeActive:
				_register()
			return result
	else:
		terminate = None

	registerProvider._greekMathReaderGuard = True
	if initialize is not None:
		initialize._greekMathReaderGuard = True
	if terminate is not None:
		terminate._greekMathReaderGuard = True
	_originalRegisterProvider = originalRegister
	_originalMathPresInitialize = originalInitialize
	_originalMathPresTerminate = originalTerminate
	_registerProviderGuard = registerProvider
	_mathPresInitializeGuard = initialize
	_mathPresTerminateGuard = terminate
	_exclusiveModeActive = True
	mathPres.registerProvider = registerProvider
	if initialize is not None:
		mathPres.initialize = initialize
	if terminate is not None:
		mathPres.terminate = terminate
	log.info("Greek Math Reader: exclusive math provider guards installed")


def _removeMathPresGuards():
	"""Remove only the mathPres hooks that are still owned by this add-on."""
	global _exclusiveModeActive
	global _originalRegisterProvider, _originalMathPresInitialize, _originalMathPresTerminate
	global _registerProviderGuard, _mathPresInitializeGuard, _mathPresTerminateGuard
	_exclusiveModeActive = False
	if mathPres.registerProvider is _registerProviderGuard:
		mathPres.registerProvider = _originalRegisterProvider
	if _mathPresInitializeGuard is not None and getattr(mathPres, "initialize", None) is _mathPresInitializeGuard:
		mathPres.initialize = _originalMathPresInitialize
	if _mathPresTerminateGuard is not None and getattr(mathPres, "terminate", None) is _mathPresTerminateGuard:
		mathPres.terminate = _originalMathPresTerminate
	_originalRegisterProvider = None
	_originalMathPresInitialize = None
	_originalMathPresTerminate = None
	_registerProviderGuard = None
	_mathPresInitializeGuard = None
	_mathPresTerminateGuard = None


def isProviderActive():
	"""Return whether this add-on owns both speech and interaction slots."""
	return (
		_provider is not None
		and mathPres.speechProvider is _provider
		and mathPres.interactionProvider is _provider
	)


def _ownsAnyProviderSlot():
	return _provider is not None and (
		mathPres.speechProvider is _provider
		or mathPres.interactionProvider is _provider
	)


def _register():
	"""Install the exclusive provider for speech and interaction.

	The provider object is intentionally reused. The providers displaced on the
	first registration are preserved so the add-on can restore them when it is
	unloaded; later takeover attempts do not replace that original snapshot.
	"""
	global _provider, _previousSpeechProvider, _previousInteractionProvider, _registered
	if _provider is None:
		_provider = GreekMathProvider()
	replaceSpeech = mathPres.speechProvider is not _provider
	replaceInteraction = mathPres.interactionProvider is not _provider
	if not replaceSpeech and not replaceInteraction:
		_registered = True
		return
	wasRegistered = _registered
	if replaceSpeech and not wasRegistered:
		_previousSpeechProvider = mathPres.speechProvider
	if replaceInteraction and not wasRegistered:
		_previousInteractionProvider = mathPres.interactionProvider
	mathPres.registerProvider(
		_provider,
		speech=replaceSpeech,
		interaction=replaceInteraction,
	)
	_registered = True
	if wasRegistered:
		log.warning("Greek Math Reader: provider was replaced; registration recovered")
	else:
		log.info("Greek Math Reader: provider registered")


def _unregister():
	"""Restore provider slots still owned by this add-on and release our state.

	Another add-on may replace either slot after ours is registered. We must not
	overwrite that newer provider, but we must *always* clear ``_registered``;
	otherwise a later re-enable would incorrectly believe this provider was
	already active.
	"""
	global _registered, _previousSpeechProvider, _previousInteractionProvider
	if not _registered and not _ownsAnyProviderSlot():
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
	"""Enforce exclusive Greek speech while the add-on is installed."""
	_enforceRequiredNvdaSettings()
	_installMathPresGuards()
	_register()
	_installMathCatSpeechFallback()
	_installMathObjectSpeechHook()
	_installMathTextInfoSpeechHooks()
	_installFinalWordSpeechFilter()
	return isProviderActive()


def _enforceRequiredNvdaSettings():
	"""Force NVDA settings which otherwise allow English math to bypass us."""
	section = config.conf["greekMathReader"]
	section["enabled"] = True
	section["forceGreekLanguage"] = True
	try:
		config.conf["speech"]["autoLanguageSwitching"] = True
	except (KeyError, TypeError, ValueError):
		pass
	try:
		config.conf["math"]["other"]["useWordNativeMath"] = False
	except (KeyError, TypeError, ValueError):
		pass
	try:
		# Modern Word equations expose MathML through UI Automation. The legacy
		# Word object model exposes only older MathType equations as MathML.
		wordUiaChanged = int(config.conf["UIA"]["allowInMSWord"]) != _WORD_UIA_ALWAYS
		config.conf["UIA"]["allowInMSWord"] = _WORD_UIA_ALWAYS
		if wordUiaChanged:
			try:
				import UIAHandler

				if UIAHandler.handler is not None:
					UIAHandler.handler.UIAWindowHandleCache.clear()
			except (ImportError, AttributeError):
				pass
	except (KeyError, TypeError, ValueError):
		pass


def resetRecommendedDefaults():
	"""Reset add-on preferences and repair every exclusive routing layer."""
	section = config.conf["greekMathReader"]
	section["verbosity"] = 1
	section["decimalComma"] = True
	section["translateUnconfirmedWordMath"] = True
	_enforceRequiredNvdaSettings()
	_installMathPresGuards()
	_register()
	_installMathCatSpeechFallback()
	_installMathObjectSpeechHook()
	_installMathTextInfoSpeechHooks()
	_installFinalWordSpeechFilter()
	return isProviderActive()


def _isAutoLanguageSwitchingEnabled():
	"""Whether NVDA honours the Greek language tag on math speech."""
	try:
		return bool(config.conf["speech"]["autoLanguageSwitching"])
	except KeyError:
		return True


def _isWordNativeMathEnabled():
	"""Whether NVDA lets Word itself speak equations instead of math providers.

	When NVDA's "Use native math support in Word and Outlook" option is on,
	focusing Word tears down every math presentation provider (including this
	add-on) and Word's own English equation descriptions are read instead.
	"""
	try:
		return bool(config.conf["math"]["other"]["useWordNativeMath"])
	except KeyError:
		return False


def _isWordUIAAlwaysEnabled():
	"""Whether NVDA is forced to expose modern Word equations through UIA."""
	try:
		return int(config.conf["UIA"]["allowInMSWord"]) == _WORD_UIA_ALWAYS
	except (KeyError, TypeError, ValueError):
		return False


def _describeCurrentSynth():
	"""Return 'synthName voice=...' for the log, or 'unknown' outside NVDA."""
	try:
		import synthDriverHandler

		synth = synthDriverHandler.getSynth()
		if synth is None:
			return "none"
		return f"{synth.name} voice={getattr(synth, 'voice', None)}"
	except Exception:
		return "unknown"


def _getSynthDiagnostics():
	"""Return concise voice details suitable for the log or clipboard."""
	try:
		import synthDriverHandler

		synth = synthDriverHandler.getSynth()
		if synth is None:
			return "synth=none"
		greekVoices = []
		try:
			for voice in synth.availableVoices.values():
				language = getattr(voice, "language", None)
				if isinstance(language, str) and language.lower().replace("-", "_").startswith("el"):
					greekVoices.append(f"{getattr(voice, 'name', None)} ({language})")
		except Exception:
			greekVoices = ["unavailable"]
		return (
			f"synth={getattr(synth, 'name', None)!r}; "
			f"voice={getattr(synth, 'voice', None)!r}; "
			f"voiceLanguage={getattr(synth, 'language', None)!r}; "
			f"greekSupported={getGreekVoiceSupport()!r}; "
			f"greekVoices={greekVoices!r}"
		)
	except Exception as error:
		return f"synthDiagnosticsError={error!r}"


def _getPlatformDiagnostics():
	"""Return Windows details relevant to Word's custom MathML extension."""
	try:
		import winVersion

		return f"windows={winVersion.getWinVer()!r}"
	except Exception as error:
		return f"windows=unavailable ({error!r})"


_lastWordBuildDiagnostic = "Word has not been contacted since NVDA started."

# The Word.MathML UIA custom property exists in Word build 14326 and higher
# (Microsoft 365, roughly April 2021). Older builds can never expose MathML
# through UIA, so equations there rely entirely on the native OMath fallback.
_WORD_UIA_MATHML_MINIMUM_BUILD = 14326


def _describeWordApplication():
	"""Record Word's version/build and whether its UIA MathML property can exist."""
	global _lastWordBuildDiagnostic
	try:
		import api

		focus = api.getFocusObject()
		appName = getattr(getattr(focus, "appModule", None), "appName", None)
	except Exception:
		return _lastWordBuildDiagnostic
	if appName not in ("winword", "outlook"):
		return (
			_lastWordBuildDiagnostic
			+ " (focus is not in Word or Outlook right now; move to the equation "
			+ "and copy diagnostics again for Word-specific data)"
		)
	for candidate in _iterWordObjectCandidates(focus, includeFocus=True):
		try:
			application = candidate.WinwordApplicationObject
			version = str(application.Version)
			build = str(application.Build)
		except Exception:
			continue
		buildNumber = None
		try:
			parts = build.split(".")
			if len(parts) >= 3:
				buildNumber = int(parts[2])
		except (ValueError, IndexError):
			buildNumber = None
		if buildNumber is None:
			verdict = "unknown build format"
		elif buildNumber >= _WORD_UIA_MATHML_MINIMUM_BUILD:
			verdict = f"expected (build {buildNumber} >= {_WORD_UIA_MATHML_MINIMUM_BUILD})"
		else:
			verdict = (
				f"NOT AVAILABLE (build {buildNumber} < {_WORD_UIA_MATHML_MINIMUM_BUILD}): "
				"this Word cannot expose MathML through UIA; equations depend "
				"entirely on the native OMath fallback"
			)
		_lastWordBuildDiagnostic = (
			f"version={version}; build={build}; uiaMathMlProperty={verdict}"
		)
		return _lastWordBuildDiagnostic
	_lastWordBuildDiagnostic = (
		"focus is in Word or Outlook but the COM application object was "
		"unreachable; the native OMath fallback cannot work in this state"
	)
	return _lastWordBuildDiagnostic


def buildDiagnostics():
	"""Build a paste-ready report which identifies the exact installed code path."""
	try:
		import api

		obj = api.getFocusObject()
		focus = (
			f"app={getattr(getattr(obj, 'appModule', None), 'appName', None)!r}; "
			f"class={type(obj).__module__}.{type(obj).__name__}; "
			f"role={getattr(obj, 'role', None)!r}"
		)
	except Exception as error:
		focus = f"unavailable ({error!r})"
	try:
		mathCatLanguage = config.conf["math"]["speech"]["language"]
	except (KeyError, TypeError):
		mathCatLanguage = "unavailable"
	providerRequests = getattr(_provider, "speechRequestCount", 0) if _provider is not None else 0
	providerInput = (
		getattr(_provider, "lastInputDiagnostic", "No MathML received.")
		if _provider is not None
		else "Provider has not been constructed."
	)
	return "\n".join(
		[
			"Greek Math Reader diagnostics",
			f"add-on version={ADDON_VERSION}; build={BUILD_ID}",
			f"module={__file__}",
			f"providerActive={isProviderActive()}; provider={type(_provider).__name__ if _provider else None}",
			f"mathPresSpeechProvider={type(mathPres.speechProvider).__name__ if mathPres.speechProvider else None}",
			f"mathPresInteractionProvider={type(mathPres.interactionProvider).__name__ if mathPres.interactionProvider else None}",
			f"providerGuardsOwned={mathPres.registerProvider is _registerProviderGuard}",
			f"mathObjectHookOwned={_speechCoreModule is not None and _speechCoreModule.getObjectSpeech is _mathObjectSpeechHook}",
			f"wordTextInfoHookOwned={_textSpeechCoreModule is not None and _textSpeechCoreModule.getTextInfoSpeech is _textInfoSpeechHook}",
			f"textInfoMathAppenderOwned={_textSpeechCoreModule is not None and getattr(_textSpeechCoreModule, '_extendSpeechSequence_addMathForTextInfo', None) is _addMathForTextInfoHook}",
			f"mathCatFallbackOwned={_mathCatClass is not None and _mathCatClass.getSpeechForMathMl is _mathCatSpeechFallback}",
			f"finalSpeechFilterOwned={_finalSpeechFilterExtension is not None and _finalWordSpeechFilter is not None and any(handler is _finalWordSpeechFilter for handler in _finalSpeechFilterExtension.handlers)}",
			f"autoLanguageSwitching={_isAutoLanguageSwitchingEnabled()}",
			f"wordNativeMath={_isWordNativeMathEnabled()}",
			f"wordUIAAlways={_isWordUIAAlwaysEnabled()}",
			f"translateUnconfirmedWordMath={bool(config.conf['greekMathReader'].get('translateUnconfirmedWordMath', True))}",
			f"mathCatLanguage={mathCatLanguage!r} (English is normal; this setting is bypassed)",
			_getPlatformDiagnostics(),
			_getSynthDiagnostics(),
			f"focus={focus}",
			f"wordApplication={_describeWordApplication()}",
			f"lastMathObject={_lastMathObjectDiagnostic}",
			f"lastWordTextInfo={_lastWordTextInfoDiagnostic}",
			f"lastWordNotification={_lastWordNotificationDiagnostic}",
			f"lastWordFinalSpeech={_lastWordFinalSpeechDiagnostic}",
			f"finalWordSpeechCounts=invocations:{_finalWordSpeechInvocationCount}; candidates:{_finalWordSpeechCandidateCount}; replacements:{_finalWordSpeechReplacementCount}",
			f"lastWordComFallback={_lastWordComDiagnostic}",
			f"providerSpeechRequests={providerRequests}",
			f"lastProviderInput={providerInput}",
		]
	)


def copyDiagnostics():
	"""Copy and log the exact runtime diagnosis for a Windows report."""
	import api

	_enforceRequiredNvdaSettings()
	_installMathPresGuards()
	_register()
	_installMathCatSpeechFallback()
	_installMathObjectSpeechHook()
	_installMathTextInfoSpeechHooks()
	_installFinalWordSpeechFilter()
	diagnostics = buildDiagnostics()
	log.info(diagnostics)
	return bool(api.copyToClip(diagnostics))


def speakSelfTest():
	"""Speak known MathML directly and announce anything blocking Greek math.

	The sample equation always goes straight to this add-on's provider, so it
	tests the engine and voice after all exclusive routing and required NVDA
	settings have been reasserted.
	"""
	import speech

	previousSpeechProvider = mathPres.speechProvider
	_enforceRequiredNvdaSettings()
	_register()
	log.info(
		"Greek Math Reader: direct self-test; exclusive=True; "
		f"provider active={isProviderActive()}; "
		f"speech provider before test={type(previousSpeechProvider).__name__}; "
		f"synth={_describeCurrentSynth()}; "
		f"greekVoiceSupported={getGreekVoiceSupport()}; "
		f"autoLanguageSwitching={_isAutoLanguageSwitchingEnabled()}; "
		f"useWordNativeMath={_isWordNativeMathEnabled()}; "
		f"wordUIAAlways={_isWordUIAAlwaysEnabled()}; "
		f"version={ADDON_VERSION}; build={BUILD_ID}"
	)
	speech.speak(_provider.getSpeechForMathMl(_SELF_TEST_MATHML))
	if previousSpeechProvider is not None and previousSpeechProvider is not _provider:
		ui.message(
			# Translators: Spoken after the self-test when another math reader had
			# taken over NVDA's math provider slot and the add-on reclaimed it.
			_(
				"Another math reader had taken over until now; "
				"Greek math reading has been restored."
			)
		)
	if (
		config.conf["greekMathReader"]["forceGreekLanguage"]
		and getGreekVoiceSupport() is False
	):
		ui.message(
			# Translators: Spoken when the current synthesizer cannot switch to Greek.
			_(
				"Warning: the current synthesizer has no Greek voice installed. "
				"Install a Greek voice such as Microsoft Stefanos in Windows, then "
				"select Windows OneCore voices in NVDA."
			)
		)


_WORD_NATIVE_TEXT_REPLACEMENTS = (
	# Equation boundary announcements Word/NVDA speak around a display equation.
	# Kept first so these multi-word phrases match before their shorter parts.
	("end of equation", "τέλος εξίσωσης"),
	("start of equation", "αρχή εξίσωσης"),
	("end of section", "τέλος εξίσωσης"),
	("start of section", "αρχή εξίσωσης"),
	("less than or equal to", "μικρότερο ή ίσο του"),
	("greater than or equal to", "μεγαλύτερο ή ίσο του"),
	("not equal to", "διάφορο του"),
	("open parenthesis", "ανοίγει παρένθεση"),
	("close parenthesis", "κλείνει η παρένθεση"),
	("open bracket", "ανοίγει αγκύλη"),
	("close bracket", "κλείνει η αγκύλη"),
	("square root of", "τετραγωνική ρίζα του"),
	("cube root of", "κυβική ρίζα του"),
	("to the power of", "στη δύναμη"),
	("raised to", "υψωμένο σε"),
	("divided by", "διά"),
	("multiplied by", "επί"),
	("equal to", "ίσον"),
	("squared", "στο τετράγωνο"),
	("cubed", "στον κύβο"),
	("superscript", "άνω δείκτης"),
	("subscript", "κάτω δείκτης"),
	("numerator", "αριθμητής"),
	("denominator", "παρονομαστής"),
	("summation", "άθροισμα"),
	("integral", "ολοκλήρωμα"),
	("multiplied", "επί"),
	("divided", "διά"),
	("raised", "υψωμένο"),
	("fraction", "κλάσμα"),
	("equals", "ίσον"),
	("equal", "ίσον"),
	("power", "δύναμη"),
	("root", "ρίζα"),
	("limit", "όριο"),
	("over", "διά"),
	("plus", "συν"),
	("minus", "πλην"),
	("times", "επί"),
	("open paren", "ανοίγει παρένθεση"),
	("close paren", "κλείνει η παρένθεση"),
	("degrees", "μοίρες"),
	("degree", "μοίρες"),
	("percent", "τοις εκατό"),
	("infinity", "άπειρο"),
	("prime", "τόνος"),
	("vector", "διάνυσμα"),
	("sum", "άθροισμα"),
	("product", "γινόμενο"),
	# Greek letter names as Word verbalizes them in English. These both widen
	# the math-detection gate and translate correctly in the mtext fallback.
	("alpha", "άλφα"), ("beta", "βήτα"), ("gamma", "γάμα"), ("delta", "δέλτα"),
	("epsilon", "έψιλον"), ("zeta", "ζήτα"), ("eta", "ήτα"), ("theta", "θήτα"),
	("iota", "γιώτα"), ("kappa", "κάπα"), ("lambda", "λάμδα"), ("mu", "μι"),
	("nu", "νι"), ("xi", "ξι"), ("omicron", "όμικρον"), ("pi", "πι"),
	("rho", "ρο"), ("sigma", "σίγμα"), ("tau", "ταυ"), ("upsilon", "ύψιλον"),
	("phi", "φι"), ("chi", "χι"), ("psi", "ψι"), ("omega", "ωμέγα"),
)

_WORD_NATIVE_MATH_WORDS = tuple(
	source for source, _replacement in _WORD_NATIVE_TEXT_REPLACEMENTS
)


def _normalizeWordNativeMathText(text):
	"""Translate explicit English structure in Word's unstructured fallback."""
	import re

	for source, replacement in _WORD_NATIVE_TEXT_REPLACEMENTS:
		text = re.sub(
			rf"(?<!\w){re.escape(source)}(?!\w)",
			replacement,
			text,
			flags=re.IGNORECASE,
		)
	return re.sub(r"\s+", " ", text).strip()


def _normalizeWordNativeSpeechSequence(sequence):
	"""Normalize strings and discard conflicting language tags only if changed."""
	try:
		from speech.commands import LangChangeCommand
	except ImportError:
		LangChangeCommand = ()
	normalized = []
	changed = False
	for item in sequence:
		if isinstance(item, str):
			normalizedItem = _normalizeWordNativeMathText(item)
			changed = changed or normalizedItem != item
			normalized.append(normalizedItem)
		elif isinstance(item, LangChangeCommand):
			# Drop Word's English tag only when the sequence is ultimately
			# normalized; tokensToSpeechSequence adds one el_GR wrapper.
			normalized.append(item)
		else:
			normalized.append(item)
	if changed and LangChangeCommand:
		normalized = [item for item in normalized if not isinstance(item, LangChangeCommand)]
	return normalized, changed


def _getWordMathContextAtCaret(obj, allowAdjacentEnd=False, transformOmml=True):
	"""Return ``(MathML, confirmedMath)`` at Word's current caret.

	UIA is probed first without COM.  Word's COM selection describes the same
	caret regardless of which TextInfo position exposed it, so the comparatively
	expensive native OMath lookup is performed at most once.
	"""
	try:
		import textInfos
	except ImportError:
		return None, False
	candidates = list(_iterWordObjectCandidates(obj, includeFocus=True))
	confirmedMath = False
	wordObj = None
	for candidate in candidates:
		if wordObj is None:
			try:
				selection = candidate.WinwordSelectionObject
			except Exception:
				selection = None
			if selection is not None:
				wordObj = candidate
		for position in (textInfos.POSITION_CARET, textInfos.POSITION_SELECTION):
			try:
				info = candidate.makeTextInfo(position)
			except Exception:
				continue
			if wordObj is None:
				try:
					infoObj = info.obj
					selection = infoObj.WinwordSelectionObject
				except Exception:
					selection = None
				if selection is not None:
					wordObj = infoObj
			mathMl, infoConfirmedMath = _getMathContextFromTextInfo(
				info,
				allowWordCom=False,
			)
			confirmedMath = confirmedMath or infoConfirmedMath
			if mathMl is not None:
				return mathMl, True
	if wordObj is not None:
		try:
			if transformOmml:
				mathMl, insideOMath = _getWordComMathContext(
					wordObj,
					allowAdjacentEnd=allowAdjacentEnd,
				)
			else:
				insideOMath = _findContainingWordOMath(
					wordObj,
					allowAdjacentEnd=allowAdjacentEnd,
				) is not None
				mathMl = None
			confirmedMath = confirmedMath or insideOMath
			if mathMl is not None:
				return mathMl, True
		except Exception:
			log.exception("Greek Math Reader: unexpected Word notification OMath failure")
	return None, confirmedMath


def _looksLikeWordNativeMathSpeech(text):
	if not isinstance(text, str):
		return False
	import re

	return any(
		re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text, flags=re.IGNORECASE)
		for word in _WORD_NATIVE_MATH_WORDS
	)


def _notificationIsFromFocusedApp(obj):
	"""Mirror NVDA's guard against speaking background UIA notifications."""
	try:
		import api

		return obj.appModule == api.getFocusObject().appModule
	except Exception:
		return False


def _isPlausibleWordLinearMathText(text):
	"""Reject prose while accepting Word's compact English math linearization."""
	if not isinstance(text, str) or not text.strip() or len(text) > 2000:
		return False
	if not _looksLikeWordNativeMathSpeech(text):
		return False
	import re

	tokens = re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)
	if len(tokens) <= 2:
		return True
	knownWords = {
		word.casefold()
		for source, _replacement in _WORD_NATIVE_TEXT_REPLACEMENTS
		for word in source.split()
	}
	knownWords.update(
		{
			"zero", "one", "two", "three", "four", "five", "six", "seven",
			"eight", "nine", "ten", "eleven", "twelve", "infinity", "negative",
			"positive", "from", "to", "of", "with", "respect", "as", "approaches",
			"tends", "towards", "the", "a", "an", "and", "at", "begin", "end",
			"start", "equation", "math", "selected", "selection", "unselected",
			"selecting", "unselecting", "blank", "row", "column",
			# NVDA's Greek UI announces selections in Greek around the English math.
			"επιλέχθηκε", "αποεπιλέχθηκε", "επιλογή", "επιλεγμένο", "γραμμή", "κενό",
			"matrix", "determinant", "alpha", "beta", "gamma", "delta", "epsilon",
			"theta", "lambda", "mu", "pi", "rho", "sigma", "phi", "chi", "psi",
			"omega", "sin", "cos", "tan", "log", "ln", "det", "max", "min",
			"sup", "inf",
		}
	)
	unknown = [
		token
		for token in tokens
		if token not in knownWords and not token.isdigit() and len(token) > 1
	]
	return len(unknown) <= max(1, len(tokens) // 5)


def _isShortWordMathToken(text):
	"""Return whether one split speech string is plainly equation content."""
	if not isinstance(text, str) or not text.strip() or len(text) > 120:
		return False
	if _looksLikeWordNativeMathSpeech(text):
		return True
	import re

	return bool(
		re.fullmatch(
			r"[\s\d\u0370-\u03ff\u1f00-\u1fffA-Za-z+\-−=×÷*/^_.,()\[\]{}|<>≤≥≠∞]+",
			text,
		)
		and len(re.findall(r"[A-Za-z]+", text)) <= 2
	)


def _wordTextAsFallbackMathMl(text):
	"""Wrap trusted Word speech as safe MathML mtext for Greek normalization."""
	from html import escape

	clean = "".join(
		char
		if char in ("\t", "\n", "\r")
		or 0x20 <= ord(char) <= 0xD7FF
		or 0xE000 <= ord(char) <= 0xFFFD
		or 0x10000 <= ord(char) <= 0x10FFFF
		else "\ufffd"
		for char in text
	)
	return (
		"<math xmlns='http://www.w3.org/1998/Math/MathML'><mtext>"
		+ escape(clean, quote=False)
		+ "</mtext></math>"
	)


def _confirmedUtteranceLooksMathematical(items, text):
	"""Whether a COM/UIA-confirmed utterance plausibly *contains* the equation.

	A confirmed caret only proves where the caret rests, not what NVDA is
	saying: dialog or help prose spoken while the caret sits in an equation
	must stay untouched. Conversely, a mouse or keyboard selection
	announcement mixes the equation's English verbalization with prose (often
	Greek), which sinks the whole-text classifier — so individual sequence
	items and the Latin-only projection of the text each get their own chance.
	"""
	import re

	if _isPlausibleWordLinearMathText(text):
		return True
	for item in items:
		if isinstance(item, str) and item != text and _isPlausibleWordLinearMathText(item):
			return True
	asciiText = " ".join(re.findall(r"[A-Za-z0-9.,+\-^/=()]+", text))
	return bool(asciiText) and asciiText != text and _isPlausibleWordLinearMathText(asciiText)


def _replaceFinalWordSpeechSequence(speechSequence):
	"""Translate Word's English math at NVDA's final speech boundary.

	Some Word routes (current line, Say All, keyboard echo and Office-specific
	announcements) arrive directly at ``speech.speak`` and never request math
	presentation.  This last-mile safeguard changes a sequence only when it has
	explicit English math vocabulary *and* the live Word caret independently
	belongs to a UIA math field or native OMath.
	"""
	global _lastWordFinalSpeechDiagnostic
	global _finalWordSpeechCandidateCount, _finalWordSpeechReplacementCount
	if not isinstance(speechSequence, (list, tuple)):
		return None
	items = list(speechSequence)
	text = " ".join(item for item in items if isinstance(item, str)).strip()
	# Single characters and keyboard echo must never be rewritten, and without
	# at least one explicit English math word there is nothing to translate.
	# The stricter prose classifier is applied later, but only for utterances
	# that no native OMath or UIA math field could confirm: a confirmed
	# equation (for example a mouse selection spanning prose plus equation)
	# must not be discarded just because the prose outweighs the math words.
	if len(text) < 3 or not _looksLikeWordNativeMathSpeech(text):
		return None
	_finalWordSpeechCandidateCount += 1
	try:
		import api
		import core
		from utils.security import objectBelowLockScreenAndWindowsIsLocked

		focus = api.getFocusObject()
		appName = getattr(getattr(focus, "appModule", None), "appName", None)
	except Exception:
		return None
	if appName not in ("winword", "outlook"):
		return None
	if not core.isMainThread() or objectBelowLockScreenAndWindowsIsLocked(focus):
		return None
	mathMl, confirmedMath = _getWordMathContextAtCaret(
		focus,
		# Word often reports the collapsed caret at OMath.Range.End after
		# typing.  The strict prose classifier above makes the adjacent-left
		# read-only paragraph probe safe for this final fallback.
		allowAdjacentEnd=True,
		# Transform the located OMath so a whole equation line can be spoken
		# through the real Greek engine instead of keyword substitution.
		transformOmml=True,
	)
	_lastWordFinalSpeechDiagnostic = (
		f"app={appName!r}; confirmedMath={confirmedMath}; "
		f"structuredMathMlAvailable={mathMl is not None}; text={text[:240]!r}"
	)
	if not confirmedMath:
		# Backup mode: when no OMath/UIA confirmation is possible (COM
		# unreachable, protected view, Outlook reading pane), translate the
		# English anyway — but only when the strict classifier accepts the
		# utterance as Word's math verbalization rather than ordinary prose,
		# and only unless the user disabled it.
		try:
			backupEnabled = bool(config.conf["greekMathReader"]["translateUnconfirmedWordMath"])
		except KeyError:
			backupEnabled = True
		if not backupEnabled:
			_lastWordFinalSpeechDiagnostic += "; unconfirmed and backup mode disabled"
			return None
		if not _isPlausibleWordLinearMathText(text):
			_lastWordFinalSpeechDiagnostic += "; unconfirmed and rejected by prose classifier"
			return None
		_lastWordFinalSpeechDiagnostic += "; unconfirmed: backup translation"
	elif not _confirmedUtteranceLooksMathematical(items, text):
		# The caret is in an equation, but NVDA is saying something else
		# (dialog text, help prose, formatting announcements). Leave it alone.
		_lastWordFinalSpeechDiagnostic += "; confirmed caret but utterance reads as prose"
		return None
	if _provider is None:
		_register()
	try:
		from speech.commands import LangChangeCommand
	except ImportError:
		LangChangeCommand = ()
	stringItems = [item for item in items if isinstance(item, str) and item.strip()]
	allStringsAreMath = bool(stringItems) and all(
		_isShortWordMathToken(item) or _isPlausibleWordLinearMathText(item)
		for item in stringItems
	)
	if mathMl is not None and allStringsAreMath:
		# The whole utterance is the equation (a display-equation line, Say All
		# chunk, or selection announcement): speak the *parsed* equation once,
		# via the OMML→MathML transform, instead of translating Word's English
		# sentence word by word.  Word's own language tags are dropped; the
		# provider adds its Greek tag itself.
		replacement = []
		spokeMath = False
		for item in items:
			if isinstance(item, str) and item.strip():
				if not spokeMath:
					replacement.extend(_provider.getSpeechForMathMl(mathMl))
					spokeMath = True
			elif LangChangeCommand and isinstance(item, LangChangeCommand):
				continue
			else:
				replacement.append(item)
		_finalWordSpeechReplacementCount += 1
		_lastWordFinalSpeechDiagnostic += "; replaced entire utterance with transformed OMML"
		return replacement
	replacement = []
	replacedStrings = 0
	for item in items:
		if isinstance(item, str) and _isShortWordMathToken(item):
			replacement.extend(_provider.getSpeechForMathMl(_wordTextAsFallbackMathMl(item)))
			replacedStrings += 1
		else:
			replacement.append(item)
	if not replacedStrings:
		return None
	_finalWordSpeechReplacementCount += 1
	_lastWordFinalSpeechDiagnostic += f"; replacedStrings={replacedStrings}"
	return replacement


def _installFinalWordSpeechFilter():
	"""Register the last-mile safeguard at NVDA's official speech filter.

	Unlike monkeypatching ``speech.speak``, this also covers cached callables used
	by Say All and other modules initialized before this add-on.
	"""
	global _finalSpeechFilterExtension, _finalWordSpeechFilter
	global _hasLoggedFinalWordSpeechRoute
	try:
		from speech.extensions import filter_speechSequence
	except (ImportError, AttributeError):
		return False
	if _finalWordSpeechFilter is not None:
		if not any(handler is _finalWordSpeechFilter for handler in filter_speechSequence.handlers):
			filter_speechSequence.register(_finalWordSpeechFilter)
			log.warning("Greek Math Reader: repaired final Word speech filter")
		filter_speechSequence.moveToEnd(_finalWordSpeechFilter, last=False)
		_finalSpeechFilterExtension = filter_speechSequence
		return True

	def filterSpeechSequence(speechSequence):
		global _hasLoggedFinalWordSpeechRoute, _finalWordSpeechFilterActive
		global _finalWordSpeechInvocationCount
		_finalWordSpeechInvocationCount += 1
		if not _exclusiveModeActive or _finalWordSpeechFilterActive:
			return speechSequence
		_finalWordSpeechFilterActive = True
		try:
			replacement = _replaceFinalWordSpeechSequence(speechSequence)
		except Exception:
			log.exception("Greek Math Reader: final Word speech filter failed open")
			return speechSequence
		finally:
			_finalWordSpeechFilterActive = False
		if replacement is None:
			return speechSequence
		if not _hasLoggedFinalWordSpeechRoute:
			log.warning(
				"Greek Math Reader: replaced English at NVDA's final Word speech "
				"boundary; " + _lastWordFinalSpeechDiagnostic
			)
			_hasLoggedFinalWordSpeechRoute = True
		return replacement

	filterSpeechSequence._greekMathReaderFinalWordSpeechRoute = True
	_finalSpeechFilterExtension = filter_speechSequence
	_finalWordSpeechFilter = filterSpeechSequence
	filter_speechSequence.register(filterSpeechSequence)
	filter_speechSequence.moveToEnd(filterSpeechSequence, last=False)
	log.info("Greek Math Reader: final Word speech filter installed")
	return True


def _removeFinalWordSpeechFilter():
	"""Unregister the add-on's final speech filter."""
	global _finalSpeechFilterExtension, _finalWordSpeechFilter
	if _finalSpeechFilterExtension is not None and _finalWordSpeechFilter is not None:
		_finalSpeechFilterExtension.unregister(_finalWordSpeechFilter)
	_finalSpeechFilterExtension = None
	_finalWordSpeechFilter = None


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		from .settingsPanel import GreekMathSettingsPanel

		self._settingsPanel = GreekMathSettingsPanel
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(GreekMathSettingsPanel)
		log.info(
			f"Greek Math Reader: startup; version={ADDON_VERSION}; build={BUILD_ID}; "
			f"module={__file__}"
		)
		applyProviderRegistration()
		self._terminating = False
		self._providerWatchdog = None
		self._profileSwitchRegistered = False
		try:
			config.post_configProfileSwitch.register(self._handleConfigProfileSwitch)
			self._profileSwitchRegistered = True
		except AttributeError:
			pass
		# Run after the full global-plugin initialization loop. This reclaims the
		# provider if another installed math add-on registers after this one.
		self._lateRegistration = core.callLater(0, self._registerAfterPluginStartup)

	def _registerAfterPluginStartup(self):
		self._lateRegistration = None
		applyProviderRegistration()
		self._scheduleProviderWatchdog()

	def _scheduleProviderWatchdog(self):
		if not self._terminating and self._providerWatchdog is None:
			self._providerWatchdog = core.callLater(
				_PROVIDER_WATCHDOG_INTERVAL_MS,
				self._checkProviderOwnership,
			)

	def _checkProviderOwnership(self):
		"""Recover from provider changes that occur without a focus event."""
		self._providerWatchdog = None
		if self._terminating:
			return
		applyProviderRegistration()
		self._scheduleProviderWatchdog()

	def _handleConfigProfileSwitch(self, **kwargs):
		"""Prevent a Word-specific profile from restoring the English route."""
		if not self._terminating:
			applyProviderRegistration()

	def terminate(self):
		self._terminating = True
		if self._profileSwitchRegistered:
			try:
				config.post_configProfileSwitch.unregister(self._handleConfigProfileSwitch)
			except (AttributeError, LookupError):
				pass
			self._profileSwitchRegistered = False
		if self._lateRegistration is not None:
			self._lateRegistration.Stop()
			self._lateRegistration = None
		if self._providerWatchdog is not None:
			self._providerWatchdog.Stop()
			self._providerWatchdog = None
		_removeFinalWordSpeechFilter()
		_removeMathPresGuards()
		_removeMathCatSpeechFallback()
		_removeMathTextInfoSpeechHooks()
		_removeMathObjectSpeechHook()
		_unregister()
		_clearWordOmmlCaches()
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(self._settingsPanel)
		except ValueError:
			pass
		super().terminate()

	def event_UIA_notification(
		self,
		obj,
		nextHandler,
		displayString=None,
		activityId=None,
		notificationProcessing=None,
		**kwargs,
	):
		"""Stop Word notification text from bypassing every math provider."""
		global _lastWordNotificationDiagnostic
		try:
			appName = getattr(getattr(obj, "appModule", None), "appName", None)
		except Exception:
			appName = None
		if (
			_exclusiveModeActive
			and appName in ("winword", "outlook")
			and activityId not in ("AccSN1", "AccSN2")
			and _notificationIsFromFocusedApp(obj)
			and _looksLikeWordNativeMathSpeech(displayString)
		):
			mathMl, confirmedMath = _getWordMathContextAtCaret(
				obj,
				allowAdjacentEnd=True,
			)
			_lastWordNotificationDiagnostic = (
				f"app={appName!r}; activityId={activityId!r}; "
				f"displayString={displayString!r}; confirmedMath={confirmedMath}; "
				f"mathMlAvailable={mathMl is not None}"
			)
			if confirmedMath:
				if mathMl is None:
					# Some Office/Windows combinations expose a native OMath but
					# withhold UIA MathML or the Office transform stylesheet.  The
					# independently confirmed notification is still safer than
					# allowing Word's explicitly English linearization through.
					from html import escape

					mathMl = (
						"<math xmlns='http://www.w3.org/1998/Math/MathML'><mtext>"
						+ escape(displayString)
						+ "</mtext></math>"
					)
				import speech

				if _provider is None:
					_register()
				log.info(
					"Greek Math Reader: replaced Word's English math notification; "
					+ _lastWordNotificationDiagnostic
				)
				priority = None
				try:
					import UIAHandler

					if notificationProcessing in (
						UIAHandler.NotificationProcessing_ImportantMostRecent,
						UIAHandler.NotificationProcessing_MostRecent,
					):
						if speech.sayAll.SayAllHandler.isRunning():
							priority = speech.priorities.Spri.NOW
						else:
							speech.cancelSpeech()
				except (ImportError, AttributeError):
					pass
				sequence = _provider.getSpeechForMathMl(mathMl)
				if priority is None:
					speech.speak(sequence)
				else:
					speech.speak(sequence, priority=priority)
				return
		nextHandler()

	def event_gainFocus(self, obj, nextHandler):
		"""Recover if NVDA removed the custom provider during an app switch.

		NVDA's Word app module can intentionally clear all math providers when
		native Word math is selected. Other math add-ons can also replace the
		global slots after this add-on starts. A focus event is the earliest safe
		point after those app-switch hooks to restore Greek math reading.
		"""
		_enforceRequiredNvdaSettings()
		applyProviderRegistration()
		if _redirectStaleMathCatInteraction(obj):
			return
		nextHandler()

	@script(
		# Translators: Describes a diagnostic command that directly speaks a sample equation in Greek.
		description=_("Tests Greek math speech with a sample equation"),
		category=_("Greek Math Reader"),
		gesture="kb:NVDA+alt+shift+g",
	)
	def script_testGreekMath(self, gesture):
		speakSelfTest()

	@script(
		# Translators: Describes the LaTeX reading command in the input gestures dialog.
		description=_("Reads the selected or copied LaTeX math expression in Greek"),
		category=_("Greek Math Reader"),
		gesture="kb:NVDA+alt+l",
	)
	def script_readLatex(self, gesture):
		from scriptHandler import getLastScriptRepeatCount

		self._readLatex(interact=getLastScriptRepeatCount() > 0)

	def _readLatex(self, interact=False):
		import speech

		from .engine import LatexParseError, latex_to_tree, looks_like_latex, speak_latex
		from .provider import getReadingConfig, tokensToSpeechSequence

		source = self._getLatexSource()
		if not source or not source.strip():
			# Translators: Announced when there is no text to read as LaTeX.
			ui.message(_("Select or copy a LaTeX expression first"))
			return
		if not looks_like_latex(source):
			# Translators: Announced when the text does not appear to be LaTeX math.
			ui.message(_("The selected text does not look like LaTeX math"))
			return
		try:
			if interact:
				from .interaction import GreekMathInteraction

				interaction = GreekMathInteraction(provider=_provider, tree=latex_to_tree(source))
				interaction.setFocus()
				return
			tokens = speak_latex(source, getReadingConfig())
		except LatexParseError:
			# Translators: Announced when a LaTeX expression cannot be read.
			ui.message(_("Could not read the LaTeX expression"))
			return
		speech.speak(tokensToSpeechSequence(tokens))

	def _getLatexSource(self):
		"""Return the current selection, or the clipboard text as a fallback."""
		import api
		import textInfos

		try:
			obj = api.getFocusObject()
			treeInterceptor = getattr(obj, "treeInterceptor", None)
			if treeInterceptor is not None and getattr(treeInterceptor, "isReady", False):
				obj = treeInterceptor
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
			selection = info.text
			if selection and selection.strip():
				return selection
		except Exception:
			pass
		try:
			return api.getClipData()
		except Exception:
			return ""

	@script(
		# Translators: Describes the repair command in the input gestures dialog.
		description=_("Repairs exclusive Greek math reading"),
		# Translators: Category of the add-on's commands in the input gestures dialog.
		category=_("Greek Math Reader"),
		gesture="kb:NVDA+alt+g",
	)
	def script_repairGreekMath(self, gesture):
		applyProviderRegistration()
		# Translators: Announced after the exclusive provider is reasserted.
		ui.message(_("Greek Math Reader is active and exclusive"))
