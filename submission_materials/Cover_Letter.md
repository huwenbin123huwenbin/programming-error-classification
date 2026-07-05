# Cover Letter for ACM TOCE Submission

**To:** ACM Transactions on Computing Education  
**From:** Wenbin Hu, Xijing University  
**Date:** 2026-06-26  
**Subject:** Manuscript Submission - ML vs. LLM for Programming Error Classification

---

Dear Editor,

We are pleased to submit our manuscript entitled "**Comparative Analysis of Machine Learning and Large Language Models for Programming Error Pattern Recognition in Competitive Programming**" for consideration in ACM Transactions on Computing Education.

## Novelty and Significance

This work presents the **first systematic comparison** of traditional ML classifiers and LLM-based methods for programming error classification using **only submission metadata** (no source code access). Our key contributions include:

1. **Novel ML-LLM comparison** using identical evaluation protocols on a large dataset (13,360 samples)
2. **Execution time dominance finding** with ablation validation (8.8pp accuracy drop, p<0.001)
3. **Cost-effectiveness analysis**: ML achieves superior accuracy at 10-15× lower cost
4. **Actionable guidelines** for educators and platform developers

## Relevance to TOCE

This research directly addresses the "CS1 problem" by providing educators with practical tools for automated error diagnosis. Our metadata-only approach enables deployment at platform scale without privacy concerns associated with source code access.

## Key Findings

- Gradient Boosting achieves **95.02% accuracy**, significantly outperforming DeepSeek (78.29% 0-shot, 17.37% 5-shot)
- Execution time is the dominant predictor (42.5% feature importance)
- ML offers **10-15× cost advantage** with faster inference (2ms vs. 3s)

## Data and Code Availability

All data, code, and experimental results are publicly available at: https://github.com/huwenbin123huwenbin/programming-error-classification

The repository includes the full dataset (13,360 samples), all experimental code, and complete results for reproducibility.

## Previous Presentation

This manuscript has not been published previously and is not under consideration elsewhere.

We believe this work makes significant contributions to computing education research and would be suitable for publication in TOCE.

Sincerely,

**Wenbin Hu**  
School of Computer Science  
Xijing University  
Email: wenbin.hu2026@outlook.com
