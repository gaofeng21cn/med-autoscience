from __future__ import annotations

import importlib

import pytest

from .shared import write_profile


def test_launch_study_command_rejects_unsupported_entry_mode(monkeypatch, tmp_path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    def fake_launch(**kwargs) -> dict:
        raise ValueError("study launch entry mode 不支持: managed; supported_entry_modes=direct, opl-handoff")

    monkeypatch.setattr(cli.product_entry, "launch_study", fake_launch)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "study",
                "launch",
                "--profile",
                str(profile_path),
                "--study-id",
                "001-risk",
                "--entry-mode",
                "managed",
                "--format",
                "json",
            ]
        )
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "study launch entry mode 不支持: managed" in captured.err
