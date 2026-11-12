# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。0.x 期间，合同仍可能调整；调整会在此说明迁移方法。

## [0.4.0] - 2026-11-11

针对“产品抽象没有被验证”和“分叉必然冲突”两项结构性问题的改动。规则内容不变。

### 新增

- 产品层改为可替换：每个产品一个目录，`profile.yaml` 定义面向受访者的文字、表头、题型名称、连词、默认编码和正文外附录标题。渲染和校验脚本不再写死中文产品的内容。
- 第二个产品 `survey-en-minimal`（最小英文产品，默认编码 90/91）。它的存在用来验证产品抽象：同一份 spec 用两个产品渲染，表头、题型名称、`(ALL)`、`required` 和编码都不同，脚本和合同不用改。`python -m unittest` 中有对应用例。
- `local.yaml`：分叉版本自己的覆盖文件，默认写入 `.gitignore`，可设置 `product`、`overlays` 和 `validation.add`。示例见 `local.example.yaml`。规则见组合与覆盖合同第 5 节。
- `contracts/manifest.json`：锁定合同版本，记录各类合同文件的 sha256 和 revision（见 `contracts/manifest.json`，当前 revision 由脚本前移）。范围包括四份合同、schema、`evals/conformance/cases.yaml` 和 `evals/scoring.md`。合同内容变化时，`python scripts/contract_manifest.py write` 会自动把 revision 前移为 `YYYY-MM-DD.N`；`check` 校验。

### 变更

- `product.yaml` 增加 `default_product` 和 `products` 注册表；`product` 一项保留为兼容旧读取方式。
- 渲染和校验脚本新增 `--product` / `--profile`；`check_render.py` 的表头、附录标题和题型名称从产品配置读取，标题正则由 `headings.question` 生成。
- 每份合同开头标明 revision 的查看与书写方式。
- 兼容性声明必须带 revision：`m-survey-contract-v1@<revision>`。只写 `v1` 不足以说明兼容的时点。

### 修正

- 产品配置缺必需字段（tokens、codes、tables、type_labels、headings、separators）时直接报错，不再静默显示为空或退回中文产品。
- 传入未注册的 `--product` 时报错，不再静默渲染成默认产品。
- 显示条件（连词、“已作答”）、题型规则引用和自定义分隔符全部按产品配置解析，换语言后检查不再误报。

### 评测

- 跑通端到端行为评测并达到声明门槛：16 个 `conformance` 用例各 3 次，48 次运行全部通过。结果为 [2026-11-11-conformance-n3](evals/baselines/2026-11-11-conformance-n3.json)，据此可声明 `m-survey-contract-v1@2026-11-11.3`（写入本条结论时 scoring.md 有文案改动，revision 前移到 `2026-11-11.4`，不影响用例结论）。
- 该基线的限制：评审为同族自评、无独立复核；被测快照落后于当前 HEAD（`method-selection.md` 之后新增“类型边界”）；只覆盖 conformance 组。
- 早先的 N=1 冒烟基线保留作对照，不用于声明。

### 已知状态

- 官方产品当前**不声明兼容**：尚无满足 N≥3 且评审可复核的基线。结构检查通过不等于兼容。

### 迁移

- 分叉版本：把 `product.yaml` 里改过的产品项和 overlay 列表移到 `local.yaml`，恢复 `product.yaml` 为上游版本，之后合并上游更新不会冲突。
- 自定义产品：在 `products` 中登记，并提供 `profile.yaml`（必填字段见 `scripts/check_repo.py` 的 `check_profiles`）。
- `headings.question` 不能使用方括号：方括号表示待替换占位符。

## [0.3.3] - 2026-11-11

### 修正

- 用错 `--codes` 时不再逐选项刷错误：缺少编码按题合并成一条，并直接给出应改用的模式。此前对示例用 `--codes explicit` 会报 38 条同类错误，容易让人以为问卷坏了。

### 文档

- 示例 README 说明为什么用 `--codes default`，以及 `--codes explicit` 报错不是示例出错。
- 安装说明补充：目录名必须是 `m-survey`，与 `SKILL.md` 的 `name` 一致；当前文件夹名是 `M-survey`，直接使用需要重命名。
- `evals/baselines/README.md` 明确：目录为空意味着行为表现尚未正式测过，结构检查不能替代行为评测。

