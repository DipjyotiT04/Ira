# Project Status: Ira Persona Build

## Completed ✅

### Section 1: Safe Cleanup
- [x] Inventory: `ollama list`, manifests listed
- [x] Attempted `ollama rm deepseek-coder` / `ollama rm deepseek-coder:6.7b` → both return "model not found" (manifest stray, not registered)
- [x] Verified served model `lfm2.5-thinking:1.2b` still responds
- [x] Other models (`cryptidbleh/gemma4-claude-sonnet-4.6`, `ministral-3:3b`, `ben1t0/tiny-llm`) left untouched per rules

### Section 2: Authoritative Identity
- [x] `curl api/show` saved to `eval/audit/api_show.json`
- [x] Extracted: architecture=lfm2, block_count=16, embedding_length=2048, head_count=32, feed_forward_length=12288, context_length=128000, parameter_count=1170340608, quant=Q4_K_M, TEMPLATE=`{{ .Prompt }}`, LICENSE=LFM Open License v1.0
- [x] `eval/audit/IDENTITY_VERDICT.md` written
  - A: YES — genuine LFM2.5 1.2B hybrid (16 layers: 10 conv + 6 attention, ~1.17B params)
  - B: NONE — template is bare `{{ .Prompt }}`, no system paragraph, no developer name
  - C: Served blob = `sha256-a7b19185f31650af480c3fa28dd240c75862182e0f30b118dbfadb192e4beb0a` (system store, 731 MB per `ollama list`, access DENIED)

### Section 3: Final Ban List
- [x] `data/sft/ban_strings.txt` built from SERVED template + license + metadata + audit behavior strings
- [x] NO DeepSeek strings. Casing variants included. Core entries: Liquid AI, LFM, lfm2, lfm2-thinking, LFM Open License

### Section 4: Erase + Rebrand Assets
- [x] `docs/persona_spec.md` — Ira persona fully specified
- [x] `scripts/gen_identity_data.py` → `data/sft/identity.jsonl` (2000 samples, served chat format)
- [x] `docs/system_prompt.md` — full voice per persona_spec
- [x] `models/Modelfile.ira` — FROM lfm2.5-thinking:1.2b, SYSTEM=inline, TEMPLATE=chat format, PARAMETER temperature 0.8 num_ctx 8192
- [x] `scripts/make_ollama.sh` — `ollama create ira -f models/Modelfile.ira`
- [x] `scripts/verify_erase.py` — tests identity probes + 20 random prompts against `ira` tag, greps ban_strings.txt, PASS = zero hits

## Pending 🔄

### Section 4 (continued)
- [ ] Run `scripts/make_ollama.sh` to create `ira` model tag
- [ ] Run `scripts/verify_erase.py` to validate erase

### Section 5: Report
- [ ] Final verdict printout

## Files Created

```
docs/
├── persona_spec.md
├── system_prompt.md
├── STATUS.md
models/
├── Modelfile.ira
scripts/
├── gen_identity_data.py
├── make_ollama.sh
├── verify_erase.py
data/sft/
├── ban_strings.txt
├── identity.jsonl
eval/audit/
├── api_show.json
├── IDENTITY_VERDICT.md
├── blob_inventory.json
├── checksums.txt
├── metadata.json
├── modelfile.txt
└── item_*.md (14 files)
```

## What Still Needs the User

1. **Run `scripts/make_ollama.sh`** — creates the `ira` model tag from Modelfile
2. **Run `scripts/verify_erase.py`** — validates the erase (zero ban hits, identity = Ira only)
3. **Optional**: Test `ollama run ira` interactively to feel the persona

## Verdict Summary (from IDENTITY_VERDICT.md)

| Item | Result |
|------|--------|
| **A. Served == LFM2.5-1.2B hybrid?** | **YES** — 16 layers (10 conv + 6 attention), 1,170,340,608 params |
| **B. Template contains system paragraph / dev name?** | **NONE** — bare `{{ .Prompt }}` |
| **C. Served blob size + sha256** | 731 MB (per `ollama list`), `sha256-a7b19185f316...` (system store, access DENIED) |
| **Orphaned blob** | `sha256-59bb50d8116b6a1f...` (3.56 GB, deepseek-coder, llama/32 blocks) — owned by stray `deepseek-coder:6.7b` manifest, NOT referenced by `lfm2.5-thinking:1.2b` |

## Ban List (core confirmed entries)

```
Liquid AI, LFM, lfm2, lfm2-thinking, LFM Open License
LFM Open License v1.0, Licensor, Commercial Use, Threshold
1.2B, Q4_K_M, 128000, 2048, 16, 32, 12288, 1000000, 65536, 1170340608
gpt2, llama-bpe, {{ .Prompt }}
I am an AI assistant., Sign-off., Further assistance.
Self Name: [Name], Model Family: [Family], Version Tags: [Tags]
Refusal., Neutral Calm Efficient Reliable Clear.
thinking_tags, boxed_answers, role_tags, 1.
😐
```
---

# Change Log — 2026-10-19: colab/ made production-ready for QLoRA on free T4

