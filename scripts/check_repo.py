#!/usr/bin/env python3
"""仓库一致性检查。CONTRIBUTING.md 中“发布前检查”的自动化版本。

用法：
    python scripts/check_repo.py

检查内容：YAML 可解析、product.yaml 路径、版本一致、SKILL.md 元数据、Markdown 内链、
CSV 结构和跨文件 ID、方法模块章节、规则标识唯一且被引用的规则都有定义、评测用例结构和覆盖、
overlay 格式、示例规格和渲染结果、本地路径泄漏。存在 error 时退出码为 1。
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec_lib import ROOT, load_yaml  # noqa: E402

import contract_manifest  # noqa: E402
import render_markdown  # noqa: E402
import validate_spec  # noqa: E402
import check_render  # noqa: E402
from spec_lib import Report  # noqa: E402

METHOD_SECTIONS = ["解决的问题", "适用条件", "不适用条件", "必需输入", "设计和样本要求", "产生的输出",
                   "允许的结论", "不允许的结论", "验证规则", "来源与许可"]
RULE_DOMAINS = ("evidence", "measurement", "sampling", "privacy", "spec", "routing", "method", "overlay", "adapter", "format")
RULE_DEF_RE = re.compile(r"^\|\s*`((?:%s)\.[a-z0-9.-]+)`\s*\|" % "|".join(RULE_DOMAINS), re.M)
RULE_REF_RE = re.compile(r"`((?:%s)\.[a-z0-9][a-z0-9.-]*[a-z0-9])`" % "|".join(RULE_DOMAINS))
SKIP_DIRS = {".git", "runs", "__pycache__", "node_modules"}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


class Checker:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def files(pattern: str) -> list[Path]:
    return sorted(p for p in ROOT.rglob(pattern) if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS))


def strip_code(md: str) -> str:
    return re.sub(r"```.*?```", "", md, flags=re.S)


# ------------------------------------------------------------------ 基础
def check_contract_manifest(c: Checker) -> None:
    """合同清单必须与合同文件一致；分叉声明兼容时以清单的 revision 为准。"""
    for problem in contract_manifest.check():
        c.err(problem)


def check_yaml(c: Checker) -> None:
    for p in files("*.yaml"):
        try:
            load_yaml(p)
        except Exception as exc:  # noqa: BLE001
            c.err(f"{rel(p)}：YAML 解析失败：{exc}")


def walk_paths(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in {"trigger", "id", "version", "framework_contract", "default"}:
                continue
            yield from walk_paths(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_paths(v)
    elif isinstance(node, str) and "/" in node:
        yield node


def check_product(c: Checker) -> dict:
    product = load_yaml(ROOT / "product.yaml")
    for key in ("schema_version", "id", "version", "framework_contract", "contracts", "validation", "modules",
                "product", "adapters", "overlays", "evals"):
        if key not in product:
            c.err(f"product.yaml：缺少 {key}")
    for path in walk_paths(product):
        if not (ROOT / path).exists():
            c.err(f"product.yaml：路径不存在：{path}")
    default_id = product.get("default_product")
    products = product.get("products") or {}
    if default_id not in products:
        c.err(f"product.yaml：default_product {default_id} 不在 products 中")
    for pid, files in products.items():
        if not (files or {}).get("profile"):
            c.err(f"product.yaml：产品 {pid} 缺少 profile")
        for key, rel_path in (files or {}).items():
            if key in {"profile", "readme"} or key.endswith("_format") or key in {"workflow", "writing", "coding", "templates", "case_index"}:
                if not (ROOT / rel_path).exists():
                    c.err(f"product.yaml：产品 {pid} 的 {key} 路径不存在：{rel_path}")
    if product.get("product") and product["product"] not in products:
        c.err(f"product.yaml：product {product['product']} 不在 products 中")
    adapters = product.get("adapters", {})
    if adapters.get("default") not in (adapters.get("available") or {}):
        c.err("product.yaml：adapters.default 不在 adapters.available 中")
    if not SEMVER_RE.match(str(product.get("version", ""))):
        c.err("product.yaml：version 不是 x.y.z 格式")
    return product


def check_versions(c: Checker, product: dict) -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
    if not m:
        c.err("SKILL.md：缺少 YAML frontmatter")
        return
    fm = __import__("yaml").safe_load(m.group(1))
    name = fm.get("name", "")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name) or len(name) > 64:
        c.err("SKILL.md：name 必须是不超过 64 字符的小写字母、数字和连字符")
    desc = fm.get("description", "")
    if not desc or len(desc) > 1024:
        c.err(f"SKILL.md：description 为空或超过 1024 字符（当前 {len(desc)}）")
    meta = fm.get("metadata") or {}
    if str(meta.get("version")) != str(product.get("version")):
        c.err(f"版本不一致：SKILL.md {meta.get('version')} ≠ product.yaml {product.get('version')}")
    if meta.get("contract") != product.get("framework_contract"):
        c.err("合同版本不一致：SKILL.md metadata.contract ≠ product.yaml framework_contract")
    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        m2 = re.search(r"^## \[?(\d+\.\d+\.\d+)\]?", changelog.read_text(encoding="utf-8"), re.M)
        if not m2 or m2.group(1) != str(product.get("version")):
            c.err(f"版本不一致：CHANGELOG 最新版本 {m2.group(1) if m2 else '无'} ≠ product.yaml {product.get('version')}")
    else:
        c.err("缺少 CHANGELOG.md")
    if len(skill.splitlines()) > 500:
        c.warn("SKILL.md 超过 500 行，建议拆分到 references/")


def check_links(c: Checker) -> None:
    for p in files("*.md"):
        text = strip_code(p.read_text(encoding="utf-8"))
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0]
            if path and not (p.parent / path).resolve().exists():
                c.err(f"{rel(p)}：链接失效：{target}")


def check_local_paths(c: Checker) -> None:
    pat = re.compile(r"/Users/|/sessions/|C:\\\\Users|Library/Mobile Documents")
    for ext in ("*.md", "*.yaml", "*.py", "*.json", "*.csv"):
        for p in files(ext):
            if p.name == "check_repo.py":
                continue
            if pat.search(p.read_text(encoding="utf-8")):
                c.err(f"{rel(p)}：包含本地绝对路径")


# ------------------------------------------------------------------ CSV 与方法目录
def read_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]
    return [dict(zip(header, r)) | {"__len__": len(r), "__hlen__": len(header)} for r in body]


def expand_q(token: str) -> list[str]:
    m = re.match(r"^(Q-[A-Z]+-)(\d{2})[–-](\d{2})$", token)
    if m:
        return [f"{m.group(1)}{i:02d}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
    return [token]


def check_csv(c: Checker) -> None:
    for p in files("*.csv"):
        rows = read_csv(p)
        bad = [i + 2 for i, r in enumerate(rows) if r["__len__"] != r["__hlen__"]]
        if bad:
            c.err(f"{rel(p)}：第 {bad} 行列数与表头不一致")
        first = list(rows[0].keys())[0] if rows else None
        ids = [r[first] for r in rows]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            c.err(f"{rel(p)}：ID 重复：{dup}")

    mdir = ROOT / "references/modules/methods"
    kdir = ROOT / "references/modules/knowledge"
    catalog_md = (mdir / "catalog.md").read_text(encoding="utf-8")
    items_md = (mdir / "standard-items.md").read_text(encoding="utf-8")
    sources_md = (mdir / "sources.md").read_text(encoding="utf-8")
    md_ids = set(re.findall(r"^\| ([A-DF-Z]\d{2}) \|", catalog_md, re.M))  # E 开头的是文献编号
    csv_ids = {r["id"] for r in read_csv(mdir / "catalog.csv")}
    if md_ids != csv_ids:
        c.err(f"catalog.md 与 catalog.csv 方法 ID 不一致：仅 md {sorted(md_ids - csv_ids)}，仅 csv {sorted(csv_ids - md_ids)}")

    # catalog.md 的映射表 ID 必须都能在标准问法索引中找到
    mapped = set()
    for cell in re.findall(r"^\| ([A-Z]\d{2}[^|]*) \| Q-", catalog_md, re.M):
        for part in re.split(r"[、,;；\s]+", cell.strip()):
            if re.match(r"^[A-Z]\d{2}$", part):
                mapped.add(part)
    if mapped - csv_ids:
        c.err(f"catalog.md 5.1 之前的映射行引用了不存在的方法 ID：{sorted(mapped - csv_ids)}")

    # 标准问法 ID 和标准状态
    md_status = {}
    sec = items_md.split("## 1. 标准问法索引", 1)[1].split("## 2.", 1)[0] if "## 1. 标准问法索引" in items_md else ""
    if not sec:
        c.err("standard-items.md：找不到“## 1. 标准问法索引”章节")
    for row in re.findall(r"^\| [^|]+ \| (Q-[^|]+?) \| [^|]+ \| ([^|]+?) \|$", sec, re.M):
        for q in expand_q(row[0].strip()):
            md_status[q] = row[1].strip()
    qb_status = {}
    for r in read_csv(kdir / "question-bank.csv"):
        for q in r["标准问法ID"].split(";"):
            qb_status[q.strip()] = r["标准状态"].strip()
    if set(md_status) != set(qb_status):
        c.err(f"standard-items.md 与 question-bank.csv 的标准问法 ID 不一致：仅 md {sorted(set(md_status) - set(qb_status))}，"
              f"仅 csv {sorted(set(qb_status) - set(md_status))}")
    for q in sorted(set(md_status) & set(qb_status)):
        if md_status[q] != qb_status[q]:
            c.err(f"{q} 的标准状态不一致：standard-items.md「{md_status[q]}」，question-bank.csv「{qb_status[q]}」")

    # 文献编号：定义在 sources.md，引用可以出现在任意方法文件
    defined = set(re.findall(r"^\| (E\d+[a-z]?) \|", sources_md, re.M))
    used = set()
    for p in list(mdir.rglob("*.md")) + list(mdir.rglob("*.csv")) + [kdir / "question-bank.csv"]:
        used |= set(re.findall(r"\bE\d+[a-z]?\b", p.read_text(encoding="utf-8")))
    if used - defined:
        c.err(f"引用了未定义的文献编号：{sorted(used - defined)}")
    if defined - used:
        c.warn(f"定义但未引用的文献编号：{sorted(defined - used)}")

    # 澄清问题：问题分布在两个文件中，合计必须与 CSV 一致
    cq_csv = {r["问题 ID"] for r in read_csv(kdir / "clarification-questions.csv")}
    cq_md = set()
    for name in ("clarification-questions.md", "clarification-probes.md"):
        path = kdir / name
        if not path.exists():
            c.err(f"缺少 {rel(path)}")
            continue
        cq_md |= set(re.findall(r"^\| ([CFU]\d{2}) \|", path.read_text(encoding="utf-8"), re.M))
    if cq_csv != cq_md:
        c.err(f"澄清问题 md 与 csv 的 ID 不一致：仅 md {sorted(cq_md - cq_csv)}，仅 csv {sorted(cq_csv - cq_md)}")
    dup = [q for q in cq_md if sum(1 for n in ("clarification-questions.md", "clarification-probes.md")
                                   if re.search(rf"^\| {q} \|", (kdir / n).read_text(encoding="utf-8"), re.M)) > 1]
    if dup:
        c.err(f"澄清问题在两个文件中重复定义：{sorted(dup)}")


# ------------------------------------------------------------------ 方法模块
def check_method_file(c: Checker, path: Path, mid: str) -> None:
    text = path.read_text(encoding="utf-8")
    heads = re.findall(r"^## (.+?)\s*$", text, re.M)
    if heads != METHOD_SECTIONS:
        c.err(f"{rel(path)}：二级标题应依次为 {METHOD_SECTIONS}，实际为 {heads}")
    m = re.match(r"<!-- module: method; id: ([a-z0-9-]+);", text)
    if not m or m.group(1) != mid:
        c.err(f"{rel(path)}：首行元数据 id 应为 {mid}")
    sect = text.split("## 验证规则", 1)[-1].split("## 来源与许可", 1)[0]
    rules = re.findall(r"^\|\s*`([^`]+)`", sect, re.M)
    if not rules:
        c.err(f"{rel(path)}：验证规则章节没有 rule_id 表")
    for r in rules:
        if not r.startswith(f"method.{mid}."):
            c.err(f"{rel(path)}：规则 {r} 应以 method.{mid}. 开头")


PROFILE_KEYS = {"schema_version", "id", "language", "codes", "tables", "type_labels", "tokens", "headings",
                "separators", "appendices"}


def check_profiles(c: Checker, product: dict) -> None:
    seen_ids = set()
    for pid, files in (product.get("products") or {}).items():
        rel_path = (files or {}).get("profile")
        if not rel_path or not (ROOT / rel_path).exists():
            continue
        data = load_yaml(ROOT / rel_path)
        if not isinstance(data, dict):
            c.err(f"{rel_path}：不是有效的产品配置")
            continue
        for key in ("schema_version", "id", "language", "codes", "tables", "type_labels", "tokens", "headings",
                    "separators"):
            if key not in data:
                c.err(f"{rel_path}：缺少 {key}（产品配置的必填字段）")
        if data.get("id") != pid:
            c.err(f"{rel_path}：id {data.get('id')} 与 product.yaml 中的 {pid} 不一致")
        if data.get("id") in seen_ids:
            c.err(f"{rel_path}：产品 id {data.get('id')} 重复")
        seen_ids.add(data.get("id"))
        for key, default in (("options", 3), ("matrix", 3)):
            cols = (data.get("tables") or {}).get(key)
            if not cols or len(cols) != default:
                c.err(f"{rel_path}：tables.{key} 必须有 {default} 列")
        for key in ("other", "none"):
            if key not in (data.get("codes") or {}):
                c.err(f"{rel_path}：codes.{key} 未定义")
        for key in ("single", "multi", "scale", "open_text"):
            if key not in (data.get("type_labels") or {}):
                c.err(f"{rel_path}：type_labels.{key} 未定义")
        for key in ("question", "part", "intro"):
            if key not in (data.get("headings") or {}):
                c.err(f"{rel_path}：headings.{key} 未定义")
        if "[" in str((data.get("headings") or {}).get("question", "")) or \
                "]" in str((data.get("headings") or {}).get("question", "")):
            c.err(f"{rel_path}：headings.question 不能使用方括号——方括号在合同中表示待替换占位符")
        placeholders = set(re.findall(r"\{([a-z_]+)\}", str((data.get("headings") or {}).get("question", ""))))
        if placeholders != {"id", "label", "condition", "prompt", "rules"}:
            c.err(f"{rel_path}：headings.question 必须且只能使用 {{id}} {{label}} {{condition}} {{prompt}} {{rules}}，"
                  f"当前 {sorted(placeholders)}")
        for key in ("rule", "label"):
            if key not in (data.get("separators") or {}):
                c.err(f"{rel_path}：separators.{key} 未定义")
        for key, rel_file in (data.get("files") or {}).items():
            if not (ROOT / rel_path).parent.joinpath(rel_file).exists():
                c.err(f"{rel_path}：files.{key} 指向的文件不存在：{rel_file}")
        if "schema_version" in data and data.get("schema_version") != 1:
            c.err(f"{rel_path}：schema_version 应为 1")


def check_methods(c: Checker, product: dict) -> None:
    methods = product["modules"]["methods"]
    for mid, path in methods.items():
        check_method_file(c, ROOT / path, mid)
    index = (ROOT / product["modules"]["method_index"]).read_text(encoding="utf-8")
    idx_ids = set(re.findall(r"^\| `([a-z0-9-]+)` \|", index, re.M))
    if idx_ids != set(methods):
        c.err(f"方法索引与 product.yaml modules.methods 不一致：{sorted(idx_ids ^ set(methods))}")


# ------------------------------------------------------------------ 规则标识
def collect_rules(c: Checker) -> set[str]:
    where: dict[str, list[str]] = {}
    for p in files("*.md"):
        if not str(rel(p)).startswith("references"):
            continue
        for rid in RULE_DEF_RE.findall(p.read_text(encoding="utf-8")):
            where.setdefault(rid, []).append(rel(p))
    for rid, locs in where.items():
        if len(locs) > 1:
            c.err(f"规则 {rid} 定义了多次：{locs}")
    return set(where)


def check_rule_refs(c: Checker, rules: set[str]) -> None:
    for p in files("*.md"):
        text = p.read_text(encoding="utf-8")
        for rid in RULE_REF_RE.findall(text):
            if rid.endswith((".yaml", ".md", ".json", ".py", ".csv")) or "<" in rid:
                continue
            if rid not in rules:
                c.err(f"{rel(p)}：引用了未定义的规则 {rid}")
    for p in files("*.py"):
        if p.parent.name != "scripts":
            continue
        for rid in re.findall(r'"((?:%s)\.[a-z0-9.-]+)"' % "|".join(RULE_DOMAINS), p.read_text(encoding="utf-8")):
            if rid.endswith((".yaml", ".md", ".json", ".py")):
                continue
            if rid not in rules:
                c.err(f"{rel(p)}：脚本输出的规则 {rid} 没有在 references/ 中定义")


# ------------------------------------------------------------------ 评测
def check_eval_file(c: Checker, path: Path, rules: set[str], suite: str, known_modules: set[str]) -> list[dict]:
    data = load_yaml(path)
    if data.get("version") != 2:
        c.err(f"{rel(path)}：version 应为 2")
    cases = data.get("cases") or []
    ids = [x.get("id") for x in cases]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        c.err(f"{rel(path)}：用例 ID 重复：{d}")
    for case in cases:
        cid = case.get("id")
        for key in ("id", "kind", "request", "expected"):
            if not case.get(key):
                c.err(f"{rel(path)}:{cid}：缺少 {key}")
        if case.get("kind") not in {"positive", "boundary", "negative"}:
            c.err(f"{rel(path)}:{cid}：kind 必须是 positive、boundary 或 negative")
        if "blocking" in case and not isinstance(case["blocking"], bool):
            c.err(f"{rel(path)}:{cid}：blocking 必须是 true 或 false")
        if suite in {"modules", "overlay"} and case.get("module") not in known_modules:
            c.err(f"{rel(path)}:{cid}：module 必须是已知模块 {sorted(known_modules)}")
        for fx in case.get("fixtures", []) or []:
            if not (ROOT / fx).exists():
                c.err(f"{rel(path)}:{cid}：夹具不存在：{fx}")
        for ov in (case.get("setup") or {}).get("overlays", []) or []:
            if not (ROOT / ov).exists():
                c.err(f"{rel(path)}:{cid}：setup overlay 不存在：{ov}")
        for t in case.get("targets", []) or []:
            if t not in rules:
                c.err(f"{rel(path)}:{cid}：targets 中的规则 {t} 没有定义")
        if not case.get("targets"):
            c.warn(f"{rel(path)}:{cid}：没有 targets")
    return cases


def coverage(c: Checker, cases: list[dict], methods: set[str], where: str) -> None:
    for mid in sorted(methods):
        kinds = {x.get("kind") for x in cases if x.get("module") == mid}
        if "positive" not in kinds or not kinds & {"boundary", "negative"}:
            c.err(f"{where}：方法 {mid} 至少需要一个 positive 和一个 boundary 或 negative 用例，当前 {sorted(kinds)}")


# ------------------------------------------------------------------ overlay
OVERLAY_KEYS = {"schema_version", "id", "description", "targets", "overrides", "services", "modules",
                "adapters", "validation", "evals"}
OVERLAY_SUBKEYS = {
    "modules": {"methods", "knowledge"},
    "modules.methods": {"add", "replace"},
    "modules.knowledge": {"add"},
    "adapters": {"add", "default"},
    "validation": {"add"},
}


def check_overlay(c: Checker, path: Path, product: dict, rules: set[str]) -> list[dict]:
    ov = load_yaml(path)
    base = path.parent
    where = rel(path)
    for key in set(ov) - OVERLAY_KEYS:
        c.err(f"{where}：未定义的顶层键 {key}（overlay 不能覆盖合同；可用键：{sorted(OVERLAY_KEYS)}）")
    for dotted, allowed in OVERLAY_SUBKEYS.items():
        node = ov
        for part in dotted.split("."):
            node = (node or {}).get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            for key in set(node) - allowed:
                c.err(f"{where}：{dotted}.{key} 不是允许的操作（允许：{sorted(allowed)}）")
    adapter_ids = set((product.get("adapters") or {}).get("available") or {}) | \
        {a.get("id") for a in (ov.get("adapters") or {}).get("add", []) or []}
    default_adapter = (ov.get("adapters") or {}).get("default")
    if default_adapter is not None and default_adapter not in adapter_ids:
        c.err(f"{where}：adapters.default {default_adapter} 不是已有或新增的适配器")
    if ov.get("schema_version") != 2:
        c.err(f"{where}：schema_version 应为 2")
    if not re.match(r"^[a-z0-9-]+$", str(ov.get("id", ""))):
        c.err(f"{where}：id 必须是小写字母、数字和连字符")
    if ov.get("targets") != product.get("id"):
        c.err(f"{where}：targets {ov.get('targets')} 与产品 id {product.get('id')} 不一致")
    default_files = (product.get("products") or {}).get(product.get("default_product")) or {}
    for key, entry in (ov.get("overrides") or {}).items():
        if key not in default_files:
            c.err(f"{where}：overrides.{key} 不是产品配置项")
        if entry.get("mode") not in {"replace", "extend"}:
            c.err(f"{where}：overrides.{key} 必须显式写明 mode: replace 或 extend")
        if not (base / entry.get("file", "")).is_file():
            c.err(f"{where}：overrides.{key} 文件不存在")
    for key, entry in (ov.get("services") or {}).items():
        if key not in product["services"]:
            c.err(f"{where}：services.{key} 不是官方服务")
        if entry.get("mode") != "extend":
            c.err(f"{where}：services.{key} 只允许 mode: extend")
        if not (base / entry.get("file", "")).is_file():
            c.err(f"{where}：services.{key} 文件不存在")
    official = set(product["modules"]["methods"])
    methods = (ov.get("modules") or {}).get("methods") or {}
    added = set()
    for item in methods.get("add", []) or []:
        mid = item.get("id")
        if mid in official:
            c.err(f"{where}：新增方法 {mid} 与官方方法重复，应使用 replace")
        added.add(mid)
        if (base / item.get("file", "")).is_file():
            check_method_file(c, base / item["file"], mid)
        else:
            c.err(f"{where}：方法 {mid} 文件不存在")
    for item in methods.get("replace", []) or []:
        mid = item.get("id")
        if mid not in official:
            c.err(f"{where}：替换的方法 {mid} 不在 modules.methods 中")
        added.add(mid)
        if (base / item.get("file", "")).is_file():
            check_method_file(c, base / item["file"], mid)
        else:
            c.err(f"{where}：方法 {mid} 文件不存在")
    for item in ((ov.get("modules") or {}).get("knowledge") or {}).get("add", []) or []:
        if not (base / item.get("file", "")).is_file():
            c.err(f"{where}：知识模块 {item.get('id')} 文件不存在")
    for item in (ov.get("adapters") or {}).get("add", []) or []:
        if not (base / item.get("file", "")).is_file():
            c.err(f"{where}：适配器 {item.get('id')} 文件不存在")
    for item in (ov.get("validation") or {}).get("add", []) or []:
        if not (base / item.get("file", "")).is_file():
            c.err(f"{where}：验证文件不存在：{item.get('file')}")
    # overlay 自带评测
    ov_rules = set(rules)
    for p in base.rglob("*.md"):
        ov_rules |= set(RULE_DEF_RE.findall(p.read_text(encoding="utf-8")))
    cases = []
    for rel_eval in ov.get("evals", []) or []:
        ep = base / rel_eval
        if not ep.is_file():
            c.err(f"{where}：评测文件不存在：{rel_eval}")
            continue
        cases += check_eval_file(c, ep, ov_rules, "overlay",
                                 official | added | {"overlay", "sample-planning", "spss", "codebook", "markdown"})
    coverage(c, cases, added, where)
    return cases


# ------------------------------------------------------------------ 示例
def check_examples(c: Checker) -> None:
    for spec_path in files("spec.yaml"):
        if "examples" not in spec_path.parts:
            continue
        spec = load_yaml(spec_path)
        report = validate_spec.validate(spec)
        for r in report.results:
            c.err(f"{rel(spec_path)}：示例规格不应有验证结果：{r.rule_id} {r.target} {r.message}")
        md_path = spec_path.parent / "03-questionnaire.md"
        if md_path.exists() and not report.errors:
            from spec_lib import product_profile
            profile = product_profile()
            rendered = render_markdown.Renderer(spec, "default", profile=profile).render()
            if rendered != md_path.read_text(encoding="utf-8"):
                c.err(f"{rel(md_path)}：与 spec.yaml 的渲染结果不一致，运行 render_markdown.py 重新生成")
            rep = Report()
            qs = check_render.check(md_path.read_text(encoding="utf-8"), rep, profile)
            check_render.compare(qs, spec, "default", rep, profile)
            for r in rep.results:
                c.err(f"{rel(md_path)}：{r.rule_id} {r.target} {r.message}")


LOCAL_KEYS = {"schema_version", "product", "products", "overlays", "validation"}


def check_local_override(c: Checker, product: dict) -> None:
    """local.yaml 是使用者自己的文件，只允许覆盖产品和 overlay，不允许改合同。"""
    example = ROOT / "local.example.yaml"
    for path in [p for p in (ROOT / "local.yaml", example) if p.exists()]:
        data = load_yaml(path) or {}
        if not isinstance(data, dict):
            c.err(f"{rel(path)}：不是 YAML 对象")
            continue
        for key in set(data) - LOCAL_KEYS:
            c.err(f"{rel(path)}：未定义的键 {key}（允许：{sorted(LOCAL_KEYS)}）")
        if data.get("schema_version") != 1:
            c.err(f"{rel(path)}：schema_version 应为 1")
        local_products = data.get("products") or {}
        known = set(product.get("products") or {}) | set(local_products)
        pid = data.get("product")
        if pid and pid not in known:
            c.err(f"{rel(path)}：product {pid} 不在 products 中（product.yaml 或本文件的 products）")
        for name, entry in local_products.items():
            for key, rel_file in (entry or {}).items():
                if not (ROOT / rel_file).exists():
                    c.err(f"{rel(path)}：products.{name}.{key} 路径不存在：{rel_file}")
        for entry in data.get("overlays") or []:
            if not (ROOT / entry).exists():
                c.err(f"{rel(path)}：overlay 不存在：{entry}")
        for item in (data.get("validation") or {}).get("add", []) or []:
            if not (ROOT / item.get("file", "")).exists():
                c.err(f"{rel(path)}：验证文件不存在：{item.get('file')}")
        allowed_validation = {"add"}
        for key in set(data.get("validation") or {}) - allowed_validation:
            c.err(f"{rel(path)}：validation.{key} 不是允许的操作（只允许 add）")


def main() -> int:
    c = Checker()
    check_yaml(c)
    check_contract_manifest(c)
    product = check_product(c)
    check_versions(c, product)
    check_links(c)
    check_local_paths(c)
    check_csv(c)
    check_methods(c, product)
    check_profiles(c, product)
    rules = collect_rules(c)
    check_rule_refs(c, rules)
    methods = set(product["modules"]["methods"])
    known = methods | {"sample-planning", "spss", "codebook", "markdown"}
    for suite, rel_path in (("conformance", product["evals"]["conformance"]), ("modules", product["evals"]["modules"]),
                            ("product", product["evals"]["product"])):
        cases = check_eval_file(c, ROOT / rel_path, rules, suite, known)
        if suite == "modules":
            coverage(c, cases, methods, rel_path)
    for ov_path in files("overlay.yaml"):
        check_overlay(c, ov_path, product, rules)
    check_local_override(c, product)
    for entry in product.get("overlays") or []:
        if not (ROOT / entry).is_file():
            c.err(f"product.yaml：overlay 不存在：{entry}")
    check_examples(c)

    for w in c.warnings:
        print(f"[warning] {w}")
    for e in c.errors:
        print(f"[error] {e}")
    print(f"\n规则 {len(rules)} 条；error {len(c.errors)}，warning {len(c.warnings)}")
    return 1 if c.errors else 0


if __name__ == "__main__":
    sys.exit(main())
