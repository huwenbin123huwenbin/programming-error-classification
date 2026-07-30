# Simulated TOCE Peer Review
## Paper: "Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming"
### Reviewer Simulation (4 Reviewers, 2026-07-30)

---

## REVIEWER A — ML/Statistics Expert (Brett A. Becker profile)

**Expertise**: Machine learning methodology, statistical testing in educational data mining, CS1 programming education.

### Summary Recommendation: **Major Revision**

---

### Major Concerns

**1. [STAT-1] Ablation table reports uncorrected p-values despite claiming Holm-Bonferroni correction**

The paper states in the ablation methodology (Section 4.5): *"Statistical significance of ablation results was evaluated using McNemar's test with Holm-Bonferroni correction."* However, Table 4 (ablation study) reports raw p-values "<0.001***" without any correction. This is a direct contradiction. The Holm-Bonferroni correction for 7 comparisons sets α' = 0.05/7 = 0.007. If the authors applied this correction, then the smallest p-values (e.g., problem_rating, problem_type, hour) should be re-evaluated against α' = 0.007, not α = 0.05. At minimum, the authors must either: (a) apply the correction and report corrected significance levels, or (b) clarify that the ablation p-values are uncorrected and reserve the Holm-Bonferroni correction only for the primary ML-LLM McNemar comparisons.

This is a methodological integrity issue that must be resolved before publication.

**2. [STAT-2] 95.02% accuracy is misleading as a headline metric**

The paper leads with "95.02% accuracy" (Gradient Boosting) as its primary performance claim. However, 76.6% of the test set is Wrong Answer (WA). A trivial majority-class baseline achieves 76.6% accuracy. The 95.02% figure is dominated by the WA class (F1=0.97), while Runtime Error — which represents the most pedagogically interesting boundary — achieves only F1=0.52. 

I recommend the authors lead with **balanced accuracy** (reported as 0.89 for GB) as the primary metric, or at minimum prominently report the class-conditional results alongside overall accuracy. The current framing makes the method appear more effective than it is for the hard cases.

**3. [STAT-3] Per-class F1 for LLMs is inconsistently reported**

Table 5 (LLM results) reports Macro F1 = 0.5447 for DeepSeek-V3 but the per-class F1 breakdown is deferred to "Supplementary Materials." Given that per-class performance is the central story (DeepSeek-V3 collapses on RE: F1=0.03), these numbers should appear in the main paper. The reviewer cannot assess the validity of the "platform-encoding boundary" claim without seeing whether LLMs fail on the same classes as ML models.

**4. [STAT-4] Confidence intervals not reported for ablation drops**

Table 4 reports accuracy drops (e.g., "8.8 pp") as point estimates without confidence intervals. Without CI, it is impossible to assess whether the 8.8 pp drop for time_consumed_ms is statistically distinguishable from the 3.6 pp drop for user_success_rate. Bootstrap CIs or formal tests comparing ablation drop magnitudes are needed.

---

### Minor Concerns

**5. [STAT-5] Sensitivity table reports single-seed results**

Table 3 (sensitivity analysis) is explicitly labeled "values from a single-seed run." For a power analysis to be credible, these results should be replicated across multiple random seeds, or at minimum the variance across seeds should be reported. A single run is insufficient evidence for sample size adequacy.

**6. [STAT-6] Logistic Regression CV SD is 3.26 pp — unusually high**

Random Forest CV SD is ±0.65 pp and Gradient Boosting is ±0.39 pp, but Logistic Regression shows ±3.26 pp. This 5× higher variance suggests instability in the LR model, which is noted but not investigated. The authors should either investigate the source of this variance or remove LR as a baseline if it is not stable.

---

## REVIEWER B — Automated Assessment / CS Education Expert (Juho Leinonen profile)

**Expertise**: Automated assessment systems, LLM-generated feedback, CS1/CS2 education, educational data mining.

### Summary Recommendation: **Major Revision**

---

### Major Concerns

**1. [ED-1] Core pedagogical claim is circular and trivially true**

The central contribution is characterizing the "platform-encoding boundary" — the finding that CE, TLE, and MLE are deterministically recoverable from metadata because execution time = 0, time_limit, and memory_limit define these verdicts. But **the platform already returns these verdicts**. The online judge already tells the student "Compilation Error" or "Time Limit Exceeded." Building a classifier to recover a verdict that is already explicitly provided is circular.

