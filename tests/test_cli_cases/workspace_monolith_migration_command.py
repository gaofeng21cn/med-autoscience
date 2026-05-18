from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_runtime_workspace_monolith_migrate_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_workspace_monolith_migration(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "workspace_monolith_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.workspace_monolith_migration,
        "run_workspace_monolith_migration",
        fake_run_workspace_monolith_migration,
    )

    exit_code = cli.main(
        [
            "runtime",
            "workspace-monolith-migrate",
            "--profile",
            str(profile_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": True}
    assert json.loads(captured.out)["mode"] == "apply"


def test_workspace_legacy_physical_cleanup_audit_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_build_workspace_legacy_physical_cleanup_audit(*, profile_path: Path) -> dict[str, object]:
        called["profile_path"] = profile_path
        return {"surface_kind": "workspace_legacy_physical_cleanup_audit", "mode": "audit_only"}

    monkeypatch.setattr(
        cli.workspace_legacy_physical_cleanup,
        "build_workspace_legacy_physical_cleanup_audit",
        fake_build_workspace_legacy_physical_cleanup_audit,
    )

    exit_code = cli.main(
        [
            "workspace-legacy-physical-cleanup-audit",
            "--profile",
            str(profile_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path}
    assert json.loads(captured.out)["mode"] == "audit_only"


def test_workspace_legacy_physical_cleanup_apply_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_apply_workspace_legacy_physical_cleanup(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "workspace_legacy_physical_cleanup_apply", "mode": "apply"}

    monkeypatch.setattr(
        cli.workspace_legacy_physical_cleanup,
        "apply_workspace_legacy_physical_cleanup",
        fake_apply_workspace_legacy_physical_cleanup,
    )

    exit_code = cli.main(
        [
            "workspace-legacy-physical-cleanup-apply",
            "--profile",
            str(profile_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": True}
    assert json.loads(captured.out)["mode"] == "apply"


def test_publication_clean_authority_migration_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_paper_authority_clean_migration(
        *,
        profile_path: Path,
        study_ids: tuple[str, ...],
        apply: bool,
    ) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["study_ids"] = study_ids
        called["apply"] = apply
        return {"surface_kind": "paper_authority_clean_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.paper_authority_migration,
        "run_paper_authority_clean_migration",
        fake_run_paper_authority_clean_migration,
    )

    exit_code = cli.main(
        [
            "publication",
            "clean-authority-migration",
            "--profile",
            str(profile_path),
            "--studies",
            "002-dm-china-us-mortality-attribution",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "profile_path": profile_path,
        "study_ids": ("002-dm-china-us-mortality-attribution",),
        "apply": True,
    }
    assert json.loads(captured.out)["surface_kind"] == "paper_authority_clean_migration"


def test_runtime_study_config_clean_migration_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_run_study_config_clean_migration(
        *,
        profile_path: Path,
        study_ids: tuple[str, ...],
        apply: bool,
    ) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["study_ids"] = study_ids
        called["apply"] = apply
        return {"surface_kind": "study_config_clean_migration", "mode": "apply"}

    monkeypatch.setattr(
        cli.study_config_migration,
        "run_study_config_clean_migration",
        fake_run_study_config_clean_migration,
    )

    exit_code = cli.main(
        [
            "runtime",
            "study-config-clean-migration",
            "--profile",
            str(profile_path),
            "--studies",
            "001-dm-cvd-mortality-risk",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "profile_path": profile_path,
        "study_ids": ("001-dm-cvd-mortality-risk",),
        "apply": True,
    }
    assert json.loads(captured.out)["surface_kind"] == "study_config_clean_migration"


def test_agent_lab_medical_manuscript_quality_suite_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    called: dict[str, object] = {}

    def fake_materialize_medical_manuscript_quality_agent_lab_suite(
        *,
        study_root: Path,
        reviewer_feedback_ref: str | None = None,
    ) -> dict[str, object]:
        called["study_root"] = study_root
        called["reviewer_feedback_ref"] = reviewer_feedback_ref
        return {
            "surface_kind": "mas_agent_lab_medical_manuscript_quality_suite",
            "status": "materialized",
        }

    monkeypatch.setattr(
        cli.agent_lab_medical_manuscript_quality,
        "materialize_medical_manuscript_quality_agent_lab_suite",
        fake_materialize_medical_manuscript_quality_agent_lab_suite,
    )

    exit_code = cli.main(
        [
            "agent-lab-medical-manuscript-quality-suite",
            "--study-root",
            str(study_root),
            "--reviewer-feedback-ref",
            "task-intake:gpt-5.5-review",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "study_root": study_root,
        "reviewer_feedback_ref": "task-intake:gpt-5.5-review",
    }
    assert json.loads(captured.out)["surface_kind"] == "mas_agent_lab_medical_manuscript_quality_suite"
