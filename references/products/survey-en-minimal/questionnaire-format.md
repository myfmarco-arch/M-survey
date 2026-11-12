# Questionnaire format (minimal English)

Layout is driven by `profile.yaml`. This file explains the conventions in prose.

A question heading has four parts: id, label, condition, prompt, then the rules in brackets:

```markdown
##### Q12. (Feature use) (Q8=1/2) Which of the following have you used? (Multiple choice, randomize options, required)
```

- Write `(ALL)` when a question is always shown.
- Do not use square brackets in the heading template: square brackets mean "unresolved placeholder" in the contracts and trigger `spec.no-placeholder`.
- Conditions use codes: `Q8=1/2` (selected 1 or 2), `Q8≠91` (did not select 91), `Q3=4-5` (rating 4 to 5).
- Type names come from `type_labels` in `profile.yaml`.

Options use the three-column table named in `profile.yaml` (`Code | Option text | Program tags`). The default codes for "other" and "none" are **90 / 91** in this product.

Program tags come from `tokens` in `profile.yaml`: `pin bottom`, `exclusive`, `open text`, `terminate`, `quota: …`.

Rating questions print a line under the heading, formatted by `tokens.scale_line`.

Place anything that blocks delivery in a section titled `Items to confirm` after the questionnaire body. That section is not scanned for placeholders.
