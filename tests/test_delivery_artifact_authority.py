from __future__ import annotations

import importlib
from pathlib import Path


def _write(path: Path, content: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_delivery_authority_sync_blocks_generated_surfaces_as_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_artifact_authority")
    study_root = tmp_path / "studies" / "001-risk"
    generated_paths = (
        _write(study_root / "manuscript" / "current_package" / "manuscript.docx"),
        _write(study_root / "manuscript" / "current_package.zip", "zip\n"),
        _write(study_root / "paper" / "submission_minimal" / "paper.pdf", "%PDF\n"),
    )

    sync = module.build_delivery_authority_sync(study_root=study_root, paths=generated_paths)

    assert sync["status"] == "projection_only"
    assert sync["direct_edit_allowed"] is False
    assert sync["quality_authority_allowed"] is False
    assert sync["dispatch_authority_allowed"] is False
    assert sync["blocked_authority_paths"] == [str(path.resolve()) for path in generated_paths]


def test_delivery_package_layout_preserves_mas_package_semantics(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_artifact_authority")
    package_root = tmp_path / "studies" / "001-risk" / "manuscript" / "current_package"
    manuscript = _write(package_root / "manuscript.docx")
    _write(package_root / "audit" / "submission_manifest.json", "{}\n")
    _write(package_root / "reproducibility" / "source_signature.json", "{}\n")

    artifact = module.classify_delivery_package_layout(manuscript)

    assert artifact == {
        "status": "v2",
        "package_root": str(package_root.resolve()),
        "package_surface": "current_package",
        "section": "human_submission_files",
        "audit_root": str((package_root / "audit").resolve()),
        "reproducibility_root": str((package_root / "reproducibility").resolve()),
        "legacy_root_audit_files_present": False,
        "open_guidance": "open_root_submission_files",
        "audit_guidance": "inspect_audit_and_reproducibility_directories",
        "edit_source_allowed": False,
    }


def test_delivery_manifest_keeps_mas_artifact_authority_hook(tmp_path: Path) -> None:
    delivery_sync = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    shared = importlib.import_module("tests.test_study_delivery_sync_cases.shared")
    paper_root, _study_root = shared.make_delivery_workspace(tmp_path)

    manifest = delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    lifecycle = manifest["artifact_lifecycle"]
    assert lifecycle["surface_kind"] == "study_delivery_sync_lifecycle"
    assert lifecycle["authority_sync"]["status"] == "authority_source_unblocked"
    assert lifecycle["lifecycle_roles"]["submission_minimal"] == (
        "controller_authorized_package_source"
    )
