from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.stage_artifact_materializer import materialize_stage_artifact_delta
from med_autoscience.controllers.stage_run_kernel import stage_run_kernel_projection_from_stage_folder
from med_autoscience.runtime_protocol import domain_authority_refs_index

from .helpers import TERMINAL_HANDOFF_STAGE_ID, attach_publication_handoff_closeout_binding


def test_execute_dispatch_writes_publication_handoff_owner_receipt_when_terminal_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(study_root / "study.yaml", {"study_id": study_id})
    materialize_stage_artifact_delta(
        study_id=study_id,
        study_root=study_root,
        workspace_root=profile.workspace_root,
        apply=True,
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
            "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
    )
    attach_publication_handoff_closeout_binding(dispatch, study_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_handoff_owner_gate.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    readiness = {
        "surface": "medical_paper_readiness",
        "schema_version": 1,
        "study_root": str(study_root),
        "overall_status": "ready",
        "ready_count": 1,
        "required_count": 1,
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "status": "present",
                "required_for_ready": True,
            }
        ],
        "next_action": {
            "action_id": "continue_managed_execution",
            "surface_key": None,
        },
    }
    _write_json(
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        readiness,
    )
    index_before = domain_authority_refs_index.inspect_authority_refs_index(
        domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root)
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_handoff_owner_gate",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    receipt_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "handoff_owner_receipt.json"
    )
    stage_receipt_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "owner_receipt.json"
    )
    blocker_path = stage_receipt_path.parent / "typed_blocker.json"
    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "publication_handoff_owner_gate.evaluate_terminal_handoff"
    assert receipt_path.is_file()
    assert stage_receipt_path.is_file()
    assert not blocker_path.exists()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["receipt_kind"] == "publication_handoff_owner_gate"
    assert receipt["receipt_status"] == "ready_for_human_submission_handoff"
    assert receipt["closeout_binding"]["closeout_refs"] == [
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat-publication-handoff.json"
    ]
    assert receipt["source_fingerprint"] == (
        "truth-source::003-dpcc-primary-care-phenotype-treatment-gap::publication-handoff-binding"
    )
    assert receipt["stage_run_id"] == f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}"
    assert receipt["can_authorize_publication_ready"] is False
    assert receipt["can_authorize_submission_ready"] is False
    manifest = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "08-publication_package_handoff"
            / "stage_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["owner_receipt_refs"] == [
        "handoff_owner_receipt.json",
        "receipts/owner_receipt.json",
    ]
    assert manifest["closeout_binding_refs"] == [
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat-publication-handoff.json"
    ]
    current_pointer = json.loads((stage_receipt_path.parents[1] / "current.json").read_text(encoding="utf-8"))
    assert current_pointer["current_stage"]["status"] == "success"
    assert current_pointer["current_stage"]["terminal_outcome_kind"] == "owner_receipt"
    current_owner_delta = json.loads(
        (stage_receipt_path.parents[1] / "projection" / "current_owner_delta.json").read_text(encoding="utf-8")
    )
    assert current_owner_delta["latest_owner_answer_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json"
    )
    assert current_owner_delta["latest_owner_answer_kind"] == "owner_receipt"
    assert current_owner_delta["delta_id"] == current_owner_delta["hard_gate"]["owner_answer_idempotency_key"]
    stage_run = stage_run_kernel_projection_from_stage_folder(
        study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    )
    assert stage_run["status"] == "DomainAccepted"
    assert stage_run["current_owner_delta"]["owner"] == "human_gate"
    assert stage_run["current_owner_delta"]["action"] == "human_submission_decision"
    assert stage_run["closeout_binding"]["source_fingerprint"] == (
        "truth-source::003-dpcc-primary-care-phenotype-treatment-gap::publication-handoff-binding"
    )
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    index = domain_authority_refs_index.inspect_authority_refs_index(
        domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root)
    )
    assert index["tables"]["dispatch_receipts"] == index_before["tables"].get("dispatch_receipts", 0) + 1
    assert index["tables"]["paper_work_unit_receipts"] == index_before["tables"].get("paper_work_unit_receipts", 0)
