# 组合与覆盖合同

`m-survey-contract-v1`。当前 revision 见 [contracts/manifest.json](../../contracts/manifest.json)，声明兼容时写成 `m-survey-contract-v1@<revision>`。

本合同定义 `product.yaml` 如何组合能力文件，以及 overlay 如何替换或扩展官方产品。它属于 `m-survey-contract-v1`。

## 1. 可以覆盖什么

| 对象 | 允许的操作 | 说明 |
|---|---|---|
| 产品配置：`workflow`、`writing`、`questionnaire_format`、`coding`、`templates`、`case_index` | `replace` 或 `extend` | 团队写作、格式、编码和工作流 |
| 服务：`routing`、`method_selection`、`sample_planning` | 只允许 `extend` | 增加组织偏好、超范围事项或历史参数来源；不得删除公共规则 |
| 方法模块 | `add` 或 `replace` | 新增方法，或用自己的版本替换官方方法 |
| 知识模块 | `add` | 行业概念、组织题库、历史基准说明 |
| 输出适配器 | `add`；可指定新的 `default` | 平台文档、其他数据字典格式 |
| 验证服务 | 只允许 `add` | 组织额外检查；官方验证始终生效 |
| 评测 | `add` | overlay 自己的回归评测 |

以下内容不能被 overlay 覆盖：

- `references/contracts/` 中的全部合同。
- 官方验证服务和验证严重程度定义。
- 研究产物字段语义和 ValidationResult 格式。
- 用户事实、已有数据合同和证据状态。

## 2. overlay.yaml 格式

```yaml
schema_version: 2
id: team-custom                  # 小写字母、数字和连字符
description: 团队问卷规范
targets: survey-zh-default       # 适用的产品 id

overrides:                       # 产品配置
  writing:
    mode: extend                 # 必填：extend 或 replace
    file: writing.md
  coding:
    mode: replace
    file: coding.md

services:                        # 只允许 extend
  method_selection:
    mode: extend
    file: method-preferences.md

modules:
  methods:
    add:
      - id: van-westendorp
        capability: 探索可接受价格区间
        file: methods/van-westendorp.md
    replace:
      - id: kano                 # 必须是 product.yaml modules.methods 中已有的 id
        file: methods/kano.md
  knowledge:
    add:
      - id: industry-terms
        use_when: 涉及本行业术语时
        file: knowledge/industry-terms.md

adapters:
  add:
    - id: platform-doc
      use_when: 用户要求平台导入文档时
      file: adapters/platform-doc.md
  default: markdown              # 可选；填写 product.yaml adapters.available 或本 overlay 新增的适配器 id

validation:
  add:
    - file: validation/team-checks.md
      trigger: 每次交付前

evals:
  - evals/cases.yaml
```

规则：

- 所有 `file` 路径相对于 `overlay.yaml` 所在目录。
- `product.yaml` 中的 `overlays` 路径相对于仓库根目录。
- `mode` 必须显式填写。缺少 `mode` 的条目不生效，并按 `error` 报告。
- 除 `schema_version`、`id` 和 `targets` 外，其余区块都是可选的。
- `targets` 与 `product.yaml` 的 `id` 不一致时，不启用该 overlay，并报告 `error`。

## 3. 合并语义

### replace

丢弃此前的结果，只使用 overlay 文件。替换文件必须是完整版本，不能只写差异。

### extend

先读取此前的结果，再读取 overlay 文件。

- overlay 文件中的规则与此前规则冲突时，以 overlay 为准。
- 此前规则中没有被 overlay 提到的内容继续有效。
- 需要明确删除此前的某条规则时，在 overlay 文件中使用 `## 取消的默认规则` 小节，逐条引用原文。没有该小节时，不删除任何此前规则。

`## 取消的默认规则` 小节格式：

```markdown
## 取消的默认规则

- 取消：「删除不影响理解的套话、礼貌语和重复提示。」（来源：survey-zh-default/writing.md）
```

### 多个 overlay

`product.yaml` 中的 `overlays` 按列表顺序应用，后者在前者结果之上继续合并：

- 后一个 overlay 的 `replace` 覆盖前面所有结果。
- 后一个 overlay 的 `extend` 叠加在前面结果之上。
- 两个 overlay 新增同一个方法或知识 `id` 时，报告 `error`，不静默选择。

## 4. 方法模块的新增和替换

