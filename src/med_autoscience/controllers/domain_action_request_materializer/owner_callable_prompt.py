from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


TypedCloseoutContract = Callable[..., Mapping[str, Any]]


def executor_prompt(
    *,
    action_type: str,
    study_id: str,
    next_executable_owner: str,
    required_output_surface: str,
    typed_closeout_contract: TypedCloseoutContract,
) -> str:
    closeout_contract = typed_closeout_contract(action_type=action_type)
    return (
        "Use Codex CLI as the default MAS repair executor. "
        f"Handle action `{action_type}` for study `{study_id}` as owner `{next_executable_owner}`. "
        f"Read the referenced MAS durable truth surfaces and write only the owner-authorized output `{required_output_surface}` "
        "or the supervision handoff surfaces listed in this dispatch. Do not patch paper/current_package, "
        "manuscript/current_package, publication gates, or medical conclusions outside the owner workflow. "
        f"{closeout_contract['terminal_output_instruction']}"
    )


__all__ = ["executor_prompt"]
