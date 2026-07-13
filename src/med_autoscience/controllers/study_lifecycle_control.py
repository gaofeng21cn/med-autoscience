from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile


STUDY_LIFECYCLE_SCHEMA = "mas.study_lifecycle_control.v1"
WORKSPACE_LIFECYCLE_SCHEMA = "mas.workspace_study_lifecycle_control.v1"
STUDY_LIFECYCLE_RELPATH = Path("control") / "lifecycle.json"
STUDY_LIFECYCLE_HISTORY_RELPATH = (
    Path("artifacts") / "controller" / "lifecycle_control" / "history"
)
WORKSPACE_LIFECYCLE_RELPATH = (
    Path("runtime") / "artifacts" / "study_lifecycle_control" / "latest.json"
)
WORKSPACE_LIFECYCLE_HISTORY_RELPATH = (
    Path("runtime") / "artifacts" / "study_lifecycle_control" / "history"
)
SUPPORTED_LIFECYCLE_STATES = (
    "active",
    "paused",
    "delivered_paused",
    "stopped",
)
INACTIVE_LIFECYCLE_STATES = frozenset(
    {"paused", "delivered_paused", "stopped"}
)


def set_study_lifecycle(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_id: str,
    lifecycle_state: str,
    reason_code: str,
    reason_summary: str,
    source_kind: str,
    source_ref: str,
    evidence_refs: Iterable[str] = (),
    recorded_at: str | None = None,
) -> dict[str, Any]:
    study_root = _resolve_study_root(profile=profile, study_id=study_id)
    state = _validated_state(lifecycle_state)
    current = read_study_lifecycle(study_root=study_root, study_id=study_id)
    generation = int((current or {}).get("generation") or 0) + 1
    event_time = _normalized_timestamp(recorded_at)
    materialized_at = _utc_now()
    payload = {
        "schema_version": STUDY_LIFECYCLE_SCHEMA,
        "surface_kind": "study_lifecycle_control",
        "study_id": study_id,
        "lifecycle_state": state,
        "business_status": state,
        "generation": generation,
        "recorded_at": event_time,
        "materialized_at": materialized_at,
        "reason_code": _required_text(reason_code, "reason_code"),
        "reason_summary": _required_text(reason_summary, "reason_summary"),
        "source_kind": _required_text(source_kind, "source_kind"),
        "source_ref": _required_text(source_ref, "source_ref"),
        "evidence_refs": _unique_texts(evidence_refs),
        "lifecycle_ref": STUDY_LIFECYCLE_RELPATH.as_posix(),
        **_state_semantics(state),
        "authority_boundary": {
            "truth_owner": "MedAutoScience",
            "domain_truth": True,
            "opl_consumption": "read_only_projection",
            "runtime_or_telemetry_can_override": False,
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "submission_package_promoted": False,
        },
    }
    if current is not None and _semantic_lifecycle_payload(current) == _semantic_lifecycle_payload(payload):
        payload = current
        write_status = "unchanged"
    else:
        _write_study_lifecycle(study_root=study_root, payload=payload)
        write_status = "recorded"

    workspace_ledger = materialize_workspace_lifecycle_ledger(
        profile=profile,
        changed_study_id=study_id,
        changed_generation=int(payload["generation"]),
    )
    workspace_projection_status: dict[str, Any]
    if profile_ref is None:
        workspace_projection_status = {
            "status": "not_materialized",
            "reason": "profile_ref_not_provided",
        }
    else:
        from med_autoscience.controllers.study_workspace_status import (
            run_study_workspace_status,
        )

        workspace_status = run_study_workspace_status(
            profile_path=Path(profile_ref).expanduser().resolve(),
            study_ids=None,
            apply=True,
        )
        workspace_projection_status = {
            "status": "materialized",
            "study_count": workspace_status["study_count"],
            "recorded_at": workspace_status["recorded_at"],
        }
    return {
        "schema_version": 1,
        "surface_kind": "set_study_lifecycle_result",
        "status": write_status,
        "study_id": study_id,
        "lifecycle_state": payload["lifecycle_state"],
        "lifecycle": payload,
        "lifecycle_ref": str(study_root / STUDY_LIFECYCLE_RELPATH),
        "history_root": str(study_root / STUDY_LIFECYCLE_HISTORY_RELPATH),
        "workspace_lifecycle_ref": str(
            profile.workspace_root.expanduser().resolve() / WORKSPACE_LIFECYCLE_RELPATH
        ),
        "workspace_lifecycle": workspace_ledger,
        "workspace_index_ref": str(
            profile.workspace_root.expanduser().resolve() / "workspace_index.json"
        ),
        "workspace_projection_status": workspace_projection_status,
    }


