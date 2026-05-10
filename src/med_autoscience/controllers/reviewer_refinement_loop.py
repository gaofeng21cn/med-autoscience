from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies import DEFAULT_PUBLICATION_CRITIQUE_POLICY
from med_autoscience.controllers.ai_reviewer_calibration import (
    build_ai_reviewer_calibration_learning_read_model,
)
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    stable_publication_eval_latest_path,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from med_autoscience.study_decision_record import StudyDecisionType
from med_autoscience.controllers.revision_rebuttal_loop import (
    build_revision_rebuttal_loop_projection,
)
from med_autoscience.controllers.reviewer_refinement_loop_parts.repair_work_units import (
    EXECUTION_CONTRACT,
    build_repair_work_units,
)


__all__ = ["build_reviewer_refinement_loop_read_model"]


_SURFACE = "reviewer_refinement_loop"
_SCHEMA_VERSION = 1
_POLICY_ID = DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]
_ACCEPTABLE_VERDICTS = frozenset({"promising"})
_ACCEPTABLE_PRIMARY_CLAIM_STATUSES = frozenset({"supported"})
_BLOCKING_GAP_SEVERITIES = frozenset({"must_fix", "important"})
_CALIBRATION_LEARNING_PATH = Path("artifacts/publication_eval/ai_reviewer_calibration_learning.json")
_REPAIR_PLANNING_MODE = "repair_planning_only"
_ACCEPTED_MODE = "accepted"


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _calibration_case_id(ref: str) -> str:
    return ref.rsplit("#", 1)[-1].strip()


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


def _snapshot_ref(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
) -> dict[str, Any]:
    return {
        "source_surface": "publication_eval/latest.json",
        "source_eval_id": _text(publication_eval.get("eval_id")),
        "source_artifact_path": str(publication_eval_path),
    }


def _snapshot_refs(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
) -> list[dict[str, Any]]:
    return [
        _snapshot_ref(
            publication_eval=publication_eval,
            publication_eval_path=publication_eval_path,
        )
    ]


def _worklog_lifecycle(
    *,
    accepted: bool,
    route_back: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if accepted:
        return {
            "state": "accepted",
            "route": "accepted",
            "accepted": True,
            "reverted": False,
            "source": "ai_reviewer_backed_publication_eval_latest",
        }
    lifecycle: dict[str, Any] = {
        "state": "reverted",
        "route": "same_line_route_back",
        "accepted": False,
        "reverted": True,
        "source": "ai_reviewer_backed_publication_eval_latest",
        "direct_package_mutation_allowed": False,
    }
    if route_back:
        action_id = _text(route_back.get("action_id"))
        route_target = _text(route_back.get("route_target"))
        if action_id:
            lifecycle["route_back_action_id"] = action_id
        if route_target:
            lifecycle["route_target"] = route_target
    return lifecycle


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


def _read_calibration_learning_model(study_root: Path) -> dict[str, Any]:
    path = study_root / _CALIBRATION_LEARNING_PATH
    if not path.exists():
        return build_ai_reviewer_calibration_learning_read_model()
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return build_ai_reviewer_calibration_learning_read_model(payload)


def _required_calibration_ref_blockers(required_refs: list[str]) -> list[str]:
    return [f"required_calibration_ref_missing:{_calibration_case_id(ref)}" for ref in required_refs]


def _first_same_line_route_back(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
) -> dict[str, Any] | None:
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
            "artifact_refs": _text_list(action.get("evidence_refs")),
            "snapshot_refs": _snapshot_refs(
                publication_eval=publication_eval,
                publication_eval_path=publication_eval_path,
            ),
        }
    return None


def _quality_worklog(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    accepted: bool,
    route_back: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    worklog: list[dict[str, Any]] = []
    for dimension, payload in quality_assessment.items():
        item = _mapping(payload)
        status = _text(item.get("status"))
        if not status or status == "ready":
            continue
        summary = _text(item.get("summary"))
        artifact_refs = _text_list(item.get("evidence_refs"))
        worklog.append(
            {
                "kind": "quality_dimension",
                "concern_id": f"quality_dimension:{dimension}",
                "reviewer_concern": summary,
                "section": dimension,
                "dimension": dimension,
                "status": status,
                "summary": summary,
                "reviewer_revision_advice": _text(item.get("reviewer_revision_advice")) or None,
                "reviewer_next_round_focus": _text(item.get("reviewer_next_round_focus")) or None,
                "evidence_refs": artifact_refs,
                "artifact_refs": artifact_refs,
                "snapshot_refs": _snapshot_refs(
                    publication_eval=publication_eval,
                    publication_eval_path=publication_eval_path,
                ),
                "lifecycle": _worklog_lifecycle(
                    accepted=accepted,
                    route_back=route_back,
                ),
            }
        )
    return worklog


def _gap_worklog(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    accepted: bool,
    route_back: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    worklog: list[dict[str, Any]] = []
    for gap in _list_of_mappings(publication_eval.get("gaps")):
        gap_id = _text(gap.get("gap_id"))
        gap_type = _text(gap.get("gap_type"))
        summary = _text(gap.get("summary"))
        artifact_refs = _text_list(gap.get("evidence_refs"))
        worklog.append(
            {
                "kind": "publication_gap",
                "concern_id": f"publication_gap:{gap_id}",
                "reviewer_concern": summary,
                "section": gap_type,
                "gap_id": gap_id,
                "gap_type": gap_type,
                "severity": _text(gap.get("severity")),
                "summary": summary,
                "evidence_refs": artifact_refs,
                "artifact_refs": artifact_refs,
                "snapshot_refs": _snapshot_refs(
                    publication_eval=publication_eval,
                    publication_eval_path=publication_eval_path,
                ),
                "lifecycle": _worklog_lifecycle(
                    accepted=accepted,
                    route_back=route_back,
                ),
            }
        )
    return worklog


def _worklog(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    accepted: bool,
    route_back: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        *_quality_worklog(
            publication_eval=publication_eval,
            publication_eval_path=publication_eval_path,
            accepted=accepted,
            route_back=route_back,
        ),
        *_gap_worklog(
            publication_eval=publication_eval,
            publication_eval_path=publication_eval_path,
            accepted=accepted,
            route_back=route_back,
        ),
    ]


def _reviewer_comments_from_worklog(worklog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    for item in worklog:
        section = _text(item.get("section"))
        severity = _text(item.get("severity")) or "major"
        if severity in _BLOCKING_GAP_SEVERITIES:
            severity = "major"
        requested_change = (
            _text(item.get("reviewer_revision_advice"))
            or _text(item.get("summary"))
            or "Repair this reviewer concern before acceptance."
        )
        if section in {"claim", "evidence", "evidence_strength"} and "analysis" not in requested_change.lower():
            requested_change = f"Add additional analysis or evidence repair before acceptance. {requested_change}"
        comments.append(
            {
                "comment_id": _text(item.get("concern_id")),
                "source": "ai_reviewer",
                "concern": _text(item.get("reviewer_concern")) or _text(item.get("summary")),
                "severity": severity,
                "requested_change": requested_change,
                "target_section": section,
                "target_claim": _text(item.get("claim_id")) or None,
            }
        )
    return comments


def _dedupe_refs(refs: list[str]) -> list[str]:
    deduped: list[str] = []
    for ref in refs:
        if ref and ref not in deduped:
            deduped.append(ref)
    return deduped


def _review_refs_for_repair_loop(
    *,
    publication_eval: Mapping[str, Any],
    worklog: list[dict[str, Any]],
) -> list[str]:
    refs: list[str] = []
    reviewer_os = _mapping(publication_eval.get("reviewer_operating_system"))
    input_bundle = _mapping(reviewer_os.get("input_bundle"))
    refs.extend([_text(input_bundle.get("review_ledger"))])
    for item in worklog:
        refs.extend(_text_list(item.get("reviewer_trace_refs")))
        if not any(refs):
            refs.extend(_text(snapshot.get("source_artifact_path")) for snapshot in _list_of_mappings(item.get("snapshot_refs")))
    return _dedupe_refs(refs) or ["publication_eval/latest.json"]


def _comment_matrix_for_worklog(
    *,
    worklog: list[dict[str, Any]],
    review_refs: list[str],
) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for item, comment in zip(worklog, _reviewer_comments_from_worklog(worklog), strict=True):
        evidence_refs = _dedupe_refs(
            _text_list(item.get("evidence_refs")) + _text_list(item.get("artifact_refs"))
        )
        projection = build_revision_rebuttal_loop_projection(
            {
                "reviewer_comments": [comment],
                "evidence_ledger_refs": evidence_refs,
                "review_ledger_refs": review_refs,
            }
        )
        matrix.extend(projection["comment_to_action_matrix"])
    return matrix


def _repair_plan(action_matrix: list[dict[str, Any]]) -> dict[str, bool]:
    return {
        "analysis_repair_required": any(
            item["repair_routes"]["analysis_repair"]["required"] for item in action_matrix
        ),
        "text_repair_required": any(
            item["repair_routes"]["text_repair"]["required"] for item in action_matrix
        ),
        "ai_reviewer_recheck_required": any(
            item["repair_routes"]["ai_reviewer_recheck"]["required"] for item in action_matrix
        ),
        "mechanical_projection_can_authorize_quality": False,
    }


def _next_repair_loop_action(action_matrix: list[dict[str, Any]]) -> dict[str, str]:
    if any(item["repair_routes"]["analysis_repair"]["required"] for item in action_matrix):
        return {
            "action": "repair_recheck_required",
            "reason": "analysis_repair_requires_ai_reviewer_recheck",
        }
    if any(item["repair_routes"]["text_repair"]["required"] for item in action_matrix):
        return {
            "action": "repair_recheck_required",
            "reason": "text_repair_requires_ai_reviewer_recheck",
        }
    return {
        "action": "repair_recheck_required",
        "reason": "rebuttal_closure_requires_ai_reviewer_recheck",
    }


def _repair_loop_projection(
    *,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
    worklog: list[dict[str, Any]],
) -> dict[str, Any]:
    review_refs = _review_refs_for_repair_loop(
        publication_eval=publication_eval,
        worklog=worklog,
    )
    action_matrix = _comment_matrix_for_worklog(worklog=worklog, review_refs=review_refs)
    repair_work_units = build_repair_work_units(
        publication_eval=publication_eval,
        publication_eval_path=publication_eval_path,
        worklog=worklog,
        action_matrix=action_matrix,
    )
    return {
        "mode": _REPAIR_PLANNING_MODE,
        "status": "executable_ready" if repair_work_units else "blocked",
        "blockers": [] if repair_work_units else ["missing_executable_repair_work_units"],
        "comment_to_action_matrix": action_matrix,
        "repair_work_units": repair_work_units,
        "repair_plan": _repair_plan(action_matrix),
        "execution_contract": dict(EXECUTION_CONTRACT),
        "next_action": _next_repair_loop_action(action_matrix) if action_matrix else {
            "action": "collect_revision_intake",
            "reason": "missing_reviewer_comments",
        },
    }


def _fallback_route_back(
    *,
    authority_blockers: list[str],
    accept_blockers: list[str],
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path,
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
        "artifact_refs": [],
        "snapshot_refs": _snapshot_refs(
            publication_eval=publication_eval,
            publication_eval_path=publication_eval_path,
        ),
    }


def build_reviewer_refinement_loop_read_model(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval_path = stable_publication_eval_latest_path(study_root=resolved_study_root)
    publication_eval = read_publication_eval_latest(study_root=resolved_study_root)
    calibration_learning = _read_calibration_learning_model(resolved_study_root)
    required_calibration_refs = calibration_learning["required_calibration_refs"]
    authority_blockers = _ai_reviewer_authority_blockers(publication_eval)
    accept_blockers = _accept_blockers(publication_eval, authority_blockers)
    accept_blockers.extend(_required_calibration_ref_blockers(required_calibration_refs))
    accepted = not accept_blockers
    route_back = None if accepted else _first_same_line_route_back(
        publication_eval=publication_eval,
        publication_eval_path=publication_eval_path,
    )
    if route_back is None and not accepted:
        route_back = _fallback_route_back(
            authority_blockers=authority_blockers,
            accept_blockers=accept_blockers,
            publication_eval=publication_eval,
            publication_eval_path=publication_eval_path,
        )
    worklog = _worklog(
        publication_eval=publication_eval,
        publication_eval_path=publication_eval_path,
        accepted=accepted,
        route_back=route_back,
    )
    executable_repair_allowed = not accepted and not authority_blockers
    repair_loop = _repair_loop_projection(
        publication_eval=publication_eval,
        publication_eval_path=publication_eval_path,
        worklog=worklog,
    ) if executable_repair_allowed else {
        "mode": _ACCEPTED_MODE,
        "status": "accepted" if accepted else "blocked",
        "blockers": [] if accepted else list(authority_blockers),
        "comment_to_action_matrix": [],
        "repair_work_units": [],
        "repair_plan": {
            "analysis_repair_required": False,
            "text_repair_required": False,
            "ai_reviewer_recheck_required": False,
            "mechanical_projection_can_authorize_quality": False,
        },
        "execution_contract": dict(EXECUTION_CONTRACT),
        "next_action": {
            "action": "none",
            "reason": "reviewer_refinement_accepted",
        },
    }

    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "mode": _ACCEPTED_MODE if accepted else _REPAIR_PLANNING_MODE,
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
        "required_calibration_refs": required_calibration_refs,
        "calibration_learning": calibration_learning,
        "comment_to_action_matrix": repair_loop["comment_to_action_matrix"],
        "repair_work_units": repair_loop["repair_work_units"],
        "repair_loop": repair_loop,
        "revert": {
            "required": not accepted,
            "strategy": "same_line_route_back" if not accepted else "none",
            "direct_package_mutation_allowed": False,
            "route_back": route_back,
        },
        "worklog": worklog,
        "contract": {
            "read_model_only": True,
            "mode_when_blocked": _REPAIR_PLANNING_MODE,
            "required_calibration_refs_must_be_read_before_accept": True,
            "accept_authority": "AI reviewer-backed artifacts/publication_eval/latest.json",
            "revert_authority": "same-line route-back decision surface",
            "direct_package_mutation_allowed": False,
            "learning_can_authorize_repair_completion": False,
            "learning_can_authorize_quality": False,
            "learning_can_authorize_submission": False,
            "learning_can_authorize_finalize": False,
        },
    }
