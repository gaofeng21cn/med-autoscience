from __future__ import annotations

import importlib

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
