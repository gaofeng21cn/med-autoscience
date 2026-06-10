from __future__ import annotations

from . import shared as _shared
from med_autoscience.workspace_paths import DATA_ASSET_LAYER_IDS, DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


DATASET_LAYER_NAMES = DATA_ASSET_LAYER_IDS
DATA_ASSET_REGISTRY_DIRS = tuple(path.as_posix() for path in DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS)


def test_init_data_assets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"private": {"release_count": 1}, "public": {"dataset_count": 0}}

    monkeypatch.setattr(cli.data_assets, "init_data_assets", fake_init)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(["data", "init-assets", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert '"release_count": 1' in captured.out
    for layer_name in DATASET_LAYER_NAMES:
        assert (workspace_root / "data" / "datasets" / layer_name).is_dir()
    for registry_dir in DATA_ASSET_REGISTRY_DIRS:
        assert (workspace_root / "memory" / "portfolio" / "data_assets" / registry_dir).is_dir()
    assert payload["layout"]["schema_version"] == 2
    assert payload["layout"]["layout_ready"] is True
    assert payload["layout"]["missing_directories"] == []
    assert payload["layout"]["body_plane"]["layer_names"] == list(DATASET_LAYER_NAMES)
    assert payload["layout"]["registry_lineage_plane"]["directory_names"] == list(DATA_ASSET_REGISTRY_DIRS)
    assert payload["layout"]["study_binding_plane"]["study_yaml_pattern"] == "studies/<study-id>/study.yaml"
    assert payload["layout"]["study_binding_plane"]["data_body_allowed"] is False


def test_init_workspace_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init_workspace(
        *,
        workspace_root: Path,
        workspace_name: str,
        dry_run: bool,
        force: bool,
        default_publication_profile: str,
        default_citation_style: str,
        hermes_agent_repo_root: Path | None,
        hermes_home_root: Path | None,
        initialize_git: bool,
    ) -> dict:
        called["workspace_root"] = workspace_root
        called["workspace_name"] = workspace_name
        called["dry_run"] = dry_run
        called["force"] = force
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        called["hermes_agent_repo_root"] = hermes_agent_repo_root
        called["hermes_home_root"] = hermes_home_root
        called["initialize_git"] = initialize_git
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "dry_run": dry_run,
            "force": force,
            "initialize_git": initialize_git,
        }

    monkeypatch.setattr(cli.workspace_init_controller, "init_workspace", fake_init_workspace)

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--workspace-name",
            "diabetes",
            "--dry-run",
            "--force",
            "--hermes-agent-repo-root",
            str(tmp_path / "_external" / "hermes-agent"),
            "--hermes-home-root",
            str(tmp_path / ".hermes"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["workspace_name"] == "diabetes"
    assert called["dry_run"] is True
    assert called["force"] is True
    assert called["default_publication_profile"] == "general_medical_journal"
    assert called["default_citation_style"] == "AMA"
    assert called["hermes_agent_repo_root"] == tmp_path / "_external" / "hermes-agent"
    assert called["hermes_home_root"] == tmp_path / ".hermes"
    assert called["initialize_git"] is False
    assert '"workspace_name": "diabetes"' in captured.out
    assert '"initialize_git": false' in captured.out

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace-with-git"),
            "--workspace-name",
            "diabetes",
            "--with-git",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace-with-git"
    assert called["initialize_git"] is True
    assert '"initialize_git": true' in captured.out
def test_data_assets_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"layout_ready": True, "private": {"release_count": 2}}

    monkeypatch.setattr(cli.data_assets, "data_assets_status", fake_status)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(["data", "assets-status", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert '"layout_ready": true' in captured.out
    assert payload["layout"]["layout_ready"] is False
    assert payload["layout"]["missing_directories"]
    assert payload["layout"]["body_plane"]["layer_names"] == list(DATASET_LAYER_NAMES)
    assert payload["layout"]["registry_lineage_plane"]["directory_names"] == list(DATA_ASSET_REGISTRY_DIRS)


def test_assess_data_asset_impact_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_assess(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"study_count": 1, "studies": [{"study_id": "002-early-risk", "status": "review_needed"}]}

    monkeypatch.setattr(cli.data_assets, "assess_data_asset_impact", fake_assess)

    exit_code = cli.main(["data", "assess-asset-impact", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"review_needed"' in captured.out
def test_diff_private_release_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_diff(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> dict:
        called["workspace_root"] = workspace_root
        called["family_id"] = family_id
        called["from_version"] = from_version
        called["to_version"] = to_version
        return {"report_path": "/tmp/report.json", "family_id": family_id}

    monkeypatch.setattr(cli.data_assets, "build_private_release_diff", fake_diff)

    exit_code = cli.main(
        [
            "data",
            "diff-private-release",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--family-id",
            "master",
            "--from-version",
            "v2026-03-28",
            "--to-version",
            "v2026-04-10",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["family_id"] == "master"
    assert called["from_version"] == "v2026-03-28"
    assert called["to_version"] == "v2026-04-10"
    assert "/tmp/report.json" in captured.out
def test_validate_public_registry_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_validate(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"invalid_dataset_count": 0, "dataset_count": 2}

    monkeypatch.setattr(cli.data_assets, "validate_public_registry", fake_validate)

    exit_code = cli.main(["data", "validate-public-registry", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"dataset_count": 2' in captured.out
