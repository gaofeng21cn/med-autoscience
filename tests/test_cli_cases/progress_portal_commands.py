from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_workspace_progress_portal_grouped_command_materializes(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    class FakeProgressPortal:
        @staticmethod
        def materialize_progress_portal(**kwargs):
            calls.update(kwargs)
            return {
                "status": "materialized",
                "payload_path": str(tmp_path / "artifacts" / "runtime" / "progress_portal" / "latest.json"),
                "html_path": str(tmp_path / "ops" / "mas" / "progress" / "index.html"),
                "hosted_package_path": str(
                    tmp_path / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
                ),
                "opl_handoff": {
                    "payload_ref": str(tmp_path / "artifacts" / "runtime" / "progress_portal" / "latest.json"),
                    "deep_link": str(tmp_path / "ops" / "mas" / "progress" / "index.html"),
                },
            }

    monkeypatch.setattr(cli, "progress_portal", FakeProgressPortal)

    exit_code = cli.main(
        [
            "workspace",
            "progress-portal",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--open",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "materialized"
    assert calls["profile"].name == "nfpitnet"
    assert calls["profile_ref"] == profile_path
    assert calls["study_id"] == "001-risk"
    assert calls["study_root"] is None
    assert calls["entry_mode"] is None
    assert calls["open_browser"] is True
    assert payload["opl_handoff"]["deep_link"] == str(tmp_path / "ops" / "mas" / "progress" / "index.html")
    assert payload["opl_handoff"]["payload_ref"] == str(
        tmp_path / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    )
    assert payload["hosted_package_path"] == str(
        tmp_path / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
    )


def test_workspace_progress_portal_grouped_command_materializes_workspace_overview_without_study_selector(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    class FakeProgressPortal:
        @staticmethod
        def materialize_progress_portal(**kwargs):
            calls.update(kwargs)
            return {
                "status": "materialized",
                "payload_path": str(tmp_path / "artifacts" / "runtime" / "progress_portal" / "latest.json"),
                "html_path": str(tmp_path / "ops" / "mas" / "progress" / "index.html"),
                "hosted_package_path": str(
                    tmp_path / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
                ),
            }

    monkeypatch.setattr(cli, "progress_portal", FakeProgressPortal)

    exit_code = cli.main(["workspace", "progress-portal", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["status"] == "materialized"
    assert calls["study_id"] is None
    assert calls["study_root"] is None


def test_workspace_progress_portal_grouped_command_serves_read_only(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    class FakeProgressPortal:
        @staticmethod
        def serve_progress_portal(**kwargs):
            calls.update(kwargs)
            return {
                "status": "serving",
                "url": "http://127.0.0.1:4201",
                "html_path": str(tmp_path / "ops" / "mas" / "progress" / "index.html"),
                "hosted_package_path": str(
                    tmp_path / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
                ),
            }

    monkeypatch.setattr(cli, "progress_portal", FakeProgressPortal)

    exit_code = cli.main(
        [
            "workspace",
            "progress-portal",
            "--profile",
            str(profile_path),
            "--study-root",
            str(tmp_path / "studies" / "001-risk"),
            "--serve",
            "--host",
            "127.0.0.1",
            "--port",
            "4201",
            "--interval-seconds",
            "15",
            "--format",
            "text",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "http://127.0.0.1:4201" in captured.out
    assert "hosted_package:" in captured.out
    assert calls["profile"].name == "nfpitnet"
    assert calls["profile_ref"] == profile_path
    assert calls["study_id"] is None
    assert calls["study_root"] == tmp_path / "studies" / "001-risk"
    assert calls["entry_mode"] is None
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 4201
    assert calls["interval_seconds"] == 15
    assert calls["open_browser"] is False
