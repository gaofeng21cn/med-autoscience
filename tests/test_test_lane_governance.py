from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from tests.standard_agent_purity_helpers import (
    assert_standard_agent_purity_boundary,
)


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _test_lane_manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_meta_lane_does_not_rerun_family_or_architecture_owner_tests() -> None:
    makefile = _read("Makefile")
    conftest = _read("tests/conftest.py")

    meta_block = makefile.split("test-meta:", maxsplit=1)[1].split("\ntest-display:", maxsplit=1)[0]
    assert "scripts/run-pytest-clean.sh -q -m meta" in meta_block
    assert "ARCH_OWNER_BOUNDARY_TEST" not in meta_block
    meta_files_block = conftest.split("META_FILES = {", maxsplit=1)[1].split("\n}", maxsplit=1)[0]
    assert "tests/test_dev_preflight.py" not in meta_files_block
    assert "tests/test_dev_preflight_contract.py" not in meta_files_block


def test_test_lane_manifest_paths_exist_and_are_used_by_makefile() -> None:
    manifest = _test_lane_manifest()
    makefile = _read("Makefile")

    for lane in manifest["lanes"].values():
        for path in lane.get("paths", []):
            assert (REPO_ROOT / path).exists(), path
    for lane_id, lane in manifest["focused_lanes"].items():
        for key in ("paths", "docs"):
            for path in lane.get(key, []):
                assert (REPO_ROOT / path).exists(), f"{lane_id} references missing {key}: {path}"
    assert " ".join(manifest["lanes"]["smoke"]["paths"]) in makefile


def test_functional_privatization_audit_exposes_standard_agent_purity_guard() -> None:
    audit = json.loads(_read("contracts/functional_privatization_audit.json"))
    boundary = audit["functional_consumer_boundary"]

    assert audit["classification_buckets"] == [
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    ]
    assert audit["standard_agent_purity_policy"] == (
        "default_surfaces_must_remain_standard_agent_purity_guarded"
    )
    assert_standard_agent_purity_boundary(boundary)


def test_smoke_lane_files_do_not_perform_subprocess_or_repo_root_writes() -> None:
    manifest = _test_lane_manifest()

    for path in manifest["lanes"]["smoke"]["paths"]:
        tree = ast.parse(_read(path), filename=path)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert "subprocess" not in imported_modules | imported_from_modules
        assert ".sentrux" not in _read(path)


