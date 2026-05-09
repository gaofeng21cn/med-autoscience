from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_runtime_supervision_status_command_dispatches_scheduler_facade(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_read_supervision_status(*, profile, interval_seconds: int, manager: str) -> dict[str, object]:
        called["profile"] = profile
        called["interval_seconds"] = interval_seconds
        called["manager"] = manager
        return {"status": "loaded", "scheduler_owner": "mas_supervision_scheduler", "adapter_id": "local_launchd"}

    monkeypatch.setattr(cli.supervision_scheduler, "read_supervision_status", fake_read_supervision_status)

    exit_code = cli.main(["runtime", "supervision-status", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["interval_seconds"] == 300
    assert called["manager"] == "local"
    assert json.loads(captured.out)["scheduler_owner"] == "mas_supervision_scheduler"
    assert json.loads(captured.out)["adapter_id"] == "local_launchd"


def test_runtime_ensure_supervision_command_defaults_to_local_manager(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_ensure_supervision(
        *,
        profile,
        interval_seconds: int,
        trigger_now: bool,
        manager: str,
        dry_run: bool,
        write_install_proof: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["interval_seconds"] = interval_seconds
        called["trigger_now"] = trigger_now
        called["manager"] = manager
        called["dry_run"] = dry_run
        called["write_install_proof"] = write_install_proof
        return {"action": "created"}

    monkeypatch.setattr(cli.supervision_scheduler, "ensure_supervision", fake_ensure_supervision)

    exit_code = cli.main(
        [
            "runtime",
            "ensure-supervision",
            "--profile",
            str(profile_path),
            "--interval-seconds",
            "600",
            "--no-trigger-now",
            "--write-install-proof",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["interval_seconds"] == 600
    assert called["trigger_now"] is False
    assert called["manager"] == "local"
    assert called["dry_run"] is False
    assert called["write_install_proof"] is True
    assert json.loads(captured.out)["action"] == "created"


def test_runtime_ensure_supervision_command_allows_explicit_hermes_adapter(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_ensure_supervision(
        *,
        profile,
        interval_seconds: int,
        trigger_now: bool,
        manager: str,
        dry_run: bool,
        write_install_proof: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["manager"] = manager
        called["dry_run"] = dry_run
        return {"action": "created", "adapter_id": "hermes_gateway_cron"}

    monkeypatch.setattr(cli.supervision_scheduler, "ensure_supervision", fake_ensure_supervision)

    exit_code = cli.main(
        [
            "runtime",
            "ensure-supervision",
            "--profile",
            str(profile_path),
            "--manager",
            "hermes",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["manager"] == "hermes"
    assert called["dry_run"] is False
    assert json.loads(captured.out)["adapter_id"] == "hermes_gateway_cron"


def test_runtime_remove_supervision_command_defaults_to_local_manager(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_remove_supervision(*, profile, interval_seconds: int, manager: str) -> dict[str, object]:
        called["profile"] = profile
        called["interval_seconds"] = interval_seconds
        called["manager"] = manager
        return {"removed_job_ids": ["job-001"]}

    monkeypatch.setattr(cli.supervision_scheduler, "remove_supervision", fake_remove_supervision)

    exit_code = cli.main(["runtime", "remove-supervision", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["interval_seconds"] == 300
    assert called["manager"] == "local"
    assert json.loads(captured.out)["removed_job_ids"] == ["job-001"]
