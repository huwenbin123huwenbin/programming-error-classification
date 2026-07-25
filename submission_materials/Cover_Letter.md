# Cover Letter for ACM Transactions on Computing Education

**To:** Editor-in-Chief, ACM Transactions on Computing Education  
**From:** Wenbin Hu, School of Computer Science, Xijing University  
**Date:** July 10, 2026  
**Subject:** Manuscript Submission - Metadata-Based Programming Error Classification

---

Dear Editor,

We are pleased to submit our manuscript entitled **"Metadata Ceiling: Why Machine Learning Outperforms Large Language Models in Programming Error Classification"** for consideration in ACM Transactions on Computing Education.

## Novelty and Significance

This work presents the **first systematic comparison** of traditional ML classifiers and LLM-based methods for programming error classification using **only submission metadata** (no source code access). Our key contributions include:

1. **Novel ML-LLM comparison** using identical evaluation protocols on 2,672 test samples
2. **"Metadata ceiling" phenomenon**: Execution time alone achieves 91.99% accuracy, establishing a realistic upper bound; LLMs cannot close this gap
3. **95.02% accuracy** with 5-feature Gradient Boosting, significantly outperforming DeepSeek-V3 (76.65%, p<0.001) and Qwen2.5:3B (31.92%, p<0.001)
4. **Theoretical grounding**: Hattie & Timperley feedback model + Bandura self-efficacy theory
5. **Cross-difficulty validation**: Model robust across Easy (9.3% CE) to Hard (6.1% CE) problems

## Relevance to TOCE

This work directly addresses TOCE's focus on computing education tools and methods:

- **Immediate pedagogical impact**: Provides educators with cost-effective automated feedback (2ms inference, 10-15× cheaper than LLM APIs)
- **Evidence-based guidelines**: Clear decision framework for choosing between ML and LLM approaches
- **Open dataset**: Enables reproducible research and benchmarking

## Key Findings

| Condition | Accuracy | Cost/Sample | Inference Time |
|-----------|----------|-------------|----------------|
| Gradient Boosting | 95.02% | $0.0001 | 2ms |
| DeepSeek-V3 | 76.65% | $0.001 | 3s |
| Qwen2.5:3B | 31.92% | $0 | 5s (local) |

**Main insight**: ML models outperform LLMs on this task because execution time and memory consumption encode sufficient signal for error type discrimination. LLMs struggle with fine-grained WA↔RE boundary despite strong general coding capabilities.

## Submission Materials

- Manuscript (30 pages, 9 tables, 8 figures)
- Highlights (6 key contributions)
- Open dataset and code: https://github.com/huwenbin123huwenbin/programming-error-classification

We confirm this manuscript is original, unpublished, and not under review elsewhere.

Thank you for considering our submission.

Best regards,

**Wenbin Hu**  
Lecturer, School of Computer Science  
Xijing University  
Email: wenbin.hu2026@outlook.com

---

## Suggested Reviewers

1. **Prof. Salehu Abubeker** - University of Illinois, salehu@illinois.edu  
   *Expertise: ML for education, automated assessment*

2. **Dr. Juho Leinonen** - University of Helsinki, juho.leinonen@helsinki.fi  
   *Expertise: Programming education, error analysis*

3. **Prof. Hieke Loomans** - Open University Netherlands, h.loomans@ou.nl  
   *Expertise: CS1/CS2 pedagogy, formative feedback*

4. **Dr. Andrew Petersen** - University of Toronto, andrew.petersen@utoronto.ca  
   *Expertise: Automated grading, educational data mining*

5. **Prof. Matti Tedre** - University of Eastern Finland, matti.tedre@uef.fi  
   *Expertise: Programming education, computational thinking*
