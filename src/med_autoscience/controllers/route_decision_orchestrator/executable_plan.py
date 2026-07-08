from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ADVERSE_RESULT_ALIGNMENTS = frozenset({"weak", "contradictory", "blocked", "negative"})
ANALYSIS_REQUIRED_REPAIRS = ("evidence_ledger", "manuscript", "review_ledger", "analysis")
EXECUTABLE_ACTIONS = (
    "claim_downgrade",
    "bounded_repair",
    "switch_line",
    "return_to_scout",
    "stop_loss",
    "human_gate",
)
ACTION_CALLABLE_SURFACES = {
    "claim_downgrade": "paper_repair_executor.dispatch_repair_work_unit",
    "bounded_repair": "route_decision_orchestrator:bounded_repair",
    "switch_line": "route_decision_orchestrator:switch_line",
    "return_to_scout": "route_decision_orchestrator:return_to_scout",
    "stop_loss": "route_control_stoploss.materialize_route_control_stoploss_memo",
    "human_gate": "route_decision_orchestrator:human_gate",
}


def build_analysis_direction_decision(
    *,
    route_signals: Mapping[str, Any],
    route_control_decision: str,
    controller_decision_ref: str,
    schema_version: int,
) -> dict[str, Any]:
    result_alignment = _result_alignment(route_signals)
    has_analysis_signal = bool(
        result_alignment
        or _text(route_signals.get("expected_result"))
        or _text(route_signals.get("observed_result"))
        or _text(route_signals.get("actual_result"))
        or _text(route_signals.get("claim_id"))
        or _text_list(route_signals.get("failed_path_refs"))
        or _text_list(route_signals.get("statistical_blockers"))
    )
    if not has_analysis_signal:
        return {}

    action_type = _analysis_action_type(route_control_decision, result_alignment)
    if not action_type:
        return {}

    normalized_alignment = result_alignment or "blocked"
    failed_refs = _failed_path_evidence_refs(route_signals)
    claim_policy = _claim_policy(
        route_signals=route_signals,
        result_alignment=normalized_alignment,
        action_type=action_type,
    )
    analysis_slice_contract = _analysis_slice_contract(
        route_signals=route_signals,
        action_type=action_type,
    )
    executable_owner_tasks = _executable_owner_tasks(
        route_signals=route_signals,
        result_alignment=normalized_alignment,
        action_type=action_type,
        analysis_slice_contract=analysis_slice_contract,
        failed_path_evidence_refs=failed_refs,
        claim_policy=claim_policy,
        controller_decision_ref=controller_decision_ref,
    )
    return {
        "surface": "analysis_direction_decision",
        "schema_version": schema_version,
        "decision": action_type,
        "action_type": action_type,
        "result_alignment": normalized_alignment,
        "claim_id": _text(route_signals.get("claim_id")) or None,
        "expected_result": _text(route_signals.get("expected_result")) or None,
        "observed_result": _text(route_signals.get("observed_result")) or None,
        "analysis_slice_contract": analysis_slice_contract,
        "failed_path_evidence_refs": failed_refs,
        "failure_reasons": _route_failure_reasons(route_signals),
        "statistical_blockers": _text_list(route_signals.get("statistical_blockers")),
        "alternative_routes": _text_list(route_signals.get("alternative_routes")),
        "claim_policy": claim_policy,
        "executable_owner_tasks": executable_owner_tasks,
        "required_repairs": list(ANALYSIS_REQUIRED_REPAIRS),
        "authority_boundary": {
            "controller_decision_role": "executable_owner_task_plan",
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "quality_claim_authorized": False,
        },
        "controller_decision_ref": controller_decision_ref,
    }


def _analysis_slice_contract(
    *,
    route_signals: Mapping[str, Any],
    action_type: str,
) -> dict[str, Any]:
    return {
        "hypothesis": _text(route_signals.get("hypothesis")) or None,
        "endpoint": _text(route_signals.get("endpoint")) or _text(route_signals.get("primary_endpoint")) or None,
        "method": _text(route_signals.get("method")) or _text(route_signals.get("analysis_method")) or None,
        "expected_result": _text(route_signals.get("expected_result")) or None,
        "failure_criteria": _failure_criteria(route_signals),
        "actual_result": _text(route_signals.get("actual_result")) or _text(route_signals.get("observed_result")) or None,
        "interpretation": _text(route_signals.get("interpretation")) or None,
        "route_impact": action_type,
    }


