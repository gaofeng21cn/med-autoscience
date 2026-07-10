from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write(path: Path, content: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_artifact_lifecycle_reads_opl_projection_without_scanning_workspace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"

    missing = module.read_opl_artifact_lifecycle_refs(study_root=study_root)

    assert missing["status"] == "opl_projection_required"
    assert missing["refs"] == {}
    assert missing["authority_boundary"]["mas_scans_workspace_for_lifecycle"] is False

    index_path = study_root / "control" / "opl" / "artifact_lifecycle" / "artifact_lifecycle_index.json"
    _write(
        index_path,
        json.dumps(
            {
                "surface_kind": "opl_workspace_artifact_lifecycle_index",
                "status": "healthy",
                "refs": {
                    "memory_lifecycle": "control/opl/artifact_lifecycle/memory_lifecycle.json",
                    "output_lifecycle": "control/opl/artifact_lifecycle/output_lifecycle.json",
                },
            }
        ),
    )

    available = module.read_opl_artifact_lifecycle_refs(study_root=study_root)

    assert available["status"] == "available"
    assert available["lifecycle_status"] == "healthy"
    assert available["refs"] == {
        "memory_lifecycle": "control/opl/artifact_lifecycle/memory_lifecycle.json",
        "output_lifecycle": "control/opl/artifact_lifecycle/output_lifecycle.json",
    }
    assert available["opl_owner_surface_ref"].endswith("workspace-artifact-lifecycle.ts")


def test_artifact_lifecycle_report_consumes_declared_opl_projects_without_discovery(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.artifact_lifecycle_operations_report"
    )
    workspace_root = tmp_path / "workspace"
    declared_root = workspace_root / "projects" / "study-001"
    undeclared_root = workspace_root / "projects" / "study-hidden"
    _write(
        workspace_root / "workspace_index.json",
        json.dumps(
            {
                "surface_kind": "opl_workspace_index",
                "version": "workspace-index.v1",
                "projects": [
                    {
                        "project_id": "study-001",
                        "project_root": "projects/study-001",
                    }
                ],
            }
        ),
    )
    for project_root, status in (
        (declared_root, "passed"),
        (undeclared_root, "must-not-be-discovered"),
    ):
        _write(
            project_root
            / "control"
            / "opl"
            / "artifact_lifecycle"
            / "artifact_lifecycle_index.json",
            json.dumps(
                {
                    "surface_kind": "opl_workspace_artifact_lifecycle_index",
                    "status": status,
                    "refs": {
                        "output_lifecycle": (
                            "control/opl/artifact_lifecycle/output_lifecycle.json"
                        )
                    },
                }
            ),
        )

    report = report_module.run_lifecycle_operations_report(
        workspace_roots=[workspace_root],
        deep=True,
        max_files=1,
        max_seconds=0.01,
    )

    assert report["surface_kind"] == "mas_artifact_lifecycle_refs_report"
    assert report["project_count"] == 1
    assert report["available_project_count"] == 1
    assert report["scan_policy"] == {
        "inventory_owner": "one-person-lab",
        "inventory_source": "opl_workspace_artifact_lifecycle_index",
        "recursive_scan_enabled": False,
        "filesystem_discovery_enabled": False,
        "mas_builds_lifecycle_registry": False,
        "mas_computes_restore_or_cleanup_readiness": False,
    }
    project = report["workspaces"][0]["projects"][0]
    assert project["project_id"] == "study-001"
    assert project["lifecycle_status"] == "passed"
    assert "study-hidden" not in json.dumps(report)
    assert report["requested_options"]["options_affect_inventory"] is False
    assert report["authority_boundary"]["mas_scans_workspace_for_lifecycle"] is False


def test_delivery_authority_sync_blocks_generated_surfaces_as_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
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


def test_delivery_package_layout_projection_preserves_domain_package_semantics(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    package_root = study_root / "manuscript" / "current_package"
    manuscript = _write(package_root / "manuscript.docx")
    _write(package_root / "audit" / "submission_manifest.json", "{}\n")
    _write(package_root / "reproducibility" / "source_signature.json", "{}\n")

    artifact = module.classify_artifact(path=manuscript, study_root=study_root)

    assert artifact["role"] == "derived_projection"
    assert artifact["edit_source_allowed"] is False
    assert artifact["quality_authority_allowed"] is False
    assert artifact["delivery_package_layout"] == {
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
