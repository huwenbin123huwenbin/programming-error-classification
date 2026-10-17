#!/usr/bin/env python3
"""
Equivalence spectrum: how much of the corpus sits in mixed signature groups,
and how binding each group actually is.

The paper reports the two largest mixed groups because they are the ones that
bind Compilation Error and the WA<->RE distinction. A reviewer will ask the
obvious follow-up: 95 mixed groups cover 64.8% of the corpus, so why single out
two of them? This script answers that question quantitatively.

Two measures are reported:

1. Normalised entropy of each mixed group, H / log(k), where k is the number of
   verdicts present. A group holding 99% WA and 1% RE is mixed but almost pure;
   a group split 50/50 is maximally binding.

2. Majority-class recall ceiling per verdict: assign every group to its modal
   verdict, then count how many rows of each verdict survive. This is the best
   any metadata-only classifier can do on this corpus if it must commit to one
   label per signature, expressed as a recall ceiling per class.

Output: experiment_results/equivalence_spectrum.json
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_authoritative import load_rows, ROOT  # noqa: E402

OUT = os.path.join(ROOT, 'experiment_results', 'equivalence_spectrum.json')


def entropy(counts):
    n = sum(counts.values())
    return -sum((c / n) * math.log(c / n) for c in counts.values() if c > 0)


def main():
    rows, _ = load_rows()
    groups = defaultdict(Counter)
    for r in rows:
        key = (r['time_consumed_ms'], r['memory_kb'], r['passed_test_count'])
        groups[key][r['verdict']] += 1

    mixed = [(k, Counter(v)) for k, v in groups.items() if len(set(v)) > 1]
    mixed.sort(key=lambda kv: -sum(kv[1].values()))

    # --- entropy spectrum -------------------------------------------------
    spectrum = []
    for k, c in mixed:
        n = sum(c.values())
        h = entropy(c)
        h_norm = h / math.log(len(c)) if len(c) > 1 else 0.0
        spectrum.append({
            'signature': {'time_ms': k[0], 'memory_kb': k[1], 'passed_tests': k[2]},
            'size': n,
            'composition': dict(c),
            'entropy': round(h, 4),
            'entropy_norm': round(h_norm, 4),
            'modal_share': round(max(c.values()) / n, 4),
        })

    hs = sorted(s['entropy_norm'] for s in spectrum)
    def q(p):
        return hs[min(len(hs) - 1, int(p * len(hs)))]

    high = [s for s in spectrum if s['entropy_norm'] >= 0.5]
    low = [s for s in spectrum if s['entropy_norm'] < 0.5]

    # --- majority-class rule over the three-field signature --------------
    # A rule that sees only (time, memory, tests) and must commit to one label
    # per signature. This is NOT a bound on the six-field models; it quantifies
    # how much of the corpus the signature alone cannot resolve.
    verdicts = ['CE', 'TLE', 'MLE', 'WA', 'RE']
    total = Counter(r['verdict'] for r in rows)
    recovered = Counter()
    lost = Counter()
    modal_errors = 0
    for _, c in mixed:
        win, win_n = c.most_common(1)[0]
        recovered[win] += win_n
        for v, n in c.items():
            if v != win:
                lost[v] += n
                modal_errors += n
    for _, v in groups.items():
        if len(set(v)) == 1:
            recovered[next(iter(v))] += sum(v.values())

    modal_rule = {
        'errors': modal_errors,
        'error_rate': round(modal_errors / len(rows), 4),
        'by_verdict': {
            v: {
                'total': total[v],
                'recovered': recovered[v],
                'lost': lost[v],
                'recall_under_modal_rule': round(recovered[v] / total[v], 4),
            }
            for v in verdicts
        },
    }

    out = {
        'n_rows': len(rows),
        'n_signature_groups': len(groups),
        'n_mixed_groups': len(mixed),
        'rows_in_mixed_groups': sum(s['size'] for s in spectrum),
        'share_in_mixed_groups': round(sum(s['size'] for s in spectrum) / len(rows), 4),
        'entropy_norm': {
            'median': round(q(0.5), 4),
            'q25': round(q(0.25), 4),
            'q75': round(q(0.75), 4),
            'max': round(hs[-1], 4),
        },
        'high_entropy_groups': {
            'n': len(high),
            'rows': sum(s['size'] for s in high),
            'share_of_corpus': round(sum(s['size'] for s in high) / len(rows), 4),
        },
        'low_entropy_groups': {
            'n': len(low),
            'rows': sum(s['size'] for s in low),
            'share_of_corpus': round(sum(s['size'] for s in low) / len(rows), 4),
        },
        'modal_rule_signature_only': modal_rule,
        'top_groups': spectrum[:6],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print(json.dumps({k: v for k, v in out.items() if k != 'top_groups'},
                     indent=1, ensure_ascii=False))
    print('\nTop groups:')
    for s in out['top_groups']:
        print(f"  {s['size']:5d} rows  H_norm={s['entropy_norm']:.2f}  "
              f"modal={s['modal_share']:.2f}  {s['composition']}  {s['signature']}")


if __name__ == '__main__':
    main()
