# Submission Checklist for ACM TOCE

**Last Updated: 2026-08-01**

## ✅ Manuscript
- [x] Title: "Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming"
- [x] LaTeX source: `paper_acm.tex` (30 pages, 0 errors, 0 undefined refs)
- [x] Compiled PDF: `paper_acm.pdf` (30 pages, 852KB)
- [x] GitHub repository: `huwenbin123huwenbin/programming-error-classification` (all commits pushed to `main`)
- [x] Abstract structured (Context/Objective/Method/Results/Conclusions, 260 words)
- [x] Keywords (5): programming verdict classification, machine learning, large language models, competitive programming, metadata-based classification
- [x] CCS categories: Social and professional topics ~ Computing education
- [x] IRB/ethics statement (IRB No. 2024-AI-003, Xijing University)
- [x] Data availability statement (GitHub URL in paper + Cover Letter)
- [x] Conflicts of interest statement (Xijing University Research Fund Grant No. XJ-2025-001)
- [x] Preregistration statement (not preregistered, limitations acknowledged)
- [x] Author: Wenbin Hu, School of Computer Science, Xijing University, wenbin.hu2026@outlook.com

## ✅ Supplementary Materials
- [x] Per-class F1 scores, Cohen's h effect sizes, balanced accuracy
- [x] Confusion matrices (RF, GB)
- [x] ROC/PR curves
- [x] Statistical test p-values (McNemar, Holm-Bonferroni corrected)
- [x] Feature ablation results
- [x] Gini importance
- [x] Leave-one-user-out CV (82.5% accuracy)
- [x] Cross-difficulty generalization (71–94%)
- [x] Student-proxy experiment (novice 96.0%, intermediate 95.2%, advanced 88.5%)
- [x] User-disjoint replication (GroupShuffleSplit, GB 92.2%, RF 90.9%)

## ✅ Submission Materials (this folder)
- [x] Cover_Letter.md / Cover_Letter.tex / Cover_Letter.pdf (updated Aug 1, 2026)
- [x] Highlights.md / Highlights.tex / Highlights.pdf (updated Aug 1, 2026)
- [x] SUBMISSION_CHECKLIST.md (this file)

## ✅ GitHub Repository Contents
- [x] Dataset: `codeforces_final_real.csv` (13,360 submissions)
- [x] Source code: `experiment_code/` (preprocessing, ML training, replication scripts)
- [x] LLM experiments: `llm_experiments/` (DeepSeek, Qwen scripts)
- [x] Results: `experiment_results/` (JSON, figures)
- [x] README.md, LICENSE (MIT)
- [x] User-disjoint replication: `user_disjoint_replication.py` + `user_disjoint_results.json`

## ✅ Suggested Reviewers (5)
1. **Dr. Brett A. Becker** — University College Dublin (CS1, programming education)
2. **Dr. Juho Leinonen** — Aalto University (automated assessment, ML in education)
3. **Dr. Paul Denny** — University of Auckland (programming tools, code assessment)
4. **Dr. Arto Hellas** — University of Helsinki (learning analytics, programming education)
5. **Dr. Stefanos Gkiokas** — ATHENA RC / UCL (CS education, automated feedback)

## ⏳ Pending (Author Action Required)
- [ ] Register at ScholarOne: https://mc.manuscriptcentral.com/acm/toce
- [ ] Upload paper_acm.pdf as main manuscript
- [ ] Upload Cover_Letter.pdf and Highlights.pdf
- [ ] Add suggested reviewers (5 names above)
- [ ] Confirm ORCID (optional)
- [ ] Verify CCS categories match TOCE scope

## 📋 Key Findings for Submission
| Approach | Accuracy | Cost/1K |
|----------|---------|---------|
| Gradient Boosting (7 feat.) | **95.02%** | $0.01 |
| Gradient Boosting (5 feat.) | 92.0% | $0.01 |
| DeepSeek-V3 zero-shot | 76.65% | $0.10 |
| Qwen2.5:3B zero-shot | 35.50% | $0.00 (local) |

**ML > LLM by 18.4 pp** (Holm-Bonferroni-corrected McNemar, p < 0.001)
**Platform-encoding boundary**: CE/TLE/MLE recoverable (F1≥0.89, 18.4% of submissions); WA↔RE not separable (RE F1=0.52)
