# M-survey

中文定量问卷设计 Skill。它帮助用户研究员从业务问题出发选择方法、规划样本、写出可执行可分析的问卷，并审核已有问卷。

*A Claude / Codex skill for designing, revising and auditing Chinese quantitative research questionnaires, with method guidance (KANO, MaxDiff, conjoint, SUS, NPS…), sample planning, validation rules, and a customizable overlay mechanism.*

## 它能做什么

| 你说 | 它做 |
|---|---|
| “新功能上线两个月了，想知道该先改哪些问题” | 澄清业务决策，给出研究简报、方法方案、样本建议和完整问卷 |
| “帮我审核这份问卷” | 按严重程度列出题号、问题、影响和修改建议 |
| “这份问卷已经回收过，加一个选项” | 保留原题号和编码，只改需要改的部分，并提示跨期可比性 |
| “12 个功能该用 KANO 还是 MaxDiff？” | 说明各自回答什么问题、成立前提和结论边界 |
| “样本量要多少？” | 写出计算参数和公式；参数不足时只给情景，不拍数字 |

它会主动拦住的常见问题：让没用过的人评价使用体验、把满意度当成真实行为、把便利样本说成全国代表、把工作译文包装成正式量表、给未成年人生成可投放问卷、无依据给出 n=500。

它不做：普通报名表、定性访谈大纲、问卷平台编程、已回收数据的清洗和统计分析。

## 输出示例

下面摘自 [完整示例](examples/expense-app-autocat/)（虚构产品）：

```markdown
##### Q5.【遇到的问题】【Q2=1/2】过去 30 天，您在使用自动分类时遇到过以下哪些情况？【多选，选项随机，必答】

| 编码 | 选项细节 | 程序标签 |
|---:|---|---|
| 1 | 分类错误，需要手动修改 |  |
| 2 | 同一商家的账单每次被分到不同分类 |  |
| …… | …… |  |
| 98 | 其他，请注明____ | 置底；开放填空 |
| 99 | 以上都没有遇到 | 置底；排他 |
```

## 安装

Skill 目录名必须是 `m-survey`，与 `SKILL.md` 中的 `name` 一致。

**Claude Code**：把本仓库放到 `~/.claude/skills/m-survey/`（所有项目可用）或项目内的 `.claude/skills/m-survey/`。之后直接描述问卷任务即可自动触发，也可以输入 `/m-survey`。

目录名必须与 `SKILL.md` 的 `name` 一致，即小写的 `m-survey`。仓库当前的文件夹名是 `M-survey`（大写 M），直接放进去不会被识别，需要重命名。macOS 的文件系统通常不区分大小写，改名时要确认大小写真的生效。

**Claude 应用**：打包为 zip 后在设置的 Skills 页面上传（入口位置以当前版本为准）。在仓库中运行 `git archive --format=zip --prefix=m-survey/ -o m-survey.zip HEAD` 可以得到不含本地缓存的压缩包。

**Codex**：把仓库放到 Codex 的 skills 目录（例如 `~/.codex/skills/m-survey/`，以 Codex 当前文档为准），使用 `$m-survey` 调用。`agents/openai.yaml` 提供界面显示信息。

Skill 本身只需要文本文件（Markdown、YAML、CSV、JSON），不需要安装任何依赖。`scripts/` 中的检查脚本是可选的，需要 Python 3.9+：

```bash
pip install -r requirements.txt
```

## 定制成你团队的版本

不需要改官方文件。复制 [overlay 示例](references/overlays/example-custom/)，按需修改，再在 [product.yaml](product.yaml) 中启用：

```yaml
overlays:
  - references/overlays/my-team/overlay.yaml
```

overlay 可以扩展或替换写作规范、问卷格式、默认编码和工作流，也可以新增或替换方法模块。每一项都要写明 `extend` 还是 `replace`。合同和官方验证规则不能被覆盖。完整规则见 [组合与覆盖合同](references/contracts/overlay-contract.md)。

**分叉版本不要改 `product.yaml` 和 `SKILL.md`。** 换产品、启用 overlay、追加组织验证都写进根目录的 `local.yaml`（已在 `.gitignore` 中，示例见 [local.example.yaml](local.example.yaml)），否则每次合并上游更新都会冲突。

