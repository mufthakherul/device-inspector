"""Validate documentation claims against repository file reality."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

FILE_TOKEN = re.compile(r"`([^`]+)`")


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _looks_like_path(token: str) -> bool:
    if token.startswith("http://") or token.startswith("https://"):
        return False
    if " " in token:
        return False
    return "/" in token or token.endswith(".yml") or token.endswith(".py")


def extract_claimed_paths(content: str) -> list[str]:
    paths: list[str] = []
    for token in FILE_TOKEN.findall(content):
        candidate = token.strip()
        if _looks_like_path(candidate):
            paths.append(candidate)
    return sorted(set(paths))


def validate_doc(repo_root: Path, doc_path: Path) -> dict:
    content = doc_path.read_text(encoding="utf-8")
    claims = extract_claimed_paths(content)
    missing: list[str] = []

    for claim in claims:
        normalized = claim.lstrip("./")
        target = repo_root / normalized
        if not target.exists():
            missing.append(claim)

    return {
        "doc": str(doc_path.relative_to(repo_root)).replace("\\", "/"),
        "claimed_paths": len(claims),
        "missing_paths": missing,
        "ok": len(missing) == 0,
    }


def build_report(repo_root: Path, docs: list[Path]) -> dict:
    results = [validate_doc(repo_root, doc) for doc in docs]
    return {
        "report_version": "1.0.0",
        "generated_at": _now_iso(),
        "docs_checked": len(results),
        "all_ok": all(item["ok"] for item in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate doc claims against repo files"
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--docs",
        nargs="+",
        default=["ROADMAP.md", "PROJECT_GOAL.md", "PROJECT_READINESS.md"],
    )
    parser.add_argument("--report", default="test-output/doc-claim-report.json")
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs = [(repo_root / path).resolve() for path in args.docs]

    report = build_report(repo_root, docs)

    report_path = (repo_root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[doc-claim-validator] complete")
    print(f"  docs_checked: {report['docs_checked']}")
    print(f"  all_ok: {report['all_ok']}")
    print(f"  report: {report_path}")

    if args.fail_on_missing and not report["all_ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
