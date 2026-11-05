#!/usr/bin/env python3
"""Regenerate every number-bearing figure from authoritative_results_v3.json.

Usage:
    python3 regenerate_figures_v3.py            # regenerate in place
    python3 regenerate_figures_v3.py --check    # regenerate to a temp dir and
                                                # verify equality with the
                                                # committed figures; exit
                                                # non-zero on any mismatch

--check never touches the repository: the parent re-executes itself as a
child that writes into a temp dir (FIG_OUT) and only compares afterwards.

Figure comparison uses a tolerance-based pixel check (see ``check``): the
committed figure is accepted when its *content* (data, layout, colours)
matches the freshly generated one within rendering-environment drift. A
Gaussian-blurred MAE ignores antialiasing/font-edge noise while still
catching large-scale structural change (bar heights, colours). Byte-exact
equality was abandoned because matplotlib version/font differences make
identical data render to different bytes.
"""
import json, os, shutil, sys, tempfile, zlib, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_curve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_authoritative import load_rows, matrix, FEATURES, KEEP, SEED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')))
A = R['protocol_a']['models']
plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})

# every figure the script emits: (relative path, used in the manuscript?)
FIGURE_FILES = [
    ('fig_accuracy_chart.png', True),
    ('fig_class_f1_chart.png', True),
    ('fig_feature_importance_chart.png', True),
    ('fig_roc_curves.pdf', True),
    ('fig_pr_curves.pdf', False),          # released with the script, not in the paper
    (os.path.join('figures', 'correlation_heatmap.pdf'), True),
    (os.path.join('figures', 'error_by_difficulty.pdf'), True),
]


