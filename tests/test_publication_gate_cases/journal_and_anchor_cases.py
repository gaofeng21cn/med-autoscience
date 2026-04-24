from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_build_gate_state_reads_authoritative_paper_line_state_when_projected_manifest_is_selected(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"

    dump_json(
        authoritative_paper_root / "paper_line_state.json",
        {
            "paper_root": str(authoritative_paper_root.resolve()),
            "paper_branch": "paper/main",
            "open_supplementary_count": 0,
            "recommended_action": "continue_bundle_stage",
            "blocking_reasons": [],
        },
    )
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(authoritative_paper_root / "paper_bundle_manifest.json", projected_manifest)
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(analysis_paper_root.resolve()),
            "paper_branch": "analysis/paper-line-paper-main-outline-001-run/analysis-faea0014-live-submission-package-projection-recovery",
            "open_supplementary_count": 1,
            "recommended_action": "complete_required_supplementary",
            "blocking_reasons": ["analysis mirror still thinks a slice is open"],
        },
    )
    (analysis_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (analysis_paper_root / "draft.md").write_text("analysis slice mirror", encoding="utf-8")
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_manifest
    assert state.paper_root == authoritative_paper_root.resolve()
    assert state.paper_line_state_path == (authoritative_paper_root / "paper_line_state.json").resolve()
    assert state.paper_line_state == {
        "paper_root": str(authoritative_paper_root.resolve()),
        "paper_branch": "paper/main",
        "open_supplementary_count": 0,
        "recommended_action": "continue_bundle_stage",
        "blocking_reasons": [],
    }
    assert report["paper_line_open_supplementary_count"] == 0
    assert "paper_line_required_supplementary_pending" not in report["blockers"]
def test_build_gate_report_marks_stale_study_delivery_mirror_when_authority_package_disappears(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "missing_source_paths": [
                "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "missing_submission_minimal" in report["blockers"]
    assert "stale_study_delivery_mirror" in report["blockers"]
    assert report["study_delivery_status"] == "stale_source_missing"
    assert report["study_delivery_stale_reason"] == "current_submission_source_missing"
    assert report["study_delivery_manifest_path"] == "/tmp/studies/002/manuscript/delivery_manifest.json"
    assert report["supervisor_phase"] == "bundle_stage_blocked"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "complete_bundle_stage"
def test_build_gate_report_blocks_stale_submission_minimal_authority_when_paper_inputs_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={"schema_version": 1, "figures": []},
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(paper_root / "build" / "review_manuscript.md", "# Review Manuscript\n\nOriginal authority draft.\n")
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [],
        },
    )
    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Review Manuscript\n\nAuthority draft updated after submission package generation.\n",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["submission_minimal_authority_status"] == "stale_source_changed"
    assert report["submission_minimal_authority_stale_reason"] == "submission_source_newer_than_manifest"
    assert "stale_submission_minimal_authority" in report["blockers"]
def test_build_gate_report_marks_bundle_tasks_downstream_when_publication_anchor_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="running",
    )
    paper_bundle_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "paper_bundle_manifest.json"
    )
    paper_bundle_manifest_path.unlink()

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "missing"
    assert report["allow_write"] is False
    assert "missing_publication_anchor" in report["blockers"]
    assert report["supervisor_phase"] == "scientific_anchor_missing"
    assert report["phase_owner"] == "publication_gate"
    assert report["upstream_scientific_anchor_ready"] is False
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert report["deferred_downstream_actions"] == []
def test_build_gate_report_marks_bundle_tasks_downstream_when_post_main_gate_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["allow_write"] is False
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["phase_owner"] == "publication_gate"
    assert report["upstream_scientific_anchor_ready"] is True
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert report["deferred_downstream_actions"] == []
def test_run_controller_handles_finalize_only_bundle_blockers_without_main_metrics(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert "missing_submission_minimal" in result["blockers"]
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "missing_submission_minimal" in queue["pending"][0]["content"]
def test_run_controller_materializes_stable_publication_eval_when_apply_clear(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    state = module.build_gate_state(quest_root)
    assert state.paper_root is not None

    monkeypatch.setattr(
        module,
        "build_gate_report",
        lambda gate_state: {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-18T18:12:13+00:00",
            "anchor_kind": "paper_bundle",
            "anchor_path": str(gate_state.paper_root / "paper_bundle_manifest.json"),
            "quest_id": "002-early-residual-risk",
            "run_id": "paper-run-1",
            "main_result_path": None,
            "paper_root": str(gate_state.paper_root),
            "compile_report_path": str(gate_state.paper_root / "build" / "compile_report.json"),
            "latest_gate_path": str(
                quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
            ),
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
            "paper_bundle_manifest_path": str(gate_state.paper_root / "paper_bundle_manifest.json"),
            "submission_checklist_path": None,
            "submission_checklist_present": False,
            "submission_checklist_overall_status": None,
            "submission_checklist_handoff_ready": False,
            "submission_checklist_blocking_items": [],
            "submission_checklist_unclassified_blocking_items": [],
            "non_scientific_handoff_gaps": [],
            "closure_bundle_ready": True,
            "submission_minimal_manifest_path": str(
                gate_state.paper_root / "submission_minimal" / "submission_manifest.json"
            ),
            "submission_minimal_present": True,
            "submission_minimal_docx_present": True,
            "submission_minimal_pdf_present": True,
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "study_delivery_manifest_path": None,
            "study_delivery_current_package_root": None,
            "study_delivery_current_package_zip": None,
            "study_delivery_missing_source_paths": [],
            "draft_handoff_delivery_required": False,
            "draft_handoff_delivery_status": "current",
            "draft_handoff_delivery_manifest_path": None,
            "draft_handoff_current_package_root": None,
            "draft_handoff_current_package_zip": None,
            "paper_line_open_supplementary_count": 0,
            "paper_line_recommended_action": "continue_per_gate",
            "paper_line_blocking_reasons": [],
            "active_manuscript_figure_count": 5,
            "submission_grade_min_active_figures": 4,
            "prebundle_display_floor_pending": False,
            "prebundle_display_floor_gap": None,
            "prebundle_display_advisories": [],
            "medical_publication_surface_status": "clear",
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "bundle-stage work is unlocked and can proceed on the current line",
            "conclusion": "bundle-stage work is unlocked and can proceed on the current line",
            "controller_note": "The controller does not decide scientific publishability by itself.",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "Publication gate is clear and the current line can continue.",
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    latest_eval_path = (
        tmp_path
        / "studies"
        / "002-early-residual-risk"
        / "artifacts"
        / "publication_eval"
        / "latest.json"
    )
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert payload["emitted_at"] == "2026-04-18T18:12:13+00:00"
    assert payload["verdict"]["overall_verdict"] == "promising"
    assert payload["recommended_actions"][0]["action_type"] == "bounded_analysis"
    assert payload["runtime_context_refs"]["main_result_ref"] == str(
        quest_root / "artifacts" / "results" / "main_result.json"
    )
def test_run_controller_prefers_finalize_route_when_bundle_stage_is_ready_alongside_main_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=True,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F2", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F3", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F4", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
            ],
        },
    )
    main_result_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    bundle_manifest_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "allow_write": False,
            "blockers": [],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(bundle_manifest_path, (2, 2))
    os.utime(surface_report_path, (3, 3))
    os.utime(gate_report_path, (4, 4))

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["supervisor_phase"] == "bundle_stage_ready"
    assert result["current_required_action"] == "continue_bundle_stage"
    latest_eval_path = (
        tmp_path
        / "studies"
        / "002-early-residual-risk"
        / "artifacts"
        / "publication_eval"
        / "latest.json"
    )
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert payload["recommended_actions"][0]["action_type"] == "continue_same_line"
    assert payload["recommended_actions"][0]["route_target"] == "finalize"
def test_run_controller_materializes_stale_study_delivery_notice_when_apply_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "missing_source_paths": [
                "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
            ],
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: calls.append(kwargs)
        or {
            "status": "stale_source_missing",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert len(calls) == 1
    assert calls[0]["stale_reason"] == "current_submission_source_missing"
    assert calls[0]["missing_source_paths"] == [
        "/tmp/runtime/quests/002/paper/submission_minimal/submission_manifest.json",
    ]
    assert result["study_delivery_stale_sync"]["status"] == "stale_source_missing"
def test_run_controller_resyncs_delivery_when_only_current_package_projection_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_projection_missing",
                "stale_reason": "delivery_projection_missing",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }
def test_run_controller_unlocks_write_after_main_result_stale_delivery_resync(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=True,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    main_result_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_study_delivery_mirror"],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(gate_report_path, (2, 2))

    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_projection_missing",
                "stale_reason": "delivery_projection_missing",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["supervisor_phase"] == "bundle_stage_ready"
    assert result["current_required_action"] == "continue_bundle_stage"
def test_run_controller_resyncs_delivery_when_authority_package_changes_without_root_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_source_changed",
                "stale_reason": "delivery_manifest_source_changed",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("source-changed should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }
def test_run_controller_resyncs_delivery_when_authority_package_source_mismatch_is_reported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "stale_source_mismatch",
                "stale_reason": "delivery_manifest_source_mismatch",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
            {
                "applicable": True,
                "status": "current",
                "stale_reason": None,
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "missing_source_paths": [],
            },
        ]
    )
    sync_calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": next(describe_calls),
    )

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("source-mismatch should use sync_study_delivery")),
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert result["status"] == "clear"
    assert result["study_delivery_stale_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }
