from __future__ import annotations

from typing import Any, Mapping


_EXTERNAL_ACCOUNT_CODES = frozenset(
    {
        "codex_upstream_quota_error",
        "provider_env_missing",
        "runner_model_unavailable",
    }
)
_EXTERNAL_TRANSIENT_CODES = frozenset({"codex_upstream_provider_error"})
_RUNTIME_RECONCILIATION_CODES = frozenset(
    {
        "daemon_no_live_worker",
        "daemon_stalled_live_turn",
    }
)
_HUMAN_GATE_CODES = frozenset({"runtime_intentionally_parked"})
_PLATFORM_BUG_CODES = frozenset(
    {
        "provider_invalid_params",
        "minimax_tool_result_sequence_error",
        "chat_wire_tool_argument_parse_error",
        "runner_retry_budget_exhausted",
        "runner_argument_list_too_long",
        "runner_binary_attachment_path_unsupported",
    }
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _diagnosis_from_profile(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in (
        "mds_failure_diagnosis",
        "runtime_failure_diagnosis",
        "failure_diagnosis",
    ):
        diagnosis = _mapping(profile_payload.get(key))
        if diagnosis:
            return diagnosis
    mds_activity = _mapping(profile_payload.get("mds_worker_activity"))
    for key in ("mds_failure_diagnosis", "runtime_failure_diagnosis", "failure_diagnosis"):
        diagnosis = _mapping(mds_activity.get(key))
        if diagnosis:
            return diagnosis
    diagnosis_code = _text(mds_activity.get("diagnosis_code"))
    if diagnosis_code is not None:
        return {
            "diagnosis_code": diagnosis_code,
            "retriable": _bool(mds_activity.get("retriable")),
            "problem": _text(mds_activity.get("problem")),
        }
    return {}


def classify_mds_failure_diagnosis(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    diagnosis_code = _text(diagnosis.get("diagnosis_code")) or _text(diagnosis.get("code"))
    retriable = _bool(diagnosis.get("retriable"))
    if diagnosis_code is None:
        return {
            "diagnosis_code": None,
            "blocker_class": "none",
            "action_mode": "continue_slo_policy",
            "auto_recovery_allowed": True,
            "external_blocker": False,
            "requires_human_gate": False,
            "problem": _text(diagnosis.get("problem")),
        }
    if diagnosis_code in _EXTERNAL_ACCOUNT_CODES:
        blocker_class = "external_provider_account_blocker"
        action_mode = "external_fix_required"
        auto_recovery_allowed = False
        external_blocker = True
        requires_human_gate = True
    elif diagnosis_code in _EXTERNAL_TRANSIENT_CODES:
        blocker_class = "external_provider_transient"
        action_mode = "provider_backoff_and_recheck"
        auto_recovery_allowed = retriable is not False
        external_blocker = True
        requires_human_gate = False
    elif diagnosis_code in _RUNTIME_RECONCILIATION_CODES:
        blocker_class = "runtime_reconciliation_required"
        action_mode = "runtime_reconcile_then_resume"
        auto_recovery_allowed = True
        external_blocker = False
        requires_human_gate = False
    elif diagnosis_code in _HUMAN_GATE_CODES:
        blocker_class = "intentional_human_or_resume_gate"
        action_mode = "wait_for_user_or_explicit_resume"
        auto_recovery_allowed = False
        external_blocker = False
        requires_human_gate = True
    elif diagnosis_code in _PLATFORM_BUG_CODES:
        blocker_class = "platform_protocol_or_runner_bug"
        action_mode = "platform_repair_required"
        auto_recovery_allowed = False
        external_blocker = False
        requires_human_gate = True
    else:
        blocker_class = "unknown_runtime_failure"
        action_mode = "inspect_before_resume"
        auto_recovery_allowed = retriable is True
        external_blocker = False
        requires_human_gate = retriable is not True
    return {
        "diagnosis_code": diagnosis_code,
        "blocker_class": blocker_class,
        "action_mode": action_mode,
        "auto_recovery_allowed": auto_recovery_allowed,
        "external_blocker": external_blocker,
        "requires_human_gate": requires_human_gate,
        "problem": _text(diagnosis.get("problem")),
        "retriable": retriable,
    }


def classify_runtime_failure_from_profile(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    return classify_mds_failure_diagnosis(_diagnosis_from_profile(profile_payload))
