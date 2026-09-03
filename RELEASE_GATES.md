# Semantic release gates

Version 2.1 is a development preview until every applicable row below has
recorded evidence. A blank approval is a blocker, not an implicit pass.

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

Greek mathematical braille is not a 2.1 release target. Production work requires
an authoritative specification, a Greek braille expert, blind-user validation
and at least 200 specification-derived examples.

## MathCAT migration gate

The automatic adapter may use an installed backend that advertises `el`, but a
stable migration requires the shared golden corpus to pass in MathCAT and the
NVDA matrix above to pass with MathCAT interaction. Preserve its braille path.
After two stable NVDA releases ship that verified Greek backend, audit and
retire the add-on's global provider guards and keep only Word-specific routing
that still has a reproduced, tested need.
