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
