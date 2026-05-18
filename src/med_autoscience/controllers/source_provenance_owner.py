from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


OWNER = "source_provenance_owner"
WORK_UNIT = "recover_transport_model_provenance"
BLOCKED_REASON = "transport_model_provenance_recovery_required"
CALLABLE_SURFACE = f"{OWNER}.{WORK_UNIT}_or_typed_blocker"
RESULT_RELATIVE_PATH = Path("artifacts/controller/source_provenance/latest.json")
REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/source_provenance/latest.json")

_ANALYSIS_OWNER_RESULT = Path("artifacts/controller/analysis_harmonization/latest.json")
_MODEL_SPEC = Path("analysis/clean_room_execution/20_transportability/model_spec_and_feature_list.md")
_INPUT_CACHE = Path("analysis/clean_room_execution/20_transportability/analysis_input_cache_manifest.json")
_METRICS = Path("analysis/clean_room_execution/20_transportability/metrics_summary.json")
_MAIN_RESULT = Path("artifacts/results/main_result.json")
_LEGACY_METHODS_MANIFEST = Path(
    "runtime/archives/legacy_mds/20260516T123324511821Z/med-deepscientist/paper/methods_implementation_manifest.json"
)
_LEGACY_REPRODUCIBILITY_SUPPLEMENT = Path(
    "runtime/archives/legacy_mds/20260516T123324511821Z/med-deepscientist/paper/manuscript_safe_reproducibility_supplement.json"
)

_FORBIDDEN_WRITE_SURFACES = (
    "paper/**",
    "manuscript/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
)

_PROVENANCE_REQUIREMENTS = (
    "cox_model_coefficients",
    "feature_order_and_coding",
    "baseline_survival_or_cumulative_hazard_at_5_years",
    "penalty_or_tuning_provenance",
    "standardization_or_scaler_state",
    "original_result_artifact",
)


