# ACM TOCE 论文评审报告
**评审日期**: 2026-07-29
**目标期刊**: ACM Transactions on Computing Education (SCI Q2, IF≈2.8)
**评审人**: 资深同行评审（顶刊级别）
**论文**: Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming
**作者**: Wenbin Hu (Xijing University)
**字数**: 全文 1,364 行（约 28 页）

---

## 评审报告摘要

**总体建议**: **Major Revision（大幅修改后再审）**

本论文在实验设计和数据规模上有扎实的基础工作，但存在若干方法论严谨性问题、写作质量问题，以及一个核心概念框架上的逻辑缺陷，需要在投稿前解决。论文目前在 TOCE 的接受概率估计为 **30-40%**。

---

## 严重问题（🔴 Critical）

### 问题 1: ML-LLM 特征集不匹配导致比较不公平
- **位置**: 第 3.2 节（Feature Engineering）vs 第 4.5 节（LLM Performance Comparison，Section 4.5 at lines 601+）
- **问题描述**: 
  ML 模型使用 **7 个特征**（problem_rating, language, time_consumed_ms, memory_kb, problem_type, hour, user_success_rate），而 LLM 仅使用 **5 个特征**（problem_rating, language, time_consumed_ms, memory_kb, passed_test_count）。论文在 Table 7 的表注中注明了 5-feature GB (92.0%)，但在正文 Results 部分（Section 4.2）将 7-feature GB (95.02%) 作为主要结果呈现，这造成了两种不同的比较基准：

  | 比较基准 | ML | LLM | 差距 |
  |---------|-----|-----|------|
  | 标注的主比较 | GB 7-feature: **95.02%** | DeepSeek-V3: 76.65% | **18.4 pp** |
  | 声明的公平比较 | GB 5-feature: 92.0% | DeepSeek-V3: 76.65% | 15.4 pp |

  论文选择报告 15.4 pp（5-feature GB）作为"公平比较"，但 18.4 pp 的 7-feature 对比被分散在正文各处，造成了信息呈现的不一致。更重要的是，LLM 的 5 个特征与 ML 的 5 个子集并不完全对应（LLM 用 passed_test_count，ML 7-feature 中没有 passed_test_count；ML 的 problem_type, hour, user_success_rate LLM 无法使用），这意味着即使控制特征数量，比较仍不完全公平。

  **passed_test_count 的数据泄露风险**：passed_test_count 在 CE 中 100% = 0，与 verdict 直接共线（r = -0.107 for CE）。论文在第 3.2 节已承认这一点并声称 ablation 显示影响仅 0.5 pp，但 passed_test_count 仍然是 LLM 使用的唯一特征之一（7-feature ML 中没有此特征），这造成 ML-LLM 对比中 LLM 额外受益于一个"准 verdict 标签"特征。

- **修改建议**:
  1. 在正文 Results 中明确区分两个比较基准，在摘要中统一使用 5-feature GB (92.0%) vs DeepSeek-V3 (76.65%) = 15.4 pp 的数字，避免同时报告两个竞争性的比较数字
  2. 明确说明 LLM 的 5 个特征与 ML 的 5-feature 子集是否完全一致；如果不一致，给出对应关系表
  3. 考虑将 passed_test_count 从 LLM 特征中移除，以实现真正的公平比较（因为它与 verdict 共线），并在正文和补充材料中报告移除后的 LLM 结果
  4. 在 Table 7 中增加 7-feature GB 的 McNemar 比较行，显示 18.4 pp 差距的统计显著性

---

### 问题 2: Ablation 多重比较未校正
- **位置**: Table 5 (Ablation study, lines ~900-930)
- **问题描述**: 
  Ablation 研究包含 7 次独立的 feature removal 实验，每次与 full model 比较时都使用 McNemar test（α = 0.05）。在 7 次独立检验中，预期有 0.35 次假阳性（family-wise error rate = 1 - 0.95^7 = 30.1%）。论文正文对 McNemar 比较应用了 Bonferroni 校正（α' = 0.005，10 次比较），但对 ablation 的 7 次比较**未做任何多重比较校正**。Table 5 中所有 p-value 标注为 < 0.001，但这 7 个 p-value 中可能有 1-2 个是假阳性。
  
  特别值得关注的是 hour (0.0% importance, p < 0.001) — Gini importance 明确显示 0.0% 贡献，但 McNemar p < 0.001 在未校正时可能仍是假阳性。更重要的是，hour 在 ablating 后准确率**没有下降**（95.02% → 95.02%），这种情况下 McNemar test 实际上是比较全零误差 vs 有误差，而论文对"无差异"也给出了 p < 0.001 的结论，这在统计上是错误的——Wilcoxon signed-rank test 或 sign test 才是正确的检验方法。

