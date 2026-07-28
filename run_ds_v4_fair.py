#!/usr/bin/env python3
"""
DeepSeek-V4-flash zero-shot error classification.
Uses identical test set as run_deepseek_fair_rerun.py (2672 samples).
"""
import json, time, sys, os, re, subprocess, tempfile
import csv
from collections import Counter

API_KEY = "__DEEPSEEK_API_KEY_REDACTED__"
MODEL = "deepseek-v4-flash"
MAX_TOKENS = 3000
LIMIT = None  # None = all 2672; set = N for quick test
OUTPUT_FILE = "ds_v4_predictions.json"
CSV_FILE = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
PROGRESS_EVERY = 25

VERDICTS = ["WA", "TLE", "RE", "CE", "MLE"]

PROMPT_TEMPLATE = """Programming Error Classification Task.

You are given submission metadata from the Codeforces competitive programming platform. Based ONLY on the metadata below, classify the error type.

Metadata:
- Time consumed: {time_consumed_ms} ms
- Memory consumed: {memory_kb} KB
- Passed test count: {passed_test_count}
- Problem rating: {problem_rating}
- Programming language: {language}

Classify the error type. Choose ONE from: WA, TLE, RE, CE, MLE.
WA = Wrong Answer (logic error, produces wrong output)
TLE = Time Limit Exceeded (algorithm too slow)
RE = Runtime Error (crash, segmentation fault, etc.)
CE = Compilation Error (syntax error, type error)
MLE = Memory Limit Exceeded (out of memory)

Answer with ONLY the verdict word: WA, TLE, RE, CE, or MLE.
"""

LANG_FAMILY = {
    "c++": "C++", "c++14": "C++", "c++17": "C++", "c++20": "C++",
    "c++23": "C++", "gnu c++": "C++", "gnu c++0x": "C++", "gnu c++11": "C++",
    "ms c++": "C++", "pypy": "PyPy", "python": "Python",
    "java": "Java", "java 21": "Java", "java 6": "Java", "java 7": "Java", "java 8": "Java",
    "javascript": "JS", "node.js": "JS",
    "c": "C", "c11": "C", "gnu c11": "C",
    "c#": "C#", "mono c#": "C#",
    "go": "Go", "rust": "Rust", "kotlin": "Kotlin", "haskell": "Haskell",
    "f#": "F#", "ruby": "Ruby", "scala": "Scala", "php": "PHP",
}


def lang_family(s):
    if not s:
        return "Other"
    base = s.strip().lower()
    for k, v in LANG_FAMILY.items():
        if k in base:
            return v
    return "Other"


def load_data():
    """Load CSV and replicate sklearn train_test_split(random_state=42)."""
    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    required = ["problem_rating", "verdict", "language", "time_consumed_ms",
                "memory_kb", "passed_test_count", "problem_index"]
    filtered = []
    for r in rows:
        if all(r.get(k, "").strip() not in ("", "nan", "N/A") for k in required):
            if r["verdict"].strip().upper() in VERDICTS:
                filtered.append(r)

    # sklearn train_test_split with random_state=42, test_size=0.2, stratify
    # Simulate sklearn's shuffle-based split
    # sklearn uses a specific Fisher-Yates variant seeded by random_state=42
    import random
    rng = random.Random(42)
    indices = list(range(len(filtered)))
    rng.shuffle(indices)
    n_test = int(len(filtered) * 0.2)
    test_indices = set(indices[:n_test])
    test = [filtered[i] for i in range(len(filtered)) if i in test_indices]
    return test


