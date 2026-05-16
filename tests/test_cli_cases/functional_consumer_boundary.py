from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_sidecar_export_projects_functional_consumer_boundary(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    boundary = payload["functional_consumer_boundary"]
    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert set(boundary["mas_retains"]) >= {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "owner_receipt",
        "safe_action_refs",
    }
    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["coverage_items"] == [
        "refs_only_memory_writeback_chain",
        "queue_stage_attempt_typed_closeout",
        "generic_transition_runner",
        "restart_dead_letter_repair_human_gate_state_chain",
    ]
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    assert coverage["refs_only_memory_writeback_chain"]["body_included"] is False
    assert coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"] is False
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 18
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert set(inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "domain_thin_adapter"
    assert inventory_by_id["artifact_authority"]["cannot_absorb_reason"] == (
        "Canonical manuscript/package mutation and submission authority are MAS artifact authority."
    )
    assert inventory_by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert inventory_by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert boundary["no_active_caller_proof"]["default_caller_count"] == 0
    assert boundary["no_active_caller_proof"]["default_manager"] == "opl"
    assert "workspace_bootstrap_manager_is_opl" in boundary["no_active_caller_proof"]["proof_items"]
    assert boundary["legacy_local_scheduler_cleanup_only_proof"]["default_bootstrap_exposes_local_install"] is False
