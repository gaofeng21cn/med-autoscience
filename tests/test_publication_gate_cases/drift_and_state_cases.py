from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_build_gate_report_exposes_submission_minimal_status_when_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_root"].endswith("/paper")
    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"].endswith("paper/submission_minimal/submission_manifest.json")
    assert report["paper_bundle_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_present"] is True
    assert report["submission_minimal_docx_present"] is True
    assert report["submission_minimal_pdf_present"] is True
def test_build_gate_report_uses_authoritative_source_markdown_path_for_submission_surface_qc(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        include_submission_authority_inputs=False,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "manuscript_status": "main_text",
                }
            ],
        },
    )
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    worktree_paper_root = worktree_root / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        worktree_paper_root / "paper_bundle_manifest.json",
        projected_paper_root / "paper_bundle_manifest.json",
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_root": str(worktree_paper_root),
        },
    )

    submission_manifest_path = worktree_paper_root / "submission_minimal" / "submission_manifest.json"
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["manuscript"]["source_markdown_path"] = "paper/submission_minimal/manuscript_submission.md"
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(worktree_paper_root / "submission_minimal" / "manuscript_submission.md", "# authoritative\n")
    write_text(projected_paper_root / "submission_minimal" / "manuscript_submission.md", "# projected copy\n")

    captured: dict[str, Path] = {}

    def fake_build_submission_manuscript_surface_qc(
        *,
        publication_profile: str,
        source_markdown_path: Path,
        docx_path: Path,
        pdf_path: Path,
        expected_main_figure_count: int,
    ) -> dict[str, object]:
        captured["source_markdown_path"] = source_markdown_path
        captured["docx_path"] = docx_path
        captured["pdf_path"] = pdf_path
        assert publication_profile == "general_medical_journal"
        assert expected_main_figure_count == 1
        return {
            "qc_profile": "submission_manuscript_surface",
            "status": "pass",
            "failures": [],
        }

    monkeypatch.setattr(
        module.submission_minimal,
        "build_submission_manuscript_surface_qc",
        fake_build_submission_manuscript_surface_qc,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"] == str(projected_paper_root / "paper_bundle_manifest.json")
    assert captured["source_markdown_path"] == worktree_paper_root / "submission_minimal" / "manuscript_submission.md"
    assert captured["docx_path"] == worktree_paper_root / "submission_minimal" / "manuscript.docx"
    assert captured["pdf_path"] == worktree_paper_root / "submission_minimal" / "paper.pdf"
def test_build_gate_report_marks_submission_minimal_missing_when_absent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"] is None
    assert report["submission_minimal_present"] is False
    assert report["submission_minimal_docx_present"] is False
    assert report["submission_minimal_pdf_present"] is False
def test_build_gate_report_reports_missing_journal_requirements_for_primary_target(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_primary_target(paper_root)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["primary_journal_target"]["journal_slug"] == "rheumatology-international"
    assert report["journal_requirements_status"] == "missing"
    assert "missing_journal_requirements" in report["blockers"]
def test_build_gate_report_reports_missing_journal_package_when_requirements_exist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    write_primary_target(paper_root)
    write_journal_requirements_snapshot(study_root)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["journal_requirements_status"] == "resolved"
    assert report["journal_package_status"] == "missing"
    assert "missing_journal_package" in report["blockers"]
def test_build_gate_state_uses_latest_parseable_gate_report_when_newer_report_is_malformed(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    reports_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    older_report = reports_root / "2026-04-17T000000Z.json"
    newer_report = reports_root / "2026-04-17T000001Z.json"

    dump_json(
        older_report,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "controller_stage_note": "older parseable report",
        },
    )
    newer_report.parent.mkdir(parents=True, exist_ok=True)
    newer_report.write_text(
        '{"schema_version": 1, "status": "clear"}\n{"schema_version": 1, "status": "blocked"}\n',
        encoding="utf-8",
    )
    os.utime(older_report, (1, 1))
    os.utime(newer_report, (2, 2))

    state = module.build_gate_state(quest_root)

    assert state.latest_gate_path == older_report
    assert state.latest_gate == {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-04-17T00:00:00+00:00",
        "status": "clear",
        "controller_stage_note": "older parseable report",
    }
def test_build_gate_report_supports_finalize_only_paper_bundle_without_main_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["paper_root"].endswith("/paper")
    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"].endswith("paper/submission_minimal/submission_manifest.json")
    assert report["paper_bundle_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_manifest_path"].startswith(report["paper_root"])
    assert report["submission_minimal_present"] is True
    assert report["submission_minimal_docx_present"] is True
    assert report["submission_minimal_pdf_present"] is True
    assert report["run_id"] is None
    assert report["headline_metrics"] == {}
    assert report["results_summary"] == "compile report summary"
    assert report["supervisor_phase"] == "bundle_stage_ready"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["phase_owner"] == "publication_gate"
def test_build_gate_report_clears_stale_paper_line_blockers_when_bundle_stage_reopens(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        paper_line_state={
            "paper_root": str(
                (
                    tmp_path
                    / "runtime"
                    / "quests"
                    / "002-early-residual-risk"
                    / ".ds"
                    / "worktrees"
                    / "paper-run-1"
                    / "paper"
                ).resolve()
            ),
            "recommended_action": "branch_upstream_controller_contract_durability_fix",
            "blocking_reasons": [
                "The latest hard-control message supersedes the earlier reopen-write snapshot."
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)
    markdown = module.render_gate_markdown(report)

    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["current_required_action"] == "continue_bundle_stage"
    assert report["paper_line_recommended_action"] == "continue_per_gate"
    assert report["paper_line_blocking_reasons"] == []
    assert "Paper-Line Scientific Blockers" not in markdown
    assert "branch_upstream_controller_contract_durability_fix" not in markdown
def test_build_gate_report_blocks_finalize_only_bundle_without_current_surface_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
def test_build_gate_report_allows_handoff_ready_bundle_with_non_scientific_pageproof_gap(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_draft_bundle_not_submission_ready",
            "checks": [
                {"key": "claim_evidence_alignment", "status": "pass"},
                {"key": "proofing_present", "status": "pass"},
            ],
            "blocking_items": [
                {
                    "key": "full_manuscript_pageproof",
                    "notes": "Rendered page proof is still unavailable.",
                }
            ],
            "handoff_ready": True,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "paper_bundle"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["submission_minimal_present"] is False
    assert report["submission_checklist_handoff_ready"] is True
    assert report["non_scientific_handoff_gaps"] == ["full_manuscript_pageproof"]
    assert report["blockers"] == []
    assert report["supervisor_phase"] == "bundle_stage_ready"
    assert report["current_required_action"] == "continue_bundle_stage"
def test_build_gate_report_keeps_handoff_ready_bundle_blocked_for_unknown_submission_gap(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "draft_bundle_with_unresolved_method_gap",
            "blocking_items": [
                {
                    "key": "methods_completeness",
                    "notes": "Methods section still misses a required implementation detail.",
                }
            ],
            "handoff_ready": True,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["submission_checklist_handoff_ready"] is True
    assert report["submission_checklist_unclassified_blocking_items"] == ["methods_completeness"]
    assert "submission_checklist_contains_unclassified_blocking_items" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
def test_build_gate_report_marks_draft_handoff_sync_missing_when_bundle_is_handoff_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_slice_handoff_not_submission_ready",
            "blocking_items": [
                {
                    "key": "placeholder_heavy_branch_local_draft",
                    "notes": "Current draft is still placeholder-heavy.",
                }
            ],
            "handoff_ready": True,
        },
    )
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": True,
            "status": "missing",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "missing_source_paths": [],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["draft_handoff_delivery_required"] is True
    assert report["draft_handoff_delivery_status"] == "missing"
    assert report["draft_handoff_delivery_manifest_path"] is None
def test_run_controller_syncs_draft_handoff_surface_when_missing(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        submission_checklist={
            "overall_status": "display_materialized_slice_handoff_not_submission_ready",
            "blocking_items": [
                {
                    "key": "placeholder_heavy_branch_local_draft",
                    "notes": "Current draft is still placeholder-heavy.",
                }
            ],
            "handoff_ready": True,
        },
    )
    describe_calls = iter(
        [
            {
                "applicable": True,
                "status": "missing",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "delivery_manifest_path": None,
            },
            {
                "applicable": True,
                "status": "current",
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            },
        ]
    )
    sync_calls: list[tuple[str, str]] = []

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: next(describe_calls),
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "missing_source_paths": [],
        },
    )

    def fake_sync(*, paper_root: Path, stage: str, publication_profile: str = "general_medical_journal", promote_to_final: bool = False) -> dict[str, object]:
        sync_calls.append((stage, publication_profile))
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {
                "current_package_root": "/tmp/studies/002/manuscript/current_package",
                "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            },
        }

    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [("draft_handoff", "general_medical_journal")]
    assert result["draft_handoff_delivery_status"] == "current"
    assert result["draft_handoff_delivery_sync"] == {
        "stage": "draft_handoff",
        "publication_profile": "general_medical_journal",
        "targets": {
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
        },
    }
def test_build_gate_report_blocks_finalize_only_bundle_when_surface_report_is_stale(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    report_path = quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    bundle_manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    )
    os.utime(report_path, (bundle_manifest_path.stat().st_mtime - 10, bundle_manifest_path.stat().st_mtime - 10))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
def test_build_gate_report_ignores_stale_blocked_surface_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
    )
    report_path = quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    bundle_manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    )
    os.utime(report_path, (bundle_manifest_path.stat().st_mtime - 10, bundle_manifest_path.stat().st_mtime - 10))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_current_medical_publication_surface_report" in report["blockers"]
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert "claim_evidence_consistency_failed" not in report["blockers"]
    assert report["medical_publication_surface_current"] is False
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None
def test_build_gate_report_keeps_bundle_stage_when_only_submission_minimal_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["blockers"] == ["missing_submission_minimal"]
    assert report["supervisor_phase"] == "bundle_stage_blocked"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "complete_bundle_stage"
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None
    assert report["controller_stage_note"] == "bundle-stage blockers are now on the critical path for this paper line"
