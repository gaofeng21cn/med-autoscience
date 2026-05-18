from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


OWNER = "analysis_harmonization_owner"
WORK_UNIT = "unit_harmonized_external_validation_rerun"
BLOCKED_REASON = "unit_harmonized_rerun_required"
CALLABLE_SURFACE = f"{OWNER}.{WORK_UNIT}_or_typed_blocker"
RESULT_RELATIVE_PATH = Path("artifacts/controller/analysis_harmonization/latest.json")
REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/analysis_harmonization/latest.json")

_CHINA_INPUT = Path("analysis/clean_room_execution/20_transportability/china_transportability_input.csv")
_NHANES_INPUT = Path("analysis/clean_room_execution/20_transportability/nhanes_transportability_input.csv")
_MAPPING_TABLE = Path("analysis/clean_room_execution/00_harmonization/predictor_mapping_table.md")
_MODEL_SPEC = Path("analysis/clean_room_execution/20_transportability/model_spec_and_feature_list.md")
_INPUT_CACHE = Path("analysis/clean_room_execution/20_transportability/analysis_input_cache_manifest.json")
_METRICS = Path("analysis/clean_room_execution/20_transportability/metrics_summary.json")
_MAIN_RESULT = Path("artifacts/results/main_result.json")

_FORBIDDEN_WRITE_SURFACES = (
    "paper/**",
    "manuscript/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
)


