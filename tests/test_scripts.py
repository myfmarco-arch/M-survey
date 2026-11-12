"""脚本回归测试。运行：python -m unittest discover -s tests"""
from __future__ import annotations

import copy
import io
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_render  # noqa: E402
import render_markdown  # noqa: E402
import validate_spec  # noqa: E402
from spec_lib import Report, load_yaml  # noqa: E402

EXAMPLE = ROOT / "examples" / "expense-app-autocat" / "spec.yaml"


def find_q(spec: dict, qid: str) -> dict:
    for s in spec["sections"]:
        for q in s["questions"]:
            if q["id"] == qid:
                return q
    raise KeyError(qid)


def rule_ids(spec: dict) -> set[str]:
    return {r.rule_id for r in validate_spec.validate(spec).results}


class ValidateSpecTest(unittest.TestCase):
    def setUp(self):
        self.base = load_yaml(EXAMPLE)

    def mutate(self):
        return copy.deepcopy(self.base)

    def test_example_is_clean(self):
        report = validate_spec.validate(self.base)
        self.assertEqual([r.as_dict() for r in report.results], [])

    def test_schema_error_stops_early(self):
        spec = self.mutate()
        find_q(spec, "Q1")["response_type"] = "dropdown"
        self.assertEqual(rule_ids(spec), {"spec.schema"})

    def test_duplicate_question_id(self):
        spec = self.mutate()
        find_q(spec, "Q9")["id"] = "Q8"
        self.assertIn("spec.id-unique", rule_ids(spec))

    def test_duplicate_option_and_code(self):
        spec = self.mutate()
        q = find_q(spec, "Q1")
        q["options"][1]["id"] = "o1"
        self.assertIn("spec.option-id-unique", rule_ids(spec))
        spec = self.mutate()
        q = find_q(spec, "Q1")
        q["options"][0]["code"] = 5
        q["options"][1]["code"] = 5
        self.assertIn("spec.code-unique", rule_ids(spec))

    def test_rq_reference(self):
        spec = self.mutate()
        find_q(spec, "Q3")["purpose"]["refs"] = ["RQ9"]
        ids = rule_ids(spec)
        self.assertIn("spec.rq-reference", ids)
        spec = self.mutate()
        for qid in ("Q8",):
            find_q(spec, qid)["purpose"]["refs"] = ["RQ1"]
        self.assertIn("evidence.metric-linked", rule_ids(spec))

    def test_forward_reference(self):
        spec = self.mutate()
        find_q(spec, "Q2")["display_logic"] = {"all": [{"question": "Q5", "selected_any": ["o1"]}]}
        self.assertIn("spec.logic-reference", rule_ids(spec))

    def test_missing_option_in_logic(self):
        spec = self.mutate()
        find_q(spec, "Q3")["display_logic"]["all"][0]["selected_any"] = ["o1", "o9"]
        self.assertIn("spec.logic-option-reference", rule_ids(spec))

    def test_logic_type(self):
        spec = self.mutate()
        find_q(spec, "Q9")["display_logic"] = {"all": [{"question": "Q3", "selected_any": ["o1"]}]}
        self.assertIn("spec.logic-type", rule_ids(spec))
        spec = self.mutate()
        find_q(spec, "Q9")["display_logic"] = {"all": [{"question": "Q3", "value_between": [4, 7]}]}
        self.assertIn("spec.logic-type", rule_ids(spec))

    def test_pipe_token(self):
        spec = self.mutate()
        find_q(spec, "Q3")["prompt"] = "{{item}}满意吗？"
        self.assertIn("spec.pipe-token", rule_ids(spec))

    def test_exclusive_none(self):
        spec = self.mutate()
        find_q(spec, "Q5")["options"][-1]["exclusive"] = False
        self.assertIn("spec.exclusive-none", rule_ids(spec))

    def test_other_text(self):
        spec = self.mutate()
        find_q(spec, "Q5")["options"][-2]["open_text"] = False
        self.assertIn("spec.other-text", rule_ids(spec))
        spec = self.mutate()
        other = find_q(spec, "Q5")["options"][-2]
        other["open_text"] = False
        other["terminate"] = True
        self.assertNotIn("spec.other-text", rule_ids(spec))

    def test_select_range(self):
        spec = self.mutate()
        find_q(spec, "Q8")["response_rules"]["max_select"] = 9
        self.assertIn("spec.select-range", rule_ids(spec))

    def test_experience_required(self):
        spec = self.mutate()
        del find_q(spec, "Q3")["experience_gate"]
        self.assertIn("measurement.experience-required", rule_ids(spec))
        spec = self.mutate()
        del find_q(spec, "Q3")["display_logic"]
        self.assertIn("measurement.experience-required", rule_ids(spec))
        spec = self.mutate()
        find_q(spec, "Q3")["experience_gate"] = "Q1"
        self.assertIn("measurement.experience-required", rule_ids(spec))

    def test_placeholder(self):
        spec = self.mutate()
        find_q(spec, "Q1")["prompt"] = "您是否知道[功能名称]？"
        self.assertIn("spec.no-placeholder", rule_ids(spec))
        for mark in ("⟨场景行为⟩", "〈场景行为〉", "〔场景行为〕"):
            spec = self.mutate()
            find_q(spec, "Q1")["prompt"] = f"您是否有过这样的经历：{mark}？"
            self.assertIn("spec.no-placeholder", rule_ids(spec), mark)
        self.assertIn("spec.no-placeholder", rule_ids(spec))
        spec = self.mutate()
        find_q(spec, "Q1")["options"][0]["text"] = "待定"
        self.assertIn("spec.no-placeholder", rule_ids(spec))

    def test_fielded_requires_codes(self):
        spec = self.mutate()
        spec["meta"]["status"] = "fielded"
        self.assertIn("spec.fielded-codes", rule_ids(spec))

    def test_terminate_position(self):
        spec = self.mutate()
        find_q(spec, "Q1")["options"][1]["terminate"] = True
        self.assertIn("spec.terminate-position", rule_ids(spec))

    def test_scale_consistency(self):
        spec = self.mutate()
        find_q(spec, "Q3")["scale"]["max"] = 7
        self.assertIn("measurement.scale-consistency", rule_ids(spec))


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.spec = load_yaml(EXAMPLE)

    def render(self, spec, **kw):
        r = render_markdown.Renderer(spec, kw.get("codes", "default"), 98, 99)
        return r, r.render()

    def test_example_matches_committed_markdown(self):
        _, md = self.render(self.spec)
        committed = (EXAMPLE.parent / "03-questionnaire.md").read_text(encoding="utf-8")
        self.assertEqual(md, committed, "examples 中的问卷与 spec 渲染结果不一致；运行 render_markdown.py 重新生成。")

    def test_render_passes_check_and_compare(self):
        _, md = self.render(self.spec)
        report = Report()
        qs = check_render.check(md, report)
        check_render.compare(qs, self.spec, "default", report)
        self.assertEqual([r.as_dict() for r in report.results], [])

    def test_default_codes(self):
        _, md = self.render(self.spec)
        self.assertIn("| 98 | 其他，请注明____ | 置底；开放填空 |", md)
        self.assertIn("| 99 | 以上都没有遇到 | 置底；排他 |", md)
        self.assertIn("【Q2=1/2且Q5≠99】", md)

    def test_existing_codes_preserved(self):
        spec = copy.deepcopy(self.spec)
        q = find_q(spec, "Q5")
        q["options"][-2]["code"] = 7
        q["options"][-1]["code"] = 0
        _, md = self.render(spec)
        self.assertIn("| 7 | 其他，请注明____ |", md)
        self.assertIn("| 0 | 以上都没有遇到 |", md)
        self.assertIn("Q5≠0", md)

    def test_explicit_mode_requires_codes(self):
        r, _ = self.render(self.spec, codes="explicit")
        results = [x for x in r.report.results if x.rule_id == "spec.code-required"]
        self.assertTrue(results)
        # 用错模式时不应刷屏：每题最多一条，且给出改法
        self.assertLessEqual(len(results), len(self.spec["sections"][1]["questions"]))
        self.assertIn("--codes default", results[0].resolution)

    def test_dont_know_without_code(self):
        spec = copy.deepcopy(self.spec)
        del find_q(spec, "Q2")["options"][-1]["code"]
        r, _ = self.render(spec)
        self.assertIn("spec.code-required", {x.rule_id for x in r.report.results})

    def test_code_collision_after_defaults(self):
        spec = copy.deepcopy(self.spec)
        find_q(spec, "Q5")["options"][0]["code"] = 98
        r, _ = self.render(spec)
        self.assertIn("spec.code-unique", {x.rule_id for x in r.report.results})


