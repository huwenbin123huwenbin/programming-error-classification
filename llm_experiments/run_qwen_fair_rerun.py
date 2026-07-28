#!/usr/bin/env python3
"""
Fair LLM re-run for SCI1 paper.

Apples-to-apples comparison: Qwen2.5:3B with same 7 metadata features
as the ML models, grammar-constrained output, and same test split.
Self-healing: restarts Ollama on hang/failure.
"""
import json, re, os, urllib.request, time, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT   = Path("/Users/mac/Desktop/SCI1")
DATA   = ROOT / "01_原始数据" / "codeforces_final_real.csv"
OUT    = ROOT / "06_论文定稿" / "llm_experiments"
OUT.mkdir(parents=True, exist_ok=True)

MODEL        = "qwen2.5:3b"
URL          = "http://localhost:11434/api/generate"
OLLAMA_BIN   = "/usr/local/bin/ollama"
BATCH        = 8       # samples per Ollama call
WORKERS      = 1       # Ollama serialises to one at a time on CPU
NTHREAD      = 4
CALL_TIMEOUT = 60      # seconds; hang -> restart Ollama
CLASSES      = ["WA", "TLE", "RE", "CE", "MLE"]

# ── load data ────────────────────────────────────────────────────────────────
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

# ── language family simplification (for clean prompt) ─────────────────────────
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

# ── prompt construction ─────────────────────────────────────────────────────
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
    prompt = EX + "Classify each item. Return a JSON object with key 'verdicts' = " \
                 "array of one token per item, in the same order.\n" \
                 + "\n".join(lines) + "\nVerdicts:"
    return prompt

FORMAT_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {
        "type": "array",
        "items": {"type": "string", "enum": CLASSES}}},
    "required": ["verdicts"]}

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

# ── Ollama self-healing ─────────────────────────────────────────────────────
def restart_ollama():
    for cmd in ["pkill -9 -f 'ollama serve'", "pkill -9 -f ollama"]:
        subprocess.run(cmd, shell=True, check=False)
    time.sleep(3)
    with open("/tmp/ollama.log", "a") as lf:
        subprocess.Popen([OLLAMA_BIN, "serve"],
                         stdout=lf, stderr=lf, start_new_session=True)
    for _ in range(30):
        try:
            urllib.request.urlopen(
                urllib.request.Request("http://localhost:11434/api/tags"), timeout=3)
            return True
        except Exception:
            time.sleep(2)
    return False

def ollama_up():
    try:
        urllib.request.urlopen(
            urllib.request.Request("http://localhost:11434/api/tags"), timeout=3)
        return True
    except Exception:
        return False

def call_ollama(prompt):
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 40, "num_thread": NTHREAD},
        "format": FORMAT_SCHEMA}).encode()
    for attempt in range(2):
        if not ollama_up():
            restart_ollama()
        try:
            req = urllib.request.Request(URL, data=body,
                                        headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as r:
                return json.load(r).get("response", "")
        except Exception as e:
            print(f"  [call err: {e}] restarting ollama...", flush=True)
            restart_ollama()
    return ""  # batch marked all-INVALID

# ── resume / run ────────────────────────────────────────────────────────────
done = {}
outfile = OUT / "qwen25_fair_rerun_predictions.json"
if outfile.exists():
    try:
        prev = json.load(open(outfile))
        done = {r["idx"]: r for r in prev.get("predictions", [])}
        print(f"resuming: {len(done)} done", flush=True)
    except Exception:
        done = {}

# use positional index (0..len-1) for alignment with ML predictions
todo = list(test.itertuples())

def worker(batch_rows):
    prompt = build_batch(batch_rows)
    resp = call_ollama(prompt)
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
              f"  ETA={((len(test)-len(done))/rate/60):.0f}min" if rate > 0 else "",
              flush=True)

json.dump({"predictions": list(done.values())}, open(outfile, "w"))
print(f"DONE: {len(done)} in {time.time()-t0:.0f}s -> {outfile}", flush=True)
