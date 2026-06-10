from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "data_asset_operating_contract.json"
SCHEMA_PATH = REPO_ROOT / "contracts" / "schemas" / "v1" / "data-asset-operating-contract.schema.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_data_asset_operating_contract_is_readable_and_schema_linked() -> None:
    contract = _contract()
    schema = _schema()

    assert contract["surface_kind"] == "mas_data_asset_operating_contract"
    assert contract["version"] == "mas-data-asset-operating-contract.v3"
    assert contract["owner"] == "MedAutoScience"
    assert contract["state"] == "active_contract"
    assert contract["schema_ref"] == "contracts/schemas/v1/data-asset-operating-contract.schema.json"
    assert schema["$id"] == contract["schema_ref"]
    assert set(schema["required"]) <= set(contract)


def test_contract_declares_four_planes_allowed_layers_and_refs_only_lineage() -> None:
    contract = _contract()
    planes = contract["planes"]

    assert set(planes) == {"body", "contract", "registry_lineage", "study_binding"}

    body = planes["body"]
    assert body["root_ref"] == "data/datasets"
    assert body["layout"] == "data/datasets/<layer>/<version>/"
    assert body["role"] == "dataset_release_body_authority"
    assert body["allowed_layers"] == [
        "restricted_raw",
        "deidentified_linkage",
        "master",
        "deidentified_longitudinal",
        "standardized_longitudinal",
        "external",
    ]
    assert body["contains_dataset_body"] is True
    assert body["runtime_residue"] is False

    release_contract = planes["contract"]
    assert release_contract["accepted_contract_surfaces"] == [
        "dataset_manifest.yaml",
        "release_contract",
    ]
    assert release_contract["contains_dataset_body"] is False
    assert release_contract["body_storage_allowed"] is False
    assert {
        "dataset_id",
        "version",
        "family_id",
        "layer_id",
        "main_outputs",
        "lineage_refs",
        "manifest_refs",
    } <= set(release_contract["required_ref_fields"])

    registry_lineage = planes["registry_lineage"]
    assert registry_lineage["root_ref"] == "memory/portfolio/data_assets"
    assert registry_lineage["refs_only"] is True
    assert registry_lineage["contains_dataset_body"] is False
    assert registry_lineage["surfaces"]["manifest_refs_ref"] == (
        "memory/portfolio/data_assets/lineage/manifest_refs.json"
    )


def test_manifest_refs_are_rebuildable_projection_without_cleanup_authority() -> None:
    manifest_refs = _contract()["planes"]["registry_lineage"]["manifest_refs_projection"]

    assert manifest_refs["surface_kind"] == "mas_data_asset_manifest_refs"
    assert manifest_refs["role"] == "rebuildable_refs_only_projection"
    assert manifest_refs["source_of_truth"] == [
        "data/datasets/<layer>/<version>/dataset_manifest.yaml",
        "release_contract",
    ]
    assert manifest_refs["refs_only"] is True
    assert manifest_refs["contains_dataset_body"] is False
    assert manifest_refs["derived_projection_rebuildable"] is True
    assert manifest_refs["projection_can_authorize_cleanup"] is False
    assert manifest_refs["projection_can_authorize_study_binding"] is False
    assert manifest_refs["projection_can_authorize_release_body_mutation"] is False


def test_body_retention_excludes_dataset_body_from_runtime_cleanup_and_sqlite_compact() -> None:
    contract = _contract()
    body_retention = contract["planes"]["body"]["retention"]
    runtime = contract["runtime_retention_boundary"]

    assert body_retention == {
        "excluded_from_runtime_residue_cleanup": True,
        "excluded_from_payload_externalization": True,
        "excluded_from_restore_proof_compaction": True,
        "excluded_from_sqlite_generic_compact": True,
        "reason": "dataset_body_plane_is_domain_data_asset_authority",
    }
    assert "runtime_residue_cleanup" in contract["planes"]["body"]["forbidden_consumers"]
    assert "sqlite_generic_compact" in contract["planes"]["body"]["forbidden_consumers"]
    assert runtime["dataset_body_plane_ref"] == "data/datasets"
    assert runtime["dataset_body_is_runtime_residue"] is False
    assert runtime["runtime_storage_retention_may_cleanup_dataset_body"] is False
    assert runtime["payload_externalization_may_move_dataset_body"] is False
    assert runtime["restore_proof_compaction_may_compact_dataset_body"] is False
    assert runtime["legacy_path_provenance_may_redefine_authority"] is False
    assert {
        "explicit_mas_data_asset_owner_receipt",
        "target_ref_not_under_data/datasets",
        "target_ref_not_release_body",
        "target_ref_not_study_binding_source",
    } <= set(runtime["cleanup_authority_requires"])


