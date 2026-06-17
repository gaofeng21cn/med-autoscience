from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_materialized_current_control_clears_previous_gate_queue_when_ai_reviewer_is_current(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "generated_at": "2026-06-09T04:53:07+00:00",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "handoff_scan_status": "previous_gate_queue",
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "run_gate_clearing_batch",
                            "status": "queued",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": "publication_gate_replay",
                        },
                    ],
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "next_work_unit": "publication_gate_replay",
                        "source": "previous_current_control",
                    },
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:stale-gate",
                },
            ],
            "current_execution_envelopes": {
                study_id: {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                    "source": "previous_current_control",
                },
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=True,
        report={
            "scanned_at": "2026-06-09T05:16:53+00:00",
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
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "work_unit_fingerprint": "sha256:fresh-ai-reviewer-recheck",
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                    },
                },
            },
            "developer_supervisor_same_tick": {
                "stop_reason": "provider_handoff_written_transition_request_pending",
                "materialize": {
                    "owner_callable_adapters": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_gate_clearing_batch",
                            "dispatch_status": "ready",
                            "dispatch_authority": "consumer_default_executor_dispatch",
                            "next_executable_owner": "gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": "sha256:stale-gate",
                            "action_fingerprint": "sha256:stale-gate",
                        },
                    ],
                },
            },
        },
    )

    assert result is not None
    assert result["written"] is True
    assert result["action_queue"] == []
    assert result["provider_admission_pending_count"] == 0
    assert result["studies"][0]["handoff_scan_status"] == "scanned_no_provider_admission"
    assert result["current_execution_envelopes"][study_id]["owner"] == "ai_reviewer"

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["action_queue"] == []
    assert latest["provider_admission_candidates"] == []
    assert latest["current_execution_envelopes"][study_id]["owner"] == "ai_reviewer"
