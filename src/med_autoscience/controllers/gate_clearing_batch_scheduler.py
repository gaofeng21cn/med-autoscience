from __future__ import annotations

import hashlib
import json
from typing import Any


def _unit_id(unit: Any) -> str:
    return str(getattr(unit, "unit_id", "") or "").strip()


def _depends_on(unit: Any) -> tuple[str, ...]:
    return tuple(str(item or "").strip() for item in getattr(unit, "depends_on", ()) if str(item or "").strip())


def _label(unit: Any) -> str:
    return str(getattr(unit, "label", "") or "").strip()


def _parallel_safe(unit: Any) -> bool:
    return bool(getattr(unit, "parallel_safe", False))


def _stable_idempotency_key(*, prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{prefix}::sha256:{hashlib.sha256(encoded).hexdigest()}"


def _unit_idempotency_key(unit: Any) -> str:
    return _stable_idempotency_key(
        prefix="repair-unit",
        payload={
            "unit_id": _unit_id(unit),
            "label": _label(unit),
            "parallel_safe": _parallel_safe(unit),
            "depends_on": list(_depends_on(unit)),
        },
    )


def _execution_policy() -> dict[str, Any]:
    return {
        "mode": "quality_preserving_fast_lane",
        "gate_relaxation_allowed": False,
        "requires_publication_gate_replay": True,
        "requires_authority_surface_refresh": True,
    }


def _quality_gate_policy() -> dict[str, Any]:
    return {
        "mode": "quality_preserving_fast_lane",
        "gate_relaxation_allowed": False,
        "requires_publication_gate_replay": True,
        "requires_authority_surface_refresh": True,
        "requires_successful_replay_before_completion": True,
    }


def _replay_requirements() -> dict[str, bool]:
    return {
        "publication_gate_replay_required": True,
        "controller_apply_required": True,
        "replay_after_action_batches": True,
        "quality_gate_relaxation_allowed": False,
    }


def _checkpoint_requirements() -> dict[str, Any]:
    return {
        "before_execute": [
            "publication_eval/latest.json",
            "gate_report",
            "latest_gate_clearing_batch",
        ],
        "after_each_action_batch": [
            "unit_results",
            "unit_fingerprints",
            "batch_status",
        ],
        "after_replay": [
            "gate_replay_step",
            "publication_work_unit_lifecycle",
            "current_package_freshness_proof",
        ],
        "requires_durable_record": True,
    }


def _dependency_dag(repair_units: list[Any]) -> dict[str, Any]:
    units_by_id = {_unit_id(unit): unit for unit in repair_units if _unit_id(unit)}
    nodes = [
        {
            "unit_id": unit_id,
            "label": _label(unit),
            "parallel_safe": _parallel_safe(unit),
            "idempotency_key": _unit_idempotency_key(unit),
        }
        for unit_id, unit in units_by_id.items()
    ]
    edges = [
        {
            "from_unit_id": dependency_id,
            "to_unit_id": unit_id,
        }
        for unit_id, unit in units_by_id.items()
        for dependency_id in _depends_on(unit)
        if dependency_id in units_by_id
    ]
    return {"nodes": nodes, "edges": edges}


def _dispatch_batches(waves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for wave in waves:
        parallel_ids = list(wave.get("parallel_unit_ids") or [])
        sequential_ids = list(wave.get("sequential_unit_ids") or [])
        if parallel_ids:
            batches.append(
                {
                    "batch_index": len(batches) + 1,
                    "dispatch_mode": "parallel",
                    "unit_ids": parallel_ids,
                    "quality_gate_relaxation_allowed": False,
                }
            )
        if sequential_ids:
            batches.append(
                {
                    "batch_index": len(batches) + 1,
                    "dispatch_mode": "sequential",
                    "unit_ids": sequential_ids,
                    "quality_gate_relaxation_allowed": False,
                }
            )
    return batches


def _action_batches(*, dispatch_batches: list[dict[str, Any]], units_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    batch_index_by_unit_id = {
        unit_id: int(batch["batch_index"])
        for batch in dispatch_batches
        for unit_id in list(batch.get("unit_ids") or [])
    }
    action_batches: list[dict[str, Any]] = []
    for batch in dispatch_batches:
        batch_index = int(batch["batch_index"])
        unit_ids = [unit_id for unit_id in list(batch.get("unit_ids") or []) if unit_id in units_by_id]
        depends_on_batch_indices = sorted(
            {
                dependency_batch_index
                for unit_id in unit_ids
                for dependency_id in _depends_on(units_by_id[unit_id])
                if (dependency_batch_index := batch_index_by_unit_id.get(dependency_id)) is not None
                and dependency_batch_index != batch_index
            }
        )
        unit_idempotency_keys = {unit_id: _unit_idempotency_key(units_by_id[unit_id]) for unit_id in unit_ids}
        payload = {
            "batch_index": batch_index,
            "dispatch_mode": str(batch.get("dispatch_mode") or ""),
            "unit_ids": unit_ids,
            "depends_on_batch_indices": depends_on_batch_indices,
            "unit_idempotency_keys": unit_idempotency_keys,
        }
        action_batches.append(
            {
                **payload,
                "quality_gate_relaxation_allowed": False,
                "idempotency_key": _stable_idempotency_key(prefix="action-batch", payload=payload),
            }
        )
    return action_batches


def _fast_lane_execution_manifest(
    *,
    status: str,
    repair_units: list[Any],
    dispatch_batches: list[dict[str, Any]],
) -> dict[str, Any]:
    units_by_id = {_unit_id(unit): unit for unit in repair_units if _unit_id(unit)}
    dependency_dag = _dependency_dag(repair_units)
    action_batches = _action_batches(dispatch_batches=dispatch_batches, units_by_id=units_by_id)
    return {
        "manifest_type": "gate_clearing_fast_lane_execution_plan",
        "status": status,
        "quality_gate_policy": _quality_gate_policy(),
        "replay_requirements": _replay_requirements(),
        "checkpoint_requirements": _checkpoint_requirements(),
        "dependency_dag": dependency_dag,
        "action_batches": action_batches,
    }


def build_repair_unit_execution_plan(repair_units: list[Any]) -> dict[str, Any]:
    units_by_id = {_unit_id(unit): unit for unit in repair_units if _unit_id(unit)}
    pending_ids = [_unit_id(unit) for unit in repair_units if _unit_id(unit)]
    completed_ids: set[str] = set()
    waves: list[dict[str, Any]] = []
    critical_path_depth = 0
    while pending_ids:
        ready_ids = [
            unit_id
            for unit_id in pending_ids
            if all(dependency_id in completed_ids or dependency_id not in units_by_id for dependency_id in _depends_on(units_by_id[unit_id]))
        ]
        if not ready_ids:
            dispatch_batches = _dispatch_batches(waves)
            return {
                "status": "unresolved_dependency_graph",
                "wave_count": len(waves),
                "waves": waves,
                "execution_policy": _execution_policy(),
                "dispatch_batches": dispatch_batches,
                "fast_lane_execution_manifest": _fast_lane_execution_manifest(
                    status="unresolved_dependency_graph",
                    repair_units=repair_units,
                    dispatch_batches=dispatch_batches,
                ),
                "unresolved_unit_ids": pending_ids,
            }
        parallel_ids = [unit_id for unit_id in ready_ids if bool(getattr(units_by_id[unit_id], "parallel_safe", False))]
        sequential_ids = [
            unit_id
            for unit_id in ready_ids
            if unit_id not in set(parallel_ids)
        ]
        wave_ids = parallel_ids + sequential_ids
        critical_path_depth += 1
        waves.append(
            {
                "wave_index": len(waves) + 1,
                "parallel_unit_ids": parallel_ids,
                "sequential_unit_ids": sequential_ids,
                "unit_ids": wave_ids,
            }
        )
        completed_ids.update(wave_ids)
        pending_ids = [unit_id for unit_id in pending_ids if unit_id not in completed_ids]
    dispatch_batches = _dispatch_batches(waves)
    return {
        "status": "planned",
        "wave_count": len(waves),
        "parallel_wave_count": sum(1 for wave in waves if wave["parallel_unit_ids"]),
        "parallel_unit_count": sum(len(wave["parallel_unit_ids"]) for wave in waves),
        "sequential_unit_count": sum(len(wave["sequential_unit_ids"]) for wave in waves),
        "critical_path_depth": critical_path_depth,
        "execution_policy": _execution_policy(),
        "dispatch_batches": dispatch_batches,
        "fast_lane_execution_manifest": _fast_lane_execution_manifest(
            status="planned",
            repair_units=repair_units,
            dispatch_batches=dispatch_batches,
        ),
        "waves": waves,
    }
