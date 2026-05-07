from .shared import *  # noqa: F403
def _write_stop_loss_status_fixture(
    monkeypatch,
    tmp_path: Path,
    *,
    quest_status: str,
):
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="clinical_phenotype",
    )
    quest_root = profile.runtime_root / "004-invasive-architecture"
    write_text(quest_root / "quest.yaml", "quest_id: 004-invasive-architecture\n")
    write_text(quest_root / ".ds" / "runtime_state.json", f'{{"status":"{quest_status}"}}\n')
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        entry_mode="full_research",
        task_intake_kind="publishability_stop_loss",
        task_intent=(
            "临床专家反馈：Knosp 分型本来就是看侵袭性，当前结果没有临床意义、没有新结论，"
            "论文不成立，应触发 publishability stop-loss。"
        ),
        constraints=["不要路由为 reviewer_revision 或 bundle cleanup。"],
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "004-invasive-architecture"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "complete_bundle_stage",
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "stale bundle-stage blocker should not outrank stop-loss task intake",
            "blockers": ["stale_submission_minimal_authority"],
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
        },
    )
    return module, profile


def test_task_intake_stop_loss_overrides_publication_supervisor_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module, profile = _write_stop_loss_status_fixture(
        monkeypatch,
        tmp_path,
        quest_status="running",
    )

    result = module.study_runtime_status(profile=profile, study_id="004-invasive-architecture")

    assert result["publication_supervisor_state"]["supervisor_phase"] == "stop_loss"
    assert result["publication_supervisor_state"]["phase_owner"] == "task_intake"
    assert result["publication_supervisor_state"]["current_required_action"] == "stop_runtime"
    assert "publishability stop-loss" in result["publication_supervisor_state"]["controller_stage_note"]


def test_task_intake_stop_loss_blocks_stopped_auto_resume(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module, profile = _write_stop_loss_status_fixture(
        monkeypatch,
        tmp_path,
        quest_status="stopped",
    )

    result = module.study_runtime_status(profile=profile, study_id="004-invasive-architecture")

    assert result["publication_supervisor_state"]["supervisor_phase"] == "stop_loss"
    assert result["decision"] == "blocked"
    assert result["reason"] == "publishability_stop_loss_recommended"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "publishability_stop_loss"
    assert result["progress_projection"]["auto_runtime_parked"]["parked"] is True
    assert result["progress_projection"]["auto_runtime_parked"]["parked_state"] == "publishability_stop_loss"


def test_task_intake_manual_hold_blocks_active_no_live_auto_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-dpcc-longitudinal-care-inertia-intensification-gap",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="clinical_phenotype",
    )
    quest_root = profile.runtime_root / "004-dpcc-longitudinal-care-inertia-intensification-gap"
    write_text(quest_root / "quest.yaml", "quest_id: 004-dpcc-longitudinal-care-inertia-intensification-gap\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        '{"status":"active","active_run_id":null,"continuation_policy":"auto","continuation_reason":"runtime_platform_repair_redrive"}\n',
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="004-dpcc-longitudinal-care-inertia-intensification-gap",
        study_root=study_root,
        entry_mode="full_research",
        task_intake_kind="manual_hold",
        task_intent=(
            "用户确认糖尿病004已经到达里程碑投稿包后手动停止；当前结果没有达到预期，"
            "暂不应由 MAS/MDS 自动恢复写入，等待形成新方案后再显式唤醒大改。"
        ),
        constraints=[
            "保持当前论文线停驻；不得由 runtime_platform_repair 或 supervisor redrive 自动恢复写入。",
            "未来若重启必须先形成新的方案和显式 wakeup。",
        ],
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(
            workspace_root,
            "004-dpcc-longitudinal-care-inertia-intensification-gap",
        ),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none", "session_count": 0, "live_session_count": 0},
        },
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "schema_version": 1,
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publication gate remains blocked.",
        },
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="004-dpcc-longitudinal-care-inertia-intensification-gap",
    )

    assert result["publication_supervisor_state"]["supervisor_phase"] == "manual_hold"
    assert result["decision"] == "pause"
    assert result["reason"] == "quest_waiting_for_explicit_wakeup_after_manual_hold"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "manual_hold"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
    assert result["progress_projection"]["current_stage"] == "auto_runtime_parked"
    assert result["progress_projection"]["paper_stage"] == "manual_hold"
