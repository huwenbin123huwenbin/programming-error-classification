#!/usr/bin/env python3
"""
Preprocess the raw Codeforces export into the analysis dataset.

Input : ../01_原始数据/codeforces_final_real.csv  (13,360 failing submissions)
Output: preprocessed_data.csv      (one row per submission, six model fields
                                    plus user/verdict identifiers)
        feature_config.json        (field list, class distribution, split sizes)

This script is the first stage of the reproducibility chain documented in the
paper. Stage two is pipeline_authoritative.py, which retrains every model and
regenerates every number and figure in the manuscript.

Run:  python3 preprocess_data.py
"""
import csv, json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(ROOT), '01_原始数据', 'codeforces_final_real.csv')
if not os.path.exists(SRC):                       # repository-layout fallback
    SRC = os.path.join(ROOT, '01_原始数据', 'codeforces_final_real.csv')

KEEP = ['CE', 'TLE', 'MLE', 'WA', 'RE']
FEATURES = ['problem_rating', 'time_consumed_ms', 'memory_kb',
            'language_encoded', 'passed_test_count', 'problem_type']

EXPECTED = {'CE': 980, 'TLE': 1288, 'MLE': 202, 'WA': 10234, 'RE': 656}


def main():
    rows, dropped = [], 0
    with open(SRC, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['verdict'] not in KEEP:
                dropped += 1
                continue
            try:
                rating = float(r['problem_rating'])
                time_ms = float(r['time_consumed_ms'])
            except (ValueError, TypeError):
                dropped += 1
                continue
            idx = (r['problem_index'] or '').strip().upper()
            rows.append({
                'submission_id': r['submission_id'],
                'user_handle': r['user_handle'],
                'problem_rating': rating,
                'time_consumed_ms': time_ms,
                'memory_kb': float(r['memory_kb']) if r['memory_kb'].strip() else 0.0,
                'passed_test_count': float(r['passed_test_count']) if r['passed_test_count'].strip() else 0.0,
                'language': (r['language'] or '').strip(),
                'problem_slot': ord(idx[0]) - ord('A') + 1 if idx else 0,
                'verdict': r['verdict'],
            })

    langs = sorted({r['language'] for r in rows})
    lang_map = {l: i for i, l in enumerate(langs)}
    for r in rows:
        r['language_encoded'] = lang_map[r['language']]

    counts = Counter(r['verdict'] for r in rows)
    out_csv = os.path.join(HERE, 'preprocessed_data.csv')
    fields = (['submission_id', 'user_handle'] + FEATURES +
              ['language', 'problem_slot', 'verdict'])
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})

    config = {
        'source': os.path.relpath(SRC, ROOT),
        'n_samples': len(rows),
        'n_features': len(FEATURES),
        'features': FEATURES,
        'note': ('problem_slot was released as problem_type in earlier versions; '
                 'passed_test_count replaces the hour field, which cannot be '
                 'constructed because the public payload carries no timestamp'),
        'class_distribution': dict(counts),
        'classes': sorted(counts),
        'languages': len(langs),
        'train_test_split': {'method': 'stratified', 'test_size': 0.2,
                             'random_state': 42,
                             'expected_train': 10688, 'expected_test': 2672},
        'dropped_rows': dropped,
    }
    with open(os.path.join(HERE, 'feature_config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=1, ensure_ascii=False)

    print(f'samples           : {len(rows)}')
    print(f'class distribution: {dict(counts)}')
    print(f'languages         : {len(langs)}')
    print(f'written           : {out_csv}')

    # ---- verification gate: abort loudly if the dataset drifted ----
    problems = []
    if len(rows) != 13360:
        problems.append(f'sample count {len(rows)} != 13360')
    for k, v in EXPECTED.items():
        if counts.get(k) != v:
            problems.append(f'class {k}: {counts.get(k)} != {v}')
    if problems:
        raise SystemExit('DATASET CHECK FAILED:\n  ' + '\n  '.join(problems))
    print('dataset check     : OK (13,360 rows; class counts match the paper)')


if __name__ == '__main__':
    main()
