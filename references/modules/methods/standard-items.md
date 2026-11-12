# 标准问法和量表题组

业务需求到方法的映射和路由见 [方法目录](catalog.md)。本文件只放具体题项、评分方式、计分和使用规则，只在需要写下题目时读取。

标准状态（完整题组已内置、外部正式题组、代表题、结构说明、方法指令、项目模板）的权威来源是 [question-bank.csv](../knowledge/question-bank.csv)；文献编号见 [来源与检索范围](sources.md)。

## 1. 标准问法索引

下表中的标准问法 ID 与完整映射表的 ID 关联。机器可读题项库见 [question-bank.csv](../knowledge/question-bank.csv)。

“标准状态”描述当前知识库可以交付的内容，不代表方法本身的学术地位：

- **完整题组已内置**：当前库包含可核对的完整原文题组；语言版本、计分和许可仍需检查。
- **外部正式题组**：当前库未内置题项，必须从官方或授权来源取得。
- **代表题**：只用于理解构念，不得声称为完整题组。
- **结构说明**：只说明维度或组成，不得据此补写正式题项。
- **方法指令、项目模板或分析模板**：不是验证量表。

无法核验完整题项、正式语言版本、计分方式和许可时，只能交付方法建议、结构和资料缺口，不得声称使用正式标准量表。

| 映射 ID | 标准问法 ID | 方法 | 标准状态 |
|---|---|---|---|
| D01–D04 | Q-GENERIC-01–04 | 常规结构化题、召回期、原因题、痛点题 | 通用模板 |
| D05 | Q-UA-01 | U&A 研究 | 项目模板 |
| N01 | Q-KANO-01 | KANO | 方法指令 |
| N02 | Q-MD-01 | MaxDiff / Best-Worst Scaling | 方法指令 |
| N03、P03 | Q-CBC-01 | 选择型联合分析 | 方法指令 |
| N04、B03 | Q-CONCEPT-01 | 概念测试 | 项目模板 |
| N05、I01 | Q-EXPERIMENT-01 | 随机化调查实验 | 方法指令 |
| P01 | Q-VW-01 | Van Westendorp PSM | 方法指令 |
| P02 | Q-GG-01 | Gabor-Granger | 方法指令 |
| X01 | Q-CSAT-01 | 交易型 CSAT | 通用模板 |
| X02 | Q-ACSI-01 | ACSI 型满意度 | 结构说明；正式版本未内置 |
| X03 | Q-SERVPERF-01 | SERVPERF | 行业适配框架；正式题组未内置 |
| X04 | Q-SEQ-01 | SEQ | 标准单题 |
| X05 | Q-SUS-01 | SUS | 完整英文题组已内置；中文为工作译文 |
| X06 | Q-UMUX-01 | UMUX-LITE | 完整英文题组已内置；中文为工作译文 |
| X07 | Q-UEQ-01 | UEQ / UEQ-S | 外部正式题组；当前库未内置 |
| X08 | Q-CES-01 | CES 型努力题 | 版本模板 |
| X09 | Q-DRIVER-01 | 关键驱动分析 | 分析模板 |
| G01 | Q-NPS-01 | NPS | 官方口径；中文为工作译文 |
| G02 | Q-LOYALTY-01 | 忠诚、续用、复购 | 项目模板 |
| G03 | Q-TAM-01 | TAM | 代表题；完整题组未内置 |
| G04 | Q-UTAUT-01 | UTAUT | 代表题；完整题组未内置 |
| G05 | Q-PMF-01 | PMF “非常失望”问法 | 行业启发式 |
| G06 | Q-JUSTER-01 | Juster 购买概率 | 标准评分 |
| B01 | Q-AWARE-01 | 品牌认知漏斗 | 通用模板 |
| B02 | Q-CBBE-01 | 顾客基础品牌资产 | 结构说明；正式量表未内置 |
| B04 | Q-BHT-01 | 品牌健康度追踪（BHT） | 项目模板 |
| S01 | Q-SEGMENT-01 | 潜类别或聚类分群 | 分析模板 |
| I02 | Q-PREPOST-01 | 前后测或重复横截面 | 设计模板 |

## 2. 可直接核对的标准题项

#### Q-NPS-01：Net Promoter Score

