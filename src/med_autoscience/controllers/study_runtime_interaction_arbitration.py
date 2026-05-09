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


def _invalid_decision_request_note(
    *,
    kind: str | None,
    guidance_requires_user_decision: object,
    options_count: int,
    structured_reply_schema: bool,
) -> str | None:
    if kind != "decision_request":
        return (
            "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
            "runtime blocking is rejected unless it is a valid structured decision request."
        )
    if guidance_requires_user_decision is False:
        return "MAS rejects blocking interactions that explicitly declare no user decision is required."
    if options_count <= 0 and not structured_reply_schema:
        return "Blocking decision requests must carry structured options or a non-trivial reply schema."
    return None


def _invalid_blocking_result(
    *,
    kind: str | None,
    decision_type: str | None,
    source_artifact_path: str | None,
    controller_stage_note: str,
) -> dict[str, Any]:
    return {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": "blocking_requires_structured_decision_request",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": kind,
        "decision_type": decision_type,
        "source_artifact_path": source_artifact_path,
        "controller_stage_note": controller_stage_note,
    }


def arbitrate_waiting_for_user(
    *,
    pending_interaction: dict[str, Any] | None,
    decision_policy: str | None,
    submission_metadata_only: bool,
    publication_gate_report: dict[str, Any] | None = None,
    blocked_closeout: dict[str, Any] | None = None,
    continuation_state: dict[str, Any] | None = None,
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
        pending_redrive = _pending_user_message_redrive(continuation_state)
        if pending_redrive is not None:
            return pending_redrive
        platform_repair_redrive = _platform_repair_decision_redrive(continuation_state)
        if platform_repair_redrive is not None:
            return platform_repair_redrive
        blocked_closeout_wait = _blocked_closeout_owner_wait(blocked_closeout)
        if blocked_closeout_wait is not None:
            return blocked_closeout_wait
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
    publication_gate_status = _text((publication_gate_report or {}).get("status"))
    publication_gate_blockers = list((publication_gate_report or {}).get("blockers") or [])
    publication_gate_required_action = _text((publication_gate_report or {}).get("current_required_action"))

    if decision_type == "quest_completion_approval" and publication_gate_status not in {None, "clear"}:
        return {
            "classification": "premature_completion_request",
            "action": "resume",
            "reason_code": "completion_requested_before_publication_gate_clear",
            "requires_user_input": False,
            "valid_blocking": False,
            "kind": kind,
            "decision_type": decision_type,
            "source_artifact_path": source_artifact_path,
            "publication_gate_status": publication_gate_status,
            "publication_gate_blockers": publication_gate_blockers,
            "publication_gate_required_action": publication_gate_required_action,
            "controller_stage_note": (
                "Runtime completion approval was requested before the MAS publication gate cleared; "
                "resume the managed runtime so it fixes publication blockers instead of asking the user."
            ),
        }

    invalid_decision_note = _invalid_decision_request_note(
        kind=kind,
        guidance_requires_user_decision=guidance_requires_user_decision,
        options_count=options_count,
        structured_reply_schema=structured_reply_schema,
    )
    if invalid_decision_note is not None:
        return _invalid_blocking_result(
            kind=kind,
            decision_type=decision_type,
            source_artifact_path=source_artifact_path,
            controller_stage_note=invalid_decision_note,
        )

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


def _pending_user_message_redrive(continuation_state: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(continuation_state, dict):
        return None
    continuation_policy = _text(continuation_state.get("continuation_policy"))
    continuation_anchor = _text(continuation_state.get("continuation_anchor"))
    continuation_reason = _text(continuation_state.get("continuation_reason"))
    if continuation_policy != "auto":
        return None
    if continuation_anchor != "user_message_queue":
        return None
    if continuation_reason != "runtime_platform_repair_resume_existing_pending_user_message":
        return None
    pending_count = continuation_state.get("pending_user_message_count")
    if not isinstance(pending_count, int) or pending_count <= 0:
        return None
    return {
        "classification": "pending_user_message_redrive",
        "action": "resume",
        "reason_code": "runtime_platform_repair_pending_user_message_redrive",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "user_message_queue",
        "decision_type": None,
        "source_artifact_path": None,
        "pending_user_message_count": pending_count,
        "controller_stage_note": (
            "Runtime platform repair marked an existing pending user-message queue for autonomous redrive; "
            "resume the managed runtime instead of parking on waiting_for_user."
        ),
    }


def _platform_repair_decision_redrive(continuation_state: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(continuation_state, dict):
        return None
    continuation_policy = _text(continuation_state.get("continuation_policy"))
    continuation_anchor = _text(continuation_state.get("continuation_anchor"))
    continuation_reason = _text(continuation_state.get("continuation_reason"))
    if continuation_policy != "auto":
        return None
    if continuation_anchor != "decision":
        return None
    if continuation_reason not in {
        "runtime_platform_repair_redrive",
        "controller_work_unit_pending",
    }:
        return None
    pending_count = continuation_state.get("pending_user_message_count")
    if isinstance(pending_count, int) and pending_count > 0:
        return None
    return {
        "classification": "platform_repair_decision_redrive",
        "action": "resume",
        "reason_code": "runtime_platform_repair_decision_redrive",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "runtime_platform_repair",
        "decision_type": None,
        "source_artifact_path": None,
        "pending_user_message_count": int(pending_count or 0),
        "controller_stage_note": (
            "Runtime platform repair marked the controller decision lane for autonomous redrive; "
            "resume the managed runtime instead of parking on waiting_for_user."
        ),
    }


def _blocked_closeout_owner_wait(blocked_closeout: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(blocked_closeout, dict):
        return None
    closeout_path = _text(blocked_closeout.get("closeout_path"))
    next_owner = _text(blocked_closeout.get("next_owner"))
    if closeout_path is None and next_owner is None:
        return None
    return {
        "classification": "blocked_closeout_owner_wait",
        "action": "block",
        "reason_code": "blocked_turn_closeout_waiting_for_owner",
        "requires_user_input": False,
        "valid_blocking": True,
        "kind": "turn_closeout",
        "decision_type": None,
        "source_artifact_path": closeout_path,
        "run_id": _text(blocked_closeout.get("run_id")),
        "next_owner": next_owner,
        "blocked_reason": _text(blocked_closeout.get("blocked_reason")),
        "controller_stage_note": (
            "The latest MAS turn closeout parked execution for a named owner; "
            "this is a controller-readable wait state, not a missing pending interaction payload."
        ),
    }
