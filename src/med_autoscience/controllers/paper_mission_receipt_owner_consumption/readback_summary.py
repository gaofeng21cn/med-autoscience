from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption.common import (
    _first_text,
    _mapping,
    _read_json_object,
    _text,
    _text_list,
)
from med_autoscience.paper_mission_opl_readback.receipt_events import (
    matches_receipt_bundle,
)

def _stage_closure_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    decision = _effective_stage_closure_decision(readback)
    outcome = _mapping(decision.get("outcome"))
    guard = _mapping(readback.get("durable_mission_stop_guard"))
    opl_closeout = _mapping(decision.get("opl_closeout"))
    carrier = _carrier(readback)
    carrier_terminal_closeout = _mapping(carrier.get("terminal_closeout"))
    carrier_receipt_evidence = _mapping(carrier.get("receipt_evidence"))
    carrier_consumption = _mapping(carrier.get("mas_receipt_consumption"))
    carrier_supersedes_decision = _carrier_route_back_closeout_supersedes_stage_closure_decision(
        carrier_terminal_closeout=carrier_terminal_closeout,
        carrier_consumption=carrier_consumption,
        decision_opl_closeout=opl_closeout,
        decision_source_ref=_first_currentness_ref(
            decision.get("decision_ref"),
            readback.get("stage_closure_decision_ref"),
            decision.get("source_ref"),
            _mapping(decision.get("inputs")).get("source_ref"),
        ),
        carrier_receipt_evidence=carrier_receipt_evidence,
        carrier_receipt=_mapping(carrier.get("opl_transition_receipt")),
    )
    if carrier_supersedes_decision:
        opl_closeout = carrier_terminal_closeout
    domain_transition = _mapping(readback.get("domain_transition"))
    domain_next_action = _mapping(domain_transition.get("next_action"))
    domain_next_work_unit = _mapping(domain_transition.get("next_work_unit"))
    prefers_domain_successor = (
        _text(outcome.get("transition_kind")) == "route_back_candidate_checkpoint"
        and (
            _first_text(
                domain_next_action.get("stage_id"),
                domain_transition.get("route_target"),
            )
            is not None
            or _first_text(
                domain_next_action.get("work_unit_id"),
                domain_next_work_unit.get("unit_id"),
            )
            is not None
        )
    )
    stage_attempt_id = _first_text(opl_closeout.get("stage_attempt_id"))
    derived_stage_attempt_ref = (
        f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None
    )
    derived_checkpoint_ref = _first_text(
        carrier_receipt_evidence.get("route_checkpoint_evidence_ref")
        if carrier_supersedes_decision
        else None,
        carrier_receipt_evidence.get("runtime_closeout_ref")
        if carrier_supersedes_decision
        else None,
        carrier_terminal_closeout.get("closeout_ref")
        if carrier_supersedes_decision
        else None,
        _route_checkpoint_evidence_ref_from_opl_closeout(
            readback=readback,
            stage_attempt_id=stage_attempt_id,
        ),
    )
    return {
        "stage_id": _first_text(
            domain_next_action.get("stage_id") if prefers_domain_successor else None,
            domain_transition.get("route_target") if prefers_domain_successor else None,
            decision.get("stage_id"),
            outcome.get("stage_id"),
            domain_next_action.get("stage_id"),
            domain_transition.get("route_target"),
        ),
        "work_unit_id": _first_text(
            domain_next_action.get("work_unit_id") if prefers_domain_successor else None,
            domain_next_work_unit.get("unit_id") if prefers_domain_successor else None,
            decision.get("work_unit_id"),
            outcome.get("work_unit_id"),
            domain_next_action.get("work_unit_id"),
            domain_next_work_unit.get("unit_id"),
        ),
        "outcome_kind": _text(outcome.get("kind")) or _text(readback.get("stage_closure_outcome")),
        "transition_kind": _text(outcome.get("transition_kind")) or None,
        "next_legal_action": _first_text(outcome.get("next_legal_action"), decision.get("next_legal_action")),
        "decision_ref": _first_text(decision.get("decision_ref"), readback.get("stage_closure_decision_ref")),
        "durable_stop_allowed": guard.get("durable_stop_allowed") is True,
        "opl_closeout": opl_closeout,
        "receipt_evidence_ref": _first_text(
            derived_stage_attempt_ref if carrier_supersedes_decision else None,
            decision.get("receipt_evidence_ref"),
            outcome.get("receipt_evidence_ref"),
            derived_stage_attempt_ref,
        ),
        "route_checkpoint_evidence_ref": _first_text(
            derived_checkpoint_ref if carrier_supersedes_decision else None,
            decision.get("route_checkpoint_evidence_ref"),
            outcome.get("route_checkpoint_evidence_ref"),
            derived_checkpoint_ref,
        ),
    }


