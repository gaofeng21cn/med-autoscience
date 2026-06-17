from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.action_catalog import TARGET_DOMAIN_ID, build_mas_action_catalog
from med_autoscience.agent_tool_arsenal_parts.capability_resolver import (
    attach_capability_invocation_os_fields,
    capability_resolver_contract,
    resolve_capability_candidates_from_arsenal,
)
from med_autoscience.agent_tool_arsenal_parts.operational_contract import (
    agent_execution_index,
    default_invocation_for_action,
    drift_checks,
    failure_classes_for_card,
    fallback_cards_for_action,
    next_safe_actions_for_action_card,
    next_step_hint_for_card,
    operational_card_view,
    operational_fields,
    preflight_checks_for_card,
    success_signals_for_action,
)
from med_autoscience.agent_tool_arsenal_parts import runtime_boundary
from med_autoscience.agent_tool_arsenal_parts import schemas as arsenal_schemas
from med_autoscience.runtime_control.owner_callable_registry import (
    owner_callable_registry,
    paper_work_unit_lifecycle_for_action,
)
from med_autoscience.scientific_capability_registry import build_scientific_capability_registry


CONTRACT_ID = "mas_agent_tool_arsenal.v1"
CONTRACT_REF = "contracts/agent_tool_arsenal.json"
RESULT_ENVELOPE_SCHEMA_REF = f"{CONTRACT_REF}#/result_envelope_schema"
AUDIT_TRAIL_SCHEMA_REF = f"{CONTRACT_REF}#/tool_audit_trail_schema"
LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF = (
    "src/med_autoscience/lightweight_executor_receipts.py::"
    "build_lightweight_executor_receipt_contract"
)
ORDINARY_PLANNING_ROOT = "current_owner_delta"
FORBIDDEN_DOMAIN_AUTHORITY = [
    "study_truth",
    "publication_quality",
    "submission_readiness",
    "artifact_authority",
    "memory_accept_reject",
    "current_package",
]
REQUIRED_TOOL_CARD_FIELDS = [
    "mcp_invocation",
    "risk_annotations",
    "discovery_hint",
    "fit_signal",
    "invocation_gate",
    "adaptation_policy",
    "authority_boundary",
    "result_envelope_schema_ref",
    "forbidden_authority",
    "idempotency_policy",
    "current_delta_applicability",
    "default_invocation",
    "required_refs",
    "optional_refs",
    "preflight_checks",
    "success_signals",
    "failure_classes",
    "next_safe_actions",
]
EMPTY_LIST_ALLOWED_TOOL_CARD_FIELDS = {"required_refs", "optional_refs"}


def build_tool_result_envelope_schema() -> dict[str, Any]:
    return arsenal_schemas.build_tool_result_envelope_schema(
        lightweight_executor_receipt_contract_ref=LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
    )


