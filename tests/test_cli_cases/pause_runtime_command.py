from .shared import *


def test_pause_study_runtime_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_pause(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        force: bool,
        source: str,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["force"] = force
        called["source"] = source
        return {
            "decision": "pause",
            "reason": "human_takeover_requested",
            "study_id": study_id,
            "quest_status": "paused",
        }

    monkeypatch.setattr(cli.domain_status_projection, "pause_study_runtime", fake_pause)

    exit_code = cli.main(
        [
            "study",
            "pause-runtime",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--entry-mode",
            "full_research",
            "--force",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] == "full_research"
    assert called["force"] is True
    assert called["source"] == "cli"
    assert json.loads(captured.out)["quest_status"] == "paused"