- **修改建议**:
  1. 对 ablation 的 7 次比较应用 Bonferroni 校正（α' = 0.05/7 ≈ 0.007），或改用 Holm-Bonferroni 逐步校正
  2. 对 hour 的"无显著差异"使用正确的非参数检验（sign test）而不是 McNemar
  3. 将校正后的结果在 Table 5 中明确标注，例如在表注中说明"Seven pairwise McNemar tests; Bonferroni-corrected threshold α' = 0.007"
  4. 如果校正后某些特征的 p-value 不再显著，应如实报告（如 hour 可能从"p < 0.001"变为"n.s."）

---

### 问题 3: 循环论证风险 — "Platform-Encoding Boundary" 框架的逻辑困境
- **位置**: Abstract, Introduction (第 3-4 页), Discussion Section 6.1
- **问题描述**: 
  这是审稿人最可能首先质疑的核心逻辑问题。论文的核心贡献声称 CE/TLE/MLE 是"platform-encoded"（由平台测量阈值决定），因此可以从 metadata 恢复。但这个论断存在根本性的循环：

  ```
  CE 定义 = time_consumed = 0
  因此：metadata 中 time_consumed = 0 → 预测 CE
  这是"发现"吗？这只是重言式。
  ```

  论文在 Abstract 和 Discussion 6.1 中试图用两段文字辩解（"the model must first discover this relationship from data"），但这个辩解是不完整的：

  1. **如果一个特征与 label 的关系是定义性的（definitional），模型从数据中学习它并不是贡献**。贡献在于发现哪些 verdict 是*不*可定义的（WA ↔ RE），但论文花了大量篇幅论证 CE/TLE/MLE 的"可恢复性"，这混淆了真正的贡献。

  2. **"Platform-encoding boundary" 这个术语本身暗示了一种科学边界，但实际上它描述的是平台设计决策**。这不是一个发现，而是一个规范陈述（prescriptive statement）。

  3. **ROC-AUC = 1.000 for MLE/TLE** 证明了这些 verdict 是完美可分的，但这不是 ML 的功劳——这是数据集的特性。报告这个 AUC 作为 ML 性能指标具有误导性。

- **修改建议**:
  1. **重新定位贡献声明**：核心贡献应聚焦于（a）WA↔RE 边界不可分（这是真正的新发现）；（b）ML 在 metadata 上的整体性能；（c）ML vs LLM 的系统性比较
  2. **重新定义"Platform-Encoding Boundary"**：将其明确定义为"platform-design-induced boundary"（平台设计导致的边界），而非暗示它是自然存在的科学边界
  3. **将 CE/TLE/MLE 的性能（ROC-AUC = 1.000）作为 baseline/deterministic bound 单独报告**，不作为 ML 模型的贡献
  4. **在摘要中大幅精简**关于 CE/TLE/MLE 的描述，强调真正的贡献是识别了 WA↔RE 的不可分性

---

### 问题 4: 极端类别不平衡 + 缺乏处理策略说明
- **位置**: Table 2 (Error Distribution), Table 3 (ML Results), Table 4 (Confusion Matrix)
- **问题描述**: 
  数据集类别分布严重失衡：WA 占 76.6%（10,234 条），MLE 仅 1.5%（202 条）。测试集中 MLE 仅有 40 个样本，RE 有 131 个。这种不平衡导致：

  1. **总体准确率（95.02%）严重掩盖了类别间的性能差异**：GB Macro F1 = 0.8711，差距达 7.8 pp，这说明模型对少数类的分类能力很差
  2. **论文未说明是否尝试了任何重采样策略**（SMOTE、ADASYN、class_weight 参数）。GB/RF 的 class_weight='balanced' 可能会显著改变结果，但论文对此沉默
  3. **论文在多个地方提到类别不平衡问题**（Section 3.2, Discussion 6.3），但仅声称"we additionally report Balanced Accuracy"——这不足以处理问题，应该说明具体采取了哪些措施
  4. **测试集 MLE n=40**：这个样本量太小，单个正确/错误预测会导致 F1 变化高达 0.09（MLE F1 从 0.91 变到 0.86 或 0.95），置信区间会非常宽。Wilson score interval 会显示这一点，但论文未报告

