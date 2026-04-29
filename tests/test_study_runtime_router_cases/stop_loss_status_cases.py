def test_task_intake_stop_loss_overrides_publication_supervisor_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        entry_mode="full_research",
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

    result = module.study_runtime_status(profile=profile, study_id="004-invasive-architecture")

    assert result["publication_supervisor_state"]["supervisor_phase"] == "stop_loss"
    assert result["publication_supervisor_state"]["phase_owner"] == "task_intake"
    assert result["publication_supervisor_state"]["current_required_action"] == "stop_runtime"
    assert "publishability stop-loss" in result["publication_supervisor_state"]["controller_stage_note"]
