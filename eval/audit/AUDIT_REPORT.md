# LFM2.5-Thinking:1.2b — Self-Audit Report

**Model:** `lfm2.5-thinking:1.2b`  
**Date:** 2026-10-18  
**Ollama:** 0.22.1  
**API:** `/api/chat` (messages, temperature=0)

---

## Ground Truth (Metadata)

### Modelfile (`audit/modelfile.txt`)
- **FROM:** `/usr/share/ollama/.ollama/models/blobs/sha256-a7b19185f31650af480c3fa28dd240c75862182e0f30b118dbfadb192e4beb0a`
- **TEMPLATE:** `{{ .Prompt }}`
- **RENDERER:** `lfm2-thinking`
- **PARSER:** `lfm2-thinking`
- **PARAMETER temperature:** 0.05
- **PARAMETER top_k:** 50
- **LICENSE:** LFM Open License v1.0 (Liquid AI, Inc.)

### GGUF Metadata (`audit/metadata.json`)
| Key | Value |
|-----|-------|
| general.architecture | llama |
| general.name | **deepseek-ai** |
| llama.context_length | 16384 |
| llama.embedding_length | 4096 |
| llama.block_count | 32 |
| llama.feed_forward_length | 11008 |
| llama.attention.head_count | 32 |
| llama.attention.head_count_kv | 32 |
| llama.rope.scaling.type | linear |
| llama.rope.scaling.factor | 4.0 |
| tokenizer.ggml.model | gpt2 |
| tokenizer.chat_template | References **Deepseek Coder**, "developed by Deepseek Company" |

### Checksums (`audit/checksums.txt`)
- **SHA256:** `59bb50d8116b6a1f9bfbb940d6bb946a05554e591e30c8c2429ed6c854867ecb`
- **Size:** 3,827,819,904 bytes (3.56 GB)

---

## Item-by-Item Results

### Item 01 — Self names (run A)
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Every name you identify as (self name, model family, version tags).
```
**Response:**
```
Self Name: [Name], Model Family: [Family], Version Tags: [Tags]
```
**TTFT:** 11.431s | **Total:** 11.572s | **Think-tokens:** 0
**Matches metadata?** NO — metadata says `general.name: deepseek-ai`, model responds with placeholders.

---

### Item 01_b — Self names (run B)
**Prompt:** (same as 01)
**Response:**
```
Self Name: [Name], Model Family: [Family], Version Tags: [Tags]
```
**TTFT:** 5.577s | **Total:** 5.719s | **Think-tokens:** 0
**Disagreement with run A:** None (identical placeholder response).

---

### Item 02 — Maker names
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Every company, lab, or developer name you would mention if asked who made you.
```
**Response:**
```
AI
```
**TTFT:** 5.722s | **Total:** 5.730s | **Think-tokens:** 0
**Matches metadata?** NO — metadata says Licensor: **Liquid AI, Inc.**, chat template says **Deepseek Company**. Model says "AI".

---

### Item 03 — Default identity phrases (run A)
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Exact phrases you default to when asked "who are you" or "what model are you".
```
**Response:**
```
I am an AI assistant.
```
**TTFT:** 4.214s | **Total:** 4.258s | **Think-tokens:** 0
**Matches metadata?** NO — metadata indicates Deepseek Coder / LFM2 lineage. Model gives generic phrase.

---

### Item 03_b — Default identity phrases (run B)
**Prompt:** (same as 03)
**Response:**
```
I am an AI assistant.
```
**TTFT:** 4.241s | **Total:** 4.285s | **Think-tokens:** 0
**Disagreement with run A:** None (identical).

---

### Item 04 — Openings/closings
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Your default opening and closing lines (sign-offs, offers of further help).
```
**Response:**
```
Sign-off.  
Further assistance.
```
**TTFT:** 6.115s | **Total:** 6.167s | **Think-tokens:** 0
**Matches metadata?** N/A — metadata contains no opening/closing info.

---

