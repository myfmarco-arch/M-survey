#!/usr/bin/env python3
"""检查 QuestionnaireSpec YAML 的结构、逻辑引用和可机器判断的测量规则。

用法：
    python scripts/validate_spec.py path/to/spec.yaml [--format text|yaml|json]

输出遵循 references/contracts/validation-contract.md 的 ValidationResult 格式。
存在 error 时退出码为 1。脚本只覆盖 spec.* 和部分 measurement.* / evidence.* 规则，
不能替代模型对方法前提、证据和隐私风险的判断。
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_lib import (  # noqa: E402
    CHOICE_TYPES,
    DRAFT_WORD_RE,
    EXCLUSIVE_SEMANTICS,
    PIPE_TOKEN_RE,
    PLACEHOLDER_RE,
    Report,
    SpecIndex,
    iter_questions,
    load_schema,
    load_yaml,
    option_semantic,
)

SRC_SPEC = "references/services/validation/spec-integrity.md"
SRC_MEAS = "references/services/validation/measurement-integrity.md"
SRC_EVID = "references/services/validation/evidence-integrity.md"


def schema_check(spec: dict, report: Report) -> bool:
    try:
        import jsonschema
    except ImportError:
        sys.exit("缺少依赖 jsonschema。请运行：pip install -r requirements.txt")
    validator = jsonschema.Draft7Validator(load_schema())
    ok = True
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.absolute_path)):
        ok = False
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        report.add(
            "spec.schema",
            "error",
            f"QuestionnaireSpec:{path}",
            f"结构不符合 schema：{err.message}",
            "按 schemas/questionnaire-spec.schema.json 修正字段名称、类型或必填项。",
            SRC_SPEC,
        )
    return ok


def check_ids(spec: dict, report: Report) -> None:
    sec_ids = Counter(s.get("id") for s in spec.get("sections", []))
    for sid, n in sec_ids.items():
        if n > 1:
            report.add("spec.id-unique", "error", f"QuestionnaireSpec.{sid}", f"模块标识 {sid} 重复 {n} 次。",
                       "为每个模块使用唯一标识。", SRC_SPEC)
    q_ids = Counter(q.get("id") for _, q in iter_questions(spec))
    for qid, n in q_ids.items():
        if n > 1:
            report.add("spec.id-unique", "error", f"QuestionnaireSpec.{qid}", f"题目标识 {qid} 重复 {n} 次。",
                       "为每道题使用唯一且稳定的标识；新增题目使用不冲突的编号。", SRC_SPEC)
    vars_ = Counter(q.get("var") for _, q in iter_questions(spec) if q.get("var"))
    for v, n in vars_.items():
        if n > 1:
            report.add("spec.id-unique", "error", f"QuestionnaireSpec.var:{v}", f"变量名 {v} 重复 {n} 次。",
                       "为每道题使用唯一变量名。", SRC_SPEC)
    for _, q in iter_questions(spec):
        qid = q.get("id")
        for kind in ("options", "rows"):
            ids = Counter(o.get("id") for o in q.get(kind, []) or [])
            for oid, n in ids.items():
                if n > 1:
                    report.add("spec.option-id-unique", "error", f"QuestionnaireSpec.{qid}.{oid}",
                               f"{qid} 的{ '选项' if kind == 'options' else '矩阵行' }标识 {oid} 重复。",
                               "同一题内的选项和矩阵行标识必须唯一。", SRC_SPEC)
        codes = [o["code"] for o in q.get("options", []) or [] if "code" in o]
        for code, n in Counter(codes).items():
            if n > 1:
                report.add("spec.code-unique", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 的编码 {code} 被 {n} 个选项使用。", "同一题内每个选项使用不同编码。", SRC_SPEC)


def check_research_links(spec: dict, report: Report) -> None:
    rq_ids = {rq["id"] for rq in spec.get("research_questions", [])}
    covered: set[str] = set()
    for _, q in iter_questions(spec):
        qid = q["id"]
        purpose = q.get("purpose", {})
        refs = purpose.get("refs", []) or []
        if purpose.get("type") == "research_question" and not refs:
            report.add("spec.rq-reference", "error", f"QuestionnaireSpec.{qid}",
                       f"{qid} 的用途是研究问题，但没有指向任何研究问题。",
                       "在 purpose.refs 中填写对应的 RQ 标识，或改为样本控制、逻辑等用途。", SRC_SPEC)
        for ref in refs:
            if ref not in rq_ids:
                report.add("spec.rq-reference", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 引用了不存在的研究问题 {ref}。", "修正 purpose.refs 或补充研究问题。", SRC_SPEC)
            covered.add(ref)
    for rq in sorted(rq_ids - covered):
        report.add("evidence.metric-linked", "warning", f"ResearchBrief.{rq}",
                   f"研究问题 {rq} 没有任何题目对应。",
                   "增加对应测量，或说明该问题由行为数据等其他来源回答。", SRC_EVID)


def _ref_check(idx: SpecIndex, report: Report, qid: str, ref: str, what: str,
               rule: str = "spec.logic-reference") -> bool:
    if ref not in idx.questions:
        report.add(rule, "error", f"QuestionnaireSpec.{qid}",
                   f"{qid} 的{what}引用了不存在的题目 {ref}。", "修正引用题号。", SRC_SPEC)
        return False
    if idx.position(ref) >= idx.position(qid):
        report.add(rule, "error", f"QuestionnaireSpec.{qid}",
                   f"{qid} 的{what}引用了同题或后续题目 {ref}。",
                   "逻辑只能引用前面已作答的题目；调整题目顺序或引用对象。", SRC_SPEC)
        return False
    return True


def check_logic(idx: SpecIndex, report: Report) -> None:
    for qid in idx.order:
        q = idx.questions[qid]
        logic = q.get("display_logic") or {}
        for cond in (logic.get("all") or []) + (logic.get("any") or []):
            ref = cond.get("question")
            if not _ref_check(idx, report, qid, ref, "显示条件"):
                continue
            src = idx.questions[ref]
            rtype = src.get("response_type")
            if "row" in cond:
                if rtype != "matrix" or cond["row"] not in {r.get("id") for r in src.get("rows", []) or []}:
                    report.add("spec.logic-option-reference", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 的显示条件引用了 {ref} 中不存在的矩阵行 {cond['row']}。",
                               "使用被引用矩阵题中存在的行标识。", SRC_SPEC)
                    continue
            elif rtype == "matrix" and "answered" not in cond:
                report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 对矩阵题 {ref} 设置条件时没有指定矩阵行。", "在条件中填写 row。", SRC_SPEC)
                continue
            if rtype == "matrix" and ("selected_any" in cond or "selected_none" in cond):
                if src.get("scale"):
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 对评分矩阵 {ref} 使用了选项条件。", "评分矩阵使用 value_between。", SRC_SPEC)
                    continue
                valid = {o.get("id") for o in src.get("options", []) or []}
                for oid in cond.get("selected_any", []) + cond.get("selected_none", []):
                    if oid not in valid:
                        report.add("spec.logic-option-reference", "error", f"QuestionnaireSpec.{qid}",
                                   f"{qid} 的显示条件引用了 {ref} 中不存在的选项 {oid}。",
                                   "使用被引用题目中存在的选项标识。", SRC_SPEC)
                continue
            if "selected_any" in cond or "selected_none" in cond:
                if rtype not in CHOICE_TYPES:
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 对 {ref}（{rtype}）使用了选项条件。",
                               "选项条件只用于单选、多选或排序题；评分和数值题使用 value_between。", SRC_SPEC)
                    continue
                valid = idx.option_ids(ref)
                for oid in cond.get("selected_any", []) + cond.get("selected_none", []):
                    if oid not in valid:
                        report.add("spec.logic-option-reference", "error", f"QuestionnaireSpec.{qid}",
                                   f"{qid} 的显示条件引用了 {ref} 中不存在的选项 {oid}。",
                                   "使用被引用题目中存在的选项标识。", SRC_SPEC)
            if "value_between" in cond:
                if rtype not in {"scale", "numeric", "matrix"} or (rtype == "matrix" and not src.get("scale")):
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 对 {ref}（{rtype}）使用了数值区间条件。",
                               "数值区间条件只用于评分、数值或矩阵题。", SRC_SPEC)
                lo, hi = cond["value_between"]
                if lo > hi:
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 的数值区间 [{lo}, {hi}] 下限大于上限。", "修正区间。", SRC_SPEC)
                sc = src.get("scale")
                if sc and (lo < sc["min"] or hi > sc["max"]):
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 的数值区间 [{lo}, {hi}] 超出 {ref} 的评分范围 {sc['min']}–{sc['max']}。",
                               "使用评分范围内的值。", SRC_SPEC)
        for key, what in (("options_from", "选项引用"), ("loop_over", "循环")):
            pipe = q.get(key)
            if pipe and _ref_check(idx, report, qid, pipe.get("question"), what):
                if idx.questions[pipe["question"]].get("response_type") not in CHOICE_TYPES:
                    report.add("spec.logic-type", "error", f"QuestionnaireSpec.{qid}",
                               f"{qid} 的{what}来源 {pipe['question']} 不是选择题。",
                               "只从单选、多选或排序题引用选项。", SRC_SPEC)
        texts = [q.get("prompt", "")] + [o.get("text", "") for o in q.get("options", []) or []] + \
                [r.get("text", "") for r in q.get("rows", []) or []]
        for text in texts:
            for token in PIPE_TOKEN_RE.findall(text):
                if token == "item":
                    if not q.get("loop_over"):
                        report.add("spec.pipe-token", "error", f"QuestionnaireSpec.{qid}",
                                   f"{qid} 使用了 {{{{item}}}}，但没有设置 loop_over。",
                                   "设置 loop_over，或删除循环引用标记。", SRC_SPEC)
                else:
                    _ref_check(idx, report, qid, token, "文本引用", rule="spec.pipe-token")


def check_options(idx: SpecIndex, report: Report) -> None:
    for qid in idx.order:
        q = idx.questions[qid]
        rtype = q.get("response_type")
        opts = q.get("options", []) or []
        resolved = idx.resolved_options(qid)
        rules = q.get("response_rules", {}) or {}
        if rtype in CHOICE_TYPES and not q.get("options_from") and len(opts) < 2:
            report.add("spec.choice-options", "error", f"QuestionnaireSpec.{qid}",
                       f"{qid} 是选择题，但只有 {len(opts)} 个选项。", "至少提供两个选项，或改为其他题型。", SRC_SPEC)
        if rtype in {"open_text", "info", "numeric", "scale"} and opts:
            report.add("spec.non-choice-options", "warning", f"QuestionnaireSpec.{qid}",
                       f"{qid} 的题型为 {rtype}，但定义了选项。", "删除选项，或改为选择题。", SRC_SPEC)
        for o in opts:
            sem = option_semantic(o)
            target = f"QuestionnaireSpec.{qid}.{o.get('id')}"
            if rtype == "multi" and sem in EXCLUSIVE_SEMANTICS and not o.get("exclusive"):
                report.add("spec.exclusive-none", "error", target,
                           f"{qid} 的“{o.get('text')}”（{sem}）在多选题中没有设为排他。",
                           "设置 exclusive: true，使其不能与普通选项同时选中。", SRC_SPEC)
            if sem == "regular" and o.get("exclusive") and rtype == "multi":
                report.add("spec.exclusive-none", "info", target,
                           f"{qid} 的普通选项“{o.get('text')}”被设为排他。", "确认该选项确实与其他选项互斥。", SRC_SPEC)
            if sem == "other" and not o.get("open_text") and not o.get("terminate"):
                report.add("spec.other-text", "warning", target,
                           f"{qid} 的“其他”选项没有关联开放文本。", "设置 open_text: true，以便编码遗漏答案。", SRC_SPEC)
            if o.get("terminate"):
                section = idx.section_of[qid]
                if q.get("purpose", {}).get("type") not in {"screening", "eligibility", "consent"} and \
                        section.get("role") != "screening":
                    report.add("spec.terminate-position", "warning", target,
                               f"{qid} 不是甄别或资格题，却设置了终止访问。",
                               "把终止条件移到甄别模块，或说明终止原因。", SRC_SPEC)
        if rtype in {"multi", "ranking"} and not q.get("options_from"):
            n_select = sum(1 for o in resolved if option_semantic(o) not in EXCLUSIVE_SEMANTICS)
            mn, mx = rules.get("min_select"), rules.get("max_select")
            if mn is not None and mx is not None and mn > mx:
                report.add("spec.select-range", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 的最少选择数 {mn} 大于最多选择数 {mx}。", "修正限选范围。", SRC_SPEC)
            if mn is not None and mn > n_select:
                report.add("spec.select-range", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 至少要选 {mn} 项，但只有 {n_select} 个可同时选择的选项。", "修正限选范围。", SRC_SPEC)
            if mx is not None and mx > n_select:
                report.add("spec.select-range", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 最多可选 {mx} 项，但只有 {n_select} 个可同时选择的选项。", "修正限选范围。", SRC_SPEC)
            if rtype == "ranking" and rules.get("rank_count", 0) > n_select:
                report.add("spec.select-range", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 要求排序 {rules['rank_count']} 项，但只有 {n_select} 个选项。", "修正排序数量。", SRC_SPEC)
        if rtype == "single" and rules.get("max_select", 1) != 1:
            report.add("spec.select-range", "error", f"QuestionnaireSpec.{qid}",
                       f"{qid} 是单选题，但 max_select 不是 1。", "改为多选题，或删除 max_select。", SRC_SPEC)
        if rtype == "scale" and not q.get("scale"):
            report.add("spec.scale-definition", "error", f"QuestionnaireSpec.{qid}",
                       f"{qid} 是评分题，但没有定义分值范围和两端含义。", "填写 scale 的 min、max、low 和 high。", SRC_SPEC)
        sc = q.get("scale")
        if sc and sc["min"] >= sc["max"]:
            report.add("spec.scale-definition", "error", f"QuestionnaireSpec.{qid}",
                       f"{qid} 的评分最小值不小于最大值。", "修正评分范围。", SRC_SPEC)
        if rtype == "matrix":
            if not q.get("rows"):
                report.add("spec.matrix-rows", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 是矩阵题，但没有矩阵行。", "填写 rows。", SRC_SPEC)
            if not q.get("scale") and len(opts) < 2:
                report.add("spec.matrix-rows", "error", f"QuestionnaireSpec.{qid}",
                           f"{qid} 是矩阵题，但没有评分范围或列选项。", "填写 scale 或至少两个 options。", SRC_SPEC)


def check_eligible_usage(idx: SpecIndex, report: Report) -> None:
    gates = {q.get("experience_gate") for q in idx.questions.values() if q.get("experience_gate")}
    for qid in idx.order:
        q = idx.questions[qid]
        if qid not in gates and any(o.get("eligible") for o in q.get("options", []) or []):
            report.add("spec.eligible-usage", "warning", f"QuestionnaireSpec.{qid}",
                       f"{qid} 不是任何题目的 experience_gate，却标记了 eligible 选项。",
                       "删除 eligible，或让相应体验题的 experience_gate 指向本题。", SRC_SPEC)


def check_scale_consistency(idx: SpecIndex, report: Report) -> None:
    by_construct: dict[str, set[tuple]] = {}
    where: dict[str, list[str]] = {}
    for qid in idx.order:
        q = idx.questions[qid]
        sc = q.get("scale")
        if not sc:
            continue
        key = q.get("construct")
        by_construct.setdefault(key, set()).add((sc["min"], sc["max"]))
        where.setdefault(key, []).append(qid)
    for construct, shapes in by_construct.items():
        if len(shapes) > 1:
            report.add("measurement.scale-consistency", "warning", "QuestionnaireSpec." + "/".join(where[construct]),
                       f"测量 {construct} 的评分使用了不同范围：{sorted(shapes)}。",
                       "同类测量统一点数和方向；确需不同评分范围时在 note 中说明理由（例如保留标准量表的原始计分）。", SRC_MEAS)


def check_experience(idx: SpecIndex, report: Report) -> None:
    """使用体验题只能向资格题中选择了 eligible 选项的受访者显示。"""
    for qid in idx.order:
        q = idx.questions[qid]
        if q.get("construct") != "usage_experience":
            continue
        gate = q.get("experience_gate")
        target = f"QuestionnaireSpec.{qid}"

        def fail(message: str, resolution: str) -> None:
            report.add("measurement.experience-required", "error", target, message, resolution, SRC_MEAS)

        if not gate:
            fail(f"{qid} 评价实际使用体验，但没有指明确认使用经历的题目。",
                 "设置 experience_gate，并只向确认使用过的受访者显示本题。")
            continue
        if not _ref_check(idx, report, qid, gate, "使用资格"):
            continue
        g = idx.questions[gate]
        if g.get("construct") != "behavior" or g.get("response_type") not in {"single", "multi"}:
            fail(f"{qid} 的使用资格题 {gate} 不是测量实际行为的单选或多选题。",
                 "使用测量真实使用行为的选择题作为资格题。")
            continue
        g_opts = g.get("options", []) or []
        eligible = {o["id"] for o in g_opts if o.get("eligible")}
        if not eligible:
            fail(f"资格题 {gate} 没有标记表示实际使用的选项。",
                 f"在 {gate} 中为表示“使用过”的选项设置 eligible: true。")
            continue
        # 方式一：资格题终止全部非使用者
        non_eligible = [o for o in g_opts if o["id"] not in eligible]
        if non_eligible and all(o.get("terminate") for o in non_eligible) and not g.get("display_logic"):
            continue
        # 方式二：显示条件（all）中要求资格题选择了 eligible 选项
        conds = (q.get("display_logic") or {}).get("all") or []
        gated = False
        for c in conds:
            if c.get("question") != gate:
                continue
            chosen = set(c.get("selected_any", []))
            if chosen and chosen <= eligible:
                gated = True
            elif chosen:
                fail(f"{qid} 的显示条件包含资格题 {gate} 中不表示实际使用的选项 {sorted(chosen - eligible)}。",
                     f"显示条件只使用 {gate} 中 eligible 的选项 {sorted(eligible)}。")
                gated = None
                break
        if gated is None:
            continue
        # 方式三：从多选资格题的已选使用项引用或循环
        for key in ("loop_over", "options_from"):
            pipe = q.get(key) or {}
            if pipe.get("question") == gate and pipe.get("filter") == "selected":
                regular = {o["id"] for o in g_opts if option_semantic(o) == "regular"}
                if regular and regular <= eligible:
                    gated = True
        if not gated:
            fail(f"{qid} 没有限定为资格题 {gate} 中选择了使用选项的受访者。",
                 f"在 display_logic.all 中加入 {{question: {gate}, selected_any: {sorted(eligible)}}}，"
                 f"或在 {gate} 中终止全部非使用者。")


def check_text(idx: SpecIndex, spec: dict, report: Report) -> None:
    def scan(text: str, target: str, is_option: bool = False) -> None:
        stripped = PIPE_TOKEN_RE.sub("", text or "")
        m = PLACEHOLDER_RE.search(stripped)
        if m:
            report.add("spec.no-placeholder", "error", target, f"文本包含未解释占位符“{m.group(0)}”。",
                       "替换为实际内容；无法确定时移到正文外的需确认项。", SRC_SPEC)
            return
        m = DRAFT_WORD_RE.search(stripped)
        if m:
            if is_option:
                report.add("spec.no-placeholder", "warning", target, f"选项文字包含“{m.group(0)}”。",
                           "如果这是受访者可选的正式选项，可以保留；如果是未完成内容，替换为实际选项。", SRC_SPEC)
            else:
                report.add("spec.no-placeholder", "error", target, f"文本包含未解释占位符“{m.group(0)}”。",
                           "替换为实际内容；无法确定时移到正文外的需确认项。", SRC_SPEC)

    scan(spec.get("meta", {}).get("intro", ""), "QuestionnaireSpec.meta.intro")
    for qid in idx.order:
        q = idx.questions[qid]
        scan(q.get("prompt", ""), f"QuestionnaireSpec.{qid}")
        scan(q.get("label", ""), f"QuestionnaireSpec.{qid}")
        scan(q.get("program_note", ""), f"QuestionnaireSpec.{qid}")
        for o in q.get("options", []) or []:
            scan(o.get("text", ""), f"QuestionnaireSpec.{qid}.{o.get('id')}", is_option=True)
        for r in q.get("rows", []) or []:
            scan(r.get("text", ""), f"QuestionnaireSpec.{qid}.{r.get('id')}", is_option=True)


def check_fielded(spec: dict, idx: SpecIndex, report: Report) -> None:
    if spec.get("meta", {}).get("status") != "fielded":
        return
    for qid in idx.order:
        for o in idx.questions[qid].get("options", []) or []:
            if "code" not in o:
                report.add("spec.fielded-codes", "error", f"QuestionnaireSpec.{qid}.{o.get('id')}",
                           f"问卷已回收，但 {qid} 的选项 {o.get('id')} 没有显式编码。",
                           "已回收问卷的全部选项必须写明现有编码；新增选项使用不冲突的新编码。", SRC_SPEC)


def check_sections(spec: dict, report: Report) -> None:
    for s in spec.get("sections", []):
        if not s.get("questions"):
            report.add("spec.empty-section", "warning", f"QuestionnaireSpec.{s.get('id')}",
                       f"模块 {s.get('id')} 没有题目。", "删除空模块或补充题目。", SRC_SPEC)


def validate(spec: dict) -> Report:
    report = Report()
    if not isinstance(spec, dict):
        report.add("spec.schema", "error", "QuestionnaireSpec", "文件不是 YAML 对象。", "检查文件内容。", SRC_SPEC)
        return report
    if not schema_check(spec, report):
        return report  # 结构错误时不继续，避免连锁误报
    idx = SpecIndex(spec)
    check_ids(spec, report)
    check_research_links(spec, report)
    check_logic(idx, report)
    check_options(idx, report)
    check_scale_consistency(idx, report)
    check_experience(idx, report)
    check_eligible_usage(idx, report)
    check_text(idx, spec, report)
    check_fielded(spec, idx, report)
    check_sections(spec, report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("--format", choices=["text", "yaml", "json"], default="text")
    args = ap.parse_args(argv)
    report = validate(load_yaml(args.spec))
    report.dump(args.format)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
