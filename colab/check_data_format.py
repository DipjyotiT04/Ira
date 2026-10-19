#!/usr/bin/env python3
"""Validate a {"messages": [...]} JSONL against a Jinja chat template (CPU only).

Usage:
  python scripts/check_data_format.py --jsonl colab/data/identity.jsonl \
      --template colab/configs/chat_template.txt \
      --tokenizer /path/to/tokenizer_dir \
      [--ban-strings data/sft/ban_strings.txt] [--max-tokens 1024] [--show 3]

Hard assertions per sample:
  a) roles alternate, first==system, last==assistant
  b) exactly one think-open and one think-close marker in assistant turns (rendered)
  c) no adjacent double-wrapped role tokens in the rendered text
  d) rendered token count <= max-tokens (default 1024)
  e) no ban string (whole-word, case-insensitive, len>=4) in assistant content

Prints `--show` fully rendered examples verbatim with token counts.
Exit 0 = all pass, 1 = one or more samples failed, 2 = config/input error.
Never exits silently: every failure path prints a readable message.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FAIL = 1
CONFIG = 2


def die(msg: str, code: int = CONFIG) -> None:
    print(f"\nCHECK DATA FORMAT: CONFIG ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_template(path: Path) -> str:
    if not path.is_file():
        die(f"template file not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    body = "\n".join(l for l in lines if not l.startswith("# ")).strip()
    if not body:
        die(f"template file is empty: {path}")
    if body == "{{ .Prompt }}" or "{{ .Prompt }}" == body.strip():
        die(
            "template is literally '{{ . Prompt }}' — that is the OLLAMA serving "
            "template, WRONG SOURCE. Refusing to continue."
        )
    for required in ("<|im_start|>", "<|im_end|>", "<think>", "</think>"):
        if required not in body:
            die(f"template does not contain required marker {required!r}: {path}")
    return body


def load_ban_strings(path: Path) -> list[str]:
    if not path.is_file():
        die(f"ban strings file not found: {path}")
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if len(s) >= 4:
            out.append(s)
    return out


def ban_regexes(bans: list[str]) -> list[re.Pattern]:
    return [re.compile(r"\b" + re.escape(b) + r"\b", re.IGNORECASE) for b in bans]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", required=True, type=Path)
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--tokenizer", required=True, type=Path,
                    help="directory containing tokenizer.json + tokenizer_config.json")
    ap.add_argument("--ban-strings", type=Path, default=Path("data/sft/ban_strings.txt"))
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--think-open", default="<think>")
    ap.add_argument("--think-close", default="</think>")
    ap.add_argument("--role-start", default="<|im_start|>")
    ap.add_argument("--role-end", default="<|im_end|>")
    args = ap.parse_args()

    if not args.ban_strings.is_file():
        for alt in (Path("data/ban_strings.txt"), Path("colab/data/ban_strings.txt")):
            if alt.is_file():
                args.ban_strings = alt
                break
    if not args.jsonl.is_file():
        for alt in (Path("data/identity.jsonl"), Path("colab/data/identity.jsonl")):
            if alt.is_file():
                args.jsonl = alt
                break
    if not args.template.is_file():
        for alt in (Path("configs/chat_template.txt"), Path("colab/configs/chat_template.txt")):
            if alt.is_file():
                args.template = alt
                break
    if not args.jsonl.is_file():
        die(f"jsonl not found: {args.jsonl}")
    if not (args.tokenizer / "tokenizer.json").is_file():
        die(f"tokenizer.json not found in {args.tokenizer}")

    try:
        from transformers import AutoTokenizer
        import jinja2
    except Exception as e:  # pragma: no cover
        die(f"import failed: {e}")

    try:
        tok = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True)
    except Exception as e:
        die(f"tokenizer load failed: {e}")

    template = load_template(args.template)
    tok.chat_template = template
    bans = ban_regexes(load_ban_strings(args.ban_strings))
    rs, re_, to, tc = args.role_start, args.role_end, args.think_open, args.think_close

    samples = []
    for i, line in enumerate(args.jsonl.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            die(f"invalid JSON at line {i + 1} of {args.jsonl}: {e}")
        if "messages" not in obj or not isinstance(obj["messages"], list):
            die(f"line {i + 1}: missing 'messages' list")
        samples.append((i, obj["messages"]))
    if not samples:
        die(f"no samples found in {args.jsonl}")

    print(f"check_data_format: {len(samples)} samples | template={args.template} "
          f"| tokenizer={args.tokenizer} | max_tokens={args.max_tokens} | bans={len(bans)}")

    failures: dict[int, list[str]] = {}
    rendered_cache: dict[int, tuple[str, int]] = {}
    seg_re = re.compile(re.escape(rs) + r"([a-z]+)\n(.*?)" + re.escape(re_) + r"\n?", re.DOTALL)

    for idx, messages in samples:
        errs: list[str] = []

        roles = [m.get("role") for m in messages]
        # --- assertion (a): role structure in the sample ---
        if not roles or roles[0] != "system":
            errs.append(f"a: first role is {roles[0]!r}, expected 'system'")
        if roles and roles[-1] != "assistant":
            errs.append(f"a: last role is {roles[-1]!r}, expected 'assistant'")
        for j in range(1, len(roles)):
            if roles[j] == roles[j - 1]:
                errs.append(f"a: roles not alternating at position {j}: {roles[j-1]!r}->{roles[j]!r}")
        if any(r not in ("system", "user", "assistant") for r in roles):
            errs.append(f"a: unknown role in {roles}")

        # --- render through the real template ---
        try:
            rendered = tok.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
        except Exception as e:
            errs.append(f"render: {type(e).__name__}: {e}")
            failures[idx] = errs
            continue
        try:
            n_tokens = len(tok(rendered, add_special_tokens=False).input_ids)
        except Exception as e:
            errs.append(f"tokenize: {type(e).__name__}: {e}")
            failures[idx] = errs
            continue
        rendered_cache[idx] = (rendered, n_tokens)

        # --- assertion (d): token budget ---
        if n_tokens > args.max_tokens:
            errs.append(f"d: rendered {n_tokens} tokens > max {args.max_tokens}")

        # --- assertion (c): adjacent double-wrapped role tokens ---
        for marker in (rs, re_):
            if marker + marker in rendered:
                errs.append(f"c: adjacent double-wrapped role token {marker * 2!r}")
        # any special token repeated back-to-back
        for sp in filter(None, list(tok.all_special_tokens)):
            if len(sp) >= 5 and sp + sp in rendered and sp not in (rs, re_):
                if sp in (to, tc):
                    continue
                errs.append(f"c: adjacent duplicate special token {sp!r}")
                break

        # --- assertion (b): exactly one think pair in each assistant turn (rendered) ---
        segments = seg_re.findall(rendered)
        if segments:
            for srole, sbody in segments:
                if srole != "assistant":
                    continue
                no, nc = sbody.count(to), sbody.count(tc)
                if no != 1 or nc != 1:
                    errs.append(
                        f"b: assistant turn has {no}x {to} / {nc}x {tc}, expected 1 each"
                    )
            # exactly one assistant segment must exist in a valid sample
            if not any(sr == "assistant" for sr, _ in segments):
                errs.append("b: no assistant segment found in rendered output")
        else:
            errs.append(f"b: rendered output has no {rs}...{re_} segments at all")

        # --- assertion (e): ban strings in assistant content ---
        for m in messages:
            if m.get("role") != "assistant":
                continue
            content = str(m.get("content", ""))
            for rx in bans:
                if rx.search(content):
                    errs.append(f"e: ban string matched in assistant content: {rx.pattern!r}")

        if errs:
            failures[idx] = errs

    # --- report 3 rendered examples verbatim ---
    shown = 0
    for idx, _ in samples:
        if shown >= args.show:
            break
        if idx in rendered_cache:
            text, nt = rendered_cache[idx]
            print("\n" + "=" * 78)
            print(f"RENDERED EXAMPLE sample_id={idx} tokens={nt}")
            print("=" * 78)
            print(text)
            print("=" * 78)
            shown += 1
    if shown == 0:
        print("\n(no rendered examples available — every sample failed to render)",
              file=sys.stderr)

    # --- verdict ---
    if failures:
        print(f"\nCHECK DATA FORMAT: FAIL — {len(failures)}/{len(samples)} samples failed")
        for idx, errs in sorted(failures.items()):
            print(f"  sample_id={idx}:")
            for e in errs:
                print(f"    - {e}")
        print(f"\nfirst 20 failing ids: {sorted(failures)[:20]}")
        sys.exit(FAIL)

    print(f"\nCHECK DATA FORMAT: PASS — all {len(samples)} samples OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
