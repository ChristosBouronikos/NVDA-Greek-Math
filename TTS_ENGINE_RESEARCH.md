# Alternative TTS engines for Greek Math Reader — research notes

Branch: `feature/alternative-tts-voices`
Date: 2026-09-05
Status: **research only — no implementation decision committed yet**

Goal: let users replace Windows OneCore / eSpeak NG with a better-sounding
Greek voice, selectable from NVDA's own Settings → Speech → Synthesizer list,
with the voice downloaded on demand from the add-on's settings panel.

---

## 1. Hard constraints

| Constraint | Consequence |
|---|---|
| Add-on Store requires GPL-2-or-later–**compatible** licensing for everything shipped | Non-commercial (CC-BY-NC), CPML and OpenRAIL-M model weights **cannot be bundled** |
| NVDA selects a synthesizer globally, not per utterance | A neural voice improves *all* speech, not just math. There is no supported "neural for math, OneCore for prose" split |
| Manifest targets NVDA 2024.1 → 2026.1.1 | Spans the 32-bit → 64-bit transition; any native binary must ship as **both win32 and win_amd64** |
| Synth drivers are discovered at NVDA startup | The driver module must be bundled; only the *voice models* can be downloaded later |
| Store submissions are scanned by VirusTotal + CodeQL | Prefer bundling binaries over downloading executable code at runtime |

An add-on may contain **both** `globalPlugins/` and `synthDrivers/`, so the
"appears in NVDA's synthesizer list" requirement is satisfiable inside this
existing package — no second add-on needed.

---

## 2. Model survey

### Greek-capable, license-clean

| Model | License | Arch / size | Notes |
|---|---|---|---|
| **Piper `el_GR-rapunzelina-low`** | **CC0** (public domain) | VITS ONNX, ~63 MB, 16 kHz, single speaker | The only fully unencumbered neural Greek voice. Fine-tuned from the US-English *Ryan* voice on the Kaggle *Greek Single Speaker Speech Dataset*. **"low" quality tier — must be listened to before committing** |
| moiralabs/`GreekTTS` | Apache-2.0 | sesame/csm-1b — **1 B params, PyTorch** | Licence is fine; size and PyTorch dependency make it non-viable inside NVDA |

### Greek-capable, license-blocked

| Model | License | Why blocked |
|---|---|---|
| `Supertone/supertonic-3` (el) | **OpenRAIL-M** (weights); MIT (code) | 31 languages incl. Greek, 99 M params, ONNX, very fast — technically ideal. But OpenRAIL-M adds use-based restrictions → **not a free-software licence, not GPL-compatible**. Cannot be bundled; downloading it on the user's behalf still needs legal review |
| `facebook/mms-tts-ell` | CC-BY-NC-4.0 | Non-commercial |
| `PetrosStav/F5-TTS-Greek` | CC-BY-NC-4.0 | Non-commercial; also PyTorch, needs reference audio, Greek input must be lowercase |
| Coqui XTTS-v2 | CPML | Non-commercial |

### No Greek at all

| Model | License | Languages |
|---|---|---|
| **Kokoro-82M** | Apache-2.0 ✓ | en-US/GB, es, fr, hi, it, ja, pt-BR, zh — **no Greek** |
| **Breeze TTS 2** | code Apache-2.0; **weights research/non-commercial** | English + Chinese only |
| RHVoice | GPL ✓ | 23 languages — **no Greek** |
| Zonos, MeloTTS | Apache/MIT | No Greek |

### Baselines already available to the user

- **eSpeak NG** (GPL-3, in NVDA core) — Greek, formant synthesis, robotic.
- **Windows OneCore "Microsoft Stefanos"** — current setup. Note: Microsoft's
  *neural* Greek voices (`el-GR-NestorasNeural`, `el-GR-AthinaNeural`) are
  **Azure cloud only**; they are not downloadable as local Windows voices, so
  "just install the natural voice" is not an option for Greek.

---

## 3. Runtime: the important finding

The expensive part of a neural synth driver is not the driver, it is the
inference runtime (ONNX Runtime + espeak-ng phonemisation) as native binaries
for two architectures.

**`sherpa-onnx` (k2-fsa) solves this**:

- **Apache-2.0** — compatible with this add-on's GPL-3.0-or-later.
- Publishes prebuilt Windows wheels for **both `win32` and `win_amd64`**
  (e.g. `sherpa_onnx-1.13.6-cp314-cp314-win32.whl`), so the 32/64-bit split is
  covered by upstream rather than by us.
- Bundles ONNX Runtime and espeak-ng phonemisation internally — no separate
  `piper-phonemize` build.
- Already supports the exact model families in play:
  `vits-piper-el_GR-rapunzelina-low` and `supertonic-3-el` are both in its
  published Greek model catalogue.

