from __future__ import annotations

from typing import Any


def _unit_id(unit: Any) -> str:
    return str(getattr(unit, "unit_id", "") or "").strip()


def _depends_on(unit: Any) -> tuple[str, ...]:
    return tuple(str(item or "").strip() for item in getattr(unit, "depends_on", ()) if str(item or "").strip())


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
            return {
                "status": "unresolved_dependency_graph",
                "wave_count": len(waves),
                "waves": waves,
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
    return {
        "status": "planned",
        "wave_count": len(waves),
        "parallel_wave_count": sum(1 for wave in waves if wave["parallel_unit_ids"]),
        "parallel_unit_count": sum(len(wave["parallel_unit_ids"]) for wave in waves),
        "sequential_unit_count": sum(len(wave["sequential_unit_ids"]) for wave in waves),
        "critical_path_depth": critical_path_depth,
        "waves": waves,
    }
