# Colab Training Folder — Ira QLoRA (LFM2.5-1.2B-Thinking, free T4)

> **Self-contained — upload and train.** Zip this folder (`zip -r ira_colab.zip colab/`),
> upload to Colab, unzip, open `00_smoke.ipynb`, run. Everything the notebooks need is
> inside this folder (configs, data, eval prompts, format checker). No repo clone required.
> Optional pre-flight (CPU, runs in seconds): `!python check_data_format.py --jsonl data/identity.jsonl --template configs/chat_template.txt --tokenizer /content/base_model` after smoke C2 — must print `PASS`.

<!--
SEEDS HOWTO (for Dip) — 10 lines, read this first:
1. Persona training is blocked until you write real seeds. File: colab/data/seeds_template.jsonl
2. Shape per line: {"stage":n,"mood":"...","trait":["..."],"user":"...","ira":"..."}
3. stage = 1 (new/awkward), 2 (knows him a bit), 3 (close) — see docs/PERSONA_SPEC.md
4. mood = how Dip feels in that moment (low, playful, venting, good, busy, ...)
5. trait = which Ira behaviour shows (rizz, shy, ragebait, empathy, cry-with, roast)
6. user = what Dip types, in YOUR casual texting style, real lines you'd actually send
7. ira = her reply IN YOUR OWN WORDS — how you want her to sound, not "correct English"
8. Write 60-100 of these. Mix stages and moods. Short replies are GOOD (one-liners too)
9. Save as JSONL (one JSON object per line), send it over — it becomes persona.jsonl
10. Until then 01_train MODE="persona" and MODE="both" will refuse to start. That is on purpose.
-->

## Run Order

```
00_smoke.ipynb  →  01_train.ipynb  →  02_merge_export.ipynb
   (~15 min)        (identity 2K ≈ 1.5-2h)      (~10 min)
```

Full procedure, disconnect protocol and quota math: **`colab/RUNBOOK.md`**.

## Prerequisites

- Google Colab free tier — T4 GPU (Runtime > Change runtime type > T4)
- Google Drive mounted at `/content/drive`
- Repo cloned to `/content/Ira` (or the `colab/` zip uploaded)

## Drive Layout (every artifact that must survive a disconnect)

```
MyDrive/ira/
├── data/
│   ├── identity.jsonl          # copied from colab/data/ (sha-checked)
│   ├── persona.jsonl           # PLACEHOLDER until Dip's seeds arrive
│   ├── ban_strings.txt
│   └── configs/
│       ├── chat_template.txt   # source of truth (sha in header)
│       └── lora_config.json
├── cache/                      # tokenized dataset cache (.arrow)
├── ckpts/
│   ├── checkpoint-500/ ...     # adapter + optimizer + scheduler + rng + meta.json
│   ├── checkpoint-interrupt-N/ # written by the Ctrl+C handler (C15)
│   └── final/
├── logs/
│   ├── loss.jsonl              # loss curve, every 25 steps (C14)
│   └── mid_eval.jsonl          # 20-prompt mid-run eval, every 500 steps (C11)
└── merged/                     # merged HF model from 02_merge_export
```

## Notebook Summary

| Notebook | Purpose | Key settings |
|----------|---------|--------------|
| `00_smoke.ipynb` | Prove the path works in <15 min | 4-bit NF4, LoRA r=8, 10 dummy samples, 20 steps. GATE: loss must drop + adapter save/reload hash match |
| `01_train.ipynb` | Real QLoRA run, resumable | 4-bit NF4, LoRA r=16/alpha=32, seq 1024, eff. batch 16, cosine 2e-4, 2 epochs, mid-eval every 500, OOM guard, early stop, Ctrl+C save |
| `02_merge_export.ipynb` | Merge best adapter → export | fp16 CPU merge, picks best adapter by mid-eval score, sha256 manifest, zip to Drive |

## Critical Rules

1. **Checkpoint or lose everything** — free tier will disconnect you; RESUME=True in 01 C10
2. **Data must pass `colab/check_data_format.py` first** — `!python check_data_format.py --jsonl data/identity.jsonl --template configs/chat_template.txt --tokenizer /content/base_model` must print `PASS` (01_train C5 re-guards this anyway)
3. **Never commit >50MB** — no `.gguf` / `.safetensors` / `.bin`, ever
4. **GGUF conversion is LAPTOP only** — never in Colab
5. **Chat template source of truth** = `colab/configs/chat_template.txt` (never hardcode)
6. Identity SFT makes the model Ira — never names base model, developer or license
