from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_provider_admission_current_control_cases.current_identity_cases import *  # noqa: F403,F401
from tests.test_provider_admission_current_control_cases.diagnostic_surface_cases import *  # noqa: F403,F401
from tests.test_provider_admission_current_control_cases.owner_gate_route_back_cases import *  # noqa: F403,F401
from tests.test_provider_admission_current_control_cases.queue_candidate_cases import *  # noqa: F403,F401
from tests.test_provider_admission_current_control_cases.provider_admission_report_identity_cases import *  # noqa: F403,F401
from tests.test_domain_health_diagnostic_cases.shared import dump_json


def test_current_control_provider_admission_rejects_queue_without_current_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    action_fingerprint = "sha256:gate-replay-without-current-identity"
    work_unit_id = "publication_gate_replay"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "action_fingerprint": action_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_rejects_root_action_queue_identity_under_typed_blocker(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    work_unit_id = "manuscript_story_repair"
    action_fingerprint = "gate-replay-route-back::write::publication-blockers::497d1260db522f01"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "owner_route": {
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-current",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": "stage-native-next-action::stale-dispatch-basis",
                    }
                },
            },
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "status": "queued",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "write",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "current_stage_id": "08-publication_package_handoff",
                            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "MedAutoScience",
                        "action_type": "complete_medical_paper_readiness_surface",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "target_surface": {
                            "surface_ref": "publication_handoff_owner_gate",
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {"blocker_type": "medical_paper_readiness_missing"},
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_rejects_action_queue_self_identity_under_typed_blocker(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "status": "queued",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "write",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "current_stage_id": "08-publication_package_handoff",
                            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": {
                        "next_owner": "write",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "current_stage_id": "08-publication_package_handoff",
                            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
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
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_uses_study_current_work_unit_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_fingerprint = "sha256:stale-ai-reviewer-with-current-study-work-unit"
    current_fingerprint = "sha256:current-study-gate-replay"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "action_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "queued",
                    "owner": "ai_reviewer",
                    "next_work_unit": "stale_ai_reviewer_recheck",
                    "action_fingerprint": stale_fingerprint,
                    "work_unit_fingerprint": stale_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                        "action_fingerprint": current_fingerprint,
                    },
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "work_unit_fingerprint": current_fingerprint,
                        "source_refs": {
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": current_fingerprint,
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {"blocker_type": "medical_paper_readiness_missing"},
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_uses_study_current_action_when_top_level_queue_empty(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    action_fingerprint = "domain-transition::route_back_same_line::dpcc_publication_gate_replay"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
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
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "next_work_unit": work_unit_id,
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["next_executable_owner"] == "gate_clearing_batch"


def test_current_control_provider_admission_reads_transition_request_path_without_legacy_dispatch_ref(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
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
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_actions"
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


def test_current_control_provider_admission_allows_write_owner_gate_clearing_target(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "ai_reviewer_record_gate_consumption"
    action_fingerprint = "route-currentness::dm002-write-gate-clearing-current"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_gate_clearing_batch",
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
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_gate_clearing_batch",
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
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["next_executable_owner"] == "write"
    assert candidate["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"


def test_current_control_provider_admission_rejects_write_owner_gate_clearing_without_strong_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_allows_write_quality_repair_from_study_current_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
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
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_quality_repair_batch"],
                        "target_surface": {
                            "surface_ref": (
                                "canonical manuscript story-surface delta or "
                                "typed blocker:manuscript_story_surface_delta_missing"
                            ),
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["next_executable_owner"] == "write"
    assert candidate["dispatch_path"] == str(dispatch_path)


def test_provider_admission_candidate_never_promotes_provider_completion_to_domain_completion(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    dispatch_path = tmp_path / "dispatches" / "return_to_ai_reviewer_workflow.json"
    action_fingerprint = "sha256:current-provider-admission-boundary"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    execution = {
        "source": "default_executor_execution",
        "execution_status": "handoff_ready",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": True,
        "owner_route_current": True,
        "owner_route": {
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

    candidate = provider_admission.provider_admission_candidate_from_execution(
        execution,
        execution_ref="runtime/artifacts/supervision/consumer/default_executor_execution/latest.json",
        status_study_id=study_id,
        current_action_identity={
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    )

    assert candidate is not None
    assert candidate["provider_completion_is_domain_completion"] is False
    assert candidate["authority_boundary"]["provider_completion_is_domain_completion"] is False
    assert (
        candidate["stage_transition_authority_boundary"]["provider_completion_counts_as_stage_transition"]
        is False
    )
