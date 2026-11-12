#!/usr/bin/env python3
"""将 QuestionnaireSpec 渲染为官方产品 survey-zh-default 的 Markdown 问卷正文。

用法：
    python scripts/render_markdown.py spec.yaml [-o questionnaire.md]
        [--codes default|explicit|ids] [--other-code 98] [--none-code 99] [--force]

--codes default   缺少编码时按官方默认编码分配：普通选项 1、2、3……，其他 98，以上都没有 99。
                  已写明的编码保持不变。
--codes explicit  不分配默认编码；任何选项缺少编码时报错（用于已回收问卷或已导出平台编码）。
--codes ids       编码列显示选项标识（o1、other、none……），用于编码由平台生成、设计阶段不分配数字的情况。

选择方式见 SKILL.md“可选的脚本检查”：按当前生效的编码配置选择，不默认使用 default。
当前产品的问卷格式被 overlay 替换时，本脚本不适用。

渲染前先运行 validate_spec 的全部检查；存在 error 时不渲染，除非使用 --force。
本脚本是 Markdown 适配器在官方产品下的参考实现，overlay 可以使用自己的渲染方式。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_lib import (  # noqa: E402
    PIPE_TOKEN_RE,
    SPECIAL_SEMANTICS,
    ZH_PROFILE,
    Profile,
    Report,
    SpecIndex,
    ROOT,
    assign_default_codes,
    load_profile,
    product_profile,
    load_yaml,
    option_semantic,
)
import validate_spec  # noqa: E402

SRC = "references/services/validation/spec-integrity.md"
CJK = r"　-〿㐀-鿿＀-￯“”‘’"
CJK_GAP_RE = re.compile(rf"(?<=[{CJK}])\s+(?=[{CJK}])")


class RenderError(Exception):
    pass


class Renderer:
    def __init__(self, spec: dict, codes_mode: str, other_code=None, none_code=None, profile: Profile | None = None):
        self.profile = profile or ZH_PROFILE
        if other_code is None:
            other_code = self.profile.codes()["other"]
        if none_code is None:
            none_code = self.profile.codes()["none"]
        self.spec = spec
        self.idx = SpecIndex(spec)
        self.codes_mode = codes_mode
        self.other_code = other_code
        self.none_code = none_code
        self.report = Report()
        self.codes: dict[str, dict[str, object]] = {}
        for qid in self.idx.order:
            self.codes[qid] = self._codes_for(qid)

    # ---------- 编码 ----------
    def _codes_for(self, qid: str) -> dict[str, object]:
        q = self.idx.questions[qid]
        src = (q.get("options_from") or {}).get("question")
        piped = {}
        if src in self.codes:
            piped = {o["id"]: self.codes[src].get(o["id"]) for o in self.idx.resolved_options(src)
                     if option_semantic(o) == "regular"}
        if self.codes_mode == "ids":
            codes = {o["id"]: o["id"] for o in q.get("options", []) or []}
        elif self.codes_mode == "explicit":
            codes = {o["id"]: o.get("code") for o in q.get("options", []) or []}
        else:
            codes = assign_default_codes(q, self.other_code, self.none_code, reserved=piped.values())
        seen: dict[object, str] = {code: f"{src}.{oid}" for oid, code in piped.items() if code is not None}
        missing: list[str] = []
        for o in q.get("options", []) or []:
            code = codes.get(o["id"])
            if code is None:
                missing.append(f"{qid}.{o['id']}（{o['text']}）")
                continue
            if code in seen:
                self.report.add(
                    "spec.code-unique", "error", f"QuestionnaireSpec.{qid}",
                    f"{qid} 渲染后编码 {code} 同时用于选项 {seen[code]} 和 {o['id']}。",
                    "为冲突选项写明不同的显式编码。", SRC)
            seen[code] = o["id"]
        if missing:
            # 缺编码通常是一个整体选择错误（用错 --codes），合并成一条并给出改法，避免刷出几十条同类错误
            preview = "、".join(missing[:3]) + (f" 等 {len(missing)} 项" if len(missing) > 3 else "")
            self.report.add(
                "spec.code-required", "error", f"QuestionnaireSpec.{qid}",
                f"在 --codes {self.codes_mode} 下，{preview}没有编码。",
                "编码没有在 spec 中写全时，改用 --codes default（按当前产品默认值分配）或 --codes ids"
                "（编码列显示选项标识）；只有 spec 已写明全部编码、或问卷已回收时，才用 --codes explicit。",
                SRC)
        return codes

    def code_of(self, qid: str, oid: str):
        if oid in self.codes.get(qid, {}):
            return self.codes[qid][oid]
        q = self.idx.questions.get(qid, {})
        src = (q.get("options_from") or {}).get("question")
        if src:
            return self.code_of(src, oid)
        return oid

    # ---------- 条件 ----------
    def condition_text(self, q: dict) -> str:
        logic = q.get("display_logic") or {}
        if not logic:
            return self.profile.token("all", "ALL")
        joiner = self.profile.token("conjunction_all", "且") if "all" in logic else self.profile.token("conjunction_any", "或")
        parts = []
        for c in logic.get("all") or logic.get("any") or []:
            ref = c["question"]
            name = f"{ref}_{c['row']}" if c.get("row") else ref
            if "selected_any" in c:
                parts.append(f"{name}=" + "/".join(str(self.code_of(ref, o)) for o in c["selected_any"]))
            elif "selected_none" in c:
                parts.append(f"{name}≠" + "/".join(str(self.code_of(ref, o)) for o in c["selected_none"]))
            elif "value_between" in c:
                lo, hi = c["value_between"]
                lo, hi = _num(lo), _num(hi)
                parts.append(f"{name}={lo}" if lo == hi else f"{name}={lo}-{hi}")
            elif "answered" in c:
                # token 自带前置分隔符（中文“已作答”，英文“ answered”），避免语言之间拼接出错
                parts.append(f"{name}{self.profile.token('answered', '已作答')}" if c["answered"]
                             else f"{name}{self.profile.token('unanswered', '未作答')}")
        return joiner.join(parts)

    # ---------- 题目 ----------
    def type_text(self, q: dict) -> str:
        rtype = q["response_type"]
        rules = q.get("response_rules", {}) or {}
        lg = self.profile
        parts = [lg.type_label(rtype, has_scale=bool(q.get("scale")))]
        if q.get("options_from"):
            p = q["options_from"]
            parts.append(lg.token("reference_options", "引用{q}{filter}选项", q=p["question"], filter=lg.token(f"filter_{p['filter']}", "")))
        if q.get("loop_over"):
            p = q["loop_over"]
            parts.append(lg.token("loop_items", "循环出示{q}{filter}项", q=p["question"], filter=lg.token(f"filter_{p['filter']}", "")))
        if rules.get("randomize_options"):
            parts.append(lg.token("randomize_options", "选项随机"))
        if rules.get("randomize_rows"):
            parts.append(lg.token("randomize_rows", "行随机"))
        mn, mx = rules.get("min_select"), rules.get("max_select")
        if rtype == "multi":
            if mn is not None and mx is not None and mn == mx:
                parts.append(lg.token("select_exactly", "限选{n}项", n=mx))
            else:
                if mn is not None and mn > 1:
                    parts.append(lg.token("select_min", "至少选{n}项", n=mn))
                if mx is not None:
                    parts.append(lg.token("select_max", "最多选{n}项", n=mx))
        if rtype == "ranking" and rules.get("rank_count"):
            parts.append(lg.token("rank_top", "排出前{n}项", n=rules["rank_count"]))
        if rules.get("single_page"):
            parts.append(lg.token("single_page", "单独一页"))
        if rules.get("hidden"):
            parts.append(lg.token("hidden", "隐藏"))
        if rtype != "info":
            parts.append(lg.token("required", "必答") if rules.get("required", True) else lg.token("optional", "选答"))
        return lg.separator("rule", "，").join(parts)

    def render_text(self, text: str) -> str:
        """渲染单行文本：替换引用标记，合并换行，去掉中文之间多余的空白。"""
        def sub(m):
            token = m.group(1)
            lg = self.profile
            if token == "item":
                return lg.token("loop_item_placeholder", "「当前循环项」")
            return lg.token("pipe_placeholder", "「{q} 的回答」", q=token)
        text = PIPE_TOKEN_RE.sub(sub, (text or "").strip())
        text = re.sub(r"\s*\n\s*", " ", text)
        return CJK_GAP_RE.sub("", text)

    def render_paragraphs(self, text: str) -> list[str]:
        """渲染多段文本：空行分段，段内按单行规则处理。"""
        paras = [p for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]
        out: list[str] = []
        for p in paras:
            out += [self.render_text(p), ""]
        return out

    def option_rows(self, qid: str, q: dict) -> list[str]:
        rows = []
        for o in q.get("options", []) or []:
            sem = option_semantic(o)
            text = self.render_text(o["text"])
            if o.get("open_text") and self.profile.token("option_note_suffix", "，请注明____").strip() not in text:
                text += self.profile.token("option_note_suffix", "，请注明____")
            labels = []
            pos = o.get("position") or ("bottom" if sem in SPECIAL_SEMANTICS else None)
            lg = self.profile
            if pos == "top":
                labels.append(lg.token("top", "置顶"))
            elif pos == "bottom":
                labels.append(lg.token("bottom", "置底"))
            elif pos == "fixed":
                labels.append(lg.token("fixed", "不随机"))
            if o.get("exclusive"):
                labels.append(lg.token("exclusive", "排他"))
            if o.get("open_text"):
                labels.append(lg.token("open_fill", "开放填空"))
            if o.get("terminate"):
                labels.append(lg.token("terminate", "终止访问"))
            if o.get("quota"):
                labels.append(lg.token("quota", "配额：{value}", value=o["quota"]))
            rows.append(f"| {self.code_of(qid, o['id'])} | {_cell(text)} | {lg.separator('label', '；').join(labels)} |")
        return rows

    def render_question(self, qid: str) -> list[str]:
        q = self.idx.questions[qid]
        lg = self.profile
        out = [lg.heading("question", "##### {id}.【{label}】【{condition}】{prompt}【{rules}】",
                          id=qid, label=q["label"], condition=self.condition_text(q),
                          prompt=self.render_text(q["prompt"]), rules=self.type_text(q)), ""]
        rtype = q["response_type"]
        if q.get("options_from"):
            p = q["options_from"]
            out += [lg.token("reference_line", "选项：引用 {q} 的{filter}选项，编码沿用 {q}。",
                             q=p["question"], filter=lg.token(f"filter_{p['filter']}", "")), ""]
        if rtype == "matrix":
            out += ["| " + " | ".join(lg.table("matrix")) + " |", "|---|---|---|"]
            for r in q.get("rows", []):
                out.append(f"| {qid}_{r['id']} | {_cell(self.render_text(r['text']))} |  |")
            out.append("")
        sc = q.get("scale")
        if sc:
            line = lg.token("scale_line", "评分：{min}–{max} 分；{min} = {low}，{max} = {high}",
                            min=sc["min"], max=sc["max"], low=sc["low"], high=sc["high"])
            if sc.get("mid"):
                line += lg.token("scale_mid", "；中点 = {mid}", mid=sc["mid"])
            out += [line, ""]
        if rtype == "numeric" and q.get("numeric"):
            n = q["numeric"]
            rng = f"{_num(n.get('min', ''))}–{_num(n.get('max', ''))}" if "min" in n or "max" in n else "不限"
            line = lg.token("numeric_line", "填写范围：{range}{unit}", range=rng, unit=n.get("unit", ""))
            if n.get("integer"):
                line += lg.token("integer", "；整数")
            out += [line, ""]
        if q.get("options"):
            out += ["| " + " | ".join(lg.table("options")) + " |", "|---:|---|---|"] + self.option_rows(qid, q) + [""]
        if q.get("program_note"):
            out += [lg.token("program_note", "程序说明：{text}", text=self.render_text(q["program_note"])), ""]
        return out

    def render(self) -> str:
        meta = self.spec["meta"]
        out = [f"# {meta['title']}", ""]
        lg = self.profile
        if meta.get("intro"):
            out += ["### " + lg.heading("intro", "卷首语"), ""] + self.render_paragraphs(meta["intro"])
        for n, section in enumerate(self.spec["sections"], 1):
            out += ["## " + lg.heading("part", "Part {n}. {title}", n=n, title=section["title"]), ""]
            for q in section.get("questions", []):
                out += self.render_question(q["id"])
        return "\n".join(out).rstrip() + "\n"


def _cell(text: str) -> str:
    return text.replace("|", "｜").replace("\n", " ")


def _num(x):
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--codes", choices=["default", "explicit", "ids"], default="default")
    ap.add_argument("--product", help="产品 id，默认读取 product.yaml 的 product")
    ap.add_argument("--profile", type=Path, help="直接指定 profile.yaml，优先于 --product")
    ap.add_argument("--other-code", type=_code_arg)
    ap.add_argument("--none-code", type=_code_arg)
    ap.add_argument("--force", action="store_true", help="存在验证 error 时仍然渲染（仅用于调试）")
    args = ap.parse_args(argv)

    profile = resolve_profile(args.profile, args.product)
    spec = load_yaml(args.spec)
    report = validate_spec.validate(spec)
    if report.errors and not args.force:
        report.dump("text", sys.stderr)
        sys.stderr.write("\n规格存在 error，未渲染。修复后重试。\n")
        return 1
    r = Renderer(spec, args.codes, args.other_code, args.none_code, profile=profile)
    md = r.render()
    if r.report.errors and not args.force:
        r.report.dump("text", sys.stderr)
        sys.stderr.write("\n编码存在 error，未渲染。\n")
        return 1
    if args.out:
        args.out.write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    return 0


def resolve_profile(profile_path: Path | None, product_id: str | None) -> Profile:
    """按 --profile、--product、local.yaml、product.yaml 的顺序确定产品配置。"""
    if profile_path:
        return load_profile(profile_path)
    return product_profile(product_id)


def _code_arg(value: str):
    return int(value) if value.lstrip("-").isdigit() else value


if __name__ == "__main__":
    sys.exit(main())
