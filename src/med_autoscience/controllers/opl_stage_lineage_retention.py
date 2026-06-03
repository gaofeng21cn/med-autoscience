from __future__ import annotations

from typing import Any, Mapping

UNIFIED_EVENT_MODEL = "stage_attempt_manifest_receipt_current_pointer"


def stage_lineage_retention_drilldown(
    *,
    stage_projection: Mapping[str, Any] | None = None,
    refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = _source(stage_projection=stage_projection, refs=refs)
    event_families = _event_families(source)
    retention_restore_gate = _retention_restore_gate(
        source=source,
        event_families=event_families,
    )
    return {
        "surface_kind": "opl_stage_lineage_retention_drilldown",
        "status": "ready" if retention_restore_gate["status"] == "passed" else "blocked",
        "stage_id": _text(source.get("stage_id")),
        "latest_attempt_id": _text(source.get("latest_attempt_id")),
        "source_kind": "stage_projection" if stage_projection is not None else "refs",
        "unified_event_model": UNIFIED_EVENT_MODEL,
        "event_families": event_families,
        "retention_restore_gate": retention_restore_gate,
        "read_only": True,
        "cleanup_authorized": False,
        "body_included": False,
    }


def _source(
    *,
    stage_projection: Mapping[str, Any] | None,
    refs: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source = dict(refs or {})
    if stage_projection is None:
        return source
    source.update(dict(stage_projection))
    lineage = _mapping(stage_projection.get("lineage"))
    promotion = _mapping(stage_projection.get("promotion"))
    current_pointer = _mapping(stage_projection.get("current_pointer"))
    if "lineage_events_ref" not in source:
        source["lineage_events_ref"] = lineage.get("lineage_events_ref")
    if "lineage_graph_ref" not in source:
        source["lineage_graph_ref"] = lineage.get("lineage_graph_ref")
    if "current_pointer_ref" not in source:
        source["current_pointer_ref"] = promotion.get("pointer_ref")
    if "current_pointer_artifact_refs" not in source:
        source["current_pointer_artifact_refs"] = current_pointer.get("artifact_refs")
    if "manifest_artifact_refs" not in source:
        source["manifest_artifact_refs"] = stage_projection.get("current_outputs")
    return source


def _event_families(source: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    owner_receipt_refs = _text_list(source.get("owner_receipt_refs"))
    return {
        "lineage_events": _family(
            refs=_single_ref(source.get("lineage_events_ref")),
            missing_field="lineage_events_ref",
        ),
        "lineage_graph": _family(
            refs=_single_ref(source.get("lineage_graph_ref")),
            missing_field="lineage_graph_ref",
        ),
        "manifest": _family(
            refs=_single_ref(source.get("manifest_ref")),
            missing_field="manifest_ref",
        ),
        "receipt": _family(
            refs=[*_single_ref(source.get("receipt_ref")), *owner_receipt_refs],
            missing=[
                *([] if _single_ref(source.get("receipt_ref")) else ["receipt_ref"]),
                *([] if owner_receipt_refs else ["owner_receipt_refs"]),
            ],
        ),
        "current_pointer": _family(
            refs=_single_ref(source.get("current_pointer_ref")),
            missing_field="current_pointer_ref",
        ),
        "restore_proof": _family(
            refs=_restore_proof_refs(source),
            missing_field="restore_proof_refs",
        ),
        "retention_policy": _family(
            refs=_text_list(source.get("retention_refs")),
            missing_field="retention_refs",
        ),
    }


def _family(
    *,
    refs: list[str],
    missing_field: str | None = None,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    missing_refs = list(missing if missing is not None else ([] if refs else [str(missing_field)]))
    return {
        "status": "observed" if not missing_refs else "missing",
        "refs": refs,
        "missing": missing_refs,
        "body_included": False,
    }


def _retention_restore_gate(
    *,
    source: Mapping[str, Any],
    event_families: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    failed_checks: list[str] = []
    for family in event_families.values():
        failed_checks.extend(_text_list(family.get("missing")))
    if source.get("cleanup_requested") is True:
        failed_checks.append("cleanup_not_authorized_by_projection")
    orphan_refs = _orphan_current_pointer_artifact_refs(source)
    if orphan_refs:
        failed_checks.append("current_pointer_to_orphan_artifact_forbidden")
    return {
        "surface_kind": "opl_stage_retention_restore_gate",
        "status": "passed" if not failed_checks else "blocked",
        "failed_checks": failed_checks,
        "restore_contract_required_before_cleanup": True,
        "cleanup_authorized": False,
        "cleanup_authorized_by_projection": False,
        "current_pointer_to_orphan_artifact_forbidden": True,
        "orphan_current_pointer_artifact_refs": orphan_refs,
        "body_included": False,
    }


def _orphan_current_pointer_artifact_refs(source: Mapping[str, Any]) -> list[str]:
    current_pointer_artifact_refs = _text_list(source.get("current_pointer_artifact_refs"))
    if not current_pointer_artifact_refs:
        return []
    manifest_artifact_refs = _manifest_artifact_refs(source)
    return sorted(ref for ref in current_pointer_artifact_refs if ref not in manifest_artifact_refs)


def _manifest_artifact_refs(source: Mapping[str, Any]) -> set[str]:
    refs = set(_text_list(source.get("manifest_artifact_refs")))
    refs.update(_text_list(source.get("current_outputs")))
    refs.update(_text_list(source.get("present_outputs")))
    for item in _mapping_list(source.get("manifest_hash_refs")):
        text = _text(item.get("path"))
        if text is not None:
            refs.add(text)
    return refs


def _restore_proof_refs(source: Mapping[str, Any]) -> list[str]:
    refs = _text_list(source.get("restore_proof_refs"))
    refs.extend(_text_list(source.get("restore_refs")))
    return list(dict.fromkeys(refs))


def _single_ref(value: object) -> list[str]:
    text = _text(value)
    return [text] if text is not None else []


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = [
    "UNIFIED_EVENT_MODEL",
    "stage_lineage_retention_drilldown",
]
