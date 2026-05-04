from __future__ import annotations

import importlib
from pathlib import Path

from . import control_plane_fixtures as fixtures


def _write(path: Path, text: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _record_file_size_calls(module):
    original_file_size = module._file_size
    touched_paths: list[Path] = []

    def recording_file_size(path: Path) -> int:
        touched_paths.append(path)
        return original_file_size(path)

    return recording_file_size, touched_paths


def _touched_relative_paths(root: Path, touched_paths: list[Path]) -> set[str]:
    return {path.relative_to(root).as_posix() for path in touched_paths}


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
    assert report["retention_policy_catalog"]["report_default"] == {
        "read_only": True,
        "operation_listing": "bounded",
    }
    assert report["retention_policy_catalog"]["default_keep_online_roles"] == [
        "audit_log",
        "canonical_source",
        "data_release",
        "human_handoff_mirror",
    ]
    assert report["retention_policy_catalog"]["derived_projection_removal_marker"] == "regenerate-before-remove"
    assert report["retention_policy_catalog"]["live_runtime_rule"] == "audit-only"
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
    assert workspace_plan["retention_policy_catalog"]["physical_apply_allowlist"] == ["delete-safe-cache"]
    assert workspace_plan["operation_listing"] == "bounded"
    assert "operations" not in workspace_plan
    projection_operations = [
        item
        for item in workspace_plan["operation_sample"]
        if item["retention_action"] == "regenerate_projection_then_remove_stale"
    ]
    assert projection_operations
    assert all(item["physical_delete_allowed"] is False for item in projection_operations)
    assert {item["removal_marker"] for item in projection_operations} == {"regenerate-before-remove"}


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

    recording_file_size, touched_paths = _record_file_size_calls(module)
    monkeypatch.setattr(module, "_file_size", recording_file_size)

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    touched_relative_paths = _touched_relative_paths(workspace_root, touched_paths)

    assert report["scan_policy"]["deep_scan_enabled"] is False
    assert "studies/001-risk/paper/source/manuscript_source.md" in touched_relative_paths
    assert "ops/med-deepscientist/runtime/quests/quest-001/payload/huge.bin" not in touched_relative_paths
    assert "datasets/raw/release/nested/rows.csv" not in touched_relative_paths
    assert ".ds/worktrees/lane-a/nested/payload.bin" not in touched_relative_paths
    source_totals = report["source_totals"]
    assert source_totals["runtime"]["scan_mode"] == "statistical_only"
    assert source_totals["dataset"]["scan_mode"] == "statistical_only"


def test_lifecycle_operations_report_default_does_not_walk_nested_audit_payloads(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source" / "manuscript_source.md")
    audit_payload = (
        workspace_root
        / "studies"
        / "001-risk"
        / "artifacts"
        / "autonomy"
        / "ai_doctor_attempts"
        / "nested"
        / "attempt.json"
    )
    _write(audit_payload, "{}\n")

    original_file_size = module._file_size
    touched_paths: list[Path] = []

    def recording_file_size(path: Path) -> int:
        touched_paths.append(path)
        return original_file_size(path)

    monkeypatch.setattr(module, "_file_size", recording_file_size)

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    touched_relative_paths = _touched_relative_paths(workspace_root, touched_paths)

    assert "studies/001-risk/paper/source/manuscript_source.md" in touched_relative_paths
    assert "studies/001-risk/artifacts/autonomy/ai_doctor_attempts/nested/attempt.json" not in touched_relative_paths
    audit_stats = report["workspaces"][0]["statistical_directories"][0]
    assert audit_stats["workspace_relative_path"] == "studies/001-risk/artifacts/autonomy"
    assert audit_stats["source_bucket"] == "audit_log"
    assert audit_stats["role"] == "audit_log"
    assert audit_stats["scan_mode"] == "statistical_only"
    assert report["source_totals"]["audit_log"]["scan_mode"] == "statistical_only"


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


def test_lifecycle_operations_report_deep_classified_scan_uses_workspace_budget(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "a.txt")
    _write(workspace_root / "b.txt")
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source" / "manuscript_source.md")

    report = module.run_lifecycle_operations_report(
        workspace_roots=[workspace_root],
        deep=True,
        max_files=1,
        max_seconds=10,
    )
    workspace = report["workspaces"][0]

    assert workspace["classified_artifact_count"] == 1
    assert workspace["classified_scan_truncated"] is True


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


def test_lifecycle_operations_report_adds_compact_storage_budget_operational_summary(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md", "source\n")
    _write(study_root / "manuscript" / "current_package" / "manuscript.docx", "d" * 100)
    _write(study_root / "manuscript" / "current_package.zip", "z" * 50)
    _write(workspace_root / ".ds" / "runs" / "run-1" / "stdout.jsonl", "runtime\n")
    _write(workspace_root / "datasets" / "release" / "dataset_manifest.yaml", "dataset\n")
    _write(
        workspace_root / "storage_audit" / "latest.json",
        (
            '{"source_totals": {'
            '"runtime": {"bytes": 1200, "file_count": 12, "directory_count": 3}, '
            '"dataset": {"bytes": 300, "file_count": 3, "directory_count": 1}'
            "}}\n"
        ),
    )

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    summary = report["operational_summary"]

    assert summary["storage_budget"]["mode"] == "bounded_read_only"
    assert summary["storage_budget"]["total_bytes"] == report["summary"]["total_bytes"]
    assert summary["storage_budget"]["physical_cleanup_performed"] is False
    growth_by_bucket = {item["source_bucket"]: item for item in summary["top_growth_buckets"]}
    assert summary["top_growth_buckets"][0]["source_bucket"] == "runtime"
    assert summary["top_growth_buckets"][0]["bytes"] == 1200
    assert growth_by_bucket["dataset"]["bytes"] == 300
    assert growth_by_bucket["delivery_projection"]["bytes"] == 150
    blocked = {item["reason"]: item for item in summary["blocked_cleanup_reasons"]}
    assert blocked["canonical_regeneration_required_before_projection_removal"]["count"] == 2
    assert blocked["snapshot_reference_no_physical_cleanup_contract"]["count"] == 2
    assert blocked["canonical_regeneration_required_before_projection_removal"]["actions"] == [
        "regenerate_projection_then_remove_stale",
    ]
    projection_paths = {
        item["workspace_relative_path"]
        for item in summary["projection_regeneration_candidates"]
    }
    assert projection_paths == {
        "studies/001-risk/manuscript/current_package/manuscript.docx",
        "studies/001-risk/manuscript/current_package.zip",
    }
    assert all(
        item["canonical_regeneration_gate"]["status"] == "required_before_physical_removal"
        for item in summary["projection_regeneration_candidates"]
    )
    assert all(item["physical_delete_allowed"] is False for item in summary["projection_regeneration_candidates"])
    assert summary["restore_contract_gaps"] == []


def test_lifecycle_operations_report_markdown_includes_operational_summary(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write(study_root / "paper" / "source" / "manuscript_source.md", "source\n")
    _write(study_root / "manuscript" / "current_package" / "manuscript.docx", "docx\n")
    _write(workspace_root / ".ds" / "runs" / "run-1" / "stdout.jsonl", "runtime\n")
    _write(
        workspace_root / "storage_audit" / "latest.json",
        '{"runtime": {"bytes": 1200, "file_count": 12, "directory_count": 3}}\n',
    )

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    markdown = module.render_lifecycle_operations_report_markdown(report)

    assert "## Operational Summary" in markdown
    assert f"- storage budget: `bounded_read_only`, bytes `{report['summary']['total_bytes']}`" in markdown
    assert "`runtime` 1200 bytes" in markdown
    assert "`delivery_projection` 5 bytes" in markdown
    assert "- blocked cleanup reasons:" in markdown
    assert "`canonical_regeneration_required_before_projection_removal` x1" in markdown
    assert "- projection regeneration candidates:" in markdown
    assert "`studies/001-risk/manuscript/current_package/manuscript.docx`" in markdown
    assert "- restore contract gaps: none" in markdown

def test_lifecycle_operations_report_projects_delivery_manifest_historical_backfill_plan(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])

    assert report["mutation_policy"]["read_only"] is True
    assert report["mutation_policy"]["physical_cleanup_performed"] is False
    assert report["historical_backfill_plan_count"] == 1
    workspace = report["workspaces"][0]
    assert workspace["historical_backfill_plan_count"] == 1
    study = workspace["studies"][0]
    assert study["delivery_manifest_summary"] == {
        "delivery_manifest_count": 1,
        "lifecycle_hook_present": False,
        "source_signature_present": False,
        "publication_refs_present": False,
    }
    assert study["historical_backfill_plan"] == {
        "plan_type": "delivery_manifest_historical_backfill",
        "read_only": True,
        "missing_surfaces": [
            "delivery_manifest_lifecycle_hook",
            "source_signature",
            "publication_refs",
        ],
        "missing_lifecycle_hook": True,
        "missing_source_signature": True,
        "missing_publication_refs": True,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "regenerate_delivery_manifest_lifecycle_hook",
            "recompute_delivery_manifest_source_signature",
            "relink_delivery_manifest_publication_refs",
            "rerun_publication_gate",
        ],
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "manual_patch_allowed": False,
            "allowed_mutating_actions": [],
        },
    }


def test_lifecycle_operations_report_markdown_is_renderable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_operations_report")
    workspace_root = tmp_path / "workspace"
    _write(workspace_root / "studies" / "001-risk" / "paper" / "source.md")

    report = module.run_lifecycle_operations_report(workspace_roots=[workspace_root])
    markdown = module.render_lifecycle_operations_report_markdown(report)

    assert "# Control Plane Lifecycle Report" in markdown
    assert "`001-risk`" in markdown
