from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EntryMode:
    mode_id: str
    display_name: str
    default_runtime_mode: str
    compatible_agents: tuple[str, ...]
    preconditions: tuple[str, ...]
    lightweight_scope: str
    managed_entry_actions: tuple[str, ...]
    lightweight_routes: tuple[str, ...]
    managed_routes: tuple[str, ...]
    governance_routes: tuple[str, ...]
    auxiliary_routes: tuple[str, ...]
    upgrade_triggers: tuple[str, ...]


def load_entry_modes_payload(path: Path | None = None) -> dict[str, object]:
    resolved_path = path.expanduser().resolve() if path is not None else None
    if resolved_path is not None:
        raw_text = resolved_path.read_text(encoding="utf-8")
    else:
        raw_text = files("med_autoscience.agent_entry.resources").joinpath("agent_entry_modes.yaml").read_text(
            encoding="utf-8"
        )
    payload = yaml.safe_load(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("entry mode payload must be a mapping")
    return payload


def load_entry_modes() -> tuple[EntryMode, ...]:
    payload = load_entry_modes_payload()
    compatible_agents = _string_tuple(payload.get("compatible_agents"), "compatible_agents")
    modes_payload = payload.get("modes")
    if not isinstance(modes_payload, list):
        raise ValueError("modes must be a list")

    modes: list[EntryMode] = []
    for item in modes_payload:
        if not isinstance(item, dict):
            raise ValueError("each mode must be a mapping")
        mode_agents = item.get("compatible_agents", list(compatible_agents))
        modes.append(
            EntryMode(
                mode_id=_string_value(item, "mode_id"),
                display_name=_string_value(item, "display_name"),
                default_runtime_mode=_string_value(item, "default_runtime_mode"),
                compatible_agents=_string_tuple(mode_agents, "compatible_agents"),
                preconditions=_string_tuple(item.get("preconditions", []), "preconditions"),
                lightweight_scope=_string_value(item, "lightweight_scope"),
                managed_entry_actions=_string_tuple(item.get("managed_entry_actions", []), "managed_entry_actions"),
                lightweight_routes=_string_tuple(item.get("lightweight_routes", []), "lightweight_routes"),
                managed_routes=_string_tuple(item.get("managed_routes", []), "managed_routes"),
                governance_routes=_string_tuple(item.get("governance_routes", []), "governance_routes"),
                auxiliary_routes=_string_tuple(item.get("auxiliary_routes", []), "auxiliary_routes"),
                upgrade_triggers=_string_tuple(item.get("upgrade_triggers", []), "upgrade_triggers"),
            )
        )
    return tuple(modes)


def _string_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain only strings")
    return tuple(value)
