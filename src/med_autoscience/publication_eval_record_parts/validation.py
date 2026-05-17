from __future__ import annotations

from typing import Any


_RECORD_ALLOWED_FIELDS = frozenset(
    {
        "schema_version",
        "eval_id",
        "study_id",
        "quest_id",
        "emitted_at",
        "evaluation_scope",
        "charter_context_ref",
        "runtime_context_refs",
        "delivery_context_refs",
        "assessment_provenance",
        "authority_boundary",
        "verdict",
        "quality_assessment",
        "reviewer_operating_system",
        "future_facing_limitations_plan",
        "gaps",
        "recommended_actions",
    }
)
_CHARTER_CONTEXT_REF_ALLOWED_FIELDS = frozenset({"ref", "charter_id", "publication_objective"})
_VERDICT_ALLOWED_FIELDS = frozenset({"overall_verdict", "primary_claim_status", "summary", "stop_loss_pressure"})
_QUALITY_DIMENSION_ALLOWED_FIELDS = frozenset(
    {
        "status",
        "summary",
        "evidence_refs",
        "reviewer_reason",
        "reviewer_revision_advice",
        "reviewer_next_round_focus",
    }
)
_QUALITY_ASSESSMENT_ALLOWED_FIELDS = frozenset(
    {
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    }
)
_GAP_ALLOWED_FIELDS = frozenset({"gap_id", "gap_type", "severity", "summary", "evidence_refs"})
_RECOMMENDED_ACTION_ALLOWED_FIELDS = frozenset(
    {
        "action_id",
        "action_type",
        "priority",
        "reason",
        "route_target",
        "route_key_question",
        "route_rationale",
        "evidence_refs",
        "requires_controller_decision",
        "work_unit_fingerprint",
        "blocking_work_units",
        "next_work_unit",
        "specificity_targets",
    }
)
_ALLOWED_OVERALL_VERDICTS = frozenset({"promising", "mixed", "weak", "blocked"})
_ALLOWED_PRIMARY_CLAIM_STATUSES = frozenset({"supported", "partial", "unsupported", "blocked"})
_ALLOWED_STOP_LOSS_PRESSURES = frozenset({"none", "watch", "high"})
_ALLOWED_QUALITY_DIMENSION_STATUSES = frozenset({"ready", "partial", "blocked", "underdefined"})
_ALLOWED_GAP_TYPES = frozenset({"claim", "evidence", "reporting", "delivery"})
_ALLOWED_GAP_SEVERITIES = frozenset({"must_fix", "important", "optional"})
_ALLOWED_ACTION_TYPES = frozenset(
    {
        "continue_same_line",
        "route_back_same_line",
        "bounded_analysis",
        "stop_loss",
        "return_to_controller",
        "prepare_promotion_review",
    }
)
_ALLOWED_ACTION_PRIORITIES = frozenset({"now", "next"})
_ROUTE_CONTRACT_ACTION_TYPES = frozenset(
    {"continue_same_line", "route_back_same_line", "bounded_analysis", "stop_loss"}
)
_ALLOWED_ROUTE_TARGETS = frozenset(
    {
        "intake-audit",
        "scout",
        "baseline",
        "idea",
        "decision",
        "experiment",
        "analysis-campaign",
        "write",
        "review",
        "finalize",
        "controller",
        "stop",
    }
)
_REQUIRED_RUNTIME_CONTEXT_REF_KEYS = frozenset({"runtime_escalation_ref", "main_result_ref"})
_REQUIRED_DELIVERY_CONTEXT_REF_KEYS = frozenset({"paper_root_ref", "submission_minimal_ref"})
_AUTHORITY_BOUNDARY_ALLOWED_FIELDS = frozenset(
    {
        "mutated_current_package",
        "mutated_submission_minimal",
        "mutated_publication_gate_conclusion",
        "mutated_medical_result_values",
        "quality_gate_relaxation",
        "publication_gate_allow_write_respected",
    }
)


