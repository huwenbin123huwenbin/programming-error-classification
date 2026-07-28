#!/bin/bash
# DeepSeek-V4-flash test: 4 samples
CSV="/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
API="https://api.deepseek.com/v1/chat/completions"
KEY="__DEEPSEEK_API_KEY_REDACTED__"
MODEL="deepseek-v4-flash"
LOG="ds_v4_test_log.txt"
OUT="ds_v4_predictions.json"

echo "Starting test at $(date)" >> $LOG

# Use Python to load data and generate prompts
/usr/bin/python3 << 'PYEOF' >> $LOG
import csv, json, random, subprocess, time

API = "https://api.deepseek.com/v1/chat/completions"
KEY = "__DEEPSEEK_API_KEY_REDACTED__"
MODEL = "deepseek-v4-flash"
CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
OUT = "/Users/mac/Desktop/SCI1/06_论文定稿/ds_v4_predictions.json"

VERDICTS = ["WA", "TLE", "RE", "CE", "MLE"]

LANG_FAMILY = {
    "c++": "C++", "c++14": "C++", "c++17": "C++", "c++20": "C++",
    "c++23": "C++", "gnu c++": "C++", "gnu c++0x": "C++", "gnu c++11": "C++",
    "pypy": "PyPy", "python": "Python",
    "java": "Java", "javascript": "JS", "node.js": "JS",
    "c": "C", "c11": "C", "go": "Go", "rust": "Rust",
    "c#": "C#", "ruby": "Ruby", "scala": "Scala", "php": "PHP",
}

def lang_family(s):
    if not s: return "Other"
    base = s.strip().lower()
    for k, v in LANG_FAMILY.items():
        if k in base: return v
    return "Other"

# Load CSV
rows = []
with open(CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        ok = all(r.get(k,"").strip() not in ("","nan","N/A") for k in
                 ["problem_rating","verdict","language","time_consumed_ms","memory_kb","passed_test_count","problem_index"])
        if ok and r["verdict"].strip().upper() in VERDICTS:
            rows.append(r)

# sklearn-like stratified split (random_state=42)
rng = random.Random(42)
indices = list(range(len(rows)))
rng.shuffle(indices)
n_test = int(len(rows) * 0.2)
test = [rows[i] for i in indices[:n_test]][:4]  # only 4 samples

print(f"Loaded {len(test)} test samples", flush=True)

PROMPT = """Programming Error Classification Task.
You are given submission metadata from the Codeforces platform. Based ONLY on the metadata below, classify the error type.
Metadata:
- Time consumed: {time_consumed_ms} ms
- Memory consumed: {memory_kb} KB
- Passed test count: {passed_test_count}
- Problem rating: {problem_rating}
- Programming language: {language}
Classify the error type. Choose ONE from: WA, TLE, RE, CE, MLE.
WA = Wrong Answer (logic error, wrong output)
TLE = Time Limit Exceeded (algorithm too slow)
RE = Runtime Error (crash, segmentation fault)
CE = Compilation Error (syntax/type error)
MLE = Memory Limit Exceeded (out of memory)
Answer with ONLY the verdict word: WA, TLE, RE, CE, or MLE."""

results = []
start = time.time()
for i, row in enumerate(test):
    lang = lang_family(row.get("language",""))
    prompt = PROMPT.format(
        time_consumed_ms=row.get("time_consumed_ms","N/A"),
        memory_kb=row.get("memory_kb","N/A"),
        passed_test_count=row.get("passed_test_count","N/A"),
        problem_rating=row.get("problem_rating","N/A"),
        language=lang,
    )
    payload = json.dumps({"model":MODEL,"messages":[{"role":"user","content":prompt}],"max_tokens":3000,"temperature":0})
    
    t0 = time.time()
    try:
        r = subprocess.run(
            ["curl","-s",API,
             "-H",f"Authorization: Bearer {KEY}",
             "-H","Content-Type: application/json",
             "-d",payload,
             "--max-time","120"],
            capture_output=True, text=True, timeout=130
        )
        elapsed = time.time() - t0
        raw = r.stdout
        print(f"Sample {i+1}: curl returned in {elapsed:.1f}s, len={len(raw)}", flush=True)
        if not raw:
            print(f"  EMPTY RESPONSE stderr={r.stderr[:200]}", flush=True)
            results.append({"idx":i,"true":row["verdict"].upper(),"pred":"INVALID","valid":False,"error":r.stderr[:200]})
            continue
        try:
            d = json.loads(raw)
            if "error" in d:
                print(f"  API ERROR: {d['error']}", flush=True)
                results.append({"idx":i,"true":row["verdict"].upper(),"pred":"INVALID","valid":False,"error":str(d["error"])})
            else:
                content = d["choices"][0]["message"].get("content","")
                # extract verdict
                verdict = "INVALID"
                for v in VERDICTS:
                    if v in content:
                        verdict = v
                        break
                valid = verdict in VERDICTS
                print(f"  {row['verdict'].upper()} -> {verdict} (valid={valid})", flush=True)
                results.append({"idx":i,"true":row["verdict"].upper(),"pred":verdict,"valid":valid})
        except json.JSONDecodeError as e:
            print(f"  JSON ERROR: {e} raw={raw[:200]}", flush=True)
            results.append({"idx":i,"true":row["verdict"].upper(),"pred":"INVALID","valid":False,"error":str(e)})
    except subprocess.TimeoutExpired:
        print(f"Sample {i+1}: TIMEOUT", flush=True)
        results.append({"idx":i,"true":row["verdict"].upper(),"pred":"INVALID","valid":False,"error":"timeout"})
    time.sleep(0.5)

# Save
with open(OUT,"w") as f:
    json.dump({"predictions":results}, f, indent=2)
print(f"Saved to {OUT}", flush=True)

# Summary
valid = [r for r in results if r["valid"]]
correct = [r for r in valid if r["pred"]==r["true"]]
print(f"\nValid: {len(valid)}/{len(results)}, Correct: {len(correct)}, Acc: {len(correct)/max(len(valid),1)*100:.1f}%", flush=True)
PYEOF

echo "Done at $(date)" >> $LOG
