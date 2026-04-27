from __future__ import annotations

from . import shared as _shared
from . import runtime_projection_basics as _runtime_projection_basics
from . import autonomy_quality_and_route_projection as _autonomy_quality_and_route_projection
from . import operator_status_and_eval_refresh as _operator_status_and_eval_refresh

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_runtime_projection_basics)
_module_reexport(_autonomy_quality_and_route_projection)
_module_reexport(_operator_status_and_eval_refresh)

def test_study_progress_projects_supervisor_tick_gap_for_unsupervised_managed_runtime(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_paused",
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 MedAutoScience supervisor tick / heartbeat 调度，再继续托管监管与自动恢复。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 1800,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
        },
    )

    profile_ref = tmp_path / "profile.local.toml"

    result = module.read_study_progress(profile=profile, study_id="001-risk", profile_ref=profile_ref)

    assert result["current_stage"] == "managed_runtime_supervision_gap"
    assert result["intervention_lane"]["lane_id"] == "workspace_supervision_gap"
    assert result["intervention_lane"]["recommended_action_id"] == "refresh_supervision"
    assert result["operator_verdict"] == {
        "surface_kind": "study_operator_verdict",
        "verdict_id": "study_operator_verdict::001-risk::workspace_supervision_gap",
        "study_id": "001-risk",
        "lane_id": "workspace_supervision_gap",
        "severity": "critical",
        "decision_mode": "intervene_now",
        "needs_intervention": True,
        "focus_scope": "workspace",
        "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
        "reason_summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
        "primary_step_id": "refresh_supervision",
        "primary_surface_kind": "runtime_watch_refresh",
        "primary_command": (
            "uv run python -m med_autoscience.cli runtime watch --runtime-root "
            + str(profile.runtime_root)
            + " --profile "
            + str(profile_ref.resolve())
            + " --ensure-study-runtimes --apply"
        ),
    }
    assert result["recommended_command"].endswith(
        "runtime watch --runtime-root "
        + str(profile.runtime_root)
        + " --profile "
        + str(profile_ref.resolve())
        + " --ensure-study-runtimes --apply"
    )
    assert result["recommended_commands"][0]["step_id"] == "refresh_supervision"
    assert result["recovery_contract"]["action_mode"] == "refresh_supervision"
    assert "监管心跳已陈旧" in result["current_stage_summary"]
    assert any("监管心跳已陈旧" in item for item in result["current_blockers"])
    assert "supervisor tick" in result["next_system_action"]
    assert result["supervision"]["supervisor_tick_status"] == "stale"


