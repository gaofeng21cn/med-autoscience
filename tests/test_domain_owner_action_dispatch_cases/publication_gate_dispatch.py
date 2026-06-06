from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.stage_artifact_materializer import materialize_stage_artifact_delta
from med_autoscience.controllers.stage_run_kernel import stage_run_kernel_projection_from_stage_folder
from med_autoscience.runtime_protocol import domain_authority_refs_index


TERMINAL_HANDOFF_STAGE_ID = "08-publication_package_handoff"


def _attach_publication_handoff_closeout_binding(dispatch: dict[str, object], *, study_id: str) -> None:
    source_fingerprint = f"truth-source::{study_id}::publication-handoff-binding"
    closeout_ref = (
        "artifacts/supervision/consumer/stage_attempt_closeouts/"
        "sat-publication-handoff.json"
    )
    binding = {
        "surface_kind": "publication_handoff_closeout_binding",
        "stage_run_id": f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}",
        "stage_run_ref": f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}",
        "stage_manifest_ref": (
            f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/stage_manifest.json"
        ),
        "current_pointer_ref": f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/current.json",
        "closeout_refs": [closeout_ref],
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": source_fingerprint,
        "body_included": False,
    }
    dispatch["closeout_binding"] = binding
    dispatch["closeout_refs"] = [closeout_ref]
    dispatch["source_fingerprint"] = source_fingerprint
    dispatch["work_unit_fingerprint"] = source_fingerprint
    dispatch["opl_execution_authorization"] = {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli",
        "provider_attempt_ref": f"opl://stage-attempts/{study_id}/publication-handoff",
        "stage_attempt_id": f"stage-attempt::{study_id}::publication-handoff",
        "attempt_lease_ref": f"opl://stage-attempts/{study_id}/publication-handoff/leases/current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": (
            f"opl://stage-attempts/{study_id}/publication-handoff/execution-authorizations/current"
        ),
    }
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["closeout_binding"] = binding
    prompt_contract["closeout_refs"] = [closeout_ref]
    prompt_contract["source_fingerprint"] = source_fingerprint
    prompt_contract["work_unit_fingerprint"] = source_fingerprint
    prompt_contract["opl_execution_authorization"] = dispatch["opl_execution_authorization"]


def _remove_opl_execution_authorization(dispatch: dict[str, object]) -> None:
    dispatch.pop("opl_execution_authorization", None)
    prompt_contract = dispatch.get("prompt_contract")
    if isinstance(prompt_contract, dict):
        prompt_contract.pop("opl_execution_authorization", None)


