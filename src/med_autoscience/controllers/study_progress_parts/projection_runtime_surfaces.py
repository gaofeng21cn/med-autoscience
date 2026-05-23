from __future__ import annotations

from typing import Any, Mapping

from .shared import _non_empty_text


def supervision_health_status(
    *,
    publication_gate_stationary: bool,
    auto_runtime_parked: Mapping[str, Any],
    runtime_facts: Any,
    runtime_health_status: str | None,
) -> str | None:
    if publication_gate_stationary:
        return "publication_gate_blocked"
    if bool(auto_runtime_parked.get("parked")):
        return "parked"
    if runtime_facts.recovery_pending or runtime_facts.missing_live_session:
        return "recovering"
    if runtime_facts.strict_live:
        return runtime_health_status or "live"
    return runtime_health_status


def status_absorbing_live_runtime_surfaces(
    *,
    status: dict[str, Any],
    study_id: str,
    opl_runtime_owner_handoff_payload: Mapping[str, Any] | None,
    launch_report_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    del study_id, opl_runtime_owner_handoff_payload, launch_report_payload
    quest_status = _non_empty_text(status.get("quest_status"))
    if quest_status not in {"active", "running"}:
        return status
    return status
