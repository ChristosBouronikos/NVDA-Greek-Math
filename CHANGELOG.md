# Changelog

## 2.0.0 — 2026-07-13

First major release. Greek Math Reader now reads mathematics reliably across the web, EPUB, and Microsoft Word, and can read LaTeX on demand.

**Highlights since 1.0.0**

* **Microsoft Word equations** are read in Greek: structured MathML through UI Automation where Word exposes it, a read-only native OMath transform (Office's own OMML2MML stylesheet) where it does not, and a backup translation of Word's English math speech when no equation can be confirmed.
* **Greek LaTeX reading** with **NVDA+Alt+L** (double-press to explore interactively): fractions, roots, scripts, big operators with bounds, matrices, accents, Greek letters and named functions.
* **Expanded vocabulary** for school and university mathematics: geometry, statistics and probability, linear algebra, complex analysis, partial derivatives and multiple integrals, plus SI physics units.
* **Clearer speech of short Greek letter names** (ψι, χι, φι …): the synthesizer now reads them as single words instead of spelling them out, while the copied reading stays orthographically clean.
* **Greek equation-boundary announcements**: "end of equation" / "end of section" are spoken as «τέλος εξίσωσης».
* Robust MathML parsing (namespace prefixes, semantic annotations, `maction`, deprecated `mfenced`) and extensive provider-recovery, self-repair and diagnostics for NVDA 2024.1 through 2026.1.1.

## 1.1.8 — 2026-07-13

* Fixes characters right next to an equation being spoken as the whole equation (for example «χ» or «x» after an equation sounding like equation content such as ordinals): Word reports an equation in its `Selection.OMaths` collection even when the caret only touches the equation's end, so strict caret containment is now enforced for character and word navigation. End-adjacency remains available only to the notification and final-speech paths that need it.
* Makes selections that span an equation (mouse or keyboard) translate reliably: a confirmed equation is no longer discarded just because the selection also contains ordinary prose — the strict prose classifier now applies only to unconfirmed backup translations. The final filter also never rewrites utterances shorter than three characters, protecting typing echo.
* The prose classifier additionally recognizes NVDA's Greek and English selection announcements («επιλέχθηκε», "selected" and variants) so they don't disqualify backup translations.

## 1.1.7 — 2026-07-13

* Adds **backup mode** (on by default, toggleable in the settings panel): when Word or Outlook speech clearly reads as English mathematics but no native OMath or UIA math field can confirm an equation — COM unreachable, protected view, the Outlook reading pane — the English is translated to Greek anyway instead of being left unreadable. Every rewrite still passes the strict math-text classifier, and diagnostics record whether a replacement was confirmed or backup.
* The diagnostics report now shows whether backup mode is enabled.

## 1.1.6 — 2026-07-13

* Whole Word equation lines are now spoken through the real Greek engine: when the final speech filter confirms the caret's native OMath and the utterance is entirely mathematical, the equation is transformed with Office's OMML2MML stylesheet and parsed structurally, instead of translating Word's English sentence word by word.
* Recognizes all Greek letter names (alpha…omega) plus degrees, percent, infinity, prime, vector, sum and product in Word's English math stream, both for detection and for the unstructured mtext fallback — fixes lines like «a squared plus beta squared» being left in English because their tokens looked like prose.
* Copy diagnostics now reports the Word application version and build, and states outright whether that build can expose MathML through UI Automation (requires build 14326+); when it cannot, equation reading depends entirely on the native OMath fallback.

## 1.1.5 — 2026-07-13

* Closes the whole-line and cached-speech hole exposed by real Word diagnostics: an official NVDA final-speech filter now catches Word's English linear equation stream from current-line, Say All, typing, selection and other retained speech callables, while preserving callbacks and every non-text speech command.
* Requires live UIA math or native Word OMath confirmation before the final filter changes any text, and records filter ownership, candidates and replacements in Copy diagnostics.
* Resolves Word document and COM context through UIA roots, browse-mode proxies and the focused document, including a read-only adjacent-equation probe for Word's collapsed end-of-equation caret.

## 1.1.4 — 2026-07-13

* Fixes the confirmed Word caret-routing defect behind mixed output such as «χί squared plus ένα»: NVDA deliberately retained Word's English linear equation text for character/word navigation and skipped the registered math provider because the equation was an enclosing text field rather than the focused object.
* Hooks Word/Outlook TextInfo speech for character and word units, silently preserves NVDA's control-field cache, and emits only the Greek provider's rendering of the enclosing MathML.
* Routes NVDA's internal TextInfo math appender directly to Greek Math Reader and intercepts Word UIA math notifications that otherwise call `ui.message` with English text outside the math-provider framework.
* Adds a read-only native Word OMath fallback for character/word caret navigation and equation notifications when the UIA custom MathML property is unavailable: the add-on reads `OMath.Range.WordOpenXML`, transforms OMML with Office's installed `OMML2MML.XSL`, and never changes the selection, clipboard, equation representation, document, or Undo history.
* Reapplies required settings immediately after NVDA configuration-profile switches and invalidates a stale Word UIA-window decision when the setting changes.
* Translates explicit English structural vocabulary found inside fallback `<mtext>` MathML, preventing prewritten strings such as `χ squared plus 1` from leaking English words into Greek speech.
* Extends copyable diagnostics with the Word TextInfo route, notification route, Windows/Office information, and each OMath fallback stage.

## 1.1.3 - 2026-07-13

* Corrects the NVDA 2026.1.1 guidance: **Math → Language** has no Automatic choice and normally defaults to English; that MathCAT setting is bypassed by this add-on.
* Forces **Advanced → UI Automation → Microsoft Word** to **Always**, because modern Word equations expose MathML through UIA while the legacy Word path generally does not.
* Forces `Role.MATH` objects with real MathML directly through the Greek provider, suppressing an English accessible name that could otherwise win NVDA's generic-text route.
* Replaces an already-focused/stale MathCAT interaction navigator with the Greek interaction tree, closing MathCAT's separate direct-English navigation path.
* Makes the provider guards, MathCAT fallback, and math-object route self-repairing if another component overwrites a hook after startup.
* Adds a uniquely logged build identifier and a **Copy diagnostics** button reporting the installed module, active provider, equation exposure, Word route, and OneCore Greek voices.
* Logs whether received input is structural MathML or prewritten `<mtext>`/alt text; English alt text cannot be converted into a structured equation after the source application has discarded the math structure.

## 1.1.2 - 2026-07-13

* Makes Greek Math Reader the exclusive speech and interaction provider while installed. Later speech/interaction registrations are blocked; built-in braille support remains available.
* Guards NVDA's math-provider registration, initialization, and termination paths, while retaining focus recovery, the MathCAT speech delegate, and a 500 ms ownership watchdog.
* Enforces automatic language switching, Greek language tagging, and disabled native Word/Outlook math so those settings cannot silently restore English math speech.
* Replaces the on/off control with a **Reset settings and repair Greek math** button. Reset restores smart verbosity, decimal comma, the required NVDA settings, and every exclusive routing layer.
* Documents the recommended NVDA Speech, Audio, and Math settings.

## 1.1.1 - 2026-07-13

* Keeps ownership of NVDA's math speech provider with a lightweight watchdog, covering late provider resets that do not produce a focus event.
* Adds a narrowly scoped fallback that redirects built-in MathCAT speech requests to the Greek engine while the add-on is enabled, and restores MathCAT's original method when the add-on unloads.
* Clarifies in the settings panel and documentation that NVDA's **Math → Language** list belongs only to MathCAT. Greek is not expected in that list because this add-on replaces MathCAT's speech path.

## 1.1.0 - 2026-07-13

* Fixes the reported English/mixed-language output path on NVDA 2026.1.1: the provider is reclaimed after application switches, Word native math is diagnosed, math is tagged explicitly as `el_GR`, and the self-test now reports both disabled automatic language switching and a synthesizer with no installed Greek voice.
* Adds Greek LaTeX reading with **NVDA+Alt+L** from the current selection or clipboard. Press twice to explore the parsed expression interactively. The parser covers fractions, roots, scripts, big operators, functions, Greek letters, relations, accents, binomial coefficients, and matrices, while unknown commands degrade safely.
* Expands school, university, statistics, and physics readings: named angles and arcs, conditional probability and expected value, mean/conjugate bars, matrix inverse, trace/rank, complex modulus, mixed partial derivatives, extrema, SI units and unit ratios, Δ-change notation, and scientific notation.
* Accepts unbound `mml:` tag prefixes, presentation MathML inside `annotation-xml`, semantic annotations, invisible wrappers, `maction`, and namespace-heavy MathML. Adds representative MathJax, Word UIA, and MathType corpus smoke tests.
* Updates the English and Greek documentation, store metadata, and localization for version 1.1.0.

## 1.0.5 - 2026-07-13

* Fixes Word equations not being read in Greek. NVDA's **"Use native math support in Word and Outlook"** option (Math settings) removes every math reader while Word has focus, so equations were spoken by Word itself in English; and when the add-on's reader is toggled off, NVDA's built-in MathCAT reads equations with a partial Greek translation ("x to the minus ένα"). The settings panel now offers to disable native Word math, and the self-test announces both situations aloud.
* The self-test (`NVDA+Alt+Shift+G` and the settings-panel button) is now a full spoken diagnosis: it reports when the add-on is toggled off, when another math reader had taken over the provider slot (and reclaims it), when automatic language switching is off, and when native Word math is enabled.
* Documents reading equations in Microsoft Word, including the native-math option and the limitation with compatibility-mode (.doc) files whose equations are Equation 3.0/MathType objects.

## 1.0.4 - 2026-07-13

* Fixes math being read with an English voice: when NVDA's **Automatic language switching** speech option is disabled, NVDA silently discards the Greek language tag the add-on puts on math speech. The add-on now logs a clear warning, the self-test announces the problem aloud, and the settings panel offers to enable the option directly.
* The self-test (`NVDA+Alt+Shift+G` and the settings-panel button) now logs the active synthesizer and voice, making voice-routing problems diagnosable from the NVDA log.
* Documents how to hear math with a natural Greek voice such as **Microsoft Stefanos** (Windows OneCore), including installing the Greek voice in Windows and configuring NVDA.

## 1.0.3 - 2026-07-13

* Adds a **Test Greek math speech** button to the settings panel, avoiding keyboard-layout and gesture conflicts.
* Reclaims the Greek provider after all global add-ons have finished starting, in case another math add-on registers later.
* Logs the first MathML request received by the Greek provider to distinguish provider routing from synthesizer problems.

## 1.0.2 - 2026-07-13

* Adds `NVDA+Alt+Shift+G`, a direct Greek speech self-test that bypasses document and application math routing.
* Logs whether the Greek provider is active when the self-test runs, making provider failures distinguishable from content that is not exposed as MathML.

## 1.0.1 - 2026-07-13

* Restores Greek speech and interaction automatically if NVDA or another math add-on replaces the active provider during an application switch.
* Adds integration tests for provider ownership, recovery, and clean restoration of the previous math reader.

## 1.0.0 - 2026-07-09

Initial release.

* Greek speech for MathML using Greek school and university dictation conventions.
* Coverage for fractions, powers, roots, integrals, sums, products, limits, derivatives, matrices, determinants, systems of equations, set notation, vectors, intervals, trigonometric functions, logarithms, and common mathematical symbols.
* Interactive expression navigation with `NVDA+Alt+M`.
* Settings panel with verbosity, decimal comma, and Greek synthesizer language switching options.
* Greek UI translation and Greek/English documentation.
