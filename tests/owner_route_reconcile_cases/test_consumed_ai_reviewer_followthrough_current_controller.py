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


def test_consumed_ai_reviewer_record_production_projects_current_controller_write_followthrough(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = __import__("med_autoscience.controllers.owner_route_reconcile", fromlist=["owner_route_reconcile"])
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm002::ai-reviewer-current-inputs::20260601T073237Z"
    previous_work_unit = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    followthrough_work_unit = "current_manuscript_prose_currentness_and_gate_replay_write_closeout"
    followthrough_fingerprint = f"domain-transition::route_back_same_line::{followthrough_work_unit}"
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "dm002-current-ai-reviewer-write-followthrough",
            "decision_type": "route_back_same_line",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_opl_stage_attempt"}],
            "route_target": "write",
            "work_unit_fingerprint": followthrough_fingerprint,
            "next_work_unit": {
                "unit_id": followthrough_work_unit,
                "lane": "write",
                "summary": "Replay current manuscript prose currentness and gate write closeout.",
            },
        },
    )
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260601T073237Z_publication_eval_record.json"
    )
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    manuscript_text = "# Draft\n\nCurrent DM002 manuscript.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_map_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_map_payload)
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
        "publication_eval": {"eval_id": eval_id, "assessment_provenance": {"owner": "ai_reviewer"}},
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": previous_work_unit,
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record before dispatching write.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": str(record_path.resolve()),
                "eval_id": eval_id,
                "next_action": "honor_ai_reviewer_publication_eval_authority",
            },
            "guard_boundary": {"opl_generic_runner_may_resume": False},
        },
        "runtime_health_snapshot": {
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "retry_budget_remaining": 0,
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
            "runtime_health_epoch": "runtime-health-dm002-consumed-ai-reviewer-followthrough",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-consumed-ai-reviewer-followthrough",
            "source_signature": "truth-source-dm002-consumed-ai-reviewer-followthrough",
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
        "autonomy_slo": {"breach_types": ["same_fingerprint_loop"]},
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
            "record_ref": str(record_path.resolve()),
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "source_eval": {"status": "current", "eval_id": eval_id},
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": _sha256_text(json.dumps(evidence_payload, sort_keys=True)),
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": _sha256_text(json.dumps(claim_map_payload, sort_keys=True)),
                },
            }
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm002::write-followthrough",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": followthrough_fingerprint,
                "next_work_unit": {
                    "unit_id": followthrough_work_unit,
                    "lane": "write",
                    "summary": "Replay current manuscript prose currentness and gate write closeout.",
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
                "next_work_unit": previous_work_unit,
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
    assert action["owner"] == "write"
    assert action["next_work_unit"] == followthrough_work_unit
    assert action["controller_work_unit_id"] == followthrough_work_unit
    assert action["work_unit_fingerprint"] == followthrough_fingerprint
    assert action["controller_route"]["work_unit_fingerprint"] == followthrough_fingerprint
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
    assert study["next_owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["source_refs"]["work_unit_id"] == followthrough_work_unit
    assert study["paper_progress_stall"]["terminal"] is True
