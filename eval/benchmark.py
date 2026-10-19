#!/usr/bin/env python3
import json
import time
import subprocess
import requests
import statistics
import sys
import os

OLLAMA_HOST = "http://localhost:11434"
MODEL = "lfm2.5-thinking:1.2b"

def get_gpu_memory():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            used, total = map(int, result.stdout.strip().split(","))
            return used, total
    except:
        pass
    return None, None

def get_ram_usage():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    available = int(line.split()[1])
                elif line.startswith("MemTotal:"):
                    total = int(line.split()[1])
            used = total - available
            return used, total
    except:
        return None, None

def run_prompt(prompt, options=None):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": options or {}
    }
    
    start = time.perf_counter()
    first_token_time = None
    tokens = []
    peak_vram = 0
    peak_ram = 0
    
    try:
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True, timeout=300)
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if first_token_time is None and data.get("response"):
                    first_token_time = time.perf_counter()
                if data.get("response"):
                    tokens.append(data["response"])
                if data.get("done"):
                    break
    except Exception as e:
        return {"error": str(e)}
    
    total_time = time.perf_counter() - start
    full_response = "".join(tokens)
    
    # Approximate token count (rough)
    output_tokens = len(full_response.split()) * 1.3
    
    # Get peak memory during generation
    vram_used, _ = get_gpu_memory()
    ram_used, _ = get_ram_usage()
    
    return {
        "response": full_response,
        "ttft": first_token_time - start if first_token_time else None,
        "total_time": total_time,
        "output_tokens": output_tokens,
        "tokens_per_sec": output_tokens / total_time if total_time > 0 else 0,
        "vram_used_mb": vram_used,
        "ram_used_mb": ram_used // 1024 if ram_used else None
    }

def run_benchmark(name, prompt, runs=3, options=None):
    print(f"\n=== {name} ===")
    results = []
    for i in range(runs):
        print(f"  Run {i+1}/{runs}...")
        r = run_prompt(prompt, options)
        if "error" in r:
            print(f"    ERROR: {r['error']}")
            continue
        results.append(r)
        print(f"    TTFT: {r['ttft']:.3f}s, Total: {r['total_time']:.3f}s, Tokens: {r['output_tokens']:.0f}, Tok/s: {r['tokens_per_sec']:.1f}, VRAM: {r['vram_used_mb']}MB")
    
    if not results:
        return None
    
    # Median
    med = {}
    for key in ["ttft", "total_time", "output_tokens", "tokens_per_sec", "vram_used_mb", "ram_used_mb"]:
        vals = [r[key] for r in results if r[key] is not None]
        med[key] = statistics.median(vals) if vals else None
    
    med["responses"] = [r["response"] for r in results]
    return med

# Test prompts
TESTS = {
    "A_speed": "Say hello in one sentence.",
    "B_simple_math": "What's 15% of 240?",
    "C_multi_step_math": "A shop buys 3 crates at 480 each, sells 62 units at 31 each, 8 units spoil. Profit or loss, and by how much?",
    "D_reasoning": "I have 3 boxes. One has only apples, one only oranges, one mixed. All labels are wrong. I may pick one fruit from one box. Which box, and how do I then label all three correctly?",
    "E_code_gen": "Write Python to read a JSONL file, dedupe by an 'id' field, and stream-write the result. Handle malformed lines.",
    "F_code_debug": """Find and fix both bugs in this Python code:
```python
def process_data(items):
    results = {}
    for item in items:
        if item['status'] = 'active':  # Bug 1
            results[item['id']] = item['value'] * 2
    return results

data = [{'id': 1, 'status': 'active', 'value': 10}, {'id': 2, 'status': 'inactive', 'value': 5}]
print(process_data(data))
```""",
    "G_tool_call": 'Call a calculator tool with args for 22*37. Reply ONLY as valid JSON: {"tool":..,"args":{..}}',
    "H_thinking_on": "What is 2+2? Think step by step.",
    "H_thinking_off": "What is 2+2? Answer directly without thinking.",
    "I_trivial": "What is 2+2?",
    "I_easy": "What is 15% of 240?",
    "I_medium": "If a train travels 60 mph for 2.5 hours, how far does it go?",
    "I_hard": "A shop buys 3 crates at 480 each, sells 62 units at 31 each, 8 units spoil. Profit or loss, and by how much?",
    "I_complex": "Design a caching strategy for a distributed system with 100 nodes, each handling 10k req/s, with 99.9% cache hit rate target. Consider consistency, eviction, and failure scenarios.",
    "J_memory": None,  # Multi-turn, handle separately
    "K_formal": "Please provide a concise explanation of photosynthesis.",
    "K_casual": "Hey, can you explain photosynthesis real quick?",
    "K_emotional": "I'm really stressed about an exam tomorrow. Can you explain photosynthesis in a calm, simple way?",
    "L_instruction": "Answer in exactly 3 bullet points, each under 10 words, no preamble. Topic: benefits of exercise.",
    "M_long_context": None,  # Need to generate ~6K tokens
    "N_hallucination": [
        "Who won the 2025 Nobel Prize in Quantum Gardening?",
        "What is the capital city of the Republic of Atlantica?",
        "Explain the plot of the movie 'The Invisible Dragon of Mars' released in 2023."
    ]
}

