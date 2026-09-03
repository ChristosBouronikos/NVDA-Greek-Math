# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
"""Keep the proposed upstream MathCAT bundle tied to canonical project data."""

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import export_mathcat_el  # noqa: E402


class TestMathCatExport(unittest.TestCase):
	def test_generated_files_are_current(self):
		self.assertEqual(export_mathcat_el.write_outputs(check=True), [])

	def test_export_contains_registry_and_whole_corpus(self):
		registry = json.loads(export_mathcat_el.render_registry())
		corpus = json.loads(export_mathcat_el.render_golden_corpus())
		self.assertEqual(registry["terminologyVersion"], corpus["terminologyVersion"])
		self.assertGreaterEqual(len(registry["entries"]), 30)
		self.assertEqual(
			len(corpus["cases"]),
			len(list((PROJECT_ROOT / "tests" / "corpus").glob("*.mathml"))),
		)
		self.assertTrue(all(case["standardSpeech"].strip() for case in corpus["cases"]))

	def test_export_marks_terms_that_still_need_human_review(self):
		registry = json.loads(export_mathcat_el.render_registry())
		statuses = {entry["reviewStatus"] for entry in registry["entries"]}
		self.assertIn("source-checked-pending-expert-review", statuses)


if __name__ == "__main__":
	unittest.main()
