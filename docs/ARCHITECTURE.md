# 架构说明

本文面向想分叉、扩展或贡献 M-survey 的人。只想使用 Skill 的读者看 [README](../README.md) 即可。

## 设计目标

M-survey 把问卷设计拆成三类内容：

| 内容 | 稳定性 | 谁会改 |
|---|---|---|
| 研究判断：方法前提、证据边界、样本规则、测量规则 | 最稳定 | 上游维护者 |
| 方法和知识：KANO、MaxDiff、题库、澄清问题 | 较稳定 | 上游维护者和贡献者 |
| 产品偏好：写作风格、表格格式、默认编码、工作流 | 最常变化 | 每个团队 |

分层的目的是让团队只改第三类，而第一类在所有分叉中保持一致，并能合并上游更新。

## 分层

```text
SKILL.md                        入口：解析配置、路由、加载、验证
└── product.yaml                组合清单：本产品用哪些文件
    ├── contracts/              合同：产物字段、模块、验证格式、组合与覆盖
    ├── services/               公共服务：路由、方法选择、样本规划
    │   └── validation/         验证规则（每条规则有唯一 rule_id）
    ├── modules/                方法模块和知识模块
    ├── adapters/               输出适配器：Markdown、Codebook、SPSS
    ├── products/<id>/          产品配置：工作流、写作、格式、编码、模板、案例
    └── overlays/               团队覆盖：extend 或 replace 产品配置，新增方法等
```

依赖方向从下到上：合同只定义格式和语义，不依赖服务、模块或产品的具体内容（合同中指向 schema、示例和服务的链接只用于导航）；服务和模块引用合同；产品引用服务和模块；overlay 只覆盖产品层和可扩展的服务、模块。规则见 [模块合同](../references/contracts/module-contract.md) 的“分层约束”。

## 研究产物

各层之间交换的是 [研究产物合同](../references/contracts/artifacts.md) 定义的五种产物：

```text
ResearchBrief → MethodPlan → SamplePlan → QuestionnaireSpec → Deliverable
                                       ↘ ValidationResult ↙
```

QuestionnaireSpec 是问卷语义的唯一来源，有 [JSON Schema](../schemas/questionnaire-spec.schema.json)。适配器只能改变表达，不能改变语义。对官方 Markdown 格式，`check_render.py --spec` 把问卷与规格的参考渲染逐题比较（题干、题型规则、显示条件、选项、标签、矩阵行、评分范围和程序说明）。

## 验证

每条验证规则有唯一的 `rule_id`（如 `measurement.experience-required`），定义在对应文件的规则表中，并写明默认严重程度。`check_repo.py` 保证：

- 每条规则只定义一次。
- 文档、评测用例和脚本引用的规则都有定义。

验证有两种执行方式：模型按规则表检查（所有环境），脚本检查（有代码执行环境时，覆盖 `spec.*` 等结构规则）。两者输出同一种 ValidationResult。

`product.yaml` 中的验证分为 `always`（每次交付前）和 `when`（触发条件成立时），避免无关任务加载隐私或样本规则。

## 组合与覆盖

[组合与覆盖合同](../references/contracts/overlay-contract.md) 定义了：

- 可以覆盖什么：产品配置可以 `replace` 或 `extend`；服务只能 `extend`；方法可以 `add` 或 `replace`；验证只能 `add`；合同不能覆盖。
- `extend` 的含义：未被提到的原规则继续生效；需要删除原规则时必须在“取消的默认规则”小节逐条引用。
- 多个 overlay 按顺序应用，后者优先；新增 ID 冲突时报错，不静默选择。

## 兼容性

`m-survey-contract-v1` 由以下内容组成：`references/contracts/` 中的四份合同、`schemas/questionnaire-spec.schema.json`、验证规则的 `rule_id` 和默认严重程度，以及 `evals/conformance/` 中的行为评测。

一个分叉版本可以：

- 任意修改产品配置（写作、格式、编码、工作流），仍然兼容。
- 新增方法、知识、适配器和验证规则，仍然兼容。

以下修改会破坏兼容性，需要新的合同主版本：

- 改变研究产物字段的语义。
- 改变 ValidationResult 的格式、规则标识或严重程度定义。
- 删除或削弱官方验证规则。

声明兼容的条件见 [evals/scoring.md](../evals/scoring.md) 的“兼容性声明”。当前有一份 N=3 的 conformance 基线（[evals/baselines/](../evals/baselines/)），据此可声明 `m-survey-contract-v1@2026-11-11.3`（revision 现值见 manifest）；限制是评审无独立方、被测快照落后于当前 HEAD、`modules` 与 `product` 两组尚未运行。

### 合同 revision

合同名 `m-survey-contract-v1` 是主版本；具体内容由 `contracts/manifest.json` 锁定：

- `revision`：形如 `2026-11-11.1`，每次修改合同或 schema 前移。
- `files`：每份合同的 sha256，`python scripts/contract_manifest.py check` 校验。
- 声明兼容时写 `m-survey-contract-v1@<revision>`，避免“兼容 v1”说不清是哪个时点。

0.x 版本期间，合同仍可能调整。调整会前移 revision 并写入 [CHANGELOG](../CHANGELOG.md)，同时说明迁移方法。

## 评测

| 组 | 检查什么 | 何时运行 |
|---|---|---|
| `conformance` | 所有兼容产品必须保留的研究判断 | 修改合同、服务、验证规则时 |
| `modules` | 方法和适配器的输入、输出和失败行为 | 修改对应模块时 |
| `product` | 官方产品的格式和默认值 | 修改官方产品配置时 |
| `overlay` | overlay 新增或替换的能力 | 修改 overlay 时 |

每个用例写明 `targets`（覆盖的规则）、`kind`（positive / boundary / negative）和 `blocking`。执行和评分见 [evals/README.md](../evals/README.md)。

## 为什么用 Markdown 而不是代码实现规则

Skill 运行在模型的上下文中。规则写成 Markdown，模型可以直接读取和执行，也方便研究员审阅和修改。脚本只覆盖能确定判断的结构规则，作为补充而不是前提：没有代码执行环境时，Skill 仍然完整可用。

## 按需加载

`SKILL.md` 保持简短，只做路由，并内联最常用的两个摘要（研究简报字段、验证严重程度和阻断条件），使澄清阶段不必先读合同。

读取分三层：

1. 入口：`SKILL.md`、`product.yaml`、任务路由。澄清开始前只需这两个文件加上澄清问题。
2. 判断层：方法目录、样本规划、隐私基线、写作与格式规范。按任务触发。
3. 细节层：标准题项原文、来源与检索边界、单个方法模块、适配器和合同。只在写下对应内容时读取。

因此文件按“什么时候需要”拆分，而不是按知识类别堆放：方法目录只放路由和映射（约 6 千字），题项原文和文献来源各自独立。新增内容时保持这一原则：新文件应能说清“什么任务才需要读我”，单个文件不要超过约 8 千字。