def test_study_binding_policy_keeps_body_out_of_study_contracts() -> None:
    study_binding = _contract()["planes"]["study_binding"]

    assert study_binding["root_ref"] == "studies/<study-id>/study.yaml"
    assert study_binding["binding_policy"] == "asset_refs_only"
    assert study_binding["accepted_ref_fields"] == [
        "dataset_id",
        "version",
        "family_id",
        "source",
        "asset_ref",
    ]
    assert study_binding["binds_consumable_release_refs_only"] is True
    assert study_binding["study_local_derived_artifacts_stay_in_study_analysis_tree"] is True
    assert study_binding["body_storage_allowed"] is False
    assert {
        "embedded_dataset_body",
        "runtime_payload_body",
        "sqlite_blob_body",
        "opl_substrate_body_ref_as_authority",
        "lineage_projection_as_release_body_authority",
    } <= set(study_binding["forbidden_binding_shapes"])


def test_opl_substrate_boundary_and_sqlite_compact_are_refs_only() -> None:
    contract = _contract()
    boundary = contract["opl_substrate_boundary"]
    sqlite = contract["sqlite_compact_accounting"]

    assert {
        "generic_locator",
        "cold_store",
        "restore",
        "lineage_event",
        "quality_result_index",
        "workbench_projection",
    } <= set(boundary["opl_allowed_roles"])
    assert {
        "dataset_body_authority",
        "direct_study_consumption_authority",
        "clinical_semantic_mapping_authority",
        "source_readiness_authority",
        "study_binding_authority",
        "owner_receipt_authority",
        "typed_blocker_authority",
        "data_datasets_body_surface",
    } <= set(boundary["opl_forbidden_roles"])
    assert {
        "access_tier",
        "direct_study_consumption",
        "clinical_semantic_mapping",
        "source_readiness",
        "study_binding",
        "owner_receipt",
        "typed_blocker",
        "release_contract",
        "dataset_body_plane",
    } <= set(boundary["mas_retained_authority"])
    assert boundary["substrate_can_transport_refs"] is True
    assert boundary["substrate_can_index_refs"] is True
    assert boundary["substrate_can_display_refs"] is True
    assert boundary["substrate_can_store_dataset_body"] is False
    assert boundary["substrate_can_redefine_data_asset_authority"] is False

    assert sqlite["role"] == "refs_only_rebuildable_read_model_accounting"
    assert sqlite["generic_sqlite_compact_can_index_refs"] is True
    assert sqlite["generic_sqlite_compact_can_compact_dataset_body"] is False
    assert sqlite["generic_sqlite_compact_can_store_dataset_body"] is False
    assert sqlite["manifest_refs_rebuildable_projection"] is True
    assert {
        "ref",
        "locator",
        "checksum",
        "manifest_ref",
        "lineage_ref",
        "asset_ref",
    } <= set(sqlite["allowed_sqlite_payload_roles"])
    assert {
        "dataset_body",
        "study_truth_body",
        "memory_body",
        "artifact_body",
        "owner_receipt_authority",
        "typed_blocker_authority",
    } <= set(sqlite["forbidden_sqlite_payloads"])
    assert sqlite["accounting_ledgers"] == {
        "runtime_process_body_compaction": "runtime_lifecycle_or_attempt_evidence_ledger",
        "data_asset_body_retention": "mas_data_asset_owner_surface",
        "refs_only_projection_rebuild": "data_asset_manifest_refs_projection",
        "sqlite_index_compact": "opl_or_runtime_refs_only_index_accounting",
    }


def test_forbidden_global_claims_block_body_in_runtime_sqlite_or_opl_surfaces() -> None:
    assert set(_contract()["forbidden_global_claims"]) == {
        "data_datasets_is_runtime_residue",
        "manifest_refs_contains_dataset_body",
        "sqlite_compact_can_store_dataset_body",
        "opl_substrate_owns_dataset_body",
        "study_binding_can_embed_dataset_body",
        "registry_lineage_projection_authorizes_body_cleanup",
    }
