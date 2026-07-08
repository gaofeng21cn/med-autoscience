from tests.test_cli_cases.shared import (
    annotations,
    argparse,
    builtins,
    importlib,
    json,
    Path,
    sys,
    pytest,
    render_codex_entry_skill,
    render_openclaw_entry_prompt,
    render_public_yaml,
    render_stage_route_contract_guide,
    render_stage_route_contract_payload,
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    build_figure_route,
    write_profile,
)


def test_removed_grouped_pause_runtime_command_is_removed(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `study`\.$"):
        cli.main(["study", "pause-runtime", "--profile", str(profile_path), "--study-id", "001-risk"])
