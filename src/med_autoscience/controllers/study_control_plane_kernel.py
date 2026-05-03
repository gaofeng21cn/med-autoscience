from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


SCHEMA_VERSION = 1

READY_ACTIONS_REQUIRING_AI_REVIEWER = frozenset(
    {
        "reviewer_ready",
        "bundle_only_remaining",
        "finalize",
        "finalize_ready",
        "submission_ready",
        "direct_paper_line_write",
        "direct_bundle_build",
        "direct_compiled_bundle_proofing",
    }
)
PAPER_WRITE_ACTIONS = frozenset(
    {
        "direct_study_execution",
        "direct_runtime_owned_write",
        "direct_paper_line_write",
    }
)
BUNDLE_ACTIONS = frozenset({"direct_bundle_build", "direct_compiled_bundle_proofing"})
LEDGER_BLOCKING_STATES = frozenset(
    {
        "closed",
        "needs_specificity",
        "platform_repair_required",
        "await_artifact_delta",
        "await_artifact_delta_or_gate_replay",
        "gate_reread_required",
    }
)
BASE_ALLOWED_ACTIONS = (
    "read_runtime_status",
    "probe_runtime_liveness",
    "reconcile_control_plane",
    "reconcile_truth",
    "reconcile_runtime_health",
    "open_monitoring_entry",
    "record_user_decision",
)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _string_items(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, str | bytes | Mapping):
        text = _text(value)
        return [text] if text is not None else []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _authority_ref(snapshot: Mapping[str, Any], *, epoch_key: str, path_key: str | None = None) -> dict[str, Any]:
    return {
        "epoch": _text(snapshot.get(epoch_key)),
        "path": _text(snapshot.get(path_key)) if path_key is not None else None,
        "source_signature": _text(snapshot.get("source_signature")),
    }


def _publication_eval_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("publication_eval", "publication_eval_latest", "publication_eval_payload"):
        candidate = _mapping(payload.get(key))
        if candidate:
            return candidate
    return {}


def _ledger_lifecycle_state(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        direct = _mapping(payload.get(key))
        if not direct:
            continue
        state = (
            _text(direct.get("lifecycle_state"))
            or _text(direct.get("state"))
            or _text(direct.get("latest_event_type"))
        )
        if state is not None:
            return state
    return None


def _control_state(blocking_reasons: list[str], runtime_action: str) -> str:
    if "publication_eval.ai_reviewer_required" in blocking_reasons:
        return "blocked_quality_review"
    if "runtime_recovery_retry_budget_exhausted" in blocking_reasons or runtime_action == "escalate_runtime":
        return "blocked_runtime_escalation"
    if any(reason.startswith("controller_decision.") for reason in blocking_reasons):
        return "blocked_controller_decision"
    if any(reason.startswith("ledger.") for reason in blocking_reasons):
        return "blocked_ledger"
    if "study_truth_epoch_missing" in blocking_reasons or "runtime_health_epoch_missing" in blocking_reasons:
        return "needs_reconcile"
    if (
        "execution_owner_guard.supervisor_only" in blocking_reasons
        or "publication_supervisor_state.bundle_tasks_downstream_only" in blocking_reasons
    ):
        return "supervisor_gated"
    return "ready"


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reason for reason in reasons if reason))


