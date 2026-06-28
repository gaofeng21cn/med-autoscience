from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def candidate_with_transition_log_readback(
    candidate: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    payload = dict(candidate)
    if candidate_opl_transition_readback(payload):
        return payload
    idempotency_key = transition_request_idempotency_key(payload)
    if idempotency_key is None:
        return payload
    log_path = domain_progress_transition_command_event_log_path(study_root=study_root)
    readbacks_by_key = domain_progress_transition_log_readbacks_by_idempotency_key(log_path)
    readback = readbacks_by_key.get(idempotency_key)
    if readback is None:
        return payload
    with_readback = {
        **payload,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    readback_identity = _mapping(readback.get("identity"))
    stage_run_identity = _mapping(readback_identity.get("stage_run_identity"))
    route_identity_key = _non_empty_text(stage_run_identity.get("route_identity_key"))
    attempt_idempotency_key = _non_empty_text(stage_run_identity.get("attempt_idempotency_key"))
    request_idempotency_key = _non_empty_text(readback_identity.get("idempotency_key"))
    source_refs = dict(_mapping(payload.get("source_refs")))
    if route_identity_key is not None:
        with_readback["route_identity_key"] = route_identity_key
        source_refs["route_identity_key"] = route_identity_key
    if attempt_idempotency_key is not None:
        with_readback["attempt_idempotency_key"] = attempt_idempotency_key
        source_refs["attempt_idempotency_key"] = attempt_idempotency_key
    if request_idempotency_key is not None:
        with_readback["idempotency_key"] = request_idempotency_key
        source_refs["request_idempotency_key"] = request_idempotency_key
    if source_refs:
        with_readback["source_refs"] = source_refs
    provider_identity = dict(_mapping(payload.get("provider_admission_identity")))
    if route_identity_key is not None:
        provider_identity["route_identity_key"] = route_identity_key
    if attempt_idempotency_key is not None:
        provider_identity["attempt_idempotency_key"] = attempt_idempotency_key
    if request_idempotency_key is not None:
        provider_identity["idempotency_key"] = request_idempotency_key
    provider_identity["opl_domain_progress_transition_runtime_live_readback"] = readback
    with_readback["provider_admission_identity"] = provider_identity
    if not provider_admission_opl_transition_readback(
        with_readback,
        require_explicit_identity=True,
    ):
        return payload
    return with_readback


def domain_progress_transition_command_event_log_path(*, study_root: Path) -> Path:
    root = Path(study_root).expanduser().resolve()
    workspace_root = root.parent.parent if root.parent.name == "studies" else root
    return (
        workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )


def domain_progress_transition_log_readbacks_by_idempotency_key(
    path: Path,
) -> dict[str, dict[str, Any]]:
    from med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff import (
        _domain_progress_transition_log_readbacks_by_idempotency_key as _readbacks,
    )

    return _readbacks(path)


def transition_request_idempotency_key(candidate: Mapping[str, Any]) -> str | None:
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    stage_run_identity = _mapping(transition_request.get("stage_run_identity"))
    source_refs = _mapping(candidate.get("source_refs"))
    return (
        _non_empty_text(transition_request.get("idempotency_key"))
        or _non_empty_text(transition_request.get("request_idempotency_key"))
        or _non_empty_text(stage_run_identity.get("route_identity_key"))
        or _non_empty_text(stage_run_identity.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("request_idempotency_key"))
        or _non_empty_text(candidate.get("request_idempotency_key"))
        or _non_empty_text(candidate.get("idempotency_key"))
        or _non_empty_text(candidate.get("route_identity_key"))
        or _non_empty_text(candidate.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("route_identity_key"))
        or _non_empty_text(source_refs.get("attempt_idempotency_key"))
    )