def _carrier_route_back_closeout_supersedes_stage_closure_decision(
    *,
    carrier_terminal_closeout: Mapping[str, Any],
    carrier_consumption: Mapping[str, Any],
    decision_opl_closeout: Mapping[str, Any],
    decision_source_ref: str | None,
    carrier_receipt_evidence: Mapping[str, Any],
    carrier_receipt: Mapping[str, Any],
) -> bool:
    if _text(carrier_consumption.get("status")) != "requires_mas_owner_consumption":
        return False
    if not carrier_terminal_closeout:
        return False
    carrier_attempt_id = _first_text(carrier_terminal_closeout.get("stage_attempt_id"))
    if carrier_attempt_id is None:
        return False
    decision_attempt_id = _first_text(decision_opl_closeout.get("stage_attempt_id"))
    if decision_attempt_id == carrier_attempt_id:
        return False
    carrier_closeout_ref = _first_text(
        carrier_receipt_evidence.get("runtime_closeout_ref"),
        carrier_receipt_evidence.get("route_checkpoint_evidence_ref"),
        carrier_terminal_closeout.get("closeout_ref"),
    )
    if decision_attempt_id is not None and _ref_newer(
        candidate=decision_source_ref,
        current=carrier_closeout_ref,
    ):
        return False
    return _first_text(
        carrier_receipt_evidence.get("route_back_evidence_ref"),
        carrier_receipt.get("route_back_evidence_ref"),
        carrier_consumption.get("route_back_evidence_ref"),
    ) is not None


def _route_checkpoint_evidence_ref_from_opl_closeout(
    *,
    readback: Mapping[str, Any],
    stage_attempt_id: str | None,
) -> str | None:
    if stage_attempt_id is None:
        return None
    next_action = _mapping(readback.get("next_action"))
    if _text(next_action.get("action_family")) != "paper.stage_closure.owner_consumption":
        return None
    if _first_text(next_action.get("outcome_ref")) is None:
        return None
    study_root = _first_text(readback.get("study_root"))
    study_id = _first_text(readback.get("study_id"))
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        workspace_root = root.parent.parent if root.parent.name == "studies" else root
        relative_candidates = [
            Path("ops")
            / "medautoscience"
            / "paper_mission_stage_attempts"
            / stage_attempt_id
            / "stage_attempt_closeout_packet.json",
        ]
        if study_id is not None:
            relative_candidates.append(
                Path("ops")
                / "medautoscience"
                / "paper_mission_stage_attempts"
                / stage_attempt_id
                / study_id
                / "stage_attempt_closeout_packet.json"
            )
        for relative in relative_candidates:
            if (workspace_root / relative).exists():
                return relative.as_posix()
    return (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"{stage_attempt_id}/stage_attempt_closeout_packet.json"
    )


def _effective_stage_closure_decision(readback: Mapping[str, Any], *, synthesize: bool = True) -> dict[str, Any]:
    next_action_decision = _next_action_stage_closure_decision(readback, synthesize=synthesize)
    if next_action_decision:
        return next_action_decision
    decision = _mapping(readback.get("stage_closure_decision"))
    decision_outcome = _mapping(decision.get("outcome"))
    if (
        decision_outcome.get("kind") == "next_stage_transition"
        and decision_outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    ):
        return decision
    if synthesize:
        carrier_decision = _synthesized_next_action_stage_closure_decision(readback)
        if carrier_decision:
            return carrier_decision
    return decision


