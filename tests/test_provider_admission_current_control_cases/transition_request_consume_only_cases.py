from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import (
    opl_transition_readback as _opl_transition_readback,
    provider_candidate as _provider_candidate,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    current_control_provider_admission_candidates,
)
from tests.test_provider_admission_current_control_cases.transition_request_consume_only_cases_cases.test_request_only_dry_run_closeout import *  # noqa: F403,F401


def test_provider_admission_current_control_treats_mas_request_without_opl_readback_as_non_advancing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-ai-reviewer-no-opl-readback"
    candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )
    candidate.update(
        {
            "event_id": "bare-event-fragment",
            "outbox_item_id": "bare-outbox-fragment",
            "stage_run_identity": {
                "stage_run_id": "bare-stage-run-fragment",
                "route_identity_key": candidate["route_identity_key"],
                "attempt_idempotency_key": candidate["attempt_idempotency_key"],
            },
        }
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-17T08:40:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request_candidate] = result["transition_request_candidates"]
    assert transition_request_candidate["provider_admission_pending"] is False
    assert (
        transition_request_candidate["provider_admission_requires_opl_runtime_result"]
        is True
    )
    action = result["action_queue"][0]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_attempt_or_lease_required"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_domain_progress_transition_result" not in action
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    assert decision["anti_loop_classification"] == "non_advancing_apply_required"
    assert decision["evidence"]["required_runtime"] == "DomainProgressTransitionRuntime"
    assert decision["evidence"]["candidate_has_opl_transition_readback"] is False
    assert "opl_transition_event_consumption" not in decision["evidence"]
    assert (
        decision["evidence"]["required_readback_surface_kind"]
        == "opl_domain_progress_transition_runtime_live_readback"
    )
    assert decision["evidence"]["missing_readback_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]
    assert decision["evidence"]["mas_can_authorize_provider_admission"] is False
    assert decision["evidence"]["mas_can_create_opl_outbox_record"] is False
    assert decision["evidence"]["mas_can_create_opl_event"] is False
    assert decision["evidence"]["mas_can_create_opl_stage_run"] is False
    assert (
        decision["evidence"]["event_or_outbox_fragment_is_provider_admission_authority"]
        is False
    )
    assert decision["evidence"]["no_progress_signal"] == "transition_request_waits_for_opl_runtime"


def test_provider_admission_current_control_backfills_owner_from_transition_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "paper-policy-request:afa135a3051e8aa76700b447"
    route_key = action_fingerprint
    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_owner": "ai_reviewer",
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "request_idempotency_key": route_key,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "owner": "ai_reviewer",
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": transition_request["currentness_basis"],
        "opl_domain_progress_transition_request": dict(transition_request),
        "paper_progress_policy_result": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "opl_domain_progress_transition_request": dict(transition_request),
        },
        "opl_domain_progress_transition_runtime_live_readback": _opl_transition_readback(
            study_id,
            action_fingerprint=action_fingerprint,
            work_unit_id=work_unit_id,
            route_identity_key=route_key,
            attempt_idempotency_key=route_key,
            request_idempotency_key=route_key,
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-20T22:35:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    [provider_candidate] = result["provider_admission_candidates"]
    assert provider_candidate["owner"] == "ai_reviewer"
    assert provider_candidate["next_executable_owner"] == "ai_reviewer"
    [study] = result["studies"]
    assert study["next_owner"] == "ai_reviewer"
    assert study["current_execution_envelope"]["owner"] == "ai_reviewer"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["provider_admission_candidates"][0]["next_executable_owner"] == "ai_reviewer"
    [action] = result["action_queue"]
    assert action["next_executable_owner"] == "ai_reviewer"
    assert action["owner_route"]["next_owner"] == "ai_reviewer"
    assert action["handoff_packet"]["next_executable_owner"] == "ai_reviewer"


def test_owner_receipt_current_work_unit_keeps_accepted_owner_gate_transition_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    study_root = profile.studies_root / study_id
    stage_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_quality_repair_batch"
        / "33abc53e0c18295f5fa03738.json"
    )
    stage_packet_path.parent.mkdir(parents=True, exist_ok=True)
    stage_packet_path.write_text(
        json.dumps(
            {
                "dispatch_status": "ready",
                "dispatch_authority": "consumer_default_executor_dispatch",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "next_executable_owner": "write",
                "required_output_surface": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_route": {
                    "next_owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "work_unit_fingerprint": action_fingerprint,
                    "source_refs": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "owner_route_currentness_basis": {
                            "truth_epoch": "truth-event-000035",
                            "runtime_health_epoch": "runtime-health-event-006980",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    stage_packet_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "supervision/consumer/default_executor_dispatches/immutable/"
        "run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )

    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(study_root),
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "currentness_basis": {
                "truth_epoch": "truth-event-000035",
                "runtime_health_epoch": "runtime-health-event-006980",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
            },
            "state": {
                "state_kind": "owner_receipt_recorded",
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
            },
        },
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
        },
        "study_intervention_events": [
            {
                "surface": "study_intervention_event",
                "intent": "owner_gate_decision",
                "event_id": "intervention-event-000001-b9cbb92d925e979c",
                "recorded_at": "2026-06-19T16:46:50+00:00",
                "payload": {
                    "decision": "admit_identity_bound_stage_packet",
                    "provider_admission_allowed": True,
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:0863b0b9a2d94867284fa160"
                    ),
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:0863b0b9a2d94867284fa160"
                    ),
                    "current_owner_identity": {
                        "study_id": study_id,
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    },
                    "stage_packet_ref": stage_packet_ref,
                    "stage_packet_refs": [stage_packet_ref],
                },
            }
        ],
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "currentness_basis": {
                        "truth_epoch": "truth-event-000035",
                        "runtime_health_epoch": "runtime-health-event-006980",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                    },
                },
            },
            "conditions": [
                {
                    "condition": "accepted_owner_gate_decision",
                    "decision": "admit_identity_bound_stage_packet",
                }
            ],
            "next_safe_action": {
                "kind": "admit_identity_bound_stage_packet",
                "owner": "write",
                "provider_admission_allowed": True,
            },
            "evidence_refs": [
                "human_gate:owner-gate-decision:0863b0b9a2d94867284fa160",
                "owner-gate-decision:0863b0b9a2d94867284fa160",
                stage_packet_ref,
            ],
        },
    }
    candidates = current_control_provider_admission_candidates(
        {"studies": [scanned_study], "action_queue": []},
        study_root=study_root,
        status_payload=scanned_study,
    )

    assert len(candidates) == 1
    assert candidates[0]["dispatch_path"] == str(stage_packet_path)
    assert candidates[0]["stage_packet_ref"] == stage_packet_ref
    assert candidates[0]["mas_owner_action_source"] == (
        "paper_recovery_state.accepted_owner_gate_decision"
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at="2026-06-20T00:20:00+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request] = result["transition_request_candidates"]
    assert transition_request["status"] == "transition_request_pending"
    assert transition_request["provider_admission_pending"] is False
    assert transition_request["provider_attempt_or_lease_required"] is False
    assert transition_request["provider_admission_requires_opl_runtime_result"] is True
    assert transition_request["dispatch_path"] == str(stage_packet_path)
    assert transition_request["stage_packet_ref"] == stage_packet_ref
    assert transition_request["mas_owner_action_source"] == (
        "paper_recovery_state.accepted_owner_gate_decision"
    )
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    [decision] = result["stage_route_arbiter_decisions"]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    [action] = result["action_queue"]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_attempt_or_lease_required"] is False


def test_provider_admission_current_control_treats_current_transition_authority_as_non_advancing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-transition-authority-no-opl-readback"
    candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )
    candidate["current_transition_authority_confirmed"] = True
    candidate["current_transition_authority_sources"] = ["opl_transition_log_readback"]

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-18T18:05:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request_candidate] = result["transition_request_candidates"]
    assert transition_request_candidate["provider_admission_pending"] is False
    assert (
        transition_request_candidate["provider_admission_requires_opl_runtime_result"]
        is True
    )
    action = result["action_queue"][0]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_attempt_or_lease_required"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is True
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"


