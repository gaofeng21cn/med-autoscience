from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_provider_admission_report_derives_owner_gate_route_back_candidate(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    route_identity_key = f"paper-recovery-owner-gate::{study_id}::run_quality_repair_batch::{fingerprint}"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_packet_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_quality_repair_batch"
        / "d4b2229c300acd93d67676bf.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    stage_packet_path.parent.mkdir(parents=True, exist_ok=True)
    dispatch_payload = {
        "surface": "default_executor_dispatch_request",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "dispatch_status": "ready",
        "dispatch_authority": "consumer_default_executor_dispatch",
        "next_executable_owner": "write",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "action_fingerprint": fingerprint,
        "work_unit_fingerprint": fingerprint,
        "work_unit_id": work_unit_id,
        "stage_packet_ref": str(stage_packet_path),
        "stage_packet_refs": [str(stage_packet_path)],
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": route_identity_key,
        "owner_route": {
            "next_owner": "write",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_fingerprint": fingerprint,
            "source_refs": {
                "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
                "source_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "stage_packet_ref": str(stage_packet_path),
                "stage_packet_refs": [str(stage_packet_path)],
                "route_identity_key": route_identity_key,
                "attempt_idempotency_key": route_identity_key,
            },
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "immutable_dispatch_path": str(stage_packet_path),
            "stage_packet_ref": str(stage_packet_path),
            "stage_packet_refs": [str(stage_packet_path)],
        },
        "prompt_contract": {
            "owner_route_currentness_basis": {
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "source_action": {
            "authority": "paper_recovery_state.accepted_owner_gate_decision",
            "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
            "source_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
    dispatch_path.write_text(json.dumps(dispatch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stage_packet_path.write_text(json.dumps(dispatch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "active_run_id": None,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "typed_blocker",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "one-person-lab",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "state": {
                                "state_kind": "typed_blocker",
                                "typed_blocker": {
                                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                                    "owner": "one-person-lab",
                                    "action_type": "run_quality_repair_batch",
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": fingerprint,
                                },
                            },
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "typed_blocker",
                            "owner": "one-person-lab",
                            "typed_blocker": {
                                "blocker_id": "stage_packet_not_current_selected_dispatch",
                                "blocker_type": "stage_packet_not_current_selected_dispatch",
                                "owner": "one-person-lab",
                            },
                        },
                        "paper_recovery_state": {
                            "surface_kind": "paper_recovery_state",
                            "phase": "owner_action_ready",
                            "next_safe_action": {
                                "kind": "route_back_to_owner_or_repair_materialization",
                                "owner": "MedAutoScience",
                                "provider_admission_allowed": False,
                                "accepted_owner_gate_decision": {
                                    "decision": "route_back_to_mas_packet_materialization_bug",
                                    "action_type": "run_quality_repair_batch",
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": fingerprint,
                                    "route_back_evidence_ref": (
                                        "route_back:owner-gate-decision:c7027de42ca336cfe0782428"
                                    ),
                                },
                            },
                        },
                    },
                },
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "decision": "blocked",
                    "reason": "stage_packet_not_current_selected_dispatch",
                }
            ],
        },
        apply=False,
        generated_at="2026-06-14T07:20:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    [candidate] = result["provider_admission_candidates"]
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["stage_packet_ref"] == (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/d4b2229c300acd93d67676bf.json"
    )
    assert candidate["route_identity_key"] == route_identity_key
    assert candidate["attempt_idempotency_key"] == route_identity_key
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
