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

_SEARCH_TOKENS = ("model", "cox", "coef", "coeff", "survival", "hazard", "provenance", "result")
_SEARCH_SUFFIXES = {".json", ".yaml", ".yml", ".csv", ".txt", ".md", ".pkl", ".pickle", ".joblib", ".rds", ".rda"}
_EXCLUDED_SEARCH_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "consumer",
    "controller",
    "node_modules",
    "requests",
    "source_provenance",
    "supervision",
}
_ROOT_SEARCH_LIMITS = {
    "study_artifacts": {"max_depth": 5, "max_files_visited": 1500, "max_candidates": 80},
    "study_analysis": {"max_depth": 6, "max_files_visited": 1500, "max_candidates": 80},
    "study_experiments": {"max_depth": 6, "max_files_visited": 1500, "max_candidates": 80},
    "study_paper_analysis": {"max_depth": 5, "max_files_visited": 1000, "max_candidates": 50},
    "runtime_quest": {"max_depth": 5, "max_files_visited": 1200, "max_candidates": 60},
    "legacy_archive": {"max_depth": 4, "max_files_visited": 800, "max_candidates": 40},
}


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
        profile=profile,
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
        "next_owner": _text(payload.get("next_owner")) or OWNER,
        "next_work_unit": _text(payload.get("next_work_unit")) or WORK_UNIT,
        "owner_result": payload,
        "result_path": str(result_path),
        "required_output_surface": str(result_path),
    }


