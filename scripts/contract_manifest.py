#!/usr/bin/env python3
"""生成和校验合同清单 contracts/manifest.json。

用法：
    python scripts/contract_manifest.py check      # 校验清单与文件一致（CI 与 check_repo 使用）
    python scripts/contract_manifest.py write      # 改动合同后重新生成，并把 revision 前移

清单锁定合同版本：每个文件的 sha256 加一个 revision 标识。分叉版本声明兼容时应写
`m-survey-contract-v1@<revision>`，这样“兼容 v1”能指向具体时点，而不只是一个还在变动的名字。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "contracts" / "manifest.json"
# 合同由这些文件组成；修改其中任何一个都需要重新生成清单并前移 revision
FILES = [
    "references/contracts/artifacts.md",
    "references/contracts/module-contract.md",
    "references/contracts/validation-contract.md",
    "references/contracts/overlay-contract.md",
    "schemas/questionnaire-spec.schema.json",
    "evals/conformance/cases.yaml",
    "evals/scoring.md",
]


def digest(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def next_revision(old_revision: str | None, changed: bool) -> str:
    """内容变化时把 revision 前移到 today.N+1；没变化就沿用原值。"""
    today = dt.date.today().isoformat()
    if not old_revision:
        return f"{today}.1"
    if not changed:
        return old_revision
    date_part, _, n = old_revision.rpartition(".")
    if date_part == today and n.isdigit():
        return f"{today}.{int(n) + 1}"
    return f"{today}.1"


def build(revision: str | None = None) -> dict:
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    files = {rel: digest(rel) for rel in FILES}
    changed = (old.get("files") or {}) != files
    if revision is None:
        revision = next_revision(old.get("revision"), changed)
    return {
        "contract": "m-survey-contract-v1",
        "revision": revision,
        "declaring_compatibility": f"m-survey-contract-v1@{revision}",
        "note": "修改 contracts、schema 或 conformance 评测后运行 python scripts/contract_manifest.py write；"
                "内容变化时 revision 自动前移为 YYYY-MM-DD.N。",
        "files": files,
    }


def check() -> list[str]:
    problems: list[str] = []
    if not MANIFEST.exists():
        return [f"缺少 {MANIFEST.relative_to(ROOT)}，运行 python scripts/contract_manifest.py write 生成"]
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("contract") != "m-survey-contract-v1":
        problems.append("manifest.contract 必须是 m-survey-contract-v1")
    if not data.get("revision"):
        problems.append("manifest 缺少 revision")
    files = data.get("files") or {}
    for rel in FILES:
        if rel not in files:
            problems.append(f"manifest 未登记 {rel}")
        elif files[rel] != digest(rel):
            problems.append(f"{rel} 自 manifest 生成后已修改，运行 python scripts/contract_manifest.py write")
    for rel in set(files) - set(FILES):
        problems.append(f"manifest 登记的 {rel} 不在合同文件列表中")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "write"])
    ap.add_argument("--revision", help="write 时使用的 revision，默认沿用原值或使用今天日期加 .1")
    args = ap.parse_args(argv)
    if args.command == "write":
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        data = build(args.revision)
        MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {MANIFEST.relative_to(ROOT)}：{data['declaring_compatibility']}")
        return 0
    problems = check()
    for p in problems:
        print(f"[error] {p}")
    if not problems:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        print(f"合同清单一致：{data['declaring_compatibility']}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
