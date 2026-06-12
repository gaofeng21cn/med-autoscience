from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_provider_admission_candidate_requires_current_action_identity() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    typed_blocker_ref = (
        "/workspace/studies/002-dm-china-us-mortality-attribution/"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    current_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    stale_fingerprint = "paper_progress_stall:002-dm-china-us-mortality-attribution:old-ai-reviewer"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-ai-reviewer.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "return_to_ai_reviewer_workflow",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/current-readiness.json",
                    "action_fingerprint": current_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": current_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
                "source_ref": typed_blocker_ref,
            },
        },
    )

    assert [candidate["action_fingerprint"] for candidate in result] == [current_fingerprint]


def test_provider_admission_candidate_accepts_study_progress_owner_ticket_identity() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    typed_blocker_ref = (
        f"/workspace/studies/{study_id}/"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    ticket_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "complete_medical_paper_readiness_surface::complete_medical_paper_readiness_surface"
    )
    stale_fingerprint = f"paper_progress_stall::{study_id}::old-readiness"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-readiness.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
                {
                    "study_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/current-readiness.json",
                    "action_fingerprint": ticket_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": ticket_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
                "source_ref": typed_blocker_ref,
            },
        },
    )

    assert [candidate["action_fingerprint"] for candidate in result] == [ticket_fingerprint]


def test_provider_admission_candidate_rejects_cross_action_current_ticket_authorization_blocker() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs::return_to_ai_reviewer_workflow"
    )

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
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
                    "dispatch_path": "/workspace/current-quality-repair.json",
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        },
    )

    assert result == []


def test_provider_admission_candidate_rejects_current_ticket_after_cross_action_routeback_translation() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs::return_to_ai_reviewer_workflow"
    )

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
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
                    "dispatch_path": "/workspace/current-quality-repair.json",
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
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        },
    )

    assert result == []


def test_provider_admission_candidate_rejects_cross_action_authorization_blocker_despite_stale_runtime_envelope() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs::return_to_ai_reviewer_workflow"
    )

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": "/workspace/current-gate-clearing.json",
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "med-autoscience",
                "typed_blocker": {
                    "blocker_type": "quest_waiting_for_user",
                    "owner": "med-autoscience",
                },
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        },
    )

    assert result == []


def test_provider_admission_candidate_accepts_gate_replay_authorization_after_current_ai_reviewer_record_routeback() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    gate_fingerprint = f"domain-transition::route_back_same_line::{gate_work_unit_id}"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": "/workspace/current-gate-clearing.json",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": gate_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": gate_fingerprint,
                        "source_refs": {
                            "work_unit_id": gate_work_unit_id,
                            "work_unit_fingerprint": gate_fingerprint,
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "ai-reviewer-record::20260608T175710Z::sat_current"
                            ),
                            "owner_route_currentness_basis": {
                                "work_unit_id": gate_work_unit_id,
                                "work_unit_fingerprint": gate_fingerprint,
                                "source_eval_id": (
                                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                    "ai-reviewer-record::20260608T175710Z::sat_current"
                                ),
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                },
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        },
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == gate_work_unit_id
    assert candidate["action_fingerprint"] == gate_fingerprint
    assert candidate["blocked_reason"] == "opl_execution_authorization_required"


def test_provider_admission_rejects_gate_replay_with_only_ai_reviewer_fingerprint_match() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    shared_fingerprint = "sha256:accepted-repair-progress-source"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": "/workspace/stale-gate-clearing.json",
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": shared_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": shared_fingerprint,
                        "source_refs": {
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": shared_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": shared_fingerprint,
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                },
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": shared_fingerprint,
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {"source_fingerprint": shared_fingerprint},
            },
        },
    )

    assert result == []