Open items to verify before committing: wheel size on disk per architecture,
Python ABI tags matching NVDA 2024.1 (cp311) through 2026.1, and real-time
factor on a low-end Windows laptop.

---

## 4. Recommendation

1. **Listen first.** `el_GR-rapunzelina-low` is a 16 kHz "low" tier voice
   fine-tuned from an English speaker. It may or may not beat Microsoft
   Stefanos. Generate Greek mathematical sentences through it and compare
   before any code is written — this is a one-hour check that could cancel
   the whole feature.
2. If it wins: add `synthDrivers/greekMathVoice.py` to this add-on, backed by
   bundled `sherpa-onnx` wheels, with a voice manager in the existing settings
   panel that downloads CC0/permissive models on demand. Ship the driver
   disabled-by-default; NVDA's synthesizer list stays the user's choice.
3. If it loses: drop the bundled-synth idea and instead detect and recommend
   the maintained neural-voice add-ons (Dengjen / piper-nvda) from our
   settings panel, which costs ~300 lines and no binaries.

## 5. Sources

- Piper Greek voice + model card (CC0): https://huggingface.co/rhasspy/piper-voices/tree/main/el/el_GR/rapunzelina
- Supertonic-3: https://huggingface.co/Supertone/supertonic-3
- sherpa-onnx Greek catalogue: https://k2-fsa.github.io/sherpa/onnx/tts/all/Greek/index.html
- sherpa-onnx (Apache-2.0): https://github.com/k2-fsa/sherpa-onnx
- Kokoro-82M: https://huggingface.co/hexgrad/Kokoro-82M
- Breeze TTS 2: https://huggingface.co/BreezeBlue/Breeze-TTS-2
- MMS Greek: https://huggingface.co/facebook/mms-tts-ell
- F5-TTS-Greek: https://huggingface.co/PetrosStav/F5-TTS-Greek
- RHVoice languages: https://rhvoice.org/languages/
- NVDA add-on review criteria: https://addons.nvda-project.org/processes
- NVDA 64-bit porting guide: https://groups.google.com/a/nvaccess.org/g/nvda-users/c/z_TOySDuatE
- Dengjen (ex-Sonata): https://github.com/OnjLouis/dengjen-nvda

---

## 6. Specifically-requested candidates — why each was excluded

