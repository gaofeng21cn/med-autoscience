from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


from .provider_admission_current_control_report_envelope_cases import *  # noqa: F403,F401,E402


def test_same_tick_materialized_current_ai_reviewer_dispatch_survives_progress_currentness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:fresh-ai-reviewer-recheck"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-09T04:34:00+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                            "next_owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                    },
                },
            },
            "developer_supervisor_same_tick": {
                "stop_reason": "provider_handoff_written_admission_pending",
                "materialize": {
                    "default_executor_dispatches": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "dispatch_status": "ready",
                            "dispatch_authority": "ai_reviewer_record_production_handoff",
                            "dispatch_path": str(dispatch_path),
                            "next_executable_owner": "ai_reviewer",
                            "required_output_surface": (
                                "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
                            ),
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "action_fingerprint": work_unit_fingerprint,
                        },
                    ],
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_fingerprint"] == work_unit_fingerprint


def test_current_control_action_supplies_work_unit_identity_when_dispatch_is_legacy_shape(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::0915410f804b3697"

    candidates = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "action_fingerprint": work_unit_fingerprint,
                        "allowed_actions": ["run_quality_repair_batch"],
                        "target_surface": {
                            "ref_kind": "publication_work_unit",
                            "route_target": "write",
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        },
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "action_fingerprint": work_unit_fingerprint,
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                        "typed_blocker": None,
                    },
                }
            ],
            "action_queue": [],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        current_control_ref="runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)


def test_domain_health_diagnostic_dry_run_surfaces_current_control_ai_reviewer_queue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    action_fingerprint = "sha256:current-control-ai-reviewer-recheck"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dump_json(
        dispatch_path,
        {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    current_control_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        current_control_path,
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "queued",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="blocked",
            reason="quest_waiting_for_user",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / "quests" / study_id),
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "medical_paper_readiness_missing",
                "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
            },
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-08T06:40:00+00:00",
            "current_execution_envelope": status_payload["current_execution_envelope"],
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {"source_fingerprint": action_fingerprint},
            },
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 1
    candidate = result["managed_study_opl_provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.action_queue"
    assert candidate["action_type"] == "return_to_ai_reviewer_workflow"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert result["action_fingerprints"] == [action_fingerprint]


def test_request_opl_stage_attempt_carries_current_provider_admission_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
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
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                        }
                    },
                }
            ]
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "quest_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
            "source_ref": str(typed_blocker_ref),
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "complete_medical_paper_readiness_surface"
    assert identity["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert identity["action_fingerprint"] == work_unit_fingerprint
    assert identity["dispatch_path"] == str(dispatch_path)
    assert result["provider_admission_identity"] == identity


def test_same_tick_owner_route_apply_refreshes_report_currentness_before_provider_admission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    action_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    def stale_impl(**_: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-11T20:54:00+00:00",
            "runtime_root": str(profile.runtime_root),
            "scanned_quests": [],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "blocked",
                    "reason": "closed_with_domain_owner_refs",
                    "running_provider_attempt": False,
                }
            ],
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "current_execution_evidence": {
                "managed_study_actions": [],
                "provider_admission_candidates": [],
                "progress_currentness": {},
            },
            "action_fingerprints": [],
            "reports": [],
        }

    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", stale_impl)
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **_: {
            "surface": "developer_supervisor_same_tick",
            "schema_version": 1,
            "stop_reason": "provider_handoff_written_admission_pending",
            "study_ids": [study_id],
            "iterations": [],
            "materialize": {
                "surface": "domain_action_request_materializer",
                "default_executor_dispatch_count": 1,
                "ready_default_executor_dispatch_count": 1,
                "default_executor_dispatches": [
                    {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "action_type": "run_gate_clearing_batch",
                        "dispatch_status": "ready",
                        "dispatch_authority": "consumer_default_executor_dispatch",
                        "dispatch_path": str(dispatch_path),
                        "next_executable_owner": "gate_clearing_batch",
                        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                    }
                ],
            },
        },
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-11T20:54:31+00:00",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    "route_target": "finalize",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": work_unit_id,
            },
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    currentness = result["current_execution_evidence"]["progress_currentness"][study_id]
    assert currentness["current_work_unit"]["work_unit_id"] == work_unit_id
    assert result["provider_admission_pending_count"] == 1
    candidate = result["managed_study_opl_provider_admission_candidates"][0]
    assert candidate["source"] == "same_tick_materialized_dispatch"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 1
    assert result["action_fingerprints"] == [action_fingerprint]


