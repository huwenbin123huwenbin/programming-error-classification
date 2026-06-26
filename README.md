# Programming Error Classification using ML vs. LLM

**Paper**: Comparative Analysis of Machine Learning and Large Language Models for Programming Error Pattern Recognition in Competitive Programming

**Author**: Wenbin Hu (Xijing University)

**Journal**: ACM Transactions on Computing Education (TOCE) - Under Review

---

## 📊 Overview

This repository contains the code and data for our systematic comparison of traditional ML classifiers and LLM-based methods for programming error classification using submission metadata only.

### Key Results

| Model | Test Accuracy | Macro F1 | Cost |
|-------|--------------|----------|------|
| **Gradient Boosting** | **95.02%** | **0.871** | $0.10 |
| Random Forest | 94.24% | 0.864 | $0.10 |
| Logistic Regression | 73.91% | 0.687 | $0.10 |
| DeepSeek 0-shot | 78.29% | 0.3467 | $1.00 |
| DeepSeek 5-shot | 17.37% | 0.1724 | $1.50 |
| Qwen2.5:3B (local) | 11.34% | - | Free |

**Dataset**: 13,360 Codeforces submissions (10,688 train / 2,672 test)

**Features**: 7 metadata features (time, memory, user_success_rate, problem_rating, language, problem_type, hour)

---

## 📂 Repository Structure

```
├── experiment_code/
│   ├── generate_figures.py          # Generate all figures
│   ├── preprocess_data.py           # Data preprocessing
│   └── run_experiments.py           # Main experiment runner
│
├── experiment_results/
│   └── experiment_results_v2.json   # Final results
│
├── llm_experiments/
│   ├── deepseek_zero-shot_full_*.json
│   ├── deepseek_few-shot_*.json
│   └── qwen25_3b_zeroshot_full_*.json
│
├── generalizability_results/
│   └── generalizability_results.json
│
├── paper.tex                        # LaTeX source (A4 format)
├── paper_acm_format.tex             # LaTeX source (ACM format)
├── paper.pdf                        # Compiled PDF (A4)
├── paper_acm_format.pdf             # Compiled PDF (ACM)
│
└── references.bib                   # Bibliography
```

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

### Run Experiments

```bash
cd experiment_code
python run_experiments.py
```

### Generate Figures

```bash
python generate_figures.py
```

---

## 📈 Features

### 7 Metadata Features

1. **time_consumed_ms**: Execution time (milliseconds)
2. **memory_consumed_bytes**: Memory usage (bytes)
3. **user_success_rate**: User's historical success rate
4. **problem_rating**: Problem difficulty rating
5. **language**: Programming language (encoded)
6. **problem_type**: Problem category (encoded)
7. **hour**: Submission hour (0-23)

### 5 Error Types

- Wrong Answer (WA): 76.6%
- Time Limit Exceeded (TLE): 9.6%
- Compilation Error (CE): 7.3%
- Runtime Error (RE): 4.9%
- Memory Limit Exceeded (MLE): 1.5%

---

## 🔬 Methodology

### Data Collection

- **Source**: Codeforces competitive programming platform
- **Period**: Multiple contests (2023-2024)
- **Filter**: Error submissions only (no Accepted)
- **Final dataset**: 13,360 samples

### Experimental Setup

- **Split**: 80/20 stratified train-test split
- **Validation**: 5-fold cross-validation
- **Metrics**: Accuracy, Macro F1, Confusion Matrix
- **Statistical test**: McNemar's test (α = 0.05)

### ML Models

- Random Forest (100 trees)
- Gradient Boosting (100 estimators)
- Logistic Regression (L2 regularization)

### LLM Models

- DeepSeek-V3 (0-shot and 5-shot prompting)
- Qwen2.5:3B (local, 0-shot)

---

## 📊 Key Findings

1. **ML dominates**: Gradient Boosting achieves 95.02% accuracy, significantly outperforming LLMs
2. **Time is key**: Execution time is the dominant predictor (42.5% feature importance)
3. **Cost advantage**: ML costs 10-15× less than LLMs
4. **Speed advantage**: ML inference 2ms vs. LLM 3s
5. **Ablation study**: Removing time causes 8.8pp accuracy drop (p < 0.001)

---

## 📝 Citation

```bibtex
@article{hu2026error,
  title={Comparative Analysis of Machine Learning and Large Language Models for Programming Error Pattern Recognition in Competitive Programming},
  author={Hu, Wenbin},
  journal={ACM Transactions on Computing Education},
  year={2026},
  note={Under Review}
}
```

---

## 📄 License

MIT License

---

## 📧 Contact

**Wenbin Hu**  
School of Computer Science, Xijing University  
Email: wenbin.hu2026@outlook.com

---

## 🙏 Acknowledgments

- Codeforces for providing the platform and data
- DeepSeek for API access
- Open-source community for ML libraries