def test_domain_health_diagnostic_dry_run_aggregates_gate_admission_candidates_for_focused_studies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    dm002 = "002-dm-china-us-mortality-attribution"
    dm003 = "003-dpcc-primary-care-phenotype-treatment-gap"

    for study_id in (dm002, dm003):
        study_root = profile.studies_root / study_id
        study_root.mkdir(parents=True, exist_ok=True)
        dump_json(study_root / "study.yaml", {"study_id": study_id})
        dump_json(study_root / "artifacts" / "controller" / "study_charter.json", {"study_id": study_id})

    dm002_root = profile.studies_root / dm002
    dm003_root = profile.studies_root / dm003
    dm002_fingerprint = "sha256:dm002-current-gate-replay"
    dm003_work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    dm003_fingerprint = f"domain-transition::route_back_same_line::{dm003_work_unit}"

    dump_json(
        dm002_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "executions": [
                {
                    "study_id": dm002,
                    "quest_id": dm002,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": str(dm002_root / "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": dm002_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": dm002_fingerprint,
                        "source_refs": {
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": dm002_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": dm002_fingerprint,
                            },
                        },
                    },
                }
            ]
        },
    )
    dump_json(
        dm003_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "executions": [
                {
                    "study_id": dm003,
                    "quest_id": dm003,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": str(dm003_root / "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"),
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": dm003_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": dm003_fingerprint,
                        "source_refs": {
                            "work_unit_id": dm003_work_unit,
                            "work_unit_fingerprint": dm003_fingerprint,
                            "source_eval_id": "publication-eval::dm003::ai-reviewer-record::current",
                            "owner_route_currentness_basis": {
                                "work_unit_id": dm003_work_unit,
                                "work_unit_fingerprint": dm003_fingerprint,
                                "source_eval_id": "publication-eval::dm003::ai-reviewer-record::current",
                            },
                        },
                    },
                }
            ]
        },
    )

    status_by_study = {
        dm002: {
            **make_progress_projection_payload(
                study_id=dm002,
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "study_root": str(dm002_root),
            "quest_id": dm002,
            "quest_root": str(profile.runtime_root / "quests" / dm002),
        },
        dm003: {
            **make_progress_projection_payload(
                study_id=dm003,
                decision="blocked",
                reason="quest_waiting_opl_runtime_owner_route",
            ),
            "study_root": str(dm003_root),
            "quest_id": dm003,
            "quest_root": str(profile.runtime_root / "quests" / dm003),
        },
    }

    def progress_projection(**kwargs):
        study_root = Path(kwargs["study_root"])
        return status_by_study[study_root.name]

    def read_study_progress(**kwargs):
        study_id = kwargs["study_id"]
        if study_id == dm002:
            return {
                "study_id": study_id,
                "generated_at": "2026-06-09T02:30:00+00:00",
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
                    "work_unit_fingerprint": dm002_fingerprint,
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
            }
        return {
            "study_id": study_id,
            "generated_at": "2026-06-09T02:30:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {"blocker_type": "medical_paper_readiness_missing"},
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:dm003-current-ai-reviewer-record",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", progress_projection)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(study_progress, "read_study_progress", read_study_progress)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(dm002, dm003),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 1
    candidates = result["managed_study_opl_provider_admission_candidates"]
    assert [candidate["study_id"] for candidate in candidates] == [dm002]
    assert [candidate["action_type"] for candidate in candidates] == ["run_gate_clearing_batch"]
    assert [candidate["work_unit_fingerprint"] for candidate in candidates] == [dm002_fingerprint]
    assert result["action_fingerprints"] == [dm002_fingerprint]
    assert dm003_fingerprint not in result["action_fingerprints"]
    assert result["provider_admission_current_control_state"]["stage_route_arbiter"][
        "decision_counts"
    ] == {"pending_provider_admission": 1}


def test_provider_probe_requires_running_attempt_fingerprint_match() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    current_fingerprint = "sha256:current-provider-handoff"
    stale_fingerprint = "sha256:stale-provider-attempt"
    scan_result = {
        "studies": [
            {
                "study_id": study_id,
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-stale",
                "active_stage_attempt_id": "sat-stale",
                "opl_provider_attempt": {
                    "running_provider_attempt": True,
                    "active_run_id": "opl-stage-attempt://sat-stale",
                    "active_stage_attempt_id": "sat-stale",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "action_fingerprint": stale_fingerprint,
                    "work_unit_fingerprint": stale_fingerprint,
                    "dispatch_ref": (
                        f"studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
                    ),
                },
            }
        ]
    }
    identity = {
        "study_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "action_fingerprint": current_fingerprint,
        "work_unit_fingerprint": current_fingerprint,
        "dispatch_path": (
            f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
            "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
        ),
    }

    assert provider_admission.provider_probe_has_matching_attempt(scan_result, identity=identity) is False
    scan_result["studies"][0]["opl_provider_attempt"]["action_fingerprint"] = current_fingerprint
    scan_result["studies"][0]["opl_provider_attempt"]["work_unit_fingerprint"] = current_fingerprint
    assert provider_admission.provider_probe_has_matching_attempt(scan_result, identity=identity) is True


def test_provider_probe_rejects_action_only_running_attempt_match() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    scan_result = {
        "studies": [
            {
                "study_id": study_id,
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-action-only",
                "active_stage_attempt_id": "sat-action-only",
                "opl_provider_attempt": {
                    "running_provider_attempt": True,
                    "active_run_id": "opl-stage-attempt://sat-action-only",
                    "active_stage_attempt_id": "sat-action-only",
                    "action_type": "run_gate_clearing_batch",
                },
            }
        ]
    }
    identity = {
        "study_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "work_unit_fingerprint": "sha256:current-gate-replay",
        "dispatch_path": (
            f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
            "default_executor_dispatches/run_gate_clearing_batch.json"
        ),
    }

    assert provider_admission.provider_probe_has_matching_attempt(scan_result, identity=identity) is False

def test_provider_admission_candidate_is_suppressed_by_typed_blocker_envelope() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    stale_fingerprint = "domain-transition::003-dpcc-primary-care-phenotype-treatment-gap::finalize"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "request_opl_stage_attempt",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": "/workspace/stale-finalize.json",
                    "action_fingerprint": stale_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "work_unit_fingerprint": stale_fingerprint,
                        }
                    },
                },
            ]
        },
        status_payload={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": {
                "source": "domain_transition",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["request_opl_stage_attempt"],
            },
        },
    )

    assert result == []


