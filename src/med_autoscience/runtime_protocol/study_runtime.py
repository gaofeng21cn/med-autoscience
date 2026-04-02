from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .layout import build_workspace_runtime_layout_for_profile

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def resolve_study_runtime_paths(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Path]:
    layout = build_workspace_runtime_layout_for_profile(profile)
    resolved_study_root = Path(study_root).expanduser().resolve()
    return {
        "quest_root": layout.quest_root(quest_id),
        "runtime_binding_path": resolved_study_root / "runtime_binding.yaml",
        "startup_payload_root": layout.startup_payload_root(study_id),
        "launch_report_path": resolved_study_root / "artifacts" / "runtime" / "last_launch_report.json",
    }


def write_runtime_binding(
    *,
    runtime_binding_path: Path,
    runtime_root: Path,
    study_id: str,
    study_root: Path,
    quest_id: str,
    last_action: str,
    source: str,
    recorded_at: str,
) -> None:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    resolved_study_root = Path(study_root).expanduser().resolve()
    _write_yaml(
        runtime_binding_path,
        {
            "schema_version": 1,
            "engine": "med-deepscientist",
            "study_id": study_id,
            "study_root": str(resolved_study_root),
            "quest_id": quest_id,
            "runtime_root": str(resolved_runtime_root / "quests"),
            "med_deepscientist_runtime_root": str(resolved_runtime_root),
            "last_action": last_action,
            "last_action_at": recorded_at,
            "last_source": source,
        },
    )


def write_launch_report(
    *,
    launch_report_path: Path,
    status: dict[str, Any],
    source: str,
    force: bool,
    startup_payload_path: Path | None,
    daemon_result: dict[str, Any] | None,
    recorded_at: str,
) -> None:
    report = dict(status)
    report.update(
        {
            "source": source,
            "force": force,
            "recorded_at": recorded_at,
            "startup_payload_path": str(startup_payload_path) if startup_payload_path is not None else None,
            "daemon_result": daemon_result,
        }
    )
    _write_json(launch_report_path, report)


def archive_invalid_partial_quest_root(
    *,
    quest_root: Path,
    runtime_root: Path,
    slug: str,
) -> dict[str, Any] | None:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_yaml_path = resolved_quest_root / "quest.yaml"
    if not resolved_quest_root.exists() or quest_yaml_path.exists():
        return None

    recovery_root = Path(runtime_root).expanduser().resolve() / "recovery" / "invalid_partial_quest_roots"
    archive_root = recovery_root / f"{resolved_quest_root.name}-{slug}"
    recovery_root.mkdir(parents=True, exist_ok=True)
    if archive_root.exists():
        raise FileExistsError(f"invalid partial quest recovery target already exists: {archive_root}")
    resolved_quest_root.rename(archive_root)
    return {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": str(resolved_quest_root),
        "archived_root": str(archive_root),
        "missing_required_files": ["quest.yaml"],
    }
