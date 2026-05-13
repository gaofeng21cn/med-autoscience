from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


@dataclass(frozen=True)
class RuntimeControlPorts:
    """Controller-facing operations used by runtime watch orchestration."""

    get_status: Callable[..., dict[str, Any]]
    ensure_runtime: Callable[..., dict[str, Any]]
    build_outer_loop_request: Callable[..., dict[str, Any] | None]
    dispatch_outer_loop: Callable[..., dict[str, Any]]
    materialize_non_dispatching_decision: Callable[..., dict[str, Any]]
    refresh_status_after_ensure: Callable[..., dict[str, Any]]
    materialize_supervision: Callable[..., dict[str, Any] | None]
    deliver_alert: Callable[..., dict[str, Any] | None]
    reconcile_health: Callable[..., Any]
    materialize_autonomy_slo: Callable[..., dict[str, Any]]
    read_ready_ai_repair: Callable[..., dict[str, Any] | None]
    apply_ai_repair: Callable[..., dict[str, Any] | None]
    read_ai_repair_lifecycle: Callable[..., dict[str, Any] | None]
    reconcile_ai_repair_lifecycle: Callable[..., dict[str, Any] | None]


def runtime_status_payload(
    *,
    ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    study_root: Path,
) -> dict[str, Any]:
    return dict(ports.get_status(profile=profile, study_root=study_root))


def ensure_runtime(
    *,
    ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    return dict(ports.ensure_runtime(profile=profile, study_root=study_root, source=source))


def build_outer_loop_request(
    *,
    ports: RuntimeControlPorts,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    result = ports.build_outer_loop_request(study_root=study_root, status_payload=dict(status_payload))
    return dict(result) if isinstance(result, Mapping) else None


def dispatch_outer_loop(
    *,
    ports: RuntimeControlPorts,
    profile: WorkspaceProfile,
    source: str,
    tick_request: Mapping[str, Any],
) -> dict[str, Any]:
    return dict(ports.dispatch_outer_loop(profile=profile, source=source, **dict(tick_request)))


__all__ = [
    "RuntimeControlPorts",
    "build_outer_loop_request",
    "dispatch_outer_loop",
    "ensure_runtime",
    "runtime_status_payload",
]
