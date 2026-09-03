# Contributing to Greek Math Reader

Greek Math Reader is primarily a terminology-sensitive NVDA add-on. Small wording changes matter because users hear the result directly.

Maintainer: **Bouronikos Christos** ·
[chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com) ·
[GitHub](https://github.com/ChristosBouronikos). If the add-on helps you, a
[kind, optional PayPal donation](https://paypal.me/christosbouronikos) supports
continued development.

## What to Report

Please open an issue for:

* incorrect Greek mathematical terminology;
* expressions that are spoken ambiguously;
* MathML that fails to parse;
* NVDA interaction problems, especially with `NVDA+Alt+M`;
* compatibility problems with a specific NVDA version.

Include the MathML source when possible, the expected Greek reading, the actual reading, and the NVDA version.

## Terminology Changes

Most Greek wording lives in:

* `addon/globalPlugins/greekMathReader/engine/symbols_el.py`
* `addon/globalPlugins/greekMathReader/engine/grammar_el.py`
* `addon/globalPlugins/greekMathReader/engine/terminology_el.py` for meanings rather than glyphs
* `addon/globalPlugins/greekMathReader/engine/morphology_el.py` for grammatical agreement

When changing terminology, update the review status/source in
`TERMINOLOGY_REVIEW.md` and add an exact-wording test in `tests/test_engine.py`
or `tests/test_semantics.py`. Every semantic concept also needs an ambiguity or
fallback test and profile tests wherever the wording changes.

## Local Checks

Run these before submitting a change:

```sh
python3 -m unittest discover tests -v
python3 preview.py --demo
python3 build.py
python3 tests/validate_package.py greekMathReader-2.1.0-dev.nvda-addon
```

The built `*.nvda-addon` file is a release artifact and is intentionally ignored by Git. Official installation is through the NVDA Add-on Store only.

## Release Policy

Public releases are submitted to the NVDA Add-on Store from a stable GitHub release asset. Do not distribute ad-hoc `.nvda-addon` builds as an installation path; they should only be used for local testing and store submission.

A semantic domain may leave the development channel only after approval from a
relevant Greek domain expert, the Greek-language reviewer, and two blind Greek
NVDA users. Meaning-changing speech, silent content loss, raw English structural
leakage, unreviewed default terminology, or broken core navigation blocks a
stable release. Existing MathCAT braille output is preserved; no Greek
math-braille code may ship without an authoritative specification and the
separate validation process documented in `TERMINOLOGY_REVIEW.md`.

AI-assisted contributions are welcome when they are disclosed and carefully
reviewed. Contributors remain responsible for correctness, licensing, privacy,
and tests. See [AI_DISCLOSURE.md](AI_DISCLOSURE.md) for this project's use of
AI-assisted tools.

## Licensing of Contributions

The project is licensed **GPL-3.0-or-later** with additional author-attribution
terms under section 7 of that license — see [LICENSE.md](LICENSE.md).

By submitting a contribution you agree that it is licensed on those same terms
(inbound equals outbound). Keep the existing header block, including the
attribution notice and the pointer to `LICENSE.md`, in every file you touch, and
add it to new source files:

```python
# SPDX-License-Identifier: GPL-3.0-or-later
# NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)
# Additional attribution terms under GPL-3.0 section 7 apply - see LICENSE.md.
```

You are welcome to add your own copyright line for your changes. Please do not
remove or alter the attribution notice; the section 7(b) term requires it to be
preserved.
