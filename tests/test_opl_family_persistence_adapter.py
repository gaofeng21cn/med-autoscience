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
        "surface": "runtime_supervisor_owner_route",
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
        "surface": "runtime_supervisor_dispatch_receipt",
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
    assert provider["truth_source_precedence"]["direct_mas_skill_path"] == "authoritative"
    assert provider["truth_source_precedence"]["opl_provider_attempt_history"] == "transport_receipt_only"
    assert provider["truth_source_precedence"]["paper_progress_requires_mas_artifact_delta_or_gate_owner"] is True
    assert provider["workspace_runtime_artifact_root_locator"]["repo_root_tracks_real_artifacts"] is False
    assert provider["workspace_runtime_artifact_root_locator"]["locators"]["publication_eval"] == (
        "studies/<study_id>/artifacts/publication_eval/latest.json"
    )
    inventory = payload["opl_lifecycle_inventory"]
    assert inventory == provider["lifecycle_inventory"]
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
    assert skeleton["mapping_mode"] == "contract_only_no_physical_artifact_move"
    assert skeleton["repo_tracks_real_workspace_artifacts"] is False
    assert "mas_family_sidecar_dispatch_receipt" in skeleton["skeleton"]["contracts/runtime/sidecar"]
