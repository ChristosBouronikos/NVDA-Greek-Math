# -*- coding: utf-8 -*-
# Greek Math Reader for NVDA
# Copyright (C) 2026 Christos Bouronikos
# This file is covered by the GNU General Public License version 3 or later.
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
"""Optional neural speech: catalogue, verified install, layout and conversion."""

import io
import os
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "addon" / "globalPlugins" / "greekMathReader"))

from neural import catalogue, installer, layout, paths, platforms, synthesis  # noqa: E402


def fakeOpener(payload):
	"""Return an opener yielding ``payload``, usable as a context manager."""

	def opener(url, timeout=120):
		return io.BytesIO(payload)

	return opener


class TestPlatformSelection(unittest.TestCase):
	def test_python_tag_follows_the_running_interpreter(self):
		self.assertEqual(platforms.pythonTag((3, 11, 9)), "cp311")
		self.assertEqual(platforms.pythonTag((3, 13, 1)), "cp313")

	def test_setuptools_platform_names_are_normalised_to_wheel_tags(self):
		self.assertEqual(platforms.platformTag("win-amd64"), "win_amd64")
		self.assertEqual(platforms.platformTag("win-arm64"), "win_arm64")
		self.assertEqual(platforms.platformTag("win32"), "win32")

	def test_platform_key_combines_interpreter_and_architecture(self):
		self.assertEqual(platforms.platformKey((3, 11, 0), "win32"), "cp311-win32")
		self.assertEqual(platforms.platformKey((3, 13, 0), "win-amd64"), "cp313-win_amd64")

	def test_non_windows_platforms_are_reported_unsupported(self):
		self.assertFalse(platforms.isSupportedPlatform("macosx-15.0-arm64"))


class TestCatalogue(unittest.TestCase):
	def setUp(self):
		self.catalogue = catalogue.loadCatalogue()

	def test_every_download_is_digest_pinned(self):
		# An unpinned entry would be installed without verification, so this is
		# a release gate rather than a nicety.
		self.assertTrue(self.catalogue.validate())

	def test_greek_voices_are_offered_with_the_recommended_one_first(self):
		greek = self.catalogue.voicesForLanguage("el")
		self.assertTrue(greek)
		self.assertTrue(greek[0].recommended)

	def test_kokoro_is_not_offered_for_greek_because_it_cannot_speak_it(self):
		greekIds = {voice.id for voice in self.catalogue.voicesForLanguage("el")}
		self.assertNotIn("kokoro-multi-int8", greekIds)

	def test_locale_variants_still_match_a_language(self):
		voice = self.catalogue.voice("piper-el-int8")
		self.assertTrue(voice.speaks("el_GR"))
		self.assertTrue(voice.speaks("el-GR"))
		self.assertFalse(voice.speaks("en_US"))

	def test_restrictively_licensed_weights_are_flagged_for_acceptance(self):
		# Supertonic's OpenRAIL-M terms bind downstream recipients, so the
		# add-on may not ship it silently.
		self.assertTrue(self.catalogue.voice("supertonic-3").requiresLicenseAcceptance)
		self.assertFalse(self.catalogue.voice("piper-el-int8").requiresLicenseAcceptance)

	def test_runtime_resolves_for_both_supported_nvda_generations(self):
		# NVDA 2024.1-2025.x is 32-bit CPython 3.11; 2026.1 is 64-bit CPython 3.13.
		for versionInfo, platformName in (((3, 11, 0), "win32"), ((3, 13, 0), "win-amd64")):
			downloads = self.catalogue.runtimeDownloads(versionInfo, platformName)
			self.assertEqual(len(downloads), 2, msg=str(platformName))
			self.assertTrue(all(download.isPinned for download in downloads))

	def test_unknown_interpreter_yields_no_runtime_rather_than_a_wrong_one(self):
		self.assertEqual(self.catalogue.runtimeDownloads((3, 99, 0), "win32"), [])

	def test_missing_catalogue_raises_a_catalogue_error(self):
		with self.assertRaises(catalogue.CatalogueError):
			catalogue.loadCatalogue("/nonexistent/catalogue.json")


class TestVerifiedDownload(unittest.TestCase):
	def setUp(self):
		self.payload = b"greek math reader payload"
		self.directory = tempfile.mkdtemp()
		self.destination = os.path.join(self.directory, "payload.bin")

	def _download(self, sha256=None, size=None, url="https://example.invalid/a.bin"):
		import hashlib

		return catalogue.Download(
			"a.bin",
			url,
			len(self.payload) if size is None else size,
			hashlib.sha256(self.payload).hexdigest() if sha256 is None else sha256,
		)

	def test_a_matching_download_is_written_out(self):
		installer.downloadVerified(
			self._download(), self.destination, opener=fakeOpener(self.payload)
		)
		with open(self.destination, "rb") as handle:
			self.assertEqual(handle.read(), self.payload)

	def test_a_wrong_digest_is_rejected_and_the_partial_file_removed(self):
		with self.assertRaises(installer.InstallError):
			installer.downloadVerified(
				self._download(sha256="0" * 64), self.destination, opener=fakeOpener(self.payload)
			)
		self.assertFalse(os.path.exists(self.destination))

	def test_a_wrong_size_is_rejected(self):
		with self.assertRaises(installer.InstallError):
			installer.downloadVerified(
				self._download(size=999), self.destination, opener=fakeOpener(self.payload)
			)

	def test_an_unpinned_entry_is_refused_before_any_request_is_made(self):
		def explode(url, timeout=120):
			raise AssertionError("no request should be attempted for an unpinned entry")

		with self.assertRaises(installer.InstallError):
			installer.downloadVerified(self._download(sha256=""), self.destination, opener=explode)

	def test_plaintext_urls_are_refused(self):
		with self.assertRaises(installer.InstallError):
			installer.downloadVerified(
				self._download(url="http://example.invalid/a.bin"),
				self.destination,
				opener=fakeOpener(self.payload),
			)

	def test_progress_can_abort_a_download(self):
		with self.assertRaises(installer.InstallError):
			installer.downloadVerified(
				self._download(),
				self.destination,
				opener=fakeOpener(self.payload),
				progress=lambda done, total: False,
			)
		self.assertFalse(os.path.exists(self.destination))


