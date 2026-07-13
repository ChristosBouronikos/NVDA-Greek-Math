# Greek Math Reader

Reads mathematical content aloud in **natural Greek**, following the dictation conventions used in Greek schools and universities — the way a Greek math teacher would read an expression at the blackboard.

NVDA's built-in math support (MathCAT, since NVDA 2026.1) reads math in English and other languages, but not in Greek. This add-on fills that gap for Greek-speaking users.

## Features

* **Greek speech for MathML** anywhere NVDA finds it: web pages (Wikipedia, e-class platforms, MathJax/MathML content), EPUB books, and Word equations exposed as MathML.
* **Comprehensive coverage**: fractions (including nested), powers ("χι στο τετράγωνο"), roots ("κυβική ρίζα"), integrals with bounds ("ολοκλήρωμα από 0 έως 1 του…"), sums and products ("άθροισμα για νι από 1 έως άπειρο"), limits ("όριο καθώς το χι τείνει στο 0"), derivatives (f′ "εφ τόνος", dy/dx "παράγωγος του ψι ως προς χι"), matrices and determinants with row/column announcements, systems of equations, absolute values, intervals, set notation, logic, vectors, trigonometric functions with the Greek naming (ημίτονο, συνημίτονο, εφαπτομένη), logarithms, and more.
* **Greek school conventions**: capital letters are read with their Greek names ("τρίγωνο άλφα βήτα γάμα"), decimals are read with the Greek decimal comma, and both Latin (sin, cos) and Greek (ημ, συν, λογ) notation are recognized.
* **Deep symbol coverage**: signed number sets (ℝ⁺ "το σύνολο των θετικών πραγματικών αριθμών", ℝ² "ρο στο τετράγωνο"), angle minutes and seconds (30° 15′ "30 μοίρες 15 πρώτα λεπτά"), repeating decimals (0,3̄ "0 κόμμα 3 περιοδικό"), powers and roots with full Greek ordinals up to 99 ("στην εικοστή πρώτη"), order relations, logic, currency, ready-made fraction characters (½ ¾), and the Unicode mathematical alphabets that Word and MathJax produce (𝑥, 𝐀, 𝛼 are read as regular letters).
* **Interactive navigation**: press NVDA+Alt+M on an expression to explore it part by part.
* **Three verbosity levels**: terse, smart (default), and verbose.
* **LaTeX reading**: select or copy a LaTeX expression and press **NVDA+Alt+L** to hear it in Greek; press twice to explore its structure interactively.
* **Expanded 1.1 vocabulary**: probability and statistics, geometry, number theory, linear algebra, complex analysis, partial derivatives and multiple integrals, plus SI physics units and scientific notation.

## Installation

Version 1.1.5 is an unpublished diagnostic build for testing the Word fix. Install the exact supplied `greekMathReader-1.1.5.nvda-addon` file manually, accept replacement, then restart both NVDA and Word. After this version is published, use the NVDA Add-on Store for normal installation:

1. Open the NVDA menu (NVDA+N) → **Tools** → **Add-on Store**.
2. In **Available add-ons**, search for **Greek Math Reader**.
3. Choose **Install** and restart NVDA when prompted.

Do not use an older 1.1.4 file: install 1.1.5 and verify its build identifier with **Copy diagnostics**.

## Usage

