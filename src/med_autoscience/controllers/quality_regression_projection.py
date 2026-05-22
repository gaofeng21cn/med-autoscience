from __future__ import annotations

from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
SURFACE = "quality_regression_projection"
QUALITY_DIMENSIONS: tuple[str, ...] = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)
QUALITY_STATUS_RANK = {
    "blocked": 0,
    "underdefined": 1,
    "partial": 2,
    "ready": 3,
}
REAL_STUDY_SOAK_STAGES: tuple[str, ...] = (
    "literature_scout",
    "line_selection",
    "main_analysis",
    "bounded_analysis",
    "route_back",
    "stop_loss",
    "revision_reopen",
    "runtime_recovery",
    "finalize_rebuild",
    "final_pre_submission_audit",
)
AUTHORITY = {
    "owner": "MAS Evaluation OS",
    "role": "observability_projection_only",
    "can_authorize_publication_quality": False,
    "can_authorize_submission_readiness": False,
    "can_replace_ai_reviewer": False,
    "can_replace_publication_eval_latest": False,
    "can_replace_controller_decision_latest": False,
    "can_replace_progress_projection": False,
    "can_replace_study_truth": False,
    "publication_authority_surface": "artifacts/publication_eval/latest.json",
    "controller_authority_surface": "artifacts/controller_decisions/latest.json",
    "runtime_authority_surface": "progress_projection",
    "study_truth_authority_surface": "StudyTruthKernel",
    "submission_readiness_authority_surface": "submission readiness",
    "judge_score_role": "calibration_evidence_only",
}

__all__ = ["build_quality_regression_projection"]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return dict(value)


