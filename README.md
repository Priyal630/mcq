# MCQ Hiring-Assessment Localizer

Converts English multiple-choice hiring-assessment questions into Hindi,
Marathi, or Gujarati — while keeping them valid as test items, not just
translated sentences.

This is **not** a general translation tool. It is built specifically around
4 documented failure modes seen in real AI-translated assessment exports
(see "Why this exists" below), using a 3-layer pipeline:

```
Layer 1   Translate natural language          sarvam-translate
Layer 2   Protect & transliterate tech terms  glossary + placeholder swap
Layer 3   Fix MCQ sentence structure/mood      Qwen2.5-7B-Instruct
```

---

## Why this exists

A QA review of an earlier AI-translated assessment batch (Odia, but the
same patterns apply to Hindi/Marathi/Gujarati) found 4 recurring problems:

1. **Technical words mistranslated.** "Refractory" isn't a real word in
   the target language, so the translator either invents something wrong
   or translates it semantically into something that doesn't mean
   "refractory" at all. *Fix: transliterate these terms (spell them out
   phonetically), don't translate them.*

2. **Wrong letters/conjuncts.** Phonetic-only translation produces
   spellings missing proper conjunct/ligature letters, because the model
   is reproducing how a word sounds, not how it's actually written.
   *Fix: pull transliterations from a curated, human-reviewed glossary
   instead of letting a model guess every time.*

