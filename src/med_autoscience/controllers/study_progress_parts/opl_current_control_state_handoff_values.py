from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared_base import _non_empty_text

PAPER_STAGE_LOG_KEYS = (
    "surface_kind",
    "schema_version",
    "status",
    "stage_name",
    "current_owner",
    "problem_summary",
    "stage_goal",
    "stage_work_done",
    "paper_work_done",
    "changed_stage_surfaces",
    "changed_paper_surfaces",
    "outcome",
    "remaining_blockers",
    "duration",
    "token_usage",
    "cost",
    "accounting_policy",
    "semantic_incomplete_policy",
    "usage_refs",
    "cost_refs",
    "progress_delta_classification",
    "deliverable_progress_delta",
    "paper_progress_delta",
    "platform_repair_delta",
    "next_forced_delta",
    "evidence_refs",
    "research_pack_progress_summary",
    "research_evidence_pack_summary",
)
STAGE_PROGRESS_LOG_KEYS = (
    "surface_kind",
    "projection_scope",
    "attempt_count",
    "completed_attempt_count",
    "blocked_attempt_count",
    "activity_event_count",
    "runner_progress_event_count",
    "duration_observed_attempt_count",
    "missing_usage_telemetry_attempt_count",
    "temporal_attempt_count",
    "temporal_webui_ref_count",
    "temporal_visibility_readiness_statuses",
    "activity_event_ref_count",
    "attempt_refs",
    "temporal_webui_refs",
    "authority_boundary",
)
OWNER_ROUTE_PROJECTION_KEYS = (
    "next_owner",
    "owner_reason",
    "failure_signature",
    "source_fingerprint",
    "source_refs",
    "allowed_actions",
    "allowed_action_refs",
    "route_target",
    "next_route",
    "target_surface",
    "next_forced_target_surface",
    "acceptance_refs",
    "acceptance_criteria",
    "owner_action",
    "idempotency_key",
)


def _copy_mapping_keys(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in keys if key in value}


def _first_present_mapping_value(mappings: tuple[Mapping[str, Any], ...], key: str) -> Any:
    for item in mappings:
        if key in item:
            return item[key]
    return None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [
        text
        for item in value
        if (text := _non_empty_text(item)) is not None
    ]


def _stage_log_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in PAPER_STAGE_LOG_KEYS if key in value}


def _stage_progress_log_mapping(value: object) -> dict[str, Any]:
    return _copy_mapping_keys(value, STAGE_PROGRESS_LOG_KEYS)


def _observability_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _owner_route_projection(value: object) -> dict[str, Any]:
    return _copy_mapping_keys(value, OWNER_ROUTE_PROJECTION_KEYS)


def _number_value(value: object) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = float(text)
        except ValueError:
            return None
        return int(parsed) if parsed.is_integer() else parsed
    return None


def _first_number_value(*values: object) -> int | float | None:
    for value in values:
        number = _number_value(value)
        if number is not None:
            return number
    return None


def _duration_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    duration = _observability_mapping(value.get("duration"))
    if duration:
        return duration
    seconds = _first_number_value(
        value.get("duration_seconds"),
        value.get("elapsed_seconds"),
        value.get("runtime_duration_seconds"),
    )
    if seconds is not None:
        return {"seconds": seconds}
    return {
        "status": "missing",
        "seconds": None,
        "missing_duration_reason": "no_terminal_stage_duration_observed",
    }


def _token_usage_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("token_usage", "usage", "tokenUsage"):
        usage = _observability_mapping(value.get(key))
        if usage:
            return usage
    return {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
    }


def _cost_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    cost = _observability_mapping(value.get("cost"))
    if cost:
        return cost
    usd = _first_number_value(value.get("cost_usd"), value.get("usd_cost"))
    if usd is not None:
        return {"usd": usd}
    return {
        "status": "missing",
        "usd": None,
        "missing_cost_reason": "no_terminal_stage_cost_observed",
    }


def _refs_from_unknown(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return [
            text
            for candidate in (
                value.get("ref"),
                value.get("ref_id"),
                value.get("path"),
                value.get("uri"),
            )
            if (text := _non_empty_text(candidate)) is not None
        ]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list | tuple | set):
        return []
    refs: list[str] = []
    for item in value:
        refs.extend(_refs_from_unknown(item))
    return refs


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def _usage_refs(value: Mapping[str, Any]) -> list[str]:
    token_usage = _observability_mapping(value.get("token_usage"))
    usage = _observability_mapping(value.get("usage"))
    return _unique_strings(
        [
            *_refs_from_unknown(value.get("usage_ref")),
            *_refs_from_unknown(value.get("usage_refs")),
            *_refs_from_unknown(value.get("token_usage_ref")),
            *_refs_from_unknown(value.get("token_usage_refs")),
            *_refs_from_unknown(token_usage.get("source_refs")),
            *_refs_from_unknown(usage.get("source_refs")),
        ]
    )


def _cost_refs(value: Mapping[str, Any]) -> list[str]:
    cost = _observability_mapping(value.get("cost"))
    return _unique_strings(
        [
            *_refs_from_unknown(value.get("cost_ref")),
            *_refs_from_unknown(value.get("cost_refs")),
            *_refs_from_unknown(cost.get("source_refs")),
        ]
    )
