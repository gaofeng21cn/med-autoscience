from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_lifecycle_control


def resolve_study_ids(profile: Any) -> tuple[str, ...]:
    studies_root = Path(profile.studies_root).expanduser().resolve()
    if not studies_root.exists():
        return ()
    return tuple(
        child.name
        for child in sorted(studies_root.iterdir(), key=lambda item: item.name)
        if child.is_dir() and (child / "study.yaml").is_file()
    )


def build_study_state_matrix(
    *,
    profile: Any,
    domain_status_projection: Any,
    study_ids: Iterable[str] | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    studies: list[dict[str, Any]] = []
    for study_id in tuple(study_ids or ()) or resolve_study_ids(profile):
        study_root = Path(profile.studies_root).expanduser().resolve() / study_id
        lifecycle = study_lifecycle_control.read_study_lifecycle(
            study_root=study_root,
            study_id=study_id,
        )
        lifecycle_inactive = study_lifecycle_control.lifecycle_is_inactive(lifecycle)
        try:
            if lifecycle_inactive:
                status = study_lifecycle_control.apply_lifecycle_to_progress_readback(
                    payload={"study_id": study_id},
                    study_root=study_root,
                    lifecycle=lifecycle,
                )
            else:
                status = _mapping(
                    domain_status_projection.progress_projection(
                        profile=profile,
                        study_id=study_id,
                        study_root=None,
                        entry_mode=entry_mode,
                    )
                )
            projection_status = "readable"
            projection_error = None
        except Exception as exc:
            status = {}
            projection_status = "unreadable"
            projection_error = f"{type(exc).__name__}: {exc}"
        progress = _mapping(status.get("progress_projection")) or status
        refs = _readable_refs(_mapping(progress.get("refs")) or _mapping(status.get("refs")))
        if lifecycle is not None:
            refs = sorted(
                {
                    *refs,
                    str(study_root / study_lifecycle_control.STUDY_LIFECYCLE_RELPATH),
                }
            )
        studies.append(
            {
                "study_id": study_id,
                "business_status": (
                    lifecycle.get("lifecycle_state") if lifecycle is not None else None
                ),
                "lifecycle_state": (
                    lifecycle.get("lifecycle_state") if lifecycle is not None else None
                ),
                "lifecycle_ref": (
                    str(study_root / study_lifecycle_control.STUDY_LIFECYCLE_RELPATH)
                    if lifecycle is not None
                    else None
                ),
                "lifecycle_reason_code": (
                    lifecycle.get("reason_code") if lifecycle is not None else None
                ),
                "next_action": (
                    dict(lifecycle.get("next_action") or {})
                    if lifecycle is not None
                    else None
                ),
                "projection_status": projection_status,
                "projection_error": projection_error,
                "current_stage": None
                if lifecycle_inactive
                else _text(progress.get("current_stage")) or _text(status.get("current_stage")),
                "paper_stage": None
                if lifecycle_inactive
                else _text(progress.get("paper_stage")) or _text(status.get("paper_stage")),
                "quest_id": _text(status.get("quest_id")),
                "quest_status": None if lifecycle_inactive else _text(status.get("quest_status")),
                "active_run_id": None
                if lifecycle_inactive
                else _text(progress.get("active_run_id")) or _text(status.get("active_run_id")),
                "readable_artifact_refs": refs,
                "has_readable_artifact": bool(refs),
                "quality_debt": _mapping(progress.get("quality_debt")) or None,
                "ai_route_context": _mapping(progress.get("ai_route_context"))
                or {
                    "surface_kind": "mas_ai_route_context",
                    "semantic_route_owner": "codex_cli",
                    "may_start_any_declared_stage": True,
                    "may_advance_repeat_skip_or_route_back": True,
                    "program_recommendation_can_execute_or_block_route": False,
                },
            }
        )
    return {
        "surface": "study_state_matrix",
        "schema_version": 2,
        "workspace_root": str(Path(profile.workspace_root).expanduser().resolve()),
        "study_count": len(studies),
        "semantic_route_owner": "codex_cli",
        "transition_table_present": False,
        "program_can_select_or_block_stage": False,
        "studies": studies,
    }


def render_study_state_matrix_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Study State Matrix",
        "",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- study_count: `{payload.get('study_count')}`",
        "- semantic_route_owner: `codex_cli`",
        "",
        "| study_id | lifecycle | stage | quest | artifacts | projection |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for item in payload.get("studies") or []:
        study = _mapping(item)
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(study.get("study_id")) or "",
                    _text(study.get("lifecycle_state")) or "",
                    _text(study.get("current_stage")) or "",
                    _text(study.get("quest_status")) or "",
                    str(len(study.get("readable_artifact_refs") or [])),
                    _text(study.get("projection_status")) or "",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _readable_refs(refs: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            value.strip()
            for value in refs.values()
            if isinstance(value, str) and value.strip()
        }
    )


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        return dict(payload) if isinstance(payload, Mapping) else {}
    return {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_study_state_matrix",
    "render_study_state_matrix_markdown",
    "resolve_study_ids",
]
