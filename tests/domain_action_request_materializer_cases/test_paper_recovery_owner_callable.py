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

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
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
        / "owner_callable_adapters"
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

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
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
    assert dispatch["source_action"]["supervisor_policy_projection"] == (
        "paper_autonomy_supervisor_policy_projection"
    )
    assert dispatch["source_action"]["supervisor_authority"] == (
        "paper_autonomy_supervisor_policy_projection"
    )
    assert dispatch["source_action"]["supervisor_authority_boundary"] == (
        "policy_projection_requires_opl_readback"
    )
    boundary = dispatch["source_action"]["supervisor_policy_projection_boundary"]
    assert boundary["decision_field_role"] == "policy_recommendation_label"
    assert boundary["decision_field_is_authority"] is False
    assert boundary["mas_can_authorize_provider_admission"] is False
    assert boundary["mas_can_run_supervisor_decision_engine"] is False
    assert boundary["mas_can_store_recovery_obligation"] is False
    assert boundary["requires_opl_supervisor_decision_engine_readback"] is True
    handoff = dispatch["source_action"]["handoff_packet"]
    assert handoff["supervisor_policy_projection"] == (
        "paper_autonomy_supervisor_policy_projection"
    )
    assert handoff["supervisor_policy_projection_boundary"] == boundary
    assert "supervisor_authority" not in dispatch["owner_route"]["source_refs"]
    assert dispatch["action_fingerprint"] == fingerprint


def test_materializer_dispatches_identity_different_paper_recovery_successor_action(
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
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    successor_fingerprint = "publication-blockers::0915410f804b3697"
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
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "owner_answer_binding": {
                        "latest_owner_answer_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_d2b4c700b31294ab17c225d4.closeout.json"
                        )
                    },
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "latest_owner_answer_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_d2b4c700b31294ab17c225d4.closeout.json"
                        ),
                    },
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "gate_replay_status": "blocked",
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": successor_fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "latest_record_path": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "controller/gate_clearing_batch/latest.json"
                ),
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
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["work_unit_id"] == "medical_prose_write_repair"
    assert dispatch["work_unit_fingerprint"] == successor_fingerprint
    assert dispatch["source_action"]["authority"] == "paper_recovery_state"
    assert dispatch["source_action"]["reason"] == "publication_gate_replay_blocked"
    assert dispatch["source_action"]["supervisor_decision"]["decision"] == (
        "materialize_recovery_action"
    )
    assert dispatch["owner_route"]["source_refs"]["predecessor_work_unit_id"] == (
        "publication_gate_replay"
    )
    assert dispatch["owner_route"]["source_refs"]["predecessor_work_unit_fingerprint"] == (
        gate_fingerprint
    )


def test_materializer_prefers_fresh_paper_recovery_successor_over_stale_scan_state(
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
    stale_repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"

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
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "action_fingerprint": gate_fingerprint,
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_type": "current_owner_route_missing",
                                "owner": "one-person-lab",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": gate_fingerprint,
                            },
                        },
                    },
                    "paper_recovery_state": {
                        "phase": "owner_action_ready",
                        "current_authority": {
                            "owner": "one-person-lab",
                            "obligation": {
                                "study_id": study_id,
                                "quest_id": quest_id,
                                "owner": "one-person-lab",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": gate_fingerprint,
                                "blocker_type": "medical_prose_write_repair",
                            },
                        },
                        "supervisor_decision": {
                            "decision": "materialize_recovery_action",
                            "decision_id": "supervisor-decision::materialize_recovery_action::stale-scan",
                        },
                        "next_safe_action": {
                            "kind": "materialize_successor_owner_action",
                            "owner": "write",
                            "provider_admission_allowed": True,
                            "successor_owner_action": {
                                "action_type": "run_quality_repair_batch",
                                "owner": "write",
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": stale_repair_fingerprint,
                                "source_surface": "stale_scan.paper_recovery_state",
                                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            },
                        },
                    },
                    "action_queue": [],
                }
            ],
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
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "current_owner_route_missing",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                },
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "conditions": [
                    {
                        "condition": "terminal_typed_blocker_successor_evidence",
                        "blocker_type": "current_owner_route_missing",
                    }
                ],
                "current_authority": {
                    "owner": "one-person-lab",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "blocker_type": "current_owner_route_missing",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": "supervisor-decision::materialize_recovery_action::fresh",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "gate_clearing_batch",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_gate_clearing_batch",
                        "owner": "gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    },
                },
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_done": True,
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
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["next_executable_owner"] == "gate_clearing_batch"
    assert dispatch["work_unit_id"] == "publication_gate_replay"
    assert dispatch["work_unit_fingerprint"] == gate_fingerprint
    assert dispatch["source_action"]["source_ref"] != (
        "supervisor-decision::materialize_recovery_action::stale-scan"
    )
    assert dispatch["owner_route"]["source_refs"]["successor_source_surface"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )


def test_materializer_prefers_fresh_progress_owner_action_over_stale_scan_paper_recovery(
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
    gate_fingerprint = (
        "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    )
    repair_fingerprint = "publication-blockers::0915410f804b3697"

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
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "action_fingerprint": gate_fingerprint,
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_type": "current_owner_route_missing",
                                "owner": "one-person-lab",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": gate_fingerprint,
                            },
                        },
                    },
                    "paper_recovery_state": {
                        "phase": "owner_action_ready",
                        "current_authority": {
                            "owner": "one-person-lab",
                            "obligation": {
                                "study_id": study_id,
                                "quest_id": quest_id,
                                "owner": "one-person-lab",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": gate_fingerprint,
                                "blocker_type": "current_owner_route_missing",
                            },
                        },
                        "supervisor_decision": {
                            "decision": "materialize_recovery_action",
                            "decision_id": "supervisor-decision::materialize_recovery_action::stale-scan",
                        },
                        "next_safe_action": {
                            "kind": "run_mas_owner_callable",
                            "owner": "one-person-lab",
                            "provider_admission_allowed": False,
                            "owner_callable": {
                                "owner": "one-person-lab",
                                "action_type": "run_gate_clearing_batch",
                                "callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
                            },
                        },
                    },
                    "action_queue": [],
                }
            ],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "action_fingerprint": repair_fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "target_surface": {
                    "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
                },
            },
            "owner_route": {
                "surface": "domain_route_owner_route",
                "schema_version": 2,
                "study_id": study_id,
                "quest_id": quest_id,
                "truth_epoch": f"truth-epoch::{study_id}",
                "route_epoch": f"truth-epoch::{study_id}",
                "runtime_health_epoch": f"runtime-health::{study_id}::repair",
                "work_unit_fingerprint": repair_fingerprint,
                "source_fingerprint": repair_fingerprint,
                "current_owner": "mas_controller",
                "next_owner": "write",
                "owner_reason": "medical_prose_write_repair",
                "active_run_id": None,
                "allowed_actions": ["run_quality_repair_batch"],
                "blocked_actions": [],
                "idempotency_key": f"owner-route::{study_id}::medical_prose_write_repair",
                "source_refs": {
                    "study_truth_epoch": f"truth-epoch::{study_id}",
                    "runtime_health_epoch": f"runtime-health::{study_id}::repair",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "owner_route_currentness_basis": {
                        "runtime_health_epoch": f"runtime-health::{study_id}::repair",
                        "truth_epoch": f"truth-epoch::{study_id}",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                    },
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

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["work_unit_id"] == "medical_prose_write_repair"
    assert dispatch["work_unit_fingerprint"] == repair_fingerprint
    assert dispatch["source_action"]["authority"] == "study_progress.current_executable_owner_action"
    assert any(
        item["action_type"] == "run_gate_clearing_batch"
        and item["reason"] == "superseded_by_fresh_study_progress_current_owner_ticket"
        for item in result["ignored_actions"]
    )


def test_materializer_suppresses_paper_recovery_after_same_identity_owner_receipt(
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
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    owner_receipt_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/repair_execution_receipts/latest.json"
    )
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
                "status": "owner_receipt_recorded",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "owner_receipt_ref": owner_receipt_ref,
                    "owner_answer_binding": {
                        "answer_kind": "owner_receipt_ref",
                        "owner_receipt_ref": owner_receipt_ref,
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "owner_answer_binding": {
                    "answer_kind": "owner_receipt_ref",
                    "owner_receipt_ref": owner_receipt_ref,
                },
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                        "blocker_type": "medical_prose_write_repair",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": "supervisor-decision::materialize_recovery_action::dm003",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
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

    assert result["domain_progress_transition_request_count"] == 0
    assert result["request_task_count"] == 0
    assert result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"] == []


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
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["work_unit_id"] == "publishability_repair_sprint"
    assert dispatch["work_unit_fingerprint"] == repair_fingerprint
    assert dispatch["action_fingerprint"] == repair_fingerprint
    assert dispatch["source_action"]["authority"] == "paper_recovery_state"
    assert dispatch["source_action"]["required_delta_kind"] == (
        "publishability_repair_sprint_or_single_typed_blocker_or_human_or_operator_gate"
    )
    assert dispatch["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert dispatch["owner_route"]["source_refs"]["bridge_authority"] == (
        "domain_action_request_materializer_paper_recovery_owner_callable"
    )
    assert dispatch["owner_route"]["source_refs"]["predecessor_action_type"] == (
        "run_gate_clearing_batch"
    )
    assert dispatch["owner_route"]["source_refs"]["predecessor_work_unit_id"] == (
        "ai_reviewer_record_gate_consumption"
    )


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

    observe_payload = module.current_owner_callable_adapters(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=False,
    )
    execution_payload = module.current_owner_callable_adapters(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert observe_payload["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0][
        "dispatch_status"
    ] == "dry_run"
    assert execution_payload["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0][
        "dispatch_status"
    ] == "transition_request_pending"


def test_materialize_dry_run_reports_paper_recovery_callable_as_would_be_ready(
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
    fingerprint = "sha256:paper-recovery-successor-ready"
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
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "current_owner_route_missing",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "one-person-lab",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "blocker_type": "current_owner_route_missing",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": "supervisor-decision::materialize_recovery_action::dm003",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "gate_clearing_batch",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_gate_clearing_batch",
                        "owner": "gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    },
                },
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert result["dry_run"] is True
    assert result["dispatch_ready_for_execution_preview"] is False
    assert result["dispatch_ready_for_execution_preview_requested"] is True
    assert result["dispatch_ready_for_execution_preview_blocked_reason"] == (
        "opl_execution_authorization_required"
    )
    assert result["written_files"] == []
    assert result["domain_progress_transition_request_count"] == 1
    assert result["ready_domain_progress_transition_request_count"] == 0
    assert result["transition_request_pending_domain_progress_transition_request_count"] == 1
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert dispatch["opl_transition_runtime_required_for_durable_carrier"] is True
    assert dispatch["dispatch_ready_for_execution_authority"] is False
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )
    assert dispatch["work_unit_id"] == "publication_gate_replay"
    assert dispatch["work_unit_fingerprint"] == fingerprint
