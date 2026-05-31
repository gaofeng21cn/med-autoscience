from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_describe_submission_delivery_flags_stale_when_authority_source_disappears(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(paper_root / "submission_minimal")
    write_text(paper_root / "submission_minimal" / "README.md", "# Placeholder\n")
    write_text(paper_root / "submission_minimal" / "journal_declarations.md", "# Placeholder\n")

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "stale_source_missing"
    assert result["stale_reason"] == "current_submission_source_missing"
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")
    assert result["missing_source_paths"] != []


def test_describe_submission_delivery_flags_stale_when_current_package_projection_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(study_root / "manuscript" / "current_package")
    (study_root / "manuscript" / "current_package.zip").unlink()

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["status"] == "stale_projection_missing"
    assert result["stale_reason"] == "delivery_projection_missing"


def test_describe_submission_delivery_flags_stale_when_authority_package_changes_under_same_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "updated docx")

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "stale_source_changed"
    assert result["stale_reason"] == "delivery_manifest_source_changed"
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_when_only_authority_source_mtime_changes(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    source_path = paper_root / "submission_minimal" / "manuscript.docx"
    stat = source_path.stat()
    os.utime(source_path, ns=(stat.st_atime_ns + 1_000_000_000, stat.st_mtime_ns + 1_000_000_000))

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_with_generated_current_package_readme(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    (paper_root / "submission_minimal" / "README.md").write_text(
        "# Canonical Submission Package\n\nAuthoritative paper-owned package.\n",
        encoding="utf-8",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_describe_submission_delivery_keeps_current_when_evidence_ledger_updated_at_changes_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    evidence_ledger_path = paper_root / "evidence_ledger.json"
    evidence_ledger = json.loads(evidence_ledger_path.read_text(encoding="utf-8"))
    evidence_ledger["updated_at"] = "2026-03-29T04:16:28+00:00"
    evidence_ledger_path.write_text(
        json.dumps(evidence_ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    evidence_ledger["updated_at"] = "2026-03-29T05:16:28+00:00"
    evidence_ledger_path.write_text(
        json.dumps(evidence_ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = module.describe_submission_delivery(paper_root=paper_root)

    assert result["applicable"] is True
    assert result["status"] == "current"
    assert result["stale_reason"] is None
    assert result["delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
    assert result["current_package_root"] == str(study_root / "manuscript" / "current_package")


def test_materialize_submission_delivery_stale_notice_clears_stale_mirror_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    shutil.rmtree(paper_root / "submission_minimal" / "figures")
    shutil.rmtree(paper_root / "submission_minimal" / "tables")

    result = module.describe_submission_delivery(paper_root=paper_root)
    stale_sync = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason=str(result["stale_reason"]),
        missing_source_paths=list(result["missing_source_paths"]),
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "dispatch_gate": {
                    "state": "open",
                    "dispatch_allowed": True,
                    "blocking_reasons": [],
                },
                "route_authorization": {
                    "authorized": True,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": True,
                    "runtime_recovery_allowed": True,
                },
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
            },
        },
    )

    manuscript_root = study_root / "manuscript"
    status_path = manuscript_root / "delivery_status.json"

    assert stale_sync["status"] == "stale_source_missing"
    assert stale_sync["current_package_root"] == str(manuscript_root / "current_package")
    assert (manuscript_root / "manuscript.docx").exists()
    assert (manuscript_root / "paper.pdf").exists()
    assert (manuscript_root / "audit" / "submission_manifest.json").exists()
    assert not (manuscript_root / "submission_package").exists()
    assert not (manuscript_root / "submission_package.zip").exists()
    assert (manuscript_root / "current_package" / "README.md").exists()
    assert (manuscript_root / "current_package.zip").exists()
    assert "audit preview" in (
        manuscript_root / "current_package" / "README.md"
    ).read_text(encoding="utf-8")
    assert (manuscript_root / "current_package" / "review_manuscript.md").exists()
    assert (manuscript_root / "current_package" / "compile_report.json").exists()
    assert (manuscript_root / "current_package" / "submission_checklist.json").exists()
    assert (manuscript_root / "current_package" / "figures" / "figure_catalog.json").exists()
    assert (manuscript_root / "current_package" / "figures" / "F1_authority_preview.pdf").exists()
    assert (manuscript_root / "current_package" / "tables" / "table_catalog.json").exists()
    assert (manuscript_root / "current_package" / "tables" / "T1_authority_preview.csv").exists()
    status_payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert status_payload["status"] == "stale_source_missing"
    assert status_payload["stale_reason"] == "delivery_manifest_sources_missing"
    assert status_payload["preview_mode"] == "authority_audit_preview"
    assert status_payload["submission_ready"] is False
    assert status_payload["active_delivery_manifest_path"] == str(manuscript_root / "delivery_manifest.json")
    assert status_payload["missing_source_paths"] != []


def test_materialize_submission_delivery_stale_notice_blocks_without_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )
    manuscript_root = study_root / "manuscript"
    baseline_status = manuscript_root / "delivery_status.json"
    assert not baseline_status.exists()

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        missing_source_paths=[str(paper_root / "submission_minimal" / "submission_manifest.json")],
    )

    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["action"] == "submission_notice_materialize"
    assert "authority_snapshot_missing" in result["authority_route_gate"]["blocking_reasons"]
    assert not baseline_status.exists()
    assert (manuscript_root / "current_package" / "manuscript.docx").exists()


def test_materialize_submission_delivery_stale_notice_allows_open_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "dispatch_gate": {
                    "state": "open",
                    "dispatch_allowed": True,
                    "blocking_reasons": [],
                },
                "route_authorization": {
                    "authorized": True,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": True,
                    "runtime_recovery_allowed": True,
                },
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
            },
        },
    )

    manuscript_root = study_root / "manuscript"
    assert result["status"] == "stale_source_missing"
    assert result["authority_route_gate"]["action"] == "submission_notice_materialize"
    assert result["authority_route_gate"]["authorized"] is True
    assert (manuscript_root / "delivery_status.json").exists()


def test_materialize_submission_delivery_stale_notice_blocks_projection_only_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        route_context={"projection_only": True},
    )

    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["projection_only"] is True
    assert "projection_only_write_blocked" in result["authority_route_gate"]["blocking_reasons"]
    assert not (study_root / "manuscript" / "delivery_status.json").exists()
