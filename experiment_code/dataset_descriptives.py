#!/usr/bin/env python3
"""Dataset descriptives -- provenance for Table 1, its footnote, and the
Figure 2 caption of the manuscript.

Why this script exists
----------------------
Round 9 replaced Table 1's execution-time column after discovering it came
from the retired 14,673-row dataset, and regenerated Figure 2 from the
authoritative rows. The replacement numbers (WA 81 ms, TLE 2,508 ms, RE 177 ms,
CE 0 ms, MLE 775 ms; 61.7% of TLE at exactly 2,000 ms; 65.3% of MLE at
262,100 KB; the five difficulty-tier shares in the figure caption) were
computed once and never persisted. This script reproduces all of them from
the authoritative rows and checks the manuscript figure by figure.

Output: experiment_results/dataset_descriptives.json
Exit 0 = every manuscript figure reproduces; exit 1 = mismatch.
"""
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

OUT = os.path.join(ROOT, 'experiment_results', 'dataset_descriptives.json')

# (quantity, value_as_printed, tolerance)
EXPECTED = [
    ('WA_count', 10234, 0), ('WA_pct', 76.6, 0.05), ('WA_mean_ms', 81, 0.5),
    ('TLE_count', 1288, 0), ('TLE_pct', 9.6, 0.05), ('TLE_mean_ms', 2508, 0.5),
    ('RE_count', 656, 0), ('RE_pct', 4.9, 0.05), ('RE_mean_ms', 177, 0.5),
    ('CE_count', 980, 0), ('CE_pct', 7.3, 0.05), ('CE_mean_ms', 0, 0.5),
    ('MLE_count', 202, 0), ('MLE_pct', 1.5, 0.05), ('MLE_mean_ms', 775, 0.5),
    ('TLE_mode_share_pct', 61.7, 0.05), ('MLE_mode_share_pct', 65.3, 0.05),
    ('MLE_mode_kb', 262100, 0),
    ('n_users', 4005, 0), ('median_subs_per_user', 2, 0), ('users_ge5', 773, 0),
    ('rating_min', 800, 0), ('rating_max', 3500, 0), ('rating_median', 1300, 0),
    # Figure 2 caption (five tiers: <=800, 801-1200, 1201-1600, 1601-2000, >2000)
    ('tier_le800_WA', 80.7, 0.05),
    ('tier_801_1200_WA', 85.1, 0.05),
    ('tier_gt2000_WA', 55.4, 0.05),
    ('tier_gt2000_TLE', 19.3, 0.05),
    ('tier_gt2000_RE', 10.1, 0.05),
    ('tier_gt2000_MLE', 6.6, 0.05),
    ('tier_gt2000_CE', 8.7, 0.05),
    ('platform_encoded_share_pct', 18.5, 0.05),
]


def main():
    rows, _ = pa.load_rows()
    n = len(rows)
    out = {'n_rows': n, 'by_verdict': {}, 'figure2_tiers': {}}

    for v in pa.KEEP:
        sub = [r for r in rows if r['verdict'] == v]
        t = [r['time_consumed_ms'] for r in sub]
        mem = [r['memory_kb'] for r in sub]
        out['by_verdict'][v] = {
            'count': len(sub), 'share_pct': 100.0 * len(sub) / n,
            'mean_time_ms': float(np.mean(t)),
            'mean_memory_kb': float(np.mean(mem)),
            'mode_time_ms': Counter(t).most_common(1)[0],
            'mode_memory_kb': Counter(mem).most_common(1)[0],
        }

    tle = out['by_verdict']['TLE']; mle = out['by_verdict']['MLE']
    out['TLE_mode_share_pct'] = 100.0 * tle['mode_time_ms'][1] / tle['count']
    out['MLE_mode_share_pct'] = 100.0 * mle['mode_memory_kb'][1] / mle['count']
    out['MLE_mode_kb'] = mle['mode_memory_kb'][0]

    # submitter statistics
    per_user = Counter(r['user'] for r in rows)
    counts = sorted(per_user.values())
    ratings = sorted(r['problem_rating'] for r in rows)
    out['n_users'] = len(per_user)
    out['median_subs_per_user'] = float(np.median(counts))
    out['users_ge5'] = sum(1 for c in counts if c >= 5)
    out['rating_min'] = ratings[0]
    out['rating_max'] = ratings[-1]
    out['rating_median'] = float(np.median(ratings))

    # Figure 2 tiers
    tiers = [('le800', lambda r: r <= 800), ('801_1200', lambda r: 800 < r <= 1200),
             ('1201_1600', lambda r: 1200 < r <= 1600),
             ('1601_2000', lambda r: 1600 < r <= 2000),
             ('gt2000', lambda r: r > 2000)]
    for name, cut in tiers:
        sub = [r for r in rows if cut(r['problem_rating'])]
        c = Counter(r['verdict'] for r in sub)
        shares = {v: 100.0 * c.get(v, 0) / len(sub) for v in pa.KEEP}
        out['figure2_tiers'][name] = {'n': len(sub), **shares}
        for v in pa.KEEP:
            out[f'tier_{name}_{v}'] = shares[v]

    encoded = sum(out['by_verdict'][v]['count'] for v in ('CE', 'TLE', 'MLE'))
    out['platform_encoded_share_pct'] = 100.0 * encoded / n

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    print('Dataset descriptives (authoritative rows, n=%d)' % n)
    for v in pa.KEEP:
        s = out['by_verdict'][v]
        print(f"  {v:4s} n={s['count']:6d} ({s['share_pct']:5.2f}%)  "
              f"mean_time={s['mean_time_ms']:8.1f} ms  mode_time={s['mode_time_ms']}")
    print(f"  TLE at exactly 2,000 ms: {out['TLE_mode_share_pct']:.1f}%   "
          f"MLE at {out['MLE_mode_kb']} KB: {out['MLE_mode_share_pct']:.1f}%")
    print(f"  users={out['n_users']} median_subs={out['median_subs_per_user']:.0f} "
          f">=5: {out['users_ge5']}  rating {out['rating_min']:.0f}-"
          f"{out['rating_max']:.0f} median {out['rating_median']:.0f}")
    for name, _ in tiers:
        t = out['figure2_tiers'][name]
        print(f"  tier {name:10s} n={t['n']:5d}  " +
              ' '.join(f"{v}={t[v]:.1f}%" for v in pa.KEEP))

    print('\nManuscript check (Table 1 + footnote + Figure 2 caption):')
    ok = True
    for q, printed, tol in EXPECTED:
        if q.startswith(('WA_', 'TLE_', 'RE_', 'CE_', 'MLE_')) and \
                q.split('_', 1)[1] in ('count', 'pct', 'mean_ms'):
            v, field = q.split('_', 1)
            actual = out['by_verdict'][v][{'pct': 'share_pct',
                                           'mean_ms': 'mean_time_ms'}.get(field, field)]
        else:
            actual = out[q]
        good = abs(actual - printed) <= tol
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {q:26s} "
              f"manuscript {printed:>8}  artifact {actual:.4g}")
    print('=' * 68)
    print('DATASET DESCRIPTIVES ' + ('PASSED' if ok else 'FAILED'))
    print('=' * 68)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
