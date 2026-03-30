from __future__ import annotations

import re

import pytest
import yaml

from med_autoscience.agent_entry import load_entry_modes_payload
from med_autoscience.agent_entry.renderers import (
    render_codex_entry_skill,
    render_entry_modes_guide,
    render_entry_modes_payload,
    render_openclaw_entry_prompt,
    render_public_yaml,
    sync_agent_entry_assets,
)


def test_sync_agent_entry_assets_writes_public_files(tmp_path) -> None:
    result = sync_agent_entry_assets(repo_root=tmp_path)
    expected_assets = {
        "guides/agent_entry_modes.md": render_entry_modes_guide(),
        "templates/agent_entry_modes.yaml": render_public_yaml(),
        "templates/codex/medautoscience-entry.SKILL.md": render_codex_entry_skill(),
        "templates/openclaw/medautoscience-entry.prompt.md": render_openclaw_entry_prompt(),
    }

    assert result["written_count"] == 4
    assert set(result["written_files"]) == {str(tmp_path / path) for path in expected_assets}
    for relative_path, expected_content in expected_assets.items():
        output_path = tmp_path / relative_path
        assert output_path.is_file()
        assert output_path.read_text(encoding="utf-8") == expected_content


def test_render_public_yaml_round_trip_matches_canonical_payload() -> None:
    rendered = render_public_yaml()

    assert yaml.safe_load(rendered) == load_entry_modes_payload()


def test_render_entry_modes_guide_contains_required_contract_context() -> None:
    guide = render_entry_modes_guide()
    payload = render_entry_modes_payload()
    modes_payload = payload["modes"]

    assert "managed" in guide
    assert "lightweight" in guide
    assert (
        "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
        "upgrade from lightweight to managed before continuing."
    ) in guide

    assert isinstance(modes_payload, list)
    for mode in modes_payload:
        assert isinstance(mode, dict)
        mode_id = mode["mode_id"]
        assert isinstance(mode_id, str)
        mode_block = _extract_guide_mode_block(guide, mode_id)
        assert _extract_scalar_value(mode_block, "default_runtime_mode") == mode["default_runtime_mode"]
        assert _extract_scalar_value(mode_block, "lightweight_scope") == mode["lightweight_scope"]
        assert _extract_contract_list(mode_block, "preconditions") == mode["preconditions"]
        assert _extract_contract_list(mode_block, "managed_entry_actions") == mode["managed_entry_actions"]
        assert _extract_contract_list(mode_block, "lightweight_routes") == mode["lightweight_routes"]
        assert _extract_contract_list(mode_block, "managed_routes") == mode["managed_routes"]
        assert _extract_contract_list(mode_block, "governance_routes") == mode["governance_routes"]
        assert _extract_contract_list(mode_block, "auxiliary_routes") == mode["auxiliary_routes"]
        assert _extract_contract_list(mode_block, "upgrade_triggers") == mode["upgrade_triggers"]


@pytest.mark.parametrize("render_prompt", [render_codex_entry_skill, render_openclaw_entry_prompt])
def test_entry_prompts_include_per_mode_route_contract_and_upgrade_rule(render_prompt) -> None:
    prompt = render_prompt()
    payload = render_entry_modes_payload()
    modes_payload = payload["modes"]

    assert isinstance(modes_payload, list)
    assert (
        "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
        "upgrade from lightweight to managed before continuing."
    ) in prompt

    for mode in modes_payload:
        assert isinstance(mode, dict)
        mode_id = mode["mode_id"]
        assert isinstance(mode_id, str)
        mode_block = _extract_mode_block(prompt, mode_id)
        runtime_mode, lightweight_scope = _extract_prompt_mode_header(mode_block, mode_id)
        assert runtime_mode == mode["default_runtime_mode"]
        assert lightweight_scope == mode["lightweight_scope"]
        assert _extract_contract_list(mode_block, "preconditions") == mode["preconditions"]
        assert _extract_contract_list(mode_block, "managed_entry_actions") == mode["managed_entry_actions"]
        assert _extract_contract_list(mode_block, "lightweight_routes") == mode["lightweight_routes"]
        assert _extract_contract_list(mode_block, "managed_routes") == mode["managed_routes"]
        assert _extract_contract_list(mode_block, "governance_routes") == mode["governance_routes"]
        assert _extract_contract_list(mode_block, "auxiliary_routes") == mode["auxiliary_routes"]
        assert _extract_contract_list(mode_block, "upgrade_triggers") == mode["upgrade_triggers"]


def _extract_mode_block(prompt: str, mode_id: str) -> str:
    mode_pattern = rf"^- {re.escape(mode_id)}:.*(?:\n  .*)*"
    match = re.search(mode_pattern, prompt, flags=re.MULTILINE)
    assert match is not None
    return match.group(0)


def _extract_guide_mode_block(guide: str, mode_id: str) -> str:
    mode_pattern = rf"^### {re.escape(mode_id)} .*?(?=\n### |\n## |\Z)"
    match = re.search(mode_pattern, guide, flags=re.MULTILINE | re.DOTALL)
    assert match is not None
    return match.group(0)


def _extract_prompt_mode_header(mode_block: str, mode_id: str) -> tuple[str, str]:
    match = re.search(
        rf"^- {re.escape(mode_id)}: runtime=(.*?), scope=(.*)$",
        mode_block,
        flags=re.MULTILINE,
    )
    assert match is not None
    return match.group(1).strip(), match.group(2).strip()


def _extract_scalar_value(mode_block: str, field: str) -> str:
    field_pattern = rf"{re.escape(field)}: (.+)"
    match = re.search(field_pattern, mode_block)
    assert match is not None
    return match.group(1).strip()


def _extract_contract_list(mode_block: str, field: str) -> list[str]:
    field_pattern = rf"{re.escape(field)}: (.+)"
    match = re.search(field_pattern, mode_block)
    assert match is not None
    rendered = match.group(1).strip()
    if rendered == "(none)":
        return []
    return [item.strip() for item in rendered.split(",")]
