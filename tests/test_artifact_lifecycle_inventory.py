from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write(path: Path, text: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_artifact_inventory_classifies_roles_and_lifecycle(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"

    paths_by_expected_role = {
        "canonical_source": _write(study_root / "paper" / "source" / "manuscript_source.md"),
        "runtime_ephemeral": _write(quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"),
        "derived_projection": _write(study_root / "manuscript" / "current_package" / "manuscript.docx"),
        "human_handoff_mirror": _write(study_root / "manuscript" / "submission_minimal" / "paper.pdf"),
        "data_release": _write(tmp_path / "datasets" / "master" / "v1" / "dataset_manifest.yaml"),
        "cold_archive": _write(quest_root / ".ds" / "cold_archive" / "worktree_runtime_payloads" / "run.tar.gz"),
        "audit_log": _write(study_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "latest.json"),
    }

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        quest_root=quest_root,
        paths=tuple(paths_by_expected_role.values()),
    )

    by_path = {Path(item["path"]): item for item in inventory["artifacts"]}
    assert {item["role"] for item in inventory["artifacts"]} == set(paths_by_expected_role)
    assert by_path[paths_by_expected_role["canonical_source"]]["lifecycle"] == "active_authority"
    assert by_path[paths_by_expected_role["runtime_ephemeral"]]["lifecycle"] == "runtime_transient"
    assert by_path[paths_by_expected_role["derived_projection"]]["lifecycle"] == "rebuildable_projection"
    assert by_path[paths_by_expected_role["human_handoff_mirror"]]["lifecycle"] == "human_handoff"
    assert by_path[paths_by_expected_role["data_release"]]["lifecycle"] == "retained_release"
    assert by_path[paths_by_expected_role["cold_archive"]]["lifecycle"] == "archived_restore_candidate"
    assert by_path[paths_by_expected_role["audit_log"]]["lifecycle"] == "audit_retained"


def test_delivery_authority_sync_blocks_generated_surfaces_as_edit_or_quality_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    generated_paths = (
        _write(study_root / "manuscript" / "current_package" / "manuscript.docx"),
        _write(study_root / "manuscript" / "current_package.zip", "zip\n"),
        _write(study_root / "paper" / "submission_minimal" / "paper.pdf", "%PDF\n"),
        _write(study_root / "paper" / "submission_minimal" / "manuscript.docx"),
    )

    sync = module.build_delivery_authority_sync(study_root=study_root, paths=generated_paths)

    assert sync["status"] == "projection_only"
    assert sync["direct_edit_allowed"] is False
    assert sync["quality_authority_allowed"] is False
    assert sync["blocked_authority_paths"] == [str(path.resolve()) for path in generated_paths]
    assert sync["authority_source_roles"] == ["canonical_source"]


def test_paper_artifact_resolver_exposes_projection_only_authority_for_submission_outputs(tmp_path: Path) -> None:
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
    paper_bundle_manifest = tmp_path / "study" / "paper" / "paper_bundle_manifest.json"
    paper_bundle_manifest.parent.mkdir(parents=True, exist_ok=True)
    paper_bundle_manifest.write_text(json.dumps({"schema_version": 1}) + "\n", encoding="utf-8")
    submission_manifest = {
        "manuscript": {
            "docx_path": "paper/submission_minimal/manuscript.docx",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        }
    }

    resolution = paper_artifacts.resolve_submission_minimal_artifact_authority(
        paper_bundle_manifest_path=paper_bundle_manifest,
        submission_minimal_manifest=submission_manifest,
    )

    assert resolution["status"] == "resolved"
    assert resolution["docx"]["role"] == "derived_projection"
    assert resolution["pdf"]["role"] == "derived_projection"
    assert resolution["docx"]["edit_source_allowed"] is False
    assert resolution["pdf"]["quality_authority_allowed"] is False


def test_live_runtime_inventory_is_audit_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    runtime_log = _write(quest_root / ".ds" / "runs" / "run-live" / "stdout.jsonl")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=tmp_path / "studies" / "001-risk",
        quest_root=quest_root,
        paths=(runtime_log,),
        runtime_status={"status": "running", "active_run_id": "run-live"},
    )

    artifact = inventory["artifacts"][0]
    assert artifact["role"] == "runtime_ephemeral"
    assert artifact["lifecycle"] == "runtime_transient"
    assert artifact["cleanup_candidate_action"] == "audit-only"
    assert artifact["cleanup_blockers"] == ["live_runtime_active"]


def test_archive_cleanup_requires_restore_checksum_and_rehydrate_verification(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    archive_path = _write(tmp_path / "runtime" / "quests" / "001-risk" / ".ds" / "cold_archive" / "payload.tar.gz")

    missing = module.evaluate_archive_cleanup_readiness(
        archive_path=archive_path,
        restore_metadata={},
    )
    verified = module.evaluate_archive_cleanup_readiness(
        archive_path=archive_path,
        restore_metadata={
            "restore_handle": "s3://archive/payload.tar.gz",
            "sha256": "abc123",
            "rehydrate_verification": {"status": "verified"},
        },
    )

    assert missing["candidate_action"] == "blocked"
    assert missing["blockers"] == [
        "missing_restore_handle",
        "missing_checksum",
        "missing_rehydrate_verification",
    ]
    assert verified["candidate_action"] == "cleanup-expanded-copy"
    assert verified["blockers"] == []


def test_delivery_manifest_records_lifecycle_authority_sync(tmp_path: Path) -> None:
    delivery_sync = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    shared = importlib.import_module("tests.test_study_delivery_sync_cases.shared")
    paper_root, study_root = shared.make_delivery_workspace(tmp_path)

    manifest = delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    lifecycle = manifest["artifact_lifecycle"]
    assert lifecycle["surface_kind"] == "study_delivery_sync_lifecycle"
    assert lifecycle["authority_sync"]["status"] == "projection_only"
    assert lifecycle["authority_sync"]["direct_edit_allowed"] is False
    assert lifecycle["authority_sync"]["quality_authority_allowed"] is False
    assert lifecycle["lifecycle_roles"]["current_package"] == "derived_projection"
