from __future__ import annotations

import importlib
import json
import os

from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_newer_terminal_typed_closeout_discovery_outranks_stale_provider_admission_handoff(
    tmp_path,
    monkeypatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    stale_fingerprint = "publication-blockers::f11710a114497b27"
    stale_route_key = "paper-policy-request:60cf5242a09d91458cb21e22"
    terminal_work_unit_id = "consume_current_ai_reviewer_publication_eval_record_and_replay_gate"
    terminal_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    handoff_path = tmp_path / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    handoff_path.parent.mkdir(parents=True)
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=stale_fingerprint,
        work_unit_id="analysis_claim_evidence_repair",
        route_identity_key=stale_route_key,
        attempt_idempotency_key=stale_route_key,
        request_idempotency_key=stale_route_key,
    )
    handoff_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state",
                "generated_at": "2026-06-21T11:05:29+00:00",
                "provider_admission_pending_count": 1,
                "studies": [
                    {
                        "study_id": study_id,
                        "quest_status": "provider_admission_pending",
                        "next_owner": "analysis-campaign",
                        "blocked_reason": "provider_admission_current_control_state_required",
                        "action_queue": [
                            {
                                "action_type": "run_quality_repair_batch",
                                "status": "provider_admission_pending",
                                "owner": "analysis-campaign",
                                "work_unit_id": "analysis_claim_evidence_repair",
                                "next_work_unit": "analysis_claim_evidence_repair",
                                "work_unit_fingerprint": stale_fingerprint,
                                "action_fingerprint": stale_fingerprint,
                                "route_identity_key": stale_route_key,
                                "attempt_idempotency_key": stale_route_key,
                                "opl_domain_progress_transition_runtime_live_readback": readback,
                                "handoff_packet": {
                                    "opl_domain_progress_transition_live_readback": readback,
                                    "opl_domain_progress_transition_runtime_live_readback": readback,
                                },
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    closeout_path = (
        tmp_path
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_006cf0ce68e11a4661912a37.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_006cf0ce68e11a4661912a37",
                "generated_at": "2026-06-22T12:30:51+00:00",
                "status": "blocked",
                "outcome": "typed_blocker",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": terminal_work_unit_id,
                "source_fingerprint": "mas_default_executor_provider_admission_source_d0c856af9cdc18ddd4976cb9",
                "idempotency_key": "idem_ad67a8665d189e47139e0fef",
                "typed_blocker_ref": (
                    f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                    "sat_006cf0ce68e11a4661912a37.closeout.json#typed_blocker"
                ),
                "typed_blocker": {
                    "surface_kind": "mas_domain_typed_blocker",
                    "status": "blocked",
                    "blocker_id": "stage_outcome_authority_execution_count_zero",
                    "blocker_type": "stage_outcome_authority_execution_count_zero",
                    "owner": "med-autoscience",
                    "write_permitted": False,
                },
                "paper_stage_log": {
                    "surface_kind": "mas_paper_facing_stage_log_summary",
                    "status": "available",
                    "stage_name": "run_gate_clearing_batch",
                    "stage_goal": "Consume the current AI reviewer publication evaluation record.",
                    "stage_work_done": ["Recorded this typed closeout packet."],
                    "paper_work_done": ["No paper authority surface was modified."],
                    "changed_stage_surfaces": [
                        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                        "sat_006cf0ce68e11a4661912a37.closeout.json"
                    ],
                    "changed_paper_surfaces": [],
                    "outcome": "typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "next_forced_delta": {
                        "required_delta_kind": "current_stage_packet_or_matching_owner_receipt_or_typed_blocker",
                        "work_unit_id": terminal_work_unit_id,
                        "owner_action": {
                            "next_owner": "med-autoscience/one-person-lab",
                            "action_type": "bind_current_stage_packet_and_rerun_gate_clearing_batch",
                        },
                    },
                },
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
                    "work_unit_id": terminal_work_unit_id,
                    "work_unit_fingerprint": terminal_fingerprint,
                },
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
            }
        ),
        encoding="utf-8",
    )
    os.utime(handoff_path, (1_000_000_000, 1_000_000_000))
    os.utime(closeout_path, (1_000_000_100, 1_000_000_100))
    monkeypatch.setattr(module, "opl_current_control_state_handoff_path", lambda *, profile: handoff_path)
    profile = type(
        "Profile",
        (),
        {
            "studies_root": tmp_path / "studies",
            "managed_runtime_home": tmp_path / "runtime",
            "managed_runtime_quests_root": tmp_path / "runtime" / "quests",
            "workspace_root": tmp_path,
        },
    )()

    result = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id=study_id,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["current_executable_owner_action"] is None
    assert result["typed_blocker"]["blocker_type"] == "stage_outcome_authority_execution_count_zero"
    assert result["typed_blocker"]["owner"] == "med-autoscience"
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["action_type"] == "run_gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == terminal_work_unit_id
    assert result["current_work_unit"]["work_unit_fingerprint"] == terminal_fingerprint
    assert result["provider_admission_terminal_closeout_consumed"]["stage_attempt_id"] == (
        "sat_006cf0ce68e11a4661912a37"
    )
    assert result["provider_admission_terminal_closeout_consumed"]["typed_blocker"]["owner"] == "med-autoscience"
    assert result["provider_admission_terminal_closeout_consumed"]["currentness_precedence"] == (
        "newer_terminal_typed_closeout_supersedes_stale_provider_admission"
    )
    assert result["provider_admission_terminal_closeout_consumed"]["authority_boundary"][
        "provider_completion_is_domain_completion"
    ] is False
