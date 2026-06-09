from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.controllers.stage_run_kernel import (
    stage_run_kernel_projection_from_stage_folder,
)
from med_autoscience.controllers.study_progress_parts.stage_kernel_projection import (
    stage_kernel_projection_from_artifact_index,
)


pytestmark = pytest.mark.meta

STAGE_ID = "07-independent_review_and_revision"
ATTEMPT_ID = "ai-reviewer-rebuild-001"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_stage_folder(
    tmp_path: Path,
    *,
    terminal_status: str = "success",
    owner_receipt: dict[str, Any] | None = None,
    typed_blocker: dict[str, Any] | None = None,
) -> Path:
    stage_root = tmp_path / "stage_outputs" / STAGE_ID
    for child in ("inputs", "outputs", "receipts", "lineage"):
        (stage_root / child).mkdir(parents=True, exist_ok=True)
    _write_json(
        stage_root / "inputs" / "consumed_artifact_refs.json",
        {
            "artifact_refs": [
                "paper/current_draft.md",
                "artifacts/publication_eval/latest.json",
            ],
        },
    )
    _write_json(
        stage_root / "outputs" / "ai_reviewer_record.json",
        {
            "eval_id": "publication-eval::dm003::2026-06-05T00:00:00Z::ai-reviewer",
        },
    )
    _write_json(
        stage_root / "lineage" / "prov.json",
        {
            "surface_kind": "stage_lineage_prov",
            "attempt_id": ATTEMPT_ID,
        },
    )
    receipt_refs: list[str] = []
    typed_blocker_refs: list[str] = []
    if owner_receipt is not None:
        _write_json(stage_root / "receipts" / "owner_receipt.json", owner_receipt)
        receipt_refs.append("receipts/owner_receipt.json")
    if typed_blocker is not None:
        _write_json(stage_root / "receipts" / "typed_blocker.json", typed_blocker)
        typed_blocker_refs.append("receipts/typed_blocker.json")
    _write_json(
        stage_root / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "stage_run_id": "stage-run::dm003::ai-reviewer-rebuild",
            "attempt_id": ATTEMPT_ID,
            "work_unit": "ai_reviewer_publication_eval_rebuild",
            "terminal_status": terminal_status,
            "required_outputs": ["outputs/ai_reviewer_record.json"],
            "present_outputs": ["outputs/ai_reviewer_record.json"],
            "input_refs": ["inputs/consumed_artifact_refs.json"],
            "owner_receipt_refs": receipt_refs,
            "typed_blocker_refs": typed_blocker_refs,
            "lineage_refs": ["lineage/prov.json"],
        },
    )
    return stage_root


def _assert_current_owner_delta(
    actual: dict[str, Any],
    expected_core: dict[str, Any],
) -> None:
    for key, value in expected_core.items():
        assert actual[key] == value
    assert actual["projection_role"] == (
        "mas_stage_local_owner_delta_projection_not_opl_current_owner_delta_publish"
    )
    assert actual["stage_transition_authority_required"] is True
    assert actual["stage_run_current_authority"] == "opl_stage_transition_authority_only"
    assert actual["authority_boundary"] == {
        "can_write_stage_current_pointer": False,
        "can_write_stage_run_terminal_state": False,
        "can_publish_opl_current_owner_delta": False,
        "provider_completion_counts_as_stage_transition": False,
        "read_model_update_counts_as_stage_transition": False,
        "worklist_update_counts_as_stage_transition": False,
    }


def test_stage_run_kernel_accepts_manifest_backed_ai_reviewer_owner_receipt(
    tmp_path: Path,
) -> None:
    stage_root = _write_stage_folder(
        tmp_path,
        owner_receipt={
            "surface_kind": "mas_stage_owner_receipt",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "attempt_id": ATTEMPT_ID,
            "authority_type": "medical_owner_receipt",
            "receipt_ref": "mas-owner-receipt:dm003:ai-reviewer-rebuild:001",
            "schema_refs": [
                "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
            ],
            "capability_refs": [
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/medical_owner_receipt",
            ],
            "domain_semantic_refs": {
                "owner_route_refs": ["owner-route:dm003:ai-reviewer"],
                "medical_owner_receipt_refs": [
                    "mas-owner-receipt:dm003:ai-reviewer-rebuild:001"
                ],
            },
            "owner": "MedAutoScience",
            "next_owner_delta": {
                "owner": "publication_supervisor",
                "action": "publication_gate",
                "reason": "ai_reviewer_record_consumed",
            },
            "publication_eval_projection_ref": "artifacts/publication_eval/latest.json",
        },
    )

    projection = stage_run_kernel_projection_from_stage_folder(stage_root)

    assert projection["surface_kind"] == "stage_run_kernel_projection"
    assert projection["status"] == "DomainAccepted"
    assert projection["completion_authority"] == "owner_receipt"
    _assert_current_owner_delta(
        projection["current_owner_delta"],
        {
            "owner": "publication_supervisor",
            "action": "publication_gate",
            "reason": "ai_reviewer_record_consumed",
            "source_ref": str((stage_root / "receipts" / "owner_receipt.json").resolve()),
            "source_kind": "owner_receipt",
        },
    )
    assert projection["evidence_projection"] == {
        "latest_json_ref": "artifacts/publication_eval/latest.json",
        "latest_json_is_authority": False,
    }


