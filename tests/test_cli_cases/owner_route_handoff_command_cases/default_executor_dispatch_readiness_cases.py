from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_readiness_surface_key_changes_default_executor_source_identity(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    _write_json(study_root / "study.yaml", {"study_id": study_id})

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="complete_medical_paper_readiness_surface.json",
        action_type="complete_medical_paper_readiness_surface",
        next_owner="MedAutoScience",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="MedAutoScience",
            owner_reason="medical_paper_readiness_not_ready",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            work_unit_fingerprint="truth-snapshot::bounded_analysis_candidate_board",
            runtime_health_epoch="runtime-health-event-readiness-001",
            blocked_actions=[],
        ),
    )

    first_decision = {
        "surface": "controller_decision",
        "schema_version": 1,
        "decision_type": "medical_paper_readiness_owner_blocker",
        "generated_at": "2026-06-06T15:00:00Z",
        "source": "medical_paper_readiness.complete_medical_paper_readiness_surface",
        "route_decision": "stable_blocker",
        "runtime_decision": "blocked",
        "blocked_reason": "medical_paper_readiness_missing",
        "readiness_status": "blocked",
        "readiness_next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "bounded_analysis_candidate_board",
            "summary": "补齐 bounded analysis candidate board。",
        },
    }
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(decision_path, first_decision)
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        work_unit_id="complete_medical_paper_readiness_surface",
        work_unit_fingerprint=None,
        owner="MedAutoScience",
        source="controller_decisions.readiness_next_action",
    )

    first_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    first_payload = json.loads(capsys.readouterr().out)
    assert first_exit_code == 0
    first_task = next(
        task
        for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    second_decision = {
        **first_decision,
        "generated_at": "2026-06-06T15:17:29Z",
        "readiness_next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "stop_loss_memo",
            "summary": "补齐 Stop-loss Memo 后再继续自动论文链路。",
        },
    }
    _write_json(decision_path, second_decision)
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        work_unit_id="complete_medical_paper_readiness_surface",
        work_unit_fingerprint=None,
        owner="MedAutoScience",
        source="controller_decisions.readiness_next_action",
    )

    second_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    second_payload = json.loads(capsys.readouterr().out)
    assert second_exit_code == 0
    study_projection = next(study for study in second_payload["studies"] if study["study_id"] == study_id)
    second_task = next(
        task
        for task in second_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    assert study_projection["current_owner_action"]["surface_key"] == "stop_loss_memo"
    assert second_task["payload"]["readiness_surface_identity"] == {
        "action_type": "complete_medical_paper_readiness_surface",
        "surface_key": "stop_loss_memo",
        "source": "controller_decisions.readiness_next_action",
    }
    assert "surface_key" not in second_task["payload"]
    assert "prompt_contract" not in second_task["payload"]
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "medical_paper_readiness"
        / "latest.json"
    ).exists()
    assert second_task["source_fingerprint"] != first_task["source_fingerprint"]
    assert second_task["dedupe_key"] != first_task["dedupe_key"]


def test_domain_handler_export_carries_stage_current_provider_admission_identity(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    _write_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    typed_blocker_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    work_unit_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=dispatch_path.name,
        action_type="complete_medical_paper_readiness_surface",
        next_owner="MedAutoScience",
        dispatch_authority="consumer_default_executor_dispatch",
        generated_at="2026-06-07T14:15:03+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="MedAutoScience",
            owner_reason="medical_paper_readiness_not_ready",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            work_unit_fingerprint="truth-snapshot::stale-readiness-dispatch",
            runtime_health_epoch="runtime-health-event-stale-readiness",
            blocked_actions=[],
        ),
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "surface": "controller_decision",
            "schema_version": 1,
            "decision_type": "medical_paper_readiness_owner_blocker",
            "generated_at": "2026-06-07T14:15:03Z",
            "readiness_next_action": {
                "action_id": "complete_medical_paper_readiness_surface",
                "surface_key": "authoring_runtime_authorization",
                "summary": "Use the current Stage Native typed blocker as the owner action.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "dispatch_path": str(dispatch_path),
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                    "next_executable_owner": "MedAutoScience",
                    "required_output_surface": "complete_medical_paper_readiness_surface",
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                        }
                    },
                }
            ],
        },
    )
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        work_unit_id="complete_medical_paper_readiness_surface",
        work_unit_fingerprint=work_unit_fingerprint,
        owner="MedAutoScience",
        source="stage_kernel_projection.current_owner_delta",
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    task = next(
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )
    assert "provider_admission_identity" not in task
    transition_request = task["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["aggregate_identity"]["work_unit_id"] == (
        "complete_medical_paper_readiness_surface"
    )
    assert transition_request["aggregate_identity"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert transition_request["dispatch_ref"].endswith(dispatch_path.name)
    assert task["work_unit_fingerprint"] == work_unit_fingerprint
    assert task["source_fingerprint"] == work_unit_fingerprint
    assert task["dedupe_key"].endswith(work_unit_fingerprint)
    assert task["provider_completion_is_domain_completion"] is False
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    assert task["authority_boundary"]["authority"] == "med_autoscience.domain_intent_adapter"
    assert task["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert (
        task["stage_transition_authority_boundary"]["stage_transition_authority"]
        == "one-person-lab"
    )
    assert (
        task["stage_transition_authority_boundary"][
            "provider_completion_counts_as_stage_transition"
        ]
        is False
    )
    assert "provider_admission_identity" not in task["payload"]
    assert task["payload"]["opl_domain_progress_transition_request"] == transition_request
    assert task["payload"]["provider_admission_pending"] is False
    assert task["payload"]["provider_admission_requires_opl_runtime_result"] is True
    assert task["payload"]["provider_completion_is_domain_completion"] is False
    assert task["payload"]["authority_boundary"] == task["authority_boundary"]
    assert (
        task["payload"]["stage_transition_authority_boundary"]
        == task["stage_transition_authority_boundary"]
    )
    assert task["payload"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert task["payload"]["source_fingerprint"] == work_unit_fingerprint
    assert task["payload"]["owner_route_currentness_basis"]["work_unit_fingerprint"] == work_unit_fingerprint