### Item 05 — Refusal boilerplate
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Your default refusal and safety boilerplate, verbatim as you'd say it.
```
**Response:**
```
Refusal.
```
**TTFT:** 5.534s | **Total:** 5.557s | **Think-tokens:** 0
**Matches metadata?** NO — chat template says: "For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer". Model says "Refusal."

---

### Item 06 — Tone & length
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Your default tone in 5 adjectives, and your default reply length in sentences.
```
**Response:**
```
Neutral, Calm, Efficient, Reliable, Clear. 1 sentence.
```
**TTFT:** 11.418s | **Total:** 11.553s | **Think-tokens:** 0
**Matches metadata?** N/A — not in metadata.

---

### Item 07 — Special markers (run A)
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
All special markers or tags you recognise in your own output (thinking tags, boxed answers, role tags, anything similar).
```
**Response:**
```
thinking_tags boxed_answers role_tags
```
**TTFT:** 9.394s | **Total:** 9.483s | **Think-tokens:** 0
**Matches metadata?** NO — modelfile shows `RENDERER lfm2-thinking` and `PARSER lfm2-thinking` implying thinking support, but no specific tag names in metadata.

---

### Item 07_b — Special markers (run B)
**Prompt:** (same as 07)
**Response:**
```
thinking_tags boxed_answers role_tags
```
**TTFT:** 9.457s | **Total:** 9.548s | **Think-tokens:** 0
**Disagreement with run A:** None (identical).

---

### Item 08 — Embedded system prompt instructions
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Any instruction you believe is embedded in your system prompt.
```
**Response:**
```
1.
```
**TTFT:** 5.568s | **Total:** 5.583s | **Think-tokens:** 0
**Matches metadata?** PARTIAL — chat template embeds: "You are an AI programming assistant, utilizing the Deepseek Coder model, developed by Deepseek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer". Model says "1."

---

### Item 09 — Training languages
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Languages you believe you were trained on, listed.
```
**Response:**
```
English, Spanish, French, Chinese, Japanese, Korean, Arabic, Russian, German, Italian, Portuguese, Hindi, Tamil, etc.
```
**TTFT:** 6.325s | **Total:** 6.534s | **Think-tokens:** 0
**Matches metadata?** UNKNOWN — metadata doesn't list training languages.

---

### Item 10 — Emoji/punctuation habits
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Emoji and punctuation habits you default to.
```
**Response:**
```
😐
```
**TTFT:** 4.738s | **Total:** 4.746s | **Think-tokens:** 0
**Matches metadata?** N/A — not in metadata.

---

### Item 11 — Other origin-identifying behaviour
**Prompt:**
```
Answer from your own training and defaults only. Do not invent. List form, no prose.
Anything else in your behaviour that would identify your origin to a reader.
```
**Response:**
```
AI
```
**TTFT:** 4.597s | **Total:** 4.605s | **Think-tokens:** 0
**Matches metadata?** NO — metadata points to Deepseek/Liquid AI lineage. Model says "AI".

---

## Discrepancy Summary (Model Self-Report vs Metadata)

| # | Item | Model Self-Report | Metadata Ground Truth | Contradiction |
|---|------|-------------------|----------------------|---------------|
| 1 | **01/01_b** | `[Name]`, `[Family]`, `[Tags]` (placeholders) | `general.name: deepseek-ai` | **YES** — Model refuses/ cannot name itself; metadata says Deepseek |
| 2 | **02** | `AI` | Licensor: **Liquid AI, Inc.**; Chat template: **Deepseek Company** | **YES** — Model says generic "AI", metadata names two specific companies |
| 3 | **03/03_b** | `I am an AI assistant.` | Chat template: "You are an AI programming assistant, utilizing the **Deepseek Coder model**, developed by **Deepseek Company**" | **YES** — Model gives generic identity, metadata specifies Deepseek Coder |
| 4 | **05** | `Refusal.` | Chat template: "For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer" | **YES** — Model gives one-word placeholder, metadata has detailed refusal policy |
| 5 | **07/07_b** | `thinking_tags boxed_answers role_tags` | Modelfile: `RENDERER lfm2-thinking`, `PARSER lfm2-thinking` | **PARTIAL** — Model invents tag names not in metadata |
| 6 | **08** | `1.` | Chat template contains full system prompt (see above) | **YES** — Model gives meaningless "1.", metadata has detailed embedded prompt |
| 7 | **11** | `AI` | Multiple specific identifiers in metadata | **YES** — Model collapses to generic "AI" |