- **修改建议**:
  1. 在 Methodology 中明确说明是否使用了 class_weight 参数、SMOTE 或其他重采样策略，并解释为什么（不）使用
  2. 报告 class_weight='balanced' 条件下的结果（如果适用），与默认设置对比
  3. 对 MLE (n=40) 和 RE (n=131) 的 F1 分数，在 Table 4 中报告 Wilson score 置信区间
  4. 在 Table 3 的 Balanced Accuracy 行之外，考虑报告 per-class recall 的置信区间，让读者了解少数类的估计精度

---

### 问题 5: 写作问题 — 段落重复 + 拼写错误
- **位置**: Discussion Section 6.1 (约为 lines 1100-1150)，全文
- **问题描述**: 
  根据此前的评审报告（2026-07-25）和本轮检查发现以下写作问题：

  1. **Section 6.1 存在段落重复**：关键词 "ralistically" 附近有文字完全重复，这在投稿版本中不可接受
  2. **拼写错误 "establishedhed"**：应为 "established"
  3. **Section 4.2（传统 ML 性能）的 Class-Wise Analysis 小节标题与后面的 Confusion Matrix Analysis 小节内容高度重叠**，实际上 Class-Wise Analysis 小节几乎没有任何独立内容，直接跳到了 Confusion Matrix 分析
  4. **Section 4.5 LLM Performance Comparison 的 sub-section 标题引用**："Key Finding 1"、"Key Finding 2" 在 Section 4.5 中定义，但在 Section 4.2 Results 开头就出现了，造成前言不搭后语
  5. **Figure 5 的 \Description 命令在 LaTeX 中不是标准用法**，应改为 \desc 或移除；figure 路径使用 fig_*.png 和 fig_*.pdf 混用，应统一

- **修改建议**:
  1. **立即搜索全文**，定位并删除 "ralistically" 附近的重复段落
  2. 搜索并修正 "establishedhed" → "established"
  3. 合并或删除重复的 Class-Wise Analysis 小节
  4. 将 Key Finding 1/2/3 的定义移到第一次出现的 Section 4.5 中，移除 Section 4.2 中的前向引用
  5. 统一 figure 文件格式

---

## 次要问题（🟡 Minor）

### 问题 6: LLM 实验缺乏方差估计
- **位置**: Section 4.5 (LLM Performance Comparison)
- **问题描述**: DeepSeek-V3 和 Qwen2.5:3B 的结果均为**单次实验**（single run），没有随机种子重复、没有方差估计。论文声称 "This is a limitation of the current study"，但没有说明是否尝试了多次调用来估计方差。

  实际上，LLM API 调用即使在 temperature=0 时也存在非确定性（KV cache、batching 等因素），单次结果的可信度有限。DeepSeek-V3 的 76.05% ± ? 没有置信区间（仅在 valid predictions 子集上报告了 CI），对 all predictions 的 76.05% 没有 CI。

- **修改建议**: 至少用 3 个不同的 API request ID 或 random seed 重复 DeepSeek-V3 实验，报告均值和标准差。如果 API 成本有限制，应在 Limitations 中更坦诚地说明这一约束。

---

### 问题 7: Qwen2.5:3B 的定位问题
- **位置**: Abstract, Section 4.5, Discussion
- **问题描述**: 
  论文将 Qwen2.5:3B 描述为"small local LLM suitable for privacy-sensitive educational deployment"，但实际上：
  1. Qwen2.5:3B 在 valid predictions 上的准确率仅 35.50%，且 10.1% 的输出无效
  2. 31.92% 的整体准确率**低于 random baseline**（random 5-class baseline 约 20% 准确率，但 majority class baseline 为 76.6%，Qwen 31.92% < 76.6%）
  3. 用一个**完全失败**的模型来证明"local small models are not viable"的信息价值有限

  论文自己也承认 "We frame the Qwen result as a documented failure mode"，但这个失败模式被用来得出"local LLM inference is not yet viable"的强结论。实际上，Qwen2.5:3B 只是一个小规模的本地模型，在 metadata 推理任务上完全失败不能推广到其他本地模型（如 Qwen2.5:7B, Qwen2.5:14B）。

