#!/usr/bin/env python3
"""Gate: LLM prediction files must align row-for-row with the authoritative
test partition before any McNemar test that uses them can be trusted.

Why this gate exists
--------------------
The LLM prediction files store one record per call *batch*, so the file order
is the batch order, not the sample order (the first eight records carry
idx 0-7, the next eight idx 24-31, and so on). Two audits silently disagreed
because one zipped the file order against the pipeline's test-set order and
the other sorted by idx. Only one of them is right.

The check below rebuilds the authoritative partition with
pipeline_authoritative, sorts each LLM file by idx, and compares the verdict,
rating and language sequences element by element. A file passes only if all
three sequences are identical; anything less means the McNemar pairing is
partly scrambled and the chi-square values in Table 8 cannot be attributed to
that file.

Exit 0 = every file aligns; exit 1 = at least one file is scrambled.
"""
import json
import os
import sys

import numpy as np
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

LLM = os.path.join(ROOT, 'llm_experiments')

FILES = [
    'deepseek_fair_rerun_predictions.json',
    'qwen25_fair_rerun_predictions.json',
    'deepseek_zero-shot_full_20260620_164311.json',
    'qwen25_3b_zeroshot_full_20260620_181736.json',
]


def load_predictions(name):
    with open(os.path.join(LLM, name), encoding='utf-8') as f:
        d = json.load(f)
    if isinstance(d, dict) and 'predictions' in d:
        return d['predictions']
    return d


def check(name, v_te, r_te, l_te):
    preds = load_predictions(name)
    has_idx = bool(preds) and 'idx' in preds[0]
    if has_idx:
        seq = sorted(preds, key=lambda p: p['idx'])
        if [p['idx'] for p in seq] != list(range(len(seq))):
            print(f'  [FAIL] {name}: idx values are not a permutation of 0..n-1')
            return False
        basis = 'idx-sorted'
    else:
        # single-item writers stored one record per submission in file order
        seq = preds
        basis = 'file-order'
    v = [p['true_label'] for p in seq]
    r = [int(p['problem_rating']) for p in seq] if 'problem_rating' in seq[0] else None
    l = [p['language'] for p in seq] if 'language' in seq[0] else None
    dv = sum(1 for a, b in zip(v_te, v) if a != b)
    dr = sum(1 for a, b in zip(r_te, r) if a != b) if r else 0
    dl = sum(1 for a, b in zip(l_te, l) if a != b) if l else 0
    ok = (dv, dr, dl) == (0, 0, 0)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} ({basis}): n={len(seq)} "
          f"verdict_diff={dv} rating_diff={dr} language_diff={dl}")
    return ok


def main():
    rows, _ = pa.load_rows()
    y = np.array([r['verdict'] for r in rows])
    idx = np.arange(len(rows))
    _, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED, stratify=y)
    v_te = [str(y[i]) for i in te]
    r_te = [int(rows[i]['problem_rating']) for i in te]
    l_te = [rows[i]['language'] for i in te]

    print('LLM file alignment against the authoritative test partition')
    print(f'  partition: n={len(te)} classes={sorted(set(v_te))}')
    results = [check(n, v_te, r_te, l_te) for n in FILES]
    print('=' * 68)
    print('ALIGNMENT ' + ('PASSED' if all(results) else 'FAILED'))
    print('=' * 68)
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
