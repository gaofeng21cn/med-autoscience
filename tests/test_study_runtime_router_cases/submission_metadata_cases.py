def test_study_runtime_status_treats_submission_metadata_only_waiting_quest_as_resumable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"


def test_study_runtime_status_treats_submission_metadata_only_waiting_quest_as_resumable_when_checklist_uses_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "build" / "compile_report.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "compiled_with_open_submission_items",
                "author_metadata_status": "placeholder_external_input_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "proof_ready_with_author_metadata_and_submission_declarations_pending",
                "blocking_items": [
                    {
                        "key": "author_metadata",
                        "status": "external_input_required",
                        "detail": "author metadata pending",
                    },
                    {
                        "key": "ethics_statement",
                        "status": "external_input_required",
                        "detail": "ethics statement pending",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"


def test_study_runtime_status_treats_external_metadata_gap_status_as_submission_metadata_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "build" / "compile_report.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "success",
                "author_metadata_status": "placeholder_external_input_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "overall_status": "pituitary_target_package_rebuilt_with_external_metadata_gap",
                "package_status": "auditable_package_ready_with_external_metadata_blocker",
                "blocking_items": [
                    "The title-page packet still needs externally confirmed final author order."
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"


def test_study_runtime_status_parks_submission_metadata_only_waiting_quest_after_auditable_package_delivery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"


def test_ensure_study_runtime_keeps_submission_metadata_only_waiting_quest_parked_after_auditable_package_delivery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    calls: list[str] = []
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append("resume") or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="runtime_watch")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_pauses_live_delivered_submission_package_milestone(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-package",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(study_root / "manuscript" / "current_package" / "figures" / "Figure1.png", "figure placeholder")
    write_text(study_root / "manuscript" / "current_package" / "tables" / "Table1.md", "table placeholder")
    write_text(
        study_root / "manuscript" / "current_package" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
                "figures": [{"id": "Figure1"}],
                "tables": [{"id": "Table1"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "manuscript" / "current_package" / "SUBMISSION_TODO.md",
        "# Submission TODO\n\n- author affiliations\n- ethics approval number\n- conflict of interest\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-package",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-package",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )
    calls: list[tuple[str, str]] = []

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        calls.append(("pause", quest_id))
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "paused"
    assert calls == [("pause", "001-risk")]


def test_study_runtime_status_auto_resumes_invalid_blocking_waiting_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-invalid-001.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": "progress-invalid-001",
                "id": "progress-invalid-001",
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
                "summary": "等待 Gateway 侧转发新的用户指令。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": "progress-invalid-001",
                "expects_reply": True,
                "reply_mode": "blocking",
                "surface_actions": [],
                "options": [],
                "allow_free_text": True,
                "reply_schema": {"type": "free_text"},
                "guidance_vm": {"requires_user_decision": False},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "waiting_for_user",
                "waiting_interaction_id": "progress-invalid-001",
                "default_reply_interaction_id": "progress-invalid-001",
                "pending_decisions": ["progress-invalid-001"],
                "active_interaction_id": "progress-invalid-001",
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
    assert result["interaction_arbitration"] == {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": "blocking_requires_structured_decision_request",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "progress",
        "decision_type": None,
        "source_artifact_path": str(
            quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-invalid-001.json"
        ),
        "controller_stage_note": (
            "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
            "runtime blocking is rejected unless it is a valid structured decision request."
        ),
    }


def test_study_runtime_status_marks_finalize_metadata_gap_progress_as_user_decision_signal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            }
        )
        + "\n",
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "overall_status": "pituitary_target_package_rebuilt_with_external_metadata_gap",
                "package_status": "auditable_package_ready_with_external_metadata_blocker",
                "blocking_items": [
                    "The title-page packet still needs externally confirmed final author order."
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    interaction_id = "progress-finalize-001"
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / f"{interaction_id}.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": interaction_id,
                "id": interaction_id,
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "当前只剩题名页与投稿声明的最终外部元数据需要确认。",
                "summary": "请确认最终作者顺序、单位映射与声明文案。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": interaction_id,
                "expects_reply": True,
                "reply_mode": "blocking",
                "options": [
                    {"id": "1", "label": "完整元数据"},
                    {"id": "2", "label": "最小字段"},
                    {"id": "3", "label": "继续等待"},
                ],
                "allow_free_text": True,
                "reply_schema": {
                    "type": "object",
                    "properties": {
                        "choice": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["choice"],
                },
                "guidance_vm": {"requires_user_decision": False},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "local_runtime_state_contract",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {"ok": False, "status": "unknown", "error": "daemon unavailable"},
            "bash_session_audit": {"ok": False, "status": "unknown", "error": "daemon unavailable"},
            "local_runtime_state": {
                "status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            },
            "probe_error": "daemon unavailable | daemon unavailable",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "waiting_for_user",
                "waiting_interaction_id": interaction_id,
                "default_reply_interaction_id": interaction_id,
                "pending_decisions": [interaction_id],
                "active_interaction_id": interaction_id,
            },
        },
        raising=False,
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_parked_on_unchanged_finalize_state"
    assert result["pending_user_interaction"]["guidance_requires_user_decision"] is True
    assert result["interaction_arbitration"]["action"] == "resume"


def test_study_runtime_status_auto_resumes_premature_completion_request_when_publication_gate_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    decision_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "artifacts"
        / "decisions"
        / "decision-completion-001.json"
    )
    write_text(
        decision_path,
        json.dumps(
            {
                "kind": "decision",
                "schema_version": 1,
                "artifact_id": "decision-completion-001",
                "id": "decision-completion-001",
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "message": "[等待决策] 批准 completion。",
                "summary": "请求批准 completion。",
                "interaction_id": "decision-completion-001",
                "expects_reply": True,
                "reply_mode": "blocking",
                "allow_free_text": True,
                "reply_schema": {"decision_type": "quest_completion_approval"},
                "guidance_vm": {"requires_user_decision": True},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terminology"],
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "waiting_for_user",
                "waiting_interaction_id": "decision-completion-001",
                "default_reply_interaction_id": "decision-completion-001",
                "pending_decisions": ["decision-completion-001"],
                "active_interaction_id": "decision-completion-001",
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert result["interaction_arbitration"] == {
        "classification": "premature_completion_request",
        "action": "resume",
        "reason_code": "completion_requested_before_publication_gate_clear",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "decision",
        "decision_type": "quest_completion_approval",
        "source_artifact_path": str(decision_path),
        "publication_gate_status": "blocked",
        "publication_gate_blockers": ["forbidden_manuscript_terminology"],
        "publication_gate_required_action": "complete_bundle_stage",
        "controller_stage_note": (
            "Runtime completion approval was requested before the MAS publication gate cleared; "
            "resume the managed runtime so it fixes publication blockers instead of asking the user."
        ),
    }
    assert "human_gate_hint" not in result["family_event_envelope"]
    assert result["family_checkpoint_lineage"]["resume_contract"]["resume_mode"] == "resume_from_checkpoint"
    assert result["family_checkpoint_lineage"]["resume_contract"]["human_gate_required"] is False
    assert result["family_human_gates"] == []


def test_study_runtime_status_reroutes_live_write_drift_back_to_publication_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            }
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": [
                "active_run_drifting_into_write_without_gate_approval",
                "missing_reporting_guideline_checklist",
            ],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_drifting_into_write_without_gate_approval"
    assert result["publication_supervisor_state"]["current_required_action"] == "return_to_publishability_gate"
    assert result["execution_owner_guard"]["supervisor_only"] is True


def test_explicit_reviewer_revision_intake_resumes_paused_delivered_package(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    calls: list[str] = []
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running"}},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="user_explicit_wakeup")

    assert result["decision"] == "resume"
    assert result["quest_status"] == "running"
    assert calls == ["prepare_overlay", "sync_context", "resume"]


def test_explicit_reviewer_revision_intake_keeps_live_delivered_package_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-revision",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-revision",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-revision",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "pause_quest",
        lambda **kwargs: pytest.fail("pause_quest should not run for explicit reviewer revision wakeup"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="user_explicit_wakeup")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["quest_status"] == "running"
