from tests.submission_minimal_cases.shared import *

from med_autoscience.controllers.submission_minimal import (
    package_builder,
    source_contract,
)
from med_autoscience.controllers.submission_minimal.authority import (
    describe_submission_minimal_authority,
)
from med_autoscience.controllers.submission_minimal.package_builder import (
    create_submission_minimal_package,
)
from med_autoscience.controllers.submission_minimal.shared_base import (
    resolve_compiled_markdown_path,
    resolve_compiled_pdf_path,
)


def test_create_submission_minimal_package_prefers_compile_report_current_draft_over_stale_bundle_input(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        """# Current MAS Draft Title

## Abstract

### Importance

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
""",
    )
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "schema_version": 1,
            "source_markdown_path": "paper/draft.md",
            "output_pdf": "paper/paper.pdf",
        },
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    assert "Current MAS Draft Title" in submission_text
    assert "Current draft methods." in submission_text
    assert "Test Medical Manuscript" not in submission_text


def test_create_submission_minimal_package_refreshes_review_manuscript_when_current_draft_is_newer(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    current_story = """# Current MAS Draft Title

## Abstract

Current draft abstract.

## Introduction

Current draft introduction.
"""
    write_text(paper_root / "draft.md", current_story)
    write_text(paper_root / "build" / "review_manuscript.md", "# Stale Review\n\nOld text.\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "schema_version": 1,
            "source_markdown_path": "paper/draft.md",
            "output_pdf": "paper/paper.pdf",
        },
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == current_story.rstrip() + "\n"


def test_general_medical_submission_source_alias_is_authority_note_and_appendix_stays_in_projection(
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    review_manuscript_path = paper_root / "build" / "review_manuscript.md"
    write_text(
        review_manuscript_path,
        review_manuscript_path.read_text(encoding="utf-8")
        + """

# Appendix: Retained Public Evidence After Screening

The retained MRI dataset is the mapping-pituitary MRI cohort, which contributes 136 total cases.
The retained omics dataset is the GSE169498 transcriptomic series, which preserves a clean invasiveness-labeled biology surface.
""",
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_note = (submission_root / "manuscript_source.md").read_text(encoding="utf-8")
    submission_text = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")

    assert manifest["manuscript"]["source_markdown_alias_role"] == "authority_note"
    assert not any(line.lstrip().startswith("#") for line in source_note.splitlines())
    for phrase in (
        "authority note",
        "not the full manuscript",
        "Canonical full manuscript surface",
        "Export-ready submission projection",
        "source signature",
    ):
        assert phrase in source_note
    for study_specific_phrase in (
        "mapping-pituitary",
        "GSE169498",
        "transcriptomic series",
        "invasiveness-labeled biology surface",
    ):
        assert study_specific_phrase not in source_note
        assert study_specific_phrase in submission_text
    assert "# Appendix: Retained Public Evidence After Screening" in submission_text
    surface_qc = manifest["manuscript"]["surface_qc"]
    assert surface_qc["status"] == "pass"
    assert surface_qc["authority_note"]["role_clarity_pass"] is True
    assert surface_qc["authority_note"]["forbidden_study_anchor_hits"] == []


def test_describe_submission_minimal_authority_detects_changed_compiled_markdown(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    current = describe_submission_minimal_authority(paper_root=paper_root)
    assert current["status"] == "current"
    assert current["evaluated_source_signature"] == current["source_signature"]
    assert current["authority_source_signature"] == current["recorded_source_signature"]
    assert current["blocking_artifact_refs"] == []

    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Updated review manuscript\n\nLate-stage authority change.\n",
    )

    stale = describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_signature_mismatch"
    assert stale["evaluated_source_signature"] == stale["source_signature"]
    assert stale["authority_source_signature"] == stale["recorded_source_signature"]
    assert stale["gate_fingerprint"].startswith("submission-minimal-authority::")
    assert stale["blocking_artifact_refs"] == [
        {
            "blocker": "stale_submission_minimal_authority",
            "artifact_path": str(paper_root / "submission_minimal" / "audit" / "submission_manifest.json"),
            "artifact_role": "submission_minimal_authority",
            "stale_reason": "submission_source_signature_mismatch",
        }
    ]


def test_describe_submission_minimal_authority_flags_legacy_manifest_when_source_is_newer(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    v2_manifest_path = paper_root / "submission_minimal" / "audit" / "submission_manifest.json"
    v2_manifest_path.unlink()
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest.pop("source_signature", None)
    manifest.pop("source_contract", None)
    dump_json(manifest_path, manifest)

    current = describe_submission_minimal_authority(paper_root=paper_root)
    assert current["status"] == "current"

    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Updated review manuscript\n\nLegacy package is now stale.\n",
    )

    stale = describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_newer_than_manifest"


def test_describe_submission_minimal_authority_ignores_source_mtime_only_drift(tmp_path: Path) -> None:
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

    authority = describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["source_signature"] == manifest["source_signature"]


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

    authority = describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"


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

    submission_root = study_root / "submission"
    source_note = (submission_root / "manuscript_source.md").read_text(encoding="utf-8")

    assert manifest["output_root"] == "submission"
    assert manifest["manuscript"]["source_markdown_path"] == "submission/manuscript_submission.md"
    assert manifest["manuscript"]["source_markdown_alias_path"] == "submission/manuscript_source.md"
    assert manifest["manuscript"]["pdf_path"] == "submission/paper.pdf"
    assert manifest["manuscript"]["docx_path"] == "submission/manuscript.docx"
    assert (
        "Canonical full manuscript surface: "
        "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md."
    ) in source_note
    assert "Export-ready submission projection: submission/manuscript_submission.md." in source_note
    assert "Manifest and source signature surface: submission/audit/submission_manifest.json#source_signature." in source_note

    authority = describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"


def test_create_submission_minimal_package_authority_ignores_post_gate_evidence_ledger_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from med_autoscience.controllers import study_delivery_sync

    paper_root = make_paper_workspace(tmp_path)
    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[]}' + "\n")

    monkeypatch.setattr(study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)

    def sync_study_delivery(*, paper_root: Path, stage: str, publication_profile: str) -> dict:
        write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[{"id":"post-sync"}]}' + "\n")
        return {"status": "synced", "stage": stage, "publication_profile": publication_profile}

    monkeypatch.setattr(study_delivery_sync, "sync_study_delivery", sync_study_delivery)
    monkeypatch.setattr(
        package_builder,
        "replay_post_submission_minimal_sync",
        lambda *, paper_root, publication_profile, authority_route_context=None: {"status": "synced"},
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert "paper/evidence_ledger.json" not in manifest["source_contract"]["source_paths"]

    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[{"id":"gate-refresh"}]}' + "\n")

    authority = describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"


def test_create_submission_minimal_package_accepts_current_bundle_contract_shape(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "pdf_path": "paper/paper.pdf",
        },
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
            "included_assets": [
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
            ],
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "manuscript.docx").exists()
    assert (submission_root / "paper.pdf").exists()
    assert manifest["manuscript"]["source_markdown_path"] == "paper/submission_minimal/manuscript_submission.md"
    assert manifest["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"


def test_resolve_compiled_markdown_path_skips_submission_surface_candidates(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(
        submission_root / "manuscript_source.md",
        """---
title: "Wrong self-referential manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Wrong self reference text.
""",
    )

    resolved = resolve_compiled_markdown_path(
        workspace_root=paper_root.parent,
        bundle_manifest={
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
        },
        compile_report={
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown": "paper/submission_minimal/manuscript_source.md",
        },
        excluded_roots=(submission_root,),
    )

    assert resolved == paper_root / "build" / "review_manuscript.md"


def test_resolve_compiled_pdf_path_skips_submission_surface_candidates(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(submission_root / "paper.pdf", "%PDF-1.4\n%self referential pdf\n")

    resolved = resolve_compiled_pdf_path(
        workspace_root=paper_root.parent,
        bundle_manifest={
            "schema_version": 1,
            "pdf_path": "paper/paper.pdf",
        },
        compile_report={
            "output_pdf": "paper/submission_minimal/paper.pdf",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
        excluded_roots=(submission_root,),
    )

    assert resolved == paper_root / "paper.pdf"


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
        {
            "source_markdown_path": "paper/build/review_manuscript.md",
        },
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


def test_create_submission_minimal_package_skips_self_referential_compiled_sources(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(
        submission_root / "manuscript_source.md",
        """---
title: "Wrong self-referential manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Wrong self reference text.

# Main Figures

## Figure 1. Wrong figure

Wrong caption.

![](../figures/F1_main.png)
""",
    )
    write_text(submission_root / "paper.pdf", "%PDF-1.4\n%self referential pdf\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown": "paper/submission_minimal/manuscript_source.md",
            "output_pdf": "paper/submission_minimal/paper.pdf",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
            "pdf_path": "paper/paper.pdf",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "This is a manuscript citation [@ref1]." in submission_markdown
    assert "Wrong self reference text." not in submission_markdown


def test_create_submission_minimal_package_prefers_compiled_markdown_over_draft_path(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)

    write_text(
        paper_root / "draft.md",
        """# Draft

## Title

Wrong draft title

## Abstract

Wrong draft abstract.
""",
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/draft.md",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert 'title: "Test Medical Manuscript"' in submission_markdown
    assert 'bibliography: references.bib' in submission_markdown
    assert "Wrong draft title" not in submission_markdown


def test_create_submission_minimal_package_ignores_recursive_compile_report_path(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    repeated_compile_path = (
        "studies/002-early-residual-risk/paper/"
        "studies/002-early-residual-risk/paper/"
        "build/compile_report.json"
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
            "pdf_path": "paper/paper.pdf",
            "compile_report_path": repeated_compile_path,
            "bundle_inputs": {
                "compile_report_path": repeated_compile_path,
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["output_root"] == "paper/submission_minimal"
    assert (paper_root / "submission_minimal" / "paper.pdf").exists()


def test_submission_source_contract_signature_changes_when_renderer_contract_changes(
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

    baseline_contract = source_contract.build_submission_minimal_source_contract(**kwargs)
    monkeypatch.setattr(
        source_contract,
        "_controller_renderer_contract_entries",
        lambda: [
            {
                "path": "controller_module://submission_minimal/profile_builders.py",
                "size": 1,
                "mtime_ns": 1,
                "sha256": "1" * 64,
            }
        ],
    )
    changed_contract = source_contract.build_submission_minimal_source_contract(**kwargs)

    assert baseline_contract["controller_renderer_signature"] != changed_contract["controller_renderer_signature"]
    assert baseline_contract["source_signature"] != changed_contract["source_signature"]
