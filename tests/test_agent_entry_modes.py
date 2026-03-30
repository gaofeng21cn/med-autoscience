from __future__ import annotations

from med_autoscience.agent_entry import load_entry_modes, load_entry_modes_payload


def test_load_entry_modes_returns_five_canonical_modes() -> None:
    modes = load_entry_modes()

    assert len(modes) == 5
    assert tuple(mode.mode_id for mode in modes) == (
        "full_research",
        "literature_scout",
        "idea_exploration",
        "project_optimization",
        "writing_delivery",
    )
    assert all("Claude Code" in mode.compatible_agents for mode in modes)


def test_load_entry_modes_keeps_formal_chain_and_writing_constraints() -> None:
    modes = {mode.mode_id: mode for mode in load_entry_modes()}
    full_research = modes["full_research"]
    writing_delivery = modes["writing_delivery"]

    assert full_research.default_runtime_mode == "managed"
    assert full_research.preconditions == ("workspace/profile available",)
    assert full_research.managed_routes == (
        "doctor",
        "bootstrap",
        "overlay-status",
        "scout",
        "idea",
        "experiment",
        "write",
        "finalize",
    )
    assert full_research.governance_routes == ("decision",)
    assert writing_delivery.lightweight_routes == ("write",)
    assert writing_delivery.auxiliary_routes == ("journal-resolution",)
    assert "submission bundle or final delivery requested" in writing_delivery.upgrade_triggers


def test_load_entry_modes_payload_reads_canonical_agents_and_mode_count() -> None:
    payload = load_entry_modes_payload()

    assert payload["compatible_agents"] == ["Codex", "Claude Code", "OpenClaw"]
    assert len(payload["modes"]) == 5


def test_payload_modes_explicitly_define_managed_entry_actions() -> None:
    payload = load_entry_modes_payload()
    modes = payload["modes"]

    assert isinstance(modes, list)
    for mode in modes:
        assert isinstance(mode, dict)
        assert mode["managed_entry_actions"] == ["doctor", "bootstrap", "overlay-status"]
