from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import runtime_health_kernel


def runtime_health_epoch_for_ai_reviewer_route(
    *,
    study_root: Path,
    route_context: Mapping[str, Any],
    controller_context: Mapping[str, Any],
    current_owner_route: Mapping[str, Any],
    work_unit: Mapping[str, Any],
) -> str | None:
    current_owner_refs = _mapping(current_owner_route.get("source_refs"))
    current_owner_basis = _mapping(current_owner_refs.get("owner_route_currentness_basis"))
    work_unit_owner_route = _mapping(work_unit.get("owner_route"))
    work_unit_owner_refs = _mapping(work_unit_owner_route.get("source_refs"))
    work_unit_owner_basis = _mapping(work_unit_owner_refs.get("owner_route_currentness_basis"))
    work_unit_refs = _mapping(work_unit.get("source_refs"))
    route_context_refs = _mapping(route_context.get("source_refs"))
    route_context_basis = _mapping(route_context_refs.get("owner_route_currentness_basis")) or _mapping(
        route_context.get("owner_route_currentness_basis")
    )
    runtime_health_snapshot = _mapping(route_context.get("runtime_health_snapshot"))
    for value in (
        controller_context.get("runtime_health_epoch"),
        _mapping(controller_context.get("runtime_health_snapshot")).get("runtime_health_epoch"),
        current_owner_route.get("runtime_health_epoch"),
        current_owner_refs.get("runtime_health_epoch"),
        current_owner_basis.get("runtime_health_epoch"),
        route_context.get("runtime_health_epoch"),
        runtime_health_snapshot.get("runtime_health_epoch"),
        route_context_refs.get("runtime_health_epoch"),
        route_context_basis.get("runtime_health_epoch"),
        work_unit.get("runtime_health_epoch"),
        work_unit_refs.get("runtime_health_epoch"),
        work_unit_owner_route.get("runtime_health_epoch"),
        work_unit_owner_refs.get("runtime_health_epoch"),
        work_unit_owner_basis.get("runtime_health_epoch"),
        _runtime_health_epoch_from_study_surfaces(study_root=study_root),
    ):
        if text := _text(value):
            return text
    return None


def _runtime_health_epoch_from_study_surfaces(*, study_root: Path) -> str | None:
    for path in (
        runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root),
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
    ):
        payload = _read_json(path)
        if not payload:
            continue
        runtime_health_snapshot = _mapping(payload.get("runtime_health_snapshot"))
        if text := _text(payload.get("runtime_health_epoch")):
            return text
        if text := _text(runtime_health_snapshot.get("runtime_health_epoch")):
            return text
    return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["runtime_health_epoch_for_ai_reviewer_route"]
