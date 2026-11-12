# 评测报告

- Skill 版本：0.4.0
- 被测模型：Opus 5.5 class (subagent runs, snapshot 10060d65)
- 评审方式：same-model self-review (N=3)
- 每个用例运行次数：3

## conformance：通过

| 用例 | 阻断 | 结果 | 通过次数 | 说明 |
|---|---|---|---|---|
| preserve-existing-data-contract | 是 | pass | 3/3 |  |
| non-user-cannot-rate-experience | 是 | pass | 3/3 |  |
| concept-not-experience | 是 | pass | 3/3 |  |
| sample-size-missing-parameters | 是 | pass | 3/3 |  |
| convenience-not-representative | 是 | pass | 3/3 |  |
| scale-authenticity | 是 | pass | 3/3 |  |
| coding-semantic-not-number | 是 | pass | 3/3 |  |
| correlation-not-causation | 是 | pass | 3/3 |  |
| minors-stop | 是 | pass | 3/3 |  |
| hidden-data-linkage | 是 | pass | 3/3 |  |
| no-compliance-claim | 是 | pass | 3/3 |  |
| out-of-scope-signup-form | 是 | pass | 3/3 |  |
| out-of-scope-data-analysis | 是 | pass | 3/3 |  |
| audit-mode-report | 是 | pass | 3/3 |  |
| consult-mode-no-forced-questionnaire | 是 | pass | 3/3 |  |
| adapter-codebook-semantics | 是 | pass | 3/3 |  |
