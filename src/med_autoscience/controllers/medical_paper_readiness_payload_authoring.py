from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers import medical_analysis_contract
from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers import literature_provider_runtime
from med_autoscience.controllers import real_paper_ai_first_soak
from med_autoscience.controllers import route_control_stoploss
from med_autoscience.controllers import statistical_discipline_runtime
from med_autoscience.controllers import study_line_decision_engine
from med_autoscience.controllers.medical_paper_readiness_payload_authoring_parts import (
    authoring_runtime_authorization as authoring_runtime_authorization_authoring,
    literature_provider_runtime as literature_provider_runtime_authoring,
    provider_adapters as provider_adapter_authoring,
    route_decision as route_decision_authoring,
    revision_rebuttal_loop as revision_rebuttal_loop_authoring,
    soak_matrix as soak_matrix_authoring,
    statistical_discipline as statistical_discipline_authoring,
    writing_context as writing_context_authoring,
)
from med_autoscience.policies import publication_critique
from med_autoscience.profiles import WorkspaceProfile


SOURCE = "medical_paper_readiness_owner_payload_authoring"
SURFACE = "medical_paper_readiness_operator_payload_authoring"
SCHEMA_VERSION = 1
SUPPORTED_SURFACE_KEYS = {
    "literature_scout",
    "literature_provider_runtime",
    "study_line_selection",
    "archetype_analysis_contract",
    "bounded_analysis_candidate_board",
    "stop_loss_memo",
    "target_journal_writing_layer",
    "real_study_soak_matrix_evidence",
    "route_decision_orchestrator",
    "statistical_discipline_operations",
    "revision_rebuttal_loop",
    "authoring_runtime_authorization",
}


