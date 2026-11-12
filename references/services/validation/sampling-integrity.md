# 样本完整性验证

本服务检查样本建议的输入、计算和外推说明。具体规划方法见 [样本规划](../sample-planning.md)。

触发条件：交付物包含样本量、配额、邀约量、样本框架或样本代表性说明时执行。

## 规则

| rule_id | 检查 | 默认严重程度 |
|---|---|---|
| `sampling.population-defined` | 明确目标总体、样本来源、纳入条件和排除条件 | `warning` |
| `sampling.analysis-aligned` | 样本量建议与拟议分析和最小比较单元一致 | `warning` |
| `sampling.parameters-documented` | 精确建议列出输入参数、计算依据、有效样本和损耗假设 | `error` |
| `sampling.no-unfounded-number` | 参数不足时，不使用无依据的常见数字代替规划 | `error` |
| `sampling.project-number-labeled` | 项目已给出的目标数字标记为项目建议或执行约束，不伪装成统计计算结果 | `warning` |
| `sampling.complex-method-params` | MaxDiff、联合分析、分群、驱动模型和重复测量按各自设计参数判断，不套用统一阈值 | `error` |
| `sampling.quota-purpose` | 结构配额和分析配额分开说明；等额配额不自动代表自然总体结构 | `warning` |
| `sampling.convenience-not-representative` | 便利样本不描述为总体代表样本 | `error` |

## 严重程度判断

- 无依据给出精确样本量或配额：`error`。
- 可执行，但样本来源限制结果解释：`warning`。
- 可增加情景范围或敏感性说明：`info`。
