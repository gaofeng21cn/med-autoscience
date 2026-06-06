from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]

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


def test_stage_native_compensation_tail_retirement_requires_same_work_unit_live_evidence() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    gate = contract["stage_native_compensation_retirement_gate"]

    assert gate["status"] == "active_delete_gate"
    assert gate["physical_retirement_allowed_before_gate"] is False
    assert gate["required_live_evidence"] == [
        "opl_stage_run_status",
        "mas_owner_receipt_or_typed_blocker",
        "stage_manifest",
        "study_progress_current_owner_delta",
    ]
    assert gate["same_work_unit_consistency_keys"] == [
        "study_id",
        "stage_id",
        "work_unit_id_or_fingerprint",
        "stage_run_id",
        "generation",
        "source_fingerprint",
        "idempotency_key",
    ]

    retirement = gate["retirement_allowed_when"]
    assert retirement["all_required_live_evidence_present"] is True
    assert retirement["all_required_live_evidence_points_to_same_work_unit"] is True
    assert retirement["owner_answer_has_closeout_binding"] is True
    assert retirement["opportunistic_read_model_refresh_counts"] is False
    assert retirement["provider_completion_counts"] is False
    assert retirement["stage_folder_file_presence_counts"] is False
    assert set(gate["allowed_before_gate"]) == {
        "tombstone_ref",
        "provenance_ref",
        "delete_gate_context",
        "stale_superseded_diagnostic",
    }
    assert {
        "delete_or_disable_current_owner_route_callable",
        "delete_or_disable_current_materializer_path",
        "delete_or_disable_current_dispatch_path",
        "claim_compensation_chain_physically_retired",
        "claim_publication_ready_or_package_ready",
    } <= set(gate["forbidden_until_gate_passes"])
