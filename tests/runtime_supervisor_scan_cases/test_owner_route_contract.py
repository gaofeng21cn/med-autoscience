from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _specificity_targets(study_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
    ]


def test_supervisor_scan_projects_single_owner_route_for_current_queue(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::current-route",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::route",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::route",
                "next_work_unit": {"unit_id": "publication_gate_blocker_review", "lane": "review"},
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "active_run_id": "run-dm002",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-dm002",
                "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-dm002"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "observe_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "authority_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
                "canonical_next_action": "supervise_runtime",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": "run-dm002", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    route = study["owner_route"]
    assert route == result["action_queue"][0]["owner_route"]
    assert route["route_epoch"] == "truth-epoch-dm002"
    assert route["source_fingerprint"] == "truth-source-dm002"
    assert route["current_owner"] == "managed_runtime"
    assert route["next_owner"] == "ai_reviewer"
    assert route["owner_reason"] == "ai_reviewer_assessment_required"
    assert route["active_run_id"] == "run-dm002"
    assert route["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert route["blocked_actions"] == [
        "runtime_platform_repair",
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
    ]
    assert route["idempotency_key"].startswith(
        "owner-route::002-dm-china-us-mortality-attribution::truth-epoch-dm002::ai_reviewer::"
    )
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["external_supervisor_required"] is False


def test_supervisor_consume_preserves_owner_route_in_dispatch(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    owner_route = {
        "route_epoch": "truth-epoch-dm002",
        "source_fingerprint": "truth-source-dm002",
        "current_owner": "managed_runtime",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_assessment_required",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": ["runtime_platform_repair", "publication_gate_specificity_required"],
        "idempotency_key": "owner-route::dm002::truth-epoch-dm002::ai_reviewer::ai_reviewer_assessment_required::abc123",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": owner_route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": owner_route,
                    },
                }
            ],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    packet = result["request_tasks"][0]["handoff_packet"]
    assert dispatch["owner_route"] == owner_route
    assert dispatch["prompt_contract"]["owner_route"] == owner_route
    assert dispatch["prompt_contract"]["idempotency_key"] == owner_route["idempotency_key"]
    assert packet["owner_route"] == owner_route
    assert packet["idempotency_key"] == owner_route["idempotency_key"]
    persisted = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    assert persisted["owner_route"] == owner_route


def test_execute_dispatch_blocks_stale_owner_route(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    owner_route = {
        "route_epoch": "truth-epoch-old",
        "source_fingerprint": "truth-source-old",
        "current_owner": "managed_runtime",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_assessment_required",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": ["runtime_platform_repair", "publication_gate_specificity_required"],
        "idempotency_key": "owner-route::dm002::truth-epoch-old::ai_reviewer::ai_reviewer_assessment_required::old",
    }
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "executor_name": "Codex CLI",
        "executor_mode": "autonomous_agent_loop",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "action_type": "return_to_ai_reviewer_workflow",
        "action_id": "dispatch::dm002::ai-reviewer",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "action_type": "return_to_ai_reviewer_workflow",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "owner_route": owner_route,
            "idempotency_key": owner_route["idempotency_key"],
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
            ],
            "allowed_write_surfaces": ["artifacts/supervision/**"],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }
    dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [dispatch],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": {
                        **owner_route,
                        "route_epoch": "truth-epoch-new",
                        "source_fingerprint": "truth-source-new",
                        "next_owner": "publication_gate",
                        "owner_reason": "publication_gate_specificity_required",
                        "allowed_actions": ["publication_gate_specificity_required"],
                        "idempotency_key": "owner-route::dm002::truth-epoch-new::publication_gate::publication_gate_specificity_required::new",
                    },
                }
            ],
        },
    )

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("stale owner route dispatch must not execute owner workflow")

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_if_called)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_stale"
    assert execution["owner_route_current"] is False
    assert execution["current_owner_route"]["route_epoch"] == "truth-epoch-new"


def test_owner_route_fallback_source_fingerprint_tracks_action_payload_targets() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan_parts.owner_route")
    base = {
        "action_type": "publication_gate_specificity_required",
        "owner": "publication_gate",
        "reason": "publication_gate_specificity_required",
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
    }
    common_kwargs = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "quest-dm002",
        "status": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "running",
            "reason": "publication_gate_specificity_required",
            "active_run_id": "run-dm002",
        },
        "progress": {
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
        },
        "blocked_reason": "publication_gate_specificity_required",
        "next_owner": "publication_gate",
        "active_run_id": "run-dm002",
    }

    claim_route = module.build_owner_route(
        **common_kwargs,
        actions=[{**base, "missing_target_kinds": ["claim"]}],
    )
    metric_route = module.build_owner_route(
        **common_kwargs,
        actions=[{**base, "missing_target_kinds": ["metric"]}],
    )

    assert claim_route["route_epoch"] == metric_route["route_epoch"]
    assert claim_route["source_fingerprint"] != metric_route["source_fingerprint"]
    assert claim_route["idempotency_key"] != metric_route["idempotency_key"]


