# Identity Verdict: `lfm2.5-thinking:1.2b` (Post-Cleanup)

## A. Served == LFM2.5-1.2B hybrid (16 layers, ~1.17B params)?

**YES.**

**Evidence from `api_show.json` / `model_info`:**
- `general.architecture`: `"lfm2"` (not `llama`)
- `general.parameter_count`: `1170340608` (~1.17B)
- `lfm2.block_count`: `16`
- `lfm2.context_length`: `128000`
- `lfm2.embedding_length`: `2048`
- `lfm2.feed_forward_length`: `12288`
- `lfm2.attention.head_count`: `32`
- `general.file_type`: `15` (Q4_K_M)
- **Tensor inspection** (from `tensors` array): 16 blocks indexed 0–15.
  - **Conv blocks** (have `shortconv.conv.weight`, `shortconv.in_proj.weight`, `shortconv.out_proj.weight`): blk.0, 1, 3, 4, 6, 7, 9, 11, 13, 15 → **10 conv layers**
  - **Attention blocks** (have `attn_q/k/v/output/q_norm/k_norm`): blk.2, 5, 8, 10, 12, 14 → **6 attention layers**
- Quantization: mixed Q4_K / Q6_K per tensor (consistent with Q4_K_M)

This exactly matches the published LFM2.5 1.2B hybrid architecture (10 conv + 6 attention = 16 layers, ~1.17B params).

---

## B. Does served TEMPLATE contain any system paragraph or developer name?

**NONE.**

**Served TEMPLATE (verbatim):**
```
{{ .Prompt }}
```

No embedded system prompt, no developer name, no refusal policy, no "computer science only" instruction.

---

## C. Served blob size + sha256

**FROM digest (from modelfile):**
```
sha256-a7b19185f31650af480c3fa28dd240c75862182e0f30b118dbfadb192e4beb0a
```

**Location:** `/usr/share/ollama/.ollama/models/blobs/sha256-a7b19185f31650af480c3fa28dd240c75862182e0f30b118dbfadb192e4beb0a` (system store — access DENIED)

**Reported size by `ollama list`:** 731 MB

**Local blobs (user store):**
- `sha256-59bb50d8116b6a1f9bfbb940d6bb946a05554e591e30c8c2429ed6c854867ecb` — 3,827,819,904 bytes (3.56 GB) — **deepseek-coder (llama, 32 blocks)**, orphaned
- The served model's blob is **not present in user store** (`~/.ollama/models/blobs/`)

---

## Cleanup Status

| Model | Status |
|-------|--------|
| `lfm2.5-thinking:1.2b` | **KEPT** (served, system store) |
| `deepseek-coder:6.7b` | Manifest exists in `~/.ollama/models/manifests/...` but `ollama rm deepseek-coder` / `ollama rm deepseek-coder:6.7b` both return **"model not found"** — not registered in ollama index. Manifest is stray/orphaned; blobs not removed per rules. |
| `cryptidbleh/gemma4-claude-sonnet-4.6:latest` | Present in `ollama list` — **NOT removed** (task only specified deepseek-coder) |
| `ministral-3:3b` | Present in `ollama list` — **NOT removed** |
| `ben1t0/tiny-llm:latest` | Present in `ollama list` — **NOT removed** |

**Verification:** Served model still replies (tested: "say ok" → response received).