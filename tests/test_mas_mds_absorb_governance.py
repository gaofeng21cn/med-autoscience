from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

EXPECTED_CLASSIFICATIONS = [
    "mas_owned",
    "rewrite_in_mas",
    "fixture_only",
    "retire",
    "external_source_archive_only",
]
EXPECTED_REMAINING_SURFACE_IDS = [
    "runtime_core_daemon",
    "quest_lifecycle",
    "worker_runner_lifecycle",
    "channels_connectors_transport",
    "mcp_surface",
    "tui_web_visual_status",
    "gitops_workspace_state",
    "skills_overlay_templates",
    "team_multiagent_coordination",
    "upstream_source_archive",
]


def test_absorb_governance_contract_freezes_no_history_import_and_source_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()

    assert contract["surface"] == "mas_mds_absorb_governance_contract"
    assert contract["schema_version"] == 1
    assert contract["owner"] == "MedAutoScience"
    assert contract["upstream_role"] == "MedDeepScientist optional oracle/intake/backend-audit source"
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
    assert provenance["upstream_repo"] == "med-deepscientist"
    assert provenance["upstream_ref"] == "med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc"
    assert provenance["snapshot_sha256"] == "f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b"
    assert provenance["snapshot_archive_format"] == "git archive --format=tar HEAD"
    assert provenance["snapshot_file_count"] == 1843
    assert "LICENSE (Apache-2.0; Copyright 2026 ResearAI)" in provenance["license_refs"]
    assert provenance["capability_classification"] in EXPECTED_CLASSIFICATIONS


def test_capability_classification_only_allows_functional_monolith_cutover_contract_values() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()

    assert contract["allowed_capability_classifications"] == EXPECTED_CLASSIFICATIONS
    assert [item["classification"] for item in contract["capability_classification_guard"]] == [
        "mas_owned",
        "rewrite_in_mas",
        "fixture_only",
        "retire",
        "external_source_archive_only",
    ]
    validation = module.validate_mas_mds_absorb_governance_contract(contract)
    assert validation["ok"] is True

    contract["source_provenance"]["capability_classification"] = "oracle"
    contract["capability_classification_guard"].append(
        {
            "capability_id": "old_oracle_claim",
            "classification": "oracle",
            "mds_role": "legacy_oracle",
            "authority_claims": [],
        }
    )

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "invalid_source_provenance_capability_classification",
        "invalid_capability_classification",
    }


def test_doc_reference_semantic_guard_freezes_thin_hub_and_mas_owned_packaging() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    guard = module.build_mas_mds_doc_reference_semantic_guard()

    assert guard["surface"] == "mas_mds_doc_reference_semantic_guard"
    assert guard["schema_version"] == 1
    assert guard["owner"] == "MedAutoScience"
    assert guard["guarded_doc_families"] == [
        "README",
        "docs/README",
        "docs/status",
        "docs/policies",
        "docs/program",
        "docs/runtime",
        "docs/references",
    ]
    assert guard["doc_prose_wording_tests_allowed"] is False
    assert guard["markdown_as_machine_truth_allowed"] is False
    assert guard["readme_status_policy_may_create_owner_truth"] is False
    assert guard["default_operation_requires_external_mds"] is False
    assert guard["default_diagnostic_requires_external_mds"] is False
    assert guard["mds_webui_default_allowed"] is False
    assert guard["hosted_runtime_packaging_owner"] == "MedAutoScience"
    assert guard["allowed_mds_roles"] == [
        "frozen_source_archive",
        "historical_fixture",
        "explicit_legacy_diagnostic",
        "provenance_reference",
        "parity_oracle",
        "upstream_intake_source",
    ]
    assert guard["forbidden_mds_claims"] == [
        "default_runtime_dependency",
        "default_diagnostic_dependency",
        "default_webui_progress_owner",
        "default_runner",
        "product_owner",
        "study_truth_authority",
        "quality_authority",
        "publication_authority",
        "runtime_authority",
        "artifact_authority",
        "contributor_history_import",
    ]
    assert guard["mas_owned_packaging_surfaces"] == [
        "artifacts/runtime/progress_portal/latest.json",
        "ops/mas/progress/index.html",
        "ops/mas/bin/start-web",
        "medautosci workspace progress-portal --serve",
        "optional_local_read_only_progress_service",
    ]

    hubs = {item["surface_id"]: item for item in guard["hub_reference_roles"]}
    assert hubs["product_entry"]["hub_role"] == "read_model"
    assert hubs["study_progress"]["hub_role"] == "read_model"
    assert hubs["mcp"]["hub_role"] == "adapter"
    assert hubs["progress_portal"]["hub_role"] == "materializer"
    assert hubs["display_quality_entrances"]["hub_role"] == "adapter"
    assert hubs["progress_portal"]["materializes_only"] == [
        "artifacts/runtime/progress_portal/latest.json",
        "ops/mas/progress/index.html",
    ]
    for hub in hubs.values():
        assert hub["authority_claims"] == []
        assert hub["may_control_runtime"] is False
        assert hub["may_authorize_publication"] is False
        assert hub["may_write_study_truth"] is False
    assert module.validate_mas_mds_doc_reference_semantic_guard(guard)["ok"] is True


