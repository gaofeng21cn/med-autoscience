from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materializer_turns_dm002_anti_loop_owner_gate_into_publishability_repair_sprint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    gate_fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    repair_fingerprint = "publishability-repair-sprint::anti-loop::ai_reviewer_record_gate_consumption"
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "owner_answer_binding": {
                        "answer_kind": "typed_blocker_ref",
                        "typed_blocker_ref": (
                            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
                            "#typed_blocker"
                        ),
                        "latest_owner_answer_ref": (
                            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
                            "#typed_blocker"
                        ),
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": gate_fingerprint,
                        "stage_attempt_id": "sat_67e10efde628859185249aa0",
                    },
                    "typed_blocker": {
                        "blocker_type": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": gate_fingerprint,
                        "latest_owner_answer_kind": "typed_blocker",
                        "owner_answer_shape": "typed_blocker_ref",
                        "latest_owner_answer_ref": (
                            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
                            "#typed_blocker"
                        ),
                    },
                },
            },
            "terminal_closeout_precedence_evidence": {
                "stage_attempt_id": "sat_67e10efde628859185249aa0",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": gate_fingerprint,
                "source_path": (
                    "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                    "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
                ),
                "paper_stage_log": {
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": ["anti_loop_budget_exhausted"],
                    "next_forced_delta": {
                        "required_delta": (
                            "publishability_repair_sprint_or_single_typed_blocker_"
                            "or_human_or_operator_gate"
                        ),
                    },
                },
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "conditions": [
                    {
                        "condition": "terminal_typed_blocker_owner_gate_required",
                        "blocker_type": "anti_loop_budget_exhausted",
                    }
                ],
                "current_authority": {
                    "owner": "one-person-lab",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": gate_fingerprint,
                        "blocker_type": "anti_loop_budget_exhausted",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": "supervisor-decision::materialize_recovery_action::paper-autonomy::dm002",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_gate",
                    "owner": "one-person-lab",
                    "provider_admission_allowed": False,
                    "required_input": (
                        "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
                    ),
                    "successor_owner_gate": {
                        "owner": "one-person-lab",
                        "required_input": (
                            "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
                        ),
                        "work_unit_id": "ai_reviewer_record_gate_consumption",
                        "work_unit_fingerprint": gate_fingerprint,
                        "source_surface": "terminal_typed_blocker.next_forced_delta",
                        "evidence_refs": [
                            (
                                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                                "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
                            )
                        ],
                    },
                },
            },
            "authority_snapshot": {
                "allowed_controller_actions": [
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["work_unit_id"] == "publishability_repair_sprint"
    assert dispatch["work_unit_fingerprint"] == repair_fingerprint
    assert dispatch["action_fingerprint"] == repair_fingerprint
    assert dispatch["source_action_ref"]["authority"] == "paper_recovery_state"
    assert dispatch["source_action_ref"]["required_delta_kind"] == (
        "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
    )
    assert dispatch["owner_route_ref"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert dispatch["owner_route_ref"]["source_refs"]["bridge_authority"] == (
        "domain_action_request_materializer_paper_recovery_owner_callable"
    )
    assert dispatch["owner_route_ref"]["source_refs"]["predecessor_action_type"] == (
        "run_gate_clearing_batch"
    )
    assert dispatch["owner_route_ref"]["source_refs"]["predecessor_work_unit_id"] == (
        "ai_reviewer_record_gate_consumption"
    )
