# SCI1 论文第5轮修订完成

**时间**: 2026-07-26 00:30
**任务**: 替换旧文献为近5年（2020-2025）+ 增加图表

## 完成工作

### 1. 文献替换（107篇，52.3%近5年）

**新增13篇近期文献**（全部2020-2025，Crossref验证）：
- Crockett et al. 2023 — CS1学生保留率 (IEEE FIE)
- van der Heyden et al. 2025 — Python新手错误模式 (CSEDU)
- Fwa 2024 — 新手编程误解识别 (SIGCSE)
- Albrecht & Grabowski 2020 — 编程错误与粗心 (SIGCSE)
- Soni et al. 2025 — 学生表现预测EDM (ICAART)
- Tang & Sian 2025 — 学生表现预测 (Scientific Programming)
- Groher et al. 2024 — 学习分析仪表板 (CSEDU)
- Ramaswami et al. 2023 — 仪表板有效性 (JLA)
- Irons & Elkington 2021 — 形成性评估技术 (Routledge)
- Kokinda et al. 2024 — 自我效能与编程结果 (CSEDU)
- Román-González & Pérez-González 2024 — 计算思维评估 (MIT Press)
- Yuen 2021 — 大规模CT评估 (AERA)
- Höll & Kufer 2025 — LLM代码生成评估 (IEEE FLLM)

**替换策略**：
- **保留理论经典**：McNemar 1947、Cohen 1988、Breiman 2001、Hattie 2007、Bandura 1997
- **替换实证文献**：Bennedsen 2007 → Crockett 2023、Spohrer 1986 → Fwa 2024、Baker 2009 → Soni 2025 等
- **正文引用更新**：14处替换，涉及引言、相关工作、自我效能、LLM对比等段落

### 2. 新增图表（3个）

**Figure: Feature Correlation Matrix**
- 位置：Dataset部分，Table 1后
- 内容：5×5特征相关性热力图（Time、Memory、User Success Rate、Problem Rating、Language）
- 关键发现：Time-Memory r=0.32、Memory-Language r=0.17

**Figure: Error Type Distribution by Difficulty**
- 位置：Dataset部分，Table 1后
- 内容：堆叠条形图展示不同难度级别的错误分布
- 关键发现：Novice WA 79% → Expert WA 41%，Expert RE/TLE/MLE显著增加

**Figure: Model Performance Comparison**
- 位置：Statistical Significance部分，McNemar表后
- 内容：双面板图（Accuracy + Macro F1）对比5个模型
- 关键发现：ML（RF 94.24%、GB 95.02%）>> LLM（DeepSeek 76.65%、Qwen 31.92%）

### 3. 最终统计

| 指标 | 值 |
|------|-----|
| 总引用 | 107篇 |
| 近5年（2020-2025） | 56篇（52.3%）✓ |
| 近3年（2023-2025） | 37篇（34.6%）|
| PDF页数 | 32页 |
| 文件大小 | 938 KB |
| 编译错误 | 0 |
| 未定义引用 | 0 |

### 4. GitHub同步

✓ paper_acm.tex
✓ references.bib
✓ figures/correlation_heatmap.pdf
✓ figures/error_by_difficulty.pdf
✓ figures/model_comparison.pdf

## 剩余工作

- P3: ScholarOne注册投稿（用户手动）
- P3: GPT-4补充实验（需API费用）

## 文件位置

- 论文：`/Users/mac/Desktop/sci1/06_论文定稿/paper_acm.tex`
- 引用：`/Users/mac/Desktop/sci1/06_论文定稿/references.bib`
- 图表：`/Users/mac/Desktop/sci1/06_论文定稿/figures/`
- PDF：`/Users/mac/Desktop/sci1/06_论文定稿/paper_acm.pdf`（32页，938KB）