产品层是可替换的：换语言或换排版只需要新增一个产品目录，提供 `profile.yaml`，再在 `local.yaml` 的 `products` 中登记。仓库自带一个最小英文产品 [survey-en-minimal](references/products/survey-en-minimal/README.md) 作为例子，同一份问卷规格用它渲染会得到英文表头和 `90/91` 编码。

## 质量保证

| 检查 | 命令 | 说明 |
|---|---|---|
| 仓库一致性 | `python scripts/check_repo.py` | 链接、版本、CSV、规则定义、评测结构、overlay、示例 |
| 问卷规格 | `python scripts/validate_spec.py spec.yaml` | 题号、引用、排他、编码、使用资格、占位符 |
| 问卷文稿 | `python scripts/check_render.py questionnaire.md --spec spec.yaml` | 格式和与规格的一致性 |
| 脚本测试 | `python -m unittest discover -s tests` | 检查脚本本身的回归测试 |
| 行为评测 | `python scripts/run_evals.py …` | 用真实模型运行 Skill 并评审，见 [evals/README.md](evals/README.md) |

前四项在 GitHub Actions 中自动运行。行为评测需要调用模型，在本地运行。

## 兼容性状态

当前可声明：**`m-survey-contract-v1@2026-11-11.3`**（revision 现值见 [contracts/manifest.json](contracts/manifest.json)；写入本结论后前移过一次，只改文书记述），依据 [conformance N=3 基线](evals/baselines/2026-11-11-conformance-n3.json)——16 个兼容性用例各跑 3 次，48 次全部通过。

四条限制必须一起看：

- 评审由同一模型族完成，没有独立复核方；
- 被测快照（指纹 `10060d65`）之后仓库又有修改，本轮未覆盖 `method-selection.md` 的“类型边界”等新增内容；
- 只覆盖 `conformance` 组，`modules` 和 `product` 两组尚未运行；
- 通过子代理执行，不含 CLI 原生工具链差异。

详见 [evals/baselines/README.md](evals/baselines/README.md)。

结构检查通过只说明文件自洽、规则引用完整、示例可复现，不说明模型会按规则行事。基线的产生方法和发表条件见 [evals/README.md](evals/README.md)。

声明兼容时须写明合同 revision，例如 `m-survey-contract-v1@<revision>`，当前值见 [contracts/manifest.json](contracts/manifest.json)。revision 与每个合同文件的校验和锁在 [contracts/manifest.json](contracts/manifest.json)：合同一改，revision 就前移，别人也能分辨“兼容的是哪个时点的 v1”。

## 目录

```text
m-survey/
├── SKILL.md                     Skill 入口和路由
├── product.yaml                 当前产品的组合清单
├── schemas/                     QuestionnaireSpec 的 JSON Schema
├── contracts/manifest.json      合同 revision 和每份合同的校验和
├── local.example.yaml           本地覆盖示例（复制为 local.yaml 后不提交）
├── references/
│   ├── contracts/               研究产物、模块、验证、组合与覆盖合同
│   ├── services/                路由、方法选择、样本规划和验证规则
│   ├── modules/                 方法模块和知识模块（方法目录、标准问法、来源分开）
│   ├── adapters/                Markdown、Codebook、SPSS 适配器
│   ├── products/                产品层：survey-zh-default（中文）、survey-en-minimal（英文最小示例）
│   └── overlays/example-custom/ 定制示例
├── examples/                    完整示例：需求 → 方案 → 规格 → 问卷
├── evals/                       行为评测用例、夹具和评分规则
├── scripts/                     检查、渲染和评测脚本（可选）
├── tests/                       脚本测试
└── docs/ARCHITECTURE.md         框架设计说明
```

想了解分层设计、兼容性和扩展方式，见 [架构说明](docs/ARCHITECTURE.md)。

## 许可和第三方内容

项目原创内容使用 [MIT License](LICENSE)。

方法名称、外部量表、标准题组、工作译文和引用来源可能受其他权利和使用条件约束，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

M-survey 不提供法律、伦理或隐私合规保证。正式项目应按适用地区、组织政策和研究对象进行审查。

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CHANGELOG.md](CHANGELOG.md)。
