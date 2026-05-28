from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_authority_snapshot
from med_autoscience.controllers import runtime_health_kernel


def refresh_status(
    status_payload: Mapping[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    provider_readiness: Mapping[str, Any] | None,
    recorded_at: str,
) -> dict[str, Any]:
    return refresh_status_runtime_health_from_provider_readiness(
        status_payload=status_payload,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        provider_readiness=provider_readiness,
        recorded_at=recorded_at,
    )


def refresh_status_runtime_health_from_provider_readiness(
    *,
    status_payload: Mapping[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    provider_readiness: Mapping[str, Any] | None,
    recorded_at: str,
) -> dict[str, Any]:
    status = dict(status_payload)
    readiness = _mapping(provider_readiness)
    if not readiness or quest_id is None:
        return status
    supervisor_tick = _mapping(status.get("supervisor_tick_audit"))
    if not supervisor_tick:
        return status
    supervisor_tick["provider_readiness"] = readiness
    status["supervisor_tick_audit"] = supervisor_tick
    runtime_health = runtime_health_kernel.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        status_payload=status,
        recorded_at=recorded_at,
    )
    status["runtime_health_snapshot"] = runtime_health
    status["runtime_health_epoch"] = runtime_health.get("runtime_health_epoch")
    status["authority_snapshot"] = domain_authority_snapshot.build_authority_snapshot(status)
    return status


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
