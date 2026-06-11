from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_user_visible_projection_prefers_current_executable_owner_action_over_stale_paper_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {
                    "route_owner": "ai_reviewer",
                    "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
                "conditions": [],
            },
            "paper_progress_state": {"next_owner": "ai_reviewer"},
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["next_owner"] == "finalize"
    assert projection["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert projection["current_executable_owner_action"]["next_owner"] == "finalize"

def test_user_visible_projection_does_not_mark_stale_live_macro_state_as_running_when_owner_action_is_pending() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "opl-stage-attempt://sat-stale"},
                "conditions": [],
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {"status": "stale"},
                "activity_timeout": {"state": "timed_out"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "artifact_delta": {"status": "stale"},
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["writer_state"] == "live"
    assert projection["actual_write_active"] is False
    assert projection["owner_resolution_state"] == "ready_for_owner_action"
    assert projection["next_owner"] == "gate_clearing_batch"
    assert projection["next_system_action"] == (
        "等待 gate_clearing_batch owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )


def test_user_visible_projection_treats_current_work_unit_typed_blocker_as_not_live() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "002-dm-china-us-mortality-attribution",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "opl-stage-attempt://sat_stale_or_superseded"},
                "conditions": [],
            },
            "supervision": {
                "active_run_id": "opl-stage-attempt://sat_stale_or_superseded",
                "health_status": "live",
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "med-autoscience",
                "action_type": "return_to_ai_reviewer_workflow",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "medical_prose_review_request_digest_missing",
                        "owner": "med-autoscience",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "med-autoscience",
                "typed_blocker": {
                    "blocker_type": "medical_prose_review_request_digest_missing",
                    "owner": "med-autoscience",
                },
            },
        }
    )

    assert projection["state"] == "queued/repair/quality"
    assert projection["writer_state"] == "queued"
    assert projection["actual_write_active"] is False
    assert projection["owner_resolution_state"] == "ready_for_owner_action"
    assert projection["next_owner"] == "med-autoscience"
    assert projection["study_macro_state"]["writer_state"] == "queued"
    assert projection["study_macro_state"]["details"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat_stale_or_superseded"
    )
    assert projection["supervision"]["active_run_id"] is None
    assert projection["supervision"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat_stale_or_superseded"
    )
    assert projection["supervision"]["liveness_suppressed_by"] == "canonical_current_work_unit"


def test_user_visible_projection_ignores_stale_run_id_when_owner_action_supersedes_user_park() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-terminal-stale",
            "supervision": {
                "active_run_id": "opl-stage-attempt://sat-terminal-stale",
                "health_status": "stale",
            },
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {
                    "decision_owner": "MedAutoScience",
                    "route_owner": "MedAutoScience",
                    "next_work_unit": "complete_medical_paper_readiness_surface",
                },
                "conditions": [
                    {
                        "type": "CurrentOwnerActionSupersedesStaleUserPark",
                        "status": "true",
                        "reason": (
                            "Stage Native current owner action exists and no current "
                            "human-gate authority ref is present."
                        ),
                    }
                ],
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
                "source_reason": "quest_waiting_for_user",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "source_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                ),
            },
        }
    )

    assert projection["state"] == "queued/repair/quality"
    assert projection["writer_state"] == "queued"
    assert projection["actual_write_active"] is False
    assert projection["owner_resolution_state"] == "ready_for_owner_action"
    assert projection["next_owner"] == "MedAutoScience"

def test_current_owner_handoff_projection_prefers_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]

def test_current_owner_handoff_decision_uses_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {"decision_type": "current_owner_handoff"},
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]


def test_current_owner_action_projection_suppresses_non_human_stale_user_park() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_stage": "auto_runtime_parked",
        "current_stage_summary": "旧 user park 投影。",
        "next_system_action": "等待用户明确确认后，再继续下一步托管推进。",
        "status_narration_contract": {
            "stage": {"current_stage": "auto_runtime_parked"},
            "next_step": "等待用户明确确认后，再继续下一步托管推进。",
        },
        "auto_runtime_parked": {
            "surface_kind": "auto_runtime_parked",
            "schema_version": 1,
            "parked": True,
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
            "source_reason": "quest_waiting_for_user",
            "runtime_failure_classification": {
                "requires_human_gate": False,
                "auto_recovery_allowed": True,
                "blocker_class": "none",
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "stage_kernel_projection.current_owner_delta",
            "next_owner": "MedAutoScience",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "allowed_actions": ["complete_medical_paper_readiness_surface"],
            "source_ref": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
            ),
        },
    }

    result = module.reconcile_current_owner_action_projection(payload)

    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_current_owner_action"] is True
    assert result["parked_state"] is None
    assert result["parked_owner"] is None
    assert result["needs_user_decision"] is False
    assert result["needs_physician_decision"] is False
    assert result["current_stage"] == "publication_supervision"
    assert result["study_macro_state"]["writer_state"] == "queued"
    assert result["study_macro_state"]["user_next"] == "repair"
    assert result["study_macro_state"]["reason"] == "quality"
    assert result["study_macro_state"]["details"]["decision_owner"] == "MedAutoScience"
    assert result["status_narration_contract"]["next_step"] == (
        "等待 MedAutoScience owner 执行 complete_medical_paper_readiness_surface，"
        "处理 work unit complete_medical_paper_readiness_surface，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )


def test_current_owner_action_projection_requires_human_gate_authority_ref() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_stage": "auto_runtime_parked",
        "auto_runtime_parked": {
            "surface_kind": "auto_runtime_parked",
            "schema_version": 1,
            "parked": True,
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
            "source_reason": "quest_waiting_for_user",
            "runtime_failure_classification": {
                "requires_human_gate": True,
                "auto_recovery_allowed": False,
                "blocker_class": "publication_gate_recheck",
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "stage_kernel_projection.current_owner_delta",
            "next_owner": "MedAutoScience",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "allowed_actions": ["complete_medical_paper_readiness_surface"],
            "source_ref": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
            ),
        },
    }

    result = module.reconcile_current_owner_action_projection(payload)

    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_current_owner_action"] is True
    assert result["parked_state"] is None
    assert result["needs_user_decision"] is False
    assert result["current_stage"] == "publication_supervision"
    assert result["study_macro_state"]["details"]["decision_owner"] == "MedAutoScience"


def test_current_owner_action_projection_preserves_authorized_human_gate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_stage": "auto_runtime_parked",
        "auto_runtime_parked": {
            "surface_kind": "auto_runtime_parked",
            "schema_version": 1,
            "parked": True,
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
            "source_reason": "quest_waiting_for_user",
            "runtime_failure_classification": {
                "requires_human_gate": True,
                "auto_recovery_allowed": False,
                "blocker_class": "publication_gate_recheck",
            },
        },
        "family_human_gates": [
            {
                "gate_id": "status-waiting-dm003-publication-gate-recheck",
                "evidence_refs": [
                    {
                        "ref_kind": "repo_path",
                        "ref": "artifacts/controller_decisions/latest.json",
                        "label": "controller_human_gate_decision",
                    }
                ],
            }
        ],
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "stage_kernel_projection.current_owner_delta",
            "next_owner": "MedAutoScience",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "allowed_actions": ["complete_medical_paper_readiness_surface"],
        },
    }

    result = module.reconcile_current_owner_action_projection(payload)

    assert result["auto_runtime_parked"]["parked"] is True
    assert "superseded_by_current_owner_action" not in result["auto_runtime_parked"]
    assert result["study_macro_state"]["writer_state"] == "parked"


__all__ = [name for name in globals() if name.startswith("test_")]
