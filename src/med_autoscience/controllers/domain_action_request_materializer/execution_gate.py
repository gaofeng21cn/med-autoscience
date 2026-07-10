from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    trusted_opl_execution_authorization,
)


OPL_EXECUTION_AUTHORIZATION_CONTRACT_REF = (
    "one-person-lab:contracts/opl-framework/stage-run-kernel-contract.json"
    "#execution_authorization_policy"
)
OPL_EXECUTION_AUTHORIZATION_LEDGER_REF = (
    "one-person-lab:src/modules/stagecraft/"
    "stage-run-execution-authorization-ledger.ts"
)


def projection(
    *,
    dispatch_status: str,
    blocked_reason: str | None,
    opl_execution_authorization: Mapping[str, Any] | None,
    evidence_gap_projection: Mapping[str, Any] | None = None,
    authorization_required: bool = True,
) -> dict[str, Any]:
    authorization = trusted_opl_execution_authorization(opl_execution_authorization)
    missing_authorization = authorization_required and authorization is None
    evidence_gap_gate = _evidence_gap_gate(evidence_gap_projection)
    blocked = dispatch_status == "blocked" or missing_authorization or evidence_gap_gate["blocked"]
    reason = blocked_reason
    if reason is None and missing_authorization:
        reason = OPL_EXECUTION_AUTHORIZATION_BLOCKER
    if reason is None and evidence_gap_gate["blocked"]:
        reason = "evidence_gap_decision_required"
    return {
        "gate_kind": "execution_authorization",
        "blocked": blocked,
        "reason": reason,
        "authorization_required": authorization_required,
        "authorization_present": authorization is not None,
        "authorization": dict(authorization or {}),
        "contract_ref": OPL_EXECUTION_AUTHORIZATION_CONTRACT_REF,
        "ledger_ref": OPL_EXECUTION_AUTHORIZATION_LEDGER_REF,
        "evidence_gap_gate": evidence_gap_gate,
        "authority_boundary": {
            "authorization_owner": "one-person-lab",
            "mas_can_define_developer_identity_policy": False,
            "mas_can_define_repo_write_policy": False,
            "mas_can_authorize_provider_admission": False,
            "mas_can_validate_domain_preconditions": True,
        },
    }


def provider_admission_effect(
    *,
    dispatch_status: str,
    opl_execution_authorization: Mapping[str, Any] | None,
    authorization_required: bool = True,
) -> str | None:
    if authorization_required and trusted_opl_execution_authorization(opl_execution_authorization) is None:
        return "not_admitted_until_opl_execution_authorization"
    if dispatch_status == "blocked":
        return "not_admitted_until_domain_preconditions_clear"
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _evidence_gap_gate(value: Mapping[str, Any] | None) -> dict[str, Any]:
    projection = _mapping(value)
    summary = _mapping(projection.get("evidence_gap_decision_summary"))
    hard_gate_count = int(summary.get("hard_gate_count") or 0)
    human_gate_count = int(summary.get("human_gate_count") or 0)
    return {
        "gate_kind": "evidence_gap_decision",
        "blocked": hard_gate_count > 0 or human_gate_count > 0,
        "hard_gate_count": hard_gate_count,
        "human_gate_count": human_gate_count,
        "soft_gap_count": int(summary.get("soft_gap_count") or 0),
        "observability_backlog_count": int(summary.get("observability_backlog_count") or 0),
        "evidence_tail_count": int(summary.get("evidence_tail_count") or 0),
        "current_action_can_continue": summary.get("current_action_can_continue") is True,
        "forbidden_claims": list(summary.get("forbidden_claims") or []),
    }


__all__ = [
    "OPL_EXECUTION_AUTHORIZATION_CONTRACT_REF",
    "OPL_EXECUTION_AUTHORIZATION_LEDGER_REF",
    "projection",
    "provider_admission_effect",
]
