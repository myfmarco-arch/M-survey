"""M-survey 脚本共用函数。

只依赖 Python 3.9+、PyYAML 和 jsonschema。
"""
from __future__ import annotations

import json
import re
import sys

sys.dont_write_bytecode = True  # 不在 Skill 目录中留下 __pycache__

from dataclasses import dataclass, field  # noqa: E402
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 PyYAML。请运行：pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "questionnaire-spec.schema.json"

SPECIAL_SEMANTICS = {"other", "none", "dont_know", "not_applicable", "refused"}
EXCLUSIVE_SEMANTICS = {"none", "dont_know", "not_applicable", "refused"}
CHOICE_TYPES = {"single", "multi", "ranking"}
VALUE_TYPES = {"scale", "numeric", "matrix"}

# 未解释占位符。管道标记 {{Q5}} / {{item}} 另行检查。
# PLACEHOLDER_RE：中括号占位和英文占位词，任何位置都视为 error。
# DRAFT_WORD_RE：“待定”类词语。题干中视为 error；选项文字中可能是正式选项（例如“还没想好/待定”），视为 warning。
# 中括号占位同时覆盖全角 ⟨…⟩、〈…〉、〔…〕——它们常被用来标记“待替换的内容”。
# 【】是官方问卷格式的标记，不在此列。
PLACEHOLDER_RE = re.compile(r"\b(?:TBD|TODO|XXX)\b|\[[^\]\n]{1,40}\]|[⟨〈〔][^⟩〉〕\n]{1,60}[⟩〉〕]", re.IGNORECASE)
DRAFT_WORD_RE = re.compile(r"待定|待确认|待补")
PIPE_TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}")


