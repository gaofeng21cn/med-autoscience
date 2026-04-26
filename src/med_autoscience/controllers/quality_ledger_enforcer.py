from __future__ import annotations

from typing import Any, Mapping


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _explicit_repair_available(publication_eval_payload: Mapping[str, Any]) -> bool:
    for action in _list(publication_eval_payload.get("recommended_actions")):
        if not isinstance(action, Mapping):
            continue
        action_type = _text(action.get("action_type"))
        if action_type in {"bounded_analysis", "return_to_analysis_campaign", "return_to_write", "return_to_finalize"}:
            return True
        if _mapping(action.get("next_work_unit")) or _list(action.get("blocking_work_units")):
            return True
    return False


def _publication_eval_has_must_fix_gap(publication_eval_payload: Mapping[str, Any]) -> bool:
    for gap in _list(publication_eval_payload.get("gaps")):
        if not isinstance(gap, Mapping):
            continue
        if _text(gap.get("severity")) in {"must_fix", "blocking", "critical"}:
            return True
    verdict = _mapping(publication_eval_payload.get("verdict"))
    return _text(verdict.get("overall_verdict")) in {"blocked", "not_ready"}


def _ledger_closure_blocker(*, ledger_payload: Mapping[str, Any], blocker_id: str) -> bool:
    if _text(ledger_payload.get("status")) not in {None, "closed"}:
        return True
    for item in _list(ledger_payload.get("charter_expectation_closures")):
        if not isinstance(item, Mapping):
            continue
        if _text(item.get("status")) != "closed":
            return True
    return False


def _reporting_guideline_gate_open(reporting_guideline_gate_payload: Mapping[str, Any]) -> bool:
    gates = _mapping(reporting_guideline_gate_payload.get("gates"))
    for gate in gates.values():
        if not isinstance(gate, Mapping):
            continue
        status = _text(gate.get("status"))
        if status is not None and status != "closed":
            return True
    return False


def build_quality_gate_ledger_enforcement(
    *,
    evidence_ledger_payload: Mapping[str, Any],
    review_ledger_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    reporting_guideline_gate_payload: Mapping[str, Any],
) -> dict[str, Any]:
    hard_blockers: list[str] = []
    repairable_blockers: list[str] = []
    explicit_repair_available = _explicit_repair_available(publication_eval_payload)

    def add_blocker(blocker_id: str, *, repairable: bool) -> None:
        if repairable:
            _append_unique(repairable_blockers, blocker_id)
        else:
            _append_unique(hard_blockers, blocker_id)

    if bool(reporting_guideline_gate_payload.get("gate_relaxation_allowed")):
        add_blocker("reporting_guideline_gate_relaxation_requested", repairable=False)
    if _reporting_guideline_gate_open(reporting_guideline_gate_payload):
        add_blocker("reporting_guideline_gate_not_closed", repairable=False)
    if _ledger_closure_blocker(
        ledger_payload=evidence_ledger_payload,
        blocker_id="evidence_ledger_charter_expectation_not_closed",
    ):
        add_blocker(
            "evidence_ledger_charter_expectation_not_closed",
            repairable=explicit_repair_available,
        )
    if _ledger_closure_blocker(
        ledger_payload=review_ledger_payload,
        blocker_id="review_ledger_charter_expectation_not_closed",
    ):
        add_blocker(
            "review_ledger_charter_expectation_not_closed",
            repairable=explicit_repair_available,
        )
    if _publication_eval_has_must_fix_gap(publication_eval_payload):
        add_blocker("publication_eval_must_fix_gap", repairable=explicit_repair_available)

    if hard_blockers:
        fast_lane_execution_state = "blocked"
        fast_lane_execution_allowed = False
    elif repairable_blockers:
        fast_lane_execution_state = "repairable"
        fast_lane_execution_allowed = True
    else:
        fast_lane_execution_state = "ready"
        fast_lane_execution_allowed = True
    return {
        "surface": "quality_gate_ledger_enforcement",
        "schema_version": 1,
        "fast_lane_execution_allowed": fast_lane_execution_allowed,
        "fast_lane_execution_state": fast_lane_execution_state,
        "gate_relaxation_allowed": False,
        "hard_blockers": hard_blockers,
        "repairable_blockers": repairable_blockers,
        "required_authority_surfaces": [
            "study_charter",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "artifacts/publication_eval/latest.json",
            "reporting_guideline_checklist.json",
        ],
    }
