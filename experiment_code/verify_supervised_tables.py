"""Verify the supervised-result tables and the claims that read them out.

Covers, in order:

  1. Table 2 (tab:ml-results)   -- RF / GB / LR test accuracy, bootstrap CI,
                                   CV mean +/- SD, macro F1, balanced accuracy,
                                   and the three difference claims in the text
                                   (GB-vs-RF agreement, LR trail in accuracy
                                   and in macro F1).
  2. Table 3 (tab:gb-cm)        -- the full 5x5 confusion matrix and per-class
                                   F1, re-derived by retraining Gradient
                                   Boosting on the protocol-A split (the model
                                   is deterministic, so this both checks the
                                   manuscript against the artifact and the
                                   artifact against a fresh run), plus the
                                   note's claims: 261 CE predictions, all of
                                   them on the all-zero signature, 79 WA->CE
                                   and 6 RE->CE.
  3. Gini figure caption        -- the six importances and the 89.0 / 11.0 /
                                   <=3.6% readings, from the same retraining.
  4. Section 4 narrative        -- LR recovering 5 of 196 CEs, TLE recall 1.00
                                   with four false positives, MLE/WA F1 0.95,
                                   the 87.8% share, the 79-of-98 exchange
                                   count, the four execution-based confusions,
                                   RE recall 0.22 / 94-of-131 / precision 0.66.
  5. Section 5.4 (robustness)   -- the submitter-disjoint replication numbers
                                   (93.13 / 92.15 / 91.99 / 87.15 and the
                                   per-class F1s) and the corpus homogeneity
                                   figures (4,005 submitters, median 2, mean
                                   3.34, maximum 134).

Static expectations are checked against experiment_results/
authoritative_results_v3.json, the artifact pipeline_authoritative.py
writes. The GB retrain additionally proves that artifact reproduces.

Run: python verify_supervised_tables.py
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

ROOT = os.path.dirname(HERE)
AUTH = os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')

# manuscript table order (differs from KEEP order)
COLS = ['CE', 'MLE', 'RE', 'TLE', 'WA']          # tab:gb-cm column order
CLASSES = ['CE', 'TLE', 'MLE', 'WA', 'RE']       # pa.KEEP order

# Table 2, protocol A: (model, quantity, printed, tolerance)
ML_EXPECTED = [
    ('Random Forest', 'test_accuracy', 91.80, 0.005),
    ('Random Forest', 'ci_lower', 90.8, 0.05),
    ('Random Forest', 'ci_upper', 92.8, 0.05),
    ('Random Forest', 'cv_mean', 92.36, 0.005),
    ('Random Forest', 'cv_std', 0.54, 0.005),
    ('Random Forest', 'macro_f1', 0.798, 0.0005),
    ('Random Forest', 'balanced_accuracy', 0.791, 0.0005),
    ('Gradient Boosting', 'test_accuracy', 91.77, 0.005),
    ('Gradient Boosting', 'ci_lower', 90.6, 0.05),
    ('Gradient Boosting', 'ci_upper', 92.8, 0.05),
    ('Gradient Boosting', 'cv_mean', 92.42, 0.005),
    ('Gradient Boosting', 'cv_std', 0.33, 0.005),
    ('Gradient Boosting', 'macro_f1', 0.799, 0.0005),
    ('Gradient Boosting', 'balanced_accuracy', 0.804, 0.0005),
    ('Logistic Regression', 'test_accuracy', 85.63, 0.005),
    ('Logistic Regression', 'ci_lower', 84.2, 0.05),
    ('Logistic Regression', 'ci_upper', 86.9, 0.05),
    ('Logistic Regression', 'cv_mean', 86.03, 0.005),
    ('Logistic Regression', 'cv_std', 0.23, 0.005),
    ('Logistic Regression', 'macro_f1', 0.494, 0.0005),
    ('Logistic Regression', 'balanced_accuracy', 0.486, 0.0005),
]

# Table 3 rows in manuscript order, columns CE, MLE, RE, TLE, WA
CM_EXPECTED = {
    'CE': [176, 0, 0, 0, 20],
    'MLE': [0, 38, 1, 1, 0],
    'RE': [6, 1, 29, 1, 94],
    'TLE': [0, 0, 0, 258, 0],
    'WA': [79, 1, 14, 2, 1951],
}
F1_EXPECTED = {'CE': 0.77, 'MLE': 0.95, 'RE': 0.33, 'TLE': 0.99, 'WA': 0.95}

# Gini caption: field -> printed percent (of impurity reduction)
GINI_EXPECTED = [('time_consumed_ms', 81.5), ('memory_kb', 7.5),
                 ('problem_rating', 3.5), ('language_encoded', 3.5),
                 ('passed_test_count', 3.2), ('problem_type', 0.9)]

# submitter-disjoint replication (protocol B), Section 5.4
PROTOB_EXPECTED = [
    ('Gradient Boosting', 'test_accuracy', 93.13, 0.005),
    ('Gradient Boosting', 'cv_mean', 92.15, 0.005),
    ('Gradient Boosting', 'class_f1', 'CE', 0.788, 0.0005),
    ('Gradient Boosting', 'class_f1', 'TLE', 1.000, 0.0005),
    ('Gradient Boosting', 'class_f1', 'MLE', 0.988, 0.0005),
    ('Gradient Boosting', 'class_f1', 'WA', 0.957, 0.0005),
    ('Gradient Boosting', 'class_f1', 'RE', 0.256, 0.0005),
    ('Random Forest', 'test_accuracy', 91.99, 0.005),
    ('Logistic Regression', 'test_accuracy', 87.15, 0.005),
]

# corpus homogeneity, Section 5.4
HOMOGENEITY_EXPECTED = [('n_users', 4005, 0), ('median_subs', 2, 0),
                        ('mean_subs', 3.34, 0.005), ('max_subs', 134, 0)]


def report(name, good, detail):
    print(f"  [{'PASS' if good else 'FAIL'}] {name:44s} {detail}")
    return good


def main():
    with open(AUTH, encoding='utf-8') as f:
        auth = json.load(f)
    models = auth['protocol_a']['models']
    ok = True

    # ---------------------------------------------------------- Table 2
    print('Table 2 (tab:ml-results) vs authoritative_results_v3.json:')
    for model, q, printed, tol in ML_EXPECTED:
        m = models[model]
        if q == 'ci_lower':
            actual = m['bootstrap']['ci_lower'] * 100
        elif q == 'ci_upper':
            actual = m['bootstrap']['ci_upper'] * 100
        elif q == 'cv_mean':
            actual = m['cv_mean'] * 100
        elif q == 'cv_std':
            actual = m['cv_std'] * 100
        elif q == 'test_accuracy':
            actual = m['test_accuracy'] * 100
        else:
            actual = m[q]
        ok &= report(f'{model} {q}', abs(actual - printed) <= tol,
                     f'manuscript {printed}  artifact {actual:.4g}')

    # the three difference claims in the Table 2 paragraph
    rf, gb, lr = (models['Random Forest'], models['Gradient Boosting'],
                  models['Logistic Regression'])
    d_ens = abs(rf['test_accuracy'] - gb['test_accuracy']) * 100
    d_lr_acc = (gb['test_accuracy'] - lr['test_accuracy']) * 100
    d_lr_f1 = gb['macro_f1'] - lr['macro_f1']
    ok &= report('GB vs RF agreement (0.04pp)', abs(d_ens - 0.04) <= 0.005,
                 f'manuscript 0.04  artifact {d_ens:.4f}')
    ok &= report('LR trail in accuracy (6.1pp)', abs(d_lr_acc - 6.1) <= 0.05,
                 f'manuscript 6.1  artifact {d_lr_acc:.4f}')
    ok &= report('LR trail in macro F1 (0.30)', abs(d_lr_f1 - 0.30) <= 0.005,
                 f'manuscript 0.30  artifact {d_lr_f1:.4f}')
    mc = next(r for r in auth['protocol_a']['mcnemar']
              if r['comparison'] == 'Gradient Boosting vs Random Forest')
    ok &= report('GB vs RF McNemar (chi2=0.00, p=1.00)',
                 abs(mc['chi2']) < 0.005 and abs(mc['p_value'] - 1.0) < 1e-9,
                 f"artifact chi2={mc['chi2']:.2f} p={mc['p_value']:.2f}")

    # --------------------------------------- Table 3 + Gini + narrative
    # retrain GB: deterministic, so this both reproduces the artifact and
    # yields the predictions the note-level claims need
    print('\nRetraining Gradient Boosting (protocol A) for Tables 3 / Figure 5:')
    rows, _ = pa.load_rows()
    X, y = pa.matrix(rows, pa.FEATURES)
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED,
                              stratify=y)
    model = pa.models()['Gradient Boosting'].fit(X[tr], y[tr])
    pred = model.predict(X[te])
    cm = {a: {b: 0 for b in CLASSES} for a in CLASSES}
    for t, p in zip(y[te], pred):
        cm[t][p] += 1
    f1 = {c: round(float(v), 4) for c, v in
          zip(CLASSES, f1_score(y[te], pred, labels=CLASSES, average=None,
                                zero_division=0))}

    print('\nTable 3 (tab:gb-cm) vs retrained model:')
    for a in CM_EXPECTED:
        for j, b in enumerate(COLS):
            ok &= report(f'cm[{a}][{b}]', cm[a][b] == CM_EXPECTED[a][j],
                         f'manuscript {CM_EXPECTED[a][j]}  artifact {cm[a][b]}')
    for c in COLS:
        ok &= report(f'class F1 {c}', abs(f1[c] - F1_EXPECTED[c]) <= 0.005,
                     f'manuscript {F1_EXPECTED[c]:.2f}  artifact {f1[c]:.4f}')
    # the same matrix against the stored artifact (reproducibility)
    stored = models['Gradient Boosting']['cm_matrix']
    ok &= report('cm reproduces the stored artifact',
                 [[cm[a][b] for b in CLASSES] for a in CLASSES] == stored,
                 'retrained == authoritative_results_v3.json')

    # note-level claims that need predictions, not just counts
    ce_pred_idx = [k for k, p in enumerate(pred) if p == 'CE']
    all_zero = all(rows[te[k]]['time_consumed_ms'] == 0
                   and rows[te[k]]['memory_kb'] == 0
                   and rows[te[k]]['passed_test_count'] == 0 for k in ce_pred_idx)
    ok &= report('all CE predictions on the all-zero signature',
                 len(ce_pred_idx) == 261 and all_zero,
                 f'{len(ce_pred_idx)} CE predictions, all-zero={all_zero}')
    ok &= report('79 WA->CE and 6 RE->CE cells',
                 cm['WA']['CE'] == 79 and cm['RE']['CE'] == 6,
                 f"artifact WA->CE={cm['WA']['CE']} RE->CE={cm['RE']['CE']}")
    for a in CLASSES:
        ok &= report(f'{a} row sums to support',
                     sum(cm[a].values()) == int((y[te] == a).sum()),
                     f"row {sum(cm[a].values())} vs support {int((y[te]==a).sum())}")

    print('\nGini caption vs retrained model:')
    imp = model.feature_importances_ * 100
    for f, printed in GINI_EXPECTED:
        v = imp[pa.FEATURES.index(f)]
        ok &= report(f'Gini {f}', abs(v - printed) <= 0.06,
                     f'manuscript {printed}  artifact {v:.2f}')
    exec_two = imp[pa.FEATURES.index('time_consumed_ms')] + \
        imp[pa.FEATURES.index('memory_kb')]
    prob_four = 100 - exec_two
    ok &= report('execution pair share (89.0%)', abs(exec_two - 89.0) <= 0.06,
                 f'manuscript 89.0  artifact {exec_two:.2f}')
    ok &= report('problem fields share (11.0%)', abs(prob_four - 11.0) <= 0.06,
                 f'manuscript 11.0  artifact {prob_four:.2f}')
    ok &= report('no problem field exceeds 3.6%',
                 max(imp[pa.FEATURES.index(f)] for f in
                     ['problem_rating', 'language_encoded',
                      'passed_test_count', 'problem_type']) <= 3.6,
                 f"artifact max {max(imp[pa.FEATURES.index(f)] for f in ['problem_rating','language_encoded','passed_test_count','problem_type']):.2f}")

    print('\nSection 4 narrative claims:')
    lr_cm = models['Logistic Regression']['cm_matrix']   # KEEP order
    k = {c: i for i, c in enumerate(CLASSES)}
    ok &= report('LR recovers 5 of 196 CEs (F1 0.05, 191 as WA)',
                 lr_cm[k['CE']][k['CE']] == 5 and lr_cm[k['CE']][k['WA']] == 191
                 and abs(models['Logistic Regression']['class_f1']['CE']
                         - 0.05) <= 0.005,
                 f"artifact {lr_cm[k['CE']][k['CE']]} CE, "
                 f"{lr_cm[k['CE']][k['WA']]} WA, F1="
                 f"{models['Logistic Regression']['class_f1']['CE']}")
    tle_fp = sum(cm[a]['TLE'] for a in CLASSES) - cm['TLE']['TLE']
    ok &= report('TLE recall 1.00, four false positives',
                 cm['TLE']['TLE'] == 258 and tle_fp == 4,
                 f"artifact recall {cm['TLE']['TLE']}/258, FP={tle_fp}")
    ok &= report('MLE and WA at F1 0.95',
                 abs(f1['MLE'] - 0.95) <= 0.005 and abs(f1['WA'] - 0.95) <= 0.005,
                 f"artifact MLE {f1['MLE']:.4f} WA {f1['WA']:.4f}")
    share3 = (int((y[te] == 'TLE').sum()) + int((y[te] == 'MLE').sum())
              + int((y[te] == 'WA').sum())) / len(y[te]) * 100
    ok &= report('three execution classes = 87.8% of test',
                 abs(share3 - 87.8) <= 0.05, f'artifact {share3:.2f}')
    err3 = (sum(cm['WA'].values()) - cm['WA']['WA']
            + sum(cm['MLE'].values()) - cm['MLE']['MLE']
            + sum(cm['TLE'].values()) - cm['TLE']['TLE'])
    ok &= report('79 of 98 errors are exchanges with CE',
                 err3 == 98 and cm['WA']['CE'] == 79,
                 f'artifact {err3} errors, {cm["WA"]["CE"]} WA->CE')
    ok &= report('four execution-based confusions (2+1+1)',
                 cm['WA']['TLE'] == 2 and cm['WA']['MLE'] == 1
                 and cm['MLE']['TLE'] == 1,
                 f"artifact WA->TLE={cm['WA']['TLE']} WA->MLE={cm['WA']['MLE']} "
                 f"MLE->TLE={cm['MLE']['TLE']}")
    ok &= report('RE recall 0.22, 94 of 131 as WA',
                 abs(cm['RE']['RE'] / 131 - 0.22) <= 0.005
                 and cm['RE']['WA'] == 94,
                 f"artifact {cm['RE']['RE']}/131, {cm['RE']['WA']} WA")
    re_prec = cm['RE']['RE'] / sum(cm[a]['RE'] for a in CLASSES)
    ok &= report('RE precision 0.66', abs(re_prec - 0.66) <= 0.005,
                 f'artifact {re_prec:.4f}')

    # ---------------------------------------------- protocol B / homogeneity
    print('\nSubmitter-disjoint replication (protocol B):')
    bmodels = auth['protocol_b']['models']
    for item in PROTOB_EXPECTED:
        model_name, q, printed, tol = item[0], item[1], item[-2], item[-1]
        m = bmodels[model_name]
        if q == 'class_f1':
            actual = m['class_f1'][item[2]]
        elif q == 'test_accuracy':
            actual = m['test_accuracy'] * 100
        else:
            actual = m[q] * 100
        ok &= report(f'B {model_name} {q}'
                     + (f' {item[2]}' if q == 'class_f1' else ''),
                     abs(actual - printed) <= tol,
                     f'manuscript {printed}  artifact {actual:.4g}')
    b = auth['protocol_b']
    ok &= report('B split sizes / zero overlap',
                 b['n_train'] == 10900 and b['n_test'] == 2460
                 and b['overlap_users'] == 0,
                 f"artifact {b['n_train']}/{b['n_test']}, overlap {b['overlap_users']}")

    print('\nCorpus homogeneity (Section 5.4):')
    sizes = defaultdict(int)
    for r in rows:
        sizes[r['user']] += 1
    vals = list(sizes.values())
    actual = {'n_users': len(vals), 'median_subs': float(np.median(vals)),
              'mean_subs': len(rows) / len(vals), 'max_subs': max(vals)}
    for q, printed, tol in HOMOGENEITY_EXPECTED:
        ok &= report(q, abs(actual[q] - printed) <= tol,
                     f'manuscript {printed}  artifact {actual[q]:.4g}')

    print('SUPERVISED TABLES OK' if ok else 'SUPERVISED TABLES MISMATCH')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
