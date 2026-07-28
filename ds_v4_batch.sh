#!/bin/bash
# DeepSeek-V4-flash full experiment: 2672 samples
CSV="/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
API="https://api.deepseek.com/v1/chat/completions"
KEY="__DEEPSEEK_API_KEY_REDACTED__"
MODEL="deepseek-v4-flash"
LOG="ds_v4_full_log.txt"
OUT="ds_v4_predictions.json"
PROGRESS=25

echo "=== DeepSeek-V4-flash Full Run ===" | tee $LOG
echo "Started: $(date)" | tee -a $LOG

/usr/bin/python3 << 'PYEOF' 2>&1 | tee -a $LOG
import csv, json, random, subprocess, time

CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
OUT = "/Users/mac/Desktop/SCI1/06_论文定稿/ds_v4_predictions.json"
MODEL = "deepseek-v4-flash"
API = "https://api.deepseek.com/v1/chat/completions"
KEY = "__DEEPSEEK_API_KEY_REDACTED__"
PROGRESS = 25
VERDICTS = ["WA", "TLE", "RE", "CE", "MLE"]

LANG_FAMILY = {
    "c++": "C++", "c++14": "C++", "c++17": "C++", "c++20": "C++",
    "c++23": "C++", "gnu c++": "C++", "gnu c++0x": "C++", "gnu c++11": "C++",
    "ms c++": "C++", "pypy": "PyPy", "python": "Python",
    "java": "Java", "java 21": "Java", "javascript": "JS", "node.js": "JS",
    "c": "C", "c11": "C", "go": "Go", "rust": "Rust",
    "c#": "C#", "ruby": "Ruby", "scala": "Scala", "php": "PHP",
    "kotlin": "Kotlin", "haskell": "Haskell", "f#": "F#",
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

print(f"Loaded {len(rows)} total samples", flush=True)

# sklearn train_test_split(random_state=42, test_size=0.2, stratify)
rng = random.Random(42)
indices = list(range(len(rows)))
rng.shuffle(indices)
n_test = int(len(rows) * 0.2)
test = [rows[i] for i in indices[:n_test]]
print(f"Test set: {len(test)} samples", flush=True)

PROMPT = """Programming Error Classification Task.
You are given submission metadata from the Codeforces competitive programming platform. Based ONLY on the metadata below, classify the error type.
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
total = len(test)

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
    
    verdict = "INVALID"
    valid = False
    error_msg = ""
    tokens_used = 0
    
    for attempt in range(3):
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
            
            if not raw:
                error_msg = f"empty_response (attempt {attempt+1})"
                time.sleep(2**attempt)
                continue
            
            try:
                d = json.loads(raw)
                if "error" in d:
                    error_msg = f"API_error: {d['error']}"
                    time.sleep(2**attempt)
                    continue
                msg = d["choices"][0]["message"]
                content = msg.get("content","") or ""
                tokens_used = d.get("usage",{}).get("total_tokens",0)
                for v in VERDICTS:
                    if v in content:
                        verdict = v
                        valid = True
                        break
                break
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                error_msg = f"parse_error: {e} (attempt {attempt+1})"
                time.sleep(2**attempt)
        except subprocess.TimeoutExpired:
            error_msg = f"timeout (attempt {attempt+1})"
            time.sleep(2**attempt)
        except Exception as e:
            error_msg = f"exception: {e} (attempt {attempt+1})"
            time.sleep(2**attempt)
    
    results.append({
        "idx": i,
        "true_label": row["verdict"].strip().upper(),
        "predicted": verdict,
        "valid": valid,
        "tokens": tokens_used,
    })

    if (i+1) % PROGRESS == 0 or (i+1) == total:
        elapsed = time.time() - start
        rate = (i+1)/elapsed if elapsed > 0 else 0
        eta = (total - i - 1)/rate/3600 if rate > 0 else 0
        valid_r = [r for r in results if r["valid"]]
        correct = [r for r in valid_r if r["predicted"]==r["true_label"]]
        acc = len(correct)/len(valid_r)*100 if valid_r else 0
        print(f"  [{i+1}/{total}] valid={len(valid_r)} acc={acc:.1f}% {rate:.1f}/s ETA={eta:.1f}h", flush=True)
    
    time.sleep(0.3)

# Save
with open(OUT,"w") as f:
    json.dump({"predictions":results}, f, indent=2)

elapsed_total = time.time() - start
valid = [r for r in results if r["valid"]]
correct = [r for r in valid if r["predicted"]==r["true_label"]]
acc_v = len(correct)/len(valid)*100 if valid else 0
acc_f = len(correct)/len(results)*100 if results else 0
print(f"\n=== RESULTS ===", flush=True)
print(f"Total: {len(results)} | Valid: {len(valid)} ({len(valid)/len(results)*100:.1f}%) | Invalid: {len(results)-len(valid)}", flush=True)
print(f"Accuracy (valid): {acc_v:.2f}% | Accuracy (full): {acc_f:.2f}%", flush=True)
print(f"Time: {elapsed_total/3600:.2f}h | Rate: {len(results)/elapsed_total:.2f}/s", flush=True)
print(f"Saved: {OUT}", flush=True)

print("\nPer-class (valid):", flush=True)
for v in VERDICTS:
    ct = [r for r in results if r["true_label"]==v and r["valid"]]
    cc = [r for r in ct if r["predicted"]==v]
    p = len(cc)/len(ct)*100 if ct else 0
    r_all = len([r for r in results if r["predicted"]==v and r["valid"]])
    r_val = len(cc)/r_all*100 if r_all else 0
    print(f"  {v}: n={len(ct)}, P={p:.1f}%, R={r_val:.1f}%", flush=True)

print("\nConfusion matrix (rows=true, cols=pred):", flush=True)
header = f"{'':>10}" + "".join(f"{v:>7}" for v in VERDICTS)
print(header, flush=True)
for tv in VERDICTS:
    row = f"{tv:>10}"
    for pv in VERDICTS:
        cnt = len([r for r in results if r["true_label"]==tv and r["predicted"]==pv])
        row += f"{cnt:>7}"
    print(row, flush=True)

print(f"\nCompleted: $(date)", flush=True)
PYEOF

echo "Script finished: $(date)" >> $LOG
