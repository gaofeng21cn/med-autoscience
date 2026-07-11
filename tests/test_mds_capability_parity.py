from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

AUTHORITY_FLAGS = (
    "quality_ready_authority_allowed",
    "quality_authority_allowed",
    "publication_ready_authority_allowed",
    "submission_ready_authority_allowed",
)
READY_AUTHORITY_FLAGS = (
    "quality_ready_authorized",
    "publication_ready_authorized",
    "submission_ready_authorized",
)
PROVENANCE_REF = "docs/references/med-deepscientist/source_provenance.json"


def _module():
    return importlib.import_module("med_autoscience.controllers.mds_capability_parity")


def _issue_codes(validation: dict[str, object]) -> set[str]:
    return {issue["code"] for issue in validation["issues"]}


def _source_provenance_payload() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]
    provenance_path = repo_root / PROVENANCE_REF
    return json.loads(provenance_path.read_text(encoding="utf-8"))


def test_mds_parity_matrix_keeps_archive_only_authority_boundary() -> None:
    module = _module()

    matrix = module.build_mds_capability_parity_matrix()
    gate = module.build_mds_capability_cutover_gate()

    assert module.validate_mds_capability_parity_matrix(matrix)["ok"] is True
    assert matrix["mds_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert matrix["mds_quality_authority"] == "none"
    assert matrix["mas_owner"] == "MedAutoScience"
    assert matrix["parity_summary"]["medical_quality_authority"] == "blocked_for_mds"
    assert matrix["parity_summary"]["capability_count"] == len(matrix["capabilities"]) == 6
    assert matrix["parity_summary"]["oracle_fixture_count"] == 6
    assert gate["owner_switch_allowed"] is False
    assert gate["proof_bundle_status"] == "missing"
    assert gate["mds_quality_authority"] == "none"

    for capability in matrix["capabilities"]:
        assert capability["provenance_ref"] == PROVENANCE_REF
        assert capability["oracle_fixture_ref"]
        assert capability["mas_owner_surface"]
        assert capability["can_authorize_medical_quality"] is False
        assert all(capability[flag] is False for flag in AUTHORITY_FLAGS)
        for proof in capability["supersede_proofs"]:
            assert proof["mds_mechanical_signal_role"] == "evidence_only"
            assert proof["mechanical_signal_can_only"].startswith("request_")
            assert all(proof[flag] is False for flag in READY_AUTHORITY_FLAGS)


def test_mds_remaining_surfaces_reject_legacy_runtime_authority() -> None:
    module = _module()

    inventory = module.build_mds_remaining_surface_inventory()

    assert module.validate_mds_remaining_surface_inventory(inventory)["ok"] is True
    assert inventory["mds_final_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert inventory["default_operation_requires_external_mds"] is False
    assert inventory["default_diagnostic_requires_external_mds"] is False
    assert inventory["upstream_history_import_allowed"] is False

    by_id = {surface["surface_id"]: surface for surface in inventory["remaining_surfaces"]}
    assert by_id["runtime_core_daemon"]["classification"] == "retired_mas_runtime_surface"
    assert by_id["runtime_core_daemon"]["mas_target_owner"] == "one-person-lab"
    assert by_id["upstream_source_archive"]["classification"] == "external_source_archive_only"

    for surface in inventory["remaining_surfaces"]:
        assert surface["provenance_ref"] == PROVENANCE_REF
        assert surface["authority_claims"] == []
        assert surface["imports_upstream_history"] is False
        assert surface["default_runtime_dependency_allowed"] is False
        assert surface["quality_authority_allowed"] is False
        assert surface["publication_ready_authority_allowed"] is False


def test_mds_behavior_equivalence_rejects_daemon_equivalence_and_owner_writes() -> None:
    module = _module()

    matrix = module.build_mds_behavior_equivalence_matrix()

    assert module.validate_mds_behavior_equivalence_matrix(matrix)["ok"] is True
    assert matrix["default_operation_requires_external_mds"] is False
    assert matrix["default_diagnostic_requires_external_mds"] is False
    assert matrix["mas_default_runtime_is_resident_daemon"] is False
    assert matrix["mds_daemon_was_resident_http_websocket_server"] is True
    assert matrix["completion_claim"] == "default_independence_not_full_behavior_equivalence"
    assert matrix["summary"]["fully_equivalent_to_mds_daemon"] is False

    continuity = matrix["runtime_continuity_completion"]
    assert continuity["external_mds_repo_required"] is False
    assert continuity["mds_daemon_required"] is False
    assert continuity["current_control_state_projection"]["role"] == "read_model"
    assert continuity["current_control_state_projection"]["writes_authority_surface"] is False
    assert continuity["retired_mas_recovery_projection"]["allowed_current_actions"] == []
    assert continuity["user_surface_projection"]["reinterprets_study_truth"] is False
    assert all(continuity[flag] is False for flag in READY_AUTHORITY_FLAGS)

    for surface in matrix["behavior_surfaces"]:
        assert surface["provenance_ref"] == PROVENANCE_REF
        assert surface["mas_default_requires_external_mds"] is False
        assert surface["requires_mds_daemon_for_default_operation"] is False
        assert surface["quality_authority_allowed"] is False
        assert surface["publication_ready_authority_allowed"] is False


def test_mds_live_worker_history_is_provenance_only() -> None:
    module = _module()
    repo_root = Path(__file__).resolve().parents[1]
    provenance = json.loads(
        (repo_root / PROVENANCE_REF).read_text(encoding="utf-8")
    )

    assert provenance["surface"] == "mds_no_history_snapshot_manifest"
    assert provenance["source_provenance"]["capability_classification"] == (
        "external_source_archive_only"
    )
    matrix = module.build_mds_behavior_equivalence_matrix()
    session_surface = next(
        surface for surface in matrix["behavior_surfaces"] if surface["surface_id"] == "live_worker_session_tracking"
    )
    assert session_surface["mds_behavior"]["live_worker_state_registry"] is True
    assert session_surface["mas_behavior"]["current_control_state_read_model"] == {
        "owner": "one-person-lab",
        "read_only": True,
        "can_write_domain_truth": False,
    }


def test_source_provenance_json_keeps_archive_readable_without_authority() -> None:
    module = _module()

    payload = _source_provenance_payload()

    assert payload["surface"] == "mds_no_history_snapshot_manifest"
    assert payload["import_mode"] == "no_history_snapshot_only"
    assert payload["default_operation_requires_external_mds"] is False
    assert payload["source_provenance"]["capability_classification"] == "external_source_archive_only"
    assert payload["source_provenance"]["snapshot_sha256"]
    assert payload["author_audit"]["import_commit_author_policy"] == "mas_maintainer_only"
    assert len(payload["retained_capability_ids"]) == 6
    assert all(capability["authority_claims"] == [] for capability in payload["capabilities"])
    assert module.validate_mds_remaining_surface_inventory(payload["remaining_surface_inventory"])["ok"] is True


def test_mds_validators_fail_closed_on_authority_and_legacy_runtime_drift() -> None:
    module = _module()

    parity = module.build_mds_capability_parity_matrix()
    parity["mds_quality_authority"] = "quality_owner"
    parity["capabilities"][0]["quality_authority_allowed"] = True
    parity["capabilities"][0]["submission_ready_authority_allowed"] = True
    parity["capabilities"][0]["supersede_proofs"][0:0] = [
        {
            "proof_id": "runtime_execution",
            "mas_owned": True,
            "mds_mechanical_signal_role": "evidence_only",
            "mechanical_signal_can_only": "authorize_quality",
            "quality_ready_authorized": True,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        }
    ]
    parity["capabilities"][1]["provenance_ref"] = ""

    parity_codes = _issue_codes(module.validate_mds_capability_parity_matrix(parity))
    assert parity_codes >= {
        "mds_quality_authority_drift",
        "capability_quality_authority_allowed",
        "capability_submission_ready_authority_allowed",
        "capability_supersede_proof_signal_role_drift",
        "capability_supersede_proof_ready_authority_drift",
        "capability_missing_provenance_ref",
    }

    behavior = module.build_mds_behavior_equivalence_matrix()
    behavior["default_operation_requires_external_mds"] = True
    behavior["mas_default_runtime_is_resident_daemon"] = True
    behavior["behavior_surfaces"][0]["requires_mds_daemon_for_default_operation"] = True
    behavior["runtime_continuity_completion"]["mds_daemon_required"] = True
    behavior["runtime_continuity_completion"]["current_control_state_projection"]["writes_authority_surface"] = True
    behavior["runtime_continuity_completion"]["submission_ready_authorized"] = True

    behavior_codes = _issue_codes(module.validate_mds_behavior_equivalence_matrix(behavior))
    assert behavior_codes >= {
        "behavior_matrix_external_mds_default_dependency",
        "behavior_matrix_resident_daemon_overclaim",
        "behavior_surface_requires_mds_daemon_for_default_operation",
        "runtime_continuity_mds_daemon_dependency",
        "runtime_continuity_session_authority_write",
        "runtime_continuity_submission_ready_authorized",
    }

    inventory = module.build_mds_remaining_surface_inventory()
    inventory["default_operation_requires_external_mds"] = True
    inventory["remaining_surfaces"][0]["authority_claims"] = ["quality_authority"]
    inventory["remaining_surfaces"][0]["default_runtime_dependency_allowed"] = True

    inventory_codes = _issue_codes(module.validate_mds_remaining_surface_inventory(inventory))
    assert inventory_codes >= {
        "default_operation_requires_external_mds",
        "remaining_surface_claims_mas_authority",
        "remaining_surface_default_runtime_dependency_allowed",
    }
