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


def test_scan_domain_routes_projects_single_owner_route_for_current_queue(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
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
        module.domain_status_projection,
        "progress_projection",
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
                "runtime_health_epoch": "runtime-health-epoch-dm002",
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    route = study["owner_route"]
    assert route == result["action_queue"][0]["owner_route"]
    assert route["schema_version"] == 2
    assert route["truth_epoch"] == "truth-epoch-dm002"
    assert route["runtime_health_epoch"] == "runtime-health-epoch-dm002"
    assert route["work_unit_fingerprint"] == "publication-blockers::route"
    assert route["failure_signature"] == "ai_reviewer_assessment_required"
    assert route["trace_id"].startswith("owner-route-trace::002-dm-china-us-mortality-attribution::")
    assert route["route_epoch"] == "truth-epoch-dm002"
    assert route["source_fingerprint"] == "truth-source-dm002"
    assert route["current_owner"] == "managed_runtime"
    assert route["next_owner"] == "ai_reviewer"
    assert route["owner_reason"] == "ai_reviewer_assessment_required"
    assert route["active_run_id"] == "run-dm002"
    assert route["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert route["blocked_actions"] == [
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
        "run_gate_clearing_batch",
    ]
    assert route["idempotency_key"].startswith(
        "owner-route::002-dm-china-us-mortality-attribution::truth-epoch-dm002::ai_reviewer::"
    )
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["external_supervisor_required"] is False


def test_owner_route_allows_quality_repair_batch_for_write_route() -> None:
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": "truth-epoch-dm003-medical-prose",
        "runtime_health_epoch": "runtime-health-dm003-medical-prose",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "trace_id": "owner-route-trace::dm003::medical-prose",
        "route_epoch": "truth-epoch-dm003-medical-prose",
        "source_fingerprint": "truth-source-dm003-medical-prose",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm003::medical-prose",
    }
    action = {
        "action_type": "run_quality_repair_batch",
        "next_executable_owner": "write",
        "owner_route": owner_route,
    }

    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    assert owner_route_module.route_allows_action(action=action, owner_route=owner_route) is True


