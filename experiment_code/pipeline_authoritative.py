#!/usr/bin/env python3
"""
Authoritative pipeline for the Codeforces verdict-classification study.

Corrections applied to the earlier analysis
-------------------------------------------
1. `hour` removed. The public submission payload carries no timestamp, so the
   former feature was a constant (12). It is replaced by `passed_test_count`,
   which *is* in the payload and is one of the five fields the LLMs received.
2. `user_success_rate` removed from the primary model. It was computed over the
   whole dataset, so each row's own label contributed to its own predictor
   (target leakage); the dataset also contains only failing submissions, so a
   true success rate cannot be formed. A leakage-free variant is retained as an
   ablation to show that the aggregate does not help.
3. Logistic Regression is standardised before fitting; the earlier run never
   converged on raw features spanning five orders of magnitude.

Protocols
---------
A. stratified random 80/20 split  (identical rows to the LLM runs)
B. user-disjoint split            (cold-start setting, no submitter overlap)

Usage:  /usr/bin/python3 experiment_code/pipeline_authoritative.py [stage]
        stage in {a, b, misc, llm, figs, all}
"""
import csv, json, os, sys, itertools
from collections import defaultdict, Counter
import numpy as np

from sklearn.model_selection import (train_test_split, GroupShuffleSplit,
                                     StratifiedKFold)
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, f1_score, balanced_accuracy_score,
                             confusion_matrix, log_loss)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(os.path.dirname(ROOT), '01_原始数据', 'codeforces_final_real.csv')
if not os.path.exists(CSV):
    CSV = os.path.join(ROOT, '01_原始数据', 'codeforces_final_real.csv')
OUT_JSON = os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')

KEEP = ['CE', 'TLE', 'MLE', 'WA', 'RE']
# primary feature set: exactly the five fields shown to the LLMs, plus the
# problem slot letter (an ordinal position within the contest)
FEATURES = ['problem_rating', 'time_consumed_ms', 'memory_kb',
            'language_encoded', 'passed_test_count', 'problem_type']
FEATURES_LLM = ['problem_rating', 'time_consumed_ms', 'memory_kb',
                'language_encoded', 'passed_test_count']
SEED = 42


# ----------------------------------------------------------------- data ----
def load_rows():
    rows = []
    with open(CSV, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['verdict'] not in KEEP:
                continue
            try:
                pr = float(r['problem_rating']); tc = float(r['time_consumed_ms'])
            except (ValueError, TypeError):
                continue
            idx = (r['problem_index'] or '').strip().upper()
            rows.append({
                'user': r['user_handle'],
                'problem_rating': pr,
                'time_consumed_ms': tc,
                'memory_kb': float(r['memory_kb']) if r['memory_kb'].strip() else 0.0,
                'passed_test_count': float(r['passed_test_count']) if r['passed_test_count'].strip() else 0.0,
                'language': (r['language'] or '').strip(),
                'problem_type': ord(idx[0]) - ord('A') + 1 if idx else 0,
                'verdict': r['verdict'],
            })
    langs = sorted({r['language'] for r in rows})
    lm = {l: i for i, l in enumerate(langs)}
    for r in rows:
        r['language_encoded'] = lm[r['language']]
    return rows, langs


def matrix(rows, feats):
    X = np.array([[r[f] for f in feats] for r in rows], dtype=float)
    y = np.array([r['verdict'] for r in rows])
    return X, y


def user_rate(rows, train_idx):
    """Leakage-free user aggregate: computed on training users only."""
    agg = defaultdict(lambda: [0, 0])
    for i in train_idx:
        agg[rows[i]['user']][1] += 1
        if rows[i]['verdict'] == 'WA':
            agg[rows[i]['user']][0] += 1
    rate = {u: v[0] / v[1] for u, v in agg.items() if v[1]}
    prior = float(np.mean(list(rate.values())))
    return np.array([rate.get(r['user'], prior) for r in rows]), prior


# --------------------------------------------------------------- models ----
def models():
    return {
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=SEED),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=SEED),
        'Logistic Regression': Pipeline([
            ('scale', StandardScaler()),
            ('clf', LogisticRegression(max_iter=5000, random_state=SEED))]),
    }