The paper never explains: *in what realistic deployment scenario would a classifier need to re-classify verdicts the platform already delivers?* The only plausible scenario is (a) the platform's verdict API is unavailable, or (b) a third-party system is receiving metadata streams without the verdict label. Neither scenario is discussed or motivated.

The paper would become significantly stronger if it focused on the **WA↔RE boundary** (which is genuinely non-trivial — neither is deterministically encoded) as the primary contribution, with the CE/TLE/MLE analysis as context.

**2. [ED-2] Population generalizability is unestablished**

The dataset is from competitive programmers (Codeforces, rating 800–3,500). The paper explicitly acknowledges this limitation and names CS1QA and Blackbox as needed validation targets, but **no such validation is performed or reported**. For a paper claiming pedagogical relevance — "provides educators with cost-effective verdict-screening tools" — the lack of student population validation is a critical gap.

CS1 students produce a fundamentally different error distribution: Altadmri & Brown (2015) found 42% CE in novice populations, compared to 7.3% in this dataset. If CE is 6× more prevalent in CS1, the 95.02% accuracy figure (driven by CE being trivially separable) will have very different behavior when deployed in a classroom context. I recommend either: (a) conducting a student validation study, or (b) substantially reframing the contribution as a competitive programming study with potential classroom implications, not a general computing education contribution.

**3. [ED-3] The `user_success_rate` feature is circular and deployment-unrealistic**

The paper acknowledges that `user_success_rate` encodes verdict information because WA and RE submissions are classified as unsuccessful. More critically, in a **formative assessment** context — where this tool would presumably be used — the feature would be continuously updated as students submit, creating a moving target that partially encodes the target variable.

Furthermore, `user_success_rate` is a **historical aggregate** that would not be available for new students in early-semester deployment. The feature's 19.4% Gini importance (second largest after time_consumed_ms) means the model's accuracy substantially depends on a feature that is: (a) circular with the target, and (b) unavailable at deployment time for new students. The paper should either remove this feature and report the resulting accuracy drop, or more prominently flag this as a limitation.

**4. [ED-4] LLM evaluation protocol does not reflect state-of-the-art practice**

The paper uses zero-shot prompting only, dismissing fine-tuning and few-shot with a single sentence: "Future work should compare fine-tuned LLMs." However, the few-shot experiment is actually reported in the text (DeepSeek-V3 few-shot: 64.55% accuracy), showing that the authors have the data to include this comparison but chose not to. This omission makes the ML-LLM comparison appear more favorable to ML than it should be.

Moreover, the paper does not compare against GPT-4 or Claude 3.5, which are the most widely discussed LLMs in CS education research. Using only DeepSeek-V3 and Qwen2.5:3B as LLM representatives limits the generalizability of the LLM comparison claims.

---

### Minor Concerns

**5. [ED-5] Feedback theory claims are asserted, not demonstrated**

The paper grounds its contribution in Hattie & Timperley's feedback model and Bandura's self-efficacy theory, testing two "theoretical predictions." However, these predictions are merely stated to be "consistent with" the findings — no causal mechanism is established. The paper explicitly says "causal validation would require a controlled study...which is beyond the scope of this work." If the theoretical framing cannot be validated within the paper's scope, it should be removed or substantially de-emphasized, as it currently reads as rhetorical scaffolding rather than genuine theoretical contribution.

**6. [ED-6] Deployment guidelines (Table 7) are unsubstantiated**

Table 7 (deployment guidelines) recommends ML-based verdict classification for six educational contexts based on the paper's results. However, these recommendations are not validated through any teacher or student study. The guidelines assume that automated verdict classification translates to learning improvement, which is a non-trivial pedagogical claim that requires evidence. At minimum, the paper should cite prior work showing that automated verdict feedback improves learning outcomes.

---

## REVIEWER C — Statistics / Research Methodology Expert (Paul Denny profile)

**Expertise**: Programming assessment research design, statistical methodology, experimental validity.

### Summary Recommendation: **Major Revision**

---

### Major Concerns

**1. [METH-1] The "fair comparison" ML-LLM design is not actually fair**

The paper acknowledges that the ML-LLM comparison is asymmetric (ML trained on 10,688 samples; LLMs zero-shot) but frames this as reflecting "realistic deployment conditions." I disagree. The paper's own results undermine this framing: the few-shot experiment (3-shot per class, 15 examples) reduces DeepSeek-V3 accuracy from 76.65% to 64.55%, demonstrating that **more data hurts this particular prompt setup**. This indicates a prompt engineering problem, not an LLM capability ceiling.

