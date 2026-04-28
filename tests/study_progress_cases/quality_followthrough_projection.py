from __future__ import annotations

from . import shared as _shared
from . import runtime_projection_basics as _runtime_projection_basics
from . import autonomy_quality_and_route_projection as _autonomy_quality_and_route_projection
from . import operator_status_and_eval_refresh as _operator_status_and_eval_refresh
from . import supervision_blockers_and_task_reopen as _supervision_blockers_and_task_reopen

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_runtime_projection_basics)
_module_reexport(_autonomy_quality_and_route_projection)
_module_reexport(_operator_status_and_eval_refresh)
_module_reexport(_supervision_blockers_and_task_reopen)

def test_quality_review_followthrough_projects_auto_re_review_pending_when_runtime_recovery_requested() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    payload = module._quality_review_followthrough_projection(
        quality_review_loop={
            "current_phase": "re_review_required",
            "re_review_ready": True,
        },
        needs_physician_decision=False,
        interaction_arbitration={},
        runtime_decision="relaunch_stopped",
        quest_status="stopped",
        current_blockers=[],
        next_system_action="继续观察下一轮复评是否启动。",
    )

    assert payload == {
        "surface_kind": "quality_review_followthrough",
        "state": "auto_re_review_pending",
        "state_label": "等待系统自动复评",
        "waiting_auto_re_review": True,
        "auto_continue_expected": True,
        "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
        "blocking_reason": None,
        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
        "user_intervention_required_now": False,
    }


def test_render_study_progress_markdown_surfaces_quality_review_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publishability_blocked",
            "current_stage_summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review。",
            "paper_stage": "write",
            "paper_stage_summary": "当前主要是等待复评回写。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待系统自动复评。",
            "runtime_decision": "relaunch_stopped",
            "runtime_reason": "quest_stopped_requires_explicit_rerun",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {
                "handling_state_label": "持续监督中",
                "user_visible_verdict": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                "current_focus": "当前在等系统自动发起下一轮复评，主线会自动继续。",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            },
            "quality_review_followthrough": {
                "state_label": "等待系统自动复评",
                "waiting_auto_re_review": True,
                "auto_continue_expected": True,
                "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
                "blocking_reason": None,
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            },
            "quality_review_loop": {
                "current_phase_label": "等待复评",
                "recommended_next_phase_label": "发起复评",
                "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
                "blocking_issue_count": 1,
                "blocking_issues": ["当前 blocking issues 是否已真正闭环"],
                "next_review_focus": ["当前 blocking issues 是否已真正闭环"],
            },
            "module_surfaces": {},
        }
    )

    assert "当前判断: 当前在等系统自动发起下一轮复评，主线会自动继续。" in markdown
    assert "## 自动复评后续" in markdown
    assert "当前状态: 等待系统自动复评" in markdown
    assert "系统自动继续: 会" in markdown
    assert "后续摘要: 当前在等系统自动发起下一轮复评，主线会自动继续。" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。" in markdown


def test_study_progress_projects_gate_clearing_batch_followthrough(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "当前还存在 publication gate blocker。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    gate_batch_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    _write_json(
        gate_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "freeze_scientific_anchor_fields", "status": "updated"},
                {"unit_id": "materialize_display_surface", "status": "updated"},
            ],
            "gate_replay": {
                "status": "blocked",
                "blockers": ["claim_evidence_consistency_failed", "registry_contract_mismatch"],
            },
        },
    )

    result = module._gate_clearing_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=json.loads(publication_eval_path.read_text(encoding="utf-8")),
    )

    assert result == {
        "surface_kind": "gate_clearing_batch_followthrough",
        "status": "executed",
        "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
        "gate_replay_status": "blocked",
        "blocking_issue_count": 2,
        "failed_unit_count": 0,
        "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
        "user_intervention_required_now": False,
        "latest_record_path": str(gate_batch_path),
    }


def test_study_progress_projects_quality_repair_batch_followthrough(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "当前仍需 deterministic quality repair。",
                "stop_loss_pressure": "watch",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    _write_json(
        quality_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "source_summary_id": "evaluation-summary::001-risk::latest",
            "status": "executed",
            "quality_closure_state": "quality_repair_required",
            "quality_execution_lane_id": "general_quality_repair",
            "gate_clearing_batch": {
                "status": "executed",
                "unit_results": [
                    {"unit_id": "materialize_display_surface", "status": "updated"},
                ],
                "gate_replay": {
                    "status": "blocked",
                    "blockers": ["medical_publication_surface_blocked"],
                },
            },
        },
    )

    result = module._quality_repair_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=json.loads(publication_eval_path.read_text(encoding="utf-8")),
        recommended_command="uv run python -m med_autoscience.cli study quality-repair-batch --profile profile.local.toml --study-id 001-risk",
    )

    assert result == {
        "surface_kind": "quality_repair_batch_followthrough",
        "status": "executed",
        "quality_closure_state": "quality_repair_required",
        "quality_execution_lane_id": "general_quality_repair",
        "summary": "最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。",
        "gate_replay_status": "blocked",
        "blocking_issue_count": 1,
        "failed_unit_count": 0,
        "next_confirmation_signal": "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。",
        "user_intervention_required_now": False,
        "recommended_step_id": "run_quality_repair_batch",
        "recommended_command": "uv run python -m med_autoscience.cli study quality-repair-batch --profile profile.local.toml --study-id 001-risk",
        "latest_record_path": str(quality_batch_path),
    }


def test_render_study_progress_markdown_surfaces_gate_clearing_batch_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前仍在门控收口。",
            "paper_stage": "finalize",
            "paper_stage_summary": "当前只剩投稿打包收尾。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待下一轮门控回放。",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_waiting_for_submission_metadata",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {},
            "gate_clearing_batch_followthrough": {
                "status": "executed",
                "summary": "最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。",
                "failed_unit_count": 0,
                "blocking_issue_count": 2,
                "next_confirmation_signal": "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。",
            },
            "module_surfaces": {},
        }
    )

    assert "## Gate-Clearing Batch" in markdown
    assert "当前判断: 最近一轮 gate-clearing batch 已执行；当前仍剩 2 个 gate blocker。" in markdown
    assert "剩余 gate blocker: 2" in markdown


def test_render_study_progress_markdown_surfaces_quality_repair_batch_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前仍在质量修复收口。",
            "paper_stage": "finalize",
            "paper_stage_summary": "当前仍需 deterministic quality repair。",
            "latest_events": [],
            "current_blockers": [],
            "next_system_action": "等待下一轮质量门控回放。",
            "runtime_decision": "blocked",
            "runtime_reason": "publication_quality_gap",
            "progress_freshness": {},
            "supervision": {},
            "intervention_lane": {},
            "operator_status_card": {},
            "quality_repair_batch_followthrough": {
                "status": "executed",
                "summary": "最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。",
                "failed_unit_count": 0,
                "blocking_issue_count": 1,
                "next_confirmation_signal": "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。",
            },
            "module_surfaces": {},
        }
    )

    assert "## Quality-Repair Batch" in markdown
    assert "当前判断: 最近一轮 quality-repair batch 已执行；当前 gate replay 仍剩 1 个 blocker。" in markdown
    assert "剩余 gate blocker: 1" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。" in markdown


