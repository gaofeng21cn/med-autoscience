from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.controllers.stage_artifact_index import build_stage_artifact_index
from med_autoscience.controllers.stage_run_kernel import (
    stage_run_kernel_projection_from_stage_folder,
)
from med_autoscience.controllers.study_progress_parts.stage_kernel_projection import (
    stage_kernel_projection_from_artifact_index,
)
from tests.stage_artifact_index_cases.shared import (
    STUDY_INTAKE_REFS,
    write_json as _write_json,
    write_opl_physical_stage_attempt as _write_opl_physical_stage_attempt,
    write_stage_native_contract as _write_stage_native_contract,
    write_text as _write_text,
)


pytestmark = pytest.mark.meta

STAGE_ID = "07-independent_review_and_revision"
ATTEMPT_ID = "attempt-001"
REQUIRED_CHECKS = [
    "role",
    "hash",
    "source",
    "current_truth",
    "receipt_authority",
    "lineage",
    "retention_restore",
    "domain_validation",
]
AUTHORITY_BOUNDARY = {
    "derived_projection": True,
    "writes_mas_truth": False,
    "writes_publication_eval_latest": False,
    "writes_controller_decision_latest": False,
    "claims_publication_ready": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_artifact_mutation": False,
    "file_presence_counts_as_consumability_authority": False,
    "manifest_hash_counts_as_consumability_authority": False,
    "manifest_validity_counts_as_semantic_receipt": False,
    "read_model_counts_as_consumability_authority": False,
}


def _write_local_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _valid_owner_receipt() -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_owner_receipt",
        "schema_version": 1,
        "stage_id": STAGE_ID,
        "attempt_id": ATTEMPT_ID,
        "authority_type": "medical_owner_receipt",
        "receipt_ref": f"mas-owner-receipt:{STAGE_ID}:{ATTEMPT_ID}",
        "schema_refs": [
            "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
        ],
        "capability_refs": [
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/medical_owner_receipt",
        ],
        "domain_semantic_refs": {
            "owner_route_refs": [f"owner-route:{STAGE_ID}:{ATTEMPT_ID}"],
            "medical_owner_receipt_refs": [
                f"mas-owner-receipt:{STAGE_ID}:{ATTEMPT_ID}"
            ],
        },
        "owner": "MedAutoScience",
    }


