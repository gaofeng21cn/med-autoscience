from __future__ import annotations

import importlib
from pathlib import Path


def _artifact(
    path: Path,
    *,
    role: str,
    lifecycle: str,
    cleanup_candidate_action: str,
    cleanup_blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "path": str(path),
        "workspace_relative_path": str(path),
        "role": role,
        "lifecycle": lifecycle,
        "cleanup_candidate_action": cleanup_candidate_action,
        "cleanup_blockers": cleanup_blockers or [],
    }


def test_retention_plan_keeps_authority_release_audit_and_handoff_online(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/paper/source/manuscript.md"),
            role="canonical_source",
            lifecycle="active_authority",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("datasets/release/dataset_manifest.yaml"),
            role="data_release",
            lifecycle="retained_release",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/artifacts/runtime/latest.json"),
            role="audit_log",
            lifecycle="audit_retained",
            cleanup_candidate_action="keep-online",
        ),
        _artifact(
            Path("studies/001/manuscript/README.md"),
            role="human_handoff_mirror",
            lifecycle="human_handoff",
            cleanup_candidate_action="keep-online",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert plan["surface_kind"] == "artifact_retention_operations_plan"
    assert plan["mutation_policy"]["physical_cleanup_performed"] is False
    assert plan["mutation_policy"]["allowed_physical_actions"] == ["delete-safe-cache"]
    assert plan["retention_policy_catalog"]["default_keep_online_roles"] == [
        "audit_log",
        "canonical_source",
        "data_release",
        "human_handoff_mirror",
    ]
    assert {item["retention_action"] for item in plan["operations"]} == {"keep_online"}
    assert all(item["physical_delete_allowed"] is False for item in plan["operations"])
    assert plan["summary"]["action_counts"]["keep_online"] == 4


def test_retention_plan_projects_generated_surfaces_without_physical_delete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("studies/001/manuscript/current_package/manuscript.docx"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            Path("studies/001/paper/submission_minimal/paper.pdf"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
        _artifact(
            Path("studies/001/manuscript/current_package.zip"),
            role="derived_projection",
            lifecycle="rebuildable_projection",
            cleanup_candidate_action="rebuildable",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert {item["retention_action"] for item in plan["operations"]} == {
        "regenerate_projection_then_remove_stale",
    }
    for item in plan["operations"]:
        assert item["projection_status"] == "stale_or_rebuildable_projection"
        assert item["removal_marker"] == "regenerate-before-remove"
        assert item["canonical_regeneration_gate"]["required"] is True
        assert item["canonical_regeneration_gate"]["status"] == "required_before_physical_removal"
        assert "canonical_regeneration_required_before_projection_removal" in item["blockers"]
        assert item["physical_delete_allowed"] is False
    assert plan["retention_policy_catalog"]["derived_projection_removal_marker"] == "regenerate-before-remove"


def test_retention_plan_blocks_runtime_archive_compress_and_keeps_live_runtime_audit_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path("ops/runtime/quests/001/.ds/runs/run-live/stdout.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="audit-only",
            cleanup_blockers=["live_runtime_active"],
        ),
        _artifact(
            Path("ops/runtime/quests/002/.ds/runs/run-stopped/stderr.jsonl"),
            role="runtime_ephemeral",
            lifecycle="runtime_transient",
            cleanup_candidate_action="archive-compress",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)
    live = plan["operations"][0]
    terminal = plan["operations"][1]

    assert live["retention_action"] == "keep_online"
    assert live["runtime_retention_mode"] == "audit_only"
    assert live["blockers"] == ["live_runtime_active"]
    assert live["physical_delete_allowed"] is False
    assert terminal["retention_action"] == "archive_compress_candidate_blocked"
    assert terminal["physical_archive_compress_allowed"] is False
    assert terminal["restore_contract_gate"]["required"] is True
    assert terminal["restore_contract_gate"]["status"] == "apply_implementation_required"
    assert "physical_archive_compress_not_open" in terminal["blockers"]
    assert "restore_contract_apply_implementation_required" in terminal["blockers"]


def test_retention_plan_only_marks_safe_cache_as_applyable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        _artifact(
            Path(".pytest_cache/v/cache/nodeids"),
            role="cache",
            lifecycle="cache_transient",
            cleanup_candidate_action="delete-safe-cache",
        ),
        _artifact(
            Path("ops/runtime/quests/001/.ds/cold_archive/payload.tar.gz"),
            role="cold_archive",
            lifecycle="archived_restore_candidate",
            cleanup_candidate_action="restore-gated",
        ),
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)

    assert plan["summary"]["applyable_action_counts"] == {"delete_safe_cache": 1}
    assert plan["retention_policy_catalog"]["physical_apply_allowlist"] == ["delete-safe-cache"]
    assert plan["operations"][0]["retention_action"] == "delete_safe_cache"
    assert plan["operations"][0]["physical_delete_allowed"] is True
    assert plan["operations"][1]["retention_action"] == "restore_contract_required"
    assert plan["operations"][1]["physical_delete_allowed"] is False
    assert plan["operations"][1]["restore_contract_gate"]["status"] == "required_before_cleanup"
