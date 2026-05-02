from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies import DEFAULT_PUBLICATION_CRITIQUE_POLICY
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    stable_publication_eval_latest_path,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from med_autoscience.study_decision_record import StudyDecisionType


__all__ = ["build_reviewer_refinement_loop_read_model"]


_SURFACE = "reviewer_refinement_loop"
_SCHEMA_VERSION = 1
_POLICY_ID = DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]
_ACCEPTABLE_VERDICTS = frozenset({"promising"})
_ACCEPTABLE_PRIMARY_CLAIM_STATUSES = frozenset({"supported"})
_BLOCKING_GAP_SEVERITIES = frozenset({"must_fix", "important"})


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _ai_reviewer_authority_blockers(publication_eval: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if not provenance:
        return ["publication_eval_ai_reviewer_provenance_missing"]
    if _text(provenance.get("owner")) != "ai_reviewer":
        blockers.append("publication_eval_not_ai_reviewer_backed")
    if provenance.get("ai_reviewer_required") is not False:
        blockers.append("publication_eval_still_requires_ai_reviewer")
    if _text(provenance.get("policy_id")) != _POLICY_ID:
        blockers.append("publication_eval_policy_not_ai_reviewer_critique")
    blockers.extend(
        f"publication_eval_reviewer_operating_system_invalid:{error}"
        for error in validate_ai_reviewer_operating_system_trace(
            publication_eval.get("reviewer_operating_system")
        )
    )
    return blockers


def _blocking_gap_summaries(publication_eval: Mapping[str, Any]) -> list[str]:
    summaries: list[str] = []
    for gap in _list_of_mappings(publication_eval.get("gaps")):
        severity = _text(gap.get("severity"))
        if severity not in _BLOCKING_GAP_SEVERITIES:
            continue
        summary = _text(gap.get("summary"))
        summaries.append(summary or _text(gap.get("gap_id")) or severity)
    return summaries


def _accept_blockers(publication_eval: Mapping[str, Any], authority_blockers: list[str]) -> list[str]:
    blockers = list(authority_blockers)
    verdict = _mapping(publication_eval.get("verdict"))
    overall_verdict = _text(verdict.get("overall_verdict"))
    primary_claim_status = _text(verdict.get("primary_claim_status"))
    if overall_verdict not in _ACCEPTABLE_VERDICTS:
        blockers.append("publication_eval_overall_verdict_not_acceptable")
    if primary_claim_status not in _ACCEPTABLE_PRIMARY_CLAIM_STATUSES:
        blockers.append("publication_eval_primary_claim_not_supported")
    blocking_gaps = _blocking_gap_summaries(publication_eval)
    if blocking_gaps:
        blockers.append("publication_eval_has_blocking_gaps")
    return blockers


def _first_same_line_route_back(publication_eval: Mapping[str, Any]) -> dict[str, Any] | None:
    for action in _list_of_mappings(publication_eval.get("recommended_actions")):
        if _text(action.get("action_type")) != StudyDecisionType.ROUTE_BACK_SAME_LINE.value:
            continue
        return {
            "action_id": _text(action.get("action_id")) or None,
            "action_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
            "priority": _text(action.get("priority")) or "now",
            "route_target": _text(action.get("route_target")) or "review",
            "route_key_question": _text(action.get("route_key_question")) or None,
            "route_rationale": _text(action.get("route_rationale"))
            or _text(action.get("reason"))
            or "AI reviewer requested same-line refinement before package-facing advance.",
            "requires_controller_decision": action.get("requires_controller_decision") is True,
        }
    return None


def _quality_worklog(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    worklog: list[dict[str, Any]] = []
    for dimension, payload in quality_assessment.items():
        item = _mapping(payload)
        status = _text(item.get("status"))
        if not status or status == "ready":
            continue
        worklog.append(
            {
                "kind": "quality_dimension",
                "dimension": dimension,
                "status": status,
                "summary": _text(item.get("summary")),
                "reviewer_revision_advice": _text(item.get("reviewer_revision_advice")) or None,
                "reviewer_next_round_focus": _text(item.get("reviewer_next_round_focus")) or None,
                "evidence_refs": [
                    _text(ref)
                    for ref in item.get("evidence_refs", [])
                    if _text(ref)
                ],
            }
        )
    return worklog


def _gap_worklog(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    worklog: list[dict[str, Any]] = []
    for gap in _list_of_mappings(publication_eval.get("gaps")):
        worklog.append(
            {
                "kind": "publication_gap",
                "gap_id": _text(gap.get("gap_id")),
                "gap_type": _text(gap.get("gap_type")),
                "severity": _text(gap.get("severity")),
                "summary": _text(gap.get("summary")),
                "evidence_refs": [
                    _text(ref)
                    for ref in gap.get("evidence_refs", [])
                    if _text(ref)
                ],
            }
        )
    return worklog


def _worklog(publication_eval: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [*_quality_worklog(publication_eval), *_gap_worklog(publication_eval)]


def _fallback_route_back(
    *,
    authority_blockers: list[str],
    accept_blockers: list[str],
    publication_eval: Mapping[str, Any],
) -> dict[str, Any]:
    target = "review" if authority_blockers else "write"
    if authority_blockers:
        key_question = "Does publication_eval/latest.json carry AI reviewer provenance and a complete reviewer OS trace?"
        rationale = "Reviewer refinement cannot accept without AI reviewer-backed publication_eval authority."
    else:
        key_question = "Which same-line manuscript or evidence issue blocks reviewer acceptance?"
        rationale = _text(_mapping(publication_eval.get("verdict")).get("summary")) or (
            "AI reviewer publication_eval has not accepted the current manuscript line."
        )
    return {
        "action_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
        "priority": "now",
        "route_target": target,
        "route_key_question": key_question,
        "route_rationale": rationale,
        "requires_controller_decision": True,
        "blockers": list(accept_blockers),
    }


def build_reviewer_refinement_loop_read_model(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval_path = stable_publication_eval_latest_path(study_root=resolved_study_root)
    publication_eval = read_publication_eval_latest(study_root=resolved_study_root)
    authority_blockers = _ai_reviewer_authority_blockers(publication_eval)
    accept_blockers = _accept_blockers(publication_eval, authority_blockers)
    accepted = not accept_blockers
    route_back = None if accepted else _first_same_line_route_back(publication_eval)
    if route_back is None and not accepted:
        route_back = _fallback_route_back(
            authority_blockers=authority_blockers,
            accept_blockers=accept_blockers,
            publication_eval=publication_eval,
        )

    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "snapshot": {
            "source_surface": "publication_eval/latest.json",
            "source_eval_id": _text(publication_eval.get("eval_id")),
            "source_study_id": _text(publication_eval.get("study_id")),
            "source_quest_id": _text(publication_eval.get("quest_id")),
            "source_artifact_path": str(publication_eval_path),
            "verdict": _mapping(publication_eval.get("verdict")),
            "authority_blockers": authority_blockers,
        },
        "accept": {
            "accepted": accepted,
            "status": "accepted" if accepted else "blocked",
            "source": "ai_reviewer_backed_publication_eval_latest",
            "blockers": accept_blockers,
            "package_mutation_allowed": False,
        },
        "revert": {
            "required": not accepted,
            "strategy": "same_line_route_back" if not accepted else "none",
            "direct_package_mutation_allowed": False,
            "route_back": route_back,
        },
        "worklog": _worklog(publication_eval),
        "contract": {
            "read_model_only": True,
            "accept_authority": "AI reviewer-backed artifacts/publication_eval/latest.json",
            "revert_authority": "same-line route-back decision surface",
            "direct_package_mutation_allowed": False,
        },
    }