def _required_text(payload: Mapping[str, Any], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be non-empty")
    return value.strip()


def _text_sequence(value: Any, label: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be a list")
    refs: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label} entries must be non-empty strings")
        ref = item.strip()
        if ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    if not refs:
        raise ValueError(f"{label} must not be empty")
    return refs


def _quality_assessment(eval_payload: Mapping[str, Any], label: str) -> dict[str, Any]:
    quality = eval_payload.get("quality_assessment")
    if not isinstance(quality, Mapping):
        raise ValueError(f"{label}.quality_assessment must be a mapping")
    normalized = dict(quality)
    for dimension in QUALITY_DIMENSIONS:
        item = normalized.get(dimension)
        if not isinstance(item, Mapping):
            raise ValueError(f"{label}.quality_assessment.{dimension} must be a mapping")
        status = item.get("status")
        if status not in QUALITY_STATUS_RANK:
            allowed = ", ".join(QUALITY_STATUS_RANK)
            raise ValueError(f"{label}.quality_assessment.{dimension}.status must be one of: {allowed}")
    return normalized


def _eval_ref(eval_payload: Mapping[str, Any], label: str) -> str:
    return _required_text(eval_payload, "eval_ref", label)


def _trajectory(draft_status: str, revision_status: str, final_status: str) -> str:
    draft_rank = QUALITY_STATUS_RANK[draft_status]
    revision_rank = QUALITY_STATUS_RANK[revision_status]
    final_rank = QUALITY_STATUS_RANK[final_status]
    if final_rank < draft_rank or final_rank < revision_rank:
        return "regressed"
    if final_rank > draft_rank or final_rank > revision_rank:
        return "improved"
    return "unchanged"


def _repair_results_for_dimension(
    *,
    dimension: str,
    historical_repair_results: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for index, raw_result in enumerate(historical_repair_results):
        result = _mapping(raw_result, f"historical_repair_results[{index}]")
        if result.get("dimension") != dimension:
            continue
        results.append(
            {
                "repair_id": _required_text(result, "repair_id", f"historical_repair_results[{index}]"),
                "result": _required_text(result, "result", f"historical_repair_results[{index}]"),
                "evidence_ref": _required_text(result, "evidence_ref", f"historical_repair_results[{index}]"),
            }
        )
    return results


def _normalized_judge_scores(judge_scores: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, raw_score in enumerate(judge_scores):
        score = _mapping(raw_score, f"judge_scores[{index}]")
        compared_stages = _text_sequence(score.get("compared_stages"), f"judge_scores[{index}].compared_stages")
        normalized.append(
            {
                "judge_id": _required_text(score, "judge_id", f"judge_scores[{index}]"),
                "compared_stages": compared_stages,
                "score": score.get("score"),
                "calibration_evidence_ref": _required_text(
                    score,
                    "calibration_evidence_ref",
                    f"judge_scores[{index}]",
                ),
                "role": "calibration_evidence_only",
                "can_authorize_publication_quality": False,
                "can_replace_ai_reviewer": False,
                "can_authorize_submission_readiness": False,
            }
        )
    return normalized


def _normalized_rubric_node(raw_node: Mapping[str, Any], label: str) -> dict[str, Any]:
    node = _mapping(raw_node, label)
    reviewer_kind = _required_text(node, "reviewer_kind", label)
    if reviewer_kind not in {"human_reviewer", "ai_reviewer"}:
        raise ValueError(f"{label}.reviewer_kind must be one of: human_reviewer, ai_reviewer")
    children = node.get("children", [])
    if not isinstance(children, Sequence) or isinstance(children, (str, bytes)):
        raise ValueError(f"{label}.children must be a list")
    return {
        "node_id": _required_text(node, "node_id", label),
        "label": _required_text(node, "label", label),
        "reviewer_kind": reviewer_kind,
        "evidence_refs": _text_sequence(node.get("evidence_refs"), f"{label}.evidence_refs"),
        "judge_calibration_refs": _text_sequence(
            node.get("judge_calibration_refs"),
            f"{label}.judge_calibration_refs",
        ),
        "score": node.get("score"),
        "score_role": "calibration_evidence_only",
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "children": [
            _normalized_rubric_node(child, f"{label}.children[{index}]")
            for index, child in enumerate(children)
            if isinstance(child, Mapping)
        ],
    }


def _normalized_rubric_tree(rubric_nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not rubric_nodes:
        return None
    if not isinstance(rubric_nodes, Sequence) or isinstance(rubric_nodes, (str, bytes)):
        raise ValueError("rubric_nodes must be a list")
    return {
        "surface": "paperbench_style_hierarchical_rubric_tree",
        "owner": "MAS Evaluation OS",
        "role": "calibration_evidence_only",
        "can_replace_publication_eval_latest": False,
        "can_replace_controller_decision_latest": False,
        "can_replace_progress_projection": False,
        "can_replace_study_truth": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_publication_quality": False,
        "publication_authority_surface": "artifacts/publication_eval/latest.json",
        "reviewer_distinction": {
            "human_reviewer_role": "calibration_signal_only",
            "ai_reviewer_role": "publication_eval_trace_evidence_only",
            "rubric_can_replace_ai_reviewer": False,
        },
        "nodes": [
            _normalized_rubric_node(node, f"rubric_nodes[{index}]")
            for index, node in enumerate(rubric_nodes)
            if isinstance(node, Mapping)
        ],
    }


def build_quality_regression_projection(
    *,
    draft_eval: Mapping[str, Any],
    revision_eval: Mapping[str, Any],
    final_package_eval: Mapping[str, Any],
    historical_repair_results: Sequence[Mapping[str, Any]],
    calibration_evidence_refs: Sequence[str],
    judge_scores: Sequence[Mapping[str, Any]] = (),
    rubric_nodes: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    draft_payload = _mapping(draft_eval, "draft_eval")
    revision_payload = _mapping(revision_eval, "revision_eval")
    final_payload = _mapping(final_package_eval, "final_package_eval")
    calibration_refs = _text_sequence(calibration_evidence_refs, "calibration_evidence_refs")

    draft_quality = _quality_assessment(draft_payload, "draft_eval")
    revision_quality = _quality_assessment(revision_payload, "revision_eval")
    final_quality = _quality_assessment(final_payload, "final_package_eval")

    dimension_comparisons: list[dict[str, Any]] = []
    for dimension in QUALITY_DIMENSIONS:
        draft_status = str(draft_quality[dimension]["status"])
        revision_status = str(revision_quality[dimension]["status"])
        final_status = str(final_quality[dimension]["status"])
        dimension_comparisons.append(
            {
                "dimension": dimension,
                "draft_status": draft_status,
                "revision_status": revision_status,
                "final_status": final_status,
                "trajectory": _trajectory(draft_status, revision_status, final_status),
                "historical_repair_results": _repair_results_for_dimension(
                    dimension=dimension,
                    historical_repair_results=historical_repair_results,
                ),
            }
        )

    improved = sum(1 for item in dimension_comparisons if item["trajectory"] == "improved")
    regressed = sum(1 for item in dimension_comparisons if item["trajectory"] == "regressed")
    repair_count = sum(len(item["historical_repair_results"]) for item in dimension_comparisons)
    calibration_evidence = {
        "refs": calibration_refs,
        "judge_scores": _normalized_judge_scores(judge_scores),
    }
    rubric_tree = _normalized_rubric_tree(rubric_nodes)
    if rubric_tree is not None:
        calibration_evidence["rubric_tree"] = rubric_tree
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "package_eval_refs": {
            "draft": _eval_ref(draft_payload, "draft_eval"),
            "revision": _eval_ref(revision_payload, "revision_eval"),
            "final": _eval_ref(final_payload, "final_package_eval"),
        },
        "dimension_comparisons": dimension_comparisons,
        "regression_summary": {
            "dimensions_compared": len(dimension_comparisons),
            "dimensions_improved": improved,
            "dimensions_regressed": regressed,
            "historical_repair_results_compared": repair_count,
            "status": "regression_detected" if regressed else "no_regression_detected",
        },
        "calibration_evidence": calibration_evidence,
        "soak_matrix_evidence": {
            "role": "soak_proof_only",
            "can_authorize_publication_quality": False,
            "required_stages": list(REAL_STUDY_SOAK_STAGES),
            "stage_results": [],
        },
    }
