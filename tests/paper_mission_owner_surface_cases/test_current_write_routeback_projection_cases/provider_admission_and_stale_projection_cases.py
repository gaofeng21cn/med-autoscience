from __future__ import annotations

from pathlib import Path
import json

import pytest

from med_autoscience.controllers.paper_mission_owner_surface_parts import provider_admission_projection
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_routes_rejects_provider_admission_when_retained_queue_conflicts_with_current_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_fingerprint = "sha256:stale-ai-reviewer-recheck"
    _write_json(
        stale_dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "action_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(stale_dispatch_path)},
            "owner_route": {
                "next_owner": "ai_reviewer",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_fingerprint": stale_fingerprint,
                "source_refs": {
                    "work_unit_id": "stale_ai_reviewer_recheck",
                    "work_unit_fingerprint": stale_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "stale_ai_reviewer_recheck",
                        "work_unit_fingerprint": stale_fingerprint,
                    },
                },
            },
        },
    )
    current_gate_fingerprint = "sha256:current-gate-clearing"
    studies = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(study_root),
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "action_fingerprint": current_gate_fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "canonical_current_work_unit",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    ]
    action_queue = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "queued",
            "owner": "ai_reviewer",
            "next_work_unit": "stale_ai_reviewer_recheck",
            "action_fingerprint": stale_fingerprint,
            "work_unit_fingerprint": stale_fingerprint,
            "refs": {"dispatch_path": str(stale_dispatch_path)},
        }
    ]

    candidates = provider_admission_projection.candidates_from_current_control(
        studies=studies,
        action_queue=action_queue,
        current_control_ref=str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
    )

    assert candidates == []


def test_scan_routes_projects_provider_admission_when_queue_matches_current_work_unit(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    current_gate_fingerprint = "sha256:current-gate-clearing"
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_owner_callable_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "action_fingerprint": current_gate_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
        },
    )
    studies = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(study_root),
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": current_gate_fingerprint,
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_gate_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_gate_fingerprint,
                    },
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "action_fingerprint": current_gate_fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "canonical_current_work_unit",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_gate_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    ]
    action_queue = [
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "status": "queued",
            "owner": "gate_clearing_batch",
            "next_work_unit": "publication_gate_replay",
            "action_fingerprint": current_gate_fingerprint,
            "work_unit_fingerprint": current_gate_fingerprint,
            "refs": {"dispatch_path": str(dispatch_path)},
        }
    ]

    candidates = provider_admission_projection.candidates_from_current_control(
        studies=studies,
        action_queue=action_queue,
        current_control_ref=str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
    )

    assert len(candidates) == 1
    assert candidates[0]["action_type"] == "run_gate_clearing_batch"
    assert candidates[0]["work_unit_id"] == "publication_gate_replay"
    assert candidates[0]["action_fingerprint"] == current_gate_fingerprint


