from __future__ import annotations

import re
from pathlib import Path

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

EXPECTED_ROUTE_KEY_QUESTIONS = {
    "scout": "Is this direction worth entering the current study line?",
    "idea": "Which study line is strongest enough to justify the next route?",
    "baseline": "Does the current claim have reproducible baseline support?",
    "experiment": "Does the primary result answer the current study question?",
    "analysis-campaign": "Have the bounded evidence gaps been closed?",
    "write": "Does the manuscript narrative faithfully carry the current evidence?",
    "finalize": "Is the submission package ready for final audit?",
    "decision": "Should the current study line continue, route back, stop, or enter a human gate?",
    "journal-resolution": "Which outlet or packaging path best preserves the current claim boundary?",
}


def test_sync_agent_entry_assets_writes_public_files(tmp_path) -> None:
    result = sync_agent_entry_assets(repo_root=tmp_path)
    expected_assets = {
        "docs/runtime/agent_entry_modes.md": render_entry_modes_guide(),
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


def test_repo_public_agent_entry_assets_match_renderers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    expected_assets = {
        repo_root / "docs" / "runtime" / "agent_entry_modes.md": render_entry_modes_guide(),
        repo_root / "templates" / "agent_entry_modes.yaml": render_public_yaml(),
        repo_root / "templates" / "codex" / "medautoscience-entry.SKILL.md": render_codex_entry_skill(),
        repo_root / "templates" / "openclaw" / "medautoscience-entry.prompt.md": render_openclaw_entry_prompt(),
    }

    for output_path, expected_content in expected_assets.items():
        assert output_path.is_file()
        assert output_path.read_text(encoding="utf-8") == expected_content


def test_render_public_yaml_round_trip_matches_canonical_payload() -> None:
    rendered = render_public_yaml()

    assert yaml.safe_load(rendered) == load_entry_modes_payload()


def test_load_entry_modes_payload_requires_route_human_gate_boundary(tmp_path: Path) -> None:
    payload = render_entry_modes_payload()
    route_contracts = payload["route_contracts"]
    assert isinstance(route_contracts, dict)
    route_contracts["scout"].pop("human_gate_boundary", None)
    yaml_path = tmp_path / "agent_entry_modes.yaml"
    yaml_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match=r"route_contracts\[scout\] missing required field: human_gate_boundary"):
        load_entry_modes_payload(yaml_path)


def test_load_entry_modes_payload_requires_route_key_question(tmp_path: Path) -> None:
    payload = render_entry_modes_payload()
    route_contracts = payload["route_contracts"]
    assert isinstance(route_contracts, dict)
    route_contracts["scout"].pop("key_question", None)
    yaml_path = tmp_path / "agent_entry_modes.yaml"
    yaml_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match=r"route_contracts\[scout\] missing required field: key_question"):
        load_entry_modes_payload(yaml_path)


def test_load_entry_modes_payload_rejects_empty_route_key_question(tmp_path: Path) -> None:
    payload = render_entry_modes_payload()
    route_contracts = payload["route_contracts"]
    assert isinstance(route_contracts, dict)
    route_contracts["scout"]["key_question"] = ""
    yaml_path = tmp_path / "agent_entry_modes.yaml"
    yaml_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match=r"route_contracts\[scout\] key_question must be a non-empty string"):
        load_entry_modes_payload(yaml_path)