def test_study_progress_projects_explicit_runtime_blocker_before_publication_supervision(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "explicit_rerun_required",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-4e192147",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "runtime_blocked"
    assert "显式" in result["current_stage_summary"]
    assert any("显式" in item for item in result["current_blockers"])
    assert "显式" in result["next_system_action"]


def test_study_progress_projects_manual_finishing_contract_before_runtime_blocker(
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
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: 当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口，不再把它视为默认自动续跑对象。",
                "  next_action_summary: 继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "explicit_rerun_required",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-4e192147",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert "人工打磨收尾" in result["current_stage_summary"]
    assert not any("显式" in item for item in result["current_blockers"])
    assert "兼容性" in result["next_system_action"]


def test_study_progress_projects_manual_finishing_fast_lane_intake(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: 当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口，不再把它视为默认自动续跑对象。",
                "  next_action_summary: 继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="manuscript_fast_lane",
        task_intent=(
            "Reviewer feedback asks for text-only manuscript revision during manual finishing. "
            "Use existing evidence only and revise controller-authorized canonical paper sources."
        ),
        constraints=(
            "runtime must be inactive or foreground takeover must be allowed before editing",
            "edit only canonical paper/ manuscript text and structure",
            "all claims must come from existing evidence; do not run new analysis",
        ),
        first_cycle_outputs=(
            "controller-visible intake and handoff, canonical paper patch, export/sync, QC and package consistency checks",
        ),
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "manuscript_fast_lane",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert result["task_intake"]["manuscript_fast_lane"]["status"] == "requested"
    assert result["intervention_lane"]["lane_id"] == "manual_finishing_fast_lane"
    assert result["quality_execution_lane"]["lane_id"] == "manuscript_fast_lane"
    assert result["operator_verdict"]["decision_mode"] == "compatibility_guard_only"
    assert result["operator_verdict"]["repair_mode"] == "same_line_route_back"
    assert "fast lane" in result["next_system_action"]
    assert "canonical paper" in result["next_system_action"]


def test_study_progress_projects_bundle_only_submission_ready_parking_before_runtime_blocker(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_review_loop": {"closure_state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "read_evaluation_summary",
        lambda *, study_root, ref: {
            "schema_version": 1,
            "quality_closure_truth": {"state": "bundle_only_remaining"},
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_hardening",
                "current_phase_label": "投稿包收口",
                "recommended_next_phase": "finalize",
                "recommended_next_phase_label": "定稿与投稿收尾",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "planned",
                "blocking_issue_count": 1,
                "blocking_issues": ["Only finalize-level cleanup remains."],
                "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
                "re_review_ready": False,
                "summary": "Core scientific quality is closed; only finalize-level bundle cleanup remains.",
                "recommended_next_action": "Return to finalize only if the runtime is explicitly resumed later.",
            },
            "module": "eval_hygiene",
            "surface_kind": "evaluation_module_surface",
            "summary_id": "evaluation-summary::001-risk::latest",
            "summary_ref": str(study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"),
            "promotion_gate_ref": str(study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"),
            "next_action_summary": "先在 finalize 修订，完成当前最小投稿包收口。",
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "stop_loss_pressure": "none",
            "requires_controller_decision": True,
            "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "status_summary": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "manual_finishing"
    assert "投稿包里程碑" in result["current_stage_summary"]
    assert "显式 rerun 或 relaunch" not in result["current_stage_summary"]
    assert "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。" not in result["current_blockers"]


def test_study_progress_reopened_task_intake_overrides_bundle_only_parking(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_root.mkdir(parents=True, exist_ok=True)
    for rel in ["manuscript.docx", "paper.pdf", "references.bib", "submission_manifest.json", "SUBMISSION_TODO.md"]:
        path = current_package_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").write_text("zip\n", encoding="utf-8")
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_review_loop": {"closure_state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开 001 同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口；"
            "必须补做并写入 manuscript 的分层统计分析，并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T07:22:54+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-26T07:22:54+00:00",
            "verdict": {
                "overall_verdict": "promising",
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json",
        {
            "schema_version": 1,
            "scanned_at": "2026-04-26T07:17:19+00:00",
            "controllers": {
                "publication_gate": {
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            },
        },
    )
    monkeypatch.setattr(
        module,
        "read_evaluation_summary",
        lambda *, study_root, ref: {
            "schema_version": 1,
            "quality_closure_truth": {"state": "bundle_only_remaining"},
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "same_line_route_truth": {
                "surface_kind": "same_line_route_truth",
                "same_line_state": "finalize_only_remaining",
                "same_line_state_label": "同线定稿与投稿包收尾",
                "route_mode": "return",
                "route_target": "finalize",
                "route_target_label": "定稿与投稿收尾",
                "summary": "旧的 finalize-only 判断。",
                "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            },
            "same_line_route_surface": {
                "surface_kind": "same_line_route_surface",
                "lane_id": "submission_hardening",
                "repair_mode": "same_line_route_back",
                "route_target": "finalize",
                "summary": "旧的 submission hardening 判断。",
                "closure_state": "bundle_only_remaining",
            },
            "module": "eval_hygiene",
            "surface_kind": "evaluation_module_surface",
            "summary_id": "evaluation-summary::001-risk::latest",
            "summary_ref": str(summary_path),
            "promotion_gate_ref": str(study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"),
            "next_action_summary": "先在 finalize 修订，完成当前最小投稿包收口。",
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "stop_loss_pressure": "none",
            "requires_controller_decision": True,
            "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "status_summary": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["manual_finish_contract"] is None
    assert result["current_stage"] == "publication_supervision"
    assert result["paper_stage"] == "analysis-campaign"
    assert "待修订状态" in result["current_stage_summary"]
    assert "价格顾虑有/无分层" in result["next_system_action"]
    assert any("待修订状态" in item for item in result["current_blockers"])
    assert result["quality_closure_truth"]["state"] == "quality_repair_required"
    assert result["quality_execution_lane"]["lane_id"] == "general_quality_repair"
    assert result["same_line_route_truth"]["same_line_state"] == "bounded_analysis"
    assert result["same_line_route_truth"]["route_target"] == "analysis-campaign"
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"]["route_target"] == "analysis-campaign"
    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    event_summaries = [str(item.get("summary") or "") for item in result["latest_events"]]
    assert "待修订状态" in result["latest_events"][0]["summary"]
    assert not any("bundle-stage work is unlocked" in item for item in event_summaries)


def test_study_progress_reopened_task_intake_yields_to_fresh_bundle_only_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开 001 同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口；"
            "必须补做并写入 manuscript 的分层统计分析，并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    _write_json(
        summary_path,
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::quest-001::2099-01-01T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2099-01-01T00:00:00+00:00",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                }
            },
        },
    )
    monkeypatch.setattr(
        module,
        "read_evaluation_summary",
        lambda *, study_root, ref: {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::latest",
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "stop_loss_pressure": "none",
            "requires_controller_decision": True,
            "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾。",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "same_line_route_truth": {
                "surface_kind": "same_line_route_truth",
                "same_line_state": "finalize_only_remaining",
                "same_line_state_label": "同线定稿与投稿包收尾",
                "route_mode": "return",
                "route_target": "finalize",
                "route_target_label": "定稿与投稿收尾",
                "summary": "当前同线路由已经收窄到定稿与投稿包收尾。",
                "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            },
            "same_line_route_surface": {
                "surface_kind": "same_line_route_surface",
                "lane_id": "submission_hardening",
                "repair_mode": "same_line_route_back",
                "route_target": "finalize",
                "summary": "Only finalize-level submission hardening remains.",
                "closure_state": "bundle_only_remaining",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_hardening",
                "current_phase_label": "投稿包收口",
                "recommended_next_phase": "finalize",
                "recommended_next_phase_label": "定稿与投稿收尾",
                "active_plan_execution_status": "planned",
                "blocking_issue_count": 1,
                "blocking_issues": ["Only finalize-level cleanup remains."],
                "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
                "re_review_ready": False,
                "summary": "Core scientific quality is closed; only finalize-level bundle cleanup remains.",
                "recommended_next_action": "先在 finalize 修订，完成当前最小投稿包收口。",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "none",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "MedAutoScience 外环监管心跳已陈旧。",
                "next_action_summary": "等待新的状态刷新。",
            },
            "runtime_supervision": {
                "health_status": "live",
                "summary": "托管运行时在线，研究仍在自动推进。",
                "next_action_summary": "继续监督当前托管运行，并等待新的阶段事件。",
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["manual_finish_contract"] is not None
    assert result["current_stage"] == "manual_finishing"
    assert result["quality_closure_truth"]["state"] == "bundle_only_remaining"
    assert result["same_line_route_truth"]["route_target"] == "finalize"
    assert not any("待修订状态" in item for item in result["current_blockers"])
    assert result["module_surfaces"]["runtime"]["status_summary"].startswith("当前论文线已到投稿包里程碑")
    assert "自动推进" not in result["module_surfaces"]["runtime"]["status_summary"]
    assert result["module_surfaces"]["runtime"]["next_action_summary"].startswith("当前包已经可直接交给用户审阅")


def test_study_progress_does_not_project_study_completed_when_completion_contract_is_not_ready(
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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-002",
                "auto_resume": False,
            },
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "completed",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {
                "ready": False,
                "status": "incomplete",
                "completion_status": "completed",
                "summary": "论文交付声明已写，但 final submission evidence 还没真正补齐。",
                "missing_evidence_paths": ["manuscript/final/submission_manifest.json"],
            },
            "decision": "blocked",
            "reason": "study_completion_contract_not_ready",
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "completed",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": None,
                "continuation_reason": None,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["current_stage"] == "runtime_blocked"
    assert "收尾/交付" not in result["current_stage_summary"]
    assert any("final submission 证据还未补齐" in item for item in result["current_blockers"])
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