def test_stage_artifact_index_consumability_gate_exposes_fail_closed_owner_drilldown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    physical = _write_opl_physical_stage_attempt(
        tmp_path / "opl-state",
        study_id="001-risk",
        stage_id="01-study_intake",
        attempt_id="attempt-001",
        output_ref="study_truth_snapshot.json",
    )
    manifest_path = Path(physical["manifest_ref"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["decision_receipt_refs"] = []
    manifest["restore_refs"] = []
    manifest["retention_refs"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    gate = index["stages"][0]["artifact_classification"]["consumability"]
    assert gate["surface_kind"] == "stage_artifact_consumability_projection"
    assert gate["required_checks"] == REQUIRED_CHECKS
    assert gate["status"] == "blocked"
    assert gate["fail_closed"] is True
    assert gate["failed_checks"] == ["retention_restore", "domain_validation"]
    assert gate["next_owner_delta"] == {
        "surface_kind": "stage_artifact_consumability_owner_delta",
        "owner": "MedAutoScience",
        "action": "emit_stage_artifact_consumability_receipt_or_typed_blocker",
        "reason": "artifact_consumability_gate_failed:retention_restore,domain_validation",
        "stage_id": "01-study_intake",
        "attempt_id": "attempt-001",
        "blocked_surface": "stage_artifact_consumability_gate",
        "required_refs": [
            "retention_ref_or_restore_ref",
            "domain_semantic_receipt_ref_or_typed_blocker_ref",
        ],
        "source_ref": physical["manifest_ref"],
        "source_kind": "stage_manifest",
    }
    assert gate["insufficient_authority_refs"] == [
        "file_presence",
        "manifest_hash",
        "manifest_structural_validity",
        "read_model_projection",
    ]
    assert gate["authority_boundary"] == AUTHORITY_BOUNDARY


def test_stage_artifact_index_stage_gate_declares_required_checks_and_non_authority_refs(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_stage_native_contract(
        study_root,
        stage_id="01-study_intake",
        refs=STUDY_INTAKE_REFS,
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    gate = index["stages"][0]["consumability_gate"]
    assert gate["surface_kind"] == "stage_artifact_consumability_gate"
    assert gate["required_checks"] == REQUIRED_CHECKS
    assert gate["status"] == "ready_for_consumability_validation"
    assert gate["failed_checks"] == []
    assert gate["next_owner_delta"] is None
    assert gate["insufficient_authority_refs"] == [
        "file_presence",
        "manifest_hash",
        "manifest_structural_validity",
        "read_model_projection",
    ]
    assert gate["authority_boundary"] == AUTHORITY_BOUNDARY


def test_stage_kernel_projection_carries_consumability_gate_drilldown() -> None:
    result = stage_kernel_projection_from_artifact_index(
        {
            "surface_kind": "stage_artifact_index",
            "study_root": "/tmp/study",
            "current_stage": {"stage_id": STAGE_ID},
            "next_owner_action": {
                "owner": STAGE_ID,
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
            },
            "stages": [
                {
                    "stage_id": STAGE_ID,
                    "stage_progress_status": "artifact_contract_required",
                    "required_output_refs": [
                        {"role": "reviewer_record", "ref": "outputs/review.json"}
                    ],
                    "stage_folder_contract": {
                        "manifest_ref": "stage_manifest.json",
                        "receipt_ref": "receipts/owner_receipt.json",
                    },
                    "artifact_classification": {
                        "current": [],
                        "missing": [],
                        "fail_closed_reason": "receipt_required",
                        "owner_receipt_refs": [],
                        "typed_blocker_refs": [],
                        "decision_receipt_refs": [],
                        "consumability": {
                            "surface_kind": "stage_artifact_consumability_projection",
                            "required_checks": REQUIRED_CHECKS,
                            "status": "blocked",
                            "fail_closed": True,
                            "checks": {
                                "role": True,
                                "hash": True,
                                "source": True,
                                "current_truth": False,
                                "receipt_authority": False,
                                "lineage": False,
                                "retention_restore": False,
                                "domain_validation": False,
                            },
                            "failed_checks": [
                                "current_truth",
                                "receipt_authority",
                                "lineage",
                                "retention_restore",
                                "domain_validation",
                            ],
                            "next_owner_delta": {
                                "owner": "MedAutoScience",
                                "action": "emit_stage_artifact_consumability_receipt_or_typed_blocker",
                            },
                            "authority_boundary": AUTHORITY_BOUNDARY,
                        },
                        "semantic_validation": {"status": "missing_domain_receipt"},
                        "promotion": {"state": "receipt_required"},
                    },
                    "current_pointer": {"promotion_state": "receipt_required"},
                    "physical_stage_folder_kernel": {"status": "missing"},
                }
            ],
        }
    )

    gate = result["artifact_consumability_gate"]
    assert gate["surface_kind"] == "stage_artifact_consumability_projection"
    assert gate["required_checks"] == REQUIRED_CHECKS
    assert gate["failed_checks"] == [
        "current_truth",
        "receipt_authority",
        "lineage",
        "retention_restore",
        "domain_validation",
    ]
    assert gate["next_owner_delta"]["owner"] == "MedAutoScience"
    assert gate["authority_boundary"] == AUTHORITY_BOUNDARY


def test_stage_run_kernel_exposes_consumability_gate_without_promoting_manifest_hash_read_model(
    tmp_path: Path,
) -> None:
    stage_root = tmp_path / "stage_outputs" / STAGE_ID
    _write_local_json(
        stage_root / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "attempt_id": ATTEMPT_ID,
            "terminal_status": "success",
            "required_outputs": ["outputs/review.json"],
            "present_outputs": ["outputs/review.json"],
            "output_hashes": [{"path": "outputs/review.json", "sha256": "0" * 64}],
            "projection_refs": ["projection/current_owner_delta.json"],
        },
    )

    projection = stage_run_kernel_projection_from_stage_folder(stage_root)

    assert projection["status"] == "Terminalizing"
    assert projection["completion_authority"] is None
    assert projection["artifact_consumability_gate"]["status"] == "blocked"
    assert projection["artifact_consumability_gate"]["failed_checks"] == [
        "current_truth",
        "receipt_authority",
        "lineage",
        "retention_restore",
        "domain_validation",
    ]
    assert projection["artifact_consumability_gate"]["next_owner_delta"]["owner"] == (
        "MedAutoScience"
    )
    assert projection["artifact_consumability_gate"]["authority_boundary"] == AUTHORITY_BOUNDARY
    assert projection["state_invariants"]["artifact_consumability_gate_required"] is True
    assert projection["state_invariants"]["manifest_hash_counts_as_consumable"] is False
    assert projection["state_invariants"]["read_model_counts_as_consumable"] is False


def test_stage_run_kernel_consumability_gate_passes_for_domain_owner_receipt_closeout(
    tmp_path: Path,
) -> None:
    stage_root = tmp_path / "stage_outputs" / STAGE_ID
    _write_local_json(stage_root / "outputs" / "review.json", {"status": "accepted"})
    _write_local_json(stage_root / "lineage" / "prov.json", {"attempt_id": ATTEMPT_ID})
    _write_local_json(stage_root / "receipts" / "owner_receipt.json", _valid_owner_receipt())
    _write_local_json(
        stage_root / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "attempt_id": ATTEMPT_ID,
            "terminal_status": "success",
            "required_outputs": ["outputs/review.json"],
            "present_outputs": ["outputs/review.json"],
            "required_role_artifacts": [
                {"role": "reviewer_record", "ref": "outputs/review.json"}
            ],
            "output_hashes": [{"path": "outputs/review.json", "sha256": "0" * 64}],
            "owner_receipt_refs": ["receipts/owner_receipt.json"],
            "lineage_refs": ["lineage/prov.json"],
            "retention_refs": ["retention-ledger:review"],
            "restore_refs": ["restore-index:review"],
            "current_pointer_ref": "projection/current.json",
            "current_pointer_state": "current_pointer_promoted",
            "domain_decision_receipt_refs": [
                f"mas-domain-decision:{STAGE_ID}:{ATTEMPT_ID}"
            ],
        },
    )

    projection = stage_run_kernel_projection_from_stage_folder(stage_root)

    assert projection["status"] == "DomainAccepted"
    assert projection["completion_authority"] == "owner_receipt"
    assert projection["artifact_consumability_gate"]["status"] == "passed"
    assert projection["artifact_consumability_gate"]["failed_checks"] == []
    assert projection["artifact_consumability_gate"]["next_owner_delta"] is None
    assert projection["artifact_consumability_gate"]["authority_boundary"] == AUTHORITY_BOUNDARY
