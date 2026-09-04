# Greek Math Reader

Reads mathematical content aloud in **natural Greek**, following the dictation conventions used in Greek schools and universities — the way a Greek math teacher would read an expression at the blackboard.

Upstream MathCAT now has an early, in-development Greek rule pack. It may not yet be included in the MathCAT version bundled with an installed NVDA release, and it has not passed Greek Math Reader's semantic parity gates. The add-on retains a complete local Greek engine and uses MathCAT only when the installed backend explicitly advertises `el` support.

## Features

* **Greek speech for MathML** anywhere NVDA finds it: web pages, EPUB books, Word equations, and accessible PDF formulas exposed as MathML.
* **Broad structural coverage**: fractions, powers, roots, integrals, sums/products, limits, derivatives, matrices/determinants, systems, absolute values, intervals, sets, logic, vectors, trigonometric functions, logarithms, and more.
* **Greek school conventions**: capital letters are read with their Greek names ("τρίγωνο άλφα βήτα γάμα"), decimals are read with the Greek decimal comma, and both Latin (sin, cos) and Greek (ημ, συν, λογ) notation are recognized.
* **Deep symbol coverage**: signed number sets (ℝ⁺ "το σύνολο των θετικών πραγματικών αριθμών", ℝ² "ρο στο τετράγωνο"), angle minutes and seconds (30° 15′ "30 μοίρες 15 πρώτα λεπτά"), repeating decimals (0,3̄ "0 κόμμα 3 περιοδικό"), powers and roots with full Greek ordinals up to 99 ("στην εικοστή πρώτη"), order relations, logic, currency, ready-made fraction characters (½ ¾), and the Unicode mathematical alphabets that Word and MathJax produce (𝑥, 𝐀, 𝛼 are read as regular letters).
* **Interactive navigation**: press NVDA+Alt+M to explore known semantic operands and otherwise-safe structural parts.
* **Three verbosity levels**: terse, smart (default), and verbose.
* **One semantic engine** for MathML, LaTeX and UnicodeMath: valid `intent` wins, ambiguity is not guessed, and unknown symbols remain in speech and diagnostics.
* **LaTeX and UnicodeMath reading**: select or copy an expression and press **NVDA+Alt+L**; the format is announced and a double press opens interactive exploration.
* **2.1 semantic coverage**: adjoints, grad/div/curl/Laplacian, inner/cross/exterior/tensor products, probability/statistics concepts, independence, bra–ket, matrix elements, context-gated commutators, and compound SI units. Preview modules cover university mathematics, physics and specialist terminology through author `intent` until review and automatic inference are safe.
* **Expanded 1.1 vocabulary**: probability and statistics, geometry, number theory, linear algebra, complex analysis, partial derivatives and multiple integrals, plus SI physics units and scientific notation.

## Installation

Install Greek Math Reader only from the **NVDA Add-on Store**:

1. Press **NVDA+N** to open the NVDA menu.
2. Choose **Tools → Add-on Store**.
3. Open **Available add-ons** and search for **Greek Math Reader**.
4. Select the add-on, choose **Install**, and restart NVDA when prompted.

This version (2.2.0) ships on the stable channel by explicit maintainer decision. New semantic terms remain “source-checked, pending expert review”: specialist/language approval and listening tests with blind Greek NVDA users are still open, tracked in `RELEASE_GATES.md` and `TERMINOLOGY_REVIEW.md` in the source repository.

## Usage