def test_paper_recovery_successor_request_opl_stage_attempt_without_dispatch_becomes_transition_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "provider_admission_pending": False,
            },
            "currentness_basis": {
                "source": "domain_transition",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-f4ac5a781b3258a4",
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "domain_transition",
            "next_owner": "write",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "action_type": "request_opl_stage_attempt",
            "allowed_actions": ["request_opl_stage_attempt"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            "owner_route_currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                "runtime_health_epoch": "runtime-health-event-006980-f4ac5a781b3258a4",
            },
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
                "source_surface": "domain_transition",
            },
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": work_unit_id,
            "typed_blocker": None,
            "parked_state": None,
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
            },
            "conditions": [
                {
                    "condition": "consumed_owner_receipt_domain_transition_successor",
                    "source_condition": "same_work_unit_owner_receipt_recorded",
                }
            ],
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": False,
                "successor_owner_action": {
                    "action_type": "request_opl_stage_attempt",
                    "owner": "write",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "domain_transition_decision_type": "route_back_same_line",
                    "domain_transition_controller_action": "request_opl_stage_attempt",
                    "source_surface": "domain_transition",
                    "source_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                },
            },
        },
    }
    candidates = current_control_provider_admission_candidates(
        {"studies": [scanned_study], "action_queue": []},
        study_root=profile.studies_root / study_id,
        status_payload=scanned_study,
    )

    assert len(candidates) == 1
    [candidate] = candidates
    assert candidate["status"] == "transition_request_pending"
    assert candidate["action_type"] == "request_opl_stage_attempt"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_attempt_or_lease_required"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert "dispatch_path" not in candidate

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at="2026-06-20T13:58:02+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request] = result["transition_request_candidates"]
    assert transition_request["action_type"] == "request_opl_stage_attempt"
    assert transition_request["work_unit_id"] == work_unit_id
    assert transition_request["work_unit_fingerprint"] == action_fingerprint
    assert transition_request["provider_admission_pending"] is False
    assert transition_request["provider_attempt_or_lease_required"] is False
    assert transition_request["provider_admission_requires_opl_runtime_result"] is True
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    [decision] = result["stage_route_arbiter_decisions"]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"


