from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import (
    dump_json,
    make_progress_projection_payload,
)


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
    progress_projection_calls: list[dict[str, object]] = []

    def progress_projection(**kwargs: object) -> dict[str, object]:
        progress_projection_calls.append(dict(kwargs))
        return status_payload

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", progress_projection)
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
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
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
    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["managed_study_opl_transition_request_candidates"] == []
    action = result["managed_study_actions"][0]
    assert action["decision"] == "human_gate"
    assert action["paper_recovery_state"]["phase"] == "human_gate"
    assert action["paper_recovery_state"]["next_safe_action"]["provider_admission_allowed"] is False
    assert action["current_executable_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["current_executable_owner_action"]["work_unit_id"] == work_unit_id
    assert action["current_executable_owner_action"]["action_fingerprint"] == action_fingerprint
    assert result["action_fingerprints"] == []
    assert progress_projection_calls
    assert all(call.get("sync_runtime_summary") is False for call in progress_projection_calls)
