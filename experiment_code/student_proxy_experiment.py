import pandas as pd
import numpy as np
import json
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Load dataset
df = pd.read_csv('/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv')
print(f"Total rows: {len(df)}")

# Load user ratings
with open('/Users/mac/Desktop/SCI1/06_论文定稿/user_ratings.json') as f:
    user_ratings = json.load(f)

df['user_rating'] = df['user_handle'].map(user_ratings)

# Feature engineering (same as run_experiment_v2.py)
if 'memory_kb' not in df.columns:
    if 'memory_consumed_bytes' in df.columns:
        df['memory_kb'] = df['memory_consumed_bytes'] / 1024.0
    else:
        df['memory_kb'] = 0

df['memory_kb'] = df['memory_kb'].fillna(0)
df['problem_rating'] = pd.to_numeric(df['problem_rating'], errors='coerce')
df['time_consumed_ms'] = pd.to_numeric(df['time_consumed_ms'], errors='coerce')

# Language encoding
language_map = {str(lang): i for i, lang in enumerate(df['language'].dropna().unique())}
df['language_encoded'] = df['language'].astype(str).map(language_map).fillna(0).astype(int)

# Problem type from problem_index
def extract_problem_type(idx):
    if pd.isna(idx): return 0
    idx = str(idx).upper()
    return ord(idx[0]) - ord('A') + 1 if idx else 0

df['problem_type'] = df['problem_index'].apply(extract_problem_type)

# Hour (fallback to 12 as no submission_time available)
df['hour'] = 12

# User success rate (proportion of WA per user, as in original script)
if 'user_handle' in df.columns:
    user_stats = df.groupby('user_handle')['verdict'].apply(
        lambda x: (x == 'WA').sum() / len(x) if len(x) > 0 else 0.5
    ).to_dict()
    df['user_success_rate'] = df['user_handle'].map(user_stats).fillna(0.5)
else:
    df['user_success_rate'] = 0.5

# Clean
df_clean = df.dropna(subset=['problem_rating', 'time_consumed_ms']).copy()
print(f"Clean rows: {len(df_clean)}")

# Features
ALL_FEATURES = ['problem_rating', 'time_consumed_ms', 'memory_kb', 'language_encoded', 'problem_type', 'hour', 'user_success_rate']
X = df_clean[ALL_FEATURES].values
y = df_clean['verdict'].values
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Skill groups
def skill_group(rating):
    if pd.isna(rating): return 'unknown'
    if rating < 1400: return 'novice'
    if rating < 2000: return 'intermediate'
    return 'advanced'

df_clean['skill_group'] = df_clean['user_rating'].apply(skill_group)

# 80/20 split (same as paper)
X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
    X, y_encoded, np.arange(len(X)), test_size=0.2, random_state=42, stratify=y_encoded
)

# Train GB (same as paper)
gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
gb.fit(X_train, y_train)

# Predictions
y_pred = gb.predict(X_test)
overall_acc = accuracy_score(y_test, y_pred)

print(f"\nOverall test accuracy: {overall_acc:.4f}")
print(f"Classes: {list(le.classes_)}")

# Per-skill-group evaluation on test set
test_df = df_clean.iloc[idx_test].copy()
test_df['pred'] = le.inverse_transform(y_pred)
test_df['true'] = le.inverse_transform(y_test)

results = {}
print("\n=== Per-skill-group performance ===")
for group in ['novice', 'intermediate', 'advanced']:
    subset = test_df[test_df['skill_group'] == group]
    if len(subset) == 0:
        continue
    acc = accuracy_score(subset['true'], subset['pred'])
    macro_f1 = f1_score(subset['true'], subset['pred'], average='macro', zero_division=0)
    
    results[group] = {
        'n_samples': len(subset),
        'accuracy': float(acc),
        'macro_f1': float(macro_f1),
        'class_distribution': subset['true'].value_counts().to_dict(),
        'class_f1': {}
    }
    
    for cls in le.classes_:
        f1 = f1_score(subset['true'], subset['pred'], labels=[cls], average=None, zero_division=0)[0]
        results[group]['class_f1'][cls] = float(f1)
    
    print(f"\n{group.upper()} (n={len(subset)}):")
    print(f"  Accuracy: {acc:.4f}")
    print(f"  Macro F1: {macro_f1:.4f}")
    print(f"  Class distribution: {dict(subset['true'].value_counts())}")
    print(f"  Class F1: {results[group]['class_f1']}")

# Compare with/without user_rating filtering
# Also compute per-user accuracy distribution
print("\n=== Per-group detailed statistics ===")
for group in ['novice', 'intermediate', 'advanced']:
    subset = test_df[test_df['skill_group'] == group]
    if len(subset) == 0:
        continue
    
    # Per-user accuracy (for those with multiple submissions in test set)
    per_user = subset.groupby('user_handle').apply(
        lambda x: (x['true'] == x['pred']).mean()
    )
    print(f"{group}: per-user acc mean={per_user.mean():.4f}, std={per_user.std():.4f}, median={per_user.median():.4f}")

# Save results
with open('/Users/mac/Desktop/SCI1/06_论文定稿/student_proxy_experiment.json', 'w') as f:
    json.dump({
        'overall_accuracy': float(overall_acc),
        'groups': results,
        'rating_thresholds': {'novice': '<1400', 'intermediate': '1400-1999', 'advanced': '>=2000'},
        'n_users_total': int(df_clean['user_handle'].nunique()),
        'n_users_with_rating': int(df_clean['user_rating'].notna().sum())
    }, f, indent=2)

print(f"\nResults saved to student_proxy_experiment.json")
