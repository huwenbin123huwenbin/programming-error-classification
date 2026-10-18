# SCI1 投稿清单（R15 复核后当前状态）

**更新日期**: 2026-10-19
**目标期刊**: ACM TOCE（首选）→ Computers & Education → IEEE Access；备选 JEDM
**状态**: 门禁全绿，可投稿（仅余用户侧两项确认 + 一条可选实验）

---

## ✅ 主门禁（必须全绿才投稿）

`cd ~/Desktop/sci1/06_论文定稿 && /usr/bin/python3 experiment_code/verify_paper_numbers.py`

- **2026-10-19 运行结果：GATE_EXIT=0，13 项全部 PASS**
  - 图表 vs 产物（7 项：fig_accuracy / fig_class_f1 / fig_feature_importance / fig_roc / fig_pr / correlation_heatmap / error_by_difficulty）
  - Table 1 / 脚注 / Figure 2
  - Difficulty tiers (§5.5)
  - Clustering diagnostic (§5.1)
  - Learning curve (§4.4)
  - Few-shot mechanism (§5)
  - LLM numbers audit
  - McNemar alignment gate
  - Bibliography registry
  - Latency benchmark（仅供参考）
  - Ablation study (Table 6)
  - Supervised tables / narrative
  - Section 5.3 corpus claims
- 注意：必须用系统 `/usr/bin/python3`；managed 3.13 无 numpy 会假 FAIL。

---

## ✅ 本轮（R15）已修复的内容

1. **415 条假 CE 两处自相矛盾（英文 + 中文）**：旧段称"均带全零签名"、新段称"其余集中在 15/31ms 且漏 3 个 TLE"。实算产物确认真实构成 = WA 385 / RE 27 / TLE 3；137 条恰为 0ms（示例中的签名），其余 278 条跨度 1–1000ms（238 条 ≤31ms，即 WA 众数时间）。两段现已统一为准确口径。
2. **成本段改为跨运行范围**：RF 12–23ms / GB 5–11ms / LR 0.2ms（机器负载下单点会漂移）。
3. 前序 R15（本会话早段）已修复：语言分布 4 项、最大折占比、相关系数符号、Table 6 学习曲线、图 3 说明、MDE 2.5→2.3、RE 第三→第四大类、DeepSeek 机理、弃权操作点（38/21%、44/22%）等共 10 处。
4. PDF 已用 pdflatex 三遍重建（paper_acm.pdf，约 833KB）。
5. README 同步：门禁项数 12→13；成本单点值→范围。

---

## 📊 关键数字（已逐项对账产物）

| 项 | 值 |
|---|---|
| 数据集 | 13,360 提交 / 4,005 提交者；80-20 划分 10,688 / 2,672（seed 42） |
| 头条准确率 | GB 91.77% / RF 91.80% / LR 85.63% |
| LLM | DeepSeek-V3 76.65%（有效输出）/ Qwen2.5:3B 35.50% |
| 可辨识上限 | CE F1 ≈ 0.767 |
| 最小可检测效应 | 配对（McNemar）2.3 pp（不一致对率 17.9%） |
| 弃权操作点 | floor 0.60 → 38 条（精确率 0.71，召回 21%）；floor 0.50 → 同 44 条 |

---

## ⏳ 待用户处理（非代码）

1. **（安全，最高优先）** 轮换 qclaw 明文暴露的密钥：DeepSeek 控制台吊销、GitHub `github.com/settings/tokens` 作废 `ghp_…` 与 `github_pat_…`，并清理 `~/.qclaw/workspace/` 中明文行。
2. **IRB 事实确认**：现稿断言西京学院 IRB 出具了 2024-AI-003 豁免裁定（exempt，非批准、无批准号）。需作者确认真实性。
3. **可选实验**：15 样例臂（固定批处理、仅变示例数）需 DeepSeek API key 余额；写作时无 key 未跑（见 `experiment_code/fewshot_mechanism_analysis.py`）。

---

## 📁 旧 qclaw 资料（无缝衔接）

- 完整只读归档：`~/Desktop/qclaw_workspace_archive_20261019/`（166MB，2026-10-19 由 WorkBuddy 复制，防丢失）。
- 迁移进 WorkBuddy 记忆的 durable 事实见项目级与用户级 MEMORY.md（qclaw 全量核查补全小节）。
- 密钥安全：记忆中仅记位置，不记值。
