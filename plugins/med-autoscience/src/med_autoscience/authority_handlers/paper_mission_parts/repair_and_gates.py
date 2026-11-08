"""PaperMission repair-state and hard-gate normalizers."""

from __future__ import annotations

from typing import Any

from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_keys,
    integer,
    mapping,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    typed_ref_list as _typed_ref_list,
)
from .constants import _HARD_GATE_KINDS

def _normalize_repair(value: Any) -> dict[str, Any]:
    field = "repair_state"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "status",
            "attempts_used",
            "max_attempts",
            "repair_attempt_refs",
            "latest_repair_output_ref",
        },
        field,
    )
    attempts_used = integer(payload.get("attempts_used"), f"{field}.attempts_used")
    max_attempts = integer(payload.get("max_attempts"), f"{field}.max_attempts")
    if max_attempts != 3:
        raise RequestShapeError(
            "repair_state.max_attempts must equal the OPL scope budget of 3"
        )
    if attempts_used > max_attempts:
        raise RequestShapeError("repair_state.attempts_used cannot exceed max_attempts")
    attempt_refs = _typed_ref_list(
        payload.get("repair_attempt_refs"),
        f"{field}.repair_attempt_refs",
        "opl_stage_attempt",
    )
    if len(attempt_refs) != attempts_used:
        raise RequestShapeError("repair_attempt_refs must exactly match attempts_used")
    return {
        "status": enum_text(
            payload.get("status"),
            f"{field}.status",
            {"not_required", "pending", "completed", "exhausted", "failed"},
        ),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "repair_attempt_refs": attempt_refs,
        "latest_repair_output_ref": _optional_typed_ref(
            payload.get("latest_repair_output_ref"),
            f"{field}.latest_repair_output_ref",
            "opl_action_output",
        ),
    }


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    field = "hard_gate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        field,
    )
    kind = enum_text(
        payload.get("kind"),
        f"{field}.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": optional_text(
            payload.get("reason_code"), f"{field}.reason_code"
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"),
            f"{field}.evidence_refs",
            "mas_gate_evidence",
        ),
        "next_owner": optional_text(payload.get("next_owner"), f"{field}.next_owner"),
        "resume_condition": optional_text(
            payload.get("resume_condition"), f"{field}.resume_condition"
        ),
    }
    if kind == "none":
        if any(
            (
                normalized["reason_code"] is not None,
                bool(normalized["evidence_refs"]),
                normalized["next_owner"] is not None,
                normalized["resume_condition"] is not None,
            )
        ):
            raise RequestShapeError("hard_gate.kind none requires an empty gate record")
        return normalized
    missing = [
        name
        for name in ("reason_code", "next_owner", "resume_condition")
        if normalized[name] is None
    ]
    if not normalized["evidence_refs"]:
        missing.append("evidence_refs")
    if missing:
        raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    return normalized
