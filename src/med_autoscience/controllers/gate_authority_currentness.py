from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


DIRECT_DELIVERY_SYNC_STALE_REASONS = frozenset(
    {
        "delivery_projection_missing",
        "delivery_manifest_source_changed",
        "delivery_manifest_source_mismatch",
    }
)
DIRECT_DELIVERY_SYNC_STATUSES = frozenset(
    {
        "stale_projection_missing",
        "stale_source_changed",
        "stale_source_mismatch",
    }
)
DELIVERY_MISSING_SOURCE_REASONS = frozenset({"delivery_manifest_sources_missing"})
DELIVERY_MISSING_SOURCE_STATUSES = frozenset({"stale_source_missing"})
STALE_AUTHORITY_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "stale_study_delivery_mirror",
    }
)
_SYNC_BLOCKING_STATUSES = frozenset(
    {
        "control_plane_route_blocked",
        "failed",
        "missing",
        "skipped_failed_dependency",
        "skipped_authority_not_settled",
    }
)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text_set(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        return frozenset()
    return frozenset(str(item or "").strip() for item in value if str(item or "").strip())


def _text_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item or "").strip() for item in value if str(item or "").strip())


def _blocking_refs_have_missing_source_paths(value: object) -> bool:
    if not isinstance(value, list):
        return False
    missing_source_keys = {
        "missing_source_path",
        "missing_source_paths",
        "source_path",
        "source_paths",
        "delivery_source_path",
        "delivery_source_paths",
    }
    for item in value:
        if not isinstance(item, Mapping):
            continue
        if any(item.get(key) for key in missing_source_keys):
            return True
    return False