def build_agent_tool_arsenal_completeness_diagnostic(
    *,
    arsenal: Mapping[str, Any] | None = None,
    mcp_tool_names: list[str] | tuple[str, ...] | set[str] | None = None,
    mcp_tool_manifest: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
) -> dict[str, Any]:
    payload = arsenal if arsenal is not None else build_agent_tool_arsenal_index()
    tool_cards = [item for item in list(payload.get("tool_cards") or []) if isinstance(item, Mapping)]
    manifest_names = _manifest_tool_names(
        mcp_tool_names=mcp_tool_names,
        mcp_tool_manifest=mcp_tool_manifest,
    )
    public_runtime_cards = [
        card
        for card in tool_cards
        if card.get("callability") == "mcp_runtime"
        and bool(_mapping(card.get("mcp_invocation")).get("public_runtime"))
    ]
    public_runtime_tool_names = {
        _text(_mapping(card.get("mcp_invocation")).get("tool_name")) or _text(card.get("tool_id"))
        for card in public_runtime_cards
    }
    public_runtime_tool_names = {name for name in public_runtime_tool_names if name}
    support_or_diagnostic = sorted(manifest_names - public_runtime_tool_names)
    missing_manifest = sorted(public_runtime_tool_names - manifest_names) if manifest_names else []
    manifest_by_name = {
        _text(item.get("name")): item
        for item in list(mcp_tool_manifest or [])
        if isinstance(item, Mapping) and _text(item.get("name"))
    }
    issues: list[dict[str, Any]] = []
    manifest_output_schema_missing: list[str] = []
    manifest_input_schema_missing: list[str] = []
    manifest_annotation_missing: list[str] = []
    for card in tool_cards:
        missing_fields = [
            field
            for field in REQUIRED_TOOL_CARD_FIELDS
            if field not in card
            or card.get(field) in (None, "", {})
            or (card.get(field) == [] and field not in EMPTY_LIST_ALLOWED_TOOL_CARD_FIELDS)
        ]
        if missing_fields:
            issues.append(
                {
                    "issue_id": "tool_card_missing_required_abi_fields",
                    "action_id": _text(card.get("action_id")),
                    "tool_id": _text(card.get("tool_id")),
                    "missing_fields": missing_fields,
                }
            )
        tool_name = _text(_mapping(card.get("mcp_invocation")).get("tool_name")) or _text(card.get("tool_id"))
        if tool_name in manifest_by_name:
            manifest_entry = manifest_by_name[tool_name]
            if not isinstance(manifest_entry.get("outputSchema"), Mapping):
                manifest_output_schema_missing.append(tool_name)
            if not isinstance(manifest_entry.get("inputSchema"), Mapping):
                manifest_input_schema_missing.append(tool_name)
            if not isinstance(manifest_entry.get("annotations"), Mapping):
                manifest_annotation_missing.append(tool_name)
        forbidden = set(str(item) for item in list(card.get("forbidden_authority") or []))
        missing_forbidden = sorted(set(FORBIDDEN_DOMAIN_AUTHORITY) - forbidden)
        if missing_forbidden:
            issues.append(
                {
                    "issue_id": "tool_card_missing_forbidden_authority",
                    "action_id": _text(card.get("action_id")),
                    "tool_id": _text(card.get("tool_id")),
                    "missing_forbidden_authority": missing_forbidden,
                }
            )
    for name in missing_manifest:
        issues.append(
            {
                "issue_id": "public_runtime_action_missing_mcp_manifest_tool",
                "tool_id": name,
            }
        )
    issues.extend(
        {
            "issue_id": "manifest_tool_missing_output_schema",
            "tool_id": name,
        }
        for name in sorted(set(manifest_output_schema_missing))
    )
    issues.extend(
        {
            "issue_id": "manifest_tool_missing_input_schema",
            "tool_id": name,
        }
        for name in sorted(set(manifest_input_schema_missing))
    )
    issues.extend(
        {
            "issue_id": "manifest_tool_missing_annotations",
            "tool_id": name,
        }
        for name in sorted(set(manifest_annotation_missing))
    )
    diagnostic_drift_checks = drift_checks(
        tool_cards=tool_cards,
        issues=issues,
        support_or_diagnostic=support_or_diagnostic,
        result_envelope_schema_ref=RESULT_ENVELOPE_SCHEMA_REF,
    )
    return {
        "surface_kind": "mas_agent_tool_arsenal_completeness_diagnostic",
        "doctor_surface_kind": "mas_agent_tool_arsenal_drift_parity_doctor",
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "status": "complete" if not issues else "attention_required",
        "ordinary_planning_root": ORDINARY_PLANNING_ROOT,
        "required_tool_card_fields": list(REQUIRED_TOOL_CARD_FIELDS),
        "tool_card_count": len(tool_cards),
        "public_runtime_action_card_count": len(public_runtime_cards),
        "public_runtime_mcp_tools": sorted(public_runtime_tool_names),
        "mcp_manifest_tools": sorted(manifest_names),
        "support_or_diagnostic_mcp_tools": support_or_diagnostic,
        "descriptor_only_action_count": len(
            [card for card in tool_cards if card.get("callability") == "descriptor_only"]
        ),
        "owner_callable_card_count": len(
            [item for item in list(payload.get("owner_callable_cards") or []) if isinstance(item, Mapping)]
        ),
        "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
        "executor_receipt_ref_policy": _executor_receipt_ref_policy(),
        "parity_summary": {
            "surface_kind": "mas_agent_tool_arsenal_drift_parity_summary",
            "status": "complete" if not issues else "attention_required",
            "public_runtime_manifest_missing": missing_manifest,
            "missing_public_runtime_mcp_tools": missing_manifest,
            "unexpected_public_runtime_mcp_tools": [],
            "manifest_output_schema_missing": sorted(set(manifest_output_schema_missing)),
            "manifest_input_schema_missing": sorted(set(manifest_input_schema_missing)),
            "manifest_annotation_missing": sorted(set(manifest_annotation_missing)),
            "support_or_diagnostic_tool_count": len(support_or_diagnostic),
            "support_or_diagnostic_tools": support_or_diagnostic,
            "support_or_diagnostic_mcp_tools": support_or_diagnostic,
            "doctor_audit_available": "doctor_audit" in manifest_names,
            "agent_tool_arsenal_available": "agent_tool_arsenal" in manifest_names,
            "operator_contract_direct_read_required": False,
        },
        "drift_checks": diagnostic_drift_checks,
        "issues": issues,
        "authority_boundary": {
            "diagnostic_only": True,
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "support_or_diagnostic_tools_are_not_current_owner_delta_action_cards": True,
            "support_or_diagnostic_tools_are_projection_only": True,
            "non_read_only_tools_require_current_owner_delta_or_human_gate": True,
            "non_read_only_tools_require_owner_receipt_or_typed_blocker_proof": True,
        },
    }