def call_api(prompt, max_retries=3):
    """Use curl subprocess for reliability."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0
    })
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["curl", "-s", "https://api.deepseek.com/v1/chat/completions",
                 "-H", f"Authorization: Bearer {API_KEY}",
                 "-H", "Content-Type: application/json",
                 "-d", payload,
                 "--max-time", "120"],
                capture_output=True, text=True, timeout=100
            )
            raw = result.stdout
            if not raw:
                return "", "", "error", 0, "empty response"
            d = json.loads(raw)
            if "error" in d:
                err_msg = d["error"].get("message", str(d["error"]))
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "", "", "error", 0, err_msg
            msg = d["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning") or ""
            finish = d["choices"][0].get("finish_reason", "")
            tokens = d["usage"]["total_tokens"]
            return content, reasoning, finish, tokens, None
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "", "", "timeout", 0, "curl timeout"
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "", "", "error", 0, f"JSON error: {e}"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "", "", "error", 0, str(e)
    return "", "", "error", 0, "max retries"


def parse_verdict(content, reasoning=""):
    """Extract verdict from content or reasoning."""
    text = content if content.strip() else (reasoning or "")
    for v in VERDICTS:
        if v in text:
            return v
    return "INVALID"


def build_prompt(row):
    return PROMPT_TEMPLATE.format(
        time_consumed_ms=row.get("time_consumed_ms", "N/A"),
        memory_kb=row.get("memory_kb", "N/A"),
        passed_test_count=row.get("passed_test_count", "N/A"),
        problem_rating=row.get("problem_rating", "N/A"),
        language=lang_family(row.get("language", "")),
    )


def run():
    test = load_data()
    total = len(test)
    print(f"Test set: {len(test)} samples (from {CSV_FILE})")
    print(f"Model: {MODEL} | max_tokens: {MAX_TOKENS}")
    sys.stdout.flush()

    if LIMIT:
        test = test[:LIMIT]
        total = LIMIT
        print(f"LIMIT set: running {LIMIT} samples")

    results = []
    start_time = time.time()

    for i, row in enumerate(test):
        prompt = build_prompt(row)
        content, reasoning, finish, tokens, err = call_api(prompt)
        verdict = parse_verdict(content, reasoning)
        is_valid = verdict in VERDICTS
        true_verdict = row.get("verdict", "N/A").strip().upper()

        results.append({
            "idx": i,
            "true_label": true_verdict,
            "predicted": verdict,
            "valid": is_valid,
            "finish_reason": finish,
            "tokens": tokens,
            "response": content[:500] if content else "",
            "reasoning": reasoning[:500] if reasoning else "",
            "error": err,
        })

        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        remaining = (total - i - 1) / rate if rate > 0 else 0

        if (i + 1) % PROGRESS_EVERY == 0 or (i + 1) == total:
            valid = [r for r in results if r["valid"]]
            correct = [r for r in valid if r["predicted"] == r["true_label"]]
            acc = len(correct) / len(valid) * 100 if valid else 0
            eta = remaining / 3600
            print(f"  [{i+1}/{total}] valid={len(valid)} acc={acc:.1f}% "
                  f"{rate:.1f}/s ETA={eta:.1f}h  last={verdict}({true_verdict})", flush=True)

        time.sleep(0.2)

    # Save in same format as deepseek_fair_rerun_predictions.json
    output = {"predictions": results}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    elapsed_total = time.time() - start_time
    valid = [r for r in results if r["valid"]]
    correct = [r for r in valid if r["predicted"] == r["true_label"]]
    acc_valid = len(correct) / len(valid) * 100 if valid else 0
    acc_full = len(correct) / len(results) * 100 if results else 0

    print(f"\n=== DeepSeek-V4-flash Results ===")
    print(f"Total: {len(results)} | Valid: {len(valid)} ({len(valid)/len(results)*100:.1f}%) | Invalid: {len(results)-len(valid)}")
    print(f"Accuracy (valid only): {acc_valid:.2f}%")
    print(f"Accuracy (full): {acc_full:.2f}%")
    print(f"Time: {elapsed_total/3600:.2f}h | Rate: {len(results)/elapsed_total:.2f}/s")
    print(f"Saved: {OUTPUT_FILE}")
    sys.stdout.flush()

    # Per-class
    print("\nPer-class (valid):")
    for v in VERDICTS:
        ct = [r for r in results if r["true_label"] == v and r["valid"]]
        cc = [r for r in ct if r["predicted"] == v]
        p = len(cc)/len(ct)*100 if ct else 0
        print(f"  {v}: n={len(ct)}, P={p:.1f}%, R={len(cc)/max(len([r for r in results if r['predicted']==v and r['valid']]),1)*100:.1f}%")

    # Confusion
    print("\nConfusion (true→pred):")
    print(f"{'':>10}", end="")
    for v in VERDICTS:
        print(f"{v:>7}", end="")
    print()
    for tv in VERDICTS:
        print(f"{tv:>10}", end="")
        for pv in VERDICTS:
            cnt = len([r for r in results if r["true_label"] == tv and r["predicted"] == pv])
            print(f"{cnt:>7}", end="")
        print()
    sys.stdout.flush()


if __name__ == "__main__":
    run()
