from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_control_provider_admission_reads_transition_request_path_without_legacy_dispatch_ref(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    action_type = "return_to_ai_reviewer_workflow"
    work_unit_id = "ai_reviewer_medical_prose_quality_review"
    action_fingerprint = "domain-transition::ai-reviewer-quality-review"
    transition_request_path = (
        study_root
        / "artifacts"
        / "runtime"
        / "paper_progress_transition_refs"
        / "transition_requests"
        / f"{action_type}.json"
    )
    dump_json(
        transition_request_path,
        {
            "surface": "opl_domain_progress_transition_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "action_fingerprint": action_fingerprint,
            "owner_route": {
                "next_owner": "ai_reviewer",
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-current",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                    },
                },
            },
            "refs": {"transition_request_ref": str(transition_request_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": action_type,
                    "status": "transition_request_pending",
                    "owner": "one-person-lab",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
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
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "ai_reviewer",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                        "next_owner": "ai_reviewer",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "allowed_actions": [action_type],
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "ai_reviewer",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["dispatch_path"] == str(transition_request_path)
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["provider_attempt_or_lease_required"] is False
    assert candidate["provider_admission_pending"] is False
    assert candidate["opl_transition_runtime_required"] is True
    assert candidate["next_executable_owner"] == "ai_reviewer"


def test_current_control_provider_admission_defaults_missing_carrier_to_transition_request_path(
    tmp_path: Path,
) -> None:
    actions = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    action_type = "return_to_ai_reviewer_workflow"

    result = actions._current_control_action_dispatch_path(  # noqa: SLF001
        {},
        study_root=study_root,
        action_type=action_type,
    )

    assert result == (
        study_root
        / "artifacts"
        / "runtime"
        / "paper_progress_transition_refs"
        / "transition_requests"
        / f"{action_type}.json"
    ).resolve()