def _next_action_stage_closure_decision(readback: Mapping[str, Any], *, synthesize: bool = True) -> dict[str, Any]:
    next_action = _mapping(readback.get("next_action"))
    if _text(next_action.get("action_family")) != "paper.stage_closure.owner_consumption":
        return {}
    outcome_ref = _first_text(next_action.get("outcome_ref"))
    if outcome_ref is not None:
        payload = _read_json_object(Path(outcome_ref))
        if _text(payload.get("surface_kind")) != "mas_stage_closure_decision":
            return {}
        if _text(payload.get("study_id")) != _text(readback.get("study_id")):
            return {}
        outcome = _mapping(payload.get("outcome"))
        if (
            _text(outcome.get("kind")) == "next_stage_transition"
            and _text(outcome.get("transition_kind"))
            == "route_back_candidate_checkpoint"
        ):
            return payload
    if not synthesize:
        return {}
    return _synthesized_next_action_stage_closure_decision(readback)


def _synthesized_next_action_stage_closure_decision(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier = _carrier(readback)
    next_action = _mapping(readback.get("next_action"))
    terminal_closeout = _mapping(carrier.get("terminal_closeout"))
    receipt = _mapping(carrier.get("opl_transition_receipt"))
    evidence = _mapping(carrier.get("receipt_evidence"))
    consumption = _mapping(carrier.get("mas_receipt_consumption"))
    if _text(consumption.get("next_legal_action")) != (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    ):
        return {}
    route_checkpoint_ref = _first_text(
        terminal_closeout.get("closeout_ref"),
        evidence.get("runtime_closeout_ref"),
        receipt.get("runtime_closeout_ref"),
    )
    if route_checkpoint_ref is None:
        return {}
    domain_transition = _mapping(readback.get("domain_transition"))
    domain_next_action = _mapping(domain_transition.get("next_action"))
    domain_next_work_unit = _mapping(domain_transition.get("next_work_unit"))
    work_unit_id = _first_text(
        next_action.get("work_unit_id"),
        domain_next_action.get("work_unit_id"),
        domain_next_work_unit.get("unit_id"),
        terminal_closeout.get("work_unit_id"),
    )
    stage_id = _first_text(
        next_action.get("stage_id"),
        domain_next_action.get("stage_id"),
        domain_transition.get("route_target"),
        terminal_closeout.get("stage_id"),
    )
    stage_attempt_id = _first_text(
        terminal_closeout.get("stage_attempt_id"),
        receipt.get("stage_attempt_id"),
    )
    return {
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "study_id": _text(readback.get("study_id")) or None,
        "stage_id": stage_id,
        "work_unit_id": work_unit_id,
        "receipt_evidence_ref": _first_text(
            evidence.get("receipt_ref"),
            receipt.get("stage_attempt_ref"),
        ),
        "route_checkpoint_evidence_ref": route_checkpoint_ref,
        "opl_closeout": {
            "status": "opl_runtime_terminal_readback_observed",
            "stage_attempt_id": stage_attempt_id,
            "work_unit_id": work_unit_id,
        },
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            "route_checkpoint_evidence_ref": route_checkpoint_ref,
        },
    }


def _current_package_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    package = _mapping(readback.get("current_package"))
    return {
        "status": _first_text(package.get("status"), package.get("freshness")),
        "package_kind": _text(package.get("package_kind")) or None,
        "can_submit": package.get("can_submit") is True,
        "quality_gate_status": _first_text(package.get("quality_gate_status"), package.get("gate_status")),
        "known_blockers": _text_list(package.get("known_blockers")),
        "root": _text(package.get("root")) or None,
        "zip_path": _text(package.get("zip_path")) or None,
        "zip_exists": package.get("zip_exists") is True,
    }


