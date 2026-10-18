"""Learning curve for the Gradient Boosting model (protocol A).

The manuscript (Section 4.4, "Learning curves confirm that the gap to the
LLMs is not a data-volume artefact") prints the measured curve this script
produces: 85.8% at 200, 87.7% at 400, 91.1% at 2,800 and 91.8% at 10,688
training submissions (the full training partition). Round 13 added this
script: the paragraph previously carried three figures (87.8% / 91.5% /
91.8%, "saturates by roughly a quarter of the available data") that matched
no artifact — the middle point sits 0.4pp above every reproducible variant
and the saturation claim contradicts the measured curve (the gain beyond
2,800 is 0.65pp, not 0.3pp). The printed figures are now the five-repeat
means, and the argument is carried by the 400-submission point (11.1pp above
the strongest prompted LLM) instead of by a saturation claim.

Subsets are drawn with a fixed seed per size (plain random, not stratified:
the point of the curve is what an arbitrary sample of the available
submissions buys). Five repeats per size are averaged so the curve is not a
single-seed artefact; the printed figures are single-seed style, so the
check tolerance reflects repeat spread, not exact equality.

Run: python learning_curve.py
Writes: experiment_results/learning_curve.json
"""
import json
import os
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

OUT = os.path.join(HERE, '..', 'experiment_results', 'learning_curve.json')

# training-subset sizes to sweep; the last is the full training partition
SIZES = [200, 400, 800, 1600, 2800, 4200, 5600, 8400, 10688]
N_REPEAT = 5

# figures printed in the manuscript: (n_train, accuracy%, tolerance_pp)
EXPECTED = [(200, 85.8, 0.15), (400, 87.7, 0.15), (2800, 91.1, 0.15),
            (10688, 91.8, 0.15)]
# Table 6 (tab:sensitivity) rows -- every printed row must reproduce
TABLE_EXPECTED = [(200, 85.8, 0.05), (400, 87.7, 0.05), (800, 89.8, 0.05),
                  (1600, 90.5, 0.05), (2800, 91.1, 0.05), (4200, 91.5, 0.05),
                  (5600, 91.8, 0.05), (8400, 91.8, 0.05), (10688, 91.77, 0.05)]


def main():
    rows, _ = pa.load_rows()
    X, y = pa.matrix(rows, pa.FEATURES)
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED,
                              stratify=y)
    X_te, y_te = X[te], y[te]

    curve = []
    for n in SIZES:
        n = min(n, len(tr))
        accs = []
        for rep in range(N_REPEAT):
            rng = np.random.RandomState(pa.SEED + rep)
            sub = rng.choice(tr, size=n, replace=False)
            m = pa.models()['Gradient Boosting']
            m.fit(X[sub], y[sub])
            accs.append(float((m.predict(X_te) == y_te).mean()))
        curve.append({
            'n_train': int(n),
            'share_of_training': round(n / len(tr), 4),
            'accuracy_mean': float(np.mean(accs)),
            'accuracy_std': float(np.std(accs)),
            'accuracy_runs': [round(a, 4) for a in accs],
        })
        print(f"  n={n:6d} ({n/len(tr)*100:5.1f}% of train)  "
              f"acc={np.mean(accs)*100:.2f}% +/- {np.std(accs)*100:.2f}")

    out = {
        'model': 'Gradient Boosting (protocol A, six fields)',
        'n_test': int(len(te)),
        'n_train_full': int(len(tr)),
        'n_repeat': N_REPEAT,
        'curve': curve,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)

    print('\nManuscript check (Section 4.4):')
    ok = True
    for n, printed, tol in EXPECTED:
        row = next(c for c in curve if c['n_train'] == n)
        actual = row['accuracy_mean'] * 100
        good = abs(actual - printed) <= tol
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] n={n:6d}  "
              f"manuscript {printed:.1f}%  artifact {actual:.2f}% "
              f"(+/- {row['accuracy_std']*100:.2f})")
    # Table 6 (tab:sensitivity): every printed row
    print('Table 6 rows:')
    for n, printed, tol in TABLE_EXPECTED:
        row = next(c for c in curve if c['n_train'] == n)
        actual = row['accuracy_mean'] * 100
        good = abs(actual - printed) <= tol
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] n={n:6d}  "
              f"table {printed:.2f}%  artifact {actual:.2f}%")
    # the "gap is not a data-volume artefact" claim: at 400 submissions the
    # model already leads the strongest prompted LLM (76.65%) by > 11 pp
    a400 = next(c for c in curve if c['n_train'] == 400)['accuracy_mean']
    lead = (a400 - 0.7665) * 100
    good = lead >= 11.0
    ok &= good
    print(f"  [{'PASS' if good else 'FAIL'}] lead over DeepSeek-V3 at n=400 "
          f">= 11.0pp: artifact {lead:.2f}pp")
    print('LEARNING CURVE OK' if ok else 'LEARNING CURVE MISMATCH')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
