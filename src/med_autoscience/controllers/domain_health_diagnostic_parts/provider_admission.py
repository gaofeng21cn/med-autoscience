from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_EXECUTOR_EXECUTION_LATEST = Path(
    "artifacts/supervision/consumer/default_executor_execution/latest.json"
)


def materialized_record_only_provider_handoff(materialize_result: Mapping[str, Any]) -> bool:
    return bool(materialized_record_only_provider_handoffs(materialize_result))


def materialized_record_only_provider_handoffs(materialize_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    handoffs: list[Mapping[str, Any]] = []
    for item in materialize_result.get("default_executor_dispatches") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("dispatch_status")) != "ready":
            continue
        if _non_empty_text(item.get("dispatch_authority")) != "ai_reviewer_record_production_handoff":
            continue
        handoffs.append(item)
    return handoffs


def provider_admission_pending_dispatch_result(
    *,
    materialize_result: Mapping[str, Any],
) -> dict[str, Any]:
    executions: list[dict[str, Any]] = []
    for handoff in materialized_record_only_provider_handoffs(materialize_result):
        executions.append(
            {
                "surface": "default_executor_dispatch_execution",
                "study_id": _non_empty_text(handoff.get("study_id")),
                "quest_id": _non_empty_text(handoff.get("quest_id")),
                "action_type": _non_empty_text(handoff.get("action_type")),
                "work_unit_id": handoff_work_unit_id(handoff),
                "dispatch_path": handoff_dispatch_path(handoff),
                "dispatch_authority": _non_empty_text(handoff.get("dispatch_authority")),
                "execution_status": "provider_admission_pending",
                "blocked_reason": None,
                "next_executable_owner": _non_empty_text(handoff.get("next_executable_owner")),
                "required_output_surface": _non_empty_text(handoff.get("required_output_surface")),
                "will_start_llm": False,
                "provider_attempt_or_lease_required": True,
                "provider_completion_is_domain_completion": False,
            }
        )
    return {
        "surface": "domain_owner_action_dispatch",
        "schema_version": 1,
        "execution_count": 0,
        "executed_count": 0,
        "blocked_count": 0,
        "repeat_suppressed_count": 0,
        "dry_run_count": 0,
        "codex_dispatch_count": 0,
        "suppressed_dispatch_count": len(executions),
        "provider_admission_pending_count": len(executions),
        "executions": executions,
        "written_files": [],
    }


def handoff_dispatch_path(handoff: Mapping[str, Any]) -> str | None:
    refs = _mapping(handoff.get("refs"))
    return (
        _non_empty_text(handoff.get("dispatch_path"))
        or _non_empty_text(handoff.get("stage_packet_ref"))
        or _non_empty_text(refs.get("stage_packet_path"))
        or _non_empty_text(refs.get("immutable_dispatch_path"))
        or _non_empty_text(refs.get("dispatch_path"))
    )


