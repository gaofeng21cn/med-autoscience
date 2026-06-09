from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from med_autoscience.runtime_protocol import paper_artifacts
from med_autoscience.runtime_protocol.paper_artifacts import (
    find_unmanaged_submission_surface_roots,
    resolve_archived_submission_surface_roots,
    resolve_artifact_manifest_from_main_result,
    resolve_latest_paper_root,
    resolve_managed_submission_surface_roots,
    resolve_paper_bundle_manifest,
    resolve_submission_minimal_manifest,
    resolve_submission_minimal_output_paths,
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_complete_canonical_study_paper_surface(
    paper_root: Path,
    *,
    paper_branch: str,
) -> None:
    dump_json(paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": paper_branch})
    (paper_root / "draft.md").write_text("# Draft\n\nJournal-style manuscript.\n", encoding="utf-8")
    dump_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})


def test_resolve_latest_paper_root_ignores_legacy_worktree_manifests_by_default(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    old_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    new_manifest = quest_root / ".ds" / "worktrees" / "paper-run-2" / "paper" / "paper_bundle_manifest.json"
    dump_json(old_manifest, {"schema_version": 1})
    time.sleep(0.01)
    dump_json(new_manifest, {"schema_version": 1})

    with pytest.raises(FileNotFoundError, match="No paper_bundle_manifest.json"):
        resolve_latest_paper_root(quest_root)

    assert resolve_paper_bundle_manifest(quest_root) is None


def test_resolve_paper_bundle_manifest_ignores_legacy_worktree_by_default(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    legacy_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    dump_json(legacy_manifest, {"schema_version": 1})

    result = resolve_paper_bundle_manifest(quest_root)

    assert result is None


def test_resolve_latest_paper_root_ignores_projected_paper_line_legacy_ds_root(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    dump_json(worktree_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/run-1"})
    dump_json(projected_manifest, {"schema_version": 1, "paper_branch": "paper/projected"})
    dump_json(
        quest_root / "paper" / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/run-1",
            "paper_root": str(worktree_paper_root.resolve()),
        },
    )

    result = resolve_latest_paper_root(quest_root)

    assert result == projected_manifest.parent.resolve()


def test_resolve_latest_paper_root_prefers_newer_bound_study_canonical_paper(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001"
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = workspace_root / "studies" / "q001"
    study_paper_root = study_root / "paper"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"

    dump_json(runtime_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    dump_json(projected_manifest, {"schema_version": 1, "paper_branch": "paper/main"})
    dump_json(
        quest_root / "paper" / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "paper_root": str(runtime_paper_root.resolve()),
        },
    )
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: q001\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: q001\n", encoding="utf-8")
    write_complete_canonical_study_paper_surface(study_paper_root, paper_branch="paper/main")
    newer_time = runtime_paper_root.joinpath("paper_bundle_manifest.json").stat().st_mtime + 60
    os.utime(study_paper_root / "paper_bundle_manifest.json", (newer_time, newer_time))

    result = resolve_latest_paper_root(quest_root)

    assert result == study_paper_root.resolve()


def test_resolve_latest_paper_root_rejects_legacy_runtime_paper_when_bound_study_surface_is_incomplete(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001"
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = workspace_root / "studies" / "q001"
    study_paper_root = study_root / "paper"

    dump_json(runtime_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: q001\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: q001\n", encoding="utf-8")
    dump_json(study_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/other"})
    newer_time = runtime_paper_root.joinpath("paper_bundle_manifest.json").stat().st_mtime + 60
    os.utime(study_paper_root / "paper_bundle_manifest.json", (newer_time, newer_time))

    with pytest.raises(FileNotFoundError, match="No paper_bundle_manifest.json"):
        resolve_latest_paper_root(quest_root)


def test_resolve_latest_paper_root_prefers_complete_bound_study_canonical_paper_when_branch_differs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001"
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = workspace_root / "studies" / "q001"
    study_paper_root = study_root / "paper"

    dump_json(runtime_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: q001\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: q001\n", encoding="utf-8")
    write_complete_canonical_study_paper_surface(study_paper_root, paper_branch="main")

    result = resolve_latest_paper_root(quest_root)

    assert result == study_paper_root.resolve()


def test_resolve_latest_paper_root_prefers_stage_native_bound_study_body(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "runtime" / "quests" / "q001"
    study_root = workspace_root / "studies" / "q001"
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )

    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: q001\nstudy_id: q001\n", encoding="utf-8")
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: q001\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text("quest_id: q001\n", encoding="utf-8")
    write_complete_canonical_study_paper_surface(stage_native_paper_root, paper_branch="paper/main")

    result = resolve_latest_paper_root(quest_root)

    assert result == stage_native_paper_root.resolve()


def test_resolve_paper_bundle_and_submission_minimal_manifest(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    paper_bundle_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    dump_json(paper_bundle_manifest, {"schema_version": 1})
    submission_manifest = paper_bundle_manifest.parent / "submission_minimal" / "submission_manifest.json"
    dump_json(submission_manifest, {"schema_version": 1})

    resolved_bundle = resolve_paper_bundle_manifest(quest_root)
    resolved_submission = resolve_submission_minimal_manifest(resolved_bundle)

    assert resolved_bundle == paper_bundle_manifest
    assert resolved_submission == submission_manifest


def test_resolve_paper_bundle_manifest_ignores_legacy_worktree_mirrors(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    paper_manifest = (
        quest_root / ".ds" / "worktrees" / "paper-paper-run-1-outline-001-run" / "paper" / "paper_bundle_manifest.json"
    )
    analysis_manifest = (
        quest_root
        / ".ds"
        / "worktrees"
        / "analysis-analysis-aaaa1111-ppr002-public-evidence-adjudication"
        / "paper"
        / "paper_bundle_manifest.json"
    )
    dump_json(paper_manifest, {"schema_version": 1, "role": "paper"})
    time.sleep(0.01)
    dump_json(analysis_manifest, {"schema_version": 1, "role": "analysis"})

    resolved_bundle = resolve_paper_bundle_manifest(quest_root)

    assert resolved_bundle is None


def test_resolve_paper_bundle_manifest_prefers_runtime_worktree_over_newer_projected_mirror(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    worktree_manifest = quest_root / ".ds" / "worktrees" / "paper-run-2" / "paper" / "paper_bundle_manifest.json"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    dump_json(worktree_manifest, {"schema_version": 1, "paper_branch": "paper/run-2"})
    time.sleep(0.01)
    dump_json(projected_manifest, {"schema_version": 1, "paper_branch": "paper/run-legacy"})

    resolved_bundle = resolve_paper_bundle_manifest(quest_root)

    assert resolved_bundle == projected_manifest


def test_resolve_paper_bundle_manifest_prefers_projected_state_authority_with_stale_manifest_branch(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    active_paper_root = quest_root / ".ds" / "worktrees" / "run-current" / "paper"
    stale_paper_root = quest_root / ".ds" / "worktrees" / "paper-paper-legacy" / "paper"
    active_manifest = active_paper_root / "paper_bundle_manifest.json"
    stale_manifest = stale_paper_root / "paper_bundle_manifest.json"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    projected_state = quest_root / "paper" / "paper_line_state.json"

    dump_json(active_manifest, {"schema_version": 1, "paper_branch": "paper/legacy"})
    dump_json(stale_manifest, {"schema_version": 1, "paper_branch": "paper/legacy"})
    dump_json(projected_manifest, {"schema_version": 1, "paper_branch": "paper/legacy"})
    dump_json(
        projected_state,
        {
            "schema_version": 1,
            "paper_branch": "run/current",
            "paper_root": str(active_paper_root),
        },
    )

    resolved_bundle = resolve_paper_bundle_manifest(quest_root)

    assert resolved_bundle == projected_manifest


def test_resolve_artifact_manifest_from_main_result_evidence_paths(tmp_path: Path) -> None:
    worktree_root = tmp_path / "worktree"
    manifest = worktree_root / "artifacts" / "artifact_manifest.json"
    dump_json(manifest, {"schema_version": 1})
    main_result = {
        "worktree_root": str(worktree_root),
        "evidence_paths": ["artifacts/artifact_manifest.json", "paper/build/review_manuscript.md"],
    }

    result = resolve_artifact_manifest_from_main_result(main_result)

    assert result == manifest


def test_resolve_artifact_manifest_from_main_result_accepts_absolute_evidence_without_worktree_root(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "artifacts" / "artifact_manifest.json"
    dump_json(manifest, {"schema_version": 1})
    main_result = {
        "evidence_paths": [str(manifest), str(tmp_path / "paper" / "build" / "review_manuscript.md")],
    }

    result = resolve_artifact_manifest_from_main_result(main_result)

    assert result == manifest


def test_resolve_submission_minimal_output_paths_from_manifest(tmp_path: Path) -> None:
    paper_bundle_manifest = tmp_path / "worktree" / "paper" / "paper_bundle_manifest.json"
    dump_json(paper_bundle_manifest, {"schema_version": 1})
    submission_manifest = {
        "manuscript": {
            "docx_path": "paper/submission_minimal/manuscript.docx",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        }
    }
    docx = tmp_path / "worktree" / "paper" / "submission_minimal" / "manuscript.docx"
    pdf = tmp_path / "worktree" / "paper" / "submission_minimal" / "paper.pdf"
    docx.parent.mkdir(parents=True, exist_ok=True)
    docx.write_text("docx", encoding="utf-8")
    pdf.write_text("%PDF", encoding="utf-8")

    docx_path, pdf_path = resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=paper_bundle_manifest,
        submission_minimal_manifest=submission_manifest,
    )

    assert docx_path == docx
    assert pdf_path == pdf


def test_submission_minimal_artifact_authority_uses_lifecycle_kernel_shape(tmp_path: Path) -> None:
    paper_bundle_manifest = tmp_path / "worktree" / "paper" / "paper_bundle_manifest.json"
    dump_json(paper_bundle_manifest, {"schema_version": 1})
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

    assert resolution["docx"]["role"] == "derived_projection"
    assert resolution["docx"]["owner"] == "artifact_lifecycle_authority_kernel"
    assert resolution["docx"]["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}
    assert resolution["docx"]["projection_currentness"] == "projection_only"
    assert resolution["pdf"]["role"] == "derived_projection"
    assert resolution["pdf"]["owner"] == "artifact_lifecycle_authority_kernel"
    assert resolution["pdf"]["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}
    assert resolution["pdf"]["projection_currentness"] == "projection_only"
    assert resolution["submission_minimal_edit_source_allowed"] is False
    assert resolution["submission_minimal_quality_authority_allowed"] is False
    assert resolution["submission_minimal_dispatch_authority_allowed"] is False


def test_resolve_submission_minimal_paths_follow_authoritative_projected_paper_line(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    submission_manifest_path = projected_manifest.parent / "submission_minimal" / "submission_manifest.json"
    legacy_submission_manifest_path = worktree_paper_root / "submission_minimal" / "submission_manifest.json"
    docx = projected_manifest.parent / "submission_minimal" / "manuscript.docx"
    pdf = projected_manifest.parent / "submission_minimal" / "paper.pdf"

    dump_json(
        projected_manifest,
        {
            "schema_version": 1,
            "paper_branch": "paper/run-1",
        },
    )
    dump_json(
        quest_root / "paper" / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/run-1",
            "paper_root": str(worktree_paper_root),
        },
    )
    submission_payload = {
        "schema_version": 1,
        "manuscript": {
            "docx_path": "paper/submission_minimal/manuscript.docx",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
    }
    dump_json(submission_manifest_path, submission_payload)
    dump_json(legacy_submission_manifest_path, submission_payload)
    docx.parent.mkdir(parents=True, exist_ok=True)
    docx.write_text("docx", encoding="utf-8")
    pdf.write_text("%PDF", encoding="utf-8")

    resolved_submission = resolve_submission_minimal_manifest(
        projected_manifest,
    )
    docx_path, pdf_path = resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=projected_manifest,
        submission_minimal_manifest=json.loads(submission_manifest_path.read_text(encoding="utf-8")),
    )

    assert resolved_submission == submission_manifest_path
    assert docx_path == docx
    assert pdf_path == pdf


def test_submission_surface_resolution_distinguishes_managed_and_unmanaged_roots(tmp_path: Path) -> None:
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    (paper_root / "submission_minimal").mkdir(parents=True, exist_ok=True)
    (paper_root / "journal_submissions" / "frontiers_family_harvard").mkdir(parents=True, exist_ok=True)
    (paper_root / "submission_pituitary").mkdir(parents=True, exist_ok=True)
    (paper_root / "journal_submissions" / "pituitary").mkdir(parents=True, exist_ok=True)

    managed = resolve_managed_submission_surface_roots(paper_root)
    unmanaged = find_unmanaged_submission_surface_roots(paper_root)

    assert managed == (
        (paper_root / "submission_minimal").resolve(),
        (paper_root / "journal_submissions" / "frontiers_family_harvard").resolve(),
    )
    assert unmanaged == (
        (paper_root / "submission_pituitary").resolve(),
        (paper_root / "journal_submissions" / "pituitary").resolve(),
    )


def test_submission_surface_resolution_recognizes_archived_reference_only_legacy_root(tmp_path: Path) -> None:
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    submission_minimal_manifest = paper_root / "submission_minimal" / "submission_manifest.json"
    dump_json(
        submission_minimal_manifest,
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    archived_manifest = paper_root / "submission_pituitary" / "submission_manifest.json"
    dump_json(
        archived_manifest,
        {
            "schema_version": 1,
            "surface_status": "archived_reference_only",
            "archive_reason": "Retained only as a historical journal-target package.",
            "active_managed_submission_manifest_path": "paper/submission_minimal/submission_manifest.json",
        },
    )

    archived = resolve_archived_submission_surface_roots(paper_root)
    unmanaged = find_unmanaged_submission_surface_roots(paper_root)

    assert archived == ((paper_root / "submission_pituitary").resolve(),)
    assert unmanaged == ()


def test_materializes_archived_reference_only_manifest_for_legacy_journal_surface(tmp_path: Path) -> None:
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    legacy_surface_root = paper_root / "journal_submissions" / "rheumatology_international"
    legacy_surface_root.mkdir(parents=True, exist_ok=True)
    (legacy_surface_root / "frontiers_manuscript.md").write_text("stale generated text", encoding="utf-8")
    (legacy_surface_root / "tables").mkdir()
    (legacy_surface_root / "tables" / "Table3.md").write_text("stale table text", encoding="utf-8")

    materialized = paper_artifacts.materialize_archived_reference_only_submission_surface_manifests(paper_root)

    assert materialized == (legacy_surface_root.resolve(),)
    archived_manifest = json.loads(
        (legacy_surface_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8")
    )
    assert archived_manifest == {
        "schema_version": 1,
        "surface_status": "archived_reference_only",
        "archive_reason": "Retained only as a historical journal-target package.",
        "active_managed_submission_manifest_path": "paper/submission_minimal/submission_manifest.json",
    }
    archived_files = sorted(
        path.relative_to(legacy_surface_root).as_posix()
        for path in legacy_surface_root.rglob("*")
        if path.is_file()
    )
    assert archived_files == ["audit/submission_manifest.json"]
    assert resolve_archived_submission_surface_roots(paper_root) == (legacy_surface_root.resolve(),)
    assert find_unmanaged_submission_surface_roots(paper_root) == ()


def test_submission_surface_resolution_rejects_archived_reference_only_when_target_manifest_is_outside_current_paper(
    tmp_path: Path,
) -> None:
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    external_paper_root = tmp_path / "other" / "paper"
    dump_json(
        external_paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    dump_json(
        paper_root / "submission_pituitary" / "submission_manifest.json",
        {
            "schema_version": 1,
            "surface_status": "archived_reference_only",
            "archive_reason": "Retained only as a historical journal-target package.",
            "active_managed_submission_manifest_path": str(
                (external_paper_root / "submission_minimal" / "submission_manifest.json").resolve()
            ),
        },
    )

    archived = resolve_archived_submission_surface_roots(paper_root)
    unmanaged = find_unmanaged_submission_surface_roots(paper_root)

    assert archived == ()
    assert unmanaged == ((paper_root / "submission_pituitary").resolve(),)


def test_submission_surface_resolution_rejects_archived_reference_only_when_target_manifest_is_not_a_managed_root(
    tmp_path: Path,
) -> None:
    paper_root = tmp_path / "quest" / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    dump_json(
        paper_root / "notes" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    dump_json(
        paper_root / "submission_pituitary" / "submission_manifest.json",
        {
            "schema_version": 1,
            "surface_status": "archived_reference_only",
            "archive_reason": "Retained only as a historical journal-target package.",
            "active_managed_submission_manifest_path": "paper/notes/submission_manifest.json",
        },
    )

    archived = resolve_archived_submission_surface_roots(paper_root)
    unmanaged = find_unmanaged_submission_surface_roots(paper_root)

    assert archived == ()
    assert unmanaged == ((paper_root / "submission_pituitary").resolve(),)
