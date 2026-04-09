from __future__ import annotations

from typing import Any


_EXTERNAL_INPUT_DECISION_TYPES = frozenset(
    {
        "external_credential_request",
        "external_secret_request",
    }
)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _has_structured_reply_schema(reply_schema: dict[str, Any]) -> bool:
    if not reply_schema:
        return False
    if set(reply_schema) == {"type"} and str(reply_schema.get("type") or "").strip().lower() == "free_text":
        return False
    return True


def arbitrate_waiting_for_user(
    *,
    pending_interaction: dict[str, Any] | None,
    decision_policy: str | None,
    submission_metadata_only: bool,
) -> dict[str, Any]:
    if submission_metadata_only:
        return {
            "classification": "submission_metadata_only",
            "action": "resume",
            "reason_code": "submission_metadata_only",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": None,
            "decision_type": None,
            "source_artifact_path": None,
            "controller_stage_note": (
                "Submission metadata gaps stay controller-owned and must not block autonomous runtime continuation."
            ),
        }

    if not isinstance(pending_interaction, dict):
        return {
            "classification": "unclassified_waiting_state",
            "action": "block",
            "reason_code": "missing_pending_interaction_payload",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": None,
            "decision_type": None,
            "source_artifact_path": None,
            "controller_stage_note": (
                "MAS-managed waiting_for_user requires a controller-readable interaction payload before it can be classified."
            ),
        }

    kind = _text(pending_interaction.get("kind"))
    decision_type = _text(pending_interaction.get("decision_type"))
    source_artifact_path = _text(pending_interaction.get("source_artifact_path"))
    options_count = int(pending_interaction.get("options_count") or 0)
    guidance_requires_user_decision = pending_interaction.get("guidance_requires_user_decision")
    reply_schema = pending_interaction.get("reply_schema")
    structured_reply_schema = isinstance(reply_schema, dict) and _has_structured_reply_schema(reply_schema)
    normalized_policy = _text(decision_policy) or "autonomous"

    if kind != "decision_request":
        return {
            "classification": "invalid_blocking",
            "action": "resume",
            "reason_code": "blocking_requires_structured_decision_request",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": kind,
            "decision_type": decision_type,
            "source_artifact_path": source_artifact_path,
            "controller_stage_note": (
                "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
                "runtime blocking is rejected unless it is a valid structured decision request."
            ),
        }

    if guidance_requires_user_decision is False:
        return {
            "classification": "invalid_blocking",
            "action": "resume",
            "reason_code": "blocking_requires_structured_decision_request",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": kind,
            "decision_type": decision_type,
            "source_artifact_path": source_artifact_path,
            "controller_stage_note": (
                "MAS rejects blocking interactions that explicitly declare no user decision is required."
            ),
        }

    if options_count <= 0 and not structured_reply_schema:
        return {
            "classification": "invalid_blocking",
            "action": "resume",
            "reason_code": "blocking_requires_structured_decision_request",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": kind,
            "decision_type": decision_type,
            "source_artifact_path": source_artifact_path,
            "controller_stage_note": (
                "Blocking decision requests must carry structured options or a non-trivial reply schema."
            ),
        }

    if decision_type in _EXTERNAL_INPUT_DECISION_TYPES:
        return {
            "classification": "external_input_required",
            "action": "block",
            "reason_code": "external_secret_or_credential_required",
            "requires_user_input": True,
            "valid_blocking": True,
            "kind": kind,
            "decision_type": decision_type,
            "source_artifact_path": source_artifact_path,
            "controller_stage_note": (
                "Only explicit external secrets or credentials may stay user-blocking under MAS management."
            ),
        }

    reason_code = (
        "autonomous_policy_rejects_runtime_user_gate"
        if normalized_policy == "autonomous"
        else "mas_managed_policy_rejects_runtime_user_gate"
    )
    return {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": reason_code,
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": kind,
        "decision_type": decision_type,
        "source_artifact_path": source_artifact_path,
        "controller_stage_note": (
            "MAS-managed studies must keep routing, finalize, adequacy, publishability, and completion decisions "
            "inside the MAS outer loop; runtime blocking may only ask for external secrets or credentials."
        ),
    }
