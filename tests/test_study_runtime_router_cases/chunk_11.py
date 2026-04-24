def test_study_runtime_status_materializes_route_back_same_line_for_blocked_bundle_stage(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-03T04:00:00+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(quest_root / "paper" / "paper_bundle_manifest.json"),
            "quest_id": "001-risk",
            "run_id": "run-1",
            "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "paper_root": str(study_root / "paper"),
            "compile_report_path": None,
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "status": "blocked",
            "blockers": ["stale_study_delivery_mirror", "submission_surface_qc_failure_present"],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(quest_root / "paper" / "paper_bundle_manifest.json"),
            "submission_minimal_manifest_path": str(quest_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "study_delivery_status": "stale_source_changed",
            "medical_publication_surface_status": "clear",
            "submission_surface_qc_failures": ["submission_docx_older_than_source_markdown"],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "summary",
            "conclusion": "conclusion",
            "controller_note": "note",
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert result["publication_supervisor_state"]["supervisor_phase"] == "bundle_stage_blocked"
    assert payload["verdict"]["overall_verdict"] == "blocked"
    assert payload["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert payload["recommended_actions"][0]["route_target"] == "finalize"
    assert payload["recommended_actions"][0]["requires_controller_decision"] is True
    assert payload["quality_assessment"]["evidence_strength"]["status"] == "ready"
    assert payload["quality_assessment"]["human_review_readiness"]["status"] == "blocked"
    assert payload["quality_assessment"]["novelty_positioning"]["status"] == "underdefined"
    assert (
        payload["quality_assessment"]["clinical_significance"]["reviewer_reason"]
        == "主临床问题与结果表面已具备，但 clinician-facing interpretation target 仍未显式冻结。"
    )
    assert (
        payload["quality_assessment"]["evidence_strength"]["reviewer_revision_advice"]
        == "核心证据链已达标，下一轮优先清理交付与刷新层阻塞，避免再次影响审阅入口。"
    )
    assert (
        payload["quality_assessment"]["novelty_positioning"]["reviewer_next_round_focus"]
        == "补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。"
    )
    assert (
        payload["quality_assessment"]["human_review_readiness"]["reviewer_reason"]
        == "publication gate 尚未清关，当前稿件还不能作为正式人工审阅包放行。"
    )


@pytest.mark.parametrize(
    ("charter_status", "charter_body", "expected_reason"),
    [
        ("study_charter_missing", None, "study_charter_missing"),
        ("study_charter_invalid", "{invalid\n", "study_charter_invalid"),
    ],
)
def test_study_runtime_status_blocks_when_study_charter_gate_fails(
    monkeypatch,
    tmp_path: Path,
    charter_status: str,
    charter_body: str | None,
    expected_reason: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    if charter_body is None:
        if charter_path.exists():
            charter_path.unlink()
    else:
        write_text(charter_path, charter_body)
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-20T10:00:00+00:00",
            "anchor_kind": "main_result",
            "anchor_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "quest_id": "001-risk",
            "run_id": "run-1",
            "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "paper_root": str(study_root / "paper"),
            "compile_report_path": None,
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": None,
            "medical_publication_surface_current": False,
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "status": "blocked",
            "blockers": [charter_status],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": None,
            "submission_minimal_manifest_path": None,
            "submission_minimal_present": False,
            "submission_minimal_docx_present": False,
            "submission_minimal_pdf_present": False,
            "medical_publication_surface_status": "blocked",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "summary",
            "conclusion": "conclusion",
            "controller_note": "note",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "controller-owned charter contract must be repaired before publication work continues",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == expected_reason
    assert result["publication_supervisor_state"]["current_required_action"] == "return_to_publishability_gate"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_study_runtime_status_publication_eval_keeps_bundle_stage_as_same_line_when_gate_is_clear(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T02:04:11+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "quest_id": "001-risk",
            "run_id": "paper-main-outline-001-run",
            "main_result_path": None,
            "paper_root": str(runtime_paper_root),
            "compile_report_path": str(runtime_paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "status": "clear",
            "blockers": [],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "submission_minimal_manifest_path": str(runtime_paper_root / "submission_minimal" / "submission_manifest.json"),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "medical_publication_surface_status": "clear",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [str(runtime_paper_root / "submission_pituitary")],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "bundle-stage work is unlocked and can proceed on the critical path",
            "conclusion": "bundle-stage work is unlocked and can proceed on the critical path",
            "controller_note": "The controller does not decide scientific publishability by itself.",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert result["publication_supervisor_state"]["supervisor_phase"] == "bundle_stage_ready"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_bundle_stage"
    assert payload["verdict"]["overall_verdict"] == "promising"
    assert payload["recommended_actions"][0]["action_type"] == "continue_same_line"
    assert payload["recommended_actions"][0]["reason"] == "bundle-stage work is unlocked and can proceed on the critical path"
    assert payload["recommended_actions"][0]["requires_controller_decision"] is True


def test_study_runtime_status_publication_eval_uses_bounded_analysis_when_write_stage_is_clear(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T02:04:11+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "quest_id": "001-risk",
            "run_id": "paper-main-outline-001-run",
            "main_result_path": None,
            "paper_root": str(runtime_paper_root),
            "compile_report_path": str(runtime_paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "status": "clear",
            "blockers": [],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "submission_minimal_manifest_path": str(runtime_paper_root / "submission_minimal" / "submission_manifest.json"),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "medical_publication_surface_status": "clear",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "write-stage work is clear and needs one bounded robustness pass before promotion review",
            "conclusion": "write-stage work is clear and needs one bounded robustness pass before promotion review",
            "controller_note": "The controller does not decide scientific publishability by itself.",
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": ["continue_bundle_stage"],
            "controller_stage_note": "write stage is clear and should continue through one bounded supplementary analysis pass",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert result["publication_supervisor_state"]["supervisor_phase"] == "write_stage_ready"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_write_stage"
    assert payload["verdict"]["overall_verdict"] == "promising"
    assert payload["recommended_actions"][0]["action_type"] == "bounded_analysis"
    assert (
        payload["recommended_actions"][0]["reason"]
        == "write stage is clear and should continue through one bounded supplementary analysis pass"
    )
    assert payload["recommended_actions"][0]["requires_controller_decision"] is True


def test_study_runtime_status_publication_eval_materializes_same_line_route_back_for_blocked_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T02:04:11+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "quest_id": "001-risk",
            "run_id": "paper-main-outline-001-run",
            "main_result_path": None,
            "paper_root": str(runtime_paper_root),
            "compile_report_path": str(runtime_paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "status": "blocked",
            "blockers": [
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
            ],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "submission_minimal_manifest_path": str(runtime_paper_root / "submission_minimal" / "submission_manifest.json"),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["reviewer_first_concerns_unresolved"],
            "medical_publication_surface_route_back_recommendation": "return_to_write",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
            "conclusion": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
            "controller_note": "The controller does not decide scientific publishability by itself.",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert result["publication_supervisor_state"]["supervisor_phase"] == "publishability_gate_blocked"
    assert payload["verdict"]["overall_verdict"] == "blocked"
    assert payload["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert payload["recommended_actions"][0]["reason"] == "稿件书写面还有医学论文表达硬阻塞，需要继续修文。"
    assert payload["recommended_actions"][0]["route_target"] == "write"
    assert (
        payload["recommended_actions"][0]["route_key_question"]
        == "What is the narrowest same-line manuscript repair or continuation step required now?"
    )
    assert payload["recommended_actions"][0]["requires_controller_decision"] is True


def test_study_runtime_status_publication_eval_uses_runtime_paper_surface_when_submission_minimal_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-03T04:00:00+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "quest_id": "001-risk",
            "run_id": "run-1",
            "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "paper_root": str(runtime_paper_root),
            "compile_report_path": str(runtime_paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": str(
                quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
            ),
            "medical_publication_surface_current": True,
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "missing_submission_minimal"],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": str(runtime_paper_root / "paper_bundle_manifest.json"),
            "submission_minimal_manifest_path": None,
            "submission_minimal_present": False,
            "submission_minimal_docx_present": False,
            "submission_minimal_pdf_present": False,
            "medical_publication_surface_status": "blocked",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "summary",
            "conclusion": "conclusion",
            "controller_note": "note",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )

    module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert payload["delivery_context_refs"] == {
        "paper_root_ref": str(runtime_paper_root),
        "submission_minimal_ref": str(runtime_paper_root / "submission_minimal" / "submission_manifest.json"),
    }
    assert payload["gaps"] == [
        {
            "gap_id": "gap-001",
            "gap_type": "reporting",
            "severity": "must_fix",
            "summary": "medical_publication_surface_blocked",
            "evidence_refs": [
                str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
                str(runtime_paper_root),
                str(quest_root.resolve()),
            ],
        },
        {
            "gap_id": "gap-002",
            "gap_type": "delivery",
            "severity": "must_fix",
            "summary": "missing_submission_minimal",
            "evidence_refs": [
                str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
                str(runtime_paper_root),
                str(quest_root.resolve()),
            ],
        },
    ]


def test_study_runtime_status_surfaces_pending_user_interaction_for_waiting_quest(
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
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-standby-001.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": "progress-standby-001",
                "id": "progress-standby-001",
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
                "summary": "等待 Gateway 侧转发新的用户指令。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": "progress-standby-001",
                "expects_reply": True,
                "reply_mode": "blocking",
                "surface_actions": [],
                "options": [],
                "allow_free_text": True,
                "reply_schema": {"type": "free_text"},
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
                "waiting_interaction_id": "progress-standby-001",
                "default_reply_interaction_id": "progress-standby-001",
                "pending_decisions": ["progress-standby-001"],
                "active_interaction_id": "progress-standby-001",
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
    assert result["quest_status"] == "waiting_for_user"
    assert result["pending_user_interaction"] == {
        "interaction_id": "progress-standby-001",
        "kind": "progress",
        "waiting_interaction_id": "progress-standby-001",
        "default_reply_interaction_id": "progress-standby-001",
        "pending_decisions": ["progress-standby-001"],
        "blocking": True,
        "reply_mode": "blocking",
        "expects_reply": True,
        "allow_free_text": True,
        "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
        "summary": "等待 Gateway 侧转发新的用户指令。",
        "reply_schema": {"type": "free_text"},
        "decision_type": None,
        "options_count": 0,
        "guidance_requires_user_decision": None,
        "source_artifact_path": str(
            quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-standby-001.json"
        ),
        "relay_required": True,
    }
    assert result["interaction_arbitration"] == {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": "blocking_requires_structured_decision_request",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "progress",
        "decision_type": None,
        "source_artifact_path": str(
            quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-standby-001.json"
        ),
        "controller_stage_note": (
            "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
            "runtime blocking is rejected unless it is a valid structured decision request."
        ),
    }
    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["session"]["study_id"] == "001-risk"
    assert "human_gate_hint" not in result["family_event_envelope"]
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_checkpoint_lineage"]["resume_contract"]["resume_mode"] == "resume_from_checkpoint"
    assert result["family_checkpoint_lineage"]["resume_contract"]["human_gate_required"] is False
    assert result["family_human_gates"] == []
