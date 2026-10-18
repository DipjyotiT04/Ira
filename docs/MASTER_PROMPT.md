# MASTER PROMPT — Ira local build

Paste this entire block to a coding agent working in the Ira repository.

---

You are building the local side of **Ira**, a fine-tune of `lfm2.5-thinking:1.2b`.
Work only inside this repository. GPU training happens later on Colab — do NOT
attempt any training here. Everything you do here must run on CPU.

Follow every section in order. If a step fails, record the exact error in
`docs/STATUS.md`, mark it FAILED, and continue with the next section.
Never silently skip. Never invent results.

## 1. Workspace layout
Create exactly:
```
models/            # gguf files, NEVER committed
data/raw/          # user's source jsonl
data/sft/          # split training subsets
data/dpo/          # preference pairs
scripts/
eval/
eval/runs/
memory/
docs/
```
Add to `.gitignore`: `models/`, `*.gguf`, `*.safetensors`, `*.bin`,
`data/raw/`, `memory/*.db`, `__pycache__/`, `outputs/`.
Commit only code, configs, and small generated datasets (<50MB).

## 2. Save the model
- If `ollama` exists: `ollama pull lfm2.5-thinking:1.2b` if absent.
- Locate the blob (`ollama show --modelfile` or `~/.ollama/models/blobs`),
  copy it to `models/lfm2.5-thinking-q4.gguf`.
- If ollama is missing: download the GGUF from the official release source
  instead and say which one you used.
- Record sha256 + byte size in `models/CHECKSUMS.txt`.
- Dump ALL GGUF metadata to `models/metadata_original.json` using a pure-python
  gguf reader (no torch needed). This is a private provenance record.
  Never publish it, never claim the model is scratch-built.

## 3. Model fact sheet
Write `docs/model_facts.md`: architecture layers (conv vs attention counts),
vocab size, context, quant, parameter count, license text you found, sha256.
Flag anything you could not verify as UNVERIFIED.

## 4. Ingest + organise user data
- Ingest every jsonl the user provides into `data/raw/` (coding, GK, etc).
- Validate: every line parses, has role/content fields. Count malformed lines.
- Exact-dedupe + minhash near-dedupe (threshold 0.9). Report before/after counts.
- Write `data/stats.json`: per-source counts, token estimate, dedupe loss.
- Do NOT split into training subsets yet. Just clean + report.

## 5. Local build assets (no GPU needed)
- `data/sft/ban_strings.txt` — every string that must never appear in output:
  base model names, developer names, "as an AI", their casing variants.
  Start with: Liquid AI, LFM2, LFM, lfm2.5-thinking. Agent: extend with variants.
- `scripts/gen_identity_data.py` — generates ~2000 SFT samples teaching:
  name is Ira; never names a base model or company; deflects identity probes
  naturally (not robotically); keeps the user's persona warm and curious.
  Output `data/sft/identity.jsonl` in the base model's EXACT chat format.
- `scripts/chat_template.txt` — the base template, copied verbatim from the
  GGUF metadata. Add a comment showing where ``-style or equivalent
  markers sit. Mismatch here breaks everything later.
- `docs/system_prompt.md` — Ira's system prompt: identity, tone (warm, curious,
  playful, honest), brevity rules, no emoji unless user uses one first,
  empathy-before-advice rule, `heat` dial 0-3 for teasing with the hard gate:
  never when user state is sad/stressed/angry/venting.
- `models/Modelfile.ira` — FROM ira-q4.gguf + SYSTEM (inline the system prompt)
  + TEMPLATE (inline the chat template) + PARAMETER temperature 0.8,
  num_ctx 8192.

## 6. Eval harness
- `eval/prompts.jsonl` — 200 prompts, ~20 per category: trivial, simple-math,
  multi-step-math, code-gen, code-debug, tool-json, tone-formal, tone-casual,
  tone-emotional, instruction-follow, hallucination, multi-turn-recall,
  identity-probe (who are you / who made you / what model are you).
- `eval/run_eval.py` — calls the LOCAL ollama chat API using real message
  roles (never string concatenation). Records: full response text, think-token
  count (text between the think tags), answer-token count, TTFT, tok/s, device,
  model tag, timestamp. Writes `eval/runs/<n>_<tag>.json`.
- Run it NOW against `lfm2.5-thinking:1.2b` → `eval/runs/00_baseline.json`.
- Print a category summary table.

## 7. Memory layer
- `memory/ira_memory.py` — SQLite, 3 tables:
  `messages(id, ts, role, text)`, `memory(id, kind, key, value, ts)`,
  `vec(id, chunk_id, embedding)`. FTS5 index on messages.
  Functions: `log_turn()`, `extract_entities()` (names, people, preferences,
  dates, tasks — regex+rules, no model), `upsert_memory()`,
  `build_recap()` (<=5 lines), `summarise_old()`.
- `memory/test_memory.py` — proves: recap contains a fact added 5 turns ago,
  and survives a process restart. Must pass.

## 8. RAG index builder
- `scripts/build_index.py` — chunks text at 512 tokens / 50 overlap, embeds
  with `bge-m3` or `embeddinggemma-2:270m` via ollama ON CPU, truncates to
  256 dims, stores in the `vec` table. Idempotent: re-running skips known chunks.
- Run it over `data/raw/`. Report chunk + vector counts.

## 9. Export pipeline (scripts only — run AFTER Colab training)
- `scripts/merge_lora.py` — merge adapter into base, save HF dir.
- `scripts/convert_to_gguf.sh` — llama.cpp convert, pinned version noted.
- `scripts/quantize.sh` — Q4_K_M output `models/ira-q4.gguf`.
- `scripts/rewrite_metadata.py` — rewrite every `general.*` key:
  name, author, description, license-source, urls → the user's values from
  `docs/rebrand_values.json` (create it with placeholders for user to fill).
  Must NOT touch tensors. Verify sha of tensor block unchanged.
- `scripts/make_ollama.sh` — `ollama create ira -f models/Modelfile.ira`.
- `scripts/verify_erase.py` — asks the 3 identity probes + 20 random prompts,
  greps every output against `ban_strings.txt`. PASS = zero hits and identity
  answers say only Ira. Writes `eval/runs/erase_check_<date>.json`.

## 10. Colab notebook skeleton
- `scripts/colab_train.ipynb` — mounts Drive; loads base 4-bit; LoRA r=16 a=32
  dropout .05; fp16 (T4 has no bf16); gradient checkpointing; 8-bit AdamW;
  sequence packing; seq 1024 first run; cosine lr 2e-4 warmup 3%; 2 epochs;
  checkpoint adapter to Drive every 500 steps AND on KeyboardInterrupt;
  resume flag `--resume <dir>`; saves loss curve json.
- Must contain a 10-sample SMOKE cell at the top that runs before real data.

## Rules
- No GPU training here. No torch install unless a script truly needs it.
- Never commit anything >50MB. Never commit the GGUF.
- Keep `models/metadata_original.json` private; do not reference provenance
  in any public-facing file.
- Every script: standalone, idempotent, `--help`, clear exit codes.
- Log progress to `docs/STATUS.md` as you go: DONE / FAILED / SKIPPED per step.

## Final output
Print: workspace tree, `docs/STATUS.md` content, the baseline eval summary,
memory test result, and the list of items still needing the user
(rebrand values, data files, phone-free GPU choice).
