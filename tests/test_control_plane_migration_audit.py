from __future__ import annotations

import importlib
from pathlib import Path

from . import control_plane_fixtures as fixtures


def _regular_files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_migration_audit_dry_run_covers_dm_cvd_and_nf_pitnet_layouts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    report = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert report["surface"] == "control_plane_migration_audit"
    assert report["dry_run"] is True
    assert report["workspace_count"] == 2
    assert report["study_count"] == 4
    assert report["unclassified_authority_surface"] == 0
    assert report["apply_actions"] == []
    assert report["delete_actions"] == []
    assert report["write_actions"] == []
    assert {workspace["workspace_style"] for workspace in report["workspaces"]} == {
        "dm_cvd",
        "nf_pitnet",
    }
    assert all(study["current_package_count"] >= 1 for study in report["studies"])
    assert all(study["submission_minimal_count"] >= 1 for study in report["studies"])
    assert all(study["manifest_count"] >= 2 for study in report["studies"])


def test_migration_audit_is_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    first = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)
    second = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert second == first


def test_migration_audit_dry_run_does_not_write_delete_or_mutate(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]
    before = _regular_files(tmp_path)

    def fail_write(*args, **kwargs):
        raise AssertionError("migration audit dry-run attempted a write")

    monkeypatch.setattr(Path, "write_text", fail_write)
    monkeypatch.setattr(Path, "write_bytes", fail_write)
    monkeypatch.setattr(Path, "unlink", fail_write)

    report = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert report["dry_run"] is True
    assert _regular_files(tmp_path) == before


def test_migration_audit_skips_runtime_and_vcs_noise(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_with_runtime_noise(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert report["study_count"] == 2
    assert {study["study_id"] for study in report["studies"]} == {
        "001-dm-cvd-mortality-risk",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
