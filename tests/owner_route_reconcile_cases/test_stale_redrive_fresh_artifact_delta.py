from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_repeated_nonconsumable_execution(study_root: Path, owner_route: dict) -> None:
    def execution(execution_id: str) -> dict:
        return {
            "surface": "default_executor_dispatch_execution",
            "schema_version": 1,
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "execution_status": "executed",
            "execution_id": execution_id,
            "idempotency_key": owner_route["idempotency_key"],
            "current_owner_route": owner_route,
            "prompt_contract": {"owner_route": owner_route},
            "owner_result": {
                "status": "executed",
                "ok": True,
                "repair_execution_evidence": {
                    "status": "progress_delta_candidate",
                    "manuscript_surface_hygiene": {
                        "story_surface_delta_required": True,
                        "story_surface_delta_present": False,
                    },
                    "changed_artifact_refs": [
                        {"path": str(study_root / "paper" / "claim_evidence_map.json")}
                    ],
                },
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
        }

    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executions": [],
            "execution_ledger": [
                execution(f"execution::{study_root.name}::run_quality_repair_batch::first"),
                execution(f"execution::{study_root.name}::run_quality_repair_batch::second"),
            ],
        },
    )


def test_scan_routes_fresh_artifact_delta_supersedes_stale_redrive_budget(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::ai-reviewer-current-inputs",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [
            {
                "action_id": "route-back-current-write-after-artifact-delta",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
                "next_work_unit": {
                    "unit_id": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                    "lane": "write",
                },
            }
        ],
    }
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(publication_eval_path, publication_eval)
    truth_snapshot = {
        "truth_epoch": "truth-event-000035-after-artifact-delta",
        "source_signature": "truth-snapshot::after-fresh-artifact-delta",
    }
    status = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "active",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-fresh-artifact-delta",
            "canonical_runtime_action": "recover_runtime",
            "attempt_state": "recovering",
            "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": truth_snapshot,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                "lane": "write",
            },
            "typed_blocker": None,
        },
    }
    progress = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": truth_snapshot,
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {
                "status": "fresh",
                "latest_progress_at": "2026-06-03T04:47:17+00:00",
                "latest_progress_source": "gate_clearing_batch",
            }
        },
    }
    monkeypatch.setattr(scan, "_read_study_projection_inputs", lambda **_: (status, progress, study_id, publication_eval))
    before_receipt = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )
    owner_route = before_receipt["studies"][0]["action_queue"][0]["owner_route"]
    _write_repeated_nonconsumable_execution(study_root, owner_route)

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    receipt = study["default_executor_execution_receipt_consumption"]
    assert receipt["blocked_reason"] == "progress_first_owner_redrive_budget_exhausted"
    assert receipt["stale_blocker_resolution"]["status"] == "superseded"
    assert receipt["stale_blocker_resolution"]["basis"] == "fresh_meaningful_artifact_delta"
    assert study["blocked_reason"] != "progress_first_owner_redrive_budget_exhausted"
    assert study["next_owner"] == "write"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
    assert study["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert study["current_execution_envelope"]["typed_blocker"] is None
