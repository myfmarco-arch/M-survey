# Markdown 问卷适配器

本适配器将 ResearchBrief、SamplePlan 和 QuestionnaireSpec 渲染为普通 Markdown 问卷文稿。

## 输入

- 已通过必需验证的 QuestionnaireSpec。
- 当前产品的写作、问卷格式和编码配置（可能已被 overlay 替换或扩展）。
- 用户已有文稿格式。修改任务中优先保留现有有效格式。

## 转换规则

- 保留题目和选项的稳定标识。
- 保留显示、跳转、引用、循环、终止和排他语义。
- 按当前格式配置渲染题目标题、选项表和程序标签。
- 按当前编码配置渲染具体编码。适配器本身不强制 `98/99`。
- 开放题没有选项时，不生成空表。
- 正文不混入内部思考过程、工作日志和无关方法教学。

官方产品的参考实现是 `scripts/render_markdown.py`。模型直接写 Markdown 时，结果必须与参考实现在语义上等价。

## 输出

默认产品可以按任务需要包含：

1. 简短研究简报。
2. 样本框架。
3. 问卷说明和作答逻辑。
4. 问卷正文。
5. 正文外的必要限制或需确认项。

用户只要求最终问卷时，只交付成文稿和必要限制。

## 验证

| rule_id | 检查 | 默认严重程度 |
|---|---|---|
| `adapter.semantic-preserved` | 转换前后的题目、顺序、选项数量、编码、排他和显示逻辑一致 | `error` |
| `adapter.data-contract` | 编码方案不与已有数据合同冲突 | `error` |
| `adapter.no-placeholder` | 最终正文没有“待定”“待确认”或未解释占位符（同 `spec.no-placeholder`） | `error` |

有代码执行环境时，运行 `python scripts/check_render.py questionnaire.md --spec spec.yaml` 检查 `adapter.semantic-preserved`。
