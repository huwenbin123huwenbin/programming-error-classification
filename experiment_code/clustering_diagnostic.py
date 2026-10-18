#!/usr/bin/env python3
"""Clustering diagnostic for the submitter dependence in §5.1.

Submissions from the same submitter are not independent. This script
quantifies how strong that dependence is, so the unadjusted McNemar
statistics in Table 8 can be read with a known margin:

  ICC      one-way random-effects intraclass correlation of the verdict,
           computed per class on one-hot indicators and averaged. It is the
           correlation between the verdicts of two submissions drawn from the
           same submitter.
  design   the variance inflation (design effect) a random split suffers:
           deff = 1 + (kbar - 1) * ICC, with kbar the mean submissions per
           submitter. n_eff = n / deff is the effective sample size.

Run:  /usr/bin/python3 clustering_diagnostic.py

Output: experiment_results/clustering_diagnostic.json (the manuscript's
§5.1 figures — ICC 0.41-0.53, mean 0.483, deff 2.13, n_eff ≈ 6,300 — are
read from this artifact).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

OUT = os.path.join(ROOT, 'experiment_results', 'clustering_diagnostic.json')

# manuscript figures (§5.1): (quantity, printed, tolerance)
EXPECTED = [
    ('icc_min', 0.40, 0.005), ('icc_max', 0.53, 0.005), ('icc_mean', 0.483, 0.0005),
    ('deff', 2.13, 0.005), ('n_eff', 6300, 50),
    ('modal_share', 0.920, 0.0005), ('entropy_ratio', 0.181, 0.0005),
]


def main():
    rows, _ = pa.load_rows()
    users = np.array([r['user'] for r in rows])
    verdicts = np.array([r['verdict'] for r in rows])
    classes = sorted(set(verdicts))
    n = len(rows)
    print(f'n={n} submitters={len(set(users))} classes={classes}')

    # per-submitter group sizes
    sizes = {}
    for u in users:
        sizes[u] = sizes.get(u, 0) + 1
    kbar = n / len(sizes)
    print(f'submissions per submitter: mean={kbar:.2f} '
          f'median={int(np.median(list(sizes.values())))} '
          f'max={max(sizes.values())}')

    # per-class ICC on one-hot indicators (one-way random effects, unequal k)
    iccs = {}
    for c in classes:
        x = (verdicts == c).astype(float)
        grand = x.mean()
        ss_b = 0.0
        ss_w = 0.0
        for u in set(users):
            m = users == u
            xg = x[m]
            ss_b += len(xg) * (xg.mean() - grand) ** 2
            ss_w += ((xg - xg.mean()) ** 2).sum()
        iccs[c] = ss_b / (ss_b + ss_w) if (ss_b + ss_w) > 0 else 0.0
        print(f'  ICC[{c:3s}] = {iccs[c]:.3f}   (class share {grand:.3f})')

    icc_mean = float(np.mean(list(iccs.values())))
    print(f'mean ICC = {icc_mean:.3f}')

    deff = 1 + (kbar - 1) * icc_mean
    print(f'design effect = 1 + ({kbar:.2f} - 1) x {icc_mean:.3f} = {deff:.2f}')
    print(f'effective n = {n} / {deff:.2f} = {n / deff:.0f}')

    # per-submitter modal share and entropy ratio (reported in the manuscript)
    modal, ent_ratio = [], []
    from collections import Counter
    for u in set(users):
        m = users == u
        vg = verdicts[m]
        cnt = Counter(vg)
        p = np.array([cnt.get(c, 0) for c in classes], dtype=float) / len(vg)
        modal.append(p.max())
        with np.errstate(divide='ignore', invalid='ignore'):
            terms = np.where(p > 0, p * np.log(p), 0.0)
        h = -terms.sum()
        pg = np.array([(verdicts == c).mean() for c in classes])
        hg = -(pg * np.log(pg)).sum()
        ent_ratio.append(h / hg)
    print(f'mean per-submitter modal share = {np.mean(modal):.3f}')
    print(f'mean entropy ratio (within/global) = {np.mean(ent_ratio):.3f}')

    report = {
        'n': int(n), 'n_submitters': len(sizes),
        'submissions_per_submitter': {'mean': kbar,
                                      'median': float(np.median(list(sizes.values()))),
                                      'max': int(max(sizes.values()))},
        'icc_per_class': {c: float(v) for c, v in iccs.items()},
        'icc_min': float(min(iccs.values())), 'icc_max': float(max(iccs.values())),
        'icc_mean': icc_mean, 'deff': float(deff), 'n_eff': float(n / deff),
        'modal_share': float(np.mean(modal)),
        'entropy_ratio': float(np.mean(ent_ratio)),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f'wrote {OUT}')

    print('\nManuscript check (§5.1):')
    ok = True
    for q, printed, tol in EXPECTED:
        actual = report[q]
        good = abs(actual - printed) <= tol
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {q:14s} "
              f"manuscript {printed:>8}  artifact {actual:.4g}")
    print('=' * 60)
    print('CLUSTERING ' + ('PASSED' if ok else 'FAILED'))
    print('=' * 60)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
