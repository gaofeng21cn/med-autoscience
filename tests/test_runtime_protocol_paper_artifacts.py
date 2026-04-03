from __future__ import annotations

import json
import time
from pathlib import Path

from med_autoscience.runtime_protocol.paper_artifacts import (
    find_unmanaged_submission_surface_roots,
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
