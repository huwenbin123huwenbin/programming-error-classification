# Submission Checklist for ACM TOCE

## ✅ Pre-Submission Checklist

### Manuscript
- [x] Title page with author information
- [x] Abstract (166 words, ≤200 required) ✓
- [x] Keywords (5 keywords)
- [x] Main text (19 pages, within limit)
- [x] References (66 citations, all verified)
- [x] Figures (11 figures, all included)
- [x] Tables (multiple tables, formatted)
- [x] LaTeX source file (paper.tex, paper_acm_format.tex)
- [x] Compiled PDF (paper.pdf, paper_acm_format.pdf)

### Formatting
- [x] ACM format (paper_acm_format.tex) ✓
- [x] Alternative format (paper.tex, A4)
- [x] Bibliography in ACM format (apalike)

### Supplementary Materials
- [x] README.md with repository structure
- [x] LICENSE (MIT)
- [x] Source code (experiment_code/)
- [x] Experimental results (experiment_results/)
- [x] LLM evaluation results (llm_experiments/)
- [x] Generalizability analysis (generalizability_results/)

### Data Availability
- [x] Dataset description in paper
- [x] GitHub repository prepared
- [ ] GitHub repository published (requires gh auth login)

### Author Information
- [x] Name: Wenbin Hu
- [x] Affiliation: Xijing University
- [x] Email: wenbin.hu2026@outlook.com
- [ ] ORCID: (optional)

---

## 📝 Cover Letter

### To: ACM Transactions on Computing Education

**Dear Editor,**

We are pleased to submit our manuscript entitled "**Comparative Analysis of Machine Learning and Large Language Models for Programming Error Pattern Recognition in Competitive Programming**" for consideration in ACM Transactions on Computing Education.

**Novelty and Significance:**

This work presents the **first systematic comparison** of traditional ML classifiers and LLM-based methods for programming error classification using **only submission metadata** (no source code access). Our key contributions include:

1. **Novel ML-LLM comparison** using identical evaluation protocols on a large dataset (13,360 samples)
2. **Execution time dominance finding** with ablation validation (8.8pp accuracy drop, p<0.001)
3. **Cost-effectiveness analysis**: ML achieves superior accuracy at 10-15× lower cost
4. **Actionable guidelines** for educators and platform developers

**Relevance to TOCE:**

This research directly addresses the "CS1 problem" by providing educators with practical tools for automated error diagnosis. Our metadata-only approach enables deployment at platform scale without privacy concerns associated with source code access.

**Key Findings:**

- Gradient Boosting achieves 95.02% accuracy, significantly outperforming DeepSeek (78.29% 0-shot, 17.37% 5-shot)
- Execution time is the dominant predictor (42.5% feature importance)
- ML offers 10-15× cost advantage with faster inference (2ms vs. 3s)

**Data and Code Availability:**

All data, code, and experimental results will be made publicly available on GitHub upon acceptance.

**Previous Presentation:**

This manuscript has not been published previously and is not under consideration elsewhere.

We believe this work makes significant contributions to computing education research and would be suitable for publication in TOCE.

Sincerely,

Wenbin Hu
School of Computer Science
Xijing University
wenbin.hu2026@outlook.com

---

## 🎯 Highlights

1. **First ML-LLM comparison** for error classification using metadata only
2. **95.02% accuracy** achieved by Gradient Boosting (10-15× lower cost than LLMs)
3. **Execution time dominance** identified via ablation study (8.8pp drop, p<0.001)
4. **Platform-scale deployment** enabled without source code access
5. **Practical guidelines** for ML vs. LLM selection across educational contexts
6. **Open dataset and code** for reproducibility

---

## 📧 Author Contact Information

**Corresponding Author:**
- Name: Wenbin Hu
- Email: wenbin.hu2026@outlook.com
- Affiliation: School of Computer Science, Xijing University
- Address: Xi'an, China

---

## 📋 Suggested Reviewers

1. **Dr. Brett A. Becker**
   - University College Dublin
   - Expertise: Programming education, CS1
   - Email: (to be searched)

2. **Dr. Juho Leinonen**
   - Aalto University
   - Expertise: Automated assessment, ML in education
   - Email: (to be searched)

3. **Dr. Paul Denny**
   - University of Auckland
   - Expertise: Programming tools, code assessment
   - Email: (to be searched)

---

## 📄 Data Availability Statement

The dataset and code supporting this study will be made publicly available in a GitHub repository upon acceptance. The repository includes:
- Curated dataset (13,360 samples)
- Python scripts for data preprocessing and model training
- All experimental results (JSON format)
- Figure generation scripts

During the review process, data and code are available upon request from the corresponding author.

---

## ⚖️ Ethics Statement

This research uses publicly available data from Codeforces competitive programming platform. No human subjects were involved. The data consists of submission metadata without personal identification information.

---

## 💰 Funding Statement

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

---

## 🔗 Conflicts of Interest

The author declares no conflicts of interest.

---

**Last Updated: 2026-06-26**
