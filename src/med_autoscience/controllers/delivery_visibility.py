from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

READ_MODEL_NAME = "delivery_visibility_read_model"
WRITE_AUTHORITY = "controller_authorized_delivery_sync_apply_only"
DOCTOR_README_STRUCTURE = [
    {
        "section": "Submission files",
        "purpose": "List human-facing manuscript, PDF, figures, tables, and journal package files.",
        "editable_source": False,
    },
    {
        "section": "Audit and reproducibility",
        "purpose": "Point to manifest, evidence ledger, review ledger, source signatures, and provenance.",
        "editable_source": False,
    },
    {
        "section": "Delivery status",
        "purpose": "Show current/stale/legacy_pending/missing without authorizing publication quality.",
        "editable_source": False,
    },
    {
        "section": "Next controller-authorized sync",
        "purpose": "Name the controller command that may backfill or upgrade the delivery mirror.",
        "editable_source": False,
    },
]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _package_label(package: Mapping[str, Any], fallback: str) -> str:
    return _text(package.get("role")) or fallback


def _package_missing(package: Mapping[str, Any]) -> bool:
    exists = package.get("exists")
    if exists is False:
        return True
    return _text(package.get("layout_status")) == "missing"


def _package_legacy(package: Mapping[str, Any]) -> bool:
    if _text(package.get("layout_status")) == "legacy":
        return True
    legacy_status = _mapping(package.get("legacy_root_file_status"))
    return _text(legacy_status.get("status")) == "present"


def _package_incomplete(package: Mapping[str, Any], key: str) -> bool:
    completeness = _mapping(package.get(key))
    status = _text(completeness.get("status"))
    return bool(status and status in {"partial"})