A genuinely fair comparison would either: (a) provide LLMs with few-shot examples from the same training distribution, (b) compare ML models trained on the same small sample sizes as would be available in early-deployment scenarios, or (c) clearly frame the comparison as "supervised ML with abundant labels vs. zero-shot LLM with no labels," without claiming the gap reflects inherent capability differences.

The current framing allows the reader to conclude that "ML outperforms LLMs," when the more accurate conclusion is "supervised ML with 10,688 labels outperforms zero-shot inference with no labels."

**2. [METH-2] Multiple comparison problem in ablation study is unresolved**

Seven features are ablated, generating seven pairwise McNemar comparisons against the full model. The paper claims to apply Holm-Bonferroni correction but Table 4 does not reflect this. Even if the correction were applied, seven comparisons at α' = 0.007 would require very small p-values for significance. The hour feature (0.00 pp drop, labeled "n.s.") already fails to reach significance, but several borderline features (problem_rating: 0.10 pp, problem_type: 0.10 pp) may flip from significant to non-significant under correction.

The authors should report both corrected and uncorrected results, or use a more powerful alternative (e.g., Likelihood Ratio Test comparing full vs. reduced models).

**3. [METH-3] Train-test split by (user, problem) pair may not prevent leakage**

The paper deduplicates submissions by retaining only the final submission per (user, problem) pair to "prevent train-test leakage." However, this only prevents leakage within the same (user, problem) pair. A user who solves problem A multiple times across different attempts can appear in both training and test sets on different problems, potentially allowing the model to learn user-specific patterns that generalize across problems. This is particularly concerning given that `user_success_rate` (19.4% Gini importance) captures exactly this user-level signal.

A leave-one-user-out cross-validation would more rigorously assess generalization to unseen users.

**4. [METH-4] The power analysis references the wrong baseline**

The power analysis (Section 3.4) assumes expected accuracy of 85% and calculates minimum sample size ~600. However, the actual majority-class baseline is 76.6%, and the paper's primary comparison is between models with 95.02%, 94.24%, 76.65%, and 35.50% accuracy — a range far exceeding the 85% assumption. The power analysis is irrelevant to the actual research questions and should either be removed or recalculated based on the relevant effect sizes (e.g., detecting a 15 pp difference between GB and DeepSeek-V3).

---

### Minor Concerns

**5. [METH-5] IRB approval number "2026-AI-003" appears non-standard**

The paper states "IRB Approval No. 2026-AI-003, Xijing University." The "2026-AI" prefix suggests this may be a placeholder or future-dated identifier. Reviewers cannot verify this through standard channels. If this is a real IRB approval, the authors should provide the full protocol number or institutional contact for verification. If it is not a real approval, it must be removed.

---

## REVIEWER D — HCI / Writing / CS Education Theory Expert (Arto Hellas profile)

**Expertise**: LLM-based feedback, programming education theory, human-computer interaction in educational tools.

### Summary Recommendation: **Major Revision**

---

### Major Concerns

**1. [WRITE-1] The "platform-encoding boundary" framing is conceptually confused**

The paper defines the "platform-encoding boundary" as "the point at which verdict information is determined by platform measurement thresholds rather than by features that generalize across different platform configurations." This definition conflates two distinct concepts:

- **Concept 1**: A statistical finding (execution time = 0 → CE is deterministically recoverable)
- **Concept 2**: A generalization claim (features should "generalize across different platform configurations")

For Concept 2, the paper provides no evidence whatsoever. The dataset is from a single platform (Codeforces). There is no cross-platform validation. The paper cannot claim "features that generalize across platforms" without actually testing generalization across platforms.

The definition should be simplified to the statistical finding: "the platform-encoding boundary is the point at which verdict information is deterministically recoverable from metadata." The generalization dimension should be removed or experimentally validated.

**2. [WRITE-2] The pedagogical contribution is asserted, not demonstrated**

The paper claims that verdict classification "provides educators with cost-effective verdict-screening tools" and "enables immediate diagnostic feedback." These are product claims, not research findings. No teacher or student was consulted. No learning outcome was measured. No usability study was conducted.