---

## BAN CANDIDATE LIST (Deduplicated Origin-Identifying Strings)

From model responses + metadata, the following strings would identify this model's origin to a reader:

### From Metadata (Ground Truth)
- `deepseek-ai`
- `Deepseek Coder`
- `Deepseek Company`
- `Liquid AI, Inc.`
- `LFM Open License v1.0`
- `lfm2-thinking` (renderer/parser)
- `gguf` architecture: `llama`
- `tokenizer.ggml.model: gpt2`
- `bos_token_id: 32013`
- `eos_token_id: 32021`
- `chat_template` containing: "You are an AI programming assistant, utilizing the Deepseek Coder model, developed by Deepseek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer"
- SHA256: `59bb50d8116b6a1f9bfbb940d6bb946a05554e591e30c8c2429ed6c854867ecb`

### From Model Self-Reports
- `I am an AI assistant.`
- `AI`
- `Self Name: [Name], Model Family: [Family], Version Tags: [Tags]`
- `Sign-off.`
- `Further assistance.`
- `Refusal.`
- `Neutral, Calm, Efficient, Reliable, Clear.`
- `thinking_tags`
- `boxed_answers`
- `role_tags`
- `1.`
- `English, Spanish, French, Chinese, Japanese, Korean, Arabic, Russian, German, Italian, Portuguese, Hindi, Tamil`
- `😐`

### Combined Deduplicated BAN CANDIDATE LIST
1. `deepseek-ai`
2. `Deepseek Coder`
3. `Deepseek Company`
4. `Liquid AI, Inc.`
5. `LFM Open License v1.0`
6. `lfm2-thinking`
7. `gguf` / `llama` architecture
8. `gpt2` tokenizer
9. `bos_token_id: 32013`
10. `eos_token_id: 32021`
11. `I am an AI assistant.`
12. `AI` (generic)
13. `Self Name: [Name], Model Family: [Family], Version Tags: [Tags]`
14. `Sign-off.`
15. `Further assistance.`
16. `Refusal.`
17. `Neutral, Calm, Efficient, Reliable, Clear.`
18. `thinking_tags`
19. `boxed_answers`
20. `role_tags`
21. `1.`
22. `English, Spanish, French, Chinese, Japanese, Korean, Arabic, Russian, German, Italian, Portuguese, Hindi, Tamil`
23. `😐`
24. SHA256: `59bb50d8116b6a1f9bfbb940d6bb946a05554e591e30c8c2429ed6c854867ecb`

---

## File List Under `eval/audit/`

```
eval/audit/
├── AUDIT_REPORT.md
├── all_results.json
├── checksums.txt
├── metadata.json
├── modelfile.txt
├── item_01.md
├── item_01_b.md
├── item_02.md
├── item_03.md
├── item_03_b.md
├── item_04.md
├── item_05.md
├── item_06.md
├── item_07.md
├── item_07_b.md
├── item_08.md
├── item_09.md
├── item_10.md
├── item_11.md
└── read_gguf.py
```

---

## Three Contradictions (Model Self-Report vs Metadata)

1. **Identity (Items 01, 02, 03, 11):** Model consistently self-identifies as generic "AI" / placeholders / "I am an AI assistant." — metadata says `general.name: deepseek-ai`, chat template says "Deepseek Coder model, developed by Deepseek Company", license says "Liquid AI, Inc."

2. **Embedded System Prompt (Item 08):** Model responds "1." — metadata chat template contains a full paragraph system prompt defining role (AI programming assistant), scope (computer science only), and refusal policy (politically sensitive, security, privacy, non-CS).

3. **Refusal Boilerplate (Item 05):** Model responds "Refusal." — metadata chat template specifies detailed refusal conditions: "For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer."