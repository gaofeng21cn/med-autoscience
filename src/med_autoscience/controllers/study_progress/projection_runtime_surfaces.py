from __future__ import annotations

from typing import Any, Mapping

def supervision_health_status(
    *,
    auto_runtime_parked: Mapping[str, Any],
    runtime_facts: Any,
    runtime_health_status: str | None,
) -> str | None:
    if bool(auto_runtime_parked.get("parked")):
        return "parked"
    if runtime_facts.recovery_pending or runtime_facts.missing_live_session:
        return "recovering"
    if runtime_facts.strict_live:
        return runtime_health_status or "live"
    return runtime_health_status
