from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_projects_canonical_current_work_unit_aliases() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "canonical_gate_replay_unit",
                "required_output_contract": {
                    "owner_receipt_required": True,
                    "typed_blocker_accepted": True,
                    "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
                    "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "finalize",
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
                "acceptance_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
            "next_forced_delta": {
                "required_delta_kind": "stale_delta",
                "work_unit_id": "stale_delta_unit",
                "owner_action": {
                    "next_owner": "stale-owner",
                    "work_unit_id": "stale_delta_unit",
                    "allowed_actions": ["stale_action"],
                },
            },
        }
    )

    assert monitoring["current_work_unit"]["work_unit_id"] == "canonical_gate_replay_unit"
    assert monitoring["owner_action_current"] is True
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "canonical_gate_replay_unit"
    assert monitoring["next_forced_delta"]["required_delta_kind"] == (
        "publication_gate_replay_delta_or_typed_blocker"
    )
    assert monitoring["next_forced_delta"]["work_unit_id"] == "canonical_gate_replay_unit"
    assert monitoring["next_forced_delta"]["owner_action"]["next_owner"] == "finalize"


def test_progress_first_monitoring_keeps_terminal_domain_blocker_over_artifact_and_repeat_gate_actions() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "artifact_os",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "display_surface_materialization_failed",
                        "blocked_reason": "display_surface_materialization_failed",
                        "owner": "artifact_os",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "terminal_closeout_status": "blocked",
                        "terminal_closeout_outcome": "blocked_with_domain_typed_blocker",
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": work_unit_id,
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": work_unit_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "artifact_native_contract_ref": "mas-opl-stage-native-artifact-contract.v1",
                "stale_platform_repairs": ["sat_857dcf8b3164f75dfd037e22"],
                "next_owner_action": {
                    "next_owner": "08-publication_package_handoff",
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                    "allowed_actions": ["materialize_stage_artifact_delta"],
                    "required_delta_kind": "stage_artifact_delta",
                },
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "active_stage_attempt_id": "sat_857dcf8b3164f75dfd037e22",
                "action_queue": [],
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_857dcf8b3164f75dfd037e22",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "paper_stage_log": {
                        "stage_name": "run_gate_clearing_batch",
                        "outcome": "blocked_with_domain_typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [
                            "display_surface_materialization_failed",
                            "template_execution_mode_mismatch",
                        ],
                        "next_forced_delta": {
                            "required_delta_kind": "repair_display_surface_materialization_then_replay_gate",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "artifact_os",
                                "action_type": "artifact_display_surface_materialization_required",
                            },
                        },
                    },
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["owner_action_current"] is False
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["owner_action_admission"] is None
    assert monitoring["typed_blocker"]["blocker_type"] == "display_surface_materialization_failed"
    assert monitoring["next_owner"] == "artifact_os"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == work_unit_id


def test_progress_first_monitoring_prefers_canonical_typed_blocker_over_stale_terminal_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": (
                    "owner-route::write::manuscript_story_surface_delta_missing::"
                    "run_quality_repair_batch"
                ),
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "surface_kind": "mas_domain_typed_blocker",
                        "blocker_type": "anti_loop_budget_exhausted",
                        "blocker_kind": "anti_loop_budget_exhausted",
                        "reason": "anti_loop_budget_exhausted",
                        "blocker_id": "opl_execution_authorization_required",
                        "blocked_reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": (
                            "owner-route::write::manuscript_story_surface_delta_missing::"
                            "run_quality_repair_batch"
                        ),
                    },
                },
            },
            "current_blockers": [
                "quest marked running but no live session",
                "stale owner-route handoff residue",
            ],
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [],
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_stale_terminal",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "source_path": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_stale_terminal.closeout.json"
                    ),
                    "paper_stage_log": {
                        "stage_name": "run_quality_repair_batch",
                        "outcome": "blocked_with_domain_typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": ["opl_execution_authorization_required"],
                        "next_forced_delta": {
                            "required_delta_kind": "legacy_runtime_owner_route",
                            "work_unit_id": "stale_runtime_authorization",
                            "owner_action": {
                                "next_owner": "one-person-lab",
                                "action_type": "recover_runtime",
                            },
                        },
                    },
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert monitoring["typed_blocker"]["work_unit_id"] == work_unit_id
    assert monitoring["next_owner"] == "one-person-lab"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == work_unit_id
    assert monitoring["current_blockers"] == ["anti_loop_budget_exhausted"]


def test_progress_first_monitoring_blocks_admission_when_canonical_typed_blocker_owns_current_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-current",
                "action_fingerprint": "sha256:gate-replay-current",
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "medical_publication_surface_blocked",
                        "blocked_reason": "medical_publication_surface_blocked",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:gate-replay-current",
                        "action_fingerprint": "sha256:gate-replay-current",
                        "source_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_gate_replay.closeout.json"
                        ),
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-current",
                "action_fingerprint": "sha256:gate-replay-current",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "provider_admission_pending_count": 0,
                "action_queue": [],
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["owner_action_current"] is False
    assert monitoring["typed_blocker"]["blocker_type"] == "medical_publication_surface_blocked"
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is True
    assert admission["hard_gate_reasons"] == ["current_work_unit_typed_blocker"]
    assert admission["blocked_by"]["current_work_unit_typed_blocker"] == {
        "status": "typed_blocker",
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "blocker_type": "medical_publication_surface_blocked",
        "blocked_reason": "medical_publication_surface_blocked",
        "source_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat_gate_replay.closeout.json"
        ),
    }


__all__ = [name for name in globals() if name.startswith("test_")]