1. After installation, math on web pages is read in Greek automatically as you move through the text.
2. To explore an expression in depth, move to it and press **NVDA+Alt+M** (NVDA's standard "interact with math" command). Then:
	* **Down arrow**: move into the current part (e.g. into the numerator).
	* **Up arrow**: move out to the containing part.
	* **Left/right arrows**: previous/next part at the same level.
	* **Home**: return to the whole expression.
	* **End**: last inner part; **Backspace**: previous navigation position.
	* **Control+arrows**: move by table cell; **P**: report position.
	* **Space**: repeat the current part.
	* **Control+C**: copy the Greek reading to the clipboard.
	* **Control+Shift+C**: copy the current part as MathML.
	* **Escape**: exit interaction.
3. **NVDA+Alt+G** repairs and reasserts exclusive Greek math routing. While the add-on is installed there is no English speech-reader fallback.
4. **NVDA+Alt+Shift+G** tests the Greek engine and voice directly, independently of the current application. It should say “χι στο τετράγωνο συν 1”. If this succeeds but Word remains English, focus the equation and use **Copy diagnostics**; the problem is then in Word/NVDA routing or equation exposure, not Stefanos.
5. Select or copy LaTeX such as `\frac{x^2+1}{x-1}`, or UnicodeMath such as `∑_(n=1)^∞ 1/n²`, and press **NVDA+Alt+L**. Press twice for interactive exploration.

## Choosing a Greek voice (Microsoft Stefanos and others)

The add-on decides **what** is said in Greek; **which voice** says it is decided by NVDA's synthesizer settings. For natural Greek speech with **Microsoft Stefanos** (Windows OneCore):

1. Install the Greek voice in Windows, if it is not already present: **Windows Settings → Time & Language → Speech → Manage voices → Add voices**, and add **Ελληνικά (Greek)**. This installs Microsoft Stefanos.
2. In NVDA: **NVDA menu → Preferences → Settings → Speech → Change… ** and set the synthesizer to **Windows OneCore voices**.
3. Then either:
	* set the **Voice** to **Microsoft Stefanos** so everything is spoken in Greek, or
	* keep your usual voice for the rest of the screen and enable **Automatic language switching** in NVDA's Speech settings. Math is tagged as Greek by this add-on, so NVDA switches to Stefanos just for the math and back afterwards.

**Important:** if NVDA's **Automatic language switching** option is disabled, NVDA discards the Greek language tag and math is read with the current voice's language — with an English voice, Greek math comes out as mangled English. The add-on's repair/self-test turns this setting back on. It also warns when the current synthesizer has no installed Greek voice; install Microsoft Stefanos or use another synthesizer with Greek support.

The same applies to eSpeak NG (which has a Greek voice, robotic but functional) and to any other synthesizer with Greek support: either select its Greek voice directly, or enable automatic language switching.

## Reading equations in Microsoft Word

Word exposes two accessibility representations inside a modern equation: structural MathML on the enclosing equation and an English linear speech stream such as `χ squared plus 1`. NVDA 2026.1.1 can choose that English stream during character/word movement, current-line reading, typing, selection, or cached Say All speech and skip every math provider. Version 2.0.0 covers both the TextInfo route and NVDA's official final-speech filter.

1. Keep NVDA's **"Use native math support in Word and Outlook" unchecked**. The health check reports a bad setting and **Repair** changes it explicitly.
2. Set **Advanced → Use UI Automation to access Microsoft Word document controls** to **Always**, or use Repair. Restart NVDA and Word afterwards.
3. Greek speech and interaction are exclusive while the add-on is installed. **NVDA+Alt+G** repairs the routing instead of turning Greek reading off.
4. Use a **normal .docx document** with modern (OMath) equations, in a recent Word 365. Documents in **compatibility mode (.doc)** contain old Equation 3.0 or MathType objects, which Word may not expose as MathML — convert the document (File → Info → Convert) and, if needed, re-create those equations with Insert → Equation.

If Word's UIA custom MathML property is absent, version 2.0.0 uses Word's read-only COM model to confirm the native OMath at the caret. Structured caret routes can also read its `WordOpenXML` and transform OMML to MathML in memory with Office's stylesheet. The final-speech filter changes English math vocabulary only after UIA or OMath confirmation. It does not move the selection, use the clipboard, linearize the equation, edit the document, or touch Undo history.

If an equation is still not read in Greek, focus that equation and choose **Copy diagnostics** in the Greek Math Reader settings. The copied report distinguishes the TextInfo, UIA-notification, UIA MathML, and native OMath routes. The self-test checks only the Greek engine and voice.

## Settings

NVDA menu → Preferences → Settings → **Greek Math Reader**:

In NVDA 2026.1.1, **Math → Language** has no Automatic choice and normally defaults to English. It belongs to the built-in MathCAT reader and is bypassed by this add-on.

* **Speech verbosity**: terse / smart / verbose.
* **Terminology and context**: Standard/School/University wording and a domain hint for ambiguous notation.
* **Rate and pauses**, automatic MathCAT Greek use when the installed backend advertises it, and validated personal terminology imported/exported as JSON.
* **Decimal comma**: read "3.14" as "3,14" (τρία κόμμα δεκατέσσερα).
* **Health check / Repair**: checking is read-only; repair changes the required NVDA settings explicitly.
* **Test Greek math speech**: speaks a sample expression directly, independently of the current application or webpage.
* **Reset settings and repair Greek math**: restores smart verbosity, decimal comma, automatic language switching, disabled native Word math, Word UI Automation set to Always, and every exclusive provider hook.
* **Copy diagnostics**: copies the exact add-on build, module path, active provider, Word TextInfo/notification route, UIA or OMath fallback result, Windows/Office details, focused object, last MathML exposure, and installed Greek OneCore voices.

### Recommended NVDA configuration

**Speech:** use **Windows OneCore voices** with the Greek **Microsoft Stefanos** voice installed in Windows. Select Stefanos directly for an all-Greek NVDA setup, or keep another OneCore voice and leave **Automatic language switching** checked. Keep **Trust voice's language when processing characters and symbols** and **Unicode normalization** checked. Rate, pitch, punctuation level, and volume are personal preferences.

**Audio:** select the output device you actually use, or **Default output device** if Windows manages it. For a clean baseline use **No ducking**, **Volume of NVDA sounds follows voice volume: off**, **NVDA sounds: 100**, **Sound split: Disabled**, and **Keep audio device awake: 30 seconds**. These settings do not determine whether math is Greek or English.

**Math:** built-in **Language** and MathCAT speech style do not affect the local engine; use this add-on's relative rate and pause controls. When MathCAT advertises Greek, the automatic adapter can delegate speech and interaction to it. Keep **Use native math support in Word and Outlook** unchecked. Braille settings still belong to NVDA/MathCAT and remain available.

**MathJax 4:** if a page exposes only an English `aria-label`, use the equation's MathJax context menu to enable **Assistive/Hidden MathML** and disable MathJax **Speech** generation. The add-on can replace a math reader only when the page exposes real MathML; it cannot reconstruct structure from a prewritten English alt description.

### Mathematics in PDF

Automatic reading works when the PDF and viewer expose a formula to NVDA as a math object containing MathML. Selectable text or generic tagging alone does not guarantee that semantic structure. If the formula is exposed as linear text, select it and press **NVDA+Alt+L** for LaTeX/UnicodeMath reading. Images, English-only alternative text, and text whose structure was discarded require a compatible PDF/viewer or external remediation/OCR.

## Compatibility

NVDA 2024.1 through 2026.1.1. The final Word speech filter is used on NVDA 2026.1.1; older versions continue through their available provider/TextInfo routes. The add-on exclusively owns math speech and interaction while installed; braille output remains with the built-in provider.

## Feedback

Please report issues and terminology suggestions at the repository. Symbol, grammar, semantic-registry and morphology data live in `symbols_el.py`, `grammar_el.py`, `terminology_el.py`, and `morphology_el.py`. Specialist and blind NVDA-user corrections are required before stable release.

## Development disclosure

Artificial intelligence (AI) tools were used in the development and documentation of this repository and add-on.

## Support

Greek Math Reader is free software. If it makes mathematics more accessible for
you, please consider making a kind, optional donation to support its continued
development.

* Author: Bouronikos Christos
* Email: [chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com)
* GitHub: [ChristosBouronikos](https://github.com/ChristosBouronikos)
* PayPal: [Make a donation](https://paypal.me/christosbouronikos)

## Attribution

NVDA Greek Math (Greek Math Reader) by Bouronikos Christos (cbouronikos@uth.gr)

This notice must be preserved by anyone who copies, modifies, or redistributes
the add-on. It places no obligation on you as a user: you may run the add-on
freely, for any purpose.

If you deploy or recommend the add-on in an accessibility centre, a school, or a
university, please also name it and its author in your materials. That is a
request rather than a licence condition, and it helps the add-on reach more
blind and visually impaired students.

## License

GNU General Public License version 3 or later (`GPL-3.0-or-later`), with
additional author-attribution terms under section 7 of that license. The
complete license, including the additional terms, is included in the add-on
package as `LICENSE.md`.