def _current_package_freshness_payload(
    gate_report: Mapping[str, Any],
    *,
    current_package_freshness: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return _mapping(current_package_freshness) or _mapping(gate_report.get("current_package_freshness"))


def _status_current_or_fresh(value: object) -> bool:
    return _non_empty_text(value) in {"current", "fresh", "synced", "updated", "unchanged", "ready"}


def _current_package_refs_present(gate_report: Mapping[str, Any], package_freshness: Mapping[str, Any]) -> bool:
    package_ref = _first_non_empty_text(
        package_freshness.get("current_package_root"),
        package_freshness.get("current_package_zip"),
        gate_report.get("current_package_root"),
        gate_report.get("current_package_zip"),
        gate_report.get("study_delivery_current_package_root"),
        gate_report.get("study_delivery_current_package_zip"),
    )
    submission_ref = _first_non_empty_text(
        package_freshness.get("submission_manifest_path"),
        gate_report.get("submission_minimal_manifest_path"),
    )
    return bool(package_ref and submission_ref)


def _current_package_freshness_proof_current(package_freshness: Mapping[str, Any]) -> bool:
    if not _status_current_or_fresh(package_freshness.get("status")):
        return False
    if _first_non_empty_text(package_freshness.get("proof_path")) is None:
        return False
    if _first_non_empty_text(package_freshness.get("current_package_root"), package_freshness.get("current_package_zip")) is None:
        return False
    return _first_non_empty_text(package_freshness.get("submission_manifest_path")) is not None


def _signatures_match(*, evaluated: str | None, authority: str | None) -> bool:
    return bool(evaluated and authority and evaluated == authority)


@dataclass(frozen=True)
class GateAuthorityCurrentness:
    gate_fingerprint: str | None
    evaluated_source_signature: str | None
    authority_source_signature: str | None
    study_delivery_evaluated_source_signature: str | None
    study_delivery_authority_source_signature: str | None
    current_package_source_signature: str | None
    current_package_authority_source_signature: str | None
    submission_authority_current: bool
    stale_submission_authority_current: bool
    submission_authority_sync_required: bool
    delivery_sync_required: bool
    delivery_missing_sources_need_specificity: bool
    delivery_sync_closed: bool
    current_package_fresh: bool

    @property
    def authority_signatures_match(self) -> bool:
        return _signatures_match(
            evaluated=self.evaluated_source_signature,
            authority=self.authority_source_signature,
        )

    @property
    def study_delivery_signatures_match(self) -> bool:
        return _signatures_match(
            evaluated=self.study_delivery_evaluated_source_signature,
            authority=self.study_delivery_authority_source_signature,
        )

    @property
    def current_package_signatures_match(self) -> bool:
        return _signatures_match(
            evaluated=self.current_package_source_signature,
            authority=self.current_package_authority_source_signature,
        )

    @property
    def delivery_current_after_sync(self) -> bool:
        return self.delivery_sync_closed or self.study_delivery_signatures_match


def sync_completed_current_package(unit_results: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    for item in unit_results or []:
        if not isinstance(item, Mapping) or _non_empty_text(item.get("unit_id")) != "sync_submission_minimal_delivery":
            continue
        status = _non_empty_text(item.get("status"))
        if status is None or status in _SYNC_BLOCKING_STATUSES:
            continue
        result = _mapping(item.get("result"))
        source_signature = _first_non_empty_text(
            result.get("source_signature"),
            result.get("evaluated_source_signature"),
        )
        authority_signature = _non_empty_text(result.get("authority_source_signature"))
        if source_signature is not None and authority_signature is not None and source_signature != authority_signature:
            continue
        return {"status": status, "result": dict(result)}
    return None


def resolve_gate_authority_currentness(
    gate_report: Mapping[str, Any],
    *,
    unit_results: list[dict[str, Any]] | None = None,
    current_package_freshness: Mapping[str, Any] | None = None,
) -> GateAuthorityCurrentness:
    blockers = _text_set(gate_report.get("blockers"))
    package_freshness = _current_package_freshness_payload(
        gate_report,
        current_package_freshness=current_package_freshness,
    )
    sync_result = sync_completed_current_package(unit_results)
    sync_payload = _mapping((sync_result or {}).get("result"))
    evaluated_source_signature = _first_non_empty_text(
        gate_report.get("submission_minimal_evaluated_source_signature"),
        gate_report.get("evaluated_source_signature"),
    )
    authority_source_signature = _first_non_empty_text(
        gate_report.get("submission_minimal_authority_source_signature"),
        gate_report.get("authority_source_signature"),
    )
    study_delivery_evaluated_source_signature = _first_non_empty_text(
        sync_payload.get("source_signature"),
        sync_payload.get("evaluated_source_signature"),
        gate_report.get("study_delivery_evaluated_source_signature"),
    )
    study_delivery_authority_source_signature = _first_non_empty_text(
        sync_payload.get("authority_source_signature"),
        gate_report.get("study_delivery_authority_source_signature"),
    )
    current_package_source_signature = _first_non_empty_text(
        package_freshness.get("source_signature"),
        package_freshness.get("evaluated_source_signature"),
        gate_report.get("current_package_source_signature"),
        gate_report.get("study_delivery_evaluated_source_signature"),
    )
    current_package_authority_source_signature = _first_non_empty_text(
        package_freshness.get("authority_source_signature"),
        gate_report.get("current_package_authority_source_signature"),
        gate_report.get("study_delivery_authority_source_signature"),
        authority_source_signature,
    )
    submission_authority_current = (
        _non_empty_text(gate_report.get("submission_minimal_authority_status")) == "current"
        and _signatures_match(
            evaluated=evaluated_source_signature,
            authority=authority_source_signature,
        )
    )
    delivery_stale_reason = _non_empty_text(gate_report.get("study_delivery_stale_reason"))
    delivery_status = _non_empty_text(gate_report.get("study_delivery_status"))
    delivery_missing_source_paths = (
        _text_list(gate_report.get("study_delivery_missing_source_paths"))
        or _text_list(gate_report.get("delivery_manifest_missing_source_paths"))
        or _text_list(gate_report.get("missing_source_paths"))
    )
    delivery_missing_sources = (
        "stale_study_delivery_mirror" in blockers
        and (
            delivery_stale_reason in DELIVERY_MISSING_SOURCE_REASONS
            or delivery_status in DELIVERY_MISSING_SOURCE_STATUSES
        )
    )
    delivery_missing_sources_need_specificity = bool(
        delivery_missing_sources
        and not delivery_missing_source_paths
        and not _blocking_refs_have_missing_source_paths(gate_report.get("blocking_artifact_refs"))
    )
    current_package_fresh = _current_package_freshness_proof_current(package_freshness) and _signatures_match(
        evaluated=current_package_source_signature,
        authority=current_package_authority_source_signature,
    )
    delivery_sync_required = (
        "stale_study_delivery_mirror" in blockers
        and submission_authority_current
        and current_package_fresh
        and not delivery_missing_sources_need_specificity
        and (
            delivery_stale_reason in DIRECT_DELIVERY_SYNC_STALE_REASONS
            or delivery_status in DIRECT_DELIVERY_SYNC_STATUSES
            or delivery_missing_sources
        )
    )
    submission_authority_sync_required = (
        "stale_submission_minimal_authority" in blockers
        and evaluated_source_signature is not None
        and not _signatures_match(
            evaluated=evaluated_source_signature,
            authority=authority_source_signature,
        )
    )
    return GateAuthorityCurrentness(
        gate_fingerprint=_non_empty_text(gate_report.get("gate_fingerprint")),
        evaluated_source_signature=evaluated_source_signature,
        authority_source_signature=authority_source_signature,
        study_delivery_evaluated_source_signature=study_delivery_evaluated_source_signature,
        study_delivery_authority_source_signature=study_delivery_authority_source_signature,
        current_package_source_signature=current_package_source_signature,
        current_package_authority_source_signature=current_package_authority_source_signature,
        submission_authority_current=submission_authority_current,
        stale_submission_authority_current=(
            "stale_submission_minimal_authority" in blockers and submission_authority_current
        ),
        submission_authority_sync_required=submission_authority_sync_required,
        delivery_sync_required=delivery_sync_required,
        delivery_missing_sources_need_specificity=delivery_missing_sources_need_specificity,
        delivery_sync_closed=sync_result is not None,
        current_package_fresh=current_package_fresh,
    )