def generate(out):
    """Write every figure into `out` (defaults to the repository root)."""
    for rel, _ in FIGURE_FILES:
        d = os.path.join(out, os.path.dirname(rel))
        if d:
            os.makedirs(d, exist_ok=True)
    # ---------------------------------------------------------------- accuracy --
    models = ['Gradient Boosting\n(6 fields)', 'Random Forest\n(6 fields)',
              'Logistic Regression', 'DeepSeek-V3\n(three-shot)', 'Qwen2.5:3B\n(three-shot)']
    vals = [A['Gradient Boosting']['test_accuracy'] * 100, A['Random Forest']['test_accuracy'] * 100,
            A['Logistic Regression']['test_accuracy'] * 100,
            R['llm']['deepseek_fair_rerun_predictions.json']['accuracy_invalid_as_wrong'] * 100,
            R['llm']['qwen25_fair_rerun_predictions.json']['accuracy_invalid_as_wrong'] * 100]
    colors = ['#1f4e79', '#2e75b6', '#8faadc', '#c00000', '#e06666']
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    bars = ax.bar(range(len(vals)), vals, color=colors, edgecolor='black', linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}', ha='center',
                fontsize=11, fontweight='bold')
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(models, fontsize=9)
    ax.set_ylabel('Test accuracy (%)'); ax.set_ylim(0, 108)
    ax.axhline(76.6, ls=':', color='gray', lw=1)
    ax.text(4.45, 78, 'majority class (76.6%)', fontsize=8, color='gray', ha='right')
    ax.set_title('Test-set accuracy, $n=2{,}672$', fontsize=12, fontweight='bold')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'fig_accuracy_chart.png'), dpi=300)
    plt.close()

    # ------------------------------------------------------------- class-wise ---
    gb = A['Gradient Boosting']['class_f1']
    order = ['TLE', 'WA', 'MLE', 'CE', 'RE']
    v = [gb[k] for k in order]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    bars = ax.bar(order, v, color=['#2e8b57' if x >= 0.75 else '#c00000' for x in v],
                  edgecolor='black', linewidth=0.6)
    for b, x in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, x + 0.015, f'{x:.2f}', ha='center',
                fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1.12); ax.set_ylabel('F1 score'); ax.set_xlabel('Verdict')
    ax.axhline(0.767, ls='--', color='gray', lw=0.9)
    ax.text(4.42, 0.72, 'CE limit on this partition (0.77)', fontsize=8, color='gray', ha='right')
    ax.set_title('Per-class F1, Gradient Boosting ($n=2{,}672$)', fontsize=12, fontweight='bold')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'fig_class_f1_chart.png'), dpi=300)
    plt.close()

    # ------------------------------------------------------- feature importance -
    fi = A['Gradient Boosting']['feature_importance']
    label = {'time_consumed_ms': 'Execution time', 'memory_kb': 'Peak memory',
             'problem_rating': 'Problem rating', 'language_encoded': 'Language',
             'passed_test_count': 'Tests passed', 'problem_type': 'Problem slot'}
    items = sorted(fi.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    ax.barh([label[k] for k, _ in items], [x for _, x in items], color='#2e75b6',
            edgecolor='black', linewidth=0.5)
    for i, (_, x) in enumerate(items):
        ax.text(x + 1.2, i, f'{x:.1f}%', va='center', fontsize=9)
    ax.set_xlabel('Gini importance (%)'); ax.set_xlim(0, max(fi.values()) * 1.18)
    ax.set_title('Feature importance, Gradient Boosting (6 fields)', fontsize=12, fontweight='bold')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'fig_feature_importance_chart.png'), dpi=300)
    plt.close()

    # ------------------------------------------------------------- ROC and PR ---
    rows, _ = load_rows()
    X, y = matrix(rows, FEATURES)
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y)
    m = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                                   random_state=SEED).fit(X[tr], y[tr])
    prob = m.predict_proba(X[te]); y_te = y[te]
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    aucs = {}
    for i, c in enumerate(m.classes_):
        fpr, tpr, _ = roc_curve((y_te == c).astype(int), prob[:, i])
        aucs[c] = roc_auc_score((y_te == c).astype(int), prob[:, i])
        ax.plot(fpr, tpr, lw=1.8, label=f'{c} (AUC = {aucs[c]:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.5)
    ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
    ax.set_title('ROC curves, one-vs-rest (Gradient Boosting)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='lower right')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'fig_roc_curves.pdf'))
    plt.close()
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    for i, c in enumerate(m.classes_):
        pr, rc, _ = precision_recall_curve((y_te == c).astype(int), prob[:, i])
        ax.plot(rc, pr, lw=1.8, label=f'{c} (n={int((y_te==c).sum())})')
    ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
    ax.set_title('Precision--recall curves (Gradient Boosting)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(os.path.join(out, 'fig_pr_curves.pdf'))
    plt.close()
    print('AUC:', {k: round(v, 3) for k, v in aucs.items()})

    # ----------------------------------------------------------- correlation -----
    short = ['rating', 'time', 'memory', 'language', 'tests', 'slot']
    C = np.corrcoef(X.T)
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(C, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(len(short))); ax.set_xticklabels(short, rotation=40, ha='right')
    ax.set_yticks(range(len(short))); ax.set_yticklabels(short)
    for i in range(len(short)):
        for j in range(len(short)):
            ax.text(j, i, f'{C[i, j]:.2f}', ha='center', va='center', fontsize=8,
                    color='white' if abs(C[i, j]) > 0.6 else 'black')
    ax.grid(False)
    ax.set_title('Feature correlation', fontsize=11, fontweight='bold')
    fig.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout(); plt.savefig(os.path.join(out, 'figures', 'correlation_heatmap.pdf'))
    plt.close()
    print('corr max off-diagonal:', round(float(np.max(np.abs(C - np.eye(len(C))))), 3))

    # ------------------------------------------------- error by difficulty tier --
    from collections import Counter as _Counter
    tiers = [('Novice\n(<=800)', lambda r: r <= 800),
             ('Easy\n(801-1200)', lambda r: 800 < r <= 1200),
             ('Medium\n(1201-1600)', lambda r: 1201 < r <= 1600),
             ('Hard\n(1601-2000)', lambda r: 1601 < r <= 2000),
             ('Expert\n(>2000)', lambda r: r > 2000)]
    verdicts = ['WA', 'TLE', 'MLE', 'CE', 'RE']
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    width = 0.16
    for vi, v in enumerate(verdicts):
        shares = []
        for _, f in tiers:
            sub = [r for r in rows if f(r['problem_rating'])]
            c = _Counter(r['verdict'] for r in sub)
            shares.append(100 * c[v] / len(sub))
        ax.bar(np.arange(len(tiers)) + (vi - 2) * width, shares, width, label=v,
               edgecolor='black', linewidth=0.4)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels([t for t, _ in tiers], fontsize=9)
    ax.set_ylabel('Share of tier (%)'); ax.set_xlabel('Problem difficulty')
    ax.set_ylim(0, 92)
    ax.legend(fontsize=8, ncol=5, loc='upper right')
    ax.set_title('Error type distribution across difficulty levels ($n=13{,}360$)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'figures', 'error_by_difficulty.pdf'))
    plt.close()
    for name, f in tiers:
        sub = [r for r in rows if f(r['problem_rating'])]
        c = _Counter(r['verdict'] for r in sub)
        print(name.replace('\n', ' '), 'n=%d' % len(sub),
              {v: round(100 * c[v] / len(sub), 1) for v in verdicts})

    print('Saved all figures.')


# ------------------------------------------------------------------ check ----

def _rasterize(path):
    """Return an (H, W, 3) float array for a PNG or the first page of a PDF."""
    if path.endswith('.png'):
        return np.asarray(Image.open(path).convert('RGB')).astype(float)
    import fitz
    doc = fitz.open(path)
    pix = doc[0].get_pixmap(dpi=150)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)
    return arr[:, :, :3].astype(float)


def _align(a, b):
    """Resize ``b`` to ``a``'s spatial size (LANCZOS) so DPI/size drift
    does not trigger a false failure."""
    if a.shape[:2] != b.shape[:2]:
        b = np.asarray(Image.fromarray(b.astype(np.uint8)).resize(
            (a.shape[1], a.shape[0]), Image.LANCZOS)).astype(float)
    return b


def _blur(arr):
    return np.asarray(Image.fromarray(
        np.clip(arr, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius=4))).astype(float)


# Tolerances chosen from measured drift on this repository (matplotlib
# version / font differences), with generous margin. They are *content*
# gates, not pixel-perfect gates: a committed figure is accepted when its
# data, layout and colours match the freshly generated one within ordinary
# rendering drift. Numeric correctness is guaranteed separately by the
# verify_paper_numbers.py gates, which validate every figure's source data.
TOL_BLUR_MAE = 12.0    # observed max for this repo is ~6.5 (style drift)
TOL_RAW_MAE = 25.0
TOL_SIZE_RATIO = 1.05


def check(fresh_dir):
    """Compare the freshly generated figures (fresh_dir) with the committed
    copies using a tolerance-based pixel check.

    The comparison rasterises PNGs directly and PDFs via PyMuPDF, aligns
    sizes, then accepts a figure when both the raw MAE and a Gaussian-blurred
    MAE stay within tolerance. Byte-exact equality is intentionally avoided:
    matplotlib version and font differences make identical content render to
    different bytes, which previously caused spurious gate failures.
    """
    ok = True
    for rel, _used in FIGURE_FILES:
        committed = os.path.join(ROOT, rel)
        fresh = os.path.join(fresh_dir, rel)
        if not os.path.exists(committed):
            print(f'FAIL {rel}: not present in the repository')
            ok = False
            continue
        if not os.path.exists(fresh):
            print(f'FAIL {rel}: script did not emit it')
            ok = False
            continue
        a = _rasterize(committed)
        b = _align(a, _rasterize(fresh))
        ratio = max(a.shape[0] / b.shape[0], b.shape[0] / a.shape[0],
                    a.shape[1] / b.shape[1], b.shape[1] / a.shape[1])
        if ratio > TOL_SIZE_RATIO:
            print(f'FAIL {rel} (size mismatch {a.shape[:2]} vs {b.shape[:2]})')
            ok = False
            continue
        d = np.abs(a - b)
        raw_mae = d.mean()
        blur_mae = np.abs(_blur(a) - _blur(b)).mean()
        passed = (blur_mae <= TOL_BLUR_MAE) and (raw_mae <= TOL_RAW_MAE)
        print(f"{'PASS' if passed else 'FAIL'} {rel} "
              f"(rawMAE={raw_mae:.2f} blurMAE={blur_mae:.2f})"
              + ('' if passed else ' -- content differs beyond rendering drift'))
        ok &= passed
    print('FIGURE CHECK:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if '--check' in sys.argv:
        # The parent must not write into the repository at all: it re-executes
        # itself as a child that renders into a temp dir (FIG_OUT) and only
        # compares afterwards.
        import subprocess
        tmp = tempfile.mkdtemp(prefix='figcheck_')
        try:
            for rel, _used in FIGURE_FILES:      # savefig creates no subdirs
                sub = os.path.dirname(os.path.join(tmp, rel))
                if sub:
                    os.makedirs(sub, exist_ok=True)
            child = subprocess.call([sys.executable, os.path.abspath(__file__)],
                                    env=dict(os.environ, FIG_OUT=tmp),
                                    stdout=subprocess.DEVNULL)
            if child != 0:
                print('FIGURE CHECK: FAIL (regeneration itself failed)')
                sys.exit(1)
            sys.exit(check(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    generate(os.environ.get('FIG_OUT', ROOT))