英文原始问法：

> How likely is it that you would recommend [company/product/service] to a friend or colleague?

中文工作译文：

> 您有多大可能将[产品/服务]推荐给朋友或同事？

使用 0–10 分评分。0 表示“完全不可能”（not at all likely），10 表示“极有可能”（extremely likely）。官方分组为 0–6、7–8、9–10。NPS = Promoters 比例 − Detractors 比例，取值 −100 到 +100。中文句子是工作译文。正式跨期或跨市场追踪必须固定语言版本并记录翻译过程 [E03][E25]。

措辞核对：Reichheld（2003）使用 “How likely is it that you would recommend [company X] to a friend or colleague?”。行业中常见 “How likely are you to recommend…” 等简化变体；追踪项目应固定一种措辞，不在波次之间切换。

#### Q-KANO-01：KANO 成对题

| 类型 | 英文标准形式 | 中文工作译文 |
|---|---|---|
| 功能题 | If [attribute] is present, how do you feel? | 如果产品具有[功能]，您感觉如何？ |
| 反功能题 | If [attribute] is absent, how do you feel? | 如果产品不具有[功能]，您感觉如何？ |

两题使用同一组回答：

1. I like it that way. / 我喜欢这样。
2. It must be that way. / 理应如此。
3. I am neutral. / 无所谓。
4. I can live with it that way. / 我可以接受。
5. I dislike it that way. / 我不喜欢这样。

中文是工作译文。正式项目应做认知访谈和语言验证。属性必须具体到用户可以理解“有”和“没有”的差异 [E07]。

#### Q-SUS-01：System Usability Scale

标准英文题项如下。每题使用 1–5 点同意度评分。中文题项是工作译文，不能自动称为已验证中文 SUS。

| 编号 | 标准英文题项 | 中文工作译文 |
|---|---|---|
| 1 | I think that I would like to use this system frequently. | 我认为我会愿意经常使用这个系统。 |
| 2 | I found the system unnecessarily complex. | 我觉得这个系统不必要地复杂。 |
| 3 | I thought the system was easy to use. | 我觉得这个系统容易使用。 |
| 4 | I think that I would need the support of a technical person to be able to use this system. | 我认为我需要技术人员的支持才能使用这个系统。 |
| 5 | I found the various functions in this system were well integrated. | 我认为这个系统的各项功能衔接得很好。 |
| 6 | I thought there was too much inconsistency in this system. | 我觉得这个系统存在太多不一致。 |
| 7 | I would imagine that most people would learn to use this system very quickly. | 我想象大多数人会很快学会使用这个系统。 |
| 8 | I found the system very cumbersome to use. | 我觉得这个系统使用起来很笨拙。 |
| 9 | I felt very confident using the system. | 我使用这个系统时感到很有信心。 |
| 10 | I needed to learn a lot of things before I could get going with this system. | 我需要先学习很多东西，才能开始使用这个系统。 |

计分：奇数题得分减 1；偶数题用 5 减去得分；求和后乘以 2.5，得到 0–100 的 SUS 分数。这个分数不是百分比。标准题组来源为 Brooke 的原始 SUS 题组及后续经验评价 [E11a][E11]。

#### Q-UMUX-01：UMUX-LITE

标准英文题项：

