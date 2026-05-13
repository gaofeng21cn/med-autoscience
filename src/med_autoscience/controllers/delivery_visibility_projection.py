from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.delivery_visibility import (
    build_delivery_visibility_read_model,
)

SUBMISSION_MINIMAL_LABEL = "controller-authorized source"
CURRENT_PACKAGE_LABEL = "human-facing mirror"
LAYOUT_MIGRATION_UPGRADE_NOTE = "layout migration 会在下一次 authorized sync 升级"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _layout_pending_sync(inspection: Mapping[str, Any]) -> bool:
    if bool(inspection.get("layout_migration_pending_sync")):
        return True
    freshness = _mapping(inspection.get("freshness"))
    if freshness.get("verdict") == "legacy":
        return True
    source_package = _mapping(inspection.get("source_package"))
    human_package = _mapping(inspection.get("human_package"))
    return "legacy" in {
        str(source_package.get("layout_status") or "").strip(),
        str(human_package.get("layout_status") or "").strip(),
    }


def _inspection_status(inspection: Mapping[str, Any]) -> str:
    freshness = _mapping(inspection.get("freshness"))
    verdict = str(freshness.get("verdict") or "").strip()
    delivery_status = str(freshness.get("delivery_status") or "").strip()
    incoming_status = str(inspection.get("status") or "").strip()
    if incoming_status == "legacy_layout_pending_sync":
        incoming_status = ""
    if _layout_pending_sync(inspection) and not (
        verdict == "stale" or delivery_status.startswith("stale") or incoming_status.startswith("stale")
    ):
        return "layout_migration_pending_sync"
    if verdict:
        return verdict
    return delivery_status or incoming_status or "unknown"


def _inspection_summary(inspection: Mapping[str, Any], *, status: str) -> str:
    summary = str(inspection.get("summary") or "").strip()
    if summary:
        return summary
    freshness = _mapping(inspection.get("freshness"))
    delivery_status = str(freshness.get("delivery_status") or "").strip()
    if status == "layout_migration_pending_sync":
        return LAYOUT_MIGRATION_UPGRADE_NOTE
    if delivery_status:
        return f"delivery status: {delivery_status}"
    return "Delivery inspection is available as a read-only projection."


def compact_delivery_inspection_projection(value: object) -> dict[str, Any] | None:
    inspection = _mapping(value)
    if not inspection:
        return None
    status = _inspection_status(inspection)
    compact: dict[str, Any] = {}
    for key in (
        "surface",
        "surface_kind",
        "schema_version",
        "study_id",
        "freshness",
        "mutation_policy",
        "source_package",
        "human_package",
        "zip",
        "journal_package_count",
        "next_sync_command",
        "layout_migration",
    ):
        if key in inspection:
            compact[key] = inspection[key]
    compact.setdefault("surface_kind", "study_delivery_inspection_projection")
    compact["status"] = status
    compact["summary"] = _inspection_summary(inspection, status=status)
    compact["layout_migration_pending_sync"] = _layout_pending_sync(inspection)
    compact["source_labels"] = {
        "submission_minimal": SUBMISSION_MINIMAL_LABEL,
        "current_package": CURRENT_PACKAGE_LABEL,
    }
    compact["layout_migration_upgrade_note"] = LAYOUT_MIGRATION_UPGRADE_NOTE
    delivery_visibility = build_delivery_visibility_read_model(inspection)
    if delivery_visibility is not None:
        compact["delivery_visibility"] = delivery_visibility
    compact["authority"] = "observability_projection_only"
    compact["read_model"] = "delivery_visibility_projection"
    compact["projection_only"] = True
    compact["can_authorize_submission"] = False
    compact["can_authorize_publication_quality"] = False
    compact["can_dispatch_delivery_sync"] = False
    return compact


def build_study_delivery_inspection_projection(
    *,
    profile: Any,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    publication_profile: str | None = None,
) -> dict[str, Any] | None:
    from med_autoscience.controllers.delivery_inspector import (
        compact_delivery_inspection,
        inspect_study_delivery,
    )

    inspection = inspect_study_delivery(
        profile=profile,
        profile_ref=Path(profile_ref).expanduser().resolve() if profile_ref is not None else None,
        study_id=study_id,
        study_root=study_root,
        publication_profile=publication_profile,
    )
    if not isinstance(inspection, Mapping):
        return None
    compact = compact_delivery_inspection(inspection)
    projection = compact_delivery_inspection_projection(compact)
    if projection is None:
        return None
    if study_id is not None:
        projection.setdefault("study_id", study_id)
    elif study_root is not None:
        projection.setdefault("study_id", Path(study_root).name)
    if "layout_migration" not in projection:
        layout_migration = _mapping(inspection.get("layout_migration"))
        if layout_migration:
            projection["layout_migration"] = layout_migration
    return projection


def render_delivery_inspection_markdown_lines(value: object, *, heading: str) -> list[str]:
    projection = compact_delivery_inspection_projection(value)
    if projection is None:
        return []
    lines = [
        "",
        heading,
        "",
        "- submission_minimal = controller-authorized source",
        "- current_package = human-facing mirror",
        f"- layout migration: {LAYOUT_MIGRATION_UPGRADE_NOTE}",
        f"- 当前状态: `{projection.get('status') or 'unknown'}`",
    ]
    summary = str(projection.get("summary") or "").strip()
    if summary:
        lines.append(f"- 当前摘要: {summary}")
    delivery_visibility = _mapping(projection.get("delivery_visibility"))
    traffic_light = _mapping(delivery_visibility.get("traffic_light"))
    if traffic_light:
        lines.append(f"- delivery traffic-light: `{traffic_light.get('status') or 'missing'}`")
    layout_migration_queue = delivery_visibility.get("layout_migration_queue")
    if not isinstance(layout_migration_queue, list):
        layout_migration_queue = delivery_visibility.get("legacy_upgrade_queue")
    if isinstance(layout_migration_queue, list):
        lines.append(f"- layout migration queue: `{len(layout_migration_queue)}` item(s)")
    blocker_report = _mapping(delivery_visibility.get("backfill_blocker_report"))
    if blocker_report:
        lines.append(
            "- backfill blockers: "
            f"`{blocker_report.get('status') or 'missing'}` "
            f"({int(blocker_report.get('blocker_count') or 0)})"
        )
    lines.append(
        "- authority: "
        f"`{projection.get('authority') or 'observability_projection_only'}`；"
        "quality/submission/dispatch authorization: "
        f"`{bool(projection.get('can_authorize_publication_quality'))}/"
        f"{bool(projection.get('can_authorize_submission'))}/"
        f"{bool(projection.get('can_dispatch_delivery_sync'))}`"
    )
    return lines


__all__ = [
    "CURRENT_PACKAGE_LABEL",
    "LAYOUT_MIGRATION_UPGRADE_NOTE",
    "SUBMISSION_MINIMAL_LABEL",
    "build_study_delivery_inspection_projection",
    "compact_delivery_inspection_projection",
    "render_delivery_inspection_markdown_lines",
]
