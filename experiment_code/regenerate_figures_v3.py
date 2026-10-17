#!/usr/bin/env python3
"""Regenerate every number-bearing figure from authoritative_results_v3.json."""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_curve
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_authoritative import load_rows, matrix, FEATURES, KEEP, SEED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')))
A = R['protocol_a']['models']
plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})

# ---------------------------------------------------------------- accuracy --
models = ['Gradient Boosting\n(6 fields)', 'Random Forest\n(6 fields)',
          'Logistic Regression', 'DeepSeek-V3\n(three-shot)', 'Qwen2.5:3B\n(three-shot)']
vals = [A['Gradient Boosting']['test_accuracy'] * 100, A['Random Forest']['test_accuracy'] * 100,
        A['Logistic Regression']['test_accuracy'] * 100,
        R['llm']['deepseek_fair_rerun_predictions.json']['accuracy_invalid_as_wrong'] * 100,
        R['llm']['qwen25_fair_rerun_predictions.json']['accuracy_invalid_as_wrong'] * 100]
colors = ['#1f4e79', '#2e75b6', '#8faadc', '#c00000', '#e06666']
fig, ax = plt.subplots(figsize=(8.0, 4.4))
bars = ax.bar(range(len(vals)), vals, color=colors, edgecolor='black', linewidth=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}', ha='center',
            fontsize=11, fontweight='bold')
ax.set_xticks(range(len(vals))); ax.set_xticklabels(models, fontsize=9)
ax.set_ylabel('Test accuracy (%)'); ax.set_ylim(0, 108)
ax.axhline(76.6, ls=':', color='gray', lw=1)
ax.text(4.45, 78, 'majority class (76.6%)', fontsize=8, color='gray', ha='right')
ax.set_title('Test-set accuracy, $n=2{,}672$', fontsize=12, fontweight='bold')
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'fig_accuracy_chart.png'), dpi=300)
plt.close()

# ------------------------------------------------------------- class-wise ---
gb = A['Gradient Boosting']['class_f1']
order = ['TLE', 'WA', 'MLE', 'CE', 'RE']
v = [gb[k] for k in order]
fig, ax = plt.subplots(figsize=(7.4, 4.2))
bars = ax.bar(order, v, color=['#2e8b57' if x >= 0.75 else '#c00000' for x in v],
              edgecolor='black', linewidth=0.6)
for b, x in zip(bars, v):
    ax.text(b.get_x() + b.get_width() / 2, x + 0.015, f'{x:.2f}', ha='center',
            fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.12); ax.set_ylabel('F1 score'); ax.set_xlabel('Verdict')
ax.axhline(0.767, ls='--', color='gray', lw=0.9)
ax.text(4.42, 0.72, 'CE limit on this partition (0.77)', fontsize=8, color='gray', ha='right')
ax.set_title('Per-class F1, Gradient Boosting ($n=2{,}672$)', fontsize=12, fontweight='bold')
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'fig_class_f1_chart.png'), dpi=300)
plt.close()

# ------------------------------------------------------- feature importance -
fi = A['Gradient Boosting']['feature_importance']
label = {'time_consumed_ms': 'Execution time', 'memory_kb': 'Peak memory',
         'problem_rating': 'Problem rating', 'language_encoded': 'Language',
         'passed_test_count': 'Tests passed', 'problem_type': 'Problem slot'}
items = sorted(fi.items(), key=lambda kv: kv[1])
fig, ax = plt.subplots(figsize=(7.6, 3.9))
ax.barh([label[k] for k, _ in items], [x for _, x in items], color='#2e75b6',
        edgecolor='black', linewidth=0.5)
for i, (_, x) in enumerate(items):
    ax.text(x + 1.2, i, f'{x:.1f}%', va='center', fontsize=9)
ax.set_xlabel('Gini importance (%)'); ax.set_xlim(0, max(fi.values()) * 1.18)
ax.set_title('Feature importance, Gradient Boosting (6 fields)', fontsize=12, fontweight='bold')
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'fig_feature_importance_chart.png'), dpi=300)
plt.close()