3. **Declarative statement instead of a question.** English MCQs are
   often written as incomplete affirmative sentences ("Module
   installation is done to reduce ____") where the options complete the
   sentence. Translated literally, this often becomes a *finished*
   statement in the target language ("Module installation has been done
   to reduce X") — the test-taker can no longer tell it's a question.
   *Fix: a dedicated structure-repair pass that rewrites the stem as an
   unambiguous question.*

4. **Options not in matching grammatical form.** Options should stay as
   noun phrases if the English options were noun phrases. Naive
   translation sometimes turns them into full imperative sentences that
   no longer grammatically complete the question stem.
   *Fix: same structure-repair pass also normalizes option form.*

Layers 1–2 fix problems 1–2. Layer 3 fixes problems 3–4.

---

## Two models, two jobs

| Layer | Model | Why this model |
|---|---|---|
| 1 — Translation | `sarvam-translate` | Purpose-built single-task translator (Gemma3-4B based). Fast, accurate at plain translation, but only understands a one-line system prompt — it cannot follow multi-step instructions, which is why Layer 3 is a separate model. |
| 3 — Structure repair | `Qwen2.5-7B-Instruct` | Needs genuine instruction-following to rewrite sentence mood and option form on request — a task `sarvam-translate` was never trained for. Qwen2.5-7B has solid multilingual coverage (29+ languages) and fits comfortably alongside Layer 1's model on an 8GB GPU. |

### Memory budget (RTX 5050 Laptop, 8GB VRAM)

Both models run simultaneously, both 4-bit quantized:

| Model | Approx. size (4-bit) |
|---|---|
| sarvam-translate (~4B) | ~2.5 GB |
| Qwen2.5-7B-Instruct | ~4.5 GB |
| **Combined** | **~7 GB**, leaving ~1GB headroom for activations/KV cache |

This is genuinely tight. If you hit `CUDA out of memory`:
- Lower `MAX_NEW_TOKENS` (default 512) — try 256
- Close every other GPU program (browser hardware acceleration counts)
- As a last resort, the two models can be loaded one at a time instead of
  simultaneously (load Layer 1, process all rows' translations, unload it,
  then load Layer 3, process all rows' structure fixes). This isn't
  implemented in `server.py` yet — flag it if you need it and it can be
  added; it trades speed for a much safer memory ceiling.

---

## Setup

```bash
cd mcq-localizer
pip install -r requirements.txt
```

### Download Qwen2.5-7B-Instruct

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-7B-Instruct
```

(`sarvam-translate` — you already have this from the earlier translation
project; point `TRANSLATE_MODEL` at the same local path.)

### Run

```bash
# Windows (cmd)
set TRANSLATE_MODEL=C:\Users\ASUS\sarvam-translate
python server.py

# Windows (PowerShell)
$env:TRANSLATE_MODEL="C:\Users\ASUS\sarvam-translate"
python server.py

# macOS/Linux
TRANSLATE_MODEL=/path/to/sarvam-translate python server.py
```

Open **http://localhost:5000**. The status pill in the top bar shows when
both models have finished loading (this can take a couple of minutes).

---

## How to use it

1. **Upload** your English `.xlsx` (same schema as your existing
   assessment exports: Question, Choice A–E, Answer, Type, Tags, etc.)
2. **Pick a target language** — Hindi, Marathi, or Gujarati
3. **Per row**, the tool auto-flags candidate technical terms (capitalized
   words, known trade-term patterns, suffix heuristics). Click a term tag
   to confirm or reject it before processing — confirmed terms get
   transliterated instead of translated.
4. **Run the pipeline** (single row or all rows). Each row shows English
   source next to the final localized result.
5. **Edit inline** if the model didn't get it perfectly right — every
   field in the "Final" column is directly editable.
6. **Approve** rows you're satisfied with.
7. **Export** — downloads a clean `.xlsx` with only approved rows, in the
   exact same column schema as your input file.

This is deliberately a **review tool, not an auto-pilot**. Per the
original QA recommendation: *"instead of bulk translation, we should do
it in batches, then review it, then highlight the errors... and train
[the prompts] accordingly."* The per-row approve step is that review
loop, built into the UI instead of a separate spreadsheet pass.

---

## Extending the glossary

`glossaries/glossary.py` contains the curated term → transliteration
mapping. It's seeded with terms found in the actual uploaded assessment
files (Civil-Supervisor-Refractory, Civil-Fitter-General) plus common
construction/trade vocabulary. Add new entries as you encounter them:

```python
"your_new_term": {"hi": "हिंदी रूप", "mr": "मराठी रूप", "gu": "ગુજરાતી રૂપ"},
```

Terms not yet in the glossary fall back to staying in **English/Latin
script** rather than risking a broken phonetic guess (this directly
avoids documented Issue 2 — wrong conjunct letters from auto-transliteration).
The auto-detector (`glossaries/term_detector.py`) will keep flagging new
candidate terms for you to add as you process more trades/files.

---

## Files

```
mcq-localizer/
├── server.py                  # Flask server, both models, all API routes
├── pipeline.py                 # 3-layer orchestration logic
├── glossaries/
│   ├── glossary.py              # Curated term -> transliteration map
│   └── term_detector.py         # Auto-flags candidate technical terms
├── public/
│   └── index.html               # Review UI
├── requirements.txt
└── README.md
```

## API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | Model loading status |
| `/api/upload` | POST | Upload .xlsx, parse rows, flag candidate terms |
| `/api/process_row` | POST | Run all 3 layers on one row |
| `/api/export` | POST | Write approved rows to a new .xlsx |
| `/api/download/<filename>` | GET | Download the exported file |

## Troubleshooting

**CUDA out of memory with both models loaded**
See "Memory budget" above — lower `MAX_NEW_TOKENS`, close other GPU
programs, or ask for the sequential-loading variant.

**Layer 3 output isn't valid JSON / row shows "Layer 3 output wasn't
valid JSON, falling back to Layer 1+2 result"**
Qwen2.5-7B occasionally wraps its JSON in extra text despite instructions.
The row still shows the Layer 1+2 result (translated + transliterated,
just not structure-repaired) so nothing is lost — re-run that row, or
edit the final fields manually.

**A technical term wasn't transliterated correctly**
It's either not yet in `glossaries/glossary.py` (add it) or wasn't
confirmed in the term-tag list before you ran the pipeline (confirm the
tag, then re-run that row).
