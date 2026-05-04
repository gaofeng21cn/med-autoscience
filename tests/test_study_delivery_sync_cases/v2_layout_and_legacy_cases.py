from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_sync_study_delivery_mirrors_v2_source_manifest_into_v2_current_package(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    source_manifest_path = paper_root / "submission_minimal" / "audit" / "submission_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    current_package_root = study_root / "manuscript" / "current_package"
    mirrored_manifest_path = current_package_root / "audit" / "submission_manifest.json"
    mirrored_manifest = json.loads(mirrored_manifest_path.read_text(encoding="utf-8"))

    assert "audit/submission_manifest.json" in manifest["source_relative_paths"]
    assert "submission_manifest.json" not in manifest["source_relative_paths"]
    assert manifest["delivery_layout"]["layout_version"] == "submission-package.v2"
    assert manifest["delivery_layout"]["source_package_root"] == str(paper_root / "submission_minimal")
    assert manifest["delivery_layout"]["human_package_root"] == str(current_package_root)
    assert manifest["delivery_layout"]["audit_paths"]["submission_manifest"] == str(mirrored_manifest_path)
    assert mirrored_manifest == source_manifest
    assert not (current_package_root / "submission_manifest.json").exists()
    assert not (current_package_root / "evidence_ledger.json").exists()
    assert not (current_package_root / "review" / "review_ledger.json").exists()
    assert not (current_package_root / "controller" / "study_charter.json").exists()


def test_sync_study_delivery_reads_legacy_source_manifest_but_writes_v2_mirror_layout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    source_root = paper_root / "submission_minimal"
    legacy_manifest_path = source_root / "submission_manifest.json"
    source_manifest_path = source_root / "audit" / "submission_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest_path.unlink()
    dump_json(legacy_manifest_path, source_manifest)

    manifest = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )
    status = module.describe_submission_delivery(paper_root=paper_root)

    current_package_root = study_root / "manuscript" / "current_package"
    mirrored_manifest_path = current_package_root / "audit" / "submission_manifest.json"
    copied_manifest_records = [
        record
        for record in manifest["copied_files"]
        if record["target_path"] == str(mirrored_manifest_path.resolve())
    ]

    assert status["status"] == "current"
    assert "submission_manifest.json" in manifest["source_relative_paths"]
    assert "audit/submission_manifest.json" not in manifest["source_relative_paths"]
    assert copied_manifest_records[0]["source_path"] == str(legacy_manifest_path.resolve())
    assert mirrored_manifest_path.exists()
    assert not (current_package_root / "submission_manifest.json").exists()


def test_current_package_zip_has_shallow_v2_layout_without_embedded_package_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    with zipfile.ZipFile(study_root / "manuscript" / "current_package.zip") as archive:
        names = set(archive.namelist())

    assert "audit/submission_manifest.json" in names
    assert "audit/evidence_ledger.json" in names
    assert "reproducibility/source_signature.json" in names
    assert "submission_manifest.json" not in names
    assert "evidence_ledger.json" not in names
    assert "review/review_ledger.json" not in names
    assert "controller/study_charter.json" not in names
    assert not any(name.startswith(("current_package/", "submission_package/", "manuscript/")) for name in names)
