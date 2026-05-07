from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_apply_data_asset_update_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    payload_file = tmp_path / "payload.json"
    payload_file.write_text('{"action":"refresh_all"}\n', encoding="utf-8")

    def fake_apply(*, workspace_root: Path, payload: dict) -> dict:
        called["workspace_root"] = workspace_root
        called["payload"] = payload
        return {"status": "applied", "action": payload["action"]}

    monkeypatch.setattr(cli.data_asset_updates_controller, "apply_data_asset_update", fake_apply)

    exit_code = cli.main(
        [
            "data",
            "apply-asset-update",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["payload"] == {"action": "refresh_all"}
    assert '"action": "refresh_all"' in captured.out


def test_load_json_payload_from_args_rejects_non_object_payload_json() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    args = argparse.Namespace(payload_file=None, payload_json='["not", "an", "object"]')
    with pytest.raises(SystemExit, match="JSON payload must be an object"):
        cli._load_json_payload_from_args(args)


def test_load_json_payload_from_args_accepts_object_payload_json() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    args = argparse.Namespace(payload_file=None, payload_json='{"action":"refresh_all"}')
    assert cli._load_json_payload_from_args(args) == {"action": "refresh_all"}
