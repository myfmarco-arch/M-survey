---
name: m-survey
description: 设计、修改和审核中文定量用户研究问卷，并提供定量方法咨询。提供可直接使用的默认产品，也支持研究者通过 overlay 替换写作、格式、编码和方法。适用于满意度与体验诊断、购买决策、需求优先级（KANO、MaxDiff、联合分析）、概念测试、命名研究和用户招募甄别；不用于普通报名表、纯定性访谈大纲、已回收数据的清洗与统计分析或问卷平台编程。
license: MIT
metadata:
  version: 0.4.0
  contract: m-survey-contract-v1
---

# M-survey

在研究判断成立后生成可执行、可分析的问卷。默认使用 `survey-zh-default` 产品配置。

## 运行起点

只做两步就可以开口：

1. 读取 [产品清单](product.yaml)。根目录存在 `local.yaml` 时一并读取，它覆盖产品选择并追加 overlay 和验证（规则见 [组合与覆盖合同](references/contracts/overlay-contract.md) 第 5 节）。确定当前产品、其 `profile.yaml`、启用的 overlay 和验证清单。启用了 overlay 或 local.yaml 时，在第一次回复中用一句话说明生效的 overlay `id` 和当前产品。
2. 按 [任务路由](references/services/task-routing.md) 判断工作模式：`create` 从零设计、`revise` 修改、`audit` 审核、`consult` 方法咨询。

然后按下面的顺序工作。每项只在实际需要时读取，不要一次读完。

## 内联摘要（不读文件即可使用）

研究简报字段：`decision`、`research_questions`、`object`、`experience_stage`、`target_population`、`comparisons`、`constraints`、`assumptions`。字段完整定义和其余产物的语义见 [研究产物合同](references/contracts/artifacts.md)，在写研究方案或问卷规格时读取。

验证严重程度（内部值 → 面向用户的标签）：

| 内部值 | 用户可见 | 交付行为 |
|---|---|---|
| `error` | 严重 | 停止交付可投放版本 |
| `warning` | 重要 | 可继续，在交付物外说明限制 |
| `info` | 建议 | 按任务需要报告 |

以下情形直接返回 `error`：关键输入缺失且会改变方法、样本或核心结构；方法前提不成立；问卷逻辑使题目无法作答或分析；声称使用无法核验的正式量表、译本、常模或许可；已知隐私、伦理或安全条件未满足却要求交付可投放版本。结果字段格式见 [验证合同](references/contracts/validation-contract.md)，在输出审核报告或验证清单时读取。

## 工作模式

- **从零设计**：研究简报 → 方法方案 → 问卷规格 → 最终问卷。用户要求样本量、配额或样本框架时，另外形成样本方案。
- **修改问卷**：优先保留现有题号、语义、逻辑和编码，只修改与目标有关的内容。
- **审核问卷**：先输出问题、严重程度和修改建议；用户未要求时不重写全文。
- **方法咨询**：说明首选方法、成立前提、替代方案和结论边界，不强制生成问卷。

## 按需读取

| 需要做什么 | 读取 | 大约 |
|---|---|---|
| 澄清需求、判断信息是否足够 | [澄清问题](references/modules/knowledge/clarification-questions.md)、[默认工作流](references/products/survey-zh-default/workflow.md)（首轮提问上限） | 3.8 千字 |
| 追问条件主题或执行约束 | [条件追问与执行约束](references/modules/knowledge/clarification-probes.md) | 3.3 千字 |
| 选择方法 | [方法选择服务](references/services/method-selection.md)、[方法目录](references/modules/methods/catalog.md) | 7 千字 |
| 写具体题目、用标准量表 | [标准问法](references/modules/methods/standard-items.md)、[题库](references/modules/knowledge/question-bank.csv) | 需要时 |
| 核对来源、证据等级或许可 | [来源与检索范围](references/modules/methods/sources.md) | 需要时 |
| 特殊方法设计（KANO、MaxDiff、联合分析） | [方法索引](references/modules/methods/index.md) 指向对应的单个方法文件 | 每个约 1.3 千字 |
| 样本量或配额 | [样本规划](references/services/sample-planning.md)、[样本完整性](references/services/validation/sampling-integrity.md) | 4 千字 |
| 隐私、敏感信息、未成年人或跨境 | [隐私基线](references/services/validation/privacy-baseline.md) | 2.3 千字 |
| 写完整问卷 | [撰写规范](references/products/survey-zh-default/writing.md)、[问卷格式](references/products/survey-zh-default/questionnaire-format.md)、[默认编码](references/products/survey-zh-default/coding.md)、[模板](references/products/survey-zh-default/templates.md)、[规格结构完整性](references/services/validation/spec-integrity.md) | 6 千字 |
| 写问卷规格或审核报告 | [研究产物合同](references/contracts/artifacts.md)、[验证合同](references/contracts/validation-contract.md) | 4.4 千字 |
| Codebook 或 SPSS 配置 | [Codebook 适配器](references/adapters/codebook.md)、[SPSS 适配器](references/adapters/spss.md) | 需要时 |