def test_owner_route_registers_domain_transition_publication_gate_blocker() -> None:
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "truth_epoch": "truth-epoch-dm003-publication-gate",
        "runtime_health_epoch": "runtime-health-dm003-publication-gate",
        "work_unit_fingerprint": "domain-transition::publication_gate_blocker::publication_gate_replay",
        "failure_signature": "domain_transition_publication_gate_blocker",
        "trace_id": "owner-route-trace::dm003::publication-gate",
        "route_epoch": "truth-epoch-dm003-publication-gate",
        "source_fingerprint": "truth-source-dm003-publication-gate",
        "current_owner": "mas_controller",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "domain_transition_publication_gate_blocker",
        "active_run_id": None,
        "allowed_actions": ["run_gate_clearing_batch"],
        "blocked_actions": [],
        "source_refs": {"work_unit_id": "publication_gate_replay"},
        "idempotency_key": "owner-route::dm003::publication-gate",
    }
    protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")

    decorated = protocol.decorate_owner_route(owner_route)

    assert decorated["allowed_actions"] == ["run_gate_clearing_batch"]
    assert decorated["owner_reason_contract"]["registered"] is True
    assert decorated["owner_reason_contract"]["owner"] == "gate_clearing_batch"
    assert decorated["owner_reason_contract"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert decorated["owner_route_attempt_protocol"]["dispatchable"] is True


def test_scan_domain_routes_projects_parked_macro_state_as_current_truth_owner_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    cases = {
        "001-submit-info": {
            "reason": "quest_waiting_for_submission_metadata",
            "quality_state": {},
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "external_metadata_pending",
                "auto_execution_complete": True,
            },
            "expected_reason": "external_info",
            "expected_user_next": "submit_info",
        },
        "002-stop-loss": {
            "reason": "publishability_stop_loss_recommended",
            "quality_state": {"state": "stop_loss_recommended"},
            "auto_runtime_parked": {"parked": False, "auto_execution_complete": False},
            "expected_reason": "stop_loss",
            "expected_user_next": "none",
        },
        "003-user-stop": {
            "reason": "manual_stop",
            "quality_state": {"state": "user_stopped"},
            "auto_runtime_parked": {"parked": False, "auto_execution_complete": False},
            "expected_reason": "user_stop",
            "expected_user_next": "none",
        },
    }
    statuses: dict[str, dict] = {}
    progresses: dict[str, dict] = {}
    quest_ids: dict[str, str] = {}
    publication_evals: dict[str, dict] = {}
    for study_id, case in cases.items():
        quest_id = f"quest-{study_id}"
        study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
        quest_root = profile.runtime_root / quest_id
        publication_eval = {
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            "recommended_actions": [],
        }
        statuses[study_id] = {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_status": "paused",
            "decision": "resume",
            "reason": case["reason"],
            "active_run_id": None,
            "auto_runtime_parked": case["auto_runtime_parked"],
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": f"truth-epoch-{study_id}",
                "source_signature": f"truth-source-{study_id}",
                "quality_state": case["quality_state"],
            },
        }
        progresses[study_id] = {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "bundle_stage_blocked",
            "auto_runtime_parked": case["auto_runtime_parked"],
            "supervision": {"active_run_id": None, "health_status": "escalated"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
            },
        }
        quest_ids[study_id] = quest_id
        publication_evals[study_id] = publication_eval

    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda *, study_id, **_: (
            statuses[study_id],
            progresses[study_id],
            quest_ids[study_id],
            publication_evals[study_id],
        ),
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=tuple(cases),
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    for study in result["studies"]:
        case = cases[study["study_id"]]
        macro_source = study["owner_route"]["source_refs"]["study_macro_state"]
        assert macro_source["writer_state"] == "parked"
        assert macro_source["user_next"] == case["expected_user_next"]
        assert macro_source["reason"] == case["expected_reason"]
        assert macro_source["source_fingerprint"].startswith("study-macro-state::")
        assert study["action_queue"] == []
        assert study["ai_repair_lifecycle"] is None
        assert study["why_not_applied"] is None
        assert study["blocked_reason"] is None
        assert study["next_owner"] is None
        assert study["external_supervisor_required"] is False
        assert study["owner_route"]["current_owner"] == "controller_stop"
        assert study["owner_route"]["next_owner"] is None
        assert study["owner_route"]["owner_reason"] is None


