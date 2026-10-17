# TOCE 顶刊级别评审报告
**审稿人视角 | 2026-08-02 | 目标：TOE/ITiCSE/Koli Calling 一区顶刊**
**论文**：Automated Programming Verdict Classification from Submission Metadata: Comparing Machine Learning and Large Language Models in Competitive Programming
**审稿人定位**：计算教育 + 机器学习 + 统计方法论三重专家

---

## ⚫ CRITICAL / 会直接导致Major Revision或Reject的问题

---

### C1. 循环论证——核心贡献的逻辑根基动摇

**位置**：§1 Introduction / §5.1 Discussion / 全文核心框架

**问题**：论文的核心贡献是发现"platform-encoding boundary"——CE/TLE/MLE 可从元数据恢复，WA↔RE 不能。但这个结论的逻辑是**循环**的：

> 平台（Codeforces）产生判决（CE/TLE/MLE）→ 判决由平台执行环境决定（编译错误=0时间，MLE=内存耗尽）→ ML 分类器从判决标签中学习到这些模式 → 论文宣称"CE/TLE/MLE是平台编码的"

分类器学的就是平台本身输出的标签。你不需要分类器也知道 CE=0 执行时间——这是平台 API 直接告诉你的判决结果。分类器只是把"读取平台判决"这件事重新包装了一遍。

论文在 §5.1 的辩护（"这不是分类器结果，是平台设计属性"）是对的，但它紧接着说"然而需要从标记数据学习"——这恰恰证明了循环：你用平台自己的判决做标签，再声称分类器"发现"了平台编码规律。

**顶刊预期**：这个边界概念如果要有理论价值，必须回答：*给定一个新平台（或学生平台），这个边界是否可预测，而不需要先收集大量标记数据？* 目前论文没有回答这个问题。实验只在同一个平台（Codeforces）上做，没有跨平台验证。

**建议修复**：
- 明确将"platform-encoding boundary"重新定义为：给定一个在线评测平台的执行环境描述（时间限制、内存限制），哪些判决类别是可预测的。这是一个来自平台设计的事实，而非从数据中学习的经验发现。
- 增加跨平台验证（即使是小规模的），证明这个边界在 LeetCode / AtCoder / CS1QA 等不同平台上是一致的
- 在贡献点中更准确地描述：我们验证了元数据中已有的平台阈值信息足以支持特定类别的分类

---

### C2. 敏感度分析表格严重错误——张冠李戴

**位置**：Table 3 (tab:sensitivity)，§3.7

**具体错误**：
```
N (Training) | Test Accuracy | Drop from Full
...
10,688       | 94.24%        | ---
```

论文注："the 10,688 training point corresponds to the full training split and its test accuracy (94.24%) **matches the RF result** in Table 2"

**这是错的**：
- N=10,688 是 Gradient Boosting 在完整训练集上的测试精度
- GB 的完整训练集测试精度应该是 **95.02%**，不是 94.24%
- 94.24% 是 Random Forest 的精度（Table 2 明确标注）

**这意味着**：要么表格填错了数据（把 RF 的结果填进了 GB 的敏感度分析），要么对 10,688 样本的预期理解错误。

**影响**：敏感度分析是经验证据重要组成部分，表格数据与模型不匹配是事实性错误，任何认真审稿的审稿人都会发现并将其作为 major flaw。

**建议**：重新运行 N=10,688 的 GB 实验，确认实际值是否为 95.02%（符合预期），更新表格和注释。

---

### C3. 理论框架段落残缺 + Hattie & Timperley 引用错误

**位置**：§3.4 Theoretical Framework

**问题一（格式破损）**：
理论框架最后一段在 "(2) Bandura's theory..." 处**没有换行**，直接连接正文：
```
task-level feedback (distinguishing logic errors from runtime failures) may require
source-code analysis. (2) Bandura's theory predicts that...
```
这个 "(2)" 前面应该有完整的段落结束和新段落开始，但现在是一个连续句子，语义断裂。

