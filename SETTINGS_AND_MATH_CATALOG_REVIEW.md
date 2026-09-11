Greek Math Reader: settings and mathematics catalog review
========================================================

Review date: 7 September 2026. Source version: 2.2.0, build `20260904-word-fallback-language-fixes`.

The highest-value next release would make mathematical distinctions audible, make existing preferences work consistently, and repair meaning-changing interpretations before expanding the subject menu. General relativity exposes all three needs: capital G and lowercase g sound identical in Smart mode, upper tensor indices are treated as powers, and the current Physics context is too broad to resolve the notation safely.

This is a source review and proposed roadmap. No production code, translations, defaults, or release artifacts were changed. Findings below distinguish executed engine examples, source inspection, and proposed wording. The review did not include a running Windows NVDA installation or listening tests with Microsoft Stefanos, eSpeak, or the neural voices.

The existing checks passed: `python3 -m unittest discover tests -q` ran 441 tests; `python3 tools/export_mathcat_el.py --check` passed. Additional direct engine probes reproduced the issues below. Passing the existing suite does not establish that the proposed Greek terminology is linguistically approved.

The current settings offer the following controls.

| Control | Choices / default | What the implementation actually does |
|---|---|---|
| Speech verbosity | Terse, Smart, Verbose; Smart default | Changes structural announcements. Verbose also announces capitals, coupling two different needs. |
| Terminology profile | Standard, School, University; Standard default | Chooses semantic-registry forms. Only seven of the 94 registry concepts currently have different profile forms. Legacy symbol/function readings do not consistently use the profile. |
| Notation context | Automatic, General mathematics, Geometry, Probability and statistics, Linear algebra, Vector calculus, Physics, Quantum physics, Abstract algebra | The current semantic interpreter explicitly branches on Physics, Quantum physics, Vector calculus, and Abstract algebra. General mathematics, Geometry, Probability/statistics, and Linear algebra have no dedicated domain-dependent behavior in the inspected engine. Automatic does not classify the surrounding document or course. |
| Relative speech rate | 1–100%; default 100% | Slows mathematical speech relative to NVDA's rate; cannot speed it above the NVDA baseline. Uses NVDA rate commands when available. |
| Pause factor | 0–100; default 50 | Scales existing breaks by `value / 50`: 0 removes their duration, 50 is normal, 100 doubles them. The label does not explain this scale. |
| Decimal comma | Enabled by default | Normalizes numeric text to the Greek decimal convention; this is not a full digit-by-digit or thousands-separator policy. |
| Literal English Latin letters | Disabled by default | Returns raw Latin characters instead of Greek school names. It does not explicitly assign an English language span to each letter; the provider forces mathematical speech to Greek. Actual sound remains synthesizer-dependent. |
| Word/Outlook backup translation | Enabled by default | Allows English mathematical speech translation even when an equation cannot be independently confirmed. |
| Automatic MathCAT Greek backend | Enabled by default | Delegates when the installed backend advertises Greek, can select it, and supplies a speech delegate. The adapter sets the language but does not forward the local terminology/profile/rate/pause/letter preferences. |
| Personal terminology | Import/export JSON; clear all; reset selected concept | Accepts known semantic concept IDs only. There is no term editor, catalog browser, or individual-letter override. Import replaces the pending personal dictionary. |
| Test Greek math speech | One sample equation | Reads the saved configuration, not pending panel choices. The self-test also enforces required NVDA settings and re-registers the provider. |
| Health, repair, reset, diagnostics | Status plus action buttons | Repair and reset act immediately. Reset also repairs routing and selected NVDA settings. The health label is initially sampled, and Repair sets it to ready without re-querying the health result. |
| Optional neural voices | Feature disabled by default; manager for download/remove | Manager displays languages, download sizes, licenses, installation status, and disk usage. Selecting the synthesizer affects all NVDA speech. There is no sample playback control in this manager. |

Sources: [settings panel](addon/globalPlugins/greekMathReader/settingsPanel.py), [configuration and self-test](addon/globalPlugins/greekMathReader/__init__.py), [provider](addon/globalPlugins/greekMathReader/provider.py), [backend adapter](addon/globalPlugins/greekMathReader/backend.py), [voice manager](addon/globalPlugins/greekMathReader/neuralVoicesDialog.py).

The settings additions below are ordered by user benefit and dependencies. “First” means the next implementation batch; “next” means after the underlying correctness work; “later” means a larger optional enhancement.