def mcnemar(ca, cb):
    from scipy.stats import binomtest, chi2
    b = int(np.sum(ca & ~cb)); c = int(np.sum(~ca & cb)); n = b + c
    if n == 0:
        return {'b': 0, 'c': 0, 'p_value': 1.0, 'test': 'none'}
    if n < 25:
        return {'b': b, 'c': c, 'p_value': float(binomtest(min(b, c), n, 0.5).pvalue),
                'test': 'exact binomial'}
    stat = (abs(b - c) - 1) ** 2 / n
    return {'b': b, 'c': c, 'chi2': float(stat),
            'p_value': float(chi2.sf(stat, 1)), 'test': 'chi2 continuity-corrected'}


def boot(y, p, n_boot=1000):
    rng = np.random.RandomState(SEED)
    a = [accuracy_score(y[i], p[i]) for i in (rng.randint(0, len(y), len(y)) for _ in range(n_boot))]
    return {'mean': float(np.mean(a)), 'ci_lower': float(np.percentile(a, 2.5)),
            'ci_upper': float(np.percentile(a, 97.5))}


def fit_eval(model, X_tr, y_tr, X_te, y_te):
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    cf1 = f1_score(y_te, pred, labels=KEEP, average=None, zero_division=0)
    cm = confusion_matrix(y_te, pred, labels=KEEP)
    res = {
        'train_accuracy': float(accuracy_score(y_tr, model.predict(X_tr))),
        'test_accuracy': float(accuracy_score(y_te, pred)),
        'macro_f1': float(f1_score(y_te, pred, average='macro')),
        'weighted_f1': float(f1_score(y_te, pred, average='weighted')),
        'balanced_accuracy': float(balanced_accuracy_score(y_te, pred)),
        'class_f1': {k: round(float(v), 4) for k, v in zip(KEEP, cf1)},
        'confusion_matrix': {f'{a}_{b}': int(cm[i, j]) for i, a in enumerate(KEEP)
                             for j, b in enumerate(KEEP)},
        'cm_matrix': cm.tolist(),
        'bootstrap': boot(y_te, pred),
    }
    if hasattr(model, 'feature_importances_'):
        res['feature_importance'] = {f: round(float(v) * 100, 2)
                                     for f, v in zip(FEATURES, model.feature_importances_)}
    if isinstance(model, Pipeline):
        co = model.named_steps['clf'].coef_
        res['lr_abs_coef'] = {f: round(float(np.abs(co[:, i]).mean()), 3)
                              for i, f in enumerate(FEATURES)}
        res['lr_n_iter'] = int(model.named_steps['clf'].n_iter_[0])
    return res, pred


# ------------------------------------------------------------- protocol -----
def protocol(rows, tr, te, label, feats=FEATURES, extra=None):
    X, y = matrix(rows, feats)
    if extra is not None:                     # append a leakage-free user rate
        X = np.column_stack([X, extra])
    X_tr, X_te, y_tr, y_te = X[tr], X[te], y[tr], y[te]
    print(f'\n=== {label} === train {len(tr)} / test {len(te)}')
    out = {'protocol': label, 'features': feats + (['user_wa_rate'] if extra is not None else []),
           'n_train': len(tr), 'n_test': len(te),
           'test_class_distribution': {k: int((y_te == k).sum()) for k in KEEP},
           'models': {}}
    preds = {}
    for name in models():
        res, pred = fit_eval(models()[name], X_tr, y_tr, X_te, y_te)
        # honest 5-fold CV: aggregate recomputed inside each fold
        skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
        sc = []
        for a, b in skf.split(X_tr, y_tr):
            m = models()[name]
            m.fit(X_tr[a], y_tr[a])
            sc.append(accuracy_score(y_tr[b], m.predict(X_tr[b])))
        res['cv_mean'] = float(np.mean(sc)); res['cv_std'] = float(np.std(sc))
        out['models'][name] = res; preds[name] = pred
        print(f"  {name:22s} acc={res['test_accuracy']*100:.2f}% F1m={res['macro_f1']:.4f} "
              f"BAcc={res['balanced_accuracy']:.3f} cv={res['cv_mean']*100:.2f}")
        print('     class F1:', res['class_f1'])
        if 'feature_importance' in res:
            print('     Gini:', res['feature_importance'])
        if 'lr_n_iter' in res:
            print('     LR iters:', res['lr_n_iter'])
    tests = []
    for a, b in itertools.combinations(preds, 2):
        r = mcnemar(preds[a] == y_te, preds[b] == y_te)
        r['comparison'] = f'{a} vs {b}'
        tests.append(r)
    for r in tests:
        r['p_bonferroni'] = float(min(1.0, r['p_value'] * len(tests)))
        r['significant'] = bool(r['p_bonferroni'] < 0.05)
    out['mcnemar'] = tests
    print('  McNemar:')
    for r in tests:
        print(f"    {r['comparison']:45s} p={r['p_value']:.2e} b={r['b']} c={r['c']}")
    return out, preds, X_tr, y_tr, X_te, y_te


