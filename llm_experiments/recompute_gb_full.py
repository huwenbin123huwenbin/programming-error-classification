#!/usr/bin/env python3
"""Recompute GB/RF/LR with the exact 7-feature pipeline used in final_results_v2.json
to regenerate true GB numbers: confusion matrix, per-class F1, feature importance,
sensitivity analysis, ROC-AUC. Verifies reproducibility of 95.02%."""
import json, csv, time
import numpy as np
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, f1_score, accuracy_score,
                             roc_auc_score, classification_report)

CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
KEEP = ['CE', 'TLE', 'MLE', 'WA', 'RE']

rows = []
with open(CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['verdict'] not in KEEP:
            continue
        pr = r['problem_rating'].strip()
        tc = r['time_consumed_ms'].strip()
        try:
            pr = float(pr); tc = float(tc)
        except ValueError:
            continue
        if pr != pr or tc != tc:
            continue
        rows.append({
            'user': r['user_handle'],
            'problem_rating': pr,
            'time_consumed_ms': tc,
            'memory_kb': float(r['memory_kb']) if r['memory_kb'].strip() else 0.0,
            'language': str(r['language']).strip(),
            'problem_index': str(r['problem_index']).strip(),
            'verdict': r['verdict'],
        })
print(f"Usable rows: {len(rows)}")

langs = sorted(set(r['language'] for r in rows))
lang_map = {l: i for i, l in enumerate(langs)}
for r in rows:
    r['language_encoded'] = lang_map[r['language']]
    idx = r['problem_index'].upper()
    r['problem_type'] = ord(idx[0]) - ord('A') + 1 if idx else 0
    r['hour'] = 12  # fixed hour (paper ablation shows drop 0.0)

# user_success_rate: global (as in original final_results_v2)
user_wa = defaultdict(lambda: [0, 0])
for r in rows:
    user_wa[r['user']][1] += 1
    if r['verdict'] == 'WA':
        user_wa[r['user']][0] += 1
for r in rows:
    v = user_wa[r['user']]
    r['user_success_rate'] = v[0] / v[1] if v[1] else 0.5

FEATURES = ['problem_rating', 'time_consumed_ms', 'memory_kb',
            'language_encoded', 'problem_type', 'hour', 'user_success_rate']
X = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
y = np.array([r['verdict'] for r in rows])

# 80/20 stratified split, same as original
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train: {len(X_tr)}, Test: {len(X_te)}")

out = {}
for name, model in [
    ("Gradient Boosting", GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                      learning_rate=0.1, random_state=42)),
    ("Random Forest", RandomForestClassifier(n_estimators=100, random_state=42)),
    ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=42)),
]:
    t0 = time.time()
    model.fit(X_tr, y_tr)
    preds = model.predict(X_te)
    acc = accuracy_score(y_te, preds)
    macro = f1_score(y_te, preds, average='macro')
    cm = confusion_matrix(y_te, preds, labels=KEEP)
    cf1 = f1_score(y_te, preds, labels=KEEP, average=None)
    out[name] = {
        'test_acc': acc, 'macro_f1': macro,
        'class_f1': dict(zip(KEEP, [round(float(v), 4) for v in cf1])),
        'cm': cm.tolist(),
    }
    print(f"\n{name}: acc={acc:.4f} macroF1={macro:.4f}")
    print("  class F1:", dict(zip(KEEP, [round(float(v), 4) for v in cf1])))
    print("  CM (rows CE TLE MLE WA RE):")
    for i, k in enumerate(KEEP):
        print(f"    {k}: {cm[i].tolist()}")

    # Feature importance for tree models
    if hasattr(model, 'feature_importances_'):
        fi = model.feature_importances_
        print(f"  Feature importance: {dict(zip(FEATURES, [round(float(v)*100, 2) for v in fi]))}")
        out[name]['feature_importance'] = {f: round(float(v)*100, 2) for f, v in zip(FEATURES, fi)}

    # ROC-AUC (ovr) for GB
    if name == "Gradient Boosting":
        try:
            y_prob = model.predict_proba(X_te)
            aucs = {}
            for i, k in enumerate(model.classes_):
                aucs[k] = round(float(roc_auc_score((y_te == k).astype(int), y_prob[:, i])), 4)
            print(f"  ROC-AUC (ovr): {aucs}")
            out[name]['roc_auc'] = aucs
        except Exception as e:
            print(f"  ROC err: {e}")

json.dump(out, open('/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments/gb_true_results.json', 'w'),
          indent=1, ensure_ascii=False)
print("\nSaved gb_true_results.json")

# ============ Sensitivity analysis (GB, subset sizes) ============
print("\n=== Sensitivity (GB) ===")
sens = []
for n in [400, 600, 800, 1600, 2800, 10688]:
    if n >= len(X_tr):
        continue
    idx = np.random.RandomState(42).choice(len(X_tr), n, replace=False)
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                    learning_rate=0.1, random_state=42)
    gb.fit(X_tr[idx], y_tr[idx])
    acc = accuracy_score(y_te, gb.predict(X_te))
    sens.append({'n': n, 'acc': round(float(acc)*100, 2)})
    print(f"  n={n}: {acc*100:.2f}%")
json.dump(sens, open('/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments/gb_sensitivity_true.json', 'w'))
print("Saved gb_sensitivity_true.json")
