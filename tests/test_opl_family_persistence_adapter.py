from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_lifecycle_store_builds_opl_family_adoption_surface_from_sidecar_refs(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    db_path = lifecycle_store.workspace_lifecycle_store_path(workspace_root)
    owner_receipt_path = study_root / "artifacts" / "runtime" / "owner_route" / "latest.json"
    dispatch_receipt_path = quest_root / "artifacts" / "runtime" / "dispatch" / "dispatch-001.json"
    surface_ref_path = study_root / "artifacts" / "runtime" / "surface_refs" / "runtime_watch.json"
    owner_receipt = {
        "surface": "domain_route_owner_route",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "idempotency_key": "route-001",
        "route_epoch": "truth-epoch-001",
        "current_owner": "runtime",
        "next_owner": "mas_controller",
        "owner_reason": "runtime_controller_redrive_required",
        "allowed_actions": ["runtime-redrive"],
        "source_refs": {"study_runtime_status": "studies/001-risk/artifacts/runtime/status/latest.json"},
    }
    dispatch_receipt = {
        "surface": "domain_owner_action_dispatch_receipt",
        "dispatch_id": "dispatch-001",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "created_at": "2026-05-06T00:01:00+00:00",
        "owner_route": owner_receipt,
        "status": "dispatched",
    }
    surface_ref = {
        "surface": "runtime_watch/latest.json",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "ref_key": "runtime_watch",
        "path": str(study_root / "artifacts" / "runtime_watch" / "latest.json"),
        "sha256": "abc123",
        "observed_at": "2026-05-06T00:02:00+00:00",
    }
    for path, payload in (
        (owner_receipt_path, owner_receipt),
        (dispatch_receipt_path, dispatch_receipt),
        (surface_ref_path, surface_ref),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lifecycle_store.record_lineage_node(
        workspace_root=workspace_root,
        db_path=db_path,
        node={
            "node_id": "quest-001",
            "node_kind": "quest",
            "object_scope": "quest",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "status": "active",
        },
    )
    lifecycle_store.record_owner_route_receipt(
        study_root=study_root,
        receipt=owner_receipt,
        receipt_path=owner_receipt_path,
        db_path=db_path,
    )
    lifecycle_store.record_dispatch_receipt(
        quest_root=quest_root,
        receipt=dispatch_receipt,
        receipt_path=dispatch_receipt_path,
        db_path=db_path,
    )
    lifecycle_store.record_surface_ref(
        object_root=study_root,
        object_scope="study",
        ref=surface_ref,
        ref_path=surface_ref_path,
        db_path=db_path,
    )

    surface = lifecycle_store.build_opl_family_adoption_surface(
        workspace_root=workspace_root,
        db_path=db_path,
    )

    assert surface["surface_kind"] == "mas_opl_family_persistence_lifecycle_owner_route_adoption"
    assert surface["workspace_root"] == str(workspace_root.resolve())
    assert surface["refs"]["sqlite_sidecar"]["db_path"] == str(db_path.resolve())
    assert surface["refs"]["source_contract"] == "contracts/opl-framework/family-contract-adoption.json"
    assert surface["refs"]["runtime_lifecycle_contract"] == (
        "med_autoscience.runtime_protocol.runtime_lifecycle_contract.runtime_lifecycle_contract"
    )
    assert surface["refs"]["authority_boundary"]["domain_truth_owner"] == "MedAutoScience"
    assert surface["refs"]["authority_boundary"]["opl_role"] == "OPL stage-runtime discovery and indexing only"
    assert surface["refs"]["authority_boundary"]["forbidden_opl_authority_surfaces"] == [
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "AI reviewer workflow",
        "paper/manuscript/current_package",
        "current_package.zip",
    ]
    assert surface["payload"]["persistence"]["sqlite_tables"]["lineage_nodes"] == 1
    assert surface["payload"]["owner_route"]["current_ticket"]["idempotency_key"] == "route-001"
    assert surface["payload"]["owner_route"]["current_ticket"]["next_owner"] == "mas_controller"
    assert surface["payload"]["owner_route"]["allowed_actions"] == ["runtime-redrive"]
    assert surface["payload"]["lifecycle"]["dispatch_receipts"][0]["dispatch_id"] == "dispatch-001"
    assert surface["payload"]["surface_refs"][0]["surface"] == "runtime_watch/latest.json"
    assert surface["payload"]["surface_refs"][0]["target_path"].endswith(
        "studies/001-risk/artifacts/runtime_watch/latest.json"
    )
    assert "publication_eval/latest.json" not in json.dumps(surface["payload"]["surface_refs"], ensure_ascii=False)


def test_product_entry_manifest_exposes_opl_family_adapter_discovery_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)

    adoption = payload["opl_family_persistence_lifecycle_owner_route_adoption"]
    assert adoption["surface_kind"] == "mas_opl_family_persistence_lifecycle_owner_route_adoption"
    assert adoption["refs"]["source_contract"] == "contracts/opl-framework/family-contract-adoption.json"
    assert adoption["refs"]["sqlite_sidecar"]["workspace_relative_path"] == "artifacts/runtime/runtime_lifecycle.sqlite"
    assert adoption["payload"]["persistence"]["source_tables"] == [
        "lineage_nodes",
        "lineage_edges",
        "workspace_allocations",
        "runtime_snapshots",
        "snapshot_file_refs",
        "revision_diffs",
        "canvas_projection",
        "study_macro_state_snapshots",
        "owner_route_receipts",
        "dispatch_receipts",
        "turn_receipts",
        "paper_work_unit_receipts",
        "surface_refs",
        "archive_refs",
        "report_index",
    ]
    assert adoption["payload"]["authority_boundary"]["publication_eval_owner"] == "MedAutoScience"
    assert adoption["payload"]["authority_boundary"]["ai_reviewer_owner"] == "MedAutoScience"
    assert adoption["payload"]["owner_route"]["source_table"] == "owner_route_receipts"
    assert payload["persistence_policy"]["surface_kind"] == "family_persistence_policy"
    assert payload["persistence_policy"]["sidecar_indexes"][0]["owner"] == "one-person-lab"
    assert payload["persistence_policy"]["sidecar_indexes"][0]["surface_role"] == (
        "domain_sidecar_reference_adapter"
    )
    assert payload["persistence_policy"]["sidecar_indexes"][0]["storage_role"] == "refs_only_sidecar_index"
    assert payload["persistence_policy"]["sidecar_indexes"][0]["ref"]["ref"] == (
        "artifacts/runtime/runtime_lifecycle.sqlite"
    )
    assert payload["lifecycle_ledger"]["surface_kind"] == "family_lifecycle_ledger"
    assert payload["lifecycle_ledger"]["actions"][0]["sha256"] == "0" * 64
    assert payload["owner_route"]["surface_kind"] == "family_owner_route"
    assert payload["owner_route"]["next_owner"] == "med-autoscience"
    provider = payload["opl_provider_ready_contract"]
    assert provider["surface_kind"] == "mas_opl_provider_ready_contract"
    assert provider["provider_topology"]["target_provider"] == "temporal"
    assert provider["provider_topology"]["provider_attempt_owner"] == "one-person-lab"
    assert provider["provider_topology"]["domain_action_owner"] == "med-autoscience"
    assert provider["provider_topology"]["provider_attempt_is_truth"] is False
    runtime_handoff = payload["runtime_transport_handoff_projection"]
    assert runtime_handoff == provider["runtime_transport_handoff_projection"]
    assert runtime_handoff["surface_kind"] == "mas_runtime_transport_handoff_projection"
    assert runtime_handoff["generic_runtime_owner"] == "one-person-lab"
    assert runtime_handoff["domain_owner"] == "med-autoscience"
    assert runtime_handoff["mas_runtime_core_role"] == (
        "domain_owner_receipt_adapter_or_standalone_diagnostic"
    )
    assert runtime_handoff["default_caller_policy"] == {
        "default_online_runtime_owner": "one-person-lab",
        "default_provider": "Temporal",
        "mas_default_scheduler_allowed": False,
        "mas_default_queue_allowed": False,
        "mas_default_attempt_ledger_allowed": False,
        "mas_default_worker_residency_allowed": False,
        "mas_default_transition_runner_allowed": False,
        "mas_default_persistence_engine_allowed": False,
        "mas_runtime_transport_active_as_generic_provider": False,
    }
    assert "generic_queue_owner" in runtime_handoff["forbidden_mas_roles"]
    assert "generic_persistence_engine_owner" in runtime_handoff["forbidden_mas_roles"]
    assert "provider_backed_family_runtime" in runtime_handoff["opl_replacement_surfaces"]
    assert "runtime_lifecycle_index" in runtime_handoff["opl_replacement_surfaces"]
    code_path_roles = {item["path"]: item for item in runtime_handoff["code_path_roles"]}
    assert code_path_roles[
        "src/med_autoscience/runtime_transport/mas_runtime_core.py"
    ]["allowed_mas_role"] == "domain_owner_receipt_adapter"
    assert code_path_roles[
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py"
    ]["current_role"] == "refs_only_sqlite_sidecar_index"
    assert provider["truth_source_precedence"]["direct_mas_skill_path"] == "authoritative"
    assert provider["truth_source_precedence"]["opl_provider_attempt_history"] == "transport_receipt_only"
    assert provider["truth_source_precedence"]["paper_progress_requires_mas_artifact_delta_or_gate_owner"] is True
    assert provider["workspace_runtime_artifact_root_locator"]["repo_root_tracks_real_artifacts"] is False
    assert provider["workspace_runtime_artifact_root_locator"]["locators"]["publication_eval"] == (
        "studies/<study_id>/artifacts/publication_eval/latest.json"
    )
    inventory = payload["opl_lifecycle_inventory"]
    assert inventory == provider["lifecycle_inventory"]
    lifecycle_index = next(
        item for item in inventory["framework_generic"] if item["item_id"] == "runtime_lifecycle_sidecar_index"
    )
    assert "reference adapter" in lifecycle_index["summary"]
    assert "generic persistence/lifecycle replacement contract" in lifecycle_index["summary"]
    assert {item["item_id"] for item in inventory["framework_generic"]} == {
        "provider_stage_attempt",
        "runtime_lifecycle_sidecar_index",
        "artifact_locator_and_retention_projection",
        "operator_projection_cache",
    }
    assert all(item["mas_exports_refs_only"] is True for item in inventory["framework_generic"])
    assert {item["item_id"] for item in inventory["mas_domain_specific"]} == {
        "study_truth_and_runtime_health",
        "publication_quality_and_ai_reviewer",
        "paper_package_and_artifact_authority",
        "owner_route_and_domain_dispatch_receipts",
    }
    assert all(item["owner"] == "med-autoscience" for item in inventory["mas_domain_specific"])
    skeleton = payload["opl_domain_agent_skeleton_mapping"]
    assert skeleton == provider["domain_agent_skeleton_mapping"]
    assert skeleton["mapping_mode"] == "repo_source_physical_anchors_landed"
    assert skeleton["repo_tracks_real_workspace_artifacts"] is False
    assert "mas_family_sidecar_dispatch_receipt" in skeleton["skeleton"]["contracts/runtime/sidecar"]
    standard_skeleton = payload["standard_domain_agent_skeleton"]
    assert standard_skeleton["surface_kind"] == "standard_domain_agent_skeleton"
    assert standard_skeleton["version"] == "standard-domain-agent-skeleton.v1"
    assert standard_skeleton["skeleton_id"] == "mas.standard_domain_agent_skeleton.v1"
    assert standard_skeleton["target_domain_id"] == "med-autoscience"
    assert standard_skeleton["mapping_mode"] == "repo_source_physical_anchors_landed"
    assert standard_skeleton["repo_tracks_real_workspace_artifacts"] is False
    assert standard_skeleton["repo_source_boundary"]["required_dirs"] == [
        "agent",
        "contracts",
        "runtime",
        "docs",
    ]
    assert standard_skeleton["repo_source_boundary"]["forbidden_dirs"] == ["artifacts"]
    assert standard_skeleton["skeleton"]["agent/stages"] == skeleton["skeleton"]["agent/stages"]
    assert (
        "workspace_runtime_artifact_root_locator"
        in standard_skeleton["skeleton"]["contracts/runtime/lifecycle_adapters"]
    )
    default_slots = standard_skeleton["default_new_surface_slots"]
    assert default_slots == {
        "stage": "agent/stages",
        "prompt": "agent/prompts",
        "skill": "agent/skills",
        "knowledge": "agent/knowledge",
        "quality": "agent/quality_gates",
        "projection": "contracts/runtime/projection_builders",
    }
    assert standard_skeleton["artifact_boundary"]["repo_contains_real_artifacts"] is False
    assert standard_skeleton["artifact_boundary"]["artifact_roots_are_locators"] is True
    assert standard_skeleton["artifact_boundary"]["workspace_artifact_locator_refs"] == [
        "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    ]
    assert standard_skeleton["workspace_runtime_artifact_root_locator_ref"] == (
        "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    )
    physical_audit = standard_skeleton["physical_skeleton_layout_audit"]
    assert physical_audit["surface_kind"] == "standard_domain_agent_physical_skeleton_layout_audit"
    assert physical_audit["status"] == "repo_source_physical_anchors_landed"
    assert physical_audit["repo_source_root"] == "repo:med-autoscience"
    assert physical_audit["repo_source_anchor_status"]["status"] == "landed"
    assert physical_audit["repo_source_anchor_status"] == standard_skeleton["repo_source_anchor_status"]
    assert physical_audit["standard_layout_version"] == "standard-domain-agent-physical-layout.v1"
    assert physical_audit["repo_tracks_real_workspace_artifacts"] is False
    assert physical_audit["artifact_body_included"] is False
    assert physical_audit["workspace_runtime_artifact_root_locator_ref"] == (
        "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    )
    assert physical_audit["default_placement_policy"] == {
        "new_repo_source_surfaces_follow_standard_slots": True,
        "preserve_current_locator_boundaries": True,
        "destructive_directory_reorganization_allowed": False,
        "real_workspace_artifacts_remain_locator_only": True,
    }
    by_slot = {item["slot_id"]: item for item in physical_audit["slots"]}
    assert by_slot["agent/stages"]["repo_paths"] == [
        "docs/policies/study-workflow/stage_led_research_autonomy.md",
        "agent/stages/stage_route_contract.yaml",
        "src/med_autoscience/controllers/stage_knowledge_plane.py",
    ]
    assert by_slot["agent/stages"]["status"] == "mapped_to_existing_repo_paths"
    assert by_slot["agent/stages"]["surface_class"] == "stage"
    assert by_slot["agent/stages"]["default_for_new_surfaces"] is True
    assert by_slot["agent/stages"]["mapping_explanation"] == (
        "New stage definitions should land in the standard slot while existing stage policy "
        "and stage knowledge controller paths remain the active repo mapping."
    )
    assert by_slot["agent/prompts"]["surface_class"] == "prompt"
    assert by_slot["agent/prompts"]["default_for_new_surfaces"] is True
    assert by_slot["agent/skills"]["surface_class"] == "skill"
    assert by_slot["agent/skills"]["default_for_new_surfaces"] is True
    assert by_slot["agent/knowledge"]["repo_paths"] == [
        "docs/policies/study-workflow/publication_route_memory_policy.md",
        "docs/policies/study-workflow/publication_route_memory_library.md",
        "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
    ]
    assert by_slot["agent/knowledge"]["surface_class"] == "knowledge"
    assert by_slot["agent/quality_gates"]["surface_class"] == "quality"
    assert by_slot["agent/quality_gates"]["default_for_new_surfaces"] is True
    assert by_slot["contracts/runtime/sidecar"]["repo_paths"] == [
        "src/med_autoscience/controllers/sidecar_family_adapter.py",
        "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
    ]
    assert by_slot["contracts/runtime/projection_builders"]["surface_class"] == "projection"
    assert by_slot["contracts/runtime/projection_builders"]["default_for_new_surfaces"] is True
    assert by_slot["runtime/artifact_locator"]["locator_refs"] == [
        "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    ]
    assert by_slot["runtime/artifact_locator"]["status"] == "locator_only_no_artifact_body"
    assert by_slot["runtime/artifact_locator"]["default_for_new_surfaces"] is False
    assert by_slot["artifacts"]["status"] == "forbidden_repo_artifact_body"
    assert by_slot["artifacts"]["repo_paths"] == []
    assert by_slot["artifacts"]["locator_refs"] == [
        "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    ]
    assert physical_audit["summary"] == {
        "mapped_slot_count": 7,
        "locator_only_slot_count": 2,
        "missing_required_slot_count": 0,
        "forbidden_repo_artifact_body": True,
    }
    assert payload["workspace_runtime_artifact_root_locator"]["surface_kind"] == (
        "workspace_runtime_artifact_root_locator"
    )
    assert payload["workspace_runtime_artifact_root_locator"]["repo_root_tracks_real_artifacts"] is False
    assert payload["workspace_runtime_artifact_root_locator"]["locators"]["study_artifact_root"] == (
        "studies/<study_id>/artifacts"
    )
    assert standard_skeleton["authority_boundary"]["opl"] == "framework_transport_and_projection_only"
    assert standard_skeleton["authority_boundary"]["domain_agent"] == "truth_quality_artifact_owner"
    assert "domain_truth" in standard_skeleton["authority_boundary"]["forbidden_opl_authority"]
    assert "quality_verdict" in standard_skeleton["authority_boundary"]["forbidden_opl_authority"]
    assert "canonical_artifact_blob" in standard_skeleton["authority_boundary"]["forbidden_opl_authority"]
