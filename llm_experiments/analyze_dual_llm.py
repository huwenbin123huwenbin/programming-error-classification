#!/usr/bin/env python3
"""Comprehensive analysis: DeepSeek-V3 (online) vs Qwen2.5:3B (local) vs ML baselines.
Aligned by test-set index for paired McNemar tests.
"""
import json, math
from collections import Counter
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score

ROOT = "/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments"
CLASSES = ["WA", "TLE", "RE", "CE", "MLE"]

def load(path):
    return json.load(open(f"{ROOT}/{path}"))["predictions"]

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n
    den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den
    m = (z * (p*(1-p)/n + z*z/(4*n*n))**0.5) / den
    return (max(0, c-m), min(1, c+m))

def analyze_llm(name, preds):
    n = len(preds)
    valid = [x for x in preds if x["valid"]]
    nv = len(valid)
    invalid = n - nv
    correct_valid = sum(1 for x in valid if x["prediction"] == x["true_label"])
    acc_valid = correct_valid / nv
    correct_all = sum(1 for x in preds if x.get("valid") and x["prediction"] == x["true_label"])
    acc_all = correct_all / n
    y_true = [x["true_label"] for x in valid]
    y_pred = [x["prediction"] for x in valid]
    macro_f1 = f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)
    per_class_f1 = f1_score(y_true, y_pred, labels=CLASSES, average=None, zero_division=0)
    pred_dist = Counter(x["prediction"] for x in valid)
    true_dist = Counter(x["true_label"] for x in valid)
    print(f"\n=== {name} (n={n}) ===")
    print(f"  invalid (unparseable)    : {invalid} ({invalid/n*100:.1f}%)")
    print(f"  valid                    : {nv}")
    print(f"  accuracy (valid only)    : {acc_valid*100:.2f}%  Wilson95% [{wilson(correct_valid,nv)[0]*100:.1f}, {wilson(correct_valid,nv)[1]*100:.1f}]")
    print(f"  accuracy (all, inv=wrong) : {acc_all*100:.2f}%")
    print(f"  Macro-F1 (valid)         : {macro_f1:.4f}")
    print(f"  per-class F1             : " + ", ".join(f"{c}={per_class_f1[i]:.2f}" for i,c in enumerate(CLASSES)))
    print(f"  predicted dist           : {dict(pred_dist)}")
    print(f"  true dist                : {dict(true_dist)}")
    cm = confusion_matrix(y_true, y_pred, labels=CLASSES)
    print(f"  confusion (rows=true, cols=pred):")
    print("    " + "  ".join(f"{c:>4}" for c in CLASSES))
    for i, c in enumerate(CLASSES):
        print(f"    {c:>3}" + "  ".join(f"{cm[i][j]:>4}" for j in range(5)))
    return {
        "name": name, "n": n, "valid": nv, "invalid": invalid,
        "acc_valid": acc_valid, "acc_all": acc_all, "macro_f1": macro_f1,
        "per_class_f1": per_class_f1,
        "by_idx": {x["idx"]: (x["true_label"], x["prediction"] if x["valid"] else None) for x in preds}
    }

def mcnemar(name_a, res_a, name_b, res_b):
    """Paired McNemar on same-index samples. Returns (chi2, p, b, c)."""
    a = res_a["by_idx"]; b = res_b["by_idx"]
    common = set(a) & set(b)
    b_count = c_count = 0  # b: A right B wrong; c: A wrong B right
    for idx in common:
        ta, pa = a[idx]; tb, pb = b[idx]
        ca = (pa == ta)
        cb = (pb == tb)
        if ca and not cb: b_count += 1
        elif cb and not ca: c_count += 1
    stat = (abs(b_count - c_count) - 1) ** 2 / (b_count + c_count) if (b_count + c_count) > 0 else 0
    # p-value from chi-square with 1 df
    p = math.exp(-stat/2) * (1 + stat/2 + stat*stat/8) if stat > 0 else 1.0
    significant = stat > 3.841  # p < 0.05
    print(f"  {name_a} vs {name_b}: b={b_count}, c={c_count}, χ²={stat:.2f}, p{'<0.001' if p<0.001 else f'={p:.3f}'} → {'SIGNIFICANT' if significant else 'ns'}")
    return stat, p, b_count, c_count

# ── load ──────────────────────────────────────────────────────────────────────
ds = analyze_llm("DeepSeek-V3 (online, zero-shot)", load("deepseek_fair_rerun_predictions.json"))
qw = analyze_llm("Qwen2.5:3B (local, zero-shot)", load("qwen25_fair_rerun_predictions.json"))
ml = json.load(open(f"{ROOT}/../experiment_results/final_results_v2.json"))
# ML predictions on same test set (keyed by index)
ml_by_idx = {int(k): (v["true_label"], v["prediction"]) for k, v in ml.items()}
ml_res = {"name": "ML (GB)", "by_idx": ml_by_idx}
# Check ML accuracy
ml_correct = sum(1 for idx,(t,p) in ml_by_idx.items() if p == t)
ml_n = len(ml_by_idx)
print(f"\n=== Gradient Boosting (ML baseline, n={ml_n}) ===")
print(f"  accuracy: {ml_correct/ml_n*100:.2f}%")

# ── McNemar ───────────────────────────────────────────────────────────────────
print("\n=== McNemar tests (paired, same test set) ===")
mcnemar("GB", ml_res, "DeepSeek-V3", ds)
mcnemar("GB", ml_res, "Qwen2.5:3B", qw)
mcnemar("DeepSeek-V3", ds, "Qwen2.5:3B", qw)

# ── summary for paper ──────────────────────────────────────────────────────────
print("\n=== PAPER SUMMARY ===")
print(f"DeepSeek-V3 : acc_all={ds['acc_all']*100:.2f}%, acc_valid={ds['acc_valid']*100:.2f}%, invalid={ds['invalid']/ds['n']*100:.1f}%, macroF1={ds['macro_f1']:.4f}")
print(f"Qwen2.5:3B  : acc_all={qw['acc_all']*100:.2f}%, acc_valid={qw['acc_valid']*100:.2f}%, invalid={qw['invalid']/qw['n']*100:.1f}%, macroF1={qw['macro_f1']:.4f}")
print(f"GB (ML)     : acc={ml_correct/ml_n*100:.2f}%")
