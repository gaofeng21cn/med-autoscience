from __future__ import annotations

from tests.test_study_delivery_sync_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_sync_study_delivery_materializes_submission_root_and_keeps_manifest_under_manuscript(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(
        tmp_path,
        quest_id="002-early-residual-risk-managed-20260402",
        runtime_reentry_study_id="002-early-residual-risk",
    )

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    submission_root = study_root / "submission"
    manifest_path = study_root / "manuscript" / "delivery_manifest.json"

    assert manifest_path.exists()
    assert (submission_root / "manuscript.docx").exists()
    assert (submission_root / "paper.pdf").exists()
    assert (submission_root / "audit" / "submission_manifest.json").exists()
    assert (submission_root / "audit" / "evidence_ledger.json").exists()
    assert (submission_root / "audit" / "review_ledger.json").exists()
    assert (submission_root / "audit" / "study_charter.json").exists()
    assert (submission_root / "figures" / "Figure1.pdf").exists()
    assert (submission_root / "tables" / "Table1.csv").exists()
    assert (study_root / "submission.zip").exists()
    assert manifest["quest_id"] == "002-early-residual-risk-managed-20260402"
    assert manifest["surface_roles"] == {
        "controller_authorized_paper_root": str(paper_root),
        "controller_authorized_package_source_root": str(submission_root),
        "human_facing_delivery_root": str(submission_root),
        "human_facing_current_package_root": str(submission_root),
        "human_facing_current_package_zip": str(study_root / "submission.zip"),
        "auxiliary_evidence_root": None,
        "journal_submission_mirror_root": None,
    }


def test_sync_study_delivery_writes_v2_layout_and_freshness_proof_for_submission_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    eval_id = "publication-eval::002-early-residual-risk::freshness-test"
    dump_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": eval_id,
            "study_id": study_root.name,
        },
    )

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    submission_root = study_root / "submission"
    proof_path = study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))

    assert manifest["delivery_layout"]["layout_version"] == "submission-package.v2"
    assert manifest["delivery_layout"]["human_package_root"] == str(submission_root)
    assert manifest["delivery_layout"]["audit_root"] == str(submission_root / "audit")
    assert manifest["delivery_layout"]["reproducibility_root"] == str(submission_root / "reproducibility")
    assert proof["status"] == "fresh"
    assert proof["source_eval_id"] == eval_id
    assert proof["current_package_root"] == str(submission_root)
    assert proof["current_package_zip"] == str(study_root / "submission.zip")
    assert proof["source_signature"] == manifest["source_signature"]


def test_sync_study_delivery_refreshes_existing_legacy_package_aliases(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    legacy_submission_root = paper_root / "submission_minimal"
    worktree_current_package_root = paper_root.parent / "manuscript" / "current_package"
    fresh_references = "@article{fresh,title={Hong Kong and U.S. adults}}\n"

    write_text(legacy_submission_root / "references.bib", "@article{old,title={stale}}\n")
    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )
    write_text(study_root / "submission" / "references.bib", fresh_references)
    write_text(legacy_submission_root / "references.bib", "@article{old,title={stale}}\n")
    write_text(worktree_current_package_root / "references.bib", "@article{old,title={stale}}\n")

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (legacy_submission_root / "references.bib").read_text(encoding="utf-8") == fresh_references
    assert (worktree_current_package_root / "references.bib").read_text(encoding="utf-8") == fresh_references
    assert (paper_root.parent / "manuscript" / "current_package.zip").exists()
    assert manifest["compatibility_mirrors"] == [
        {
            "role": "legacy_submission_minimal_alias",
            "root": str(legacy_submission_root),
            "source_root": str(study_root / "submission"),
        },
        {
            "role": "legacy_current_package_mirror",
            "root": str(worktree_current_package_root),
            "zip": str(paper_root.parent / "manuscript" / "current_package.zip"),
            "source_root": str(study_root / "submission"),
        },
    ]


def test_describe_submission_delivery_uses_submission_root_and_detects_staleness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    current = module.describe_submission_delivery(paper_root=paper_root)
    assert current["status"] == "current"
    assert current["current_package_root"] == str(study_root / "submission")
    assert current["current_package_zip"] == str(study_root / "submission.zip")

    write_text(paper_root / "submission_minimal" / "manuscript.docx", "updated docx")
    changed = module.describe_submission_delivery(paper_root=paper_root)
    assert changed["status"] == "current"
    assert changed["stale_reason"] is None

    shutil.rmtree(study_root / "submission")
    (study_root / "submission.zip").unlink()
    missing_projection = module.describe_submission_delivery(paper_root=paper_root)
    assert missing_projection["status"] == "stale_projection_missing"
    assert missing_projection["stale_reason"] == "delivery_projection_missing"


def test_stale_notice_materializes_preview_into_submission_root(
    tmp_path: Path,
) -> None:
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

    submission_root = study_root / "submission"
    status_path = study_root / "manuscript" / "delivery_status.json"
    status_payload = json.loads(status_path.read_text(encoding="utf-8"))

    assert stale_sync["status"] == "stale_source_missing"
    assert stale_sync["current_package_root"] == str(submission_root)
    assert (submission_root / "README.md").exists()
    assert (submission_root / "review_manuscript.md").exists()
    assert (submission_root / "compile_report.json").exists()
    assert (submission_root / "submission_checklist.json").exists()
    assert (submission_root / "figures" / "figure_catalog.json").exists()
    assert (submission_root / "tables" / "table_catalog.json").exists()
    assert (study_root / "submission.zip").exists()
    assert status_payload["status"] == "stale_source_missing"
    assert status_payload["stale_reason"] == "delivery_manifest_sources_missing"
    assert status_payload["active_delivery_manifest_path"] == str(study_root / "manuscript" / "delivery_manifest.json")
