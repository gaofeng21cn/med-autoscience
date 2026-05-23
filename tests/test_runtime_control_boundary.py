from __future__ import annotations

import ast
from pathlib import Path


RUNTIME_WATCH_HELPERS = (
    Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan.py"),
    Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/managed_recovery.py"),
    Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/control_plane_gate.py"),
    Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/gate_specificity.py"),
)
FORBIDDEN_CONTROLLER_TARGETS = (
    "med_autoscience.controllers.domain_status_projection",
    "med_autoscience.controllers.study_outer_loop",
)


def _string_literals(tree: ast.AST) -> list[str]:
    return [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def test_domain_health_diagnostic_execution_helpers_do_not_import_router_or_outer_loop() -> None:
    for path in RUNTIME_WATCH_HELPERS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        for target in FORBIDDEN_CONTROLLER_TARGETS:
            assert target not in imported, f"{path} imports {target}"
            assert target not in _string_literals(tree), f"{path} dynamically references {target}"


def test_runtime_scan_uses_runtime_control_ports_for_controller_execution() -> None:
    path = Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "run_domain_health_diagnostic_for_runtime"]
    assert len(functions) == 1
    arg_names = {arg.arg for arg in functions[0].args.kwonlyargs}
    assert "runtime_control_ports" in arg_names