- 新增或替换的方法文件必须包含 [模块合同](module-contract.md) 规定的十个章节。
- 新增方法加入可用方法列表，等同于在 [方法索引](../modules/methods/index.md) 中增加一行。
- 替换方法时，`id` 必须是 `product.yaml` 中 `modules.methods` 已有的键；官方同 `id` 方法文件不再读取。
- 新增方法的 `id` 不得与 `modules.methods` 已有的键重复。
- 每个新增或替换的方法至少提供一个正向评测和一个边界或反向评测，放在 overlay 的 `evals` 中。

## 5. 本地覆盖 local.yaml

分叉版本不应修改上游维护的文件。为此约定一个本地覆盖文件：

- 路径：仓库根目录的 `local.yaml`，默认写入 `.gitignore`。
- 形状：包含 `product`（切换产品）、`products`（登记自己的产品目录）、`overlays`（启用列表）和 `validation.add`（追加组织验证）。
- 优先级：`local.yaml` 中的设置覆盖 `product.yaml` 的同名项；`product.yaml` 的 `overlays` 与 `local.yaml` 的 `overlays` 合并，后者排在后面。
- 不存在时忽略，行为与没有该文件一致。示例见 [local.example.yaml](../../local.example.yaml)。

这样分叉版本只维护 `local.yaml`、自己的产品目录和 overlay 目录，`product.yaml` 与 `SKILL.md` 保持上游原样，合并上游更新时不会冲突。

`local.yaml` 中的 `products` 与 `product.yaml` 的 `products` 合并，同名产品以 `local.yaml` 为准。示例：

```yaml
schema_version: 1
product: my-team-product
products:
  my-team-product:
    profile: my-team/profile.yaml
    writing: my-team/writing.md
```

产品自己的 `profile.yaml` 可以在 `files` 块中声明相对路径；`product.yaml` 与 `local.yaml` 中登记的路径优先。

## 6. 解析步骤

Skill 在每次任务开始时执行：

1. 读取 `product.yaml`，确定官方产品配置、服务、模块、适配器和验证。
2. `overlays` 为空时，直接使用官方配置。
3. 读取 `local.yaml`（如存在）并合并；再按顺序读取每个 `overlay.yaml`，检查 `schema_version`、`targets` 和文件路径。
4. 按本合同第 3、4 节合并，得到本次任务实际使用的文件集合。
5. 只读取当前任务需要的文件。overlay 不改变按需读取原则。
6. 启用了 overlay 或 local.yaml 时，在第一次回复中用一句话说明生效的 overlay `id` 和当前产品；最终问卷正文不提及。

## 7. 规则

| rule_id | 检查 | 默认严重程度 |
|---|---|---|
| `overlay.schema` | `overlay.yaml` 可解析，`schema_version`、`id` 和 `targets` 存在，没有未定义的顶层键或操作 | `error` |
| `overlay.target-mismatch` | `targets` 与 `product.yaml` 的 `id` 一致 | `error` |
| `overlay.mode-required` | 每个覆盖条目显式填写 `mode` | `error` |
| `overlay.forbidden-op` | 服务只用 `extend`，验证只用 `add`，不覆盖合同 | `error` |
| `overlay.missing-file` | 所有 `file` 路径存在 | `error` |
| `overlay.duplicate-id` | 新增方法、知识或适配器的 `id` 不与官方或其他 overlay 重复；替换的 `id` 必须存在 | `error` |
| `overlay.method-sections` | 新增或替换的方法文件包含模块合同要求的十个章节 | `error` |
| `overlay.extend` | `extend` 时，未被提到的原有规则继续生效 | `error` |
| `overlay.replace` | `replace` 时，只使用替换文件，原有文件不再生效 | `error` |
| `overlay.announce` | 启用 overlay 或 local.yaml 时，在第一次回复中说明 overlay `id` 和当前产品 | `info` |
| `overlay.local` | `local.yaml` 只包含 `product`、`overlays`、`validation.add`；启用列表指向存在的文件 | `error` |

## 8. 机器检查

`scripts/check_repo.py` 检查：

- `overlay.yaml` 可解析，必填字段存在。
- `mode` 显式填写，且服务和验证没有使用不允许的操作。
- 所有 `file` 路径存在。
- 替换方法的 `id` 在 `modules.methods` 中存在；新增方法 `id` 不与官方方法重复。
- 新增和替换的方法文件包含模块合同要求的章节。
