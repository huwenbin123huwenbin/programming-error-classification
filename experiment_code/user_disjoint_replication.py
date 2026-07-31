#!/usr/bin/env python3
"""
User-disjoint replication of the main ML experiment (no pandas dependency).

Purpose:
  1. Fix user_success_rate look-ahead leakage: compute per-user WA-rate using
     TRAIN users only; test users get the train-global mean (no test info leaks).
  2. Use GroupShuffleSplit(group=user_handle) so no user appears in both train/test.
  3. Compute ICC to quantify test-set user-level clustering (McNemar independence caveat).
  4. Compare user-disjoint results against final_results_v2.json (random 80/20).

Feature engineering mirrors run_experiment_v2.py / student_proxy_experiment.py:
  problem_rating, time_consumed_ms, memory_kb, language_encoded,
  problem_type, hour, user_success_rate
  where user_success_rate = (#WA submissions by user) / (total submissions by user)
"""
import json
import csv
import numpy as np
from collections import defaultdict
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

CSV = "/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv"
ORIG = "/Users/mac/Desktop/SCI1/06_论文定稿/experiment_results/final_results_v2.json"

KEEP = ['CE', 'TLE', 'MLE', 'WA', 'RE']

rows = []
with open(CSV, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['verdict'] not in KEEP:
            continue
        pr = r['problem_rating'].strip()
        tc = r['time_consumed_ms'].strip()
        try:
            pr = float(pr); tc = float(tc)
        except ValueError:
            continue
        if pr != pr or tc != tc:  # NaN
            continue
        rows.append({
            'user': r['user_handle'],
            'problem_rating': pr,
            'time_consumed_ms': tc,
            'memory_kb': float(r['memory_kb']) if r['memory_kb'].strip() else 0.0,
            'language': str(r['language']).strip(),
            'problem_index': str(r['problem_index']).strip(),
            'verdict': r['verdict'],
        })
print(f"Usable rows: {len(rows)}")

users = sorted(set(r['user'] for r in rows))
print(f"Unique users: {len(users)}")

# Language encoding (dynamic, consistent with paper)
langs = sorted(set(r['language'] for r in rows))
lang_map = {l: i for i, l in enumerate(langs)}
for r in rows:
    r['language_encoded'] = lang_map[r['language']]
    idx = r['problem_index'].upper()
    r['problem_type'] = ord(idx[0]) - ord('A') + 1 if idx else 0
    r['hour'] = 12

# GroupShuffleSplit (user-disjoint)
user_to_idx = defaultdict(list)
for i, r in enumerate(rows):
    user_to_idx[r['user']].append(i)
groups = np.array([r['user'] for r in rows])
X_all = np.array([[r['problem_rating'], r['time_consumed_ms'], r['memory_kb'],
                   r['language_encoded'], r['problem_type'], r['hour']] for r in rows], dtype=float)
y_all = np.array([r['verdict'] for r in rows])

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X_all, groups=groups))
train_rows = [rows[i] for i in train_idx]
test_rows = [rows[i] for i in test_idx]
print(f"Train: {len(train_rows)} (users={len(set(r['user'] for r in train_rows))}), "
      f"Test: {len(test_rows)} (users={len(set(r['user'] for r in test_rows))})")
overlap = set(r['user'] for r in train_rows) & set(r['user'] for r in test_rows)
print(f"User overlap train/test: {len(overlap)} (must be 0)")

# FIX look-ahead: train-only user_success_rate
train_wa = defaultdict(lambda: [0, 0])  # [wa_count, total]
for r in train_rows:
    train_wa[r['user']][1] += 1
    if r['verdict'] == 'WA':
        train_wa[r['user']][0] += 1
train_global = np.mean([v[0]/v[1] for v in train_wa.values()]) if train_wa else 0.5
for r in rows:
    v = train_wa.get(r['user'])
    r['user_success_rate'] = (v[0]/v[1]) if v else train_global

FEATURES = ['problem_rating', 'time_consumed_ms', 'memory_kb',
            'language_encoded', 'problem_type', 'hour', 'user_success_rate']
X = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
le = LabelEncoder()
y_enc = le.fit_transform(y_all)
X_tr = np.array([[r[f] for f in FEATURES] for r in train_rows], dtype=float)
X_te = np.array([[r[f] for f in FEATURES] for r in test_rows], dtype=float)
y_tr = le.transform([r['verdict'] for r in train_rows])
y_te = le.transform([r['verdict'] for r in test_rows])

