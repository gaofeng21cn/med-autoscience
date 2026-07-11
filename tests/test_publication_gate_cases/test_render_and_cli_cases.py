from __future__ import annotations

from tests.test_publication_gate_cases.shared import dump_json, importlib, json, make_quest, write_text

def test_build_gate_report_uses_projected_paper_surface_over_legacy_runtime_worktree(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    legacy_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    idea_worktree_root = quest_root / ".ds" / "worktrees" / "idea-run-1"

    dump_json(
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(idea_worktree_root),
            "metric_contract": {
                "required_non_scalar_deliverables": [],
            },
            "metrics_summary": {
                "roc_auc": 0.81,
            },
            "baseline_comparisons": {"items": []},
            "results_summary": "summary",
            "conclusion": "conclusion",
        },
    )
    dump_json(
        legacy_paper_root / "paper_line_state.json",
        {
            "paper_root": str(legacy_paper_root.resolve()),
            "paper_branch": "paper/run-1",
        },
    )
    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/stale-mirror",
            "compile_report_path": "paper/build/compile_report.json",
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "paper_branch": "paper/stale-mirror",
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:33Z.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_paper_root / "paper_bundle_manifest.json"
    assert report["paper_root"] == str(projected_paper_root.resolve())
    assert report["medical_publication_surface_status"] == "clear"
    assert "medical_publication_surface_blocked" not in report["blockers"]
def test_build_gate_report_allows_clinical_cohort_wording_without_internal_labels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "draft.md": (
                "We analyzed the institutional first-surgery NF-PitNET cohort and "
                "ascertained outcomes through June 30, 2024.\n"
            )
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "forbidden_manuscript_terminology" not in report["blockers"]
    assert report["manuscript_terminology_violations"] == []
def test_run_controller_enqueues_message_when_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is False
    assert result["intervention_handoff"]["runtime_owner"] == "one-person-lab"
    assert result["intervention_handoff"]["message_body_included"] is False
    assert not (quest_root / ".ds" / "user_message_queue.json").exists()


def test_run_controller_dry_run_does_not_write_gate_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    result = module.run_controller(
        quest_root=quest_root,
        apply=False,
    )

    assert result["status"] == "blocked"
    assert result["report_json"] is None
    assert result["report_markdown"] is None
    assert result["gate_kind"] == "publishability_control"
    assert not (quest_root / "artifacts" / "reports" / "publishability_gate").exists()


def test_build_gate_report_keeps_blocker_logic_in_controller_after_adapter_patch(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    monkeypatch.setattr(module.paper_artifacts, "resolve_artifact_manifest_from_main_result", lambda main_result: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_paper_bundle_manifest", lambda quest_root: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_submission_minimal_manifest", lambda paper_bundle_manifest_path: None)
    monkeypatch.setattr(
        module.paper_artifacts,
        "resolve_submission_minimal_output_paths",
        lambda *, paper_bundle_manifest_path, submission_minimal_manifest: (None, None),
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert "missing_required_non_scalar_deliverables" not in report["blockers"]


def test_write_gate_files_materializes_domain_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
    report = {
        "generated_at": "2026-04-03T04:00:00+00:00",
        "quest_id": quest_root.name,
        "run_id": "run-1",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "stop",
        "blockers": ["missing_post_main_publishability_gate"],
        "missing_non_scalar_deliverables": [],
        "paper_bundle_manifest_path": None,
        "submission_minimal_manifest_path": None,
        "submission_minimal_present": False,
        "submission_minimal_docx_present": False,
        "submission_minimal_pdf_present": False,
        "headline_metrics": {},
        "results_summary": "summary",
        "conclusion": "conclusion",
        "controller_note": "note",
    }

    json_path, md_path = module.write_gate_files(quest_root, report)

    report_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    assert json_path == report_root / "2026-04-03T040000Z.json"
    assert md_path == report_root / "2026-04-03T040000Z.md"
    assert json.loads(json_path.read_text(encoding="utf-8")) == report
    assert (report_root / "latest.json").read_text(encoding="utf-8") == json_path.read_text(encoding="utf-8")
    assert (report_root / "latest.md").read_text(encoding="utf-8") == md_path.read_text(encoding="utf-8")