def _receipt_summary(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": _text(receipt.get("surface_kind")) or None,
        "receipt_status": _text(receipt.get("receipt_status")) or None,
        "role": _text(receipt.get("role")) or None,
        "task_id": _text(receipt.get("task_id")) or None,
        "task_status": _text(receipt.get("task_status")) or None,
        "stage_attempt_id": _text(receipt.get("stage_attempt_id")) or None,
        "stage_attempt_ref": _text(receipt.get("stage_attempt_ref")) or None,
        "closeout_receipt_status": _text(receipt.get("closeout_receipt_status")) or None,
        "blocked_reason": _text(receipt.get("blocked_reason")) or None,
        "can_claim_paper_progress": receipt.get("can_claim_paper_progress") is True,
    }


def _ref_newer(*, candidate: str | None, current: str | None) -> bool:
    candidate_mtime = _ref_mtime(candidate)
    current_mtime = _ref_mtime(current)
    if candidate_mtime is None:
        return False
    if current_mtime is None:
        return True
    return candidate_mtime > current_mtime


def _first_currentness_ref(*values: object) -> str | None:
    texts = [_first_text(value) for value in values]
    for text in texts:
        if _ref_mtime(text) is not None:
            return text
    return next((text for text in texts if text is not None), None)


def _ref_mtime(ref: str | None) -> float | None:
    text = _first_text(ref)
    if text is None or text.startswith(("opl://", "temporal://")):
        return None
    try:
        return Path(text).expanduser().stat().st_mtime
    except OSError:
        return None


def _carrier(readback: Mapping[str, Any]) -> Mapping[str, Any]:
    request_carrier = _request_carrier(readback)
    current_carrier = dict(_mapping(readback.get("current_opl_runtime_carrier_readback")))
    terminal_carrier = dict(_mapping(readback.get("opl_runtime_carrier_readback")))
    carrier = current_carrier
    if _terminal_carrier_matches_stage_closure_decision(
        readback=readback,
        current_carrier=current_carrier,
        terminal_carrier=terminal_carrier,
    ):
        carrier = terminal_carrier
    if _terminal_carrier_requires_consumption_after_current_consumed(
        current_carrier=current_carrier,
        terminal_carrier=terminal_carrier,
        request_carrier=request_carrier,
    ):
        carrier = terminal_carrier
    if _terminal_carrier_is_newer_consumable_than_current(
        current_carrier=current_carrier,
        terminal_carrier=terminal_carrier,
        request_carrier=request_carrier,
    ):
        carrier = terminal_carrier
    if not _has_consumable_receipt(
        carrier,
        request_carrier=request_carrier,
    ) and _has_consumable_receipt(
        terminal_carrier,
        request_carrier=request_carrier,
    ):
        carrier = terminal_carrier
    if not carrier:
        carrier = terminal_carrier
    for key in ("opl_transition_receipt", "receipt_evidence", "mas_receipt_consumption"):
        if not _mapping(carrier.get(key)):
            value = _mapping(readback.get(key))
            if value:
                carrier[key] = value
    return carrier


def _terminal_carrier_matches_stage_closure_decision(
    *,
    readback: Mapping[str, Any],
    current_carrier: Mapping[str, Any],
    terminal_carrier: Mapping[str, Any],
) -> bool:
    request_carrier = _request_carrier(readback)
    if not (
        _has_consumable_receipt(current_carrier, request_carrier=request_carrier)
        and _has_consumable_receipt(terminal_carrier, request_carrier=request_carrier)
    ):
        return False
    if _consumption_status(current_carrier) not in {
        "owner_consumed_route_checkpoint",
        "owner_consumed_typed_blocker",
        "owner_consumption_applied",
    }:
        return False
    if _consumption_status(terminal_carrier) != "requires_mas_owner_consumption":
        return False
    decision_attempt_id = _first_text(
        _mapping(_mapping(readback.get("stage_closure_decision")).get("opl_closeout")).get(
            "stage_attempt_id"
        )
    )
    if decision_attempt_id is None:
        return False
    return decision_attempt_id == _carrier_stage_attempt_id(terminal_carrier)


