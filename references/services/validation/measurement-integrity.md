# 测量完整性验证

本服务检查题目是否实际测量了所声称的内容。每次交付问卷或审核结果前执行。

## 受访资格

- 先问真实行为和使用资格，再问体验评价、原因和需求。
- 未使用过功能的用户不评价实际使用体验。可以测量认知、未使用原因和未来需求。
- 测试未上线概念时，使用概念评价语言，不使用实际体验语言。

## 题目和选项

- 一道题只测量一个主要概念。
- 题目明确对象、时间范围和使用场景。
- 选项保持同一层级，并在任务允许范围内尽量互斥、穷尽。
- 不知道、不适用、拒答、“其他”和“以上都没有”按语义需要设置，不按统一数字编码强制设置。
- 量表方向和端点含义保持一致。

## 标准题组和量表

- 代表题、结构说明、工作译文和项目模板不得包装为完整正式量表。
- 无法核验完整题项、正式语言版本、计分方式和许可时，不得声称交付正式标准量表。
- 修改标准题组后标记为适配版，不继续使用原常模或跨研究比较结论。
- 正式跨语言、跨市场或跨期追踪项目记录翻译、回译、认知访谈和预测试状态。

## 规则

| rule_id | 检查 | 默认严重程度 | 脚本可检 |
|---|---|---|---|
| `measurement.experience-required` | 使用体验评价题只向有实际使用经历的受访者显示 | `error` | 是（需在资格题中标记 `eligible`） |
| `measurement.concept-language` | 未上线概念使用概念评价语言，不使用实际体验语言 | `error` | 否 |
| `measurement.single-construct` | 一道题只测量一个主要概念；不出现双重提问 | `warning` | 否 |
| `measurement.explicit-frame` | 题干明确对象、时间范围和使用场景 | `warning` | 否 |
| `measurement.options-mece` | 选项同层级，并尽量互斥、穷尽 | `warning` | 否 |
| `measurement.special-options` | 特殊选项按语义设置，不按统一数字强制设置 | `warning` | 否 |
| `measurement.scale-consistency` | 评分点数、方向和端点含义在同类题中一致 | `warning` | 是 |
| `measurement.scale-authenticity` | 不将代表题、工作译文或项目模板声称为正式量表 | `error` | 否 |
| `measurement.adapted-scale` | 修改后的标准题组标记为适配版，不沿用原常模 | `warning` | 否 |
| `measurement.translation-record` | 正式跨语言、跨市场或追踪项目记录翻译和预测试状态 | `warning` | 否 |
| `measurement.leading-wording` | 题干不暗示期望答案，不预设受访者立场 | `warning` | 否 |

## 阻断条件

无经验者评价真实体验，或者交付物伪造正式量表状态时，返回 `error`。
