from __future__ import annotations

from . import shared as _shared
from . import runtime_projection_basics as _runtime_projection_basics
from . import autonomy_quality_and_route_projection as _autonomy_quality_and_route_projection

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_runtime_projection_basics)
_module_reexport(_autonomy_quality_and_route_projection)

def test_study_progress_drops_stale_submission_authority_blocker_after_controller_closure(
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
    source_eval_id = "publication-eval::002-risk::quest-002::2026-05-13T04:00:00+00:00"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": source_eval_id,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-13T04:00:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "bundle-stage blockers are now on the critical path for this paper line",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                }
            ],
            "recommended_actions": [],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "status": "done",
            "work_unit": {"unit_id": "submission_authority_sync_closure", "lane": "controller"},
            "unit_statuses": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "settled_by_current_gate"},
            ],
            "gate_replay_status": "clear",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "status": "fresh",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-002",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": True,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-002",
                "continuation_policy": "auto",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert "stale_submission_minimal_authority" not in result["current_blockers"]
    assert not any("投稿包" in item for item in result["current_blockers"])


def test_study_progress_filters_cached_projection_after_controller_closure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")
    source_eval_id = "publication-eval::002-risk::quest-002::2026-05-13T04:00:00+00:00"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": source_eval_id,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "verdict": {"overall_verdict": "blocked"},
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "status": "done",
            "work_unit": {"unit_id": "submission_authority_sync_closure", "lane": "controller"},
            "unit_statuses": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "settled_by_current_gate"},
            ],
            "gate_replay_status": "clear",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "status": "fresh",
        },
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="002-risk",
        study_root=study_root,
        status_payload={
            "study_id": "002-risk",
            "publication_supervisor_state": {},
            "progress_projection": {
                "schema_version": 1,
                "study_id": "002-risk",
                "current_stage": "publication_supervision",
                "current_blockers": [
                    "stale_submission_minimal_authority",
                    "仍需人工复核主文叙事。",
                ],
                "user_visible_projection": {
                    "current_blockers": [
                        "stale_submission_minimal_authority",
                        "仍需人工复核主文叙事。",
                    ],
                },
                "status_narration_contract": {
                    "current_blockers": [
                        "stale_submission_minimal_authority",
                        "仍需人工复核主文叙事。",
                    ],
                },
            },
        },
    )

    assert result["current_blockers"] == ["仍需人工复核主文叙事。"]
    assert result["user_visible_projection"]["current_blockers"] == ["仍需人工复核主文叙事。"]
    assert result["status_narration_contract"]["current_blockers"] == ["仍需人工复核主文叙事。"]


def test_study_progress_refreshes_publication_eval_from_newer_gate_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-12T09:30:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "Objective text",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"),
                "submission_minimal_ref": str(
                    quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "旧的外层结论还停在投稿包镜像过期。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(quest_root)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::2026-04-12T09:30:00+00:00",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "旧 blocker 仍未清掉。",
                    "evidence_refs": [str(quest_root)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    gate_report_path = _write_publishability_gate_report(quest_root)
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    gate_report.update(
        {
            "generated_at": "2026-04-12T09:40:00+00:00",
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["reviewer_first_concerns_unresolved"],
            "medical_publication_surface_route_back_recommendation": "return_to_write",
            "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
        }
    )
    _write_json(gate_report_path, gate_report)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    refreshed_publication_eval = json.loads(
        (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8")
    )

    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:40:00+00:00"
    assert refreshed_publication_eval["gaps"][0]["summary"] == "medical_publication_surface_blocked"
    assert refreshed_publication_eval["recommended_actions"][0]["action_type"] == "return_to_controller"
    assert refreshed_publication_eval["recommended_actions"][0]["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。" not in result["current_blockers"]
    assert "论文叙事或方法/结果书写面仍有硬阻塞。" in result["current_blockers"]
    assert result["operator_status_card"]["handling_state"] == "publication_gate_specificity_required"
    assert "普通分析" in result["operator_status_card"]["user_visible_verdict"]
    assert result["module_surfaces"]["eval_hygiene"]["overall_verdict"] == "blocked"
    assert result["module_surfaces"]["eval_hygiene"]["status_summary"] == "稿件书写面还有医学论文表达硬阻塞，需要继续修文。"
    assert result["intervention_lane"]["repair_mode"] == "gate_needs_specificity"
    assert result["intervention_lane"]["route_target"] == "controller"
    assert result["intervention_lane"]["work_unit_id"] == "gate_needs_specificity"
    assert "没有具体对象前不再启动普通分析或写作 worker" in result["next_system_action"]


def test_study_progress_refreshes_semantically_stale_publication_eval_even_when_eval_is_newer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    stale_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    stale_eval.update(
        {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-12T09:45:00+00:00",
            "emitted_at": "2026-04-12T09:45:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "bundle suggestions are downstream-only until the publication gate allows write",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(quest_root)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::2026-04-12T09:45:00+00:00",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "旧 blocker 仍未清掉。",
                    "evidence_refs": [str(quest_root)],
                    "requires_controller_decision": True,
                }
            ],
        }
    )
    _write_json(publication_eval_path, stale_eval)
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    gate_report_path = _write_publishability_gate_report(quest_root)
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    gate_report.update(
        {
            "generated_at": "2026-04-12T09:40:00+00:00",
            "status": "clear",
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "blockers": [],
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        }
    )
    _write_json(gate_report_path, gate_report)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "旧的 publication_eval 仍把纸面镜像错判成过期。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    module.read_study_progress(profile=profile, study_id="001-risk")
    refreshed_publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))

    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:40:00+00:00"
    assert refreshed_publication_eval["verdict"]["overall_verdict"] == "promising"
    assert all(gap["severity"] == "optional" for gap in refreshed_publication_eval["gaps"])
    assert "stale_study_delivery_mirror" not in {
        gap["summary"] for gap in refreshed_publication_eval["gaps"]
    }

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
