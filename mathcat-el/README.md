# MathCAT Greek contribution bundle

This directory is an upstream-oriented, generated bridge between Greek Math
Reader and MathCAT. It does not replace MathCAT's complete language rules.

MathCAT's upstream repository now contains an early `el` language pack. The
pack was audited at commit `5bafcd80f2833017856b6d87b5897175315ccc95`
(2026-07-31). It already covers substantial structural speech and SI units, but
its source still contains terminology review notes and untranslated navigation
words. Capability detection alone therefore does not establish semantic parity.

The files in `generated/` provide:

* `semantic-intents.yaml`: MathCAT-format candidates for every canonical
  semantic concept in the add-on registry;
* `terminology-registry.json`: all profile forms, morphology metadata, sources,
  pronunciation overrides and review states; and
* `golden-corpus.json`: the shared real-world MathML corpus with exact Standard
  Greek readings and diagnostics.

Regenerate and verify them with:

```sh
python3 tools/export_mathcat_el.py
python3 tools/export_mathcat_el.py --check
```

An upstream contribution should merge reviewed entries into
`Rules/Languages/el/definitions.yaml`, translate `NavigationParts` (`in` and
`out` are currently English upstream), and convert the JSON cases to MathCAT's
Rust test helper. It must then pass both MathCAT's existing `el` suite and this
project's parity corpus. Entries labelled
`source-checked-pending-expert-review` are preview material and must not be
represented as approved terminology.

Greek Math Reader preserves MathCAT's existing braille output. This bundle adds
no Greek mathematical-braille code; that remains a separate research and
validation track.
