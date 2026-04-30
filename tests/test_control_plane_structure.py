from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CONTROL_PLANE_MODULES = (
    "src/med_autoscience/controllers/mds_worker_activity.py",
    "src/med_autoscience/controllers/runtime_supervision.py",
    "src/med_autoscience/controllers/runtime_watch_parts/managed_wakeup.py",
    "src/med_autoscience/controllers/runtime_watch_recovery_policy.py",
    "src/med_autoscience/controllers/study_outer_loop_parts/runtime_refs.py",
    "src/med_autoscience/controllers/study_progress_parts/projection.py",
    "src/med_autoscience/controllers/study_progress_parts/runtime_efficiency.py",
    "src/med_autoscience/controllers/study_progress_parts/runtime_liveness_projection.py",
)

ALLOWED_COMPAT_ALIAS_FUNCTIONS = {
    "_payload_active_run_id",
    "_payload_runtime_liveness_status",
    "_payload_strict_live",
    "_probe_has_live_worker",
    "_runtime_status_active_run_id",
    "_status_active_run_id",
    "_supervision_active_run_id",
}


def _source(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _function_name_for_node(tree: ast.AST, target: ast.AST) -> str | None:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    current = target
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return None


def _string_constants(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


def _is_live_comparison(node: ast.Compare) -> bool:
    constants = _string_constants(node)
    return "live" in constants and (
        "runtime_liveness_status" in constants
        or "runtime_liveness_audit" in constants
        or "status" in constants
    )


def test_control_plane_modules_depend_on_canonical_fact_resolver() -> None:
    for relative_path in CONTROL_PLANE_MODULES:
        source = _source(relative_path)
        assert "control_plane_facts" in source or "resolve_control_plane_facts" in source, relative_path


def test_control_plane_modules_do_not_reparse_strict_live_directly() -> None:
    violations: list[str] = []
    for relative_path in CONTROL_PLANE_MODULES:
        tree = ast.parse(_source(relative_path), filename=relative_path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare) or not _is_live_comparison(node):
                continue
            function_name = _function_name_for_node(tree, node)
            if function_name in ALLOWED_COMPAT_ALIAS_FUNCTIONS:
                continue
            violations.append(f"{relative_path}:{node.lineno}")

    assert violations == []


def test_control_plane_fact_resolution_stays_in_single_source_module() -> None:
    for relative_path in CONTROL_PLANE_MODULES:
        source = _source(relative_path)
        assert "runtime_liveness_status = (" not in source, relative_path
        assert "runtime_liveness_audit.get(\"active_run_id\")" not in source, relative_path
        assert "runtime_audit.get(\"active_run_id\")" not in source, relative_path
