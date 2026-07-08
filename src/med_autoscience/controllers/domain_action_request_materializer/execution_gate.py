from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SUPERVISOR_GATE_REASONS = frozenset(
    {
        "developer_apply_safe_required",
        "developer_supervisor_disabled_by_user_config",
        "developer_apply_safe_not_allowed_by_user_config",
        "opl_family_user_config_invalid",
        "github_cli_unavailable",
        "github_user_lookup_failed",
        "github_user_requires_pull_request_route",
    }
)


def projection(
    *,
    dispatch_status: str,
    blocked_reason: str | None,
    developer_mode_payload: Mapping[str, Any],
    supported_mode: str,
    evidence_gap_projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    supervisor_reason = developer_supervisor_gate_reason(blocked_reason)
    evidence_gap_gate = _evidence_gap_gate(evidence_gap_projection)
    developer_mode_gate = {
        "gate_kind": "developer_supervisor",
        "blocked": dispatch_status == "blocked" and supervisor_reason is not None,
        "reason": supervisor_reason,
        "requested_mode": _text(developer_mode_payload.get("requested_mode")),
        "effective_mode": _text(developer_mode_payload.get("mode")),
        "required_mode": supported_mode,
        "safe_actions_enabled": developer_mode_payload.get("safe_actions_enabled") is True,
        "authority_gate": dict(_mapping(developer_mode_payload.get("authority_gate"))),
        "github_user_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
        "repo_write_policy": dict(_mapping(developer_mode_payload.get("repo_write_policy"))),
    }
    if developer_mode_gate["blocked"] is True:
        return developer_mode_gate
    return {
        "gate_kind": "execution_authority",
        "blocked": dispatch_status == "blocked",
        "reason": blocked_reason,
        "developer_supervisor_gate": developer_mode_gate,
        "evidence_gap_gate": evidence_gap_gate,
    }


def provider_admission_effect(
    *,
    dispatch_status: str,
    blocked_reason: str | None,
) -> str | None:
    if dispatch_status == "blocked" and developer_supervisor_gate_reason(blocked_reason) is not None:
        return "not_admitted_until_execution_gate_clears"
    return None


def developer_supervisor_gate_reason(reason: str | None) -> str | None:
    if reason in SUPERVISOR_GATE_REASONS:
        return reason
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


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
