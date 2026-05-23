from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_domain_authority_refs_index_builds_opl_family_adoption_surface_from_sidecar_refs(tmp_path: Path) -> None:
    refs_index = importlib.import_module("med_autoscience.runtime_protocol.domain_authority_refs_index")
    adoption_module = importlib.import_module("med_autoscience.opl_domain_pack.family_adoption")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    db_path = refs_index.workspace_authority_refs_index_path(workspace_root)
    owner_receipt_path = study_root / "artifacts" / "runtime" / "owner_route" / "latest.json"
    dispatch_receipt_path = quest_root / "artifacts" / "runtime" / "dispatch" / "dispatch-001.json"
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
        "source_refs": {"progress_projection": "studies/001-risk/progress_projection.json"},
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
    for path, payload in (
        (owner_receipt_path, owner_receipt),
        (dispatch_receipt_path, dispatch_receipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    refs_index.record_owner_route_receipt(
        study_root=study_root,
        receipt=owner_receipt,
        receipt_path=owner_receipt_path,
        db_path=db_path,
    )
    refs_index.record_dispatch_receipt(
        quest_root=quest_root,
        receipt=dispatch_receipt,
        receipt_path=dispatch_receipt_path,
        db_path=db_path,
    )

    surface = adoption_module.build_opl_family_adoption_surface(
        workspace_root=workspace_root,
        db_path=db_path,
    )

    assert surface["surface_kind"] == "mas_opl_family_domain_authority_refs_adoption"
    assert surface["workspace_root"] == str(workspace_root.resolve())
    assert surface["refs"]["sqlite_refs_index"]["db_path"] == str(db_path.resolve())
    assert surface["refs"]["sqlite_refs_index"]["workspace_relative_path"] == "artifacts/runtime/domain_authority_refs.sqlite"
    assert surface["refs"]["source_contract"] == "contracts/opl-framework/family-contract-adoption.json"
    assert surface["refs"]["domain_authority_refs_contract"] == (
        "med_autoscience.runtime_protocol.domain_authority_refs_index.domain_authority_refs_index_contract"
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
    assert surface["payload"]["persistence"]["sqlite_tables"]["owner_route_receipts"] == 1
    assert surface["payload"]["persistence"]["sqlite_tables"]["dispatch_receipts"] == 1
    assert surface["payload"]["owner_route"]["current_ticket"]["idempotency_key"] == "route-001"
    assert surface["payload"]["owner_route"]["current_ticket"]["next_owner"] == "mas_controller"
    assert surface["payload"]["owner_route"]["allowed_actions"] == ["runtime-redrive"]
    assert surface["payload"]["lifecycle"]["dispatch_receipts"][0]["dispatch_id"] == "dispatch-001"
    assert "publication_eval/latest.json" not in json.dumps(surface["payload"], ensure_ascii=False)


def test_product_entry_manifest_exposes_opl_family_adapter_discovery_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)

    adoption = payload["opl_family_persistence_lifecycle_owner_route_adoption"]
    assert adoption["surface_kind"] == "mas_opl_family_domain_authority_refs_adoption"
    assert adoption["refs"]["source_contract"] == "contracts/opl-framework/family-contract-adoption.json"
    assert adoption["refs"]["domain_authority_refs_contract"] == (
        "med_autoscience.runtime_protocol.domain_authority_refs_index.domain_authority_refs_index_contract"
    )
    assert adoption["refs"]["sqlite_refs_index"]["workspace_relative_path"] == "artifacts/runtime/domain_authority_refs.sqlite"
    assert adoption["payload"]["persistence"]["source_tables"] == [
        "authority_ref_metadata",
        "archive_refs",
        "owner_route_receipts",
        "dispatch_receipts",
        "paper_work_unit_receipts",
    ]
    assert adoption["payload"]["authority_boundary"]["publication_eval_owner"] == "MedAutoScience"
    assert adoption["payload"]["authority_boundary"]["ai_reviewer_owner"] == "MedAutoScience"
    assert adoption["payload"]["owner_route"]["source_table"] == "owner_route_receipts"
    assert payload["persistence_policy"]["surface_kind"] == "family_persistence_policy"
    assert payload["persistence_policy"]["lifecycle_ref_indexes"][0]["owner"] == "one-person-lab"
    assert payload["persistence_policy"]["lifecycle_ref_indexes"][0]["surface_role"] == (
        "domain_authority_refs_index"
    )
    assert payload["persistence_policy"]["lifecycle_ref_indexes"][0]["storage_role"] == "refs_only_domain_authority_ref_index"
    assert payload["persistence_policy"]["lifecycle_ref_indexes"][0]["ref"]["ref"] == (
        "artifacts/runtime/domain_authority_refs.sqlite"
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
    runtime_handoff = payload["opl_unique_control_plane_handoff"]
    assert "runtime_transport_handoff_projection" not in payload
    assert "runtime_transport_handoff_projection" not in provider
    assert runtime_handoff == provider["opl_unique_control_plane_handoff"]
    assert runtime_handoff["surface_kind"] == "mas_opl_unique_control_plane_handoff"
    assert runtime_handoff["generic_runtime_owner"] == "one-person-lab"
    assert runtime_handoff["domain_owner"] == "med-autoscience"
    assert runtime_handoff["domain_intent_adapter_role"] == (
        "refs_only_owner_route_typed_blocker_and_owner_receipt_handoff"
    )
    retired = {item["path"]: item for item in runtime_handoff["retired_runtime_transport_surfaces"]}
    assert retired["src/med_autoscience/runtime_transport/mas_runtime_core.py"]["retirement_status"] == (
        "physically_retired_no_alias"
    )
    assert runtime_handoff["default_caller_policy"] == {
        "default_online_runtime_owner": "one-person-lab",
        "default_provider": "temporal",
        "opl_temporal_hosted_autonomy_enabled_by_default": True,
        "persistent_online_control_plane": "opl_temporal",
        "task_start_handoff": "mas_domain_intent_to_opl_stage_attempt",
        "wakeup_retry_resume_owner": "one-person-lab",
        "codex_app_outer_driver_required": False,
        "mas_default_scheduler_allowed": False,
        "mas_default_daemon_allowed": False,
        "mas_default_queue_allowed": False,
        "mas_default_attempt_ledger_allowed": False,
        "mas_default_attempt_loop_allowed": False,
        "mas_default_worker_residency_allowed": False,
        "mas_default_transition_runner_allowed": False,
        "mas_default_persistence_engine_allowed": False,
        "mas_runtime_transport_active_as_generic_provider": False,
        "mas_runtime_transport_active_contract_surface": False,
    }
    assert runtime_handoff["generated_default_caller_boundary"] == payload[
        "functional_consumer_boundary"
    ]["generated_default_caller_boundary"]
    assert runtime_handoff["physical_retirement_gate_matrix"] == payload[
        "functional_consumer_boundary"
    ]["physical_retirement_gate_matrix"]
    retirement_candidates = {
        item["surface_id"]: item
        for item in runtime_handoff["physical_retirement_gate_matrix"]["retirement_candidates"]
    }
    assert retirement_candidates["runtime_transport"]["stale_surface_scan_clean"] is True
    assert retirement_candidates["runtime_transport"]["physical_delete_permitted"] is True
    assert retirement_candidates["runtime_transport"]["no_resurrection_proof"][
        "physical_delete_allowed"
    ] is True
    assert retirement_candidates["runtime_transport"]["current_ref_status"] == "physical_retired_no_alias"
    assert retirement_candidates["runtime_transport"]["gate_results"] == {
        "stale_surface_scan_clean": True,
        "opl_replacement_parity": "satisfied_or_not_runtime_candidate",
        "opl_default_caller_readiness": "ready",
        "mas_owner_receipt_parity": "satisfied_or_not_runtime_candidate",
        "focused_tests_green": "focused_lane_tracks_no_resurrection",
        "tombstone_refs_landed": "not_required_for_no_alias_physical_retirement",
    }
    assert retirement_candidates["lifecycle_refs_sqlite_index"]["physical_delete_permitted"] is True
    assert retirement_candidates["lifecycle_refs_sqlite_index"]["current_ref_status"] == (
        "physical_retired_no_alias_replaced_by_domain_authority_refs_index"
    )
    assert retirement_candidates["lifecycle_refs_sqlite_index"]["latest_thinning_evidence"] == {
        "status": "runtime_lifecycle_sqlite_adapter_physically_absent",
        "replacement_surface": "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "does_not_claim_generic_persistence_owner": True,
        "does_not_claim_paper_closure": True,
    }
    assert "domain_authority_refs_index" in runtime_handoff["opl_replacement_surfaces"]
    assert "generic_queue_owner" in runtime_handoff["forbidden_mas_roles"]
    assert "generic_persistence_engine_owner" in runtime_handoff["forbidden_mas_roles"]
    assert "provider_backed_family_runtime" in runtime_handoff["opl_replacement_surfaces"]
    code_path_roles = {item["path"]: item for item in runtime_handoff["code_path_roles"]}
    assert "src/med_autoscience/runtime_transport/opl_provider_backed_stage_runtime.py" not in code_path_roles
    assert code_path_roles[
        "OPL current_control_state provider/stage runtime"
    ]["allowed_mas_role"] == "domain_intent_refs_and_typed_blocker_adapter"
    assert code_path_roles[
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py"
    ]["current_role"] == "refs_only_domain_authority_refs_index"
    cleanup_gates = {
        item["residue_id"]: item
        for item in runtime_handoff["physical_cleanup_gate"]["active_path_residue_cleanup_gates"]
    }
    assert runtime_handoff["physical_cleanup_gate"][
        "no_alias_facade_compat_wrapper_allowed"
    ] is False
    assert set(cleanup_gates) == {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "lifecycle_refs_sqlite_index",
        "workbench_shell_domain_projection_refs",
        "owner_route_handoff_domain_ref_entry",
        "status_projection_domain_truth_refs",
        "legacy_supervisor_scheduler_tombstone",
    }
    assert cleanup_gates["runtime_transport_core_bridge"]["current_role"] == "none_physically_retired_no_alias"
    assert cleanup_gates["runtime_transport_core_bridge"]["current_paths"] == []
    assert cleanup_gates["runtime_transport_core_bridge"]["retirement_proof_status"] == "stale_surface_scan_clean"
    assert cleanup_gates["runtime_transport_core_bridge"]["no_resurrection_guard"] is True
    assert cleanup_gates["runtime_transport_core_bridge"]["physical_delete_permitted"] is True
    assert cleanup_gates["runtime_transport_core_bridge"]["physical_delete_completed"] is True
    assert cleanup_gates["lifecycle_refs_sqlite_index"]["current_role"] == (
        "none_physically_retired_no_alias"
    )
    assert cleanup_gates["lifecycle_refs_sqlite_index"]["current_paths"] == []
    assert cleanup_gates["lifecycle_refs_sqlite_index"]["physical_delete_completed"] is True
    lane_d_closeout = runtime_handoff["physical_cleanup_gate"]["lane_d_closeout"]
    assert lane_d_closeout["status"] == "retired_runtime_control_surfaces_plus_domain_refs_boundary"
    assert lane_d_closeout["delete_or_archive_authorized"] is False
    assert lane_d_closeout["tombstone_new_active_residue_authorized"] is False
    assert lane_d_closeout["resurrection_alias_or_wrapper_allowed"] is False
    assert {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "lifecycle_refs_sqlite_index",
        "legacy_supervisor_scheduler_tombstone",
    } <= set(lane_d_closeout["tombstone_only_residue_ids"])
    assert {
        "workbench_shell_domain_projection_refs",
        "owner_route_handoff_domain_ref_entry",
        "status_projection_domain_truth_refs",
    } <= set(lane_d_closeout["opl_owned_gap_or_domain_ref_residue_ids"])
    assert cleanup_gates["workbench_shell_domain_projection_refs"]["current_role"] == (
        "domain_projection_refs_for_opl_workbench"
    )
    assert cleanup_gates["owner_route_handoff_domain_ref_entry"]["physical_delete_permitted"] is False
    sidecar_worklist = cleanup_gates["owner_route_handoff_domain_ref_entry"]["deletion_readiness_worklist"]
    assert sidecar_worklist["status"] == "blocked_domain_owner_route_handoff_ref_consumer_present_no_runtime_control_owner"
    assert "artifacts/publication_eval/latest.json" in sidecar_worklist["must_not_write"]
    assert (
        "owner_route_handoff_response.forbidden_write_guard_proof"
        in sidecar_worklist["no_forbidden_write_proof_refs"]
    )
    assert cleanup_gates["status_projection_domain_truth_refs"]["current_role"] == (
        "domain_truth_status_projection"
    )
    assert cleanup_gates["legacy_supervisor_scheduler_tombstone"]["current_role"] == (
        "history_tombstone_provenance_only"
    )
    assert cleanup_gates["legacy_supervisor_scheduler_tombstone"]["no_resurrection_guard"] is True
    assert cleanup_gates["legacy_supervisor_scheduler_tombstone"]["tombstone_permitted"] is True
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
        item for item in inventory["framework_generic"] if item["item_id"] == "lifecycle_refs_sqlite_index"
    )
    assert "lifecycle refs" in lifecycle_index["summary"]
    assert "generic persistence/lifecycle replacement contract" in lifecycle_index["summary"]
    assert {item["item_id"] for item in inventory["framework_generic"]} == {
        "provider_stage_attempt",
        "lifecycle_refs_sqlite_index",
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
        "src/med_autoscience/controllers/owner_route_handoff.py",
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
