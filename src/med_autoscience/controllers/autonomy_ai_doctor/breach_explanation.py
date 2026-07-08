from __future__ import annotations

from collections.abc import Mapping
from typing import Any


BREACH_REASON_PRIORITY = (
    "human_gate_required",
    "publication_gate_missing",
    "runtime_recovery_retry_budget_exhausted",
    "opl_runtime_handoff_required",
    "read_churn_without_artifact_delta",
    "same_fingerprint_loop",
    "stale_truth_surface",
    "gate_closure_drift",
    "no_meaningful_progress",
    "late_success_timeout",
)


def with_breach_explanation(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    result = dict(payload)
    if _text(result.get("state")) != "breach":
        return result
    breach_reason = _breach_reason(result)
    result["breach_reason"] = breach_reason
    result["breach_explanation"] = _breach_explanation(result, breach_reason=breach_reason)
    return result


def _breach_reason(payload: Mapping[str, Any]) -> str:
    explicit = _text(payload.get("breach_reason"))
    if explicit is not None:
        return explicit
    breach_types = {item for value in _list(payload.get("breach_types")) if (item := _text(value)) is not None}
    blockers = {
        item
        for value in (
            *_list(payload.get("blocking_reasons")),
            *_list(_mapping(payload.get("runtime_health_snapshot")).get("blocking_reasons")),
            *_list(_mapping(payload.get("authority_snapshot")).get("blocking_reasons")),
        )
        if (item := _text(value)) is not None
    }
    resume_contract = _mapping(_mapping(payload.get("family_checkpoint_lineage")).get("resume_contract"))
    if resume_contract.get("human_gate_required") is True or "human_gate_required" in blockers:
        return "human_gate_required"
    if "publication_gate_missing" in blockers:
        return "publication_gate_missing"
    if (
        "runtime_recovery_retry_budget_exhausted" in blockers
        or _mapping(payload.get("runtime_health_snapshot")).get("retry_budget_remaining") == 0
    ):
        return "runtime_recovery_retry_budget_exhausted"
    for candidate in BREACH_REASON_PRIORITY:
        if candidate in breach_types:
            return candidate
    return sorted(breach_types)[0] if breach_types else "unclassified_breach"


def _breach_explanation(payload: Mapping[str, Any], *, breach_reason: str) -> dict[str, Any]:
    owner_route = _first_mapping(
        payload.get("owner_route"),
        _mapping(_mapping(payload.get("runtime_continuity")).get("domain_authority_handoff")).get("owner_route"),
        _mapping(payload.get("domain_authority_handoff")).get("owner_route"),
    )
    runtime_health = _mapping(payload.get("runtime_health_snapshot"))
    provider_state = _provider_state_projection(runtime_health=runtime_health)
    continuity_refs = _continuity_refs(
        payload=payload,
        owner_route=owner_route,
    )
    category = _breach_category(
        breach_reason=breach_reason,
        payload=payload,
        owner_route=owner_route,
        provider_state=provider_state,
    )
    return {
        "status": "explained" if category != "unclassified_breach" else "needs_classification",
        "category": category,
        "reason": breach_reason,
        "breach_types": list(_list(payload.get("breach_types"))),
        "owner_route": owner_route or None,
        "human_gate": _human_gate_projection(payload),
        "bundle_blocker": _bundle_blocker_projection(payload),
        "quality_repair": _quality_repair_projection(payload),
        "provider_state": provider_state or None,
        "continuity_refs": continuity_refs,
        "low_information_breach_rejected": _low_information_breach_rejected(payload),
        "authority": {
            "kind": "read_model_projection",
            "writes_runtime": False,
            "writes_publication_truth": False,
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
    }


def _breach_category(
    *,
    breach_reason: str,
    payload: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    provider_state: Mapping[str, Any],
) -> str:
    if _human_gate_projection(payload).get("required") is True:
        return "human_gate"
    if _bundle_blocker_projection(payload).get("blocked") is True:
        return "bundle_blocker"
    if _quality_repair_projection(payload).get("required") is True:
        return "quality_repair"
    if provider_state:
        return "opl_provider_state"
    if owner_route:
        return "owner_route"
    if breach_reason in {"human_gate_required"}:
        return "human_gate"
    if breach_reason in {"publication_gate_missing", "gate_closure_drift", "stale_truth_surface"}:
        return "bundle_blocker"
    if breach_reason in {"read_churn_without_artifact_delta", "same_fingerprint_loop", "no_meaningful_progress"}:
        return "quality_repair"
    if breach_reason in {"opl_runtime_handoff_required", "late_success_timeout", "runtime_recovery_retry_budget_exhausted"}:
        return "opl_provider_state"
    return "unclassified_breach"


def _provider_state_projection(*, runtime_health: Mapping[str, Any]) -> dict[str, Any]:
    projection = {
        "canonical_runtime_action": _text(runtime_health.get("canonical_runtime_action")),
        "attempt_state": _text(runtime_health.get("attempt_state")),
        "retry_budget_remaining": runtime_health.get("retry_budget_remaining"),
        "runtime_control_owner": "one-person-lab" if runtime_health else None,
    }
    return {key: value for key, value in projection.items() if value is not None}


def _continuity_refs(
    *,
    payload: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    checkpoint = _first_mapping(
        payload.get("family_checkpoint_lineage"),
        payload.get("checkpoint_lineage"),
    )
    idempotent_dispatch = _first_mapping(
        payload.get("idempotent_dispatch"),
        payload.get("dispatch_receipt"),
        {
            "idempotency_key": _text(owner_route.get("idempotency_key"))
        },
    )
    controller_apply_receipt = _first_mapping(
        payload.get("controller_apply_receipt"),
        payload.get("authorized_action_apply_receipt"),
        _mapping(payload.get("controller_action_receipt")),
    )
    refs = {
        "checkpoint_lineage": checkpoint or None,
        "idempotent_dispatch": idempotent_dispatch or None,
        "controller_apply_receipt": controller_apply_receipt or None,
    }
    return {key: value for key, value in refs.items() if value}


def _human_gate_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    resume_contract = _mapping(_mapping(payload.get("family_checkpoint_lineage")).get("resume_contract"))
    required = resume_contract.get("human_gate_required") is True
    return {
        "required": required,
        "source": "family_checkpoint_lineage.resume_contract" if required else None,
    }


def _bundle_blocker_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    supervisor = _mapping(payload.get("publication_supervisor_state"))
    blocked = supervisor.get("bundle_tasks_downstream_only") is True
    return {
        "blocked": blocked,
        "current_required_action": _text(supervisor.get("current_required_action")),
        "source": "publication_supervisor_state" if supervisor else None,
    }


def _quality_repair_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    repair = _mapping(payload.get("repair_recommendation"))
    top_action = _mapping(repair.get("top_action"))
    breach_types = set(_text(item) for item in _list(payload.get("breach_types")) if _text(item) is not None)
    required = bool(repair) or bool(
        breach_types & {"read_churn_without_artifact_delta", "same_fingerprint_loop", "no_meaningful_progress"}
    )
    return {
        "required": required,
        "repair_state": _text(repair.get("state")),
        "top_action_type": _text(top_action.get("action_type")),
        "repair_kind": _text(top_action.get("repair_kind")),
    }


def _low_information_breach_rejected(payload: Mapping[str, Any]) -> bool:
    existing = _mapping(payload.get("breach_explanation"))
    if existing.get("low_information_breach_rejected") is True:
        return True
    return not (_text(payload.get("breach_reason")) and isinstance(payload.get("breach_explanation"), Mapping))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        candidate = dict(value) if isinstance(value, Mapping) else {}
        if candidate:
            return candidate
    return {}


__all__ = ["with_breach_explanation"]
