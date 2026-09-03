# Greek terminology review ledger

The executable semantic registry is `engine/terminology_el.py`, version
`2026.08.2`. Its records include the stable concept ID, three profile forms,
grammatical metadata, pronunciation override, domain, source family and review
status. `source-checked-pending-expert-review` does **not** mean that a Greek
domain expert or blind-user review has happened.

The 2.1 work remains a development preview. It must not move to the stable
channel until every default entry used by a stable domain has approvals from:

1. a relevant Greek mathematics or physics specialist;
2. the Greek-language reviewer; and
3. at least two blind Greek NVDA users who listened with the supported voices.

The initial source set is the Greek Ministry of Education's [school algebra and
probability material](https://ebooks.edu.gr/ebooks/handle/8547/2364), the
[Kallipos probability material](https://repository.kallipos.gr/get-brochure-pdf?handle=11419%2F2810&locale=el),
and discipline-specific Kallipos texts. Sources establish vocabulary candidates;
they do not substitute for the approvals above.

## 2.1 semantic candidates

| Concept ID / notation | Standard candidate | School | University | Current status |
|---|---|---|---|---|
| `adjoint`, `A†` | «συζυγής ανάστροφος του Α» | same | «προσαρτημένος τελεστής του Α» | Source-checked; specialist review pending |
| `quantum_adjoint`, `A†` | «ερμιτιανός συζυγής του Α» | same | same | Quantum specialist review pending |
| `gradient`, `∇f` | «βαθμίδα του f» | «κλίση του f» | «βαθμίδα του f» | Source-checked; listening review pending |
| `divergence`, `∇·F` | «απόκλιση του F» | same | same | Source-checked; listening review pending |
| `curl`, `∇×F` | «στροβιλισμός του F» | same | same | Source-checked; listening review pending |
| `laplacian`, `∇²f` | «λαπλασιανή του f» | same | same | Source-checked; listening review pending |
| `expectation`, `E[X]` | «αναμενόμενη τιμή του X» | «μέση τιμή του X» | standard | Probability reviewer pending |
| `conditional_expectation` | «δεσμευμένη αναμενόμενη τιμή» | «δεσμευμένη μέση τιμή» | standard | Probability reviewer pending |
| `braket`, `⟨ψ|φ⟩` | «εσωτερικό γινόμενο ψ με φ» | same | «μπρα-κετ» as terminology head | Quantum reviewer pending |
| `commutator`, `[A,B]` | «μεταθέτης των Α και Β» | same | same | Spoken only with author intent or quantum/algebra context; review pending |
| `jacobian`, `hessian` | «ιακωβιανός / εσσιανός πίνακας» | same | same | Analysis reviewer pending |
| `hamiltonian`, `lagrangian` | «χαμιλτονιανός τελεστής», «λαγκρανζιανή συνάρτηση» | same | same | Mechanics/quantum reviewer pending |
| `cross_product`, `exterior_product` | «διανυσματικό γινόμενο», «εξωτερικό γινόμενο» | same | same | Kept as distinct concepts; algebra/physics review pending |

The `university_core`, `physics`, and `specialist` registry modules are explicitly
marked `preview`. Their intent-only entries cover the staged domains listed in
the roadmap, but several specialist records deliberately say “citation pending”.
They cannot enter a stable module until each exact form has a page-level Greek
source and the three human approvals above. Merely exporting an entry to the
MathCAT contribution bundle does not change that status.

Personal overrides are validated against concept IDs, cannot be empty or contain
control characters, and never change the semantic interpretation. Unknown or
ambiguous notation is read structurally and recorded in diagnostics.

## Earlier 1.1/2.0 forms

The following table records forms introduced or materially changed before the
semantic registry. Items marked **review** remain open review questions.

| Area | Notation | Current reading | Status / alternative |
|---|---|---|---|
| Ordinals | `x^4`, fourth root | «χι στην τέταρτη», «τέταρτη ρίζα» | **Review:** «τετάρτη» is also heard in traditional dictation. |
| Latin letters | `b`, `g`, `h` | «μπε», «ζε», «ας» | **Review:** modern English-influenced alternatives are «μπι», «τζι», «έιτς». |
| Geometry | `∠ABC`, `AB ⟂ CD`, `AB ∥ CD` | «γωνία…», «κάθετο στο», «παράλληλο στο» | Current default. |
| Number theory | `gcd(a,b)`, `lcm(a,b)`, `a∣b`, `a mod n` | «μέγιστος κοινός διαιρέτης…», «ελάχιστο κοινό πολλαπλάσιο…», «διαιρεί», «υπόλοιπο δια…» | Current default. |
| Probability | `P(A)`, `P(A∣B)`, `E(X)`, `Var(X)` | «πιθανότητα του…», «πιθανότητα του… δεδομένου του…», «αναμενόμενη τιμή…», «διακύμανση…» | Current default. |
| Statistics | `x̄`, `n!`, binomial coefficient | «μέσος όρος του χι», «νι παραγοντικό», «δυωνυμικός συντελεστής…» | Current default. |
| Linear algebra | `Aᵀ`, `A⁻¹`, `tr(A)`, `rank(A)`, `‖A‖`, `⟨u,v⟩` | «ανάστροφος…», «αντίστροφος πίνακας…», «ίχνος…», «βαθμός…», «νόρμα…», «εσωτερικό γινόμενο…» | Current default. |
| Complex analysis | `z̄`, `|z|`, `Re(z)`, `Im(z)`, `arg(z)` | «συζυγής του ζήτα», «μέτρο του ζήτα», «πραγματικό μέρος…», «φανταστικό μέρος…», «όρισμα…» | Current default. |
| Calculus | partial and mixed derivatives, `∇`, multiple integrals, extrema under constraints | «μερική παράγωγος…», «μικτή μερική παράγωγος…», «νάμπλα», «διπλό/τριπλό ολοκλήρωμα…», «μέγιστο/ελάχιστο υπό τη συνθήκη…» | Current default. |
| Physics | `Δx`, `ẋ`, `ℏ`, `ε₀` | «μεταβολή του χι», «χι τελεία», «ας μπαρ», «έψιλον μηδέν» | Current default. |
| SI units | `m`, `kg`, `m/s`, `m/s²`, prefixes | Greek unit names and «ανά» forms | Recognized only when MathML marks the identifier as upright/normal, avoiding ordinary variables. |
| Scientific notation | `3×10⁸` | «3 επί 10 στην όγδοη» | Current default. |
| Short letter names (speech only) | `x`→χι, `y`→ψι, `ρ`, `φ` … | Spoken as «χί», «ψί», «ρό», «φί» (accented) | **New in 2.0.0.** OneCore/Stefanos spells the unaccented 2‑letter names out (ψι → "ψι γιώτα"); the tonos forces one word. The copied/clipboard reading stays unaccented («ψι»). The preposition «σε» is deliberately excluded. |
| Equation boundaries | Word "end of equation" / "end of section" | «τέλος εξίσωσης» | **New in 2.0.0. Review:** «τέλος γραμμής» is an alternative. Please confirm the exact English phrase Word speaks on your machine (via Copy diagnostics) so the trigger can be tightened. |
