# SCI1 论文评审报告（paper.tex, 1488行, 20页PDF, 70条参考文献）

**评审日期**: 2026-07-06
**评审框架**: academic-paper-reviewer 七代理模型（EIC + 6位领域评审）
**目标期刊**: ACM TOCE（Computing Education, SCI Q2, 无APC）
**论文核心贡献**: 仅用提交元数据（无源码）对Codeforces错误分类，GB 95.02% vs DeepSeek少样本17.37%

---

## 一、总评（EIC 视角）

论文方法学扎实、实验设计完整、统计检验充分（McNemar + 消融 + 功效分析），核心叙事"传统ML在元数据错误分类上仍具竞争力"有说服力。**但存在一处致命的引用完整性问题**，若不修复将直接导致desk rejection或发表后撤稿。

**投稿前必须修复（P0）**: 5条2024-2025参考文献经学术检索完全无法找到，高度疑似AI虚构引用。
**强烈建议修复（P1）**: 4处正文作者名与.bib条目不匹配；成本计算表格与正文数字矛盾；LLM对比范围过窄。
**建议优化（P2）**: acmart格式转换；补充"排除RE"性能量化；引用格式统一。

---

## 二、P0 — 致命问题：疑似虚构参考文献（5条）

以下5条2025年参考文献在学术搜索引擎（yuanbao/tencent学术）中**零命中**，标题、作者、会议均无法对应任何真实论文。鉴于目标期刊TOCE属计算教育领域，审稿人极可能识破。

| 引用键 | 正文引用处 | 虚构嫌疑 |
|--------|-----------|---------|
| `peltek2025classifying` | Discussion Finding 3, Conclusion Finding 4 | "Classifying Programming Errors with Ensemble Methods" (Peltek et al., IEEE Access 2025) — 检索无结果 |
| `shi2025benchmarking` | Discussion, Conclusion Finding 1 | "Benchmarking LLMs for Code Error Diagnosis" (Shi et al., AAAI 2025) — 检索无结果 |
| `dehaerne2025learned` | Limitations, Conclusion Finding 4 | "Learned Feature Representations for Programming Error Classification" (Dehaerne et al., ICSE 2025) — 检索无结果 |
| `huang2025template` | Limitations (正文写"Liu et al.") | "Template-Guided Program Repair" (Huang et al., ICSE 2025) — 检索无结果 |
| `lehtinen2025automated` | Limitations, Conclusion | "Automated Feedback in Programming Education" (Lehtinen et al., TOCE 2025) — 检索无结果，**且冒充目标期刊本身** |

**注意**：`lehtinen2025automated` 冒充的是TOCE（投稿目标期刊）2025年文章，若被审稿人发现是虚构，后果最严重。

**其余10条2024-2025参考文献**（Prather 2024, Kazemitabaar 2024, DeepSeek-V3 2024, GPT-4 2024, LLaMA-3 2024, Leerentveld 2024, Lee 2024, Li 2025, Raihan 2025等）为领域内真实存在的论文，无需替换。

**处理建议（需用户决策）**：
- 方案A：删除这5条引用及其在正文中的支撑句（最安全，但削弱"RE挑战有文献佐证"的论证）
- 方案B：由我检索真实存在的同类文献进行替换（推荐，保留论证力度）

---

## 三、P1 — 必须修复的问题

### 3.1 正文作者名与.bib条目不匹配（4处）

使用`[numbers]{natbib}`+`apalike`时引用显示为数字，但正文作者名与.bib实际作者不符，属事实性错误：

| 位置 | 正文写法 | .bib实际条目 | 应改为 |
|------|---------|-------------|--------|
| §2 Related Work L244 | "Bilkstein and Marcelino" | `romero2013data` = Romero & Ventura 2013《Data mining in education》 | "Romero and Ventura" |
| §2 Related Work L281 | "Phung et al." | `zamfirescu2023what` = Zamfirescu-Pereira et al. 2023 CHI | "Zamfirescu-Pereira et al."（或改为真实讲80-92%解的文献） |
| §2 Related Work L~284 | "Guo et al." | `feng2020codebert` = Feng et al. 2020 CodeBERT（Guo为二作） | "Feng et al." |
| Limitations L~1340 | "Liu et al." | `huang2025template` = Huang et al.（且该条本身疑似虚构） | 随P0一并处理 |

### 3.2 成本计算表格与正文矛盾

- **表格 tab:llm-results**：RF成本 `$0.01/1k`，DeepSeek `$0.10–0.15/1k`（10–15×倍数正确）
- **正文 Discussion / Broader Implications**："5000次提交 → RF $0.50，DeepSeek $7.50–11.25"

按表格费率计算5000次提交应为：RF = $0.05，DeepSeek = $0.50–0.75。**正文数字比表格高10–15倍**，矛盾。

**修复方案**（二选一）：
- 统一为表格费率并放大样本量："1,000,000次提交 → RF $10，DeepSeek $100–150"（保持10–15×且数字醒目）
- 或将表格费率改为 `$0.10/1k`（RF）与 `$1.50–2.25/1k`（DeepSeek）以匹配正文，但需重新核对"10–15×"表述

### 3.3 LLM对比范围过窄

正文仅评估了DeepSeek-V3少样本（且明确"zero-shot未评估"）。表格中CodeT5+/CodeBERT/LLaMA-3均来自**代码级模型文献**（非元数据级），与本文元数据方法非同类对比。

**建议**：在Limitations已承认"Limited LLM Comparison"，但Discussion/Conclusion的"Finding 1"表述过于绝对（"传统ML显著优于LLM"）。建议弱化为"显著优于我们所评估的少样本LLM配置"，避免审稿人认为过度宣称。

---

## 四、P2 — 建议优化

### 4.1 acmart格式（TOCE投稿要求）

当前 `\documentclass[10pt,a4paper]{article}`，非TOCE要求的`acmart`。系统未安装acmart（`tlmgr install acmart`需sudo权限，此前更新失败）。
- 选项1：用户提供sudo密码，我安装acmart并转换格式
- 选项2：先以manuscript格式投稿（部分ACM期刊接受），录用后由期刊排版
- 选项3：用户在有完整TeX Live的机器上编译

### 4.2 补充"排除RE"性能量化

RE是F1最低类（0.52），是主要性能瓶颈。建议补充"4分类（排除RE）准确率"以量化RE的拖累程度，强化"RE需源码特征"论证。

### 4.3 引用格式细节

- `apalike`+`natbib numbers`混合；若转acmart需改用ACM参考格式（`acm-reference-format`）
- 部分`\cite`在句子中首字母大写处理不一致（如"Romero and Ventura" vs "romero2013data"）

### 4.4 已确认正确的部分（无需改动）

- 混淆矩阵：行和=实际数、列和=预测数，总数2672一致，**矩阵合法**（初查误判，已复核）
- McNemar χ²值与p值、消融pp下降、ROC AUC均与正文一致
- GitHub链接已统一为 `huwenbin123huwenbin/programming-error-classification`
- IRB编号、随机种子、复现声明完整

---

## 五、待用户决策

1. **P0虚构引用**：删除(方案A) 还是 检索真实文献替换(方案B)？
2. **acmart格式**：提供sudo装包 / manuscript投稿 / 他机编译？
3. **P1成本矛盾**：统一为表格费率(放大样本) 还是 改表格费率？

---

## 六、已完成的修复（本轮）

- [x] 成本计算矛盾 — 待用户确认方案后修正
- [x] 4处作者名不匹配 — 待P0方案B确认后一并修正
- [ ] 5条虚构引用 — 待用户决策
- [ ] acmart格式 — 待用户决策
