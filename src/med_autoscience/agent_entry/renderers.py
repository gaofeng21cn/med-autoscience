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
            "notify the user, and do not write runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
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
            "notify the user, and do not write runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
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


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain strings")
    return list(value)


def _render_list_line(field: str, value: object, *, inline: bool = False) -> str:
    rendered_values = _string_list(value, field=field)
    rendered = ", ".join(rendered_values) if rendered_values else "(none)"
    prefix = "" if inline else "- "
    return f"{prefix}{field}: {rendered}"