| Priority | Proposed option / feature | Concrete user benefit and recommended behavior |
|---|---|---|
| First | Announce capital letters independently | Expose the existing `announce_capitals` capability without requiring Verbose mode. Offer an explicit checkbox initially. Verify all identifier paths, including multi-letter identifiers and literal mode. |
| First | Latin-letter naming convention | Replace the binary checkbox with Greek school names, English letter names written for Greek speech, and literal characters. For the second convention, test G → «τζι», J → «τζέι», H → «έιτς». Retain the established school convention as a selectable option. |
| First | Individual symbol pronunciation editor | Search for a symbol, edit its spoken name, listen, reset. Distinguish G/g/Γ/γ and allow a course-specific choice. Apply edits to letter tokens, not arbitrary Greek text, where «σε» can be a preposition. Keep pronunciation separate from mathematical meaning. |
| First | Preview pending settings | “Listen to example” and “Listen to current expression,” with a text transcript, should use unsaved choices. Include capitals, fractions, tensor indices, matrices, and unknown symbols. Keep preview independent of Repair. |
| First | Explicit index reading | Offer mathematical scripts as “upper/lower index” in a tensor reading preset, with a one-expression structural-reading command. Do not infer that every superscript in a Physics document is an index: genuine powers such as c⁴ must remain powers. |
| First | Searchable mathematical catalog | Browse by subject, symbol, or Greek/English name. Show an example, current reading, alternate profile readings, whether recognition is automatic or needs author annotation, and any personal wording. This provides an accessible editor for the JSON functionality already present. |
| Next | Fraction and grouping detail | Natural fraction names, explicit numerator/denominator, and automatic structural boundaries. Make exponent/root endings separately adjustable where useful. Preserve enough boundaries to distinguish `(a/b)c` from `a/(bc)`. |
| Next | Saved course presets and quick switching | Save combinations for school algebra, statistics, linear algebra, relativity, and quantum mechanics. Build on NVDA configuration profiles where appropriate. Start with explicit selection and an announced active preset; scope document-specific behavior carefully. |
| Next | Recognized names versus structural description | Let a user request structural reading of the current expression or repeat it with a supported concept name. Author-provided meaning and reliable recognition should remain explainable; an arbitrary glyph must not acquire a physical meaning solely from a preset. |
| Next | Matrix reading preferences | Whole matrix, dimensions followed by exploration, row reading, and column reading. Optional position announcements and adjustable boundary sounds would extend existing cell navigation. Avoid silently skipping zero entries. |
| Next | Numbers and units | Whole-number versus digit reading; explicit decimal digits; unit name versus unit symbol. Test decimal comma, grouped numbers, negative powers, Greek/Latin micro symbols, and compound SI units. |
| Next | Understandable rate and pause controls | Show rate as a percentage of normal NVDA speech and pauses as 0%, 100%, 200% of the standard breaks. Add sample playback. Consider rates above 100% only after testing supported synthesizers. |
| Next | Backend status and supported settings | Display the active local/MathCAT backend and explain which controls apply. Either translate supported preferences into backend settings or clearly mark unsupported ones. Do not let an automatic switch silently discard personal reading choices. |
| Next | Report a reading problem | Prepare a local report containing the selected expression, actual speech, expected speech entered by the user, format, preset, backend, and voice. Let the user inspect/copy it; do not automatically send it. |
| Later | Voice audition and pronunciation samples | Add playback for installed voices using the same mathematical samples and show which voice is active. A separate voice just for equations needs dedicated speech-routing work; it is not a simple extra selector. |
| Later | Navigation preferences | Separate spoken part labels from boundary beeps; add repeat slowly, jump to numerator/denominator or an index, and full-expression copy alongside the existing current-part copy. |

The panel should group related controls into Reading, Letters and indices, Terminology, Navigation, Voices, and Compatibility/support, with short explanations and keyboard-accessible labels. A single growing list of checkboxes would make navigation harder. Repair and reset should have distinct descriptions, and resetting reading preferences should have predictable scope.

The G concern is supported by the current code and direct engine output.

