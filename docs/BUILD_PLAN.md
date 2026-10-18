# Ira — Build Plan

Goal: turn `lfm2.5-thinking:1.2b` into **Ira** — a curious, warm, honest personal assistant
that thinks only as much as the question deserves.

Hardware: training on free T4 (Kaggle/Colab) · runtime on GTX 1650 4GB · llama.cpp

---

## The 5 defects we are fixing

| # | Defect | Evidence | Fix route |
|---|--------|----------|-----------|
| 1 | Over-thinking | "hi" → ~120 think tokens; joke → ~600 | SFT think-tiers + runtime router |
| 2 | Rumination loops | "Alternatively… Wait…" repeated 8+ times | SFT + stop-token guard |
| 3 | Stale instruction bleed | "one sentence" leaked into every later turn | Multi-turn SFT with instruction decay |
| 4 | Weak in-context recall | Forgot "Dipjoy" two turns later | **External memory (no training)** |
| 5 | Robotic tone | "Your preference is well understood!" | Persona SFT + DPO |

Order matters: **#4 and the latency half of #1 need no training.** Do those first.

---

## Phase 0 — Verify the arch trains (BLOCKER)

Hybrid conv+GQA architecture. QLoRA support is **unconfirmed**. Everything else is
wasted if this fails.

- [ ] Colab free T4, 10-sample dataset
- [ ] Install: `torch`, `transformers`, `trl`, `peft`, `bitsandbytes`, `unsloth` (try both)
- [ ] Load base 4-bit, attach LoRA r=8, run 20 steps
- [ ] Confirm: loss decreases, no arch error, checkpoint saves, model loads back

**GATE:** if it errors or needs unsupported custom code → stop, switch base to
`granite4.2:3b` or `qwen3.5:2b`. Do not fight this.

Notes:
- T4 has **no bf16** → use `fp16=True`
- Enable `gradient_checkpointing` + 8-bit AdamW + paged optimizer to fit 16GB

---

## Phase 1 — Eval baseline (before touching weights)

You cannot improve what you do not measure.

- [ ] Write `eval/prompts.jsonl` — 200 prompts across 10 categories
- [ ] Categories: trivial, math, multi-step, code-gen, code-debug, tool-JSON,
      tone-formal, tone-casual, tone-emotional, instruction-following,
      hallucination, multi-turn recall
- [ ] Script must use the **real chat API with message roles**, never string concat
      (this bug invalidated the first run)
- [ ] Save per test: full response text, think-token count, answer-token count,
      TTFT, tok/s, VRAM, device
- [ ] Lock one device config and record it
- [ ] Store baseline as `eval/runs/00_baseline.json`

**GATE:** baseline exists and is reproducible before any training.

---

## Phase 2 — No-training fixes (biggest felt win, ~70%)

### 2a. Memory layer — fixes defect #4 permanently
Model attention is unreliable at 1.2B. Do not ask it to remember. Hand it the facts.

- [ ] SQLite file, 3 tables:
  - `messages(id, ts, role, text)` — raw log, FTS5 index
  - `memory(id, kind, key, value, ts)` — distilled facts + rolling summaries
  - `vec(id, chunk_id, embedding)` — `sqlite-vec`, 256-dim
- [ ] Every turn: extract entities (names, people, preferences, dates, tasks)
      → upsert into `memory`
- [ ] Every turn: inject a **≤5-line recap** into the system prompt
      (name, key people, active preferences, current task)
- [ ] When history > threshold → summarise old turns into `memory`, drop from context
- [ ] Decide now: encrypt the DB or accept plaintext

Result: it never has to *find* a fact. Recall stops being a model problem.

### 2b. Think-budget router — fixes defect #1 latency
- [ ] Tiny classifier on **CPU** (`d1-omni 600m` or a regex+length heuristic first)
- [ ] Tiers: `fast` (0 think tokens) · `mid` (~60) · `deep` (~300)
- [ ] Sets `/no_think` vs `/think` + `num_predict` cap before the main model runs
- [ ] Start with the heuristic. Upgrade to the model only if it misroutes.

### 2c. Runtime guards
- [ ] Stop-token on runaway patterns (`Alternatively`, repeated `Wait`)
- [ ] KV / prompt-cache reuse across turns — stop reprocessing full history
- [ ] Streaming output
- [ ] `-ngl 99`, flash-attn, q8_0 KV, context capped at 4–8K

### 2d. Tools
- [ ] Calculator + Python exec via **GBNF grammar** so JSON cannot malformed
- [ ] Sandbox: allowlist, timeout, no network by default
- [ ] Math goes to the tool, never to the weights. 40% → 99% accuracy.

