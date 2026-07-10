from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_state_index_source_adapter_builds_opl_family_adoption_surface(tmp_path: Path) -> None:
    source_adapter = importlib.import_module(
        "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
    )
    adoption_module = importlib.import_module("med_autoscience.opl_domain_pack.family_adoption")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    manifest_path = workspace_root / source_adapter.STATE_INDEX_SOURCE_ADAPTER_REF
    owner_receipt_path = study_root / "artifacts" / "runtime" / "owner_route" / "latest.json"
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
    owner_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    owner_receipt_path.write_text(
        json.dumps(owner_receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    source_adapter.emit_owner_route_receipt_source(
        receipt=owner_receipt,
        receipt_path=owner_receipt_path,
    )
    assert not manifest_path.exists()

    surface = adoption_module.build_opl_family_adoption_surface(
        workspace_root=workspace_root,
    )

    assert surface["surface_kind"] == "mas_opl_family_domain_authority_refs_adoption"
    assert surface["workspace_root"] == str(workspace_root.resolve())
    assert surface["refs"]["state_index_source_adapter"] == {
        "surface_kind": "mas_opl_state_index_source_adapter",
        "manifest_ref": "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json",
        "workspace_relative_path": "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json",
        "status": "source_adapter_manifest_projected",
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "source_families": [
            "authority_ref_metadata",
            "archive_refs",
            "owner_route_receipts",
            "dispatch_receipts",
            "stage_artifact_delta_refs",
        ],
        "local_persistence": "absent",
        "body_included": False,
    }
    assert "legacy_sqlite_refs_index" not in surface["refs"]
    assert surface["refs"]["source_contract"] == "contracts/opl-framework/family-contract-adoption.json"
    assert surface["refs"]["domain_authority_refs_contract"] == (
        "med_autoscience.runtime_protocol.opl_state_index_source_adapter.source_adapter_contract"
    )
    assert surface["refs"]["authority_boundary"]["domain_truth_owner"] == "MedAutoScience"
    assert surface["refs"]["authority_boundary"]["opl_role"] == (
        "OPL stage-runtime discovery and indexing only"
    )
    assert surface["refs"]["authority_boundary"]["forbidden_opl_authority_surfaces"] == [
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "AI reviewer workflow",
        "paper/manuscript/current_package",
        "current_package.zip",
    ]
    assert surface["payload"]["persistence"]["state_index_source_adapter_ref"] == (
        "/refs/state_index_source_adapter"
    )
    assert surface["payload"]["persistence"]["local_persistence"] == "absent"
    assert surface["payload"]["persistence"]["body_included"] is False
    assert surface["payload"]["owner_route"]["source_family"] == "owner_route_receipts"
    assert surface["payload"]["lifecycle"]["source_families"] == [
        "dispatch_receipts",
        "archive_refs",
    ]
    assert "publication_eval/latest.json" not in json.dumps(surface["payload"], ensure_ascii=False)