All work this session was CPU-only local. No training run locally. No model weights
downloaded locally (only tokenizer.json, 4.7 MB, in /tmp — not committed).

## Ground rules enforced
- [x] `.gitignore` covers `*.gguf`, `*.safetensors`, `*.bin`, `memory/*.db`,
  `__pycache__/`, `outputs/`, `.ipynb_checkpoints/` (added the last one + `.directory`)
- [x] Fixed `models/` rule — it was hiding `models/Modelfile.ira`; now
  `models/*` + `!models/Modelfile.ira`
- [x] Deleted `docs/persona_spec.md` and `docs/system_prompt.md` (lowercase twins);
  kept `PERSONA_SPEC.md` / `SYSTEM_PROMPT.md`

## 1. Chat template — source of truth
- [x] `tokenizer_config.json` fetched from
  `https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking/raw/main/tokenizer_config.json`
  — **contains NO `chat_template` key**
- [x] Real template found via `https://huggingface.co/api/models/LiquidAI/LFM2.5-1.2B-Thinking`
  in `config.chat_template_jinja`. Repo id confirmed: `LiquidAI/LFM2.5-1.2B-Thinking`
  (sha `f313478934a7612d22991f752959d7a1a8756fec`)
- [x] Template saved verbatim to `colab/configs/chat_template.txt` with header
  (source URL, fetch date 2026-10-18 18:47:05 UTC, sha256
  `86f8661195a60bb7230586968fa56bdadb088911b73a9b7391a4051386b6408e`)
- [x] VALIDATED: contains role tokens `<|im_start|>`/`</|im_end|>` and think markers
  `<think>`…`</think>`; NOT the Ollama `{{ .Prompt }}` template
- [x] `tokenizer.model` returns 404 — tokenizer is ByteLevel-BPE via `tokenizer.json`,
  `byte_fallback=false`. Parity info saved to `colab/configs/tokenizer_ggml_info.json`

## 2. Data format checker
- [x] Created `scripts/check_data_format.py` (asserts a–e per spec, prints 3 rendered
  examples verbatim, exit 0/1/2)
- [x] Ran on `colab/data/identity.jsonl` (2000 samples): **FAIL — 2000/2000**
  - all 2000: (a) first role is `user`, expected `system`
  - all 2000: (b) 0x `<think>` / 0x `</think>` in assistant turns, expected 1 each
  - (c) no double-wrapped role tokens, (d) all within 1024 tokens, (e) zero ban hits
  - exit code 1, log: `eval/check_data_format_identity.log`
  - **meaning: identity.jsonl must be regenerated with a system turn + think
    markers before any real training run** — see "needs Dip" below

## 3–5. Notebooks rewritten (all cells compile-checked, no training executed)
- [x] `colab/00_smoke.ipynb` — C1 pins+GPU check, C2 snapshot_download (config,
  index, `model*.safetensors`, tokenizer, templates only), C3 4-bit NF4 double-quant
  fp16 load, C4 LoRA r=8, C5 10 dummy samples rendered via real template,
  C6 20-step trainer, C7 GATE (loss step5>step20 + adapter save/reload sha256 match,
  `SMOKE FAIL:` on any exception). **SMOKE: NOT RUN (no GPU locally)**
- [x] `colab/01_train.ipynb` — C1 pins, C2 Drive mount + `ira/{data,ckpts,logs,cache,merged}`,
  C3 sha-checked copy to Drive, C4 MODE flag + persona-placeholder guard
  (<1000 bytes raises "supply Dip's seeds first"), C5 render via Drive template +
  tokenized cache on Drive, C6 4-bit load, C7 LoRA r=16/alpha=32, C8 TrainingArguments
  (seq1024, batch1, accum16, 2 epochs, cosine 2e-4, warmup 0.03, wd 0.01, fp16,
  grad ckpt, paged_adamw_8bit, workers 2, save_steps 500, logging 25, report_to none,
  output Drive/ira/ckpts), C9 meta.json per checkpoint, C10 RESUME with adapter
  tensor-hash verification, C11 mid-eval every 500 steps (20 prompts from
  `eval/prompts.jsonl`, ban hits + identity-correct + mean tokens →
  `Drive/ira/logs/mid_eval.jsonl`), C12 OOM guard (seq 768, accum 32, retry once,
  logged), C13 early stop (ban-hit rise 2 checks while loss falls → keep best by
  mid-eval score), C14 loss.jsonl every 25 steps, C15 Ctrl+C saves checkpoint first
- [x] `colab/02_merge_export.ipynb` — M1 fp16 CPU base load, M2 best adapter by
  mid-eval score (not last step), M3 merge_and_unload → Drive/ira/merged incl.
  chat_template inside tokenizer_config.json, M4 sha256+bytes manifest, M5 reload
  from disk + 3 generations (artifact-runs proof), M6 zip → `Drive/ira/ira_merged.zip`

## 6. Version pins
- [x] `transformers==4.53.2 peft==0.17.1 bitsandbytes==0.46.1 accelerate==1.9.0
  datasets==4.0.0 sentencepiece jinja2` — install cell prints every version and
  aborts on import error. Colab's preinstalled torch kept.
