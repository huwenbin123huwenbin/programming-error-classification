#!/usr/bin/env python3
"""Analyze the fair Qwen2.5:3B re-run vs the ML baselines.
Reads qwen25_fair_rerun_predictions.json (produced by run_qwen_fair_rerun.py)
and the ML predictions (final_results_v2.json) to compute a fair comparison.
"""
import json, os
from collections import Counter, defaultdict
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score

ROOT = "/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments"
PREDS = os.path.join(ROOT, "qwen25_fair_rerun_predictions.json")
MLPREDS = os.path.join(ROOT, "final_results_v2.json")  # ML model predictions on same test set
CLASSES = ["WA", "TLE", "RE", "CE", "MLE"]

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n
    den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den
    m = (z * (p*(1-p)/n + z*z/(4*n*n))**0.5) / den
    return (max(0, c-m), min(1, c+m))

def main():
    d = json.load(open(PREDS))
    pr = d["predictions"]
    n = len(pr)
    valid = [x for x in pr if x["valid"]]
    nv = len(valid)
    invalid = n - nv
    # overall accuracy (valid only) and (all, invalid treated as wrong)
    correct_valid = sum(1 for x in valid if x["prediction"] == x["true_label"])
    acc_valid = correct_valid / nv
    correct_all = sum(1 for x in pr if x.get("valid") and x["prediction"] == x["true_label"])
    acc_all = correct_all / n
    print(f"== Qwen2.5:3B fair re-run (n={n}) ==")
    print(f"  invalid (unparseable) : {invalid} ({invalid/n*100:.1f}%)")
    print(f"  valid                 : {nv}")
    print(f"  accuracy (valid only) : {acc_valid*100:.2f}%  Wilson95% [{wilson(correct_valid,nv)[0]*100:.1f}, {wilson(correct_valid,nv)[1]*100:.1f}]")
    print(f"  accuracy (all, inv=wrong): {acc_all*100:.2f}%")
    # predicted distribution
    pred_dist = Counter(x["prediction"] if x["valid"] else "INVALID" for x in pr)
    true_dist = Counter(x["true_label"] for x in pr)
    print("  predicted dist:", dict(pred_dist))
    print("  true dist     :", dict(true_dist))
    # per-class on valid
    print("\n  per-class (valid predictions):")
    y_true = [x["true_label"] for x in valid]
    y_pred = [x["prediction"] for x in valid]
    rep = classification_report(y_true, y_pred, labels=CLASSES, output_dict=True, zero_division=0)
    for c in CLASSES:
        print(f"    {c}: P={rep[c]['precision']:.2f} R={rep[c]['recall']:.2f} F1={rep[c]['f1-score']:.2f} support={int(rep[c]['support'])}")
    macros = f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)
    print(f"    Macro-F1 (valid): {macros:.4f}")
    # confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=CLASSES)
    print("\n  confusion (rows=true, cols=pred), labels", CLASSES)
    for i, c in enumerate(CLASSES):
        print(f"    {c:4}:", cm[i].tolist())
    # WA<->RE confusion specifically
    wa_idx, re_idx = CLASSES.index("WA"), CLASSES.index("RE")
    wa_as_re = cm[wa_idx][re_idx]; re_as_wa = cm[re_idx][wa_idx]
    print(f"\n  WA->RE misclass: {wa_as_re}   RE->WA misclass: {re_as_wa}")
    # McNemar vs best ML (GB 95.02%) -- need ML predictions aligned by idx
    if os.path.exists(MLPREDS):
        ml = json.load(open(MLPREDS))
        # align by index
        mlmap = {}
        if isinstance(ml, dict) and "predictions" in ml:
            for x in ml["predictions"]:
                mlmap[int(x.get("idx", x.get("index", -1)))] = x
        elif isinstance(ml, list):
            for x in ml:
                mlmap[int(x.get("idx", x.get("index", -1)))] = x
        agree_q, disagree_q = 0, 0
        b, c = 0, 0  # McNemar cells: qwen correct & ml wrong (c), qwen wrong & ml correct (b)
        common = 0
        for x in pr:
            i = int(x["idx"])
            if i in mlmap:
                m = mlmap[i]
                mlp = m.get("prediction", m.get("y_pred"))
                # ML treated as correct if mlp == true
                qc = x.get("valid") and x["prediction"] == x["true_label"]
                mc = (mlp == x["true_label"])
                common += 1
                if qc and not mc: c += 1
                if (not qc) and mc: b += 1
        if (b+c) > 0:
            chi2 = (abs(b-c)-1)**2 / (b+c)
            sig = "Yes" if chi2 > 3.841 else "No"
            print(f"\n  McNemar Qwen2.5:3B vs ML-best (n={common} aligned): b={b} c={c} chi2={chi2:.2f} p<0.05? {sig}")
    # save summary json
    summary = {
        "n": n, "valid": nv, "invalid": invalid,
        "acc_valid": acc_valid, "acc_all": acc_all,
        "pred_dist": dict(pred_dist), "true_dist": dict(true_dist),
        "macro_f1_valid": macros,
        "wa_as_re": int(wa_as_re), "re_as_wa": int(re_as_wa),
        "per_class": {c: {"P": rep[c]['precision'], "R": rep[c]['recall'],
                           "F1": rep[c]['f1-score'], "support": int(rep[c]['support'])} for c in CLASSES},
    }
    json.dump(summary, open(os.path.join(ROOT, "fair_rerun_summary.json"), "w"), indent=2)
    print("\n  saved fair_rerun_summary.json")

if __name__ == "__main__":
    main()
