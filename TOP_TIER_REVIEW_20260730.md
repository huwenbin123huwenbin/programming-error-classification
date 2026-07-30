# SCI1 顶刊水平评审报告（2026-07-30）

**目标期刊语境**：TOCE（ACM Transactions on Computing Education）是计算教育领域旗舰期刊（SCI Q2，IF≈2.8）。若对标更高影响因子，Computers & Education（Elsevier，Q1，IF≈8.3）是更宽口径的教育技术顶刊。两者对"核心贡献新颖性 + 方法严谨性 + 教育相关性的实证支撑"要求都很高。

---

## 一、本轮已完成的修复（P0 结构与诚实性）

| # | 问题 | 状态 |
|---|------|------|
| 1 | 摘要重复句 "The WA↔RE boundary is not separable..." 出现 3 次 | ✅ 已清理为 1 次 |
| 2 | Related Work 孤立 "Jadud" 行 | ✅ 已确认原文件无此问题（前期已修） |
| 3 | §4.1 断裂的 few-shot 句子（本应只在 LLM 段出现） | ✅ 已删除重复体 |
| 4 | §4 方差句尾部重复 "LLM performance; this is a limitation..." | ✅ 已清理 |
| 5 | 成本段尾部断裂 "classifications (no API call)..." | ✅ 已清理 |
| 6 | 结论段悬空碎片 "learning (ML) and large language model..." | ✅ 已删除 |
| 7 | "source-code analysis is necessary/becomes necessary" 当作已证实事实 | ✅ 改为假设/下一步（数据无源码，不能当结论） |
| 8 | "a student receiving a CE verdict benefits from..." 因果式断言 | ✅ 改为 "we hypothesize...remains to be validated in a classroom study" |

编译验证：28 页 / 0 errors / 0 overfull / 811KB PDF。

---

## 二、论文当前的真实强项（顶刊审稿人会认可）

1. **问题定义清晰**：platform-encoding boundary 的分解（CE/TLE/MLE 由平台阈值定义 vs WA↔RE 无执行特征）是一个干净、可证伪的框架。
2. **方法严谨性已大幅提升**：McNemar + Bonferroni / Holm-Bonferroni 多重比较校正、ablation、LOUO、Student-Proxy、公平性护栏均已具备；统计报告达到 CER 顶刊标准。
3. **诚实的 ML–LLM 框架**：已明确"监督 ML（10k 标注）vs 零样本 LLM"是不对称部署对比，并报告了同特征 GB 对照（92.0%）。这一处理规避了最常见的"苹果对橘子"审稿意见。
4. **伦理护栏**：平台编码边界对资源薄弱院校学生的危害 + 三条部署护栏，是 CER 审稿人加分项。

---

## 三、阻挡"顶刊"的四类核心问题（按致命度排序）

### ★★★ P0 — 最核心新颖性被"构造性平凡"削弱
**问题**：CE（time=0）、TLE（time=limit）、MLE（memory=limit）这三类判决，本质上就是由定义它们的元数据值决定的。说"用执行时间/内存能分类 CE/TLE/MLE"，等价于"用温度计读数判断温度是否 >100°C"——这是构造性平凡（trivial by construction）。

论文 95.02% 的准确率由三部分构成：
- WA 多数类（测试集 76.6%，F1=0.97）—— 无需模型也能高准确
- 三个阈值定义类（共 18.4%）—— 由构造决定可恢复
- WA↔RE —— **所有方法都失败**（RE F1=0.52）

**审稿人必问**："真正有科学价值的问题是 WA 能否与 RE 分开——而 ML 和 LLM 都答不出。那这篇论文的 novel contribution 到底是什么？"

**可选解法**：
- (A) **补一个源码基线实验**（最高杠杆，见下）——把"边界"从"限制"变成"被实证确立的发现"；
- (B) **重框贡献为 characterization/feasibility 研究**：明确声明"本文不是性能突破，而是首次系统刻画元数据能/不能支撑哪些判决分类，并为部署划界"。当前摘要/引言已朝此方向，但标题与贡献(2)仍带"performance"味。

### ★★★ P0 — "源码分析必要"从未被验证（最大方法空洞）
**问题**：全文 6+ 处说"WA↔RE 需要源码分析"，但**数据集根本没有源码**（仅元数据；`01_原始数据/codeforces_*.csv` 列：submission_id / verdict / time / memory / passed_test_count / problem_rating / language，无 source code 列）。论文断言了一个从未测试过的主张。

**顶刊审稿人必杀**："你说源码能解决 WA↔RE，怎么证明？你试过吗？" 答"没试过" = 核心主张悬空。

**解法**：
- (A) **重新采集源码并重跑**（见下，多日工程）；
- (B) 若不做实验，必须全文改为**假设/未来工作**语气（已部分完成），并在 Limitations 明确写"我们未采集源码，故'源码可解 WA↔RE'是待验证假设，非本文结论"。这一点当前 Limitations 是否写清需要确认。