| Input | Current Smart output, including Physics context | Proposed reading behavior |
|---|---|---|
| G | «ζε» | In the proposed English-name convention: «κεφαλαίο τζι» when capitals are enabled. |
| g | «ζε» | «τζι», or «πεζό τζι» in an explicit letter-identification command. |
| G with lower μν | «ζε μι νι» | «κεφαλαίο τζι με κάτω δείκτες μι νι». |
| g with lower μν | «ζε μι νι» | «πεζό τζι με κάτω δείκτες μι νι» when distinguishing case explicitly. |
| Γ with upper ρ and lower μν | «γάμα μι νι υψωμένο σε ρο» | «κεφαλαίο γάμα με άνω δείκτη ρο και κάτω δείκτες μι νι» in structural tensor reading. |
| A with upper μ | «έι στη μι» | If the superscript is an index: «κεφαλαίο έι με άνω δείκτη μι». |

These are proposed speech examples, not an assertion that all Greek lecturers use the same Latin-letter convention. The repository itself records «ζε» versus «τζι» as an unresolved convention question. The unambiguous defect is that the default reading loses the G/g distinction and does not express the tensor-index roles. Switching to Verbose currently restores the capital announcement, but does not resolve tensor semantics. Literal mode returns G/g without guaranteeing how a Greek voice pronounces them; its early return also bypasses the capital prefix.

In Einstein's field equations, G with two indices conventionally denotes the Einstein tensor; lowercase g with two indices denotes the metric. Γ with the relevant index pattern denotes a Christoffel symbol. A plain G in the coupling factor can be the gravitational constant. These identities are supported by [Greek university relativity research, printed pages 26 and 50](https://pergamos.lib.uoa.gr/uoa/dl/object/2287856/file.pdf) and the [Greek school physics constants table](https://ebooks.edu.gr/ebooks/v/html/8547/2728/Fysiki-G-Lykeiou-ThSp_html-apli/index_par.html). They do not establish a universal pronunciation for Latin G. The same university source also uses capital G for a configuration-space metric elsewhere, reinforcing the need to honor the author's meaning.

A semantic reader could optionally say «τανυστής του Αϊνστάιν», «μετρικός τανυστής», «σύμβολο Christoffel», or «βαρυτική σταθερά» when the meaning is established, while retaining the symbol and indices on request. Replacing every G with the Einstein tensor or with Greek gamma would be incorrect. The current registry includes `metric_tensor`, but has no dedicated entries for the Einstein tensor, Christoffel symbols, Ricci/Riemann tensors, or the gravitational constant.

The broader catalog has substantial existing coverage, but the different kinds of coverage need clearer labeling. The snapshot contains 215 merged operator/symbol keys, 112 function spellings, 58 unit spellings, and 94 semantic concept records. These counts are not additive counts of distinct mathematical concepts: aliases overlap, and structural rules add further functionality. Only seven semantic concepts vary across the three terminology profiles. The registry marks 16 concepts reviewed and 78 pending expert review; 16 source fields explicitly say citation pending. Those metadata labels do not prove that the human/listening approvals in the release ledger have occurred.

The explicit module lists contain 8 foundation, 23 university-core, 18 physics, and 14 specialist concepts. The latter three modules are marked preview. Another 31 registry concepts are not assigned to those explicit module lists. Module membership is metadata, not a settings switch or runtime release gate. Advanced preview records generally become usable through author `intent`; a matching Greek headword alone does not supply parsing, parameter roles, navigation, or automatic recognition.

Sources: [symbol and function tables](addon/globalPlugins/greekMathReader/engine/symbols_el.py), [semantic registry](addon/globalPlugins/greekMathReader/engine/terminology_el.py), [recognition rules](addon/globalPlugins/greekMathReader/engine/semantics.py), [terminology review ledger](TERMINOLOGY_REVIEW.md), and [release evidence](RELEASE_GATES.md).

The mathematical expansion roadmap should cover the following areas. These are implementation targets, not claims that the current reader already understands all the listed meanings.

