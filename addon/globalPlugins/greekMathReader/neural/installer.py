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

"""Verified download and extraction of speech runtimes and voice models.

Every archive is fetched over HTTPS, checked against the size and SHA-256 pinned
in the catalogue, and only then unpacked. Extraction is done member by member
with the destination path re-checked each time, because these archives contain
native code and are unpacked into the user's configuration directory.

No NVDA imports: the URL opener is injectable so the whole path can be tested
offline.
"""

import hashlib
import os
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

#: Read size that keeps the progress callback responsive without thrashing.
_CHUNK = 256 * 1024

#: Refuse plaintext transports outright rather than trusting a redirect.
_ALLOWED_SCHEMES = ("https://",)


class InstallError(Exception):
	"""A download failed verification or could not be unpacked."""


def _defaultOpener(url, timeout=120):
	return urllib.request.urlopen(url, timeout=timeout)


def downloadVerified(download, destination, opener=None, progress=None):
	"""Fetch ``download`` to ``destination``, verifying size and digest.

	``progress`` is called with (bytesSoFar, totalBytes) and may return ``False``
	to abort. The partial file is removed on any failure, so a cancelled or
	corrupt download never leaves something that looks installable behind.
	"""
	if not download.isPinned:
		raise InstallError("refusing to install {0}: no SHA-256 pinned".format(download.filename))
	if not download.url.startswith(_ALLOWED_SCHEMES):
		raise InstallError("refusing to fetch {0} over a non-HTTPS URL".format(download.filename))

	open_ = opener or _defaultOpener
	digest = hashlib.sha256()
	total = 0
	try:
		with open_(download.url) as response, open(destination, "wb") as output:
			while True:
				chunk = response.read(_CHUNK)
				if not chunk:
					break
				total += len(chunk)
				digest.update(chunk)
				output.write(chunk)
				if progress is not None and progress(total, download.size) is False:
					raise InstallError("cancelled")
	except InstallError:
		_discard(destination)
		raise
	except Exception as error:
		_discard(destination)
		raise InstallError("download of {0} failed: {1}".format(download.filename, error))

	if total != download.size:
		_discard(destination)
		raise InstallError(
			"{0} is {1} bytes, expected {2}".format(download.filename, total, download.size)
		)
	actual = digest.hexdigest()
	if actual != download.sha256:
		_discard(destination)
		raise InstallError(
			"{0} failed verification: got {1}, expected {2}".format(
				download.filename, actual, download.sha256
			)
		)
	return destination


def _discard(path):
	try:
		os.remove(path)
	except OSError:
		pass


def _resolvedInside(root, name):
	"""Return the destination for archive member ``name``, or None if unsafe.

	Rejects absolute paths, drive letters and anything that climbs out of the
	destination once resolved.
	"""
	if not name or name.startswith("/") or name.startswith("\\") or ":" in name.split("/")[0]:
		return None
	target = os.path.abspath(os.path.join(root, name))
	prefix = os.path.abspath(root) + os.sep
	if not target.startswith(prefix):
		return None
	return target


def _isWheelSideload(name):
	"""Whether a wheel member belongs to the non-importable ``.data`` tree.

	``sherpa_onnx_core`` ships its DLLs twice: once inside the package and once
	under ``*.data/data/Scripts`` for a real pip install to relocate. Nothing
	imports the second copy, and skipping it saves about 19 MB per architecture.
	"""
	parts = [part.lower() for part in name.split("/")]
	for index, part in enumerate(parts[:-1]):
		if part.endswith(".data") and index + 1 < len(parts):
			return parts[index + 1] in ("data", "scripts")
	return False


def extractZip(archivePath, destination):
	"""Unpack a wheel, skipping anything that escapes ``destination``."""
	try:
		with zipfile.ZipFile(archivePath) as bundle:
			for member in bundle.infolist():
				if member.is_dir() or _isWheelSideload(member.filename):
					continue
				target = _resolvedInside(destination, member.filename)
				if target is None:
					raise InstallError("archive member escapes the destination: " + member.filename)
				os.makedirs(os.path.dirname(target), exist_ok=True)
				with bundle.open(member) as source, open(target, "wb") as output:
					shutil.copyfileobj(source, output)
	except InstallError:
		raise
	except Exception as error:
		raise InstallError("could not unpack {0}: {1}".format(os.path.basename(archivePath), error))


def extractTar(archivePath, destination):
	"""Unpack a model archive, rejecting links and escaping paths.

	Symbolic and hard links are skipped rather than followed: none of the model
	archives need them, and honouring a link would let an archive write outside
	the destination even when its own path looks safe.
	"""
	try:
		with tarfile.open(archivePath, "r:*") as bundle:
			for member in bundle.getmembers():
				if member.islnk() or member.issym():
					continue
				if not (member.isfile() or member.isdir()):
					continue
				target = _resolvedInside(destination, member.name)
				if target is None:
					raise InstallError("archive member escapes the destination: " + member.name)
				if member.isdir():
					os.makedirs(target, exist_ok=True)
					continue
				os.makedirs(os.path.dirname(target), exist_ok=True)
				source = bundle.extractfile(member)
				if source is None:
					continue
				with source, open(target, "wb") as output:
					shutil.copyfileobj(source, output)
	except InstallError:
		raise
	except Exception as error:
		raise InstallError("could not unpack {0}: {1}".format(os.path.basename(archivePath), error))


def installArchives(downloads, destination, extractor, opener=None, progress=None):
	"""Download and unpack ``downloads`` into ``destination`` atomically.

	Work happens in a sibling temporary directory that is swapped into place only
	once every archive has been verified and unpacked, so an interrupted install
	cannot leave a half-populated voice behind.
	"""
	parent = os.path.dirname(os.path.abspath(destination))
	os.makedirs(parent, exist_ok=True)
	staging = tempfile.mkdtemp(prefix=".partial-", dir=parent)
	try:
		with tempfile.TemporaryDirectory(prefix=".download-", dir=parent) as scratch:
			for download in downloads:
				archive = os.path.join(scratch, download.filename)
				downloadVerified(download, archive, opener=opener, progress=progress)
				extractor(archive, staging)
		if os.path.exists(destination):
			shutil.rmtree(destination, ignore_errors=True)
		os.rename(staging, destination)
	except Exception:
		shutil.rmtree(staging, ignore_errors=True)
		raise
	return destination
