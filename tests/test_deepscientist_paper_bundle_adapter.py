from __future__ import annotations

import importlib
import json
import time
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_resolve_latest_paper_root_prefers_latest_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.paper_bundle")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    old_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    new_manifest = quest_root / ".ds" / "worktrees" / "paper-run-2" / "paper" / "paper_bundle_manifest.json"
    dump_json(old_manifest, {"schema_version": 1})
    time.sleep(0.01)
    dump_json(new_manifest, {"schema_version": 1})

    result = module.resolve_latest_paper_root(quest_root)

    assert result == new_manifest.parent


def test_resolve_paper_bundle_and_submission_minimal_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.paper_bundle")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    paper_bundle_manifest = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    dump_json(paper_bundle_manifest, {"schema_version": 1})
    submission_manifest = paper_bundle_manifest.parent / "submission_minimal" / "submission_manifest.json"
    dump_json(submission_manifest, {"schema_version": 1})

    resolved_bundle = module.resolve_paper_bundle_manifest(quest_root)
    resolved_submission = module.resolve_submission_minimal_manifest(resolved_bundle)

    assert resolved_bundle == paper_bundle_manifest
    assert resolved_submission == submission_manifest


def test_resolve_artifact_manifest_from_main_result_evidence_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.paper_bundle")
    worktree_root = tmp_path / "worktree"
    manifest = worktree_root / "artifacts" / "artifact_manifest.json"
    dump_json(manifest, {"schema_version": 1})
    main_result = {
        "worktree_root": str(worktree_root),
        "evidence_paths": ["artifacts/artifact_manifest.json", "paper/build/review_manuscript.md"],
    }

    result = module.resolve_artifact_manifest(main_result)

    assert result == manifest


def test_resolve_submission_minimal_output_paths_from_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.paper_bundle")
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

    docx_path, pdf_path = module.resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=paper_bundle_manifest,
        submission_minimal_manifest=submission_manifest,
    )

    assert docx_path == docx
    assert pdf_path == pdf