def _build_owner_result(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    dispatch: Mapping[str, Any],
    request: Mapping[str, Any],
    result_path: Path,
) -> dict[str, Any]:
    evidence_refs = _evidence_refs(study_root)
    provenance_search = _provenance_search(profile=profile, study_root=study_root, study_id=study_id)
    assessment = _provenance_assessment(
        study_root=study_root,
        evidence_refs=evidence_refs,
        provenance_search=provenance_search,
    )
    accepted_bundle_ref = provenance_search["accepted_bundle_ref"]
    recovered = accepted_bundle_ref is not None
    terminal_blocker = not recovered and provenance_search.get("searched") is True and "accepted_bundle_ref" in provenance_search
    next_owner = "analysis_harmonization_owner" if recovered else "decision" if terminal_blocker else OWNER
    next_work_unit = (
        "unit_harmonized_external_validation_rerun"
        if recovered
        else "methodology_reframe_route_decision"
        if terminal_blocker
        else WORK_UNIT
    )
    return {
        "surface": "source_provenance_owner_result",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "study_id": study_id,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "status": "completed" if recovered else "blocked",
        "blocked_reason": None if recovered else BLOCKED_REASON,
        "source_blocked_reason": None if recovered else BLOCKED_REASON,
        "typed_blocker_owner": None if recovered else OWNER,
        "typed_blocker": None if recovered else _typed_blocker(assessment=assessment),
        "transport_model_provenance_recovered": recovered,
        "canonical_transport_model_provenance_bundle_ref": accepted_bundle_ref,
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
        "provenance_search": provenance_search,
        "evidence_refs": evidence_refs,
        "source_action_ref": _source_action_ref(dispatch=dispatch, request=request),
        "request_ref": {
            "path": str(study_root / REQUEST_RELATIVE_PATH),
            "request_kind": _text(request.get("request_kind")) or WORK_UNIT,
        },
        "result_ref": str(result_path),
        "next_owner": next_owner,
        "next_work_unit": next_work_unit,
        "terminal_source_provenance_blocker": terminal_blocker,
        "current_transport_claim_must_not_be_used_as_medical_conclusion": terminal_blocker,
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


def _typed_blocker(*, assessment: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "blocker_id": BLOCKED_REASON,
        "owner": OWNER,
        "work_unit": WORK_UNIT,
        "reason": (
            "The transported Cox model cannot be re-applied as the original development model until "
            "its coefficients, feature coding, baseline survival, penalty provenance, standardization "
            "state, and original result artifact are recovered."
        ),
        "blocking_reasons": list(assessment["blocking_reasons"]),
    }


def _provenance_assessment(
    *,
    study_root: Path,
    evidence_refs: Mapping[str, Any],
    provenance_search: Mapping[str, Any],
) -> dict[str, Any]:
    if provenance_search.get("accepted_bundle_ref"):
        return {
            "status": "completed",
            "blocking_reasons": [],
            "required_requirements": list(_PROVENANCE_REQUIREMENTS),
            "available_refs": {
                "canonical_transport_model_provenance_bundle": {
                    "path": provenance_search["accepted_bundle_ref"],
                    "available": True,
                }
            },
            "recovery_without_original_model_artifact_allowed": False,
            "refit_substitute_model_allowed": False,
            "medical_claim_authoring_allowed": False,
        }
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
    if provenance_search.get("searched") is True and not provenance_search.get("accepted_bundle_ref"):
        missing.append("canonical_transport_model_provenance_bundle_missing")
    return {
        "status": "blocked",
        "blocking_reasons": _unique_texts(missing or ["canonical_transport_model_provenance_bundle_not_materialized"]),
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


def _provenance_search(*, profile: WorkspaceProfile, study_root: Path, study_id: str) -> dict[str, Any]:
    roots = _search_roots(profile=profile, study_root=study_root, study_id=study_id)
    candidates, root_scan_summaries = _candidate_files(roots)
    accepted_bundle_ref: str | None = None
    candidate_payloads: list[dict[str, Any]] = []
    for path in candidates:
        validation = _validate_candidate_bundle(path)
        if validation["accepted"] and accepted_bundle_ref is None:
            accepted_bundle_ref = str(path)
        candidate_payloads.append(
            {
                "path": str(path),
                "root_kind": _root_kind(path=path, roots=roots),
                "candidate_kind": validation["candidate_kind"],
                "accepted": validation["accepted"],
                "missing_requirements": validation["missing_requirements"],
            }
        )
    return {
        "searched": True,
        "bounded_search": True,
        "search_roots": [{"root_kind": root_kind, "path": str(path), "available": path.exists()} for root_kind, path in roots],
        "root_scan_summaries": root_scan_summaries,
        "candidate_count": len(candidate_payloads),
        "accepted_bundle_ref": accepted_bundle_ref,
        "candidates": candidate_payloads,
        "accepted_bundle_required_surface": "canonical_transport_model_provenance_bundle",
        "result_summary_acceptance_allowed": False,
        "substitute_refit_allowed": False,
    }


def _search_roots(*, profile: WorkspaceProfile, study_root: Path, study_id: str) -> list[tuple[str, Path]]:
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return [
        ("study_artifacts", study_root / "artifacts"),
        ("study_analysis", study_root / "analysis"),
        ("study_experiments", study_root / "experiments"),
        ("study_paper_analysis", study_root / "paper"),
        ("runtime_quest", Path(profile.runtime_root).expanduser().resolve() / study_id),
        ("legacy_archive", workspace_root / "runtime" / "archives" / "legacy_mds"),
    ]


def _candidate_files(roots: list[tuple[str, Path]]) -> tuple[list[Path], list[dict[str, Any]]]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    summaries: list[dict[str, Any]] = []
    for root_kind, root in roots:
        root_candidates, summary = _candidate_files_for_root(root_kind=root_kind, root=root, seen=seen)
        candidates.extend(root_candidates)
        summaries.append(summary)
    return sorted(candidates, key=lambda path: str(path)), summaries


def _candidate_files_for_root(*, root_kind: str, root: Path, seen: set[Path]) -> tuple[list[Path], dict[str, Any]]:
    limits = _ROOT_SEARCH_LIMITS.get(root_kind, {"max_depth": 4, "max_files_visited": 800, "max_candidates": 40})
    max_depth = int(limits["max_depth"])
    max_files_visited = int(limits["max_files_visited"])
    max_candidates = int(limits["max_candidates"])
    candidates: list[Path] = []
    summary: dict[str, Any] = {
        "root_kind": root_kind,
        "path": str(root),
        "available": root.is_dir(),
        "bounded": True,
        "max_depth": max_depth,
        "max_files_visited": max_files_visited,
        "max_candidates": max_candidates,
        "directories_scanned": 0,
        "files_visited": 0,
        "candidate_count": 0,
        "excluded_directory_count": 0,
        "skipped_by_depth_count": 0,
        "truncated": False,
        "errors": [],
    }
    if not root.is_dir():
        return candidates, summary

    pending: list[tuple[Path, int]] = [(root, 0)]
    while pending:
        directory, depth = pending.pop()
        try:
            entries = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            summary["errors"].append({"path": str(directory), "error": exc.__class__.__name__})
            continue
        summary["directories_scanned"] += 1
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name.lower() in _EXCLUDED_SEARCH_PARTS:
                    summary["excluded_directory_count"] += 1
                    continue
                if depth >= max_depth:
                    summary["skipped_by_depth_count"] += 1
                    continue
                pending.append((entry, depth + 1))
                continue
            if not entry.is_file():
                continue
            summary["files_visited"] += 1
            if summary["files_visited"] > max_files_visited:
                summary["truncated"] = True
                summary["files_visited"] = max_files_visited
                summary["candidate_count"] = len(candidates)
                return candidates, summary
            if not _is_candidate_path(entry):
                continue
            resolved = entry.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(resolved)
            if len(candidates) >= max_candidates:
                summary["truncated"] = True
                summary["candidate_count"] = len(candidates)
                return candidates, summary
        summary["candidate_count"] = len(candidates)
    return candidates, summary


def _is_candidate_path(path: Path) -> bool:
    try:
        lowered_parts = {part.lower() for part in path.parts}
    except OSError:
        return False
    if lowered_parts.intersection(_EXCLUDED_SEARCH_PARTS):
        return False
    if path.suffix.lower() not in _SEARCH_SUFFIXES:
        return False
    name = path.name.lower()
    recent_parts = " ".join(part.lower() for part in path.parts[-4:])
    return any(token in name or token in recent_parts for token in _SEARCH_TOKENS)


def _validate_candidate_bundle(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload is None:
        return {
            "accepted": False,
            "candidate_kind": "non_json_or_non_object_candidate",
            "missing_requirements": list(_PROVENANCE_REQUIREMENTS),
        }
    surface = _text(payload.get("surface")) or _text(payload.get("surface_kind"))
    candidate_kind = surface or "json_candidate"
    if surface != "canonical_transport_model_provenance_bundle":
        return {
            "accepted": False,
            "candidate_kind": candidate_kind,
            "missing_requirements": ["canonical_transport_model_provenance_bundle_surface_missing"],
        }
    missing = _bundle_missing_requirements(payload)
    return {
        "accepted": not missing,
        "candidate_kind": candidate_kind,
        "missing_requirements": missing,
    }


def _bundle_missing_requirements(payload: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    coefficients = payload.get("coefficients") or payload.get("model_coefficients")
    if not _contains_coefficients({"coefficients": coefficients}):
        missing.append("cox_model_coefficients")
    if not _non_empty(payload.get("feature_order")) or not _non_empty(
        payload.get("feature_coding") or payload.get("coding")
    ):
        missing.append("feature_order_and_coding")
    if not _has_bundle_baseline(payload):
        missing.append("baseline_survival_or_cumulative_hazard_at_5_years")
    if not _non_empty(payload.get("penalty") or payload.get("tuning") or payload.get("penalty_or_tuning")):
        missing.append("penalty_or_tuning_provenance")
    if not _non_empty(
        payload.get("standardization")
        or payload.get("standardisation")
        or payload.get("scaler")
        or payload.get("unit_conversions")
    ):
        missing.append("standardization_or_scaler_state")
    if not _non_empty(payload.get("original_result_artifact") or payload.get("original_result_ref")):
        missing.append("original_result_artifact")
    return missing


def _has_bundle_baseline(payload: Mapping[str, Any]) -> bool:
    baseline_keys = (
        "baseline_survival_at_5_years",
        "baseline_survival",
        "baseline_hazard_at_5_years",
        "baseline_hazard",
        "cumulative_baseline_hazard_at_5_years",
        "cumulative_baseline_hazard",
    )
    return any(_non_empty(payload.get(key)) for key in baseline_keys)


def _root_kind(*, path: Path, roots: list[tuple[str, Path]]) -> str:
    for root_kind, root in roots:
        if not root.exists():
            continue
        try:
            path.relative_to(root.resolve())
        except ValueError:
            continue
        return root_kind
    return "unknown"


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
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _unique_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


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
