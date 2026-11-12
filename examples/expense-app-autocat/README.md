# 示例：自动分类功能体验调研

本示例完整展示 M-survey 从业务需求到最终问卷的产物链。产品“账小满”和全部数字均为虚构，不对应任何真实产品、公司或项目。不要把示例中的样本数、比例或阈值复制到真实项目。

## 文件

| 文件 | 内容 | 对应产物 |
|---|---|---|
| [01-request.md](01-request.md) | 用户提交的需求 | 输入 |
| [02-research-plan.md](02-research-plan.md) | 研究简报、方法方案、样本方案和验证摘要 | ResearchBrief、MethodPlan、SamplePlan、ValidationResult |
| [spec.yaml](spec.yaml) | 机器可读的问卷规格 | QuestionnaireSpec |
| [03-questionnaire.md](03-questionnaire.md) | 官方产品格式的最终问卷 | Deliverable |

`03-questionnaire.md` 由脚本从 `spec.yaml` 生成，不手工修改。

## 复现

在仓库根目录运行：

```bash
pip install -r requirements.txt
python scripts/validate_spec.py examples/expense-app-autocat/spec.yaml
python scripts/render_markdown.py examples/expense-app-autocat/spec.yaml -o examples/expense-app-autocat/03-questionnaire.md
python scripts/check_render.py examples/expense-app-autocat/03-questionnaire.md --spec examples/expense-app-autocat/spec.yaml
```

本示例只显式写了“不记得”的编码 97，其余选项依赖官方默认编码，所以用默认的 `--codes default`。用 `--codes explicit` 会逐题报 `spec.code-required`：那是“已回收问卷或编码全部写死”时才用的模式，不是示例出错。

`scripts/check_repo.py` 会检查 `03-questionnaire.md` 是否与 `spec.yaml` 的渲染结果一致。

## 示例展示的要点

- 甄别题终止未成年人、行业从业者和非活跃用户（S1–S3）。
- 只有确认使用过自动分类的人评价使用体验（Q3–Q7 的 `experience_gate: Q2`）。
- 认知、使用和满意分开测量（Q1、Q2、Q3）。
- 多选题的“其他”关联开放文本，“以上都没有遇到”排他（Q5）。
- 循环追问和选项引用（Q6、Q7）。
- “不记得”使用项目约定的编码 97，而不是框架默认值（Q2、Q6、Q8）。
- 样本方案写明全部参数和假设，并说明结论边界。
