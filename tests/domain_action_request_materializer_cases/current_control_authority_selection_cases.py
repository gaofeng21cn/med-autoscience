from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_materializer_selects_identity_different_current_owner_action_over_prior_typed_blocker(
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
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                    "work_unit_id": "publication_gate_replay",
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "target_surface": {
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
            },
        },
        "current_owner_ticket": {
            "surface_kind": "mas_current_owner_ticket",
            "owner": "write",
            "allowed_action": "run_gate_clearing_batch",
            "work_unit": {
                "work_unit_id": "ai_reviewer_record_gate_consumption",
            },
            "target_surface": {
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
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
            "studies": [progress_payload],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return dict(progress_payload)

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    assert result["request_tasks"][0]["action_type"] == "run_quality_repair_batch"
    assert result["request_tasks"][0]["authority"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    assert result["domain_progress_transition_requests"][0]["dispatch_status"] == "dry_run"
    assert result["request_tasks"][0]["handoff_packet"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert (
        result["domain_progress_transition_requests"][0]["source_action"]["work_unit_id"]
        == "analysis_claim_evidence_repair"
    )
    assert (
        result["domain_progress_transition_requests"][0]["action_fingerprint"]
        == "publication-blockers::497d1260db522f01"
    )


def test_materializer_selects_owner_gate_route_back_followthrough_over_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    fingerprint = "publication-blockers::497d1260db522f01"
    route_back_ref = "route_back:owner-gate-decision:c7027de42ca336cfe0782428"
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_gate_replay_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_gate_clearing_batch",
        "action_id": "stale-gate-replay",
        "owner": "one-person-lab",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "stale-publication-gate-replay",
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "MedAutoScience",
                "authority": "med-autoscience",
            },
            "conditions": [
                {
                    "condition": "accepted_owner_gate_decision",
                    "decision": "route_back_to_mas_packet_materialization_bug",
                }
            ],
            "next_safe_action": {
                "kind": "route_back_to_owner_or_repair_materialization",
                "owner": "MedAutoScience",
                "provider_admission_allowed": False,
                "accepted_owner_gate_decision": {
                    "decision": "route_back_to_mas_packet_materialization_bug",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": fingerprint,
                    "route_back_evidence_ref": route_back_ref,
                },
            },
            "evidence_refs": [
                "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
                route_back_ref,
                "owner-gate-decision:c7027de42ca336cfe0782428",
            ],
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
            "studies": [{**progress_payload, "action_queue": [stale_gate_replay_action]}],
            "action_queue": [stale_gate_replay_action],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return dict(progress_payload)

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    assert result["request_tasks"][0]["action_type"] == "run_quality_repair_batch"
    assert result["request_tasks"][0]["authority"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert result["request_tasks"][0]["request_owner"] == "write"
    assert result["request_tasks"][0]["reason"] == "analysis_claim_evidence_repair"
    assert result["request_tasks"][0]["handoff_packet"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["request_tasks"][0]["handoff_packet"]["work_unit_fingerprint"] == fingerprint
    assert result["request_tasks"][0]["source_action"]["source_ref"] == route_back_ref
    assert result["request_tasks"][0]["source_action"]["provider_admission_allowed"] is False
    assert result["request_tasks"][0]["source_action"]["paper_progress_stall"] == {
        "kind": "owner_gate_route_back",
        "route_back_evidence_ref": route_back_ref,
        "provider_admission_allowed": False,
        "provider_admission_requires_opl_runtime_result": True,
    }
    assert result["domain_progress_transition_requests"][0]["action_fingerprint"] == fingerprint
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_gate_clearing_batch": "superseded_by_fresh_study_progress_current_owner_ticket",
    }


def test_opl_authorization_typed_blocker_fails_closed_before_gate_replay_materialization(
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
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:blocked-publication-gate-replay",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:blocked-publication-gate-replay",
                },
                "stale_queue_or_handoff_can_override": True,
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {
                "blocker_id": "opl_execution_authorization_required",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:blocked-publication-gate-replay",
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:new-gate-replay-attempt",
            "target_surface": {"surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"},
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
            "studies": [progress_payload],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return dict(progress_payload)

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert any(
        item["action_type"] == "current_execution_envelope_typed_blocker"
        and item["reason"] == "unsupported_action_type"
        for item in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    ).exists()


def test_owner_receipt_recorded_preempts_stale_owner_route_observability_action(
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
    receipt_fingerprint = "publication-blockers::0915410f804b3697"
    stale_route_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    owner_receipt_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/repair_execution_receipts/latest.json"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": study_id,
        "work_unit_fingerprint": stale_route_fingerprint,
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": ["run_gate_clearing_batch"],
        "source_refs": {
            "source_eval_id": "publication-eval::003::ai-reviewer-record",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_route_fingerprint,
            "owner_route_currentness_basis": {
                "source_eval_id": "publication-eval::003::ai-reviewer-record",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": stale_route_fingerprint,
                "truth_epoch": study_id,
            },
        },
        "currentness_contract": {
            "basis": {
                "source_eval_id": "publication-eval::003::ai-reviewer-record",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": stale_route_fingerprint,
                "truth_epoch": study_id,
            }
        },
        "idempotency_key": "owner-route::dm003::write::quest_waiting_opl_runtime_owner_route",
    }
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "action_id": (
            "supervisor-action::003-dpcc-primary-care-phenotype-treatment-gap::"
            "run_quality_repair_batch::quest_waiting_opl_runtime_owner_route"
        ),
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "next_work_unit": "medical_prose_write_repair",
        "work_unit_fingerprint": stale_route_fingerprint,
        "owner_route": owner_route,
        "handoff_packet": {
            "authority": "observability_only",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "next_executable_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": stale_route_fingerprint,
            "owner_route": owner_route,
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
                    "owner_route": owner_route,
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                    },
                    "action_queue": [stale_action],
                }
            ],
            "action_queue": [stale_action],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "owner_receipt_recorded",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": receipt_fingerprint,
                "currentness_basis": {
                    "truth_epoch": "truth-event-000035",
                    "runtime_health_epoch": "runtime-health-event-006980",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": receipt_fingerprint,
                },
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "owner_receipt_ref": owner_receipt_ref,
                    "owner_answer_binding": {
                        "answer_kind": "owner_receipt_ref",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                    "stale_queue_or_handoff_can_override": False,
                },
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "owner_answer_binding": {
                    "answer_kind": "owner_receipt_ref",
                    "owner_receipt_ref": owner_receipt_ref,
                },
            },
            "current_executable_owner_action": None,
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "obligation": {
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": receipt_fingerprint,
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

    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_quality_repair_batch": "superseded_by_current_work_unit_owner_receipt",
        "current_execution_envelope_owner_receipt_recorded": "unsupported_action_type",
    }


def test_fresh_opl_authorization_blocker_preempts_stale_executable_scan(
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
    stale_scan_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
        "state": {
            "state_kind": "executable_owner_action",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        },
    }
    stale_scan_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        "target_surface": {"surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"},
    }
    fresh_typed_blocker = {
        "blocker_type": "opl_execution_authorization_required",
        "blocked_reason": "opl_execution_authorization_required",
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
    }
    fresh_progress = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": fresh_typed_blocker,
                "stale_queue_or_handoff_can_override": False,
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": fresh_typed_blocker,
        },
        "current_executable_owner_action": None,
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
                    "current_work_unit": stale_scan_work_unit,
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                    },
                    "current_executable_owner_action": stale_scan_action,
                    "action_queue": [],
                }
            ],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return dict(fresh_progress)

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "run_gate_clearing_batch": "superseded_by_current_work_unit_typed_blocker",
        "current_execution_envelope_typed_blocker": "unsupported_action_type",
    }
