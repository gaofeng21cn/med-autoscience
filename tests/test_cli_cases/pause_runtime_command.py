from .shared import *


def test_removed_grouped_pause_runtime_command_is_removed(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `study`\.$"):
        cli.main(["study", "pause-runtime", "--profile", str(profile_path), "--study-id", "001-risk"])