| Area | Existing coverage | Most useful improvements |
|---|---|---|
| Arithmetic and numbers | Signs, fractions, mixed numbers, powers, roots, decimals, scientific notation | Reliable fraction scope; digit-reading options; thousands/decimal separator tests; explicit root and exponent boundaries; agreement of numerical phrases. |
| School algebra and functions | Polynomials, equations, function application/definitions, logarithms, inverse notation | Distinguish scalar reciprocal, matrix inverse, and inverse function from evidence; improve nested/composed function scope and multi-line derivations. |
| Trigonometry and geometry | Greek/Latin trigonometric names, inverse and hyperbolic forms, angles, vectors, parallel/perpendicular notation | Consistent function-argument boundaries; distinguish angle labels, line segments, tuples, and intervals; review sine-inverse versus reciprocal conventions. |
| Sets, logic, and discrete mathematics | Membership, set builders, number sets, quantifiers, common logical relations, gcd/lcm, factorials and combinations | Distinguish ℙ as primes, a probability measure, or projective notation; add quantifier scope, modular congruence structures, graph notation, and recurrence/generating-function examples. |
| Single-variable calculus | Limits, one-sided limits, sums/products, derivatives and integrals | Consistent Greek grammatical connectors, evaluation bounds and differential scope; convergence and series examples; better structural reading of operator-only derivatives. |
| Multivariable and vector calculus | Gradient/divergence/curl/Laplacian recognition; derivative/integral terminology; Jacobian/Hessian names | Preserve vector styling across input encodings; restrict vector-product inference; distinguish ∇, covariant derivatives, and Δ meanings; structured line/surface/volume integral parameters. |
| Linear and multilinear algebra | Matrices, determinants, transpose, adjoint, inverse, norms, several products; preview eigenvalue/matrix types | Upper/lower index roles; adjugate versus adjoint; scalar/vector/matrix identity; block and augmented-matrix boundaries; consistent tensor/exterior/cross products; row/column reading preferences. |
| Differential equations and numerical methods | Ordinary/partial derivatives, systems, transform names, initial/boundary-condition terminology | Correct piecewise-function versus system recognition; equation labels and coupled systems; finite differences, discretized operators, and initial/boundary data with explicit roles. |
| Probability and statistics | Probability, expectation, conditional expectation, variance/covariance, standard deviation, distributions by function name, preview inference terms | Align E(X)/E[X] and all profile paths; distribution families and parameters; conditional independence; estimates, hats, confidence/credible interval distinctions, likelihood and test-statistic roles. |
| Complex analysis and special functions | Conjugation, modulus, real/imaginary parts, argument, residues by name, erf and sinc | Review sinc wording; add Gamma/Beta/Bessel and other requested families with argument roles; branch/contour conventions; avoid interpreting every overbar as the same operation. |
| Fourier analysis and signal processing | Fourier/Laplace names, sums/integrals, some special-function spellings | Convolution versus multiplication; DFT/Z-transform notation; normalized versus unnormalized sinc; frequency/angular-frequency and transform-variable distinctions. |
| Classical mechanics, electromagnetism, and thermodynamics | SI units and compound units; preview physical-quantity terms; Hamiltonian/Lagrangian terminology | Separate Hamiltonian function from quantum Hamiltonian operator; parameterized physical quantities and constants; scalar versus vector fields; derivatives and unit powers; review partition-function wording by source. |
| Special/general relativity | Four-vector, four-momentum, metric tensor, proper time, and covariant/contravariant terminology records; structural multiscripts | First add case-aware Latin letters and tensor-index reading. Then Einstein/Ricci/Riemann, Christoffel, covariant/Lie derivatives, contraction, metric signature, interval and geodesic structures. Preserve powers and constant G. |
| Quantum mechanics | Bra/ket, braket, matrix elements, commutator, anticommutator, quantum adjoint; preview wavefunction/operator names | Operator/state distinction; creation/annihilation operators and indexed state labels; density matrices, partial traces and expectation forms; spin/Pauli notation without conflating symbols and physical quantities. |
| Abstract algebra and category theory | Group/ring/field/ideal/morphism terminology; Hom/End/Aut/Gal function names | Structured quotient groups/rings, homomorphisms, kernels/images, direct sums/products, categorical composition and arrows; a glyph alone should not determine the algebraic structure. |
| Topology, measure, and functional analysis | Space/open-set/measure/manifold/bounded-operator terminology; closure/interior/support names | Parameterized spaces, topological closure versus conjugation, measures and measurable sets, almost-everywhere statements, Lp/Sobolev spaces, weak convergence and operator domains. |
| Differential geometry, distributions, and stochastic calculus | Manifold, differential form, generalized function, stochastic integral heads | Differential-form degree, exterior derivative/wedge, pullbacks/pushforwards; distribution pairings; Ito/Stratonovich distinctions and differentials. Start with explicit meaning and role-aware examples. |

