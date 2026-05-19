from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.profiles import WorkspaceProfile


OWNER = "provenance_limited_harmonization_owner"
WORK_UNIT = "provenance_limited_harmonization_audit"
BLOCKED_REASON = "provenance_limited_harmonization_audit_required"
REBUILD_ROUTE_REQUIRED = "rebuild_reproducible_model_route_required"
REBUILD_AUTHORIZATION_KIND = "methodology_rebuild_authorization"
REBUILD_AUTHORIZED_RERUN_REQUIRED = "unit_harmonized_rerun_required"
REBUILD_AUTHORIZED_OWNER = "analysis_harmonization_owner"
REBUILD_AUTHORIZED_WORK_UNIT = "unit_harmonized_external_validation_rerun"
CALLABLE_SURFACE = f"{OWNER}.{WORK_UNIT}_or_typed_blocker"
RESULT_RELATIVE_PATH = Path("artifacts/controller/provenance_limited_harmonization/latest.json")
REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/provenance_limited_harmonization/latest.json")
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
TASK_INTAKE_RELATIVE_PATH = Path("artifacts/controller/task_intake/latest.json")

_METHODOLOGY_REFRAME_FINGERPRINT = "decision::methodology_reframe_route_decision"
_ROUTE_OPTIONS = (
    "stop_loss_current_transport_claim",
    "provenance_limited_harmonization_audit",
    "rebuild_reproducible_model_route",
    "human_gate",
)
_FORBIDDEN_WRITE_SURFACES = (
    "paper/**",
    "manuscript/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
)


def stable_provenance_limited_harmonization_owner_result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def controller_decision_requests_audit(*, study_root: Path) -> bool:
    decision = _read_json_object(Path(study_root).expanduser().resolve() / CONTROLLER_DECISION_RELATIVE_PATH)
    return _decision_contract(decision)["valid"]


def rebuild_authorization(*, study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    path = root / TASK_INTAKE_RELATIVE_PATH
    payload = _read_json_object(path)
    if _text(_mapping(payload).get("task_intake_kind")) != REBUILD_AUTHORIZATION_KIND:
        return {"authorized": False, "path": str(path)}
    return {
        "authorized": True,
        "path": str(path),
        "task_id": _text(_mapping(payload).get("task_id")),
        "task_intake_kind": REBUILD_AUTHORIZATION_KIND,
        "emitted_at": _text(_mapping(payload).get("emitted_at")),
        "summary": _text(_mapping(payload).get("task_intent")) or _text(_mapping(payload).get("summary")),
    }


def rebuild_authorization_supersedes_result(*, study_root: Path, result_payload: Mapping[str, Any] | None) -> bool:
    authorization = rebuild_authorization(study_root=study_root)
    if authorization.get("authorized") is not True:
        return False
    result = _mapping(result_payload)
    if result.get("rebuild_authorization_consumed") is True:
        return False
    emitted_at = _text(authorization.get("emitted_at"))
    generated_at = _text(result.get("generated_at"))
    if emitted_at is not None and generated_at is not None:
        return emitted_at > generated_at
    authorization_mtime = _path_mtime(Path(str(authorization["path"])))
    result_mtime = _path_mtime(stable_provenance_limited_harmonization_owner_result_path(study_root=study_root))
    return authorization_mtime is not None and (result_mtime is None or authorization_mtime > result_mtime)


def provenance_limited_harmonization_audit_or_typed_blocker(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any] | None = None,
    request: Mapping[str, Any] | None = None,
    apply: bool,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    result_path = stable_provenance_limited_harmonization_owner_result_path(study_root=study_root)
    payload = _build_owner_result(
        study_root=study_root,
        study_id=study_id,
        dispatch=_mapping(dispatch),
        request=_mapping(request),
        result_path=result_path,
    )
    if apply:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": CALLABLE_SURFACE,
        "next_owner": payload["next_owner"],
        "owner_result": payload,
        "result_path": str(result_path),
        "required_output_surface": str(result_path),
    }


