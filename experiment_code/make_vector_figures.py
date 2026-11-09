#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 3 张结果图的 PDF 矢量版（fig_accuracy_chart / fig_class_f1_chart /
fig_feature_importance_chart），数字与现有 PNG 完全一致（同源 JSON）。

仅重画这三张图，不重训模型、不碰其他图；原 PNG 保留供门禁校验。
绘图代码逐字取自 regenerate_figures_v3.py 的三个函数块，确保视觉一致。

用法：python3 make_vector_figures.py
"""
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'experiment_results', 'authoritative_results_v3.json')))
A = R['protocol_a']['models']

plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})


def main():
    # ---------------------------------------------------------- accuracy --
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
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT, 'fig_accuracy_chart.pdf'), bbox_inches='tight')
    plt.close()

    # ------------------------------------------------------- class-wise ---
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
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT, 'fig_class_f1_chart.pdf'), bbox_inches='tight')
    plt.close()

    # ------------------------------------------------- feature importance -
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
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT, 'fig_feature_importance_chart.pdf'), bbox_inches='tight')
    plt.close()

    print("OK: generated fig_accuracy_chart.pdf / fig_class_f1_chart.pdf / fig_feature_importance_chart.pdf")


if __name__ == '__main__':
    main()