def _failure_criteria(route_signals: Mapping[str, Any]) -> list[str]:
    explicit = _text_list(route_signals.get("failure_criteria"))
    if explicit:
        return explicit
    return _route_failure_reasons(route_signals)


def _executable_owner_tasks(
    *,
    route_signals: Mapping[str, Any],
    result_alignment: str,
    action_type: str,
    analysis_slice_contract: Mapping[str, Any],
    failed_path_evidence_refs: Sequence[str],
    claim_policy: Mapping[str, Any],
    controller_decision_ref: str,
) -> list[dict[str, Any]]:
    if result_alignment not in ADVERSE_RESULT_ALIGNMENTS:
        return []
    source_fingerprint = _source_fingerprint(
        route_signals=route_signals,
        result_alignment=result_alignment,
        failed_path_evidence_refs=failed_path_evidence_refs,
    )
    return [
        _owner_task(
            action=action,
            route_signals=route_signals,
            result_alignment=result_alignment,
            analysis_slice_contract=analysis_slice_contract,
            failed_path_evidence_refs=failed_path_evidence_refs,
            claim_policy=claim_policy,
            controller_decision_ref=controller_decision_ref,
            source_fingerprint=source_fingerprint,
        )
        for action in _dedupe_text(["claim_downgrade", action_type])
        if action in EXECUTABLE_ACTIONS
    ]


def _owner_task(
    *,
    action: str,
    route_signals: Mapping[str, Any],
    result_alignment: str,
    analysis_slice_contract: Mapping[str, Any],
    failed_path_evidence_refs: Sequence[str],
    claim_policy: Mapping[str, Any],
    controller_decision_ref: str,
    source_fingerprint: str,
) -> dict[str, Any]:
    claim_id = _text(claim_policy.get("claim_id")) or _text(route_signals.get("claim_id")) or "unclaimed"
    return {
        "action": action,
        "owner": "MAS Route Decision Controller",
        "callable_surface": ACTION_CALLABLE_SURFACES[action],
        "required_inputs": _required_inputs(
            action=action,
            analysis_slice_contract=analysis_slice_contract,
            failed_path_evidence_refs=failed_path_evidence_refs,
            claim_policy=claim_policy,
            route_signals=route_signals,
        ),
        "required_outputs": _required_outputs(action),
        "artifact_delta_predicate": _artifact_delta_predicate(action),
        "gate_replay_target": controller_decision_ref,
        "idempotency_key": f"analysis_direction_decision:{claim_id}:{result_alignment}:{action}:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
    }


def _required_inputs(
    *,
    action: str,
    analysis_slice_contract: Mapping[str, Any],
    failed_path_evidence_refs: Sequence[str],
    claim_policy: Mapping[str, Any],
    route_signals: Mapping[str, Any],
) -> list[str]:
    inputs = [
        "analysis_slice_contract",
        "failed_path_evidence_refs",
        "claim_policy.supported=false",
    ]
    if action == "bounded_repair":
        inputs.extend(["statistical_blockers", "failure_criteria"])
    elif action == "switch_line":
        inputs.append("alternative_routes")
    elif action == "return_to_scout":
        inputs.append("scout_refresh_reason")
    elif action == "stop_loss":
        inputs.append("exploration_depth_review")
    elif action == "human_gate":
        inputs.append("human_gate_question")
    if not failed_path_evidence_refs:
        inputs.append("failure_reasons")
    if not _text(claim_policy.get("claim_id")):
        inputs.append("claim_scope")
    if not any(analysis_slice_contract.get(key) for key in ("hypothesis", "endpoint", "method")):
        inputs.append("analysis_scope")
    if action == "switch_line" and not _text_list(route_signals.get("alternative_routes")):
        inputs.append("explicit_alternative_line_id")
    return _dedupe_text(inputs)