**问题二（引用键错误）**：
```
Hattie and Timperley's model of effective feedback~\cite{hattie2007power}
```
引用键是 `hattie2007power`（单作者格式），但这篇论文是 **John Hattie & Helen Timperley** 合著。正确的引用应该是 `hattie2007power` 但 `author` 字段需要是 `{Hattie, John and Timperley, Helen}`。请确认 references.bib 中的 author 字段是正确的（之前的检查显示 author 字段包含 "Hattie, John and Timperley, Helen"，但引用键命名是单作者风格，混在一起不规范）。

**问题三（内容顺序）**：
Hattie & Timperley 四个层次（task→process→self-regulation→self）的介绍不完整，论文说"task-level feedback focus of this work"，但没有说清楚 process/self-regulation/self-level feedback 的关系，而这些层次直接关系到论文的"反馈"主张。

**建议修复**：
1. 将 "(2) Bandura's theory..." 拆为独立段落
2. 完善 Hattie & Timperley 四个层次的介绍，建立与 metadata-based feedback 的逻辑链
3. 统一引用键命名风格

---

### C4. IRB 编号 + 豁免声明内部矛盾

**位置**：Reproducibility Statement / Data Ethics and Privacy

**矛盾点**：
- Reproducibility Statement："IRB Approval No. 2024-AI-003, Xijing University"
- Data Ethics："qualifies as exempt research under standard IRB guidelines (IRB Approval No. 2024-AI-003)"

如果研究"符合豁免"（exempt），就不需要 IRB 批准（approval）；如果需要 IRB 批准，就不是豁免。两者同时成立在逻辑上是不可能的。

**顶刊标准**：TOCE 和相关计算教育顶刊（TOE, ITiCSE）对伦理声明要求严格。审稿人看到"exempt research" + "IRB Approval No."共存的表述，会立即质疑整个伦理流程的有效性。

**建议**：统一措辞。如果确实获得了正式批准，使用"approved by IRB"；如果确实豁免，删除批准编号，改为"exempt from IRB review per [institution] policy"。

---

### C5. Table note 中的 "$" 符号是乱码

**位置**：Table 2 (tab:ml-results) 下方注释

**原文**：
```
Note: Logistic Regression shows $5\times$ higher CV variance (\$3.26\$ pp) than RF (\$0.65\$ pp) or GB (\$0.39\$ pp)
```

**问题**：`\$3.26\$ pp`、`\$0.65\$ pp`、`\$0.39\$ pp` 中的 `\$` 是多余的。CV 标准差是数值，不是钱，用 `$` 符号是错误的 LaTeX 转义残留（可能原来是 `$3.26$ pp`，然后有人 escape 了 `$`）。

**实际数值**（应该是无美元符号的）：
- LR CV SD: 3.26 pp
- RF CV SD: 0.65 pp  
- GB CV SD: 0.39 pp

**建议**：删除所有 `\$`，改为纯数值。

---

### C6. 理论 CS1 基线是纯数学计算，标注为"发现"是误导

**位置**：§5.6 Empirical Generalization Analysis

**原文**：
> "a CS1-like distribution shifts error mass toward well-classified CE, suggesting metadata-based classification performs *at least as well* on CS1 populations (estimated weighted F1 ≈ 0.92)---pending empirical validation"

**问题**：
- 这个 0.92 是从 Blackbox 的分布数据（42% CE, 12% RE, 46% WA）和论文模型在 Codeforces 上的 per-class F1 通过**数学推算**出来的
- 不是实证发现，不是实验结果
- 论文将其包装为"理论 CS1 基线"，但在 §5.6 的小节标题和叙述中，它被当作某种证据呈现

**顶刊标准**：TOE/ITiCSE/TOCE 对"泛化性声称"要求严格。没有在学生数据集上实际运行模型，就不能声称模型在学生群体上的表现。推算值必须明确标注为"estimated" / "theoretical projection"，且不能出现在 abstract / contributions / conclusions 等核心位置。

**建议**：
- 将 0.92 这个数字从正文中降级，仅在 Limitations 中以"理论估算"形式提及
- 删除所有暗示这个数字是实证结果的措辞

---

## 🟠 MAJOR / 会在审稿中引发大量质疑的问题

---

### M1. 5-feature GB vs 7-feature GB 混淆导致公平性争议

