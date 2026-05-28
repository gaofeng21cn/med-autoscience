from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_routes_publication_gate_blocker_to_gate_clearing_despite_external_supervisor_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::gate-recheck-only"
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "review",
                "summary": "Replay the MAS publication gate and route blockers to a bounded repair unit.",
            },
            "typed_blocker": {
                "blocker_id": "publication_gate_blocked",
                "blocker_type": "publication_gate",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-gate",
            "canonical_runtime_action": "external_supervisor_required",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-gate",
            "source_signature": "truth-source-dm003-gate",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "state": "external_supervisor_required",
            "blocked_reason": "domain_transition_publication_gate_blocker",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
        "publication_quality_readiness": {
            "status": "blocked",
            "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {
                "status": "ready",
                "missing": [],
                "blockers": [],
            }
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
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_gate_clearing_batch"]
    assert [item["action_type"] for item in result["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "gate_clearing_batch"
    assert action["reason"] == "domain_transition_publication_gate_blocker"
    assert action["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert action["owner_route"]["owner_reason"] == "domain_transition_publication_gate_blocker"
    assert action["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert study["next_owner"] == "gate_clearing_batch"
    assert study["blocked_reason"] == "domain_transition_publication_gate_blocker"
    assert study["external_supervisor_required"] is False


def test_gate_recheck_only_ai_reviewer_readiness_preempts_stale_write_routeback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::gate-recheck-only-with-stale-write-routeback"
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "review",
                "summary": "Replay the MAS publication gate after AI reviewer claim-evidence closure.",
            },
            "typed_blocker": {
                "blocker_id": "publication_gate_blocked",
                "blocker_type": "publication_gate",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-gate-recheck-only",
            "canonical_runtime_action": "external_supervisor_required",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-gate-recheck-only",
            "source_signature": "truth-source-dm003-gate-recheck-only",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:review-request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                },
            },
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "status": "ready",
                "missing_required_fields": [],
                "blockers": [],
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "current_manuscript_digest": "sha256:manuscript-current",
                "review_request_digest": "sha256:review-request-current",
                "evidence_ledger_digest": "sha256:evidence-ledger-current",
                "claim_evidence_alignment_digest": "sha256:claim-evidence-current",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Stale write route from the pre-recheck AI reviewer record.",
                "work_unit_fingerprint": (
                    "current-manuscript-ai-reviewer-routeback::write::sha256:manuscript-current"
                ),
                "next_work_unit": {
                    "unit_id": "current_manuscript_claim_evidence_alignment_repair",
                    "lane": "write",
                    "summary": "Repair boundary-metric evidence path before gate replay.",
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
    assert [item["action_type"] for item in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "gate_clearing_batch"
    assert action["reason"] == "domain_transition_publication_gate_blocker"
    assert action["next_work_unit"] == "publication_gate_replay"
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert study["next_owner"] == "gate_clearing_batch"


def test_gate_blocker_domain_transition_preempts_pending_ai_reviewer_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::ai-reviewer-current-manuscript"
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_for_submission_metadata",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "review",
                "summary": "Replay the MAS publication gate and route blockers to a bounded repair unit.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-gate-after-reviewer",
            "canonical_runtime_action": "await_explicit_resume",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-gate-after-reviewer",
            "source_signature": "truth-source-dm003-gate-after-reviewer",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "status": "ready",
                "missing_required_fields": [],
                "blockers": [],
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
    }
    ai_reviewer_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        ai_reviewer_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "status": "requested",
            "study_id": study_id,
            "quest_id": quest_id,
            "ai_reviewer_record": {
                "eval_id": eval_id,
                "study_id": study_id,
                "quest_id": quest_id,
            },
        },
    )
    monkeypatch.setattr(
        scan.ai_reviewer,
        "assessment",
        lambda **_: {
            "missing": True,
            "request_state": "requested",
            "blocked_reason": "ai_reviewer_assessment_required",
        },
    )
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
    assert [item["action_type"] for item in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["reason"] == "domain_transition_publication_gate_blocker"
    assert action["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert action["owner_route"]["owner_reason"] == "domain_transition_publication_gate_blocker"
    assert action["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["owner_route"]["source_refs"]["work_unit_id"] == "publication_gate_replay"


def test_executed_blocked_gate_replay_routes_publication_surface_back_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::blocked-gate-replay-route-back-write"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(
        gate_report_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "gate_fingerprint": "gate-fingerprint-dm003-publication-surface-blocked",
            "blockers": [
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "submission_hardening_incomplete",
                "forbidden_manuscript_terminology",
            ],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
                "submission_hardening_incomplete",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "reviewer_first_concerns_unresolved",
                    "source_path": "paper/review/review_ledger.json",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "source_eval_id": eval_id,
            "current_publication_work_unit": {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair the paper story around the current evidence and claim boundary.",
            },
            "work_unit_fingerprint": "publication-blockers::dm003-story-repair",
            "gate_replay": {
                "status": "blocked",
                "allow_write": False,
                "report_json": str(gate_report_path),
                "blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                    "forbidden_manuscript_terminology",
                ],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "owner": "publication_gate",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "review",
                "summary": "Replay the MAS publication gate and route blockers to a bounded repair unit.",
            },
            "typed_blocker": {
                "blocker_id": "publication_gate_blocked",
                "blocker_type": "publication_gate",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": eval_id,
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-blocked-gate-replay",
            "canonical_runtime_action": "external_supervisor_required",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-blocked-gate-replay",
            "source_signature": "truth-source-dm003-blocked-gate-replay",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "status": "ready",
                "missing_required_fields": [],
                "blockers": [],
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
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
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "publication_gate_route_back_write_required"
    assert action["next_work_unit"] == "manuscript_story_repair"
    assert action["controller_work_unit_id"] == "manuscript_story_repair"
    assert action["controller_route"]["authorization_basis"] == "gate_replay_route_back"
    assert action["controller_route"]["gate_clearing_batch_path"].endswith(
        "artifacts/controller/gate_clearing_batch/latest.json"
    )
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["owner_reason"] == "publication_gate_route_back_write_required"
    assert study["next_owner"] == "write"
