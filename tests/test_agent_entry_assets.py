from __future__ import annotations

import yaml

from med_autoscience.agent_entry import load_entry_modes_payload
from med_autoscience.agent_entry.renderers import (
    render_entry_modes_guide,
    render_public_yaml,
    sync_agent_entry_assets,
)


def test_sync_agent_entry_assets_writes_public_files(tmp_path) -> None:
    result = sync_agent_entry_assets(repo_root=tmp_path)

    assert result["written_count"] == 4
    assert (tmp_path / "guides" / "agent_entry_modes.md").is_file()
    assert (tmp_path / "templates" / "agent_entry_modes.yaml").is_file()
    assert (tmp_path / "templates" / "codex" / "medautoscience-entry.SKILL.md").is_file()
    assert (tmp_path / "templates" / "openclaw" / "medautoscience-entry.prompt.md").is_file()


def test_render_public_yaml_round_trip_matches_canonical_payload() -> None:
    rendered = render_public_yaml()

    assert yaml.safe_load(rendered) == load_entry_modes_payload()


def test_render_entry_modes_guide_contains_required_contract_context() -> None:
    guide = render_entry_modes_guide()

    assert "full_research" in guide
    assert "literature_scout" in guide
    assert "idea_exploration" in guide
    assert "project_optimization" in guide
    assert "writing_delivery" in guide
    assert "managed" in guide
    assert "lightweight" in guide
    assert "managed_entry_actions" in guide
    assert "managed_routes" in guide
    assert "auxiliary_routes" in guide
    assert "upgrade_triggers" in guide
