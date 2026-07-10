from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from med_autoscience.controllers.submission_minimal import package_builder, source_contract
from med_autoscience.controllers.submission_minimal.authority import describe_submission_minimal_authority
from med_autoscience.controllers.submission_minimal.package_builder import create_submission_minimal_package
from med_autoscience.controllers.submission_minimal.shared_base import (
    resolve_compiled_pdf_path,
)
from tests.submission_minimal_cases.shared_base import (
    dump_json,
    lightweight_submission_exports,
    make_authoritative_worktree_source_workspace,
    make_materialized_submission_source_workspace,
    make_paper_workspace,
    make_stage_native_current_body_workspace,
    write_text,
)

pytestmark = pytest.mark.submission_heavy


def test_create_submission_minimal_package_prefers_current_compile_source_and_refreshes_review(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    current_story = """# Current MAS Draft Title

## Abstract

Current draft abstract.

## Introduction

Current draft introduction with citation [@ref1].

## Methods

Current draft methods.

## Results

Current draft results.

## Discussion

Current draft discussion.

## Conclusion

Current draft conclusion.
"""
    write_text(paper_root / "draft.md", current_story)
    write_text(paper_root / "build" / "review_manuscript.md", "# Stale Review\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {"source_markdown_path": "paper/draft.md", "output_pdf": "paper/paper.pdf"},
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    assert "Current MAS Draft Title" in submission_text
    assert "Test Medical Manuscript" not in submission_text
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == current_story


def test_general_medical_submission_source_alias_is_authority_note(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    review_path = paper_root / "build" / "review_manuscript.md"
    write_text(review_path, review_path.read_text(encoding="utf-8") + "\n# Appendix\n\nStudy-specific retained evidence.\n")

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_note = (submission_root / "manuscript_source.md").read_text(encoding="utf-8")
    submission_text = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert manifest["manuscript"]["source_markdown_alias_role"] == "authority_note"
    assert not any(line.lstrip().startswith("#") for line in source_note.splitlines())
    assert "Canonical full manuscript surface" in source_note
    assert "Study-specific retained evidence." not in source_note
    assert "Study-specific retained evidence." in submission_text
    assert manifest["manuscript"]["surface_qc"]["status"] == "pass"


def test_describe_submission_minimal_authority_detects_content_change_but_ignores_mtime(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    references_path = paper_root / "references.bib"
    references_stat = references_path.stat()
    os.utime(
        references_path,
        ns=(references_stat.st_atime_ns, references_stat.st_mtime_ns + 1_000_000_000),
    )
    assert describe_submission_minimal_authority(paper_root=paper_root)["source_signature"] == manifest[
        "source_signature"
    ]

    write_text(paper_root / "build" / "review_manuscript.md", "# Updated manuscript\n\nAuthority change.\n")
    stale = describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_signature_mismatch"
    assert stale["blocking_artifact_refs"][0]["blocker"] == "stale_submission_minimal_authority"


def test_create_submission_minimal_package_canonicalizes_authoritative_worktree_source_paths(
    tmp_path: Path,
) -> None:
    paper_root = make_authoritative_worktree_source_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    source_paths = [item["path"] for item in manifest["source_contract"]["source_files"]]
    assert all(not path.startswith("/") for path in source_paths)
    assert "paper/figures/generated/F1.png" in source_paths
    assert "paper/tables/generated/T1.csv" in source_paths
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").read_text(encoding="utf-8") == (
        "Characteristic,Value\nAge,99\n"
    )
    assert describe_submission_minimal_authority(paper_root=paper_root)["status"] == "current"


def test_create_submission_minimal_package_supports_stage_native_current_body_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from med_autoscience.controllers import study_delivery_sync

    monkeypatch.setattr(study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: False)
    paper_root = make_stage_native_current_body_workspace(tmp_path)
    study_root = paper_root.parents[5]

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    source_note = (study_root / "submission" / "manuscript_source.md").read_text(encoding="utf-8")
    assert manifest["output_root"] == "submission"
    assert manifest["manuscript"]["pdf_path"] == "submission/paper.pdf"
    assert "paper_authority_cutover/current_body/paper/draft.md" in source_note
    assert describe_submission_minimal_authority(paper_root=paper_root)["status"] == "current"


def test_create_submission_minimal_package_accepts_materialized_submission_source(
    tmp_path: Path,
) -> None:
    paper_root = make_materialized_submission_source_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    authority = describe_submission_minimal_authority(paper_root=paper_root)
    assert 'title: "Materialized Submission Title"' in submission_markdown
    assert "Materialized figure caption." in submission_markdown
    assert manifest["manuscript"]["surface_qc"]["status"] == "pass"
    assert authority["status"] == "current"
    assert authority["source_signature"] == manifest["source_signature"]


def test_submission_authority_ignores_post_gate_evidence_ledger_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from med_autoscience.controllers import study_delivery_sync

    paper_root = make_paper_workspace(tmp_path)
    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[]}\n')
    monkeypatch.setattr(study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        study_delivery_sync,
        "sync_study_delivery",
        lambda **_: {"status": "synced"},
    )
    monkeypatch.setattr(
        package_builder,
        "replay_post_submission_minimal_sync",
        lambda **_: {"status": "synced"},
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[{"id":"refresh"}]}\n')

    assert "paper/evidence_ledger.json" not in manifest["source_contract"]["source_paths"]
    assert describe_submission_minimal_authority(paper_root=paper_root)["status"] == "current"


def test_create_submission_minimal_package_wires_excluded_roots_to_compiled_source_resolvers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"
    write_text(submission_root / "manuscript_source.md", "# Wrong self reference\n")
    write_text(submission_root / "paper.pdf", "%PDF-1.4\n%wrong\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown": "paper/submission_minimal/manuscript_source.md",
            "output_pdf": "paper/submission_minimal/paper.pdf",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
    )

    observed_roots: dict[str, tuple[Path, ...]] = {}
    original_markdown_resolver = package_builder.resolve_compiled_markdown_path
    original_pdf_resolver = package_builder.resolve_compiled_pdf_path

    def resolve_markdown(**kwargs):
        observed_roots["markdown"] = kwargs["excluded_roots"]
        return original_markdown_resolver(**kwargs)

    def resolve_pdf(**kwargs):
        observed_roots["pdf"] = kwargs["excluded_roots"]
        return original_pdf_resolver(**kwargs)

    monkeypatch.setattr(package_builder, "resolve_compiled_markdown_path", resolve_markdown)
    monkeypatch.setattr(package_builder, "resolve_compiled_pdf_path", resolve_pdf)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert submission_root.resolve() in observed_roots["markdown"]
    assert observed_roots["markdown"] == observed_roots["pdf"]
    assert manifest["input_compiled_pdf_path"] == "paper/paper.pdf"


def test_describe_submission_minimal_authority_flags_legacy_manifest_when_source_is_newer(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    (paper_root / "submission_minimal" / "audit" / "submission_manifest.json").unlink()
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest.pop("source_signature", None)
    manifest.pop("source_contract", None)
    dump_json(manifest_path, manifest)

    assert describe_submission_minimal_authority(paper_root=paper_root)["status"] == "current"

    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Updated review manuscript\n\nLegacy package is now stale.\n",
    )

    stale = describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_newer_than_manifest"


def test_resolve_compiled_pdf_path_uses_present_compiled_pdf_asset_when_report_lacks_pdf_path(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    resolved = resolve_compiled_pdf_path(
        workspace_root=paper_root.parent,
        bundle_manifest={
            "schema_version": 1,
            "included_assets": [
                {"path": "paper/figures/F1_main.pdf", "kind": "figure_export", "status": "present"},
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
            ],
        },
        compile_report={},
    )

    assert resolved == paper_root / "paper.pdf"


def test_create_submission_minimal_package_rebuilds_pdf_when_compile_report_lacks_pdf_candidate(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    dump_json(
        paper_root / "build" / "compile_report.json",
        {"source_markdown_path": "paper/build/review_manuscript.md"},
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )
    (paper_root / "paper.pdf").unlink()

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert (paper_root / "submission_minimal" / "paper.pdf").exists()
    assert manifest["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"
    assert manifest["input_compiled_pdf_path"] is None
    assert manifest["input_compiled_pdf_status"] == "not_required_rebuilt_from_submission_source"


def test_submission_source_signature_changes_with_renderer_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    kwargs = {
        "paper_root": paper_root,
        "workspace_root": paper_root.parent,
        "compile_report_path": paper_root / "build" / "compile_report.json",
        "compiled_markdown_path": paper_root / "build" / "review_manuscript.md",
        "figure_catalog_path": paper_root / "figures" / "figure_catalog.json",
        "table_catalog_path": paper_root / "tables" / "table_catalog.json",
        "figure_catalog": figure_catalog,
        "table_catalog": table_catalog,
        "references_source_path": paper_root / "references.bib",
    }
    baseline = source_contract.build_submission_minimal_source_contract(**kwargs)
    monkeypatch.setattr(
        source_contract,
        "_controller_renderer_contract_entries",
        lambda: [{"path": "controller_module://submission.py", "size": 1, "mtime_ns": 1, "sha256": "1" * 64}],
    )
    changed = source_contract.build_submission_minimal_source_contract(**kwargs)

    assert baseline["controller_renderer_signature"] != changed["controller_renderer_signature"]
    assert baseline["source_signature"] != changed["source_signature"]
