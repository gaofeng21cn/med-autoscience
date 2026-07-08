from __future__ import annotations

from typing import Any, Mapping

from .shared import _mapping_copy, _publication_supervisor_blocks_same_line_route


def build_quality_projection_surfaces(
    *,
    controller_module_surface: Mapping[str, Any] | None,
    runtime_module_surface: Mapping[str, Any],
    evaluation_module_surface: Mapping[str, Any] | None,
    task_intake_progress_override: Mapping[str, Any] | None,
    publication_supervisor_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    module_surfaces = _base_module_surfaces(
        controller_module_surface=controller_module_surface,
        runtime_module_surface=runtime_module_surface,
        evaluation_module_surface=evaluation_module_surface,
    )
    projection = _evaluation_quality_projection(evaluation_module_surface)
    if task_intake_progress_override:
        projection = _task_intake_quality_projection(task_intake_progress_override)
        _replace_eval_quality_projection(module_surfaces, projection)
    if _publication_supervisor_blocks_same_line_route(publication_supervisor_state):
        projection = {**projection, "same_line_route_truth": {}, "same_line_route_surface": {}}
        _clear_eval_same_line_route(module_surfaces)
    return {**projection, "module_surfaces": module_surfaces}


def _base_module_surfaces(
    *,
    controller_module_surface: Mapping[str, Any] | None,
    runtime_module_surface: Mapping[str, Any],
    evaluation_module_surface: Mapping[str, Any] | None,
) -> dict[str, Any]:
    module_surfaces: dict[str, Any] = {}
    if controller_module_surface is not None:
        module_surfaces["controller_charter"] = controller_module_surface
    module_surfaces["runtime"] = runtime_module_surface
    if evaluation_module_surface is not None:
        module_surfaces["eval_hygiene"] = evaluation_module_surface
    return module_surfaces


def _evaluation_quality_projection(evaluation_module_surface: Mapping[str, Any] | None) -> dict[str, Any]:
    if evaluation_module_surface is None:
        return _task_intake_quality_projection({})
    return {
        "quality_closure_truth": _mapping_copy(evaluation_module_surface.get("quality_closure_truth")),
        "quality_execution_lane": _mapping_copy(evaluation_module_surface.get("quality_execution_lane")),
        "same_line_route_truth": _mapping_copy(evaluation_module_surface.get("same_line_route_truth")),
        "same_line_route_surface": _mapping_copy(evaluation_module_surface.get("same_line_route_surface")),
    }


def _task_intake_quality_projection(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "quality_closure_truth": _mapping_copy(source.get("quality_closure_truth")),
        "quality_execution_lane": _mapping_copy(source.get("quality_execution_lane")),
        "same_line_route_truth": _mapping_copy(source.get("same_line_route_truth")),
        "same_line_route_surface": _mapping_copy(source.get("same_line_route_surface")),
    }


def _replace_eval_quality_projection(
    module_surfaces: dict[str, Any],
    projection: Mapping[str, Any],
) -> None:
    eval_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    if not eval_surface:
        return
    eval_surface["quality_closure_truth"] = projection["quality_closure_truth"] or None
    eval_surface["quality_execution_lane"] = projection["quality_execution_lane"] or None
    eval_surface["same_line_route_truth"] = projection["same_line_route_truth"] or None
    eval_surface["same_line_route_surface"] = projection["same_line_route_surface"] or None
    module_surfaces["eval_hygiene"] = eval_surface


def _clear_eval_same_line_route(module_surfaces: dict[str, Any]) -> None:
    eval_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    if not eval_surface:
        return
    eval_surface["same_line_route_truth"] = None
    eval_surface["same_line_route_surface"] = None
    module_surfaces["eval_hygiene"] = eval_surface
