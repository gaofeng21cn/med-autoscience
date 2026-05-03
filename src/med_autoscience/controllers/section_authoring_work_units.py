from __future__ import annotations

import json
from pathlib import Path
from typing import Any


__all__ = ["build_section_authoring_work_units"]


_SURFACE = "section_authoring_work_units"
_SCHEMA_VERSION = 1
_CLAIM_MAP_REF = "paper/claim_evidence_map.json"
_EVIDENCE_LEDGER_REF = "paper/evidence_ledger.md"
_METHODS_REF = "paper/methods_implementation_manifest.json"
_RESULTS_NARRATIVE_REF = "paper/results_narrative_map.json"
_DISPLAY_REF = "paper/figure_semantics_manifest.json"
_NUMERIC_REF = "paper/derived_analysis_manifest.json"
_SECTIONS = ("introduction", "methods", "results", "discussion")
_SECTION_REF_PLAN: dict[str, tuple[str, ...]] = {
    "introduction": (
        _CLAIM_MAP_REF,
        _EVIDENCE_LEDGER_REF,
        _RESULTS_NARRATIVE_REF,
        _DISPLAY_REF,
        _NUMERIC_REF,
    ),
    "methods": (
        _CLAIM_MAP_REF,
        _EVIDENCE_LEDGER_REF,
        _METHODS_REF,
        _DISPLAY_REF,
        _NUMERIC_REF,
    ),
    "results": (
        _CLAIM_MAP_REF,
        _EVIDENCE_LEDGER_REF,
        _RESULTS_NARRATIVE_REF,
        _DISPLAY_REF,
        _NUMERIC_REF,
    ),
    "discussion": (
        _CLAIM_MAP_REF,
        _EVIDENCE_LEDGER_REF,
        _RESULTS_NARRATIVE_REF,
        _DISPLAY_REF,
        _NUMERIC_REF,
    ),
}


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "not_json_object"
    return payload, None


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _ref_blockers(study_root: Path, ref: str) -> list[str]:
    path = study_root / ref
    if not path.exists():
        return [f"missing_ref:{ref}"]
    if path.suffix == ".md":
        if not path.read_text(encoding="utf-8").strip():
            return [f"empty_ref:{ref}"]
        return []

    payload, read_error = _read_json_object(path)
    if read_error is not None:
        return [f"{read_error}_ref:{ref}"]
    if payload is None:
        return [f"invalid_ref:{ref}"]
    if ref == _CLAIM_MAP_REF:
        claims = payload.get("claims")
        if not isinstance(claims, list) or not claims:
            return [f"empty_claim_map:{ref}"]
    if ref == _METHODS_REF and not payload:
        return [f"empty_methods_grounding:{ref}"]
    if ref == _RESULTS_NARRATIVE_REF:
        sections = payload.get("sections")
        if not isinstance(sections, list) or not sections:
            return [f"empty_display_grounding:{ref}"]
    if ref == _DISPLAY_REF:
        figures = payload.get("figures")
        if not isinstance(figures, (list, dict)) or not figures:
            return [f"empty_display_grounding:{ref}"]
    if ref == _NUMERIC_REF:
        numeric_items = payload.get("numeric_results")
        analyses = payload.get("analyses")
        metrics = payload.get("metrics")
        if not any(isinstance(value, list) and value for value in (numeric_items, analyses, metrics)):
            return [f"empty_numeric_grounding:{ref}"]
    return []


def _grounding_for_refs(required_refs: tuple[str, ...]) -> dict[str, Any]:
    display_refs = [ref for ref in required_refs if ref in {_RESULTS_NARRATIVE_REF, _DISPLAY_REF}]
    numeric_refs = [ref for ref in required_refs if ref == _NUMERIC_REF]
    return {
        "claim_map_ref": _CLAIM_MAP_REF,
        "evidence_refs": [_EVIDENCE_LEDGER_REF],
        "display_refs": display_refs,
        "numeric_refs": numeric_refs,
    }


def _build_unit(*, study_root: Path, section: str) -> dict[str, Any]:
    required_refs = _SECTION_REF_PLAN[section]
    blockers: list[str] = []
    for ref in required_refs:
        blockers.extend(_ref_blockers(study_root, ref))
    blockers = _dedupe(blockers)
    return {
        "unit_id": f"section_authoring::{section}",
        "section": section,
        "required_refs": list(required_refs),
        "grounding": _grounding_for_refs(required_refs),
        "blockers": blockers,
        "route_back_hint": "clear" if not blockers else "restore_required_authority_refs",
        "can_mutate_package": False,
    }


def build_section_authoring_work_units(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    units = [_build_unit(study_root=resolved_study_root, section=section) for section in _SECTIONS]
    blockers = _dedupe(
        [
            str(blocker)
            for unit in units
            for blocker in unit.get("blockers", [])
            if str(blocker)
        ]
    )
    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "status": "blocked" if blockers else "ready",
        "required_before": "first_full_draft",
        "sections": list(_SECTIONS),
        "units": units,
        "blockers": blockers,
        "can_mutate_package": False,
        "authority": {
            "read_only": True,
            "can_generate_manuscript": False,
            "can_mutate_package": False,
            "can_authorize_draft_readiness": False,
        },
    }
