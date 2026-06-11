from __future__ import annotations

import importlib
from pathlib import Path


def test_provider_admission_current_control_records_retained_pending_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-ai-reviewer"
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
        "dispatch_path": str(
            profile.studies_root
            / study_id
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ),
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:00:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "mas_provider_admission_identity",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["study_id"] == study_id
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == action_fingerprint
