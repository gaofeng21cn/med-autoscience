from __future__ import annotations

from typing import Any


def build_tool_result_envelope_schema(
    *,
    lightweight_executor_receipt_contract_ref: str,
) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MAS ToolResultEnvelope",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "surface_kind",
            "tool_id",
            "status",
            "recovery",
            "audit_trail",
            "authority_boundary",
        ],
        "properties": {
            "surface_kind": {"const": "mas_tool_result_envelope"},
            "tool_id": {"type": "string"},
            "tool_mode": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["succeeded", "blocked", "no_op_current", "failed"],
            },
            "content_ref": {"type": "string"},
            "structured_content_ref": {"type": "string"},
            "structured_payload": {"type": "object"},
            "raw_surface_kind": {"type": "string"},
            "executor_receipt_ref": {"type": "string"},
            "lightweight_executor_receipt_contract_ref": {
                "const": lightweight_executor_receipt_contract_ref,
            },
            "owner_receipt_ref": {"type": "string"},
            "typed_blocker_ref": {"type": "string"},
            "receipt_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "typed_blocker_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "diagnostic_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "missing_refs": {
                "type": "array",
                "items": {"type": "string"},
            },
            "retryability": {
                "type": "string",
                "enum": ["retry_safe", "retry_after_refs", "no_retry", "owner_needed"],
            },
            "staleness": {"type": "object"},
            "next_safe_actions": {
                "type": "array",
                "items": {"type": "object"},
            },
            "owner_needed": {"type": "boolean"},
            "no_forbidden_authority_claim": {"type": "boolean"},
            "recovery": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "retryability",
                    "staleness",
                    "missing_refs",
                    "next_safe_actions",
                    "owner_needed",
                    "receipt_refs",
                    "typed_blocker_refs",
                    "diagnostic_refs",
                    "no_forbidden_authority_claim",
                ],
                "properties": {
                    "retryability": {
                        "type": "string",
                        "enum": [
                            "retry_safe",
                            "retry_after_refs",
                            "no_retry",
                            "owner_needed",
                        ],
                    },
                    "staleness": {"type": "object"},
                    "missing_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "next_safe_actions": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "owner_needed": {"type": "boolean"},
                    "receipt_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "typed_blocker_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "diagnostic_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "no_forbidden_authority_claim": {"const": True},
                },
            },
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


__all__ = [
    "build_tool_audit_trail_schema",
    "build_tool_result_envelope_schema",
]
