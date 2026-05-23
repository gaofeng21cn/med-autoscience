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
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    report = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert report["surface"] == "workspace_authority_migration_audit"
    assert report["dry_run"] is True
    assert report["workspace_count"] == 2
    assert report["study_count"] == 4
    assert report["unclassified_authority_surface"] == 0
    assert report["apply_actions"] == []
    assert report["delete_actions"] == []
    assert report["write_actions"] == []
    assert report["historical_backfill_plan_count"] == 0
    assert {workspace["workspace_style"] for workspace in report["workspaces"]} == {
        "dm_cvd",
        "nf_pitnet",
    }
    assert all(workspace["historical_backfill_plan_count"] == 0 for workspace in report["workspaces"])
    assert all(study["current_package_count"] >= 1 for study in report["studies"])
    assert all(study["submission_minimal_count"] >= 1 for study in report["studies"])
    assert all(study["manifest_count"] >= 2 for study in report["studies"])
    assert all(study["historical_backfill_plan"] is None for study in report["studies"])


def test_migration_audit_projects_stable_ids_timestamps_and_fingerprints(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    first = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)
    second = module.run_migration_audit(workspace_roots=reversed(workspace_roots), dry_run=True)

    assert first == second
    assert first["report_id"].startswith("workspace-authority-migration-audit::")
    assert first["recorded_at"].endswith("+00:00")
    assert first["workspace_fingerprint"].startswith("workspace-migration-audit::")
    assert first["study_fingerprint"].startswith("study-migration-audit::")
    assert len({workspace["workspace_fingerprint"] for workspace in first["workspaces"]}) == 2
    assert all(workspace["recorded_at"] == first["recorded_at"] for workspace in first["workspaces"])
    assert all(study["study_fingerprint"].startswith("study-migration-audit::") for study in first["studies"])
    assert all(study["workspace_fingerprint"].startswith("workspace-migration-audit::") for study in first["studies"])
    assert all(study["recorded_at"] == first["recorded_at"] for study in first["studies"])
    assert all(
        study["delivery_projection_completeness_reason"] == "current_package_and_submission_minimal_present"
        for study in first["studies"]
    )
    assert all(study["delivery_projection_completion_plan"] is None for study in first["studies"])


def test_migration_audit_projects_completion_plan_without_mutation_for_missing_submission_minimal(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_missing_submission_minimal(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert report["unclassified_authority_surface"] == 0
    assert report["action_counts"]["mutating"] == 0
    assert report["apply_actions"] == []
    assert report["delete_actions"] == []
    assert report["write_actions"] == []
    assert report["mutating_actions"] == []
    assert report["delivery_projection_completion_plan_count"] == 1
    study = report["studies"][0]
    assert study["authority_summary"]["unclassified_authority_surface"] == 0
    assert study["current_package_count"] >= 1
    assert study["submission_minimal_count"] == 0
    assert study["lifecycle_classification"] == "delivery_projection_incomplete"
    assert study["delivery_projection_completeness_reason"] == "missing_submission_minimal"
    assert study["delivery_projection_completion_plan"] == {
        "plan_type": "canonical_regeneration",
        "missing_surface": "submission_minimal",
        "manual_patch_allowed": False,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "regenerate_submission_minimal",
            "rerun_publication_gate",
        ],
        "gate_status": "publication_gate_required_before_delivery_complete",
        "mutation_policy": "dry_run_projection_only",
    }


def test_migration_audit_requires_delivery_manifest_lifecycle_hook_before_ready(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_missing_delivery_lifecycle_hook(tmp_path)
    before = _regular_files(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert _regular_files(tmp_path) == before
    assert report["action_counts"]["mutating"] == 0
    assert report["delivery_projection_completion_plan_count"] == 1
    study = report["studies"][0]
    assert study["current_package_count"] >= 1
    assert study["submission_minimal_count"] >= 1
    assert study["lifecycle_classification"] == "delivery_projection_incomplete"
    assert study["delivery_projection_completeness_reason"] == (
        "missing_delivery_manifest_lifecycle_hook_and_publication_refs"
    )
    assert study["delivery_manifest_summary"] == {
        "delivery_manifest_count": 1,
        "lifecycle_hook_present": False,
        "source_signature_present": True,
        "publication_refs_present": False,
    }
    assert study["historical_backfill_plan"] == {
        "plan_type": "delivery_manifest_historical_backfill",
        "read_only": True,
        "missing_surfaces": [
            "delivery_manifest_lifecycle_hook",
            "publication_refs",
        ],
        "missing_lifecycle_hook": True,
        "missing_source_signature": False,
        "missing_publication_refs": True,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "regenerate_delivery_manifest_lifecycle_hook",
            "relink_delivery_manifest_publication_refs",
            "rerun_publication_gate",
        ],
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "manual_patch_allowed": False,
            "allowed_mutating_actions": [],
        },
    }
    assert study["delivery_projection_completion_plan"] == {
        "plan_type": "delivery_manifest_lifecycle_backfill",
        "missing_surface": "delivery_manifest_lifecycle_hook_and_publication_refs",
        "manual_patch_allowed": False,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "backfill_delivery_manifest_lifecycle_hook",
            "backfill_delivery_manifest_publication_refs",
            "rerun_publication_gate",
        ],
        "gate_status": "publication_gate_required_before_delivery_complete",
        "mutation_policy": "dry_run_projection_only",
    }