1. [This system's] capabilities meet my requirements.
2. [This system] is easy to use.

方括号内可替换为产品名称，其余措辞保持不变。两题都来自 Finstad 的四题 UMUX 中的正向题。

建议使用原始 7 点同意度评分（1 = Strongly disagree，7 = Strongly agree）。原始分数 = (题 1 + 题 2 − 2) × 100 ÷ 12，取值 0–100。原始论文另给出向 SUS 校准的回归公式；使用校准公式前应核对后续研究对其适用性的评价。不要把 UMUX-LITE 的题项替换成 SUS 题项，也不要使用 SUS 的计分公式 [E12]。

#### Q-SEQ-01：Single Ease Question

标准英文形式：

> Overall, how difficult or easy was the task to complete?

使用 7 点评分，只标注两端：1 = Very difficult（非常困难），7 = Very easy（非常容易）。题目应紧跟具体任务。它是任务级指标，不是系统总体可用性指标 [E13]。

措辞与方向核对：部分研究使用反向锚点（1 = 非常容易）。与外部基准比较前，先确认评分方向一致；同一项目内不混用两种方向。

#### Q-UEQ-01：UEQ / UEQ-S

UEQ 使用语义差异题组，覆盖吸引力、清晰度、效率、可靠性、刺激性和新颖性等维度。不要自行翻译、重排或抽取整套 26 题。使用 [UEQ 官方语言版本、题项 PDF 和分析工具](https://www.ueq-online.org/)。如果需要短版，使用官方 UEQ-S，不要从 UEQ 随意抽题 [E14][E14b]。

#### Q-TAM-01：TAM 构念题组

以下是原始构念的代表性题干，不是完整题组：

- Perceived usefulness: “Using [system] would improve my job performance.”
- Perceived ease of use: “I would find [system] easy to use.”

正式项目应使用原始题组或有文献依据的情境适配版本，并记录删改内容。不要把 TAM 和 UTAUT 题项混成一个无定义的大量表 [E15]。

#### Q-UTAUT-01：UTAUT 构念题组

常见核心构念及代表性题干如下：

- Performance expectancy: “I would find the system useful in my job.”
- Effort expectancy: “My interaction with the system would be clear and understandable.”
- Social influence: “People who influence my behavior think that I should use the system.”
- Facilitating conditions: “I have the resources necessary to use the system.”

这些题干需要根据对象、角色和使用场景适配。完整 UTAUT 还涉及调节变量和使用行为，不能只保留一题后宣称完成 UTAUT [E16]。

#### Q-PMF-01：PMF 行业启发式

> How would you feel if you could no longer use [product]?

回答：Very disappointed / Somewhat disappointed / Not disappointed。

“非常失望”比例和 40% 阈值来自行业案例，不是普遍验证的统计界线。必须同时看留存、活跃、付费和自然增长 [E26]。

## 3. 没有唯一验证问法的方法

| 方法 | 建议模板 | 重要限制 |
|---|---|---|
| CSAT | Overall, how satisfied were you with [specific experience]? / 总体而言，您对这次[具体体验]有多满意？ | 没有唯一跨行业验证问法；必须写明对象和时间。 |
| CES | How much effort did you personally have to put forth to handle your request? / 您为处理这次请求付出了多少努力？ | “公司让事情变得容易”是另一版本；同一问卷不要混用。 |
| MaxDiff | Which item is most important to you, and which is least important to you? | 这是任务指令，不是心理量表。 |
| 概念测试 | How clear, relevant, and credible is this concept? / 这个概念有多清楚、相关和可信？ | 维度必须服务于具体决策，并经过预测试。 |
| Van Westendorp | At what price would [product] seem too cheap, cheap, expensive, or too expensive? | 四个价格判断必须使用同一货币和价格单位。 |
| 品牌认知 | What brands of [category] come to mind? / 您首先想到哪些[品类]品牌？ | 先无提示，再提示；不要把提示后的答案当无提示认知。 |
| U&A | No fixed item set. Define usage, occasions, frequency, needs, attitudes, and barriers from the decision. | U&A 是研究项目设计。必须明确品类边界、召回期和各模块用途，不能声称存在统一验证量表。 |
| BHT | Keep the target population, sampling, core KPIs, item wording, response anchors, brand presentation, and reference periods stable across waves. | BHT 是追踪项目设计。核心模块与轮换模块要分开；样本或测量口径变化必须记录为趋势断点。 |

这些模板不能标注为“经过验证的标准量表”。它们应标注为“方法模板”或“项目模板”，并在预测试后确定最终措辞 [E01][E02][E17][E22][E23][E27]。

## 4. 量表使用规则

1. 保留原始题项、回答锚点、题数、计分方式和必要的题目顺序。
2. 修改标准题项后，称为“适配版”，不要继续使用原量表的常模或跨研究比较结论。
3. 中文翻译应记录翻译、回译、认知访谈和预测试状态。
4. 记录题项来源、版本、许可和是否允许修改。
5. 多题量表应检查信度、结构效度和必要的测量等值性。Cronbach's alpha 不能单独证明量表有效。
6. NPS、CES、PMF 等行业指标不能自动升级为经过普遍验证的心理测量量表。