def test_scan_domain_routes_suppresses_repeated_owner_route_without_meaningful_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::repeat",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::repeat",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::repeat",
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }
    previous_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "truth_epoch": "truth-epoch-dm002-repeat",
        "runtime_health_epoch": "runtime-health-epoch-dm002-repeat",
        "work_unit_fingerprint": "publication-blockers::repeat",
        "failure_signature": "ai_reviewer_assessment_required",
        "trace_id": "owner-route-trace::previous",
        "route_epoch": "truth-epoch-dm002-repeat",
        "source_fingerprint": "truth-source-dm002-repeat",
        "current_owner": "managed_runtime",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_assessment_required",
        "active_run_id": "run-dm002",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": [],
        "idempotency_key": "owner-route::previous",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": previous_route, "meaningful_artifact_delta": False}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": previous_route,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
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
                "runtime_health_epoch": "runtime-health-epoch-dm002-repeat",
                "canonical_runtime_action": "observe_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002-repeat",
                "source_signature": "truth-source-dm002-repeat",
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in result["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["repeat_suppression"]["repeat_suppressed"] is False
    assert study["repeat_suppression"]["why_not_applied"] is None
    assert study["repeat_suppression"]["work_unit_fingerprint"] == "publication-blockers::repeat"
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"


def test_materialize_domain_action_requests_preserves_owner_route_in_dispatch(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
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
        "blocked_actions": ["publication_gate_specificity_required"],
        "idempotency_key": "owner-route::dm002::truth-epoch-dm002::ai_reviewer::ai_reviewer_assessment_required::abc123",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
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

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    packet = result["request_tasks"][0]["handoff_packet"]
    assert dispatch["owner_route"]["schema_version"] == 2
    assert dispatch["owner_route"]["truth_epoch"] == owner_route["route_epoch"]
    assert dispatch["owner_route"]["work_unit_fingerprint"] == owner_route["source_fingerprint"]
    assert dispatch["prompt_contract"]["owner_route"] == dispatch["owner_route"]
    assert dispatch["prompt_contract"]["idempotency_key"] == owner_route["idempotency_key"]
    assert dispatch["required_closeout_packet"]["typed_closeout_required_for_completion"] is True
    assert dispatch["required_closeout_packet"]["free_text_closeout_accepted"] is False
    assert dispatch["required_closeout_packet"]["required_user_stage_log_field"] == "paper_stage_log"
    assert "paper_work_done" in dispatch["required_closeout_packet"]["required_user_stage_log_fields"]
    assert dispatch["prompt_contract"]["required_closeout_packet"] == dispatch["required_closeout_packet"]
    assert "exactly one JSON object" in dispatch["executor_prompt"]
    assert "paper_stage_log" in dispatch["executor_prompt"]
    assert packet["owner_route"]["schema_version"] == 2
    assert packet["owner_route"]["truth_epoch"] == owner_route["route_epoch"]
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
    assert persisted["owner_route"] == dispatch["owner_route"]


def test_execute_dispatch_blocks_stale_owner_route(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
        "blocked_actions": ["publication_gate_specificity_required"],
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
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/return_to_ai_reviewer_workflow.json",
            "do_not_repeat": True,
            "repeat_suppression_key": "truth-source-old",
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "src/med_autoscience/runtime_transport/**",
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
            "surface": "domain_action_request_materializer",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [dispatch],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
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

    result = module.dispatch_domain_owner_actions(
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
    module = importlib.import_module("med_autoscience.runtime_control.owner_route")
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


def test_owner_route_requires_explicit_allowed_action_for_dispatch_execution() -> None:
    module = importlib.import_module("med_autoscience.runtime_control.owner_route")
    action = {
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_assessment_required",
    }
    route = {
        "next_owner": "ai_reviewer",
        "owner_reason": "return_to_ai_reviewer_workflow",
        "allowed_actions": [],
    }

    assert module.route_allows_action(action=action, owner_route=route) is False
    assert module.route_allows_action(
        action=action,
        owner_route={**route, "allowed_actions": ["return_to_ai_reviewer_workflow"]},
    ) is True


def test_owner_route_legacy_scan_part_reexports_shared_contract() -> None:
    shared = importlib.import_module("med_autoscience.runtime_control.owner_route")
    legacy = importlib.import_module("med_autoscience.controllers.owner_route_reconcile_parts.owner_route")

    assert legacy.ROUTED_ACTION_TYPES is shared.ROUTED_ACTION_TYPES
    assert legacy.build_owner_route is shared.build_owner_route
    assert legacy.decorate_actions is shared.decorate_actions
    assert legacy.route_and_decorate_actions is shared.route_and_decorate_actions
    assert legacy.owner_route_matches is shared.owner_route_matches
    assert legacy.route_allows_action is shared.route_allows_action


def test_owner_route_scan_consumer_and_executor_share_contract_import() -> None:
    shared = importlib.import_module("med_autoscience.runtime_control.owner_route")
    modules = [
        importlib.import_module("med_autoscience.controllers.owner_route_reconcile"),
        importlib.import_module("med_autoscience.controllers.domain_action_request_materializer"),
        importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch"),
    ]

    for module in modules:
        assert module.owner_route_part.build_owner_route is shared.build_owner_route
        assert module.owner_route_part.owner_route_matches is shared.owner_route_matches
        assert module.owner_route_part.route_allows_action is shared.route_allows_action


def test_scan_domain_routes_routes_incomplete_completion_contract_to_completion_evidence_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
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
                "quest_root": str(profile.managed_runtime_home / "quests" / "quest-002"),
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

    result = scan.scan_domain_routes(
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


def test_scan_domain_routes_completed_truth_suppresses_stale_repair_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
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
                "quest_root": str(profile.managed_runtime_home / "quests" / "quest-002"),
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

    result = scan.scan_domain_routes(
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
