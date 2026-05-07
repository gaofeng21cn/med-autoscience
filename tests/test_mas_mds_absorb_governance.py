from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def test_absorb_governance_contract_freezes_no_history_import_and_source_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()

    assert contract["surface"] == "mas_mds_absorb_governance_contract"
    assert contract["schema_version"] == 1
    assert contract["owner"] == "MedAutoScience"
    assert contract["upstream_role"] == "MedDeepScientist controlled backend/oracle/intake source"
    assert contract["history_policy"] == {
        "import_mode": "no_history_snapshot_only",
        "merge_unrelated_histories_allowed": False,
        "subtree_history_import_allowed": False,
        "filter_repo_history_import_allowed": False,
        "co_authored_by_upstream_authors_allowed": False,
        "unwanted_upstream_author_identity_allowed": False,
    }
    assert contract["required_source_provenance_fields"] == [
        "upstream_repo",
        "upstream_ref",
        "snapshot_sha256",
        "license_refs",
        "capability_classification",
    ]
    provenance = contract["source_provenance"]
    assert provenance["upstream_repo"]
    assert provenance["upstream_ref"]
    assert provenance["snapshot_sha256"]
    assert provenance["license_refs"]
    assert provenance["capability_classification"] in {"absorb", "oracle", "retire", "compat"}


def test_capability_classification_only_allows_absorb_oracle_retire_compat() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()

    assert contract["allowed_capability_classifications"] == ["absorb", "oracle", "retire", "compat"]
    assert [item["classification"] for item in contract["capability_classification_guard"]] == [
        "absorb",
        "oracle",
        "retire",
        "compat",
    ]
    validation = module.validate_mas_mds_absorb_governance_contract(contract)
    assert validation["ok"] is True

    contract["source_provenance"]["capability_classification"] = "owner"
    contract["capability_classification_guard"].append(
        {
            "capability_id": "bad_owner_claim",
            "classification": "owner",
            "mds_role": "second_owner",
            "authority_claims": [],
        }
    )

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "invalid_source_provenance_capability_classification",
        "invalid_capability_classification",
    }


def test_mds_oracle_classification_cannot_claim_mas_authority_surfaces() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()
    oracle = next(item for item in contract["capability_classification_guard"] if item["classification"] == "oracle")
    assert oracle["mds_role"] == "backend_oracle_only"
    assert oracle["authority_claims"] == []
    assert oracle["forbidden_authority_surfaces"] == [
        "publication_authority",
        "quality_authority",
        "study_authority",
        "submission_authority",
        "user_visible_next_action_authority",
    ]

    oracle["authority_claims"] = [
        "study_authority",
        "quality_authority",
        "publication_authority",
        "submission_authority",
        "user_visible_next_action_authority",
    ]

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {"mds_oracle_claims_mas_authority"}


def test_absorb_governance_validation_fails_closed_on_history_and_provenance_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()
    contract["history_policy"]["merge_unrelated_histories_allowed"] = True
    contract["history_policy"]["subtree_history_import_allowed"] = True
    contract["history_policy"]["filter_repo_history_import_allowed"] = True
    contract["history_policy"]["co_authored_by_upstream_authors_allowed"] = True
    contract["history_policy"]["unwanted_upstream_author_identity_allowed"] = True
    contract["source_provenance"]["snapshot_sha256"] = ""
    contract["source_provenance"]["license_refs"] = []

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "merge_unrelated_histories_unblocked",
        "subtree_history_import_unblocked",
        "filter_repo_history_import_unblocked",
        "upstream_coauthor_footprint_unblocked",
        "upstream_author_identity_unblocked",
        "missing_source_provenance_field",
    }


def test_no_history_snapshot_manifest_records_author_guard_and_retained_capabilities() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    manifest = module.build_mds_no_history_snapshot_manifest()

    assert manifest["surface"] == "mds_no_history_snapshot_manifest"
    assert manifest["schema_version"] == 1
    assert manifest["import_mode"] == "no_history_snapshot_only"
    assert manifest["default_operation_requires_external_mds"] is False
    assert manifest["source_provenance"]["upstream_repo"] == "med-deepscientist"
    assert manifest["source_provenance"]["snapshot_sha256"]
    assert manifest["source_provenance"]["license_refs"]
    assert manifest["author_audit"] == {
        "import_commit_author_policy": "mas_maintainer_only",
        "coauthor_trailers_allowed": False,
        "unwanted_upstream_author_identity_allowed": False,
        "default_branch_contributor_check_required": True,
    }
    assert {item["classification"] for item in manifest["capabilities"]} == {"absorb", "oracle", "retire", "compat"}
    assert manifest["retained_capability_ids"] == [
        "runtime_execution",
        "artifact_inventory",
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
        "memory_and_lesson_store",
    ]
    assert module.validate_mds_no_history_snapshot_manifest(manifest)["ok"] is True


def test_no_history_snapshot_manifest_validation_blocks_author_and_history_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    manifest = module.build_mds_no_history_snapshot_manifest()
    manifest["import_mode"] = "subtree_history_import"
    manifest["default_operation_requires_external_mds"] = True
    manifest["source_provenance"]["snapshot_sha256"] = ""
    manifest["author_audit"]["coauthor_trailers_allowed"] = True
    manifest["author_audit"]["unwanted_upstream_author_identity_allowed"] = True
    manifest["capabilities"][0]["classification"] = "owner"
    manifest["capabilities"][1]["authority_claims"] = ["quality_authority"]

    validation = module.validate_mds_no_history_snapshot_manifest(manifest)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "history_import_mode_drift",
        "external_mds_required_for_default_operation",
        "missing_source_provenance_field",
        "upstream_coauthor_footprint_unblocked",
        "upstream_author_identity_unblocked",
        "invalid_capability_classification",
        "retained_capability_claims_mas_authority",
    }


def test_no_history_source_provenance_json_is_machine_readable() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")
    repo_root = Path(__file__).resolve().parents[1]
    provenance_path = repo_root / "docs" / "references" / "med-deepscientist" / "source_provenance.json"

    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    validation = module.validate_mds_no_history_snapshot_manifest(payload)

    assert validation["ok"] is True
    assert payload["surface"] == "mds_no_history_snapshot_manifest"
    assert payload["import_mode"] == "no_history_snapshot_only"
    assert payload["default_operation_requires_external_mds"] is False
    assert payload["author_audit"]["coauthor_trailers_allowed"] is False
    assert payload["author_audit"]["unwanted_upstream_author_identity_allowed"] is False
