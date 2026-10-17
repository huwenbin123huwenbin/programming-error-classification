#!/usr/bin/env python3
"""
Submitter-disjoint replication under the AUTHORITATIVE six-feature protocol.

The earlier user_disjoint_replication.py (and its user_disjoint_results.json)
ran under the deprecated feature set (constant hour=12, leaky
user_success_rate); its numbers do not describe the paper's model. This script
repeats the GroupShuffleSplit replication with the six fields of
pipeline_authoritative.py and the same model hyperparameters.

Split: GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42) over
user_handle (identical parameters to the earlier script, so the user partition
is reproduced); only the features and model set change.
"""
import json
import os
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_authoritative import load_rows, matrix, FEATURES, models, SEED

rows, _ = load_rows()
X, y = matrix(rows, FEATURES)
groups = np.array([r['user'] for r in rows])

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
train_idx, test_idx = next(gss.split(X, groups=groups))
train_users = {rows[i]['user'] for i in train_idx}
test_users = {rows[i]['user'] for i in test_idx}
overlap = train_users & test_users
print(f"rows={len(rows)} train={len(train_idx)} test={len(test_idx)}")
print(f"train_users={len(train_users)} test_users={len(test_users)} overlap={len(overlap)}")

X_tr, X_te = X[train_idx], X[test_idx]
y_tr, y_te = y[train_idx], y[test_idx]

out = {'split': 'user-disjoint (GroupShuffleSplit, group=user_handle, random_state=42)',
       'n_train': int(len(train_idx)), 'n_test': int(len(test_idx)),
       'user_overlap_train_test': len(overlap), 'features': FEATURES,
       'results': {}}

for name in ['Gradient Boosting', 'Random Forest', 'Logistic Regression']:
    model = models()[name]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv = []
    for tr2, va2 in skf.split(X_tr, y_tr):
        m = models()[name]
        m.fit(X_tr[tr2], y_tr[tr2])
        cv.append(accuracy_score(y_tr[va2], m.predict(X_tr[va2])))
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    acc = accuracy_score(y_te, pred)
    mf1 = f1_score(y_te, pred, average='macro')
    cf1 = f1_score(y_te, pred, average=None, labels=['CE', 'TLE', 'MLE', 'WA', 'RE'])
    bal = f1_score(y_te, pred, average='macro')  # placeholder, replaced below
    from sklearn.metrics import balanced_accuracy_score
    bal = balanced_accuracy_score(y_te, pred)
    out['results'][name] = {
        'cv_mean': float(np.mean(cv)), 'cv_std': float(np.std(cv)),
        'test_accuracy': float(acc), 'macro_f1': float(mf1),
        'balanced_accuracy': float(bal),
        'per_class_f1': dict(zip(['CE', 'TLE', 'MLE', 'WA', 'RE'],
                                 [float(v) for v in cf1])),
    }
    print('%-20s test=%.4f cv=%.4f(+-%.4f) macroF1=%.4f bal=%.4f  F1=%s'
          % (name, acc, np.mean(cv), np.std(cv), mf1, bal,
             {k: round(v, 3) for k, v in zip(['CE', 'TLE', 'MLE', 'WA', 'RE'], cf1)}))

here = os.path.dirname(os.path.abspath(__file__))
dst = os.path.join(here, 'user_disjoint_results_v3.json')
with open(dst, 'w') as f:
    json.dump(out, f, indent=1)
print('wrote', dst)
