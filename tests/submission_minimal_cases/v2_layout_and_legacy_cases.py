from __future__ import annotations

from .shared import *


def test_describe_submission_minimal_authority_prefers_v2_manifest_over_stale_legacy_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    submission_root = paper_root / "submission_minimal"
    legacy_manifest_path = submission_root / "submission_manifest.json"
    dump_json(
        legacy_manifest_path,
        {
            "schema_version": 1,
            "source_signature": "stale-legacy-root-signature",
            "source_contract": {"source_signature": "stale-legacy-root-signature"},
        },
    )

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["submission_manifest_path"] == str(submission_root / "audit" / "submission_manifest.json")
    assert authority["recorded_source_signature"] != "stale-legacy-root-signature"


def test_describe_submission_minimal_authority_reads_legacy_manifest_when_v2_manifest_is_absent(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    submission_root = paper_root / "submission_minimal"
    legacy_manifest_path = submission_root / "submission_manifest.json"
    (submission_root / "audit" / "submission_manifest.json").unlink()
    dump_json(legacy_manifest_path, manifest)

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["submission_manifest_path"] == str(legacy_manifest_path)
    assert authority["recorded_source_signature"] == manifest["source_signature"]


def test_submission_minimal_v2_layout_records_source_contract_in_reproducibility_docs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_signature_doc = json.loads(
        (submission_root / "reproducibility" / "source_signature.json").read_text(encoding="utf-8")
    )
    source_paths_doc = json.loads(
        (submission_root / "reproducibility" / "source_relative_paths.json").read_text(encoding="utf-8")
    )

    assert source_signature_doc["layout_version"] == "submission-package.v2"
    assert source_signature_doc["package_role"] == "controller_authorized_package_source"
    assert source_signature_doc["source_signature"] == manifest["source_signature"]
    assert source_signature_doc["source_contract"]["source_signature"] == manifest["source_signature"]
    assert source_paths_doc["layout_version"] == "submission-package.v2"
    assert source_paths_doc["package_role"] == "controller_authorized_package_source"
    assert "paper/build/review_manuscript.md" in source_paths_doc["source_relative_paths"]
    assert "paper/submission_minimal/manuscript.docx" not in source_paths_doc["source_relative_paths"]
