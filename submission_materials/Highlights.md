# Highlights

## Research Highlights

1. **First controlled ML–LLM comparison** for programming verdict classification using only submission metadata (no source code required), evaluated under identical zero-shot protocols across Random Forest, Gradient Boosting, Logistic Regression, DeepSeek-V3, and Qwen2.5:3B.

2. **Platform-encoding boundary**: Compile-time errors (CE), time limit exceeded (TLE), and memory limit exceeded (MLE) are deterministically recoverable from execution metadata (F1 ≥ 0.89) because platform measurement thresholds define these outcomes. These three verdict types account for 18.4% of submissions. The WA↔RE boundary is not metadata-separable (RE F1 = 0.52), indicating where source-code analysis may be required.

3. **Supervised ML outperforms frontier LLMs**: Gradient Boosting (95.02%) exceeds DeepSeek-V3 zero-shot (76.65%) by 18.4 pp, and Qwen2.5:3B (35.50%) by 59.5 pp. Even with identical features, GB (92.0%) surpasses DeepSeek-V3 by 15.4 pp. Execution time is the dominant predictor (8.8 pp accuracy drop when removed).

4. **Statistical and empirical rigor**: Holm-Bonferroni-corrected McNemar tests, feature ablation, Gini importance, leave-one-user-out cross-validation (82.5% accuracy), and cross-difficulty generalization (71–94% across problem difficulties).

5. **Open dataset, code, and deployment guidelines**: 13,360 Codeforces submissions with full metadata; deployment guidelines balancing accuracy, cost ($0.01/1K), latency (2 ms), and explainability across six educational contexts. Available at: https://github.com/huwenbin123huwenbin/programming-error-classification
