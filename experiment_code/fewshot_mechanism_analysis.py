#!/usr/bin/env python3
"""Few-shot mechanism analysis -- review item M5, artifact-grounded arm.

The question M5 asks
--------------------
Two simulated reviews fault the paper for not reporting a "DeepSeek-V3
few-shot" result and for not explaining *why* worked examples change the
model's behaviour. The archived 64.55% file cannot answer either question (no
script produces it; its test-set distribution is ~14 sd from the authoritative
split; see deprecated_artifacts/fewshot_full_results_v4.README.md). A clean
dose-response (0 / 3 / 15 examples at fixed batching) needs a fresh DeepSeek
run, which needs an API key.

What this script can establish without an API key
-------------------------------------------------
The repository holds two DeepSeek-V3 runs on the *identical* 2,672-item
authoritative test partition, both verified row-for-row by
verify_mcnemar_alignment.py:

  A. deepseek_zero-shot_full_20260620_164311.json
     single-item calls, no worked examples             -> 78.29% accuracy
  B. deepseek_fair_rerun_predictions.json
     three worked examples, eight submissions per call -> 76.65% valid accuracy

Comparing them quantifies the mechanism the reviews ask about: the examples do
not merely "spread predictions", they decide whether the model applies the
platform encoding at all.

Confound (stated, not hidden)
-----------------------------
Example count (0 vs 3) co-varies with call format (single-item vs batch of 8).
The comparison therefore establishes the mechanism's direction and size on this
pair of runs; it is not a controlled dose-response. A 15-shot arm at fixed
batching would close that gap and needs an API key.

Outputs: experiment_results/fewshot_mechanism.json + printed summary.
"""
import json
import math
import os
import sys
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

LLM = os.path.join(ROOT, 'llm_experiments')
OUT = os.path.join(ROOT, 'experiment_results', 'fewshot_mechanism.json')
CLASSES = ['CE', 'TLE', 'MLE', 'WA', 'RE']


def load(name):
    with open(os.path.join(LLM, name), encoding='utf-8') as f:
        d = json.load(f)
    return d['predictions'] if isinstance(d, dict) and 'predictions' in d else d


def sorted_records(preds):
    """Align to the authoritative partition: sort by idx when present,
    otherwise trust the single-item file order (the gate has verified both)."""
    if preds and 'idx' in preds[0]:
        return sorted(preds, key=lambda p: p['idx'])
    return preds


def arm(name, preds, y_te):
    recs = sorted_records(preds)
    assert len(recs) == len(y_te), f'{name}: n={len(recs)} != {len(y_te)}'
    truth = [str(t) for t in y_te]
    # alignment re-check: the gate proves this, but a mechanism claim is only
    # as good as its pairing
    mism = sum(1 for r, t in zip(recs, truth) if str(r['true_label']) != t)
    assert mism == 0, f'{name}: {mism} label mismatches against the partition'
    valid = [r for r in recs if r['prediction'] in CLASSES]
    n = len(valid)
    acc_all = sum(1 for r in recs if r['prediction'] == r['true_label']) / len(recs)
    acc_valid = sum(1 for r in valid if r['prediction'] == r['true_label']) / n
    pc = Counter(r['prediction'] for r in valid)
    tc = Counter(truth)
    ent = -sum((c / n) * math.log2(c / n) for c in pc.values())
    per_class = {}
    for cls in CLASSES:
        tp = sum(1 for r in valid if r['true_label'] == cls and r['prediction'] == cls)
        fp = sum(1 for r in valid if r['true_label'] != cls and r['prediction'] == cls)
        fn = sum(1 for r in valid if r['true_label'] == cls and r['prediction'] != cls)
        per_class[cls] = {
            'recall': tp / (tp + fn) if tp + fn else 0.0,
            'precision': tp / (tp + fp) if tp + fp else 0.0,
            'tp': tp, 'fp': fp, 'fn': fn,
        }
    return {
        'file': name,
        'n_records': len(recs),
        'n_valid': n,
        'n_invalid': len(recs) - n,
        'accuracy_all': acc_all,
        'accuracy_valid': acc_valid,
        'prediction_distribution': {c: pc.get(c, 0) for c in CLASSES},
        'true_distribution': {c: tc.get(c, 0) for c in CLASSES},
        'prediction_entropy_bits': ent,
        'max_entropy_bits': math.log2(len(CLASSES)),
        'wa_share_of_predictions': pc.get('WA', 0) / n,
        'per_class': per_class,
    }