# -------------------------------------------------------------- analysis ----
def collision_analysis(rows):
    """Observational equivalence: identical execution signatures, different verdicts."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r['time_consumed_ms'], r['memory_kb'], r['passed_test_count'])].append(r['verdict'])
    mixed = {k: Counter(v) for k, v in groups.items() if len(set(v)) > 1}
    rows_in_mixed = sum(sum(c.values()) for c in mixed.values())
    biggest = max(mixed.items(), key=lambda kv: sum(kv[1].values()))
    out = {
        'n_signature_groups': len(groups),
        'n_mixed_groups': len(mixed),
        'rows_in_mixed_groups': rows_in_mixed,
        'share_in_mixed_groups': round(rows_in_mixed / len(rows), 4),
        'largest_group_signature': {'time_ms': biggest[0][0], 'memory_kb': biggest[0][1],
                                    'passed_tests': biggest[0][2],
                                    'composition': dict(biggest[1]),
                                    'size': sum(biggest[1].values())},
    }
    print('\n=== Observational equivalence ===')
    print(json.dumps(out, indent=1))
    # how often does a CE submission share its signature with a non-CE one?
    ce = [r for r in rows if r['verdict'] == 'CE']
    ce_shared = sum(1 for r in ce
                    if len(set(groups[(r['time_consumed_ms'], r['memory_kb'],
                                       r['passed_test_count'])])) > 1)
    out['ce_rows_sharing_signature'] = ce_shared
    out['ce_share_sharing_signature'] = round(ce_shared / len(ce), 4)
    print(f'  CE rows sharing signature with another class: {ce_shared}/{len(ce)}')
    return out


def homogeneity(rows):
    by = defaultdict(list)
    for r in rows:
        by[r['user']].append(r['verdict'])
    shares, ents = [], []
    for vs in by.values():
        p = np.array([vs.count(k) for k in KEEP], dtype=float); p /= p.sum()
        shares.append(p.max())
        nz = p[p > 0]; ents.append(float(-(nz * np.log(nz)).sum()))
    glob = np.array([sum(1 for r in rows if r['verdict'] == k) for k in KEEP], float)
    gp = glob / glob.sum(); ge = float(-(gp * np.log(gp)).sum())
    out = {'n_users': len(by), 'mean_modal_share': float(np.mean(shares)),
           'mean_user_entropy': float(np.mean(ents)), 'global_entropy': ge,
           'entropy_ratio': float(np.mean(ents) / ge),
           'median_submissions_per_user': float(np.median([len(v) for v in by.values()])),
           'users_ge5': int(sum(1 for v in by.values() if len(v) >= 5))}
    print('\n=== User clustering ===')
    print(json.dumps(out, indent=1))
    return out


def ablation(rows, tr, te):
    X, y = matrix(rows, FEATURES)
    X_tr, X_te, y_tr, y_te = X[tr], X[te], y[tr], y[te]
    full = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                      learning_rate=0.1, random_state=SEED).fit(X_tr, y_tr)
    base = full.predict(X_te); base_acc = accuracy_score(y_te, base)
    print(f'\n=== Ablation (GB, full={base_acc*100:.2f}%) ===')
    out = []
    for j, f in enumerate(FEATURES):
        keep = [i for i in range(len(FEATURES)) if i != j]
        m = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                       learning_rate=0.1, random_state=SEED).fit(X_tr[:, keep], y_tr)
        p = m.predict(X_te[:, keep])
        acc = accuracy_score(y_te, p)
        r = mcnemar(base == y_te, p == y_te)
        out.append({'removed_feature': f, 'accuracy': round(float(acc), 4),
                    'drop_pp': round(float((base_acc - acc) * 100), 2), 'p_value': r['p_value']})
        print(f"  -{f:20s} acc={acc*100:.2f}% drop={(base_acc-acc)*100:+.2f}pp p={r['p_value']:.2e}")
    # leakage-free user aggregate added on top of the primary set
    rate, prior = user_rate(rows, tr)
    X2 = np.column_stack([X, rate])
    m = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                   learning_rate=0.1, random_state=SEED).fit(X2[tr], y_tr)
    acc = accuracy_score(y_te, m.predict(X2[te]))
    out.append({'removed_feature': '+user_wa_rate (added)', 'accuracy': round(float(acc), 4),
                'drop_pp': round(float((base_acc - acc) * 100), 2), 'p_value': None,
                'note': 'leakage-free aggregate added to the primary six features'})
    print(f"  +user_wa_rate (leakage-free) acc={acc*100:.2f}% (prior={prior:.3f})")
    return out, base_acc


def sensitivity(X_tr, y_tr, X_te, y_te):
    print('\n=== Sensitivity (GB) ===')
    out = []; rng = np.random.RandomState(SEED)
    for n in [400, 600, 800, 1600, 2800, 5300, len(X_tr)]:
        if n > len(X_tr):
            continue
        idx = np.arange(len(X_tr)) if n == len(X_tr) else rng.choice(len(X_tr), n, replace=False)
        m = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                       learning_rate=0.1, random_state=SEED).fit(X_tr[idx], y_tr[idx])
        out.append({'n': int(n), 'acc': round(float(accuracy_score(y_te, m.predict(X_te))) * 100, 2)})
        print(f'  n={out[-1]["n"]:6d} acc={out[-1]["acc"]:.2f}%')
    return out


def score_llm(path, y_te):
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    preds = d['predictions'] if isinstance(d, dict) and 'predictions' in d else d
    if len(preds) != len(y_te):
        return None
    by_idx = {p['idx']: p for p in preds}
    if len(by_idx) != len(preds):
        return None
    gold, lab = [], []
    for i in range(len(y_te)):
        p = by_idx.get(i)
        if p is None:
            return None
        gold.append(y_te[i])
        q = (p.get('prediction') or p.get('predicted') or '').strip().upper()
        lab.append(q if (q in KEEP and p.get('valid') is not False) else None)
    gold = np.array(gold)
    ok = np.array([l is not None for l in lab])
    gv = gold[ok]; pv = np.array([l for l in lab if l is not None])
    cf1 = f1_score(gv, pv, labels=KEEP, average=None, zero_division=0)
    out = {'file': os.path.basename(path), 'n_total': len(lab), 'n_valid': int(ok.sum()),
           'invalid_rate': round(float(1 - ok.mean()), 4),
           'accuracy_valid_only': float(accuracy_score(gv, pv)),
           'accuracy_invalid_as_wrong': float(np.mean([1.0 if l == g else 0.0
                                                       for g, l in zip(gold, lab)])),
           'macro_f1_valid_only': float(f1_score(gv, pv, average='macro')),
           'balanced_accuracy_valid_only': float(balanced_accuracy_score(gv, pv)),
           'class_f1_valid_only': {k: round(float(v), 4) for k, v in zip(KEEP, cf1)},
           'predicted_distribution': {k: int((pv == k).sum()) for k in KEEP},
           'labels': lab}
    print(f"  {out['file'][:46]:46s} acc(valid)={out['accuracy_valid_only']*100:.2f}% "
          f"acc(all)={out['accuracy_invalid_as_wrong']*100:.2f}% inv={out['invalid_rate']*100:.1f}%")
    print('     class F1:', out['class_f1_valid_only'])
    return out


# ------------------------------------------------------------------ main ----
def main(stage='all'):
    rows, langs = load_rows()
    y = np.array([r['verdict'] for r in rows])
    idx = np.arange(len(rows))
    print(f'Rows: {len(rows)}  languages: {len(langs)}  '
          f'platform-encoded share: {np.isin(y, ["CE","TLE","MLE"]).mean()*100:.1f}%')

    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y)
    gss = GroupShuffleSplit(1, test_size=0.2, random_state=SEED)
    trb, teb = next(gss.split(idx, y, np.array([r['user'] for r in rows])))

    if os.path.exists(OUT_JSON):
        res = json.load(open(OUT_JSON))
    else:
        res = {}
    res.setdefault('meta', {
        'n_samples': len(rows), 'classes': KEEP, 'features': FEATURES,
        'features_llm': FEATURES_LLM, 'random_seed': SEED,
        'class_distribution': {k: int((y == k).sum()) for k in KEEP},
        'platform_encoded_share': round(float(np.isin(y, ['CE','TLE','MLE']).mean()), 4),
        'language_map': langs,
        'corrections': ['hour removed (constant, no timestamp in payload)',
                        'passed_test_count added (payload field, also given to LLMs)',
                        'user aggregate feature removed from primary model (target leakage)',
                        'Logistic Regression standardised (previous run did not converge)'],
    })

    if stage in ('all', 'a'):
        A, _, X_tr, y_tr, X_te, y_te = protocol(rows, tr, te, 'A: stratified random 80/20')
        res['protocol_a'] = A
        json.dump(res, open(OUT_JSON, 'w'), indent=1, ensure_ascii=False)
        print('-- saved A')

    if stage in ('all', 'b'):
        B, *_ = protocol(rows, trb, teb, 'B: user-disjoint')
        g = np.array([r['user'] for r in rows])
        B.update({'overlap_users': int(len(set(g[trb]) & set(g[teb]))),
                  'n_users_train': int(len(set(g[trb]))),
                  'n_users_test': int(len(set(g[teb]))),
                  'test_users_multi': int(sum(1 for u in set(g[teb]) if (g[teb] == u).sum() > 1)),
                  'max_subs_test_user': int(max((g[teb] == u).sum() for u in set(g[teb])))})
        res['protocol_b'] = B
        json.dump(res, open(OUT_JSON, 'w'), indent=1, ensure_ascii=False)
        print('-- saved B')

    if stage in ('all', 'misc'):
        res['collision'] = collision_analysis(rows)
        res['homogeneity'] = homogeneity(rows)
        X, _ = matrix(rows, FEATURES)
        res['ablation'], res['ablation_base'] = ablation(rows, tr, te)
        res['sensitivity'] = sensitivity(X[tr], y[tr], X[te], y[te])
        json.dump(res, open(OUT_JSON, 'w'), indent=1, ensure_ascii=False)
        print('-- saved misc')

    if stage in ('all', 'llm'):
        _, _, _, _, X_te, y_te = protocol(rows, tr, te, 'A (for LLM alignment)')
        print('\n=== LLM re-scoring on the identical test rows ===')
        llm = {}
        for p in ['llm_experiments/deepseek_fair_rerun_predictions.json',
                  'llm_experiments/qwen25_fair_rerun_predictions.json',
                  'ds_v4_predictions.json']:
            r = score_llm(os.path.join(ROOT, p), y_te)
            if r:
                llm[r['file']] = r
        # 5-field GB (exactly the LLM inputs) for a like-for-like comparison
        X5, _ = matrix(rows, FEATURES_LLM)
        m = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                       learning_rate=0.1, random_state=SEED)
        m.fit(X5[tr], y[tr]); p5 = m.predict(X5[te])
        llm['gb_5field'] = {
            'accuracy': float(accuracy_score(y_te, p5)),
            'macro_f1': float(f1_score(y_te, p5, average='macro')),
            'balanced_accuracy': float(balanced_accuracy_score(y_te, p5)),
            'class_f1': {k: round(float(v), 4) for k, v in
                         zip(KEEP, f1_score(y_te, p5, labels=KEEP, average=None, zero_division=0))},
            'labels': p5.tolist()}
        print(f"  {'GB (5 fields)':46s} acc={llm['gb_5field']['accuracy']*100:.2f}%")
        ds = llm.get('deepseek_fair_rerun_predictions.json')
        if ds:
            mask = np.array([l is not None for l in ds['labels']])
            gbc = np.array(llm['gb_5field']['labels']) == y_te
            dsc = np.array([l == g for l, g in zip(ds['labels'], y_te)])
            r = mcnemar(gbc[mask], dsc[mask]); r['comparison'] = 'GB-5field vs DeepSeek-V3'
            llm['mcnemar_gb5_vs_deepseek'] = r
            print('  McNemar GB5 vs DeepSeek:', r)
        res['llm'] = llm
        json.dump(res, open(OUT_JSON, 'w'), indent=1, ensure_ascii=False)
        print('-- saved llm')

    print('\nDone:', OUT_JSON)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