def test_supervisor_scan_routes_incomplete_completion_contract_to_completion_evidence_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": "002-risk",
                "study_root": str(study_root),
                "quest_id": "quest-002",
                "quest_root": str(profile.med_deepscientist_runtime_root / "quests" / "quest-002"),
                "quest_status": "completed",
                "decision": "blocked",
                "reason": "study_completion_contract_not_ready",
                "study_completion_contract": {
                    "ready": False,
                    "status": "incomplete",
                    "completion_status": "completed",
                    "summary": "Study delivery declared complete.",
                    "missing_evidence_paths": ["manuscript/submission_package.zip"],
                },
            },
            {
                "study_id": "002-risk",
                "quest_id": "quest-002",
                "current_stage": "runtime_blocked",
                "intervention_lane": {
                    "lane_id": "completion_evidence_required",
                    "recommended_action_id": "sync_completion_evidence",
                },
                "current_blockers": ["study-level 完成声明已存在，但 final submission 证据还未补齐。"],
                "study_completion_contract": {
                    "ready": False,
                    "status": "incomplete",
                    "missing_evidence_paths": ["manuscript/submission_package.zip"],
                },
            },
            "quest-002",
            {},
        ),
    )

    result = scan.supervisor_scan(
        profile=profile,
        study_ids=["002-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["next_owner"] == "completion_evidence"
    assert study["blocked_reason"] == "study_completion_contract_not_ready"
    assert study["external_supervisor_required"] is False
    assert study["action_queue"] == []
    assert study["owner_route"]["next_owner"] == "completion_evidence"
    assert study["owner_route"]["owner_reason"] == "study_completion_contract_not_ready"


def test_supervisor_scan_completed_truth_suppresses_stale_repair_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": "002-risk",
                "study_root": str(study_root),
                "quest_id": "quest-002",
                "quest_root": str(profile.med_deepscientist_runtime_root / "quests" / "quest-002"),
                "quest_status": "completed",
                "decision": "completed",
                "reason": "quest_already_completed",
                "study_completion_contract": {
                    "ready": True,
                    "status": "resolved",
                    "completion_status": "completed",
                    "summary": "Study delivery declared complete.",
                    "missing_evidence_paths": [],
                },
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-completed",
                    "source_signature": "completion-source",
                },
            },
            {
                "study_id": "002-risk",
                "quest_id": "quest-002",
                "current_stage": "study_completed",
                "intervention_lane": {
                    "lane_id": "completed",
                    "recommended_action_id": "inspect_progress",
                },
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "blocked_reason": "runtime_recovery_not_authorized",
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                },
                "quality_review_loop": {
                    "closure_state": "quality_repair_required",
                },
            },
            "quest-002",
            {
                "assessment_provenance": {
                    "owner": "mechanical_projection",
                    "ai_reviewer_required": True,
                },
            },
        ),
    )

    result = scan.supervisor_scan(
        profile=profile,
        study_ids=["002-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["next_owner"] is None
    assert study["blocked_reason"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] is None
    assert study["owner_route"]["owner_reason"] is None


def test_supervisor_scan_routes_no_live_current_controller_work_unit_without_external_supervisor(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.med_deepscientist_runtime_root / "quests" / study_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::current",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": f"study-decision::{study_id}::bounded_analysis",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "publication-blockers::current",
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
            },
        },
    )
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "resume",
                "reason": "quest_marked_running_but_no_live_session",
                "active_run_id": None,
                "runtime_liveness_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-current-work-unit",
                    "source_signature": "truth-source-current-work-unit",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "managed_runtime_escalated",
                "paper_stage": "publishability_gate_blocked",
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "quality_review_loop": {"closure_state": "review_required"},
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                },
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = scan.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == [
        "runtime_platform_repair",
        "return_to_ai_reviewer_workflow",
    ]
    assert study["action_queue"][0]["authority"] == "observability_only"
    assert study["action_queue"][0]["owner"] == "mas_controller"
    assert study["action_queue"][0]["reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "mas_controller"
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["next_owner"] == "mas_controller"
    assert study["owner_route"]["owner_reason"] == "runtime_controller_redrive_required"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]