class CheckRenderTest(unittest.TestCase):
    def setUp(self):
        spec = load_yaml(EXAMPLE)
        self.spec = spec
        self.md = render_markdown.Renderer(spec, "default", 98, 99).render()

    def ids_for(self, md, spec=None):
        report = Report()
        qs = check_render.check(md, report)
        if spec is not None:
            check_render.compare(qs, spec, "default", report)
        return {r.rule_id for r in report.results}

    def test_bad_heading(self):
        md = self.md.replace("##### Q3.【总体满意度】【Q2=1/2】", "##### Q3.【总体满意度】")
        self.assertIn("format.heading", self.ids_for(md))

    def test_missing_exclusive(self):
        md = self.md.replace("| 99 | 以上都没有遇到 | 置底；排他 |", "| 99 | 以上都没有遇到 | 置底 |")
        self.assertIn("spec.exclusive-none", self.ids_for(md))

    def test_table_columns(self):
        md = self.md.replace("| 1 | 知道 |  |", "| 1 | 知道 |")
        self.assertIn("format.option-table", self.ids_for(md))

    def test_unknown_label(self):
        md = self.md.replace("| 1 | 知道 |  |", "| 1 | 知道 | 优先展示 |")
        self.assertIn("format.program-label", self.ids_for(md))

    def test_forward_reference(self):
        md = self.md.replace("【Q2=1/2】总体而言", "【Q7=1】总体而言")
        self.assertIn("spec.logic-reference", self.ids_for(md))

    def test_placeholder(self):
        md = self.md.replace("您的年龄是？", "您的年龄是？（待确认）")
        self.assertIn("spec.no-placeholder", self.ids_for(md))

    def test_appendix_may_list_blockers(self):
        md = self.md + "\n\n---\n\n## 需确认项\n\n| 事项 | 说明 |\n|---|---|\n| 概念材料 | ⟨概念材料⟩ 待补 |\n"
        report = Report()
        qs = check_render.check(md, report)
        check_render.compare(qs, self.spec, "default", report)
        self.assertEqual([r.as_dict() for r in report.results], [])

    def test_semantic_drift_detected(self):
        md = self.md.replace("| 98 | 其他，请注明____ | 置底；开放填空 |\n| 99 | 以上都没有遇到 |",
                             "| 6 | 其他，请注明____ | 置底；开放填空 |\n| 99 | 以上都没有遇到 |")
        self.assertIn("adapter.semantic-preserved", self.ids_for(md, self.spec))


