# 示例平台编码（replace）

本文件以 `replace` 方式完整替换官方 [默认编码](../../products/survey-zh-default/coding.md)。启用后，官方的 `98/99` 默认值不再生效。

## 编码来源

问卷平台负责生成底层编码。设计阶段不分配数字编码。

- QuestionnaireSpec 中不填写 `code`，只使用稳定的选项标识和语义：`other`、`none`、`dont_know`、`not_applicable` 和 `refused`。
- Markdown 问卷的“编码”列填写选项标识（例如 `o1`、`other`、`none`），并在问卷说明中注明“编码由平台生成”。
- 平台导出后，建立“选项标识 → 平台编码”的映射表，随数据一起保存。
- 修改已回收问卷时，保留已有平台编码，不重新导出覆盖。

使用参考脚本时，设计阶段用 `--codes ids`（编码列显示选项标识）；平台导出编码并写入 spec 后，改用 `--codes explicit`。

## 语义要求

以下要求与官方产品相同，替换编码数字不改变它们：

- 题目和选项标识唯一、稳定。
- “其他”与对应的开放文本字段关联。
- “以上都没有”与其他普通选项排他。
- 不知道、不适用、拒答和系统缺失的语义分开。
- 随机展示不改变编码。

## 启用

在根目录 `product.yaml` 中加入：

```yaml
overlays:
  - references/overlays/example-custom/overlay.yaml
```
