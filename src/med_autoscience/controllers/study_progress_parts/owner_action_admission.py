from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_owner_action_admission_projection(
    *,
    payload: Mapping[str, Any],
    current_action: Mapping[str, Any],
    handoff: Mapping[str, Any],
    stage_progress_log: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> dict[str, Any] | None:
    owner = _text(current_action.get("next_owner"))
    work_unit_id = _text(current_action.get("work_unit_id"))
    allowed_actions = _text_list(current_action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    blocked_by = _hard_gate_blockers(payload)
    hard_gate_reasons = _hard_gate_reasons(blocked_by)
    hard_gate_blocked = bool(hard_gate_reasons)
    return {
        "surface_kind": "current_executable_owner_action_admission",
        "schema_version": 1,
        "source": "progress_first_monitoring.current_executable_owner_action",
        "admission_requested": not hard_gate_blocked,
        "provider_attempt_started": not hard_gate_blocked,
        "hard_gate_blocked": hard_gate_blocked,
        "hard_gate_reasons": hard_gate_reasons,
        "blocked_by": blocked_by or None,
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "allowed_actions": allowed_actions,
        "admission_policy": "hard_gate_only_progress_first",
        "provider_attempt_owner": _text(handoff.get("next_owner")) or owner or "one-person-lab",
        "observability_diagnostics": _observability_diagnostics(
            stage_progress_log=stage_progress_log,
            latest_terminal_stage_log=latest_terminal_stage_log,
        ),
        "authority_boundary": {
            "projection_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _hard_gate_blockers(payload: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    interaction = _mapping(payload.get("interaction_arbitration"))
    if interaction.get("requires_user_input") is True or _text(interaction.get("classification")) == "human_gate":
        result["human_gate"] = {
            "requires_user_input": interaction.get("requires_user_input") is True,
            "blocked_reason": _text(interaction.get("blocked_reason"))
            or _text(interaction.get("reason")),
        }
    guard = _mapping(payload.get("execution_owner_guard"))
    forbidden_refs = _text_list(guard.get("forbidden_write_refs"))
    if forbidden_refs:
        result["forbidden_write_refs"] = forbidden_refs
    owner_callable_missing = _owner_callable_surface_missing_blocker(payload)
    if owner_callable_missing:
        result["owner_callable_surface"] = owner_callable_missing
    source_readiness = _mapping(payload.get("source_readiness")) or _mapping(payload.get("startup_data_readiness"))
    missing_sources = _text_list(source_readiness.get("missing_required_sources")) or _text_list(
        source_readiness.get("missing_required_data")
    )
    if missing_sources:
        result["missing_required_source_or_data"] = missing_sources
    irreversible = _mapping(payload.get("irreversible_operation_gate"))
    if _text(irreversible.get("status")) == "blocked":
        result["irreversible_operation"] = {
            "status": "blocked",
            "reason": _text(irreversible.get("reason")) or _text(irreversible.get("blocked_reason")),
        }
    return result


def _owner_callable_surface_missing_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(payload.get("owner_callable_surface"))
    if _text(explicit.get("status")) == "missing":
        return {
            "status": "missing",
            "reason_code": _text(explicit.get("reason_code")) or "owner_callable_surface_missing",
        }
    sources: list[str] = []
    interaction = _mapping(payload.get("interaction_arbitration"))
    if _text(interaction.get("blocked_reason")) == "owner_callable_surface_missing":
        sources.append("interaction_arbitration.blocked_reason")
    if _text(interaction.get("reason_code")) == "owner_callable_surface_missing":
        sources.append("interaction_arbitration.reason_code")
    for surface, key in (
        ("current_execution_envelope", "typed_blocker"),
        ("domain_transition", "typed_blocker"),
        ("domain_transition", "dispatch_result"),
    ):
        if _owner_callable_surface_missing_value(_mapping(payload.get(surface)).get(key)):
            sources.append(f"{surface}.{key}")
    if _owner_callable_surface_missing_value(payload.get("current_blockers")):
        sources.append("current_blockers")
    if not sources:
        return {}
    return {
        "status": "missing",
        "reason_code": "owner_callable_surface_missing",
        "sources": _dedupe_text(sources),
    }


def _owner_callable_surface_missing_value(value: object) -> bool:
    if _text(value) == "owner_callable_surface_missing":
        return True
    if isinstance(value, Mapping):
        for key in ("blocker_id", "blocker_type", "typed_blocker", "blocked_reason", "reason_code"):
            if _text(value.get(key)) == "owner_callable_surface_missing":
                return True
        return False
    return "owner_callable_surface_missing" in _text_list(value)


def _hard_gate_reasons(blocked_by: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    reason_by_surface = {
        "human_gate": "human_gate_required",
        "forbidden_write_refs": "forbidden_write_refs",
        "owner_callable_surface": "owner_callable_surface_missing",
        "missing_required_source_or_data": "missing_required_source_or_data",
        "irreversible_operation": "irreversible_operation",
    }
    for key in blocked_by:
        reason = reason_by_surface.get(key)
        if reason is not None:
            reasons.append(reason)
    return reasons


def _observability_diagnostics(
    *,
    stage_progress_log: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    missing_usage = _numeric(stage_progress_log.get("missing_usage_telemetry_attempt_count")) or 0
    if missing_usage > 0:
        diagnostics.append(
            {
                "diagnostic": "missing_usage_telemetry",
                "authority": "observability_only",
                "attempt_count": _numeric(stage_progress_log.get("attempt_count")),
                "attempt_refs": _text_list(stage_progress_log.get("attempt_refs")),
            }
        )
    missing_user = _text_list(latest_terminal_stage_log.get("missing_user_stage_log_fields"))
    missing_observability = _text_list(latest_terminal_stage_log.get("missing_observability_fields"))
    if missing_user or missing_observability:
        diagnostics.append(
            {
                "diagnostic": "terminal_closeout_observability_incomplete",
                "authority": "observability_only",
                "stage_attempt_id": _text(latest_terminal_stage_log.get("stage_attempt_id")),
                "missing_user_stage_log_fields": missing_user,
                "missing_observability_fields": missing_observability,
            }
        )
    return diagnostics


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _numeric(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return _dedupe_text(value)


def _dedupe_text(values: list[object] | tuple[object, ...] | set[object]) -> list[str]:
    result: list[str] = []
    for item in values:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_owner_action_admission_projection"]
