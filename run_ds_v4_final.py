#!/usr/bin/env python3
"""DeepSeek-V4-flash full experiment: 2672 samples."""
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
    if not s:
        return "Other"
    base = s.strip().lower()
    for k, v in LANG_FAMILY.items():
        if k in base:
            return v
    return "Other"

# Load CSV
rows = []
with open(CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        ok = all(r.get(k,"").strip() not in ("","nan","N/A") for k in
                 ["problem_rating","verdict","language","time_consumed_ms","memory_kb","passed_test_count","problem_index"])
        if ok and r["verdict"].strip().upper() in VERDICTS:
            rows.append(r)

print(f"Total: {len(rows)} samples")

# sklearn train_test_split(random_state=42, test_size=0.2, stratify)
rng = random.Random(42)
indices = list(range(len(rows)))
rng.shuffle(indices)
n_test = int(len(rows) * 0.2)
test = [rows[i] for i in indices[:n_test]]
print(f"Test set: {len(test)} samples")

PROMPT_TPL = (
    "Programming Error Classification Task.\n"
    "You are given submission metadata from the Codeforces platform.\n"
    "Based ONLY on the metadata below, classify the error type.\n\n"
    "Metadata:\n"
    "- Time consumed: {tc} ms\n"
    "- Memory consumed: {mc} KB\n"
    "- Passed test count: {ptc}\n"
    "- Problem rating: {pr}\n"
    "- Programming language: {lang}\n\n"
    "Classify the error type. Choose ONE from: WA, TLE, RE, CE, MLE.\n"
    "WA = Wrong Answer (logic error, wrong output)\n"
    "TLE = Time Limit Exceeded (algorithm too slow)\n"
    "RE = Runtime Error (crash, segmentation fault)\n"
    "CE = Compilation Error (syntax/type error)\n"
    "MLE = Memory Limit Exceeded (out of memory)\n\n"
    "Answer with ONLY the verdict word: WA, TLE, RE, CE, or MLE."
)

def make_prompt(row):
    lang = lang_family(row.get("language",""))
    return PROMPT_TPL.format(
        tc=row.get("time_consumed_ms","N/A"),
        mc=row.get("memory_kb","N/A"),
        ptc=row.get("passed_test_count","N/A"),
        pr=row.get("problem_rating","N/A"),
        lang=lang,
    )

results = []
start = time.time()
total = len(test)

for i, row in enumerate(test):
    prompt = make_prompt(row)
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0
    })

    verdict = "INVALID"
    valid = False
    tokens = 0

    for attempt in range(3):
        t0 = time.time()
        try:
            r = subprocess.run(
                ["curl", "-s", API,
                 "-H", "Authorization: Bearer " + KEY,
                 "-H", "Content-Type: application/json",
                 "-d", payload,
                 "--max-time", "120"],
                capture_output=True, text=True, timeout=130
            )
            elapsed = time.time() - t0
            raw = r.stdout

            if not raw:
                time.sleep(2 ** attempt)
                continue

            try:
                d = json.loads(raw)
                if "error" in d:
                    time.sleep(2 ** attempt)
                    continue
                content = d["choices"][0]["message"].get("content", "") or ""
                tokens = d.get("usage", {}).get("total_tokens", 0)
                for v in VERDICTS:
                    if v in content:
                        verdict = v
                        valid = True
                        break
                break
            except (json.JSONDecodeError, KeyError, IndexError):
                time.sleep(2 ** attempt)
        except subprocess.TimeoutExpired:
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)

    true_lbl = row["verdict"].strip().upper()
    results.append({
        "idx": i,
        "true_label": true_lbl,
        "predicted": verdict,
        "valid": valid,
        "tokens": tokens,
    })

    if (i + 1) % PROGRESS == 0 or (i + 1) == total:
        elapsed = time.time() - start
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (total - i - 1) / rate / 3600 if rate > 0 else 0
        valid_r = [r for r in results if r["valid"]]
        correct = [r for r in valid_r if r["predicted"] == r["true_label"]]
        acc = len(correct) / len(valid_r) * 100 if valid_r else 0
        print(f"  [{i+1}/{total}] valid={len(valid_r)} acc={acc:.1f}% {rate:.1f}/s ETA={eta:.1f}h")

    time.sleep(0.3)

# Save
with open(OUT, "w") as f:
    json.dump({"predictions": results}, f, indent=2)

elapsed_total = time.time() - start
valid_list = [r for r in results if r["valid"]]
correct_list = [r for r in valid_list if r["predicted"] == r["true_label"]]
acc_v = len(correct_list) / len(valid_list) * 100 if valid_list else 0
acc_f = len(correct_list) / len(results) * 100 if results else 0

print(f"\n=== DeepSeek-V4-flash RESULTS ===")
print(f"Total: {len(results)} | Valid: {len(valid_list)} ({len(valid_list)/len(results)*100:.1f}%) | Invalid: {len(results)-len(valid_list)}")
print(f"Accuracy (valid): {acc_v:.2f}% | Accuracy (full): {acc_f:.2f}%")
print(f"Time: {elapsed_total/3600:.2f}h | Rate: {len(results)/elapsed_total:.2f}/s")
print(f"Saved: {OUT}")

print("\nPer-class (valid):")
for v in VERDICTS:
    ct = [r for r in results if r["true_label"] == v and r["valid"]]
    cc = [r for r in ct if r["predicted"] == v]
    p = len(cc) / len(ct) * 100 if ct else 0
    r_all = len([r for r in results if r["predicted"] == v and r["valid"]])
    r_rec = len(cc) / r_all * 100 if r_all else 0
    print(f"  {v}: n={len(ct)}, P={p:.1f}%, R={r_rec:.1f}%")

print("\nConfusion matrix (rows=true, cols=pred):")
header = "%10s" % "" + "".join("%7s" % v for v in VERDICTS)
print(header)
for tv in VERDICTS:
    row = "%10s" % tv
    for pv in VERDICTS:
        cnt = len([r for r in results if r["true_label"] == tv and r["predicted"] == pv])
        row += "%7d" % cnt
    print(row)
