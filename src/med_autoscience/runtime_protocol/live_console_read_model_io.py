from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import live_console_contract


STREAM_TOPICS: tuple[str, ...] = (
    "workspace.status",
    "study.status",
    "runtime.health",
    "runtime.supervision",
    "terminal.tail",
    "log.tail",
    "artifact.delta",
)


def read_first_json(paths: Iterable[Path]) -> tuple[Path | None, dict[str, Any]]:
    for path in paths:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, Mapping):
            return path.resolve(), dict(payload)
    return None, {}


def terminal_source(*, quest_root: Path | None) -> dict[str, Any]:
    if quest_root is None:
        return {"status": "missing", "source_ref": None, "tail": []}
    path, payload = read_first_json((quest_root / ".ds" / "bash_exec" / "summary.json",))
    if not payload:
        summary_path = quest_root / ".ds" / "bash_exec" / "summary.json"
        return {"status": "missing", "path": str(summary_path), "source_ref": str(summary_path), "tail": []}
    return {
        "status": "available",
        "path": str(path) if path is not None else None,
        "source_ref": str(path) if path is not None else None,
        "tail": tail_source_lines(payload.get("tail")),
    }


def log_source(*, quest_root: Path | None) -> dict[str, Any]:
    if quest_root is None:
        return {"status": "missing", "source_ref": None, "tail": []}
    log_path = quest_root / "logs" / "worker.log"
    if not log_path.is_file():
        return {"status": "missing", "path": str(log_path), "source_ref": str(log_path), "tail": []}
    return {
        "status": "available",
        "path": str(log_path),
        "source_ref": str(log_path),
        "tail": log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:],
    }


def tail_source_lines(value: object) -> list[str]:
    if isinstance(value, str):
        return value.splitlines()[-20:]
    if not isinstance(value, Iterable):
        return []
    return [str(item) for item in value if isinstance(item, str)][-20:]


def normalize_sources(sources: Sequence[Mapping[str, Any]] | None, *, limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for source in sources or ():
        raw_path = source.get("path")
        path_text = str(raw_path) if isinstance(raw_path, Path) else text(raw_path)
        path = Path(path_text).expanduser().resolve() if path_text else None
        source_ref = path_text or text(source.get("source_ref")) or text(source.get("ref"))
        payload = {
            "source": text(source.get("source")) or text(source.get("kind")) or "runtime_stream",
            "source_ref": str(path) if path is not None else source_ref,
            "read_only": True,
            "tail": tail_lines(path, limit=limit) if path is not None else list(source.get("tail") or []),
        }
        payload["status"] = "available" if payload["tail"] or (path is not None and path.exists()) else "missing"
        normalized.append(payload)
    return normalized


def tail_lines(path: Path, *, limit: int) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []
    rendered: list[str] = []
    for line in lines[-max(limit, 1) :]:
        rendered_line = line_from_json(line)
        if rendered_line:
            rendered.append(rendered_line)
    return rendered


def line_from_json(line: str) -> str:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return line
    if isinstance(payload, Mapping):
        return first_text(payload.get("line"), payload.get("message"), payload.get("text"), payload.get("content")) or line
    return line


def load_payload(payload: Mapping[str, Any] | None, path: Path | None) -> dict[str, Any]:
    if payload is not None:
        return dict(payload)
    if path is None:
        return {}
    try:
        loaded = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return dict(loaded) if isinstance(loaded, Mapping) else {}


def stream_topics(
    *,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {"topic": topic, "read_only": True, "source_ref": topic_source_ref(topic, terminal, logs, artifact_delta)}
        for topic in STREAM_TOPICS
    ]


def topic_source_ref(
    topic: str,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> str:
    if topic == "terminal.tail":
        return live_console_contract.first_source_ref(terminal) or "live_console.terminal"
    if topic == "log.tail":
        return live_console_contract.first_source_ref(logs) or "live_console.log"
    if topic == "artifact.delta":
        return live_console_contract.artifact_source_ref(artifact_delta) or "live_console.artifact_delta"
    return f"live_console.{topic}"


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_text(*values: object) -> str | None:
    for value in values:
        candidate = text(value)
        if candidate:
            return candidate
    return None


def text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


__all__ = [
    "STREAM_TOPICS",
    "first_text",
    "load_payload",
    "log_source",
    "normalize_sources",
    "read_first_json",
    "stream_topics",
    "terminal_source",
    "text",
    "write_json",
]
