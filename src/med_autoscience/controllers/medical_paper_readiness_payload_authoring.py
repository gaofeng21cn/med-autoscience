from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers import medical_analysis_contract
from med_autoscience.controllers import literature_intelligence_os
from med_autoscience.controllers import route_control_stoploss
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


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


__all__ = ["author_operator_payload"]
