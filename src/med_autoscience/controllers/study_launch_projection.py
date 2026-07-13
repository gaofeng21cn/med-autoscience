from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_status_projection, study_truth_kernel
from med_autoscience.controllers import study_lifecycle_control
from med_autoscience.controllers.study_progress.projection import (
    build_study_progress_projection,
)
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SUPPORTED_ENTRY_MODES = ("direct", "opl-handoff")


def launch_study(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    allow_stopped_relaunch: bool = False,
    explicit_user_wakeup: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _ = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    selected_entry_mode = _entry_mode(entry_mode)
    lifecycle = study_lifecycle_control.read_study_lifecycle(
        study_root=resolved_study_root,
        study_id=resolved_study_id,
    )
    lifecycle_gate = study_lifecycle_control.build_launch_lifecycle_gate(
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        lifecycle=lifecycle or {},
        explicit_user_wakeup=explicit_user_wakeup,
        allow_stopped_relaunch=allow_stopped_relaunch,
    )
    if lifecycle_gate is not None:
        lifecycle_gate["runtime_handoff"]["entry_mode"] = selected_entry_mode
        lifecycle_gate["runtime_handoff"]["force_requested"] = bool(force)
        return lifecycle_gate
    runtime_status = _mapping_payload(
        domain_status_projection.progress_projection(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            entry_mode=None,
        )
    )
    wakeup = _record_explicit_user_wakeup(
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        runtime_status=runtime_status,
        profile_ref=profile_ref,
        enabled=explicit_user_wakeup,
    )
    lifecycle_transition = None
    if wakeup is not None and study_lifecycle_control.lifecycle_is_inactive(lifecycle):
        lifecycle_transition = study_lifecycle_control.set_study_lifecycle(
            profile=profile,
            profile_ref=profile_ref,
            study_id=resolved_study_id,
            lifecycle_state="active",
            reason_code="explicit_user_wakeup",
            reason_summary="The user explicitly reactivated this MAS study line.",
            source_kind="explicit_user_wakeup",
            source_ref=str(wakeup["event_id"]),
            evidence_refs=(
                str(resolved_study_root / study_lifecycle_control.STUDY_LIFECYCLE_RELPATH),
                str(wakeup["snapshot_path"]),
            ),
            recorded_at=_text(wakeup.get("recorded_at")),
        )
    if wakeup is not None:
        runtime_status = _mapping_payload(
            domain_status_projection.progress_projection(
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                entry_mode=None,
            )
        )
        runtime_status["study_truth_snapshot"] = wakeup["snapshot"]
    progress = build_study_progress_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=runtime_status,
        entry_mode=selected_entry_mode,
        materialize_read_model_artifacts=False,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_study_launch_projection",
        "study_id": resolved_study_id,
        "runtime_status": runtime_status,
        "progress": progress,
        "runtime_handoff": {
            "status": "opl_attempt_admission_required",
            "entry_mode": selected_entry_mode,
            "runtime_owner": "one-person-lab",
            "domain_owner": "MedAutoScience",
            "allow_stopped_relaunch_requested": bool(allow_stopped_relaunch),
            "explicit_user_wakeup_requested": bool(explicit_user_wakeup),
            "explicit_user_wakeup_ref": (wakeup or {}).get("event_id"),
            "lifecycle_transition": lifecycle_transition,
            "force_requested": bool(force),
            "authority_boundary": {
                "mas_creates_provider_attempt": False,
                "mas_writes_runtime_queue": False,
                "mas_can_record_explicit_wakeup_truth": True,
                "opl_can_write_study_truth": False,
            },
        },
    }


def render_launch_study_markdown(payload: dict[str, Any]) -> str:
    runtime_status = dict(payload.get("runtime_status") or {})
    handoff = dict(payload.get("runtime_handoff") or {})
    return "\n".join(
        (
            "# Launch Study",
            "",
            f"- study_id: `{payload.get('study_id') or 'unknown'}`",
            f"- domain decision: `{runtime_status.get('decision') or 'unknown'}`",
            f"- domain reason: `{runtime_status.get('reason') or 'none'}`",
            f"- runtime handoff: `{handoff.get('status') or 'unknown'}`",
            "",
        )
    )


def _entry_mode(value: str | None) -> str:
    mode = _text(value) or "opl-handoff"
    if mode not in SUPPORTED_ENTRY_MODES:
        raise ValueError(
            f"study launch entry mode unsupported: {mode}; "
            f"supported_entry_modes={', '.join(SUPPORTED_ENTRY_MODES)}"
        )
    return mode


def _record_explicit_user_wakeup(
    *,
    study_root: Path,
    study_id: str,
    runtime_status: dict[str, Any],
    profile_ref: str | Path | None,
    enabled: bool,
) -> dict[str, Any] | None:
    if not enabled:
        return None
    recorded_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event = study_truth_kernel.append_truth_event(
        study_root=study_root,
        study_id=study_id,
        event_type="explicit_resume",
        payload={
            "current_required_action": "resume_same_study_line",
            "summary": "User explicitly requested MAS study resume.",
            "resume_owner": "one-person-lab",
            "domain_owner": "MedAutoScience",
            "quest_id": _text(runtime_status.get("quest_id")),
            "quest_status": _text(runtime_status.get("quest_status")),
            "previous_reason": _text(runtime_status.get("reason")),
            "previous_decision": _text(runtime_status.get("decision")),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        recorded_at=recorded_at,
    )
    snapshot_path = study_truth_kernel.materialize_truth_snapshot(
        study_root=study_root,
        study_id=study_id,
    )
    return {
        "event_id": event["event_id"],
        "recorded_at": recorded_at,
        "snapshot_path": str(snapshot_path),
        "snapshot": study_truth_kernel.rebuild_truth_snapshot(
            study_root=study_root,
            study_id=study_id,
        ),
    }


def _mapping_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, dict):
            return dict(payload)
    raise TypeError("study launch runtime status must be a mapping-like payload")


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


__all__ = ["launch_study", "render_launch_study_markdown"]
