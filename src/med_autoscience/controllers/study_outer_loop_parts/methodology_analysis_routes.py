from __future__ import annotations

from typing import Any


WORK_UNIT_TARGET_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)
METHODOLOGY_ANALYSIS_ROUTE_MARKERS = (
    "methodology",
    "methodologic",
    "methodological",
    "methodologic blocker",
    "source-documentation",
    "source documentation",
    "model reproducibility",
    "prediction-model",
    "harmonization",
    "unit harmonization",
    "unit-harmonized",
    "unit-standardized",
    "hdl",
    "calibration",
    "uncertainty",
    "方法学",
    "单位",
    "归一化",
    "对齐",
)


def _compact_texts(*values: object) -> tuple[str, ...]:
    texts: list[str] = []
    for value in values:
        if isinstance(value, dict):
            texts.extend(_compact_texts(*value.values()))
            continue
        if isinstance(value, (list, tuple)):
            texts.extend(_compact_texts(*value))
            continue
        text = str(value or "").strip()
        if text:
            texts.append(text)
    return tuple(texts)


def analysis_route_action(action: dict[str, Any] | None) -> bool:
    if not isinstance(action, dict):
        return False
    action_type = str(action.get("action_type") or "").strip()
    route_target = str(action.get("route_target") or "").strip()
    next_work_unit = action.get("next_work_unit")
    next_work_unit_lane = (
        str(next_work_unit.get("lane") or "").strip()
        if isinstance(next_work_unit, dict)
        else ""
    )
    return (
        action_type in {"bounded_analysis", "return_to_analysis_campaign"}
        or route_target == "analysis-campaign"
        or next_work_unit_lane == "analysis-campaign"
    )


def methodology_analysis_route_action(action: dict[str, Any] | None) -> bool:
    if not analysis_route_action(action):
        return False
    assert isinstance(action, dict)
    corpus = " \n".join(
        _compact_texts(
            action.get("reason"),
            action.get("route_key_question"),
            action.get("route_rationale"),
            action.get("next_work_unit"),
            action.get("blocking_work_units"),
            action.get("specificity_targets"),
        )
    ).lower()
    return any(marker.lower() in corpus for marker in METHODOLOGY_ANALYSIS_ROUTE_MARKERS)


def publication_eval_has_methodology_analysis_route(publication_eval_payload: dict[str, Any]) -> bool:
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return False
    return any(
        methodology_analysis_route_action(action)
        for action in recommended_actions
        if isinstance(action, dict) and action.get("requires_controller_decision") is True
    )


def publication_eval_methodology_analysis_action(
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any] | None:
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        if methodology_analysis_route_action(action):
            return dict(action)
    return None


def merge_publication_eval_methodology_work_unit(
    recommended_action: dict[str, Any],
    *,
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any]:
    if not analysis_route_action(recommended_action):
        return recommended_action
    source_action = publication_eval_methodology_analysis_action(publication_eval_payload)
    if source_action is None:
        return recommended_action
    next_work_unit = source_action.get("next_work_unit")
    if not isinstance(next_work_unit, dict):
        return recommended_action
    merged = dict(recommended_action)
    merged["next_work_unit"] = dict(next_work_unit)
    blocking_work_units = [
        dict(item)
        for item in (source_action.get("blocking_work_units") or [])
        if isinstance(item, dict)
    ]
    if blocking_work_units:
        merged["blocking_work_units"] = blocking_work_units
    fingerprint = str(source_action.get("work_unit_fingerprint") or "").strip()
    if fingerprint:
        merged["work_unit_fingerprint"] = fingerprint
    for key in WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in source_action and key not in merged:
            merged[key] = source_action[key]
    return merged


def methodology_analysis_route_preempts_ai_reviewer_recheck(
    *,
    domain_transition_decision_type: str,
    task_intake_action: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any],
) -> bool:
    return domain_transition_decision_type == "ai_reviewer_re_eval" and (
        methodology_analysis_route_action(task_intake_action)
        or publication_eval_has_methodology_analysis_route(publication_eval_payload)
    )
