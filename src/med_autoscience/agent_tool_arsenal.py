from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.action_catalog import TARGET_DOMAIN_ID, build_mas_action_catalog
from med_autoscience.runtime_control.owner_callable_registry import (
    owner_callable_registry,
    paper_work_unit_lifecycle_for_action,
)
from med_autoscience.scientific_capability_registry import (
    build_scientific_capability_registry,
)


CONTRACT_ID = "mas_agent_tool_arsenal.v1"
CONTRACT_REF = "contracts/agent_tool_arsenal.json"
RESULT_ENVELOPE_SCHEMA_REF = f"{CONTRACT_REF}#/result_envelope_schema"
AUDIT_TRAIL_SCHEMA_REF = f"{CONTRACT_REF}#/tool_audit_trail_schema"
ORDINARY_PLANNING_ROOT = "current_owner_delta"
FORBIDDEN_DOMAIN_AUTHORITY = [
    "study_truth",
    "publication_quality",
    "submission_readiness",
    "artifact_authority",
    "memory_accept_reject",
    "current_package",
]


def build_tool_result_envelope_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MAS ToolResultEnvelope",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "surface_kind",
            "tool_id",
            "status",
            "audit_trail",
            "authority_boundary",
        ],
        "properties": {
            "surface_kind": {"const": "mas_tool_result_envelope"},
            "tool_id": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["succeeded", "blocked", "no_op_current", "failed"],
            },
            "content_ref": {"type": "string"},
            "structured_content_ref": {"type": "string"},
            "owner_receipt_ref": {"type": "string"},
            "typed_blocker_ref": {"type": "string"},
            "result_summary": {"type": "string"},
            "audit_trail": {"$ref": "#/tool_audit_trail_schema"},
            "authority_boundary": {"type": "object"},
        },
    }


def build_tool_audit_trail_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MAS ToolAuditTrail",
        "type": "object",
        "additionalProperties": True,
        "required": ["surface_kind", "source_refs", "authority_flags"],
        "properties": {
            "surface_kind": {"const": "mas_tool_audit_trail"},
            "source_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "authority_flags": {"type": "object"},
            "allowed_write_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "forbidden_authority": {
                "type": "array",
                "items": {"type": "string"},
            },
            "receipt_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }


def build_agent_tool_arsenal_index(
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    action_catalog = catalog if catalog is not None else build_mas_action_catalog()
    tool_cards = [_build_tool_use_card(action) for action in _actions(action_catalog)]
    owner_cards = _build_owner_callable_cards()
    return {
        "surface_kind": "mas_agent_tool_arsenal_index",
        "contract_id": CONTRACT_ID,
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "owner": "MedAutoScience",
        "audience": "autonomous_agent_executor",
        "human_operator_role": "governance_and_authorization_not_manual_tool_composition",
        "ordinary_planning_root": ORDINARY_PLANNING_ROOT,
        "tool_index_refs": {
            "action_catalog": "contracts/action_catalog.json",
            "mcp_registry": "src/med_autoscience/mcp_server_parts/tool_registry.py",
            "owner_callable_registry": (
                "src/med_autoscience/runtime_control/owner_callable_registry.py"
            ),
            "scientific_capability_registry": (
                "src/med_autoscience/scientific_capability_registry.py"
            ),
            "stage_control_plane": "contracts/stage_control_plane.json",
            "plugin_skill": "plugins/mas/skills/mas/SKILL.md",
        },
        "abi_surfaces": [
            "ToolArsenalIndex",
            "ToolUseCard",
            "CapabilityInvocationPlan",
            "ToolResultEnvelope",
            "ToolAuditTrail",
        ],
        "tool_index_entries": [_index_entry(card) for card in tool_cards],
        "tool_cards": tool_cards,
        "owner_callable_cards": owner_cards,
        "scientific_capability_registry": build_scientific_capability_registry(),
        "capability_invocation_plan_contract": _capability_invocation_plan_contract(),
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "result_envelope_schema": build_tool_result_envelope_schema(),
        "tool_audit_trail_schema_ref": AUDIT_TRAIL_SCHEMA_REF,
        "tool_audit_trail_schema": build_tool_audit_trail_schema(),
        "authority_boundary": {
            "mas_owns_domain_truth_and_authority_functions": True,
            "opl_owns_generated_descriptor_projection": True,
            "tool_arsenal_can_write_domain_truth": False,
            "tool_arsenal_can_authorize_quality_or_export": False,
            "human_operator_manual_composition_required": False,
        },
    }


def build_capability_invocation_plan(
    *,
    current_owner_delta: Mapping[str, Any],
    arsenal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = arsenal if arsenal is not None else build_agent_tool_arsenal_index()
    action_type = _text(current_owner_delta.get("action_type"))
    action_id = _text(current_owner_delta.get("action_id"))
    requested = action_type or action_id
    owner_card = _owner_card_by_action_type(payload).get(requested)
    if owner_card is not None:
        return _owner_callable_invocation_plan(
            owner_card=owner_card,
            current_owner_delta=current_owner_delta,
        )
    action_card = _tool_card_by_action_or_tool_id(payload).get(requested)
    if action_card is None:
        raise ValueError(f"No tool card for current_owner_delta action: {requested}")
    return _action_invocation_plan(
        action_card=action_card,
        current_owner_delta=current_owner_delta,
    )


def get_tool_use_card(
    tool_id: str,
    *,
    arsenal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    requested = _text(tool_id)
    payload = arsenal if arsenal is not None else build_agent_tool_arsenal_index()
    card = _tool_card_by_action_or_tool_id(payload).get(requested)
    if card is None:
        card = _owner_card_by_action_type(payload).get(requested)
    if card is None:
        raise ValueError(f"Unknown MAS tool card: {tool_id}")
    return dict(card)


def mcp_tool_annotations(tool_id: str, *, read_only: bool | None = None) -> dict[str, Any]:
    is_read_only = bool(read_only)
    return {
        "readOnlyHint": is_read_only,
        "destructiveHint": False if is_read_only else True,
        "idempotentHint": is_read_only,
        "openWorldHint": False,
    }


def _build_tool_use_card(action: Mapping[str, Any]) -> dict[str, Any]:
    action_id = _required_text(action.get("action_id"), "action_id")
    effect = _required_text(action.get("effect"), "effect")
    source_command = action.get("source_command") if isinstance(action.get("source_command"), Mapping) else {}
    mcp_descriptor = _surface_descriptor(action, "mcp")
    mcp_tool_name = _text(mcp_descriptor.get("tool_name")) or action_id
    mcp_tool_mode = _text(mcp_descriptor.get("mode"))
    descriptor_only = bool(mcp_descriptor.get("descriptor_only", True))
    public_runtime = bool(mcp_descriptor.get("public_runtime", False))
    callability = "mcp_runtime" if public_runtime and not descriptor_only else "descriptor_only"
    read_only = effect == "read_only"
    refs_only_runtime_write = action_id == "scientific_capability_registry"
    human_gate_ids = [str(item) for item in list(action.get("human_gate_ids") or [])]
    authority_boundary = (
        dict(action.get("authority_boundary"))
        if isinstance(action.get("authority_boundary"), Mapping)
        else {}
    )
    requires_stage_attempt = (not read_only) and not human_gate_ids and not refs_only_runtime_write
    return {
        "surface_kind": "mas_tool_use_card",
        "card_kind": "action_catalog",
        "tool_id": mcp_tool_name,
        **({"tool_mode": mcp_tool_mode} if mcp_tool_mode else {}),
        "action_id": action_id,
        "title": _required_text(action.get("title"), "title"),
        "summary": _required_text(action.get("summary"), "summary"),
        "effect": effect,
        "callability": callability,
        "action_surface_kind": _text(source_command.get("surface_kind")),
        "command": _text(source_command.get("command")),
        "mcp_invocation": {
            "tool_name": mcp_tool_name,
            **({"mode": mcp_tool_mode} if mcp_tool_mode else {}),
            "public_runtime": public_runtime,
        },
        "supported_surfaces": sorted(str(item) for item in _surfaces(action)),
        "when_to_use": _when_to_use(action_id=action_id, summary=_text(action.get("summary"))),
        "when_not_to_use": (
            "Do not use this card to bypass MAS authority surfaces, manual-compose a human "
            "tool recipe, or infer publication readiness from tool availability."
        ),
        "risk_annotations": {
            **mcp_tool_annotations(
                mcp_tool_name,
                read_only=read_only and not refs_only_runtime_write,
            ),
            "requires_human_gate": bool(human_gate_ids),
            "requires_opl_stage_attempt_or_lease": requires_stage_attempt,
            "domain_truth_write": False,
        },
        "input_refs": [str(item) for item in list(action.get("workspace_locator_fields") or [])],
        "input_schema_ref": _text(action.get("input_schema_ref")),
        "output_schema_ref": _text(action.get("output_schema_ref")),
        "output_schema": _output_schema_for_action(action),
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "allowed_writes": _allowed_writes_for_action(action_id),
        "forbidden_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
        "human_gate_ids": human_gate_ids,
        "idempotency_policy": (
            "read_only_no_side_effects"
            if read_only and not refs_only_runtime_write
            else "requires_current_owner_delta_or_human_gate_fingerprint"
        ),
        "current_delta_applicability": (
            "inspect_current_owner_delta_and_supporting_surfaces"
            if read_only
            else "only_when_current_owner_delta_selects_this_action_or_human_gate_authorizes"
        ),
        "authority_boundary": authority_boundary,
        "authority_effects": {
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_return_owner_receipt": action_id == "domain_handler_dispatch",
            "can_return_typed_blocker": action_id == "domain_handler_dispatch",
        },
        "audit_trail_schema_ref": AUDIT_TRAIL_SCHEMA_REF,
    }


def _build_owner_callable_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for callable_payload in owner_callable_registry().values():
        action_type = _required_text(callable_payload.get("action_type"), "action_type")
        lifecycle = paper_work_unit_lifecycle_for_action(action_type) or {}
        completion_proof = (
            dict(lifecycle.get("completion_proof"))
            if isinstance(lifecycle.get("completion_proof"), Mapping)
            else {"requires_owner_receipt_or_typed_blocker": True}
        )
        cards.append(
            {
                "surface_kind": "mas_owner_callable_tool_card",
                "card_kind": "owner_callable",
                "tool_id": f"owner_callable:{action_type}",
                "action_type": action_type,
                "owner": _required_text(callable_payload.get("owner"), "owner"),
                "callable_surface": _required_text(
                    callable_payload.get("callable_surface"),
                    "callable_surface",
                ),
                "input_refs": _list_text(
                    lifecycle.get("required_input_refs") or callable_payload.get("required_inputs")
                ),
                "required_output_refs": _list_text(
                    lifecycle.get("required_output_refs") or callable_payload.get("required_outputs")
                ),
                "allowed_writes": _list_text(lifecycle.get("allowed_writes")),
                "forbidden_writes": _list_text(lifecycle.get("forbidden_writes")),
                "forbidden_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
                "closeout_contract": completion_proof,
                "risk_annotations": {
                    **mcp_tool_annotations(f"owner_callable:{action_type}", read_only=False),
                    "requires_human_gate": False,
                    "requires_opl_stage_attempt_or_lease": True,
                    "domain_truth_write": False,
                },
                "idempotency_policy": _required_text(
                    callable_payload.get("idempotency_scope"),
                    "idempotency_scope",
                ),
                "source_fingerprint_scope": _required_text(
                    callable_payload.get("source_fingerprint_scope"),
                    "source_fingerprint_scope",
                ),
                "artifact_delta_predicate": _required_text(
                    callable_payload.get("artifact_delta_predicate"),
                    "artifact_delta_predicate",
                ),
                "gate_replay_target": callable_payload.get("gate_replay_target"),
                "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
                "authority_boundary": {
                    "can_write_domain_truth": False,
                    "can_write_publication_quality": False,
                    "can_authorize_publication_quality": False,
                    "can_authorize_submission_readiness": False,
                    "owner_receipt_or_typed_blocker_required": bool(
                        completion_proof.get("requires_owner_receipt_or_typed_blocker")
                    ),
                },
            }
        )
    return sorted(cards, key=lambda item: str(item["action_type"]))


def _owner_callable_invocation_plan(
    *,
    owner_card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_invocation_plan",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "selected_card_kind": "owner_callable",
        "selected_action_type": owner_card["action_type"],
        "selected_tool_id": owner_card["tool_id"],
        "source_ref": _text(current_owner_delta.get("source_ref")),
        "work_unit_fingerprint": _text(current_owner_delta.get("work_unit_fingerprint")),
        "requires": {
            "input_refs": list(owner_card.get("input_refs") or []),
            "allowed_writes": list(owner_card.get("allowed_writes") or []),
            "owner_receipt_or_typed_blocker": bool(
                _mapping(owner_card.get("closeout_contract")).get(
                    "requires_owner_receipt_or_typed_blocker"
                )
            ),
        },
        "invocation_steps": [
            "verify_required_input_refs",
            "verify_current_owner_delta_fingerprint",
            "check_allowed_writes_and_forbidden_authority",
            "invoke_owner_callable_surface",
            "emit_tool_result_envelope",
        ],
        "authority_boundary": {
            "can_write_domain_truth": False,
            "can_write_publication_quality": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "tool_result_envelope_is_authority_outcome": False,
        },
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
    }


def _action_invocation_plan(
    *,
    action_card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_invocation_plan",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "selected_card_kind": "action_catalog",
        "selected_action_id": action_card["action_id"],
        "selected_tool_id": action_card["tool_id"],
        **({"selected_tool_mode": action_card["tool_mode"]} if action_card.get("tool_mode") else {}),
        "source_ref": _text(current_owner_delta.get("source_ref")),
        "work_unit_fingerprint": _text(current_owner_delta.get("work_unit_fingerprint")),
        "requires": {
            "input_refs": list(action_card.get("input_refs") or []),
            "allowed_writes": list(action_card.get("allowed_writes") or []),
            "owner_receipt_or_typed_blocker": bool(
                _mapping(action_card.get("authority_effects")).get("can_return_owner_receipt")
            ),
        },
        "invocation_steps": [
            "verify_required_input_refs",
            "check_allowed_writes_and_forbidden_authority",
            "invoke_mcp_or_descriptor_target",
            "emit_tool_result_envelope",
        ],
        "authority_boundary": {
            "can_write_domain_truth": False,
            "can_write_publication_quality": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "tool_result_envelope_is_authority_outcome": False,
        },
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
    }


def _capability_invocation_plan_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_invocation_plan_contract",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "agent_default": True,
        "selection_order": [
            "current_owner_delta.action_type owner callable card",
            "current_owner_delta.action_id action catalog card",
            "typed_blocker when no matching card exists",
        ],
        "hard_requirements": [
            "verify_required_input_refs",
            "verify_current_owner_delta_fingerprint_for_mutating_work",
            "check_allowed_writes_and_forbidden_authority",
            "emit_tool_result_envelope",
        ],
        "non_authority_rule": (
            "Invocation metadata never becomes MAS study truth, publication quality, "
            "artifact authority, memory authority, or production readiness."
        ),
    }


def _index_entry(card: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "tool_id": card["tool_id"],
        **({"tool_mode": card["tool_mode"]} if card.get("tool_mode") else {}),
        "action_id": card["action_id"],
        "effect": card["effect"],
        "callability": card["callability"],
        "current_delta_applicability": card["current_delta_applicability"],
        "read_only": bool(_mapping(card.get("risk_annotations")).get("readOnlyHint")),
    }


def _output_schema_for_action(action: Mapping[str, Any]) -> dict[str, Any]:
    output_schema_ref = _text(action.get("output_schema_ref"))
    if output_schema_ref:
        return {"$ref": output_schema_ref}
    return {"type": "object"}


def _allowed_writes_for_action(action_id: str) -> list[str]:
    if action_id == "scientific_capability_registry":
        return [
            "artifacts/advisory/external_learning_sidecar/latest.json",
            "artifacts/stage_outputs/<stage>/advisory/light_external_pattern_refs.json",
            "artifacts/runtime/evo_scientist_sidecar/latest.json",
            "display_pack_agent refs-only plan outputs",
        ]
    if action_id == "domain_handler_dispatch":
        return [
            "MAS owner-route dispatch receipt refs",
            "MAS owner receipt refs",
            "MAS typed blocker refs",
            "explicit OPL opt-in executor/proof refs",
        ]
    return ["MAS domain handler target refs only"]


def _when_to_use(*, action_id: str, summary: str) -> str:
    return (
        f"Use {action_id} when an autonomous agent needs this capability from the "
        f"{ORDINARY_PLANNING_ROOT} path: {summary}"
    )


def _actions(catalog: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [item for item in list(catalog.get("actions") or []) if isinstance(item, Mapping)]


def _surfaces(action: Mapping[str, Any]) -> Mapping[str, Any]:
    surfaces = action.get("supported_surfaces")
    return surfaces if isinstance(surfaces, Mapping) else {}


def _surface_descriptor(action: Mapping[str, Any], surface: str) -> Mapping[str, Any]:
    descriptor = _surfaces(action).get(surface)
    return descriptor if isinstance(descriptor, Mapping) else {}


def _tool_card_by_action_or_tool_id(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    cards: dict[str, Mapping[str, Any]] = {}
    for item in list(payload.get("tool_cards") or []):
        if not isinstance(item, Mapping):
            continue
        cards[_text(item.get("tool_id"))] = item
        cards[_text(item.get("action_id"))] = item
    return {key: value for key, value in cards.items() if key}


def _owner_card_by_action_type(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    cards: dict[str, Mapping[str, Any]] = {}
    for item in list(payload.get("owner_callable_cards") or []):
        if not isinstance(item, Mapping):
            continue
        action_type = _text(item.get("action_type"))
        tool_id = _text(item.get("tool_id"))
        if action_type:
            cards[action_type] = item
        if tool_id:
            cards[tool_id] = item
    return cards


def _list_text(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _required_text(value: object, field: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"MAS agent tool arsenal missing field: {field}")
    return text


__all__ = [
    "AUDIT_TRAIL_SCHEMA_REF",
    "CONTRACT_ID",
    "CONTRACT_REF",
    "ORDINARY_PLANNING_ROOT",
    "RESULT_ENVELOPE_SCHEMA_REF",
    "build_agent_tool_arsenal_index",
    "build_capability_invocation_plan",
    "build_tool_audit_trail_schema",
    "build_tool_result_envelope_schema",
    "get_tool_use_card",
    "mcp_tool_annotations",
]
