from __future__ import annotations

import importlib


def test_opl_tick_followthrough_timeout_is_bounded(monkeypatch) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["timeout"] = kwargs["timeout"]
        raise commands.subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
        )

    monkeypatch.setattr(commands.subprocess, "run", fake_run)

    result = commands._opl_runtime_tick_readback(
        opl_bin="/tmp/opl",
        runtime_request={
            "payload": {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm003",
            }
        },
    )

    assert observed["timeout"] == commands.OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS
    assert observed["timeout"] <= 15
    assert "--hydrate" in observed["command"]
    assert result["status"] == "timeout"
    assert result["reason"] == "opl_tick_followthrough_timeout"
    assert result["followthrough_observation_window_seconds"] == observed["timeout"]
    assert result["can_claim_stage_run_created"] is False
    assert result["can_claim_provider_running"] is False
    assert result["can_claim_paper_progress"] is False
