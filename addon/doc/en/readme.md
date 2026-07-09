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

## Installation

Install Greek Math Reader only from the NVDA Add-on Store:

1. Open the NVDA menu (NVDA+N) → **Tools** → **Add-on Store**.
2. In **Available add-ons**, search for **Greek Math Reader**.
3. Choose **Install** and restart NVDA when prompted.

Manual `.nvda-addon` downloads are not a supported installation channel for this project.

## Usage

1. After installation from the NVDA Add-on Store, math on web pages is read in Greek automatically as you move through the text.
2. To explore an expression in depth, move to it and press **NVDA+Alt+M** (NVDA's standard "interact with math" command). Then:
	* **Down arrow**: move into the current part (e.g. into the numerator).
	* **Up arrow**: move out to the containing part.
	* **Left/right arrows**: previous/next part at the same level.
	* **Home**: return to the whole expression.
	* **Space**: repeat the current part.
	* **Control+C**: copy the Greek reading to the clipboard.
	* **Escape**: exit interaction.
3. **NVDA+Alt+G** toggles Greek math reading on or off (for example, to temporarily switch back to the default English reader). The gesture can be changed in Input Gestures.

## Settings

NVDA menu → Preferences → Settings → **Greek Math Reader**:

* **Read mathematics in Greek**: enables/disables the add-on's reader.
* **Speech verbosity**: terse / smart / verbose.
* **Decimal comma**: read "3.14" as "3,14" (τρία κόμμα δεκατέσσερα).
* **Switch synthesizer language to Greek** while reading math: useful when reading Greek math inside English documents with a bilingual voice.

## Compatibility

NVDA 2024.1 through 2026.1.1. In NVDA 2026.1 and later, this add-on takes priority over the built-in MathCAT reader while enabled; braille output for math remains with the built-in provider.

## Feedback

Please report issues and terminology suggestions at the project repository. Terminology (how each symbol and structure is worded in Greek) lives in two easily editable files, and corrections from teachers and students are very welcome.
