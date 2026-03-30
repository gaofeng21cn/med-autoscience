from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.agent_entry import load_entry_modes, load_entry_modes_payload
from med_autoscience.agent_entry import modes as modes_module


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
    assert full_research.managed_entry_actions == ("doctor", "bootstrap", "overlay-status", "ensure-study-runtime")
    assert full_research.managed_routes == (
        "doctor",
        "bootstrap",
        "overlay-status",
        "scout",
        "idea",
        "write",
        "finalize",
    )
    assert full_research.startup_boundary_gated_routes == (
        "baseline",
        "experiment",
        "analysis-campaign",
    )
    assert full_research.governance_routes == ("decision",)
    assert writing_delivery.lightweight_routes == ("write",)
    assert writing_delivery.startup_boundary_gated_routes == ()
    assert writing_delivery.auxiliary_routes == ("journal-resolution",)
    assert "submission bundle or final delivery requested" in writing_delivery.upgrade_triggers


def test_load_entry_modes_payload_reads_canonical_agents_and_mode_count() -> None:
    payload = load_entry_modes_payload()

    assert payload["compatible_agents"] == ["Codex", "Claude Code", "OpenClaw"]
    assert len(payload["modes"]) == 5


def test_load_entry_modes_preserves_mode_level_managed_entry_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    def _payload_with_distinct_entry_actions() -> dict[str, object]:
        return {
            "compatible_agents": ["Codex", "Claude Code", "OpenClaw"],
            "modes": [
                {
                    "mode_id": "full_research",
                    "display_name": "Full Research",
                    "default_runtime_mode": "managed",
                    "preconditions": ["workspace/profile available"],
                    "lightweight_scope": "none",
                    "managed_entry_actions": ["doctor", "bootstrap", "ensure-study-runtime"],
                    "lightweight_routes": [],
                    "managed_routes": [
                        "doctor",
                        "bootstrap",
                        "overlay-status",
                        "scout",
                        "idea",
                        "write",
                        "finalize",
                    ],
                    "startup_boundary_gated_routes": ["baseline", "experiment", "analysis-campaign"],
                    "governance_routes": ["decision"],
                    "auxiliary_routes": [],
                    "upgrade_triggers": [],
                },
                {
                    "mode_id": "writing_delivery",
                    "display_name": "Writing Delivery",
                    "default_runtime_mode": "lightweight",
                    "preconditions": ["workspace/profile available"],
                    "lightweight_scope": "manuscript and delivery packaging",
                    "managed_entry_actions": ["doctor", "overlay-status", "ensure-study-runtime"],
                    "lightweight_routes": ["write"],
                    "managed_routes": ["doctor", "bootstrap", "overlay-status", "write", "finalize"],
                    "startup_boundary_gated_routes": [],
                    "governance_routes": [],
                    "auxiliary_routes": ["journal-resolution"],
                    "upgrade_triggers": ["submission bundle or final delivery requested"],
                },
            ],
        }

    monkeypatch.setattr(modes_module, "load_entry_modes_payload", _payload_with_distinct_entry_actions)

    modes = {mode.mode_id: mode for mode in load_entry_modes()}

    assert modes["full_research"].managed_entry_actions == ("doctor", "bootstrap", "ensure-study-runtime")
    assert modes["writing_delivery"].managed_entry_actions == ("doctor", "overlay-status", "ensure-study-runtime")


def test_payload_and_typed_loader_use_top_level_compatible_agents() -> None:
    payload = load_entry_modes_payload()
    modes_payload = payload["modes"]
    assert isinstance(modes_payload, list)
    for mode in modes_payload:
        assert isinstance(mode, dict)
        assert "compatible_agents" not in mode

    canonical_agents = tuple(payload["compatible_agents"])
    modes = load_entry_modes()
    assert all(mode.compatible_agents == canonical_agents for mode in modes)


def test_load_entry_modes_payload_rejects_missing_required_list_field(tmp_path: Path) -> None:
    path = tmp_path / "invalid_entry_modes.yaml"
    path.write_text(
        """
compatible_agents:
  - Codex
  - Claude Code
  - OpenClaw
modes:
  - mode_id: broken_mode
    display_name: Broken Mode
    default_runtime_mode: lightweight
    preconditions:
      - workspace/profile available
    lightweight_scope: demo
    managed_entry_actions:
      - doctor
      - bootstrap
      - overlay-status
    lightweight_routes:
      - write
    startup_boundary_gated_routes: []
    governance_routes: []
    auxiliary_routes: []
    upgrade_triggers: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="managed_routes"):
        load_entry_modes_payload(path=path)


def test_load_entry_modes_rejects_mode_level_compatible_agents_override(monkeypatch: pytest.MonkeyPatch) -> None:
    def _payload_with_mode_override() -> dict[str, object]:
        return {
            "compatible_agents": ["Codex", "Claude Code", "OpenClaw"],
            "modes": [
                {
                    "mode_id": "full_research",
                    "display_name": "Full Research",
                    "default_runtime_mode": "managed",
                    "compatible_agents": ["Codex"],
                    "preconditions": ["workspace/profile available"],
                    "lightweight_scope": "none",
                    "managed_entry_actions": ["doctor", "bootstrap", "overlay-status", "ensure-study-runtime"],
                    "lightweight_routes": [],
                    "managed_routes": [
                        "doctor",
                        "bootstrap",
                        "overlay-status",
                        "scout",
                        "idea",
                        "write",
                        "finalize",
                    ],
                    "startup_boundary_gated_routes": ["baseline", "experiment", "analysis-campaign"],
                    "governance_routes": ["decision"],
                    "auxiliary_routes": [],
                    "upgrade_triggers": [],
                }
            ],
        }

    monkeypatch.setattr(modes_module, "load_entry_modes_payload", _payload_with_mode_override)

    with pytest.raises(ValueError, match="compatible_agents"):
        load_entry_modes()