class CliTest(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)

    def test_validate_cli_yaml(self):
        out = self.run_script("scripts/validate_spec.py", str(EXAMPLE), "--format", "yaml")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_check_repo(self):
        out = self.run_script("scripts/check_repo.py")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)




class RunEvalsTest(unittest.TestCase):
    def setUp(self):
        import run_evals
        self.re = run_evals
        self.case = {"id": "x", "request": "设计问卷", "expected": ["a", "b", "c"], "forbidden": ["f"],
                     "fixtures": ["evals/fixtures/audit-sample.md"]}

    def j(self, met, occurred):
        return {"expected": [{"index": i + 1, "met": m} for i, m in enumerate(met)],
                "forbidden": [{"index": i + 1, "occurred": o} for i, o in enumerate(occurred)]}

    def test_verdicts(self):
        v = self.re.run_verdict
        self.assertEqual(v(self.case, self.j([True, True, True], [False]))[0], "pass")
        self.assertEqual(v(self.case, self.j([True, False, True], [False]))[0], "partial")
        self.assertEqual(v(self.case, self.j([False, False, True], [False]))[0], "fail")
        self.assertEqual(v(self.case, self.j([True, True, True], [True]))[0], "fail")
        self.assertEqual(v(self.case, self.j([True, True], [False]))[0], "invalid")
        self.assertEqual(v(self.case, self.j([True, None, True], [False]))[0], "invalid")

    def test_answer_key_hidden_from_skill_but_shown_to_judge(self):
        prompt = self.re.skill_prompt(self.case)
        self.assertNotIn("参考答案", prompt)
        self.assertIn("##### Q2.", prompt)
        judge = self.re.judge_prompt(self.case, "回答")
        self.assertIn("参考答案", judge)

    def test_all_suites_load(self):
        for name in ("conformance", "modules", "product", "overlay:references/overlays/example-custom/overlay.yaml"):
            label, cases, _ = self.re.load_suite(name)
            self.assertTrue(cases, label)


