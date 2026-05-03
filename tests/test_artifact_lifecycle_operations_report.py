from __future__ import annotations

import importlib
from pathlib import Path


def _write(path: Path, text: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_lifecycle_operations_report_summarizes_roles_sources_and_projection_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md")
    _write(study_root / "manuscript" / "current_package" / "manuscript.docx")
    _write(study_root / "manuscript" / "current_package.zip", "zip\n")
    _write(study_root / "paper" / "submission_minimal" / "paper.pdf")
    _write(study_root / "artifacts" / "runtime" / "latest.json", "{}\n")
    _write(workspace_root / "datasets" / "release" / "dataset_manifest.yaml")
    _write(workspace_root / ".ds" / "runs" / "run-1" / "stdout.jsonl")

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])

    assert report["surface"] == "control_plane_lifecycle_report"
    assert report["scan_policy"]["deep_scan_enabled"] is False
    assert report["scan_policy"]["artifact_listing"] == "bounded"
    assert report["mutation_policy"]["read_only"] is True
    assert report["mutation_policy"]["physical_cleanup_performed"] is False
    assert report["summary"]["role_counts"]["canonical_source"] == 1
    assert report["retention_plan"]["summary"]["action_counts"]["keep_online"] >= 1
    assert report["retention_plan"]["summary"]["action_counts"]["regenerate_projection_then_remove_stale"] >= 1
    assert report["source_totals"]["delivery_projection"]["file_count"] >= 3
    assert report["source_totals"]["runtime"]["scan_mode"] == "statistical_only"
    study = report["workspaces"][0]["studies"][0]
    assert study["study_id"] == "001-risk"
    assert study["projection_surfaces"]["current_package"]["role"] == "derived_projection"
    assert study["projection_surfaces"]["submission_minimal"]["role"] == "human_handoff_mirror"
    assert study["projection_completeness"]["status"] == "complete"
    assert "missing_docx" not in study["projection_completeness"]["blockers"]
    assert "missing_pdf" not in study["projection_completeness"]["blockers"]
    assert "artifacts" not in report["workspaces"][0]
    assert report["workspaces"][0]["artifact_sample"]
    workspace_plan = report["workspaces"][0]["retention_plan"]
    assert workspace_plan["mutation_policy"]["physical_cleanup_performed"] is False
    assert workspace_plan["mutation_policy"]["allowed_physical_actions"] == ["delete-safe-cache"]
    assert workspace_plan["operation_listing"] == "bounded"
    assert "operations" not in workspace_plan
    projection_operations = [
        item
        for item in workspace_plan["operation_sample"]
        if item["retention_action"] == "regenerate_projection_then_remove_stale"
    ]
    assert projection_operations
    assert all(item["physical_delete_allowed"] is False for item in projection_operations)


