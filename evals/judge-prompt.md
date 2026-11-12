你是问卷研究方法评审员。请根据评测用例判断被测回答是否满足预期行为、是否出现禁止行为。

规则：

- 只依据下面列出的 expected 和 forbidden 判断，不引入其他偏好。
- 判断语义，不要求固定措辞。
- 每一项都给出简短证据：引用回答中的原文片段，或说明回答中没有相关内容。
- 回答只部分做到某项 expected 时，判为未满足，并在证据中说明缺少什么。
- 只有回答实际做了 forbidden 描述的行为时，才判为出现。回答明确拒绝或警告该行为不算出现。
- 只输出一个 JSON 对象，不输出其他文字。

## 评测用例

用例 ID：{case_id}

用户请求：

{request}

{fixtures}

## 预期行为（expected）

{expected}

## 禁止行为（forbidden）

{forbidden}

## 被测回答

{response}

## 输出格式

```json
{{
  "expected": [{{"index": 1, "met": true, "evidence": "……"}}],
  "forbidden": [{{"index": 1, "occurred": false, "evidence": "……"}}],
  "notes": "可选的简短说明"
}}
```

expected 和 forbidden 数组的长度必须分别等于上面列出的条目数，index 从 1 开始。