def handoff_work_unit_id(handoff: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(handoff.get("owner_route")) or _mapping(
        _mapping(handoff.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
    )


def provider_probe_has_matching_attempt(
    scan_result: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_study_id = _non_empty_text(identity.get("study_id"))
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if expected_study_id is not None and _non_empty_text(study.get("study_id")) != expected_study_id:
            continue
        if not study_has_running_provider_attempt(study):
            continue
        live_attempt = _mapping(study.get("opl_provider_attempt")) or study
        if provider_attempt_matches_identity(live_attempt, identity=identity):
            return True
    return False


def study_has_running_provider_attempt(study: Mapping[str, Any]) -> bool:
    return study.get("running_provider_attempt") is True and (
        _non_empty_text(study.get("active_stage_attempt_id"))
        or _non_empty_text(study.get("active_run_id"))
        or _non_empty_text(study.get("active_workflow_id"))
    ) is not None


def provider_attempt_matches_identity(
    live_attempt: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    if expected_action is not None and _non_empty_text(live_attempt.get("action_type")) != expected_action:
        return False
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_work_unit is not None and _non_empty_text(live_attempt.get("work_unit_id")) != expected_work_unit:
        return False
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    live_dispatch = _non_empty_text(live_attempt.get("dispatch_ref")) or _non_empty_text(live_attempt.get("dispatch_path"))
    if expected_dispatch is None or live_dispatch is None:
        return True
    normalized_expected = expected_dispatch.replace("\\", "/")
    normalized_live = live_dispatch.replace("\\", "/")
    return normalized_expected == normalized_live or normalized_expected.endswith(f"/{normalized_live}")


def provider_probe_has_non_running_actions(scan_result: Mapping[str, Any]) -> bool:
    running_study_ids = {
        study_id
        for study in scan_result.get("studies") or []
        if isinstance(study, Mapping)
        and study.get("running_provider_attempt") is True
        and (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for action in scan_result.get("action_queue") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None or study_id not in running_study_ids:
            return True
    return False


def persisted_provider_admission_candidates(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    execution_ref = Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_EXECUTION_LATEST
    payload = _read_json_object(execution_ref)
    if payload is None:
        return []
    return provider_admission_candidates_from_execution_payload(
        payload,
        execution_ref=str(execution_ref),
        status_payload=status_payload,
    )


def provider_admission_candidates_from_execution_payload(
    execution_payload: Mapping[str, Any],
    *,
    execution_ref: str | None = None,
    status_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    status = _mapping(status_payload)
    if _status_envelope_blocks_provider_admission(status):
        return []
    status_study_id = _non_empty_text(status.get("study_id"))
    current_action_identity = _current_action_identity(status)
    candidates: list[dict[str, Any]] = []
    for item in execution_payload.get("executions") or []:
        if not isinstance(item, Mapping):
            continue
        candidate = provider_admission_candidate_from_execution(
            item,
            execution_ref=execution_ref,
            status_study_id=status_study_id,
            current_action_identity=current_action_identity,
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def provider_admission_candidate_from_execution(
    execution: Mapping[str, Any],
    *,
    execution_ref: str | None = None,
    status_study_id: str | None = None,
    current_action_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if _non_empty_text(execution.get("execution_status")) != "handoff_ready":
        return None
    if not _provider_attempt_required(execution):
        return None
    if execution.get("owner_route_current") is False:
        return None
    study_id = _non_empty_text(execution.get("study_id"))
    if status_study_id is not None and study_id != status_study_id:
        return None
    action_type = _non_empty_text(execution.get("action_type"))
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    dispatch_path = handoff_dispatch_path(execution)
    if (
        study_id is None
        or action_type is None
        or work_unit_id is None
        or work_unit_fingerprint is None
        or dispatch_path is None
    ):
        return None
    if not _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=_mapping(current_action_identity),
    ):
        return None
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(_mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis"))
    )
    return {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "default_executor_execution",
        "execution_ref": execution_ref,
        "study_id": study_id,
        "quest_id": _non_empty_text(execution.get("quest_id")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(execution.get("action_fingerprint")) or work_unit_fingerprint,
        "dispatch_path": dispatch_path,
        "dispatch_authority": _non_empty_text(execution.get("dispatch_authority")),
        "owner_callable_surface": _non_empty_text(execution.get("owner_callable_surface")),
        "next_executable_owner": _non_empty_text(execution.get("next_executable_owner")),
        "required_output_surface": _non_empty_text(execution.get("required_output_surface")),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": execution.get("provider_completion_is_domain_completion") is True,
        "owner_route_current": execution.get("owner_route_current") is not False,
        "owner_route_basis": _non_empty_text(execution.get("owner_route_basis")),
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
        "source_refs": {
            key: source_refs[key]
            for key in (
                "work_unit_id",
                "work_unit_fingerprint",
                "blocked_reason",
                "publication_eval_path",
                "quest_root",
                "study_truth_epoch",
                "runtime_health_epoch",
            )
            if key in source_refs
        },
    }


def _current_action_identity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(status_payload.get("current_executable_owner_action"))
    if not current:
        return {}
    study_id = _non_empty_text(status_payload.get("study_id"))
    target_surface = _mapping(current.get("target_surface"))
    next_action = _mapping(current.get("next_action"))
    action_ids = _text_items(current.get("allowed_actions"))
    action_ids.extend(_text_items([
        current.get("action_type"),
        current.get("work_unit_id"),
        next_action.get("action_id"),
    ]))
    action_ids = list(dict.fromkeys(action_ids))
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(next_action.get("action_id"))
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(target_surface.get("surface_key"))
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(current.get("latest_owner_answer_ref"))
    fingerprint = _non_empty_text(current.get("work_unit_fingerprint"))
    fingerprints: list[str] = []
    if fingerprint is not None:
        fingerprints.append(fingerprint)
    if fingerprint is None and work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    if study_id is not None and work_unit_id is not None:
        for action_id in action_ids or [work_unit_id]:
            fingerprints.append(
                f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::{action_id}"
            )
    fingerprints = list(dict.fromkeys(fingerprints))
    if fingerprint is None and fingerprints:
        fingerprint = fingerprints[0]
    return {
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": fingerprints,
        "source_ref": source_ref,
    }


def _status_envelope_blocks_provider_admission(status_payload: Mapping[str, Any]) -> bool:
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(envelope.get("execution_state_kind"))
    return state_kind in {"parked", "running_provider_attempt", "typed_blocker"}


def _matches_current_action(
    *,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return True
    action_ids = set(_text_items(current_action_identity.get("action_ids")))
    if action_ids and action_type not in action_ids:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    if expected_work_unit_id is not None and work_unit_id != expected_work_unit_id:
        return False
    expected_fingerprints = set(_text_items(current_action_identity.get("work_unit_fingerprints")))
    if expected_fingerprints:
        return work_unit_fingerprint in expected_fingerprints
    expected_fingerprint = _non_empty_text(current_action_identity.get("work_unit_fingerprint"))
    if expected_fingerprint is not None:
        return work_unit_fingerprint == expected_fingerprint
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return expected_source_ref in work_unit_fingerprint
    return True


def _provider_attempt_required(execution: Mapping[str, Any]) -> bool:
    if execution.get("provider_attempt_or_lease_required") is True:
        return True
    return _non_empty_text(execution.get("owner_callable_surface")) == "opl_default_executor.stage_attempt"


def _work_unit_fingerprint(execution: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis")
    )
    return (
        _non_empty_text(execution.get("action_fingerprint"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
