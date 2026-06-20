from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.evidence_gap_decision import (
    classify_evidence_gap,
    classify_missing_ref_family,
    materialize_typed_blocker_if_required,
    merge_gap_decisions,
    normalize_decision,
    summarize_gap_decisions,
)


def attach_evidence_gap_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    decisions = merge_gap_decisions(
        _existing_decisions(updated),
        _decisions_from_gap_inputs(updated),
        _decisions_from_missing_refs(updated),
        _decisions_from_provider_transition(updated),
        _decisions_from_human_gate(updated),
    )
    summary = summarize_gap_decisions(decisions)
    ledgers = _ledger_surfaces(decisions)
    updated["evidence_gap_decisions"] = decisions
    updated["evidence_gap_decision_summary"] = summary
    updated["hard_gate_count"] = summary["hard_gate_count"]
    updated["human_gate_count"] = summary["human_gate_count"]
    updated["soft_gap_count"] = summary["soft_gap_count"]
    updated["observability_backlog_count"] = summary["observability_backlog_count"]
    updated["evidence_tail_count"] = summary["evidence_tail_count"]
    updated["current_action_can_continue"] = summary["current_action_can_continue"]
    updated["forbidden_claims"] = summary["forbidden_claims"]
    updated.update(ledgers)
    blockers = [
        blocker
        for decision in decisions
        if (blocker := materialize_typed_blocker_if_required(decision)) is not None
    ]
    updated["evidence_gap_typed_blockers"] = blockers
    updated["evidence_gap_typed_blocker_count"] = len(blockers)
    return updated


