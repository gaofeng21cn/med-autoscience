from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from med_autoscience.controllers.mainline_status import PROGRAM_ID as DEFAULT_PROGRAM_ID


FAMILY_EVENT_ENVELOPE_VERSION = "family-event-envelope.v1"
FAMILY_CHECKPOINT_LINEAGE_VERSION = "family-checkpoint-lineage.v1"
FAMILY_HUMAN_GATE_VERSION = "family-human-gate.v1"
TARGET_DOMAIN_ID = "medautoscience"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _stable_id(prefix: str, *parts: object) -> str:
    source = "|".join(str(part or "").strip() for part in parts)
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()}


def _normalize_refs(refs: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for ref in refs or ():
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
    if isinstance(execution, Mapping):
        for key in ("program_id", "runtime_program_id", "program"):
            value = _text(execution.get(key))
            if value is not None:
                return value
    return DEFAULT_PROGRAM_ID


def resolve_active_run_id(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


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
    normalized_evidence_refs = _normalize_refs(evidence_refs)
    if not normalized_evidence_refs:
        normalized_evidence_refs = [
            {
                "ref_kind": "repo_path",
                "ref": _text(request_surface_id) or "unknown_surface",
                "label": "request_surface",
            }
        ]
    normalized_decision_options = [option for option in (_text(item) for item in decision_options) if option is not None]
    if not normalized_decision_options:
        normalized_decision_options = ["acknowledge"]
    payload: dict[str, Any] = {
        "version": FAMILY_HUMAN_GATE_VERSION,
        "gate_id": _text(gate_id),
        "target_domain_id": _text(target_domain_id),
        "gate_kind": _text(gate_kind),
        "requested_at": _text(requested_at) or _utc_now(),
        "status": _text(status) or "requested",
        "request_surface": {
            "surface_kind": _text(request_surface_kind),
            "surface_id": _text(request_surface_id),
        },
        "evidence_refs": normalized_evidence_refs,
        "decision_options": normalized_decision_options,
    }
    if command is not None:
        payload["request_surface"]["command"] = command
    if decision is not None:
        payload["decision"] = _copy_mapping(decision)
    return payload


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
    resolved_event_time = _text(event_time) or _utc_now()
    resolved_surface_kind = _text(surface_kind) or "unknown_surface"
    resolved_surface_id = _text(surface_id) or "unknown_surface_id"
    resolved_event_name = _text(event_name) or "runtime_event"
    resolved_session_id = _text(session_id) or _stable_id("session", study_id, quest_id, resolved_event_name)
    resolved_checkpoint_id = _text(checkpoint_id) or _stable_id(
        "checkpoint",
        study_id,
        quest_id,
        runtime_decision,
        runtime_reason,
        resolved_event_name,
    )
    resolved_lineage_id = _stable_id("lineage", resolved_session_id, resolved_checkpoint_id)
    resolved_envelope_id = _stable_id(
        "evt",
        resolved_surface_id,
        resolved_event_name,
        resolved_event_time,
        resolved_session_id,
        resolved_checkpoint_id,
    )
    resolved_correlation_id = _stable_id(
        "corr",
        resolved_session_id,
        resolved_event_name,
        resolved_checkpoint_id,
    )
    resolved_program_id = _text(program_id) or DEFAULT_PROGRAM_ID

    envelope_session: dict[str, Any] = {
        "session_id": resolved_session_id,
        "source_surface": _text(source_surface) or resolved_surface_kind,
    }
    if active_run_id is not None:
        envelope_session["active_run_id"] = _text(active_run_id)
    if resolved_program_id is not None:
        envelope_session["program_id"] = resolved_program_id
    if _text(study_id) is not None:
        envelope_session["study_id"] = _text(study_id)
    if _text(quest_id) is not None:
        envelope_session["quest_id"] = _text(quest_id)

    envelope_payload = _copy_mapping(payload or {})
    if runtime_decision is not None:
        envelope_payload.setdefault("runtime_decision", _text(runtime_decision))
    if runtime_reason is not None:
        envelope_payload.setdefault("runtime_reason", _text(runtime_reason))

    correlation: dict[str, Any] = {
        "correlation_id": resolved_correlation_id,
        "checkpoint_id": resolved_checkpoint_id,
        "checkpoint_lineage_id": resolved_lineage_id,
    }
    for key, value in (
        ("action_graph_id", action_graph_id),
        ("node_id", node_id),
        ("gate_id", gate_id),
        ("parent_envelope_id", parent_envelope_id),
        ("parent_session_id", parent_session_id),
    ):
        resolved = _text(value)
        if resolved is not None:
            correlation[key] = resolved

    event_envelope: dict[str, Any] = {
        "version": FAMILY_EVENT_ENVELOPE_VERSION,
        "envelope_id": resolved_envelope_id,
        "event_name": resolved_event_name,
        "event_time": resolved_event_time,
        "target_domain_id": _text(target_domain_id) or TARGET_DOMAIN_ID,
        "producer": {
            "surface_kind": resolved_surface_kind,
            "surface_id": resolved_surface_id,
        },
        "session": envelope_session,
        "correlation": correlation,
        "payload": envelope_payload,
    }
    normalized_audit_refs = _normalize_refs(audit_refs)
    if normalized_audit_refs:
        event_envelope["audit_refs"] = normalized_audit_refs

    normalized_human_gates = [_copy_mapping(gate) for gate in human_gates or () if isinstance(gate, Mapping)]
    if normalized_human_gates:
        first_gate = normalized_human_gates[0]
        gate_hint: dict[str, Any] = {
            "gate_id": _text(first_gate.get("gate_id")),
            "status": _text(first_gate.get("status")) or "requested",
        }
        request_surface = first_gate.get("request_surface")
        if isinstance(request_surface, Mapping):
            gate_hint["review_surface"] = _copy_mapping(request_surface)
        event_envelope["human_gate_hint"] = gate_hint

    checkpoint_state_refs = _normalize_refs(state_refs)
    if not checkpoint_state_refs:
        checkpoint_state_refs.append(
            {
                "role": "status",
                "ref_kind": "repo_path",
                "ref": resolved_surface_id,
                "label": "surface_status",
            }
        )
    restoration_refs = _normalize_refs(restoration_evidence)
    checkpoint_payload: dict[str, Any] = {
        "version": FAMILY_CHECKPOINT_LINEAGE_VERSION,
        "lineage_id": resolved_lineage_id,
        "checkpoint_id": resolved_checkpoint_id,
        "target_domain_id": _text(target_domain_id) or TARGET_DOMAIN_ID,
        "session": {
            "session_id": resolved_session_id,
        },
        "producer": {
            "event_envelope_id": resolved_envelope_id,
        },
        "state_refs": checkpoint_state_refs,
        "resume_contract": {
            "resume_mode": _text(resume_mode) or "resume_from_checkpoint",
            "resume_handle": _text(resume_handle) or f"{resolved_surface_kind}:{resolved_checkpoint_id}",
            "human_gate_required": bool(human_gate_required),
        },
        "integrity": {
            "status": "complete",
            "recorded_at": resolved_event_time,
            "summary": _text(checkpoint_label) or _text(runtime_reason) or "runtime checkpoint captured",
        },
    }
    if active_run_id is not None:
        checkpoint_payload["session"]["active_run_id"] = _text(active_run_id)
    if resolved_program_id is not None:
        checkpoint_payload["session"]["program_id"] = resolved_program_id
    for key, value in (
        ("action_graph_id", action_graph_id),
        ("node_id", node_id),
        ("gate_id", gate_id),
    ):
        resolved = _text(value)
        if resolved is not None:
            checkpoint_payload["producer"][key] = resolved
    parent: dict[str, Any] = {}
    for key, value in (
        ("parent_lineage_id", parent_lineage_id),
        ("parent_checkpoint_id", parent_checkpoint_id),
        ("resume_from_lineage_id", resume_from_lineage_id),
    ):
        resolved = _text(value)
        if resolved is not None:
            parent[key] = resolved
    if parent:
        checkpoint_payload["parent"] = parent
    if restoration_refs:
        checkpoint_payload["restoration_evidence"] = restoration_refs

    return {
        "family_event_envelope": event_envelope,
        "family_checkpoint_lineage": checkpoint_payload,
        "family_human_gates": normalized_human_gates,
    }
