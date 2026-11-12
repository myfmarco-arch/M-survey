# 行为评测

本目录用真实模型运行 Skill，检查它在关键场景下的研究判断。评分规则见 [scoring.md](scoring.md)。

## 目录

| 路径 | 内容 |
|---|---|
| `conformance/cases.yaml` | 兼容性用例：所有兼容产品必须通过 |
| `modules/cases.yaml` | 方法、服务和适配器用例 |
| `products/survey-zh-default.yaml` | 官方产品的格式和默认值用例 |
| `fixtures/` | 用例需要的问卷片段（虚构） |
| `judge-prompt.md` | 模型评审提示词 |
| `baselines/` | 已发布的评测基线 |
| `runs/` | 本地运行结果（不提交） |

overlay 的用例放在 overlay 自己的目录中，例如 `references/overlays/example-custom/evals/cases.yaml`。

## 用例字段

```yaml
- id: minors-stop                 # 组内唯一
  module: kano                    # modules 和 overlay 组必填：方法 id、sample-planning、spss、codebook、markdown 或 overlay
  kind: negative                  # positive：应正确完成；boundary：应识别边界；negative：应拒绝或纠正
  blocking: true                  # 是否阻断评测组通过；conformance 组一律视为 true
  targets: [privacy.minor]        # 覆盖的 rule_id，必须已在 references/ 中定义
  setup:
    overlays: [references/overlays/example-custom/overlay.yaml]   # 运行前启用的 overlay
  fixtures: [evals/fixtures/audit-sample.md]                     # 作为附件发给 Skill
  request: "给初中生设计一份手机使用习惯问卷，要能直接投放。"
  expected: [...]                 # 应当观察到的行为
  forbidden: [...]                # 不得出现的行为
```

夹具中的 HTML 注释（`<!-- -->`）只给评审看，生成被测提示时会被删除。

## 运行

```bash
# 1. 生成运行目录（默认每个用例 3 次）
python scripts/run_evals.py prepare --suite conformance --runs 3 --out evals/runs/2026-11-11

# 2a. 自动生成回答：命令从 stdin 读提示、向 stdout 写回答
python scripts/run_evals.py generate --out evals/runs/2026-11-11 --cmd "claude -p"
# 2b. 或者手动：按每个 run 目录中的 setup.md 准备，把 prompt.md 发给 Skill，回答保存为 response.md

# 3a. 模型评审
python scripts/run_evals.py judge --out evals/runs/2026-11-11 --cmd "claude -p"
# 3b. 或者人工评审：复制 judgement.template.json 为 judgement.json，逐项填写 true / false 和证据

# 4. 计算结果
python scripts/run_evals.py report --out evals/runs/2026-11-11 --model "<被测模型>" --judge-label "<评审方式>"
```

`generate` 会为每次运行创建隔离工作区，把 Skill 复制到 `--install-path`（默认 `.claude/skills/m-survey`），按用例的 `setup` 修改工作区内的 `product.yaml`，并且不复制 `evals/` 和 `tests/`。被测命令在该工作区中运行。

如果用户级目录（例如 `~/.claude/skills/m-survey`）也安装了 M-survey，被测命令可能加载用户级版本而不是工作区中的版本。评测前暂时移除用户级安装，或确认被测命令只加载工作区中的 Skill。

`--cmd` 中的命令需要你确认可用，并已登录。例如 Claude Code 的非交互模式、Codex 的非交互模式，或任何读取 stdin、输出回答的脚本。运行 `generate` 前先用一个用例试跑（`prepare --case <id> --runs 1`）。

其他评测组：`--suite modules`、`--suite product`、`--suite all`，或 `--suite overlay:references/overlays/example-custom/overlay.yaml`。

## 发布基线

全部 `conformance` 用例以 N ≥ 3 通过后，把 `results.json` 复制到 `baselines/<日期>-<模型>.json`，并在 README 中注明。
