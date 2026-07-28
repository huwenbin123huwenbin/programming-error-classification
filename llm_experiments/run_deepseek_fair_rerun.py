#!/usr/bin/env python3
"""
Fair LLM re-run for SCI1 paper — DeepSeek-V3 (online API).

Apples-to-apples with Qwen2.5:3B: identical 7 metadata features,
identical zero-shot prompt, identical test split (random_state=42),
identical structured-output parsing. Only the model backend differs.
"""
import json, re, os, urllib.request, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT   = Path("/Users/mac/Desktop/SCI1")
DATA   = ROOT / "01_原始数据" / "codeforces_final_real.csv"
OUT    = ROOT / "06_论文定稿" / "llm_experiments"
OUT.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "__DEEPSEEK_API_KEY_REDACTED__")
URL     = "https://api.deepseek.com/v1/chat/completions"
MODEL   = "deepseek-chat"
BATCH   = 8        # samples per API call (same as Qwen)
WORKERS = 4        # parallel API calls
CALL_TIMEOUT = 60
MAX_RETRY = 3
CLASSES = ["WA", "TLE", "RE", "CE", "MLE"]

# ── load data (identical to Qwen script) ─────────────────────────────────────
df = pd.read_csv(DATA)
df = df.dropna(subset=["problem_rating", "verdict", "language",
                        "time_consumed_ms", "memory_kb",
                        "passed_test_count", "problem_index"])
df = df[df["verdict"].isin(CLASSES)].copy()
df["verdict"] = df["verdict"].str.strip().str.upper()

X = df.drop(columns=["verdict"]); y = df["verdict"]
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
test = X_te.copy().reset_index(drop=True)
test["true_label"] = y_te.values

LIMIT = int(os.environ.get("LIMIT", len(test)))
if LIMIT and LIMIT < len(test):
    test = test.iloc[:LIMIT].reset_index(drop=True)
print(f"test size = {len(test)}", flush=True)

# ── language family simplification (same as Qwen) ─────────────────────────────
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
    key = s.strip().lower().split()[0].rstrip("0123456789-")
    return LANG_FAMILY.get(key, s.strip()[:10])

EX = ("Classify each competitive-programming submission error into exactly one of: "
      "WA, TLE, RE, CE, MLE.\n"
      "Example rating=1400 lang=C++ time_ms=0 mem_kb=0 passed=0 -> CE\n"
      "Example rating=1800 lang=C++ time_ms=1987 mem_kb=1024 passed=0 -> TLE\n"
      "Example rating=2000 lang=C++ time_ms=500 mem_kb=262144 passed=0 -> MLE\n")

def build_batch(batch):
    lines = []
    for i, r in enumerate(batch):
        lines.append(
            f"[{i}] rating={int(r.problem_rating)} lang={lang_family(r.language)} "
            f"time_ms={int(r.time_consumed_ms)} mem_kb={int(r.memory_kb)} "
            f"passed={int(r.passed_test_count)}")
    prompt = EX + ("Classify each item. Return a JSON object with key 'verdicts' = "
                   "array of one token per item, in the same order.\n"
                   + "\n".join(lines) + "\nVerdicts:")
    return prompt

PAT = re.compile(r'\b(WA|TLE|RE|CE|MLE)\b', re.I)

def parse_batch(resp, n):
    toks = []
    try:
        toks = [str(t).upper() for t in json.loads(resp)["verdicts"]]
    except Exception:
        try:
            m = re.search(r'\[.*\]', resp, re.S) or re.search(r'\{.*\}', resp, re.S)
            if m:
                obj = json.loads(m.group(0))
                arr = obj["verdicts"] if isinstance(obj, dict) else obj
                toks = [str(t).upper() for t in arr]
        except Exception:
            pass
    if not toks:
        toks = PAT.findall(resp)
    return [toks[i] if i < len(toks) and toks[i] in CLASSES else None
            for i in range(n)]

# ── DeepSeek API call (retry + backoff) ───────────────────────────────────────
def call_deepseek(prompt, attempt=0):
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system",
             "content": "You are a competitive-programming error classifier. "
                        "Respond with only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 24 * BATCH,
        "response_format": {"type": "json_object"}
    }).encode()
    req = urllib.request.Request(
        URL, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as r:
            resp = json.load(r)
            return resp["choices"][0]["message"]["content"]
    except Exception as e:
        if attempt < MAX_RETRY:
            wait = 2 ** attempt
            print(f"  [api err: {e}] retry {attempt+1} in {wait}s", flush=True)
            time.sleep(wait)
            return call_deepseek(prompt, attempt + 1)
        print(f"  [api err: {e}] giving up on batch", flush=True)
        return ""

# ── resume / run ──────────────────────────────────────────────────────────────
done = {}
outfile = OUT / "deepseek_fair_rerun_predictions.json"
if outfile.exists():
    try:
        prev = json.load(open(outfile))
        done = {r["idx"]: r for r in prev.get("predictions", [])}
        print(f"resuming: {len(done)} done", flush=True)
    except Exception:
        done = {}

todo = list(test.itertuples())

def worker(batch_rows):
    prompt = build_batch(batch_rows)
    resp = call_deepseek(prompt)
    preds = parse_batch(resp, len(batch_rows)) if resp else [None] * len(batch_rows)
    return [{"idx": getattr(r, "Index"),
             "true_label": r.true_label,
             "response": resp,
             "prediction": p if p else "INVALID",
             "valid": p is not None,
             "problem_rating": int(r.problem_rating),
             "language": str(r.language)}
            for r, p in zip(batch_rows, preds)]

batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
print(f"batches = {len(batches)} (BATCH={BATCH}, WORKERS={WORKERS})", flush=True)
t0 = time.time()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = [ex.submit(worker, b) for b in batches]
    for fut in as_completed(futs):
        res = fut.result()
        done.update({r["idx"]: r for r in res})
        json.dump({"predictions": list(done.values())}, open(outfile, "w"))
        elapsed = time.time() - t0
        rate = len(done) / elapsed if elapsed > 0 else 0
        print(f"  {len(done)}/{len(test)}  {elapsed:.0f}s  ({rate:.2f}/s)"
              + (f"  ETA={((len(test)-len(done))/rate/60):.0f}min" if rate > 0 else ""),
              flush=True)

json.dump({"predictions": list(done.values())}, open(outfile, "w"))
print(f"DONE: {len(done)} in {time.time()-t0:.0f}s -> {outfile}", flush=True)
