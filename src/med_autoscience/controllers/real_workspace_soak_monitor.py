from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import multistudy_soak_proof


SCHEMA_VERSION = 1
SURFACE = "real_workspace_soak_monitor"
READ_MODEL = "real_workspace_soak_monitor_read_model"
MONITOR_ROOT = Path("artifacts/medical_paper")

MATRIX_REF = MONITOR_ROOT / "real_study_soak_matrix_evidence.json"
READINESS_REF = MONITOR_ROOT / "medical_paper_readiness.json"
MONITOR_REF = MONITOR_ROOT / "real_workspace_soak_monitor.json"

SURFACE_KEY_TO_CONTRACT = {
    "literature_scout": "literature_contract",
    "archetype_analysis_contract": "statistical_contract",
    "real_study_soak_matrix_evidence": "external_validation_fixture",
}


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_read_model_only",
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _existing_refs(*refs: Path) -> list[str]:
    return [str(ref.resolve()) for ref in refs if ref.is_file()]


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
        "stages": payload.get("stages") or [],
        "contracts": _contract_flags_from_readiness(payload),
        "result_strength": _text(payload.get("result_strength"), "adequate"),
        "route_action": _text(payload.get("route_action"), "continue"),
        "durable_refs": [str(source_path.resolve())],
        "source_surface": _text(payload.get("surface"), "medical_paper_readiness"),
        "source_path": str(source_path.resolve()),
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


def _overall_status(multistudy_projection: Mapping[str, Any]) -> str:
    status = _text(multistudy_projection.get("overall_status"))
    if status == "ready":
        return "ready"
    return status if status in {"blocked", "partial"} else "blocked"


def _next_action(*, status: str, multistudy_projection: Mapping[str, Any]) -> str:
    if status == "ready":
        return "continue_real_workspace_soak"
    return _text(multistudy_projection.get("next_action"), "review_real_workspace_soak_gaps")


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


def build_real_workspace_soak_monitor(*, study_roots: Sequence[Path | str]) -> dict[str, Any]:
    source_studies = [_read_study_input(Path(root)) for root in study_roots]
    multistudy_projection = multistudy_soak_proof.build_multistudy_soak_matrix_projection(
        source_studies
    )
    source_by_id = {_text(study.get("study_id")): study for study in source_studies}
    projected_by_id = _projection_by_study_id(multistudy_projection)
    study_items: list[dict[str, Any]] = []
    for source in source_studies:
        projected = dict(projected_by_id.get(_text(source.get("study_id")), {}))
        if not projected:
            continue
        durable_refs = list(_sequence(source.get("durable_refs")))
        projected["study_root"] = source.get("study_root")
        projected["source_surface"] = source.get("source_surface")
        projected["source_path"] = source.get("source_path")
        projected["durable_refs"] = durable_refs
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

    status = _overall_status(multistudy_projection)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "overall_status": status,
        "next_action": _next_action(status=status, multistudy_projection=multistudy_projection),
        "required_archetypes": list(multistudy_projection.get("required_archetypes") or []),
        "covered_archetypes": list(multistudy_projection.get("covered_archetypes") or []),
        "missing_archetypes": list(multistudy_projection.get("missing_archetypes") or []),
        "studies": study_items,
        "action_cards": _action_cards(study_items),
        "durable_refs": [
            ref
            for study in study_items
            for ref in _sequence(study.get("durable_refs"))
            if _text(ref, "")
        ],
        "authority_contract": _authority_contract(),
    }


def materialize_real_workspace_soak_monitor(
    *,
    study_roots: Sequence[Path | str],
) -> dict[str, Any]:
    projection = build_real_workspace_soak_monitor(study_roots=study_roots)
    roots = [Path(root).expanduser().resolve() for root in study_roots]
    if not roots:
        raise ValueError("study_roots must include at least one study root")
    path = roots[0] / MONITOR_REF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "artifact_path": str(path.resolve()),
        "overall_status": projection["overall_status"],
        "next_action": projection["next_action"],
        "authority_contract": _authority_contract(),
    }
