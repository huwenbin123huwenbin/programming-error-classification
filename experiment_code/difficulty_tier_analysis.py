#!/usr/bin/env python3
"""Difficulty-tier analysis -- provenance for the Empirical Generalization
Analysis (Section 5.5, sec:skill-tier) of the manuscript.

Why this script exists
----------------------
Round 9 replaced the paper's skill-tier paragraph: the old numbers
(96.01 / 95.21 / 88.54%) came from student_proxy_experiment.json, which
groups by *submitter* rating and supports the backwards claim that novices
are classified most accurately. The replacement paragraph segments the shared
test partition into *problem-difficulty* tiers and reports
92.21 / 93.60 / 87.55%. No script produced those numbers -- they were
recomputed once, in an interactive session, and never persisted. This script
makes them reproducible and pins them to an artifact, then checks the
manuscript's exact figures.

Protocol: identical to pipeline_authoritative.protocol A -- stratified 80/20
split (random_state=42), Gradient Boosting with the pipeline's hyperparameters,
six features. Tiers are cut on problem_rating over the TEST partition only.

Output: experiment_results/difficulty_tiers.json
Exit 0 = every manuscript figure reproduces; exit 1 = mismatch.
"""
import json
import os
import sys
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, f1_score, balanced_accuracy_score,
                             recall_score)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

OUT = os.path.join(ROOT, 'experiment_results', 'difficulty_tiers.json')

# The manuscript's figures (Section 5.5). Each entry:
#   (tier, quantity, value_as_printed, tolerance)
EXPECTED = [
    ('novice',        'n',              1464, 0),
    ('intermediate',  'n',               734, 0),
    ('advanced',      'n',               474, 0),
    ('novice',        'accuracy',      92.21, 0.005),
    ('intermediate',  'accuracy',      93.60, 0.005),
    ('advanced',      'accuracy',      87.55, 0.005),
    ('novice',        'macro_f1',       0.794, 0.0005),
    ('intermediate',  'macro_f1',       0.766, 0.0005),
    ('advanced',      'macro_f1',       0.811, 0.0005),
    ('novice',        'balanced_acc',   0.826, 0.0005),
    ('intermediate',  'balanced_acc',   0.777, 0.0005),
    ('advanced',      'balanced_acc',   0.803, 0.0005),
    ('novice',        're_f1',           0.41, 0.005),
    ('intermediate',  're_f1',           0.15, 0.005),
    ('advanced',      're_f1',           0.31, 0.005),
    ('novice',        'wa_recall',      0.94, -1),   # "stays above 0.94"
    ('intermediate',  'wa_recall',      0.94, -1),
    ('advanced',      'wa_recall',      0.94, -1),
    # verdict composition shares (percent of the tier)
    ('novice',        'tle_share',       3.3, 0.05),
    ('novice',        'mle_share',       0.2, 0.05),
    ('advanced',      'tle_share',      17.5, 0.05),
    ('advanced',      'mle_share',       5.5, 0.05),
    ('novice',        're_share',        4.1, 0.05),
    ('advanced',      're_share',       10.3, 0.05),
    ('intermediate',  're_count',         22, 0),
]

TIERS = [('novice', lambda r: r < 1400),
         ('intermediate', lambda r: 1400 <= r < 2000),
         ('advanced', lambda r: r >= 2000)]


def tier_stats(pred, truth, rating):
    out = {}
    for name, cut in TIERS:
        m = np.array([cut(r) for r in rating])
        if m.sum() == 0:
            continue
        y_t, y_p = truth[m], pred[m]
        cnt = Counter(str(v) for v in y_t)
        n = int(m.sum())
        cf1 = f1_score(y_t, y_p, labels=pa.KEEP, average=None, zero_division=0)
        out[name] = {
            'n': n,
            'accuracy': float(accuracy_score(y_t, y_p)),
            'macro_f1': float(f1_score(y_t, y_p, labels=pa.KEEP, average='macro',
                                       zero_division=0)),
            'balanced_acc': float(balanced_accuracy_score(y_t, y_p)),
            'class_f1': {c: float(f) for c, f in zip(pa.KEEP, cf1)},
            're_f1': float(cf1[pa.KEEP.index('RE')]),
            'wa_recall': float(recall_score(y_t, y_p, labels=pa.KEEP,
                                            average=None, zero_division=0)[pa.KEEP.index('WA')]),
            'verdict_composition': {c: cnt.get(c, 0) for c in pa.KEEP},
            'tle_share': 100.0 * cnt.get('TLE', 0) / n,
            'mle_share': 100.0 * cnt.get('MLE', 0) / n,
            're_share': 100.0 * cnt.get('RE', 0) / n,
            're_count': cnt.get('RE', 0),
        }
    return out


def main():
    rows, _ = pa.load_rows()
    X, y = pa.matrix(rows, pa.FEATURES)
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED, stratify=y)

    gb = pa.models()['Gradient Boosting']
    gb.fit(X[tr], y[tr])
    pred = gb.predict(X[te])

    y_te = np.array([str(v) for v in y[te]])
    rating_te = [rows[i]['problem_rating'] for i in te]
    stats = tier_stats(pred, y_te, rating_te)

    report = {
        'source': 'Gradient Boosting (six features, pipeline_authoritative '
                  'hyperparameters), protocol A test partition',
        'tier_cuts': {'novice': 'problem_rating < 1400',
                      'intermediate': '1400 <= problem_rating < 2000',
                      'advanced': 'problem_rating >= 2000'},
        'tiers': stats,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print('Difficulty tiers on the shared test partition (Gradient Boosting)')
    for name in ('novice', 'intermediate', 'advanced'):
        s = stats[name]
        print(f"  {name:13s} n={s['n']:5d} acc={s['accuracy']*100:6.2f}% "
              f"macroF1={s['macro_f1']:.3f} bAcc={s['balanced_acc']:.3f} "
              f"RE_F1={s['re_f1']:.3f} WA_rec={s['wa_recall']:.3f} "
              f"TLE={s['tle_share']:.1f}% MLE={s['mle_share']:.1f}% RE={s['re_share']:.1f}%")

    print('\nManuscript check (Section 5.5):')
    ok = True
    for tier, q, printed, tol in EXPECTED:
        actual = stats[tier][q]
        # accuracy is stored as a fraction but printed as a percentage
        if q == 'accuracy':
            actual, tol = actual * 100, tol * 100
        if tol < 0:                       # "stays above" style claims
            good = actual >= printed
            shown = f">= {printed}"
        else:
            good = abs(actual - printed) <= tol
            shown = f"== {printed}"
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {tier:13s} {q:14s} "
              f"manuscript {shown:>10s}  artifact {actual:.4g}")
    print('=' * 68)
    print('DIFFICULTY TIERS ' + ('PASSED' if ok else 'FAILED'))
    print('=' * 68)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
