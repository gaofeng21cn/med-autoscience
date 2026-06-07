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

from .helpers import (
    TERMINAL_HANDOFF_STAGE_ID,
    assert_opl_closeout_binding,
    attach_publication_handoff_closeout_binding,
    remove_opl_execution_authorization,
)


def test_execute_dispatch_writes_publication_handoff_typed_blocker_when_readiness_not_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
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
        "overall_status": "blocked",
        "ready_count": 0,
        "required_count": 1,
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "status": "missing",
                "required_for_ready": True,
            }
        ],
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
        },
    }
    _write_json(
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        readiness,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_handoff_owner_gate",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    blocker_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_callable_surface"] == "publication_handoff_owner_gate.evaluate_terminal_handoff"
    assert blocker_path.is_file()
    blocker = json.loads(blocker_path.read_text(encoding="utf-8"))
    assert blocker["authority_type"] == "typed_blocker"
    assert_opl_closeout_binding(
        blocker["closeout_binding"],
        study_id=study_id,
        receipt_ref="artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
    )
    assert blocker["stage_run_id"] == f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}"
    assert blocker["stage_manifest_ref"].endswith(
        "artifacts/stage_outputs/08-publication_package_handoff/stage_manifest.json"
    )
    assert blocker["current_pointer_ref"].endswith(
        "artifacts/stage_outputs/08-publication_package_handoff/current.json"
    )
    assert blocker["can_authorize_publication_ready"] is False
    assert blocker["can_authorize_submission_ready"] is False
    manifest = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "08-publication_package_handoff"
            / "stage_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["closeout_binding_refs"] == [
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat-publication-handoff.json"
    ]
    assert manifest["source_fingerprint"] == "truth-source::002-dm-china-us-mortality-attribution::publication-handoff-binding"
    assert_opl_closeout_binding(manifest["closeout_binding"], study_id=study_id)
    current_pointer = json.loads((blocker_path.parents[1] / "current.json").read_text(encoding="utf-8"))
    assert current_pointer["current_stage"]["status"] == "blocked"
    assert current_pointer["current_stage"]["terminal_outcome_kind"] == "typed_blocker"
    assert_opl_closeout_binding(current_pointer["closeout_binding"], study_id=study_id)
    current_owner_delta = json.loads((blocker_path.parents[1] / "projection" / "current_owner_delta.json").read_text(encoding="utf-8"))
    assert current_owner_delta["latest_owner_answer_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert current_owner_delta["latest_owner_answer_kind"] == "typed_blocker"
    assert current_owner_delta["delta_id"] == current_owner_delta["hard_gate"]["owner_answer_idempotency_key"]
    assert_opl_closeout_binding(current_owner_delta["closeout_binding"], study_id=study_id)
    assert current_owner_delta["provider_attempt_ref"] == f"opl://stage-attempts/{study_id}/publication-handoff"
    assert current_owner_delta["attempt_lease_ref"] == f"opl://stage-attempts/{study_id}/publication-handoff/leases/current"
    assert current_owner_delta["execution_authorization_decision_ref"] == (
        f"opl://stage-attempts/{study_id}/publication-handoff/execution-authorizations/current"
    )
    assert current_owner_delta["hard_gate"]["owner_answer_provider_attempt_ref"] == (
        f"opl://stage-attempts/{study_id}/publication-handoff"
    )
    assert current_owner_delta["hard_gate"]["owner_answer_attempt_lease_ref"] == (
        f"opl://stage-attempts/{study_id}/publication-handoff/leases/current"
    )
    assert current_owner_delta["hard_gate"]["owner_answer_execution_authorization_decision_ref"] == (
        f"opl://stage-attempts/{study_id}/publication-handoff/execution-authorizations/current"
    )
    stage_run = stage_run_kernel_projection_from_stage_folder(
        study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    )
    assert stage_run["status"] == "TypedBlocked"
    assert stage_run["current_owner_delta"]["action"] == "complete_medical_paper_readiness_surface"
    assert stage_run["closeout_binding"]["source_fingerprint"] == (
        "truth-source::002-dm-china-us-mortality-attribution::publication-handoff-binding"
    )
    assert_opl_closeout_binding(
        stage_run["closeout_binding"],
        study_id=study_id,
        receipt_ref="artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
    )
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_execute_dispatch_requires_opl_authorization_before_publication_handoff_durable_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
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
    remove_opl_execution_authorization(dispatch)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_handoff_owner_gate.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    stage_root = study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    materialized_receipt = json.loads((stage_root / "handoff_owner_receipt.json").read_text(encoding="utf-8"))
    materialized_stage_receipt = json.loads((stage_root / "receipts" / "owner_receipt.json").read_text(encoding="utf-8"))
    _write_json(
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        {
            "surface": "medical_paper_readiness",
            "schema_version": 1,
            "study_root": str(study_root),
            "overall_status": "blocked",
            "ready_count": 0,
            "required_count": 1,
            "capability_surfaces": [
                {
                    "surface_key": "literature_provider_runtime",
                    "status": "missing",
                    "required_for_ready": True,
                }
            ],
            "next_action": {
                "action_id": "complete_medical_paper_readiness_surface",
                "surface_key": "literature_provider_runtime",
            },
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_handoff_owner_gate",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert json.loads((stage_root / "handoff_owner_receipt.json").read_text(encoding="utf-8")) == materialized_receipt
    assert json.loads((stage_root / "receipts" / "owner_receipt.json").read_text(encoding="utf-8")) == materialized_stage_receipt
    assert not (stage_root / "receipts" / "typed_blocker.json").exists()
    assert not (stage_root / "current.json").exists()
    stage_run = stage_run_kernel_projection_from_stage_folder(stage_root)
    assert stage_run["status"] == "DomainAccepted"
    assert stage_run["current_owner_delta"]["action"] == "publication_handoff_owner_gate"


def test_execute_dispatch_writes_publication_handoff_typed_blocker_when_readiness_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_handoff_owner_gate",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    blocker_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_missing"
    assert blocker_path.is_file()
    blocker = json.loads(blocker_path.read_text(encoding="utf-8"))
    assert blocker["authority_type"] == "typed_blocker"
    assert blocker["decision"]["blocked_surfaces"] == ["medical_paper_readiness"]
    assert blocker["closeout_binding"]["source_fingerprint"] == (
        "truth-source::002-dm-china-us-mortality-attribution::publication-handoff-binding"
    )
    assert not (study_root / "artifacts" / "medical_paper" / "readiness.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