| Candidate | What it actually is | Verdict |
|---|---|---|
| **Breeze TTS 2** (`BreezeBlue/Breeze-TTS-2`) | Open-**weight** TTS, Aug 2026. #1 open model on the Artificial Analysis TTS leaderboard | ❌ Two independent blockers: **weights are research/non-commercial only** (inference code is Apache-2.0, the weights are not) → incompatible with the store's GPL-2-or-later requirement; and it supports **English + Chinese only** — no Greek. Also PyTorch, far too heavy for NVDA |
| **Kokoro-82M** | 82 M-param StyleTTS2-derived model, Apache-2.0 | ❌ Licence is perfect, size is perfect, but **no Greek**: en-US, en-GB, es, fr, hi, it, ja, pt-BR, zh only. Nothing to gain for a Greek add-on |
| **Meltemi** (`ilsp/Meltemi-7B`) | **Not a TTS model.** A 7 B-param bilingual Greek *text* LLM from ILSP / Athena RC, continual-pretrained from Mistral-7B on 28.5 B Greek tokens, Apache-2.0 | ❌ Category mismatch — it generates text, not speech. ILSP does run a long-standing Greek TTS research programme, but has not published open TTS **weights**; their synthesis is offered as a demo/service, not a downloadable model. (ILSP's speech release, VOX-KRIKRI, is speech→text, i.e. ASR, not TTS) |
| **RealtimeTTS** (`KoljaB/RealtimeTTS`) | **Not a model — an orchestration library.** MIT-licensed Python wrapper providing one streaming API over ~12 backends (System, Azure, ElevenLabs, Coqui XTTS, StyleTTS2, Piper, gTTS, Edge, Parler, Kokoro, Orpheus, OpenAI) | ❌ Adds no Greek voice of its own. Its only license-clean local Greek path is **Piper — i.e. back to `rapunzelina`**. Meanwhile it pulls a large async/PyAudio dependency stack and owns its own playback loop, which conflicts with NVDA's speech manager (NVDA drives buffering, indexing and interruption itself via `nvwave`). Wrong layer for a `synthDriver` |

Takeaway: the 2025–26 wave of high-quality open TTS (Breeze, Kokoro, Zonos,
MeloTTS, Orpheus) is uniformly English/Chinese-first. **None of them speak
Greek.** Greek availability, not model quality, is what constrains this feature.

---

## 7. OpenRAIL-M analysis for `Supertone/supertonic-3`

Licence text is BigScience Open RAIL-M. Sample code is MIT; **weights** are RAIL.

**Permissions granted:** commercial use ✔, redistribution ✔, derivative works ✔.

**Attachment A use restrictions (13 clauses).** Prohibits use to: break the law
(a); exploit or harm minors (b); generate disinformation intended to harm (c);
generate PII usable to harm someone (d); disseminate machine-generated content
without intelligibly disclaiming its origin (e); defame or harass (f);
impersonate / deepfake without consent (g); make automated decisions adversely
affecting legal rights (h); discriminate on social behaviour or predicted
personal characteristics (i); exploit a group's vulnerabilities to cause harm
(j); discriminate on legally protected characteristics (k); give medical advice
or interpret results (l); generate material for justice, law enforcement,
immigration or asylum administration (m).

**Does any clause obstruct a screen reader?** No. Reading a user's own document
aloud to that same user touches none of (a)–(m). Clause (e) is the only one
worth a glance, and it concerns *disseminating* generated content to third
parties — a screen reader speaks to its operator and disseminates nothing.
**The use case itself is clearly permitted.**

**So why is it still blocked for bundling?** The downstream-obligation clause:
every redistribution and every derivative "will always have to include — at
minimum — the same use-based restrictions", and each recipient must be given
the licence and notified. That is an additional restriction on downstream
recipients, which **GPL-3.0 §7 / §10 forbid us from imposing**. Shipping the
weights inside a GPL-3.0-or-later `.nvda-addon` would therefore be a licence
conflict, independent of whether the restrictions are reasonable.

**Conclusion — usable, but only user-fetched:**

- ❌ Cannot bundle the weights in the add-on package.
- ✅ *Can* support the format and let the **user** download the weights
  themselves after being shown the licence. We would be distributing a client,
  not the model — the same posture Dengjen/piper-nvda take with their voice
  catalogues. Requires an explicit licence-acceptance step in the download UI.
- Practical upside if we do: 31 languages including Greek from one 99 M-param
  ONNX model, already supported by sherpa-onnx as `supertonic-3-el`.

---

## 8. Written quality assessment — `el_GR-rapunzelina-low` vs Microsoft Stefanos

No audio comparison run; this is a documentary assessment of what the voice is
built from, for verification on Windows later.

### Provenance — the main concern

- **Training corpus: CSS10 Greek**, ~**4 h 08 m** of LibriVox audiobook speech
  from a single speaker. That is very small for neural TTS.
- The CSS10 authors report Greek as their weakest language: they **could not
  train Tacotron on Greek at all** because of the data size, and their DCTTS
  Greek model came out at "notably lower quality" than the other nine
  languages. The dataset's own authors flag Greek as the problem case.
- Piper's voice was **fine-tuned from the US-English "Ryan" model**, so
  English phonetic colouring in the output is a live risk.
- Quality tier is **"low"** — 16 kHz output, reduced model. **No medium or high
  tier exists for Greek**, so there is no upgrade path within Piper.

### Screen-reader-specific risks to verify on Windows

1. **Speech rate.** Many NVDA users run 300–800 wpm. VITS voices scale rate via
   `length_scale`, which degrades intelligibility much faster than a formant or
   concatenative synth. This is the single most likely reason a neural voice
   loses to Stefanos in daily use, and it must be tested at *your* rate, not at
   default.
2. **Mixed Greek/Latin text — directly relevant to this add-on.** A Greek-only
   phoneme model has no sane handling of embedded Latin. Piper issue #696
   reports `el_GR-rapunzelina-low` rendering English input as "English with a
   heavy French accent". Version 2.2.0 just added the *"read Latin letters as
   literal English letters"* option — that option and this voice may interact
   badly.
3. **`SPEECH_PRONUNCIATION` is tuned for Stefanos.** The respellings in
   `provider.py` (βε→βέ, ψι→ψί …) exist because OneCore *spells* short
   unaccented monosyllables. A different synth will have entirely different
   failure modes, so that table would need re-deriving per voice — it cannot be
   assumed to transfer.
4. **No user dictionary.** Piper has no lexicon override mechanism; any
   mispronounced mathematical term can only be fixed by respelling upstream in
   our engine.
5. **Latency.** Neural synthesis has a per-utterance startup cost that formant
   synths do not. For character echo while typing, this is felt immediately.

### Honest expectation

Stefanos is a competent commercial voice. `rapunzelina-low` is a low-tier model
trained on four hours of audiobook by a single speaker, fine-tuned off English,
flagged as weak by its own dataset authors. It will very likely sound **less
robotic in tone but less reliable in pronunciation**, and may lose outright at
high speech rates. It should be treated as *unproven* until heard on Windows —
it is not a safe assumption that this feature improves the user's daily
experience.

**Recommended verification order on Windows:** install Dengjen or piper-nvda
from the Add-on Store, add the Greek voice, and live with it for a day at your
normal speech rate before any driver work starts here. That is a zero-code test
of the exact voice this feature would ship.
