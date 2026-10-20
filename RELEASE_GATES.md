# Semantic release gates

These gates record the evidence still required for reviewed semantic and voice
quality. A blank approval is not an implicit pass.

## Status of 2.6.1 stable (2026-10-20)

Reviewed the production changes from tag `v2.5.6` through `v2.6.0`. Version
2.6.1 fixes the ambiguous Greek addition/letter-name fallback and normalization
of non-final equation-boundary speech items across MathCAT, MathML and native
Word fallback. Regression tests cover both
failures and retain explicit trigonometric function calls. The provider also
produced and recorded Greek speech with NVDA's actual `AggregatedSection`
class extracted from source; the historical `dict(section)` failure was
reproduced separately.

Automated validation: 544 tests ran (536 passed, 8 skipped for deferred neural
features), generated MathCAT assets are current, the Greek message catalogue
passes format checks, the demo preview runs, and the built 2.6.1 package passes
Store metadata, structure and ZIP integrity checks.

All 16 prior GitHub releases were downloaded and checked: manifest versions,
SHA256 checksums and packaged tracked files match their tags. Their commits
remain unchanged. Release notes and submission references are corrected
without relabelling old packages as newer versions.

The declared last-tested NVDA version remains 2026.1.1. Manual Windows/NVDA,
Word and PDF listening checks remain pending, including NVDA 2026.2 and
2026.3 beta. Publication does not close the manual gates below.

## Status of 2.6.0 stable (2026-10-19)

Version 2.6.0 fixes final equation-boundary announcements and unstructured Word
math fallback translation for Latin and Greek trigonometric functions,
including limits. Automated tests and package checks pass. The declared last
tested NVDA version remains 2026.1.1; NVDA 2026.2 and 2026.3 beta have not
received manual Windows/NVDA validation, and NVDA 2027.1 is not yet available.

## Status of 2.5.9 stable (2026-10-19)

Version 2.5.9 fixes a configuration snapshot crash introduced in 2.5.0. The reproduction uses NVDA's actual `AggregatedSection`: the provider raised `ValueError` before the fix and returned Greek speech afterward. Provider and Settings tests now use an NVDA-style configuration contract instead of plain dictionaries. This release also automatically selects Word UI Automation **Default (Where suitable)**. Startup corrections persist, but profile changes do not force a save of unrelated temporary preferences. Windows/NVDA audio checks remain pending.

## Status of 2.5.8 stable (2026-10-19)

The maintainer requested publication of version 2.5.8. This maintenance release fixes flat equation operators, silent backend output, and voice compatibility diagnostics. Automated tests and package checks pass. Windows audio checks, Word integration checks, and semantic terminology approvals remain pending. Publication does not establish successful audio with every synthesizer.

## Status of 2.5.7 stable (2026-10-19)

**Version 2.5.7 is being released on the stable channel to apply the required NVDA settings automatically on first install and after every update, so new users hear equations without pressing Repair.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology remain pending as documented below.

## Status of 2.5.6 stable (2026-09-11)

**Version 2.5.6 is being released on the stable channel to scratch and defer experimental neural voices from active settings and synthesizer options, cleanly removing relative controls from the settings panel while preserving the codebase for future releases.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology remain pending as documented below.

## Status of 2.5.5 stable (2026-09-11)

**Version 2.5.5 is being released on the stable channel to add a direct download button for additional Greek voice options in Windows OneCore via Windows Speech Settings.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology and optional neural voices remain pending as documented below.

## Status of 2.5.4 stable (2026-09-11)

**Version 2.5.4 is being released on the stable channel to organize the settings panel into clean categories and provide a direct download button for Nuance Vocalizer Expressive.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology and optional neural voices remain pending as documented below.

## Status of 2.5.3 stable (2026-09-11)

**Version 2.5.3 is being released on the stable channel to fix neural voice audio playback, resolve the settings dialog hang on OK, and rename the synthesizer.** Automated engine, packaging and lifecycle checks pass. Manual review gates for semantic terminology and optional neural voices remain pending as documented below.

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

Manual audio checks remain **Pending** for each voice route:

* Windows OneCore with Microsoft Stefanos or another Greek OneCore voice.
* eSpeak NG with its Greek voice.
* Microsoft SAPI5 with an installed Greek 64-bit voice on NVDA 2026.1 or later.
* Microsoft SAPI5 32-bit through NVDA's bridge with an installed Greek 32-bit voice.
* The native 32-bit SAPI5 route on supported older NVDA releases. Before NVDA 2025.1, select Greek directly.

For each route, check direct Greek selection and supported automatic language switching. Check absent Greek voices, empty backend output, speech-off mode, muted volume, and invalid output devices separately.

Include single Latin and Greek letters, pauses, rates, nested expressions, long expressions, singular/plural units and unknown-symbol fallback. Record successful audio separately from advertised voice support or generated speech text.

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