### 2e. RAG — how knowledge gets added later
- [ ] `bge-m3 567m` or `embeddinggemma-2:270m`, **on CPU**, 256-dim
- [ ] Chunk 512 tokens, 50 overlap
- [ ] Coding JSONL, GK notes, anything you feed later → index, not weights
- [ ] Fact: fine-tuning is *bad* at storing facts and raises hallucination.
      RAG is the right channel for knowledge.

**GATE:** re-run Phase 1 eval. Recall and latency should already be fixed.

---

## Phase 3 — Training data

Target **25–30K samples, under 50MB**. At 1.2B, 30K clean beats 300K noisy.
Start with **6–8K** to validate the pipeline inside one free-tier session, then scale.

| Subset | Count | Fixes |
|---|---|---|
| Think-length tiers (trivial=0, mid=60, deep=300) | 8K | #1 #2 |
| Core assistant chat | 6K | baseline competence |
| Persona / warm tone | 4K | #5 |
| Tool-call JSON | 4K | tools |
| Instruction decay (multi-turn) | 3K | #3 |
| Emotion: state → adapted response | 2.5K | #5 |
| GK / teaching style | 2K | your use case |

Build rules:
- **Reject-sample everything**: generate 5 candidates, keep the shortest correct one
- Enforce hard token caps on the `<think>` block in the labels — the cap *is* the lesson
- Instruction-decay format: turn N sets a constraint, turn N+2 asks an open question,
  correct answer is open and long
- Emotion data = **behaviour, not knowledge**. Label user state, then adapt tone/length.
  Keep it under 2.5K or the model becomes a caricature
- Deduplicate hard. Near-dupes cause drift.
- Format must match the base chat template **exactly** — mismatch is the #1 GGUF failure
- No refusal-filtering data; keep plain assistant data mixed in so instruction-following
  doesn't degrade

Your existing assets: coding JSONL ✅ GK ✅
Missing and must build: day-to-day assistant chat, tool-call examples, emotion, decay.

---

## Phase 4 — QLoRA SFT

- Kaggle (30 h/week, 2× T4) primary · Colab free for debugging · Vast.ai ~$3 if blocked
- 4-bit base, LoRA r=16–32, alpha 2×r, dropout 0.05
- seq 2048, fp16, grad accumulation to effective batch 16–32
- lr 2e-4 cosine, warmup 3%, **2–3 epochs only**
- **Checkpoint every 500 steps + resume.** Free tiers will disconnect you.
- Log loss + a held-out 200-sample eval every 500 steps
- Watch for collapse: if eval degrades while loss drops → stop, roll back

---

## Phase 5 — DPO (tone + brevity)

After SFT, not instead of it.
- Pairs: chosen = short + warm + correct · rejected = long + robotic + padded
- ~3–5K pairs, beta 0.1, 1 epoch, lr 5e-6
- This is what kills the emoji-padding and the "well understood!" register

---

## Phase 6 — Export + rebrand

- [ ] Merge LoRA → full HF weights
- [ ] `convert_hf_to_gguf.py`
- [ ] Quantise **Q4_K_M** (≈800MB)
- [ ] Rewrite GGUF metadata: name, author, description → yours
- [ ] Identity SFT already in the data: it is **Ira**, never the base model or its maker
- [ ] Custom system prompt + chat template
- [ ] **Re-run the full eval on the quantised model** — quantising shifts personality

Replaceable: identity, tone, template, metadata, all output references.
Not replaceable: tokenizer/vocab 65,536, arch fingerprint (10 conv + 6 GQA),
weight similarity to base. A fine-tune cannot pass as scratch-built — the tensors
identify it regardless of metadata. Keep a private note of the base for yourself.

---

## Phase 7 — Runtime assembly

```
user input
   → router (CPU)      : think tier
   → memory recap      : SQLite inject
   → RAG retrieve      : bge-m3 CPU, 256d, top-K
   → Ira (GPU, Q4)     : llama.cpp, grammar-constrained tools
   → memory write      : entities + message log
```

- llama.cpp server, `0.0.0.0`, streaming
- Tool sandbox enforced
- Everything on one laptop: model GPU, embeddings + router CPU

---

## Phase 8 — Regression loop

Every change, no exceptions:
1. Run the 200-prompt eval
2. Diff against previous run — per-category, not just aggregate
3. Record think-token median per tier
4. Ship only if no category regressed >10%

Keep every eval run in `eval/runs/`. Version the adapters and the memory DB schema.

---

## Immediate next actions

1. **Phase 0 smoke test** — 10 samples, confirm QLoRA works on this arch
2. **Phase 1 eval harness** — 200 prompts, correct chat API
3. **Phase 2a memory DB** — fixes recall with zero training

Do these three before writing a single training sample.
