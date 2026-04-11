from __future__ import annotations

import importlib


def test_hermes_transport_reuses_stable_managed_runtime_transport_contract() -> None:
    hermes = importlib.import_module("med_autoscience.runtime_transport.hermes")
    stable_transport = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    assert hermes.BACKEND_ID == "hermes"
    assert hermes.ENGINE_ID == "hermes"
    assert hermes.DEFAULT_DAEMON_TIMEOUT_SECONDS == stable_transport.DEFAULT_DAEMON_TIMEOUT_SECONDS
    assert hermes.resolve_daemon_url is stable_transport.resolve_daemon_url
    assert hermes.create_quest is stable_transport.create_quest
    assert hermes.resume_quest is stable_transport.resume_quest
    assert hermes.pause_quest is stable_transport.pause_quest
    assert hermes.stop_quest is stable_transport.stop_quest
    assert hermes.get_quest_session is stable_transport.get_quest_session
    assert hermes.inspect_quest_live_runtime is stable_transport.inspect_quest_live_runtime
    assert hermes.inspect_quest_live_execution is stable_transport.inspect_quest_live_execution
    assert hermes.update_quest_startup_context is stable_transport.update_quest_startup_context
    assert hermes.artifact_complete_quest is stable_transport.artifact_complete_quest
    assert hermes.artifact_interact is stable_transport.artifact_interact