def _required_outputs(action: str) -> list[str]:
    outputs = {
        "claim_downgrade": [
            "paper/manuscript.md",
            "paper/evidence_ledger.json#claim_status_delta",
            "paper/review/review_ledger.json",
        ],
        "bounded_repair": [
            "artifacts/controller_decisions/latest.json#analysis_direction_decision.executable_owner_tasks",
            "artifacts/medical_paper/bounded_repair_plan.json",
        ],
        "switch_line": [
            "artifacts/controller_decisions/latest.json#route_decision",
            "artifacts/controller_decisions/latest.json#route_target",
        ],
        "return_to_scout": [
            "artifacts/controller_decisions/latest.json#route_decision",
            "artifacts/medical_paper/literature_scout_request.json",
        ],
        "stop_loss": [
            "artifacts/controller_decisions/latest.json#route_decision",
            "artifacts/medical_paper/stop_loss_memo.json",
        ],
        "human_gate": [
            "artifacts/controller_decisions/latest.json#route_decision",
            "artifacts/medical_paper/human_gate_request.json",
        ],
    }
    return list(outputs[action])


def _artifact_delta_predicate(action: str) -> str:
    predicates = {
        "claim_downgrade": "claim_policy.supported is false and original supported claim is not re-emitted",
        "bounded_repair": "bounded repair plan records the failed slice and replay target before analysis resumes",
        "switch_line": "route decision no longer continues the failed path as the active supported claim route",
        "return_to_scout": "route decision sends the failed slice back to scout without publication readiness authority",
        "stop_loss": "stop-loss memo preserves failed path evidence before any new route is selected",
        "human_gate": "human gate request names the failed slice and blocks autonomous claim support",
    }
    return predicates[action]


def _source_fingerprint(
    *,
    route_signals: Mapping[str, Any],
    result_alignment: str,
    failed_path_evidence_refs: Sequence[str],
) -> str:
    claim_id = _text(route_signals.get("claim_id")) or "unclaimed"
    evidence = _dedupe_text(list(failed_path_evidence_refs)) or _route_failure_reasons(route_signals)
    return "|".join([claim_id, result_alignment, *evidence])


def _analysis_action_type(route_control_decision: str, result_alignment: str) -> str:
    if route_control_decision == "route_back":
        return "return_to_scout"
    if route_control_decision in {"bounded_repair", "switch_line", "stop_loss", "human_gate"}:
        return route_control_decision
    if result_alignment in ADVERSE_RESULT_ALIGNMENTS:
        return "claim_downgrade"
    return ""


def _claim_allowed_status(action_type: str) -> str:
    if action_type == "bounded_repair":
        return "pending_bounded_repair"
    if action_type == "return_to_scout":
        return "pending_scout_reassessment"
    if action_type == "human_gate":
        return "pending_human_gate"
    return "downgraded"


def _claim_policy(
    *,
    route_signals: Mapping[str, Any],
    result_alignment: str,
    action_type: str,
) -> dict[str, Any]:
    claim_id = _text(route_signals.get("claim_id")) or None
    previous_status = _text(route_signals.get("claim_status")) or _text(route_signals.get("current_claim_status")) or None
    return {
        "claim_id": claim_id,
        "previous_status": previous_status,
        "supported": False,
        "claim_downgrade_required": True,
        "allowed_status": _claim_allowed_status(action_type),
        "reason": f"{result_alignment}_result_cannot_support_original_claim",
    }


def _failed_path_evidence_refs(route_signals: Mapping[str, Any]) -> list[str]:
    return _dedupe_text(
        [
            *_text_list(route_signals.get("failed_path_refs")),
            *_text_list(route_signals.get("failed_path_evidence_refs")),
            *_text_list(route_signals.get("evidence_refs")),
        ]
    )


def _route_failure_reasons(route_signals: Mapping[str, Any]) -> list[str]:
    reasons = _text_list(route_signals.get("failure_reasons"))
    reasons.extend(f"statistical_blocker:{item}" for item in _text_list(route_signals.get("statistical_blockers")))
    return reasons or ["route_control_signal_requires_decision"]


def _result_alignment(route_signals: Mapping[str, Any]) -> str:
    return _text(route_signals.get("result_alignment")).lower()


def _dedupe_text(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str:
    return str(value or "").strip()
