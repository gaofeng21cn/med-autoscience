from __future__ import annotations

from .shared import *


def test_scan_domain_routes_isolates_retired_manual_finish_contract_from_other_studies(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    bad_study_root = write_study(profile.workspace_root, "001-retired", quest_id="quest-retired")
    good_study_root = write_study(profile.workspace_root, "002-live", quest_id="quest-live")

    def fake_projection_inputs(*, study_id: str, **_: object) -> tuple[dict[str, object], dict[str, object], str | None, dict[str, object]]:
        if study_id == "001-retired":
            raise ValueError("manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only")
        return (
            {
                "study_id": study_id,
                "study_root": str(good_study_root),
                "quest_id": "quest-live",
                "quest_root": str(profile.runtime_root / "quest-live"),
                "quest_status": "running",
                "active_run_id": "mas-run-002-live",
                "runtime_liveness_audit": {
                    "worker_running": True,
                    "active_run_id": "mas-run-002-live",
                    "runtime_audit": {
                        "worker_running": True,
                        "active_run_id": "mas-run-002-live",
                    },
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                    "worker_liveness_state": {
                        "state": "live",
                        "worker_running": True,
                        "active_run_id": "mas-run-002-live",
                    },
                    "active_run_id": "mas-run-002-live",
                },
                "execution_owner_guard": {"supervisor_only": True},
                "publication_eval": {},
            },
            {
                "study_id": study_id,
                "study_root": str(good_study_root),
                "quest_id": "quest-live",
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {},
            },
            "quest-live",
            {},
        )

    monkeypatch.setattr(module, "_read_study_projection_inputs", fake_projection_inputs)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-retired", "002-live"),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    studies = {study["study_id"]: study for study in result["studies"]}
    assert studies["001-retired"]["why_not_applied"] == "study_projection_contract_error"
    assert studies["001-retired"]["blocked_reason"] == "study_projection_contract_error"
    assert studies["001-retired"]["projection_error"]["message"] == (
        "manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only"
    )
    assert studies["001-retired"]["action_queue"] == []
    assert studies["002-live"]["active_run_id"] == "mas-run-002-live"
    assert studies["002-live"]["runtime_health"]["worker_liveness_state"]["worker_running"] is True


def test_scan_domain_routes_queues_specificity_and_ai_reviewer_actions_without_quality_authority(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publication_gate_specificity_required",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "none",
                "attempt_state": "idle",
                "retry_budget_remaining": 0,
            },
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "current_required_action": "generic_blocker_repair",
                "assessment_provenance": {"owner": "mechanical_gate"},
                "blockers": ["generic blocker"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "current_blockers": ["generic blocker"],
            "quality_review_loop": {"closure_state": "open"},
            "authority_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    action_types = [item["action_type"] for item in result["studies"][0]["action_queue"]]
    assert action_types == ["publication_gate_specificity_required"]
    assert {item["authority"] for item in result["studies"][0]["action_queue"]} == {"observability_only"}
    assert [item["owner"] for item in result["studies"][0]["action_queue"]] == ["publication_gate"]
    assert [item["recommended_owner"] for item in result["studies"][0]["action_queue"]] == ["publication_gate"]
    assert [item["owner_pickup"]["owner"] for item in result["studies"][0]["action_queue"]] == ["publication_gate"]
    assert result["studies"][0]["current_stage"] == "publication_supervision"
    assert result["studies"][0]["gate_specificity"]["required"] is True
    assert result["studies"][0]["gate_specificity"]["missing_target_kinds"] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert result["studies"][0]["gate_specificity"]["gate_owner"] == "publication_gate"
    assert result["studies"][0]["gate_specificity"]["next_controller_write"] == {
        "surface": "publication_eval/latest.json",
        "writer": "publication_gate_controller",
        "materialization_mode": "controller_request_only",
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
    }
    assert result["studies"][0]["ai_reviewer_assessment"] == {
        "present": False,
        "owner": "mechanical_gate",
        "required": True,
        "missing": True,
    }
    assert result["studies"][0]["why_not_applied"] == "publication_gate_specificity_required"
    assert result["studies"][0]["blocked_reason"] == "publication_gate_specificity_required"
    assert result["studies"][0]["next_owner"] == "publication_gate"
    assert result["studies"][0]["supervisor_only"] is True
    assert result["studies"][0]["paper_package_mutated"] is False
    for action in result["studies"][0]["action_queue"]:
        assert action["authority"] == "observability_only"
        assert action["quality_gate_relaxation_allowed"] is False
        assert action["paper_package_mutation_allowed"] is False
        assert action["manual_study_patch_allowed"] is False
        assert action["medical_claim_authoring_allowed"] is False
        assert action["handoff_packet"]["authority"] == "observability_only"
        assert action["handoff_packet"]["request_owner"] == action["owner"]
        assert action["handoff_packet"]["recommended_owner"] == action["owner"]
        assert action["handoff_packet"]["next_executable_owner"] == action["owner"]
        assert action["handoff_packet"]["supervisor_authority_boundary"] == "request_only"
        assert action["handoff_packet"]["quality_gate_relaxation_allowed"] is False
        assert action["handoff_packet"]["paper_package_mutation_allowed"] is False
        assert action["handoff_packet"]["manual_study_patch_allowed"] is False
        assert action["handoff_packet"]["medical_claim_authoring_allowed"] is False
        assert action["handoff_packet"]["allowed_write_surfaces"] == ["artifacts/supervision/**"]


def test_scan_domain_routes_marks_ai_reviewer_eval_stale_after_new_reviewer_revision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::old",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "emitted_at": "2026-05-19T12:00:00+00:00",
        "assessment_provenance": {"owner": "ai_reviewer"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "verdict": {"overall_verdict": "blocked"},
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "schema_version": 1,
            "task_id": "study-task::dm002::20260520T083325Z",
            "emitted_at": "2026-05-20T08:33:25+00:00",
            "study_id": study_id,
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "task_intake_kind": "reviewer_revision",
            "task_intent": "按最新专家反馈重新评估医学论文质量，补 CI、校准曲线、模型复现和正式图注。",
        },
    )

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": "quest-dm002",
                "quest_status": "stopped",
                "decision": "blocked",
                "reason": "publication_gate_blocked",
                "execution_owner_guard": {"supervisor_only": True},
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "none",
                    "attempt_state": "idle",
                    "retry_budget_remaining": 0,
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": "quest-dm002",
                "current_stage": "publication_supervision",
                "paper_stage": "publishability_gate_blocked",
                "quality_review_loop": {"closure_state": "review_required"},
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            "quest-dm002",
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"] == {
        "present": False,
        "owner": "ai_reviewer",
        "required": True,
        "missing": True,
        "blocked_reason": "ai_reviewer_assessment_stale_after_reviewer_revision",
        "task_id": "study-task::dm002::20260520T083325Z",
        "task_emitted_at": "2026-05-20T08:33:25+00:00",
        "publication_eval_emitted_at": "2026-05-19T12:00:00+00:00",
    }
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["action_queue"][0]["authority"] == "observability_only"
    assert study["action_queue"][0]["owner"] == "ai_reviewer"
    assert study["action_queue"][0]["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_apply_safe_actions_materializes_stopped_dm002_lifecycle_and_request_packets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "bounded_work_unit_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::specificity",
                        "action_type": "return_to_controller",
                        "next_work_unit": {"unit_id": "gate_needs_specificity", "summary": "Name concrete targets."},
                        "work_unit_fingerprint": "publication-blockers::same",
                        "reason": "Publication gate needs specificity.",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
            "quality_review_loop": {"closure_state": "review_required"},
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    specificity_request_path = study_root / "artifacts" / "supervision" / "requests" / "publication_gate_specificity" / "latest.json"
    ai_reviewer_request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    specificity_request = json.loads(specificity_request_path.read_text(encoding="utf-8"))
    assert not ai_reviewer_request_path.exists()

    assert result["studies"][0]["ai_repair_lifecycle"]["blocked_reason"] == "publication_gate_specificity_required"
    assert result["studies"][0]["next_owner"] == "publication_gate"
    assert lifecycle["state"] == "blocked"
    assert lifecycle["blocked_reason"] == "publication_gate_specificity_required"
    assert lifecycle["next_owner"] == "publication_gate"
    assert specificity_request["authority"] == "observability_only"
    assert specificity_request["required_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert specificity_request["missing_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert specificity_request["gate_owner"] == "publication_gate"
    assert specificity_request["request_visibility"] == "owner_visible_checklist"
    assert [item["target_kind"] for item in specificity_request["owner_visible_checklist"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert specificity_request["next_controller_write"]["surface"] == "publication_eval/latest.json"
    assert specificity_request["next_controller_write"]["writer"] == "publication_gate_controller"
    assert specificity_request["next_controller_write"]["must_include_target_kinds"] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]


def test_scan_domain_routes_uses_pull_request_route_when_github_user_is_not_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-dpcc-primary-care-phenotype-treatment-gap", quest_id="quest-dpcc")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "quest-dpcc",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "runtime_recovery_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_status": "running",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_stage": "publication_supervision",
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-dpcc-primary-care-phenotype-treatment-gap",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert result["developer_supervisor_mode"]["mode"] == "developer_apply_safe"
    assert result["developer_supervisor_mode"]["developer_mode_enabled"] is True
    assert result["developer_supervisor_mode"]["safe_actions_enabled"] is True
    assert result["developer_supervisor_mode"]["github_user_gate"] == {
        "expected_login": "gaofeng21cn",
        "login": "someone-else",
        "allowed": False,
        "source": "env",
        "reason": "github_user_requires_pull_request_route",
    }
    assert result["developer_supervisor_mode"]["repo_write_policy"]["route"] == "pull_request"
    assert result["developer_supervisor_mode"]["repo_write_policy"]["pull_request_required"] is True
    assert study["action_queue"] == []
    assert study["owner_route"]["next_owner"] == "one-person-lab"
    assert study["owner_route"]["owner_reason"] == "opl_stage_attempt_admission_required"
    assert study["owner_route"]["allowed_actions"] == []
    assert study["owner_route"]["owner_route_attempt_protocol"]["dispatchable"] is False
    assert study["why_not_applied"] == "opl_stage_attempt_admission_required"
    assert study["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert not (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").exists()


def test_scan_domain_routes_apply_safe_actions_sanitizes_unsafe_repair_authority(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-risk")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "002-risk",
            "quest_id": "quest-risk",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "bounded_work_unit_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                    "paper_package_mutation_allowed": True,
                    "manual_study_patch_allowed": True,
                    "quality_gate_relaxation_allowed": True,
                    "medical_claim_authoring_allowed": True,
                    "requested_write_surfaces": [
                        "paper/submission_minimal/**",
                        "artifacts/supervision/requests/ai_reviewer/latest.json",
                    ],
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "002-risk",
            "study_root": str(study_root),
            "quest_id": "quest-risk",
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::specificity",
                        "next_work_unit": {"unit_id": "gate_needs_specificity"},
                        "work_unit_fingerprint": "publication-blockers::specificity",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "002-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "authority_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("002-risk",),
        apply_safe_actions=True,
    )

    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    top_action = lifecycle["top_action"]
    assert result["studies"][0]["supervisor_only"] is True
    assert lifecycle["authority"] == "observability_only"
    assert lifecycle["allowed_write_surfaces"] == [
        "artifacts/supervision/**",
        "artifacts/autonomy/repair_lifecycle/latest.json",
        "artifacts/autonomy/repair_actions/latest.json",
    ]
    assert lifecycle["forbidden_actions"] == [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ]
    assert top_action["paper_package_mutation_allowed"] is False
    assert top_action["manual_study_patch_allowed"] is False
    assert top_action["quality_gate_relaxation_allowed"] is False
    assert top_action["medical_claim_authoring_allowed"] is False
    assert top_action["requested_write_surfaces"] == ["artifacts/supervision/**"]
