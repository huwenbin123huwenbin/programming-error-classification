#!/usr/bin/env python3
"""Analyze the fair Qwen2.5:3B re-run predictions and produce a metrics block
to drop into the paper (replaces the old 'failed prompt' DeepSeek result)."""
import json, math
from collections import Counter, defaultdict

PRED = "/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments/qwen25_fair_rerun_predictions.json"
CLASSES = ["WA","TLE","RE","CE","MLE"]
GB_ACC = 0.9502  # Gradient Boosting, held-out test split (paper)

d = json.load(open(PRED))
preds = d["predictions"]
n_total = len(preds)
valid = [p for p in preds if p["valid"]]
n_valid = len(valid)
n_invalid = n_total - n_valid

# accuracy: (a) over valid only, (b) over all (invalid = wrong)
correct_valid = sum(1 for p in valid if p["prediction"] == p["true_label"])
acc_valid = correct_valid / n_valid if n_valid else 0
acc_all = correct_valid / n_total if n_total else 0
invalid_rate = n_invalid / n_total if n_total else 0

# per-class P/R/F1 over VALID predictions (treat invalid as not predicted)
tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
for p in valid:
    pred, true = p["prediction"], p["true_label"]
    if pred == true: tp[true]+=1
    else: fp[pred]+=1; fn[true]+=1
per_class={}
f1s=[]
for c in CLASSES:
    prec = tp[c]/(tp[c]+fp[c]) if (tp[c]+fp[c]) else 0
    rec  = tp[c]/(tp[c]+fn[c]) if (tp[c]+fn[c]) else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec) else 0
    per_class[c]=(prec,rec,f1); f1s.append(f1)
macro_f1_valid = sum(f1s)/len(f1s)

# confusion matrix (valid only)
cm = {t:{p:0 for p in CLASSES} for t in CLASSES}
for p in valid:
    cm[p["true_label"]][p["prediction"]]+=1

# majority-class baseline (WA) on test
true_counts = Counter(p["true_label"] for p in preds)
maj = max(true_counts.values())/n_total

# prediction distribution
pred_dist = Counter(p["prediction"] for p in valid)

print("=== FAIR LLM RE-RUN (local Qwen2.5:3B) ===")
print(f"n_total={n_total}  n_valid={n_valid}  n_invalid={n_invalid}")
print(f"invalid_rate={invalid_rate*100:.1f}%")
print(f"accuracy (valid only)={acc_valid*100:.2f}%   accuracy (all, invalid=wrong)={acc_all*100:.2f}%")
print(f"macro-F1 (valid)={macro_f1_valid*100:.3f}")
print(f"majority-class (WA) baseline={maj*100:.1f}%")
print(f"prediction distribution (valid): {dict(pred_dist)}")
print("\nper-class P/R/F1 (valid):")
for c in CLASSES:
    prec,rec,f1=per_class[c]
    print(f"  {c:3s} P={prec*100:5.1f} R={rec*100:5.1f} F1={f1*100:5.1f}  (n_true={true_counts.get(c,0)})")
print("\nconfusion matrix (rows=true, cols=pred):")
print("       "+" ".join(f"{c:>5s}" for c in CLASSES))
for t in CLASSES:
    print(f"{t:3s}  "+" ".join(f"{cm[t][p]:5d}" for p in CLASSES))

# ---- markdown block for paper ----
md = f"""| Model | Accuracy (valid) | Accuracy (all) | Macro-F1 | Invalid outputs |
|-------|-------------------|----------------|----------|-----------------|
| Gradient Boosting (ML) | 95.02% | 95.02% | 0.871 | 0% |
| Qwen2.5-3B (LLM, fair protocol) | {acc_valid*100:.2f}% | {acc_all*100:.2f}% | {macro_f1_valid:.3f} | {invalid_rate*100:.1f}% |"""
print("\n--- TABLE ROW (paper) ---\n"+md)
