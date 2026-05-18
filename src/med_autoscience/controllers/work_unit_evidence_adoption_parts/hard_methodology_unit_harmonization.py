from __future__ import annotations

from typing import Any, Callable


NEXT_OWNER = "analysis_harmonization_owner"
NEXT_WORK_UNIT = "unit_harmonized_external_validation_rerun"
BLOCKED_REASON = "unit_harmonized_rerun_required"
TARGET_TOKENS = frozenset(
    {
        "hdl_unit_standardized_sensitivity",
        "unit_standardized_model_application_or_sensitivity",
        NEXT_WORK_UNIT,
        BLOCKED_REASON,
        "unit_harmonization",
        "unit_harmonized",
        "unit_standardized",
        "unit-standardized",
        "unit-harmonized",
        "harmonization_route_back",
    }
)


def authorization_has_target(
    authorization_context: dict[str, Any],
    *,
    text: Callable[[object], str | None],
) -> bool:
    values: list[str] = []
    for key in ("work_unit_id", "route_key_question", "route_rationale", "source_route_key_question"):
        if value := text(authorization_context.get(key)):
            values.append(value.lower())
    next_work_unit = authorization_context.get("next_work_unit")
    if isinstance(next_work_unit, dict):
        for key in ("unit_id", "summary", "required_owner", "required_next_work_unit", "typed_blocker"):
            if value := text(next_work_unit.get(key)):
                values.append(value.lower())
    for target in authorization_context.get("specificity_targets") or []:
        if not isinstance(target, dict):
            continue
        for key in ("target_id", "blocking_reason", "source_path"):
            if value := text(target.get(key)):
                values.append(value.lower())
    return any(any(token in value for token in TARGET_TOKENS) for value in values)


def report_satisfies_authorization(
    payload: dict[str, Any],
    *,
    report_next_work_unit: Callable[[dict[str, Any]], str | None],
    text: Callable[[object], str | None],
) -> bool:
    if (
        text(payload.get("next_owner")) == NEXT_OWNER
        and report_next_work_unit(payload) == NEXT_WORK_UNIT
        and text(payload.get("blocked_reason")) == BLOCKED_REASON
    ):
        return True
    if payload.get("unit_harmonized_rerun_completed") is True:
        return True
    result = payload.get("result")
    return isinstance(result, dict) and result.get("unit_harmonized_rerun_completed") is True


def normalized_requirement_flag(payload: dict[str, Any], *, text: Callable[[object], str | None]) -> dict[str, bool]:
    if text(payload.get("blocked_reason")) != BLOCKED_REASON:
        return {}
    return {"unit_harmonized_rerun_required": True}
