#!/usr/bin/env python3
"""
数据预处理脚本 - 为SCI论文增强实验准备数据
从原始Codeforces数据生成特征工程后的数据集
"""

import pandas as pd
import json
from pathlib import Path

# 读取原始数据
data_path = Path(__file__).parent.parent / "01_原始数据" / "codeforces_submissions.csv"
output_path = Path(__file__).parent

print("📂 读取原始数据...")
df = pd.read_csv(data_path)

print(f"原始数据: {len(df)} 行")
print(f"列名: {df.columns.tolist()}")

# 过滤错误提交（非OK的）
df_errors = df[df['verdict'] != 'OK'].copy()
print(f"错误提交: {len(df_errors)} 行")

# 错误类型映射
error_mapping = {
    'WRONG_ANSWER': 'Wrong Answer',
    'TIME_LIMIT_EXCEEDED': 'Time Limit Exceeded',
    'RUNTIME_ERROR': 'Runtime Error',
    'COMPILATION_ERROR': 'Compilation Error',
    'MEMORY_LIMIT_EXCEEDED': 'Memory Limit Exceeded'
}
df_errors['error_type'] = df_errors['verdict'].map(error_mapping)

# 特征工程
print("🔧 进行特征工程...")

# 1. 编码编程语言
language_map = {'GNU++17': 0, 'GNU++14': 1, 'Kotlin': 2, 'PyPy3': 3, 'Python3': 4}
df_errors['language_encoded'] = df_errors['programming_language'].map(language_map).fillna(0).astype(int)

# 2. 提取问题类型 (A, B, C, D...)
def extract_problem_type(problem_index):
    if pd.isna(problem_index):
        return 0
    problem_index = str(problem_index).upper()
    if len(problem_index) > 0:
        return ord(problem_index[0]) - ord('A') + 1
    return 0

df_errors['problem_type'] = df_errors['problem_index'].apply(extract_problem_type)

# 3. 提取提交时间（小时）
if 'creation_time_seconds' in df_errors.columns:
    df_errors['hour'] = pd.to_datetime(df_errors['creation_time_seconds'], unit='s').dt.hour
elif 'time' in df_errors.columns:
    df_errors['hour'] = pd.to_datetime(df_errors['time'], unit='s').dt.hour

# 4. 计算用户历史成功率
user_stats = df.groupby('user_handle').apply(
    lambda x: (x['verdict'] == 'OK').mean()
).to_dict()
df_errors['user_success_rate'] = df_errors['user_handle'].map(user_stats).fillna(0.5)

# 5. 选择用于实验的特征
features = [
    'problem_rating',
    'language_encoded',
    'passed_test_count',
    'time_consumed_ms',
    'memory_consumed_bytes',
    'problem_type',
    'hour',
    'user_success_rate'
]

# 清理数据
df_clean = df_errors.dropna(subset=['problem_rating', 'time_consumed_ms']).copy()

# 转换内存为KB
if 'memory_consumed_bytes' in df_clean.columns:
    df_clean['memory_kb'] = df_clean['memory_consumed_bytes'] / 1024
    features.append('memory_kb')
else:
    df_clean['memory_kb'] = 0

# 选择最终特征列
final_features = ['problem_rating', 'language_encoded', 'passed_test_count', 
                   'time_consumed_ms', 'memory_kb', 'problem_type', 'hour', 'user_success_rate']

# 创建最终数据集
df_final = df_clean[final_features + ['error_type']].copy()
df_final = df_final.dropna()

# 标签编码
label_map = {label: idx for idx, label in enumerate(df_final['error_type'].unique())}
df_final['label'] = df_final['error_type'].map(label_map)

print(f"\n📊 最终数据集统计:")
print(f"- 样本数: {len(df_final)}")
print(f"- 特征数: {len(final_features)}")
print(f"- 类别数: {len(label_map)}")
print(f"- 类别分布:\n{df_final['error_type'].value_counts()}")

# 保存
output_csv = output_path / "preprocessed_data.csv"
output_json = output_path / "feature_config.json"

df_final.to_csv(output_csv, index=False)
print(f"\n✅ 保存预处理数据到: {output_csv}")

# 保存特征配置
config = {
    'features': final_features,
    'label_map': label_map,
    'n_samples': len(df_final),
    'n_features': len(final_features),
    'n_classes': len(label_map)
}
with open(output_json, 'w') as f:
    json.dump(config, f, indent=2)
print(f"✅ 保存特征配置到: {output_json}")

# 保存类别分布
dist = df_final['error_type'].value_counts().to_dict()
with open(output_path / "class_distribution.json", 'w') as f:
    json.dump(dist, f, indent=2)

print("\n🎉 预处理完成!")