def test_request_opl_stage_attempt_uses_fresh_progress_currentness_for_authorization_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    quest_root = profile.runtime_root / "quests" / study_id
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "dm002_current_publication_hardening_after_current_ai_reviewer_eval::run_quality_repair_batch"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": "canonical manuscript story-surface delta",
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    stale_status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "quest_marked_running_but_no_live_session",
                "owner": "med-autoscience",
            },
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: stale_status_payload)
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-08T05:40:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_fingerprint": action_fingerprint,
                "allowed_actions": ["run_quality_repair_batch"],
            },
        },
    )

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "run_quality_repair_batch"
    assert identity["work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert identity["action_fingerprint"] == action_fingerprint
    assert identity["blocked_reason"] == "opl_execution_authorization_required"
    assert result["provider_admission_identity"] == identity


def test_request_opl_stage_attempt_rejects_stale_persisted_handoff_when_fresh_progress_points_to_gate_replay(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    quest_root = profile.runtime_root / "quests" / study_id
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    current_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    current_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "handoff_ready",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
                    "dispatch_path": str(stale_dispatch_path),
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": stale_fingerprint,
                        "source_refs": {
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": stale_fingerprint,
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-stale-write-repair",
                                "runtime_health_epoch": "runtime-health-stale-write-repair",
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": stale_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    dump_json(
        current_dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "refs": {"dispatch_path": str(current_dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-current-gate-replay",
                        "runtime_health_epoch": "runtime-health-current-gate-replay",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                    },
                },
            },
        },
    )
    current_control_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        current_control_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "study_id": study_id,
                        "quest_id": study_id,
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                        "action_fingerprint": current_fingerprint,
                        "currentness_basis": {
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": current_fingerprint,
                            "truth_epoch": "truth-event-current-gate-replay",
                            "runtime_health_epoch": "runtime-health-current-gate-replay",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "next_work_unit": "publication_gate_replay",
                    },
                    "current_executable_owner_action": {
                        "status": "ready",
                        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                        "action_fingerprint": current_fingerprint,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            "route_target": "gate_clearing_batch",
                        },
                    },
                }
            ],
            "action_queue": [],
        },
    )
    stale_status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_work_unit": {
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_fingerprint,
        },
        "current_executable_owner_action": {
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_fingerprint,
            "allowed_actions": ["run_quality_repair_batch"],
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: stale_status_payload)
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-13T08:00:00+00:00",
            "current_work_unit": {
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "truth_epoch": "truth-event-current-gate-replay",
                    "runtime_health_epoch": "runtime-health-current-gate-replay",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        },
    )

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "run_gate_clearing_batch"
    assert identity["work_unit_id"] == "publication_gate_replay"
    assert identity["work_unit_fingerprint"] == current_fingerprint
    assert identity["dispatch_path"] == str(current_dispatch_path)
    assert result["provider_admission_identity"] == identity


def test_current_control_study_finalize_gate_replay_action_becomes_provider_admission(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    work_unit_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::run_gate_clearing_batch"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-previous-ai-reviewer-record",
                        "runtime_health_epoch": "runtime-health-event-previous-gate",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    },
                },
            },
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                        },
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current-ai-reviewer-record",
                            "runtime_health_epoch": "runtime-health-event-current-gate",
                            "work_unit_id": work_unit_id,
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["next_executable_owner"] == "finalize"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)


def test_current_control_study_gate_replay_uses_current_ai_reviewer_eval_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T155750Z::sat_619d680b6dc5c74022af4a3b"
    )
    coarse_ticket = (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::run_gate_clearing_batch"
    )
    expected_fingerprint = (
        f"current-ai-reviewer-gate-replay::{study_id}::{work_unit_id}::{source_eval_id}"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-previous-ai-reviewer-record",
                        "runtime_health_epoch": "runtime-health-event-previous-gate",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    },
                },
            },
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                        },
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "study_id": study_id,
                        "owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": coarse_ticket,
                        "action_fingerprint": coarse_ticket,
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current-ai-reviewer-record",
                            "runtime_health_epoch": "runtime-health-event-current-gate",
                            "source_eval_id": source_eval_id,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": coarse_ticket,
                        },
                    },
                    "intervention_lane": {
                        "route_back_checklist": {
                            "source_eval_id": source_eval_id,
                            "evidence_refs": [
                                (
                                    "/workspace/studies/003/artifacts/publication_eval/"
                                    "ai_reviewer_responses/20260610T160042Z_publication_eval_record.json"
                                )
                            ],
                        }
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["next_executable_owner"] == "finalize"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == expected_fingerprint
    assert candidate["action_fingerprint"] == expected_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["currentness_basis"]["source_eval_id"] == source_eval_id