上表中的产品文件可能已被 overlay 替换或扩展，以第 1 步的解析结果为准。

## 交付前验证

按 `product.yaml` 的 `validation` 清单执行：`always` 每次交付前执行，`when` 的触发条件成立时执行。每条规则有唯一 `rule_id`，定义在对应文件里。`error` 未消除时，不交付可投放版本。

## 可选的脚本检查

有代码执行环境时，完整问卷按以下顺序产出；没有时由模型按 [规格结构完整性](references/services/validation/spec-integrity.md) 逐项检查，结论格式相同。

脚本位于本 Skill 目录（`SKILL.md` 所在目录，下文记为 `<skill>`）的 `scripts/` 中。用绝对路径调用，不假设当前工作目录。

1. 将 QuestionnaireSpec 写成 YAML，格式见 [schema](schemas/questionnaire-spec.schema.json) 和 [完整示例](examples/expense-app-autocat/spec.yaml)。
2. 运行 `python <skill>/scripts/validate_spec.py spec.yaml`，修复全部 `error`。
3. 按当前生效的编码配置选择 `--codes`：

   | 编码配置 | 参数 |
   |---|---|
   | 官方默认编码，且没有已回收数据 | `--codes default` |
   | 已回收问卷，或 spec 中已写明全部编码 | `--codes explicit` |
   | overlay 规定由平台生成编码、设计阶段不分配数字 | `--codes ids` |

4. 运行 `python <skill>/scripts/render_markdown.py spec.yaml --codes <参数> -o questionnaire.md`；或手写问卷后运行 `python <skill>/scripts/check_render.py questionnaire.md --spec spec.yaml --codes <参数>`。

问卷格式被 overlay 替换时，跳过第 4 步，按 overlay 的格式手写问卷。脚本只检查结构和逻辑，不判断方法前提、证据边界和隐私风险。中间 YAML 和脚本输出不放入最终问卷正文。

## 规则合并

```text
研究事实和已有数据合同
> 用户对当前任务的明确要求
> product.yaml 启用的 overlay（按列表顺序，后者优先）
> 官方产品配置
> 方法和适配器默认值
> 案例与示例
```

上层选择不得伪造证据、量表、许可或合规状态。合同和官方验证服务不参与覆盖。同级规则冲突时，说明冲突并请用户选择；不静默覆盖。

## 产品与本地覆盖

产品是可替换的一层。每个产品一个目录，`profile.yaml` 定义面向受访者的文字、表头、默认编码和附录标题，其余文件（工作流、撰写规范、格式、模板）按 `product.yaml` 的 `products` 登记。

- 换产品、启用 overlay、追加组织验证，都写进根目录的 `local.yaml`（默认不提交，示例见 `local.example.yaml`），不要改 `product.yaml` 和本文件。这样分叉版本能与上游合并。
- 自定义产品：复制一个产品目录，改 `profile.yaml` 和各规范文件，在 `local.yaml` 的 `products` 中登记（不必改 `product.yaml`）。

## 交付原则

- 优先使用用户已经提供的信息。只询问会改变方法、样本或核心结构的未知信息。
- 面向受访者的语言、题型名称、表格表头、默认编码和正文外的阻断区标题由当前产品的 `profile.yaml` 决定，不在这里假设。写作与格式要求读产品目录下的 `writing.md` 和问卷格式文件。
- 不将案例和示例中的品牌、产品、样本数、阈值或项目事实复制到新项目。
- 最终正文不保留未解释占位符。阻断项放在正文外的简短“需确认项”中。
- 需要定制时，复制 [overlay 示例](references/overlays/example-custom/overlay.yaml) 所在目录，修改副本，再在 `local.yaml` 的 `overlays` 中启用。
