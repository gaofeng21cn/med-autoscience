from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.controllers.mainline_status import PROGRAM_ID as DEFAULT_PROGRAM_ID
from opl_harness_shared.family_orchestration import (
    build_family_human_gate as _build_shared_family_human_gate,
    build_family_orchestration_companion as _build_shared_family_orchestration_companion,
    resolve_active_run_id as _resolve_shared_active_run_id,
    resolve_program_id as _resolve_shared_program_id,
)


TARGET_DOMAIN_ID = "medautoscience"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_refs(refs: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for ref in refs or ():
        if not isinstance(ref, Mapping):
            continue
        ref_kind = _text(ref.get("ref_kind"))
        ref_value = _text(ref.get("ref"))
        if ref_kind is None or ref_value is None:
            continue
        payload: dict[str, Any] = {
            "ref_kind": ref_kind,
            "ref": ref_value,
        }
        role = _text(ref.get("role"))
        if role is not None:
            payload["role"] = role
        label = _text(ref.get("label"))
        if label is not None:
            payload["label"] = label
        normalized.append(payload)
    return normalized


def resolve_program_id(execution: Mapping[str, Any] | None = None) -> str:
    return _resolve_shared_program_id(execution, fallback=DEFAULT_PROGRAM_ID)


def resolve_active_run_id(*values: object) -> str | None:
    return _resolve_shared_active_run_id(*values)


def build_family_human_gate(
    *,
    gate_id: str,
    gate_kind: str,
    requested_at: str,
    request_surface_kind: str,
    request_surface_id: str,
    evidence_refs: Sequence[Mapping[str, Any]],
    decision_options: Sequence[str],
    status: str = "requested",
    decision: Mapping[str, Any] | None = None,
    target_domain_id: str = TARGET_DOMAIN_ID,
    command: str | None = None,
) -> dict[str, Any]:
    return _build_shared_family_human_gate(
        gate_id=gate_id,
        gate_kind=gate_kind,
        requested_at=requested_at,
        request_surface_kind=request_surface_kind,
        request_surface_id=request_surface_id,
        evidence_refs=_normalize_refs(evidence_refs),
        decision_options=decision_options,
        status=status,
        decision=decision,
        target_domain_id=target_domain_id,
        command=command,
    )


def build_family_orchestration_companion(
    *,
    surface_kind: str,
    surface_id: str,
    event_name: str,
    source_surface: str,
    session_id: str,
    program_id: str | None,
    study_id: str | None,
    quest_id: str | None,
    active_run_id: str | None,
    runtime_decision: str | None,
    runtime_reason: str | None,
    payload: Mapping[str, Any] | None = None,
    event_time: str | None = None,
    checkpoint_id: str | None = None,
    checkpoint_label: str | None = None,
    audit_refs: Sequence[Mapping[str, Any]] | None = None,
    state_refs: Sequence[Mapping[str, Any]] | None = None,
    restoration_evidence: Sequence[Mapping[str, Any]] | None = None,
    action_graph_id: str | None = None,
    node_id: str | None = None,
    gate_id: str | None = None,
    resume_mode: str = "resume_from_checkpoint",
    resume_handle: str | None = None,
    human_gate_required: bool = False,
    parent_envelope_id: str | None = None,
    parent_session_id: str | None = None,
    parent_lineage_id: str | None = None,
    parent_checkpoint_id: str | None = None,
    resume_from_lineage_id: str | None = None,
    human_gates: Sequence[Mapping[str, Any]] | None = None,
    target_domain_id: str = TARGET_DOMAIN_ID,
) -> dict[str, Any]:
    payload_bundle = _build_shared_family_orchestration_companion(
        surface_kind=surface_kind,
        surface_id=surface_id,
        event_name=event_name,
        source_surface=source_surface,
        session_id=session_id,
        program_id=program_id,
        study_id=study_id,
        quest_id=quest_id,
        active_run_id=active_run_id,
        runtime_decision=runtime_decision,
        runtime_reason=runtime_reason,
        payload=payload,
        event_time=event_time,
        checkpoint_id=checkpoint_id,
        checkpoint_label=checkpoint_label,
        audit_refs=_normalize_refs(audit_refs),
        state_refs=_normalize_refs(state_refs),
        restoration_evidence=_normalize_refs(restoration_evidence),
        action_graph_id=action_graph_id,
        node_id=node_id,
        gate_id=gate_id,
        resume_mode=resume_mode,
        resume_handle=resume_handle,
        human_gate_required=human_gate_required,
        parent_envelope_id=parent_envelope_id,
        parent_session_id=parent_session_id,
        parent_lineage_id=parent_lineage_id,
        parent_checkpoint_id=parent_checkpoint_id,
        resume_from_lineage_id=resume_from_lineage_id,
        human_gates=human_gates,
        target_domain_id=target_domain_id,
    )
    return {
        "family_event_envelope": payload_bundle["family_event_envelope"],
        "family_checkpoint_lineage": payload_bundle["family_checkpoint_lineage"],
        "family_human_gates": payload_bundle["family_human_gates"],
    }
