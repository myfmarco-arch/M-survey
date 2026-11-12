# 证据完整性验证

本服务检查拟议结论是否被研究设计、样本和测量支持。每次交付问卷、方法方案或审核结果前执行。

## 规则

| rule_id | 检查 | 默认严重程度 |
|---|---|---|
| `evidence.metric-linked` | 每个核心指标连接到至少一个研究问题；每个研究问题至少有一道题或一个分析对应 | `warning` |
| `evidence.conclusion-traceable` | 每个拟议结论指明对应的指标、比较或分析 | `warning` |
| `evidence.no-causal-claim` | 相关关系不表述为因果关系；非随机设计不声称因果效应 | `error` |
| `evidence.attitude-not-behavior` | 态度、意向、满意度和推荐意愿不直接表述为真实行为 | `error` |
| `evidence.purposeless-item` | 没有对应研究问题、样本控制或问卷逻辑用途的题目应删除 | `info` |
| `evidence.benchmark-source` | 使用外部数据、历史基准或常模时，记录来源和可比条件 | `warning` |

## 严重程度判断

- 拟议结论与设计直接冲突：`error`。
- 结论基本成立，但需限定人群、时间或语境：`warning`。
- 题目可删减但不影响核心设计：`info`。
