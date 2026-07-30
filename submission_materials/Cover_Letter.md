# Cover Letter

**To:** Editor-in-Chief, ACM Transactions on Computing Education  
**From:** Wenbin Hu, School of Computer Science, Xijing University  
**Date:** July 30, 2026  
**Subject:** Manuscript Submission — "Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming"

---

Dear Editor,

We are pleased to submit our manuscript, **"Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming,"** for consideration in ACM Transactions on Computing Education.

## Why This Paper Fits TOCE

Automated feedback is central to computing education, yet most existing tools require source code access. We address a deceptively simple question: **what verdict information can be recovered from metadata alone?** Our answer reveals a platform-encoding boundary—a natural limit that neither ML nor LLMs can overcome without source code.

The paper is directly relevant to TOCE readers: it provides educators with cost-effective verdict-screening tools (2 ms inference, $0.01 per 1,000 classifications), characterizes where metadata-based automated feedback is and is not feasible, and contributes an empirical framework for comparing supervised ML and zero-shot LLM approaches.

## Novelty and Contributions

1. **First controlled ML–LLM comparison** for programming verdict classification from metadata alone, with identical protocols across three ML models (Random Forest, Gradient Boosting, Logistic Regression) and two LLM configurations (DeepSeek-V3, Qwen2.5:3B).

2. **The platform-encoding boundary**: Compile-time errors (CE), time limit exceeded (TLE), and memory limit exceeded (MLE)—together 18.4% of submissions—are deterministically recoverable from execution metadata (F1 ≥ 0.89) because platform measurement thresholds define these outcomes. The WA↔RE boundary is not metadata-separable (RE F1 = 0.52), delineating where source-code analysis may be required.

3. **Statistical and deployment rigor**: Holm-Bonferroni-corrected McNemar tests, ablation analysis, Gini importance, leave-one-user-out cross-validation (82.5% accuracy), cross-difficulty generalization (71–94% across problem difficulties), and method-selection guidelines balancing accuracy, cost, and latency across six deployment contexts.

4. **Data and code publicly released**: https://github.com/huwenbin123huwenbin/programming-error-classification

## Key Findings

| Approach | Accuracy | Valid Predictions | Cost / 1K |
|----------|---------|-------------------|-----------|
| Gradient Boosting (7 feat.) | **95.02%** | 100% | $0.01 |
| Gradient Boosting (5 feat.) | 92.0% | 100% | $0.01 |
| DeepSeek-V3 zero-shot | 76.65% | 99.2% | $0.10 |
| Qwen2.5:3B zero-shot | 35.50% | 89.9% | $0.00 (local) |

Supervised ML (95.02%) outperforms DeepSeek-V3 zero-shot (76.65%) by 18.4 pp. Even with equal features, Gradient Boosting (92.0%) surpasses DeepSeek-V3 by 15.4 pp. We note that this comparison is asymmetric: ML models were trained on 10,688 labeled samples while LLMs received no task-specific training.

## Relevance to TOCE Scope

This work speaks to TOCE's interest in:
- **Automated assessment tools**: Lightweight metadata-based verdict screening is computationally tractable for resource-constrained educational settings.
- **Feedback automation**: Characterizes which verdicts benefit from immediate automated feedback (CE, TLE, MLE) and which require human expert review (WA, RE).
- **Empirical computing education research**: Controlled comparison of ML and LLM methods with transparent statistical analysis.

## Submission Materials

- Manuscript: 28 pages, 9 tables, 8 figures
- Highlights: 5 key contributions
- Supplementary Materials: per-class F1 scores, Cohen's h effect sizes, balanced accuracy, confusion matrices, statistical test p-values, ROC/PR curves

We confirm this manuscript is original, has not been published elsewhere, and is not under review at any other venue. All authors have approved the submitted version.

Thank you for considering our submission.

Best regards,

**Wenbin Hu**  
School of Computer Science, Xijing University  
Email: wenbin.hu2026@outlook.com  
