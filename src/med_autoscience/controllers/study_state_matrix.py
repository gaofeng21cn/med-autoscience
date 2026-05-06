from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_macro_state
from med_autoscience.study_manual_finish import _delivered_package_ready


def resolve_study_ids(profile: Any) -> tuple[str, ...]:
    studies_root = Path(profile.studies_root).expanduser().resolve()
    if not studies_root.exists():
        return ()
    study_ids: list[str] = []
    for child in sorted(studies_root.iterdir(), key=lambda item: item.name):
        if child.is_dir() and (child / "study.yaml").is_file():
            study_ids.append(child.name)
    return tuple(study_ids)


def build_study_state_matrix(
    *,
    profile: Any,
    study_runtime_router: Any,
    study_ids: Iterable[str] | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_ids or ()) or resolve_study_ids(profile)
    studies: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for study_id in resolved_study_ids:
        status = _dict(
            study_runtime_router.study_runtime_status(
                profile=profile,
                study_id=study_id,
                study_root=None,
                entry_mode=entry_mode,
            )
        )
        delivered_package = _delivered_package_observation(status=status)
        if delivered_package.get("observed") is True:
            status = {**status, "delivered_package": delivered_package}
        study_root = _study_root_from_status(profile=profile, study_id=study_id, status=status)
        macro = _read_materialized_macro_state(study_root=study_root) or study_macro_state.derive_study_macro_state(
            study_id=study_id,
            status=status,
            progress={},
        )
        active_run_id = _resolved_active_run_id(status=status, macro_state=macro)
        writer_state = str(macro["writer_state"])
        counts[writer_state] = counts.get(writer_state, 0) + 1
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _text(status.get("quest_id")),
                "quest_status": _text(status.get("quest_status")),
                "active_run_id": active_run_id,
                "delivered_package": delivered_package or None,
                "study_macro_state": macro,
            }
        )
    return {
        "surface": "study_state_matrix",
        "schema_version": 1,
        "workspace_root": str(Path(profile.workspace_root).expanduser().resolve()),
        "study_count": len(studies),
        "counts": counts,
        "studies": studies,
    }


def render_study_state_matrix_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Study State Matrix",
        "",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- study_count: `{payload.get('study_count')}`",
        "",
        "| study_id | writer | user_next | reason | active_run_id |",
        "| --- | --- | --- | --- | --- |",
    ]
    for study in payload.get("studies") or []:
        study_payload = _dict(study)
        macro = _dict(study_payload.get("study_macro_state"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(study_payload.get("study_id")) or "",
                    _text(macro.get("writer_state")) or "",
                    _text(macro.get("user_next")) or "",
                    _text(macro.get("reason")) or "",
                    _text(study_payload.get("active_run_id")) or "",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _study_root_from_status(*, profile: Any, study_id: str, status: Mapping[str, Any]) -> Path:
    if text := _text(status.get("study_root")):
        return Path(text).expanduser().resolve()
    return Path(profile.studies_root).expanduser().resolve() / study_id


def _read_materialized_macro_state(*, study_root: Path) -> dict[str, Any] | None:
    path = study_root / study_macro_state.SNAPSHOT_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    macro = dict(payload)
    if _text(macro.get("surface")) != "study_macro_state":
        return None
    if _text(macro.get("writer_state")) not in study_macro_state.WRITER_STATES:
        return None
    return macro


def _delivered_package_observation(*, status: Mapping[str, Any]) -> dict[str, Any]:
    study_root_text = _text(status.get("study_root"))
    if not study_root_text:
        return {}
    study_root = Path(study_root_text).expanduser().resolve()
    manuscript_root = study_root / "manuscript"
    candidates = (
        (
            "manuscript/current_package",
            manuscript_root / "current_package",
            manuscript_root / "current_package.zip",
            True,
        ),
        (
            "manuscript/submission_package",
            manuscript_root / "submission_package",
            None,
            False,
        ),
    )
    for surface, package_root, zip_path, require_administrative_todo in candidates:
        if _delivered_package_ready(
            study_root=study_root,
            package_root=package_root,
            require_zip_path=zip_path,
            require_administrative_todo=require_administrative_todo,
        ):
            return {
                "surface": surface,
                "observed": True,
                "package_root": str(package_root),
                "zip_path": str(zip_path) if zip_path is not None else None,
                "authority_role": "user_visible_milestone_package_not_quality_authority",
            }
    return {"observed": False}


def _resolved_active_run_id(*, status: Mapping[str, Any], macro_state: Mapping[str, Any]) -> str | None:
    if _text(macro_state.get("writer_state")) == "parked":
        return _text(_dict(macro_state.get("details")).get("active_run_id"))
    return (
        _text(status.get("active_run_id"))
        or _text(_dict(status.get("study_truth_snapshot")).get("active_run_id"))
        or _text(_dict(macro_state.get("details")).get("active_run_id"))
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_study_state_matrix",
    "render_study_state_matrix_markdown",
    "resolve_study_ids",
]
