from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materializer_dispatches_paper_recovery_owner_callable_for_current_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    fingerprint = "current-readiness-typed-blocker::002-dm-china-us-mortality-attribution::current"
    owner_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="MedAutoScience",
        owner_reason="complete_medical_paper_readiness_surface",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    owner_route["work_unit_fingerprint"] = fingerprint
    owner_route["source_refs"] = {
        **dict(owner_route["source_refs"]),
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": fingerprint,
        "owner_route_currentness_basis": {
            "truth_epoch": f"truth-epoch::{study_id}",
            "runtime_health_epoch": f"runtime-health::{study_id}",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": fingerprint,
        },
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": quest_id,
        "owner": "MedAutoScience",
        "action_type": "complete_medical_paper_readiness_surface",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "medical_paper_readiness_missing",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
            },
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
                    "owner_route": owner_route,
                    "current_work_unit": current_work_unit,
                    "paper_recovery_state": {
                        "phase": "owner_action_ready",
                        "conditions": [
                            {
                                "condition": "current_mas_owner_callable_ready",
                                "reason": "medical_paper_readiness_missing",
                            }
                        ],
                        "current_authority": {
                            "owner": "MedAutoScience",
                            "obligation": {
                                "study_id": study_id,
                                "quest_id": quest_id,
                                "owner": "MedAutoScience",
                                "action_type": "complete_medical_paper_readiness_surface",
                                "work_unit_id": "complete_medical_paper_readiness_surface",
                                "work_unit_fingerprint": fingerprint,
                                "blocker_type": "medical_paper_readiness_missing",
                            },
                        },
                        "next_safe_action": {
                            "kind": "run_mas_owner_callable",
                            "owner": "MedAutoScience",
                            "provider_admission_allowed": False,
                            "owner_callable": {
                                "owner": "MedAutoScience",
                                "action_type": "complete_medical_paper_readiness_surface",
                                "callable_surface": (
                                    "medical_paper_readiness.complete_medical_paper_readiness_surface"
                                ),
                            },
                        },
                    },
                    "action_queue": [],
                }
            ],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["default_executor_dispatch_count"] == 1
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["action_type"] == "complete_medical_paper_readiness_surface"
    assert dispatch["next_executable_owner"] == "MedAutoScience"
    assert dispatch["owner_route"]["work_unit_fingerprint"] == fingerprint
    assert dispatch["source_action"]["authority"] == "paper_recovery_state"
    assert dispatch["source_action"]["reason"] == "medical_paper_readiness_missing"
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    ).exists()


def test_materializer_dispatches_fresh_paper_recovery_owner_callable_without_scan_study(
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
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
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
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
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

    assert result["default_executor_dispatch_count"] == 1
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["next_executable_owner"] == "publication_gate"
    assert dispatch["source_action"]["authority"] == "paper_recovery_state"
    assert dispatch["source_action"]["supervisor_decision"]["decision"] == (
        "materialize_recovery_action"
    )
    assert dispatch["source_action"]["supervisor_decision_ref"].startswith(
        "supervisor-decision::materialize_recovery_action::"
    )
    assert dispatch["owner_route"]["source_refs"]["bridge_authority"] == (
        "domain_action_request_materializer_paper_recovery_owner_callable"
    )
    assert dispatch["owner_route"]["source_refs"]["supervisor_decision_ref"] == (
        dispatch["source_action"]["supervisor_decision_ref"]
    )
    assert dispatch["owner_route"]["source_refs"]["supervisor_authority"] == (
        "paper_autonomy_supervisor_decision"
    )
    assert dispatch["action_fingerprint"] == fingerprint


def test_current_default_dispatch_for_execution_marks_paper_recovery_callable_ready(
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
    fingerprint = "sha256:paper-recovery-ready-for-execution"
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
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
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

    observe_payload = module.current_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=False,
    )
    execution_payload = module.current_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert observe_payload["default_executor_dispatches"][0]["dispatch_status"] == "dry_run"
    assert execution_payload["default_executor_dispatches"][0]["dispatch_status"] == "ready"