def read_study_lifecycle(
    *,
    study_root: Path,
    study_id: str | None = None,
) -> dict[str, Any] | None:
    path = study_root.expanduser().resolve() / STUDY_LIFECYCLE_RELPATH
    if not path.is_file():
        return None
    payload = _read_json_object(path)
    if payload.get("schema_version") != STUDY_LIFECYCLE_SCHEMA:
        raise ValueError(f"unsupported study lifecycle schema: {path}")
    observed_study_id = _required_text(payload.get("study_id"), "study_id")
    if study_id is not None and observed_study_id != study_id:
        raise ValueError(
            f"study lifecycle identity mismatch: expected={study_id}, observed={observed_study_id}"
        )
    _validated_state(payload.get("lifecycle_state"))
    generation = payload.get("generation")
    if not isinstance(generation, int) or generation < 1:
        raise ValueError(f"study lifecycle generation must be a positive integer: {path}")
    return payload


def read_profile_study_lifecycle(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    return read_study_lifecycle(
        study_root=(profile.studies_root / study_id).expanduser().resolve(),
        study_id=study_id,
    )


def lifecycle_is_inactive(lifecycle: Mapping[str, Any] | None) -> bool:
    return bool(
        lifecycle
        and str(lifecycle.get("lifecycle_state") or "") in INACTIVE_LIFECYCLE_STATES
    )


def stage_index_respecting_lifecycle(
    *,
    stage_index: Mapping[str, Any],
    lifecycle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    projected = dict(stage_index)
    if not lifecycle_is_inactive(lifecycle):
        return projected
    previous_stage = projected.get("current_stage")
    projected["current_stage_id"] = None
    projected["current_stage"] = None
    projected["lifecycle_state"] = lifecycle.get("lifecycle_state")
    if isinstance(previous_stage, Mapping):
        projected["last_recorded_stage_id"] = previous_stage.get("stage_id")
    return projected


def package_status_respecting_lifecycle(
    *,
    package_status: Mapping[str, Any],
    lifecycle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    projected = dict(package_status)
    if not lifecycle_is_inactive(lifecycle):
        return projected
    state = str(lifecycle.get("lifecycle_state"))
    projected.update(
        {
            "status": lifecycle.get("package_status"),
            "reason": lifecycle.get("reason_code"),
            "lifecycle_state": state,
            "milestone_package_delivered": bool(
                lifecycle.get("milestone_package_delivered")
            ),
            "submission_ready": False,
            "promotion_allowed": False,
        }
    )
    return projected


def apply_lifecycle_to_progress_readback(
    *,
    payload: Mapping[str, Any],
    study_root: Path,
    lifecycle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    projected = dict(payload)
    control = dict(lifecycle or read_study_lifecycle(study_root=study_root) or {})
    if not control:
        return projected
    state = str(control["lifecycle_state"])
    lifecycle_path = study_root.expanduser().resolve() / STUDY_LIFECYCLE_RELPATH
    projected.update(
        {
            "business_status": state,
            "lifecycle_state": state,
            "lifecycle_control": control,
            "lifecycle_ref": str(lifecycle_path),
        }
    )
    refs = dict(projected.get("refs") or {})
    refs["study_lifecycle_control_path"] = str(lifecycle_path)
    projected["refs"] = refs
    if not lifecycle_is_inactive(control):
        return projected

    next_action = dict(control["next_action"])
    state_label = _state_label(state)
    summary = str(control["reason_summary"])
    next_summary = str(next_action["summary"])
    package = {
        "status": control["package_status"],
        "package_kind": (
            "milestone_submission_package"
            if control.get("milestone_package_delivered") is True
            else "no_active_submission_package"
        ),
        "milestone_package_delivered": bool(
            control.get("milestone_package_delivered")
        ),
        "submission_ready": False,
        "can_submit": False,
        "known_blockers": (
            ["submission_metadata_incomplete"]
            if state == "delivered_paused"
            else []
        ),
    }
    projected.update(
        {
            "current_stage": None,
            "current_stage_summary": f"No current automatic stage. {state_label}.",
            "paper_stage": None,
            "paper_stage_summary": f"No current automatic stage. {state_label}.",
            "active_run_id": None,
            "runtime_liveness_status": "not_running_by_lifecycle",
            "mission_state": state,
            "current_blockers": [],
            "needs_physician_decision": False,
            "needs_user_decision": False,
            "next_system_action": next_summary,
            "next_action": next_action,
            "next_legal_action": next_action,
            "next_owner_or_human_decision": {
                "kind": "lifecycle_control",
                "next_owner": next_action["owner"],
                "human_decision_required": False,
                "can_execute": False,
                "can_authorize_provider_attempt": False,
                "summary": next_summary,
            },
            "current_package": package,
            "auto_runtime_parked": {
                "schema_version": 1,
                "surface_kind": "auto_runtime_parked",
                "parked": True,
                "parked_state": state,
                "parked_state_label": state_label,
                "parked_owner": "MedAutoScience",
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": state in {"delivered_paused", "stopped"},
                "resource_release_expected": True,
                "reopen_policy": control["resume_policy"]["policy_id"],
                "next_action_summary": next_summary,
                "summary": summary,
            },
            "user_visible_projection": _user_visible_lifecycle_projection(
                control=control,
                lifecycle_path=lifecycle_path,
            ),
            "operator_status_card": {
                "surface_kind": "study_operator_status_card",
                "study_id": control["study_id"],
                "handling_state": state,
                "handling_state_label": state_label,
                "current_focus": summary,
                "owner_summary": summary,
                "user_visible_verdict": summary,
                "next_confirmation_signal": next_summary,
                "latest_truth_source": "study_lifecycle_control",
                "latest_truth_source_label": STUDY_LIFECYCLE_RELPATH.as_posix(),
                "latest_truth_time": control["recorded_at"],
            },
            "status_narration_contract": {
                "schema_version": 1,
                "surface_kind": "study_progress",
                "contract_id": f"study-progress::{control['study_id']}::lifecycle",
                "contract_kind": "lifecycle_status_narration",
                "audience": "human_user",
                "stage": {"current_stage": None, "paper_stage": None},
                "current_blockers": [],
                "latest_update": summary,
                "next_step": next_summary,
                "facts": {
                    "study_id": control["study_id"],
                    "lifecycle_state": state,
                    "lifecycle_ref": str(lifecycle_path),
                },
            },
            "ai_route_context": {
                "surface_kind": "mas_ai_route_context",
                "command_kind": "no_route_lifecycle_inactive",
                "route_selection_owner": "MedAutoScience",
                "can_submit_to_opl_runtime": False,
                "lifecycle_state": state,
            },
        }
    )
    return projected


def build_paper_mission_lifecycle_readback(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    source: str,
    dry_run: bool,
    lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    study_root = _resolve_study_root(profile=profile, study_id=study_id)
    base = {
        "surface_kind": "paper_mission_lifecycle_readback",
        "schema_version": 1,
        "paper_mission_command": paper_mission_command,
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(study_root),
        "study_root_exists": study_root.exists(),
    }
    projected = apply_lifecycle_to_progress_readback(
        payload=base,
        study_root=study_root,
        lifecycle=lifecycle,
    )
    projected.update(
        {
            "action_intent": "inspect_lifecycle_truth",
            "can_submit_to_opl_runtime": False,
            "durable_mission_stop_guard": {
                "stop": True,
                "reason": "study_lifecycle_is_not_active",
                "lifecycle_state": lifecycle["lifecycle_state"],
            },
            "dispatch_plan": {
                "domain_handler_dispatch_mode": "lifecycle_readback_no_write",
                "runtime_route_allowed": False,
                "required_reactivation": lifecycle["resume_policy"],
            },
            "mutation_policy": {
                "writes_authority": False,
                "writes_runtime": False,
                "writes_paper_body": False,
                "dry_run_only": True,
            },
        }
    )
    return projected


def build_launch_lifecycle_gate(
    *,
    study_id: str,
    study_root: Path,
    lifecycle: Mapping[str, Any],
    explicit_user_wakeup: bool,
    allow_stopped_relaunch: bool,
) -> dict[str, Any] | None:
    if not lifecycle_is_inactive(lifecycle):
        return None
    state = str(lifecycle["lifecycle_state"])
    if state == "stopped":
        allowed = explicit_user_wakeup and allow_stopped_relaunch
        required = "explicit_user_wakeup_and_allow_stopped_relaunch"
    else:
        allowed = explicit_user_wakeup
        required = "explicit_user_wakeup"
    if allowed:
        return None
    return {
        "schema_version": 1,
        "surface_kind": "mas_study_launch_projection",
        "study_id": study_id,
        "lifecycle_control": dict(lifecycle),
        "runtime_status": {
            "decision": state,
            "reason": lifecycle["reason_code"],
            "current_stage": None,
        },
        "progress": apply_lifecycle_to_progress_readback(
            payload={"study_id": study_id},
            study_root=study_root,
            lifecycle=lifecycle,
        ),
        "runtime_handoff": {
            "status": "lifecycle_reactivation_required",
            "can_submit_to_opl_runtime": False,
            "required_reactivation": required,
            "explicit_user_wakeup_requested": bool(explicit_user_wakeup),
            "allow_stopped_relaunch_requested": bool(allow_stopped_relaunch),
            "authority_boundary": {
                "mas_creates_provider_attempt": False,
                "mas_writes_runtime_queue": False,
                "lifecycle_gate_can_be_bypassed_by_force": False,
            },
        },
    }


def materialize_workspace_lifecycle_ledger(
    *,
    profile: WorkspaceProfile,
    changed_study_id: str,
    changed_generation: int,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    studies_root = profile.studies_root.expanduser().resolve()
    study_ids = tuple(
        child.name
        for child in sorted(studies_root.iterdir(), key=lambda item: item.name)
        if child.is_dir() and (child / "study.yaml").is_file()
    )
    records: list[dict[str, Any]] = []
    for study_id in study_ids:
        lifecycle = read_study_lifecycle(
            study_root=studies_root / study_id,
            study_id=study_id,
        )
        if lifecycle is not None:
            records.append(dict(lifecycle))
    recorded_at = _utc_now()
    counts: dict[str, int] = {}
    for record in records:
        state = str(record["lifecycle_state"])
        counts[state] = counts.get(state, 0) + 1
    payload = {
        "schema_version": WORKSPACE_LIFECYCLE_SCHEMA,
        "surface_kind": "workspace_study_lifecycle_control",
        "workspace_name": profile.name,
        "workspace_root": str(workspace_root),
        "recorded_at": recorded_at,
        "study_count": len(study_ids),
        "recorded_study_count": len(records),
        "unrecorded_study_ids": [
            study_id
            for study_id in study_ids
            if study_id not in {str(record["study_id"]) for record in records}
        ],
        "status_counts": counts,
        "changed_study_id": changed_study_id,
        "changed_generation": changed_generation,
        "studies": records,
        "authority_boundary": {
            "truth_owner": "MedAutoScience",
            "derived_from_per_study_lifecycle_ledgers": True,
            "opl_consumption": "read_only_projection",
            "runtime_or_telemetry_can_override": False,
        },
    }
    _write_json_atomic(workspace_root / WORKSPACE_LIFECYCLE_RELPATH, payload)
    history_name = (
        f"{_history_stamp(recorded_at)}-{_safe_segment(changed_study_id)}-"
        f"g{changed_generation:04d}.json"
    )
    _write_json_atomic(
        workspace_root / WORKSPACE_LIFECYCLE_HISTORY_RELPATH / history_name,
        payload,
    )
    return payload


def _write_study_lifecycle(*, study_root: Path, payload: Mapping[str, Any]) -> None:
    current_path = study_root / STUDY_LIFECYCLE_RELPATH
    _write_json_atomic(current_path, payload)
    history_name = (
        f"{_history_stamp(str(payload['recorded_at']))}-"
        f"g{int(payload['generation']):04d}.json"
    )
    _write_json_atomic(
        study_root / STUDY_LIFECYCLE_HISTORY_RELPATH / history_name,
        payload,
    )


def _resolve_study_root(*, profile: WorkspaceProfile, study_id: str) -> Path:
    normalized_study_id = _required_text(study_id, "study_id")
    study_root = (profile.studies_root / normalized_study_id).expanduser().resolve()
    expected_root = profile.studies_root.expanduser().resolve()
    if study_root.parent != expected_root:
        raise ValueError(f"study root must be directly under profile studies_root: {study_root}")
    study_yaml_path = study_root / "study.yaml"
    if not study_yaml_path.is_file():
        raise ValueError(f"study.yaml not found for lifecycle control: {study_yaml_path}")
    study_payload = yaml.safe_load(study_yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(study_payload, Mapping):
        raise ValueError(f"study.yaml must contain a mapping: {study_yaml_path}")
    declared_study_id = str(study_payload.get("study_id") or "").strip()
    if declared_study_id and declared_study_id != normalized_study_id:
        raise ValueError(
            "study lifecycle identity mismatch between directory and study.yaml: "
            f"directory={normalized_study_id}, declared={declared_study_id}"
        )
    return study_root


def _state_semantics(state: str) -> dict[str, Any]:
    if state == "active":
        return {
            "current_stage_id": None,
            "current_stage_status": None,
            "current_stage_policy": "project_current_runtime_stage",
            "milestone_package_delivered": False,
            "submission_ready": False,
            "package_status": "not_ready",
            "next_action": {
                "surface_kind": "mas_lifecycle_action",
                "action_id": "continue_current_study_line",
                "action_type": "agent_action",
                "owner": "MedAutoScience",
                "status": "active",
                "summary": "Continue the current study line through the canonical MAS route.",
            },
            "resume_policy": {
                "policy_id": "automatic_allowed",
                "auto_resume_allowed": True,
                "explicit_user_wakeup_required": False,
                "allow_stopped_relaunch_required": False,
            },
        }
    if state == "delivered_paused":
        return {
            "current_stage_id": None,
            "current_stage_status": None,
            "current_stage_policy": "no_current_stage_while_inactive",
            "milestone_package_delivered": True,
            "submission_ready": False,
            "package_status": "milestone_delivered",
            "next_action": {
                "surface_kind": "mas_lifecycle_action",
                "action_id": "complete_submission_metadata_or_wake_for_revision",
                "action_type": "user_action",
                "owner": "user",
                "status": "waiting",
                "summary": (
                    "The milestone submission package is delivered. Provide missing submission "
                    "metadata, or explicitly wake the study for revision."
                ),
            },
            "resume_policy": {
                "policy_id": "explicit_user_wakeup",
                "auto_resume_allowed": False,
                "explicit_user_wakeup_required": True,
                "allow_stopped_relaunch_required": False,
            },
        }
    if state == "stopped":
        return {
            "current_stage_id": None,
            "current_stage_status": None,
            "current_stage_policy": "no_current_stage_while_inactive",
            "milestone_package_delivered": False,
            "submission_ready": False,
            "package_status": "not_ready",
            "next_action": {
                "surface_kind": "mas_lifecycle_action",
                "action_id": "remain_stopped_until_explicit_relaunch",
                "action_type": "user_action",
                "owner": "user",
                "status": "stopped",
                "summary": (
                    "No automatic work is scheduled. Relaunch requires an explicit user wakeup "
                    "and stopped-study authorization."
                ),
            },
            "resume_policy": {
                "policy_id": "explicit_stopped_relaunch",
                "auto_resume_allowed": False,
                "explicit_user_wakeup_required": True,
                "allow_stopped_relaunch_required": True,
            },
        }
    return {
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "no_current_stage_while_inactive",
        "milestone_package_delivered": False,
        "submission_ready": False,
        "package_status": "not_ready",
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "wait_for_explicit_user_wakeup",
            "action_type": "user_action",
            "owner": "user",
            "status": "paused",
            "summary": "No automatic work is scheduled until the user explicitly wakes the study.",
        },
        "resume_policy": {
            "policy_id": "explicit_user_wakeup",
            "auto_resume_allowed": False,
            "explicit_user_wakeup_required": True,
            "allow_stopped_relaunch_required": False,
        },
    }


def _user_visible_lifecycle_projection(
    *,
    control: Mapping[str, Any],
    lifecycle_path: Path,
) -> dict[str, Any]:
    state = str(control["lifecycle_state"])
    next_action = dict(control["next_action"])
    return {
        "surface": "study_progress_user_visible_projection",
        "schema_version": 3,
        "read_model": "study_lifecycle_user_truth",
        "authority": "study_lifecycle_control",
        "projection_only": True,
        "study_id": control["study_id"],
        "state": state,
        "state_label": _state_label(state),
        "state_summary": control["reason_summary"],
        "status_summary": control["reason_summary"],
        "current_stage": None,
        "current_stage_label": "No current stage",
        "current_stage_summary": "No current automatic stage.",
        "paper_stage": None,
        "paper_stage_summary": "No current automatic stage.",
        "writer_state": state,
        "actual_write_active": False,
        "package_delivered": bool(control.get("milestone_package_delivered")),
        "meaningful_artifact_delta": False,
        "next_owner": next_action["owner"],
        "next_step": next_action["summary"],
        "next_system_action": next_action["summary"],
        "why_not_progressing": control["reason_summary"],
        "user_action_required": False,
        "needs_user_decision": False,
        "needs_physician_decision": False,
        "user_next": control["resume_policy"]["policy_id"],
        "lifecycle_ref": str(lifecycle_path),
        "evidence_refs": {
            "study_lifecycle_control_path": str(lifecycle_path),
            "source_ref": control["source_ref"],
            "evidence_refs": list(control.get("evidence_refs") or []),
        },
    }


def _state_label(state: str) -> str:
    return {
        "active": "Active",
        "paused": "Paused",
        "delivered_paused": "Milestone delivered; automatically paused",
        "stopped": "Stopped",
    }[state]


def _semantic_lifecycle_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    ignored = {"generation", "materialized_at"}
    return {key: value for key, value in payload.items() if key not in ignored}


def _validated_state(value: object) -> str:
    state = _required_text(value, "lifecycle_state")
    if state not in SUPPORTED_LIFECYCLE_STATES:
        raise ValueError(
            "unsupported lifecycle_state: "
            f"{state}; supported={', '.join(SUPPORTED_LIFECYCLE_STATES)}"
        )
    return state


def _normalized_timestamp(value: str | None) -> str:
    if value is None:
        return _utc_now()
    text = _required_text(value, "recorded_at")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("recorded_at must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _history_stamp(value: str) -> str:
    return (
        value.replace("-", "")
        .replace(":", "")
        .replace("+", "")
        .replace(".", "")
    )


def _safe_segment(value: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "-" for character in value)


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _unique_texts(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON surface must contain an object: {path}")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        json.dump(dict(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


__all__ = [
    "INACTIVE_LIFECYCLE_STATES",
    "STUDY_LIFECYCLE_HISTORY_RELPATH",
    "STUDY_LIFECYCLE_RELPATH",
    "SUPPORTED_LIFECYCLE_STATES",
    "WORKSPACE_LIFECYCLE_RELPATH",
    "apply_lifecycle_to_progress_readback",
    "build_launch_lifecycle_gate",
    "build_paper_mission_lifecycle_readback",
    "lifecycle_is_inactive",
    "materialize_workspace_lifecycle_ledger",
    "package_status_respecting_lifecycle",
    "read_profile_study_lifecycle",
    "read_study_lifecycle",
    "set_study_lifecycle",
    "stage_index_respecting_lifecycle",
]
