from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import live_console_read_model_io as io


def resolve_selection(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: str | Path | None,
) -> tuple[str | None, Path | None]:
    if io.text(study_id) and study_root is not None:
        raise ValueError("Specify only one of study_id or study_root")
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        return root.name, root
    selected = io.text(study_id) or None
    if selected is None:
        return None, None
    return selected, (profile.studies_root / selected).expanduser().resolve()


def study_contexts(
    *,
    profile: WorkspaceProfile,
    selected_study_id: str | None,
    selected_study_root: Path | None,
) -> list[dict[str, Any]]:
    roots = discover_study_roots(profile)
    if selected_study_root is not None and selected_study_root not in roots:
        roots.append(selected_study_root)
    contexts = [study_context(profile=profile, study_root=root) for root in sorted(set(roots))]
    if selected_study_id is None:
        return contexts
    return [context for context in contexts if context["study_id"] == selected_study_id]


def discover_study_roots(profile: WorkspaceProfile) -> list[Path]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.exists():
        return []
    return [path.resolve() for path in studies_root.iterdir() if path.is_dir() and (path / "study.yaml").exists()]


def study_context(*, profile: WorkspaceProfile, study_root: Path) -> dict[str, Any]:
    study_id = study_root.name
    cockpit_path, cockpit = io.read_first_json(
        (
            profile.workspace_root / "artifacts" / "workspace_cockpit" / "latest.json",
            profile.workspace_root / "artifacts" / "runtime" / "workspace_cockpit" / "latest.json",
        )
    )
    progress_path, progress = io.read_first_json(
        (
            study_root / "artifacts" / "study_progress" / "latest.json",
            study_root / "artifacts" / "runtime" / "study_progress" / "latest.json",
            study_root / "artifacts" / "progress" / "latest.json",
        )
    )
    runtime_status_path, runtime_status = io.read_first_json(
        (
            study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status.json",
        )
    )
    summary_path, summary = io.read_first_json((study_root / "artifacts" / "runtime" / "runtime_status_summary.json",))
    health_path, health = io.read_first_json((study_root / "artifacts" / "runtime" / "health" / "latest.json",))
    supervision_path, supervision = io.read_first_json(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",)
    )
    quest_root = quest_root_from_surfaces(profile=profile, runtime_status=runtime_status, summary=summary)
    return {
        "study_id": io.first_text(
            runtime_status.get("study_id"),
            progress.get("study_id"),
            summary.get("study_id"),
            health.get("study_id"),
            supervision.get("study_id"),
            study_id,
        ),
        "study_root": study_root,
        "quest_root": quest_root,
        "surfaces": {
            "workspace_cockpit": {"path": cockpit_path, "payload": cockpit},
            "study_progress": {"path": progress_path, "payload": progress},
            "study_runtime_status": {"path": runtime_status_path, "payload": runtime_status},
            "runtime_status_summary": {"path": summary_path, "payload": summary},
            "runtime_health": {"path": health_path, "payload": health},
            "runtime_supervision": {"path": supervision_path, "payload": supervision},
            "terminal_tail": io.terminal_source(quest_root=quest_root),
            "log_tail": io.log_source(quest_root=quest_root),
        },
    }


def quest_root_from_surfaces(
    *,
    profile: WorkspaceProfile,
    runtime_status: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> Path | None:
    for value in (
        runtime_status.get("quest_root"),
        runtime_status.get("runtime_artifact_ref"),
        summary.get("runtime_artifact_ref"),
    ):
        text = io.text(value)
        if not text:
            continue
        candidate = Path(text).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    quest_id = io.first_text(runtime_status.get("quest_id"), summary.get("quest_id"))
    if quest_id is None:
        return None
    return (profile.runtime_root / quest_id).expanduser().resolve()


def string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = io.first_text(item)
        if text:
            result.append(text)
    return result


def active_run_id(
    *,
    status: Mapping[str, Any],
    health: Mapping[str, Any],
    supervision: Mapping[str, Any],
) -> str | None:
    return io.first_text(
        status.get("active_run_id"),
        mapping(mapping(status.get("runtime_liveness_audit")).get("runtime_audit")).get("active_run_id"),
        health.get("active_run_id"),
        supervision.get("active_run_id"),
    )


def worker_running(*, status: Mapping[str, Any], health: Mapping[str, Any]) -> bool:
    for value in (
        health.get("worker_running"),
        status.get("worker_running"),
        mapping(mapping(status.get("runtime_liveness_audit")).get("runtime_audit")).get("worker_running"),
    ):
        if isinstance(value, bool):
            return value
    return False


def study_health_status(context: Mapping[str, Any]) -> str:
    health = surface_payload(context, "runtime_health")
    summary = surface_payload(context, "runtime_status_summary")
    status = surface_payload(context, "study_runtime_status")
    return io.first_text(
        health.get("health_status"),
        health.get("attempt_state"),
        summary.get("health_status"),
        status.get("quest_status"),
        "missing",
    ) or "missing"


def surface(context: Mapping[str, Any], key: str) -> dict[str, Any]:
    return mapping(mapping(context.get("surfaces")).get(key))


def surface_payload(context: Mapping[str, Any], key: str) -> dict[str, Any]:
    return mapping(surface(context, key).get("payload"))


def surface_path_text(context: Mapping[str, Any], key: str) -> str | None:
    path = surface(context, key).get("path")
    return str(path) if path is not None else None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "active_run_id",
    "discover_study_roots",
    "mapping",
    "quest_root_from_surfaces",
    "resolve_selection",
    "string_list",
    "study_context",
    "study_contexts",
    "study_health_status",
    "surface",
    "surface_path_text",
    "surface_payload",
    "worker_running",
]
