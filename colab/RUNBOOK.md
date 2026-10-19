# RUNBOOK — Ira QLoRA on Colab free T4

## 1. Start a session

Colab UI: **Runtime > Change runtime type > T4 GPU**.
Verify with the GPU name print in C1 — if it says `CUDA FAIL: no GPU visible`,
you are on CPU; fix the runtime and rerun from C1.

## 2. Get the code in

Either:

The folder is **self-contained** — pick one:

- **upload (recommended):** zip this folder (`zip -r ira_colab.zip colab/`), in Colab
  use the file browser to upload it to `/content`, then unzip in a cell:
  `!unzip -q ira_colab.zip -d /content && %cd /content/colab`
- clone (optional): `!git clone <repo-url> /content/Ira && %cd /content/Ira/colab`

Notebooks resolve paths from `cwd` (and its parents) plus `/content/colab` and
`/content/Ira` — running with the notebook's own folder as cwd is the happy path.
Everything needed (configs, data, eval prompts, format checker) is inside `colab/`.

## 3. Run order and expected wall times

| Notebook  | Order | identity 2K   | +persona 6K    |
|-----------|-------|---------------|----------------|
| `00_smoke.ipynb` | first  | ~15 min (incl. 2.4 GB download) | same |
| `01_train.ipynb` | second | **1.5–2 h**   | **+4–5 h** (≈6–7 h total) |
| `02_merge_export.ipynb` | third | ~10 min | ~10 min |

Persona: edit `MODE = "persona"` or `"both"` in 01_train **C4** before running.
It refuses to start while `persona.jsonl` is the placeholder.

## 4. Where every artifact lands

Everything that must survive a disconnect is on **Drive**:

```
/content/drive/MyDrive/ira/
├── data/       identity.jsonl, persona.jsonl, ban_strings.txt, configs/chat_template.txt
├── cache/      tokenized dataset (.arrow, sha-keyed; safe to delete to free Drive space)
├── ckpts/      checkpoint-500/ … : adapter_model.safetensors, adapter_config.json,
│              optimizer.pt, scheduler.pt, rng_state.pth, meta.json; plus final/
├── logs/       loss.jsonl (every 25 steps), mid_eval.jsonl (every 500 steps)
└── merged/     merged fp16 model + manifest.json (sha256 of every file)
```

Laptop download artifact: `/content/drive/MyDrive/ira/ira_merged.zip` (02_merge M6).

## 5. Disconnect protocol

Free tier will disconnect you mid-run. That is fine — the checkpoints are on Drive.

1. Reconnect, set the runtime back to **T4 GPU**
2. Rerun in order: **C1 (pins) → C2 (Drive) → C3 (copy, sha-skip) → C4 (MODE)**
3. C5–C9 re-execute normally (C5 reloads the tokenized cache from Drive)
4. Leave `RESUME = True` in **C10** — it finds the latest `checkpoint-*`, reloads
   adapter + optimizer + scheduler + rng state, prints `resumed at step N`,
   and **verifies the adapter tensor hash matches** before continuing
5. Mid-eval and loss logs append, never overwrite

## 6. Weekly quota math

Colab free ≈ **30 GPU-hours/week** (varies by region and load).

- identity 2K run ≈ 1.5–2 h
- identity + persona ≈ 6–7 h
- → **4 safe full (identity+persona) runs per week**, or ~15 identity-only runs
- Budget one smoke run (~15 min) before each real week of runs

Do not start a run with <2 h of quota left, unless you are deliberately
testing the disconnect path.

## 7. Laptop side, after downloading `ira_merged.zip`

Unzip it, then from a llama.cpp checkout (CPU is fine for a 1.2B):

```bash
python convert_hf_to_gguf.py merged/ --outtype f16 --outfile ira-f16.gguf
llama-quantize ira-f16.gguf ira-Q4_K_M.gguf Q4_K_M
ollama create ira -f models/Modelfile.ira
python scripts/verify_erase.py
```

`scripts/verify_erase.py` is the identity audit — it must pass before the
model goes anywhere near serving.

## 8. SERVING template note (cross-check BEFORE `ollama create`)

The `TEMPLATE` line in `models/Modelfile.ira` is an **Ollama Go-template**.
It must emit **the same special tokens** as the training template in
`colab/configs/chat_template.txt`:

- role markers: `<|im_start|>` / `</|im_end|>` (chat turns)
- think markers: `<think>` … `</think>` around the assistant's reasoning
- BOS: `<|startoftext|>` at the very start of every prompt

If serving any of these is missing or different, the served model will
hallucinate or leak assistant-mechanic voice — fix the Modelfile TEMPLATE
before `ollama create`, then re-run step 7's verify.
