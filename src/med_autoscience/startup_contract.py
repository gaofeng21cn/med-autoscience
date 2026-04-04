from __future__ import annotations

from copy import deepcopy
from typing import Any

RUNTIME_OWNED_STARTUP_CONTRACT_KEYS: tuple[str, ...] = (
    "schema_version",
    "user_language",
    "need_research_paper",
    "decision_policy",
    "launch_mode",
    "standard_profile",
    "custom_profile",
    "baseline_execution_policy",
    "review_followup_policy",
    "manuscript_edit_mode",
)

CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEYS: tuple[str, ...] = (
    "research_intensity",
    "scope",
    "baseline_mode",
    "resource_policy",
    "time_budget_hours",
    "git_strategy",
    "runtime_constraints",
    "objectives",
    "baseline_urls",
    "paper_urls",
    "entry_state_summary",
    "review_summary",
    "controller_first_policy_summary",
    "automation_ready_summary",
    "custom_brief",
    "required_first_anchor",
    "legacy_code_execution_allowed",
    "startup_boundary_gate",
    "runtime_reentry_gate",
    "journal_shortlist",
    "medical_analysis_contract_summary",
    "medical_reporting_contract_summary",
    "reporting_guideline_family",
    "submission_targets",
)


def runtime_owned_startup_contract(startup_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(startup_contract, dict):
        return {}
    return {
        key: deepcopy(startup_contract[key])
        for key in RUNTIME_OWNED_STARTUP_CONTRACT_KEYS
        if key in startup_contract
    }


def controller_owned_startup_contract_extensions(startup_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(startup_contract, dict):
        return {}
    return {
        key: deepcopy(value)
        for key, value in startup_contract.items()
        if key not in RUNTIME_OWNED_STARTUP_CONTRACT_KEYS
    }


def compose_startup_contract(
    *,
    runtime_owned: dict[str, Any],
    controller_extensions: dict[str, Any],
) -> dict[str, Any]:
    overlap = set(runtime_owned).intersection(controller_extensions)
    if overlap:
        overlap_list = ", ".join(sorted(overlap))
        raise ValueError(f"startup contract ownership overlap: {overlap_list}")
    return {**runtime_owned, **controller_extensions}
