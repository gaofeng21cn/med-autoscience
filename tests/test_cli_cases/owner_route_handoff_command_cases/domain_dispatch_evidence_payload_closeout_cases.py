from __future__ import annotations

from .shared import *  # noqa: F403,F401
import builtins


def test_domain_handler_dispatch_evidence_payload_does_not_require_pdf_dependency(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "pypdf"
            or module_name.startswith("pypdf.")
            or module_name == "med_autoscience.cli"
            or module_name == "med_autoscience.controllers.owner_route_reconcile"
            or module_name == "med_autoscience.controllers.domain_status_projection"
            or module_name == "med_autoscience.controllers.study_runtime_decision"
            or module_name == "med_autoscience.controllers.submission_minimal"
            or module_name.startswith("med_autoscience.controllers.submission_minimal_parts.")
        ):
            sys.modules.pop(module_name, None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ModuleNotFoundError("No module named 'pypdf'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_import_light"
    domain_source = "domain_source_import_light"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_import_light:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_import_light",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "nfpitnet",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert study_ids == (study_id,)
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "runtime_recovery_not_authorized",
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "source_refs": [
                            "artifacts/publication_eval/latest.json",
                            "artifacts/controller_decisions/latest.json",
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": "artifacts/publication_eval/latest.json",
                        },
                    },
                    "owner_route": {
                        "next_owner": "one-person-lab",
                        "owner_reason": "runtime_recovery_not_authorized",
                    },
                }
            ]
        }

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "typed_blocker_payload_ready"
    assert payload["opl_runtime_action_execute_payload"]["source_fingerprint"] == stage_attempt_source


def test_domain_handler_dispatch_evidence_payload_projects_stage_attempt_closeout_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_9c4ab82e4e1fdef49b662c54"
    stage_attempt_source = "mas_default_executor_source_5e75b4fe5fdc3311bffba5c5"
    domain_source = "6dc238f98af6b118"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    typed_blocker_ref = (
        "artifacts/supervision/opl_current_control_state/latest.json#/studies/0/"
        "domain_authority_handoff/typed_blocker"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "status": "blocked",
            "blocked_reason": "owner_route_blocked",
            "domain_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "blocker_kind": "owner_route_blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "next_owner": "external_supervisor",
                "provider_completion_is_domain_completion": False,
            },
            "execution_observation": {
                "execution_status": "blocked",
                "blocked_reason": "current_owner_route_missing",
                "owner_route_current": False,
            },
            "closeout_refs": [
                closeout_ref,
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/default_executor_execution/latest.json",
                dispatch_ref,
                "artifacts/supervision/opl_current_control_state/latest.json",
            ],
            "typed_blocker_ref": typed_blocker_ref,
            "owner_receipt_ref": None,
            "provider_completion_is_domain_completion": False,
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "nfpitnet",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                        },
                    },
                    "owner_route": {
                        "next_owner": "external_supervisor",
                        "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    },
                }
            ]
        }

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "typed_blocker_payload_ready"
    assert_stable_blocker_reason(
        payload,
        blocker_class="stage_attempt_closeout_blocked",
        detail_reason="stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch",
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == [typed_blocker_ref]
    assert closeout_ref in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:blocked_reason=owner_route_blocked" in record_payload[
        "evidence_refs"
    ]
    assert "stage-attempt-closeout:execution_blocked_reason=current_owner_route_missing" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_stage_attempt_owner_receipt_closeout(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_id = "sat_2b6eac11610af2c3a80ef14c"
    stage_attempt_source = "mas_default_executor_source_880838dc77dfd024def89a98"
    domain_source = "79a7c0b25a33e01d"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json"
    )
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        f"consumer/default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    publication_eval_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/publication_eval/"
        "latest.json"
    )
    request_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "requests/ai_reviewer/latest.json"
    )
    controller_decision_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "controller_decisions/20260527T162207Z-route_back_same_line.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "executed",
            "owner": "ai_reviewer",
            "owner_reason": "ai_reviewer_assessment_required",
            "route_outcome": "publication_eval_latest_materialized",
            "owner_receipt": {
                "status": "executed",
                "owner": "ai_reviewer",
                "owner_callable_surface": (
                    "ai_reviewer_publication_eval_workflow."
                    "run_ai_reviewer_publication_eval_workflow"
                ),
                "request_ref": request_ref,
                "publication_eval_ref": publication_eval_ref,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "domain_execution": {
                "execution_status": "executed",
                "domain_owner": "ai_reviewer",
                "request_ref": request_ref,
                "publication_eval_ref": publication_eval_ref,
                "controller_decision_ref": controller_decision_ref,
            },
            "verification": {
                "quality_status": "blocked",
                "claim_evidence_alignment_status": "ready",
                "remaining_publication_quality_missing_fields": [
                    "claim_evidence_alignment_digest",
                    "owner_authorized_publication_gate_recheck",
                ],
            },
            "artifact_delta_refs": [
                publication_eval_ref,
                controller_decision_ref,
            ],
            "closeout_refs": [
                closeout_ref,
                dispatch_ref,
                request_ref,
                publication_eval_ref,
                controller_decision_ref,
            ],
            "domain_completion_claimed": False,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "ai_reviewer_assessment_required",
                    "domain_transition": {
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "owner": "ai_reviewer",
                        "completion_receipt_consumption": {"status": "missing"},
                    },
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "owner_reason": "ai_reviewer_assessment_required",
                    },
                }
            ]
        }

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_receipt_payload_ready"
    assert payload["payload_reason"] == (
        "stage_attempt_closeout_owner_receipt_observed_for_default_executor_dispatch"
    )
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["mode"] == "refs_only_domain_owned_success_payload"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == []
    assert record_payload["domain_owner_receipt_refs"] == [f"{closeout_ref}#owner_receipt"]
    assert record_payload["domain_receipt_refs"] == record_payload["domain_owner_receipt_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert publication_eval_ref in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:status=executed" in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:route_outcome=publication_eval_latest_materialized" in record_payload[
        "evidence_refs"
    ]
    assert record_payload["no_regression_refs"]
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False


