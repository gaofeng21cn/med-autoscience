from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers import literature_provider_runtime
from med_autoscience.controllers import study_line_decision_engine

from .shared import list_items, mapping, mapping_list, read_json, read_yaml, text, text_list


def payload_from_existing_study_line_route_decision(
    *,
    study_root: Path,
    source: str,
    schema_version: int,
) -> dict[str, Any]:
    canonical_path = study_line_decision_engine.stable_study_line_decision_path(study_root=study_root)
    decision = read_json(canonical_path)
    if not _selected_study_line_decision(decision):
        return {}
    candidate = _route_candidate_from_study_line_decision(decision)
    if not candidate:
        return {}
    readiness = {
        "literature_status": "ready" if (study_root / literature_provider_runtime.ARTIFACT_RELATIVE_PATH).exists() else "",
        "literature_missing_reason": "",
    }
    source_refs = [
        str(canonical_path),
        *[text(item) for item in list_items(decision.get("stage_output_refs")) if text(item)],
        *[text(item) for item in list_items(candidate.get("evidence_refs")) if text(item)],
    ]
    return {
        "surface": "route_decision_orchestrator_operator_payload",
        "schema_version": schema_version,
        "requested_action": "select_line",
        "candidates": [candidate],
        "readiness": readiness,
        "payload_source": source,
        "source_basis": "selected_study_line_decision",
        "source_refs": list(dict.fromkeys(ref for ref in source_refs if ref)),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def payload_from_study_metadata_literature_and_stage_refs(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    study = read_yaml(study_root / "study.yaml")
    if not study:
        return {}
    literature_payload = read_json(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root))
    if text(literature_payload.get("status")) != "ready":
        return {}
    stage_refs = stage_output_refs(study_root=study_root)
    if not stage_refs:
        return {}
    study_id = text(study.get("study_id")) or study_root.name
    evidence_refs = [
        str(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)),
        *[text(item) for item in list_items(literature_payload.get("citation_ledger_refs")) if text(item)],
    ]
    candidate = {
        "line_id": study_id,
        "title": text(study.get("title")) or study_id,
        "dimensions": {
            "novelty": 3,
            "clinical_relevance": 4,
            "data_fit": 4,
            "external_validation": 3,
            "analysis_feasibility": 3,
            "journal_fit": 3,
            "risk_cost": 2,
            "stop_threshold": "return_to_human_or_owner_review_if_required_stage_refs_are_missing",
        },
        "evidence_refs": list(dict.fromkeys(ref for ref in evidence_refs if ref)),
        "stage_output_refs": stage_refs,
    }
    payload = study_line_decision_engine.build_study_line_decision(
        study_root=study_root,
        candidates=[candidate],
        route_decision="proceed_to_baseline",
        controller_decision_ref=str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
    )
    if text(payload.get("status")) != "selected":
        return {}
    return {
        **dict(payload),
        "payload_source": source,
        "source_basis": "study_metadata_literature_and_stage_refs",
        "source_refs": [
            str(study_root / "study.yaml"),
            str(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)),
            *stage_refs,
        ],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def stage_output_refs(*, study_root: Path) -> list[str]:
    root = Path(study_root).expanduser().resolve()
    refs: list[str] = []
    for relative_ref in (
        "artifacts/stage_outputs/01-study_intake/receipts/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/projection/current_owner_delta.json",
    ):
        if (root / relative_ref).is_file():
            refs.append(relative_ref)
    if refs:
        return refs
    stage_outputs = root / "artifacts" / "stage_outputs"
    if not stage_outputs.is_dir():
        return []
    for path in sorted(stage_outputs.glob("*/receipts/owner_receipt.json")):
        refs.append(str(path.relative_to(root)))
    return list(dict.fromkeys(refs))


def _route_candidate_from_study_line_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    line_id = text(decision.get("selected_line_id"))
    if not line_id:
        return {}
    current_route = mapping(decision.get("current_route"))
    ranked = _first_selected_ranking(decision, selected_line_id=line_id)
    source = current_route or ranked or decision
    dimensions = mapping(source.get("dimensions")) or mapping(ranked.get("dimensions")) or mapping(
        decision.get("dimensions")
    )
    if not dimensions:
        dimensions = {
            "novelty": 3,
            "clinical_relevance": 4,
            "data_fit": 4,
            "external_validation": 3,
            "analysis_feasibility": 3,
            "journal_fit": 3,
            "risk_cost": 2,
            "stop_threshold": "owner_review_required_before_quality_claim",
        }
    evidence_refs = text_list(source.get("evidence_refs")) or text_list(decision.get("evidence_refs"))
    stage_refs = text_list(source.get("stage_output_refs")) or text_list(decision.get("stage_output_refs"))
    return {
        "line_id": line_id,
        "title": text(source.get("title")) or text(decision.get("title")) or line_id,
        "question": text(source.get("question")) or text(decision.get("question")) or f"Can {line_id} answer the locked research question?",
        "evidence_basis": evidence_refs,
        "expected_artifact": text(source.get("expected_artifact")) or f"artifacts/medical_paper/candidate_paths/{line_id}.json",
        "stop_rule": text(source.get("stop_rule")) or text(dimensions.get("stop_threshold")) or "owner_review_required_before_quality_claim",
        "dimensions": dict(dimensions),
        "evidence_refs": evidence_refs,
        "stage_output_refs": stage_refs,
        "claim_boundary_change": text(source.get("claim_boundary_change")) or "unchanged",
    }


def _first_selected_ranking(decision: Mapping[str, Any], *, selected_line_id: str) -> Mapping[str, Any]:
    for item in mapping_list(decision.get("ranking")):
        if text(item.get("line_id")) == selected_line_id:
            return item
    return {}


def _selected_study_line_decision(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("surface") == study_line_decision_engine.SURFACE
        and text(payload.get("status")) == "selected"
        and bool(text(payload.get("selected_line_id")))
    )


__all__ = [
    "payload_from_existing_study_line_route_decision",
    "payload_from_study_metadata_literature_and_stage_refs",
    "stage_output_refs",
]