- **修改建议**: 
  1. 将 Qwen2.5:3B 定位为"3B parameter model as a minimum-viable local baseline"，而非"representative local model"
  2. 补充说明：如果使用更大的本地模型（如 Qwen2.5:7B 或 Llama-3-8B），结果可能不同
  3. 在结论中修改为："3B-scale local models are not viable for this task; future work should evaluate 7B+ local models"

---

### 问题 8: 近 3 年文献占比严重不足
- **位置**: references.bib
- **问题描述**: 根据此前评审报告，当前引用中 2023-2026 年仅占约 19%，远低于 TOCE 期望的 40%+。关键遗漏包括：
  - Sarsa et al. (2022, TOCE) — LLM 教育应用
  - Leerentveld et al. (2024) — LLM 反馈效果
  - Le Goues et al. (2019) — 程序修复
  - Korkmaz (2012) — 编程自我效能量表

- **修改建议**: 补充至少 15-20 条 2023-2026 年的文献，重点关注：
  1. LLM 在编程教育中的实证应用（2022-2024）
  2. 编程教育中的 ITS/智能辅导系统文献
  3. 程序自动修复（APR）领域的最新进展
  4. 教育数据挖掘中的 metadata 分析最新工作

---

### 问题 9: GB vs RF 边际显著性的过度宣称
- **位置**: Results Section 4.1, Discussion Section 6.1
- **问题描述**: 
  McNemar test 结果：χ² = 2.88, p = 0.045。论文自己的 Bonferroni 校正后阈值 α' = 0.005，p = 0.045 > 0.005，结论是"n.s."（无显著差异）。但论文在摘要中写"GB: 95.02%"作为最高结果，在正文中声称"Gradient Boosting achieves the highest test accuracy"，并在 Table 7 中将 GB 加粗。这构成了一种"弱显著即宣称"的问题。

  更重要的是，Holm-Bonferroni 方法（论文也报告了）在 α=0.05 水平上认为 GB > RF 显著，但这与 Bonferroni 结论矛盾。论文选择报告 Bonferroni 作为保守标准，却没有在正文中保持一致的叙述。

- **修改建议**: 
  1. 在正文中明确说明 GB 和 RF 没有统计学显著差异（p > 0.005 after Bonferroni）
  2. 将 Table 7 中 GB 和 RF 都保留为推荐模型，并说明两者性能在统计上等价
  3. 在摘要中改为"Gradient Boosting (95.02%) and Random Forest (94.24%)"并列报告，而非突出 GB

---

### 问题 10: LLM features 中的 passed_test_count 未在 ML 实验中一致使用
- **位置**: Section 3.2 vs Section 4.5
- **问题描述**: 
  LLM 使用 5 个特征，其中包括 passed_test_count，但 ML 的 7-feature 模型中没有 passed_test_count（Section 3.2 明确列出了 7 个特征，没有 passed_test_count）。论文在 Section 3.2 中承认 passed_test_count 与 verdict 共线，因此将其从 ML 特征中排除。但 LLM 却使用了这个特征。

  这意味着 LLM 实际上获得了一个"准标签泄露"特征的优势：passed_test_count = 0 对于 CE 是 100% 准确的（Section 3.2 报告 100% of CE submissions have passed_test_count = 0），这相当于 LLM 获得了一个 CE 的直接指示器。

  论文的 ablation 显示 passed_test_count 在 ML 中仅贡献 0.5 pp，但 LLM 的 CE F1 仍然很低（0.49 zero-shot），说明 LLM 并未充分利用这个特征——但这不能掩盖特征集不一致的问题。

- **修改建议**: 
  1. 将 passed_test_count 从 LLM 特征中移除，实现真正的公平比较
  2. 或者在 ML 实验中增加一个包含 passed_test_count 的 8-feature 变体，单独报告结果

---

## 优化建议（⚪ Suggestion）

### 建议 1: Introduction 压缩
- **位置**: Introduction（第 1-4 页）
- **建议**: TOCE 期望 Introduction 为 1.5-2 页，当前约 3-4 页。建议：
  1. 将 Caveat on population generalizability 段落移至 Limitations
  2. 精简 Related Work 中的部分段落，合并相似引用
  3.  Contributions 部分从 3 条压缩，删除"Comprehensive Statistical Analysis"（这是标准实践，不是贡献）