### ★★ P1 — 教育相关性是"设计推演"而非"实证"
**问题**：Hattie/Timperley、Bandura 的引用用于推导"某判决→某反馈最有行动性"，但全文**无任何学生、无学习产出、无部署反馈研究**。L468–480 已诚实标注"causal validation would require a controlled study...beyond the scope"，这是对的；但标题/贡献/结论仍用"educational utility""pedagogical actionability"作为卖点，风险在于审稿人期待教育实证。

**解法**：将教育部分统一标为 **design implications / hypotheses grounded in established theory**，而非 demonstrated effects。当前已改 CE 句为假设；建议通读确认"pedagogically actionable / educational utility"等词不暗示已实证。

### ★★ P1 — 外部效度（竞争程序员 ≠ CS1 学生）
**问题**：数据来自 Codeforces（rating 800–3500）竞争程序员。技能分层（novice 96% / advanced 88.5%）是学生代理的弱替代。CER 顶刊会强推外部效度。

**解法**：
- 在引言/局限明确"本研究定位为竞争编程教育（许多课程用 CF 训练），而非声称泛化到 CS1"；
- 将"学生"表述改为"学习者/编程者"，降低过度泛化暗示。

---

## 四、最高杠杆行动：源码基线实验（决定能否真正"顶刊"）

**为什么它是 game-changer**：若能为这 13,360 条提交**补采源码**并训练一个轻量源码模型（如 CodeBERT 嵌入 + 同一 GB 分类头），并证明它在 **WA↔RE 上显著超过元数据模型（RE F1 从 0.52 → 例如 0.75+）**，则：
- "platform-encoding boundary" 从"限制"变成"被实证确立的边界条件"；
- 论文核心贡献升级为：**首次实证界定元数据 vs 源码各自的能力边界**；
- 彻底消除"你凭什么说源码必要"的审稿死穴。

**可行性评估（关键障碍）**：
- 数据：当前 CSV **无源码列**，需从 Codeforces API 按 submission_id 重新抓取源码（13,360 条，需处理 API 限速；部分提交可能已不可见）；
- 模型：CodeBERT（~500MB）+ PyTorch，Intel Mac 无 GPU，13k 条 CPU 推理提取嵌入可行（数小时），训练分类头较快；
- 工作量：数据重采（1–2 天）+ 建模（0.5–1 天）+ 写作（0.5 天）。

**替代（不重采数据）**：用已有 verdict + 题目文本（problem_name/problem_index）作为"弱源码代理"训练文本模型，至少能部分验证"非元数据信号能否分离 WA↔RE"。但弱于真源码。

---

## 五、可立即执行的轻量提升（无需新实验）

1. **标题去"performance"味**：当前标题 *"Automated Programming Verdict Classification from Submission Metadata"* 已偏中性，OK；但可考虑加 "boundary" 或 "what metadata can and cannot tell us" 以匹配真实贡献。
2. **贡献列表收敛**：6 条贡献有重叠（(1)对比/(4)指南/(6)开源框架 偏工程；(2)(3)(5)偏科学）。顶刊偏好 3–4 条紧致、非重叠贡献。建议合并为：(1) platform-encoding boundary 的实证刻画；(2) WA↔RE 元数据不可分性的确立；(3) 执行时间主导 + ablation；(4) 部署指南（含公平性护栏）。
3. **AI 味/ hedge 密度**：全文仍偏多 "We note that""provides a rich signal""it is worth noting"。顶刊偏好断言式、低 hedge 学术语体。可过一遍 ai-check。
4. **Related Work 冗余**：4 个子节部分重叠，可压缩以腾出篇幅给 Discussion 的方法论辩护。

---

## 六、优先级总表

| 优先级 | 动作 | 是否需新数据/实验 | 对顶刊影响 |
|--------|------|------------------|-----------|
| P0 | 补源码基线实验（证明 WA↔RE 可被源码分离） | 是（重采+建模） | ★★★★★ 决定性 |
| P0 | 全文将"源码必要"统一为假设语气 + Limitations 明示未测 | 否 | ★★★★ 消除死穴 |
| P1 | 教育部分统一标为 design implications/hypotheses | 否 | ★★★ 规避期待落差 |
| P1 | 外部效度明确定位（竞争编程教育，非 CS1 泛化） | 否 | ★★★ |
| P2 | 贡献列表收敛为 3–4 条 | 否 | ★★ |
| P2 | AI 味/hedge 密度清理 | 否 | ★★ |
| P2 | Related Work 压缩 | 否 | ★ |

---

## 七、建议的下一步（需用户决策）

**路径 A（冲顶刊，工作量最大）**：执行源码基线实验（§四）。这是唯一能把"边界"从限制变成实证贡献的动作，也是消除"源码必要"死穴的唯一根本解法。预计 2–4 天。

**路径 B（稳健发表，工作量小）**：保持元数据 characterization 定位，把"源码必要"彻底改为假设语气 + Limitations 明示，收敛贡献、清理教育措辞与 AI 味，直接投 TOCE（已达标）或 Computers & Education。预计 0.5–1 天。

**路径 C（折中）**：先做路径 B 的轻量提升并投稿；源码实验作为后续 "boundary extension" 论文。
