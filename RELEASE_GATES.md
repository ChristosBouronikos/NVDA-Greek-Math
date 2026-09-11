# Semantic release gates

These gates record the evidence still required for reviewed semantic and voice
quality. A blank approval is not an implicit pass.

## Status of 2.5.2 stable (2026-09-11)

**Version 2.5.2 is being released on the stable channel to fix activation and discovery of the optional neural voice synthesizer in NVDA's synthesizer list.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology and optional neural voices remain pending as documented below.

## Status of 2.5.1 stable (2026-09-11)

**Version 2.5.1 is being released on the stable channel to fix modal lifecycle in the Neural voices dialog.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology and optional neural voices remain pending as documented below.

## Status of 2.5.0 stable (2026-09-11)

**Version 2.5.0 is being released on the stable channel by the maintainer's
explicit decision while the manual rows below remain Pending.** Automated
engine, packaging and catalogue checks pass. The optional neural synthesizer is
off by default, but its real Windows/NVDA installation, latency, interruption,
character echo, high-rate intelligibility and voice quality still require
manual testing. The README and settings identify it as optional and
experimental; no neural runtime or model is bundled in the add-on package.

## Status of 2.1.0 stable (2026-09-03)

**Version 2.1.0 shipped on the stable channel on 2026-09-03 with the NVDA and
document matrix and the human-approval rows below still marked Pending.** This
was the maintainer's explicit decision, made after this gap was raised
directly. It is recorded here rather than left unstated, and the Pending rows
below are left as Pending rather than backfilled, because no review or
listening test has actually occurred for them.

Several reading changes landed in 2.1.0 on release day itself — the explicit
fraction reading inside a trigonometric argument, the pause between
juxtaposed single-letter factors, and the Leibniz-derivative fixes — and have
not been heard by anyone outside this development session. A test sheet with
19 verified equations was sent to a native blind NVDA user for informal
feedback; as of this release, no response had been received yet. Closing the
rows below, and revisiting the two open wording questions the test sheet
raises (whether "του" is needed after an unparenthesized function name, and
whether the explicit fraction reading is worth its length), is the immediate
follow-up work for 2.1.x.

## Automated gates

| Gate | Required result | Evidence |
|---|---|---|
| Existing and new unit tests | All pass | `python3 -m unittest discover tests -q` |
| Generated MathCAT assets | Current | `python3 tools/export_mathcat_el.py --check` |
| Greek message catalog | No format/catalog errors | `msgfmt --check --check-format` |
| Add-on package | Manifest and contents valid | `tests/validate_package.py` |
| No silent loss | Every corpus/malformed case has non-empty literal or semantic speech | Robustness tests |
| Cross-format parity | Equivalent semantic cases agree across MathML, LaTeX and UnicodeMath | Parity tests |

## NVDA and document matrix

Record the exact version, synthesizer, tester and result for every cell. Test
the minimum supported NVDA release and the current stable release.

| Surface | Minimum NVDA | Current NVDA | Required checks |
|---|---|---|---|
| Firefox / MathJax | Pending | Pending | browse, focus, semantic navigation, copy |
| Chromium / MathJax | Pending | Pending | browse, focus, semantic navigation, copy |
| Word UIA MathML | Pending | Pending | read, navigate, Greek voice routing |
| Word OMath/OMML fallback | Pending | Pending | conversion, guarded fallback, no English leakage |
| EPUB | Pending | Pending | browse and navigation |
| Tagged PDF | Pending | Pending | browse and navigation |
| Neural voice download and selection | Pending | Pending | runtime/model verification, restart, speech and removal |
| Neural voice daily use | Pending | Pending | latency, interruption, character echo and high-rate intelligibility |

Manual listening is required with Microsoft Stefanos and eSpeak Greek. Include
single Latin and Greek letters, pauses, rates, nested expressions, long
expressions, singular/plural units and unknown-symbol fallback.

## Human approval per stable domain

| Domain/module | Greek domain expert | Greek-language reviewer | Blind NVDA user 1 | Blind NVDA user 2 |
|---|---|---|---|---|
| Foundation and school mathematics | Pending | Pending | Pending | Pending |
| University core mathematics | Pending | Pending | Pending | Pending |
| Physics | Pending | Pending | Pending | Pending |
| Each specialist module | Pending | Pending | Pending | Pending |

Meaning-changing readings, unreviewed default terminology, silent loss, raw
English structural leakage, or failure of core navigation block a stable
release. Preview diagnostics are voluntary and telemetry remains disabled.

Greek mathematical braille is not a 2.5 release target. Production work requires
an authoritative specification, a Greek braille expert, blind-user validation
and at least 200 specification-derived examples.

## MathCAT migration gate

The automatic adapter may use an installed backend that advertises `el`, but a
stable migration requires the shared golden corpus to pass in MathCAT and the
NVDA matrix above to pass with MathCAT interaction. Preserve its braille path.
After two stable NVDA releases ship that verified Greek backend, audit and
retire the add-on's global provider guards and keep only Word-specific routing
that still has a reproduced, tested need.