def build_control_plane_snapshot(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(status_payload)
    truth = _mapping(payload.get("study_truth_snapshot"))
    health = _mapping(payload.get("runtime_health_snapshot"))
    publication_eval = _publication_eval_payload(payload)
    truth_epoch = _text(truth.get("truth_epoch") or truth.get("authority_epoch"))
    health_epoch = _text(health.get("runtime_health_epoch"))
    truth_action = _text(truth.get("canonical_next_action")) or _text(payload.get("canonical_next_action")) or "observe"
    runtime_action = _text(health.get("canonical_runtime_action")) or "continue_supervising_runtime"
    allowed_actions = _string_items(truth.get("allowed_controller_actions")) or list(BASE_ALLOWED_ACTIONS)
    blocking_reasons = [
        *_string_items(truth.get("blocking_reasons")),
        *_string_items(health.get("blocking_reasons")),
    ]

    if truth_epoch is None:
        blocking_reasons.append("study_truth_epoch_missing")
    if health_epoch is None:
        blocking_reasons.append("runtime_health_epoch_missing")
        runtime_action = "probe_runtime_liveness"
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    publication_action = _text(publication_eval.get("current_required_action"))
    if (
        (_text(provenance.get("owner")) != "ai_reviewer" or publication_eval.get("ai_reviewer_required") is True)
        and (truth_action in READY_ACTIONS_REQUIRING_AI_REVIEWER or publication_action in READY_ACTIONS_REQUIRING_AI_REVIEWER)
    ):
        blocking_reasons.append("publication_eval.ai_reviewer_required")
        truth_action = "review_required"

    control_intent_state = _ledger_lifecycle_state(payload, "control_intent", "control_intent_lifecycle")
    work_unit_state = _ledger_lifecycle_state(payload, "work_unit", "work_unit_lifecycle", "work_unit_ledger")
    for ledger_name, state in (("control_intent", control_intent_state), ("work_unit", work_unit_state)):
        if state in LEDGER_BLOCKING_STATES:
            blocking_reasons.append(f"ledger.{ledger_name}.{state}")

    retry_budget = _int(health.get("retry_budget_remaining"))
    if (
        _text(health.get("attempt_state")) == "escalated"
        or retry_budget == 0
        and runtime_action in {"recover_runtime", "relaunch_runtime", "probe_runtime_liveness"}
    ):
        blocking_reasons.append("runtime_recovery_retry_budget_exhausted")
        runtime_action = "escalate_runtime"

    if "execution_owner_guard.supervisor_only" in blocking_reasons:
        allowed_actions = [action for action in allowed_actions if action not in PAPER_WRITE_ACTIONS | BUNDLE_ACTIONS]
    if "publication_supervisor_state.bundle_tasks_downstream_only" in blocking_reasons:
        allowed_actions = [action for action in allowed_actions if action not in BUNDLE_ACTIONS]

    blocking_reasons = _dedupe_reasons(blocking_reasons)
    dispatch_blocked = bool(blocking_reasons)
    if "study_truth_epoch_missing" in blocking_reasons or "runtime_health_epoch_missing" in blocking_reasons:
        truth_action = "read_runtime_status"

    paper_write_allowed = not (
        "execution_owner_guard.supervisor_only" in blocking_reasons
        or "publication_eval.ai_reviewer_required" in blocking_reasons
    )
    bundle_build_allowed = not (
        "execution_owner_guard.supervisor_only" in blocking_reasons
        or "publication_supervisor_state.bundle_tasks_downstream_only" in blocking_reasons
        or "publication_eval.ai_reviewer_required" in blocking_reasons
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface": "control_plane_snapshot",
        "study_id": _text(payload.get("study_id")) or _text(truth.get("study_id")) or _text(health.get("study_id")),
        "quest_id": _text(payload.get("quest_id")) or _text(health.get("quest_id")),
        "control_state": _control_state(blocking_reasons, runtime_action),
        "canonical_next_action": truth_action,
        "canonical_runtime_action": runtime_action,
        "dispatch_gate": {
            "state": "blocked" if dispatch_blocked else "open",
            "dispatch_allowed": not dispatch_blocked,
            "blocking_reasons": blocking_reasons,
        },
        "route_authorization": {
            "authorized": not dispatch_blocked,
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": runtime_action not in {"await_explicit_resume", "escalate_runtime"},
        },
        "blocking_reasons": blocking_reasons,
        "allowed_controller_actions": allowed_actions,
        "authority_refs": {
            "study_truth": _authority_ref(truth, epoch_key="truth_epoch", path_key="event_log_path"),
            "runtime_health": _authority_ref(health, epoch_key="runtime_health_epoch", path_key="event_log_path"),
            "publication_eval": {
                "owner": _text(provenance.get("owner")),
                "current_required_action": publication_action,
            },
            "controller_decision": _mapping(payload.get("controller_decision_ref"))
            or _mapping(payload.get("controller_decision")),
        },
        "quality_gate_relaxation_allowed": False,
        "generated_from_authority_surfaces": True,
    }
