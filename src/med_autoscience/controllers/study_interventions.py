from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
EVENT_LOG_RELATIVE_PATH = Path("artifacts") / "interventions" / "events.jsonl"
OWNER_GATE_DECISION_INTENT = "owner_gate_decision"
INTERVENTION_INTENTS = frozenset(
    {"user_decision", "new_plan", "abandon", "submit_info", OWNER_GATE_DECISION_INTENT}
)
OWNER_GATE_DECISIONS = frozenset(
    {
        "admit_identity_bound_stage_packet",
        "deny_and_stable_typed_blocker",
        "route_back_to_mas_packet_materialization_bug",
    }
)
STORAGE_POLICY = {"primary_store": "file", "sqlite_role": "index_only"}


def intervention_events_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / EVENT_LOG_RELATIVE_PATH


def read_intervention_events(*, study_root: Path) -> list[dict[str, Any]]:
    path = intervention_events_path(study_root=study_root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if isinstance(payload, Mapping):
            events.append(dict(payload))
    return events


def append_intervention_event(
    *,
    study_root: Path,
    study_id: str,
    intent: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str,
    actor: str = "user",
    source: str = "manual",
    agent_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    intent_text = _text(intent)
    if intent_text not in INTERVENTION_INTENTS:
        raise ValueError(f"unknown study intervention intent: {intent}")
    resolved_payload = dict(payload or {})
    resolved_agent_handoff = _mapping(agent_handoff)
    path = intervention_events_path(study_root=study_root)
    sequence = len(read_intervention_events(study_root=study_root)) + 1
    event = _intervention_event(
        study_id=study_id,
        intent=intent_text,
        payload=resolved_payload,
        recorded_at=recorded_at,
        sequence=sequence,
        actor=actor,
        source=source,
        agent_handoff=resolved_agent_handoff,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def owner_gate_decision_record(
    *,
    study_root: Path,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    blocker_type: str,
    decision: str,
    reason: str,
    recorded_at: str,
    apply: bool,
    actor: str = "operator",
    source: str = "codex",
    stage_packet_refs: list[str] | tuple[str, ...] | None = None,
    route_identity_key: str | None = None,
    attempt_idempotency_key: str | None = None,
    stable_typed_blocker_type: str | None = None,
    route_back_evidence_ref: str | None = None,
) -> dict[str, Any]:
    path = intervention_events_path(study_root=study_root)
    sequence = len(read_intervention_events(study_root=study_root)) + 1
    payload = _owner_gate_payload(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        blocker_type=blocker_type,
        decision=decision,
        reason=reason,
        recorded_at=recorded_at,
        stage_packet_refs=stage_packet_refs,
        route_identity_key=route_identity_key,
        attempt_idempotency_key=attempt_idempotency_key,
        stable_typed_blocker_type=stable_typed_blocker_type,
        route_back_evidence_ref=route_back_evidence_ref,
    )
    event = {
        **_intervention_event(
            study_id=study_id,
            intent=OWNER_GATE_DECISION_INTENT,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
            actor=actor,
            source=source,
            agent_handoff=None,
        ),
        "payload": payload,
    }
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    truth_event_input = build_truth_event_input(event)
    return {
        "surface": "study_owner_gate_decision_record",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "record_status": "applied" if apply else "dry_run",
        "dry_run": not apply,
        "event": event,
        "human_gate_ref": payload["human_gate_ref"],
        "owner_gate_decision_ref": payload["owner_gate_decision_ref"],
        "accepted_answer_shape": {"human_gate_ref": payload["human_gate_ref"]},
        "truth_event_input": truth_event_input,
        "refs": {
            "intervention_events_path": str(path),
            "human_gate_ref": payload["human_gate_ref"],
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "runtime_artifact_mutation_allowed": False,
    }


def build_truth_event_input(event: Mapping[str, Any]) -> dict[str, Any]:
    intent = _required_text(event.get("intent"), field="intent")
    if intent not in INTERVENTION_INTENTS:
        raise ValueError(f"unknown study intervention intent: {intent}")
    event_id = _required_text(event.get("event_id"), field="event_id")
    study_id = _required_text(event.get("study_id"), field="study_id")
    payload = _mapping(event.get("payload"))
    truth_payload = {
        "intervention_event_id": event_id,
        "intervention_intent": intent,
        "actor": _text(event.get("actor")) or "user",
        "source": _text(event.get("source")) or "manual",
        **payload,
    }
    agent_handoff = _mapping(event.get("agent_handoff"))
    if agent_handoff:
        truth_payload["agent_handoff"] = agent_handoff
    if intent == "abandon" and _text(truth_payload.get("current_required_action")) is None:
        truth_payload["current_required_action"] = "abandon_study_line"
    return {
        "study_id": study_id,
        "event_type": "task_intake" if intent == "new_plan" else "human_gate",
        "payload": truth_payload,
        "recorded_at": _required_text(event.get("recorded_at"), field="recorded_at"),
        "source_signature": f"intervention::{event_id}",
    }


def _intervention_event(
    *,
    study_id: str,
    intent: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
    actor: str,
    source: str,
    agent_handoff: Mapping[str, Any] | None,
) -> dict[str, Any]:
    event = {
        "schema_version": SCHEMA_VERSION,
        "surface": "study_intervention_event",
        "event_id": _event_id(
            study_id=study_id,
            intent=intent,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "intent": intent,
        "actor": _text(actor) or "user",
        "source": _text(source) or "manual",
        "recorded_at": recorded_at,
        "payload": dict(payload),
        "storage_policy": dict(STORAGE_POLICY),
    }
    resolved_agent_handoff = _mapping(agent_handoff)
    if resolved_agent_handoff:
        event["agent_handoff"] = resolved_agent_handoff
    return event


def _owner_gate_payload(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    blocker_type: str,
    decision: str,
    reason: str,
    recorded_at: str,
    stage_packet_refs: list[str] | tuple[str, ...] | None,
    route_identity_key: str | None,
    attempt_idempotency_key: str | None,
    stable_typed_blocker_type: str | None,
    route_back_evidence_ref: str | None,
) -> dict[str, Any]:
    identity = {
        "study_id": _required_text(study_id, field="study_id"),
        "action_type": _required_text(action_type, field="action_type"),
        "work_unit_id": _required_text(work_unit_id, field="work_unit_id"),
        "work_unit_fingerprint": _required_text(work_unit_fingerprint, field="work_unit_fingerprint"),
        "blocker_type": _required_text(blocker_type, field="blocker_type"),
    }
    decision_text = _required_text(decision, field="decision")
    if decision_text not in OWNER_GATE_DECISIONS:
        raise ValueError(f"unknown owner gate decision: {decision}")
    reason_text = _required_text(reason, field="reason")
    refs = [_required_text(ref, field="stage_packet_ref") for ref in (stage_packet_refs or ()) if _text(ref)]
    if decision_text == "admit_identity_bound_stage_packet":
        if not refs:
            raise ValueError("admit_identity_bound_stage_packet requires stage_packet_refs")
        _required_text(route_identity_key, field="route_identity_key")
        _required_text(attempt_idempotency_key, field="attempt_idempotency_key")
    if decision_text == "deny_and_stable_typed_blocker":
        _required_text(stable_typed_blocker_type, field="stable_typed_blocker_type")
    decision_ref = _owner_gate_decision_ref(
        identity=identity,
        decision=decision_text,
        reason=reason_text,
        recorded_at=recorded_at,
    )
    payload: dict[str, Any] = {
        "summary": reason_text,
        "owner_gate_kind": "opl_owner_gate",
        "decision": decision_text,
        "reason": reason_text,
        "current_required_action": "resolve_opl_owner_gate",
        "current_owner_identity": identity,
        "owner_gate_decision_ref": decision_ref,
        "human_gate_ref": f"human_gate:{decision_ref}",
        "accepted_answer_shapes": ["human_gate_ref"],
        "provider_admission_allowed": decision_text == "admit_identity_bound_stage_packet",
        "do_not_redrive_same_work_unit": True,
        "paper_package_mutation_allowed": False,
        "runtime_artifact_mutation_allowed": False,
    }
    if refs:
        payload["stage_packet_refs"] = refs
        payload["stage_packet_ref"] = refs[0]
        payload["accepted_answer_shapes"].append("identity_bound_stage_packet_ref")
    if route_identity_key_text := _text(route_identity_key):
        payload["route_identity_key"] = route_identity_key_text
    if attempt_idempotency_key_text := _text(attempt_idempotency_key):
        payload["attempt_idempotency_key"] = attempt_idempotency_key_text
    if blocker_text := _text(stable_typed_blocker_type):
        payload["stable_typed_blocker_type"] = blocker_text
        payload["stable_typed_blocker_ref"] = f"stable_typed_blocker:{decision_ref}"
        payload["accepted_answer_shapes"].append("stable_typed_blocker_ref")
    if route_back_ref_text := _text(route_back_evidence_ref):
        payload["route_back_evidence_ref"] = route_back_ref_text
    if decision_text == "route_back_to_mas_packet_materialization_bug" and "route_back_evidence_ref" not in payload:
        payload["route_back_evidence_ref"] = f"route_back:{decision_ref}"
    if "route_back_evidence_ref" in payload:
        payload["accepted_answer_shapes"].append("route_back_evidence_ref")
    return payload


def _owner_gate_decision_ref(
    *,
    identity: Mapping[str, Any],
    decision: str,
    reason: str,
    recorded_at: str,
) -> str:
    encoded = json.dumps(
        {
            "identity": dict(identity),
            "decision": decision,
            "reason": reason,
            "recorded_at": recorded_at,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"owner-gate-decision:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:24]}"


def _event_id(
    *,
    study_id: str,
    intent: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    encoded = json.dumps(
        {
            "study_id": study_id,
            "intent": intent,
            "payload": dict(payload),
            "recorded_at": recorded_at,
            "sequence": sequence,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"intervention-event-{sequence:06d}-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_text(value: object, *, field: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"study intervention event requires {field}")
    return text


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
