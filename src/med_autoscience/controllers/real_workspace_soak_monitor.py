from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import multistudy_soak_proof


SCHEMA_VERSION = 1
SURFACE = "real_workspace_soak_monitor"
READ_MODEL = "real_workspace_soak_monitor_read_model"
MONITOR_MODE = "continuous_read_only"
MONITOR_ROOT = Path("artifacts/medical_paper")

MATRIX_REF = MONITOR_ROOT / "real_study_soak_matrix_evidence.json"
READINESS_REF = MONITOR_ROOT / "medical_paper_readiness.json"
CANONICAL_READINESS_REF = MONITOR_ROOT / "readiness.json"
MONITOR_REF = MONITOR_ROOT / "real_workspace_soak_monitor.json"

SURFACE_KEY_TO_CONTRACT = {
    "literature_scout": "literature_contract",
    "archetype_analysis_contract": "statistical_contract",
    "real_study_soak_matrix_evidence": "external_validation_fixture",
}
SURFACE_KEY_TO_STAGE = {
    "literature_scout": "literature_scout",
    "literature_provider_runtime": "literature_scout",
    "study_line_selection": "line_selection",
    "route_decision_orchestrator": "route_back",
    "archetype_analysis_contract": "baseline",
    "statistical_discipline_operations": "primary_analysis",
    "bounded_analysis_candidate_board": "bounded_analysis",
    "stop_loss_memo": "stop_loss",
    "revision_rebuttal_loop": "revision_reopen",
    "authoring_runtime_authorization": "final_pre_submission_audit",
    "real_study_soak_matrix_evidence": "runtime_recovery",
    "real_workspace_soak_monitor": "finalize_rebuild",
}


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_read_model_only",
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _read_only_monitor_contract() -> dict[str, Any]:
    return {
        "mode": "read_only_monitor",
        "writes_runtime_owned_surfaces": False,
        "writable_surfaces": [SURFACE],
        "prohibited_runtime_owned_surfaces": [
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "runtime_escalation_record.json",
            "controller_decisions/latest.json",
            "quality_authorization",
            "submission_authorization",
        ],
    }


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _catalog_entries(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("studies", "study_catalog", "items"):
        entries = payload.get(key)
        if isinstance(entries, Mapping):
            return [
                {**entry, "study_id": entry.get("study_id") or str(study_id)}
                for study_id, entry in entries.items()
                if isinstance(entry, Mapping)
            ]
        if isinstance(entries, list | tuple):
            return [entry for entry in entries if isinstance(entry, Mapping)]
    if payload.get("study_id") or payload.get("study_root"):
        return [payload]
    return []


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _optional_bool(value: object) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    return None


def _truthy_bool(value: object) -> bool:
    return value is True


def _existing_refs(*refs: Path) -> list[str]:
    return [str(ref.resolve()) for ref in refs if ref.is_file()]


def _route_mapping(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    route_decision = _mapping(entry.get("route_decision"))
    if route_decision:
        return route_decision
    return _mapping(entry.get("route"))


def _catalog_route_action(entry: Mapping[str, Any]) -> str:
    route = _route_mapping(entry)
    return _text(entry.get("route_action") or route.get("action"), "")


def _catalog_route_reason(entry: Mapping[str, Any]) -> str:
    route = _route_mapping(entry)
    return _text(
        entry.get("route_reason")
        or entry.get("route_decision_reason")
        or route.get("reason")
        or route.get("decision_reason"),
        "",
    )


def _catalog_readiness_status(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    return _text(
        entry.get("readiness_status")
        or entry.get("current_readiness_status")
        or readiness.get("overall_status"),
        "",
    )


def _catalog_previous_readiness_status(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    return _text(
        entry.get("previous_readiness_status")
        or entry.get("last_readiness_status")
        or readiness.get("previous_overall_status"),
        "",
    )


def _catalog_blocked_reason(entry: Mapping[str, Any]) -> str:
    readiness = _mapping(entry.get("readiness"))
    reasons = entry.get("blocked_reasons") or readiness.get("blocked_reasons")
    if isinstance(reasons, list | tuple) and reasons:
        return "; ".join(_text(reason, "") for reason in reasons if _text(reason, ""))
    return _text(
        entry.get("blocked_reason")
        or entry.get("blocked_reason_summary")
        or readiness.get("blocked_reason")
        or readiness.get("missing_reason"),
        "",
    )


def _catalog_bool(entry: Mapping[str, Any], key: str) -> bool | None:
    readiness = _mapping(entry.get("readiness"))
    return _optional_bool(entry.get(key)) if key in entry else _optional_bool(readiness.get(key))


def _catalog_durable_refs(entry: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("durable_refs", "evidence_refs", "proof_refs"):
        refs.extend(str(ref) for ref in _sequence(entry.get(key)) if _text(ref, ""))
    readiness = _mapping(entry.get("readiness"))
    refs.extend(str(ref) for ref in _sequence(readiness.get("durable_refs")) if _text(ref, ""))
    for surface in _sequence(readiness.get("capability_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        refs.extend(str(ref) for ref in _sequence(surface.get("evidence_refs")) if _text(ref, ""))
    return refs


def _catalog_study_root(
    entry: Mapping[str, Any],
    *,
    catalog_payload: Mapping[str, Any],
) -> Path | None:
    root = _text(
        entry.get("study_root")
        or entry.get("root")
        or entry.get("path")
        or entry.get("study_path"),
        "",
    )
    if root:
        return Path(root).expanduser().resolve()
    study_id = _text(entry.get("study_id"), "")
    studies_root = _text(entry.get("studies_root") or catalog_payload.get("studies_root"), "")
    if study_id and studies_root:
        return (Path(studies_root).expanduser() / study_id).resolve()
    return None


def _catalog_source(
    *,
    catalog_payload: Mapping[str, Any],
    catalog_path: Path | None,
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if catalog_path is not None:
        kind = "path"
        path = str(catalog_path.expanduser().resolve())
    elif catalog_payload:
        kind = "payload"
        path = ""
    else:
        kind = "study_roots"
        path = ""
    return {
        "kind": kind,
        "path": path,
        "catalog_id": _text(catalog_payload.get("catalog_id"), ""),
        "study_count": len(entries),
    }


def _scan_metadata(catalog_payload: Mapping[str, Any]) -> dict[str, Any]:
    scan_id = _text(catalog_payload.get("scan_id"), "")
    scan_started_at = _text(
        catalog_payload.get("scan_started_at")
        or catalog_payload.get("scanned_at")
        or catalog_payload.get("generated_at"),
        "",
    )
    return {
        "scan_id": scan_id or "ad_hoc_scan",
        "scan_started_at": scan_started_at,
    }


def _source_key(study: Mapping[str, Any]) -> tuple[str, str]:
    return (_text(study.get("study_id"), ""), _text(study.get("study_root"), ""))


def _dedupe_roots(roots: Sequence[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = root.expanduser().resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(resolved)
    return deduped


def _contract_flags_from_readiness(payload: Mapping[str, Any]) -> dict[str, bool]:
    flags = {
        "literature_contract": False,
        "statistical_contract": False,
        "external_validation_fixture": False,
    }
    for surface in _sequence(payload.get("capability_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        contract = SURFACE_KEY_TO_CONTRACT.get(_text(surface.get("surface_key"), ""))
        if contract:
            flags[contract] = _text(surface.get("status"), "") == "present"
    return flags


def _stages_from_readiness(payload: Mapping[str, Any]) -> list[str]:
    explicit_stages = payload.get("stages")
    if explicit_stages:
        return [str(stage) for stage in _sequence(explicit_stages)]
    stages: list[str] = []
    for surface in _sequence(payload.get("capability_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        if _text(surface.get("status"), "") != "present":
            continue
        stage = SURFACE_KEY_TO_STAGE.get(_text(surface.get("surface_key"), ""))
        if stage and stage not in stages:
            stages.append(stage)
    return stages


def _durable_refs_from_payload(
    *,
    source_path: Path,
    payload: Mapping[str, Any],
    fallback_to_source: bool,
) -> list[str]:
    refs: list[str] = []
    raw_refs = payload.get("durable_refs")
    if isinstance(raw_refs, list):
        refs.extend(str(ref) for ref in raw_refs if _text(ref, ""))
    for surface in _sequence(payload.get("capability_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        refs.extend(str(ref) for ref in _sequence(surface.get("evidence_refs")) if _text(ref, ""))
    if not refs and fallback_to_source:
        refs.append(str(source_path.resolve()))
    return refs


def _study_from_matrix_payload(
    *,
    study_root: Path,
    source_path: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "study_root": str(study_root),
        "study_id": _text(payload.get("study_id"), study_root.name),
        "study_archetype": _text(payload.get("study_archetype")),
        "stages": payload.get("stages") or payload.get("required_stages") or [],
        "contracts": _mapping(payload.get("contracts")),
        "fixtures": _mapping(payload.get("fixtures")),
        "result_strength": _text(payload.get("result_strength"), "adequate"),
        "route_action": _text(payload.get("route_action"), "continue"),
        "durable_refs": _durable_refs_from_payload(
            source_path=source_path,
            payload=payload,
            fallback_to_source=True,
        ),
        "source_surface": _text(payload.get("surface"), "real_study_soak_matrix_evidence"),
        "source_path": str(source_path.resolve()),
    }


def _study_from_readiness_payload(
    *,
    study_root: Path,
    source_path: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "study_root": str(study_root),
        "study_id": _text(payload.get("study_id"), study_root.name),
        "study_archetype": _text(payload.get("study_archetype")),
        "stages": _stages_from_readiness(payload),
        "contracts": _contract_flags_from_readiness(payload),
        "result_strength": _text(payload.get("result_strength"), "adequate"),
        "route_action": _text(payload.get("route_action"), "continue"),
        "durable_refs": [str(source_path.resolve())],
        "readiness_status": _text(payload.get("overall_status"), ""),
        "source_surface": _text(payload.get("surface"), "medical_paper_readiness"),
        "source_path": str(source_path.resolve()),
    }


def _study_from_catalog_entry(
    entry: Mapping[str, Any],
    *,
    catalog_payload: Mapping[str, Any],
) -> dict[str, Any]:
    study_root = _catalog_study_root(entry, catalog_payload=catalog_payload)
    readiness = _mapping(entry.get("readiness"))
    explicit_stages = entry.get("stages") or entry.get("required_stages")
    explicit_contracts = _mapping(entry.get("contracts"))
    root_text = str(study_root) if study_root else _text(entry.get("study_root"), "")
    study_id = _text(entry.get("study_id"), study_root.name if study_root else "unknown")
    return {
        "study_root": root_text,
        "study_id": study_id,
        "study_archetype": _text(entry.get("study_archetype") or readiness.get("study_archetype")),
        "stages": explicit_stages or _stages_from_readiness(readiness),
        "contracts": explicit_contracts or _contract_flags_from_readiness(readiness),
        "fixtures": _mapping(entry.get("fixtures")),
        "result_strength": _text(entry.get("result_strength"), "adequate"),
        "route_action": _text(_catalog_route_action(entry), "continue"),
        "durable_refs": _catalog_durable_refs(entry),
        "readiness_status": _catalog_readiness_status(entry),
        "previous_readiness_status": _catalog_previous_readiness_status(entry),
        "last_green_at": _text(entry.get("last_green_at"), ""),
        "last_green_scan_id": _text(entry.get("last_green_scan_id"), ""),
        "blocked_reason": _catalog_blocked_reason(entry),
        "route_reason": _catalog_route_reason(entry),
        "stop_loss_triggered": _catalog_bool(entry, "stop_loss_triggered"),
        "revision_reopen_seen": _catalog_bool(entry, "revision_reopen_seen"),
        "runtime_recovery_seen": _catalog_bool(entry, "runtime_recovery_seen"),
        "finalize_rebuild_seen": _catalog_bool(entry, "finalize_rebuild_seen"),
        "source_surface": "workspace_catalog",
        "source_path": "",
    }


def _study_from_missing_refs(study_root: Path) -> dict[str, Any]:
    return {
        "study_root": str(study_root),
        "study_id": study_root.name,
        "study_archetype": "unknown",
        "stages": [],
        "contracts": {},
        "result_strength": "unknown",
        "route_action": "continue",
        "durable_refs": [],
        "source_surface": "missing_durable_ref",
        "source_path": "",
    }


def _merge_catalog_metadata(
    source: Mapping[str, Any],
    catalog: Mapping[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(source)
    if not catalog:
        return merged
    catalog_route_action = _text(catalog.get("route_action"), "")
    if catalog_route_action:
        merged["route_action"] = catalog_route_action
    result_strength = _text(catalog.get("result_strength"), "")
    if result_strength:
        merged["result_strength"] = result_strength
    for key in (
        "readiness_status",
        "previous_readiness_status",
        "last_green_at",
        "last_green_scan_id",
        "blocked_reason",
        "route_reason",
        "stop_loss_triggered",
        "revision_reopen_seen",
        "runtime_recovery_seen",
        "finalize_rebuild_seen",
    ):
        value = catalog.get(key)
        if value is not None and value != "":
            merged[key] = value
    catalog_refs = [str(ref) for ref in _sequence(catalog.get("durable_refs")) if _text(ref, "")]
    if catalog_refs:
        refs = list(_sequence(merged.get("durable_refs")))
        refs.extend(ref for ref in catalog_refs if ref not in refs)
        merged["durable_refs"] = refs
    return merged


def _read_study_input(study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    matrix_path = root / MATRIX_REF
    matrix_payload = _read_json(matrix_path)
    if matrix_payload:
        return _study_from_matrix_payload(
            study_root=root,
            source_path=matrix_path,
            payload=matrix_payload,
        )
    readiness_path = root / CANONICAL_READINESS_REF
    readiness_payload = _read_json(readiness_path)
    if not readiness_payload:
        readiness_path = root / READINESS_REF
        readiness_payload = _read_json(readiness_path)
    if readiness_payload:
        return _study_from_readiness_payload(
            study_root=root,
            source_path=readiness_path,
            payload=readiness_payload,
        )
    return _study_from_missing_refs(root)


def _projection_by_study_id(projection: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        _text(study.get("study_id")): study
        for study in _sequence(projection.get("studies"))
        if isinstance(study, Mapping)
    }


def _read_catalog(
    *,
    catalog_payload: Mapping[str, Any] | None,
    catalog_path: Path | str | None,
) -> tuple[Mapping[str, Any], Path | None]:
    if catalog_path is not None:
        path = Path(catalog_path).expanduser().resolve()
        return _read_json(path), path
    if catalog_payload is not None:
        return catalog_payload, None
    return {}, None


def _source_studies(
    *,
    study_roots: Sequence[Path | str],
    catalog_payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[Mapping[str, Any]]]:
    entries = _catalog_entries(catalog_payload)
    catalog_studies = [
        _study_from_catalog_entry(entry, catalog_payload=catalog_payload) for entry in entries
    ]
    catalog_by_key = {
        key: study
        for study in catalog_studies
        for key in (_source_key(study), (_text(study.get("study_id"), ""), ""))
    }
    roots = _dedupe_roots(
        [
            Path(root)
            for root in study_roots
            if _text(root, "")
        ]
        + [
            Path(study["study_root"])
            for study in catalog_studies
            if _text(study.get("study_root"), "")
        ]
    )
    sources = [_read_study_input(root) for root in roots]
    seen = {_source_key(source) for source in sources}
    for catalog_study in catalog_studies:
        if _source_key(catalog_study) in seen:
            continue
        sources.append(dict(catalog_study))
        seen.add(_source_key(catalog_study))
    return [
        _merge_catalog_metadata(
            source,
            catalog_by_key.get(_source_key(source))
            or catalog_by_key.get((_text(source.get("study_id"), ""), "")),
        )
        for source in sources
    ], entries


def _study_monitor_gaps(source: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    if not _sequence(source.get("durable_refs")):
        gaps.append("durable_refs:missing")
    if _optional_bool(source.get("finalize_rebuild_seen")) is False:
        gaps.append("proof:finalize_rebuild")
    return gaps


def _study_monitor_next_action(gaps: Sequence[str]) -> str:
    if "durable_refs:missing" in gaps:
        return "materialize_durable_refs"
    if "proof:finalize_rebuild" in gaps:
        return "materialize_finalize_rebuild_proof"
    return ""


def _has_stage(study: Mapping[str, Any], stage: str) -> bool:
    return stage in set(str(item) for item in _sequence(study.get("present_stages"))) or stage in set(
        str(item) for item in _sequence(study.get("stages"))
    )


def _derived_monitor_bool(study: Mapping[str, Any], key: str) -> bool:
    explicit = _optional_bool(study.get(key))
    if explicit is not None:
        return explicit
    if key == "revision_reopen_seen":
        return _has_stage(study, "revision_reopen")
    if key == "runtime_recovery_seen":
        return _has_stage(study, "runtime_recovery")
    if key == "finalize_rebuild_seen":
        return _has_stage(study, "finalize_rebuild")
    if key == "stop_loss_triggered":
        return _text(study.get("route_action"), "") == "stop_loss"
    return False


def _append_monitor_gaps(
    projected: Mapping[str, Any],
    source: Mapping[str, Any],
) -> dict[str, Any]:
    item = dict(projected)
    monitor_gaps = _study_monitor_gaps(source)
    if not monitor_gaps:
        return item
    missing_gaps = list(_sequence(item.get("missing_gaps")))
    missing_gaps.extend(gap for gap in monitor_gaps if gap not in missing_gaps)
    item["missing_gaps"] = missing_gaps
    if item.get("status") == "ready":
        item["status"] = "partial"
    action = _study_monitor_next_action(monitor_gaps)
    if action:
        item["next_action"] = action
    return item


def _overall_status(
    multistudy_projection: Mapping[str, Any],
    *,
    studies: Sequence[Mapping[str, Any]],
) -> str:
    statuses = {_text(study.get("status")) for study in studies}
    if "blocked" in statuses:
        return "blocked"
    if "partial" in statuses:
        return "partial"
    status = _text(multistudy_projection.get("overall_status"))
    if status == "ready":
        return "ready"
    return status if status in {"blocked", "partial"} else "blocked"


def _next_action(
    *,
    status: str,
    studies: Sequence[Mapping[str, Any]],
    multistudy_projection: Mapping[str, Any],
) -> str:
    if status == "ready":
        return "continue_real_workspace_soak"
    for study in studies:
        if study.get("status") in {"blocked", "partial"}:
            return _text(study.get("next_action"), "review_real_workspace_soak_gaps")
    return _text(multistudy_projection.get("next_action"), "review_real_workspace_soak_gaps")


def _drift_signals(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for study in studies:
        study_signals: list[str] = []
        previous = _text(study.get("previous_readiness_status"), "")
        current = _text(study.get("readiness_status"), "")
        if previous and current and previous != current:
            study_signals.append(f"readiness_status_changed:{previous}->{current}")
        if _text(study.get("source_surface"), "") == "missing_durable_ref":
            study_signals.append("durable_ref_missing")
        if "durable_refs:missing" in set(str(gap) for gap in _sequence(study.get("missing_gaps"))):
            study_signals.append("durable_refs_missing")
        if study_signals:
            signals.append({"study_id": _text(study.get("study_id")), "signals": study_signals})
    return signals


def _blocked_reason_summary(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for study in studies:
        reason = _text(study.get("blocked_reason"), "")
        gaps = [
            str(gap)
            for gap in _sequence(study.get("blocking_gaps")) or _sequence(study.get("missing_gaps"))
            if _text(gap, "")
        ]
        if not reason and not gaps:
            continue
        summary.append(
            {
                "study_id": _text(study.get("study_id")),
                "status": _text(study.get("status")),
                "blocked_reason": reason,
                "gaps": gaps,
            }
        )
    return summary


def _route_decision_summary(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "route_action": _text(study.get("route_action"), "continue"),
            "result_strength": _text(study.get("result_strength"), "adequate"),
            "next_action": _text(study.get("next_action")),
            "reason": _text(study.get("route_reason"), ""),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def _readiness_drift_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    drift: list[dict[str, Any]] = []
    for study in studies:
        previous = _text(study.get("previous_readiness_status"), "")
        current = _text(study.get("readiness_status"), "")
        if not previous or not current or previous == current:
            continue
        drift.append(
            {
                "study_id": _text(study.get("study_id")),
                "previous_status": previous,
                "current_status": current,
                "drift": f"{previous}->{current}",
                "last_green_at": _text(study.get("last_green_at"), ""),
                "last_green_scan_id": _text(study.get("last_green_scan_id"), ""),
            }
        )
    return drift


def _route_decision_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "study_archetype": _text(study.get("study_archetype")),
            "route_action": _text(study.get("route_action"), "continue"),
            "reason": _text(study.get("route_reason"), ""),
            "result_strength": _text(study.get("result_strength"), "adequate"),
            "next_action": "stop_loss"
            if _truthy_bool(study.get("stop_loss_triggered"))
            else _text(study.get("next_action")),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def _stop_loss_trigger_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    for study in studies:
        if not _truthy_bool(study.get("stop_loss_triggered")):
            continue
        triggers.append(
            {
                "study_id": _text(study.get("study_id")),
                "route_action": _text(study.get("route_action"), "continue"),
                "result_strength": _text(study.get("result_strength"), "adequate"),
                "blocked_reason": _text(study.get("blocked_reason"), ""),
            }
        )
    return triggers


def _proof_observation_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "revision_reopen_seen": bool(study.get("revision_reopen_seen")),
            "runtime_recovery_seen": bool(study.get("runtime_recovery_seen")),
            "finalize_rebuild_seen": bool(study.get("finalize_rebuild_seen")),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def _soak_read_model(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "readiness_drift": _readiness_drift_read_model(studies),
        "blocked_reasons": _blocked_reason_summary(studies),
        "route_decisions": _route_decision_read_model(studies),
        "stop_loss_triggers": _stop_loss_trigger_read_model(studies),
        "proof_observations": _proof_observation_read_model(studies),
        "authority": {
            "writes_runtime_owned_surfaces": False,
            "can_authorize_quality": False,
            "can_authorize_submission": False,
            "can_authorize_finalize": False,
        },
    }


def _any_seen(studies: Sequence[Mapping[str, Any]], key: str) -> bool:
    return any(_truthy_bool(study.get(key)) for study in studies)


def _action_cards(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for study in studies:
        if study.get("status") == "ready":
            continue
        cards.append(
            {
                "study_id": _text(study.get("study_id")),
                "status": _text(study.get("status")),
                "next_action": _text(study.get("next_action")),
                "blocking_gaps": list(_sequence(study.get("blocking_gaps"))),
                "durable_refs": list(_sequence(study.get("durable_refs"))),
            }
        )
    return cards


def _drift_history_entry(*, projection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "scan_id": _text(projection.get("scan_id"), "ad_hoc_scan"),
        "scan_started_at": _text(projection.get("scan_started_at"), ""),
        "overall_status": _text(projection.get("overall_status")),
        "next_action": _text(projection.get("next_action")),
        "drift_signals": list(_sequence(projection.get("drift_signals"))),
        "blocked_reason_summary": list(_sequence(projection.get("blocked_reason_summary"))),
        "route_decision_summary": list(_sequence(projection.get("route_decision_summary"))),
        "stop_loss_triggered": bool(projection.get("stop_loss_triggered")),
        "revision_reopen_seen": bool(projection.get("revision_reopen_seen")),
        "runtime_recovery_seen": bool(projection.get("runtime_recovery_seen")),
        "finalize_rebuild_seen": bool(projection.get("finalize_rebuild_seen")),
    }


def _merged_drift_history(
    *,
    previous: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    history = [
        dict(item)
        for item in _sequence(previous.get("drift_history"))
        if isinstance(item, Mapping)
    ]
    entry = _drift_history_entry(projection=projection)
    if not history or history[-1].get("scan_id") != entry["scan_id"]:
        history.append(entry)
    else:
        history[-1] = entry
    return history[-25:]


def _last_green_state(
    *,
    previous: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, str]:
    if projection.get("overall_status") == "ready":
        return {
            "last_green_at": _text(projection.get("scan_started_at"), ""),
            "last_green_scan_id": _text(projection.get("scan_id"), "ad_hoc_scan"),
        }
    return {
        "last_green_at": _text(previous.get("last_green_at"), ""),
        "last_green_scan_id": _text(previous.get("last_green_scan_id"), ""),
    }


def _study_items(
    *,
    source_studies: Sequence[Mapping[str, Any]],
    multistudy_projection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    source_by_id = {_text(study.get("study_id")): study for study in source_studies}
    projected_by_id = _projection_by_study_id(multistudy_projection)
    study_items: list[dict[str, Any]] = []
    for source in source_studies:
        projected = dict(projected_by_id.get(_text(source.get("study_id")), {}))
        if not projected:
            continue
        projected = _append_monitor_gaps(projected, source)
        durable_refs = list(_sequence(source.get("durable_refs")))
        projected["study_root"] = source.get("study_root")
        projected["source_surface"] = source.get("source_surface")
        projected["source_path"] = source.get("source_path")
        projected["durable_refs"] = durable_refs
        for key in (
            "readiness_status",
            "previous_readiness_status",
            "last_green_at",
            "last_green_scan_id",
            "blocked_reason",
            "route_reason",
            "stop_loss_triggered",
            "revision_reopen_seen",
            "runtime_recovery_seen",
            "finalize_rebuild_seen",
        ):
            if source.get(key) is not None and source.get(key) != "":
                projected[key] = source.get(key)
        projected["stop_loss_triggered"] = _derived_monitor_bool(projected, "stop_loss_triggered")
        projected["revision_reopen_seen"] = _derived_monitor_bool(projected, "revision_reopen_seen")
        projected["runtime_recovery_seen"] = _derived_monitor_bool(projected, "runtime_recovery_seen")
        projected["finalize_rebuild_seen"] = _derived_monitor_bool(projected, "finalize_rebuild_seen")
        projected["authority_contract"] = _authority_contract()
        study_items.append(projected)

    for projected in _sequence(multistudy_projection.get("studies")):
        if not isinstance(projected, Mapping):
            continue
        study_id = _text(projected.get("study_id"))
        if study_id in source_by_id:
            continue
        synthetic = dict(projected)
        synthetic["durable_refs"] = []
        synthetic["authority_contract"] = _authority_contract()
        study_items.append(synthetic)
    return study_items


def build_real_workspace_soak_monitor(
    *,
    study_roots: Sequence[Path | str],
    catalog_payload: Mapping[str, Any] | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    catalog, resolved_catalog_path = _read_catalog(
        catalog_payload=catalog_payload,
        catalog_path=catalog_path,
    )
    source_studies, catalog_entries = _source_studies(
        study_roots=study_roots,
        catalog_payload=catalog,
    )
    multistudy_projection = multistudy_soak_proof.build_multistudy_soak_matrix_projection(
        source_studies
    )
    study_items = _study_items(
        source_studies=source_studies,
        multistudy_projection=multistudy_projection,
    )

    status = _overall_status(multistudy_projection, studies=study_items)
    scan = _scan_metadata(catalog)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "monitor_mode": MONITOR_MODE,
        "scheduler": {
            "mode": "continuous_read_only",
            "catalog_driven": bool(catalog),
            "writes_runtime_owned_surfaces": False,
        },
        "scan_id": scan["scan_id"],
        "scan_started_at": scan["scan_started_at"],
        "catalog_source": _catalog_source(
            catalog_payload=catalog,
            catalog_path=resolved_catalog_path,
            entries=catalog_entries,
        ),
        "overall_status": status,
        "next_action": _next_action(
            status=status,
            studies=study_items,
            multistudy_projection=multistudy_projection,
        ),
        "required_archetypes": list(multistudy_projection.get("required_archetypes") or []),
        "covered_archetypes": list(multistudy_projection.get("covered_archetypes") or []),
        "missing_archetypes": list(multistudy_projection.get("missing_archetypes") or []),
        "drift_signals": _drift_signals(study_items),
        "blocked_reason_summary": _blocked_reason_summary(study_items),
        "route_decision_summary": _route_decision_summary(study_items),
        "soak_read_model": _soak_read_model(study_items),
        "stop_loss_triggered": _any_seen(study_items, "stop_loss_triggered"),
        "revision_reopen_seen": _any_seen(study_items, "revision_reopen_seen"),
        "runtime_recovery_seen": _any_seen(study_items, "runtime_recovery_seen"),
        "finalize_rebuild_seen": _any_seen(study_items, "finalize_rebuild_seen"),
        "studies": study_items,
        "action_cards": _action_cards(study_items),
        "durable_refs": [
            ref
            for study in study_items
            for ref in _sequence(study.get("durable_refs"))
            if _text(ref, "")
        ],
        "authority_contract": _authority_contract(),
        "read_only_monitor_contract": _read_only_monitor_contract(),
    }


def materialize_real_workspace_soak_monitor(
    *,
    study_roots: Sequence[Path | str],
    catalog_payload: Mapping[str, Any] | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    projection = build_real_workspace_soak_monitor(
        study_roots=study_roots,
        catalog_payload=catalog_payload,
        catalog_path=catalog_path,
    )
    roots = [Path(root).expanduser().resolve() for root in study_roots]
    if not roots:
        roots = [
            Path(study["study_root"]).expanduser().resolve()
            for study in _sequence(projection.get("studies"))
            if isinstance(study, Mapping) and _text(study.get("study_root"), "")
        ]
    if not roots:
        raise ValueError("study_roots or catalog studies must include at least one study root")
    path = roots[0] / MONITOR_REF
    previous = _read_json(path)
    history = _merged_drift_history(previous=previous, projection=projection)
    green = _last_green_state(previous=previous, projection=projection)
    projection = {
        **projection,
        "drift_history": history,
        "last_green_at": green["last_green_at"],
        "last_green_scan_id": green["last_green_scan_id"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "artifact_path": str(path.resolve()),
        "overall_status": projection["overall_status"],
        "next_action": projection["next_action"],
        "last_green_at": projection["last_green_at"],
        "last_green_scan_id": projection["last_green_scan_id"],
        "authority_contract": _authority_contract(),
        "read_only_monitor_contract": _read_only_monitor_contract(),
    }