def build_tool_audit_trail_schema() -> dict[str, Any]:
    return arsenal_schemas.build_tool_audit_trail_schema()


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
            "OperationalToolCard",
            "AgentExecutionIndex",
            "CapabilityResolverReceipt",
            "CapabilityInvocationPlan",
            "ToolResultEnvelope",
            "ToolAuditTrail",
        ],
        "tool_index_entries": [_index_entry(card) for card in tool_cards],
        "agent_execution_index": agent_execution_index(
            tool_cards=tool_cards,
            ordinary_planning_root=ORDINARY_PLANNING_ROOT,
        ),
        "tool_cards": tool_cards,
        "owner_callable_cards": owner_cards,
        "scientific_capability_registry": build_scientific_capability_registry(),
        "capability_resolver_contract": capability_resolver_contract(),
        "capability_invocation_plan_contract": _capability_invocation_plan_contract(),
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "result_envelope_schema": build_tool_result_envelope_schema(),
        "tool_audit_trail_schema_ref": AUDIT_TRAIL_SCHEMA_REF,
        "tool_audit_trail_schema": build_tool_audit_trail_schema(),
        "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
        "executor_receipt_ref_policy": _executor_receipt_ref_policy(),
        "authority_boundary": {
            "mas_owns_domain_truth_and_authority_functions": True,
            "opl_owns_generated_descriptor_projection": True,
            **runtime_boundary.opl_capability_runtime_boundary(),
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
            capability_resolver_receipt=resolve_capability_candidates(
                current_owner_delta=current_owner_delta,
                arsenal=payload,
            ),
        )
    action_card = _tool_card_by_action_or_tool_id(payload).get(requested)
    if action_card is None:
        raise ValueError(f"No tool card for current_owner_delta action: {requested}")
    return _action_invocation_plan(
        action_card=action_card,
        current_owner_delta=current_owner_delta,
        capability_resolver_receipt=resolve_capability_candidates(
            current_owner_delta=current_owner_delta,
            arsenal=payload,
        ),
    )


