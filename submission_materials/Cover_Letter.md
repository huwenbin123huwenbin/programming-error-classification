# Cover Letter for ACM Transactions on Computing Education

**To:** Editor-in-Chief, ACM Transactions on Computing Education  
**From:** Wenbin Hu, School of Computer Science, Xijing University  
**Date:** July 25, 2026  
**Subject:** Manuscript Submission - Metadata-Based Programming Error Classification

---

Dear Editor,

We are pleased to submit our manuscript entitled **"Comparative Analysis of Machine Learning and Large Language Models for Programming Error Pattern Recognition in Competitive Programming"** for consideration in ACM Transactions on Computing Education.

## Novelty and Significance

This work presents the **first systematic comparison** of traditional ML classifiers and LLM-based methods for programming error classification using **only submission metadata** (no source code access). Our key contributions include:

1. **Novel ML-LLM comparison** under identical evaluation protocols on 2,672 test samples
2. **"Metadata ceiling" characterization**: We systematically quantify how much error-type information is genuinely recoverable from execution metadata alone, identifying CE/TLE/MLE as near-deterministically separable (F1 ≥ 0.89) while the WA↔RE boundary is not (RE F1 = 0.52)
3. **Controlled comparison**: Gradient Boosting achieves 95.02% accuracy; DeepSeek-V3 (zero-shot) achieves 76.65% ($p < 0.001$). We explicitly acknowledge the asymmetry: ML models are trained on 10,688 labeled samples while LLMs receive no task-specific training
4. **Cross-difficulty validation**: Model performance is robust across Easy (9.3% CE) to Hard (6.1% CE) problem difficulties

## Relevance to TOCE

This work directly addresses TOCE's focus on computing education tools and methods:

- **Immediate pedagogical impact**: Execution time and memory provide sufficient signal for three of five error types, enabling lightweight metadata-based error screening at platform scale
- **Evidence-based method-selection guidelines**: Quantifies the accuracy--cost--latency tradeoffs across deployment contexts, informing platform design decisions
- **Open dataset**: Enables reproducible research and benchmarking

## Key Findings

| Condition | Accuracy | Cost/Sample | Inference Time |
|-----------|----------|-------------|----------------|
| Gradient Boosting (trained, 7 features) | 95.02% | $0.0001 | 2ms |
| DeepSeek-V3 (zero-shot, 5 features) | 76.65% | $0.001 | 3s |
| Qwen2.5:3B (zero-shot, 5 features) | 31.92% | $0 | 5s (local) |

**Main finding**: The platform's resource-limit design creates distinctive metadata signatures for CE, TLE, and MLE, making these three verdicts near-deterministically separable. The WA↔RE boundary—where algorithmic revision versus boundary-condition checking applies—produces no distinctive execution signatures, defining the metadata ceiling and the boundary where source-code analysis becomes necessary.

## Caveats

We acknowledge three important limitations. First, our ML models are trained on 10,688 labeled samples while LLMs are evaluated zero-shot; whether LLMs can close this gap with few-shot prompting or fine-tuning warrants further investigation. Second, our dataset is from competitive programmers (Codeforces, rating 800–3,500); cross-population validation on CS1/CS2 student data is needed before drawing conclusions for novice programming education. Third, our findings characterize metadata information content on this platform; generalizability to other environments requires empirical validation.

## Submission Materials

- Manuscript (30 pages, 9 tables, 8 figures)
- Highlights (5 key contributions)
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
