from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


from .provider_admission_current_control_report_envelope_cases import *  # noqa: F403,F401,E402
from .provider_admission_current_control_gate_replay_cases import *  # noqa: F403,F401,E402
from .provider_admission_current_control_same_tick_cases import *  # noqa: F403,F401,E402
from .provider_admission_current_control_identity_bound_cases import *  # noqa: F403,F401,E402
from .provider_admission_current_control_stale_handoff_cases import *  # noqa: F403,F401,E402


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
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
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
    assert candidate["status"] == "transition_request_pending"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    expected_identity = f"provider-admission::{study_id}::{work_unit_fingerprint}"
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [expected_stage_packet_ref]


def test_domain_health_diagnostic_projects_progress_owner_action_without_current_control_study_entry(
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
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
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
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
        },
    )
    dump_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "running_provider_attempt": False,
            "action_queue": [],
            "studies": [],
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
    }
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "explicit_publication_work_unit_id": work_unit_id,
        },
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": "executable_owner_action",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_work_unit": work_unit_id,
            "owner_answer_missing": False,
            "owner_answer_still_required": False,
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "explicit_publication_work_unit_id": work_unit_id,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
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
            "generated_at": "2026-06-13T08:31:00+00:00",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
            "current_executable_owner_action": current_action,
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

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["managed_study_opl_transition_request_candidates"] == []
    current_control_state = result["provider_admission_current_control_state"]
    assert current_control_state["provider_admission_pending_count"] == 0
    assert current_control_state["transition_request_pending_count"] == 0
    assert current_control_state["transition_request_candidates"] == []
    assert current_control_state["stage_route_arbiter"]["decision_counts"] == {
        "paper_recovery_state_blocks_provider_admission": 1,
    }
    decision = current_control_state["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "paper_recovery_state_blocks_provider_admission"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["action_type"] == "run_quality_repair_batch"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
    assert decision["dispatch_path"] == str(dispatch_path)
    assert decision["evidence"]["provider_admission_allowed"] is False


def test_domain_health_diagnostic_suppresses_pending_admission_when_fresh_progress_is_running(
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
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
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
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
        },
    )
    dump_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "target_surface": {
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        },
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
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
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    running_envelope = {
        "state_kind": "running_provider_attempt",
        "owner": "write",
        "next_work_unit": work_unit_id,
        "typed_blocker": None,
        "parked_state": None,
        "active_run_id": "opl-stage-attempt://sat_current",
        "active_stage_attempt_id": "sat_current",
        "active_workflow_id": "wf_current",
        "runtime_health": {
            "runtime_liveness_status": "live",
            "health_status": "live",
            "work_unit_id": work_unit_id,
        },
    }
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-14T13:20:00+00:00",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "running_provider_attempt",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "running_provider_attempt",
                    "provider_attempt_proof": {
                        "running_provider_attempt": True,
                        "active_run_id": "opl-stage-attempt://sat_current",
                        "active_stage_attempt_id": "sat_current",
                        "active_workflow_id": "wf_current",
                    },
                },
            },
            "current_execution_envelope": running_envelope,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
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

    assert result["provider_admission_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    action = result["managed_study_actions"][0]
    assert action["decision"] == "noop"
    assert action["reason"] == "running_provider_attempt_observed"
    assert action["running_provider_attempt"] is True
    assert action["active_stage_attempt_id"] == "sat_current"
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "running_provider_attempt"
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 0


def test_provider_admission_merge_prefers_stage_packet_bound_duplicate() -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch_path = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"
    )
    weak = {
        "study_id": study_id,
        "quest_id": study_id,
        "source": "opl_current_control_state.action_queue",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "dispatch_path": dispatch_path,
        "route_identity_key": "owner-route::current",
        "attempt_idempotency_key": "owner-route::current",
    }
    strong = {
        **weak,
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "stage_packet_ref": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/immutable/run_gate_clearing_batch/current.json",
        "stage_packet_refs": [
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/immutable/run_gate_clearing_batch/current.json"
        ],
        "currentness_basis": {
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
        },
    }

    merged = report._merge_provider_admission_candidates([weak], [strong])

    assert len(merged) == 1
    assert merged[0]["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert merged[0]["stage_packet_ref"] == strong["stage_packet_ref"]
    assert merged[0]["stage_packet_refs"] == strong["stage_packet_refs"]


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
    route_identity_key = f"provider-admission::{study_id}::{action_fingerprint}"
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
                        "route_identity_key": route_identity_key,
                        "attempt_idempotency_key": route_identity_key,
                        "stage_packet_ref": str(dispatch_path),
                        "stage_packet_refs": [str(dispatch_path)],
                        "refs": {
                            "dispatch_path": str(dispatch_path),
                            "stage_packet_path": str(dispatch_path),
                        },
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
                                "route_identity_key": route_identity_key,
                                "attempt_idempotency_key": route_identity_key,
                                "stage_packet_ref": str(dispatch_path),
                                "stage_packet_refs": [str(dispatch_path)],
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

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_provider_admission_candidates"] == []
    candidate = result["managed_study_opl_transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.action_queue"
    assert candidate["action_type"] == "return_to_ai_reviewer_workflow"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["route_identity_key"] == route_identity_key
    assert candidate["attempt_idempotency_key"] == route_identity_key
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
    )
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [expected_stage_packet_ref]
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
