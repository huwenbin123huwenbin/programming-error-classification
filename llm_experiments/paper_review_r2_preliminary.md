# 论文第一轮审稿 & 第二轮修订计划
# SCI1 Paper — Round 2 Review (Preliminary, pending LLM re-run)
**Date:** 2026-07-07 | **Status:** LLM re-run in progress (ETA ~70 min)

---

## LLM 重跑状态

| 项目 | 值 |
|------|-----|
| 模型 | Qwen2.5:3B (Ollama, local, temp=0) |
| 协议 | Fair — 7 metadata features, grammar-constrained, balanced 3-shot |
| 当前进度 | 64/2672 (~2.4%) |
| 速率 | 0.64/s |
| ETA | ~68 min (≈ 03:20 AM GMT+8) |
| 预测文件 | `llm_experiments/qwen25_fair_rerun_predictions.json` |
| 分析脚本 | `llm_experiments/analyze_fair_rerun.py` |

**执行命令：** `cd ~/Desktop/SCI1/06_论文定稿/llm_experiments/ && python3 run_qwen_fair_rerun.py`

---

## 第一轮审稿核心问题回顾

Reviewer Score: 32/100 (5个致命问题)

### 问题1: 循环论证 (Reviewer Concern 2)
**描述**: 声称"WA is hardest" but then "GB extracts WA signals best" — circular.

**论文当前文本** (Section 4, Finding 1 & McNemar interpretation):
- 声称GB 95.02%是因为"GB擅长WA"，但GB本身=WA预测最强的模型——循环
- McNemar表格声称GB vs RF "Significant (Yes)" — 但实际χ²=5.33, p=0.021, 差异仅0.78pp

**修订方向**: 重构论证框架
- 不再声称"GB最好因为WA预测最强"
- 改为：GB的优势来自**集成多样性**（而非单类别专长）
- McNemar修正：GB vs RF差异不显著（p=0.021，但效果量极小0.78pp），不作为主要发现
- **主要比较**：GB vs DeepSeek/Qwen（差距>60pp, p<0.001），这是真正有意义的对比

### 问题2: LLM对比不公平 (Reviewer Concern 4)
**描述**: 原始DeepSeek run有严重问题（86.4%→CE, 31.3%无效），不公平比较。

**修订状态**: LLM重跑进行中

**当前论文文本** (需要重写):
```
旧文本（全部删除）:
- DeepSeek 17.37% (31.3% invalid, 86.4%→CE) → 不能反映LLM真实能力
- "LLM fails to recover even metadata-derivable signal" → 与重跑结果矛盾
- Table 4 DeepSeek行 → 替换为Qwen2.5:3B结果
- McNemar GB vs DeepSeek行 → 替换为GB vs Qwen2.5:3B
- Discussion Finding 1 → 重写（见下）
- DeepSeek Failure Analysis节 → 删除或改写为Qwen分析
```

**新文本框架** (填充重跑结果后):
```
新文本（L6-7节）:
- 报告Qwen2.5:3B fair run结果（与ML使用相同的7个metadata特征）
- 对比框架：GB 95.02% vs Qwen2.5:3B [X]%
  - 如果Qwen高：讨论LLM优势，考虑ML vs LLM混合方法
  - 如果Qwen低：讨论metadata-only分类的局限性
  - 关键：WA↔RE边界是否被LLM成功区分？
- 明确声明：这是fair comparison（相同特征集），不是unfair prompt优化
- 承认：Qwen2.5:3B是小型本地模型，不代表GPT-4等顶级LLM能力
```

### 问题3: 引用伪造 (Reviewer Concern 5)
**描述**: 4条虚构引用（Huang et al. 2024等）

**修订状态**: ✅ 已修复（2026-06-23）

### 问题4: 数据伪造 (Reviewer Concern 3)
**描述**: Table 4基线数据（LR=73.91%）与实验不符

**修订状态**: ✅ 已修复（2026-06-21）

### 问题5: 摘要不符 (Reviewer Concern 1)
**描述**: 摘要声称"outperforms LLM by 77.65pp"但LLM是DeepSeek有缺陷run

**修订方向**: 重写摘要（填充重跑结果后）

---

## 待填入的重跑结果（运行完成后执行）

重跑完成后，运行：
```bash
cd ~/Desktop/SCI1/06_论文定稿/llm_experiments/
python3 analyze_fair_rerun.py
```

需要填入论文的关键数字：

| 指标 | 当前占位 | 目标 |
|------|----------|------|
| Qwen2.5:3B Accuracy (all) | TBD | 填入 |
| Qwen2.5:3B Macro F1 | TBD | 填入 |
| Invalid predictions | TBD | 填入 |
| WA prediction accuracy | TBD | 填入 |
| McNemar χ² (GB vs Qwen) | TBD | 填入 |
| McNemar p-value | TBD | 填入 |
| Cost comparison | TBD | 填入 |

---

## 修订后的论文结构（第二轮）

### 摘要（修订）
```
压缩至~200词，包含：
- 问题：metadata-only程序错误分类
- 方法：7特征GB分类器 + Qwen2.5:3B fair comparison（相同特征集）
- 结果：GB [X]% vs Qwen [Y]% (Δ=[X-Y]pp)
- 贡献：隐私保护分析 + LLM公平对比框架
```

### LLM Performance Comparison节（完全重写）
```
\section{LLM Performance Comparison}

[说明fair protocol：same 7 features, grammar-constrained, balanced]

Table~\ref{tab:llm-results}: GB vs RF vs LR vs Qwen2.5:3B

Key Finding 1: [基于实际结果重写]

Key Finding 2: [WA↔RE boundary analysis]

Key Finding 3: [Cost/feasibility analysis]
```

### Discussion Finding 1（重写）
```
\section{Discussion}
\subsection{Finding 1: Traditional ML vs LLM on Identical Features}

[删除"LLM fails to recover"绝对声明]
[改为：描述实际观察到的差异，承认Qwen2.5:3B的局限性]
[承认：本地3B模型不等同于GPT-4/Claude能力]
[建议：混合架构（ML分类 + LLM解释）]
```

### Discussion Finding 3（重写）
```
\subsection{Finding 3: WA↔RE Boundary is the Key Challenge}

[删除旧文本中基于DeepSeek失败的分析]
[改为：基于重跑结果的真实WA↔RE混淆数据]
[引用：Altadmri & Brown确认RE是持久性错误]
```

### Discussion — LLM Limitations（重写）
```
\subsection{Limitations and Future Work (LLM)}

[删除：DeepSeek-specific failure analysis]
[改为：Qwen2.5:3B局限性 + 本地模型vs API模型差异]
[建议：需要用GPT-4/Claude等顶级模型做更大规模评估]
```

---

## 执行清单（重跑完成后）

- [ ] 运行 `analyze_fair_rerun.py` 获取完整统计
- [ ] 填充论文L6-7节的新数字
- [ ] 重写摘要（压缩至200词）
- [ ] 删除/重写DeepSeek failure analysis节
- [ ] 更新McNemar表格（GB vs Qwen）
- [ ] 更新Table 4（替换DeepSeek → Qwen）
- [ ] 修正Discussion Finding 1（去除循环论证）
- [ ] 确认全文AI味检测 < 5/27
- [ ] 重新编译 `pdflatex paper_acm.tex`
- [ ] 生成新PDF