1. After installation, math on web pages is read in Greek automatically as you move through the text.
2. To explore an expression in depth, move to it and press **NVDA+Alt+M** (NVDA's standard "interact with math" command). Then:
	* **Down arrow**: move into the current part (e.g. into the numerator).
	* **Up arrow**: move out to the containing part.
	* **Left/right arrows**: previous/next part at the same level.
	* **Home**: return to the whole expression.
	* **Space**: repeat the current part.
	* **Control+C**: copy the Greek reading to the clipboard.
	* **Escape**: exit interaction.
3. **NVDA+Alt+G** repairs and reasserts exclusive Greek math routing. While the add-on is installed there is no English speech-reader fallback.
4. **NVDA+Alt+Shift+G** tests the Greek engine and voice directly, independently of the current application. It should say “χι στο τετράγωνο συν 1”. If this succeeds but Word remains English, focus the equation and use **Copy diagnostics**; the problem is then in Word/NVDA routing or equation exposure, not Stefanos.
5. Select or copy LaTeX such as `\frac{x^2+1}{x-1}` and press **NVDA+Alt+L**. Press the gesture twice to open interactive exploration of the LaTeX expression.

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

Word exposes two accessibility representations inside a modern equation: structural MathML on the enclosing equation and an English linear speech stream such as `χ squared plus 1`. NVDA 2026.1.1 can choose that English stream during character/word movement, current-line reading, typing, selection, or cached Say All speech and skip every math provider. Version 1.1.5 covers both the TextInfo route and NVDA's official final-speech filter.

1. Keep NVDA's **"Use native math support in Word and Outlook" unchecked** (NVDA menu → Preferences → Settings → **Math** → Application support). This keeps NVDA's math-provider framework loaded; it does not by itself disable Word's inner English linear text. The add-on enforces the setting automatically.
2. Set **Advanced → Use UI Automation to access Microsoft Word document controls** to **Always**. Version 1.1.5 enforces this because recent Word versions expose OMath MathML through UIA. Restart NVDA and Word after reset/installation.
3. Greek speech and interaction are exclusive while the add-on is installed. **NVDA+Alt+G** repairs the routing instead of turning Greek reading off.
4. Use a **normal .docx document** with modern (OMath) equations, in a recent Word 365. Documents in **compatibility mode (.doc)** contain old Equation 3.0 or MathType objects, which Word may not expose as MathML — convert the document (File → Info → Convert) and, if needed, re-create those equations with Insert → Equation.

If Word's UIA custom MathML property is absent, version 1.1.5 uses Word's read-only COM model to confirm the native OMath at the caret. Structured caret routes can also read its `WordOpenXML` and transform OMML to MathML in memory with Office's stylesheet. The final-speech filter changes English math vocabulary only after UIA or OMath confirmation. It does not move the selection, use the clipboard, linearize the equation, edit the document, or touch Undo history.

If an equation is still not read in Greek, focus that equation and choose **Copy diagnostics** in the Greek Math Reader settings. The copied report distinguishes the TextInfo, UIA-notification, UIA MathML, and native OMath routes. The self-test checks only the Greek engine and voice.

## Settings

NVDA menu → Preferences → Settings → **Greek Math Reader**:

In NVDA 2026.1.1, **Math → Language** has no Automatic choice and normally defaults to English. It belongs to the built-in MathCAT reader and is bypassed by this add-on.

* **Speech verbosity**: terse / smart / verbose.
* **Decimal comma**: read "3.14" as "3,14" (τρία κόμμα δεκατέσσερα).
* **Test Greek math speech**: speaks a sample expression directly, independently of the current application or webpage.
* **Reset settings and repair Greek math**: restores smart verbosity, decimal comma, automatic language switching, disabled native Word math, Word UI Automation set to Always, and every exclusive provider hook.
* **Copy diagnostics**: copies the exact add-on build, module path, active provider, Word TextInfo/notification route, UIA or OMath fallback result, Windows/Office details, focused object, last MathML exposure, and installed Greek OneCore voices.

### Recommended NVDA configuration

**Speech:** use **Windows OneCore voices** with the Greek **Microsoft Stefanos** voice installed in Windows. Select Stefanos directly for an all-Greek NVDA setup, or keep another OneCore voice and leave **Automatic language switching** checked. Keep **Trust voice's language when processing characters and symbols** and **Unicode normalization** checked. Rate, pitch, punctuation level, and volume are personal preferences.

**Audio:** select the output device you actually use, or **Default output device** if Windows manages it. For a clean baseline use **No ducking**, **Volume of NVDA sounds follows voice volume: off**, **NVDA sounds: 100**, **Sound split: Disabled**, and **Keep audio device awake: 30 seconds**. These settings do not determine whether math is Greek or English.

**Math:** **Language**, speech style, MathCAT verbosity, relative rate, and pause factor are ignored for speech by this add-on. Leave them at their defaults. Keep **Use native math support in Word and Outlook** unchecked. Braille settings still belong to NVDA/MathCAT and remain available.

**MathJax 4:** if a page exposes only an English `aria-label`, use the equation's MathJax context menu to enable **Assistive/Hidden MathML** and disable MathJax **Speech** generation. The add-on can replace a math reader only when the page exposes real MathML; it cannot reconstruct structure from a prewritten English alt description.

## Compatibility

NVDA 2024.1 through 2026.1.1. The final Word speech filter is used on NVDA 2026.1.1; older versions continue through their available provider/TextInfo routes. The add-on exclusively owns math speech and interaction while installed; braille output remains with the built-in provider.

## Feedback

Please report issues and terminology suggestions at the project repository. Terminology (how each symbol and structure is worded in Greek) lives in two easily editable files, and corrections from teachers and students are very welcome.

## Support

Greek Math Reader is free software. If it makes mathematics more accessible for
you, please consider making a kind, optional donation to support its continued
development.

* Author: Bouronikos Christos
* Email: [chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com)
* PayPal: [Make a donation](https://paypal.me/christosbouronikos)