class TestArchiveExtraction(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp()

	def _zip(self, members):
		path = os.path.join(self.directory, "bundle.whl")
		with zipfile.ZipFile(path, "w") as bundle:
			for name, data in members:
				bundle.writestr(name, data)
		return path

	def _tar(self, names):
		path = os.path.join(self.directory, "bundle.tar.bz2")
		with tarfile.open(path, "w:bz2") as bundle:
			for name in names:
				info = tarfile.TarInfo(name)
				info.size = 4
				bundle.addfile(info, io.BytesIO(b"data"))
		return path

	def test_a_wheel_unpacks_its_package_files(self):
		archive = self._zip([("sherpa_onnx/__init__.py", "x = 1"), ("sherpa_onnx/lib/a.dll", "bin")])
		destination = os.path.join(self.directory, "out")
		installer.extractZip(archive, destination)
		self.assertTrue(os.path.isfile(os.path.join(destination, "sherpa_onnx", "lib", "a.dll")))

	def test_the_duplicated_wheel_data_tree_is_skipped(self):
		# sherpa_onnx_core ships its DLLs twice; the second copy is 19 MB of
		# files nothing imports.
		archive = self._zip(
			[
				("sherpa_onnx/lib/a.dll", "bin"),
				("sherpa_onnx_core-1.13.7.data/data/Scripts/a.dll", "bin"),
			]
		)
		destination = os.path.join(self.directory, "out")
		installer.extractZip(archive, destination)
		self.assertTrue(os.path.isfile(os.path.join(destination, "sherpa_onnx", "lib", "a.dll")))
		self.assertFalse(os.path.exists(os.path.join(destination, "sherpa_onnx_core-1.13.7.data")))

	def test_a_zip_escaping_its_destination_is_refused(self):
		archive = self._zip([("../escaped.txt", "nope")])
		with self.assertRaises(installer.InstallError):
			installer.extractZip(archive, os.path.join(self.directory, "out"))

	def test_a_tar_escaping_its_destination_is_refused(self):
		archive = self._tar(["../escaped.txt"])
		with self.assertRaises(installer.InstallError):
			installer.extractTar(archive, os.path.join(self.directory, "out"))

	def test_an_absolute_tar_member_is_refused(self):
		archive = self._tar(["/etc/passwd"])
		with self.assertRaises(installer.InstallError):
			installer.extractTar(archive, os.path.join(self.directory, "out"))

	def test_a_failed_install_leaves_no_destination_behind(self):
		download = catalogue.Download("a.bin", "https://example.invalid/a.bin", 5, "0" * 64)
		destination = os.path.join(self.directory, "voice")
		with self.assertRaises(installer.InstallError):
			installer.installArchives(
				[download], destination, installer.extractTar, opener=fakeOpener(b"hello")
			)
		self.assertFalse(os.path.exists(destination))


class TestInstallationMarkers(unittest.TestCase):
	def setUp(self):
		self.configPath = tempfile.mkdtemp()

	def test_a_directory_counts_as_installed_only_once_marked(self):
		directory = paths.voiceDir(self.configPath, "piper-el-int8")
		os.makedirs(directory)
		self.assertFalse(paths.isComplete(directory))
		self.assertEqual(paths.installedVoiceIds(self.configPath), [])
		paths.markComplete(directory)
		self.assertTrue(paths.isComplete(directory))
		self.assertEqual(paths.installedVoiceIds(self.configPath), ["piper-el-int8"])

	def test_runtimes_for_different_architectures_do_not_collide(self):
		# One configuration directory can be shared by a 32-bit and a 64-bit NVDA.
		self.assertNotEqual(
			paths.runtimeDir(self.configPath, "cp311-win32"),
			paths.runtimeDir(self.configPath, "cp313-win_amd64"),
		)


class TestVoiceLayout(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp()

	def _build(self, names, nested="model-2026-01-01"):
		root = os.path.join(self.directory, nested) if nested else self.directory
		os.makedirs(root, exist_ok=True)
		for name in names:
			path = os.path.join(root, name)
			if name.endswith("/"):
				os.makedirs(path, exist_ok=True)
				continue
			with open(path, "w", encoding="utf-8") as handle:
				handle.write("x")
		return self.directory

	def test_the_single_nested_archive_directory_is_entered(self):
		self._build(["el_GR-rapunzelina-low.onnx", "tokens.txt", "espeak-ng-data/"])
		found = layout.describe("vits", self.directory)
		self.assertTrue(found["model"].endswith(".onnx"))
		self.assertTrue(found["data_dir"].endswith("espeak-ng-data"))

	def test_a_vits_voice_without_tokens_is_reported_rather_than_half_loaded(self):
		self._build(["model.onnx"])
		with self.assertRaises(layout.LayoutError):
			layout.describe("vits", self.directory)

	def test_supertonic_matches_both_quantised_and_float_graph_names(self):
		self._build(
			[
				"duration_predictor.int8.onnx",
				"text_encoder.int8.onnx",
				"vector_estimator.int8.onnx",
				"vocoder.int8.onnx",
				"tts.json",
				"unicode_indexer.bin",
				"voice.bin",
			]
		)
		found = layout.describe("supertonic", self.directory)
		self.assertTrue(found["vocoder"].endswith("vocoder.int8.onnx"))
		self.assertTrue(found["voice_style"].endswith("voice.bin"))

	def test_kokoro_needs_its_voice_bank(self):
		self._build(["model.onnx", "tokens.txt"])
		with self.assertRaises(layout.LayoutError):
			layout.describe("kokoro", self.directory)

	def test_an_unknown_family_is_rejected(self):
		self._build(["model.onnx"])
		with self.assertRaises(layout.LayoutError):
			layout.describe("nonsense", self.directory)


class FakeGeneratedAudio:
	def __init__(self, samples, sampleRate):
		self.samples = samples
		self.sample_rate = sampleRate


class FakeGenerationConfig:
	def __init__(self):
		self.sid = 0
		self.speed = 1.0
		self.extra = {}


class FakeSherpa:
	"""Enough of the sherpa-onnx surface to exercise configuration and output."""

	GenerationConfig = FakeGenerationConfig

	def __init__(self, samples=(0.0, 0.5, -0.5, 1.0), sampleRate=22050):
		self.samples = list(samples)
		self.sampleRate = sampleRate
		self.lastConfig = None
		self.lastGeneration = None

	def OfflineTtsVitsModelConfig(self, **kwargs):
		return ("vits", kwargs)

	def OfflineTtsKokoroModelConfig(self, **kwargs):
		return ("kokoro", kwargs)

	def OfflineTtsSupertonicModelConfig(self, **kwargs):
		return ("supertonic", kwargs)

	def OfflineTtsModelConfig(self, **kwargs):
		return kwargs

	def OfflineTtsConfig(self, **kwargs):
		self.lastConfig = kwargs
		return kwargs

	def OfflineTts(self, config):
		outer = self

		class Tts:
			sample_rate = outer.sampleRate

			def generate(self, text, generation=None, **kwargs):
				outer.lastGeneration = generation
				return FakeGeneratedAudio(outer.samples, outer.sampleRate)

		return Tts()


class TestAudioConversion(unittest.TestCase):
	def test_float_samples_become_signed_16_bit_little_endian(self):
		data = synthesis._toPcm16([0.0, 1.0, -1.0])
		self.assertEqual(len(data), 6)
		self.assertEqual(data[0:2], b"\x00\x00")
		self.assertEqual(data[2:4], b"\xff\x7f")

	def test_samples_beyond_full_scale_are_clipped_rather_than_wrapped(self):
		# A wrapped sample is heard as a loud click, so this must saturate.
		data = synthesis._toPcm16([4.0, -4.0])
		self.assertEqual(data[0:2], b"\xff\x7f")
		self.assertEqual(data[2:4], b"\x01\x80")

	def test_volume_scales_the_output(self):
		loud = synthesis._toPcm16([1.0], volume=1.0)
		quiet = synthesis._toPcm16([1.0], volume=0.5)
		self.assertGreater(
			int.from_bytes(loud, "little", signed=True), int.from_bytes(quiet, "little", signed=True)
		)


class TestSpeechEngine(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp()
		root = os.path.join(self.directory, "vits-piper-el_GR-rapunzelina-low-int8")
		os.makedirs(os.path.join(root, "espeak-ng-data"))
		for name in ("el_GR-rapunzelina-low.onnx", "tokens.txt"):
			with open(os.path.join(root, name), "w", encoding="utf-8") as handle:
				handle.write("x")

	def _engine(self, sherpa, family="vits"):
		return synthesis.SpeechEngine("/runtime", self.directory, family, sherpa=sherpa)

	def test_a_vits_voice_is_configured_from_the_downloaded_files(self):
		sherpa = FakeSherpa()
		self._engine(sherpa).load()
		model = sherpa.lastConfig["model"]
		self.assertIn("vits", model)
		self.assertEqual(model["provider"], "cpu")

	def test_one_sentence_per_call_keeps_the_first_word_prompt(self):
		sherpa = FakeSherpa()
		self._engine(sherpa).load()
		self.assertEqual(sherpa.lastConfig["max_num_sentences"], 1)

	def test_synthesis_returns_pcm_bytes(self):
		speech = self._engine(FakeSherpa())
		audio = speech.synthesize("ένα συν δύο")
		self.assertIsInstance(audio, bytes)
		self.assertEqual(len(audio), 8)
		self.assertEqual(speech.sampleRate, 22050)

	def test_blank_text_is_not_sent_to_the_model(self):
		self.assertEqual(self._engine(FakeSherpa()).synthesize("   "), b"")

	def test_the_language_is_passed_through_for_multilingual_models(self):
		sherpa = FakeSherpa()
		speech = self._engine(sherpa)
		speech.synthesize("ένα", language="el")
		self.assertEqual(sherpa.lastGeneration.extra["lang"], "el")

	def test_speed_reaches_the_generation_config(self):
		sherpa = FakeSherpa()
		self._engine(sherpa).synthesize("ένα", speed=1.75)
		self.assertAlmostEqual(sherpa.lastGeneration.speed, 1.75)

	def test_an_unsupported_family_is_rejected(self):
		with self.assertRaises(synthesis.EngineError):
			self._engine(FakeSherpa(), family="nonsense").load()

	def test_a_missing_runtime_directory_is_reported_clearly(self):
		with self.assertRaises(synthesis.EngineError):
			synthesis.importSherpaOnnx("/definitely/not/here")


if __name__ == "__main__":
	unittest.main()