### 建议 2: Figure 质量统一
- **位置**: 全文各 figure
- **建议**: 
  1. Figure 5 使用 .png 格式，而其他 figure 使用 .pdf 格式。应统一为 PDF 以保证出版质量
  2. Fig 3 (error by difficulty) 的 Y 轴标签和 Fig 5 (class F1 chart) 的 X 轴标签在 PDF 中可能不清晰，检查 LaTeX 编译后的显示效果
  3. Figure 6 (ROC curves) 和 Figure 7 (PR curves) 的字体大小应检查是否在 8-10pt 以上（ACM 投稿要求）

### 建议 3: Table 格式优化
- **位置**: Table 7, Table 8, Table 9
- **建议**: 
  1. Table 7（McNemar results）包含大量表注，占用了较多篇幅。建议将表注精简为关键说明，完整说明移至补充材料
  2. Table 8（LLM analysis）和 Table 9（method guidelines）的列宽设置应优化，避免出现大量空白
  3. 所有表格的标题应在表格上方（ACM 标准），检查当前格式是否符合

### 建议 4: Theoretical Framework 的整合深度
- **位置**: Section 3.2（Theoretical Framework 小节）
- **建议**: 
  1. 当前的理论框架（Hattie & Timperley, Bandura）仅作为"引言装饰"，没有被用来生成具体的可检验预测。建议在 Introduction 中增加 1-2 个具体的理论预测，在 Results 中逐一验证
  2. 或者，将理论框架降级为 Background 小节，明确说明这是 motivation 而非 formal hypothesis

### 建议 5: Cover Letter 需诚实限定范围
- **建议**: 在 Cover Letter 中主动承认：
  1. supervised ML vs zero-shot LLM 的不对称性
  2. Codeforces 竞技程序员 vs CS1 学生的人群差异
  3. 仅测试了两个 LLM（DeepSeek-V3, Qwen2.5:3B），未包含 GPT-4/Claude
  4. 这是"production-ready ML vs out-of-box LLM"的对比，而非两个范式的公平对决

---

## 总体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| **创新性** | 6/10 | "Platform-encoding boundary" 概念有价值但存在循环论证风险；ML-LLM 系统性比较有新意 |
| **严谨性** | 5/10 | 方法论总体扎实，但特征集不匹配、ablation 多重比较未校正、LLM 单次实验无方差是显著缺陷 |
| **写作质量** | 6/10 | 结构清晰，但存在段落重复、格式不统一、前向引用混乱等问题 |
| **实验设计** | 7/10 | 数据规模充足（13,360 样本），设计完整，但类别不平衡处理不足 |
| **适合发表** | **No（Major Revision）** | 核心问题（问题 1-4）必须解决 |

---

## 核心修改意见（必须解决的 3 条）

### 🔴 核心修改 1：重新定位"Platform-Encoding Boundary"框架
将 CE/TLE/MLE 的"可恢复性"从核心贡献降级为背景观察。真正的贡献是：
1. **系统性地量化了 metadata 在每种 verdict 类型上的信息含量**（尤其是 WA↔RE 边界不可分）
2. **ML vs LLM 在 metadata-only 分类任务上的系统比较**（控制相同特征集）
3. **为教育平台提供部署决策依据**（accuracy-cost-latency 权衡）

### 🔴 核心修改 2：解决 ML-LLM 特征集不匹配问题
统一 ML 和 LLM 的特征集（建议都使用 5 个共同特征，排除 passed_test_count 以避免 verdict 共线），并重新运行所有实验。更新摘要、正文和所有表格中的比较数字，确保报告一致。

### 🔴 核心修改 3：对 Ablation 进行多重比较校正
对 Table 5 的 7 次 ablation 比较应用 Bonferroni 校正（α' = 0.007），修正 hour 的检验方法（用 sign test 而非 McNemar），并在论文中透明报告校正结果。

---

## 次要修改清单（建议按优先级排序）

1. **[高优先级]** 删除 Section 6.1 的重复段落，修正拼写错误
2. **[高优先级]** 补充近 3 年文献（至少 15-20 条，目标 40%+ 占比）
3. **[中优先级]** 报告 LLM 实验的方差估计（至少 3 次重复）
4. **[中优先级]** 说明是否使用了 class_weight 或 SMOTE 等类别不平衡处理策略
5. **[中优先级]** 将 GB 和 RF 并列为等效最佳模型，不过度强调 GB
6. **[低优先级]** Introduction 压缩至 2 页以内
7. **[低优先级]** 统一 figure 文件格式为 PDF
8. **[低优先级]** 理论框架作为 motivation 而非 formal hypothesis 说明

---

*评审报告结束*