def test_doc_reference_semantic_guard_validation_fails_closed_on_doc_and_mds_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    guard = module.build_mas_mds_doc_reference_semantic_guard()
    guard["doc_prose_wording_tests_allowed"] = True
    guard["mds_webui_default_allowed"] = True
    guard["allowed_mds_roles"].append("default_webui_owner")
    guard["hub_reference_roles"][0]["authority_claims"] = ["study_truth_authority"]
    guard["hub_reference_roles"][3]["materializes_only"].append("publication_eval/latest.json")

    validation = module.validate_mas_mds_doc_reference_semantic_guard(guard)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "doc_prose_wording_tests_unblocked",
        "mds_webui_default_unblocked",
        "allowed_mds_roles_drift",
        "doc_reference_non_authority_hub_claims_authority",
        "doc_reference_hub_materializes_authority_surface",
    }


def test_mds_oracle_classification_cannot_claim_mas_authority_surfaces() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()
    fixture = next(item for item in contract["capability_classification_guard"] if item["classification"] == "fixture_only")
    assert fixture["mds_role"] == "fixture_or_historical_oracle_only"
    assert fixture["authority_claims"] == []
    assert fixture["forbidden_authority_surfaces"] == [
        "publication_authority",
        "quality_authority",
        "study_authority",
        "submission_authority",
        "user_visible_next_action_authority",
    ]

    fixture["authority_claims"] = [
        "study_authority",
        "quality_authority",
        "publication_authority",
        "submission_authority",
        "user_visible_next_action_authority",
    ]

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {"mds_fixture_claims_mas_authority"}


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


def test_absorb_governance_validation_fails_closed_on_placeholder_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    contract = module.build_mas_mds_absorb_governance_contract()
    contract["source_provenance"]["upstream_ref"] = "snapshot-ref-recorded-at-intake"
    contract["source_provenance"]["snapshot_sha256"] = "required_per_snapshot_intake"
    contract["source_provenance"]["license_refs"] = ["upstream license file"]

    validation = module.validate_mas_mds_absorb_governance_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "placeholder_source_provenance_field",
        "invalid_snapshot_sha256",
    }
    assert {issue["field"] for issue in validation["issues"]} == {
        "upstream_ref",
        "snapshot_sha256",
        "license_refs",
    }