**位置**：Table 5 (tab:mcnemar) / §4.5

**问题**：
- McNemar 比较使用 **5-feature GB** (92.0%) 与 DeepSeek-V3 (76.65%)
- 但论文核心结果和 abstract 中报告的是 **7-feature GB** (95.02%)
- 5-feature 和 7-feature 的差距是 3 pp，审稿人会问：为什么在主要比较中使用降级模型？

论文在 Table 5 注释中有说明（"$^{\dagger}$For a fair ML--LLM McNemar comparison... 5-feature GB variant (92.0%)"），但：
1. 注释字体极小（\small），读者容易忽略
2. 这意味着 ML vs LLM 的"公平比较"中，ML 已经用了一个弱化版本——为什么不让 LLMs 也用 7 个特征？（LLM 实际只用了 5 个，因为 passed_test_count 被排除了）

**审稿人必然追问**：为什么要用 5-feature GB 而不是 7-feature GB？是否在人为缩小 ML-LLM 差距？

**建议**：在 §4.5 开头的 Results 叙述中（而不仅仅在表格注释中）明确解释这个设计选择，并增加一个 7-feature GB vs DeepSeek-V3 的 McNemar 结果作为补充分析。

---

### M2. RE F1 在不同位置的数值不一致

**位置**：Abstract / §4.3 / Figure 2

**具体矛盾**：
- **Abstract**："RE F1 = 0.52" → 说的是 GB 在 RE 上的 F1
- **§4.3 (Confusion Matrix Analysis)**："CE achieves strong classification (F1 = 0.89) ... RE (F1 = 0.52) is the most challenging"
- **Figure 2 (fig:class-f1) caption**："TLE 0.98, WA 0.97, MLE 0.91, CE 0.89, RE 0.52" → 图中 RE = 0.52
- **Table 2 (tab:gb-cm)**：RE 行 F1 = **0.52**

等等——让我重新核对。RE 在 confusion matrix 中的 F1 确实是 0.52，Figure 2 也是 0.52，abstract 也是 0.52。这些是一致的。**但 Figure 2 的 Y 轴范围**需要检查——如果 Y 轴从 0 开始，0.52 的柱子会显得非常矮。

让我重新检查是否还有其他 RE F1 值...

实际上，LLM 结果表格（tab:llm-analysis）中 DeepSeek-V3 RE F1 = **0.03**，Qwen RE F1 = **0.07**。这些是 LLM 的结果，与 ML 的 0.52 不在同一比较框架下。

**我之前说错了**——这里的 RE F1 数值其实是一致的（GB RE F1 = 0.52，所有地方都一致）。但审稿人可能不会这么仔细——他们可能会问：为什么 DeepSeek-V3 在 valid predictions 上 RE F1 只有 0.03？这个巨大的差距说明了什么？

---

### M3. "BAcc=0.89 vs majority baseline=0.20" 的 69pp 提升计算错误

**位置**：§4.3, Table 2

**原文**：
> "95.02% overall accuracy, representing a 69\,pp lift in BAcc over the majority-class baseline (0.89 vs. 0.20)"

**问题**：
- BAcc = 0.89
- majority baseline BAcc = 0.20（五分类，随机猜每个类 20%，balanced accuracy 正好是 0.20）
- 差值 = 0.89 - 0.20 = **0.69**（即 69 个百分点）

这个计算是正确的。0.89 / 0.20 的比值确实是 4.45 倍（论文说 4.45× 也对），差值是 0.69 即 69pp。✅

**但是**：这个"69pp lift"的说法容易引起混淆——因为大多数读者期待的是"accuracy从20%提升到89%，提升了69pp"，但实际上是"balanced accuracy从0.20提升到0.89"。两种说法都对，但混在一起容易造成歧义。

**建议**：明确区分 overall accuracy 和 balanced accuracy 的 majority baseline 计算。

---

### M4. 实验协议不对称——ML 用 5-fold CV，LLM 不做任何方差估计

**位置**：§3.5 Evaluation Protocol

