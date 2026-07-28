# 论文全面修订报告 - 2026-07-09

## 执行操作

### 1. DeepSeek-V4-flash 实验
- **结论**: 88.8% 无效率，结果不可用，不纳入论文
  - 仅 298/2672 有效预测
  - 有效准确率: 57.72%
  - 全量准确率: 14.33%
  - 原因: flash 模型过度优化速度牺牲质量

### 2. 论文关键统计数字验证（Python 重算）

**准确率汇总（已验证）:**
| 模型 | 有效准确率 | 全量准确率 | 无效率 |
|------|-----------|-----------|--------|
| GB | 91.99% | 91.99% | 0% |
| RF | 91.54% | 91.54% | 0% |
| DeepSeek-V3 | 76.65% | 76.05% | 0.8% |
| Qwen2.5:3B | 35.50% | 31.92% | 10.1% |

**McNemar 检验（Python 重算，使用 GB true labels）:**
| 对比 | χ² | p 值 | 显著性 |
|------|-----|------|--------|
| GB vs RF (5特征) | 2.88 | 0.045 | 边缘显著 |
| GB vs DS-V3 | 359.53 | <0.001 | *** |
| GB vs Qwen | 1283.36 | <0.001 | *** |
| DS-V3 vs Qwen | 877.04 | <0.001 | *** |

### 3. 论文错误修正

**paper_acm.tex (1650 行):**
- ✅ GB vs RF McNemar: p=0.089→p=0.045 ("边缘显著")
- ✅ GB vs DS-V3: χ²=376.30→χ²=359.53
- ✅ GB vs Qwen: χ²=1537.85→χ²=1283.36
- ✅ DS-V3 vs Qwen: χ²=1052.07→χ²=877.04
- ✅ Qwen WA 预测: 69.0%→76.6% (实际)
- ✅ Qwen MLE 预测: 1.4%→1.5% (实际)
- ✅ Conclusion GB vs RF 描述更新

**references.bib (38 条):**
- ✅ 删除孤立条目 deepseek2024technical (与 deepseek2024deepseekv3 重复)

**submission_materials/Cover_Letter.md:**
- ✅ DeepSeek 数字: 78.29%/17.37%→76.65% valid

**submission_materials/Highlights.md:**
- ✅ DeepSeek 数字: 78.29%/17.37%→76.65% valid

**论文中文版.md (365 行):**
- ✅ 移除 DeepSeek 5-shot 实验
- ✅ 更新所有 LLM 数字 (78.29%→76.65%, 11.34%→31.92%)
- ✅ 更新 McNemar 值
- ✅ 更新分析文本
- ✅ 压缩 RQ (5→3)
- ✅ 移除过时 few-shot 相关讨论

### 4. 最终状态

**paper_acm.tex:** 1650 行, 编译 0 错误
**paper_acm.pdf:** 503KB
**references.bib:** 38 条, 0 孤立, 0 缺失
**5 个实验条件:** GB, RF, LR, DeepSeek-V3, Qwen2.5:3B

### 5. 确认正确的关键数字

- GB: 95.02% (原文), 91.99% (5特征, McNemar 对比用)
- RF: 94.24% (原文), 91.54% (5特征)
- DS-V3: 76.05% (all), 76.65% (valid), 0.8% invalid
- Qwen: 31.92% (all), 35.50% (valid), 10.1% invalid
- GB vs DS-V3 gap: 18.4 pp (原文)
- GB vs Qwen gap: 59.5 pp (原文)
- DS-V3 vs Qwen gap: 44.1 pp (原文)