def test_no_history_snapshot_manifest_records_author_guard_and_retained_capabilities() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    manifest = module.build_mds_no_history_snapshot_manifest()

    assert manifest["surface"] == "mds_no_history_snapshot_manifest"
    assert manifest["schema_version"] == 1
    assert manifest["import_mode"] == "no_history_snapshot_only"
    assert manifest["default_operation_requires_external_mds"] is False
    assert manifest["source_provenance"]["upstream_repo"] == "med-deepscientist"
    assert manifest["source_provenance"]["snapshot_sha256"] == (
        "f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b"
    )
    assert manifest["source_provenance"]["license_refs"] == [
        "LICENSE (Apache-2.0; Copyright 2026 ResearAI)",
        "MEDICAL_FORK_MANIFEST.json (controlled fork; upstream base a7853fda3432d37f6dee91fa6e66330f564bd8be)",
        "docs/references/med-deepscientist/med_deepscientist_upstream_source_provenance.md",
    ]
    assert manifest["author_audit"] == {
        "import_commit_author_policy": "mas_maintainer_only",
        "coauthor_trailers_allowed": False,
        "unwanted_upstream_author_identity_allowed": False,
        "default_branch_contributor_check_required": True,
    }
    assert {item["classification"] for item in manifest["capabilities"]} == {
        "mas_owned",
        "fixture_only",
        "retire",
    }
    assert manifest["retained_capability_ids"] == [
        "runtime_execution",
        "artifact_inventory",
        "paper_contract_health",
        "manuscript_coverage",
        "prompt_stage_discipline",
        "memory_and_lesson_store",
    ]
    assert module.validate_mds_no_history_snapshot_manifest(manifest)["ok"] is True


def test_no_history_snapshot_manifest_records_remaining_surface_cutover_classification() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    manifest = module.build_mds_no_history_snapshot_manifest()
    inventory = manifest["remaining_surface_inventory"]

    assert inventory["surface"] == "mds_remaining_surface_inventory"
    assert inventory["allowed_classifications"] == EXPECTED_CLASSIFICATIONS
    assert [surface["surface_id"] for surface in inventory["remaining_surfaces"]] == EXPECTED_REMAINING_SURFACE_IDS
    assert {surface["classification"] for surface in inventory["remaining_surfaces"]} == set(EXPECTED_CLASSIFICATIONS)
    for surface in inventory["remaining_surfaces"]:
        assert surface["authority_claims"] == []
        assert surface["imports_upstream_history"] is False
        assert surface["default_runtime_dependency_allowed"] is False
        assert surface["quality_authority_allowed"] is False
        assert surface["publication_ready_authority_allowed"] is False


def test_no_history_snapshot_manifest_validation_blocks_author_and_history_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mas_mds_absorb_governance")

    manifest = module.build_mds_no_history_snapshot_manifest()
    manifest["import_mode"] = "subtree_history_import"
    manifest["default_operation_requires_external_mds"] = True
    manifest["source_provenance"]["snapshot_sha256"] = ""
    manifest["author_audit"]["coauthor_trailers_allowed"] = True
    manifest["author_audit"]["unwanted_upstream_author_identity_allowed"] = True
    manifest["capabilities"][0]["classification"] = "oracle"
    manifest["capabilities"][1]["authority_claims"] = ["quality_authority"]
    manifest["remaining_surface_inventory"]["remaining_surfaces"][0]["classification"] = "absorb"

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
        "invalid_remaining_surface_classification",
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
    assert payload["source_provenance"]["upstream_ref"] == (
        "med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc"
    )
    assert payload["source_provenance"]["snapshot_sha256"] == (
        "f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b"
    )
    assert payload["author_audit"]["coauthor_trailers_allowed"] is False
    assert payload["author_audit"]["unwanted_upstream_author_identity_allowed"] is False
    assert payload["remaining_surface_inventory"]["surface"] == "mds_remaining_surface_inventory"
    assert payload["remaining_surface_inventory"]["allowed_classifications"] == EXPECTED_CLASSIFICATIONS
    assert [surface["surface_id"] for surface in payload["remaining_surface_inventory"]["remaining_surfaces"]] == (
        EXPECTED_REMAINING_SURFACE_IDS
    )