def test_canonical_payload_includes_global_route_and_evidence_review_contracts() -> None:
    payload = render_entry_modes_payload()

    route_contracts = payload.get("route_contracts")
    assert isinstance(route_contracts, dict)
    assert set(route_contracts) >= {
        "scout",
        "baseline",
        "analysis-campaign",
        "write",
        "finalize",
        "decision",
    }
    assert set(route_contracts) == set(EXPECTED_ROUTE_KEY_QUESTIONS)

    for route_id, expected_key_question in EXPECTED_ROUTE_KEY_QUESTIONS.items():
        route_payload = route_contracts.get(route_id)
        assert isinstance(route_payload, dict)
        assert route_payload.get("route_id") == route_id
        assert route_payload.get("key_question") == expected_key_question
        for field in (
            "goal",
            "enter_conditions",
            "hard_success_gate",
            "durable_outputs_minimum",
            "human_gate_boundary",
            "next_routes",
            "route_back_triggers",
        ):
            assert field in route_payload
            assert isinstance(
                route_payload[field],
                list if field.endswith(("conditions", "gate", "minimum", "routes", "triggers", "boundary")) else str,
            )

    evidence_review_contract = payload.get("evidence_review_contract")
    assert isinstance(evidence_review_contract, dict)
    for field in (
        "minimum_proof_package",
        "reviewer_first_checks",
        "claim_evidence_consistency_requirements",
        "route_back_policy",
    ):
        assert field in evidence_review_contract
        assert isinstance(evidence_review_contract[field], list)


def test_render_entry_modes_guide_contains_required_contract_context() -> None:
    guide = render_entry_modes_guide()
    payload = render_entry_modes_payload()
    modes_payload = payload["modes"]
    route_contracts = payload["route_contracts"]
    evidence_review_contract = payload["evidence_review_contract"]

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
        assert _extract_contract_list(mode_block, "startup_boundary_gated_routes") == mode["startup_boundary_gated_routes"]
        assert _extract_contract_list(mode_block, "governance_routes") == mode["governance_routes"]
        assert _extract_contract_list(mode_block, "auxiliary_routes") == mode["auxiliary_routes"]
        assert _extract_contract_list(mode_block, "upgrade_triggers") == mode["upgrade_triggers"]

    assert "## Route Contracts" in guide
    assert isinstance(route_contracts, dict)
    for route_id, route_payload in route_contracts.items():
        assert isinstance(route_payload, dict)
        route_block = _extract_route_block(guide, route_id)
        assert _extract_scalar_value(route_block, "key_question") == route_payload["key_question"]
        assert _extract_scalar_value(route_block, "goal") == route_payload["goal"]
        assert _extract_contract_list(route_block, "enter_conditions") == route_payload["enter_conditions"]
        assert _extract_contract_list(route_block, "hard_success_gate") == route_payload["hard_success_gate"]
        assert _extract_contract_list(route_block, "durable_outputs_minimum") == route_payload["durable_outputs_minimum"]
        assert _extract_contract_list(route_block, "human_gate_boundary") == route_payload["human_gate_boundary"]
        assert _extract_contract_list(route_block, "next_routes") == route_payload["next_routes"]
        assert _extract_contract_list(route_block, "route_back_triggers") == route_payload["route_back_triggers"]

    assert "## Evidence And Review Contract" in guide
    assert isinstance(evidence_review_contract, dict)
    for field in (
        "minimum_proof_package",
        "reviewer_first_checks",
        "claim_evidence_consistency_requirements",
        "route_back_policy",
    ):
        assert _extract_contract_list(guide, field) == evidence_review_contract[field]

    assert "Do not enter `startup_boundary_gated_routes`" in guide
    assert "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode" in guide
    assert "report `browser_url`, `quest_session_api_url`, and `active_run_id` when present" in guide
    assert "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions." in guide
    assert "## No Ad-hoc Execution Rule" in guide
    assert "agents must use controller-authorized `CLI`, `MCP`, `product-entry`, or runtime surfaces" in guide
    assert "stop and close the contract gap" in guide
    assert "do not bypass MAS with ad-hoc scripts" in guide
    assert "Treat reviewer feedback, manuscript revision, mentor feedback" in guide
    assert "reactivates the same study line" in guide
    assert "not permission to foreground-edit `manuscript/current_package`" in guide
    assert "relaunch/resume through MAS/MDS before editing canonical paper sources" in guide
    assert "user manuscript-change requests from Codex have been converted into a study revision intake" in guide
    assert "revision handoff stating data source, scripts, changed tables/figures, claim guardrails" in guide
    assert "no unreconciled foreground `current_package` revision overlay remains" in guide
    assert "first-draft quality scan has checked underused data-asset dimensions" in guide
    assert "field-verified multicenter/geography, subgroup/association, guideline" in guide
    assert "too-light descriptive draft leaves verified data dimensions unused" in guide


