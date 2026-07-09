# Contributing to Greek Math Reader

Greek Math Reader is primarily a terminology-sensitive NVDA add-on. Small wording changes matter because users hear the result directly.

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

When changing terminology, add or update an exact-wording test in `tests/test_engine.py`.

## Local Checks

Run these before submitting a change:

```sh
python3 -m unittest discover tests -v
python3 preview.py --demo
python3 build.py
```

The built `*.nvda-addon` file is a release artifact and is intentionally ignored by Git. Official installation is through the NVDA Add-on Store only.

## Release Policy

Public releases are submitted to the NVDA Add-on Store from a stable GitHub release asset. Do not distribute ad-hoc `.nvda-addon` builds as an installation path; they should only be used for local testing and store submission.
