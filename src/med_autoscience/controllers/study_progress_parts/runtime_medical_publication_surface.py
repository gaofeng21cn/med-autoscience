from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .shared import _candidate_path, _non_empty_text, _read_json_object, _timestamp_is_newer


_BLOCKER_LABELS = {
    "figure_layout_sidecar_missing_or_incomplete": "图表布局 sidecar 仍不完整。",
    "invalid_blocker_payload": "invalid_blocker_payload",
    "reference_citation_coverage_incomplete": "参考文献引用覆盖仍不完整。",
}


def build_runtime_medical_publication_surface_projection(
    *,
    study_root: Path,
    quest_root: Path | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    source_path = _runtime_surface_path(
        quest_root=quest_root,
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
    )
    runtime_payload = _read_json_object(source_path) if source_path is not None else None
    if runtime_payload is None:
        return None
    if not _is_medical_publication_surface_report(runtime_payload, source_path=source_path):
        return None
    study_shadow_path = study_root / "artifacts" / "medical_publication_surface" / "latest.json"
    study_shadow = _read_json_object(study_shadow_path)
    blockers = _blocker_ids(runtime_payload.get("blockers"))
    projection = {
        "surface_kind": "runtime_medical_publication_surface_projection",
        "authority": "runtime_report_projection_only",
        "source_path": str(source_path),
        "study_shadow_path": str(study_shadow_path) if study_shadow is not None else None,
        "runtime_report_newer_than_study_shadow": _runtime_report_newer_than_study_shadow(
            runtime_payload=runtime_payload,
            study_shadow=study_shadow,
        ),
        "status": _non_empty_text(runtime_payload.get("status")),
        "generated_at": _non_empty_text(runtime_payload.get("generated_at")),
        "recommended_action": _non_empty_text(runtime_payload.get("recommended_action")),
        "blockers": blockers,
        "blocker_summaries": runtime_medical_publication_surface_blocker_summaries(blockers),
        "top_hits": _top_hits(runtime_payload.get("top_hits")),
        "paper_root": _non_empty_text(runtime_payload.get("paper_root")),
        "study_root": _non_empty_text(runtime_payload.get("study_root")),
        "figure_catalog_path": _non_empty_text(runtime_payload.get("figure_catalog_path")),
        "study_shadow": _study_shadow_projection(study_shadow),
    }
    return {key: value for key, value in projection.items() if value is not None}


def runtime_medical_publication_surface_blocker_summaries(blockers: object) -> list[str]:
    return [
        _BLOCKER_LABELS.get(item, item.replace("_", " "))
        for item in _blocker_ids(blockers)
    ]


def _blocker_ids(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    blockers: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            text = (
                _non_empty_text(item.get("id"))
                or _non_empty_text(item.get("blocker"))
                or _non_empty_text(item.get("blocker_id"))
                or _non_empty_text(item.get("key"))
                or _non_empty_text(item.get("reason"))
            )
            if text is None:
                text = "invalid_blocker_payload"
        else:
            text = _non_empty_text(item)
        if text is not None and text not in blockers:
            blockers.append(text)
    return blockers


def _is_medical_publication_surface_report(
    payload: Mapping[str, Any],
    *,
    source_path: Path,
) -> bool:
    if _non_empty_text(payload.get("gate_kind")) == "medical_publication_surface_control":
        return True
    if source_path.name != "latest.json" or source_path.parent.name != "medical_publication_surface":
        return False
    if _non_empty_text(payload.get("status")) not in {"blocked", "clear"}:
        return False
    return "blockers" in payload or "recommended_action" in payload


def _runtime_surface_path(
    *,
    quest_root: Path | None,
    domain_health_diagnostic_payload: dict[str, Any] | None,
) -> Path | None:
    controller_payload = _medical_publication_surface_controller_payload(
        domain_health_diagnostic_payload,
    )
    report_path = _candidate_path(controller_payload.get("report_json"))
    latest_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
        if quest_root is not None
        else None
    )
    if report_path is None:
        return latest_path if latest_path is not None and latest_path.exists() else None
    if latest_path is None or not latest_path.exists():
        return report_path if report_path.exists() else None
    if not report_path.exists() or latest_path.stat().st_mtime >= report_path.stat().st_mtime:
        return latest_path
    return report_path


def _medical_publication_surface_controller_payload(
    domain_health_diagnostic_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    controllers = (
        domain_health_diagnostic_payload.get("controllers")
        if isinstance(domain_health_diagnostic_payload, dict)
        else None
    )
    payload = controllers.get("medical_publication_surface") if isinstance(controllers, Mapping) else None
    return dict(payload) if isinstance(payload, Mapping) else {}


def _runtime_report_newer_than_study_shadow(
    *,
    runtime_payload: dict[str, Any],
    study_shadow: dict[str, Any] | None,
) -> bool:
    runtime_timestamp = _non_empty_text(runtime_payload.get("generated_at"))
    shadow_timestamp = None
    if isinstance(study_shadow, dict):
        shadow_timestamp = (
            _non_empty_text(study_shadow.get("generated_at"))
            or _non_empty_text(study_shadow.get("updated_at"))
            or _non_empty_text(study_shadow.get("emitted_at"))
        )
    return _timestamp_is_newer(runtime_timestamp, shadow_timestamp)


def _study_shadow_projection(study_shadow: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(study_shadow, dict):
        return None
    return {
        "status": _non_empty_text(study_shadow.get("status")),
        "generated_at": _non_empty_text(study_shadow.get("generated_at")),
        "updated_at": _non_empty_text(study_shadow.get("updated_at")),
        "emitted_at": _non_empty_text(study_shadow.get("emitted_at")),
    }


def _top_hits(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    hits: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        hit = {
            key: item[key]
            for key in ("path", "location", "pattern_id", "phrase", "excerpt")
            if key in item
        }
        if hit:
            hits.append(hit)
        if len(hits) >= 6:
            break
    return hits


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [
        text
        for item in value
        if (text := _non_empty_text(item)) is not None
    ]
