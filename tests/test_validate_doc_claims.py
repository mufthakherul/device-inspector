from __future__ import annotations

from pathlib import Path

from tools.validate_doc_claims import build_report, extract_claimed_paths


def test_extract_claimed_paths_picks_file_like_tokens() -> None:
    content = "Use `agent/cli.py`, `README.md`, and `https://example.com`."
    paths = extract_claimed_paths(content)
    assert "agent/cli.py" in paths
    assert "README.md" not in paths
    assert "https://example.com" not in paths


def test_build_report_detects_missing_paths(tmp_path: Path) -> None:
    (tmp_path / "ROADMAP.md").write_text(
        "References `agent/cli.py` and `missing/file.py`",
        encoding="utf-8",
    )
    (tmp_path / "agent").mkdir()
    (tmp_path / "agent" / "cli.py").write_text("print('ok')\n", encoding="utf-8")

    report = build_report(tmp_path, [tmp_path / "ROADMAP.md"])
    assert report["docs_checked"] == 1
    assert report["all_ok"] is False
    assert "missing/file.py" in report["results"][0]["missing_paths"]