## [0.3.2] - 2026-11-11

### 修正

- `spec.no-placeholder` 识别 `⟨…⟩`、`〈…〉`、`〔…〕` 标记的待替换内容。修复前用尖括号写的“待替换”会漏检，整份问卷被判为通过。
- 正文之外的“需确认项”和“结果解释限制”小节不参与占位符检查和题目解析。按官方模板，阻断项就应写在这里；此前这些小节里的表格会被当成最后一题的表格，产生误报。
- 作为排除项并同时终止访问的“其他”选项，不要求再收集开放文本（`spec.other-text`）。

### 变更

- 官方问卷格式明确两种题型名称的写法：`评分`、`矩阵评分`，并列出全部题型名称；评分说明行写作“评分：1–5 分；1 = ……”。

## [0.3.1] - 2026-11-11

### 变更

- 面向受访者的题型名称从“量尺”改为“评分”，“矩阵量尺”改为“矩阵评分”，评分说明行的前缀改为“评分：”。依据：问卷从业者对这一题型的口语叫法是“打分/评分”，“量尺”是翻译腔。
- 官方问卷格式列出全部题型名称：单选、多选、评分、矩阵评分、矩阵单选、开放题、数值填空、排序、说明。
- 验证规则说明、脚本提示语和题库中的“标准量尺”同步改为“标准评分”。

### 影响

`response_type: scale` 和规则标识 `spec.scale-definition`、`measurement.scale-consistency` 不变，已有 spec 和分叉版本无需迁移。只有渲染出的问卷文字发生变化；手写问卷使用“打分”“量表”等其他叫法仍能通过语义比较，因为比较只看数值范围、锚点和结构。

## [0.3.0] - 2026-11-11

减少从零设计时的读取量和读取次数。规则内容不变，只是拆得更细、入口更短。

### 变更

- `SKILL.md` 运行起点从 6 步压到 2 步：先读 `product.yaml` 和任务路由即可开始澄清，合同改为按需读取。
- `SKILL.md` 内联研究简报字段名、验证严重程度对照表和阻断条件，写方案和审核时不必再读两个合同文件。
- 按需读取表增加“大约多少字”一列和缺失的行（条件追问、来源、特殊方法、写规格）。
- `catalog.md` 拆成三份：[方法目录](references/modules/methods/catalog.md)（路由与映射表）、[标准问法](references/modules/methods/standard-items.md)（题项原文、量尺、计分）、[来源与检索范围](references/modules/methods/sources.md)（文献编号与检索边界）。方法目录从 1.85 万字降到 6.3 千字。
- `clarification-questions.md` 拆成两份：本文件放使用规则、首轮 6 个核心问题和停止条件；条件追问、执行约束和对话示例移到 [clarification-probes.md](references/modules/knowledge/clarification-probes.md)。
- `product.yaml` 的 `modules` 增加 `standard_items`、`sources` 和 `knowledge.clarification_probes`。
- 产品评测增加一条：首轮不得预读写作、格式、题库和来源文件。

### 修正

- `spec.no-placeholder` 同时识别 `⟨…⟩`、`〈…〉`、`〔…〕` 标记的待替换内容。此前只认方括号和英文占位词，用尖括号写的“待替换”会漏检并让整份问卷被判为通过。

### 影响

一次从零设计的典型读取量从 17 个文件、约 4.6 万字符降到 8 个文件、约 2.6 万字符，且第一个问题出现前只需 2 次读取。之前已启用的 overlay 和分叉版本不受影响：被拆分的文件都是被引用的深层文件，不是 overlay 的覆盖对象。

## [0.2.0] - 2026-11-11

首个面向开源发布的整理版本。

### 新增