def _legacy_upgrade_queue(inspection: Mapping[str, Any]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for key, fallback in (
        ("source_package", "controller_authorized_source"),
        ("human_package", "human_facing_mirror"),
    ):
        package = _mapping(inspection.get(key))
        if not package or not _package_legacy(package):
            continue
        queue.append(
            {
                "queue_item": key,
                "role": _package_label(package, fallback),
                "root": package.get("root"),
                "layout_status": package.get("layout_status"),
                "reason": "legacy_root_audit_layout",
                "next_action": "run_controller_authorized_delivery_sync",
            }
        )
    zip_payload = _mapping(inspection.get("zip"))
    root_audit_entries = [str(item) for item in _list(zip_payload.get("root_audit_entries"))]
    if root_audit_entries:
        queue.append(
            {
                "queue_item": "current_package_zip",
                "role": "human_facing_zip_mirror",
                "root": zip_payload.get("path"),
                "layout_status": "legacy",
                "reason": "zip_contains_root_audit_entries",
                "root_audit_entries": root_audit_entries,
                "next_action": "run_controller_authorized_delivery_sync",
            }
        )
    return queue


def _traffic_light_status(
    inspection: Mapping[str, Any],
    *,
    legacy_queue: list[dict[str, Any]],
) -> tuple[str, str]:
    freshness = _mapping(inspection.get("freshness"))
    verdict = _text(freshness.get("verdict"))
    delivery_status = _text(freshness.get("delivery_status"))
    source_package = _mapping(inspection.get("source_package"))
    human_package = _mapping(inspection.get("human_package"))
    incoming_status = _text(inspection.get("status"))
    status_tokens = {verdict, delivery_status, incoming_status}
    if any(token.startswith("stale") for token in status_tokens if token):
        return "stale", delivery_status or verdict or incoming_status
    if legacy_queue and not (_package_missing(source_package) or _package_missing(human_package)):
        return "legacy_pending", "legacy layout is waiting for controller-authorized sync"
    if "missing" in status_tokens or _package_missing(source_package) or _package_missing(human_package):
        return "missing", "delivery package or mirror is missing"
    if verdict == "current" or delivery_status == "current" or incoming_status == "current":
        return "current", "delivery mirror matches controller-authorized source"
    return "missing", "delivery inspection did not expose a current delivery truth"


def _backfill_blockers(
    inspection: Mapping[str, Any],
    *,
    traffic_status: str,
    legacy_queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    source_package = _mapping(inspection.get("source_package"))
    human_package = _mapping(inspection.get("human_package"))
    if traffic_status == "current":
        return []
    for key, package in (("source_package", source_package), ("human_package", human_package)):
        if _package_missing(package):
            blockers.append(
                {
                    "blocker_id": f"{key}_missing",
                    "severity": "blocking",
                    "summary": f"{key} is missing from delivery inspection.",
                }
            )
        for completeness_key in ("audit_completeness", "reproducibility_completeness"):
            if _package_incomplete(package, completeness_key):
                blockers.append(
                    {
                        "blocker_id": f"{key}_{completeness_key}_incomplete",
                        "severity": "backfill_required",
                        "summary": f"{key} has incomplete {completeness_key}.",
                    }
                )
    if traffic_status == "stale":
        freshness = _mapping(inspection.get("freshness"))
        blockers.append(
            {
                "blocker_id": "delivery_stale",
                "severity": "controller_sync_required",
                "summary": _text(freshness.get("stale_reason"))
                or _text(freshness.get("delivery_status"))
                or "delivery mirror is stale",
            }
        )
    for item in legacy_queue:
        blockers.append(
            {
                "blocker_id": f"legacy_upgrade::{item.get('queue_item')}",
                "severity": "controller_sync_required",
                "summary": f"{item.get('role')} still uses legacy delivery layout.",
            }
        )
    return blockers


def build_delivery_visibility_read_model(value: object) -> dict[str, Any] | None:
    inspection = _mapping(value)
    if not inspection:
        return None
    legacy_queue = _legacy_upgrade_queue(inspection)
    traffic_status, traffic_reason = _traffic_light_status(inspection, legacy_queue=legacy_queue)
    blockers = _backfill_blockers(
        inspection,
        traffic_status=traffic_status,
        legacy_queue=legacy_queue,
    )
    next_sync_command = _text(inspection.get("next_sync_command"))
    backfill_status = "clear" if not blockers else "blocked"
    return {
        "surface": "delivery_visibility",
        "surface_kind": READ_MODEL_NAME,
        "schema_version": 1,
        "read_model": READ_MODEL_NAME,
        "projection_only": True,
        "study_id": inspection.get("study_id"),
        "traffic_light": {
            "status": traffic_status,
            "allowed_statuses": ["current", "stale", "legacy_pending", "missing"],
            "reason": traffic_reason,
        },
        "legacy_upgrade_queue": legacy_queue,
        "doctor_readme_structure_projection": DOCTOR_README_STRUCTURE,
        "backfill_blocker_report": {
            "status": backfill_status,
            "blocker_count": len(blockers),
            "blockers": blockers,
            "summary": (
                "No delivery backfill blockers visible in the read model."
                if not blockers
                else f"{len(blockers)} delivery backfill blocker(s) require controller-authorized sync/apply."
            ),
        },
        "authority": {
            "mode": "read_model/projection_only",
            "projection_only": True,
            "can_write_delivery_truth": False,
            "write_authority": WRITE_AUTHORITY,
        },
        "next_controller_authorized_sync": next_sync_command or None,
    }


def inspect_delivery_visibility(
    *,
    profile: Any,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    publication_profile: str | None = None,
) -> dict[str, Any] | None:
    from med_autoscience.controllers.delivery_inspector import inspect_study_delivery

    inspection = inspect_study_delivery(
        profile=profile,
        profile_ref=Path(profile_ref).expanduser().resolve() if profile_ref is not None else None,
        study_id=study_id,
        study_root=study_root,
        publication_profile=publication_profile,
    )
    return build_delivery_visibility_read_model(inspection)


__all__ = [
    "DOCTOR_README_STRUCTURE",
    "READ_MODEL_NAME",
    "WRITE_AUTHORITY",
    "build_delivery_visibility_read_model",
    "inspect_delivery_visibility",
]
