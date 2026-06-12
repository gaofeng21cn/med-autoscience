from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_input_ai_reviewer_record_consumption_route_preserves_eval_currentness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm003::current-input-ai-reviewer-record::20260528T213023Z"
    work_unit_id = "consume_current_input_ai_reviewer_record"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    review_path = study_root / "paper" / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript after input refresh.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_map_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_map_payload)
    _write_json(review_path, {"schema_version": 1})
    _write_json(charter_path, {"schema_version": 1})
    _write_json(blueprint_path, {"schema_version": 1})
    _write_json(prose_review_path, {"schema_version": 1})
    _write_json(latest_eval_path, {"schema_version": 1})
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T213023Z_publication_eval_record.json"
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": {"eval_id": eval_id, "assessment_provenance": {"owner": "ai_reviewer"}},
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "review",
                "summary": (
                    "Consume this record-only AI reviewer response and route required write reconciliation "
                    "through MAS owner surfaces."
                ),
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm003-current-input-ai-reviewer-record",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-current-input-ai-reviewer-record",
            "source_signature": "truth-source-dm003-current-input-ai-reviewer-record",
        },
    }
    progress_payload = {
        "schema_version": 1,
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
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "partial"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": _sha256_text(json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": _sha256_text(json.dumps(claim_map_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "source_eval": {"status": "current", "eval_id": eval_id},
                "current_package_freshness": {"status": "downstream_pending", "source_eval_id": eval_id},
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "reason": "Consume the current AI reviewer record through MAS owner surfaces.",
                "work_unit_fingerprint": (
                    "dm003-current-input-ai-reviewer-record::write-review-consumption-pending::2026-05-28T21:30:23Z"
                ),
                "next_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "review",
                    "summary": "Consume the current-input record-only AI reviewer response.",
                },
            }
        ],
    }
    _write_json(record_path, publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "required_currentness_refs": [
                    str(manuscript_path.resolve()),
                    str(evidence_path.resolve()),
                    str(claim_map_path.resolve()),
                ],
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": publication_eval_payload,
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
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
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["next_work_unit"] == work_unit_id
    assert action["controller_work_unit_id"] == work_unit_id
    assert action["executable_work_unit"] == work_unit_id
    assert action["source_eval_id"] == eval_id
    assert action["owner_output_consumption"] == {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": str(record_path.resolve()),
        "eval_id": eval_id,
        "consumption_mode": "refs_only_current_ai_reviewer_record",
        "required_currentness_refs": [
            str(manuscript_path.resolve()),
            str(evidence_path.resolve()),
            str(claim_map_path.resolve()),
        ],
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    assert action["route_target"] == "write"
    assert action["domain_transition_decision_type"] == "route_back_same_line"
    assert action["controller_next_work_unit"]["lane"] == "review"
    assert study["owner_route"]["source_refs"]["source_eval_id"] == eval_id
    assert study["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert study["owner_route"]["source_refs"]["work_unit_fingerprint"] == (
        f"domain-transition::route_back_same_line::{work_unit_id}"
    )
    assert study["owner_route"]["source_refs"]["publication_eval_path"] == (
        str(study_root / "artifacts" / "publication_eval" / "latest.json")
    )
    assert study["action_queue"][0]["owner"] == study["next_owner"] == study["owner_route"]["next_owner"] == "write"


def test_current_input_ai_reviewer_record_without_input_refs_keeps_ai_reviewer_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    review_path = study_root / "paper" / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript after input refresh.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_map_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_map_payload)
    _write_json(review_path, {"schema_version": 1})
    _write_json(charter_path, {"schema_version": 1})
    _write_json(blueprint_path, {"schema_version": 1})
    _write_json(prose_review_path, {"schema_version": 1})
    _write_json(latest_eval_path, {"schema_version": 1})
    eval_id = "publication-eval::dm003::stale-current-input-record::20260528T213023Z"
    stale_record = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "partial"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "consume_current_input_ai_reviewer_record",
                    "lane": "review",
                    "summary": "Consume current-input AI reviewer record.",
                },
            }
        ],
    }
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T213023Z_publication_eval_record.json"
    )
    _write_json(record_path, stale_record)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "required_currentness_refs": [str(manuscript_path.resolve())],
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": stale_record,
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                    "review_ledger": {"path": str(review_path.resolve()), "present": True, "valid": True},
                    "study_charter": {"path": str(charter_path.resolve()), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {
                        "path": str(blueprint_path.resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                    "medical_prose_review": {"path": str(prose_review_path.resolve()), "present": True, "valid": True},
                    "publication_gate_projection": {
                        "path": str(latest_eval_path.resolve()),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": stale_record,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "lane": "review",
                "summary": "Produce a current AI reviewer record against live inputs.",
            },
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-stale-current-input-record",
            "source_signature": "truth-source-dm003-stale-current-input-record",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, stale_record),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert action["required_currentness_refs"] == [
        str(manuscript_path.resolve()),
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
    ]
    assert "owner_output_consumption" not in action
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
