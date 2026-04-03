from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(
    tmp_path: Path,
    *,
    include_submission_minimal: bool,
    manuscript_files: dict[str, str] | None = None,
) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"

    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "002-early-residual-risk",
            "status": "running",
            "active_run_id": "run-1",
        },
    )
    dump_json(
        worktree_root / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(worktree_root),
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
    dump_json(
        worktree_root / "paper" / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    if include_submission_minimal:
        dump_json(
            worktree_root / "paper" / "submission_minimal" / "submission_manifest.json",
            {
                "schema_version": 1,
                "publication_profile": "general_medical_journal",
                "manuscript": {
                    "docx_path": "paper/submission_minimal/manuscript.docx",
                    "pdf_path": "paper/submission_minimal/paper.pdf",
                },
            },
        )
        (worktree_root / "paper" / "submission_minimal" / "manuscript.docx").write_text("docx", encoding="utf-8")
        (worktree_root / "paper" / "submission_minimal" / "paper.pdf").write_text("%PDF", encoding="utf-8")
    if manuscript_files:
        for relpath, body in manuscript_files.items():
            target = worktree_root / "paper" / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    return quest_root


def test_build_gate_report_exposes_submission_minimal_status_when_present(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.publication_gate")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, include_submission_minimal=True)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"].endswith("paper/submission_minimal/submission_manifest.json")
    assert report["submission_minimal_present"] is True
    assert report["submission_minimal_docx_present"] is True
    assert report["submission_minimal_pdf_present"] is True


def test_build_gate_report_marks_submission_minimal_missing_when_absent(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.publication_gate")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["paper_bundle_manifest_path"].endswith("paper/paper_bundle_manifest.json")
    assert report["submission_minimal_manifest_path"] is None
    assert report["submission_minimal_present"] is False
    assert report["submission_minimal_docx_present"] is False
    assert report["submission_minimal_pdf_present"] is False


def test_build_gate_report_blocks_for_forbidden_manuscript_terminology(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "build/review_manuscript.md": "Methods: we analyzed the locked v2026-03-31 dataset.\n",
            "submission_minimal/tables/Table1.md": "The paper-facing mainline remained unchanged.\n",
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terminology" in report["blockers"]
    violations = report["manuscript_terminology_violations"]
    assert len(violations) >= 2
    assert any(item["path"].endswith("build/review_manuscript.md") for item in violations)
    assert any(item["path"].endswith("submission_minimal/tables/Table1.md") for item in violations)
    assert any("locked v2026-03-31" in item["match"] for item in violations)
    assert any("paper-facing" in item["match"] for item in violations)


def test_run_controller_enqueues_message_when_blocked(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.publication_gate")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "publishability gate" in queue["pending"][0]["content"]


def test_build_gate_report_keeps_blocker_logic_in_controller_after_adapter_patch(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.publication_gate")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    monkeypatch.setattr(
        module.quest_state,
        "resolve_active_stdout_path",
        lambda *, quest_root, runtime_state: quest_root / ".ds" / "runs" / "run-1" / "stdout.jsonl",
    )
    monkeypatch.setattr(module.quest_state, "read_recent_stdout_lines", lambda stdout_path: ["route -> write"])
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
    assert "active_run_drifting_into_write_without_gate_approval" in report["blockers"]
    assert "missing_required_non_scalar_deliverables" not in report["blockers"]


def test_write_gate_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

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

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "publishability_gate"
    assert seen["timestamp"] == "2026-04-03T04:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