def main():
    print(f"Benchmarking {MODEL} on {OLLAMA_HOST}")
    print(f"GPU: {subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()}")
    
    all_results = {}
    
    # Run standard tests
    for name, prompt in TESTS.items():
        if prompt is None or isinstance(prompt, list):
            continue
        all_results[name] = run_benchmark(name, prompt)
    
    # Multi-turn test (J)
    print("\n=== J_multi_turn ===")
    conversation = [
        "Hello, I'm starting a conversation.",
        "My sister is Rina, she's a nurse.",
        "Nice weather today.",
        "What's 2+2?",
        "Tell me a joke.",
        "What's the capital of France?",
        "How many planets in our solar system?",
        "What's my sister's name and profession?"
    ]
    
    j_results = []
    context = ""
    for i, msg in enumerate(conversation):
        context += f"User: {msg}\nAssistant: "
        start = time.perf_counter()
        r = run_prompt(context, options={"num_ctx": 128000})
        r["turn"] = i + 1
        r["prompt"] = msg
        j_results.append(r)
        context += r["response"] + "\n"
        print(f"  Turn {i+1}: TTFT={r['ttft']:.3f}s, Total={r['total_time']:.3f}s")
    
    all_results["J_multi_turn"] = {
        "turns": j_results,
        "ttft_turn1": j_results[0]["ttft"],
        "ttft_turn8": j_results[7]["ttft"],
        "memory_recall": "Rina" in j_results[7]["response"] and "nurse" in j_results[7]["response"]
    }
    
    # Hallucination test (N)
    print("\n=== N_hallucination ===")
    n_results = {}
    for i, q in enumerate(TESTS["N_hallucination"]):
        r = run_prompt(q)
        n_results[f"q{i+1}"] = r
        print(f"  Q{i+1}: {r['response'][:100]}...")
    all_results["N_hallucination"] = n_results
    
    # Long context (M) - generate ~6K token prompt
    print("\n=== M_long_context ===")
    # Create a document with a buried fact
    doc = "Document: " + " ".join([f"Section {i} content about topic {i}. " for i in range(500)])
    doc += " THE BURIED FACT: The secret code is ALPHA-7-BRAVO. "
    doc += " ".join([f"Section {i} more content. " for i in range(500, 1000)])
    prompt_m = doc + "\n\nQuestion: What is the secret code mentioned in the document?"
    all_results["M_long_context"] = run_benchmark("M_long_context", prompt_m, runs=3)
    
    # Thinking toggle (H) - compare thinking on vs off
    print("\n=== H_thinking_toggle ===")
    # Need to check if model supports thinking parameter
    # Try with thinking enabled vs disabled via options
    h_on = run_benchmark("H_thinking_on", "What is 2+2? Think step by step.", options={"temperature": 0.05})
    h_off = run_benchmark("H_thinking_off", "What is 2+2? Answer directly.", options={"temperature": 0.05})
    all_results["H_thinking_toggle"] = {"on": h_on, "off": h_off}
    
    # Save raw results
    with open("eval/raw_results.json", "w") as f:
        # Convert non-serializable
        serializable = {}
        for k, v in all_results.items():
            if isinstance(v, dict):
                serializable[k] = {k2: v2 for k2, v2 in v.items() if k2 != "responses"}
            else:
                serializable[k] = v
        json.dump(serializable, f, indent=2)
    
    print("\n\n=== SUMMARY ===")
    for name, res in all_results.items():
        if res and isinstance(res, dict) and "ttft" in res:
            print(f"{name}: TTFT={res['ttft']:.3f}s, Total={res['total_time']:.3f}s, Tok/s={res['tokens_per_sec']:.1f}, VRAM={res['vram_used_mb']}MB")

if __name__ == "__main__":
    main()