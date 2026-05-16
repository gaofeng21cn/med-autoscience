from __future__ import annotations

import importlib
from pathlib import Path

from .shared import make_profile


def test_product_entry_manifest_exposes_functional_consumer_boundary(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    boundary = manifest["functional_consumer_boundary"]

    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["status"] == "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack"
    assert boundary["consumer_role"] == "domain_authority_pack_thin_program_surface"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert boundary["no_active_caller_required"] is True
    assert boundary["mas_does_not_own"] == [
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_transition_runner",
        "generic_workbench",
        "generic_memory_locator",
        "generic_artifact_lifecycle",
        "generic_observability",
    ]
    assert set(boundary["mas_retains"]) == {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "domain_transition_table",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }
    classification = boundary["functional_surface_classification"]
    assert classification["A_opl_owned_mas_consumes"] == [
        "runtime_lifecycle_sqlite_reference_adapter",
        "paper_work_unit_outbox_index",
        "runtime_storage_maintenance",
        "workspace_source_intake_shell",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
        "workbench_portal_generic_shell",
        "terminal_attach_transport",
        "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert set(classification["B_mas_domain_authority"]) == {
        "study_truth",
        "study_runtime_status",
        "runtime_watch_domain_health",
        "publication_quality_verdict",
        "ai_reviewer_workflow",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "domain_transition_table",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "typed_blocker",
        "safe_action_refs",
    }
    assert set(classification["C_retire_when_replaced_or_uncalled"]) == {
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    }
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 18
    by_id = {item["module_id"]: item for item in inventory}
    lifecycle_item = by_id["runtime_lifecycle_sqlite_reference_adapter"]
    assert lifecycle_item["code_paths"] == [
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert lifecycle_item["active_caller_status"] == "refs_only_domain_sidecar_adapter_active"
    assert lifecycle_item["migration_action"] == (
        "consume_opl_family_runtime_lifecycle_index_and_keep_mas_domain_receipt_refs_only"
    )
    assert set(lifecycle_item["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert by_id["runtime_supervisor_scan_consume_dispatch_shell"]["migration_action"] == (
        "move generic scan consume dispatch reconcile loop to OPL runtime manager"
    )
    assert by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert by_id["local_launchd_scheduler_install_path"]["active_caller_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["trigger_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["write_install_proof_allowed"] is False
    assert by_id["workspace_local_watch_service_wrappers"]["tombstone_required"] is True
    lifecycle_role = boundary["runtime_lifecycle_sqlite_role"]
    assert lifecycle_role["classification"] == "A_opl_owned_mas_consumes"
    assert lifecycle_role["current_mas_role"] == "domain_sidecar_index_reference_adapter"
    assert lifecycle_role["authority"] == "refs_only_index_not_generic_persistence_engine"
    assert lifecycle_role["owner"] == "one-person-lab"
    assert lifecycle_role["mas_may_index_domain_receipts"] is True
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_lifecycle_index_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False
    assert set(lifecycle_role["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert lifecycle_role["replacement_expectation"]["expected_replacements"] == [
        "opl_runtime_lifecycle_index_contract",
        "opl_artifact_lifecycle_storage_audit_shell",
        "opl_app_workbench_shell",
        "opl_terminal_attach_transport",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ]
    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["status"] == "landed_domain_authority_pack_consumer"
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
    assert (
        coverage["refs_only_memory_writeback_chain"]["opl_can_accept_or_reject_writeback"]
        is False
    )
    assert coverage["queue_stage_attempt_typed_closeout"]["queue_completion_is_paper_closure"] is False
    assert (
        coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"]
        is False
    )
    assert (
        coverage["restart_dead_letter_repair_human_gate_state_chain"][
            "state_chain_completion_is_publication_ready"
        ]
        is False
    )
    assert "product_entry_manifest.functional_consumer_boundary" in boundary["proof_surfaces"]
    assert "mas_owned_generic_queue" in boundary["forbidden_regressions"]
    assert boundary["no_active_caller_proof"] == {
        "status": "default_surfaces_use_opl_cleanup_only_local_path",
        "default_caller_count": 0,
        "default_manager": "opl",
        "replacement_owner_surface": "opl_provider_runtime_manager",
        "legacy_local_install_path_role": "explicit_cleanup_diagnostic_only",
        "cleanup_only_commands": [
            "runtime-supervision-status --profile <profile> --manager local",
            "runtime-remove-supervision --profile <profile> --manager local",
        ],
        "forbidden_default_callers": [
            "cli_default_local_scheduler_install",
            "workspace_bootstrap_local_scheduler_install",
            "product_entry_local_scheduler_install",
            "sidecar_local_scheduler_install",
            "mcp_local_scheduler_install",
        ],
        "proof_items": [
            "cli_default_manager_is_opl",
            "workspace_bootstrap_manager_is_opl",
            "product_entry_consumes_opl_replacement_projection",
            "sidecar_exports_functional_boundary_no_generic_owner",
            "local_scheduler_ensure_returns_retired_cleanup_only",
            "local_scheduler_remove_is_explicit_cleanup_only",
            "local_scheduler_install_proof_generation_forbidden",
        ],
    }
    cleanup_only = boundary["legacy_local_scheduler_cleanup_only_proof"]
    assert cleanup_only["install_allowed"] is False
    assert cleanup_only["trigger_allowed"] is False
    assert cleanup_only["write_install_proof_allowed"] is False
    assert cleanup_only["default_cli_exposes_local_install"] is False
    assert cleanup_only["default_bootstrap_exposes_local_install"] is False
