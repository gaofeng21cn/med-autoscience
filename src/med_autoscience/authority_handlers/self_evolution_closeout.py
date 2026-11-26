"""Evaluate target-owner closeout for an Agent Lab mechanism patch."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._opl_helpers.agent_lab_closeout import (
    TARGET_DOMAIN_OWNER_CLOSEOUT_SURFACE as SURFACE_KIND,
    evaluate_agent_lab_self_evolution_closeout as _evaluate_closeout,
    run_agent_lab_closeout_cli,
)


POLICY_PATH = Path("contracts/agent_lab_self_evolution_policy.json")
VERSION = "mas-agent-lab-self-evolution-closeout.v1"
OWNER = "med-autoscience"
REF_PREFIX = "mas-self-evolution-closeout"
FALLBACK_POLICY_REF = "policy:mas/agent-lab-self-evolution/unknown"


def evaluate_agent_lab_self_evolution_closeout(
    receipt_draft: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a refs-only MAS owner answer without changing publication truth."""

    return _evaluate_closeout(
        receipt_draft,
        policy,
        owner=OWNER,
        version=VERSION,
        ref_prefix=REF_PREFIX,
        fallback_policy_ref=FALLBACK_POLICY_REF,
    )


def main() -> None:
    run_agent_lab_closeout_cli(
        default_policy_path=POLICY_PATH,
        policy_env_var="MAS_SELF_EVOLUTION_POLICY_PATH",
        owner=OWNER,
        version=VERSION,
        ref_prefix=REF_PREFIX,
        fallback_policy_ref=FALLBACK_POLICY_REF,
    )


if __name__ == "__main__":
    main()


__all__ = ["evaluate_agent_lab_self_evolution_closeout"]