def test_mas_entry_boundary_lane_freezes_sidecar_skill_mcp_and_docs_contract() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-entry-boundary"]

    assert lane["kind"] == "focused_mas_entry_docs_contract_gate"
    assert lane["overlap_policy"] == "allowed_with_regression"
    assert lane["authority_boundary"] == "entry_projection_and_controlled_sidecar_bridge_no_study_truth_authority"
    assert lane["implementation_status"] == "landed_docs_contract"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path

    assert lane["docs"] == [
        "docs/status.md",
        "docs/architecture.md",
        "docs/runtime/control/controllers.md",
    ]
    assert lane["docs_boundary"] == {
        "markdown_prose_as_machine_truth_allowed": False,
        "docs_role": "human_navigation_and_boundary_explanation_only",
        "contract_lane": "focused_lanes.mas-entry-boundary",
    }

    framework = lane["family_runtime_framework"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert "legacy_optional_providers" not in framework
    assert framework["optional_executor_adapters"] == [
        {
            "adapter_id": "hermes_agent",
            "display_name": "Hermes-Agent",
            "classification": "explicit_optional_executor_adapter",
            "default_provider": False,
        }
    ]
    assert framework["role"] == "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport"
    assert set(framework["not_authority_for"]) == {
        "study_truth",
        "publication_quality",
        "quality_gate",
        "artifact_authority",
        "paper_package",
    }

    sidecar = lane["sidecar_bridge"]
    assert sidecar["export_command"] == "medautosci sidecar export --profile <profile> --format json"
    assert sidecar["dispatch_command"] == "medautosci sidecar dispatch --task <task.json> --format json"
    assert sidecar["export_surface_kind"] == "mas_family_sidecar_export"
    assert sidecar["dispatch_receipt_surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert sidecar["bridge_policy"] == "controlled_bridge_to_mas_owner_surface"
    assert sidecar["allowed_bridge_writes"] == [
        "artifacts/runtime/opl_family_sidecar/dispatch_receipts/*.json",
    ]
    assert "domain_route/owner-handoff" in sidecar["allowed_task_kinds"]
    assert "notification/receipt" in sidecar["allowed_task_kinds"]

    projections = lane["entry_projection_surfaces"]
    assert projections["action_catalog"] == "med_autoscience.action_catalog family_action_catalog"
    assert projections["mcp"] == "med_autoscience.mcp_server build_tool_manifest action_catalog_projection"
    assert projections["skill"] == "plugins/mas/skills/mas/SKILL.md"
    assert projections["plugin_manifest"] == "plugins/mas/.codex-plugin/plugin.json"
    assert (REPO_ROOT / projections["skill"]).exists()
    assert (REPO_ROOT / projections["plugin_manifest"]).exists()
    assert lane["projection_only_surfaces"] == [
        "MCP tool descriptors",
        "action_catalog projections",
        "OPL generated Skill descriptor targeting MAS domain entry",
        "product-entry manifest domain action intent metadata",
    ]
    assert lane["truth_owner"] == "MedAutoScience"
    assert set(lane["forbidden_authority_writes"]) >= {
        "study_truth",
        "progress_projection",
        "domain_health_diagnostic",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "paper/current_package",
        "manuscript/current_package",
        "quality_ready",
        "publication_ready",
        "submission_ready",
        "artifact_gate_override",
    }


def test_mas_functional_consumer_lane_freezes_generic_surface_handoff() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-functional-consumer-followthrough"]

    assert lane["kind"] == "focused_mas_functional_consumer_boundary_gate"
    assert lane["authority_boundary"] == "opl_consumed_generic_surfaces_mas_domain_authority_pack_only"
    assert lane["implementation_status"] == "landed_functional_consumer_standard_agent_purity_guard"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"
    assert lane["generic_surface_owner"] == "one-person-lab"
    assert lane["default_scheduler_owner"] == "opl_current_control_state"
    assert lane["live_soak_required_for_this_lane"] is False

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path

    assert lane["mas_does_not_own"] == [
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
    assert set(lane["mas_domain_authority_surfaces"]) == {
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

    consumer_migration = importlib.import_module(
        "med_autoscience.controllers.opl_unique_control_plane_boundary_parts.consumer_migration"
    )
    runtime_boundary = consumer_migration.build_functional_consumer_boundary()

    assert runtime_boundary["declarative_pack_compiler_input"] == lane[
        "declarative_pack_compiler_input"
    ]
    assert runtime_boundary["generated_surface_handoff"] == lane["generated_surface_handoff"]
    assert runtime_boundary["minimal_authority_function_manifest"] == lane[
        "minimal_authority_function_manifest"
    ]
    assert runtime_boundary["functional_surface_classification"] == lane[
        "functional_surface_classification"
    ]
    assert runtime_boundary["functional_module_inventory_summary"] == lane[
        "functional_module_inventory_summary"
    ]
    assert runtime_boundary["functional_followthrough_gap_summary"] == lane[
        "functional_followthrough_gap_summary"
    ]
    assert runtime_boundary["standard_agent_purity_guard"] == lane["standard_agent_purity_guard"]
    assert runtime_boundary["opl_functional_harness_consumer_coverage"] == lane[
        "opl_functional_harness_consumer_coverage"
    ]
    assert runtime_boundary["domain_authority_refs_index_role"] == lane[
        "domain_authority_refs_index_role"
    ]

    classification = lane["functional_surface_classification"]
    assert set(classification) == {
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    }
    assert set(classification) == set(lane["functional_module_inventory_classification_allowed_values"])

    inventory = runtime_boundary["functional_module_inventory"]
    assert lane["functional_module_inventory_expected_count"] == 15
    assert len(inventory) == 15
    assert sorted(item["module_id"] for item in inventory) == sorted(
        lane["functional_module_inventory_expected_modules"]
    )
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert "local_launchd_scheduler_install_path" not in inventory_by_id
    assert "workspace_local_watch_service_wrappers" not in inventory_by_id
    assert "domain_health_diagnostic_loop_shell" not in inventory_by_id
    assert inventory_by_id["domain_authority_refs_index"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "src/med_autoscience/opl_domain_pack/",
        "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
    ]
    assert set(inventory_by_id["domain_authority_refs_index"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_runtime_lifecycle_owner",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "domain_authority_refs"
    assert inventory_by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert inventory_by_id["artifact_authority"]["migration_action"] == "authority_stays_in_mas"

    summary = runtime_boundary["functional_module_inventory_summary"]
    assert summary["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "domain_authority_refs": 5,
        "minimal_authority_function": 3,
    }
    assert summary["classification_gap_count"] == 0
    assert summary["functional_structure_gap_count"] == 0
    assert summary["active_private_generic_residue_count"] == 0

    purity = runtime_boundary["standard_agent_purity"]
    assert purity["status"] == "pure_standard_agent_active"
    assert purity["active_private_generic_residue_count"] == 0
    assert purity["default_caller_count"] == 0
    assert purity["runtime_package_residue_count"] == 0
    assert purity["active_compatibility_aliases"] == []
    assert purity["history_detail_in_default_read_model"] is False
    assert purity["domain_projection_policy"] == (
        "refs_receipts_blockers_only_no_body_verdict_or_blob"
    )
    assert "mas_owned_generic_queue" in purity["forbidden_active_claims"]

    followthrough = runtime_boundary["functional_followthrough_gap_summary"]
    assert followthrough["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough["classification_gap_count"] == 0
    assert followthrough["functional_structure_gap_count"] == 0
    assert followthrough["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough["remaining_functional_followthrough_gates"] == []
    assert "standard_agent_purity_guard" in followthrough[
        "closed_functional_structure_gate_ids"
    ]
    assert "standard_agent_purity_guard" in followthrough["closed_functional_structure_gate_ids"]
    assert followthrough["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]

    assert lane["standard_agent_purity_guard"] == {
        "status": "standard_agent_purity_guard",
        "default_caller_count": 0,
        "default_manager": "opl",
        "runtime_package_residue_count": 0,
        "active_compatibility_aliases": [],
        "proof_items": [
            "standard_agent_purity.active_private_generic_residue_count=0",
            "standard_agent_purity.default_caller_count=0",
            "standard_agent_purity.domain_projection_policy=refs_receipts_blockers_only_no_body_verdict_or_blob",
        ],
    }
    assert "standard_agent_purity" in lane
    assert lane["standard_agent_purity_guard_required"] == [
        "standard_agent_purity.active_private_generic_residue_count=0",
        "standard_agent_purity.default_caller_count=0",
        "standard_agent_purity.active_compatibility_aliases=[]",
        "standard_agent_purity.history_detail_in_default_read_model=false",
        "sidecar_exports_standard_agent_purity",
        "product_entry_manifest_exports_standard_agent_purity",
        "observability_export_consumed_as_refs_only",
        "focused_tests_green",
    ]

    assert lane["required_projection_surfaces"] == [
        "product_entry_manifest.functional_consumer_boundary",
        "product_entry_manifest.functional_consumer_boundary.standard_agent_purity",
        "product_entry_manifest.functional_consumer_boundary.declarative_pack_compiler_input",
        "product_entry_manifest.functional_consumer_boundary.generated_surface_handoff",
        "product_entry_manifest.functional_consumer_boundary.minimal_authority_function_manifest",
        "sidecar_export.functional_consumer_boundary",
        "sidecar_export.functional_consumer_boundary.standard_agent_purity",
        "sidecar_export.functional_consumer_boundary.declarative_pack_compiler_input",
        "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
        "sidecar_export.functional_consumer_boundary.minimal_authority_function_manifest",
        "opl_unique_control_plane_boundary.consumer_migration.functional_consumer_boundary",
        "family_contract_adoption.runtime_observability_export",
    ]
    assert set(lane["forbidden_runtime_regressions"]) == {
        "mas_default_generic_scheduler",
        "mas_resident_generic_daemon",
        "mas_owned_generic_queue",
        "mas_owned_attempt_ledger",
        "mas_generic_transition_runner",
        "mas_generic_workbench_shell",
    }
