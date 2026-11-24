"""Verify exact MAS owner receipts for OPL Foundry authority mutations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from opl_framework.foundry_owner_gate import (
    CONTEXT_SURFACE,
    CONTEXT_VERSION,
    DEFAULT_ALLOWED_ACTIONS,
    MAX_INPUT_BYTES,
    OwnerGateError,
    PROCESS_SURFACE,
    PROCESS_VERSION,
    RECEIPT_REF_PREFIX,
    RECEIPT_SURFACE,
    RECEIPT_VERSION,
    VERIFICATION_SURFACE,
    VERIFICATION_VERSION,
    canonical_json_bytes,
    run_owner_gate_cli,
    verify_owner_gate_request as _verify_owner_gate_request,
)


POLICY_SURFACE = "mas_foundry_owner_gate_policy"
POLICY_VERSION = "mas-foundry-owner-gate-policy.v1"
EXPECTED_OWNER = "med-autoscience"
EXPECTED_TARGET = {
    "target_agent_id": "mas",
    "target_domain_id": "medautoscience",
}
VERIFIER_ID = "mas-owner-gate:foundry-v1"


def verify_owner_gate_request(
    raw_request: Any,
    *,
    policy: dict[str, Any],
    receipt_dir: Path,
    now: str,
) -> dict[str, Any]:
    """Verify one MAS Foundry OwnerGate request using the shared Framework protocol."""

    return _verify_owner_gate_request(
        raw_request,
        policy=policy,
        receipt_dir=receipt_dir,
        now=now,
        expected_policy_surface=POLICY_SURFACE,
        expected_policy_version=POLICY_VERSION,
        expected_owner=EXPECTED_OWNER,
        expected_target=EXPECTED_TARGET,
        verifier_id=VERIFIER_ID,
        expected_allowed_actions=DEFAULT_ALLOWED_ACTIONS,
    )


def main() -> None:
    run_owner_gate_cli(
        prog_label="mas-foundry-owner-gate",
        expected_policy_surface=POLICY_SURFACE,
        expected_policy_version=POLICY_VERSION,
        expected_owner=EXPECTED_OWNER,
        expected_target=EXPECTED_TARGET,
        verifier_id=VERIFIER_ID,
        expected_allowed_actions=DEFAULT_ALLOWED_ACTIONS,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "OwnerGateError",
    "canonical_json_bytes",
    "verify_owner_gate_request",
]
