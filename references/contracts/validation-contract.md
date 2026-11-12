# 验证合同

`m-survey-contract-v1`。当前 revision 见 [contracts/manifest.json](../../contracts/manifest.json)，声明兼容时写成 `m-survey-contract-v1@<revision>`。

验证服务和方法模块使用统一结果格式。验证保护研究产物的语义和证据边界，不保护官方产品的排版偏好。

## 严重程度

| 级别 | 审核报告中文标签 | 含义 | 交付行为 |
|---|---|---|---|
| `error` | 严重 | 产物不可执行、证据不成立或存在未处理高风险 | 停止交付可投放版本 |
| `warning` | 重要 | 可以继续，但结果解释或应用受限 | 在交付物外说明限制 |
| `info` | 建议 | 不影响基本成立性的改进建议 | 按任务需要报告 |
| `pass` | — | 某项明确检查已满足 | 无需单独展示，但可记录在评测中 |

审核模式面向用户时使用中文标签，内部判断和评测使用英文级别。两者一一对应，不另设级别。

## 结果字段

每项验证结果必须包含：

```yaml
rule_id: measurement.experience-required
severity: error
target: QuestionnaireSpec.Q12
message: 未使用过该功能的用户被要求评价使用满意度。
resolution: 增加使用资格题，只向实际使用者显示体验评价。
source: references/services/validation/measurement-integrity.md
```

`target` 指向研究产物或具体题目，格式为 `<产物>` 或 `<产物>.<题目 id>[.<选项 id>]`。`resolution` 说明可观察的修复条件。

## 规则标识

`rule_id` 使用 `<域>.<规则名>`；方法规则使用 `method.<方法 id>.<规则名>`；只适用于某个适配器的规则使用 `adapter.<适配器 id>.<规则名>`，适用于所有适配器的规则使用 `adapter.<规则名>`。规则名使用小写字母、数字和连字符。

| 域 | 定义文件 | 说明 |
|---|---|---|
| `evidence` | [证据完整性](../services/validation/evidence-integrity.md) | 指标、结论和证据链 |
| `measurement` | [测量完整性](../services/validation/measurement-integrity.md) | 受访资格、题目、选项和量表 |
| `sampling` | [样本完整性](../services/validation/sampling-integrity.md) | 样本量、配额和外推 |
| `privacy` | [隐私基线](../services/validation/privacy-baseline.md) | 个人信息、敏感信息和合规风险初筛 |
| `spec` | [规格结构完整性](../services/validation/spec-integrity.md) | QuestionnaireSpec 的结构和逻辑；可由脚本检查 |
| `routing` | [任务路由](../services/task-routing.md) | 工作模式、澄清和适用范围 |
| `method.<id>` | 对应方法模块的“验证规则”章节 | 方法特有前提和结论边界 |
| `overlay` | [组合与覆盖合同](overlay-contract.md) | overlay 格式和合并冲突 |
| `adapter` | 对应适配器的“验证”章节 | 转换后语义保真 |
| `format` | 当前产品 `profile.yaml` 中 `format_rules` 指向的文件 | 产品排版选择；只用于该产品的回归，不属于兼容性要求 |

每个规则在定义文件中只出现一次，并写明默认严重程度。具体情境可以提高严重程度；降低严重程度时必须说明理由。

## 阻断规则

出现以下任一情形时返回 `error`：

- 关键输入缺失，且缺失会改变方法、样本或核心问卷结构。
- 方法的必要前提不成立。
- 问卷逻辑使题目无法正确作答或无法分析。
- 声称使用无法核验的正式量表、正式译本、常模或许可。
- 已知的隐私、伦理或安全条件未满足，却要求交付可投放版本。

## 执行方式

验证有两种执行方式，结果格式相同：

| 方式 | 适用 | 范围 |
|---|---|---|
| 模型检查 | 所有环境 | 全部规则 |
| 脚本检查 | 有代码执行环境，且已写出 QuestionnaireSpec YAML | `spec.*` 和部分 `measurement.*` 规则，见 `scripts/validate_spec.py` |

脚本检查不能替代模型对证据、方法前提和隐私风险的判断。脚本未覆盖的规则仍由模型检查。

## 范围

兼容性验证检查：

- 研究产物字段是否完整。
- 方法输入和输出是否一致。
- 证据是否支持拟议结论。
- 适配器是否保留题目语义和问卷逻辑。

官方产品回归测试另行检查三列表格、默认编码和中文撰写等产品选择。
