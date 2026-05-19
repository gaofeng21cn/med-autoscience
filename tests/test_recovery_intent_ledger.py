from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_status(*, study_root: Path, quest_root: Path, quest_id: str) -> dict[str, object]:
    return {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "decision": "resume",
        "reason": "quest_stopped_by_controller_guard",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {"status": "none", "worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-001",
            "canonical_runtime_action": "recover_runtime",
            "attempt_state": "recovering",
            "retry_budget_remaining": 2,
            "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-001",
            "source_signature": "truth-source-001",
        },
    }


def _base_progress(*, study_id: str, quest_id: str) -> dict[str, object]:
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "managed_runtime_escalated",
        "paper_stage": "publication_supervision",
        "supervision": {"active_run_id": None, "health_status": "recovering"},
    }


def test_scan_domain_routes_persists_recovery_intent_for_fresh_controller_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "decision-current",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "publication-blockers::current",
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            _base_status(study_root=study_root, quest_root=quest_root, quest_id=quest_id),
            _base_progress(study_id=study_id, quest_id=quest_id),
            quest_id,
            publication_eval,
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=True,
    )

    study = result["studies"][0]
    intent = study["recovery_intent"]
    expected_path = study_root / "artifacts" / "runtime" / "recovery_intent" / "latest.json"
    history_path = study_root / "artifacts" / "runtime" / "recovery_intent" / "history.jsonl"
    assert intent["current_action"] == "safe_reconcile_ready"
    assert intent["reason"] == "runtime_controller_redrive_required"
    assert intent["next_owner"] == "mas_controller"
    assert intent["retry_budget"] == {"remaining": 2, "exhausted": False}
    assert intent["last_attempt"] is None
    assert intent["last_result"] is None
    assert intent["next_eligible_tick"] == result["generated_at"]
    assert intent["dedupe_fingerprint"] == study["owner_route"]["idempotency_key"]
    assert intent["evidence_refs"]["owner_route_trace_id"] == study["owner_route"]["trace_id"]
    assert intent["quality_ready_authorized"] is False
    assert intent["publication_ready_authorized"] is False
    assert intent["submission_ready_authorized"] is False
    assert study["refs"]["recovery_intent_path"] == str(expected_path)
    assert expected_path.is_file()
    assert json.loads(expected_path.read_text(encoding="utf-8")) == intent
    assert history_path.is_file()
    assert len(history_path.read_text(encoding="utf-8").splitlines()) == 1
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8").startswith("{}")