def _terminal_carrier_requires_consumption_after_current_consumed(
    *,
    current_carrier: Mapping[str, Any],
    terminal_carrier: Mapping[str, Any],
    request_carrier: Mapping[str, Any],
) -> bool:
    current_ref = _carrier_closeout_ref(current_carrier)
    terminal_ref = _carrier_closeout_ref(terminal_carrier)
    if _ref_newer(candidate=current_ref, current=terminal_ref):
        return False
    return (
        _has_consumable_receipt(current_carrier, request_carrier=request_carrier)
        and _has_consumable_receipt(terminal_carrier, request_carrier=request_carrier)
        and _consumption_status(current_carrier)
        in {
            "owner_consumed_route_checkpoint",
            "owner_consumed_typed_blocker",
            "owner_consumption_applied",
        }
        and _consumption_status(terminal_carrier) == "requires_mas_owner_consumption"
    )


def _terminal_carrier_is_newer_consumable_than_current(
    *,
    current_carrier: Mapping[str, Any],
    terminal_carrier: Mapping[str, Any],
    request_carrier: Mapping[str, Any],
) -> bool:
    if not (
        _has_consumable_receipt(current_carrier, request_carrier=request_carrier)
        and _has_consumable_receipt(terminal_carrier, request_carrier=request_carrier)
    ):
        return False
    if _consumption_status(current_carrier) != "requires_mas_owner_consumption":
        return False
    if _consumption_status(terminal_carrier) != "requires_mas_owner_consumption":
        return False
    current_attempt_id = _carrier_stage_attempt_id(current_carrier)
    terminal_attempt_id = _carrier_stage_attempt_id(terminal_carrier)
    if current_attempt_id is None or terminal_attempt_id is None:
        return False
    if current_attempt_id == terminal_attempt_id:
        return False
    return _ref_newer(
        candidate=_carrier_closeout_ref(terminal_carrier),
        current=_carrier_closeout_ref(current_carrier),
    )


def _carrier_stage_attempt_id(carrier: Mapping[str, Any]) -> str | None:
    return _first_text(
        _mapping(carrier.get("terminal_closeout")).get("stage_attempt_id"),
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_id"),
        _mapping(carrier.get("receipt_evidence")).get("stage_attempt_id"),
    )


def _carrier_closeout_ref(carrier: Mapping[str, Any]) -> str | None:
    receipt = _mapping(carrier.get("opl_transition_receipt"))
    evidence = _mapping(carrier.get("receipt_evidence"))
    closeout = _mapping(carrier.get("terminal_closeout"))
    return _first_currentness_ref(
        evidence.get("runtime_closeout_ref"),
        evidence.get("route_checkpoint_evidence_ref"),
        receipt.get("runtime_closeout_ref"),
        receipt.get("runtime_closeout_readback_ref"),
        closeout.get("closeout_ref"),
    )


def _consumption_status(carrier: Mapping[str, Any]) -> str:
    return _text(_mapping(carrier.get("mas_receipt_consumption")).get("status"))


def _request_carrier(readback: Mapping[str, Any]) -> Mapping[str, Any]:
    for candidate in (
        _mapping(readback.get("opl_runtime_carrier")),
        _mapping(_mapping(readback.get("artifact_first_mission_summary")).get("opl_runtime_carrier")),
        _mapping(_mapping(readback.get("opl_route_handoff")).get("opl_runtime_carrier")),
    ):
        if candidate:
            return candidate
    return {}


def _has_consumable_receipt(
    carrier: Mapping[str, Any],
    *,
    request_carrier: Mapping[str, Any],
) -> bool:
    return matches_receipt_bundle(
        receipt=_mapping(carrier.get("opl_transition_receipt")),
        evidence=_mapping(carrier.get("receipt_evidence")),
        consumption=_mapping(carrier.get("mas_receipt_consumption")),
        carrier=request_carrier,
    )
