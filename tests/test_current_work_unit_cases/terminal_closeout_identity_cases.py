from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_uses_terminal_typed_blocker_current_identity() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    requested_work_unit_id = "analysis_claim_evidence_repair"
    requested_fingerprint = "publication-blockers::497d1260db522f01"
    stale_dispatch_fingerprint = (
        "owner-route::write::manuscript_story_surface_delta_missing::"
        "run_quality_repair_batch"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_cfb833131bfa30d6661c26c2",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "blocked_reason": "stage_packet_not_current_selected_dispatch",
                    "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                    "work_unit_fingerprint": stale_dispatch_fingerprint,
                    "stage_name": requested_work_unit_id,
                    "source_path": (
                        "studies/002-dm-china-us-mortality-attribution/"
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_cfb833131bfa30d6661c26c2.closeout.json"
                    ),
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "required_owner_action": (
                            "provide or admit a current stage packet for "
                            f"{requested_work_unit_id}/{requested_fingerprint}"
                        ),
                    },
                    "domain_execution": {
                        "blocked_reason": "stage_packet_not_current_selected_dispatch",
                        "requested_stage_packet_work_unit_id": (
                            "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                        ),
                        "requested_stage_packet_work_unit_fingerprint": stale_dispatch_fingerprint,
                        "fresh_current_control_work_unit_id": requested_work_unit_id,
                        "fresh_current_control_work_unit_fingerprint": requested_fingerprint,
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "write",
            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            "work_unit_fingerprint": stale_dispatch_fingerprint,
            "action_fingerprint": stale_dispatch_fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_type": "stage_packet_not_current_selected_dispatch",
            "blocked_reason": "stage_packet_not_current_selected_dispatch",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": requested_work_unit_id,
            "work_unit_fingerprint": stale_dispatch_fingerprint,
            "source_ref": (
                "studies/002-dm-china-us-mortality-attribution/"
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_cfb833131bfa30d6661c26c2.closeout.json"
            ),
            "typed_blocker_ref": (
                "studies/002-dm-china-us-mortality-attribution/"
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_cfb833131bfa30d6661c26c2.closeout.json"
            ),
            "currentness_basis": {
                "work_unit_id": requested_work_unit_id,
                "work_unit_fingerprint": stale_dispatch_fingerprint,
            },
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == requested_work_unit_id
    assert work_unit["work_unit_fingerprint"] == requested_fingerprint
    assert work_unit["currentness_basis"]["work_unit_id"] == requested_work_unit_id
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == requested_fingerprint
    assert work_unit["state"]["typed_blocker"]["work_unit_id"] == requested_work_unit_id
    assert work_unit["state"]["typed_blocker"]["work_unit_fingerprint"] == requested_fingerprint


def test_current_work_unit_uses_progress_first_current_identity_for_stage_packet_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    current_fingerprint = "publication-blockers::497d1260db522f01"
    stale_fingerprint = (
        "owner-route::write::manuscript_story_surface_delta_missing::"
        "run_quality_repair_batch"
    )
    closeout_ref = (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat_cfb833131bfa30d6661c26c2.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
            "runtime_health_epoch": "runtime-health-event-006934-2ab409ea1e01f2c9",
            "progress_first_monitoring_summary": {
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "next_owner": "analysis-campaign",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                    "source_eval_id": (
                        "publication-eval::002-dm-china-us-mortality-attribution::"
                        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
                    ),
                    "action_type": "run_quality_repair_batch",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "owner_route_currentness_basis": {
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": current_fingerprint,
                    },
                },
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_type": "stage_packet_not_current_selected_dispatch",
            "blocked_reason": "stage_packet_not_current_selected_dispatch",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "source_ref": closeout_ref,
            "typed_blocker_ref": closeout_ref,
            "currentness_basis": {
                "owner_reason": "manuscript_story_surface_delta_missing",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "source_fingerprint": "mas_default_executor_provider_admission_source_3f9025607ed6045582b98437",
                "idempotency_key": "idem_e12d1fa19793dab9388c74cc",
                "stage_attempt_id": "sat_cfb833131bfa30d6661c26c2",
            },
        },
        blocked_reason="stage_packet_not_current_selected_dispatch",
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == current_fingerprint
    assert work_unit["action_fingerprint"] == current_fingerprint
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == current_fingerprint
    assert work_unit["state"]["typed_blocker"]["work_unit_fingerprint"] == current_fingerprint
    assert (
        work_unit["state"]["owner_answer_binding"]["work_unit_fingerprint"]
        == current_fingerprint
    )
