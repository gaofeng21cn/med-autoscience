from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def progress_first_tick_accounting(monitoring_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    study_items = _ranked_progress_first_study_items(
        [_progress_first_tick_study_item(summary) for summary in monitoring_summaries]
    )
    return {
        "surface": "progress_first_tick_accounting",
        "schema_version": 1,
        "authority": "refs_only_observability",
        "expected_owner_action_count": sum(
            item["monitoring_status"] in {"running", "ready_for_dispatch", "stalled_unconsumed_action"}
            for item in study_items
        ),
        "ready_for_owner_action_count": sum(
            item["monitoring_status"] in {"ready_for_dispatch", "stalled_unconsumed_action"}
            for item in study_items
        ),
        "running_provider_attempt_count": sum(item["running_provider_attempt"] is True for item in study_items),
        "typed_blocker_count": sum(item["monitoring_status"] == "blocked_typed_owner" for item in study_items),
        "human_gate_count": sum(item["monitoring_status"] == "human_gate" for item in study_items),
        "owner_route_contract_blocker_count": sum(
            item["monitoring_status"] == "blocked_owner_route_contract" for item in study_items
        ),
        "unconsumed_owner_action_count": sum(
            item["monitoring_status"] == "stalled_unconsumed_action" for item in study_items
        ),
        "overdue_owner_pickup_count": sum(item["owner_pickup_overdue"] is True for item in study_items),
        "missing_closeout_semantics_count": sum(item["missing_closeout_semantics"] is True for item in study_items),
        "generic_target_surface_count": sum(
            item["target_surface_specificity"] == "generic_route_obligation_fallback" for item in study_items
        ),
        "throughput_bottleneck_counts": _throughput_bottleneck_counts(study_items),
        "throughput_bottlenecks": [dict(item) for item in study_items],
        "studies": study_items,
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def redrive_budget_blocker_superseded_by_terminal_delta(summary: Mapping[str, Any]) -> bool:
    typed_blocker = _dict(summary.get("typed_blocker"))
    if not _is_redrive_budget_blocker(typed_blocker):
        return False
    latest_terminal_stage = _dict(summary.get("latest_terminal_stage"))
    if not latest_terminal_stage:
        return False
    if not _terminal_stage_has_deliverable_delta(latest_terminal_stage):
        return False
    return (
        _text(summary.get("next_owner")) is not None
        or _text(summary.get("controller_action")) is not None
        or _work_unit_id(summary.get("next_work_unit")) is not None
    )


def current_blockers_without_redrive_budget(summary: Mapping[str, Any]) -> list[str]:
    return [
        blocker
        for blocker in _string_list(summary.get("current_blockers"))
        if blocker != "progress_first_owner_redrive_budget_exhausted"
    ]


def _progress_first_tick_study_item(summary: Mapping[str, Any]) -> dict[str, Any]:
    dispatch_consumption = _dict(summary.get("dispatch_consumption"))
    latest_terminal_stage = _dict(summary.get("latest_terminal_stage"))
    semantic = _dict(latest_terminal_stage.get("semantic_completeness"))
    telemetry = _dict(latest_terminal_stage.get("telemetry_completeness"))
    next_forced_delta = _dict(summary.get("next_forced_delta"))
    running_provider_attempt = summary.get("running_provider_attempt") is True
    target_surface_specificity = _target_surface_specificity(next_forced_delta)
    missing_closeout_semantics = bool(latest_terminal_stage) and _text(semantic.get("status")) not in {
        None,
        "complete",
    }
    telemetry_status = _text(telemetry.get("status")) if telemetry else None
    missing_stage_telemetry = bool(latest_terminal_stage) and telemetry_status not in {None, "complete"}
    owner_route_contract_blocker = _owner_route_contract_blocker(
        latest_terminal_stage=latest_terminal_stage,
        missing_closeout_semantics=missing_closeout_semantics,
        next_forced_delta=next_forced_delta,
        target_surface_specificity=target_surface_specificity,
    )
    monitoring_status = _progress_first_monitoring_status(
        summary=summary,
        dispatch_consumption=dispatch_consumption,
        owner_route_contract_blocker=owner_route_contract_blocker,
    )
    owner_pickup_overdue = False if running_provider_attempt else _owner_pickup_overdue(dispatch_consumption)
    return {
        "study_id": _text(summary.get("study_id")),
        "monitoring_status": monitoring_status,
        "active_run_id": _text(summary.get("active_run_id")),
        "running_provider_attempt": running_provider_attempt,
        "next_owner": _text(summary.get("next_owner")),
        "controller_action": _text(summary.get("controller_action")),
        "next_work_unit": _dict(summary.get("next_work_unit")) or _text(summary.get("next_work_unit")),
        "typed_blocker": _dict(summary.get("typed_blocker")) or None,
        "dispatch_consumption": dispatch_consumption or None,
        "owner_pickup_overdue": owner_pickup_overdue,
        "target_surface_specificity": target_surface_specificity,
        "missing_explicit_target_surface": next_forced_delta.get("missing_explicit_target_surface") is True,
        "owner_route_contract_blocker": owner_route_contract_blocker,
        "missing_closeout_semantics": missing_closeout_semantics,
        "missing_closeout_semantic_fields": _string_list(semantic.get("missing_fields")),
        "telemetry_completeness": telemetry_status,
        "missing_telemetry_fields": _string_list(telemetry.get("missing_fields")),
        "missing_stage_telemetry": missing_stage_telemetry,
        "throughput_bottleneck": _throughput_bottleneck(
            monitoring_status=monitoring_status,
            owner_pickup_overdue=owner_pickup_overdue,
            target_surface_specificity=target_surface_specificity,
            missing_closeout_semantics=missing_closeout_semantics,
            missing_stage_telemetry=missing_stage_telemetry,
        ),
    }


def _ranked_progress_first_study_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(items, key=_throughput_priority_key)
    for index, item in enumerate(ranked, start=1):
        item["priority_rank"] = index
    return ranked


def _throughput_bottleneck_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        bottleneck = _text(item.get("throughput_bottleneck")) or "observability_only"
        counts[bottleneck] = counts.get(bottleneck, 0) + 1
    return counts


def _target_surface_specificity(next_forced_delta: Mapping[str, Any]) -> str | None:
    explicit = _text(next_forced_delta.get("target_surface_specificity"))
    if explicit is not None:
        return explicit
    diagnostic = _dict(next_forced_delta.get("target_surface_diagnostic"))
    specificity = _text(diagnostic.get("specificity"))
    if specificity == "precise":
        return "explicit_owner_route_target"
    if specificity == "generic_fallback":
        return "generic_route_obligation_fallback"
    return None


def _throughput_priority_key(item: Mapping[str, Any]) -> tuple[int, str]:
    status = _text(item.get("monitoring_status"))
    if item.get("owner_pickup_overdue") is True:
        rank = 10
    elif status == "blocked_owner_route_contract":
        rank = 15
    elif status == "stalled_unconsumed_action":
        rank = 20
    elif status == "ready_for_dispatch":
        rank = 30
    elif status == "running":
        rank = 40
    elif status == "blocked_typed_owner":
        rank = 50
    elif status == "human_gate":
        rank = 60
    elif item.get("missing_closeout_semantics") is True:
        rank = 70
    elif item.get("missing_stage_telemetry") is True:
        rank = 75
    elif status == "receipt_consumed":
        rank = 80
    else:
        rank = 90
    return (rank, _text(item.get("study_id")) or "")


def _throughput_bottleneck(
    *,
    monitoring_status: str,
    owner_pickup_overdue: bool,
    target_surface_specificity: str | None,
    missing_closeout_semantics: bool,
    missing_stage_telemetry: bool,
) -> str:
    if owner_pickup_overdue:
        return "owner_pickup_overdue"
    if monitoring_status == "blocked_owner_route_contract":
        if target_surface_specificity == "generic_route_obligation_fallback":
            return "generic_target_surface"
        if missing_closeout_semantics:
            return "missing_closeout_semantics"
        return "owner_route_contract_blocker"
    if monitoring_status == "stalled_unconsumed_action":
        return "ready_owner_action_unconsumed"
    if monitoring_status == "ready_for_dispatch":
        return "ready_owner_action"
    if monitoring_status == "running":
        return "running_provider_attempt"
    if monitoring_status == "blocked_typed_owner":
        return "typed_blocker"
    if monitoring_status == "human_gate":
        return "human_gate"
    if target_surface_specificity == "generic_route_obligation_fallback":
        return "generic_target_surface"
    if missing_closeout_semantics:
        return "missing_closeout_semantics"
    if missing_stage_telemetry:
        return "missing_stage_telemetry"
    return "observability_only"


def _progress_first_monitoring_status(
    *,
    summary: Mapping[str, Any],
    dispatch_consumption: Mapping[str, Any],
    owner_route_contract_blocker: str | None,
) -> str:
    if summary.get("running_provider_attempt") is True:
        return "running"
    if _is_human_gate(summary):
        return "human_gate"
    if _is_typed_owner_blocker(summary):
        return "blocked_typed_owner"
    consumption_status = _text(dispatch_consumption.get("consumption_status"))
    owner_action_current = summary.get("owner_action_current")
    if owner_action_current is True or (
        owner_action_current is None
        and (_text(summary.get("next_owner")) is not None or _text(summary.get("controller_action")) is not None)
    ):
        if owner_route_contract_blocker is not None:
            return "blocked_owner_route_contract"
        if consumption_status in {"unconsumed", "stale", "overdue"} or _owner_pickup_overdue(dispatch_consumption):
            return "stalled_unconsumed_action"
        return "ready_for_dispatch"
    if _dict(summary.get("typed_blocker")):
        return "blocked_typed_owner"
    if consumption_status in {"consumed", "receipt_consumed", "completed"}:
        return "receipt_consumed"
    return "observability_only"


def _terminal_stage_has_deliverable_delta(latest_terminal_stage: Mapping[str, Any]) -> bool:
    terminal_semantic = _dict(latest_terminal_stage.get("terminal_closeout_semantic_completeness"))
    progress_delta = _text(latest_terminal_stage.get("progress_delta_classification")) or _text(
        terminal_semantic.get("progress_delta_classification")
    )
    if progress_delta != "deliverable_progress":
        return False
    if not (
        _string_list(latest_terminal_stage.get("changed_stage_surfaces"))
        or _string_list(latest_terminal_stage.get("changed_paper_surfaces"))
    ):
        return False
    semantic = _dict(latest_terminal_stage.get("semantic_completeness"))
    semantic_status = _text(semantic.get("status"))
    terminal_semantic_status = _text(terminal_semantic.get("status"))
    if semantic_status not in {None, "complete"} and terminal_semantic_status != "complete":
        return False
    return _text(latest_terminal_stage.get("status")) in {
        "executed",
        "completed",
        "handoff_ready",
        "completed_for_write_owner_idempotent",
    } or _text(latest_terminal_stage.get("outcome")) in {
        "executed",
        "completed",
        "handoff_ready",
        "completed_for_write_owner_idempotent",
    }


def _is_redrive_budget_blocker(typed_blocker: Mapping[str, Any]) -> bool:
    return any(
        _text(typed_blocker.get(field)) == "progress_first_owner_redrive_budget_exhausted"
        for field in ("blocker_type", "blocker_family", "reason", "blocker_id")
    )


def _owner_route_contract_blocker(
    *,
    latest_terminal_stage: Mapping[str, Any],
    missing_closeout_semantics: bool,
    next_forced_delta: Mapping[str, Any],
    target_surface_specificity: str | None,
) -> str | None:
    if target_surface_specificity == "generic_route_obligation_fallback":
        return "owner_route_target_surface_required"
    if next_forced_delta.get("missing_explicit_target_surface") is True:
        return "owner_route_target_surface_required"
    if missing_closeout_semantics and latest_terminal_stage:
        return "typed_closeout_semantics_required"
    return None


def _is_typed_owner_blocker(summary: Mapping[str, Any]) -> bool:
    if not _dict(summary.get("typed_blocker")):
        return False
    return _text(summary.get("execution_state_kind")) in {"typed_blocker", "blocked_typed_owner"}


def _is_human_gate(summary: Mapping[str, Any]) -> bool:
    if _text(summary.get("progress_delta_classification")) == "human_gate":
        return True
    typed_blocker = _dict(summary.get("typed_blocker"))
    return _text(typed_blocker.get("owner")) in {"user", "physician", "pi"} or _text(
        typed_blocker.get("blocker_id")
    ) in {"human_gate", "study_user_decision_gate"}


def _owner_pickup_overdue(dispatch_consumption: Mapping[str, Any]) -> bool:
    if dispatch_consumption.get("owner_pickup_overdue") is True:
        return True
    hours = dispatch_consumption.get("unconsumed_duration_hours")
    return isinstance(hours, int | float) and not isinstance(hours, bool) and hours > 0


def _dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_blockers_without_redrive_budget",
    "progress_first_tick_accounting",
    "redrive_budget_blocker_superseded_by_terminal_delta",
]
