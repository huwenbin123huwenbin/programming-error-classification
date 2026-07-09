#!/usr/bin/env python3
"""
Few-shot LLM evaluation for metadata-based error classification.
Tests whether few-shot prompting narrows the ML-LLM gap.
"""

import pandas as pd
import json
import subprocess
import time
from pathlib import Path

# Load data
df = pd.read_csv('/Users/mac/Desktop/SCI1/01_原始数据/codeforces_final_real.csv')
from sklearn.model_selection import train_test_split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['verdict'])

# Load few-shot examples
with open('few_shot_examples.json') as f:
    few_shot_examples = json.load(f)

# Format few-shot examples for prompt
def format_examples():
    lines = []
    for verdict in ['WA', 'TLE', 'RE', 'CE', 'MLE']:
        for ex in few_shot_examples[verdict]:
            lines.append(
                f"Rating: {ex['problem_rating']}, Lang: {ex['language']}, "
                f"Time: {ex['time_consumed_ms']}ms, Mem: {ex['memory_kb']}kb, "
                f"Passed: {ex['passed_test_count']} → {verdict}"
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
Problem Rating: {row['problem_rating']}
Language: {row['language']}
Time Consumed: {row['time_consumed_ms']} ms
Memory Used: {row['memory_kb']} KB
Tests Passed: {row['passed_test_count']}

Output ONLY the error type (WA/TLE/RE/CE/MLE), nothing else."""

# Call DeepSeek API
def predict(prompt, api_key):
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 10
    })
    
    cmd = [
        'curl', '-s', '--max-time', '30',
        'https://api.deepseek.com/chat/completions',
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-d', data
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        response = json.loads(result.stdout)
        if 'choices' in response:
            return response['choices'][0]['message']['content'].strip()
        else:
            return "ERROR"
    except:
        return "ERROR"

# Run evaluation on subset
if __name__ == "__main__":
    # Test on first 100 samples for quick validation
    test_subset = test_df.head(100)
    
    api_key = "sk-cbb3dfb6ea5c4f7c90c8e7b5a6d2f1e3"  # Replace with actual key
    
    predictions = []
    for idx, row in test_subset.iterrows():
        prompt = create_prompt(row)
        pred = predict(prompt, api_key)
        predictions.append({
            'actual': row['verdict'],
            'predicted': pred
        })
        time.sleep(0.5)  # Rate limiting
    
    # Calculate accuracy
    correct = sum(1 for p in predictions if p['actual'] == p['predicted'])
    print(f"Few-shot accuracy: {correct}/{len(predictions)} = {correct/len(predictions)*100:.2f}%")
    
    # Save results
    with open('few_shot_results.json', 'w') as f:
        json.dump(predictions, f, indent=2)
