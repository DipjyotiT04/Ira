# Workspace Structure Documentation

## Root Directory (`/home/dinu/Desktop/Tech/Ira`)

| Item | Type | Description |
|------|------|-------------|
| `.git` | Directory | Git repository |
| `.gitignore` | File | Git ignore patterns |
| `.directory` | File | Directory metadata |
| `LICENSE` | File | License file |
| `README.md` | File | Project overview (minimal) |
| `models.md` | File | Model documentation (47KB) |
| `result.md` | File | Results documentation (13KB) |

---

## Directories

### `colab/` - Jupyter Notebooks for Training Pipeline
```
colab/
├── 00_smoke.ipynb       # Smoke test notebook (9KB)
├── 01_train.ipynb       # Training notebook (11KB)
├── 02_merge_export.ipynb # Merge & export notebook (5KB)
├── configs/             # Configuration files
│   ├── chat_template.txt      # Chat template (290B)
│   ├── lora_config.json       # LoRA configuration (234B)
│   └── system_prompt.txt      # System prompt (2.7KB)
├── data/                # Colab-specific data
│   ├── ban_strings.txt        # Ban strings list (309B)
│   ├── identity.jsonl         # Identity training data (309KB)
│   └── persona.jsonl          # Persona data (165B)
└── README.md            # Colab documentation (4.4KB)
```

### `data/` - Primary Data Storage
```
data/
└── sft/                 # Supervised Fine-Tuning data
    ├── ban_strings.txt  # Ban strings (309B)
    └── identity.jsonl   # Identity dataset (309KB)
```

### `docs/` - Documentation & Specifications
```
docs/
├── BUILD_PLAN.md        # Build plan (8.5KB)
├── MASTER_PROMPT.md     # Master prompt (6.9KB)
├── persona_spec.md      # Persona specification (2.6KB)
├── PERSONA_SPEC.md      # Persona spec (alt) (3.5KB)
├── STATUS.md            # Project status (4.1KB)
├── system_prompt.md     # System prompt (2.2KB)
└── SYSTEM_PROMPT.md     # System prompt (alt) (2.7KB)
```

### `eval/` - Evaluation & Benchmarking
```
eval/
├── audit/               # Audit results & artifacts
│   ├── all_results.json         # Aggregated results (4.9KB)
│   ├── api_show.json            # API responses (33KB)
│   ├── AUDIT_REPORT.md          # Audit report (12KB)
│   ├── blob_inventory.json      # Blob inventory (1.3KB)
│   ├── checksums.txt            # File checksums (106B)
│   ├── IDENTITY_VERDICT.md      # Identity verdict (2.7KB)
│   ├── item_01.md - item_11.md  # Individual test items
│   ├── metadata.json            # Metadata (1.9MB)
│   ├── modelfile.txt            # Modelfile (10KB)
│   ├── read_gguf.py             # GGUF reader script (4.7KB)
│   └── run_audit.py             # Audit runner (4.7KB)
├── runs/                # Evaluation runs
│   └── erase_after_config_2026-10-18.json # Run config (480B)
├── benchmark.py         # Benchmark script (9.5KB)
├── prompts.jsonl        # Evaluation prompts (23.8KB)
└── raw_results.json     # Raw evaluation results (51.8KB)
```

### `memory/` - Memory System
```
memory/
├── ira_memory.db        # SQLite memory database (45KB)
└── ira_memory.py        # Memory management module (8.3KB)
```

### `models/` - Model Definitions
```
models/
└── Modelfile.ira        # Ollama Modelfile for Ira (1.9KB)
```

### `scripts/` - Utility Scripts
```
scripts/
├── gen_identity_data.py     # Generate identity training data (8.5KB)
├── make_ollama.sh           # Create Ollama model (223B)
└── verify_erase.py          # Verify erasure (6.1KB)
```

---

## Key Files Summary

| Category | Files |
|----------|-------|
| **Training Notebooks** | `colab/00_smoke.ipynb`, `colab/01_train.ipynb`, `colab/02_merge_export.ipynb` |
| **Training Data** | `colab/data/identity.jsonl`, `data/sft/identity.jsonl` |
| **Configuration** | `colab/configs/lora_config.json`, `colab/configs/chat_template.txt`, `colab/configs/system_prompt.txt` |
| **Model Definition** | `models/Modelfile.ira` |
| **Evaluation** | `eval/benchmark.py`, `eval/prompts.jsonl`, `eval/raw_results.json` |
| **Audit** | `eval/audit/AUDIT_REPORT.md`, `eval/audit/IDENTITY_VERDICT.md` |
| **Documentation** | `docs/BUILD_PLAN.md`, `docs/MASTER_PROMPT.md`, `docs/STATUS.md` |
| **Memory** | `memory/ira_memory.py`, `memory/ira_memory.db` |
| **Scripts** | `scripts/gen_identity_data.py`, `scripts/make_ollama.sh`, `scripts/verify_erase.py` |

---

## Data Flow Overview

1. **Data Generation** → `scripts/gen_identity_data.py` → `colab/data/identity.jsonl` / `data/sft/identity.jsonl`
2. **Training** → `colab/01_train.ipynb` (uses LoRA config from `colab/configs/lora_config.json`)
3. **Merge/Export** → `colab/02_merge_export.ipynb` → `models/Modelfile.ira`
4. **Deployment** → `scripts/make_ollama.sh` creates Ollama model
5. **Evaluation** → `eval/benchmark.py` + `eval/prompts.jsonl` → `eval/raw_results.json`
6. **Audit** → `eval/audit/run_audit.py` → `eval/audit/AUDIT_REPORT.md`
7. **Memory** → `memory/ira_memory.py` manages `memory/ira_memory.db`