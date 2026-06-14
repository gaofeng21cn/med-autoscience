from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": runtime_health_epoch,
                "truth_epoch": truth_epoch,
                "work_unit_fingerprint": source_fingerprint,
                "work_unit_id": owner_reason,
            },
        },
    }


def test_materializer_rejects_top_level_action_queue_disallowed_by_current_study_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dm003"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="gate_clearing_batch",
        owner_reason="current_gate_replay",
        allowed_actions=["run_gate_clearing_batch"],
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="stale_ai_reviewer_recheck",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "action_id": f"supervisor-action::{study_id}::stale-ai-reviewer",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "stale_ai_reviewer_recheck",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": stale_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": stale_route,
        },
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                }
            ],
            "action_queue": [stale_action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert result["ignored_actions"] == [
        {
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "action_id": f"supervisor-action::{study_id}::stale-ai-reviewer",
            "reason": "superseded_by_current_owner_route_action_queue",
        }
    ]
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()


def test_materializer_rejects_top_level_action_queue_with_stale_owner_route_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dm003"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="current_ai_reviewer_recheck",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="stale_ai_reviewer_recheck",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "action_id": f"supervisor-action::{study_id}::stale-ai-reviewer",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "stale_ai_reviewer_recheck",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": stale_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": stale_route,
        },
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                }
            ],
            "action_queue": [stale_action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert result["ignored_actions"] == [
        {
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "action_id": f"supervisor-action::{study_id}::stale-ai-reviewer",
            "reason": "superseded_by_current_owner_route_action_queue",
        }
    ]
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()


def test_materializer_blocks_stale_domain_transition_when_readiness_blocker_has_no_explicit_current_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="finalize",
        owner_reason="dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        allowed_actions=["run_gate_clearing_batch"],
    )
    stale_route["source_refs"] = {
        **dict(stale_route["source_refs"]),
        "source_eval_id": "publication-eval::003::stale-ai-reviewer-record",
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": (
                f"runtime-health::{study_id}::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
            ),
            "source_eval_id": "publication-eval::003::stale-ai-reviewer-record",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": stale_route["work_unit_fingerprint"],
        },
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": stale_route,
                    "action_queue": [],
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "MedAutoScience",
                        "typed_blocker": {
                            "blocker_id": "medical_paper_readiness_missing",
                            "owner": "MedAutoScience",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                        },
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_id": "medical_paper_readiness_missing",
                                "owner": "MedAutoScience",
                                "work_unit_id": "complete_medical_paper_readiness_surface",
                            },
                        },
                    },
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "owner": "finalize",
                        "controller_action": "request_opl_stage_attempt",
                        "completion_receipt_consumption": {"status": "consumed"},
                        "next_work_unit": {
                            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "lane": "finalize",
                        },
                    },
                }
            ],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-12T00:57:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "medical_paper_readiness_missing",
                        "blocker_type": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                },
            },
            "current_executable_owner_action": None,
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "finalize",
                "allowed_action": "run_gate_clearing_batch",
                "work_unit": {
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "finalize",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "completion_receipt_consumption": {"status": "consumed"},
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "finalize",
                },
            },
            "owner_route": stale_route,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert any(
        item["action_type"] == "current_execution_envelope_typed_blocker"
        and item["reason"] == "unsupported_action_type"
        for item in result["ignored_actions"]
    )
    assert any(
        item["action_type"] == "run_gate_clearing_batch"
        and item["reason"] == "superseded_by_current_work_unit_typed_blocker"
        for item in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    ).exists()


def test_materializer_allows_explicit_readiness_current_action_to_block_stale_domain_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    readiness_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    readiness_route["source_refs"] = {
        **dict(readiness_route["source_refs"]),
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": f"runtime-health::{study_id}::readiness-current-action",
            "source_eval_id": "publication-eval::003::readiness-current-action",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": readiness_route["work_unit_fingerprint"],
        },
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": readiness_route,
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "MedAutoScience",
                        "typed_blocker": {
                            "blocker_id": "medical_paper_readiness_missing",
                            "owner": "MedAutoScience",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "MedAutoScience",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "surface_key": "authoring_runtime_authorization",
                    },
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "owner": "finalize",
                        "controller_action": "request_opl_stage_attempt",
                        "completion_receipt_consumption": {"status": "consumed"},
                        "next_work_unit": {
                            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "lane": "finalize",
                        },
                    },
                }
            ],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-12T00:57:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "surface_key": "authoring_runtime_authorization",
                "source_ref": (
                    "artifacts/stage_outputs/08-publication_package_handoff/"
                    "receipts/typed_blocker.json"
                ),
            },
            "owner_route": readiness_route,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["action_type"] == "complete_medical_paper_readiness_surface"
    assert dispatch["next_executable_owner"] == "MedAutoScience"
    assert dispatch["source_action"]["authority"] == "mas_owner_surface"
    assert dispatch["source_action"]["source_surface"] == "stage_kernel_projection.current_owner_delta"
    assert dispatch["owner_route"]["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert any(
        item["action_type"] == "run_gate_clearing_batch"
        and item["reason"] == "superseded_by_current_stage_readiness_followup"
        for item in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    ).exists()