def test_domain_handler_dispatch_evidence_payload_accepts_closed_domain_owner_refs_closeout(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_ab7f4e500c9554779b2f0198"
    stage_attempt_source = "mas_default_executor_source_2d1cf261e40558b870fe87b0"
    domain_source = "26cb24d371fbbf78"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/"
        "a92cc919119d56b6b90c90f8.json"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        f"consumer/default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    record_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/publication_eval/"
        "ai_reviewer_responses/20260529T041903Z_publication_eval_record.json"
    )
    payload_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "requests/ai_reviewer/record_production_payloads/return_to_ai_reviewer_workflow_payload.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "closed_with_domain_owner_refs",
            "owner_receipt": {
                "authority": "ai_reviewer_record_materialization",
                "controller": "materialize-ai-reviewer-publication-eval-record",
                "stage_attempt_id": stage_attempt_id,
                "stage_id": "domain_owner/default-executor-dispatch",
                "action_type": "return_to_ai_reviewer_workflow",
                "receipt_id": f"ai-reviewer-record-materialized::{stage_attempt_id}::20260529T041903Z",
                "status": "closed_with_domain_owner_refs",
                "publication_eval_record_ref": record_ref,
                "publication_eval_latest_write_authorized": False,
                "controller_decision_write_authorized": False,
                "paper_package_mutation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
                "domain_ready_verdict": "not_claimed",
            },
            "domain_execution": {
                "action_type": "return_to_ai_reviewer_workflow",
                "execution_status": "executed",
                "domain_owner": "ai_reviewer",
                "owner_callable_surface": "publication materialize-ai-reviewer-record",
                "required_output_surface": (
                    "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
                ),
                "publication_eval_record_ref": record_ref,
                "publication_eval_surface": "not_written",
            },
            "verification": {
                "forbidden_surface_mutation_avoided": True,
                "publication_eval_latest_write_observed": False,
                "controller_decision_write_observed": False,
            },
            "closeout_refs": [
                closeout_ref,
                record_ref,
                payload_ref,
                dispatch_ref,
            ],
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {"studies": [{"study_id": study_id}]}

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_receipt_payload_ready"
    assert payload["payload_reason"] == (
        "stage_attempt_closeout_owner_receipt_observed_for_default_executor_dispatch"
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["typed_blocker_refs"] == []
    assert record_payload["domain_owner_receipt_refs"] == [f"{closeout_ref}#owner_receipt"]
    assert record_ref in record_payload["evidence_refs"]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_rejects_record_only_archive_closeout(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_0f999f31a1cf114964f5ba5f"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "materialized_record_only_archive",
            "owner_receipt": None,
            "domain_execution": {
                "execution_status": "materialized_record_only_archive",
                "domain_owner": "ai_reviewer",
                "publication_eval_record_ref": (
                    "studies/002-dm-china-us-mortality-attribution/artifacts/publication_eval/"
                    "ai_reviewer_responses/20260529T042258Z_publication_eval_record.json"
                ),
            },
            "provider_completion_is_domain_completion": False,
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": "mas_default_executor_source_16152f855fba8292aca4010a",
                "domain_source_fingerprint": "9ed5ba80c04802e1",
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_ref": (
                    "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
                    "default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/"
                    "4ac8b7dbd5c500c6e0ffcfcd.json"
                ),
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {"studies": [{"study_id": study_id}]}

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "consumed_ai_reviewer_routeback_not_observed"
