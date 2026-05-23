from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_gate_specificity_as_controller_lane(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-02T12:08:13+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": (
                    "medical publication surface is blocked; route back to `analysis-campaign` "
                    "to close claim-evidence consistency gaps."
                ),
            },
            "gaps": [
                {
                    "gap_id": "gap-005",
                    "gap_type": "claim",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                    "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Gate only named generic blocker labels.",
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "publication-blockers::specificity",
                    "next_work_unit": {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": (
                            "Ask the publication gate to identify concrete claim, display, evidence, "
                            "citation, metric, or package-artifact targets."
                        ),
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "gate_needs_specificity",
                            "lane": "controller",
                            "summary": "Ask the publication gate to identify concrete blocker targets.",
                        }
                    ],
                }
            ],
        },
    )
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "decision": "blocked",
            "reason": "needs_specificity",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "publication gate needs concrete blocker objects before dispatch.",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["intervention_lane"]["lane_id"] == "publication_gate_specificity_required"
    assert result["intervention_lane"]["recommended_action_id"] == "request_gate_specificity"
    assert result["intervention_lane"]["route_target"] == "controller"
    assert result["intervention_lane"]["work_unit_id"] == "gate_needs_specificity"
    assert result["intervention_lane"].get("route_target") != "analysis-campaign"
    assert result["operator_status_card"]["handling_state"] == "publication_gate_specificity_required"
    assert "普通分析" in result["operator_status_card"]["user_visible_verdict"]
    assert "claim/figure/table/metric/source path" in result["operator_status_card"]["next_confirmation_signal"]
    assert "current_package_freshness/latest.json" in result["operator_status_card"]["next_confirmation_signal"]


def test_gate_specificity_supersedes_older_task_intake_route_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "schema_version": 1,
            "task_id": "study-task::002-risk::20260427T020548Z",
            "emitted_at": "2026-04-27T02:05:48+00:00",
            "study_id": "002-risk",
            "entry_mode": "full_research",
            "task_intent": "Reactivate the same paper line for reviewer_revision.",
            "first_cycle_outputs": [
                "paper/rebuttal/review_matrix.md and action_plan.md covering all feedback items.",
            ],
            "revision_intake": {"kind": "reviewer_revision", "status": "active"},
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-02T12:22:47+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "Gate still names generic publication blockers without concrete targets.",
            },
            "gaps": [
                {
                    "gap_id": "gap-005",
                    "gap_type": "claim",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Gate only named generic blocker labels.",
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "publication-blockers::specificity",
                    "next_work_unit": {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": "Ask the publication gate to identify concrete blocker targets.",
                    },
                }
            ],
        },
    )
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "paused",
            "decision": "blocked",
            "reason": "needs_specificity",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["task_intake"]["task_id"] == "study-task::002-risk::20260427T020548Z"
    assert result["intervention_lane"]["lane_id"] == "publication_gate_specificity_required"
    assert result["intervention_lane"]["route_target"] == "controller"
    assert result["operator_verdict"]["lane_id"] == "publication_gate_specificity_required"
    assert result["same_line_route_truth"] is None
    assert "analysis-campaign" not in result["next_system_action"]


