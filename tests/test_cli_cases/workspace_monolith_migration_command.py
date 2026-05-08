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
