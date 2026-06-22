from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SURFACE_ID = "dhd_owner_route_dispatch_paper_recovery_default_paper_mainline"


def _legacy_tombstone() -> dict[str, object]:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {item["surface_id"]: item for item in contract["tombstoned_surfaces"]}
    return surfaces[LEGACY_SURFACE_ID]


def test_old_dhd_owner_route_dispatch_recovery_path_is_not_default_mainline() -> None:
    tombstone = _legacy_tombstone()

    assert tombstone["classification"] == "diagnostics_migration_provenance_only"
    assert tombstone["default_caller"] is False
    assert tombstone["default_product_mainline_claim_allowed"] is False
    assert tombstone["default_domain_handler_mainline_claim_allowed"] is False
    assert set(tombstone["legacy_surfaces"]) >= {
        "domain_health_diagnostic",
        "DHD",
        "owner-route",
        "owner_route",
        "domain-handler export",
        "default-executor dispatch",
        "dispatch",
        "PaperRecovery",
        "paper_recovery_state",
    }


def test_old_path_replacement_points_to_paper_mission_run_contract() -> None:
    tombstone = _legacy_tombstone()

    assert tombstone["replacement_ref"] == "contracts/paper_mission_run_contract.json"
    assert tombstone["replacement_projection_ref"] == (
        "study_progress.artifact_first_mission_summary.paper_mission_run"
    )
    assert tombstone["replacement_contract"] == {
        "contract_ref": "contracts/paper_mission_run_contract.json",
        "schema_version": "paper-mission-run.v1",
        "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
        "projection_ref": "artifact_first_mission_summary.paper_mission_run",
    }


def test_old_path_forbidden_claims_include_progress_and_dm_completion() -> None:
    tombstone = _legacy_tombstone()

    assert set(tombstone["forbidden_default_claims"]) >= {
        "product_default_mainline",
        "domain_handler_default_mainline",
        "paper_progress",
        "publication_ready",
        "submission_ready",
        "runtime_ready",
        "provider_running",
        "owner_receipt_written",
        "typed_blocker_written",
        "current_package",
        "DM002_complete",
        "DM003_complete",
    }
    assert tombstone["authority_boundary"] == {
        "read_only": True,
        "history_provenance_only": True,
        "diagnostics_only": True,
        "migration_input_only": True,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
        "can_claim_dm002_complete": False,
        "can_claim_dm003_complete": False,
    }
