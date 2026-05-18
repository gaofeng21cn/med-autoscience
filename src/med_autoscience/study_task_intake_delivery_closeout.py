from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.study_delivery_package_contract import (
    current_delivery_manifest_payload,
    delivery_manifest_allows_directory_current_package,
)


_BUNDLE_STAGE_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})


def task_intake_yields_to_current_delivery_package_closeout(
    payload: dict[str, Any] | None,
    *,
    study_root: Path | None,
    publishability_gate_report: dict[str, Any] | None,
) -> bool:
    delivery_manifest = _delivery_manifest_current_payload(study_root=study_root)
    if delivery_manifest is None:
        return False
    if not _gate_report_clear_for_quality_closeout(publishability_gate_report):
        return False
    return _closeout_surface_is_fresher_than_task_intake(
        payload,
        delivery_manifest,
        publishability_gate_report,
    )


def _delivery_manifest_current_payload(*, study_root: Path | None) -> dict[str, Any] | None:
    if study_root is None:
        return None
    root = Path(study_root).expanduser().resolve()
    payload = current_delivery_manifest_payload(study_root=root)
    if payload is None:
        return None
    surface_roles = _mapping(payload.get("surface_roles"))
    package_root_text = _text(surface_roles.get("human_facing_current_package_root"))
    package_zip_text = _text(surface_roles.get("human_facing_current_package_zip"))
    package_root = Path(package_root_text).expanduser() if package_root_text is not None else root / "manuscript" / "current_package"
    package_zip = Path(package_zip_text).expanduser() if package_zip_text is not None else root / "manuscript" / "current_package.zip"
    if not package_root.exists():
        return None
    if (
        not package_zip.exists()
        and not delivery_manifest_allows_directory_current_package(
            study_root=root,
            package_root=package_root,
            package_zip=package_zip,
        )
    ):
        return None
    required_files = (
        "manuscript.docx",
        "paper.pdf",
        "references.bib",
        "SUBMISSION_TODO.md",
    )
    if not all((package_root / relative_path).exists() for relative_path in required_files):
        return None
    if not (package_root / "audit" / "submission_manifest.json").exists():
        return None
    return payload


def _gate_report_clear_for_quality_closeout(gate_report: dict[str, Any] | None) -> bool:
    if not isinstance(gate_report, dict):
        return False
    if _text(gate_report.get("status")) != "clear":
        return False
    blockers = {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
    if blockers:
        return False
    if gate_report.get("allow_write") is False:
        return False
    current_required_action = _text(gate_report.get("current_required_action"))
    return current_required_action in {None, *_BUNDLE_STAGE_ACTIONS}


def _closeout_surface_is_fresher_than_task_intake(
    payload: dict[str, Any] | None,
    *surfaces: dict[str, Any] | None,
) -> bool:
    task_intake_emitted_at = _surface_emitted_at(payload)
    if task_intake_emitted_at is None:
        return False
    latest_surface_emitted_at = max(
        (
            surface_emitted_at
            for surface_emitted_at in (_surface_emitted_at(surface) for surface in surfaces)
            if surface_emitted_at is not None
        ),
        default=None,
    )
    return latest_surface_emitted_at is not None and latest_surface_emitted_at >= task_intake_emitted_at


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(payload.get("emitted_at") or payload.get("generated_at") or payload.get("created_at"))


def _normalize_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["task_intake_yields_to_current_delivery_package_closeout"]