**问题**：
- ML 模型：报告了 5-fold CV mean ± SD，以及 test set accuracy
- LLM 模型：只报告了单个 80/20 test set accuracy，没有任何方差或置信区间（DeepSeek-V3 除外，用 Wilson score interval）

论文说"Multiple random-seed repetitions would provide variance estimates; DeepSeek-V3 was evaluated with temperature=0 (deterministic API), so within-run variance is negligible..."

**问题**：
1. "within-run variance is negligible" 不等于"跨平台/跨API调用的 variance 可忽略"——DeepSeek API 本身可能有版本更新、负载变化等
2. Qwen2.5:3B 的 Ollama 推理没有任何 variance 报告
3. 没有任何 bootstrap 或交叉验证用于 LLM 结果

**顶刊要求**：TOCE / TOE 对统计严谨性要求高。审稿人会质疑：为什么不报告 LLM 的 bootstrap CI？即使 temperature=0，API 调用之间可能有微小变化。

**建议**：为 LLM 结果增加 bootstrap confidence intervals（通过对 test set 的子样本重采样，模拟 API 调用间的 variance）。

---

### M5. Few-shot 实验结果的定位矛盾

**位置**：§4.5 / §5.3

**问题**：
- Few-shot 实验结果（DeepSeek-V3: 64.55% accuracy, Macro F1=0.6266）出现在正文多个位置
- 但 few-shot 不在原始 RQ 设计中（RQ1/RQ2/RQ3 都围绕 zero-shot 比较）
- 论文在 §4.5 Key Finding 1 中说："Few-shot prompting reduces DeepSeek-V3 accuracy to 64.55% but raises Macro F1 from 0.5447 to 0.6266"

**问题**：
1. **为什么 few-shot 降低了 accuracy 却提高了 Macro F1？** 论文没有充分解释这个 trade-off
2. Few-shot 在 Main Results 表格（tab:llm-results）中没有报告，只在正文中提到——这让读者困惑：实验到底做了哪些配置？
3. "reduces accuracy" 是相对于什么？相对于 zero-shot 的 76.65%（valid only）还是 76.05%（all）？

**建议**：
- 将 few-shot 作为独立子节或至少在主表格中增加一行
- 解释 accuracy↓ + Macro F1↑ 的机制（few-shot 促使模型更均衡地分配预测，降低 WA 主导效应）

---

### M6. 图表引用链断裂

**位置**：全文

**问题**：
论文有 8 个 figure，但正文引用中存在：
1. Figure 2 的 Y 轴范围需要验证（如果 Y 轴从 0.5 开始，0.52 和 0.97 的差距会显得更大）
2. Figure 2 的 caption 说 "Four error types achieve strong F1 (≥0.89)"，但 RE F1=0.52 不在 ≥0.89 范围内——这在视觉上可能误导读者
3. 多个 figure 的 `\Description` 是事后添加的，需要验证描述是否准确对应图中内容

**建议**：逐一检查每个 figure 的 Y 轴范围，确保视觉呈现与文字描述一致。

---

### M7. Contribution 1 的"Controlled comparative study"声称夸大

**位置**：§1 Contributions

**原文**：
> "Contribution 1: **Controlled comparative study** of ML and LLM methods for verdict classification from submission metadata under identical evaluation protocols"

**问题**：
1. "identical evaluation protocols" —— 真的吗？ML 用 5-fold CV + 80/20 test，LLM 只用 80/20 test。协议并不完全 identical。
2. "controlled comparative study" —— 在计算教育顶刊语境中，"controlled" 通常意味着控制了混淆变量（学生背景、教学环境等）。本研究的"控制"只是"在同一个 test set 上评估"——这还不够严格。

**建议**：将"controlled"改为"systematic"或"standardized"，避免夸大实验设计的严谨性。

---

### M8. 结论中的方法选择建议缺乏实证支持

**位置**：§5.4, Table 6 (tab:guidelines)

**原文**：
> "Personalized tutoring: Hybrid ML + LLM"

**问题**：
- "Hybrid ML + LLM" 是论文从未验证过的配置——论文分别评估了 ML 和 LLM，但没有实现或评估两者的结合
- 这是一个推荐实践，不是研究结果
- 将未经验证的配置放在方法选择指南（Table 6）中，会误导读者认为这是有实证支持的建议