def test_recovery_intent_projection_fail_closed_blockers(tmp_path: Path) -> None:
    ledger = importlib.import_module("med_autoscience.controllers.recovery_intent_ledger")
    study_root = tmp_path / "study"
    owner_route = {
        "schema_version": 2,
        "idempotency_key": "owner-route::fresh",
        "trace_id": "owner-route-trace::fresh",
        "next_owner": "mas_controller",
        "owner_reason": "runtime_controller_redrive_required",
        "allowed_actions": ["runtime_platform_repair"],
        "route_epoch": "truth-epoch",
        "source_fingerprint": "truth-source",
    }
    action = {
        "action_type": "runtime_platform_repair",
        "owner": "mas_controller",
        "reason": "runtime_controller_redrive_required",
        "owner_route": owner_route,
    }
    status = {
        "quest_status": "active",
        "runtime_health_snapshot": {
            "retry_budget_remaining": 2,
            "attempt_state": "recovering",
            "canonical_runtime_action": "recover_runtime",
        },
    }

    cases = {
        "stale_owner_route": {
            "owner_route": {**owner_route, "idempotency_key": "owner-route::new"},
            "action_queue": [action],
            "expected_reason": "owner_route_stale",
            "expected_action": "parked",
        },
        "route_owner_mismatch": {
            "owner_route": {
                **owner_route,
                "next_owner": "publication_gate",
                "owner_reason": "publication_gate_specificity_required",
                "allowed_actions": ["runtime_platform_repair"],
            },
            "action_queue": [{**action, "owner": "mas_controller"}],
            "expected_reason": "owner_route_mismatch",
            "expected_action": "parked",
        },
        "manual_parked": {
            "status": {"quest_status": "paused", "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold"},
            "expected_reason": "manual_parked",
            "expected_action": "parked",
        },
        "completed": {
            "status": {"quest_status": "completed", "decision": "completed"},
            "expected_reason": "completed",
            "expected_action": "parked",
        },
        "human_gate": {
            "status": {"quest_status": "active", "execution_owner_guard": {"supervisor_only": True}},
            "expected_reason": "human_gate_required",
            "expected_action": "human_gate_required",
        },
        "publication_gate_missing": {
            "status": {"quest_status": "active", "reason": "publication_gate_specificity_required"},
            "expected_reason": "publication_gate_missing",
            "expected_action": "human_gate_required",
        },
        "retry_exhausted": {
            "status": {
                "quest_status": "active",
                "runtime_health_snapshot": {
                    "retry_budget_remaining": 0,
                    "attempt_state": "escalated",
                    "canonical_runtime_action": "external_supervisor_required",
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
            },
            "action_queue": [],
            "expected_reason": "retry_exhausted",
            "expected_action": "escalated",
        },
        "failed_non_resumable_explicit_resume_projection": {
            "status": {
                "quest_status": "failed",
                "reason": "quest_exists_with_non_resumable_state",
                "active_run_id": None,
                "auto_runtime_parked": {
                    "parked": True,
                    "parked_state": "explicit_resume_pending",
                    "awaiting_explicit_wakeup": True,
                    "auto_execution_complete": False,
                    "source_reason": "quest_exists_with_non_resumable_state",
                    "source_decision": "blocked",
                    "source_quest_status": "failed",
                    "runtime_failure_classification": {
                        "auto_recovery_allowed": True,
                        "external_blocker": False,
                        "requires_human_gate": False,
                    },
                },
                "runtime_health_snapshot": {
                    "retry_budget_remaining": 0,
                    "attempt_state": "escalated",
                    "canonical_runtime_action": "external_supervisor_required",
                    "observed_quest_state": {
                        "quest_status": "failed",
                        "decision": "blocked",
                        "reason": "quest_exists_with_non_resumable_state",
                    },
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "continuation_state": {
                    "quest_status": "failed",
                    "active_run_id": None,
                    "continuation_policy": "auto",
                },
            },
            "action_queue": [
                {
                    **action,
                    "owner": "external_supervisor",
                    "authority": "external_supervisor",
                    "reason": "failed_quest_runtime_relaunch_required",
                    "owner_route": {
                        **owner_route,
                        "next_owner": "external_supervisor",
                        "owner_reason": "failed_quest_runtime_relaunch_required",
                    },
                }
            ],
            "owner_route": {
                **owner_route,
                "next_owner": "external_supervisor",
                "owner_reason": "failed_quest_runtime_relaunch_required",
            },
            "expected_reason": "failed_quest_runtime_relaunch_required",
            "expected_action": "safe_reconcile_ready",
        },
    }

    for case in cases.values():
        intent = ledger.project_recovery_intent(
            study_id="study",
            quest_id="quest",
            study_root=study_root,
            status=case.get("status", status),
            progress={},
            owner_route=case.get("owner_route", owner_route),
            action_queue=case.get("action_queue", [action]),
            generated_at="2026-05-08T00:00:00+00:00",
            persist=False,
        )

        assert intent["reason"] == case["expected_reason"]
        assert intent["current_action"] == case["expected_action"]
        if case["expected_action"] == "safe_reconcile_ready":
            assert intent["last_result"] is None
        else:
            assert intent["last_result"]["dispatch_status"] == "blocked"
        assert intent["quality_ready_authorized"] is False
        assert intent["publication_ready_authorized"] is False
        assert intent["submission_ready_authorized"] is False
    assert not (study_root / "artifacts").exists()


def test_recovery_intent_projection_is_non_persistent_when_scan_is_projection_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            }
        ]
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "work_unit_fingerprint": "publication-blockers::current",
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
        },
    )
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            _base_status(study_root=study_root, quest_root=quest_root, quest_id=quest_id),
            _base_progress(study_id=study_id, quest_id=quest_id),
            quest_id,
            publication_eval,
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    assert result["studies"][0]["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert not (study_root / "artifacts" / "runtime" / "recovery_intent" / "latest.json").exists()
