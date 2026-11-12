# English questionnaire product (minimal)

This is a deliberately small second product. It exists to show that the framework does not depend on the Chinese product: rendering, table headers, type labels, conjunctions and the default codes for "other" / "none" all come from [profile.yaml](profile.yaml), and this product uses **90 / 91** instead of 98 / 99.

It is not a full English style guide. If you need one, copy this directory, rename it, and put your language rules into `writing.md` and `questionnaire-format.md`.

## Files

| File | Purpose |
|---|---|
| [profile.yaml](profile.yaml) | Machine-read settings: codes, tables, labels, tokens, headings |
| [writing.md](writing.md) | Writing rules for respondent-facing text |
| [questionnaire-format.md](questionnaire-format.md) | How the rendered questionnaire is laid out |

Workflow, templates and coding follow the framework defaults unless this directory adds its own files; `product.yaml` lists which files a product provides.

## Trying it

Switch product without touching upstream files by creating a `local.yaml` in the repository root (see [local.example.yaml](../../../local.example.yaml)):

```yaml
product: survey-en-minimal
```

Then render the example spec:

```bash
python scripts/render_markdown.py examples/expense-app-autocat/spec.yaml --product survey-en-minimal
```

The output uses English headings, `(ALL)`, `required` / `optional`, and codes `90` / `91`.