**建议**：
1. 将 Table 6 移到 Discussion 或 Limitations，明确标注为"practical recommendations (not empirically validated)"
2. 增加 hybrid 方法的实证评估，或至少承认这个推荐是推测性的

---

## 🟡 MINOR / 修辞和格式问题，不影响接受但影响阅读体验

---

### m1. Abstract 措辞过于绝对

**位置**：Abstract

**问题**：
> "CE, TLE, and MLE are platform-encoded: deterministically recoverable from execution metadata (F1 $\ge$0.89)"

"deterministically recoverable" 这个说法太强——F1=0.89 意味着有 11% 的错误率，不是"确定性"可恢复。"deterministically recoverable" 意味着 100% 准确率，但 F1=0.89 只有 89% 的精确率和召回率的调和平均。

**建议**："reliably distinguishable" 或 "highly recoverable" 替代 "deterministically recoverable"。

---

### m2. 段落开头句与前一段衔接不当

**位置**：§4.2 ML Performance, §4.3 Error Analysis

**问题**：某些段落的开头句与前一段的结尾没有清晰的逻辑衔接。例如 §4.3 开头直接进入混淆矩阵分析，但 §4.2 的结尾在讨论 BAcc，读者需要自行建立联系。

**建议**：增加过渡句，使文章逻辑更流畅。

---

### m3. Limitations 的 8 个 bullet 过长，重复信息多

**位置**：§5.7 Limitations

**问题**：Limitations 部分有 8 个 item，其中多项有重叠（Feature Set Limitations 和 Error Type Granularity 都讨论 RE 的异质性；Student-population validation 和 Theoretical CS1 baseline 重复）。

**建议**：合并重叠的 limitations，将 8 个精简为 5-6 个核心 limitation。

---

### m4. 全文缺少对"为什么只看 Codeforces"的充分论证

**位置**：§3.1 Dataset Collection

**问题**：Codeforces 是 competitive programming 平台，其判决系统与 CS1 学生环境差异巨大。论文只在 Introduction 中简要提到了 population generalizability caveat，但没有在 Methodology 中充分论证为什么 Codeforces 是研究这个问题的合适代理。

**顶刊要求**：选择单一平台作为数据源必须有充分理由，尤其是在泛化性声明重要的情况下。

**建议**：在 §3.1 增加一段，明确论证 Codeforces 作为数据集的优势（丰富的元数据、公开 API、多样化的错误类型分布），以及为什么它足以支撑本研究的 RQs。

---

## 📊 综合评估

| 维度 | 当前状态 | 顶刊要求 | 差距 |
|------|----------|----------|------|
| 理论贡献 | 平台编码边界概念有价值，但循环论证削弱 | 理论框架严密，跨平台验证 | 中等 |
| 方法严谨性 | 敏感度表错误、协议不对称 | 无错误、数据完整 | **严重** |
| 统计方法 | McNemar + Bonferroni + user-disjoint 较好 | 需 cluster-robust SE | 中等 |
| 实证证据 | 单一平台、无跨平台验证 | 至少一个跨平台验证 | 严重 |
| 写作质量 | 结构清晰但有若干逻辑断裂 | 逻辑严密、修辞精准 | 中等 |
| 图表质量 | 图表丰富但部分标注需检查 | 图表自明、无歧义 | 轻微 |

---

## 🔧 修复优先级

**P0（必须修复，否则必拒）**：
1. C2: 敏感度分析表格错误（94.24% vs 95.02%）
2. C4: IRB 豁免 + 批准编号矛盾
3. C5: Table note 乱码 `\$` 
4. C1: 循环论证（补充跨平台验证或重构框架）

**P1（强烈建议修复，否则 major revision）**：
5. M1: 5-feature vs 7-feature GB 混淆
6. M4: LLM 无 variance 估计
7. M5: Few-shot 结果定位矛盾
8. M8: 未验证的 hybrid 方法出现在 guidelines

**P2（改进阅读体验）**：
9. m1: "deterministically" 措辞
10. C3: 理论框架段落断裂
11. m3: Limitations 合并精简
