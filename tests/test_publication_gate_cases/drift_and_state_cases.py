from __future__ import annotations

from tests.test_publication_gate_cases import shared as _shared

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
def test_build_gate_report_exposes_authority_handshake_signatures_and_gate_fingerprint(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        include_current_medical_publication_surface_report=True,
    )
    paper_root = quest_root / "paper"
    from med_autoscience.controllers.submission_minimal.authority import describe_submission_minimal_authority

    authority = describe_submission_minimal_authority(paper_root=paper_root)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["submission_minimal_authority_status"] == "current"
    assert report["submission_minimal_evaluated_source_signature"] == authority["source_signature"]
    assert report["submission_minimal_authority_source_signature"] == authority["source_signature"]
    assert report["authority_source_signature"] == authority["source_signature"]
    assert report["gate_fingerprint"].startswith("publication-gate::")
    assert "stale_submission_minimal_authority" not in report["blockers"]
    assert all(
        item.get("blocker") != "stale_submission_minimal_authority"
        for item in report["blocking_artifact_refs"]
    )


def test_build_gate_report_includes_blocking_artifact_refs_for_stale_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        include_current_medical_publication_surface_report=True,
    )
    paper_root = quest_root / "paper"
    manifest_path = tmp_path / "studies" / "002-early-residual-risk" / "submission" / "submission_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_signature"] = "stale-source-signature"
    manifest["source_contract"] = {"source_signature": "stale-source-signature"}
    dump_json(manifest_path, manifest)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "stale_submission_minimal_authority" in report["blockers"]
    assert report["submission_minimal_authority_source_signature"] == "stale-source-signature"
    assert report["submission_minimal_evaluated_source_signature"] != "stale-source-signature"
    assert any(
        item.get("blocker") == "stale_submission_minimal_authority"
        and item.get("artifact_role") == "submission_minimal_authority"
        and item.get("stale_reason") == "submission_source_signature_mismatch"
        and str(item.get("artifact_path") or "").endswith("submission_manifest.json")
        for item in report["blocking_artifact_refs"]
    )
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
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_root": str(projected_paper_root),
        },
    )

    submission_manifest_path = projected_paper_root / "submission_minimal" / "submission_manifest.json"
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["manuscript"]["source_markdown_path"] = "paper/submission_minimal/manuscript_submission.md"
    dump_json(submission_manifest_path, payload)
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
        module.discovery_and_drift,
        "build_submission_manuscript_surface_qc",
        fake_build_submission_manuscript_surface_qc,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"] == str(projected_paper_root / "paper_bundle_manifest.json")
    assert captured["source_markdown_path"] == projected_paper_root / "submission_minimal" / "manuscript_submission.md"
    assert captured["docx_path"] == projected_paper_root / "submission_minimal" / "manuscript.docx"
    assert captured["pdf_path"] == projected_paper_root / "submission_minimal" / "paper.pdf"
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
    assert state.latest_gate["status"] == "clear"
    assert state.latest_gate["controller_stage_note"] == "older parseable report"
def test_build_gate_report_supports_finalize_only_paper_bundle_without_main_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    bypass_submission_surface_qc(monkeypatch)
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


def test_run_controller_syncs_missing_draft_handoff_and_rebuilds_current_state(
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
            "blocking_items": [{"key": "placeholder_heavy_branch_local_draft"}],
            "handoff_ready": True,
        },
    )
    draft_handoff_deliveries = iter(
        [
            {
                "applicable": True,
                "status": "missing",
                "delivery_manifest_path": None,
            },
            {
                "applicable": True,
                "status": "current",
                "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            },
        ]
    )
    state_build_roots: list[Path] = []
    sync_calls: list[tuple[Path, str, str]] = []
    real_build_gate_state = module.supervisor_and_cli.build_gate_state

    def tracking_build_gate_state(root: Path):
        state_build_roots.append(root)
        return real_build_gate_state(root)

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
    ) -> dict[str, object]:
        sync_calls.append((paper_root, stage, publication_profile))
        return {"stage": stage, "publication_profile": publication_profile}

    monkeypatch.setattr(module.supervisor_and_cli, "build_gate_state", tracking_build_gate_state)
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: next(draft_handoff_deliveries),
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": False,
            "status": "not_applicable",
        },
    )
    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert sync_calls == [(quest_root / "paper", "draft_handoff", "general_medical_journal")]
    assert state_build_roots == [quest_root, quest_root]
    assert result["draft_handoff_delivery_required"] is True
    assert result["draft_handoff_delivery_status"] == "current"
    assert result["draft_handoff_delivery_manifest_path"] == (
        "/tmp/studies/002/manuscript/delivery_manifest.json"
    )
    assert result["draft_handoff_delivery_sync"] == {
        "stage": "draft_handoff",
        "publication_profile": "general_medical_journal",
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
def test_build_gate_state_uses_projected_paper_root_when_bundle_manifest_is_projected(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == projected_paper_root.resolve()


def test_build_gate_state_uses_newer_bound_study_paper_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "003-paper"
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    study_root = workspace_root / "studies" / "003-paper"
    study_paper_root = study_root / "paper"
    projected_paper_root = quest_root / "paper"

    dump_json(quest_root / ".ds" / "runtime_state.json", {"quest_id": "003-paper", "status": "stopped"})
    dump_json(runtime_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    dump_json(projected_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "paper_root": str(runtime_paper_root.resolve()),
        },
    )
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 003-paper\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: 003-paper\n", encoding="utf-8")
    dump_json(study_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    dump_json(study_paper_root / "submission_minimal" / "submission_manifest.json", {"schema_version": 1})
    newer_time = (runtime_paper_root / "paper_bundle_manifest.json").stat().st_mtime + 60
    os.utime(study_paper_root / "paper_bundle_manifest.json", (newer_time, newer_time))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == study_paper_root.resolve()
    assert state.study_root == study_root.resolve()
    assert state.paper_bundle_manifest_path == study_paper_root.resolve() / "paper_bundle_manifest.json"
    assert state.submission_minimal_manifest_path == study_paper_root.resolve() / "submission_minimal" / "submission_manifest.json"


def test_build_gate_state_uses_projected_paper_root_when_no_main_result_exists(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    projected_paper_root = quest_root / "paper"
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "paper_branch": "paper/main",
        },
    )
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"
    projected_stat = projected_manifest.stat()
    os.utime(projected_manifest, (projected_stat.st_atime, projected_stat.st_mtime + 60))

    state = module.build_gate_state(quest_root)

    assert state.paper_root == projected_paper_root.resolve()
def test_build_gate_state_uses_projected_bundle_when_projected_line_state_switches_to_analysis_slice(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
    )
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    projected_manifest = projected_paper_root / "paper_bundle_manifest.json"

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
    assert state.paper_root == projected_paper_root.resolve()
    assert state.submission_minimal_manifest_path == projected_paper_root / "submission_minimal" / "submission_manifest.json"
    assert state.submission_minimal_docx_present is True
    assert state.submission_minimal_pdf_present is True