# ------------------------------------------------------------- ROC and PR ---
rows, _ = load_rows()
X, y = matrix(rows, FEATURES)
idx = np.arange(len(rows))
tr, te = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y)
m = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                               random_state=SEED).fit(X[tr], y[tr])
prob = m.predict_proba(X[te]); y_te = y[te]
fig, ax = plt.subplots(figsize=(6.4, 5.2))
aucs = {}
for i, c in enumerate(m.classes_):
    fpr, tpr, _ = roc_curve((y_te == c).astype(int), prob[:, i])
    aucs[c] = roc_auc_score((y_te == c).astype(int), prob[:, i])
    ax.plot(fpr, tpr, lw=1.8, label=f'{c} (AUC = {aucs[c]:.3f})')
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.5)
ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
ax.set_title('ROC curves, one-vs-rest (Gradient Boosting)', fontsize=12, fontweight='bold')
ax.legend(fontsize=8, loc='lower right')
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'fig_roc_curves.pdf'))
plt.close()
fig, ax = plt.subplots(figsize=(6.4, 5.2))
for i, c in enumerate(m.classes_):
    pr, rc, _ = precision_recall_curve((y_te == c).astype(int), prob[:, i])
    ax.plot(rc, pr, lw=1.8, label=f'{c} (n={int((y_te==c).sum())})')
ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
ax.set_title('Precision--recall curves (Gradient Boosting)', fontsize=12, fontweight='bold')
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'fig_pr_curves.pdf'))
plt.close()
print('AUC:', {k: round(v, 3) for k, v in aucs.items()})

# ----------------------------------------------------------- correlation -----
short = ['rating', 'time', 'memory', 'language', 'tests', 'slot']
Xi = X
C = np.corrcoef(Xi.T)
fig, ax = plt.subplots(figsize=(5.6, 4.8))
im = ax.imshow(C, cmap='RdBu_r', vmin=-1, vmax=1)
ax.set_xticks(range(len(short))); ax.set_xticklabels(short, rotation=40, ha='right')
ax.set_yticks(range(len(short))); ax.set_yticklabels(short)
for i in range(len(short)):
    for j in range(len(short)):
        ax.text(j, i, f'{C[i, j]:.2f}', ha='center', va='center', fontsize=8,
                color='white' if abs(C[i, j]) > 0.6 else 'black')
ax.grid(False)
ax.set_title('Feature correlation', fontsize=11, fontweight='bold')
fig.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'figures', 'correlation_heatmap.pdf'))
plt.close()
print('corr max off-diagonal:', round(float(np.max(np.abs(C - np.eye(len(C))))), 3))

# ------------------------------------------------- error by difficulty tier --
from collections import Counter as _Counter
tiers = [('Novice\n(<=800)', lambda r: r <= 800),
         ('Easy\n(801-1200)', lambda r: 800 < r <= 1200),
         ('Medium\n(1201-1600)', lambda r: 1200 < r <= 1600),
         ('Hard\n(1601-2000)', lambda r: 1600 < r <= 2000),
         ('Expert\n(>2000)', lambda r: r > 2000)]
verdicts = ['WA', 'TLE', 'MLE', 'CE', 'RE']
fig, ax = plt.subplots(figsize=(8.0, 4.4))
width = 0.16
for vi, v in enumerate(verdicts):
    shares = []
    for _, f in tiers:
        sub = [r for r in rows if f(r['problem_rating'])]
        c = _Counter(r['verdict'] for r in sub)
        shares.append(100 * c[v] / len(sub))
    ax.bar(np.arange(len(tiers)) + (vi - 2) * width, shares, width, label=v,
           edgecolor='black', linewidth=0.4)
ax.set_xticks(range(len(tiers)))
ax.set_xticklabels([t for t, _ in tiers], fontsize=9)
ax.set_ylabel('Share of tier (%)'); ax.set_xlabel('Problem difficulty')
ax.set_ylim(0, 92)
ax.legend(fontsize=8, ncol=5, loc='upper right')
ax.set_title('Error type distribution across difficulty levels ($n=13{,}360$)',
             fontsize=12, fontweight='bold')
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'figures', 'error_by_difficulty.pdf'))
plt.close()
for name, f in tiers:
    sub = [r for r in rows if f(r['problem_rating'])]
    c = _Counter(r['verdict'] for r in sub)
    print(name.replace('\n', ' '), 'n=%d' % len(sub),
          {v: round(100 * c[v] / len(sub), 1) for v in verdicts})

print('Saved all figures.')