- 组合与覆盖合同（`references/contracts/overlay-contract.md`）：定义 `replace` / `extend` 合并语义、可覆盖范围、多个 overlay 的顺序和冲突处理。
- QuestionnaireSpec 的 JSON Schema（`schemas/questionnaire-spec.schema.json`）和完整示例（`examples/expense-app-autocat/`）。
- 规格结构完整性验证服务（`references/services/validation/spec-integrity.md`）。
- 全部验证规则统一使用 `rule_id`，并在各自文件的规则表中定义默认严重程度。
- 脚本：`validate_spec.py`、`render_markdown.py`、`check_render.py`、`check_repo.py`、`run_evals.py`，以及 `tests/` 回归测试和 GitHub Actions。
- 评测：用例增加 `kind`、`blocking`、`targets`、`fixtures`、`setup` 字段；新增夹具；用例从 13 个增加到 34 个（兼容性 16、模块 11、官方产品 7），另有 overlay 示例自带的 4 个；覆盖隐私、超范围请求、审核模式、方法咨询、overlay 合并和适配器语义；每个方法模块都有正向和边界用例。
- 评分规则：单次运行判定由脚本计算；每个用例默认运行 3 次；定义评测组通过条件和兼容性声明条件。
- overlay 示例新增 Van Westendorp 方法模块和配套评测，演示 `modules.methods.add`。
- `docs/ARCHITECTURE.md`、`requirements.txt`、`.gitignore`。
- QuestionnaireSpec 新增 `eligible`（资格题中表示实际使用的选项）和 `program_note`（渲染到问卷中的编程说明）。
- 渲染脚本新增 `--codes ids`，用于编码由平台生成、设计阶段不分配数字的情况。

### 变更

- `product.yaml` 升级到 `schema_version: 2`：验证分为 `always` 和 `when`；方法模块按 ID 登记；适配器按 ID 登记；新增 `schemas`、`tools` 和 `version`。
- `overlay.yaml` 升级到 `schema_version: 2`：每个覆盖条目必须写明 `mode`，并新增 `targets`。
- `SKILL.md`：运行步骤加入 overlay 解析和条件验证；新增可选的脚本检查流程；frontmatter 增加 `license` 和 `metadata`。
- 方法模块统一为十个固定二级标题，验证规则改为 `method.<id>.*` 规则表。
- 需求澄清知识模块不再写死首轮提问数量和交付结构，改为引用当前产品配置。
- 方法决策顺序只在方法选择服务中定义，方法目录不再重复。
- `catalog.csv`、`question-bank.csv` 和 `clarification-questions.csv` 明确为权威数据源，Markdown 为展开说明；`check_repo.py` 检查两者一致。
- 审核报告的“严重 / 重要 / 建议”与验证合同的 `error` / `warning` / `info` 建立一一对应。
- README 改为面向使用者；架构和兼容性说明移至 `docs/ARCHITECTURE.md`。
- 样本规划交付格式把“计算所得有效样本数”和“项目建议最低有效样本数”分为两行；问卷模板的样本框架增加“样本来源”。
- 官方工作流的首轮提问上限明确按编号问题计数。
- 两个 overlay 合并语义用例从兼容性评测移到 overlay 示例自带的评测，避免分叉产品因 `targets` 不同而必然失败。
- 非阻断用例的通过条件改为失败数不超过 max(1, ⌊n/5⌋)。

### 修正

- NPS 英文原始问法改为 “How likely is it that you would recommend…”，并注明常见简化变体。
- SEQ 英文问法补全为 “…was the task to complete?”，注明两端锚点方向和反向锚点风险。
- UMUX-LITE 题项改为 “This system's…”，补充原始计分公式，并提示 SUS 校准公式需核对后续研究。

以上三项通过检索结果和二手资料交叉核对，没有重新获取论文全文，文献获取状态未升级。

### 迁移

- 已有 `overlay.yaml`：把 `writing: writing.md` 改为 `writing: {mode: extend, file: writing.md}` 或 `mode: replace`，并增加 `targets: survey-zh-default`、`schema_version: 2`。
- 已有分叉的 `product.yaml`：把 `services.required_validation` 移到 `validation.always` / `validation.when`；把 `adapters.optional` 改为 `adapters.available` 字典。
- 自定义方法模块：把“允许和禁止的结论”拆成“允许的结论”和“不允许的结论”两个二级标题，在首行加入模块元数据注释，并把验证规则改为规则表。

## [0.1.0] - 2026-11-06

- 初始版本：研究产物、模块和验证合同；方法选择、样本规划和四项验证服务；KANO、MaxDiff、联合分析方法模块；方法目录、题库和澄清问题；Markdown、Codebook、SPSS 适配器；`survey-zh-default` 官方产品；overlay 示例；13 个行为评测用例。