def test_provider_admission_candidate_survives_readiness_typed_blocker_for_stage_native_write_repair() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = (
        "stage-native-next-action::08-publication_package_handoff::"
        "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
    )

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                    "owner_route_basis": "stage_native_workspace_next_action",
                    "dispatch_path": "/workspace/current-stage-native-write.json",
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "write",
                    "stage_attempt_admission": {
                        "surface": "opl_stage_attempt_admission_request",
                        "status": "requested",
                        "owner": "one-person-lab",
                    },
                    "owner_route": {
                        "next_owner": "write",
                        "source_refs": {
                            "work_unit_id": "run_quality_repair_batch",
                            "work_unit_fingerprint": fingerprint,
                            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
                            "current_stage_id": "08-publication_package_handoff",
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": None,
        },
    )

    assert result == []

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                    "owner_route_basis": "stage_native_workspace_next_action",
                    "dispatch_path": "/workspace/current-stage-native-write.json",
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "write",
                    "stage_attempt_admission": {
                        "surface": "opl_stage_attempt_admission_request",
                        "status": "requested",
                        "owner": "one-person-lab",
                    },
                    "owner_route": {
                        "next_owner": "write",
                        "source_refs": {
                            "work_unit_id": "run_quality_repair_batch",
                            "work_unit_fingerprint": fingerprint,
                            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
                            "current_stage_id": "08-publication_package_handoff",
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": {
                "source": "stage_native_workspace_next_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "run_quality_repair_batch",
                "work_unit_fingerprint": fingerprint,
                "allowed_actions": ["run_quality_repair_batch"],
            },
        },
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "run_quality_repair_batch"
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["provider_attempt_or_lease_required"] is True
    assert candidate["owner_route_basis"] == "stage_native_workspace_next_action"


def test_provider_admission_candidate_requires_dispatch_path() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    fingerprint = "stage-current-owner-delta::complete_medical_paper_readiness_surface::typed-blocker"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "action_fingerprint": fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": fingerprint,
                        }
                    },
                }
            ]
        },
        status_payload={"study_id": "002-dm-china-us-mortality-attribution"},
    )

    assert result == []
