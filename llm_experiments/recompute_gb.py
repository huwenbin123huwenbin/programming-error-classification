#!/usr/bin/env python3
"""Recompute Gradient Boosting on the identical test split used by the LLM runs,
so we can compute exact paired McNemar tests. Uses the same 5 metadata features
as the LLM prompt (paper claims identical features)."""
import json, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

ROOT = "/Users/mac/Desktop/SCI1"
DATA = f"{ROOT}/01_原始数据/codeforces_final_real.csv"
OUT  = "/Users/mac/Desktop/SCI1/06_论文定稿/llm_experiments"
CLASSES = ["WA", "TLE", "RE", "CE", "MLE"]

LANG_FAMILY = {
    "c++": "C++", "c++14": "C++", "c++17": "C++", "c++20": "C++",
    "c++23": "C++", "gnu c++": "C++", "gnu c++0x": "C++", "gnu c++11": "C++",
    "ms c++": "C++", "pypy": "PyPy", "python": "Python",
    "java": "Java", "java 21": "Java", "java 6": "Java", "java 7": "Java", "java 8": "Java",
    "javascript": "JS", "node.js": "JS",
    "c": "C", "c11": "C", "gnu c11": "C",
    "c#": "C#", "mono c#": "C#",
    "go": "Go", "rust": "Rust", "kotlin": "Kotlin", "haskell": "Haskell",
    "f#": "F#", "ruby": "Ruby", "scala": "Scala", "php": "PHP",
}
def lang_family(s):
    key = s.strip().lower().split()[0].rstrip("0123456789-")
    return LANG_FAMILY.get(key, s.strip()[:10])

df = pd.read_csv(DATA)
df = df.dropna(subset=["problem_rating", "verdict", "language",
                        "time_consumed_ms", "memory_kb", "passed_test_count", "problem_index"])
df["language"] = df["language"].apply(lang_family)
df = df[df["verdict"].isin(CLASSES)].copy()
df["verdict"] = df["verdict"].str.strip().str.upper()

# One-hot encode language (categorical)
df_enc = pd.get_dummies(df, columns=["language"], prefix="lang")
numeric_feats = ["problem_rating", "time_consumed_ms", "memory_kb", "passed_test_count"]
lang_feats = [c for c in df_enc.columns if c.startswith("lang_")]
features = numeric_feats + lang_feats
X = df_enc[features]; y = df_enc["verdict"]
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
test = X_te.copy().reset_index(drop=True)
test["true_label"] = y_te.values

gb = GradientBoostingClassifier(random_state=42)
gb.fit(X_tr, y_tr)
preds = gb.predict(X_te)
acc = accuracy_score(y_te, preds)
print(f"GB accuracy (5 features): {acc*100:.2f}%  (paper states 95.02% with 7 feat)")

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_tr, y_tr); rf_preds = rf.predict(X_te)
lr = LogisticRegression(max_iter=2000, random_state=42)
lr.fit(X_tr, y_tr); lr_preds = lr.predict(X_te)
print(f"RF accuracy (5 features): {accuracy_score(y_te, rf_preds)*100:.2f}%  (paper 94.24%)")
print(f"LR accuracy (5 features): {accuracy_score(y_te, lr_preds)*100:.2f}%  (paper 73.91%)")

out = {
  "GB": {int(i): {"true_label": str(test.iloc[i]["true_label"]), "prediction": str(preds[i])} for i in range(len(test))},
  "RF": {int(i): {"true_label": str(test.iloc[i]["true_label"]), "prediction": str(rf_preds[i])} for i in range(len(test))},
  "LR": {int(i): {"true_label": str(test.iloc[i]["true_label"]), "prediction": str(lr_preds[i])} for i in range(len(test))},
}
json.dump(out, open(f"{OUT}/ml_predictions_test_5feat.json", "w"))
print(f"Saved ML predictions (5-feat) -> ml_predictions_test_5feat.json")