class CheckRepoNegativeTest(unittest.TestCase):
    """在临时副本中制造问题，确认 check_repo.py 能发现。"""

    def run_on_copy(self, mutate):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "repo"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "runs", "__pycache__"))
            mutate(dst)
            out = subprocess.run([sys.executable, "scripts/check_repo.py"], cwd=dst, capture_output=True, text=True)
            return out.returncode, out.stdout

    def test_broken_link(self):
        def m(d):
            p = d / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n[坏链接](references/nope.md)\n", encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("链接失效", out)

    def test_undefined_eval_target(self):
        def m(d):
            p = d / "evals/conformance/cases.yaml"
            p.write_text(p.read_text(encoding="utf-8").replace("targets: [privacy.minor]", "targets: [privacy.minors]"), encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("privacy.minors", out)

    def test_method_missing_section(self):
        def m(d):
            p = d / "references/modules/methods/kano.md"
            p.write_text(p.read_text(encoding="utf-8").replace("## 不允许的结论", "## 禁止的结论"), encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("kano.md", out)

    def test_version_mismatch(self):
        def m(d):
            p = d / "product.yaml"
            text = p.read_text(encoding="utf-8")
            current = re.search(r"^version: (.+)$", text, re.M).group(1)
            p.write_text(text.replace(f"version: {current}", "version: 9.9.9"), encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("版本不一致", out)

    def test_overlay_without_mode(self):
        def m(d):
            p = d / "references/overlays/example-custom/overlay.yaml"
            p.write_text(p.read_text(encoding="utf-8").replace("    mode: extend        # 保留官方撰写规范，只追加或覆盖冲突的条目\n", ""), encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("mode", out)

    def test_stale_example(self):
        def m(d):
            p = d / "examples/expense-app-autocat/03-questionnaire.md"
            p.write_text(p.read_text(encoding="utf-8").replace("不到 3 个月", "不到三个月"), encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("渲染结果不一致", out)


class ReviewRegressionTest(unittest.TestCase):
    """独立审查发现的问题，修复后保持不回退。"""

    def setUp(self):
        self.base = load_yaml(EXAMPLE)
        self.md = render_markdown.Renderer(self.base, "default", 98, 99).render()

    def mutate(self):
        return copy.deepcopy(self.base)

    def compare_ids(self, md, spec=None, codes="default"):
        report = Report()
        qs = check_render.check(md, report)
        check_render.compare(qs, spec or self.base, codes, report)
        return {r.rule_id for r in report.results if r.severity == "error"}

    # --- 使用资格
    def test_gate_with_non_user_option_fails(self):
        spec = self.mutate()
        find_q(spec, "Q3")["display_logic"]["all"][0]["selected_any"] = ["o3"]
        self.assertIn("measurement.experience-required", rule_ids(spec))

    def test_gate_with_partial_terminate_fails(self):
        spec = self.mutate()
        q2 = find_q(spec, "Q2")
        q2["options"][2]["terminate"] = True  # 只终止“没有使用过”，“不记得”仍会进入
        del find_q(spec, "Q3")["display_logic"]
        self.assertIn("measurement.experience-required", rule_ids(spec))

    def test_gate_without_eligible_fails(self):
        spec = self.mutate()
        for o in find_q(spec, "Q2")["options"]:
            o.pop("eligible", None)
        self.assertIn("measurement.experience-required", rule_ids(spec))

    def test_gate_full_terminate_passes(self):
        spec = self.mutate()
        q2 = find_q(spec, "Q2")
        for o in q2["options"][2:]:
            o["terminate"] = True
        q2["purpose"]["type"] = "eligibility"
        del find_q(spec, "Q3")["display_logic"]
        self.assertNotIn("measurement.experience-required", rule_ids(spec))

    # --- check_render 语义比较
    def test_compare_detects_condition_values(self):
        self.assertIn("adapter.semantic-preserved", self.compare_ids(self.md.replace("【Q2=1/2】总体而言", "【Q2=3】总体而言")))

    def test_compare_detects_type_change(self):
        md = self.md.replace("以下哪些情况？【多选，选项随机，必答】", "以下哪些情况？【单选，选项随机，必答】")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_compare_detects_scale_change(self):
        md = self.md.replace("评分：1–5 分；1 = 非常不满意，5 = 非常满意", "评分：0–10 分；0 = 非常满意，10 = 非常不满意")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_compare_detects_option_text_and_label(self):
        md = self.md.replace("| 2 | 18–24 岁 |  |", "| 2 | 18–25 岁 | 终止访问 |")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_compare_detects_matrix_row_removed(self):
        md = self.md.replace("| Q4_r4 | 同一商家的账单分类前后一致 |  |\n", "")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_compare_detects_loop_source(self):
        md = self.md.replace("循环出示Q5已选项", "循环出示Q1已选项")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_compare_detects_program_note_removed(self):
        md = self.md.replace("程序说明：Q5 只选了一种情况", "说明：Q5 只选了一种情况")
        self.assertIn("adapter.semantic-preserved", self.compare_ids(md))

    def test_non_q_ids_supported(self):
        spec = self.mutate()
        spec["sections"][0]["questions"][0]["id"] = "S_AGE"
        md = render_markdown.Renderer(spec, "default", 98, 99).render()
        self.assertEqual(self.compare_ids(md, spec), set())

    # --- 编码模式
    def test_ids_mode(self):
        md = render_markdown.Renderer(self.base, "ids", 98, 99).render()
        self.assertIn("| other | 其他，请注明____ | 置底；开放填空 |", md)
        self.assertIn("Q5≠none", md)
        self.assertEqual(self.compare_ids(md, codes="ids"), set())

    def test_piped_own_option_codes_do_not_clash(self):
        spec = self.mutate()
        q7 = find_q(spec, "Q7")
        q7["options"] = [{"id": "unsure", "text": "说不清哪一项影响最大", "semantic": "dont_know", "code": 97}]
        q7["options"].insert(0, {"id": "extra", "text": "以上都差不多"})
        r = render_markdown.Renderer(spec, "default", 98, 99)
        codes = r.codes["Q7"]
        self.assertNotIn(codes["extra"], {1, 2, 3, 4, 5})
        self.assertNotIn("spec.code-unique", {x.rule_id for x in r.report.results})

    # --- 其他边界
    def test_min_select_exceeds_options(self):
        spec = self.mutate()
        find_q(spec, "Q8")["response_rules"]["min_select"] = 9
        self.assertIn("spec.select-range", rule_ids(spec))

    def test_placeholder_false_positives(self):
        spec = self.mutate()
        find_q(spec, "Q1")["prompt"] = "您是否用过 Todoist 或 XXXL 尺码的功能说明？"
        self.assertNotIn("spec.no-placeholder", rule_ids(spec))
        spec = self.mutate()
        find_q(spec, "D1")["options"].append({"id": "o5", "text": "还没想好/待定"})
        results = validate_spec.validate(spec).results
        sev = {r.severity for r in results if r.rule_id == "spec.no-placeholder"}
        self.assertEqual(sev, {"warning"})

    def test_multiline_prompt_and_paragraph_intro(self):
        spec = self.mutate()
        find_q(spec, "Q1")["prompt"] = "Please read:\n账小满有一项功能。"
        spec["meta"]["intro"] = "第一段。\n\n第二段。"
        md = render_markdown.Renderer(spec, "default", 98, 99).render()
        self.assertIn("【ALL】Please read: 账小满有一项功能。【", md)
        self.assertIn("第一段。\n\n第二段。", md)

    def test_single_choice_matrix_row_condition(self):
        spec = self.mutate()
        q4 = find_q(spec, "Q4")
        del q4["scale"]
        q4["options"] = [{"id": "y", "text": "符合"}, {"id": "n", "text": "不符合"}]
        find_q(spec, "Q9")["display_logic"] = {"all": [{"question": "Q4", "row": "r1", "selected_any": ["n"]}]}
        ids = rule_ids(spec)
        self.assertNotIn("spec.logic-type", ids)
        self.assertNotIn("spec.logic-option-reference", ids)

    def test_forward_pipe_token_rule(self):
        spec = self.mutate()
        find_q(spec, "Q3")["prompt"] = "您在 {{Q9}} 中提到的内容？"
        self.assertIn("spec.pipe-token", rule_ids(spec))

    def test_string_boolean_judgement_invalid(self):
        import run_evals
        case = {"expected": ["a"], "forbidden": ["f"]}
        j = {"expected": [{"index": 1, "met": "false"}], "forbidden": [{"index": 1, "occurred": False}]}
        self.assertEqual(run_evals.run_verdict(case, j)[0], "invalid")


class CheckRepoOverlayTest(unittest.TestCase):
    run_on_copy = CheckRepoNegativeTest.run_on_copy

    def test_overlay_forbidden_ops(self):
        def m(d):
            p = d / "references/overlays/example-custom/overlay.yaml"
            p.write_text(p.read_text(encoding="utf-8") + "\nvalidation:\n  replace: []\noverride: {}\n", encoding="utf-8")
        code, out = self.run_on_copy(m)
        self.assertEqual(code, 1)
        self.assertIn("validation.replace", out)
        self.assertIn("override", out)


class ProductLayerTest(unittest.TestCase):
    """产品抽象必须真的可替换：同一份 spec 用两个产品渲染，结果只在产品配置允许的地方不同。"""

    def setUp(self):
        self.spec = load_yaml(EXAMPLE)

    def render(self, product):
        from spec_lib import product_profile
        profile = product_profile(product)
        return render_markdown.Renderer(self.spec, "default", profile=profile), profile

    def test_two_products_differ_only_in_configured_words(self):
        zh, zh_profile = self.render("survey-zh-default")
        en, en_profile = self.render("survey-en-minimal")
        zh_md, en_md = zh.render(), en.render()
        # 结构相同：题目数、表格列数一致
        self.assertEqual(zh_md.count("##### "), en_md.count("##### "))
        # 产品文字不同：题型、必答、表头、编码
        self.assertIn("【单选，必答】", zh_md)
        self.assertIn("(Single choice, required)", en_md)
        self.assertIn("| 编码 | 选项细节 | 程序标签 |", zh_md)
        self.assertIn("| Code | Option text | Program tags |", en_md)
        self.assertIn("| 98 |", zh_md)
        self.assertIn("| 90 |", en_md)
        # 默认编码来自产品配置，而不是框架写死
        self.assertEqual(zh_profile.codes(), {"other": 98, "none": 99})
        self.assertEqual(en_profile.codes(), {"other": 90, "none": 91})

    def test_both_products_pass_checks(self):
        for product in ("survey-zh-default", "survey-en-minimal"):
            r, profile = self.render(product)
            md = r.render()
            report = Report()
            qs = check_render.check(md, report, profile)
            check_render.compare(qs, self.spec, "default", report, profile)
            self.assertEqual([x.as_dict() for x in report.results], [], product)

    def test_skill_md_stays_product_neutral(self):
        """SKILL.md 不应包含只属于某个产品的文字，否则换产品就得改入口。"""
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        body = text.split("---", 2)[-1]
        banned = ["98", "99", "三列", "必答", "选答", "中文问卷", "Markdown 问卷"]
        hits = [b for b in banned if b in body]
        self.assertEqual(hits, [], f"SKILL.md 正文出现了产品专属内容：{hits}")

    def test_local_override_is_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("local.yaml", ignore)
        self.assertTrue((ROOT / "local.example.yaml").exists())

    def test_current_product_prefers_local(self):
        import tempfile
        import spec_lib
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.yaml"
            local.write_text("schema_version: 1\nproduct: survey-en-minimal\n", encoding="utf-8")
            original = spec_lib.ROOT
            try:
                spec_lib.ROOT = Path(tmp)
                self.assertEqual(spec_lib.current_product(), "survey-en-minimal")
            finally:
                spec_lib.ROOT = original


class ContractManifestTest(CliTest):
    def test_manifest_matches_contracts(self):
        out = self.run_script("scripts/contract_manifest.py", "check")
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_manifest_detects_contract_edit(self):
        def m(d):
            p = d / "references/contracts/artifacts.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n<!-- edit -->\n", encoding="utf-8")
        code, out = CheckRepoNegativeTest.run_on_copy(self, m)
        self.assertEqual(code, 1)
        self.assertIn("contract_manifest", out)


class ProfileRobustnessTest(unittest.TestCase):
    """产品配置缺失或写错时应当报错，而不是静默退回中文。"""

    def setUp(self):
        self.spec = load_yaml(EXAMPLE)

    def test_missing_token_raises(self):
        from spec_lib import Profile
        p = Profile({"id": "x", "language": "en", "codes": {"other": 1, "none": 2},
                     "tables": {"options": ["a", "b", "c"], "matrix": ["a", "b", "c"]},
                     "type_labels": {"single": "S"}, "tokens": {}, "headings": {}, "separators": {"rule": ",", "label": ";"}})
        with self.assertRaises(Profile.Missing):
            p.token("required")

    def test_missing_codes_raises(self):
        from spec_lib import Profile
        p = Profile({"id": "x", "codes": {"other": 1}, "tables": {}, "type_labels": {}, "tokens": {},
                     "headings": {}, "separators": {}})
        with self.assertRaises(Profile.Missing):
            p.codes()

    def test_unknown_product_raises(self):
        from spec_lib import Profile, product_profile
        with self.assertRaises(Profile.Missing):
            product_profile("does-not-exist")

    def test_profile_flag_works(self):
        import check_render
        out = subprocess.run([sys.executable, "scripts/render_markdown.py", str(EXAMPLE),
                              "--profile", "references/products/survey-en-minimal/profile.yaml"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        rendered = out.stdout
        self.assertIn("(Single choice, required)", rendered)
        report = Report()
        qs = check_render.check(rendered, report, check_render.ZH_PROFILE.__class__ and
                                __import__("spec_lib").load_profile(ROOT / "references/products/survey-en-minimal/profile.yaml"))
        self.assertEqual(qs[0]["id"], "S1")

    def test_answered_condition_renders_and_checks_in_english(self):
        spec = copy.deepcopy(self.spec)
        q = find_q(spec, "Q9")
        q["display_logic"] = {"all": [{"question": "Q8", "answered": True}]}
        from spec_lib import product_profile
        import check_render
        profile = product_profile("survey-en-minimal")
        md = render_markdown.Renderer(spec, "default", profile=profile).render()
        self.assertIn("Q8 answered", md)
        report = Report()
        qs = check_render.check(md, report, profile)
        check_render.compare(qs, spec, "default", report, profile)
        self.assertEqual([x.as_dict() for x in report.results if x.severity == "error"], [])

    def test_custom_separators_round_trip(self):
        from spec_lib import Profile
        base = load_yaml(ROOT / "references/products/survey-zh-default/profile.yaml")
        data = copy.deepcopy(base)
        data["separators"] = {"rule": " | ", "label": " / "}
        profile = Profile(data)
        import check_render
        md = render_markdown.Renderer(self.spec, "default", profile=profile).render()
        report = Report()
        qs = check_render.check(md, report, profile)
        check_render.compare(qs, self.spec, "default", report, profile)
        self.assertEqual([x.as_dict() for x in report.results if x.severity == "error"], [])

    def test_local_products_registration(self):
        import tempfile
        import spec_lib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "product.yaml").write_text(
                "default_product: p1\nproducts:\n  p1:\n    profile: p1/profile.yaml\n", encoding="utf-8")
            (root / "local.yaml").write_text(
                "schema_version: 1\nproduct: p2\nproducts:\n  p2:\n    profile: p2/profile.yaml\n", encoding="utf-8")
            original = spec_lib.ROOT
            try:
                spec_lib.ROOT = root
                default_id, products = spec_lib.product_registry()
                self.assertEqual(default_id, "p1")
                self.assertIn("p2", products)
                self.assertEqual(spec_lib.current_product(), "p2")
            finally:
                spec_lib.ROOT = original


if __name__ == "__main__":
    unittest.main()