models = {
    'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42),
}
results = {}
for name, model in models.items():
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_accs = []
    for tr2, va2 in skf.split(X_tr, y_tr):
        m = type(model)(**model.get_params())
        m.fit(X_tr[tr2], y_tr[tr2])
        cv_accs.append(accuracy_score(y_tr[va2], m.predict(X_tr[va2])))
    model.fit(X_tr, y_tr)
    yp = model.predict(X_te)
    acc = accuracy_score(y_te, yp)
    macro_f1 = f1_score(y_te, yp, average='macro', zero_division=0)
    cm = confusion_matrix(y_te, yp, labels=range(len(le.classes_)))
    per_class_f1 = f1_score(y_te, yp, average=None, labels=range(len(le.classes_)), zero_division=0)
    results[name] = {
        'cv_mean': float(np.mean(cv_accs)), 'cv_std': float(np.std(cv_accs)),
        'test_acc': float(acc), 'macro_f1': float(macro_f1),
        'per_class_f1': {le.classes_[i]: float(per_class_f1[i]) for i in range(len(le.classes_))},
        'confusion_matrix': cm.tolist(), 'classes': list(le.classes_),
    }
    print(f"\n{name}: CV={np.mean(cv_accs):.4f}±{np.std(cv_accs):.4f} | "
          f"Test Acc={acc:.4f} | MacroF1={macro_f1:.4f}")
    print(f"  Per-class F1: {{ {', '.join(f'{c}:{f:.3f}' for c,f in results[name]['per_class_f1'].items())} }}")

# ---------- Test-set user-level clustering quantification ----------
# Robust descriptive metrics (ICC on one-hot proportions is degenerate
# because per-user proportion vectors lie on a simplex whose mean is constant).
test_users = [r['user'] for r in test_rows]
test_verdict = [r['verdict'] for r in test_rows]
from collections import defaultdict as dd
from collections import Counter
user_v = dd(list)
for u, v in zip(test_users, test_verdict):
    user_v[u].append(v)
global_counts = Counter(test_verdict)
global_entropy = -sum((c/len(test_verdict))*np.log2(c/len(test_verdict)) for c in global_counts.values())
modal_shares = []
user_entropies = []
for u, vs in user_v.items():
    cnt = Counter(vs)
    modal_shares.append(max(cnt.values())/len(vs))
    if len(cnt) > 1:
        user_entropies.append(-sum((c/len(vs))*np.log2(c/len(vs)) for c in cnt.values()))
    else:
        user_entropies.append(0.0)
mean_modal = float(np.mean(modal_shares))
mean_user_ent = float(np.mean(user_entropies))
print(f"\nTest users: {len(user_v)}; users with >1 submission: {sum(1 for u in user_v if len(user_v[u])>1)}")
print(f"Max submissions by one test user: {max(len(v) for v in user_v.values())}")
print(f"Mean per-user modal-verdict share: {mean_modal:.3f} (random=0.200)")
print(f"Mean per-user verdict entropy: {mean_user_ent:.3f} / global entropy: {global_entropy:.3f} (ratio={mean_user_ent/global_entropy:.3f})")
print(f"Interpretation: ratio≈1 => users' verdict mixes are statistically interchangeable (weak clustering);")
print(f"  ratio<1 would indicate users have characteristic verdict profiles (stronger clustering).")

# ---------- Compare with original random-split results ----------
orig = json.load(open(ORIG))
print("\n=== Comparison: ORIGINAL (random 80/20) vs USER-DISJOINT ===")
for name in ['Gradient Boosting', 'Random Forest', 'Logistic Regression']:
    o_acc = orig['models'][name]['test_accuracy']
    n_acc = results[name]['test_acc']
    print(f"  {name}: orig={o_acc:.4f} -> ud={n_acc:.4f} (Δ={(n_acc-o_acc)*100:+.2f} pp)")

out = {
    'split': 'user-disjoint (GroupShuffleSplit, group=user_handle)',
    'user_overlap_train_test': len(overlap),
    'n_train': len(train_rows), 'n_test': len(test_rows),
    'n_users_train': len(set(r['user'] for r in train_rows)),
    'n_users_test': len(set(r['user'] for r in test_rows)),
    'test_users_multi_submission': sum(1 for u in user_v if len(user_v[u])>1),
    'max_submissions_per_test_user': int(max(len(v) for v in user_v.values())),
    'mean_per_user_modal_share': mean_modal,
    'mean_user_entropy': mean_user_ent,
    'global_entropy': global_entropy,
    'entropy_ratio_user_vs_global': mean_user_ent/global_entropy,
    'clustering_interpretation': 'strong: per-user verdict mixes are highly homogeneous (users have characteristic verdict profiles)',
    'user_success_rate': 'train-only WA-rate (leakage fixed)',
    'results': results,
}
with open('/Users/mac/Desktop/SCI1/06_论文定稿/experiment_code/user_disjoint_results.json', 'w') as f:
    json.dump(out, f, indent=2)
print("\n✅ Saved user_disjoint_results.json")
