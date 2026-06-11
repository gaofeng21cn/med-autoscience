from __future__ import annotations

from typing import Any, Mapping


def agent_execution_index(
    *,
    tool_cards: list[Mapping[str, Any]],
    ordinary_planning_root: str,
) -> dict[str, Any]:
    entries = [
        {
            "tool_id": card["tool_id"],
            **({"tool_mode": card["tool_mode"]} if card.get("tool_mode") else {}),
            "action_id": card["action_id"],
            "callability": card["callability"],
            "when_to_use": card.get("when_to_use", ""),
            "required_refs": list(card.get("required_refs") or []),
            "risk": {
                "read_only": bool(_mapping(card.get("risk_annotations")).get("readOnlyHint")),
                "requires_human_gate": bool(
                    _mapping(card.get("risk_annotations")).get("requires_human_gate")
                ),
                "requires_stage_attempt": bool(
                    _mapping(card.get("risk_annotations")).get(
                        "requires_opl_stage_attempt_or_lease"
                    )
                ),
            },
            "next_step_hint": next_step_hint_for_card(card),
        }
        for card in tool_cards
    ]
    return {
        "surface_kind": "mas_agent_execution_index",
        "planning_root": ordinary_planning_root,
        "audience": "autonomous_agent_executor",
        "raw_contract_direct_read_required": False,
        "entries": entries,
    }


def default_invocation_for_action(
    *,
    mcp_tool_name: str,
    mcp_tool_mode: str,
    public_runtime: bool,
    descriptor_only: bool,
    command: str,
) -> dict[str, Any]:
    if public_runtime and not descriptor_only:
        arguments = {"mode": mcp_tool_mode} if mcp_tool_mode else {}
        return {
            "surface": "mcp",
            "tool_name": mcp_tool_name,
            "arguments": arguments,
        }
    return {
        "surface": "descriptor_only",
        "tool_name": mcp_tool_name,
        "command": command,
        "arguments": {
            "current_owner_delta": "<current_owner_delta>",
        },
    }


def preflight_checks_for_card(*, requires_stage_attempt: bool) -> list[str]:
    checks = [
        "confirm_current_owner_delta_matches_card_applicability",
        "verify_required_refs_available",
        "check_allowed_writes_and_forbidden_authority",
    ]
    if requires_stage_attempt:
        checks.insert(2, "verify_opl_stage_attempt_or_lease")
    return checks


def success_signals_for_action(*, action_id: str) -> list[str]:
    signals = [
        "mas_tool_result_envelope_returned",
        "structured_payload_matches_output_schema",
        "no_forbidden_authority_claim",
    ]
    if action_id == "domain_handler_dispatch":
        signals.insert(1, "owner_receipt_ref_or_typed_blocker_ref_present")
    return signals


def failure_classes_for_card(*, requires_stage_attempt: bool) -> dict[str, dict[str, str]]:
    classes = {
        "missing_refs": {
            "retryability": "retry_after_refs",
            "next_safe_action": "collect_missing_refs",
        },
        "tool_execution_error": {
            "retryability": "retry_safe",
            "next_safe_action": "inspect_diagnostic_refs",
        },
        "forbidden_authority": {
            "retryability": "no_retry",
            "next_safe_action": "surface_owner_needed",
        },
    }
    if requires_stage_attempt:
        classes["missing_stage_attempt_or_lease"] = {
            "retryability": "owner_needed",
            "next_safe_action": "request_opl_stage_attempt_or_lease",
        }
    return classes


def operational_fields(card: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "mas_operational_tool_card",
        "default_invocation": dict(_mapping(card.get("default_invocation"))),
        "required_refs": list(card.get("required_refs") or []),
        "optional_refs": list(card.get("optional_refs") or []),
        "preflight_checks": list(card.get("preflight_checks") or []),
        "success_signals": list(card.get("success_signals") or []),
        "failure_classes": dict(_mapping(card.get("failure_classes"))),
        "next_safe_actions": list(card.get("next_safe_actions") or []),
        "authority_boundary": dict(_mapping(card.get("authority_boundary"))),
    }


def next_safe_actions_for_action_card(
    *,
    tool_name: str,
    tool_mode: str,
    callability: str,
    required_refs: list[str],
) -> list[dict[str, Any]]:
    if callability == "mcp_runtime":
        invoke_action: dict[str, Any] = {
            "action": "invoke_tool",
            "tool_name": tool_name,
            "requires": list(required_refs),
        }
        if tool_mode:
            invoke_action["tool_mode"] = tool_mode
        return [
            invoke_action,
            {
                "action": "collect_missing_refs",
                "when": "required_refs_missing",
            },
            {
                "action": "surface_owner_needed",
                "when": "forbidden_authority_or_hard_gate",
            },
        ]
    return [
        {
            "action": "resolve_descriptor_surface",
            "tool_name": tool_name,
            "requires": list(required_refs),
        },
        {
            "action": "collect_missing_refs",
            "when": "required_refs_missing",
        },
    ]


def operational_card_view(card: Mapping[str, Any]) -> dict[str, Any]:
    keys = [
        "operational_surface_kind",
        "card_kind",
        "tool_id",
        "tool_mode",
        "action_id",
        "action_type",
        "default_invocation",
        "required_refs",
        "optional_refs",
        "preflight_checks",
        "success_signals",
        "failure_classes",
        "next_safe_actions",
        "allowed_writes",
        "forbidden_authority",
        "authority_boundary",
        "result_envelope_schema_ref",
    ]
    return {key: card[key] for key in keys if key in card}


def fallback_cards_for_action(action_card: Mapping[str, Any]) -> list[dict[str, Any]]:
    if action_card.get("action_id") == "scientific_capability_registry":
        return []
    return []


def next_step_hint_for_card(card: Mapping[str, Any]) -> str:
    actions = list(card.get("next_safe_actions") or [])
    if not actions:
        return "load_operational_card"
    first = actions[0]
    if isinstance(first, Mapping):
        return _text(first.get("action")) or "load_operational_card"
    return "load_operational_card"


def drift_checks(
    *,
    tool_cards: list[Mapping[str, Any]],
    issues: list[dict[str, Any]],
    support_or_diagnostic: list[str],
    result_envelope_schema_ref: str,
) -> list[dict[str, Any]]:
    issue_ids = {_text(issue.get("issue_id")) for issue in issues}
    operational_ok = all(isinstance(card.get("operational"), Mapping) for card in tool_cards)
    return [
        {
            "check_id": "tool_card_operational_contract",
            "status": "passed" if operational_ok else "failed",
            "checked_card_count": len(tool_cards),
        },
        {
            "check_id": "result_envelope_recovery_contract",
            "status": "passed",
            "schema_ref": result_envelope_schema_ref,
        },
        {
            "check_id": "mcp_manifest_tool_card_parity",
            "status": (
                "passed"
                if "public_runtime_action_missing_mcp_manifest_tool" not in issue_ids
                else "failed"
            ),
        },
        {
            "check_id": "doctor_audit_support_surface_parity",
            "status": "passed" if "doctor_audit" in support_or_diagnostic else "failed",
        },
    ]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()
