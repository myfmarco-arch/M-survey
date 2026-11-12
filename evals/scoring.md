# 行为评测规则

评测检查 Skill 的实际回答和问卷产物，不匹配固定措辞。

## 评测组

| 组 | 文件 | 目标 | 兼容性要求 |
|---|---|---|---|
| `conformance` | [conformance/cases.yaml](conformance/cases.yaml) | 所有兼容产品必须保留的产物语义和证据边界 | 是 |
| `modules` | [modules/cases.yaml](modules/cases.yaml) | 方法、服务和适配器的输入、输出和失败行为 | 修改相关模块时 |
| `product` | [products/survey-zh-default.yaml](products/survey-zh-default.yaml) | 官方产品的写作、格式和默认值 | 否 |
| `overlay` | overlay 目录中的 `evals/` | overlay 新增或替换的能力 | 启用该 overlay 时 |

`conformance` 不得把官方产品偏好变成框架要求。例如，它可以检查“以上都没有”是否排他，但不检查其是否编码为 `99`。

## 单次运行判定

评审者（人工或模型）逐条判断 `expected` 是否满足、`forbidden` 是否出现，用 JSON 布尔值 `true` / `false` 填写，并给出证据。字符串或空值视为无效评审，需要重新评审。判定由脚本按以下规则计算，不由评审者直接给出：

| 结果 | 条件 |
|---|---|
| 通过 | 全部 `expected` 满足，且没有出现任何 `forbidden` |
| 部分通过 | 没有出现 `forbidden`，恰好一项 `expected` 未满足 |
| 失败 | 出现任一 `forbidden`，或两项及以上 `expected` 未满足 |

## 用例判定

模型输出有随机性。每个用例默认运行 3 次（`--runs 3`），设运行次数为 N：

- 任一次运行出现 `forbidden`：用例失败。
- 否则，“通过”次数不少于 ⌈2N/3⌉：用例通过。N = 3 时需要至少 2 次通过。
- 其余情况：用例失败。“部分通过”不计入通过次数。

## 评测组判定

| 评测组 | 通过条件 |
|---|---|
| `conformance` | 全部用例通过 |
| `modules`、`product`、`overlay` | 全部 `blocking: true` 用例通过；`blocking: false` 用例的失败数不超过 max(1, ⌊n/5⌋)，n 为非阻断用例数 |

## 兼容性声明

兼容性只能通过已发布的行为评测基线证明。**没有基线时，任何版本——包括官方产品——都不能声明兼容。**

一个版本在满足以下全部条件时，才可以声明与某个合同 revision 兼容：

1. 使用 N ≥ 3 运行全部 `conformance` 用例并全部通过。
2. 将 `report` 生成的 `results.json` 保存到 `evals/baselines/<日期>-<模型>.json`，记录 Skill 版本、被测模型、评审方式和日期。
3. 在 README 的“兼容性状态”一节注明基线文件名。
4. 声明时写明 revision，格式为 `m-survey-contract-v1@<revision>`。revision 以 [contracts/manifest.json](../contracts/manifest.json) 为准。

当前状态：已有一份满足上述条件的基线（[2026-11-11-conformance-n3](baselines/2026-11-11-conformance-n3.json)），可声明 `m-survey-contract-v1@2026-11-11.3`。它的限制（评审无独立方、被测快照落后于当前 HEAD、只覆盖 conformance 组）见该基线与 [baselines/README.md](baselines/README.md)。仓库内的结构检查（`check_repo.py`、单元测试）只能证明文件自洽和规则引用完整，不能替代行为评测。

## 回归要求

- 修改合同时，运行全部兼容性评测。
- 修改方法时，运行该方法的模块评测和相关兼容性评测。
- 修改官方格式、编码或撰写时，运行官方产品评测。
- 新增规则或方法时，增加至少一个 `positive` 用例和一个 `boundary` 或 `negative` 用例。

## 评审者偏差

- 模型评审可能偏宽或偏严。正式声明兼容前，至少人工复核所有“失败”和“部分通过”的运行。
- 评审模型和被测模型相同时，在基线文件中注明。
- 不把评审提示词调整为迎合某一产品的写法；评审只看 `expected` 和 `forbidden`。
