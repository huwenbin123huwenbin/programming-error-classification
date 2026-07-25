# Highlights for ACM TOCE Submission

## Research Highlights

1. **First systematic ML-LLM comparison** for programming error classification using metadata only (no source code access), evaluating three conditions: Gradient Boosting, DeepSeek-V3, and Qwen2.5:3B

2. **95.02% accuracy** achieved by 5-feature Gradient Boosting, significantly outperforming DeepSeek-V3 (76.65% valid accuracy, χ²=376.30, p<0.001) and Qwen2.5:3B (31.92% accuracy, χ²=1537.85, p<0.001)

3. **"Metadata ceiling" phenomenon**: Execution time alone achieves 91.99% accuracy, establishing a realistic upper bound for metadata-only approaches; LLMs cannot close this gap even with advanced prompting

4. **Execution time dominance** identified via ablation study—removing this feature causes the largest accuracy drop (p<0.001)

5. **WA↔RE boundary challenge**: WA and RE exhibit near-identical metadata distributions, suggesting platform design factors may be more determinant than model capability

6. **Open dataset and code** available at https://github.com/huwenbin123huwenbin/programming-error-classification

---

## Theoretical Contributions

- **Feedback Theory**: Grounded in Hattie & Timperley (2007) feedback model, identifying "feedback gaps" that metadata-only approaches can and cannot address
- **Self-Efficacy**: Connected to Bandura (1977) theory, explaining how immediate automated feedback enhances learner confidence
- **Cross-Difficulty Validation**: Model performance validated across problem difficulty levels (Easy 9.3% CE → Hard 6.1% CE)

---

## Practical Implications

### For Educators
- Metadata-based classification provides immediate diagnostic feedback without code review
- ML models offer interpretable predictions for targeted intervention
- Cost-effective solution for large-scale deployment in CS1/CS2 courses

### For Platform Developers
- No source code access required—addresses privacy concerns
- Fast inference (2ms vs. 3s for LLMs) enables real-time feedback
- Practical selection guidelines for choosing between ML and LLM approaches

### For Researchers
- First systematic comparison using identical evaluation protocols on 2,672 test samples
- Comprehensive statistical analysis with McNemar significance testing
- Open dataset for benchmarking future methods

---

## Technical Contributions

- **Method**: Novel metadata-only approach achieving 95.02% accuracy
- **Features**: Five interpretable metadata features (execution time, memory, success rate, problem rating, language)
- **Analysis**: Comprehensive ablation study identifying execution time as most critical predictor
- **Comparison**: Head-to-head ML vs. LLM evaluation with rigorous statistical validation
- **Insight**: "Metadata ceiling" phenomenon explains why even frontier LLMs underperform ML on this task