The relativity scope above is consistent with the topics in the [University of Crete's General Relativity and Gravitation course](https://www.physics.uoc.gr/el/node/3134). MathML itself distinguishes the visual placement of scripts from their meaning and provides [prescripts and tensor indices](https://www.w3.org/TR/mathml-core/#prescripts-and-tensor-indices-mmultiscripts). This supports adding structural index speech without guessing a physical interpretation from every superscript.

Several reproduced problems should be fixed as part of catalog quality, independently of new user options.

| Finding | Executed or inspected evidence | Recommended correction |
|---|---|---|
| Physics changes scalar multiplication into a vector product | `<mn>3</mn><mo>×</mo><mn>4</mn>` with Physics → «διανυσματικό γινόμενο 3 με 4» | Require suitable operands or explicit meaning. A subject hint must not override definite scalar evidence. |
| Tensor scripts are treated as powers | Γ upper ρ/lower μν → «γάμα μι νι υψωμένο σε ρο»; T upper ν/lower μ → «ταυ μι στη νιοστή» | Add index roles across msup/msubsup/mmultiscripts and formats; retain true powers. |
| Equivalent bold vectors are interpreted differently | `mathvariant="bold"` a·b → inner product; Unicode 𝐚·𝐛 → ordinary multiplication in Automatic | Preserve mathematical style before Unicode normalization and inherited style during wrapper handling. |
| Equivalent expectation forms bypass profiles | Default E(X) → «μέση τιμή του χι»; E[X] → «αναμενόμενη τιμή του χι» | Send equivalent recognized notation through one concept renderer; keep generic function E possible where evidence requires it. |
| Personal terminology is bypassed | Overriding gradient affects ∇f, but `grad(f)` still says «κλίση του εφ»; plain absolute-value fences ignore the absolute-value override | Route equivalent established meanings through the registry, including legacy structural recognizers. |
| Author meaning disappears during simplification | Root `intent="absolute-value($x)"` speaks absolute value, but the same annotation on a one-child mrow collapses to just «χι» | Preserve semantic/style/argument metadata when simplifying wrappers. |
| Some semantic inputs lose operands | `gradient($x,$y)` speaks x only; `<mi intent="metric-tensor">g</mi>` speaks the term without the source g | Validate argument count/roles and preserve source text when an intent is incomplete or inapplicable. Decide explicitly when a semantic name substitutes for versus accompanies a symbol. |
| Piecewise functions become systems of equations | A two-branch table with x>0 and x≤0 is announced as «σύστημα 2 εξισώσεων» | Recognize value/condition columns or explicit cases intent; inequality in a branch condition is not evidence of an equation system. |
| Capital identifiers imply matrix inverse too readily | A⁻¹ is announced «αντίστροφος πίνακας έι» without matrix evidence | Use structural reciprocal/power reading when type is unknown. |
| Fraction scope is not always audible | In `(8πG/c⁴)Tμν`, Smart output lacks a fraction end before T | Add context-sensitive boundaries and a user-controlled explicit-fraction option. |
| Preview does not preview edits | Panel Test invokes `speakSelfTest()` without pending controls; self-test reads saved configuration and repairs settings | Create a non-mutating preview path and keep the existing repair action explicit. |
| Greek UI catalog is incomplete | Static extraction found 5 of 59 distinct settings-panel strings and all 34 distinct voice-manager strings absent from the add-on's Greek PO catalog | Translate the missing entries and add a source-string coverage check alongside format validation. Some common button terms may be supplied by NVDA itself; that does not cover the custom dialog messages. |

These findings come from the current local engine and source. They are not assertions about the installed MathCAT implementation or the exact audio produced by any particular voice.

The translation review should distinguish errors and inconsistencies from legitimate terminology preferences.

| Entry / area | Current wording | Proposed action |
|---|---|---|
| Latin G/g | «ζε» for both; capitals omitted in Smart | Add case identification and naming conventions. Offer «τζι» as a tested alternative; do not replace G with «γάμα». |
| Proper time | `proper_time`: «ιδιοχρόνος» | Review the stress against the school glossary's «ιδιόχρονος» and adopt the agreed spelling consistently in speech, tests, and documentation. [School glossary](https://ebooks.edu.gr/ebooks/v/html/8547/2728/Fysiki-G-Lykeiou-ThSp_html-apli/index_par.html). |
| sinc | «συνάρτηση συγχρονισμού» | Replace the unsupported expansion with an agreed sinc name; «συνάρτηση σινκ» is a pronunciation candidate. Greek academic material uses sinc for the sine-over-argument function, with normalized and unnormalized conventions. Do not infer a formula definition from the name alone. [NTUA research example](https://dspace.lib.ntua.gr/xmlui/bitstream/handle/123456789/3035/kalavrouziotisd_architecture.pdf?isAllowed=y&sequence=1), [Patras course example](https://eclass.upatras.gr/modules/document/file.php/EE861/%CE%91%CE%BA%CE%B1%CE%B4%CE%B7%CE%BC%CE%B1%CF%8A%CE%BA%CF%8C%20%CE%AD%CF%84%CE%BF%CF%82%202024-2025/SS-Skodras-S03v0.pdf). |
| ∇ and grad | Standalone ∇ is «ανάδελτα»; prose says «νάμπλα»; grad is «κλίση»; semantic gradient is «βαθμίδα» except School | Review acceptable alternatives and make symbol name, concept name, and profile choice consistent. |
| Cross versus exterior product | Fallback ⨯ says «εξωτερικό γινόμενο» while semantic cross product says «διανυσματικό γινόμενο» and exterior product has a separate record | Keep the two mathematical concepts distinct and use reviewed domain-dependent wording consistently. |
| Adjoint / adjugate / Hermitian conjugate | Different legacy and semantic paths use «προσαρτημένος», «συζυγής ανάστροφος», and «ερμιτιανός συζυγής» | Review with matrix and operator examples. Do not merge adjugate with conjugate transpose because a terminology head overlaps. |
| Hamiltonian | Always «χαμιλτονιανός τελεστής» for the semantic head | Distinguish classical Hamiltonian function from quantum operator. This changes meaning, so it needs separate concepts or clear type metadata. |
| Letter pairs and styled letters | Several Latin/Greek letters share school names; Unicode mathematical styles can be normalized away | Add a precise “identify this symbol” command for alphabet, case, style, and index role, with familiar concise reading as a separate user preference. |
| Greek grammatical connectors | Registry case/number/gender fields are present but empty/default in all 94 entries; legacy phrases embed connectors | Populate the forms actually needed by supported constructions and test agreement in full phrases. Existing unit morphology should be retained and extended, not replaced wholesale. |

The catalog should eventually have one reviewable record per meaning with accepted spellings, valid argument roles and counts, supported input forms, ambiguity counterexamples, profile phrases, pronunciation notes, source citation/page, and review evidence. A record is complete only when it can be recognized or explicitly annotated, spoken, navigated, copied, and tested without losing mathematical content. Avoid counting an intent-only label as full support for an entire subject.

A practical delivery sequence would be:

1. Repair scalar/vector confusion, lost intent metadata/operands, tensor-script speech, and piecewise recognition. Add regression examples that fail on the current behavior.
2. Expose capital announcements, implement deterministic letter conventions and per-letter customization, and add genuine preview of pending settings. Complete the Greek UI catalog.
3. Unify existing terminology/profile/override paths, improve number/fraction controls, and add the searchable catalog with transparent recognition status.
4. Implement a focused relativity package: G/g/Γ distinctions, named geometric objects with established meaning, covariant derivatives, and index navigation. Add statistics and linear-algebra parity in the same shared architecture.
5. Expand remaining subjects in the catalog table from requested examples, with precise semantic roles and documented Greek terminology. Add optional voice/navigation refinements after core reading behavior is stable.

For each meaning-sensitive addition, test MathML/LaTeX/UnicodeMath equivalents, grouped versus ungrouped representations, explicit style versus Unicode style, a plausible alternative meaning, all applicable profiles, personal overrides, and navigation/copy. For relativity specifically, include Gμν, gμν, Γ upper ρ/lower μν, a scalar G in the coupling factor, c⁴, and an Einstein summation expression in the same test set. A scalar multiplication test must continue to pass under every subject context. Listening evidence with supported voices and blind Greek NVDA users remains distinct from automated string checks.

Minimal reproduction of the central engine findings from the repository root:

```python
import sys
sys.path.insert(0, "addon/globalPlugins/greekMathReader")
from engine import ReadingConfig, speak_mathml, tokens_to_text

examples = [
    "<mi>G</mi><mo>+</mo><mi>g</mi>",
    "<mn>3</mn><mo>×</mo><mn>4</mn>",
    "<msubsup><mi>Γ</mi><mrow><mi>μ</mi><mi>ν</mi></mrow><mi>ρ</mi></msubsup>",
    '<mrow intent="absolute-value($x)"><mi arg="x">x</mi></mrow>',
]
for body in examples:
    print(tokens_to_text(speak_mathml(
        "<math>" + body + "</math>",
        ReadingConfig(domain_hint="physics"),
    )))
```
