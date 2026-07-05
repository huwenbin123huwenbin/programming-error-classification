# Highlights for ACM TOCE Submission

## Research Highlights

1. **First ML-LLM comparison** for programming error classification using metadata only (no source code access)

2. **95.02% accuracy** achieved by Gradient Boosting, significantly outperforming DeepSeek (78.29% 0-shot, 17.37% 5-shot)

3. **Execution time dominance** identified via ablation study—removing this feature causes 8.8pp accuracy drop (p<0.001)

4. **10-15× cost advantage** for ML over LLMs, enabling platform-scale deployment without source code access

5. **Practical selection guidelines** for educators and developers choosing between ML and LLM approaches

6. **Open dataset and code** available at github.com/huwenbin123huwenbin/programming-error-classification

---

## Practical Implications

### For Educators
- Metadata-based classification provides immediate diagnostic feedback without code review
- ML models offer interpretable predictions for targeted intervention
- Cost-effective solution for large-scale deployment in programming courses

### For Platform Developers
- No source code access required—addresses privacy concerns
- Fast inference (2ms vs. 3s for LLMs) enables real-time feedback
- 10-15× cost reduction compared to commercial LLM APIs

### For Researchers
- First systematic comparison using identical evaluation protocols
- Comprehensive statistical analysis with significance testing
- Open dataset for benchmarking future methods

---

## Technical Contributions

- **Method**: Novel metadata-only approach for error classification
- **Analysis**: Comprehensive ablation study identifying dominant features
- **Comparison**: First head-to-head ML vs. LLM evaluation on programming errors
- **Insight**: Execution time emerges as the most critical predictor
- **Tool**: Open-source framework for automated error diagnosis
