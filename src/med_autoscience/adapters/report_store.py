import json
from pathlib import Path
from typing import Any, Mapping


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_timestamped_report(
    *,
    quest_root: Path,
    report_group: str,
    timestamp: str,
    report: Mapping[str, Any],
    markdown: str,
) -> tuple[Path, Path]:
    stamp = timestamp.replace("+00:00", "Z").replace(":", "")
    base = quest_root / "artifacts" / "reports" / report_group
    json_path = base / f"{stamp}.json"
    md_path = base / f"{stamp}.md"
    _dump_json(json_path, dict(report))
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    _dump_json(base / "latest.json", dict(report))
    (base / "latest.md").write_text(markdown, encoding="utf-8")
    return json_path, md_path

__all__ = [
    "write_timestamped_report",
]