def _build_owner_result(
    *,
    study_root: Path,
    study_id: str,
    dispatch: Mapping[str, Any],
    request: Mapping[str, Any],
    result_path: Path,
) -> dict[str, Any]:
    decision_path = study_root / CONTROLLER_DECISION_RELATIVE_PATH
    decision = _read_json_object(decision_path)
    decision_contract = _decision_contract(decision)
    analysis_result_path = analysis_harmonization_owner_result.result_path(study_root=study_root)
    source_result_path = source_provenance_owner_result.result_path(study_root=study_root)
    source_result = source_provenance_owner_result.read_result(study_root=study_root)
    source_terminal = _source_terminal_blocker(source_result)
    provenance_recovered = _mapping(source_result).get("transport_model_provenance_recovered") is True
    authorization = rebuild_authorization(study_root=study_root)
    route = _selected_route(
        decision_contract=decision_contract,
        source_terminal=source_terminal,
        provenance_recovered=provenance_recovered,
        rebuild_authorized=authorization.get("authorized") is True,
    )
    return {
        "surface": "provenance_limited_harmonization_owner_result",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "study_id": study_id,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "status": "blocked" if route["blocked_reason"] else "completed",
        "blocked_reason": route["blocked_reason"],
        "typed_blocker_owner": OWNER if route["blocked_reason"] else None,
        "typed_blocker": _typed_blocker(route=route, decision_contract=decision_contract) if route["blocked_reason"] else None,
        "provenance_limited_audit_completed": decision_contract["valid"],
        "selected_route_option": "provenance_limited_harmonization_audit",
        "terminal_source_provenance_blocker_consumed": source_terminal,
        "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        "raw_transported_score_results_allowed_uses": [
            "harmonization_failure_evidence",
            "provenance_gap_documentation",
            "methods_limitation_context",
        ],
        "raw_transported_score_results_disallowed_uses": [
            "medical_transportability_conclusion",
            "clinical_model_validation_claim",
            "country_mortality_gap_attribution",
            "submission_readiness_verdict",
        ],
        "provenance_recovered": provenance_recovered,
        "rebuild_authorization": authorization,
        "rebuild_authorization_consumed": authorization.get("authorized") is True,
        "recommended_next_route": route["recommended_next_route"],
        "next_owner": route["next_owner"],
        "next_work_unit": route["next_work_unit"],
        "route_options": list(_ROUTE_OPTIONS),
        "route_option_assessment": route["route_option_assessment"],
        "required_output": {
            "accepted_evidence": "provenance-limited harmonization audit",
            "accepted_typed_blocker": BLOCKED_REASON,
        },
        "required_next_actions": route["required_next_actions"],
        "decision_contract": decision_contract,
        "evidence_refs": {
            "controller_decision": {"path": str(decision_path), "available": decision is not None},
            "analysis_harmonization_owner_result": {
                "path": str(analysis_result_path),
                "available": analysis_result_path.is_file(),
            },
            "source_provenance_owner_result": {
                "path": str(source_result_path),
                "available": source_result_path.is_file(),
                "terminal_source_provenance_blocker": source_terminal,
            },
        },
        "source_action_ref": _source_action_ref(dispatch=dispatch, request=request),
        "request_ref": {
            "path": str(study_root / REQUEST_RELATIVE_PATH),
            "request_kind": _text(request.get("request_kind")) or WORK_UNIT,
        },
        "result_ref": str(result_path),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "current_package_write_allowed": False,
        "submission_readiness_verdict_allowed": False,
        "quality_verdict_written": False,
        "publication_eval_written": False,
        "controller_decision_written": False,
        "forbidden_write_surfaces": list(_FORBIDDEN_WRITE_SURFACES),
    }


