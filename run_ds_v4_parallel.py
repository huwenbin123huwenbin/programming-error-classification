#!/usr/bin/env python3
import os
"""DeepSeek-V4-flash parallel experiment: 2672 samples, concurrent workers."""
import csv, json, random, subprocess, time, threading, queue

CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
OUT = "/Users/mac/Desktop/SCI1/06_论文定稿/ds_v4_predictions.json"
MODEL = "deepseek-v4-flash"
API = "https://api.deepseek.com/v1/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
WORKERS = 3  # concurrent API calls
REPORT_EVERY = 25
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

# Load and split data
rows = []
with open(CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        ok = all(r.get(k,"").strip() not in ("","nan","N/A") for k in
                 ["problem_rating","verdict","language","time_consumed_ms","memory_kb","passed_test_count","problem_index"])
        if ok and r["verdict"].strip().upper() in VERDICTS:
            rows.append(r)

rng = random.Random(42)
indices = list(range(len(rows)))
rng.shuffle(indices)
n_test = int(len(rows) * 0.2)
test = [rows[i] for i in indices[:n_test]]
print(f"Total: {len(rows)} | Test: {len(test)} | Workers: {WORKERS}", flush=True)

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

def call_api(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            payload = json.dumps({
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0
            })
            t0 = time.time()
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
                time.sleep(2**attempt); continue
            try:
                d = json.loads(raw)
                if "error" in d:
                    time.sleep(2**attempt); continue
                content = d["choices"][0]["message"].get("content","") or ""
                verdict = "INVALID"
                for v in VERDICTS:
                    if v in content: verdict = v; break
                return verdict, verdict in VERDICTS, elapsed
            except (json.JSONDecodeError, KeyError, IndexError):
                time.sleep(2**attempt); continue
        except Exception:
            time.sleep(2**attempt); continue
    return "INVALID", False, 0

# Producer-consumer pattern
result_queue = queue.Queue()
stop_event = threading.Event()
results_lock = threading.Lock()
all_results = []
results_cv = threading.Condition(results_lock)
next_report_count = REPORT_EVERY

def worker(worker_id, work_queue):
    """Worker thread: take samples from queue, process, put in result_queue."""
    while not stop_event.is_set():
        try:
            item = work_queue.get(timeout=1)
            if item is None:
                work_queue.task_done()
                break
            i, row = item
            prompt = make_prompt(row)
            verdict, valid, elapsed = call_api(prompt)
            true_lbl = row["verdict"].strip().upper()
            result = {"idx": i, "true_label": true_lbl, "predicted": verdict, "valid": valid}
            result_queue.put(result)
            work_queue.task_done()
        except queue.Empty:
            break

# Fill work queue
work_queue = queue.Queue()
for i, row in enumerate(test):
    work_queue.put((i, row))

# Start workers
threads = []
for w in range(WORKERS):
    t = threading.Thread(target=worker, args=(w, work_queue))
    t.start()
    threads.append(t)

# Collect results
start_time = time.time()
total = len(test)
collected = 0

while collected < total:
    try:
        result = result_queue.get(timeout=300)  # 5min timeout
        with results_lock:
            all_results.append(result)
            collected += 1
        
        if collected % REPORT_EVERY == 0 or collected == total:
            elapsed = time.time() - start_time
            rate = collected / elapsed if elapsed > 0 else 0
            eta = (total - collected) / rate / 3600 if rate > 0 else 0
            valid_r = [r for r in all_results if r["valid"]]
            correct = [r for r in valid_r if r["predicted"] == r["true_label"]]
            acc = len(correct)/len(valid_r)*100 if valid_r else 0
            print(f"  [{collected}/{total}] valid={len(valid_r)} acc={acc:.1f}% "
                  f"{rate:.2f}/s ETA={eta:.1f}h", flush=True)
        
        result_queue.task_done()
    except queue.Empty:
        print("WARNING: queue empty, waiting...", flush=True)
        break

# Signal stop
stop_event.set()
for t in threads:
    t.join(timeout=5)

# Sort and save
all_results.sort(key=lambda x: x["idx"])
with open(OUT, "w") as f:
    json.dump({"predictions": all_results}, f, indent=2)

total_elapsed = time.time() - start_time
valid_l = [r for r in all_results if r["valid"]]
correct_l = [r for r in valid_l if r["predicted"] == r["true_label"]]
acc_v = len(correct_l)/len(valid_l)*100 if valid_l else 0
acc_f = len(correct_l)/len(all_results)*100 if all_results else 0

print(f"\n=== DeepSeek-V4-flash RESULTS ===")
print(f"Total: {len(all_results)} | Valid: {len(valid_l)} | Invalid: {len(all_results)-len(valid_l)}")
print(f"Accuracy (valid): {acc_v:.2f}% | Accuracy (full): {acc_f:.2f}%")
print(f"Time: {total_elapsed/3600:.2f}h | Rate: {len(all_results)/total_elapsed:.2f}/s")
print(f"Saved: {OUT}")

print("\nPer-class:")
for v in VERDICTS:
    ct = [r for r in all_results if r["true_label"]==v and r["valid"]]
    cc = [r for r in ct if r["predicted"]==v]
    p = len(cc)/len(ct)*100 if ct else 0
    r_all = len([r for r in all_results if r["predicted"]==v and r["valid"]])
    r_rec = len(cc)/r_all*100 if r_all else 0
    print(f"  {v}: n={len(ct)}, P={p:.1f}%, R={r_rec:.1f}%")

print("\nConfusion matrix:")
header = "%10s" % "" + "".join("%7s" % v for v in VERDICTS)
print(header)
for tv in VERDICTS:
    row = "%10s" % tv
    for pv in VERDICTS:
        cnt = len([r for r in all_results if r["true_label"]==tv and r["predicted"]==pv])
        row += "%7d" % cnt
    print(row)
