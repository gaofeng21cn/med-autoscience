from __future__ import annotations

from importlib import import_module as _import_module

from .shared import _LazyModuleProxy

_LAZY_MODULES = (
    ".workspace_cockpit.state_and_study_items",
    ".workspace_cockpit.cockpit_payload",
    ".workspace_cockpit.cockpit_markdown",
    ".workspace_cockpit.launch_surface",
)


medical_paper_readiness = _LazyModuleProxy(
    lambda: _import_module("med_autoscience.controllers.medical_paper_readiness")
)
open_auto_research_projection = _LazyModuleProxy(
    lambda: _import_module("med_autoscience.controllers.open_auto_research_projection")
)


def _load_workspace_surface_name(name: str):
    for module_name in _LAZY_MODULES:
        module = _import_module(module_name, __package__)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(name)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return _load_workspace_surface_name(name)


def read_workspace_cockpit(*args, **kwargs):
    return _load_workspace_surface_name("read_workspace_cockpit")(*args, **kwargs)


def render_workspace_cockpit_markdown(*args, **kwargs):
    return _load_workspace_surface_name("render_workspace_cockpit_markdown")(*args, **kwargs)


def launch_study(*args, **kwargs):
    return _load_workspace_surface_name("launch_study")(*args, **kwargs)


def render_launch_study_markdown(*args, **kwargs):
    return _load_workspace_surface_name("render_launch_study_markdown")(*args, **kwargs)


def _attention_queue(*args, **kwargs):
    return _load_workspace_surface_name("_attention_queue")(*args, **kwargs)


def _autonomy_soak_focus(*args, **kwargs):
    return _load_workspace_surface_name("_autonomy_soak_focus")(*args, **kwargs)


def _gate_clearing_followthrough_focus(*args, **kwargs):
    return _load_workspace_surface_name("_gate_clearing_followthrough_focus")(*args, **kwargs)


def _mainline_snapshot(*args, **kwargs):
    return _load_workspace_surface_name("_mainline_snapshot")(*args, **kwargs)


def _operator_status_summary(*args, **kwargs):
    return _load_workspace_surface_name("_operator_status_summary")(*args, **kwargs)


def _quality_execution_focus(*args, **kwargs):
    return _load_workspace_surface_name("_quality_execution_focus")(*args, **kwargs)


def _quality_repair_followthrough_focus(*args, **kwargs):
    return _load_workspace_surface_name("_quality_repair_followthrough_focus")(*args, **kwargs)


def _quality_review_followthrough_focus(*args, **kwargs):
    return _load_workspace_surface_name("_quality_review_followthrough_focus")(*args, **kwargs)


def _same_line_route_focus(*args, **kwargs):
    return _load_workspace_surface_name("_same_line_route_focus")(*args, **kwargs)


def _study_item(*args, **kwargs):
    return _load_workspace_surface_name("_study_item")(*args, **kwargs)


def _workspace_operator_brief(*args, **kwargs):
    return _load_workspace_surface_name("_workspace_operator_brief")(*args, **kwargs)


def build_medical_paper_research_loop(*args, **kwargs):
    return _load_workspace_surface_name("build_medical_paper_research_loop")(*args, **kwargs)


def build_v4_operations_dashboard(*args, **kwargs):
    return _load_workspace_surface_name("build_v4_operations_dashboard")(*args, **kwargs)


def workspace_medical_paper_ops_health(*args, **kwargs):
    return _load_workspace_surface_name("workspace_medical_paper_ops_health")(*args, **kwargs)


def workspace_medical_paper_research_loop(*args, **kwargs):
    return _load_workspace_surface_name("workspace_medical_paper_research_loop")(*args, **kwargs)


def workspace_v4_operations_state(*args, **kwargs):
    return _load_workspace_surface_name("workspace_v4_operations_state")(*args, **kwargs)


__all__ = [
    "read_workspace_cockpit",
    "render_workspace_cockpit_markdown",
    "launch_study",
    "render_launch_study_markdown",
    "_attention_queue",
    "_autonomy_soak_focus",
    "_gate_clearing_followthrough_focus",
    "_mainline_snapshot",
    "_operator_status_summary",
    "_quality_execution_focus",
    "_quality_repair_followthrough_focus",
    "_quality_review_followthrough_focus",
    "_same_line_route_focus",
    "_study_item",
    "_workspace_operator_brief",
    "build_medical_paper_research_loop",
    "build_v4_operations_dashboard",
    "medical_paper_readiness",
    "open_auto_research_projection",
    "workspace_medical_paper_ops_health",
    "workspace_medical_paper_research_loop",
    "workspace_v4_operations_state",
]
