from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_runtime_supervision_grouped_commands_are_not_public_aliases(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    for argv in (
        ["runtime", "supervision-status", "--profile", str(profile_path)],
        ["runtime", "ensure-supervision", "--profile", str(profile_path)],
        ["runtime", "remove-supervision", "--profile", str(profile_path)],
    ):
        with pytest.raises(SystemExit) as excinfo:
            cli.main(argv)
        assert excinfo.value.code in {2, "Grouped command requires a supported subcommand under `runtime`."}


def test_runtime_supervision_flat_commands_are_not_public_aliases(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    for argv in (
        ["runtime-supervision-status", "--profile", str(profile_path)],
        ["runtime-ensure-supervision", "--profile", str(profile_path)],
        ["runtime-remove-supervision", "--profile", str(profile_path)],
    ):
        with pytest.raises(SystemExit) as excinfo:
            cli.main(argv)
        assert excinfo.value.code == 2


def test_cli_has_no_opl_unique_control_plane_boundary_runtime_callable() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    assert not hasattr(cli, "opl_unique_control_plane_boundary")
