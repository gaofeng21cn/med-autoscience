from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.agent_entry.modes import load_entry_modes_payload


def render_entry_modes_payload() -> dict[str, object]:
    return deepcopy(load_entry_modes_payload())


def render_entry_modes_guide() -> str:
    payload = render_entry_modes_payload()
    compatible_agents = _string_list(payload.get("compatible_agents"), field="compatible_agents")
    modes = _mode_payload_list(payload)
    route_contracts = _route_contract_payload_map(payload)
    evidence_review_contract = _evidence_review_contract_payload(payload)
    runtime_modes = sorted({mode["default_runtime_mode"] for mode in modes})

    lines: list[str] = [
        "# Agent Entry Modes",
        "",
        "Canonical source: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`.",
        "",
        "## Compatible Agents",
        f"- {', '.join(compatible_agents)}",
        "",
        "## Runtime Modes",
        f"- {', '.join(runtime_modes)}",
        "",
        "## Mode Contract",
    ]
    for mode in modes:
        lines.extend(
            (
                "",
                f"### {mode['mode_id']} ({mode['display_name']})",
                f"- default_runtime_mode: {mode['default_runtime_mode']}",
                f"- lightweight_scope: {mode['lightweight_scope']}",
                _render_list_line("preconditions", mode["preconditions"]),
                _render_list_line("managed_entry_actions", mode["managed_entry_actions"]),
                _render_list_line("lightweight_routes", mode["lightweight_routes"]),
                _render_list_line("managed_routes", mode["managed_routes"]),
                _render_list_line("startup_boundary_gated_routes", mode["startup_boundary_gated_routes"]),
                _render_list_line("governance_routes", mode["governance_routes"]),
                _render_list_line("auxiliary_routes", mode["auxiliary_routes"]),
                _render_list_line("upgrade_triggers", mode["upgrade_triggers"]),
            )
        )

    lines.extend(
        (
            "",
            "## Route Contracts",
        )
    )
    for route_contract in route_contracts:
        lines.extend(
            (
                "",
                f"### {route_contract['route_id']} ({route_contract['display_name']})",
                f"- key_question: {route_contract['key_question']}",
                f"- goal: {route_contract['goal']}",
                _render_list_line("enter_conditions", route_contract["enter_conditions"]),
                _render_list_line("hard_success_gate", route_contract["hard_success_gate"]),
                _render_list_line("durable_outputs_minimum", route_contract["durable_outputs_minimum"]),
                _render_list_line("human_gate_boundary", route_contract["human_gate_boundary"]),
                _render_list_line("next_routes", route_contract["next_routes"]),
                _render_list_line("route_back_triggers", route_contract["route_back_triggers"]),
            )
        )

    lines.extend(
        (
            "",
            "## Evidence And Review Contract",
            _render_list_line("minimum_proof_package", evidence_review_contract["minimum_proof_package"]),
            _render_list_line("reviewer_first_checks", evidence_review_contract["reviewer_first_checks"]),
            _render_list_line(
                "claim_evidence_consistency_requirements",
                evidence_review_contract["claim_evidence_consistency_requirements"],
            ),
            _render_list_line("route_back_policy", evidence_review_contract["route_back_policy"]),
        )
    )

    lines.extend(
        (
            "",
            "## Upgrade Rules",
            "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
            "upgrade from lightweight to managed before continuing.",
            "",
            "## Startup Boundary Rule",
            "Run `ensure-study-runtime` before any managed compute decision. Do not enter "
            "`startup_boundary_gated_routes` unless that controller reports "
            "`startup_boundary_gate.allow_compute_stage = true`; otherwise stay within "
            "`managed_routes`, `governance_routes`, and any writing-only delivery route.",
            "",
            "## Live Runtime Ownership Rule",
            "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, "
            "notify the user, report `browser_url`, `quest_session_api_url`, and `active_run_id` when present, "
            "and do not write runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
            "",
            "## No Ad-hoc Execution Rule",
            "When operating MAS-covered work, agents must use controller-authorized `CLI`, `MCP`, "
            "`product-entry`, or runtime surfaces before writing research outputs or advancing a study route.",
            "If a required capability is not exposed through those MAS contracts, stop and close the contract gap "
            "in the repo-tracked controller/callable surface before continuing; do not bypass MAS with ad-hoc "
            "scripts, direct artifact edits, prompt-only research chains, or generic document/PDF/Office tooling.",
            "",
            "## Revision Intake Rule",
            "Treat reviewer feedback, manuscript revision, mentor feedback, 审稿意见, 导师反馈, 论文修改, "
            "and Introduction/Methods/Results/Figure/Table feedback as `reviewer_revision` study task intake.",
            "Before foreground manuscript edits, require a structured revision checklist and durable "
            "handoff/evidence surface; MDS resume must read the latest revision handoff/evidence surface first.",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def render_public_yaml() -> str:
    payload = render_entry_modes_payload()
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return rendered if rendered.endswith("\n") else f"{rendered}\n"


def render_codex_entry_skill() -> str:
    return _render_agent_entry_prompt(
        title="# MedAutoScience Agent Entry (Codex)",
        intro="Use this contract to select entry mode and route actions without changing canonical definitions.",
    )


def render_openclaw_entry_prompt() -> str:
    return _render_agent_entry_prompt(
        title="# MedAutoScience Agent Entry (OpenClaw)",
        intro="Use this prompt contract to choose runtime mode and route transitions from canonical entry facts.",
    )


def sync_agent_entry_assets(repo_root: Path) -> dict[str, object]:
    root = repo_root.expanduser().resolve()
    assets: tuple[tuple[Path, str], ...] = (
        (Path("docs/runtime/agent_entry_modes.md"), render_entry_modes_guide()),
        (Path("templates/agent_entry_modes.yaml"), render_public_yaml()),
        (Path("templates/codex/medautoscience-entry.SKILL.md"), render_codex_entry_skill()),
        (Path("templates/openclaw/medautoscience-entry.prompt.md"), render_openclaw_entry_prompt()),
    )
    written_files: list[str] = []

    for relative_path, content in assets:
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        written_files.append(str(output_path))

    return {
        "repo_root": str(root),
        "written_count": len(written_files),
        "written_files": written_files,
    }


def _render_agent_entry_prompt(*, title: str, intro: str) -> str:
    payload = render_entry_modes_payload()
    modes = _mode_payload_list(payload)
    route_contracts = _route_contract_payload_map(payload)
    evidence_review_contract = _evidence_review_contract_payload(payload)
    runtime_modes = sorted({mode["default_runtime_mode"] for mode in modes})
    lines: list[str] = [
        title,
        "",
        intro,
        "",
        "Compatible agents: " + ", ".join(_string_list(payload.get("compatible_agents"), field="compatible_agents")),
        "Runtime modes: " + ", ".join(runtime_modes),
        "",
        "## Mode Contract",
    ]
    for mode in modes:
        lines.extend(
            (
                f"- {mode['mode_id']}: runtime={mode['default_runtime_mode']}, scope={mode['lightweight_scope']}",
                "  "
                + _render_list_line("preconditions", mode["preconditions"], inline=True),
                "  "
                + _render_list_line("managed_entry_actions", mode["managed_entry_actions"], inline=True),
                "  "
                + _render_list_line("lightweight_routes", mode["lightweight_routes"], inline=True),
                "  "
                + _render_list_line("managed_routes", mode["managed_routes"], inline=True),
                "  "
                + _render_list_line(
                    "startup_boundary_gated_routes",
                    mode["startup_boundary_gated_routes"],
                    inline=True,
                ),
                "  "
                + _render_list_line("governance_routes", mode["governance_routes"], inline=True),
                "  "
                + _render_list_line("auxiliary_routes", mode["auxiliary_routes"], inline=True),
                "  "
                + _render_list_line("upgrade_triggers", mode["upgrade_triggers"], inline=True),
            )
        )

    lines.extend(
        (
            "",
            "## Route Contracts",
        )
    )
    for route_contract in route_contracts:
        lines.extend(
            (
                f"- {route_contract['route_id']}: {route_contract['display_name']}",
                "  key_question: " + route_contract["key_question"],
                "  goal: " + route_contract["goal"],
                "  " + _render_list_line("enter_conditions", route_contract["enter_conditions"], inline=True),
                "  " + _render_list_line("hard_success_gate", route_contract["hard_success_gate"], inline=True),
                "  "
                + _render_list_line(
                    "durable_outputs_minimum",
                    route_contract["durable_outputs_minimum"],
                    inline=True,
                ),
                "  "
                + _render_list_line(
                    "human_gate_boundary",
                    route_contract["human_gate_boundary"],
                    inline=True,
                ),
                "  " + _render_list_line("next_routes", route_contract["next_routes"], inline=True),
                "  "
                + _render_list_line("route_back_triggers", route_contract["route_back_triggers"], inline=True),
            )
        )

    lines.extend(
        (
            "",
            "## Evidence And Review Contract",
            _render_list_line("minimum_proof_package", evidence_review_contract["minimum_proof_package"]),
            _render_list_line("reviewer_first_checks", evidence_review_contract["reviewer_first_checks"]),
            _render_list_line(
                "claim_evidence_consistency_requirements",
                evidence_review_contract["claim_evidence_consistency_requirements"],
            ),
            _render_list_line("route_back_policy", evidence_review_contract["route_back_policy"]),
        )
    )

    lines.extend(
        (
            "",
            "## Upgrade Rule",
            "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
            "upgrade from lightweight to managed before continuing.",
            "",
            "## Startup Boundary Rule",
            "Run `ensure-study-runtime` before any managed compute decision. Do not enter "
            "`startup_boundary_gated_routes` unless that controller reports "
            "`startup_boundary_gate.allow_compute_stage = true`; otherwise stay within "
            "`managed_routes`, `governance_routes`, and any writing-only delivery route.",
            "",
            "## Live Runtime Ownership Rule",
            "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, "
            "notify the user, report `browser_url`, `quest_session_api_url`, and `active_run_id` when present, "
            "and do not write runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
            "",
            "## No Ad-hoc Execution Rule",
            "When operating MAS-covered work, agents must use controller-authorized `CLI`, `MCP`, "
            "`product-entry`, or runtime surfaces before writing research outputs or advancing a study route.",
            "If a required capability is not exposed through those MAS contracts, stop and close the contract gap "
            "in the repo-tracked controller/callable surface before continuing; do not bypass MAS with ad-hoc "
            "scripts, direct artifact edits, prompt-only research chains, or generic document/PDF/Office tooling.",
            "",
            "## Revision Intake Rule",
            "Treat reviewer feedback, manuscript revision, mentor feedback, 审稿意见, 导师反馈, 论文修改, "
            "and Introduction/Methods/Results/Figure/Table feedback as `reviewer_revision` study task intake.",
            "Before foreground manuscript edits, require a structured revision checklist and durable "
            "handoff/evidence surface; MDS resume must read the latest revision handoff/evidence surface first.",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def _mode_payload_list(payload: dict[str, object]) -> list[dict[str, Any]]:
    raw_modes = payload.get("modes")
    if not isinstance(raw_modes, list):
        raise ValueError("modes must be a list")
    modes: list[dict[str, Any]] = []
    for mode in raw_modes:
        if not isinstance(mode, dict):
            raise ValueError("each mode must be a mapping")
        modes.append(mode)
    return modes


def _route_contract_payload_map(payload: dict[str, object]) -> list[dict[str, Any]]:
    raw_route_contracts = payload.get("route_contracts")
    if not isinstance(raw_route_contracts, dict):
        raise ValueError("route_contracts must be a mapping")
    route_contracts: list[dict[str, Any]] = []
    for route_id, route_contract in raw_route_contracts.items():
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("route_contracts keys must be non-empty strings")
        if not isinstance(route_contract, dict):
            raise ValueError(f"route_contracts[{route_id}] must be a mapping")
        route_contracts.append(route_contract)
    return route_contracts


def _evidence_review_contract_payload(payload: dict[str, object]) -> dict[str, Any]:
    raw_contract = payload.get("evidence_review_contract")
    if not isinstance(raw_contract, dict):
        raise ValueError("evidence_review_contract must be a mapping")
    return raw_contract


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain strings")
    return list(value)


def _render_list_line(field: str, value: object, *, inline: bool = False) -> str:
    rendered_values = _string_list(value, field=field)
    rendered = " | ".join(rendered_values) if rendered_values else "(none)"
    prefix = "" if inline else "- "
    return f"{prefix}{field}: {rendered}"
