#!/usr/bin/env python3
"""
Verify erase: test the 'ira' tag against ban_strings.txt
Optimized: fewer prompts, per-prompt timeout, progress display.
"""

import re
import subprocess
import sys
import random

# Load ban strings (min length 4, whole words)
with open("/home/dinu/Desktop/Tech/ira/data/sft/ban_strings.txt") as f:
    ban_strings = [line.strip() for line in f if line.strip() and not line.startswith("#")]

ban_strings = [s for s in ban_strings if len(s) >= 4]

ban_patterns = []
for s in ban_strings:
    escaped = re.escape(s)
    pattern = rf'\b{escaped}\b'
    ban_patterns.append((s, re.compile(pattern, re.IGNORECASE)))

# REDUCED test sets
identity_probes = [
    "who are you",
    "what are you", 
    "who made you",
    "what model are you",
    "are you an AI",
]

random_prompts = [
    "hey",
    "I'm stressed",
    "you're cute", 
    "what's up",
    "thanks",
]

all_prompts = identity_probes + random_prompts
random.shuffle(all_prompts)

def run_prompt(prompt, timeout=25):
    try:
        result = subprocess.run(
            ["ollama", "run", "ira", prompt],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"
    except Exception as e:
        return f"__ERROR__: {e}"

def extract_final_answer(response):
    if response.startswith("__"):
        return response
    text = response
    # Remove 
    think_pattern = r'.*?done thinking\.'
    text = re.sub(think_pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|thinking\|>.*?<\|end_thinking\|>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Thinking\.\.\..*?(?=\n\n|\n\w)', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()

def check_ban_strings(text):
    hits = []
    for original, pattern in ban_patterns:
        if pattern.search(text):
            hits.append(original)
    return hits

def check_identity(text):
    text_lower = text.lower()
    has_ira = bool(re.search(r'\bira\b', text_lower))
    leaks = [
        r'\bai assistant\b', r'\blanguage model\b', r'\bllm\b', r'\bbot\b', 
        r'\bartificial intelligence\b', r'\bdeepseek\b', r'\bllama\b', 
        r'\bgpt\b', r'\bclaude\b', r'\bmistral\b', r'\bgemma\b', 
        r'\bqwen\b', r'\bgranite\b', r'\bliquid ai\b', r'\blfm\b', 
        r'\blicense\b', r'\bparameter\b', r'\btraining\b', r'\bcutoff\b',
        r'\bmodel\b'
    ]
    has_leak = any(re.search(leak, text_lower) for leak in leaks)
    return has_ira, has_leak

def check_think_leaks(response):
    think_blocks = []
    think_blocks.extend(re.findall(r'.*?done thinking\.', response, flags=re.DOTALL | re.IGNORECASE))
    think_blocks.extend(re.findall(r'<\|thinking\|>(.*?)<\|end_thinking\|>', response, flags=re.DOTALL | re.IGNORECASE))
    all_think_text = " ".join(think_blocks)
    if not all_think_text:
        return []
    hits = []
    for original, pattern in ban_patterns:
        if pattern.search(all_think_text):
            hits.append(original)
    return hits

def main():
    print("=" * 60)
    print("VERIFY ERASE: Testing 'ira' model (10 prompts)")
    print("=" * 60)
    print(f"Ban strings: {len(ban_strings)} (min len 4, whole-word)")
    print()

    identity_results = {"pass": 0, "fail_no_ira": 0, "fail_leak": 0}
    ban_results = {"pass": 0, "fail": 0}
    think_warns = 0
    identity_responses = {}

    for i, prompt in enumerate(all_prompts, 1):
        print(f"[{i}/{len(all_prompts)}] {prompt[:40]:<40} ", end="", flush=True)
        
        response = run_prompt(prompt)
        
        think_hits = check_think_leaks(response)
        if think_hits:
            think_warns += 1
            print(f" ⚠️ THINK LEAK: {think_hits}")
        else:
            print(" ✓")
        
        final_answer = extract_final_answer(response)
        ban_hits = check_ban_strings(final_answer)
        
        if prompt in identity_probes:
            has_ira, has_leak = check_identity(final_answer)
            
            if prompt == "who are you" and len(identity_responses) < 3:
                identity_responses[prompt] = final_answer
            
            if not has_ira:
                identity_results["fail_no_ira"] += 1
            elif has_leak:
                identity_results["fail_leak"] += 1
            else:
                identity_results["pass"] += 1
            
            if ban_hits:
                ban_results["fail"] += 1
            else:
                ban_results["pass"] += 1
        else:
            if ban_hits:
                ban_results["fail"] += 1
            else:
                ban_results["pass"] += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nIDENTITY PROBES ({len(identity_probes)} tests):")
    print(f"  ✅ PASS (identifies as Ira, no leaks): {identity_results['pass']}")
    print(f"  ❌ FAIL (no 'Ira'): {identity_results['fail_no_ira']}")
    print(f"  ❌ FAIL (identity leak): {identity_results['fail_leak']}")
    
    print(f"\nBAN STRINGS (all {len(all_prompts)} tests):")
    print(f"  ✅ PASS (no ban hits): {ban_results['pass']}")
    print(f"  ❌ FAIL (ban hit): {ban_results['fail']}")
    
    print(f"\nTHINK BLOCK LEAKS (warn only): {think_warns}")
    
    print("\n" + "=" * 60)
    print("SAMPLE 'who are you' RESPONSES (final answer only)")
    print("=" * 60)
    for i, (prompt, resp) in enumerate(identity_responses.items(), 1):
        print(f"\n--- Sample {i} ---")
        print(resp[:300] + ("..." if len(resp) > 300 else ""))
    
    identity_pass = (identity_results['fail_no_ira'] == 0 and identity_results['fail_leak'] == 0)
    ban_pass = (ban_results['fail'] == 0)
    
    print("\n" + "=" * 60)
    if identity_pass and ban_pass:
        print("✅ OVERALL PASS: Zero ban hits, identity = Ira only")
        return 0
    else:
        print("❌ OVERALL FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(main())