def test_materializer_does_not_dispatch_weak_progress_current_owner_ticket(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_queue": [],
                }
            ],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-12T02:40:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "study_progress.next_forced_delta.owner_action",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "finalize",
                "allowed_action": "run_gate_clearing_batch",
                "work_unit": {
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                },
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": study_id,
                "quest_id": quest_id,
                "truth_epoch": "2026-06-12T02:40:00+00:00",
                "route_epoch": "2026-06-12T02:40:00+00:00",
                "current_owner": "mas_controller",
                "next_owner": "finalize",
                "owner_reason": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert any(
        item["action_type"] == "run_gate_clearing_batch"
        and item["reason"]
        == "fresh_progress_current_owner_ticket_requires_strong_currentness_identity"
        for item in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    ).exists()


def test_materializer_dispatches_fresh_progress_ticket_with_strong_currentness_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_queue": [],
                }
            ],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-12T02:41:00+00:00",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "study_progress.next_forced_delta.owner_action",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_fingerprint": "sha256:current-gate-replay-source",
                "work_unit_fingerprint": "sha256:current-gate-replay-work-unit",
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "finalize",
                "allowed_action": "run_gate_clearing_batch",
                "work_unit": {
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                },
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["owner_route"]["source_fingerprint"] == "sha256:current-gate-replay-source"
    assert dispatch["owner_route"]["work_unit_fingerprint"] == "sha256:current-gate-replay-work-unit"
    assert dispatch["owner_route"]["source_refs"]["owner_route_currentness_basis"] == {
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "work_unit_fingerprint": "sha256:current-gate-replay-work-unit",
    }


def test_materializer_blocks_stale_provider_admission_when_fresh_progress_is_stop_loss_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="analysis-campaign",
        owner_reason="analysis_claim_evidence_repair",
        allowed_actions=["run_quality_repair_batch"],
    )
    stale_route["work_unit_fingerprint"] = "publication-blockers::stale"
    stale_route["source_fingerprint"] = "publication-blockers::stale"
    stale_route["source_refs"] = {
        **dict(stale_route["source_refs"]),
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": f"runtime-health::{study_id}::stale-provider-admission",
            "source_eval_id": "publication-eval::002::stale-ai-reviewer-record",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::stale",
        },
    }
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "action_id": f"provider-admission::{study_id}::run_quality_repair_batch",
        "reason": "provider_admission_pending",
        "owner": "analysis-campaign",
        "request_owner": "analysis-campaign",
        "recommended_owner": "analysis-campaign",
        "authority": "mas_provider_admission_identity",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::stale",
        "owner_route": stale_route,
        "handoff_packet": {
            "surface": "provider_admission_current_control_handoff",
            "authority": "mas_provider_admission_identity",
            "owner": "analysis-campaign",
            "request_owner": "analysis-campaign",
            "recommended_owner": "analysis-campaign",
            "next_executable_owner": "analysis-campaign",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "next_work_unit": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::stale",
            "owner_route": stale_route,
        },
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": stale_route,
                    "action_queue": [stale_action],
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "analysis-campaign",
                    },
                }
            ],
            "action_queue": [stale_action],
            "provider_admission_pending_count": 1,
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "generated_at": "2026-06-12T01:18:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "blocker_type": "anti_loop_budget_exhausted",
                    "reason": "anti_loop_budget_exhausted",
                    "owner": "one-person-lab",
                    "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                    "source_ref": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_82a2b164657c9b4d0c312db9.closeout.json"
                    ),
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_fingerprint": (
                    "owner-route::write::manuscript_story_surface_delta_missing::"
                    "run_quality_repair_batch"
                ),
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "opl_execution_authorization_required",
                        "blocker_type": "anti_loop_budget_exhausted",
                        "reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "work_unit_id": (
                            "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                        ),
                    },
                    "stale_queue_or_handoff_can_override": False,
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert any(
        item["action_type"] == "run_quality_repair_batch"
        and item["action_id"] == f"provider-admission::{study_id}::run_quality_repair_batch"
        and item["reason"] == "superseded_by_current_work_unit_typed_blocker"
        for item in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    ).exists()


from tests.domain_action_request_materializer_cases.current_control_authority_selection_cases import *  # noqa: F403,F401,E402
from tests.domain_action_request_materializer_cases.test_paper_recovery_owner_callable import *  # noqa: F403,F401,E402
