# 贡献 M-survey

贡献应尽量小、可评审、可验证。不要因一个案例将个人偏好升级为全局规则。架构和分层见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 可贡献内容

- 新的研究方法模块。
- 对现有方法前提、样本、分析或结论边界的修正。
- 新的输出适配器。
- 通用质量验证规则。
- 人工构造且不包含真实项目信息的案例、示例和评测夹具。
- 行为评测、脚本、错误修复和文档改进。

团队特有的写作、格式和编码偏好请放在自己的 overlay 中，不提交到官方产品。

## 新增方法模块

1. 按 [模块合同](references/contracts/module-contract.md) 编写方法文件：首行写模块元数据注释，依次使用十个固定二级标题。
2. 在“验证规则”章节用规则表定义 `method.<id>.*` 规则和默认严重程度。
3. 在 `product.yaml` 的 `modules.methods` 和 [方法索引](references/modules/methods/index.md) 中登记。
4. 在 `evals/modules/cases.yaml` 中至少增加一个 `positive` 用例和一个 `boundary` 或 `negative` 用例，`module` 填方法 id。
5. 运行 `python scripts/check_repo.py`。

## 新增或修改验证规则

- 每条规则有唯一的 `rule_id`，格式为 `<域>.<规则名>`，只在一个文件的规则表中定义。
- 写明默认严重程度和判断依据。
- 能由脚本确定判断的规则，同时在 `scripts/validate_spec.py` 或 `scripts/check_render.py` 中实现，并在 `tests/` 中增加触发该规则的测试。
- 增加至少一个覆盖该规则的行为评测用例（`targets` 中填写规则）。

## 修改公共合同

`references/contracts/` 和 `schemas/` 是项目最稳定的部分。修改前必须说明：

- 现有合同无法支持的真实用例。
- 为什么新能力不能通过新模块、适配器或 overlay 实现。
- 对现有模块和分叉产品的影响。
- 迁移方法和全部兼容性评测结果。

破坏字段语义、规则标识或模块输入输出的修改需要新的合同主版本。0.x 期间的调整写入 CHANGELOG 的“迁移”小节。

修改任何合同文件后必须重新生成清单，否则 CI 会失败：

```bash
python scripts/contract_manifest.py write    # 前移 revision 并记录新的校验和
```

不要在分叉里修改 `SKILL.md` 或 `product.yaml` 来做定制；写 `local.yaml`。

## 证据与来源

- 优先引用原始方法、验证研究、方法批评和官方来源。
- 标明是否读取了全文、摘要、元数据还是官方页面。
- 区分完整正式题组、代表题、结构说明、工作译文和项目模板。
- 未核验的译文不得标记为正式验证版本。
- 不提交无权再分发的完整题组、付费文献或受限模板。
- `catalog.csv`、`question-bank.csv` 和 `clarification-questions.csv` 是权威数据源；修改时同步更新对应的 Markdown 说明。

## 案例与隐私

公开案例、示例和夹具必须是人工构造或已获得明确发布授权的内容。不保留：

- 内部品牌、未发布产品或项目代号。
- 真实参与者、联系方式或可识别组合信息。
- 项目特有阈值、配额、样本数和决策记录。
- 客户、合作方或组织内部流程。

## 发布前检查

以下检查在 GitHub Actions 中自动运行，提交前也请在本地运行：

```bash
pip install -r requirements.txt
python scripts/check_repo.py
python -m unittest discover -s tests
```

`check_repo.py` 覆盖：内部链接、YAML 解析、CSV 列数和 ID 唯一、跨文件 ID 和标准状态一致、方法模块章节、规则定义唯一且被引用的规则都存在、评测用例结构和方法覆盖、overlay 格式、示例与渲染结果一致、版本号一致、无本地绝对路径。

以下事项仍需人工检查：

- 没有临时说明、修订痕迹或内部信息。
- 第三方材料的来源和再分发状态已检查。
- 修改了合同、服务、方法或官方产品时，按 [evals/scoring.md](evals/scoring.md) 运行相关行为评测。
- 版本号和 CHANGELOG 已更新。
