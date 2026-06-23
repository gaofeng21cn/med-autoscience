from __future__ import annotations

from pathlib import Path

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "002-dm-china-us-mortality-attribution"
WORK_UNIT_ID = "medical_prose_quality_analysis_source_documentation_repair"
FINGERPRINT = "publication-blockers::5a4f2060d6d7d97e"
FOLLOWTHROUGH_FINGERPRINT = "publication-blockers::497d1260db522f01"
ROUTE_KEY = "paper-policy-request:5c3aa8f5e1e537123138c620"
SOURCE_EVAL_ID = (
    "publication-eval::002-dm-china-us-mortality-attribution::"
    "ai-reviewer-current-inputs::2026-06-20T12:00:39+00:00"
)


def test_run_mas_owner_callable_projects_executable_action_without_opl_transition_residue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(_dm002_owner_callable_payload())

    assert action is not None
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "analysis-campaign"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == WORK_UNIT_ID
    assert action["work_unit_fingerprint"] == FINGERPRINT
    assert action["transition_request_pending"] is False
    assert action["provider_admission_pending"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is False
    assert action["opl_transition_runtime_required"] is False
    assert action["paper_recovery_successor"]["source_next_safe_action_kind"] == (
        "run_mas_owner_callable"
    )
    assert action["paper_recovery_successor"]["owner_callable_surface"] == (
        "quality_repair_batch.run_quality_repair_batch"
    )
    assert action["target_surface"]["surface_ref"] == (
        "quality_repair_batch.run_quality_repair_batch"
    )


def test_run_mas_owner_callable_refresh_clears_transition_request_candidates(
    tmp_path: Path,
) -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    provider_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )

    payload = _dm002_owner_callable_payload()
    stale_handoff = _stale_transition_request_handoff()
    refreshed = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "current_stage": "publication_supervision",
        },
        handoff=stale_handoff,
        runtime_health_snapshot={"runtime_health_epoch": "runtime-health-event-007038"},
    )
    refreshed.update(
        provider_projection.provider_admission_projection_fields(
            payload=refreshed,
            handoff=stale_handoff,
            study_root=tmp_path / "studies" / STUDY_ID,
        )
    )

    action = refreshed["current_executable_owner_action"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "analysis-campaign"
    assert action["transition_request_pending"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is False
    assert refreshed["current_work_unit"]["status"] == "executable_owner_action"
    assert refreshed["current_work_unit"]["owner"] == "analysis-campaign"
    assert refreshed["current_work_unit"]["state"]["transition_request_pending"] is False
    assert refreshed["current_work_unit"]["state"]["opl_transition_runtime_required"] is False
    assert refreshed["transition_request_pending_count"] == 0
    assert refreshed["transition_request_candidates"] == []
    assert refreshed["provider_admission_pending_count"] == 0
    assert refreshed["provider_admission_candidates"] == []


def test_run_mas_owner_callable_admission_is_not_blocked_by_provider_supervisor_gate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    payload = _dm002_owner_callable_payload()
    current_action = dict(payload["current_executable_owner_action"])
    current_action.update(
        {
            "source_surface": "paper_recovery_state.next_safe_action.owner_callable",
            "transition_request_pending": False,
            "provider_admission_requires_opl_runtime_result": False,
            "opl_transition_runtime_required": False,
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "run_mas_owner_callable",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": False,
                "opl_transition_runtime_required": False,
                "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            },
        }
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            **payload,
            "current_executable_owner_action": current_action,
            "paper_autonomy_supervisor_decision": {
                "surface_kind": "paper_progress_policy_result_projection",
                "decision": "materialize_recovery_action",
                "identity_match": True,
                "paper_autonomy_obligation": {
                    "study_id": STUDY_ID,
                    "quest_id": STUDY_ID,
                    "stage_id": "publication_supervision",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WORK_UNIT_ID,
                    "work_unit_fingerprint": FINGERPRINT,
                    "route_identity_key": ROUTE_KEY,
                    "attempt_idempotency_key": ROUTE_KEY,
                },
                "next_safe_action": {
                    "kind": "materialize_recovery_work_unit_or_receipt",
                    "source_next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "provider_admission_allowed": False,
                        "owner_callable": {
                            "callable_surface": "quality_repair_batch.run_quality_repair_batch"
                        },
                    },
                },
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
                "transition_request_pending_count": 0,
                "transition_request_candidates": [],
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is False
    assert admission["hard_gate_reasons"] == []
    assert admission["blocked_by"] == "mas_owner_callable_ready_no_provider_admission_required"
    assert admission["owner_callable_ready"] is True


def test_gate_followthrough_supersedes_consumed_mas_owner_callable_residue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    payload = _dm002_owner_callable_payload()
    payload["repair_progress_projection"] = {
        "source": "mas_owner_repair_execution_evidence",
        "paper_delta_observed": True,
        "accepted_owner_receipt": True,
        "gate_replay_done": True,
        "ai_reviewer_recheck_done": True,
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FOLLOWTHROUGH_FINGERPRINT,
        "action_fingerprint": FOLLOWTHROUGH_FINGERPRINT,
        "source_eval_id": "publication-eval::dm002::2026-06-23T05:31:37+00:00",
        "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
        "gate_replay_refs": [
            "artifacts/controller/gate_clearing_batch/latest.json",
        ],
        "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
    }
    payload["gate_clearing_batch_followthrough"] = {
        "status": "executed",
        "gate_replay_status": "blocked",
        "source_eval_id": "publication-eval::dm002::2026-06-23T05:31:46+00:00",
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FOLLOWTHROUGH_FINGERPRINT,
        "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
        "gate_replay_blockers": ["claim_evidence_consistency_failed"],
        "current_publication_work_unit": {
            "unit_id": WORK_UNIT_ID,
            "lane": "analysis-campaign",
        },
        "work_unit_currentness": {
            "current_actionability_status": "actionable",
            "explicit_publication_work_unit_id": WORK_UNIT_ID,
            "selected_publication_work_unit_id": WORK_UNIT_ID,
            "current_publication_work_unit_id": WORK_UNIT_ID,
            "explicit_work_unit_fingerprint": FOLLOWTHROUGH_FINGERPRINT,
            "current_work_unit_fingerprint": FOLLOWTHROUGH_FINGERPRINT,
            "lacks_specific_blocker_object": False,
        },
    }

    action = module.build_current_executable_owner_action(payload)

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["work_unit_id"] == WORK_UNIT_ID
    assert action["work_unit_fingerprint"] == FOLLOWTHROUGH_FINGERPRINT
    assert action["target_surface"]["gate_clearing_batch_ref"] == (
        "artifacts/controller/gate_clearing_batch/latest.json"
    )


def _dm002_owner_callable_payload() -> dict[str, object]:
    return {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "publication_eval": {"eval_id": SOURCE_EVAL_ID},
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "analysis-campaign",
                "authority": "med-autoscience",
                "obligation": {
                    "study_id": STUDY_ID,
                    "quest_id": STUDY_ID,
                    "owner": "analysis-campaign",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WORK_UNIT_ID,
                    "work_unit_fingerprint": FINGERPRINT,
                    "action_fingerprint": FINGERPRINT,
                    "currentness_basis": _currentness_basis(),
                },
            },
            "conditions": [{"condition": "current_mas_owner_callable_ready"}],
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
                "owner": "analysis-campaign",
                "provider_admission_allowed": False,
                "owner_callable": {
                    "owner": "quality_repair_batch",
                    "action_type": "run_quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "required_inputs": [
                        "controller_decisions/latest.json",
                        "publication_eval/latest.json",
                        "paper_root",
                    ],
                    "required_outputs": [
                        "paper/*",
                        "artifacts/controller/quality_repair_batch/latest.json",
                    ],
                    "artifact_delta_predicate": "canonical_paper_or_quality_repair_artifact_delta",
                    "gate_replay_target": "publication_eval/latest.json",
                    "idempotency_scope": "quality_repair_work_unit",
                    "source_fingerprint_scope": "controller_decision.work_unit_fingerprint",
                },
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "stage_id": "publication_supervision",
            "owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_work_unit": WORK_UNIT_ID,
                "provider_admission_pending": False,
                "transition_request_pending": True,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
            },
            "currentness_basis": _currentness_basis(),
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "opl_current_control_state.transition_request_candidates",
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "next_owner": "analysis-campaign",
            "owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "route_identity_key": ROUTE_KEY,
            "attempt_idempotency_key": ROUTE_KEY,
            "idempotency_key": ROUTE_KEY,
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "provider_admission_pending": False,
            "transition_request_pending": True,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_transition_runtime_required": True,
            "currentness_basis": _currentness_basis(),
        },
    }


def _stale_transition_request_handoff() -> dict[str, object]:
    candidate = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "route_identity_key": ROUTE_KEY,
        "attempt_idempotency_key": ROUTE_KEY,
        "idempotency_key": ROUTE_KEY,
        "next_executable_owner": "analysis-campaign",
        "status": "transition_request_pending",
        "mas_owner_action_source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
        "currentness_basis": _currentness_basis(),
    }
    return {
        "running_provider_attempt": False,
        "transition_request_pending_count": 1,
        "transition_request_candidates": [candidate],
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "stage_id": "publication_supervision",
            "owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_work_unit": WORK_UNIT_ID,
                "transition_request_pending": True,
            },
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "analysis-campaign",
            "next_work_unit": WORK_UNIT_ID,
        },
    }


def _currentness_basis() -> dict[str, str]:
    return {
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "current_action_source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "current_work_unit_source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
        "runtime_health_epoch": "runtime-health-event-007038",
        "source_eval_id": SOURCE_EVAL_ID,
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "route_identity_key": ROUTE_KEY,
        "attempt_idempotency_key": ROUTE_KEY,
    }