def main():
    rows, _ = pa.load_rows()
    y = np.array([r['verdict'] for r in rows])
    idx = np.arange(len(rows))
    _, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED, stratify=y)
    y_te = [str(y[i]) for i in te]

    arms = {
        'zero_shot_single_item': arm(
            'deepseek_zero-shot_full_20260620_164311.json',
            load('deepseek_zero-shot_full_20260620_164311.json'), y_te),
        'three_shot_batch8': arm(
            'deepseek_fair_rerun_predictions.json',
            load('deepseek_fair_rerun_predictions.json'), y_te),
    }

    z, t = arms['zero_shot_single_item'], arms['three_shot_batch8']
    report = {
        'test_partition': {'n': len(y_te),
                           'true_distribution': dict(Counter(y_te))},
        'arms': arms,
        'mechanism': {
            'wa_share_zero_shot': z['wa_share_of_predictions'],
            'wa_share_three_shot': t['wa_share_of_predictions'],
            'entropy_ratio': t['prediction_entropy_bits'] / z['prediction_entropy_bits'],
            'ce_recall_zero_shot': z['per_class']['CE']['recall'],
            'ce_recall_three_shot': t['per_class']['CE']['recall'],
            'ce_precision_zero_shot': z['per_class']['CE']['precision'],
            'ce_precision_three_shot': t['per_class']['CE']['precision'],
            'accuracy_delta_pp': (t['accuracy_valid'] - z['accuracy_all']) * 100,
            're_recall_zero_shot': z['per_class']['RE']['recall'],
            're_recall_three_shot': t['per_class']['RE']['recall'],
        },
        'confound': ('example count (0 vs 3) co-varies with call format '
                     '(single-item vs batch of 8); direction and size are '
                     'established, a controlled dose-response is not'),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    m = report['mechanism']
    print('Few-shot mechanism on the shared authoritative test partition')
    print(f"  partition n={len(y_te)}  true={report['test_partition']['true_distribution']}")
    for k, a in arms.items():
        print(f"\n  == {k} ({a['file']})")
        print(f"     accuracy: all={a['accuracy_all']*100:.2f}%  "
              f"valid={a['accuracy_valid']*100:.2f}%  (invalid {a['n_invalid']})")
        print(f"     prediction distribution: {a['prediction_distribution']}")
        print(f"     prediction entropy: {a['prediction_entropy_bits']:.3f} / "
              f"{a['max_entropy_bits']:.3f} bits   WA share: "
              f"{a['wa_share_of_predictions']*100:.1f}%")
        for cls in CLASSES:
            c = a['per_class'][cls]
            print(f"       {cls}: recall={c['recall']:.3f} precision={c['precision']:.3f}")
    print('\n  == mechanism ==')
    print(f"     WA share of predictions: {m['wa_share_zero_shot']*100:.1f}% -> "
          f"{m['wa_share_three_shot']*100:.1f}%")
    print(f"     prediction entropy x{m['entropy_ratio']:.2f}")
    print(f"     CE recall {m['ce_recall_zero_shot']:.3f} -> {m['ce_recall_three_shot']:.3f}; "
          f"CE precision {m['ce_precision_zero_shot']:.3f} -> {m['ce_precision_three_shot']:.3f}")
    print(f"     RE recall {m['re_recall_zero_shot']:.3f} -> {m['re_recall_three_shot']:.3f}")
    print(f"     accuracy (valid basis): {m['accuracy_delta_pp']:+.2f} pp")
    print(f"\n  wrote {OUT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