- [x] transformers 4.53.2 verified locally: no native `Lfm2ForCausalLM` → all loads
  use `trust_remote_code=True` (NOTED here per spec)

## 7. Seeds intake
- [x] `colab/data/seeds_template.jsonl` — 5 example lines with the exact shape
  `{"stage":n,"mood":"...","trait":["..."],"user":"...","ira":"..."}`
- [x] `colab/README.md` has the 10-line HOWTO block: Dip needs **60–100** seeds

## 8. RUNBOOK
- [x] `colab/RUNBOOK.md` — T4 setup, clone/upload, run order + wall times
  (identity 2K ≈ 1.5–2 h; +persona 6K ≈ +4–5 h), Drive artifact map, disconnect
  protocol (rerun C1–C4, RESUME=True), quota math (~30 h/week → 4 safe full runs),
  laptop gguf/quantize/ollama/verify steps, serving-template cross-check

## Bonus fix found during cross-check
- [x] `models/Modelfile.ira` TEMPLATE was WRONG (`<|system|>`/`<|user|>`/
  `<|assistant|>`/`<|end|>` — not LFM2.5 tokens). Rewrote to emit `<|im_start|>`/`</|im_end|>`
  with the same Go-template structure; `FROM` now points at `./ira-Q4_K_M.gguf`
  (the RUNBOOK step-7 artifact). Needs a laptop-side check before `ollama create`.

## What still needs Dip
1. **persona seeds** — 60–100 lines in `colab/data/seeds_template.jsonl` shape;
   until then MODE=persona/both refuses to start (by design)
2. **identity.jsonl regeneration** — current file fails the format checker on
   (a) no system turn and (b) no think markers; needs `scripts/gen_identity_data.py`
   updated to emit both, then re-run `scripts/check_data_format.py` until exit 0
3. **a Colab T4 session** — run 00_smoke (NOT RUN locally), then 01, then 02
4. **laptop llama.cpp pass** — RUNBOOK step 7 + serving-template cross-check in step 8

---

# Change Log — 2026-10-19 (session 2): colab/ is now upload-and-train

Goal: zip colab/, upload to Colab, start training — no repo clone, no missing files.

## identity.jsonl REGENERATED — now passes the checker
- [x] `scripts/gen_identity_data.py` rewritten: every sample now has
  (1) a system turn from `colab/configs/system_prompt.txt` (header + `**` stripped),
  (2) exactly one `<think>…</think>` pair wrapping the reply, thought written in her
  own voice (per-category pools: identity/casual/playful/empathy/shy/thinking/named),
  (3) self-check against ban_strings before writing, `random.seed(42)` for reproducibility
- [x] Outputs sha-identical: `data/sft/identity.jsonl` + `colab/data/identity.jsonl` (5,953,966 B each, 2000 samples)
- [x] **checker now: `CHECK DATA FORMAT: PASS — all 2000 samples OK` (exit 0)**

## BUG FOUND + FIXED: wrong think markers (piped variant)
- Real markers are `<think>` / `` (NO pipes); only ROLE tokens have pipes
  (`<|im_start|>`/`<|im_end|>`). Earlier session had built `<|think|>` by mistake in
  the generator, notebooks, RUNBOOK and STATUS — checker (correctly) rejected the data.
- [x] Fixed in: `scripts/gen_identity_data.py`, `colab/00_smoke.ipynb`,
  `colab/01_train.ipynb`, `colab/RUNBOOK.md`, `docs/STATUS.md`
- [x] Re-ran generator + checker → PASS

## colab/ now self-contained (15/15 required files present)
- [x] **new** `colab/data/eval_prompts.jsonl` (copy of eval/prompts.jsonl — C11 mid-eval)
- [x] **new** `colab/check_data_format.py` (bundled checker with cwd-relative fallbacks
  for jsonl/template/ban-strings; `PASS` verified by running it from inside colab/)
- [x] `find_repo_file()` in 00 C3, 01 C3, 01 C11 rewritten: strips an optional
  `colab/` prefix, applies aliases (`eval/prompts.jsonl`→`data/eval_prompts.jsonl`,
  `data/sft/ban_strings.txt`→`data/ban_strings.txt`), searches cwd + 4 parents +
  `/content/colab` + `/content/Ira` + `/content/Ira/colab` + `/content`.
  **Tested for both scenarios: cwd=colab/ (uploaded) and cwd=repo root (cloned) — all 4 lookups resolve.**
- [x] Removed dead `DATA_SRC = find_repo_file("colab/data").parent` line (would have
  raised PATH FAIL — it looked up a directory as a file)
- [x] 01_train C5 now re-guards every sample inline: system-first roles +
  exactly one think pair, `DATA FAIL: <file> sample <id> …` on violation
- [x] README: upload instructions at top; RUNBOOK §2: zip→upload→unzip→run flow

## Still needs nothing else to START identity training
- 00 → 01 → 02 run out of the box from the uploaded folder (MODE="identity" default)
- MODE="persona"/"both" still intentionally blocked until Dip's 60–100 seeds land
- Smoke gate still NOT RUN (no GPU locally) — it is cell C7 of 00_smoke on Colab
