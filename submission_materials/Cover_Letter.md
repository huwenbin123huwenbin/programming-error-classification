# Cover Letter

**To:** Editor-in-Chief, ACM Transactions on Computing Education
**From:** Wenbin Hu, School of Computer Science, Xijing University
**Date:** October 17, 2026
**Subject:** Manuscript Submission — "Where the Metadata Ends: Observational Equivalence and the Limits of Verdict Classification from Submission Logs"

---

Dear Editor,

We are pleased to submit our manuscript, **"Where the Metadata Ends: Observational Equivalence and the Limits of Verdict Classification from Submission Logs,"** for consideration in ACM Transactions on Computing Education.

## The question, and why the answer is not another accuracy figure

Automated feedback is central to computing education, yet most tools require source-code access that institutions rarely have at scale. We ask what verdict information a submission log actually carries. The answer turns out not to be a number but a decomposition.

Submissions whose metadata vectors coincide while their verdicts differ are **observationally equivalent**: no classifier can separate them, because every recorded measurement agrees. In our corpus of 13,360 submissions, one signature — 0 ms, 0 KB, 0 tests passed — holds 1,504 submissions (11.3%) spanning three verdicts, since a failed compilation, a crash on the first test and a wrong answer on the first test leave identical traces. That single cell bounds Compilation Error at F1 ≈ 0.77, and our best model sits on that bound (0.770). A second cell (31 ms, 0 KB, 1 test) holds 13.0% and bounds the Wrong Answer ↔ Runtime Error distinction.

This reframes the practical question from *which classifier is better* to *what else would have to be recorded for the cell to split* — an answer the platform holds but does not publish.

## Contributions

1. **An identifiability account of the boundary.** The ceiling on metadata-based verdict classification is set by observational equivalence, not by model capacity. The argument is model-free: it holds for any classifier given these inputs, and it explains why the residual errors are irreducible rather than merely unfixed.

2. **A systematic comparison under a shared protocol.** Three supervised models and two LLM configurations on one test partition and a common feature vocabulary, with five-fold cross-validation, per-field ablation, ten Bonferroni-corrected McNemar tests, and a submitter-disjoint replication. We are explicit that supervised ML beating a prompted LLM is a replication of known behaviour (Liu et al., NAACL 2024), not a discovery; what we analyse is the structure of the gap.

3. **Deployment guidance with a leakage-free protocol.** Execution time carries 81.5% of Gini importance and costs 7.3 percentage points when removed; a submitter-history aggregate — the standard first feature in this literature — *loses* 2.1 points once computed without look-ahead, and is excluded. The final model uses six fields, all available at first contact with a submission, so it carries no cold-start penalty.

4. **Dataset, pipeline and figures released**, with a single script that regenerates every number in the paper: https://github.com/huwenbin123huwenbin/programming-error-classification

## Key findings

| Approach | Test accuracy | 95% CI | Macro F1 | Cost / 1K |
|---|---|---|---|---|
| Random Forest (6 fields) | 91.80% | [90.7, 92.8] | 0.798 | $0.0002 |
| Gradient Boosting (6 fields) | 91.77% | [90.7, 92.8] | 0.799 | $0.0002 |
| Gradient Boosting (5 fields, LLM-comparable) | 91.69% | [90.6, 92.7] | 0.797 | $0.0002 |
| Logistic Regression | 85.63% | [84.2, 86.9] | 0.494 | $0.0002 |
| DeepSeek-V3 (three-shot), valid outputs | 76.65% | [75.0, 78.2] | 0.545 | $0.01 |
| Qwen2.5:3B (three-shot), valid outputs | 35.50% | [33.6, 37.4] | 0.231 | $0.00 |

The majority-class rule scores 76.61%, so DeepSeek-V3's headline accuracy is indistinguishable from always answering Wrong Answer — yet its balanced accuracy (0.708) and its recall of every compilation error show that it has in fact learned the platform encoding, and pays the full price of the equivalence cell because a prompted model has no calibrated prior to trade recall against precision. The two tree ensembles are statistically indistinguishable from each other (χ² = 0.00, p = 1.00); we report this as a null result rather than ranking them. Under submitter-disjoint evaluation the ordering and the boundary are preserved (GB 93.13%, RF 91.99%, LR 87.15%).

## Relevance to TOCE's scope

- **Automated assessment**: identifies which verdicts can be reported at microsecond cost with no privacy exposure, and which cannot be reported at all from logs.
- **Feedback design**: argues for calibrated abstention at the WA↔RE boundary rather than a forced label, since the two root causes require different pedagogical responses.
- **Empirical computing education research**: a model-free identifiability argument, explicit leakage diagnostics, and a replication under a submitter-disjoint split.

## Submission materials

- Manuscript: 32 pages, 10 tables, 6 figures
- Highlights: 5 items
- Supplementary: per-class precision/recall/F1 for every model, balanced accuracy, confusion matrices, all pairwise tests with p-values, learning curves, and the full prompt template

We confirm this manuscript is original, has not been published elsewhere, and is not under review at any other venue. All authors have approved the submitted version. The research uses only publicly available data; the institutional review determined it exempt (reference 2024-AI-003), and no approval number is claimed because an exemption determination does not issue one.

Thank you for considering our submission.

Best regards,

**Wenbin Hu**
School of Computer Science, Xijing University
Email: wenbin.hu2026@outlook.com
