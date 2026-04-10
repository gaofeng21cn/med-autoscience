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
    "study_charter_ref",
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

_RUNTIME_OWNED_STARTUP_CONTRACT_KEY_SET = frozenset(RUNTIME_OWNED_STARTUP_CONTRACT_KEYS)
_CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEY_SET = frozenset(CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEYS)


def _raise_for_unclassified_keys(*, keys: set[str], allowed_keys: frozenset[str], error_prefix: str) -> None:
    unclassified_keys = sorted(keys.difference(allowed_keys))
    if not unclassified_keys:
        return
    raise ValueError(f"{error_prefix}: {', '.join(unclassified_keys)}")


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
    _raise_for_unclassified_keys(
        keys=set(startup_contract),
        allowed_keys=_RUNTIME_OWNED_STARTUP_CONTRACT_KEY_SET.union(_CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEY_SET),
        error_prefix="unclassified startup contract keys",
    )
    return {
        key: deepcopy(startup_contract[key])
        for key in CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEYS
        if key in startup_contract
    }


def stable_startup_contract(startup_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(startup_contract, dict):
        return {}
    return compose_startup_contract(
        runtime_owned=runtime_owned_startup_contract(startup_contract),
        controller_extensions=controller_owned_startup_contract_extensions(startup_contract),
    )


def compose_startup_contract(
    *,
    runtime_owned: dict[str, Any],
    controller_extensions: dict[str, Any],
) -> dict[str, Any]:
    overlap = set(runtime_owned).intersection(controller_extensions)
    if overlap:
        overlap_list = ", ".join(sorted(overlap))
        raise ValueError(f"startup contract ownership overlap: {overlap_list}")
    _raise_for_unclassified_keys(
        keys=set(runtime_owned),
        allowed_keys=_RUNTIME_OWNED_STARTUP_CONTRACT_KEY_SET,
        error_prefix="unclassified runtime-owned startup contract keys",
    )
    _raise_for_unclassified_keys(
        keys=set(controller_extensions),
        allowed_keys=_CONTROLLER_OWNED_STARTUP_CONTRACT_EXTENSION_KEY_SET,
        error_prefix="unclassified controller-owned startup contract keys",
    )
    return {**runtime_owned, **controller_extensions}
