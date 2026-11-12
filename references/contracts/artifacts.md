# 研究产物合同

`m-survey-contract-v1`。当前 revision 见 [contracts/manifest.json](../../contracts/manifest.json)，声明兼容时写成 `m-survey-contract-v1@<revision>`。

本合同定义 M-survey 各部分交换的研究产物。产物可以使用 Markdown、YAML 或等价的结构化表达。框架约束字段语义，不约束具体排版、语言、编码或交付格式；这些由当前产品配置决定。

## ResearchBrief

研究简报描述任务的已知事实和限制。

| 字段 | 含义 | 要求 |
|---|---|---|
| `decision` | 结果将支持的业务决策 | 设计完整问卷时必需 |
| `research_questions` | 需要通过证据回答的问题 | 至少一项 |
| `object` | 产品、功能、任务、服务、概念或其他评价对象 | 必需 |
| `experience_stage` | 未接触、认知、考虑、首次使用、近期体验或长期使用 | 与体验评价有关时必需 |
| `target_population` | 目标人群、纳入和排除条件 | 必需 |
| `comparisons` | 人群、版本、概念、时点或条件比较 | 有比较时必需 |
| `constraints` | 时长、样本、平台、语言、预算和时间限制 | 已知时记录 |
| `assumptions` | 为继续工作而采用的显式假设 | 不得与已知事实混同 |

## MethodPlan

方法方案说明为什么使用某种方法。

必须包含：

- 主要方法和必要的辅助测量。
- 方法要回答的研究问题。
- 成立前提和已满足状态。
- 方法产生的主要输出。
- 样本、设计和分析要求。
- 允许的结论和不允许的结论。

## SamplePlan

样本方案必须区分人群定义、抽样来源、分析单元和数量建议。

必须包含：

- 目标总体、样本来源、纳入条件和排除条件。
- 需要比较的最小分析单元。
- 配额的用途：接近总体结构或保证组间比较。
- 精确数量建议所使用的参数、公式或方法依据。
- 筛选、未完访和无效样本的损耗假设。
- 会改变结果解释的样本边界。

## QuestionnaireSpec

问卷规格是问卷语义的中间产物。输出适配器将其渲染为 Markdown、Codebook 或平台文档。

每道题至少包含：

| 字段 | 含义 | YAML 表达 |
|---|---|---|
| `id` | 稳定且唯一的题目标识 | `id` |
| `purpose` | 对应的研究问题、样本控制或内容逻辑 | `purpose.type`、`purpose.refs` |
| `construct` | 行为、认知、使用体验、概念评价、意向、需求等被测量内容 | `construct`；实际使用体验为 `usage_experience`，并用 `experience_gate` 指向使用资格题 |
| `prompt` | 受访者看到的题干 | `prompt`；引用前题写作 `{{Q5}}`，循环对象写作 `{{item}}` |
| `response_type` | 单选、多选、评分、矩阵、开放题等 | `response_type`、`scale`、`rows`、`numeric` |
| `options` | 选项语义和稳定标识 | `options[].id`、`options[].semantic`、`options_from` |
| `display_logic` | 显示、跳转、引用、循环和终止条件 | `display_logic`、`loop_over`、`options[].terminate` |
| `response_rules` | 必答、限选、排他、随机化和开放文本关联 | `response_rules`、`options[].exclusive`、`options[].open_text` |
| `coding_semantics` | 编码代表的语义；不强制具体数字 | `options[].semantic`、可选的 `options[].code` 和 `coding_semantics` |

随机展示不得改变题目或选项标识。已回收数据的题号、变量名和编码优先保持稳定；`meta.status: fielded` 的规格必须写明全部现有编码。

### 机器可读格式

QuestionnaireSpec 可以用 Markdown 描述，也可以写成 YAML。写成 YAML 时，必须符合 [QuestionnaireSpec schema](../../schemas/questionnaire-spec.schema.json)。完整示例见 [examples/expense-app-autocat/spec.yaml](../../examples/expense-app-autocat/spec.yaml)。

schema 只约束结构。引用、编码、排他和使用资格等规则见 [规格结构完整性](../services/validation/spec-integrity.md)。

## ValidationResult

验证结果按 [验证合同](validation-contract.md) 输出。每项结果必须指向具体产物、具体问题和可执行修复条件。

## Deliverable

交付物是适配器对上述产物的表达。适配器可以改变排版、标题、编码和文件格式，但不得静默改变题目语义、问卷逻辑或结论边界。