def test_lifecycle_operations_report_default_uses_storage_audit_snapshot_without_deep_runtime_scan(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md")
    _write(study_root / "manuscript" / "current_package" / "manuscript.docx")
    _write(study_root / "manuscript" / "current_package.zip", "zip\n")
    _write(study_root / "paper" / "submission_minimal" / "paper.pdf")
    _write(workspace_root / "storage_audit" / "latest.json", '{"runtime": {"bytes": 12, "file_count": 2}}\n')
    _write(workspace_root / ".ds" / "runs" / "run-1" / "worktrees" / "nested" / "huge.bin", "runtime\n")

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    workspace = report["workspaces"][0]

    assert workspace["statistical_directories"][0]["scan_mode"] == "snapshot_reference"
    assert workspace["statistical_directories"][0]["source_snapshot"] == "storage_audit/latest.json"
    assert workspace["statistical_directories"][0]["file_count"] == 2
    assert workspace["statistical_directories"][0]["size_bytes"] == 12
    assert report["source_totals"]["runtime"]["file_count"] == 2
    assert workspace["retention_plan"]["summary"]["action_counts"]["keep_online"] >= 1


def test_lifecycle_operations_report_default_does_not_walk_nested_runtime_or_worktree_payloads(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source" / "manuscript_source.md")
    forbidden_files = [
        workspace_root / ".ds" / "worktrees" / "lane-a" / "nested" / "payload.bin",
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "quest-001"
        / "payload"
        / "huge.bin",
        workspace_root / "datasets" / "raw" / "release" / "nested" / "rows.csv",
    ]
    for path in forbidden_files:
        _write(path, "large\n")

    original_file_size = module._file_size
    touched_paths: list[Path] = []

    def recording_file_size(path: Path) -> int:
        touched_paths.append(path)
        return original_file_size(path)

    monkeypatch.setattr(module, "_file_size", recording_file_size)

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    touched_relative_paths = {path.relative_to(workspace_root).as_posix() for path in touched_paths}

    assert report["scan_policy"]["deep_scan_enabled"] is False
    assert "studies/001-risk/paper/source/manuscript_source.md" in touched_relative_paths
    assert "ops/med-deepscientist/runtime/quests/quest-001/payload/huge.bin" not in touched_relative_paths
    assert "datasets/raw/release/nested/rows.csv" not in touched_relative_paths
    assert ".ds/worktrees/lane-a/nested/payload.bin" not in touched_relative_paths
    source_totals = report["source_totals"]
    assert source_totals["runtime"]["scan_mode"] == "statistical_only"
    assert source_totals["dataset"]["scan_mode"] == "statistical_only"


def test_lifecycle_operations_report_deep_scan_is_explicit_and_bounded(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md")
    _write(workspace_root / ".ds" / "runs" / "run-1" / "a.txt")
    _write(workspace_root / ".ds" / "runs" / "run-1" / "b.txt")

    report = module.run_lifecycle_operations_report(
        workspace_roots=[workspace_root],
        deep=True,
        max_files=1,
        max_seconds=10,
    )
    workspace = report["workspaces"][0]
    runtime_stats = workspace["statistical_directories"][0]

    assert report["scan_policy"]["deep_scan_enabled"] is True
    assert report["scan_policy"]["max_files"] == 1
    assert report["scan_policy"]["max_seconds"] == 10
    assert runtime_stats["scan_mode"] == "deep_statistical"
    assert runtime_stats["bounded"] is True
    assert runtime_stats["file_count"] == 1
    assert runtime_stats["truncated"] is True


def test_lifecycle_operations_report_deep_scan_walks_bounded_operational_payloads(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source" / "manuscript_source.md")
    _write(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001" / "a.txt")
    _write(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001" / "nested" / "b.txt")
    _write(workspace_root / "datasets" / "raw" / "release" / "nested" / "rows.csv")
    _write(workspace_root / "datasets" / "raw" / "release" / "nested" / "rows-2.csv")

    report = module.run_lifecycle_operations_report(
        workspace_roots=[workspace_root],
        deep=True,
        max_files=1,
        max_seconds=10,
    )
    workspace = report["workspaces"][0]
    stats_by_path = {
        item["workspace_relative_path"]: item
        for item in workspace["statistical_directories"]
    }

    assert stats_by_path["ops/med-deepscientist/runtime/quests"]["scan_mode"] == "deep_statistical"
    assert stats_by_path["ops/med-deepscientist/runtime/quests"]["file_count"] == 1
    assert stats_by_path["ops/med-deepscientist/runtime/quests"]["truncated"] is True
    assert stats_by_path["datasets/raw"]["scan_mode"] == "deep_statistical"
    assert stats_by_path["datasets/raw"]["file_count"] == 1
    assert stats_by_path["datasets/raw"]["truncated"] is True


def test_lifecycle_operations_report_marks_incomplete_projection_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md")
    _write(study_root / "manuscript" / "current_package" / "manuscript.docx")

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    study = report["workspaces"][0]["studies"][0]

    assert study["projection_completeness"]["status"] == "incomplete"
    assert "missing_submission_minimal" in study["projection_completeness"]["blockers"]
    assert "missing_pdf" in study["projection_completeness"]["blockers"]
    assert "missing_zip" in study["projection_completeness"]["blockers"]


def test_lifecycle_operations_report_markdown_is_renderable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source.md")

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    markdown = module.render_lifecycle_operations_report_markdown(report)

    assert "# Control Plane Lifecycle Report" in markdown
    assert "`001-risk`" in markdown