def test_execute_dispatch_runs_publication_gate_owner_surface(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-05T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        called["write_quest_root"] = quest_root_arg
        called["report"] = report
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "primary_claim",
                                "source_path": "paper/claim_evidence_map.json",
                                "blocking_reason": "claim_evidence_consistency_failed",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "paper/figures/figure_catalog.json",
                                "blocking_reason": "figure_semantics_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_manifest",
                                "source_path": "paper/submission_minimal/submission_manifest.json",
                                "blocking_reason": "submission_hardening_incomplete",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "artifacts/results/main_result.json",
                                "blocking_reason": "derived_analysis_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "gate_report",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "publication_gate_blocked",
                            },
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.action_execution.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(
        module.action_execution.publication_gate,
        "_materialize_publication_eval_latest",
        fake_materialize_publication_eval_latest,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root
    assert called["write_quest_root"] == quest_root
    assert called["materialize_kwargs"]["report"]["latest_gate_path"].endswith("latest.json")
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_runs_publication_gate_owner_when_terminal_stall_handoff_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
    )
    route.update(
        {
            "truth_epoch": "truth-event-anchor-missing",
            "route_epoch": "truth-event-anchor-missing",
            "source_fingerprint": "truth-snapshot::anchor-missing",
            "work_unit_fingerprint": "truth-snapshot::anchor-missing",
            "idempotency_key": "owner-route::publication-gate-anchor-missing",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::anchor-missing",
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_terminal",
                    "owner_route": route,
                    "prompt_contract": dispatch["prompt_contract"],
                    "repeat_suppression_key": "truth-snapshot::anchor-missing",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-17T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["missing_publication_anchor"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "source_path",
                                "target_id": "publishability_gate",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "missing_publication_anchor",
                            }
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.action_execution.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(
        module.action_execution.publication_gate,
        "_materialize_publication_eval_latest",
        fake_materialize_publication_eval_latest,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
    assert execution["action_class"] == "controller_apply"
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root


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
    _attach_publication_handoff_closeout_binding(dispatch, study_id=study_id)
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
    assert blocker["closeout_binding"]["closeout_refs"] == [
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat-publication-handoff.json"
    ]
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
    current_pointer = json.loads((blocker_path.parents[1] / "current.json").read_text(encoding="utf-8"))
    assert current_pointer["current_stage"]["status"] == "blocked"
    assert current_pointer["current_stage"]["terminal_outcome_kind"] == "typed_blocker"
    current_owner_delta = json.loads((blocker_path.parents[1] / "projection" / "current_owner_delta.json").read_text(encoding="utf-8"))
    assert current_owner_delta["latest_owner_answer_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert current_owner_delta["latest_owner_answer_kind"] == "typed_blocker"
    assert current_owner_delta["delta_id"] == current_owner_delta["hard_gate"]["owner_answer_idempotency_key"]
    stage_run = stage_run_kernel_projection_from_stage_folder(
        study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    )
    assert stage_run["status"] == "TypedBlocked"
    assert stage_run["current_owner_delta"]["action"] == "complete_medical_paper_readiness_surface"
    assert stage_run["closeout_binding"]["source_fingerprint"] == (
        "truth-source::002-dm-china-us-mortality-attribution::publication-handoff-binding"
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
    _remove_opl_execution_authorization(dispatch)
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


def test_provider_hosted_stage_attempt_identity_authorizes_publication_handoff(
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
    _remove_opl_execution_authorization(dispatch)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "publication_handoff_owner_gate"
        / "provider-hosted.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted-publication")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted-publication")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted-publication/leases/frt-provider-hosted-publication/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted-publication/execution-authorizations/frt-provider-hosted-publication/wf-provider-hosted-publication",
    )
    monkeypatch.setenv("OPL_WORKFLOW_ID", "wf-provider-hosted-publication")
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "publication_handoff_owner_gate")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "publication_handoff_owner_gate")
    monkeypatch.setenv("OPL_TASK_ID", "frt-provider-hosted-publication")

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
    assert blocker["closeout_binding"]["provider_attempt_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication"
    )
    assert blocker["closeout_binding"]["attempt_lease_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication/leases/frt-provider-hosted-publication/active"
    )
    assert blocker["closeout_binding"]["attempt_lease_status"] == "active"
    assert blocker["closeout_binding"]["execution_authorization_decision_ref"] == (
        "opl://stage-attempts/sat-provider-hosted-publication/execution-authorizations/frt-provider-hosted-publication/wf-provider-hosted-publication"
    )
    assert blocker["closeout_binding"]["trusted_opl_execution_authorization"] is True
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


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
    _attach_publication_handoff_closeout_binding(dispatch, study_id=study_id)
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
    _attach_publication_handoff_closeout_binding(dispatch, study_id=study_id)
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


def test_default_dispatch_selects_stage_artifact_publication_handoff_over_stale_defaults(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    stale_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=stale_route,
    )
    current_route = _owner_route(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
    )
    current_route["source_refs"] = {
        "work_unit_id": "publication_handoff_owner_gate",
        "work_unit_fingerprint": current_route["work_unit_fingerprint"],
        "owner_route_currentness_basis": {
            "truth_epoch": current_route["truth_epoch"],
            "runtime_health_epoch": current_route["runtime_health_epoch"],
            "work_unit_id": "publication_handoff_owner_gate",
            "work_unit_fingerprint": current_route["work_unit_fingerprint"],
        },
    }
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
            "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
        owner_route=current_route,
    )
    stale_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    current_path = stale_path.parent / "publication_handoff_owner_gate.json"
    _write_json(stale_path, stale_dispatch)
    _write_json(current_path, current_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "publication_handoff_owner_gate",
                            "owner": "publication_gate_owner",
                            "owner_route": current_route,
                        }
                    ],
                    "stage_artifact_index": {
                        "surface_kind": "stage_artifact_index",
                        "current_stage": "08-publication_package_handoff",
                        "next_owner_action": {
                            "action_type": "publication_handoff_owner_gate",
                            "allowed_actions": ["publication_handoff_owner_gate"],
                            "next_owner": "publication_gate_owner",
                            "work_unit_id": "publication_handoff_owner_gate",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_artifact_index.next_owner_action",
                        "allowed_actions": ["publication_handoff_owner_gate"],
                        "next_owner": "publication_gate_owner",
                        "work_unit_id": "publication_handoff_owner_gate",
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [
                {**stale_dispatch, "refs": {"dispatch_path": str(stale_path)}},
                {**current_dispatch, "refs": {"dispatch_path": str(current_path)}},
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [execution["action_type"] for execution in result["executions"]] == [
        "publication_handoff_owner_gate"
    ]
