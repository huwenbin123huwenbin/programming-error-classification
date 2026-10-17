#!/usr/bin/env python3
"""
Independent audit of the LLM numbers that the authoritative JSON cannot check.

authoritative_results_v3.json stores aggregate LLM metrics but not the per-row
predictions, so the following manuscript claims have no upstream source:

  - "recovers every compilation error (recall 1.00) and most TLE and MLE
    submissions (0.872 and 0.875)"                       (Sec. 4.7)
  - "precision on CE falls to 0.321: 415 wrong answers and runtime errors"  (ibid.)
  - "Runtime Error is effectively unreachable for it (recall 0.016, two of 131)"
  - Qwen prediction distribution (CE 263, TLE 644, MLE 317, WA 715, RE 464)
  - McNemar rows against the LLMs (chi2 = 364.23 / 334.72 / 92.37 / ...)

This script recomputes them from the raw prediction dumps and prints a
PASS/FAIL verdict against the manuscript, so the audit is reproducible.

Run: /usr/bin/python3 experiment_code/audit_llm_numbers.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM = os.path.join(ROOT, 'llm_experiments')
CLASSES = ['CE', 'TLE', 'MLE', 'WA', 'RE']


def load(name):
    with open(os.path.join(LLM, name), encoding='utf-8') as f:
        return json.load(f)


def mcnemar_chi2(ca, cb):
    """ca/cb are boolean lists; returns (chi2, b, c, p) with continuity correction."""
    b = sum(1 for x, y in zip(ca, cb) if x and not y)
    c = sum(1 for x, y in zip(ca, cb) if not x and y)
    n = b + c
    if n == 0:
        return 0.0, 0, 0, 1.0
    chi2 = (abs(b - c) - 1.0) ** 2 / n if n > 0 else 0.0
    try:
        from scipy.stats import binomtest
        p = min(1.0, 2.0 * binomtest(min(b, c), n, 0.5).pvalue)
    except Exception:
        p = float('nan')
    return chi2, b, c, p


def per_class(pairs, valid_only):
    """pairs: list of (true, pred, valid). Returns recall/precision per class."""
    stats = {c: {'tp': 0, 'fp': 0, 'fn': 0, 'support': 0} for c in CLASSES}
    for t, pr, v in pairs:
        if valid_only and not v:
            continue
        stats[t]['support'] += 1
        if pr == t:
            stats[t]['tp'] += 1
        else:
            stats[pr]['fp'] += 1
            stats[t]['fn'] += 1
    out = {}
    for c in CLASSES:
        s = stats[c]
        rec = s['tp'] / (s['tp'] + s['fn']) if (s['tp'] + s['fn']) else 0.0
        prec = s['tp'] / (s['tp'] + s['fp']) if (s['tp'] + s['fp']) else 0.0
        out[c] = {'recall': rec, 'precision': prec,
                  'support': s['support'], 'fp': s['fp']}
    return out


def verdict(label, got, want, tol):
    ok = abs(got - want) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: computed={got:.4f} "
          f"manuscript={want} (tol {tol})")
    return ok


def main():
    print("=" * 68)
    print("LLM number audit — recomputed from raw prediction dumps")
    print("=" * 68)
    all_ok = True

    # ---------- DeepSeek-V3 ----------
    ds = load('deepseek_fair_rerun_predictions.json')['predictions']
    pairs = [(r['true_label'], r['prediction'], r['valid']) for r in ds]
    n_valid = sum(1 for _, _, v in pairs if v)
    print(f"\nDeepSeek-V3: n={len(pairs)} valid={n_valid} invalid={len(pairs)-n_valid}")

    pc = per_class(pairs, valid_only=True)
    print("\n-- Sec. 4.7 claims (valid outputs only) --")
    all_ok &= verdict("CE recall", pc['CE']['recall'], 1.00, 0.005)
    all_ok &= verdict("TLE recall", pc['TLE']['recall'], 0.872, 0.005)
    all_ok &= verdict("MLE recall", pc['MLE']['recall'], 0.875, 0.005)
    all_ok &= verdict("CE precision", pc['CE']['precision'], 0.321, 0.005)
    print(f"       CE false positives = {pc['CE']['fp']} (manuscript: 415)")
    all_ok &= abs(pc['CE']['fp'] - 415) <= 2
    all_ok &= verdict("RE recall", pc['RE']['recall'], 0.016, 0.005)
    print(f"       RE support = {pc['RE']['support']} (manuscript: 131)")

    # macro F1 and accuracy cross-check against the authoritative JSON
    import statistics
    f1s = []
    for c in CLASSES:
        s = pc[c]
        f1 = (2 * s['precision'] * s['recall'] /
              (s['precision'] + s['recall'])) if (s['precision'] + s['recall']) else 0.0
        f1s.append(f1)
    print(f"  macro F1 (valid) = {statistics.mean(f1s):.4f}  (manuscript: 0.545)")
    acc_v = sum(1 for t, p, _ in pairs if p == t) / n_valid
    print(f"  accuracy (valid) = {acc_v:.4f}  (manuscript: 0.7665)")

    # ---------- Qwen ----------
    qw = load('qwen25_fair_rerun_predictions.json')
    qrows = qw['predictions'] if isinstance(qw, dict) and 'predictions' in qw else qw
    from collections import Counter
    dist = Counter(r['prediction'] for r in qrows)
    want = {'CE': 263, 'TLE': 644, 'MLE': 317, 'WA': 715, 'RE': 464}
    print("\n-- Qwen2.5:3B prediction distribution (Sec. 4.7) --")
    for c in CLASSES:
        got = dist.get(c, 0)
        ok = abs(got - want[c]) <= 2
        all_ok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {c}: computed={got} manuscript={want[c]}")
    print(f"  total = {sum(dist.values())}")

    # ---------- McNemar against LLMs ----------
    ds_correct = {r['idx']: (r['prediction'] == r['true_label']) for r in ds}
    qw_correct = {r['idx']: (r['prediction'] == r['true_label']) for r in qrows}

    def series(d):
        return [d[i] for i in sorted(d)]

    # ---------- authoritative ML predictions, recomputed from the pipeline ----------
    # llm_experiments/gb_predictions_test.json and ml_predictions_test_5feat.json are
    # stale dumps from an earlier pipeline (their GB scores 91.99%, not the 91.77%
    # the manuscript reports). They are archived under experiment_results/deprecated/.
    # The manuscript's ML rows must be reproducible from pipeline_authoritative, so
    # recompute them here rather than reading the dumps.
    import numpy as np
    from sklearn.model_selection import train_test_split
    import pipeline_authoritative as pa

    rows, _ = pa.load_rows()
    y_all = np.array([r['verdict'] for r in rows])
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED, stratify=y_all)
    print("\nrecomputing ML predictions from pipeline_authoritative (this trains "
          "3 models + 5-fold CV)...")
    _, preds, _, _, X_te, y_te = pa.protocol(rows, tr, te, 'A: audit re-run')

    auth = {n: {i: bool(preds[n][i] == y_te[i]) for i in range(len(y_te))}
            for n in preds}

    print("\n-- McNemar rows involving an LLM (Table 8), authoritative ML preds --")
    for name, ml in auth.items():
        chi2, b, c, p = mcnemar_chi2(series(ml), series(ds_correct))
        print(f"  {name:20s} vs DeepSeek-V3 : chi2={chi2:8.2f}  b={b:4d} c={c:4d} p={p:.2e}")
    for name, ml in auth.items():
        chi2, b, c, p = mcnemar_chi2(series(ml), series(qw_correct))
        print(f"  {name:20s} vs Qwen2.5:3B   : chi2={chi2:8.2f}  b={b:4d} c={c:4d} p={p:.2e}")
    chi2, b, c, p = mcnemar_chi2(series(ds_correct), series(qw_correct))
    print(f"  {'DeepSeek-V3':20s} vs Qwen2.5:3B   : chi2={chi2:8.2f}  b={b:4d} c={c:4d} p={p:.2e}")

    print("\n" + "=" * 68)
    print("AUDIT " + ("PASSED" if all_ok else "FOUND DISCREPANCIES"))
    print("=" * 68)
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