def test_migration_audit_projects_read_only_historical_backfill_plan_for_legacy_delivery_manifest(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    before = _regular_files(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert _regular_files(tmp_path) == before
    assert report["action_counts"]["mutating"] == 0
    assert report["mutating_actions"] == []
    assert report["historical_backfill_plan_count"] == 1
    assert report["workspaces"][0]["historical_backfill_plan_count"] == 1
    study = report["studies"][0]
    assert study["delivery_manifest_summary"] == {
        "delivery_manifest_count": 1,
        "lifecycle_hook_present": False,
        "source_signature_present": False,
        "publication_refs_present": False,
    }
    assert study["historical_backfill_plan"] == {
        "plan_type": "delivery_manifest_historical_backfill",
        "read_only": True,
        "missing_surfaces": [
            "delivery_manifest_lifecycle_hook",
            "source_signature",
            "publication_refs",
        ],
        "missing_lifecycle_hook": True,
        "missing_source_signature": True,
        "missing_publication_refs": True,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "regenerate_delivery_manifest_lifecycle_hook",
            "recompute_delivery_manifest_source_signature",
            "relink_delivery_manifest_publication_refs",
            "rerun_publication_gate",
        ],
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "manual_patch_allowed": False,
            "allowed_mutating_actions": [],
        },
    }


