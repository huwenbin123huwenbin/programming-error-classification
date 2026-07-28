# 论文审稿报告 - 2026-07-09

## 审查范围
- paper_acm.tex (1650行, 27页, 0编译错误)
- 所有数据通过 Python + 原始预测 JSON 交叉验证

---

## ✅ 验证通过

| 检查项 | 状态 |
|--------|------|
| paper_acm.tex 旧数字 (17.37/78.29/81.64) | ✅ 0处残留 |
| references.bib (38条, 完美匹配) | ✅ |
| \ref{} 标签完整性 | ✅ 全部定义 |
| DeepSeek-V3 per-class F1 (WA=0.85, TLE=0.84, CE=0.49, MLE=0.51, RE=0.03) | ✅ 全部验证 |
| Qwen per-class F1 (WA=0.48, RE=0.07) | ✅ 全部验证 |
| Qwen WA低估 (29.8% vs 76.6% actual) | ✅ 验证: 715/2403=29.8% ✓ |
| DS-V3 RE误判WA (82/127 valid) | ✅ 验证: 131 total, 127 valid, 82 WA ✓ |
| DS-V3 0.8% invalid (21/2672) | ✅ 验证 |
| Qwen 10.1% invalid (269/2672) | ✅ 验证 |
| DS-V3 76.05% all / 76.65% valid | ✅ 验证 |
| Qwen 31.92% all / 35.50% valid | ✅ 验证 |
| GB 95.02%, RF 94.24%, LR 73.91% | ✅ 验证 |
| McNemar GB vs DS-V3 χ²=359.53 | ✅ Python重算验证 |
| McNemar GB vs Qwen χ²=1283.36 | ✅ Python重算验证 |
| McNemar DS-V3 vs Qwen χ²=877.04 | ✅ Python重算验证 |
| McNemar GB vs RF χ²=2.88, p=0.045 | ✅ Python重算验证 |
| Ablation time_consumed 8.8pp | ✅ JSON验证 |
| Confusion matrix RF (CE=196, MLE=40, RE=131, TLE=258, WA=2047) | ✅ JSON验证 |
| 编译状态 | ✅ 0错误 |

---

## ⚠️ 需要修改的问题

### 1. [中等] 18.4pp gap 与 McNemar 使用不同基准

**问题**: Key Finding 1 和 Conclusion 中说 "18.4pp gap"，是用 7-feature GB (95.02%) 与 5-feature LLM (76.65%) 计算的：
- 95.02 - 76.65 = **18.4pp** ← 文本使用

但 McNemar 检验使用的是 5-feature GB (92.0%)：
- 92.0 - 76.65 = **15.4pp** ← McNemar 实际比较

**建议**: 在 gap 数字旁加注，或统一使用同一基准。例如：
> "Neither closes the 15.4pp gap (McNemar, 5-feature GB vs DS-V3) to ML" 

或在脚注中说明："GB 95.02% (7-feature) 用于准确率比较；McNemar 使用 5-feature GB 变体 (92.0%) 以确保 ML-LLM 公平对比。"

### 2. [中等] 5-feature GB 变体未说明具体特征

**问题**: McNemar 表提到 "5-feature GB variant (92.0%)"，但全文未说明哪两个特征被移除。

**建议**: 在 Evaluation Protocol 或 McNemar 节添加：
> "For the ML-LLM McNemar comparison, we retrained GB using only the five features available to the LLMs (problem_rating, language, time_consumed_ms, memory_kb, passed_test_count), yielding 92.0% accuracy."

### 3. [轻微] "82 of 127" 表述歧义

**问题**: "predicting WA for 82 of 127 true RE cases" — 读者可能误以为测试集只有127个RE样本（实际131个）。

**建议**: 
> "predicting WA for 82 of the 127 valid RE predictions (out of 131 total RE cases)"

---

## 📝 审查意见总结

### 优点
1. **方法论清晰**: 三方对比 (GB vs DeepSeek-V3 vs Qwen) 结构合理
2. **数据真实**: 所有声称数字均通过 Python + JSON 交叉验证，无虚构数据
3. **统计完整**: McNemar + Ablation + Bootstrap CI + Confusion Matrix 全套
4. **理论支撑**: Hattie & Timperley + Bandura 框架有机整合
5. **讨论深入**: WA↔RE 元数据天花板定位精准，有教育意义
6. **Limitation 诚实**: 明确承认只测了两个 LLM，未测 GPT-4/Claude

### 建议（非必须，可提升质量）
1. **DeepSeek-V4-flash 负面结果**: 作为 Limitation 中 "并非所有 LLM 优化都有效" 的证据
2. **5-feature 模型命名**: 如 "GB-5f" / "RF-5f" 便于文中引用
3. **Figure 清晰标注**: 确保所有图的 legend 在 PDF 放大后仍可读

---

## 最终状态
- **编译**: 27页, 0错误, 503KB ✅
- **数字一致性**: 全部验证 ✅
- **引用完整性**: 38/38 完美匹配 ✅
- **逻辑一致性**: 2处中等歧义 (gap vs McNemar, 5-feature未说明)