def test_build_gate_report_blocks_bundle_when_paper_line_requires_supplementary_completion(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        paper_line_state={
            "paper_root": str(
                (
                    tmp_path
                    / "runtime"
                    / "quests"
                    / "002-early-residual-risk"
                    / ".ds"
                    / "worktrees"
                    / "paper-run-1"
                    / "paper"
                ).resolve()
            ),
            "open_supplementary_count": 2,
            "recommended_action": "complete_required_supplementary",
            "blocking_reasons": ["paper-facing supplementary slices are still pending"],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "paper_line_required_supplementary_pending" in report["blockers"]
    assert report["paper_line_open_supplementary_count"] == 2
    assert report["paper_line_recommended_action"] == "complete_required_supplementary"
    assert report["paper_line_blocking_reasons"] == ["paper-facing supplementary slices are still pending"]
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
def test_build_gate_report_blocks_bundle_when_active_figure_floor_is_unmet(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F2", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {"figure_id": "F3", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
                {
                    "figure_id": "F4",
                    "paper_role": "appendix_legacy_inactive",
                    "manuscript_status": "appendix_context_only",
                },
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "submission_grade_active_figure_floor_unmet" in report["blockers"]
    assert report["active_manuscript_figure_count"] == 3
    assert report["submission_grade_min_active_figures"] == 4
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
def test_build_gate_report_surfaces_prebundle_figure_floor_pending_from_main_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=True,
        runtime_status="running",
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["allow_write"] is False
    assert report["active_manuscript_figure_count"] == 1
    assert report["prebundle_display_floor_pending"] is True
    assert report["prebundle_display_floor_gap"] == 3
    assert report["prebundle_display_advisories"] == ["submission_grade_active_figure_floor_unmet"]
def test_build_gate_report_unlocks_write_stage_when_latest_clear_gate_is_current(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=True,
        runtime_status="running",
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": "2.1.0",
            "figures": [
                {"figure_id": "F1", "paper_role": "main_text", "manuscript_status": "locked_main_text_evidence"},
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
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
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
    os.utime(surface_report_path, (2, 2))
    os.utime(gate_report_path, (3, 3))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["anchor_kind"] == "main_result"
    assert report["status"] == "clear"
    assert report["allow_write"] is True
    assert report["latest_gate_path"] == str(gate_report_path)
    assert report["supervisor_phase"] == "write_stage_ready"
    assert report["bundle_tasks_downstream_only"] is False
    assert report["current_required_action"] == "continue_write_stage"
    assert report["prebundle_display_floor_pending"] is True
    assert report["prebundle_display_floor_gap"] == 3
    assert report["prebundle_display_advisories"] == ["submission_grade_active_figure_floor_unmet"]
def test_build_gate_state_prefers_authoritative_worktree_paper_root_when_bundle_manifest_is_projected(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(worktree_paper_root / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == worktree_paper_root.resolve()
def test_build_gate_state_prefers_paper_line_authority_root_when_no_main_result_exists(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(worktree_paper_root / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(worktree_paper_root.resolve()),
            "paper_branch": "paper/main",
        },
    )
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == worktree_paper_root.resolve()
def test_build_gate_state_prefers_paper_line_authority_root_over_run_worktree_paper(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    paper_worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    run_worktree_root = quest_root / ".ds" / "worktrees" / "run-main-1"
    run_result_path = run_worktree_root / "experiments" / "main" / "run-1" / "RESULT.json"
    run_worktree_paper_root = run_worktree_root / "paper"

    dump_json(
        run_result_path,
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(run_worktree_root.resolve()),
            "metric_contract": {
                "required_non_scalar_deliverables": [],
            },
            "metrics_summary": {
                "roc_auc": 0.81,
                "average_precision": 0.45,
                "brier_score": 0.11,
                "calibration_intercept": 0.02,
                "calibration_slope": 1.01,
            },
            "baseline_comparisons": {"items": []},
            "results_summary": "summary",
            "conclusion": "conclusion",
        },
    )
    (paper_worktree_root / "experiments" / "main" / "run-1" / "RESULT.json").unlink()
    (run_worktree_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (run_worktree_paper_root / "draft.md").write_text("paper-facing placeholder", encoding="utf-8")

    projected_paper_root = quest_root / "paper"
    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paper_worktree_root / "paper" / "paper_bundle_manifest.json", projected_paper_root / "paper_bundle_manifest.json")
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str((paper_worktree_root / "paper").resolve()),
            "paper_branch": "paper/main",
        },
    )

    state = module.build_gate_state(quest_root)

    assert state.paper_root == (paper_worktree_root / "paper").resolve()
def test_build_gate_state_prefers_bundle_authority_worktree_when_projected_line_state_switches_to_analysis_slice(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"

    projected_paper_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(authoritative_paper_root / "paper_bundle_manifest.json", projected_manifest)
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(analysis_paper_root.resolve()),
            "paper_branch": "analysis/paper-line-paper-main-outline-001-run/analysis-12bdab30-authority-root-delivery-alignment",
        },
    )
    (analysis_paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (analysis_paper_root / "draft.md").write_text("analysis slice mirror", encoding="utf-8")
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_bundle_manifest_path == projected_manifest
    assert state.paper_root == authoritative_paper_root.resolve()
    assert state.submission_minimal_manifest_path == authoritative_paper_root / "submission_minimal" / "submission_manifest.json"
    assert state.submission_minimal_docx_present is True
    assert state.submission_minimal_pdf_present is True


def test_build_gate_report_classifies_science_reporting_bundle_and_human_metadata_blockers(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_unmanaged_submission_surface=True,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
        medical_publication_surface_report={
            "blockers": [
                "methods_completeness_incomplete",
                "statistical_reporting_incomplete",
                "table_figure_claim_map_missing_or_incomplete",
                "clinical_actionability_incomplete",
            ],
            "structured_reporting_checklist": {
                "methods_completeness": {"status": "blocked", "missing_items": ["validation"]},
                "clinical_actionability": {"status": "blocked", "missing_items": ["treatment_gap"]},
            },
        },
        submission_checklist={
            "handoff_ready": True,
            "blocking_items": [
                {"id": "author_metadata"},
                {"id": "ethics_statement"},
                {"id": "funding_statement"},
                {"id": "conflict_of_interest_statement"},
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert "submission_checklist_contains_unclassified_blocking_items" not in report["blockers"]
    science_reporting_blockers = report["blocker_taxonomy"]["science_reporting_blockers"]
    for blocker in [
        "medical_publication_surface_blocked",
        "methods_completeness_incomplete",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "clinical_actionability_incomplete",
    ]:
        assert blocker in science_reporting_blockers
    assert "unmanaged_submission_surface_present" in report["blocker_taxonomy"]["bundle_package_blockers"]
    assert report["blocker_taxonomy"]["human_metadata_admin_todos"] == [
        "author_metadata",
        "ethics_statement",
        "funding_statement",
        "conflict_of_interest_statement",
    ]
    assert report["non_scientific_handoff_gaps"] == [
        "author_metadata",
        "ethics_statement",
        "funding_statement",
        "conflict_of_interest_statement",
    ]
    assert report["publication_reporting_checklist"]["clinical_actionability"]["missing_items"] == ["treatment_gap"]
