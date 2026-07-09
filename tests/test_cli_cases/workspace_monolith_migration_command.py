from __future__ import annotations

from tests.test_cli_cases.shared import importlib, json, Path, write_profile


def test_workspace_monolith_migration_command_stays_no_write_json_plan(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_migrate(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "workspace_monolith_migration", "apply": apply}

    monkeypatch.setattr(
        cli.workspace_monolith_migration,
        "run_workspace_monolith_migration",
        fake_migrate,
    )
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")

    exit_code = cli.main(
        [
            "runtime",
            "workspace-monolith-migrate",
            "--profile",
            str(profile_path),
            "--dry-run",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": False}
    assert payload["surface_kind"] == "workspace_monolith_migration"
    assert payload["apply"] is False