def test_scan_projects_current_write_routeback_despite_stale_progress_active_run(monkeypatch, tmp_path: Path) -> None:
    scan = __import__("med_autoscience.controllers.paper_mission_owner_surface", fromlist=["paper_mission_owner_surface"])
    opl_attempts = __import__(
        "med_autoscience.controllers.paper_mission_owner_surface_parts.opl_provider_attempts",
        fromlist=["opl_provider_attempts"],
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "handoff_required",
        "reason": "opl_stage_attempt_admission_required",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002-write-route",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Controller-authorized paper repair and package rebuild from latest evidence.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-write-route",
            "source_signature": "truth-source-dm002-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": "mas-run-stale-progress-only",
        "supervision": {"active_run_id": "mas-run-stale-progress-only", "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    seen_preferred_actions: list[dict[str, object]] = []

    def fake_live_provider_attempt_for_study(**kwargs: object) -> None:
        seen_preferred_actions.extend(dict(action) for action in kwargs.get("preferred_actions") or [])
        return None

    monkeypatch.setattr(
        opl_attempts,
        "live_provider_attempt_for_study",
        fake_live_provider_attempt_for_study,
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    macro_source = study["owner_route"]["source_refs"]["study_macro_state"]
    assert macro_source["writer_state"] == "queued"
    assert macro_source["user_next"] == "repair"
    assert macro_source["reason"] == "quality"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert [item["action_type"] for item in result["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "opl_stage_attempt_admission_required"
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert study["active_run_id"] is None
    assert study["owner_route"]["active_run_id"] is None
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert study["next_owner"] == "write"
    assert [action["action_type"] for action in seen_preferred_actions] == ["run_quality_repair_batch"]
    assert seen_preferred_actions[0]["next_work_unit"] == "dm002_same_line_publication_paper_repair"


def test_fresh_ai_reviewer_write_routeback_supersedes_stale_reviewer_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.paper_mission_owner_surface", fromlist=["paper_mission_owner_surface"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm003-ai-reviewer-write-route",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-ai-reviewer-write-route",
            "source_signature": "truth-source-dm003-ai-reviewer-write-route",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::medical-prose-routeback::sha256-current",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "blocked"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                    "overall_style_verdict": "revise",
                }
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Repair current AI reviewer manuscript-quality concerns.",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair Methods, n/N reporting, tables, and journal prose.",
                },
            }
        ],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "opl_stage_attempt_admission_required"
    assert action["next_work_unit"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "domain-transition::route_back_same_line::medical_prose_write_repair"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["source_refs"]["source_eval_id"] == publication_eval_payload["eval_id"]


def test_owner_receipt_consumption_routes_domain_transition_reviewer_successor_over_gate_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.paper_mission_owner_surface", fromlist=["paper_mission_owner_surface"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("# Draft\n\nCurrent repaired manuscript.\n", encoding="utf-8")
    ai_reviewer_request = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    gate_replay_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    _write_json(
        ai_reviewer_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested"},
        },
    )
    _write_json(
        gate_replay_request,
        {"request_kind": "run_gate_replay_after_repair", "request_lifecycle": {"state": "requested"}},
    )
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "publication-blockers::0915410f804b3697",
            "source_eval_id": "publication-eval::dm003::owner-receipt-consumption",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "publication-eval::dm003::owner-receipt-consumption",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_refs": [str(gate_replay_request)],
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "medical_prose_write_repair",
            "repair_execution_evidence_ref": str(evidence_path),
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request),
            "gate_replay_request_ref": str(gate_replay_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-owner-receipt-consumption",
            "source_signature": "truth-source-dm003-owner-receipt-consumption",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "queued",
        "paper_stage": "analysis-campaign",
        "active_run_id": None,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": study_id,
            "quest_id": quest_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "owner_receipt_ref": str(receipt_path),
        },
        "paper_recovery_state": {
            "phase": "owner_receipt_recorded",
            "next_safe_action": {
                "kind": "consume_owner_receipt",
                "owner_receipt_ref": str(receipt_path),
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
            },
        },
        "domain_transition": status_payload["domain_transition"],
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm003::owner-receipt-consumption",
        "study_id": study_id,
        "quest_id": quest_id,
        "overall_verdict": "blocked",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
        live_attempt_max_inspect_count=0,
        provider_readiness_timeout_seconds=0,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert action["next_work_unit"] == "ai_reviewer_medical_prose_quality_review"
    assert action["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["current_work_unit"] == {}
    assert study["current_execution_envelope"] == {}
    assert study["current_executable_owner_action"] is None
    assert study["legacy_execution_projection_boundary"]["next_action_authority"] is False
    assert study["current_execution_evidence"]["diagnostic_only"] is True
    assert study["current_execution_evidence"]["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert (
        study["current_execution_evidence"]["action_queue"][0]["next_work_unit"]
        == "ai_reviewer_medical_prose_quality_review"
    )
