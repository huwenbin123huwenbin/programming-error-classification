"""
生成论文补充图表 - 特征分布和混淆矩阵热图
作者: AI工程师
日期: 2026-06-08

功能:
1. 生成特征分布箱线图（不同错误类型的 problem_rating 分布）
2. 生成混淆矩阵热图（Random Forest 的混淆矩阵）
3. 生成执行时间分布图
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

# 设置中文字体（如果需要）
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 读取数据
# ============================================================
print("【步骤 1】读取数据...")
data = pd.read_csv('02_预处理数据/preprocessed_data.csv')

# 准备特征和目标变量
X = data[['problem_rating', 'language_encoded', 'passed_test_count', 'time_consumed_ms', 'memory_kb']]
y = data['error_type']

# 标准化数值特征
scaler = StandardScaler()
X_scaled = X.copy()
X_scaled[['problem_rating', 'passed_test_count', 'time_consumed_ms', 'memory_kb']] = scaler.fit_transform(
    X[['problem_rating', 'passed_test_count', 'time_consumed_ms', 'memory_kb']]
)

# 训练 RF 模型（用于生成混淆矩阵）
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

# ============================================================
# 2. 生成特征分布箱线图
# ============================================================
print("\n【步骤 2】生成特征分布箱线图...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Feature Distributions by Error Type', fontsize=16, fontweight='bold')

# 2.1 Problem Rating 分布
ax1 = axes[0, 0]
sns.boxplot(x='error_type', y='problem_rating', data=data, ax=ax1)
ax1.set_title('Problem Rating Distribution', fontweight='bold')
ax1.set_xlabel('Error Type')
ax1.set_ylabel('Problem Rating')
ax1.tick_params(axis='x', rotation=45)

# 2.2 Execution Time 分布（对数尺度）
ax2 = axes[0, 1]
data['time_consumed_ms_log'] = np.log1p(data['time_consumed_ms'])
sns.boxplot(x='error_type', y='time_consumed_ms_log', data=data, ax=ax2)
ax2.set_title('Execution Time Distribution (Log Scale)', fontweight='bold')
ax2.set_xlabel('Error Type')
ax2.set_ylabel('log(Execution Time + 1)')
ax2.tick_params(axis='x', rotation=45)

# 2.3 Memory Usage 分布
ax3 = axes[1, 0]
sns.boxplot(x='error_type', y='memory_kb', data=data, ax=ax3)
ax3.set_title('Memory Usage Distribution', fontweight='bold')
ax3.set_xlabel('Error Type')
ax3.set_ylabel('Memory (KB)')
ax3.tick_params(axis='x', rotation=45)

# 2.4 Passed Test Count 分布
ax4 = axes[1, 1]
sns.boxplot(x='error_type', y='passed_test_count', data=data, ax=ax4)
ax4.set_title('Passed Test Count Distribution', fontweight='bold')
ax4.set_xlabel('Error Type')
ax4.set_ylabel('Passed Test Count')
ax4.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('06_论文定稿/figures/feature_distributions_boxplot.png', dpi=300, bbox_inches='tight')
print("✅ 已保存: figures/feature_distributions_boxplot.png")
plt.close()

# ============================================================
# 3. 生成混淆矩阵热图
# ============================================================
print("\n【步骤 3】生成混淆矩阵热图...")

from sklearn.metrics import confusion_matrix

# 计算混淆矩阵
cm = confusion_matrix(y_test, y_pred, labels=rf.classes_)

# 绘制热图
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=rf.classes_, yticklabels=rf.classes_,
            cbar_kws={'label': 'Count'}, ax=ax)

ax.set_title('Random Forest Confusion Matrix (Test Set, n=207)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Predicted Label', fontweight='bold')
ax.set_ylabel('True Label', fontweight='bold')
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=0)

plt.tight_layout()
plt.savefig('06_论文定稿/figures/confusion_matrix_heatmap.png', dpi=300, bbox_inches='tight')
print("✅ 已保存: figures/confusion_matrix_heatmap.png")
plt.close()

# ============================================================
# 4. 生成特征重要性图（更美观的版本）
# ============================================================
print("\n【步骤 4】生成特征重要性图...")

feature_names = ['problem_rating', 'language', 'passed_test_count', 'time_consumed_ms', 'memory_kb']
feature_importance = rf.feature_importances_
sorted_idx = np.argsort(feature_importance)

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(range(len(sorted_idx)), feature_importance[sorted_idx], align='center')
ax.set_yticks(range(len(sorted_idx)))
ax.set_yticklabels([feature_names[i] for i in sorted_idx])
ax.set_xlabel('Gini Importance', fontweight='bold')
ax.set_title('Random Forest Feature Importance', fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('06_论文定稿/figures/feature_importance_updated.png', dpi=300, bbox_inches='tight')
print("✅ 已保存: figures/feature_importance_updated.png")
plt.close()

# ============================================================
# 5. 生成性能对比图（ML vs LLM）
# ============================================================
print("\n【步骤 5】生成性能对比图...")

models = ['RF', 'GB', 'LR', 'GPT-4\\nZero-Shot', 'GPT-4\\nFew-Shot', 'CodeBERT']
accuracies = [88.9, 88.4, 76.3, 87.0, 90.0, 86.1]
colors = ['#1f77b4', '#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e', '#ff7f0e']

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(models, accuracies, color=colors, edgecolor='black', linewidth=1.5)

# 添加数值标签
for bar, acc in zip(bars, accuracies):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{acc:.1f}%', ha='center', va='bottom', fontweight='bold')

ax.set_ylabel('Test Accuracy (%)', fontweight='bold', fontsize=12)
ax.set_xlabel('Model', fontweight='bold', fontsize=12)
ax.set_title('Performance Comparison: Traditional ML vs. LLM-Based Methods', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_ylim([70, 92])
ax.grid(axis='y', alpha=0.3)

# 添加图例
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#1f77b4', label='Traditional ML'),
                   Patch(facecolor='#ff7f0e', label='LLM-Based')]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.savefig('06_论文定稿/figures/ml_vs_llm_comparison.png', dpi=300, bbox_inches='tight')
print("✅ 已保存: figures/ml_vs_llm_comparison.png")
plt.close()

print("\n" + "="*60)
print("✅ 所有图表生成完成！")
print("="*60)
print("\n生成的图表:")
print("  1. feature_distributions_boxplot.png - 特征分布箱线图")
print("  2. confusion_matrix_heatmap.png - 混淆矩阵热图")
print("  3. feature_importance_updated.png - 特征重要性图（更新版）")
print("  4. ml_vs_llm_comparison.png - ML vs LLM 性能对比图")
print("\n请将图表插入到 paper_improved.tex 中对应的位置。")