def stable_analysis_harmonization_owner_result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def unit_harmonized_external_validation_rerun_or_typed_blocker(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any] | None = None,
    request: Mapping[str, Any] | None = None,
    apply: bool,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    dispatch_payload = _mapping(dispatch)
    request_payload = _mapping(request)
    result_path = stable_analysis_harmonization_owner_result_path(study_root=study_root)
    payload = _build_owner_result(
        study_root=study_root,
        study_id=study_id,
        dispatch=dispatch_payload,
        request=request_payload,
        result_path=result_path,
    )
    if apply:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": CALLABLE_SURFACE,
        "next_owner": OWNER,
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
    evidence_refs = _evidence_refs(study_root)
    input_summary = _input_summary(study_root)
    prerequisite_assessment = _prerequisite_assessment(
        study_root=study_root,
        input_summary=input_summary,
    )
    status = "blocked" if prerequisite_assessment["blocking_reasons"] else "blocked"
    return {
        "surface": "analysis_harmonization_owner_result",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "study_id": study_id,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "status": status,
        "blocked_reason": BLOCKED_REASON,
        "typed_blocker_owner": OWNER,
        "typed_blocker": {
            "blocker_id": BLOCKED_REASON,
            "owner": OWNER,
            "work_unit": WORK_UNIT,
            "reason": (
                "The current external-validation evidence was generated from a raw-scale HDL mapping. "
                "A unit-harmonized rerun cannot be accepted until model and harmonization prerequisites are closed."
            ),
            "blocking_reasons": prerequisite_assessment["blocking_reasons"],
        },
        "unit_harmonized_rerun_completed": False,
        "rerun_evidence_ref": None,
        "analysis_lane_status": "exhausted_for_current_fingerprint",
        "recommended_next_route": "handoff_to_next_owner",
        "next_owner": OWNER,
        "next_work_unit": WORK_UNIT,
        "required_output": {
            "accepted_evidence": "unit-harmonized external-validation rerun evidence",
            "accepted_typed_blocker": BLOCKED_REASON,
        },
        "required_next_actions": [
            "verify HDL source units and select the unit-consistent NHANES HDL field or conversion",
            "verify sex and smoking coding against the development model",
            "verify continuous predictor transformations and feature order",
            "verify Cox model coefficients, penalty/tuning provenance, and 5-year baseline survival",
            "rerun external validation on unit-harmonized predictors or keep this typed blocker open",
        ],
        "input_summary": input_summary,
        "prerequisite_assessment": prerequisite_assessment,
        "evidence_refs": evidence_refs,
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


def _prerequisite_assessment(*, study_root: Path, input_summary: Mapping[str, Any]) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    hdl = _mapping(input_summary.get("hdl"))
    ratio = hdl.get("median_ratio_nhanes_to_china")
    if isinstance(ratio, int | float) and ratio > 10:
        blocking_reasons.append("hdl_unit_scale_mismatch")
    mapping_text = _read_text(study_root / _MAPPING_TABLE).lower()
    if "lbdhdd" in mapping_text and "lbdhddsi" not in mapping_text:
        blocking_reasons.append("nhanes_hdl_mapping_uses_raw_mg_dl_field_without_si_conversion_surface")
    model_text = _read_text(study_root / _MODEL_SPEC).lower()
    input_cache = _read_json_object(study_root / _INPUT_CACHE)
    model_detail_terms = ("coefficient", "baseline survival", "baseline_survival", "lambda", "penalty", "standardization")
    model_detail_text = " ".join([model_text, json.dumps(input_cache, ensure_ascii=False).lower()])
    if not any(term in model_detail_text for term in model_detail_terms):
        blocking_reasons.append("cox_model_application_provenance_insufficient_for_rerun")
    if not (study_root / _CHINA_INPUT).is_file() or not (study_root / _NHANES_INPUT).is_file():
        blocking_reasons.append("transportability_input_surface_missing")
    return {
        "status": "blocked" if blocking_reasons else "ready_for_owner_rerun",
        "blocking_reasons": blocking_reasons or ["unit_harmonized_rerun_evidence_not_materialized"],
        "raw_scale_existing_metrics_may_authorize_medical_claims": False,
        "rerun_without_prerequisites_allowed": False,
    }


def _input_summary(study_root: Path) -> dict[str, Any]:
    china_hdl = _numeric_column_summary(study_root / _CHINA_INPUT, "HDL")
    nhanes_hdl = _numeric_column_summary(study_root / _NHANES_INPUT, "HDL")
    median_ratio = None
    if china_hdl.get("median") not in (None, 0) and nhanes_hdl.get("median") is not None:
        median_ratio = nhanes_hdl["median"] / china_hdl["median"]
    return {
        "china_input_ref": str(study_root / _CHINA_INPUT),
        "nhanes_input_ref": str(study_root / _NHANES_INPUT),
        "mapping_table_ref": str(study_root / _MAPPING_TABLE),
        "model_spec_ref": str(study_root / _MODEL_SPEC),
        "metrics_ref": str(study_root / _METRICS),
        "main_result_ref": str(study_root / _MAIN_RESULT),
        "hdl": {
            "china": china_hdl,
            "nhanes": nhanes_hdl,
            "median_ratio_nhanes_to_china": median_ratio,
            "raw_scale_mismatch_suspected": isinstance(median_ratio, int | float) and median_ratio > 10,
        },
    }


def _numeric_column_summary(path: Path, column: str) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "available": False, "column": column}
    values: list[float] = []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                try:
                    values.append(float(row[column]))
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError:
        return {"path": str(path), "available": False, "column": column}
    values.sort()
    return {
        "path": str(path),
        "available": True,
        "column": column,
        "n": len(values),
        "min": values[0] if values else None,
        "median": _quantile(values, 0.5),
        "max": values[-1] if values else None,
    }


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    pos = (len(values) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(values) - 1)
    weight = pos - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _evidence_refs(study_root: Path) -> list[str]:
    refs: list[str] = []
    for relative in (
        _CHINA_INPUT,
        _NHANES_INPUT,
        _MAPPING_TABLE,
        _MODEL_SPEC,
        _INPUT_CACHE,
        _METRICS,
        _MAIN_RESULT,
    ):
        path = study_root / relative
        if path.exists():
            refs.append(str(path))
    return refs


def _source_action_ref(*, dispatch: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping(dispatch.get("refs"))
    request_source = _mapping(request.get("source_action_ref"))
    return {
        "action_type": _text(dispatch.get("action_type")) or _text(request_source.get("action_type")),
        "action_id": _text(dispatch.get("action_id")) or _text(request_source.get("action_id")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")) or _text(request_source.get("dispatch_authority")),
        "dispatch_path": _text(refs.get("dispatch_path")) or _text(request_source.get("dispatch_path")),
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = [
    "BLOCKED_REASON",
    "CALLABLE_SURFACE",
    "OWNER",
    "RESULT_RELATIVE_PATH",
    "WORK_UNIT",
    "stable_analysis_harmonization_owner_result_path",
    "unit_harmonized_external_validation_rerun_or_typed_blocker",
]