def _existing_decisions(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    for item in payload.get("evidence_gap_decisions") or []:
        if isinstance(item, Mapping):
            decisions.append(normalize_decision(item).to_payload())
    return decisions


def _decisions_from_gap_inputs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    identity = _identity(payload)
    for item in payload.get("evidence_gap_inputs") or []:
        if not isinstance(item, Mapping):
            continue
        decision = classify_evidence_gap(
            surface_kind=_text(item.get("surface_kind")) or "missing_evidence_ref",
            missing_ref_family=_text(item.get("missing_ref_family")),
            identity={**identity, **_mapping(item.get("identity"))},
            evidence_refs=item.get("evidence_refs"),
            diagnostic_refs=item.get("diagnostic_refs"),
            confidence=_text(item.get("confidence")),
        )
        decisions.append(decision.to_payload())
    return decisions


def _decisions_from_missing_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs = payload.get("missing_evidence_refs") or payload.get("missing_evidence_ref_families") or []
    decisions = []
    for item in refs:
        ref_family = _text(item)
        if ref_family is None:
            continue
        decisions.append(
            classify_missing_ref_family(
                ref_family,
                identity=_identity(payload),
                diagnostic_refs=_diagnostic_refs(payload),
            ).to_payload()
        )
    return decisions


def _decisions_from_provider_transition(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    if _int(payload.get("provider_admission_pending_count")) > 0:
        decisions.append(
            classify_evidence_gap(
                surface_kind="opl_provider_admission_authority",
                missing_ref_family="OPL event/outbox/StageRun provider admission currentness readback",
                identity=_identity(payload),
                evidence_refs=_refs_from_candidates(payload.get("provider_admission_candidates")),
                diagnostic_refs=_diagnostic_refs(payload),
                confidence="high",
            ).to_payload()
        )
    if _int(payload.get("transition_request_pending_count")) > 0:
        decisions.append(
            classify_evidence_gap(
                surface_kind="opl_transition_runtime_authorization",
                missing_ref_family="OPL runtime outbox StageRun authorization currentness",
                identity=_identity(payload),
                evidence_refs=_refs_from_candidates(payload.get("transition_request_candidates")),
                diagnostic_refs=_diagnostic_refs(payload),
                confidence="high",
            ).to_payload()
        )
    return decisions


def _decisions_from_human_gate(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    if payload.get("needs_physician_decision") is not True and payload.get("human_gate_required") is not True:
        return []
    return [
        classify_evidence_gap(
            surface_kind="human_decision_gate",
            missing_ref_family="human irreversible submission or physician decision",
            identity=_identity(payload),
            diagnostic_refs=_diagnostic_refs(payload),
            confidence="high",
        ).to_payload()
    ]


def _ledger_surfaces(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    assumptions: list[dict[str, Any]] = []
    soft_gaps: list[dict[str, Any]] = []
    observability_backlog: list[dict[str, Any]] = []
    evidence_tail: list[dict[str, Any]] = []
    for decision in decisions:
        gap_class = _text(decision.get("gap_class"))
        if gap_class == "proceed_with_assumption":
            assumptions.append(_ledger_item(decision, "assumption_ledger"))
        elif gap_class == "soft_quality_gap":
            soft_gaps.append(_ledger_item(decision, "soft_gap_ledger"))
        elif gap_class == "observability_backlog":
            observability_backlog.append(_ledger_item(decision, "observability_backlog"))
        elif gap_class == "evidence_tail":
            evidence_tail.append(_ledger_item(decision, "evidence_tail_ledger"))
    return {
        "assumption_ledger": assumptions,
        "soft_gap_ledger": soft_gaps,
        "observability_backlog": observability_backlog,
        "evidence_tail_ledger": evidence_tail,
    }


def _ledger_item(decision: Mapping[str, Any], ledger_kind: str) -> dict[str, Any]:
    return {
        "surface_kind": ledger_kind,
        "gap_class": _text(decision.get("gap_class")),
        "source_surface_kind": _text(decision.get("source_surface_kind")),
        "missing_ref_family": _text(decision.get("missing_ref_family")),
        "reason": _text(decision.get("reason")),
        "current_action_can_continue": decision.get("current_action_can_continue") is True,
        "allowed_next_actions": list(decision.get("allowed_next_actions") or []),
        "forbidden_claims": list(decision.get("forbidden_claims") or []),
        "identity": dict(_mapping(decision.get("identity"))),
        "evidence_refs": list(decision.get("evidence_refs") or []),
        "diagnostic_refs": list(decision.get("diagnostic_refs") or []),
        "assumption": dict(_mapping(decision.get("assumption"))) or None,
    }


def _identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_action = _mapping(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping(payload.get("current_work_unit"))
    return {
        key: value
        for key, value in {
            "program_id": _text(payload.get("program_id")),
            "study_id": _text(payload.get("study_id")),
            "quest_id": _text(payload.get("quest_id")),
            "active_run_id": _text(payload.get("active_run_id")) or _text(payload.get("current_active_run_id")),
            "stage_id": _text(payload.get("current_stage")) or _text(payload.get("stage_id")),
            "work_unit_id": _text(current_action.get("work_unit_id"))
            or _text(current_action.get("next_work_unit"))
            or _text(current_work_unit.get("work_unit_id")),
            "work_unit_fingerprint": _text(current_action.get("work_unit_fingerprint"))
            or _text(current_action.get("action_fingerprint"))
            or _text(current_work_unit.get("work_unit_fingerprint")),
            "action_id": _text(current_action.get("action_id")),
            "action_type": _text(current_action.get("action_type"))
            or _first_text(current_action.get("allowed_actions")),
        }.items()
        if value is not None
    }


def _refs_from_candidates(value: object) -> list[str]:
    refs: list[str] = []
    for item in value or []:
        if not isinstance(item, Mapping):
            continue
        for key in ("source_ref", "dispatch_ref", "stage_packet_ref", "typed_blocker_ref"):
            if (ref := _text(item.get(key))) is not None:
                refs.append(ref)
        refs.extend(_text_list(item.get("evidence_refs")))
        refs.extend(_text_list(item.get("diagnostic_refs")))
    return sorted(dict.fromkeys(refs))


def _diagnostic_refs(payload: Mapping[str, Any]) -> list[str]:
    refs = _mapping(payload.get("refs"))
    return [
        ref
        for ref in (
            _text(refs.get("latest_path")),
            _text(refs.get("runtime_status_summary_path")),
            _text(refs.get("controller_decision_path")),
        )
        if ref is not None
    ]


def _first_text(value: object) -> str | None:
    for item in value or []:
        if (text := _text(item)) is not None:
            return text
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


__all__ = ["attach_evidence_gap_projection"]