def resolve_capability_candidates(
    *,
    current_owner_delta: Mapping[str, Any],
    task_intent: str = "",
    available_refs: list[str] | tuple[str, ...] | set[str] | None = None,
    arsenal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = arsenal if arsenal is not None else build_agent_tool_arsenal_index()
    return resolve_capability_candidates_from_arsenal(
        current_owner_delta=current_owner_delta,
        task_intent=task_intent,
        available_refs=list(available_refs or []),
        arsenal=payload,
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


def mcp_tool_annotations(
    tool_id: str,
    *,
    read_only: bool | None = None,
    destructive: bool | None = None,
) -> dict[str, Any]:
    is_read_only = bool(read_only)
    is_destructive = (not is_read_only) if destructive is None else bool(destructive)
    return {
        "readOnlyHint": is_read_only,
        "destructiveHint": False if is_read_only else is_destructive,
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
    non_read_only_gate = (
        _non_read_only_gate(requires_human_gate=bool(human_gate_ids))
        if not read_only or refs_only_runtime_write
        else None
    )
    if non_read_only_gate is not None:
        authority_boundary.update(_non_read_only_authority_boundary_fields(non_read_only_gate))
    authority_boundary = runtime_boundary.merge_opl_capability_runtime_boundary(authority_boundary)
    required_refs = [str(item) for item in list(action.get("workspace_locator_fields") or [])]
    card = {
        "surface_kind": "mas_tool_use_card",
        "operational_surface_kind": "mas_operational_tool_card",
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
        "default_invocation": default_invocation_for_action(
            mcp_tool_name=mcp_tool_name,
            mcp_tool_mode=mcp_tool_mode,
            public_runtime=public_runtime,
            descriptor_only=descriptor_only,
            command=_text(source_command.get("command")),
        ),
        "required_refs": required_refs,
        "optional_refs": [],
        "preflight_checks": preflight_checks_for_card(
            requires_stage_attempt=requires_stage_attempt
        ),
        "success_signals": success_signals_for_action(action_id=action_id),
        "failure_classes": failure_classes_for_card(
            requires_stage_attempt=requires_stage_attempt
        ),
        "next_safe_actions": next_safe_actions_for_action_card(
            tool_name=mcp_tool_name,
            tool_mode=mcp_tool_mode,
            callability=callability,
            required_refs=required_refs,
        ),
        "risk_annotations": {
            **mcp_tool_annotations(
                mcp_tool_name,
                read_only=read_only and not refs_only_runtime_write,
                destructive=False if refs_only_runtime_write else None,
            ),
            "requires_human_gate": bool(human_gate_ids),
            "requires_opl_stage_attempt_or_lease": requires_stage_attempt,
            "domain_truth_write": False,
        },
        "input_refs": required_refs,
        "input_schema_ref": _text(action.get("input_schema_ref")),
        "output_schema_ref": _text(action.get("output_schema_ref")),
        "output_schema": _output_schema_for_action(action),
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
        "executor_receipt_ref_policy": _executor_receipt_ref_policy(),
        "allowed_writes": (
            _allowed_writes_for_action(action_id)
            if (not read_only or refs_only_runtime_write)
            else []
        ),
        "forbidden_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
        "human_gate_ids": human_gate_ids,
        **({"non_read_only_gate": non_read_only_gate} if non_read_only_gate is not None else {}),
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
    attach_capability_invocation_os_fields(
        card,
        planning_root=ORDINARY_PLANNING_ROOT,
    )
    _attach_non_read_only_invocation_gate_fields(card)
    card["operational"] = operational_fields(card)
    return card


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
        non_read_only_gate = _non_read_only_gate(requires_human_gate=False)
        callable_surface = _required_text(
            callable_payload.get("callable_surface"),
            "callable_surface",
        )
        input_refs = _list_text(
            lifecycle.get("required_input_refs") or callable_payload.get("required_inputs")
        )
        card = {
            "surface_kind": "mas_owner_callable_tool_card",
            "operational_surface_kind": "mas_operational_tool_card",
            "card_kind": "owner_callable",
            "tool_id": f"owner_callable:{action_type}",
            "action_type": action_type,
            "owner": _required_text(callable_payload.get("owner"), "owner"),
            "callable_surface": callable_surface,
            "input_refs": input_refs,
            "required_refs": input_refs,
            "optional_refs": [],
            "required_output_refs": _list_text(
                lifecycle.get("required_output_refs") or callable_payload.get("required_outputs")
            ),
            "allowed_writes": _list_text(lifecycle.get("allowed_writes")),
            "forbidden_writes": _list_text(lifecycle.get("forbidden_writes")),
            "forbidden_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
            "closeout_contract": completion_proof,
            "default_invocation": {
                "surface": "owner_callable",
                "callable_surface": callable_surface,
                "arguments": {
                    "current_owner_delta": "<current_owner_delta>",
                },
            },
            "preflight_checks": preflight_checks_for_card(requires_stage_attempt=True),
            "success_signals": [
                "owner_receipt_ref_or_typed_blocker_ref_present",
                "allowed_writes_match_owner_callable_contract",
                "no_forbidden_authority_claim",
            ],
            "failure_classes": failure_classes_for_card(requires_stage_attempt=True),
            "next_safe_actions": [
                {
                    "action": "invoke_owner_callable_surface",
                    "requires": ["current_owner_delta", "required_refs"],
                },
                {
                    "action": "collect_missing_refs",
                    "when": "required_refs_missing",
                },
                {
                    "action": "surface_owner_needed",
                    "when": "owner_receipt_or_typed_blocker_missing",
                },
            ],
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
            "lightweight_executor_receipt_contract_ref": (
                LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF
            ),
            "executor_receipt_ref_policy": _executor_receipt_ref_policy(),
            "non_read_only_gate": non_read_only_gate,
            "authority_boundary": {
                **runtime_boundary.opl_capability_runtime_boundary(),
                "can_write_domain_truth": False,
                "can_write_publication_quality": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "owner_receipt_or_typed_blocker_required": bool(
                    completion_proof.get("requires_owner_receipt_or_typed_blocker")
                ),
                **_non_read_only_authority_boundary_fields(non_read_only_gate),
            },
        }
        attach_capability_invocation_os_fields(
            card,
            planning_root=ORDINARY_PLANNING_ROOT,
        )
        _attach_non_read_only_invocation_gate_fields(card)
        card["operational"] = operational_fields(card)
        cards.append(card)
    return sorted(cards, key=lambda item: str(item["action_type"]))


def _owner_callable_invocation_plan(
    *,
    owner_card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    capability_resolver_receipt: Mapping[str, Any] | None = None,
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
            "current_owner_delta_match": True,
            "human_gate_or_owner_delta": True,
            "owner_receipt_or_typed_blocker_proof": bool(
                _mapping(owner_card.get("non_read_only_gate")).get(
                    "requires_owner_receipt_or_typed_blocker_proof"
                )
            ),
            "executor_receipt_ref_required": False,
            "lightweight_executor_receipt_contract_ref": (
                LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF
            ),
        },
        "selection_policy": {
            "surface_kind": "mas_capability_selection_policy",
            "primary_selection": "owner_callable",
            "selection_reason": "current_owner_delta.action_type matched owner callable registry",
            "fallback_order": [
                "collect_missing_refs",
                "surface_owner_needed",
                "emit_typed_blocker_candidate",
            ],
            "support_or_diagnostic_tools_auto_selected": False,
            "missing_capability_default": "fail_open_unless_hard_gate",
        },
        "capability_resolver_receipt": dict(capability_resolver_receipt or {}),
        "primary_operational_card": operational_card_view(owner_card),
        "fallback_cards": [],
        "next_safe_actions": list(owner_card.get("next_safe_actions") or []),
        "invocation_steps": [
            "verify_required_input_refs",
            "verify_current_owner_delta_fingerprint",
            "verify_current_owner_delta_or_human_gate",
            "check_allowed_writes_and_forbidden_authority",
            "invoke_owner_callable_surface",
            "emit_tool_result_envelope",
            "attach_optional_lightweight_executor_receipt_ref",
        ],
        "authority_boundary": {
            **runtime_boundary.opl_capability_runtime_boundary(),
            "can_write_domain_truth": False,
            "can_write_publication_quality": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "tool_result_envelope_is_authority_outcome": False,
            "executor_receipt_can_block_current_owner_action": False,
            "executor_receipt_counts_as_owner_receipt": False,
            "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
            "capability_invocation_plan_replaces_owner_receipt": False,
        },
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
    }


def _action_invocation_plan(
    *,
    action_card: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    capability_resolver_receipt: Mapping[str, Any] | None = None,
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
            "current_owner_delta_match": True,
            "human_gate_or_owner_delta": bool(action_card.get("non_read_only_gate")),
            "owner_receipt_or_typed_blocker_proof": bool(
                _mapping(action_card.get("non_read_only_gate")).get(
                    "requires_owner_receipt_or_typed_blocker_proof"
                )
            ),
            "executor_receipt_ref_required": False,
            "lightweight_executor_receipt_contract_ref": (
                LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF
            ),
        },
        "selection_policy": {
            "surface_kind": "mas_capability_selection_policy",
            "primary_selection": "action_catalog",
            "selection_reason": (
                "current_owner_delta.action_type/action_id matched MAS action catalog card"
            ),
            "fallback_order": [
                "collect_missing_refs",
                "invoke_refs_only_capability_when_applicable",
                "emit_typed_blocker_candidate_when_hard_gate_blocks",
            ],
            "support_or_diagnostic_tools_auto_selected": False,
            "missing_capability_default": "fail_open_unless_hard_gate",
        },
        "capability_resolver_receipt": dict(capability_resolver_receipt or {}),
        "primary_operational_card": operational_card_view(action_card),
        "fallback_cards": fallback_cards_for_action(action_card),
        "next_safe_actions": list(action_card.get("next_safe_actions") or []),
        "invocation_steps": [
            "verify_required_input_refs",
            "verify_current_owner_delta_or_human_gate",
            "check_allowed_writes_and_forbidden_authority",
            "invoke_mcp_or_descriptor_target",
            "emit_tool_result_envelope",
            "attach_optional_lightweight_executor_receipt_ref",
        ],
        "authority_boundary": {
            **runtime_boundary.opl_capability_runtime_boundary(),
            "can_write_domain_truth": False,
            "can_write_publication_quality": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "tool_result_envelope_is_authority_outcome": False,
            "executor_receipt_can_block_current_owner_action": False,
            "executor_receipt_counts_as_owner_receipt": False,
            "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
            "capability_invocation_plan_replaces_owner_receipt": False,
        },
        "result_envelope_schema_ref": RESULT_ENVELOPE_SCHEMA_REF,
        "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
    }


def _capability_invocation_plan_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_invocation_plan_contract",
        "planning_root": ORDINARY_PLANNING_ROOT,
        "agent_default": True,
        "selection_order": [
            "current_owner_delta.action_type owner callable card",
            "current_owner_delta.action_id action catalog card",
            "ordinary public runtime action card",
            "refs-only advisory capability",
            "diagnostic/support tool only when explicitly requested",
            "typed_blocker candidate when no matching card exists",
        ],
        "hard_requirements": [
            "verify_required_input_refs",
            "verify_current_owner_delta_fingerprint_for_mutating_work",
            "check_allowed_writes_and_forbidden_authority",
            "emit_tool_result_envelope",
        ],
        "optional_receipt_evidence": {
            "executor_receipt_ref": "may_attach_when_available",
            "lightweight_executor_receipt_contract_ref": LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF,
            "can_block_current_owner_action": False,
        },
        "authority_boundary": runtime_boundary.opl_capability_runtime_boundary(),
        "agent_hot_path_rule": (
            "Autonomous agents consume AgentExecutionIndex, OperationalToolCard, "
            "CapabilityInvocationPlan, and ToolResultEnvelope; raw contracts remain "
            "generation and validation inputs."
        ),
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
        "when_to_use": card.get("when_to_use", ""),
        "required_refs": list(card.get("required_refs") or card.get("input_refs") or []),
        "discovery_hint": dict(_mapping(card.get("discovery_hint"))),
        "fit_signal": dict(_mapping(card.get("fit_signal"))),
        "invocation_gate": dict(_mapping(card.get("invocation_gate"))),
        "adaptation_policy": dict(_mapping(card.get("adaptation_policy"))),
        "next_step_hint": next_step_hint_for_card(card),
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


def _non_read_only_gate(*, requires_human_gate: bool) -> dict[str, Any]:
    return {
        "surface_kind": "mas_agent_tool_non_read_only_gate",
        "gate_policy": "current_owner_delta_or_human_gate_with_owner_receipt_typed_blocker_proof",
        "requires_current_owner_delta": True,
        "requires_current_owner_delta_match": True,
        "requires_human_gate_or_owner_delta": True,
        "requires_human_gate": requires_human_gate,
        "requires_owner_receipt_or_typed_blocker_proof": True,
        "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
        "can_substitute_owner_receipt": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_provider_admission": False,
        "can_start_worker_attempt": False,
    }


def _non_read_only_authority_boundary_fields(gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
        "can_substitute_owner_receipt": False,
        "can_authorize_provider_admission": False,
        "can_start_worker_attempt": False,
        "non_read_only_gate_policy": _text(gate.get("gate_policy")),
    }


def _attach_non_read_only_invocation_gate_fields(card: dict[str, Any]) -> None:
    gate = _mapping(card.get("non_read_only_gate"))
    if not gate:
        return
    invocation_gate = dict(_mapping(card.get("invocation_gate")))
    invocation_gate["non_read_only_gate_policy"] = _text(gate.get("gate_policy"))
    invocation_gate["owner_receipt_or_typed_blocker_required"] = bool(
        gate.get("requires_owner_receipt_or_typed_blocker_proof")
    )
    card["invocation_gate"] = invocation_gate


def _executor_receipt_ref_policy() -> dict[str, Any]:
    return {
        "field": "executor_receipt_ref",
        "required": False,
        "receipt_only": True,
        "can_block_current_owner_action": False,
    }


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


def _manifest_tool_names(
    *,
    mcp_tool_names: list[str] | tuple[str, ...] | set[str] | None,
    mcp_tool_manifest: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> set[str]:
    names = {str(item).strip() for item in (mcp_tool_names or []) if str(item).strip()}
    for item in list(mcp_tool_manifest or []):
        if not isinstance(item, Mapping):
            continue
        name = _text(item.get("name"))
        if name:
            names.add(name)
    return names


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
    "LIGHTWEIGHT_EXECUTOR_RECEIPT_CONTRACT_REF",
    "ORDINARY_PLANNING_ROOT",
    "RESULT_ENVELOPE_SCHEMA_REF",
    "build_agent_tool_arsenal_completeness_diagnostic",
    "build_agent_tool_arsenal_index",
    "build_capability_invocation_plan",
    "build_tool_audit_trail_schema",
    "build_tool_result_envelope_schema",
    "get_tool_use_card",
    "mcp_tool_annotations",
    "resolve_capability_candidates",
]