def _reject_unknown_fields(label: str, payload: dict[str, Any], allowed_fields: frozenset[str]) -> None:
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ValueError(f"{label} payload contains unknown fields: {', '.join(unknown_fields)}")


def _require_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _require_ref_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be a ref string")
    return value.strip()


def _require_choice(label: str, field_name: str, value: Any, allowed_values: frozenset[str]) -> str:
    normalized = _require_text(label, field_name, value)
    if normalized not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{label} {field_name} must be one of: {allowed}")
    return normalized


def _optional_text(label: str, field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _require_text(label, field_name, value)


def _payload_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return raw_value


def _payload_text(payload: dict[str, Any], field_name: str, label: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_text(label, field_name, payload.get(field_name))


def _payload_int(payload: dict[str, Any], field_name: str, label: str) -> int:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    value = payload.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be int")
    return value


def _payload_object(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any]:
    return _payload_mapping(payload, field_name, label)


def _require_ref_mapping(
    field_name: str,
    value: Any,
    *,
    required_keys: frozenset[str] | None = None,
) -> dict[str, str]:
    label = "publication eval record"
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _require_text(label, f"{field_name} key", key)
        if not normalized_key.endswith("_ref"):
            raise ValueError(f"{label} {field_name} keys must end with _ref")
        normalized[normalized_key] = _require_ref_text(label, f"{field_name} value", item)
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    if required_keys is not None:
        missing_keys = sorted(required_keys - normalized.keys())
        if missing_keys:
            raise ValueError(f"{label} {field_name} must include {missing_keys[0]}")
        unexpected_keys = sorted(normalized.keys() - required_keys)
        if unexpected_keys:
            raise ValueError(f"{label} {field_name} contains unexpected ref key {unexpected_keys[0]}")
    return normalized


def _payload_ref_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, str]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_ref_mapping(field_name, payload.get(field_name))


def _require_text_sequence(label: str, field_name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized = tuple(
        _require_text(label, field_name[:-1] if field_name.endswith("s") else field_name, item)
        for item in value
    )
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    return normalized


def _optional_publication_work_unit(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("publication eval recommended action work unit must be a mapping")
    normalized: dict[str, str] = {}
    for field_name in ("unit_id", "lane", "summary"):
        normalized[field_name] = _require_text(
            "publication eval recommended action work unit",
            field_name,
            value.get(field_name),
        )
    return normalized


def _optional_publication_work_units(value: Any) -> tuple[dict[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("publication eval recommended action blocking_work_units must be a list")
    return tuple(
        work_unit
        for item in value
        if (work_unit := _optional_publication_work_unit(item)) is not None
    )


def _payload_object_sequence(payload: dict[str, Any], field_name: str, label: str) -> list[dict[str, Any]]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    if not raw_value:
        raise ValueError(f"{label} {field_name} must not be empty")
    for item in raw_value:
        if not isinstance(item, dict):
            raise ValueError(f"{label} {field_name} entries must be mappings")
    return raw_value


def _optional_authority_boundary(value: Any) -> dict[str, bool] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("publication eval record authority_boundary must be a mapping")
    _reject_unknown_fields("publication eval record authority_boundary", value, _AUTHORITY_BOUNDARY_ALLOWED_FIELDS)
    normalized: dict[str, bool] = {}
    for field_name, item in value.items():
        if not isinstance(item, bool):
            raise TypeError(f"publication eval record authority_boundary {field_name} must be bool")
        normalized[field_name] = item
    return normalized


def _payload_true(payload: dict[str, Any], field_name: str, label: str) -> bool:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    if payload.get(field_name) is not True:
        raise ValueError(f"{label} {field_name} must be true")
    return True


def _dedupe_ref_texts(*values: object) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, dict):
            items = value.values()
        elif isinstance(value, (list, tuple)):
            items = value
        else:
            items = (value,)
        for item in items:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            refs.append(text)
    return tuple(refs)