def _decision_contract(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(decision)
    next_work_unit = _mapping(payload.get("next_work_unit"))
    valid = bool(
        _text(payload.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and _text(payload.get("work_unit_fingerprint")) == _METHODOLOGY_REFRAME_FINGERPRINT
        and _text(next_work_unit.get("unit_id")) == WORK_UNIT
        and _text(next_work_unit.get("selected_route_option")) == WORK_UNIT
        and next_work_unit.get("terminal_source_provenance_blocker_consumed") is True
        and next_work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is True
    )
    missing: list[str] = []
    if not payload:
        missing.append("controller_decision_missing")
    if _text(payload.get("work_unit_fingerprint")) != _METHODOLOGY_REFRAME_FINGERPRINT:
        missing.append("methodology_reframe_fingerprint_missing")
    if _text(next_work_unit.get("unit_id")) != WORK_UNIT:
        missing.append("provenance_limited_harmonization_audit_not_selected")
    if next_work_unit.get("terminal_source_provenance_blocker_consumed") is not True:
        missing.append("terminal_source_provenance_blocker_not_consumed")
    if next_work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is not True:
        missing.append("transport_claim_guardrail_missing")
    return {
        "valid": valid,
        "missing_requirements": missing,
        "decision_type": _text(payload.get("decision_type")),
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint")),
        "selected_next_work_unit": next_work_unit,
    }


def _selected_route(
    *,
    decision_contract: Mapping[str, Any],
    source_terminal: bool,
    provenance_recovered: bool,
    rebuild_authorized: bool,
) -> dict[str, Any]:
    if decision_contract.get("valid") is not True:
        return {
            "blocked_reason": BLOCKED_REASON,
            "recommended_next_route": "human_gate",
            "next_owner": "decision",
            "next_work_unit": "methodology_reframe_route_decision",
            "route_option_assessment": _route_option_assessment(
                selected="human_gate",
                reason="controller_decision_contract_incomplete",
            ),
            "required_next_actions": [
                "materialize a valid methodology reframe controller decision before any paper or medical-claim work",
            ],
        }
    if provenance_recovered:
        return {
            "blocked_reason": None,
            "recommended_next_route": "rebuild_reproducible_model_route",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "route_option_assessment": _route_option_assessment(
                selected="rebuild_reproducible_model_route",
                reason="transport_model_provenance_recovered",
            ),
            "required_next_actions": [
                "rerun the transported model on unit-harmonized predictors",
                "only then re-author external-validation claims from refreshed evidence",
            ],
        }
    if source_terminal and rebuild_authorized:
        return {
            "blocked_reason": REBUILD_AUTHORIZED_RERUN_REQUIRED,
            "recommended_next_route": "rebuild_reproducible_model_route",
            "next_owner": REBUILD_AUTHORIZED_OWNER,
            "next_work_unit": REBUILD_AUTHORIZED_WORK_UNIT,
            "route_option_assessment": _route_option_assessment(
                selected="rebuild_reproducible_model_route",
                reason="human_gate_authorized_clean_reproducible_model_rebuild",
            ),
            "required_next_actions": [
                "define and execute a clean reproducible model contract with unit-harmonized predictors",
                "verify HDL units, categorical coding, feature order, Cox parameters, baseline survival, and uncertainty outputs",
                "only then re-author external-validation claims from refreshed evidence",
            ],
        }
    if source_terminal:
        return {
            "blocked_reason": REBUILD_ROUTE_REQUIRED,
            "recommended_next_route": "human_gate",
            "next_owner": "human_gate",
            "next_work_unit": "authorize_rebuild_reproducible_model_route_or_stop_loss_current_transport_claim",
            "route_option_assessment": _route_option_assessment(
                selected="human_gate",
                reason="original_transport_model_provenance_unrecovered",
            ),
            "required_next_actions": [
                "do not use the current raw transported-score results as a medical validation conclusion",
                "obtain human authorization for a clean reproducible-model rebuild route or stop-loss the current transport claim",
                "if rebuild is authorized, define a new reproducible model contract with unit-harmonized predictors and uncertainty outputs",
            ],
        }
    return {
        "blocked_reason": BLOCKED_REASON,
        "recommended_next_route": "provenance_limited_harmonization_audit",
        "next_owner": OWNER,
        "next_work_unit": WORK_UNIT,
        "route_option_assessment": _route_option_assessment(
            selected="provenance_limited_harmonization_audit",
            reason="source_provenance_terminal_blocker_missing",
        ),
        "required_next_actions": [
            "materialize or refresh source_provenance_owner_result before completing this audit",
        ],
    }


def _route_option_assessment(*, selected: str, reason: str) -> dict[str, Any]:
    return {
        option: {
            "selected": option == selected,
            "reason": reason if option == selected else "not_selected_for_current_evidence_state",
        }
        for option in _ROUTE_OPTIONS
    }


def _source_terminal_blocker(payload: Mapping[str, Any] | None) -> bool:
    state = _mapping(payload)
    return bool(
        source_provenance_owner_result.result_is_accepted_typed_blocker(state)
        and _text(state.get("blocked_reason")) == source_provenance_owner_result.BLOCKED_REASON
        and state.get("transport_model_provenance_recovered") is not True
    )


def _typed_blocker(*, route: Mapping[str, Any], decision_contract: Mapping[str, Any]) -> dict[str, Any]:
    blocker_id = _text(route.get("blocked_reason")) or BLOCKED_REASON
    reason = (
        "Human-gate authorization for a clean reproducible-model rebuild was consumed. "
        "The next owner must rerun or type-block unit-harmonized external validation before any renewed "
        "medical transportability claim is authored."
        if blocker_id == REBUILD_AUTHORIZED_RERUN_REQUIRED
        else (
            "A provenance-limited harmonization audit was required after the terminal transported-model "
            "provenance blocker. The current raw transported-score evidence cannot support a medical "
            "transportability conclusion; the next route must be explicitly authorized."
        )
    )
    return {
        "blocker_id": blocker_id,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "reason": reason,
        "blocking_reasons": [blocker_id, *list(_string_items(decision_contract.get("missing_requirements")))],
    }


def _source_action_ref(*, dispatch: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    source_action = _mapping(dispatch.get("source_action"))
    return {
        "action_type": _text(dispatch.get("action_type")) or _text(source_action.get("action_type")),
        "action_id": _text(dispatch.get("action_id")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
        "source_ref": _text(source_action.get("source_ref")) or _text(_mapping(request.get("source_action_ref")).get("source_ref")),
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _path_mtime(path: Path) -> float | None:
    try:
        return Path(path).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "BLOCKED_REASON",
    "CALLABLE_SURFACE",
    "OWNER",
    "REBUILD_ROUTE_REQUIRED",
    "REBUILD_AUTHORIZATION_KIND",
    "REBUILD_AUTHORIZED_OWNER",
    "REBUILD_AUTHORIZED_RERUN_REQUIRED",
    "REBUILD_AUTHORIZED_WORK_UNIT",
    "REQUEST_RELATIVE_PATH",
    "RESULT_RELATIVE_PATH",
    "TASK_INTAKE_RELATIVE_PATH",
    "WORK_UNIT",
    "controller_decision_requests_audit",
    "provenance_limited_harmonization_audit_or_typed_blocker",
    "rebuild_authorization",
    "rebuild_authorization_supersedes_result",
    "stable_provenance_limited_harmonization_owner_result_path",
]
