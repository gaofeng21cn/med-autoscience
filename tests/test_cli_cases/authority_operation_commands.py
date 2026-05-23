from __future__ import annotations

from . import shared as _shared


globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_delivery_authority_backfill_apply_command_passes_authority_snapshot_json(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    snapshot = {
        "surface": "authority_snapshot",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "artifact_authority": {"epoch": "artifact-1"},
        },
        "route_authorization": {"bundle_build_allowed": True},
    }

    def fake_run_backfill_apply(*, workspace_roots, apply: bool, authority_snapshot=None) -> dict[str, object]:
        called.update({
            "workspace_roots": list(workspace_roots),
            "apply": apply,
            "authority_snapshot": authority_snapshot,
        })
        return {"surface": "delivery_authority_backfill_apply", "apply": apply, "action_counts": {"mutating": 0}}

    monkeypatch.setattr(cli.delivery_authority_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    exit_code = cli.main([
        "delivery-authority-backfill-apply",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--apply",
        "--authority-snapshot-json",
        json.dumps(snapshot),
    ])

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": True,
        "authority_snapshot": snapshot,
    }
    assert json.loads(capsys.readouterr().out)["surface"] == "delivery_authority_backfill_apply"


def test_storage_governance_report_command_projects_read_only_surface(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_lifecycle_operations_report(*, workspace_roots, deep, max_files, max_seconds) -> dict[str, object]:
        called.update({
            "workspace_roots": list(workspace_roots),
            "deep": deep,
            "max_files": max_files,
            "max_seconds": max_seconds,
        })
        return {
            "surface": "artifact_lifecycle_report",
            "mutation_policy": {"read_only": True},
            "workspaces": [],
        }

    monkeypatch.setattr(
        cli.artifact_lifecycle_operations_report,
        "run_lifecycle_operations_report",
        fake_run_lifecycle_operations_report,
    )

    exit_code = cli.main([
        "storage-governance-report",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--deep",
        "--max-files",
        "10",
        "--max-seconds",
        "1.5",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "deep": True,
        "max_files": 10,
        "max_seconds": 1.5,
    }
    assert payload["surface"] == "storage_governance_report"
    assert payload["source_surface"] == "artifact_lifecycle_report"


def test_control_plane_cleanup_commands_are_not_public_cli(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit):
        cli.main([
            "control-plane-cleanup-apply",
            "--workspace-root",
            str(tmp_path / "workspace"),
        ])
    assert "invalid choice" in capsys.readouterr().err

    with pytest.raises(SystemExit):
        cli.main([
            "control-plane-safe-cache-cleanup-apply",
            "--workspace-root",
            str(tmp_path / "workspace"),
        ])
    assert "invalid choice" in capsys.readouterr().err
