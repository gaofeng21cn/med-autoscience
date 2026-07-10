from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_runtime_resolution import (
    _execution_payload,
    _resolve_study,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    render_task_intake_markdown,
    write_task_intake,
)


SCHEMA_VERSION = 1


def submit_study_task(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    task_intent: str,
    entry_mode: str | None = None,
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
    task_intake_kind: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    execution = _execution_payload(study_payload, profile=profile)
    selected_entry_mode = (
        _text(entry_mode)
        or _text(execution.get("default_entry_mode"))
        or "full_research"
    )
    payload = write_task_intake(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=selected_entry_mode,
        task_intent=task_intent,
        journal_target=journal_target,
        constraints=_text_values(constraints),
        evidence_boundary=_text_values(evidence_boundary),
        trusted_inputs=_text_values(trusted_inputs),
        reference_papers=_text_values(reference_papers),
        first_cycle_outputs=_text_values(first_cycle_outputs),
        task_intake_kind=task_intake_kind,
    )
    latest = read_latest_task_intake(study_root=resolved_study_root) or payload
    artifacts = dict(latest.get("artifact_refs") or payload.get("artifact_refs") or {})
    task_intake_ref = _text(artifacts.get("latest_json"))
    runtime_handoff = {
        "surface_kind": "mas_study_task_intake_owner_route_ref",
        "status": "opl_owner_route_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "MedAutoScience",
        "profile_ref": str(profile_ref) if profile_ref is not None else None,
        "study_id": resolved_study_id,
        "task_id": latest.get("task_id"),
        "task_intake_ref": task_intake_ref,
        "authority_boundary": {
            "mas_writes_task_intake_truth": True,
            "mas_writes_runtime_queue": False,
            "mas_creates_provider_attempt": False,
            "opl_can_rewrite_task_intake_truth": False,
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_study_task_submission",
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "task_id": latest.get("task_id"),
        "entry_mode": latest.get("entry_mode"),
        "task_intake_kind": latest.get("task_intake_kind"),
        "task_intent": latest.get("task_intent"),
        "journal_target": latest.get("journal_target"),
        "constraints": list(latest.get("constraints") or []),
        "evidence_boundary": list(latest.get("evidence_boundary") or []),
        "trusted_inputs": list(latest.get("trusted_inputs") or []),
        "reference_papers": list(latest.get("reference_papers") or []),
        "first_cycle_outputs": list(latest.get("first_cycle_outputs") or []),
        "revision_intake": latest.get("revision_intake"),
        "manual_hold_intake": latest.get("manual_hold_intake"),
        "artifacts": artifacts,
        "runtime_handoff": runtime_handoff,
    }


def render_submit_study_task_markdown(payload: dict[str, Any]) -> str:
    text = render_task_intake_markdown(
        {
            "study_id": payload.get("study_id"),
            "emitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "entry_mode": payload.get("entry_mode"),
            "task_intake_kind": payload.get("task_intake_kind"),
            "journal_target": payload.get("journal_target"),
            "task_intent": payload.get("task_intent"),
            "constraints": payload.get("constraints") or [],
            "evidence_boundary": payload.get("evidence_boundary") or [],
            "trusted_inputs": payload.get("trusted_inputs") or [],
            "reference_papers": payload.get("reference_papers") or [],
            "first_cycle_outputs": payload.get("first_cycle_outputs") or [],
        }
    ).rstrip("\n")
    return (
        f"{text}\n\n## OPL Handoff\n\n"
        f"- status: `{dict(payload.get('runtime_handoff') or {}).get('status') or 'unknown'}`\n"
        f"- task_intake_ref: `{dict(payload.get('runtime_handoff') or {}).get('task_intake_ref') or 'none'}`\n"
    )


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _text_values(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(text for value in values if (text := _text(value)) is not None))


__all__ = ["render_submit_study_task_markdown", "submit_study_task"]
