#!/usr/bin/env python3
"""Regenerate ALL GB figures with TRUE Gradient Boosting data from
final_results_v2.json + recomputed GB feature importance / ROC / sensitivity.
Replaces the old RF-data-as-GB figures."""
import json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (f1_score, accuracy_score, roc_auc_score,
                             roc_curve, precision_recall_curve)

OUT = "/Users/mac/Desktop/SCI1/06_论文定稿"
CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
KEEP = ['CE', 'TLE', 'MLE', 'WA', 'RE']

# ---------- load data (same pipeline as before) ----------
rows = []
with open(CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['verdict'] not in KEEP:
            continue
        pr = r['problem_rating'].strip(); tc = r['time_consumed_ms'].strip()
        try:
            pr = float(pr); tc = float(tc)
        except ValueError:
            continue
        if pr != pr or tc != tc:
            continue
        rows.append({'user': r['user_handle'], 'problem_rating': pr,
                     'time_consumed_ms': tc,
                     'memory_kb': float(r['memory_kb']) if r['memory_kb'].strip() else 0.0,
                     'language': str(r['language']).strip(),
                     'problem_index': str(r['problem_index']).strip(),
                     'verdict': r['verdict']})
langs = sorted(set(r['language'] for r in rows))
lang_map = {l: i for i, l in enumerate(langs)}
for r in rows:
    r['language_encoded'] = lang_map[r['language']]
    idx = r['problem_index'].upper()
    r['problem_type'] = ord(idx[0]) - ord('A') + 1 if idx else 0
    r['hour'] = 12
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
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train {len(X_tr)}, Test {len(X_te)}")

gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
gb.fit(X_tr, y_tr)
preds = gb.predict(X_te)
acc = accuracy_score(y_te, preds)
cf1 = f1_score(y_te, preds, labels=KEEP, average=None)
print(f"GB acc={acc*100:.2f}%, F1={dict(zip(KEEP,[round(float(v),3) for v in cf1]))}")

# ---------- 1. class-wise F1 chart ----------
f1_map = {k: float(v) for k, v in zip(KEEP, cf1)}
order = ['TLE', 'WA', 'MLE', 'CE', 'RE']
vals = [f1_map[k] for k in order]
colors = ['#2e8b57' if v >= 0.89 else '#d62728' for v in vals]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
bars = ax.bar(order, vals, color=colors, edgecolor='black', linewidth=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 0.01, f'{v:.2f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.12)
ax.set_ylabel('F1 Score', fontsize=12)
ax.set_xlabel('Error Type', fontsize=12)
ax.set_title('Class-Wise F1 Scores (Gradient Boosting)', fontsize=13, fontweight='bold')
ax.axhline(0.89, color='gray', linestyle='--', linewidth=0.8)
ax.text(4.42, 0.90, '0.89 threshold', fontsize=9, color='gray', ha='right')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_class_f1_chart.png", dpi=300, bbox_inches='tight')
plt.close()
print("Saved fig_class_f1_chart.png (GB)")

# ---------- 2. feature importance chart (GB) ----------
fi = gb.feature_importances_
fi_names = ['Execution Time\n(time_consumed_ms)', 'User Success Rate\n(user_success_rate)',
            'Memory\n(memory_kb)', 'Problem Rating\n(problem_rating)',
            'Language\n(language_encoded)', 'Problem Type\n(problem_type)',
            'Submission Hour\n(hour)']
fi_vals = [float(v)*100 for v in fi]
fi_order = np.argsort(fi_vals)[::-1]
fig, ax = plt.subplots(figsize=(8.2, 4.6))
bars = ax.barh([fi_names[i].replace('\n', ' ') for i in fi_order],
               [fi_vals[i] for i in fi_order],
               color='#1f77b4', edgecolor='black', linewidth=0.5)
for b, v in zip(bars, [fi_vals[i] for i in fi_order]):
    ax.text(v + 0.5, b.get_y() + b.get_height()/2, f'{v:.1f}%',
            va='center', fontsize=10)
ax.set_xlabel('Gini Importance (%)', fontsize=12)
ax.set_title('Feature Importance (Gradient Boosting, 7 features)', fontsize=13, fontweight='bold')
ax.set_xlim(0, max(fi_vals)*1.18)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_feature_importance_chart.png", dpi=300, bbox_inches='tight')
plt.close()
fi_dict = {f: round(float(v)*100, 2) for f, v in zip(FEATURES, fi)}
print("Saved fig_feature_importance_chart.png (GB)")
print("GB feature importance:", fi_dict)

# ---------- 3. ROC curves (GB, ovr) ----------
y_prob = gb.predict_proba(X_te)
classes_ = list(gb.classes_)
fig, ax = plt.subplots(figsize=(7.2, 5.6))
aucs = {}
for i, cls in enumerate(classes_):
    yb = (y_te == cls).astype(int)
    fpr, tpr, _ = roc_curve(yb, y_prob[:, i])
    a = roc_auc_score(yb, y_prob[:, i])
    aucs[cls] = round(float(a), 3)
    ax.plot(fpr, tpr, lw=1.8, label=f'{cls} (AUC = {a:.3f})')
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.5)
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('ROC Curves (Gradient Boosting, One-vs-Rest)', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='lower right')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_roc_curves.pdf")
plt.close()
print("Saved fig_roc_curves.pdf (GB):", aucs)

# ---------- 4. PR curves (GB, ovr) ----------
fig, ax = plt.subplots(figsize=(7.2, 5.6))
for i, cls in enumerate(classes_):
    yb = (y_te == cls).astype(int)
    prec, rec, _ = precision_recall_curve(yb, y_prob[:, i])
    ax.plot(rec, prec, lw=1.8, label=f'{cls}')
ax.set_xlabel('Recall', fontsize=12)
ax.set_ylabel('Precision', fontsize=12)
ax.set_title('Precision-Recall Curves (Gradient Boosting, One-vs-Rest)', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_pr_curves.pdf")
plt.close()
print("Saved fig_pr_curves.pdf (GB)")

# ---------- 5. sensitivity (GB), incl. full train ----------
sens = []
for n in [400, 600, 800, 1600, 2800, 10688]:
    if n > len(X_tr):
        continue
    if n == len(X_tr):
        idx = np.arange(len(X_tr))
    else:
        idx = np.random.RandomState(42).choice(len(X_tr), n, replace=False)
    m = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    m.fit(X_tr[idx], y_tr[idx])
    a = accuracy_score(y_te, m.predict(X_te))
    sens.append({'n': n, 'acc': round(float(a)*100, 2)})
    print(f"  sens n={n}: {a*100:.2f}%")
json.dump(sens, open(f"{OUT}/llm_experiments/gb_sensitivity_true.json', 'w"), indent=1)
json.dump({'feature_importance': fi_dict, 'roc_auc': aucs, 'class_f1': {k: round(float(v),4) for k,v in f1_map.items()}},
          open(f"{OUT}/llm_experiments/gb_metrics_true.json", 'w'), indent=1)
print("Done.")
