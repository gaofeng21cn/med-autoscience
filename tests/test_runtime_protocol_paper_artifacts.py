from __future__ import annotations

import json
import time
from pathlib import Path

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


def test_resolve_latest_paper_root_prefers_latest_manifest(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    old_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    new_manifest = quest_root / ".ds" / "worktrees" / "paper-run-2" / "paper" / "paper_bundle_manifest.json"
    dump_json(old_manifest, {"schema_version": 1})
    time.sleep(0.01)
    dump_json(new_manifest, {"schema_version": 1})

    result = resolve_latest_paper_root(quest_root)

    assert result == new_manifest.parent


def test_resolve_paper_bundle_and_submission_minimal_manifest(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    paper_bundle_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    dump_json(paper_bundle_manifest, {"schema_version": 1})
    submission_manifest = paper_bundle_manifest.parent / "submission_minimal" / "submission_manifest.json"
    dump_json(submission_manifest, {"schema_version": 1})

    resolved_bundle = resolve_paper_bundle_manifest(quest_root)
    resolved_submission = resolve_submission_minimal_manifest(resolved_bundle)

    assert resolved_bundle == paper_bundle_manifest
    assert resolved_submission == submission_manifest


def test_resolve_paper_bundle_manifest_prefers_paper_worktree_over_newer_analysis_mirror(
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

    assert resolved_bundle == paper_manifest


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

    assert resolved_bundle == worktree_manifest


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


def test_resolve_submission_minimal_paths_follow_authoritative_projected_paper_line(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    submission_manifest_path = worktree_paper_root / "submission_minimal" / "submission_manifest.json"
    docx = worktree_paper_root / "submission_minimal" / "manuscript.docx"
    pdf = worktree_paper_root / "submission_minimal" / "paper.pdf"

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
    dump_json(
        submission_manifest_path,
        {
            "schema_version": 1,
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    docx.parent.mkdir(parents=True, exist_ok=True)
    docx.write_text("docx", encoding="utf-8")
    pdf.write_text("%PDF", encoding="utf-8")

    resolved_submission = resolve_submission_minimal_manifest(projected_manifest)
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

    materialized = paper_artifacts.materialize_archived_reference_only_submission_surface_manifests(paper_root)

    assert materialized == (legacy_surface_root.resolve(),)
    archived_manifest = json.loads((legacy_surface_root / "submission_manifest.json").read_text(encoding="utf-8"))
    assert archived_manifest == {
        "schema_version": 1,
        "surface_status": "archived_reference_only",
        "archive_reason": "Retained only as a historical journal-target package.",
        "active_managed_submission_manifest_path": "paper/submission_minimal/submission_manifest.json",
    }
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