TOCE publishes empirical computing education research. A paper that reports a 95.02% accuracy figure without any validation of educational impact is not yet a computing education contribution — it is a machine learning demonstration on an education-relevant dataset. The authors should either: (a) conduct a user study validating the educational utility, or (b) substantially reframe the contribution as a technical feasibility study with identified classroom implications.

**3. [WRITE-3] The paper's structure makes it difficult to identify the primary contribution**

The paper addresses three research questions (RQ1: error patterns, RQ2: ML performance, RQ3: platform-encoding boundary) with contributions spanning data analysis, ML benchmarking, and educational theory. This breadth dilutes the focus. 

For TOCE specifically, RQ1 (error pattern analysis) is the least novel — error distributions in competitive programming are well-characterized in prior work. RQ2 (ML benchmarking) is a machine learning contribution, not primarily a computing education one. RQ3 (platform-encoding boundary) is the most distinctive, but its significance is undermined by the circularity concern (ED-1 above).

I recommend restructuring the paper around a single central question: *"What is the metadata-derivable upper bound for verdict classification, and what does this imply for automated feedback in computing education?"* with the ML-LLM comparison as supporting evidence, not the main story.

**4. [WRITE-4] Several references cannot be verified**

The paper cites several 2024-2025 conference papers without verifiable publication venues or DOI links:
- `raihan2025large`: SIGCSE 2025 paper. The DOI appears incomplete/missing in the reference list.
- `kazemitabaar2024impact`: Listed as "ACM Conference" without specific conference name or page numbers.
- `denny2024prompt`: States "to appear" with no DOI or publication confirmation.
- `leerentveld2024not`: Typo — should be "Leerentveld" not "Leerentveld" (the actual author is C. Leerentveld based on the ICER 2024 proceedings).

These reference quality issues should be addressed before publication.

---

### Minor Concerns

**5. [WRITE-5] Conclusion is too long and restates prior sections**

The Conclusion (Section 6) runs approximately 1.5 pages and substantially duplicates the contributions listed in the Introduction. A strong conclusion should synthesize findings into higher-level insights and identify specific future research directions, not re-list individual contributions. I recommend cutting the Conclusion by 50% and adding a paragraph on specific next steps (e.g., cross-platform validation, student population study).

---

## Summary of Required Revisions

| Reviewer | Priority | Issue | Severity |
|----------|----------|-------|----------|
| A (Stats/ML) | METH | Ablation p-values contradict Holm-Bonferroni claim | Critical |
| A (Stats/ML) | STAT | 95.02% accuracy misleading; should lead with balanced accuracy | Major |
| A (Stats/ML) | STAT | Per-class LLM F1 deferred to supplement | Major |
| B (Ed/Assessment) | ED | CE/TLE/MLE classification is circular (platform already returns verdict) | Critical |
| B (Ed/Assessment) | ED | No student population validation; CS1 generalizability unestablished | Major |
| B (Ed/Assessment) | ED | `user_success_rate` is circular and deployment-unrealistic | Major |
| B (Ed/Assessment) | ED | Few-shot LLM results buried; comparison incomplete | Minor |
| C (Methodology) | METH | "Fair comparison" is not actually fair (asymmetric data) | Critical |
| C (Methodology) | METH | Ablation multiple comparisons unresolved | Major |
| C (Methodology) | METH | Train-test split does not prevent all user-level leakage | Major |
| C (Methodology) | METH | Power analysis uses wrong baseline | Minor |
| D (Theory/HCI) | WRITE | "Platform-encoding boundary" definition is conceptually confused | Major |
| D (Theory/HCI) | WRITE | Pedagogical contribution is asserted, not demonstrated | Major |
| D (Theory/HCI) | WRITE | Paper structure too broad; primary contribution unclear | Major |
| D (Theory/HCI) | WRITE | Several references unverified or contain errors | Minor |

### Verdict: **Major Revision**

The paper presents a well-motivated dataset and thoughtful analysis of the ML-LLM comparison. However, four critical issues must be resolved before publication:

1. **Ablation p-values and correction claims must be reconciled** (Reviewer A/C)
2. **The circularity of classifying platform-provided verdicts must be explicitly addressed** (Reviewer B)
3. **The "fair comparison" framing must be either fixed or dropped** (Reviewer C)
4. **Student population validation or substantial reframing is required** (Reviewer B/D)

If these issues are addressed, the paper could make a strong contribution to TOCE's intersection of ML methodology and computing education.