def test_gate_specificity_takes_priority_over_live_activity_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-02T12:22:47+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "Gate still names generic publication blockers without concrete targets.",
            },
            "gaps": [
                {
                    "gap_id": "gap-005",
                    "gap_type": "claim",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Gate only named generic blocker labels.",
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "publication-blockers::specificity",
                    "next_work_unit": {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": "Ask the publication gate to identify concrete blocker targets.",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-stale",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-stale",
                    "worker_running": True,
                },
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_status": "running",
                "active_run_id": "run-live-stale",
                "browser_url": "http://127.0.0.1:20999",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-live-stale",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": False,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-live-stale",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T10:40:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 10, 40, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["progress_freshness"]["activity_timeout"]["state"] == "timed_out"
    assert result["intervention_lane"]["lane_id"] == "publication_gate_specificity_required"
    assert result["operator_status_card"]["handling_state"] == "publication_gate_specificity_required"
    assert result["operator_verdict"]["lane_id"] == "publication_gate_specificity_required"
    assert "ordinary runtime recovery" not in result["operator_status_card"]["current_focus"]
    assert "claim/figure/table/metric/source path" in result["operator_status_card"]["next_confirmation_signal"]


def test_study_progress_reads_gate_specificity_request_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_gate_specificity"
        / "latest.json"
    )
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": "publication_gate_specificity_required::002-risk::quest-002",
            "request_kind": "publication_gate_specificity_required",
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "authority": "observability_only",
            "request_owner": "controller",
            "gate_owner": "publication_gate",
            "requested_target_types": ["claim", "figure", "table", "metric", "source_path"],
            "missing_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
            "requested_targets": [],
            "owner_visible_checklist": [
                {
                    "check_id": "name_claim_target",
                    "owner": "publication_gate",
                    "status": "missing",
                    "target_kind": "claim",
                    "requirement": "Name at least one concrete claim target.",
                }
            ],
            "next_controller_write": {
                "surface": "publication_eval/latest.json",
                "writer": "publication_gate_controller",
                "materialization_mode": "controller_request_only",
                "must_include_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
            },
            "quality_gate_relaxation_allowed": False,
            "paper_package_mutation_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::specificity",
                    "action_type": "return_to_controller",
                    "next_work_unit": {"unit_id": "gate_needs_specificity"},
                }
            ],
        },
    )
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    request_projection = result["publication_gate_specificity_request"]
    assert request_projection["authority"] == "observability_only"
    assert request_projection["request_owner"] == "controller"
    assert request_projection["gate_owner"] == "publication_gate"
    assert request_projection["missing_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert request_projection["owner_visible_checklist"][0]["target_kind"] == "claim"
    assert request_projection["next_controller_write"]["writer"] == "publication_gate_controller"
    assert request_projection["paper_package_mutation_allowed"] is False
    assert request_projection["medical_claim_authoring_allowed"] is False
    assert result["refs"]["publication_gate_specificity_request_path"] == str(request_path)


def test_study_progress_suppresses_stale_gate_specificity_request_after_targets_resolve(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_gate_specificity"
        / "latest.json"
    )
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": "publication_gate_specificity_required::002-risk::quest-002",
            "request_kind": "publication_gate_specificity_required",
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "authority": "observability_only",
            "request_owner": "controller",
            "gate_owner": "publication_gate",
            "requested_target_types": ["claim", "figure", "table", "metric", "source_path"],
            "missing_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
            "owner_visible_checklist": [{"target_kind": "claim", "status": "missing"}],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::specificity-resolved",
                    "action_type": "return_to_controller",
                    "specificity_targets": [
                        {
                            "target_kind": "claim",
                            "target_id": "claim_evidence_map",
                            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                            "blocking_reason": "claim_evidence_consistency_failed",
                        },
                        {
                            "target_kind": "figure",
                            "target_id": "figure_catalog",
                            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                            "blocking_reason": "medical_publication_surface_blocked",
                        },
                        {
                            "target_kind": "table",
                            "target_id": "submission_minimal_authority",
                            "source_path": str(
                                study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                            ),
                            "blocking_reason": "submission_hardening_incomplete",
                        },
                        {
                            "target_kind": "metric",
                            "target_id": "main_result_metrics",
                            "source_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
                            "blocking_reason": "medical_publication_surface_blocked",
                        },
                        {
                            "target_kind": "source_path",
                            "target_id": "publication_gate_source_path",
                            "source_path": str(
                                quest_root
                                / "artifacts"
                                / "reports"
                                / "medical_publication_surface"
                                / "latest.json"
                            ),
                            "blocking_reason": "medical_publication_surface_blocked",
                        },
                    ],
                }
            ],
        },
    )
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["publication_gate_specificity_request"] is None
    assert result["refs"]["publication_gate_specificity_request_path"] is None


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
