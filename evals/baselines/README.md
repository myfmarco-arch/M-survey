# 评测基线

本目录存放已发布的评测结果。命名：`<日期>-<组>-<N>.json`，附同名 `.md` 报告。

| 文件 | 组 | N | 评审 | 可声明兼容 |
|---|---|---|---|---|
| [2026-11-11-conformance-n3.json](2026-11-11-conformance-n3.json) | conformance | 3 | 同族自评 | **是**（附条件，见下） |
| [2026-11-11-opus55-smoke-n1.json](2026-11-11-opus55-smoke-n1.json) | conformance | 1 | 同族自评 | 否 |

## 可声明兼容的基线（N=3）

2026-11-11 跑了全部 16 个 `conformance` 用例，各 3 次，48 次运行全部通过（每个用例 3/3）。按 [scoring.md](../scoring.md) 的规则，它满足：

- 全部用例通过（`conformance` 组要求全通过）；
- N = 3 ≥ 3，达到 ⌈2N/3⌉ 的通过次数。

对应声明：**`m-survey-contract-v1@2026-11-11.3`**。

注意：随后为写入本条结论，`evals/scoring.md` 的“当前状态”段落被修改，revision 已前移到 `2026-11-11.4`。那次改动只改文书记述，未动用例、规则或严重程度，因此本基线仍然成立；若后续再改任何合同文件，需重跑。

### 必须同时说明的限制

1. **评审没有独立方。** 判定由与执行任务同一模型族的审查完成，宽严偏差未估计。想提高可信度，需要一个不同模型或人工复核抽样。
2. **被测快照不是当前 HEAD。** 运行基于指纹 `10060d65` 的快照；之后仓库又改了 `method-selection.md`（新增“类型边界”）、`clarification-questions.md/.csv`、`clarification-probes.md` 和三份说明文档。这些不属于合同文件，`revision` 未变，但本轮结论未覆盖改动后的内容。改动影响 `consult-mode-no-forced-questionnaire`（KANO/MaxDiff 判断）和澄清类用例，建议对这些用例重跑一轮。
3. **只覆盖 conformance 组。** `modules` 和 `product` 两组尚未运行，它们的规则不算已验证。
4. **通过子代理执行**，不是 CLI 原生工具链，工具调用差异未覆盖。

## 冒烟基线（N=1）

早先的 N=1 运行保留作对照：它证明流程可跑通，但不满足 N≥3，不能用于声明兼容。

## 复现

```bash
python scripts/run_evals.py prepare --suite conformance --runs 3 --out evals/runs/<日期>
# 用被测模型逐条生成回答（run_evals generate，或按 run 目录里的 setup.md 人工执行）
python scripts/run_evals.py judge  --out evals/runs/<日期>
python scripts/run_evals.py report --out evals/runs/<日期> --model "<被测模型>" --judge-label "<评审方式>"
```

把 `results.json` 复制到本目录并补齐 `baseline_type`、`contract_revision`、`declares_compatibility` 和 `caveats` 字段。
