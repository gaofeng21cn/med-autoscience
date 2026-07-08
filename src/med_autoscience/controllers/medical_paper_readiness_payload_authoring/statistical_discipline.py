from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import statistical_discipline_runtime

from .shared import read_json, text


def payload_from_statistical_discipline_sources(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    contract_path = study_root / "paper" / "medical_analysis_contract.json"
    board_path = study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json"
    contract = read_json(contract_path)
    if text(contract.get("status")) != "resolved":
        return {}
    board = read_json(board_path)
    if text(board.get("surface")) != "bounded_analysis_candidate_board":
        return {}
    discipline_contract = _statistical_discipline_contract_from_analysis_contract(contract)
    if not discipline_contract:
        return {}
    return {
        **dict(discipline_contract),
        "contract": dict(discipline_contract),
        "medical_analysis_contract": dict(contract),
        "bounded_board": dict(board),
        "payload_source": source,
        "source_basis": "resolved_analysis_contract_and_bounded_candidate_board",
        "source_refs": [str(contract_path), str(board_path)],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _statistical_discipline_contract_from_analysis_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    archetype = _statistical_discipline_archetype(contract)
    if not archetype:
        return {}
    discipline_contract = statistical_discipline_runtime.build_statistical_discipline_contract(
        study_archetype=archetype,
    )
    if text(discipline_contract.get("status")) != "resolved":
        return {}
    return {
        **dict(discipline_contract),
        "source_medical_analysis_contract": dict(contract),
        "source_basis": "medical_analysis_contract_statistical_discipline_mapping",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _statistical_discipline_archetype(contract: Mapping[str, Any]) -> str | None:
    manuscript_family = text(contract.get("manuscript_family"))
    study_archetype = text(contract.get("study_archetype"))
    if manuscript_family == "prediction_model":
        return "prediction_model"
    aliases = {
        "clinical_classifier": "prediction_model",
        "external_validation_model_update": "external_validation",
        "clinical_subtype_reconstruction": "subtype_reconstruction",
        "survey_trend_analysis": "observational_real_world",
        "llm_agent_clinical_task": "ai_clinical_task",
    }
    return aliases.get(study_archetype)


__all__ = ["payload_from_statistical_discipline_sources"]
