from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_ai_reviewer_clean_migration_gate_replay_preempts_old_re_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260605T082301Z_publication_eval_record.json"
    )
    eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_516aa4de43310413f262443b::2026-06-05T08:21:50+00:00"
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-06-05T08:23:01+00:00",
        "_projection_source_ref": str(record_path.resolve()),
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "clinical_significance": {"status": "ready"},
            "evidence_strength": {"status": "partial"},
            "novelty_positioning": {"status": "ready"},
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "blocked"},
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {"status": "requested", "route_back_required": True},
                "current_manuscript": {"status": "current"},
            }
        },
        "recommended_actions": [
            {
                "action_id": "clean-migration-publication-gate-replay",
                "action_type": "route_back_same_line",
                "priority": "now",
                "requires_controller_decision": True,
                "route_target": "review",
                "reason": "Consume the current AI reviewer record through MAS gate replay.",
                "next_work_unit": {
                    "unit_id": "publication_gate_replay_after_clean_migration",
                    "lane": "review",
                    "summary": "Consume current record-only AI-reviewer response and replay publication gate.",
                },
            }
        ],
    }
    _write_json(record_path, publication_eval)
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": None,
                "assessment_ref": str(record_path.resolve()),
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": publication_eval,
        },
    )
    old_transition = {
        "study_id": study_id,
        "decision_type": "ai_reviewer_re_eval",
        "route_target": "review",
        "controller_action": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "next_work_unit": {
            "unit_id": "ai_reviewer_recheck",
            "lane": "review",
            "summary": "Old stale controller recheck decision.",
        },
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(profile.runtime_root / quest_id),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": old_transition,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002-current-ai-record",
            "canonical_runtime_action": "external_supervisor_required",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-current-ai-record",
            "source_signature": "truth-source-dm002-current-ai-record",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(profile.runtime_root / quest_id),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert [item["action_type"] for item in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "gate_clearing_batch"
    assert action["reason"] == "publication_gate_replay_after_clean_migration"
    assert action["controller_work_unit_id"] == "publication_gate_replay_after_clean_migration"
    assert action["source_eval_id"] == eval_id
    assert action["original_route_target"] == "review"
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
