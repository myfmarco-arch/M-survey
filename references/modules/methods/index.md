# 方法索引

先使用 [方法选择服务](../../services/method-selection.md) 判断需要什么类型的证据，再读取对应方法。

## 独立方法模块

| id | 能力 | 方法 | 文件 |
|---|---|---|---|
| `kano` | 将需求分为基本、期望、魅力等类型 | KANO | [kano.md](kano.md) |
| `maxdiff` | 测量多个项目之间的相对取舍 | MaxDiff / Best-Worst Scaling | [maxdiff.md](maxdiff.md) |
| `conjoint` | 测量属性水平组合的权衡 | 选择型联合分析 | [conjoint.md](conjoint.md) |

本表与 `product.yaml` 的 `modules.methods` 一致，由 `scripts/check_repo.py` 检查。已启用 overlay 新增或替换的方法以 overlay 声明为准。

## 完整方法目录

方法知识分三份文件读取：

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| [方法目录](catalog.md) | 业务需求到方法的映射、路由关系和优先级 | 判断方法时 |
| [标准问法](standard-items.md) | 可直接核对的题项、评分方式、计分和使用规则 | 需要具体问法或标准量表时 |
| [来源与检索范围](sources.md) | 文献编号、获取状态和检索边界 | 需要引用来源或核对证据等级时 |

[机器可读目录](catalog.csv) 是方法 ID、证据等级和来源编号的权威来源。

目录中的方法仍可以使用。当某个方法需要频繁定制、独立评测或多份资源时，再按 [模块合同](../../contracts/module-contract.md) 将其拆成独立文件，并在 `product.yaml` 的 `modules.methods` 中登记。

## 替换方法

使用者复制任一方法文件，修改为自己的版本，在 overlay 的 `modules.methods.replace` 中声明。修改后的方法必须保留模块合同规定的十个章节，并提供正向和边界评测。格式见 [组合与覆盖合同](../../contracts/overlay-contract.md)。