@pytest.mark.parametrize("render_prompt", [render_codex_entry_skill, render_openclaw_entry_prompt])
def test_entry_prompts_include_per_mode_route_contract_and_upgrade_rule(render_prompt) -> None:
    prompt = render_prompt()
    payload = render_entry_modes_payload()
    modes_payload = payload["modes"]
    route_contracts = payload["route_contracts"]
    evidence_review_contract = payload["evidence_review_contract"]

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
        assert _extract_contract_list(mode_block, "startup_boundary_gated_routes") == mode["startup_boundary_gated_routes"]
        assert _extract_contract_list(mode_block, "governance_routes") == mode["governance_routes"]
        assert _extract_contract_list(mode_block, "auxiliary_routes") == mode["auxiliary_routes"]
        assert _extract_contract_list(mode_block, "upgrade_triggers") == mode["upgrade_triggers"]

    assert "## Route Contracts" in prompt
    assert isinstance(route_contracts, dict)
    for route_id, route_payload in route_contracts.items():
        assert isinstance(route_payload, dict)
        route_block = _extract_prompt_route_block(prompt, route_id)
        assert _extract_scalar_value(route_block, "key_question") == route_payload["key_question"]
        assert _extract_scalar_value(route_block, "goal") == route_payload["goal"]
        assert _extract_contract_list(route_block, "enter_conditions") == route_payload["enter_conditions"]
        assert _extract_contract_list(route_block, "hard_success_gate") == route_payload["hard_success_gate"]
        assert _extract_contract_list(route_block, "durable_outputs_minimum") == route_payload["durable_outputs_minimum"]
        assert _extract_contract_list(route_block, "human_gate_boundary") == route_payload["human_gate_boundary"]
        assert _extract_contract_list(route_block, "next_routes") == route_payload["next_routes"]
        assert _extract_contract_list(route_block, "route_back_triggers") == route_payload["route_back_triggers"]

    assert "## Evidence And Review Contract" in prompt
    assert isinstance(evidence_review_contract, dict)
    for field in (
        "minimum_proof_package",
        "reviewer_first_checks",
        "claim_evidence_consistency_requirements",
        "route_back_policy",
    ):
        assert _extract_contract_list(prompt, field) == evidence_review_contract[field]

    assert "Do not enter `startup_boundary_gated_routes`" in prompt
    assert "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode" in prompt
    assert "report `browser_url`, `quest_session_api_url`, and `active_run_id` when present" in prompt
    assert "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions." in prompt
    assert "Treat reviewer feedback, manuscript revision, mentor feedback" in prompt
    assert "reactivates the same study line" in prompt
    assert "not permission to foreground-edit `manuscript/current_package`" in prompt
    assert "relaunch/resume through MAS/MDS before editing canonical paper sources" in prompt
    assert "user manuscript-change requests from Codex have been converted into a study revision intake" in prompt
    assert "revision handoff stating data source, scripts, changed tables/figures, claim guardrails" in prompt
    assert "no unreconciled foreground `current_package` revision overlay remains" in prompt
    assert "first-draft quality scan has checked underused data-asset dimensions" in prompt
    assert "field-verified multicenter/geography, subgroup/association, guideline" in prompt
    assert "too-light descriptive draft leaves verified data dimensions unused" in prompt


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


def _extract_route_block(guide: str, route_id: str) -> str:
    route_pattern = rf"^### {re.escape(route_id)} .*?(?=\n### |\n## |\Z)"
    match = re.search(route_pattern, guide, flags=re.MULTILINE | re.DOTALL)
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
    return [item.strip() for item in rendered.split("|")]


def _extract_prompt_route_block(prompt: str, route_id: str) -> str:
    route_pattern = rf"^- {re.escape(route_id)}:.*(?:\n  .*)*"
    match = re.search(route_pattern, prompt, flags=re.MULTILINE)
    assert match is not None
    return match.group(0)
