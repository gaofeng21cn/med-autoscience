from __future__ import annotations


RECOVERY_FIELDS = {
    "retryability",
    "staleness",
    "missing_refs",
    "next_safe_actions",
    "owner_needed",
    "receipt_refs",
    "typed_blocker_refs",
    "diagnostic_refs",
    "no_forbidden_authority_claim",
}


def _assert_recovery_envelope(envelope: dict[str, object]) -> dict[str, object]:
    recovery = envelope["recovery"]
    assert isinstance(recovery, dict)
    assert RECOVERY_FIELDS <= set(recovery)
    assert recovery["retryability"] in {
        "retry_safe",
        "retry_after_refs",
        "no_retry",
        "owner_needed",
    }
    assert isinstance(recovery["staleness"], dict)
    assert isinstance(recovery["missing_refs"], list)
    assert isinstance(recovery["next_safe_actions"], list)
    for action in recovery["next_safe_actions"]:
        assert isinstance(action, dict)
        assert action["authority"] is False
        assert action["can_execute"] is False
        assert action["can_generate_action"] is False
        assert action["action_role"] == "tool_result_consumption_metadata"
    assert isinstance(recovery["owner_needed"], bool)
    assert isinstance(recovery["receipt_refs"], list)
    assert isinstance(recovery["typed_blocker_refs"], list)
    assert isinstance(recovery["diagnostic_refs"], list)
    assert recovery["no_forbidden_authority_claim"] is True
    return recovery


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    envelope = result["structuredContent"]
    assert isinstance(envelope, dict)
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert envelope["authority_boundary"]["can_write_domain_truth"] is False
    assert envelope["authority_boundary"]["can_authorize_publication_quality"] is False
    assert envelope["authority_boundary"]["can_authorize_submission_readiness"] is False
    _assert_recovery_envelope(envelope)
    payload = envelope["structured_payload"]
    assert isinstance(payload, dict)
    return payload


def _assert_tool_result_envelope(
    result: dict[str, object],
    *,
    tool_id: str,
    tool_mode: str | None = None,
) -> dict[str, object]:
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    assert structured["tool_id"] == tool_id
    if tool_mode is not None:
        assert structured["tool_mode"] == tool_mode
    assert structured["status"] in {"succeeded", "blocked", "no_op_current", "failed"}
    assert structured["structured_content_ref"] == (
        f"mcp://med-autoscience/tools/{tool_id}/structuredContent"
    )
    assert structured["audit_trail"]["surface_kind"] == "mas_tool_audit_trail"
    assert "publication_quality" in structured["audit_trail"]["forbidden_authority"]
    assert structured["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert isinstance(structured["structured_payload"], dict)
    _assert_recovery_envelope(structured)
    assert structured["retryability"] in {
        "retry_safe",
        "retry_after_refs",
        "no_retry",
        "owner_needed",
    }
    assert isinstance(structured["staleness"], dict)
    assert isinstance(structured["missing_refs"], list)
    assert isinstance(structured["next_safe_actions"], list)
    for action in structured["next_safe_actions"]:
        assert isinstance(action, dict)
        assert action["authority"] is False
        assert action["can_execute"] is False
        assert action["can_generate_action"] is False
        assert action["action_role"] == "tool_result_consumption_metadata"
    assert isinstance(structured["owner_needed"], bool)
    assert isinstance(structured["receipt_refs"], list)
    assert isinstance(structured["typed_blocker_refs"], list)
    assert isinstance(structured["diagnostic_refs"], list)
    assert structured["no_forbidden_authority_claim"] is True
    return structured
