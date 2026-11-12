# 规格结构完整性验证

本服务检查 QuestionnaireSpec 的结构和逻辑是否可执行、可分析。规则与具体排版和编码数字无关，所有兼容产品都适用。

## 何时执行

- 交付完整问卷、修订问卷或输出 Codebook / SPSS 配置前执行。
- 有代码执行环境时，先把 QuestionnaireSpec 写成 YAML，再运行：

```bash
python scripts/validate_spec.py path/to/spec.yaml
```

- 没有代码执行环境时，由模型按下表逐项检查，结果格式相同。

规格格式见 [QuestionnaireSpec schema](../../../schemas/questionnaire-spec.schema.json) 和 [完整示例](../../../examples/expense-app-autocat/spec.yaml)。

## 规则

| rule_id | 检查 | 默认严重程度 | 脚本可检 |
|---|---|---|---|
| `spec.schema` | 字段名称、类型和必填项符合 schema | `error` | 是 |
| `spec.id-unique` | 模块、题目和变量名标识唯一 | `error` | 是 |
| `spec.option-id-unique` | 同一题内选项和矩阵行标识唯一 | `error` | 是 |
| `spec.code-unique` | 同一题内显式编码唯一 | `error` | 是 |
| `spec.rq-reference` | 研究用途的题目指向存在的研究问题 | `error` | 是 |
| `spec.logic-reference` | 显示条件、选项引用、循环和文本引用只引用前面已存在的题目 | `error` | 是 |
| `spec.logic-option-reference` | 显示条件引用的选项或矩阵行存在 | `error` | 是 |
| `spec.logic-type` | 条件类型与被引用题型匹配；数值区间在评分范围内 | `error` | 是 |
| `spec.pipe-token` | `{{item}}` 只用于循环题；`{{Q5}}` 只引用前面的题目 | `error` | 是 |
| `spec.choice-options` | 选择题至少有两个选项 | `error` | 是 |
| `spec.non-choice-options` | 开放题、数值题、评分题和说明不定义选项 | `warning` | 是 |
| `spec.exclusive-none` | 多选题中的“以上都没有”、不知道、不适用和拒答设为排他 | `error` | 是 |
| `spec.other-text` | “其他”关联开放文本；作为排除项的“其他”如同时终止访问，可以不收集文本 | `warning` | 是 |
| `spec.select-range` | 限选、最少选择和排序数量与选项数一致 | `error` | 是 |
| `spec.scale-definition` | 评分题定义分值范围和两端含义 | `error` | 是 |
| `spec.matrix-rows` | 矩阵题定义行和评分范围或列选项 | `error` | 是 |
| `spec.terminate-position` | 终止访问只出现在甄别、资格或同意题中 | `warning` | 是 |
| `spec.no-placeholder` | 受访者可见文本不含 `[产品]`、TBD、TODO 等未解释占位符；题干中的“待定”“待确认”视为占位符，选项中的同类词提示复核 | `error`；选项中为 `warning` | 是 |
| `spec.fielded-codes` | `status: fielded` 的问卷所有选项写明现有编码 | `error` | 是 |
| `spec.empty-section` | 模块不为空 | `warning` | 是 |
| `spec.eligible-usage` | `eligible` 只出现在被 `experience_gate` 引用的资格题中 | `warning` | 是 |
| `spec.code-required` | 渲染时每个选项都能得到编码；不知道、不适用和拒答没有默认编码时必须显式填写 | `error` | 渲染时 |

脚本同时检查以下其他域的规则：`measurement.experience-required`、`measurement.scale-consistency` 和 `evidence.metric-linked`。

### 使用资格的表达

`construct: usage_experience` 的题目必须用 `experience_gate` 指向一道测量实际行为的单选或多选题，并在该题中把表示“使用过”的选项标记为 `eligible: true`。以下三种方式之一成立即通过：

1. 显示条件 `display_logic.all` 中包含 `{question: <资格题>, selected_any: [...]}`，且所选选项全部是 `eligible`。
2. 资格题终止全部非 `eligible` 选项的受访者，且资格题本身没有显示条件。
3. 本题从多选资格题的已选项循环或引用（`filter: selected`），且资格题的普通选项全部是 `eligible`。

显示条件选择了非 `eligible` 选项时，返回 `error`。

## 编码与渲染

QuestionnaireSpec 中的 `code` 可以省略。省略时由当前产品的编码配置在渲染时分配。已回收问卷必须写明全部现有编码。

不知道、不适用和拒答没有框架默认编码。产品或 overlay 未定义时，渲染前必须由用户确认，不自行占用有效选项编码。
