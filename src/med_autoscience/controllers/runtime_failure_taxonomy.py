from __future__ import annotations

from typing import Any, Mapping


_EXTERNAL_ACCOUNT_CODES = frozenset(
    {
        "codex_upstream_quota_error",
        "provider_env_missing",
        "runner_model_unavailable",
        "upstream_plugin_auth_403",
        "plugin_auth_403",
    }
)
_EXTERNAL_TRANSIENT_CODES = frozenset({"codex_upstream_provider_error", "codex_external_startup_noise"})
_PLATFORM_STARTUP_NOISE_CODES = frozenset(
    {
        "mds_external_startup_noise",
        "external_startup_noise",
        "runtime_startup_noise",
    }
)
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
_EXTERNAL_ACCOUNT_TEXT_MARKERS = (
    "account balance is negative",
    "insufficient balance",
    "insufficient quota",
    "quota exceeded",
    "billing",
    "payment required",
    "account disabled",
    "account blocker",
    "auth returned http 403",
    "plugin auth returned http 403",
    "authentication returned http 403",
)
_EXTERNAL_TRANSIENT_TEXT_MARKERS = (
    "codex upstream",
    "upstream api",
    "upstream provider",
    "provider unavailable",
    "provider rate limit",
    "rate limit exceeded",
    "openai api",
    "anthropic api",
)
_STARTUP_NOISE_TEXT_MARKERS = (
    "external startup noise",
    "startup noise",
    "worker startup noise",
    "startup transient noise",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _lowered_texts(*values: object) -> tuple[str, ...]:
    return tuple(text.lower() for value in values if (text := _text(value)) is not None)


def _contains_any(texts: tuple[str, ...], markers: tuple[str, ...]) -> bool:
    return any(marker in text for text in texts for marker in markers)


def _looks_like_codex_upstream_code(value: str | None) -> bool:
    return bool(value and value.startswith("codex_upstream_"))


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
    problem = _text(diagnosis.get("problem"))
    failure_texts = _lowered_texts(diagnosis_code, problem, diagnosis.get("message"), diagnosis.get("raw_error"))
    account_like_external = _contains_any(failure_texts, _EXTERNAL_ACCOUNT_TEXT_MARKERS)
    transient_like_external = _contains_any(failure_texts, _EXTERNAL_TRANSIENT_TEXT_MARKERS)
    startup_noise = diagnosis_code in _PLATFORM_STARTUP_NOISE_CODES or _contains_any(
        failure_texts,
        _STARTUP_NOISE_TEXT_MARKERS,
    )
    codex_upstream_failure = _looks_like_codex_upstream_code(diagnosis_code) or (
        any("codex" in text for text in failure_texts)
        and any(marker in text for text in failure_texts for marker in ("upstream", "api", "provider"))
    )
    if diagnosis_code is None and not account_like_external and not transient_like_external and not codex_upstream_failure:
        return {
            "diagnosis_code": None,
            "blocker_class": "none",
            "action_mode": "continue_slo_policy",
            "auto_recovery_allowed": True,
            "external_blocker": False,
            "requires_human_gate": False,
            "paper_quality_blocker": False,
            "problem": problem,
        }
    if startup_noise:
        blocker_class = "platform_runtime_startup_noise"
        action_mode = "platform_startup_backoff_and_recheck"
        auto_recovery_allowed = retriable is not False
        external_blocker = False
        requires_human_gate = False
    elif diagnosis_code in _EXTERNAL_ACCOUNT_CODES:
        blocker_class = "external_provider_account_blocker"
        action_mode = "external_fix_required"
        auto_recovery_allowed = False
        external_blocker = True
        requires_human_gate = True
    elif account_like_external:
        blocker_class = "external_provider_account_blocker"
        action_mode = "external_fix_required"
        auto_recovery_allowed = False
        external_blocker = True
        requires_human_gate = True
    elif diagnosis_code in _EXTERNAL_TRANSIENT_CODES or codex_upstream_failure or transient_like_external:
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
        "paper_quality_blocker": False,
        "problem": problem,
        "retriable": retriable,
    }


def classify_runtime_failure_from_profile(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    return classify_mds_failure_diagnosis(_diagnosis_from_profile(profile_payload))
