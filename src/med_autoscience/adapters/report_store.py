from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _state_dir(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "reports" / "runtime_watch"


def load_watch_state(quest_root: Path) -> dict[str, Any]:
    path = _state_dir(quest_root) / "state.json"
    return _load_json(path, default={"schema_version": 1, "controllers": {}}) or {
        "schema_version": 1,
        "controllers": {},
    }


def save_watch_state(quest_root: Path, payload: Mapping[str, Any]) -> None:
    _dump_json(_state_dir(quest_root) / "state.json", dict(payload))


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
    return json_path, md_path