def test_provider_admission_current_control_consumes_opl_readback_inside_provider_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )
    candidate["provider_admission_identity"] = {
        "surface_kind": "opl_provider_admission_identity",
        "study_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "opl_domain_progress_transition_runtime_live_readback": _opl_transition_readback(
            study_id,
            action_fingerprint=action_fingerprint,
            work_unit_id=work_unit_id,
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-17T20:45:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    assert len(result["provider_admission_candidates"]) == 1
    assert result["transition_request_candidates"] == []
    assert result["stage_route_arbiter"]["pending_count"] == 1
    action = result["action_queue"][0]
    assert action["status"] == "queued"
    assert action["provider_admission_pending"] is True
    assert action["provider_attempt_or_lease_required"] is True
    assert action["provider_admission_requires_opl_runtime_result"] is False
    assert action["opl_domain_progress_transition_live_readback"]["surface_kind"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )
    readback_identity = action["opl_domain_progress_transition_live_readback"]["identity"]
    assert action["opl_domain_progress_transition_request"]["idempotency_key"] == (
        readback_identity["idempotency_key"]
    )
    assert result["provider_admission_candidates"][0]["opl_domain_progress_transition_request"][
        "idempotency_key"
    ] == readback_identity["idempotency_key"]

from tests.test_provider_admission_current_control_cases.transition_request_consume_only_cases_cases.terminal_closeout_and_identity_cases import *  # noqa: F403,F401