def test_migration_audit_report_projects_action_counts_and_study_classifications(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    report = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert report["mutation_policy"] == {
        "dry_run_read_only": True,
        "cleanup_apply_supported": False,
    }
    assert report["action_counts"] == {
        "apply": 0,
        "delete": 0,
        "write": 0,
        "mutating": 0,
    }
    assert report["mutating_actions"] == []
    assert all(study["authority_classification"] == "controller_authorized" for study in report["studies"])
    assert all(study["lifecycle_classification"] == "package_and_submission_ready" for study in report["studies"])
    assert all(study["authority_summary"]["unclassified_authority_surface"] == 0 for study in report["studies"])
    assert all(study["lifecycle_summary"]["current_package_count"] >= 1 for study in report["studies"])


def test_migration_audit_reports_v2_legacy_and_unknown_delivery_package_layouts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_mixed_delivery_package_layouts(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert report["delivery_package_layout_status_counts"] == {
        "v2": 1,
        "legacy": 1,
        "unknown": 1,
    }
    workspace = report["workspaces"][0]
    assert workspace["delivery_package_layout_status_counts"] == {
        "v2": 1,
        "legacy": 1,
        "unknown": 1,
    }
    by_study = {study["study_id"]: study for study in report["studies"]}
    assert by_study["008-v2-delivery-layout"]["delivery_package_layout_status"] == "v2"
    assert by_study["008-v2-delivery-layout"]["delivery_package_layout_summary"] == {
        "status": "v2",
        "package_roots": [
            "studies/008-v2-delivery-layout/manuscript/current_package",
            "studies/008-v2-delivery-layout/paper/submission_minimal",
        ],
        "open_submission_files": [
            "studies/008-v2-delivery-layout/manuscript/current_package/manuscript.docx",
            "studies/008-v2-delivery-layout/paper/submission_minimal/manuscript.docx",
            "studies/008-v2-delivery-layout/paper/submission_minimal/paper.pdf",
        ],
        "audit_roots": [
            "studies/008-v2-delivery-layout/manuscript/current_package/audit",
            "studies/008-v2-delivery-layout/paper/submission_minimal/audit",
        ],
        "reproducibility_roots": [
            "studies/008-v2-delivery-layout/manuscript/current_package/reproducibility",
            "studies/008-v2-delivery-layout/paper/submission_minimal/reproducibility",
        ],
        "legacy_root_audit_files": [],
        "unknown_generated_outputs": [],
        "edit_source_allowed": False,
        "guidance": {
            "open_submission_files": "open package-root DOCX/PDF/BIB/figures/tables files",
            "audit": "inspect audit/ for submission_manifest/evidence_ledger/review_ledger/study_charter",
            "reproducibility": "inspect reproducibility/ for source_signature/source_relative_paths/analysis_manifest",
            "edit_source": "delivery package files are projections; edit canonical paper sources instead",
        },
    }
    assert by_study["009-legacy-delivery-layout"]["delivery_package_layout_status"] == "legacy"
    assert by_study["009-legacy-delivery-layout"]["delivery_package_layout_summary"][
        "legacy_root_audit_files"
    ] == [
        "studies/009-legacy-delivery-layout/manuscript/current_package/submission_manifest.json",
        "studies/009-legacy-delivery-layout/paper/submission_minimal/submission_manifest.json",
    ]
    assert by_study["010-unknown-delivery-layout"]["delivery_package_layout_status"] == "unknown"
    assert by_study["010-unknown-delivery-layout"]["delivery_package_layout_summary"][
        "unknown_generated_outputs"
    ] == ["studies/010-unknown-delivery-layout/paper/build/paper.pdf"]
    assert by_study["010-unknown-delivery-layout"]["lifecycle_classification"] == "delivery_projection_incomplete"
    assert by_study["010-unknown-delivery-layout"]["delivery_projection_completeness_reason"] == (
        "unknown_delivery_package_layout"
    )
    assert by_study["010-unknown-delivery-layout"]["delivery_projection_completion_plan"] == {
        "plan_type": "delivery_package_layout_classification",
        "missing_surface": "recognized_delivery_package_layout",
        "manual_patch_allowed": False,
        "canonical_regeneration_path": [
            "refresh_canonical_manuscript_sources",
            "regenerate_submission_package_v2_layout",
            "rerun_publication_gate",
        ],
        "gate_status": "publication_gate_required_before_delivery_complete",
        "mutation_policy": "dry_run_projection_only",
    }


def test_migration_audit_is_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_roots = [
        fixtures.build_dm_cvd_migration_audit_fixture(tmp_path),
        fixtures.build_nf_pitnet_migration_audit_fixture(tmp_path),
    ]

    first = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)
    second = module.run_migration_audit(workspace_roots=workspace_roots, dry_run=True)

    assert second == first


def test_migration_audit_dry_run_does_not_write_delete_or_mutate(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
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


def test_migration_audit_rejects_non_dry_run_apply_mode(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_dm_cvd_migration_audit_fixture(tmp_path)

    try:
        module.run_migration_audit(workspace_roots=[workspace_root], dry_run=False)
    except ValueError as exc:
        assert "dry-run only" in str(exc)
    else:
        raise AssertionError("migration audit accepted non-dry-run mode")


def test_migration_audit_skips_runtime_and_vcs_noise(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_authority_migration_audit")
    workspace_root = fixtures.build_migration_audit_fixture_with_runtime_noise(tmp_path)

    report = module.run_migration_audit(workspace_roots=[workspace_root], dry_run=True)

    assert report["study_count"] == 2
    assert {study["study_id"] for study in report["studies"]} == {
        "001-dm-cvd-mortality-risk",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