def test_stage_run_kernel_projects_manifest_backed_typed_blocker_as_current_owner_delta(
    tmp_path: Path,
) -> None:
    stage_root = _write_stage_folder(
        tmp_path,
        terminal_status="blocked",
        typed_blocker={
            "surface_kind": "mas_stage_typed_blocker",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "attempt_id": ATTEMPT_ID,
            "authority_type": "typed_blocker",
            "receipt_ref": "typed-blocker:dm003:ai-reviewer-rebuild:001",
            "schema_refs": [
                "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
            ],
            "capability_refs": [
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/typed_blocker",
            ],
            "domain_semantic_refs": {
                "typed_blocker_refs": [
                    "typed-blocker:dm003:ai-reviewer-rebuild:001"
                ],
            },
            "owner": "ai_reviewer",
            "blocker_id": "ai_reviewer_closeout_packet_missing_currentness_trace",
            "required_input": "current_manuscript.currentness_checks",
            "blocked_surface": "ai_reviewer_publication_eval_rebuild",
            "next_safe_action": "rerun_ai_reviewer_with_current_manuscript_binding",
        },
    )

    projection = stage_run_kernel_projection_from_stage_folder(stage_root)

    assert projection["status"] == "TypedBlocked"
    assert projection["completion_authority"] == "typed_blocker"
    _assert_current_owner_delta(
        projection["current_owner_delta"],
        {
            "owner": "ai_reviewer",
            "action": "rerun_ai_reviewer_with_current_manuscript_binding",
            "reason": "ai_reviewer_closeout_packet_missing_currentness_trace",
            "required_input": "current_manuscript.currentness_checks",
            "blocked_surface": "ai_reviewer_publication_eval_rebuild",
            "source_ref": str((stage_root / "receipts" / "typed_blocker.json").resolve()),
            "source_kind": "typed_blocker",
        },
    )
    assert projection["state_invariants"]["file_presence_counts_as_completion"] is False
    assert projection["state_invariants"]["provider_completed_counts_as_completion"] is False


def test_stage_run_kernel_does_not_complete_from_outputs_or_provider_terminal_status(
    tmp_path: Path,
) -> None:
    stage_root = _write_stage_folder(tmp_path, terminal_status="success")

    projection = stage_run_kernel_projection_from_stage_folder(stage_root)

    assert projection["status"] == "Terminalizing"
    assert projection["completion_authority"] is None
    _assert_current_owner_delta(
        projection["current_owner_delta"],
        {
            "owner": "MedAutoScience",
            "action": "consume_closeout_and_emit_owner_receipt_or_typed_blocker",
            "reason": "manifest_backed_receipt_or_typed_blocker_required",
            "source_ref": str((stage_root / "stage_manifest.json").resolve()),
            "source_kind": "stage_manifest",
        },
    )
    assert projection["evidence_projection"]["outputs_present"] == [
        "outputs/ai_reviewer_record.json"
    ]
    assert projection["state_invariants"]["file_presence_counts_as_completion"] is False
    assert projection["state_invariants"]["provider_completed_counts_as_completion"] is False


def test_stage_kernel_projection_prefers_stage_run_manifest_backed_typed_blocker(
    tmp_path: Path,
) -> None:
    stage_root = _write_stage_folder(
        tmp_path,
        terminal_status="blocked",
        typed_blocker={
            "surface_kind": "mas_stage_typed_blocker",
            "schema_version": 1,
            "stage_id": STAGE_ID,
            "attempt_id": ATTEMPT_ID,
            "authority_type": "typed_blocker",
            "receipt_ref": "typed-blocker:dm003:ai-reviewer-rebuild:001",
            "schema_refs": [
                "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
            ],
            "capability_refs": [
                "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/typed_blocker",
            ],
            "domain_semantic_refs": {
                "typed_blocker_refs": [
                    "typed-blocker:dm003:ai-reviewer-rebuild:001"
                ],
            },
            "owner": "ai_reviewer",
            "blocker_id": "ai_reviewer_closeout_packet_missing_currentness_trace",
            "required_input": "current_manuscript.currentness_checks",
            "blocked_surface": "ai_reviewer_publication_eval_rebuild",
            "next_safe_action": "rerun_ai_reviewer_with_current_manuscript_binding",
        },
    )

    projection = stage_kernel_projection_from_artifact_index(
        {
            "surface_kind": "stage_artifact_index",
            "current_stage": {"stage_id": STAGE_ID},
            "stages": [
                {
                    "stage_id": STAGE_ID,
                    "stage_progress_status": "terminal_delivered",
                    "required_output_refs": [
                        {
                            "role": "ai_reviewer_record",
                            "ref": "outputs/ai_reviewer_record.json",
                        }
                    ],
                    "stage_folder_contract": {
                        "stage_folder_ref": str(stage_root),
                        "manifest_ref": str(stage_root / "stage_manifest.json"),
                    },
                    "artifact_classification": {
                        "current": ["outputs/ai_reviewer_record.json"],
                        "owner_receipt_refs": [],
                        "typed_blocker_refs": ["receipts/typed_blocker.json"],
                        "semantic_validation": {"status": "blocked"},
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                    },
                }
            ],
        }
    )

    assert projection["stage_run_kernel"]["status"] == "TypedBlocked"
    assert projection["stage_run_kernel"]["current_owner_delta"]["source_kind"] == "typed_blocker"
    assert projection["current_owner_delta"] == projection["stage_run_kernel"]["current_owner_delta"]
    assert projection["stage_run_kernel"]["evidence_projection"] == {
        "latest_json_ref": None,
        "latest_json_is_authority": False,
        "outputs_present": ["outputs/ai_reviewer_record.json"],
    }
