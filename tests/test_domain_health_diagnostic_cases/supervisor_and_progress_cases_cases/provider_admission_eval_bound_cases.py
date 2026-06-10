from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_current_ai_reviewer_gate_replay_provider_admission_identity_is_eval_bound() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T155750Z::sat_619d680b6dc5c74022af4a3b"
    )
    coarse_ticket = (
        "study-progress-current-owner-ticket::"
        f"{study_id}::{work_unit_id}::run_gate_clearing_batch"
    )

    action = module._study_current_action_for_provider_admission(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "status": "executable_owner_action",
                "study_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": coarse_ticket,
                "action_fingerprint": coarse_ticket,
                "currentness_basis": {
                    "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                    "runtime_health_epoch": "runtime-health-event-006574-c1b18e8bf42712c4",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": coarse_ticket,
                },
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "finalize",
                "work_unit_id": work_unit_id,
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                },
            },
            "intervention_lane": {
                "route_back_checklist": {
                    "evidence_refs": [
                        (
                            "/workspace/studies/003/artifacts/publication_eval/"
                            "ai_reviewer_responses/20260610T160042Z_publication_eval_record.json"
                        )
                    ],
                    "source_eval_id": source_eval_id,
                }
            },
        }
    )

    assert action is not None
    expected_fingerprint = (
        "current-ai-reviewer-gate-replay::"
        f"{study_id}::{work_unit_id}::{source_eval_id}"
    )
    assert action["work_unit_fingerprint"] == expected_fingerprint
    assert action["action_fingerprint"] == expected_fingerprint
    source_refs = action["owner_route"]["source_refs"]
    assert source_refs["source_eval_id"] == source_eval_id
    assert source_refs["work_unit_fingerprint"] == expected_fingerprint
    assert source_refs["owner_route_currentness_basis"]["source_eval_id"] == source_eval_id
    assert source_refs["owner_route_currentness_basis"]["work_unit_fingerprint"] == expected_fingerprint

    previous_action = {
        **action,
        "action_fingerprint": action["action_fingerprint"].replace(
            "sat_619d680b6dc5c74022af4a3b",
            "sat_previous",
        ),
        "work_unit_fingerprint": action["work_unit_fingerprint"].replace(
            "sat_619d680b6dc5c74022af4a3b",
            "sat_previous",
        ),
    }
    assert module._provider_admission_action_key(action) != module._provider_admission_action_key(
        previous_action
    )


def test_fresh_progress_currentness_preserves_ai_reviewer_gate_replay_basis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T155750Z::sat_619d680b6dc5c74022af4a3b"
    )

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "generated_at": "2026-06-10T16:24:29+00:00",
            "current_work_unit": {"status": "executable_owner_action"},
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
            "current_executable_owner_action": {
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "domain_transition": {
                "completion_receipt_consumption": {"source_eval_id": source_eval_id},
            },
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "canonical_work_unit_identity": {"source_eval_id": source_eval_id},
                }
            },
            "intervention_lane": {
                "route_back_checklist": {
                    "evidence_refs": [
                        (
                            "/workspace/studies/003/artifacts/publication_eval/"
                            "ai_reviewer_responses/20260610T160042Z_publication_eval_record.json"
                        )
                    ]
                }
            },
        },
    )

    status = module._with_fresh_progress_currentness(
        profile=profile,
        study_root=study_root,
        status_payload={"study_id": study_id},
    )

    assert status["domain_transition"]["completion_receipt_consumption"]["source_eval_id"] == source_eval_id
    assert status["progress_first_monitoring_summary"]["dispatch_consumption"][
        "canonical_work_unit_identity"
    ]["source_eval_id"] == source_eval_id
    assert "ai_reviewer_responses/20260610T160042Z_publication_eval_record.json" in status[
        "intervention_lane"
    ]["route_back_checklist"]["evidence_refs"][0]

