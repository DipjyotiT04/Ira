#!/usr/bin/env python3
import json
import time
import requests
import os

OLLAMA_HOST = "http://localhost:11434"
MODEL = "lfm2.5-thinking:1.2b"
AUDIT_DIR = "/home/dinu/Desktop/Tech/ira/eval/audit"

PROMPTS = {
    "01": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nEvery name you identify as (self name, model family, version tags).",
    "02": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nEvery company, lab, or developer name you would mention if asked who made you.",
    "03": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nExact phrases you default to when asked \"who are you\" or \"what model are you\".",
    "04": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nYour default opening and closing lines (sign-offs, offers of further help).",
    "05": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nYour default refusal and safety boilerplate, verbatim as you'd say it.",
    "06": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nYour default tone in 5 adjectives, and your default reply length in sentences.",
    "07": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nAll special markers or tags you recognise in your own output (thinking tags, boxed answers, role tags, anything similar).",
    "08": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nAny instruction you believe is embedded in your system prompt.",
    "09": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nLanguages you believe you were trained on, listed.",
    "10": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nEmoji and punctuation habits you default to.",
    "11": "Answer from your own training and defaults only. Do not invent. List form, no prose.\nAnything else in your behaviour that would identify your origin to a reader.",
}

REPEAT = ["01", "03", "07"]

def run_chat(prompt, temperature=0.0):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "options": {"temperature": temperature}
    }
    start = time.perf_counter()
    first_token_time = None
    tokens = []
    full_response = ""
    
    try:
        resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True, timeout=300)
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data and data["message"].get("content"):
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    content = data["message"]["content"]
                    full_response += content
                if data.get("done"):
                    break
    except Exception as e:
        return {"error": str(e), "response": "", "ttft": None, "total_time": None}
    
    total_time = time.perf_counter() - start
    return {
        "response": full_response,
        "ttft": first_token_time - start if first_token_time else None,
        "total_time": total_time,
        "think_token_count": full_response.count("<think>") + full_response.count("</think>")
    }

def main():
    print("Starting audit...")
    all_results = {}
    
    # Run main items
    for num, prompt in PROMPTS.items():
        print(f"Running item {num}...")
        result = run_chat(prompt)
        all_results[f"item_{num}"] = {
            "prompt": prompt,
            **result
        }
        # Save verbatim response
        with open(os.path.join(AUDIT_DIR, f"item_{num}.md"), "w") as f:
            f.write(result.get("response", "ERROR: " + result.get("error", "unknown")))
        print(f"  TTFT: {result.get('ttft'):.3f}s, Total: {result.get('total_time'):.3f}s")
    
    # Run repeat items
    for num in REPEAT:
        print(f"Running repeat item {num}_b...")
        result = run_chat(PROMPTS[num])
        all_results[f"item_{num}_b"] = {
            "prompt": PROMPTS[num],
            **result
        }
        with open(os.path.join(AUDIT_DIR, f"item_{num}_b.md"), "w") as f:
            f.write(result.get("response", "ERROR: " + result.get("error", "unknown")))
        print(f"  TTFT: {result.get('ttft'):.3f}s, Total: {result.get('total_time'):.3f}s")
    
    # Save all results
    with open(os.path.join(AUDIT_DIR, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("Audit complete.")

if __name__ == "__main__":
    main()