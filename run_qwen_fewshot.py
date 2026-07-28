#!/usr/bin/env python3
"""
Few-shot LLM evaluation using Qwen2.5:3B (local)
Tests whether few-shot prompting narrows the ML-LLM gap.
"""

import pandas as pd
import json
import requests
import time
from pathlib import Path

# Load data
df = pd.read_csv('/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv')
from sklearn.model_selection import train_test_split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['verdict'])

# Sample few-shot examples (3 per class)
few_shot_examples = {}
for verdict in ['WA', 'TLE', 'RE', 'CE', 'MLE']:
    samples = train_df[train_df['verdict'] == verdict].sample(n=3, random_state=42)
    few_shot_examples[verdict] = samples[['problem_rating', 'language', 'time_consumed_ms',
                                            'memory_kb', 'passed_test_count', 'verdict']].to_dict('records')

# Format few-shot examples for prompt
def format_examples():
    lines = []
    for verdict in ['WA', 'TLE', 'RE', 'CE', 'MLE']:
        for ex in few_shot_examples[verdict]:
            lines.append(
                f"Rating: {ex['problem_rating']:.0f}, Lang: {ex['language']}, "
                f"Time: {ex['time_consumed_ms']:.0f}ms, Mem: {ex['memory_kb']:.0f}kb, "
                f"Passed: {ex['passed_test_count']:.0f} → {verdict}"
            )
    return "\n".join(lines)

EXAMPLES = format_examples()

# Create prompt for single prediction
def create_prompt(row):
    return f"""You are a programming error classifier. Given metadata about a code submission, predict the error type.

Error Types:
- WA: Wrong Answer (logic error, incorrect output)
- TLE: Time Limit Exceeded (too slow)
- RE: Runtime Error (crash, segfault, division by zero)
- CE: Compilation Error (syntax error)
- MLE: Memory Limit Exceeded (uses too much memory)

Examples:
{EXAMPLES}

Now classify this submission:
Problem Rating: {row['problem_rating']:.0f}
Language: {row['language']}
Time Consumed: {row['time_consumed_ms']:.0f} ms
Memory Used: {row['memory_kb']:.0f} KB
Tests Passed: {row['passed_test_count']:.0f}

Output ONLY the error type (WA/TLE/RE/CE/MLE), nothing else."""

# Call Ollama API
def predict(prompt):
    data = {
        "model": "qwen2.5:3b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 10
        }
    }

    try:
        response = requests.post('http://localhost:11434/api/chat', json=data, timeout=60)
        result = response.json()
        content = result.get('message', {}).get('content', '').strip()
        # Extract verdict from response
        for v in ['WA', 'TLE', 'RE', 'CE', 'MLE']:
            if v in content:
                return v
        return "INVALID"
    except Exception as e:
        print(f"Error: {e}")
        return "ERROR"

# Run evaluation
if __name__ == "__main__":
    print("=== Qwen2.5:3B Few-shot Evaluation ===")
    print(f"Test samples: {len(test_df)}")

    # Test on full test set
    predictions = []
    correct = 0
    start_time = time.time()

    for idx, (_, row) in enumerate(test_df.iterrows()):
        prompt = create_prompt(row)
        pred = predict(prompt)
        actual = row['verdict']
        is_correct = pred == actual
        if is_correct:
            correct += 1

        predictions.append({
            'idx': idx,
            'actual': actual,
            'predicted': pred,
            'correct': is_correct
        })

        # Progress report every 100 samples
        if (idx + 1) % 100 == 0:
            elapsed = time.time() - start_time
            eta = elapsed / (idx + 1) * (len(test_df) - idx - 1)
            print(f"Progress: {idx+1}/{len(test_df)}, Accuracy: {correct}/{idx+1} = {correct/(idx+1)*100:.2f}%, ETA: {eta/60:.1f}min")

    # Final results
    elapsed = time.time() - start_time
    accuracy = correct / len(test_df) * 100
    print(f"\n=== Final Results ===")
    print(f"Few-shot accuracy: {correct}/{len(test_df)} = {accuracy:.2f}%")
    print(f"Time: {elapsed:.1f}s ({elapsed/len(test_df):.2f}s per sample)")
    print(f"Comparison:")
    print(f"  Zero-shot: 35.50%")
    print(f"  Few-shot: {accuracy:.2f}%")
    print(f"  Improvement: {accuracy - 35.50:.2f}pp")

    # Save results
    with open('fewshot_results.json', 'w') as f:
        json.dump({
            'accuracy': accuracy,
            'correct': correct,
            'total': len(test_df),
            'predictions': predictions
        }, f, indent=2)

    print(f"\nResults saved to fewshot_results.json")
