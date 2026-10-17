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
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402


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

    print('=' * 60)
    print(f'SUMMARY ICC={icc_mean:.3f} DEFF={deff:.2f} NEFF={n / deff:.0f}')


if __name__ == '__main__':
    main()