def author_operator_payload(
    *,
    study_root: Path,
    surface_key: str | None,
    profile: WorkspaceProfile | None = None,
    generated_at: str | None = None,
    write_provider_response_ledger: bool = False,
) -> dict[str, Any]:
    if _text(surface_key) not in SUPPORTED_SURFACE_KEYS:
        return _blocked_payload("unsupported_surface_key", surface_key=surface_key)
    root = Path(study_root).expanduser().resolve()
    timestamp = _text(generated_at) or _utc_now()
    if _text(surface_key) == "literature_scout":
        payload = _payload_from_existing_literature_scout(study_root=root)
        if payload:
            return payload
        payload = literature_provider_runtime_authoring.payload_from_ready_literature_provider_runtime(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_literature_scout_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "study_line_selection":
        payload = _payload_from_existing_study_line_decision(study_root=root)
        if payload:
            return payload
        payload = route_decision_authoring.payload_from_study_metadata_literature_and_stage_refs(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_study_line_selection_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "archetype_analysis_contract":
        payload = _payload_from_medical_analysis_contract(study_root=root, profile=profile)
        if payload:
            return payload
        return _blocked_payload("insufficient_archetype_analysis_contract_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "bounded_analysis_candidate_board":
        payload = _payload_from_analysis_contract_candidate_board(study_root=root)
        if payload:
            return payload
        return _blocked_payload("insufficient_bounded_analysis_candidate_board_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "stop_loss_memo":
        payload = _payload_from_route_control_stop_loss(study_root=root)
        if payload:
            return payload
        return _blocked_payload("insufficient_stop_loss_memo_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "target_journal_writing_layer":
        payload = _payload_from_existing_target_journal_writing_layer(study_root=root)
        if payload:
            return payload
        payload = writing_context_authoring.payload_from_writing_context_sources(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_target_journal_writing_layer_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "real_study_soak_matrix_evidence":
        return soak_matrix_authoring.payload_from_real_study_soak_matrix_evidence(
            study_root=root,
            source=SOURCE,
            blocked_payload=_blocked_payload(
                "insufficient_real_study_soak_matrix_evidence_sources",
                surface_key="real_study_soak_matrix_evidence",
            ),
        )
    if _text(surface_key) == "route_decision_orchestrator":
        payload = route_decision_authoring.payload_from_existing_study_line_route_decision(
            study_root=root,
            source=SOURCE,
            schema_version=SCHEMA_VERSION,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_route_decision_orchestrator_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "statistical_discipline_operations":
        payload = statistical_discipline_authoring.payload_from_statistical_discipline_sources(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_statistical_discipline_operations_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "revision_rebuttal_loop":
        payload = revision_rebuttal_loop_authoring.payload_from_revision_rebuttal_loop_sources(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_revision_rebuttal_loop_payload_sources", surface_key=surface_key)
    if _text(surface_key) == "authoring_runtime_authorization":
        payload = authoring_runtime_authorization_authoring.payload_from_authoring_runtime_authorization_sources(
            study_root=root,
            source=SOURCE,
        )
        if payload:
            return payload
        return _blocked_payload("insufficient_authoring_runtime_authorization_payload_sources", surface_key=surface_key)
    existing = provider_adapter_authoring.payload_from_existing_literature_intelligence(
        study_root=root,
        generated_at=timestamp,
        source=SOURCE,
        surface=SURFACE,
        schema_version=SCHEMA_VERSION,
    )
    if existing:
        return existing
    provider_backed = provider_adapter_authoring.payload_from_provider_adapters(
        study_root=root,
        generated_at=timestamp,
        surface_key=surface_key,
        write_provider_response_ledger=write_provider_response_ledger,
        source=SOURCE,
        surface=SURFACE,
        schema_version=SCHEMA_VERSION,
    )
    if provider_backed:
        return provider_backed
    return _blocked_payload("insufficient_literature_provider_payload_sources", surface_key=surface_key)


def _payload_from_existing_literature_scout(*, study_root: Path) -> dict[str, Any]:
    path = literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)
    payload = literature_intelligence_os.read_literature_intelligence_os(study_root=study_root)
    if _text(payload.get("status")) != "ready":
        return {}
    return {
        **dict(payload),
        "payload_source": SOURCE,
        "source_basis": "existing_literature_intelligence_os",
        "source_refs": [str(path)],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _payload_from_ready_literature_provider_runtime(*, study_root: Path) -> dict[str, Any]:
    path = (Path(study_root).expanduser().resolve() / literature_provider_runtime.ARTIFACT_RELATIVE_PATH).resolve()
    provider_runtime = _read_json(path)
    if _text(provider_runtime.get("surface")) != literature_provider_runtime.SURFACE:
        return {}
    if _text(provider_runtime.get("status")) != "ready":
        return {}
    nested = _mapping(provider_runtime.get("literature_intelligence_payload"))
    if not nested:
        return {}
    source_refs = [
        str(path),
        *[_text(item) for item in _list(provider_runtime.get("source_refs")) if _text(item)],
        *[_text(item) for item in _list(nested.get("source_refs")) if _text(item)],
    ]
    payload = {
        **nested,
        "surface": literature_intelligence_os.SURFACE,
        "schema_version": literature_intelligence_os.SCHEMA_VERSION,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "study_id": _text(nested.get("study_id")) or _text(provider_runtime.get("study_id")) or _study_id_from_root(study_root),
        "status": "ready",
        "missing_reason": "",
        "payload_source": SOURCE,
        "source_basis": "ready_literature_provider_runtime",
        "source_refs": list(dict.fromkeys(ref for ref in source_refs if ref)),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    if literature_intelligence_os._missing_reason(payload):
        return {}
    return payload


def _payload_from_existing_target_journal_writing_layer(*, study_root: Path) -> dict[str, Any]:
    path = publication_critique.stable_target_journal_writing_layer_path(study_root=study_root)
    if not path.exists():
        return {}
    try:
        payload = publication_critique.read_target_journal_writing_layer(study_root=study_root)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return {
        **dict(payload),
        "payload_source": SOURCE,
        "source_basis": "existing_target_journal_writing_layer",
        "source_refs": [str(path)],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _payload_from_writing_context_sources(*, study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    source_paths = {
        "style_corpus": root / "paper" / "medical_journal_style_corpus.json",
        "claim_evidence_map": root / "paper" / "claim_evidence_map.json",
        "display_registry": root / "paper" / "display_registry.json",
        "figure_semantics_manifest": root / "paper" / "figure_semantics_manifest.json",
        "table_catalog": root / "paper" / "tables" / "table_catalog.json",
        "results_narrative_map": root / "paper" / "results_narrative_map.json",
        "medical_manuscript_blueprint": root / "paper" / "medical_manuscript_blueprint.json",
        "medical_prose_review": root / "artifacts" / "publication_eval" / "medical_prose_review.json",
    }
    if any(not path.exists() for path in source_paths.values()):
        return {}
    style_corpus = _read_json(source_paths["style_corpus"])
    claim_map = _read_json(source_paths["claim_evidence_map"])
    display_registry = _read_json(source_paths["display_registry"])
    table_catalog = _read_json(source_paths["table_catalog"])
    prose_review = _read_json(source_paths["medical_prose_review"])
    near_neighbors = _near_neighbor_style_corpus(style_corpus)
    claim_to_paragraph = _claim_to_paragraph_map(claim_map)
    display_to_claim = _display_to_claim_map(
        claim_map,
        display_registry=display_registry,
        table_catalog=table_catalog,
    )
    if not near_neighbors or not claim_to_paragraph or not display_to_claim:
        return {}
    payload = {
        "surface": "target_journal_writing_layer",
        "schema_version": publication_critique.SCHEMA_VERSION if hasattr(publication_critique, "SCHEMA_VERSION") else 1,
        "role": "ai_reviewer_quality_context",
        "target_journal_family": "general_internal_medicine",
        "near_neighbor_style_corpus": near_neighbors,
        "section_plan": _section_plan(),
        "claim_to_paragraph_map": claim_to_paragraph,
        "display_to_claim_map": display_to_claim,
        "restrained_language_strategy": _restrained_language_strategy(
            claim_map=claim_map,
            prose_review=prose_review,
        ),
        "payload_source": SOURCE,
        "source_basis": "structured_writing_context_sources",
        "source_refs": [str(path) for path in source_paths.values()],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    try:
        normalized = publication_critique._normalize_target_journal_writing_layer(dict(payload))
    except ValueError:
        return {}
    return {
        **normalized,
        "payload_source": SOURCE,
        "source_basis": "structured_writing_context_sources",
        "source_refs": [str(path) for path in source_paths.values()],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _near_neighbor_style_corpus(style_corpus: Mapping[str, Any]) -> list[dict[str, str]]:
    source_refs = _mapping_list(style_corpus.get("source_refs"))
    if not source_refs:
        return []
    jama_refs = [
        item
        for item in source_refs
        if "jama" in " ".join(_text(item.get(key)) for key in ("source_id", "label", "journal")).lower()
    ]
    selected = jama_refs or source_refs[:3]
    neighbors: list[dict[str, str]] = []
    for item in selected[:4]:
        style_ref = _text(item.get("source_id")) or _text(item.get("url")) or _text(item.get("label"))
        journal = _journal_label(item)
        if not style_ref or not journal:
            continue
        neighbors.append(
            {
                "journal": journal,
                "article_role": _text(item.get("article_role")) or "near_neighbor_style_reference",
                "style_ref": style_ref,
            }
        )
    return neighbors


def _journal_label(item: Mapping[str, Any]) -> str:
    explicit = _text(item.get("journal"))
    if explicit:
        return explicit
    text = " ".join(_text(item.get(key)) for key in ("label", "source_id"))
    lowered = text.lower()
    if "jama network open" in lowered:
        return "JAMA Network Open"
    if "jama internal medicine" in lowered:
        return "JAMA Internal Medicine"
    if "jama" in lowered:
        return "JAMA"
    return _text(item.get("label")) or _text(item.get("source_id"))


def _claim_to_paragraph_map(claim_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for claim in _mapping_list(claim_map.get("claims")):
        claim_id = _text(claim.get("claim_id"))
        evidence_refs = _claim_evidence_refs(claim)
        if not claim_id or not evidence_refs:
            continue
        items.append(
            {
                "claim_id": claim_id,
                "section": _first_section(claim),
                "paragraph_role": _text(claim.get("paper_role")) or "claim-grounded results paragraph",
                "evidence_refs": evidence_refs,
            }
        )
    return items


def _claim_evidence_refs(claim: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for evidence in _mapping_list(claim.get("evidence_items")):
        refs.extend(_text(item) for item in _list(evidence.get("source_paths")) if _text(item))
        item_id = _text(evidence.get("item_id"))
        if item_id:
            refs.append(f"paper/claim_evidence_map.json#{item_id}")
    return list(dict.fromkeys(ref for ref in refs if ref))


def _first_section(claim: Mapping[str, Any]) -> str:
    for section in _list(claim.get("sections")):
        text = _text(section)
        if text:
            return text
    return "Results"


def _display_to_claim_map(
    claim_map: Mapping[str, Any],
    *,
    display_registry: Mapping[str, Any],
    table_catalog: Mapping[str, Any],
) -> list[dict[str, str]]:
    display_roles = _display_roles(display_registry=display_registry, table_catalog=table_catalog)
    items: list[dict[str, str]] = []
    for claim in _mapping_list(claim_map.get("claims")):
        claim_id = _text(claim.get("claim_id"))
        if not claim_id:
            continue
        for binding in _list(claim.get("display_bindings")):
            display_id, display_role = _display_binding(binding)
            if not display_id:
                continue
            items.append(
                {
                    "display_id": display_id,
                    "claim_id": claim_id,
                    "display_role": display_role or display_roles.get(display_id) or "supports claim",
                }
            )
    deduped: dict[tuple[str, str], dict[str, str]] = {}
    for item in items:
        deduped[(item["display_id"], item["claim_id"])] = item
    return list(deduped.values())


def _display_roles(
    *,
    display_registry: Mapping[str, Any],
    table_catalog: Mapping[str, Any],
) -> dict[str, str]:
    roles: dict[str, str] = {}
    for display in _mapping_list(display_registry.get("displays")):
        for key in ("display_id", "catalog_id"):
            display_id = _text(display.get(key))
            if display_id:
                roles[display_id] = _text(display.get("title")) or _text(display.get("requirement_key"))
    for table in _mapping_list(table_catalog.get("tables")):
        table_id = _text(table.get("table_id"))
        if table_id:
            roles[table_id] = _text(table.get("title")) or _text(table.get("paper_role")) or "table evidence"
    return roles


def _display_binding(binding: object) -> tuple[str, str]:
    if isinstance(binding, Mapping):
        return (
            _text(binding.get("display_id")) or _text(binding.get("catalog_id")) or _text(binding.get("table_id")),
            _text(binding.get("display_role")) or _text(binding.get("role")),
        )
    return _text(binding), ""


def _section_plan() -> dict[str, str]:
    return {
        "Introduction": "clinical problem, evidence gap, and objective",
        "Methods": "cohort, endpoint, analysis, transportability, and bias controls",
        "Results": "primary finding with uncertainty before display interpretation",
        "Discussion": "principal finding, prior work, clinical interpretation, and limitations",
    }


def _restrained_language_strategy(
    *,
    claim_map: Mapping[str, Any],
    prose_review: Mapping[str, Any],
) -> dict[str, Any]:
    forbidden = [
        _text(item)
        for claim in _mapping_list(claim_map.get("claims"))
        for item in _list(claim.get("prohibited_interpretations"))
        if _text(item)
    ]
    principles = [
        _text(item)
        for key in ("restraint_principles", "principles")
        for item in _list(prose_review.get(key))
        if _text(item)
    ]
    return {
        "forbidden_phrases": list(dict.fromkeys([*forbidden, "proves", "definitively establishes"])),
        "required_claim_qualifiers": ["was associated with", "was observed", "may support"],
        "style_principles": list(dict.fromkeys(principles)),
    }


def _payload_from_medical_analysis_contract(
    *,
    study_root: Path,
    profile: WorkspaceProfile | None,
) -> dict[str, Any]:
    if profile is None:
        return {}
    study_payload = _read_yaml(study_root / "study.yaml")
    if not study_payload:
        return {}
    payload = medical_analysis_contract.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=dict(study_payload),
        profile=profile,
    )
    if _text(payload.get("status")) != "resolved":
        return {}
    return {
        **dict(payload),
        "payload_source": SOURCE,
        "source_basis": "study_metadata_medical_analysis_contract_resolver",
        "source_refs": [str(study_root / "study.yaml")],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _payload_from_existing_study_line_decision(*, study_root: Path) -> dict[str, Any]:
    canonical = _read_json(study_line_decision_engine.stable_study_line_decision_path(study_root=study_root))
    if _selected_study_line_decision(canonical):
        return canonical
    route_decision = _read_json(study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json")
    nested = _mapping(route_decision.get("study_line_decision"))
    if _selected_study_line_decision(nested):
        return {
            **dict(nested),
            "payload_source": SOURCE,
            "source_basis": "route_decision_orchestrator.study_line_decision",
            "source_refs": [str(study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json")],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    scorecard = _mapping(route_decision.get("scorecard"))
    if _selected_study_line_decision(scorecard):
        return {
            **dict(scorecard),
            "payload_source": SOURCE,
            "source_basis": "route_decision_orchestrator.scorecard",
            "source_refs": [str(study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json")],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    return {}


def _payload_from_statistical_discipline_sources(*, study_root: Path) -> dict[str, Any]:
    contract_path = study_root / "paper" / "medical_analysis_contract.json"
    board_path = study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json"
    contract = _read_json(contract_path)
    if _text(contract.get("status")) != "resolved":
        return {}
    board = _read_json(board_path)
    if _text(board.get("surface")) != "bounded_analysis_candidate_board":
        return {}
    discipline_contract = _statistical_discipline_contract_from_analysis_contract(contract)
    if not discipline_contract:
        return {}
    return {
        **dict(discipline_contract),
        "contract": dict(discipline_contract),
        "medical_analysis_contract": dict(contract),
        "bounded_board": dict(board),
        "payload_source": SOURCE,
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
    if _text(discipline_contract.get("status")) != "resolved":
        return {}
    return {
        **dict(discipline_contract),
        "source_medical_analysis_contract": dict(contract),
        "source_basis": "medical_analysis_contract_statistical_discipline_mapping",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _statistical_discipline_archetype(contract: Mapping[str, Any]) -> str | None:
    manuscript_family = _text(contract.get("manuscript_family"))
    study_archetype = _text(contract.get("study_archetype"))
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


def _payload_from_existing_study_line_route_decision(*, study_root: Path) -> dict[str, Any]:
    canonical_path = study_line_decision_engine.stable_study_line_decision_path(study_root=study_root)
    decision = _read_json(canonical_path)
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
        *[_text(item) for item in _list(decision.get("stage_output_refs")) if _text(item)],
        *[_text(item) for item in _list(candidate.get("evidence_refs")) if _text(item)],
    ]
    return {
        "surface": "route_decision_orchestrator_operator_payload",
        "schema_version": SCHEMA_VERSION,
        "requested_action": "select_line",
        "candidates": [candidate],
        "readiness": readiness,
        "payload_source": SOURCE,
        "source_basis": "selected_study_line_decision",
        "source_refs": list(dict.fromkeys(ref for ref in source_refs if ref)),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _route_candidate_from_study_line_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    line_id = _text(decision.get("selected_line_id"))
    if not line_id:
        return {}
    current_route = _mapping(decision.get("current_route"))
    ranked = _first_selected_ranking(decision, selected_line_id=line_id)
    source = current_route or ranked or decision
    dimensions = _mapping(source.get("dimensions")) or _mapping(ranked.get("dimensions")) or _mapping(
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
    evidence_refs = _text_list(source.get("evidence_refs")) or _text_list(decision.get("evidence_refs"))
    stage_output_refs = _text_list(source.get("stage_output_refs")) or _text_list(decision.get("stage_output_refs"))
    return {
        "line_id": line_id,
        "title": _text(source.get("title")) or _text(decision.get("title")) or line_id,
        "question": _text(source.get("question")) or _text(decision.get("question")) or f"Can {line_id} answer the locked research question?",
        "evidence_basis": evidence_refs,
        "expected_artifact": _text(source.get("expected_artifact")) or f"artifacts/medical_paper/candidate_paths/{line_id}.json",
        "stop_rule": _text(source.get("stop_rule")) or _text(dimensions.get("stop_threshold")) or "owner_review_required_before_quality_claim",
        "dimensions": dict(dimensions),
        "evidence_refs": evidence_refs,
        "stage_output_refs": stage_output_refs,
        "claim_boundary_change": _text(source.get("claim_boundary_change")) or "unchanged",
    }


def _first_selected_ranking(decision: Mapping[str, Any], *, selected_line_id: str) -> Mapping[str, Any]:
    for item in _mapping_list(decision.get("ranking")):
        if _text(item.get("line_id")) == selected_line_id:
            return item
    return {}


def _payload_from_study_metadata_literature_and_stage_refs(*, study_root: Path) -> dict[str, Any]:
    study = _read_yaml(study_root / "study.yaml")
    if not study:
        return {}
    literature_payload = _read_json(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root))
    if _text(literature_payload.get("status")) != "ready":
        return {}
    stage_refs = _stage_output_refs(study_root=study_root)
    if not stage_refs:
        return {}
    study_id = _text(study.get("study_id")) or study_root.name
    evidence_refs = [
        str(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)),
        *[_text(item) for item in _list(literature_payload.get("citation_ledger_refs")) if _text(item)],
    ]
    candidate = {
        "line_id": study_id,
        "title": _text(study.get("title")) or study_id,
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
    if _text(payload.get("status")) != "selected":
        return {}
    return {
        **dict(payload),
        "payload_source": SOURCE,
        "source_basis": "study_metadata_literature_and_stage_refs",
        "source_refs": [
            str(study_root / "study.yaml"),
            str(literature_intelligence_os.stable_literature_intelligence_os_path(study_root=study_root)),
            *stage_refs,
        ],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


SOAK_STAGE_REF_HINTS: dict[str, tuple[str, ...]] = {
    "literature_scout": (
        "artifacts/stage_outputs/01-study_intake/receipts/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/owner_receipt.json",
        "artifacts/medical_paper/literature_intelligence_os.json",
        "artifacts/medical_paper/literature_provider_runtime.json",
    ),
    "line_selection": (
        "artifacts/stage_outputs/01-study_intake/projection/current_owner_delta.json",
        "artifacts/medical_paper/study_line_decision.json",
    ),
    "main_analysis": (
        "artifacts/stage_outputs/04-analysis_execution/analysis_run_record.json",
        "artifacts/stage_outputs/04-analysis_execution/primary_results_artifact_set.json",
    ),
    "bounded_analysis": (
        "artifacts/stage_outputs/04-analysis_execution/primary_results_artifact_set.json",
        "artifacts/medical_paper/bounded_analysis_candidate_board.json",
    ),
    "route_back": (
        "artifacts/stage_outputs/05-evidence_synthesis/evidence_synthesis_matrix.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/revision_action_matrix.json",
    ),
    "stop_loss": (
        "artifacts/medical_paper/stop_loss_memo.json",
        "artifacts/controller_decisions/latest.json",
    ),
    "revision_reopen": (
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/reviewer_quality_receipt.json",
        "artifacts/stage_outputs/07-independent_review_and_revision/receipts/owner_receipt.json",
    ),
    "runtime_recovery": (
        "artifacts/supervision/consumer/default_executor_execution/history.jsonl",
        "artifacts/runtime/runtime_status_summary.json",
        "artifacts/supervision/opl_current_control_state/latest.json",
    ),
    "finalize_rebuild": (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/publication_package_manifest.json",
    ),
    "final_pre_submission_audit": (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/publication_gate_receipt.json",
    ),
}


def _payload_from_real_study_soak_matrix_evidence(*, study_root: Path) -> dict[str, Any]:
    direct = real_paper_ai_first_soak.build_real_study_soak_matrix_evidence(study_roots=[study_root])
    if _text(direct.get("overall_status")) in {"complete", "partial"}:
        return {
            **dict(direct),
            "payload_source": SOURCE,
            "source_basis": "real_study_soak_matrix_evidence_builder",
            "source_refs": list(_list(direct.get("evidence_sources"))),
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    evidence_map = _soak_stage_evidence_map(study_root=study_root)
    if not any(evidence_map.values()):
        return _blocked_payload("insufficient_real_study_soak_matrix_evidence_sources", surface_key="real_study_soak_matrix_evidence")
    payload = real_paper_ai_first_soak.build_real_study_soak_matrix_evidence(evidence_map=evidence_map)
    return {
        **dict(payload),
        "payload_source": SOURCE,
        "source_basis": "real_study_soak_matrix_evidence_builder",
        "source_refs": [ref for refs in evidence_map.values() for ref in refs],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _soak_stage_evidence_map(*, study_root: Path) -> dict[str, list[str]]:
    root = Path(study_root).expanduser().resolve()
    evidence_map: dict[str, list[str]] = {}
    for stage, relative_refs in SOAK_STAGE_REF_HINTS.items():
        refs = [ref for ref in relative_refs if (root / ref).is_file()]
        evidence_map[stage] = refs
    return evidence_map


def _stage_output_refs(*, study_root: Path) -> list[str]:
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


def _payload_from_analysis_contract_candidate_board(*, study_root: Path) -> dict[str, Any]:
    path = study_root / "paper" / "medical_analysis_contract.json"
    contract = _read_json(path)
    if _text(contract.get("status")) != "resolved":
        return {}
    packages = [_text(item) for item in _list(contract.get("required_analysis_packages")) if _text(item)]
    if not packages:
        return {}
    candidates = [
        {
            "analysis_package": package,
            "target_claim": _target_claim_for_package(package=package, contract=contract),
            "expected_evidence_gain": f"Evaluate {package} against the active medical analysis contract.",
            "cost_risk": "bounded",
            "statistical_risk": "bounded_analysis_scope_requires_owner_review",
            "clinical_interpretability": "owner-review-required-before-quality-claim",
            "decision": "explore",
            "decision_reason": (
                "Generated from the resolved archetype analysis contract as a bounded candidate; "
                "this does not authorize a quality verdict."
            ),
        }
        for package in packages
    ]
    return {
        "surface": "bounded_analysis_candidate_board",
        "schema_version": SCHEMA_VERSION,
        "status": "present",
        "candidates": candidates,
        "payload_source": SOURCE,
        "source_basis": "resolved_archetype_analysis_contract_required_packages",
        "source_refs": [str(path)],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _payload_from_route_control_stop_loss(*, study_root: Path) -> dict[str, Any]:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision = _read_json(decision_path)
    next_action = _mapping(decision.get("readiness_next_action"))
    if _text(next_action.get("surface_key")) != "stop_loss_memo":
        return {}
    source_paths = (
        decision_path,
        study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff" / "receipts" / "typed_blocker.json",
        study_root / "artifacts" / "publication_eval" / "latest.json",
    )
    source_refs = [str(path) for path in source_paths if path.exists()]
    controller_blocker = _mapping(decision.get("controller_blocker"))
    failure_reasons = [
        text
        for text in (
            _text(controller_blocker.get("blocker_id")),
            _text(controller_blocker.get("reason")),
        )
        if text
    ] or ["medical_paper_readiness_stop_loss_memo_required"]
    attempted_paths = [
        text
        for text in (
            _text(next_action.get("action_id")),
            _text(next_action.get("surface_key")),
            _text(controller_blocker.get("required_owner_surface")),
        )
        if text
    ] or ["complete_medical_paper_readiness_surface"]
    payload = {
        "current_route": "complete_medical_paper_readiness_surface",
        "decision": "stop_loss",
        "evidence_state": "blocked",
        "stop_pressure": "high",
        "attempted_paths": list(dict.fromkeys(attempted_paths)),
        "failure_reasons": list(dict.fromkeys(failure_reasons)),
        "continuation_cost": {
            "runtime_scope": "repeated_readiness_surface_attempts",
            "quality_claim_authorized": False,
        },
        "evidence_gain_ceiling": "low_without_stop_loss_memo",
        "alternative_routes": ["return_to_write"],
        "evidence_refs": source_refs,
        "exploration_depth_review": {
            check: {
                "sufficient": True,
                "finding": "Current stop-loss decision is scoped to the readiness owner-route artifact gap.",
            }
            for check in route_control_stoploss.EXPLORATION_DEPTH_CHECKS
        },
        "payload_source": SOURCE,
        "source_basis": "controller_decision_readiness_next_action_stop_loss",
        "source_refs": source_refs,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    try:
        route_control_stoploss.build_route_control_stoploss_memo(
            **_payload_without_authoring_metadata(payload)
        )
    except (TypeError, ValueError):
        return {}
    return payload


def _payload_without_authoring_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata_keys = {
        "payload_source",
        "source_basis",
        "source_refs",
        "quality_claim_authorized",
        "mechanical_projection_can_authorize_quality",
    }
    return {key: value for key, value in dict(payload).items() if key not in metadata_keys}


def _target_claim_for_package(*, package: str, contract: Mapping[str, Any]) -> str:
    context = _mapping(contract.get("target_context"))
    primary_endpoint = _text(context.get("primary_endpoint")) or _text(contract.get("endpoint_type")) or "primary endpoint"
    archetype = _text(contract.get("study_archetype")) or "medical study"
    return f"{package} support for {archetype} on {primary_endpoint}"


def _selected_study_line_decision(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("surface") == study_line_decision_engine.SURFACE
        and _text(payload.get("status")) == "selected"
        and bool(_text(payload.get("selected_line_id")))
    )


def _blocked_payload(reason: str, *, surface_key: str | None) -> dict[str, Any]:
    return {
        "payload_source": SOURCE,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "blocked_reason": reason,
        "surface_key": _text(surface_key),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}



def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text_list(value: object) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


__all__ = ["author_operator_payload"]