def stable_source_provenance_owner_result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def recover_transport_model_provenance_or_typed_blocker(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any] | None = None,
    request: Mapping[str, Any] | None = None,
    apply: bool,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    result_path = stable_source_provenance_owner_result_path(study_root=study_root)
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
    assessment = _provenance_assessment(study_root=study_root, evidence_refs=evidence_refs)
    return {
        "surface": "source_provenance_owner_result",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "study_id": study_id,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "status": "blocked",
        "blocked_reason": BLOCKED_REASON,
        "typed_blocker_owner": OWNER,
        "typed_blocker": {
            "blocker_id": BLOCKED_REASON,
            "owner": OWNER,
            "work_unit": WORK_UNIT,
            "reason": (
                "The transported Cox model cannot be re-applied as the original development model until "
                "its coefficients, feature coding, baseline survival, penalty provenance, standardization "
                "state, and original result artifact are recovered."
            ),
            "blocking_reasons": assessment["blocking_reasons"],
        },
        "transport_model_provenance_recovered": False,
        "canonical_transport_model_provenance_bundle_ref": None,
        "required_output": {
            "accepted_evidence": "canonical transport model provenance bundle",
            "accepted_typed_blocker": BLOCKED_REASON,
        },
        "required_next_actions": [
            "recover the original Cox model coefficients and coefficient order",
            "recover categorical coding and reference levels for sex and smoking predictors",
            "recover the 5-year baseline survival or cumulative baseline hazard used for absolute risk",
            "recover penalty form, tuning parameter, and fitting environment provenance",
            "recover any standardization, centering, scaling, or unit conversion state used before model application",
            "recover the original RESULT/model artifact or keep this typed blocker open",
        ],
        "provenance_requirements": list(_PROVENANCE_REQUIREMENTS),
        "provenance_assessment": assessment,
        "evidence_refs": evidence_refs,
        "source_action_ref": _source_action_ref(dispatch=dispatch, request=request),
        "request_ref": {
            "path": str(study_root / REQUEST_RELATIVE_PATH),
            "request_kind": _text(request.get("request_kind")) or WORK_UNIT,
        },
        "result_ref": str(result_path),
        "next_owner": OWNER,
        "next_work_unit": WORK_UNIT,
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


def _provenance_assessment(*, study_root: Path, evidence_refs: Mapping[str, Any]) -> dict[str, Any]:
    model_spec_text = _read_text(study_root / _MODEL_SPEC).lower()
    input_cache = _read_json_object(study_root / _INPUT_CACHE)
    main_result = _read_json_object(study_root / _MAIN_RESULT)
    legacy_methods = _read_json_object(study_root / _LEGACY_METHODS_MANIFEST)
    legacy_repro = _read_json_object(study_root / _LEGACY_REPRODUCIBILITY_SUPPLEMENT)
    combined = " ".join(
        [
            model_spec_text,
            json.dumps(input_cache, ensure_ascii=False).lower(),
            json.dumps(main_result, ensure_ascii=False).lower(),
            json.dumps(legacy_methods, ensure_ascii=False).lower(),
            json.dumps(legacy_repro, ensure_ascii=False).lower(),
        ]
    )
    missing: list[str] = []
    if not _has_coefficients(main_result, input_cache, legacy_methods, legacy_repro):
        missing.append("cox_model_coefficients_missing")
    if not _has_any(combined, ("feature order", "feature_order", "reference level", "reference_level", "coding")):
        missing.append("feature_order_or_coding_missing")
    if not _has_any(combined, ("baseline survival", "baseline_survival", "baseline hazard", "baseline_hazard")):
        missing.append("baseline_survival_missing")
    if not _has_any(combined, ("penalizer", "penalty", "lambda", "tuning", "cross-validation", "cross_validation")):
        missing.append("penalty_or_tuning_provenance_incomplete")
    if not _has_any(combined, ("standardization", "standardisation", "scaler", "center", "scale", "unit conversion")):
        missing.append("standardization_or_scaler_state_unknown")
    if not _original_result_artifact_available(study_root=study_root, evidence_refs=evidence_refs, payloads=(main_result, input_cache)):
        missing.append("legacy_result_artifact_unavailable")
    return {
        "status": "blocked",
        "blocking_reasons": missing or ["canonical_transport_model_provenance_bundle_not_materialized"],
        "required_requirements": list(_PROVENANCE_REQUIREMENTS),
        "available_refs": {
            key: value
            for key, value in evidence_refs.items()
            if isinstance(value, Mapping) and value.get("available") is True
        },
        "recovery_without_original_model_artifact_allowed": False,
        "refit_substitute_model_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _has_coefficients(*payloads: Mapping[str, Any] | None) -> bool:
    for payload in payloads:
        if _contains_coefficients(payload):
            return True
    return False


def _contains_coefficients(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _text(key) in {"coefficients", "coef", "coefs", "model_coefficients"} and _non_empty(item):
                return True
            if _contains_coefficients(item):
                return True
    if isinstance(value, list):
        return any(_contains_coefficients(item) for item in value)
    return False


def _non_empty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping | list | tuple | set):
        return bool(value)
    return bool(str(value).strip())


def _original_result_artifact_available(
    *,
    study_root: Path,
    evidence_refs: Mapping[str, Any],
    payloads: tuple[Mapping[str, Any] | None, ...],
) -> bool:
    artifact_name_tokens = ("cox_model", "transport_model", "model_bundle", "coefficients", "coefs")
    for ref in evidence_refs.values():
        payload = _mapping(ref)
        path_text = _text(payload.get("path"))
        if (
            path_text
            and Path(path_text).expanduser().is_file()
            and any(token in Path(path_text).name.lower() for token in artifact_name_tokens)
            and payload.get("available") is True
        ):
            return True
    for payload in payloads:
        for path_text in _path_values(payload):
            path = Path(path_text).expanduser()
            candidate = path if path.is_absolute() else study_root / path
            if candidate.is_file() and any(token in candidate.name.lower() for token in artifact_name_tokens):
                return True
    return False


def _path_values(value: object) -> list[str]:
    values: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _text(key) in {"path", "ref", "artifact", "model_path", "result_path"} and (text := _text(item)):
                values.append(text)
            values.extend(_path_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_path_values(item))
    return values


def _evidence_refs(study_root: Path) -> dict[str, Any]:
    refs = {
        "analysis_harmonization_owner_result": study_root / _ANALYSIS_OWNER_RESULT,
        "model_spec": study_root / _MODEL_SPEC,
        "input_cache_manifest": study_root / _INPUT_CACHE,
        "metrics_summary": study_root / _METRICS,
        "main_result": study_root / _MAIN_RESULT,
        "legacy_methods_manifest": study_root / _LEGACY_METHODS_MANIFEST,
        "legacy_reproducibility_supplement": study_root / _LEGACY_REPRODUCIBILITY_SUPPLEMENT,
    }
    return {name: {"path": str(path), "available": path.is_file()} for name, path in refs.items()}


def _source_action_ref(*, dispatch: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action_type": _text(dispatch.get("action_type")),
        "action_id": _text(dispatch.get("action_id")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
        "request_path": _text(request.get("path")),
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "BLOCKED_REASON",
    "CALLABLE_SURFACE",
    "OWNER",
    "REQUEST_RELATIVE_PATH",
    "RESULT_RELATIVE_PATH",
    "WORK_UNIT",
    "recover_transport_model_provenance_or_typed_blocker",
    "stable_source_provenance_owner_result_path",
]
