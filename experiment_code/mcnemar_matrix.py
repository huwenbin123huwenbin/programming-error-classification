#!/usr/bin/env python3
"""Pairwise McNemar matrix on the Protocol A test set, plus balanced accuracy
and per-class precision/recall, emitted as LaTeX-ready numbers."""
import json, os, sys, itertools
import numpy as np
from sklearn.model_selection import train_test_split
from scipy.stats import chi2, binomtest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_authoritative import load_rows, matrix, models, FEATURES, KEEP, SEED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')))
rows, _ = load_rows()
X, y = matrix(rows, FEATURES)
idx = np.arange(len(rows))
tr, te = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y)
y_te = y[te]

pred = {}
for name in models():
    m = models()[name].fit(X[tr], y[tr])
    pred[{'Gradient Boosting': 'GB', 'Random Forest': 'RF',
          'Logistic Regression': 'LR'}[name]] = m.predict(X[te])

llm = R['llm']
pred['DS'] = np.array([l if l is not None else 'INVALID'
                       for l in llm['deepseek_fair_rerun_predictions.json']['labels']])
pred['QW'] = np.array([l if l is not None else 'INVALID'
                       for l in llm['qwen25_fair_rerun_predictions.json']['labels']])
pred['GB5'] = np.array(llm['gb_5field']['labels'])

def mcnemar(a, b):
    ca, cb = a == y_te, b == y_te
    x = int(np.sum(ca & ~cb)); z = int(np.sum(~ca & cb)); n = x + z
    if n == 0:
        return 0.0, 1.0, x, z
    if n < 25:
        return float('nan'), float(binomtest(min(x, z), n, .5).pvalue), x, z
    st = (abs(x - z) - 1) ** 2 / n
    return st, float(chi2.sf(st, 1)), x, z

names = ['GB', 'RF', 'LR', 'GB5', 'DS', 'QW']
print('acc:', {k: round(float((v == y_te).mean()) * 100, 2) for k, v in pred.items()})
for a, b in itertools.combinations(names, 2):
    st, p, x, z = mcnemar(pred[a], pred[b])
    print(f'{a:4s} vs {b:4s}  chi2={st:8.2f} p={p:.3e} b={x} c={z}')

# per-class precision / recall for GB
gb = pred['GB']
print('\nGB per-class:')
for k in KEEP:
    tp = int(np.sum((gb == k) & (y_te == k)))
    fp = int(np.sum((gb == k) & (y_te != k)))
    fn = int(np.sum((gb != k) & (y_te == k)))
    pr = tp / (tp + fp) if tp + fp else 0
    rc = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0
    print(f'  {k}: P={pr:.3f} R={rc:.3f} F1={f1:.3f}  tp={tp} fp={fp} fn={fn}')

# how many WA rows are predicted CE, and how many of those carry the 0/0/0 signature
sig = np.array([[r['time_consumed_ms'], r['memory_kb'], r['passed_test_count']] for r in rows])
sig_te = sig[te]
zero = np.all(sig_te == 0, axis=1)
pred_ce = gb == 'CE'
print(f'\nGB predicted CE: {int(pred_ce.sum())} rows; '
      f'of these {int((pred_ce & (y_te != "CE")).sum())} are not CE, '
      f'all with the 0/0/0 signature: {bool(np.all(zero[pred_ce]))}')
print(f'CE rows in test: {int((y_te=="CE").sum())}, of which predicted CE: {int((pred_ce & (y_te=="CE")).sum())}')
print(f'rows in test with 0/0/0 signature: {int(zero.sum())}, '
      f'composition: ' + str({k: int(np.sum(zero & (y_te == k))) for k in KEEP}))
