#!/usr/bin/env python3
"""检查官方产品 survey-zh-default 格式的 Markdown 问卷。

用法：
    python scripts/check_render.py questionnaire.md [--spec spec.yaml] [--codes default|explicit|ids]
        [--format text|yaml|json]

不提供 --spec 时，检查格式、题号引用、编码唯一、排他、开放填空和占位符。

提供 --spec 时，另外要求 Markdown 与 QuestionnaireSpec 的参考渲染（render_markdown.py）在语义上一致
（adapter.semantic-preserved）：题目和顺序、题型规则、显示条件、题干、选项编码和文字、程序标签、
矩阵行、评分范围、引用、循环和程序说明都必须一致。比较时忽略空白和程序标签顺序。--codes 与渲染时使用的编码方式相同。

存在 error 时退出码为 1。当前产品的问卷格式被 overlay 替换时，本脚本不适用。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_lib import ZH_PROFILE, DRAFT_WORD_RE, PLACEHOLDER_RE, Profile, Report, load_profile_by_id, load_yaml  # noqa: E402

SRC_FMT = "references/products/survey-zh-default/questionnaire-format.md"
SRC_SPEC = "references/services/validation/spec-integrity.md"
SRC_ADAPTER = "references/contracts/artifacts.md"

def heading_regex(profile: Profile) -> re.Pattern:
    """由产品配置的 headings.question 生成解析正则。

    模板中的占位符换成捕获组；占位符之外的固定文字（括号、空格）原样匹配，
    这样换语言或换括号只需改 profile.yaml，不用改脚本。
    """
    from spec_lib import ZH_PROFILE as _zh
    template = (profile.data.get("headings") or {}).get("question") or \
        (_zh.data.get("headings") or {}).get("question")
    parts = re.split(r"(\{[a-z]+\})", template)
    body = []
    for part in parts:
        if part in {"{id}", "{label}", "{condition}", "{prompt}", "{rules}"}:
            body.append({"id": r"([A-Za-z][A-Za-z0-9_-]*)",
                         "label": r"([^\[\]【】]+)",
                         "condition": r"([^\[\]【】]+)",
                         "prompt": r"(.+?)",
                         "rules": r"([^\[\]【】]+)"}[part[1:-1]])
        elif part:
            body.append(re.escape(part))
    return re.compile("^" + "".join(body) + r"\s*$")


HEADING_RE = None  # 兼容旧引用；实际使用 heading_regex(profile)

LABEL_TOKEN_KEYS = ["top", "bottom", "exclusive", "open_fill", "terminate", "fixed", "hidden",
                    "single_page", "reference_options", "loop_items"]


def allowed_labels(profile: Profile) -> set[str]:
    """产品配置里定义的固定程序标签（不含带参数的和跳转类）。"""
    return {profile.token(k) for k in LABEL_TOKEN_KEYS if profile.token(k)}


def is_allowed_label(label: str, profile: Profile) -> bool:
    if label in allowed_labels(profile):
        return True
    # 带参数的标签和跳转：用产品文字做前缀判断，避免把语言写死在正则里
    quota_prefix = profile.token("quota", "配额：{value}", value="").rstrip("：: ")
    jump = re.compile(r"^(跳转至|jump to)\s*[A-Za-z][\w-]*$")
    return label.startswith(quota_prefix) or bool(jump.match(label))
NONE_TEXT_RE = re.compile(r"以上都没有|以上均无|以上都不是|以上皆无|都没有")


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def strip_comments(md: str) -> str:
    """HTML 注释不属于问卷正文；替换为等量换行以保持行号。"""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), md, flags=re.S)


def parse(md: str, profile: Profile = ZH_PROFILE):
    """返回题目列表和格式不合格的标题。

    每道题：{id, label, cond, prompt, rules, line, tables:[{header, rows, line}], text:[非空正文行]}
    """
    questions = []
    bad_headings = []
    current = None
    in_code = False
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            i += 1
            continue
        if line.startswith("#####"):
            m = heading_regex(profile).match(line)
            if not m:
                bad_headings.append((i + 1, line))
                current = None
            else:
                current = {
                    "id": m.group(1), "label": m.group(2), "cond": m.group(3), "prompt": m.group(4),
                    "rules": m.group(5), "line": i + 1, "tables": [], "text": [],
                }
                questions.append(current)
            i += 1
            continue
        if line.startswith("#"):
            current = None
            i += 1
            continue
        if line.strip().startswith("|") and current is not None:
            start = i
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            header = split_row(block[0])
            body = [split_row(b) for b in block[2:]] if len(block) >= 2 else []
            current["tables"].append({"header": header, "rows": body, "line": start + 1})
            continue
        if current is not None and line.strip():
            current["text"].append(line.strip())
        i += 1
    return questions, bad_headings


def resolve_ref(name: str, known: list[str]) -> str | None:
    """把条件中的名称（题号或 题号_行）解析为已知题号；取最长匹配。"""
    best = None
    for qid in known:
        if name == qid or name.startswith(qid + "_"):
            if best is None or len(qid) > len(best):
                best = qid
    return best


def split_conditions(cond: str, profile: Profile) -> list[str]:
    """按产品配置的连词拆分显示条件。"""
    if cond == profile.token("all", "ALL"):
        return []
    joiner_all = profile.token("conjunction_all")
    joiner_any = profile.token("conjunction_any")
    pattern = "|".join(re.escape(x) for x in {joiner_all, joiner_any, joiner_all.strip(), joiner_any.strip()} if x)
    return [p for p in re.split(pattern, cond) if p.strip()]


def condition_refs(cond: str, profile: Profile) -> list[str]:
    """取出条件中引用的题目名称。比较运算符和“已作答”类标记由产品文字决定。"""
    names = []
    answered = profile.token_prefix("answered").strip()
    for part in split_conditions(cond, profile):
        part = part.strip()
        for marker in ("=", "≠") + ((answered,) if answered else ()):
            idx = part.find(marker)
            if idx > 0:
                part = part[:idx]
                break
        names.append(part.strip())
    return names


def rule_references(rules: str, profile: Profile) -> list[str]:
    """取出题型规则中引用的题号（引用选项、循环出示）。"""
    ref_prefixes = [profile.token_prefix("reference_options"), profile.token_prefix("loop_items")]
    filters = [profile.token(f"filter_{k}") for k in ("selected", "not_selected", "all")]
    pattern = (r"(?:" + "|".join(re.escape(p) for p in ref_prefixes if p) + r")"
               r"\s*([A-Za-z][A-Za-z0-9_-]*?)"
               r"\s*(?:" + "|".join(re.escape(f) for f in filters if f) + r")")
    return re.findall(pattern, rules)


# 正文之外的阻断区和限制区，按官方模板约定可以列出待确认内容，不检查占位符。
def appendix_re(profile: Profile) -> re.Pattern:
    names = "|".join(re.escape(n) for n in profile.appendices())
    return re.compile(rf"^#{{1,3}}\s*({names})\s*$")


def split_appendix(md: str, profile: Profile = ZH_PROFILE) -> tuple[str, str]:
    """把正文和正文外的“需确认项 / 结果解释限制”分开。附录不参与题目解析。"""
    lines = md.splitlines()
    pat = appendix_re(profile)
    for i, line in enumerate(lines):
        if pat.match(line):
            j = i
            # 附录上方的分隔线和空行也属于正文之外，不计入最后一题
            while j > 0 and lines[j - 1].strip() in {"", "---", "***", "___"}:
                j -= 1
            return "\n".join(lines[:j]), "\n".join(lines[i:])
    return md, ""


def scan_placeholders(md: str, report: Report, profile: Profile = ZH_PROFILE) -> None:
    """只扫描正文；附录按约定可以列出待确认事项。"""
    body, _ = split_appendix(md, profile)
    in_code = False
    for ln, line in enumerate(body.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = PLACEHOLDER_RE.search(line)
        if m:
            report.add("spec.no-placeholder", "error", f"Markdown:L{ln}", f"正文包含未解释占位符“{m.group(0)}”。",
                       "替换为实际内容；无法确定时移到正文外的需确认项。", SRC_SPEC)
            continue
        m = DRAFT_WORD_RE.search(line)
        if m:
            cells = split_row(line) if line.strip().startswith("|") else []
            if len(cells) == 3 and not DRAFT_WORD_RE.search(cells[0] + cells[2]):
                report.add("spec.no-placeholder", "warning", f"Markdown:L{ln}", f"选项文字包含“{m.group(0)}”。",
                           "如果这是受访者可选的正式选项，可以保留；如果是未完成内容，替换为实际选项。", SRC_SPEC)
            else:
                report.add("spec.no-placeholder", "error", f"Markdown:L{ln}", f"正文包含未解释占位符“{m.group(0)}”。",
                           "替换为实际内容；无法确定时移到正文外的需确认项。", SRC_SPEC)


def check(md: str, report: Report, profile: Profile = ZH_PROFILE) -> list[dict]:
    md = strip_comments(md)
    body, _ = split_appendix(md, profile)
    questions, bad = parse(body, profile)
    for ln, text in bad:
        report.add("format.heading", "error", f"Markdown:L{ln}",
                   f"题目标题不符合“##### 题号.【标签】【显示条件】题干【题型和规则】”格式：{text[:60]}",
                   "按官方问卷格式补齐四个部分；无显示条件时写【ALL】。", SRC_FMT)
    all_ids = [q["id"] for q in questions]
    option_header, matrix_header = profile.table("options"), profile.table("matrix")
    label_sep = profile.separator("label", "；")
    rule_sep = profile.separator("rule", "，")
    seen: dict[str, int] = {}
    for q in questions:
        qid = q["id"]
        target = f"Markdown.{qid}"
        if qid in seen:
            report.add("spec.id-unique", "error", target, f"题号 {qid} 重复（第 {seen[qid]} 行和第 {q['line']} 行）。",
                       "使用唯一题号。", SRC_SPEC)
        before = list(seen)
        seen.setdefault(qid, q["line"])
        for name in condition_refs(q["cond"], profile):
            ref = resolve_ref(name, all_ids)
            if ref is None or ref == qid or ref not in before:
                report.add("spec.logic-reference", "error", target,
                           f"{qid} 的显示条件引用了不存在或位于后面的题目 {name}。", "修正显示条件中的题号。", SRC_SPEC)
        for name in rule_references(q["rules"], profile):
            if name not in before:
                report.add("spec.logic-reference", "error", target,
                           f"{qid} 引用了不存在或位于后面的题目 {name}。", "修正引用题号。", SRC_SPEC)
        rule_parts = {x for x in re.split(re.escape(rule_sep), q["rules"]) if x}
        type_labels = profile.data.get("type_labels") or {}
        multi_label = type_labels.get("multi", "多选")
        matrix_label = type_labels.get("matrix_scale", "矩阵评分")
        choice_labels = {type_labels.get(k, k) for k in ("single", "multi", "ranking")}
        is_multi = multi_label in rule_parts
        is_choice = bool(rule_parts & choice_labels) and matrix_label not in rule_parts
        reference_prefix = profile.token_prefix("reference_options", "引用{q}{filter}选项")
        piped = bool(reference_prefix) and any(p.startswith(reference_prefix) for p in rule_parts)
        option_tables = []
        for t in q["tables"]:
            if t["header"] == option_header:
                option_tables.append(t)
            elif t["header"] != matrix_header:
                report.add("format.option-table", "error", f"Markdown:L{t['line']}",
                           f"{qid} 的表头应为“编码 | 选项细节 | 程序标签”或“子题 | 行内容 | 程序标签”，实际为 {t['header']}。",
                           "使用官方三列表格。", SRC_FMT)
                continue
            for r_i, row in enumerate(t["rows"]):
                if len(row) != 3:
                    report.add("format.option-table", "error", f"Markdown:L{t['line'] + 2 + r_i}",
                               f"{qid} 的表格行有 {len(row)} 列，应为 3 列。", "补齐或合并单元格；选项文本不放入程序标签列。", SRC_FMT)
        if is_choice and not option_tables and not piped:
            report.add("spec.choice-options", "error", target, f"{qid} 是选择题，但没有选项表。", "补充选项表。", SRC_SPEC)
        codes_seen: set[str] = set()
        q["options"] = []
        for t in option_tables:
            for row in t["rows"]:
                if len(row) != 3:
                    continue
                code, text, labels_s = row
                labels = [x.strip() for x in re.split(re.escape(label_sep), labels_s) if x.strip()]
                q["options"].append((code, text, labels))
                if code in codes_seen:
                    report.add("spec.code-unique", "error", target, f"{qid} 的编码 {code} 重复。", "同一题内使用不同编码。", SRC_SPEC)
                codes_seen.add(code)
                for lab in labels:
                    if not is_allowed_label(lab, profile):
                        report.add("format.program-label", "warning", target,
                                   f"{qid} 使用了未定义的程序标签“{lab}”。",
                                   "使用官方程序标签；选项说明文字放在“选项细节”列。", SRC_FMT)
                # 语言相关的文字判断只在中文产品下启用；其他产品的选项文字由该产品自己的 format 规则负责
                if profile.language.startswith("zh"):
                    if is_multi and NONE_TEXT_RE.search(text) and profile.token("exclusive", "排他") not in labels:
                        report.add("spec.exclusive-none", "error", f"{target}.{code}",
                                   f"{qid} 的“{text}”没有标注{profile.token('exclusive', '排他')}。",
                                   f"在程序标签中加入“{profile.token('exclusive', '排他')}”。", SRC_SPEC)
                    if text.startswith("其他") and profile.token("open_fill", "开放填空") not in labels \
                            and profile.token("terminate", "终止访问") not in labels:
                        report.add("spec.other-text", "warning", f"{target}.{code}",
                                   f"{qid} 的“{text}”没有标注{profile.token('open_fill', '开放填空')}。",
                                   f"加入“{profile.token('open_fill', '开放填空')}”并在选项细节中说明填写方式。", SRC_SPEC)
    scan_placeholders(md, report, profile)
    return questions


# ------------------------------------------------------------------ 与规格比较
def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def signature(q: dict, profile: Profile = ZH_PROFILE) -> dict:
    """题目的可比较语义：忽略空白和程序标签顺序。分隔符按产品配置切分。"""
    label_sep = profile.separator("label")
    rule_sep = profile.separator("rule")
    tables = []
    for t in q["tables"]:
        rows = []
        for row in t["rows"]:
            if len(row) == 3:
                labels = tuple(sorted(x.strip() for x in re.split(re.escape(label_sep), row[2]) if x.strip()))
                rows.append((_norm(row[0]), _norm(row[1]), labels))
            else:
                rows.append(tuple(_norm(c) for c in row))
        tables.append((tuple(t["header"]), tuple(rows)))
    return {
        "标签": _norm(q["label"]),
        "显示条件": _norm(q["cond"]),
        "题干": _norm(q["prompt"]),
        "题型规则": tuple(sorted(_norm(x) for x in re.split(re.escape(rule_sep), q["rules"]) if x.strip())),
        "表格": tuple(tables),
        "说明行": tuple(_norm(x) for x in q["text"]),
    }


def compare(questions: list[dict], spec: dict, codes_mode: str, report: Report,
            profile: Profile | None = None) -> None:
    import render_markdown  # 延迟导入，避免循环依赖

    profile = profile or ZH_PROFILE
    renderer = render_markdown.Renderer(spec, codes_mode, profile=profile)
    expected_md = renderer.render()
    for r in renderer.report.results:
        report.results.append(r)
    expected_body, _ = split_appendix(strip_comments(expected_md), profile)
    expected, _ = parse(expected_body, profile)
    exp_ids = [q["id"] for q in expected]
    got_ids = [q["id"] for q in questions]
    if got_ids != exp_ids:
        missing = [x for x in exp_ids if x not in got_ids]
        extra = [x for x in got_ids if x not in exp_ids]
        detail = []
        if missing:
            detail.append(f"缺少 {missing}")
        if extra:
            detail.append(f"多出 {extra}")
        if not detail:
            detail.append("题目顺序不同")
        report.add("adapter.semantic-preserved", "error", "Markdown",
                   "Markdown 与 QuestionnaireSpec 的题目不一致：" + "；".join(detail) + "。",
                   "重新渲染，或同步修改 QuestionnaireSpec。", SRC_ADAPTER)
    got = {q["id"]: q for q in questions}
    for eq in expected:
        gq = got.get(eq["id"])
        if gq is None:
            continue
        es, gs = signature(eq, profile), signature(gq, profile)
        for key in es:
            if es[key] != gs[key]:
                report.add("adapter.semantic-preserved", "error", f"Markdown.{eq['id']}",
                           f"{eq['id']} 的{key}与规格的参考渲染不一致。",
                           f"按 QuestionnaireSpec 修正{key}，或先修改规格再重新渲染。可用 render_markdown.py 生成参考版本对照。",
                           SRC_ADAPTER)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--spec", type=Path)
    ap.add_argument("--codes", choices=["default", "explicit", "ids"], default="default")
    ap.add_argument("--product", help="产品 id，默认为 survey-zh-default")
    ap.add_argument("--profile", type=Path, help="直接指定 profile.yaml")
    ap.add_argument("--format", choices=["text", "yaml", "json"], default="text")
    args = ap.parse_args(argv)
    import render_markdown
    profile = render_markdown.resolve_profile(args.profile, args.product)
    report = Report()
    questions = check(args.markdown.read_text(encoding="utf-8"), report, profile)
    if args.spec:
        compare(questions, load_yaml(args.spec), args.codes, report, profile)
    report.dump(args.format)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