@dataclass
class Result:
    rule_id: str
    severity: str
    target: str
    message: str
    resolution: str
    source: str

    def as_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "target": self.target,
            "message": self.message,
            "resolution": self.resolution,
            "source": self.source,
        }


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, *args: str) -> None:
        self.results.append(Result(*args))

    @property
    def errors(self) -> list[Result]:
        return [r for r in self.results if r.severity == "error"]

    def counts(self) -> dict[str, int]:
        out = {"error": 0, "warning": 0, "info": 0}
        for r in self.results:
            out[r.severity] = out.get(r.severity, 0) + 1
        return out

    def dump(self, fmt: str, stream=sys.stdout) -> None:
        if fmt == "yaml":
            yaml.safe_dump(
                [r.as_dict() for r in self.results] or [],
                stream,
                allow_unicode=True,
                sort_keys=False,
                width=1000,
            )
        elif fmt == "json":
            json.dump([r.as_dict() for r in self.results], stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        else:
            order = {"error": 0, "warning": 1, "info": 2}
            for r in sorted(self.results, key=lambda x: order.get(x.severity, 9)):
                stream.write(f"[{r.severity}] {r.rule_id} @ {r.target}\n  {r.message}\n  修复：{r.resolution}\n")
            c = self.counts()
            stream.write(f"\n合计：error {c['error']}，warning {c['warning']}，info {c['info']}\n")


def load_yaml(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def iter_questions(spec: dict) -> Iterable[tuple[dict, dict]]:
    for section in spec.get("sections", []) or []:
        for q in section.get("questions", []) or []:
            yield section, q


def option_semantic(opt: dict) -> str:
    return opt.get("semantic", "regular")


class SpecIndex:
    """按问卷顺序索引题目，供逻辑检查和渲染使用。"""

    def __init__(self, spec: dict):
        self.spec = spec
        self.order: list[str] = []
        self.questions: dict[str, dict] = {}
        self.section_of: dict[str, dict] = {}
        for section, q in iter_questions(spec):
            qid = q.get("id")
            if qid is None:
                continue
            if qid not in self.questions:
                self.order.append(qid)
                self.questions[qid] = q
                self.section_of[qid] = section

    def position(self, qid: str) -> int:
        try:
            return self.order.index(qid)
        except ValueError:
            return -1

    def option_ids(self, qid: str, include_piped: bool = True) -> set[str]:
        q = self.questions.get(qid, {})
        ids = {o.get("id") for o in q.get("options", []) or []}
        if include_piped and q.get("options_from"):
            src = q["options_from"].get("question")
            if src in self.questions and src != qid:
                ids |= self.option_ids(src, include_piped=True)
        return ids

    def resolved_options(self, qid: str) -> list[dict]:
        """返回题目可见选项：引用来源的普通选项在前，本题选项在后。"""
        q = self.questions.get(qid, {})
        own = list(q.get("options", []) or [])
        if not q.get("options_from"):
            return own
        src = q["options_from"].get("question")
        piped = [o for o in self.resolved_options(src) if option_semantic(o) == "regular"] if src in self.questions else []
        return piped + own


def assign_default_codes(q: dict, other_code: Any = 98, none_code: Any = 99, reserved: Iterable[Any] = ()) -> dict[str, Any]:
    """按官方产品默认编码为选项分配编码。

    已有显式编码优先；普通选项按顺序使用未被占用的 1、2、3……；
    other 默认 98，none 默认 99；不知道、不适用、拒答没有默认值，返回 None。
    reserved 是已被占用的编码，例如引用前题时来源题的编码。
    """
    codes: dict[str, Any] = {}
    used = {o["code"] for o in q.get("options", []) or [] if "code" in o} | set(reserved)
    nxt = 1
    for o in q.get("options", []) or []:
        oid = o.get("id")
        if "code" in o:
            codes[oid] = o["code"]
            continue
        sem = option_semantic(o)
        if sem == "regular":
            while nxt in used:
                nxt += 1
            codes[oid] = nxt
            used.add(nxt)
            nxt += 1
        elif sem == "other":
            codes[oid] = other_code
        elif sem == "none":
            codes[oid] = none_code
        else:
            codes[oid] = None
    return codes


# ------------------------------------------------------------------ 产品配置
class Profile:
    """产品配置：面向受访者的文字、表头、标签和默认编码。

    合同、脚本和 SKILL.md 不写死这些内容，产品目录下的 profile.yaml 决定它们。
    缺少字段时回退到 survey-zh-default，保证旧产品或第三方产品不会因为少写字段而崩。
    """

    FALLBACK_DIR = "references/products/survey-zh-default"

    def __init__(self, data: dict, path: Path | None = None):
        self.data = data or {}
        self.path = path
        self.id = self.data.get("id") or "unknown"
        self.language = self.data.get("language") or "zh-CN"

    # --- 取字段
    class Missing(Exception):
        """产品配置缺必需字段。宁可报错，也不要静默退回另一种语言。"""

    def _require(self, section: str, key: str):
        node = self.data.get(section) or {}
        if key not in node:
            raise Profile.Missing(f"产品 {self.id} 的 profile.yaml 缺少 {section}.{key}")
        return node[key]

    def codes(self) -> dict[str, int | str]:
        return {k: self._require("codes", k) for k in ("other", "none")}

    def table(self, kind: str) -> list[str]:
        return list(self._require("tables", kind))

    def type_label(self, rtype: str, has_scale: bool = False) -> str:
        key = ("matrix_scale" if has_scale else "matrix_choice") if rtype == "matrix" else rtype
        return self._require("type_labels", key)

    def token(self, key: str, default: str | None = None, **kwargs) -> str:
        """取产品文字模板。

        产品自己声明了 tokens 时，缺 key 直接报错（避免静默显示成空或另一种语言）；
        只有在检查工具按“未知 key”探测时才用 default。
        """
        tokens = self.data.get("tokens") or {}
        if key in tokens:
            raw = tokens[key]
        elif default is not None:
            raw = default
        else:
            raise Profile.Missing(f"产品 {self.id} 的 profile.yaml 缺少 tokens.{key}")
        if not kwargs:
            return raw
        try:
            return raw.format(**kwargs)
        except (KeyError, IndexError):
            return raw

    def token_prefix(self, key: str, default: str | None = None) -> str:
        """模板第一个占位符之前的固定文字，用于识别“引用…”“loop over…”这类前缀。"""
        raw = self.token(key) if default is None else self.token(key, default)
        return raw.split("{")[0]

    def heading(self, key: str, default: str | None = None, **kwargs) -> str:
        raw = self._require("headings", key) if default is None else \
            (self.data.get("headings") or {}).get(key, default)
        try:
            return raw.format(**kwargs)
        except (KeyError, IndexError):
            return raw

    def separator(self, key: str, default: str | None = None) -> str:
        return self._require("separators", key) if default is None else \
            (self.data.get("separators") or {}).get(key, default)

    def appendices(self) -> list[str]:
        return list(self.data.get("appendices") or [])


def _load_fallback_profile() -> Profile:
    """默认产品配置优先读磁盘上的 profile.yaml；文件不存在时用最小内置值。"""
    path = ROOT / "references" / "products" / "survey-zh-default" / "profile.yaml"
    if path.exists():
        return Profile(load_yaml(path), path)
    return Profile({"id": "survey-zh-default", "language": "zh-CN",
                    "codes": {"other": 98, "none": 99}})


ZH_PROFILE = _load_fallback_profile()


def load_profile(path: Path) -> Profile:
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path} 不是有效的产品配置")
    return Profile(data, path)


def product_dir_of(product_id: str) -> Path:
    return ROOT / "references" / "products" / product_id


def load_profile_by_id(product_id: str) -> Profile:
    path = product_dir_of(product_id) / "profile.yaml"
    if not path.exists():
        raise FileNotFoundError(f"产品 {product_id} 缺少 profile.yaml：{path}")
    return load_profile(path)


# ------------------------------------------------------------------ 产品注册表
def product_registry() -> tuple[str, dict]:
    """读取产品注册表，返回 (默认产品 id, 产品表)。

    product.yaml 是上游文件；local.yaml 中的 products 在其之上合并，同名以 local.yaml 为准。
    """
    data = load_yaml(ROOT / "product.yaml")
    products = {str(k): (v or {}) for k, v in (data.get("products") or {}).items()}
    default_id = str(data.get("default_product") or data.get("product") or "survey-zh-default")
    local = ROOT / "local.yaml"
    if local.exists():
        local_data = load_yaml(local) or {}
        for key, value in (local_data.get("products") or {}).items():
            products[str(key)] = {**products.get(str(key), {}), **(value or {})}
    return default_id, products


def current_product() -> str:
    """生效的产品 id：local.yaml 的 product 优先，其次 product.yaml 的 product / default_product。"""
    local = ROOT / "local.yaml"
    if local.exists():
        data = load_yaml(local) or {}
        if isinstance(data, dict) and data.get("product"):
            return str(data["product"])
    default_id, _ = product_registry()
    return default_id


def product_files(product_id: str) -> dict[str, str]:
    """产品提供的文件。

    来源按优先级：产品自己的 profile.yaml 中 files 块 → product.yaml 中该产品的登记 → 默认产品。
    只保留实际存在的文件，缺失的键继续向下回退。
    """
    default_id, products = product_registry()
    resolved: dict[str, str] = {}
    for source in (products.get(default_id) or {}, products.get(product_id) or {}):
        resolved.update({k: str(v) for k, v in source.items()})
    # profile 必须优先解析，才能读到它自己声明的 files
    _, registry_products = product_registry()
    profile_rel = (registry_products.get(product_id) or {}).get("profile") or \
        (registry_products.get(default_id) or {}).get("profile")
    if profile_rel and (ROOT / profile_rel).exists():
        local = (load_yaml(ROOT / profile_rel) or {}).get("files") or {}
        base_dir = (ROOT / profile_rel).parent
        for key, rel_file in local.items():
            resolved[key] = str((base_dir / rel_file).relative_to(ROOT))
    return {k: v for k, v in resolved.items() if (ROOT / v).exists()}


def product_profile(product_id: str | None = None) -> Profile:
    """按 id 取产品配置。显式传入未注册的 id 时报错，而不是静默退回中文产品。"""
    pid = product_id or current_product()
    _, products = product_registry()
    if product_id is not None and pid not in products:
        raise Profile.Missing(f"未注册的产品 {pid}。在 product.yaml 的 products 或 local.yaml 的 products 中登记。")
    files = product_files(pid)
    rel = files.get("profile")
    if not rel or not (ROOT / rel).exists():
        raise Profile.Missing(f"产品 {pid} 没有可用的 profile.yaml")
    return load_profile(ROOT / rel)
