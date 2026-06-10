from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.stage_quality_contract_parts.light_external import (
    LIGHT_BASE_OUTPUT_REF_KINDS,
    LIGHT_MATERIALIZER_OUTPUT_REF_KINDS,
)


SCHEMA_VERSION = 1
SURFACE_KIND = "light_external_advisory_materializer"
BUNDLE_SURFACE_KIND = "light_external_advisory_ref_bundle"
_STAGE_OUTPUTS_ROOT = Path("artifacts") / "stage_outputs"
_REF_KINDS: tuple[str, ...] = LIGHT_MATERIALIZER_OUTPUT_REF_KINDS
_DEFAULT_EXPECTED_REF_KINDS: tuple[str, ...] = LIGHT_BASE_OUTPUT_REF_KINDS
_PAYLOAD_SECTION_BY_REF_KIND = {
    "verified_asset_ref": "verified_asset",
    "collision_check_ref": "collision_check",
    "refusal_rehearsal_ref": "refusal_rehearsal",
    "fresh_evidence_gate_ref": "fresh_evidence_gate",
    "source_search_discipline_ref": "source_search_discipline",
    "data_access_sink_ref": "data_access_sink",
    "citation_edge_retraction_ref": "citation_edge_retraction",
    "citation_locator_audit_ref": "citation_locator_audit",
    "prisma_flow_reconciliation_ref": "prisma_flow_reconciliation",
    "figure_manifest_check_ref": "figure_manifest_check",
    "experiment_matrix_backlink_ref": "experiment_matrix_backlink",
    "statistical_analysis_triage_ref": "statistical_analysis_triage",
    "overclaim_lint_warning_ref": "overclaim_lint_warning",
    "argument_review_hint_ref": "argument_review_hint",
    "figure_integrity_warning_ref": "figure_integrity_warning",
    "style_fingerprint_hint_ref": "style_fingerprint_hint",
}


def materialize_light_advisory_refs(
    *,
    study_root: Path,
    study_id: str | None = None,
    work_unit_id: str,
    owner_action: str,
    stage: str | None = None,
    source_refs: Iterable[str] = (),
    payload: Mapping[str, Any] | None = None,
    route_required_ref_kinds: Iterable[str] = (),
    hard_gate: bool = False,
    apply: bool = False,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_study_id = _text(study_id) or resolved_study_root.name
    resolved_work_unit_id = _require_text(work_unit_id, "work_unit_id")
    resolved_owner_action = _require_text(owner_action, "owner_action")
    resolved_stage = _text(stage) or "current_owner_action"
    generated_at = _utc_now()
    payload_mapping = dict(payload or {})
    source_ref_payloads = [
        _source_ref_payload(study_root=resolved_study_root, source_ref=ref)
        for ref in _dedupe_texts(source_refs)
    ]
    if not source_ref_payloads:
        source_ref_payloads = [
            _source_ref_payload(study_root=resolved_study_root, source_ref="study.yaml")
        ]

    advisory_refs = [
        _advisory_ref_payload(
            ref_kind=ref_kind,
            study_id=resolved_study_id,
            work_unit_id=resolved_work_unit_id,
            owner_action=resolved_owner_action,
            stage=resolved_stage,
            generated_at=generated_at,
            source_refs=source_ref_payloads,
            payload=payload_mapping,
        )
        for ref_kind in _REF_KINDS
        if _payload_section(payload_mapping, ref_kind)
        or ref_kind == "verified_asset_ref"
    ]
    present_ref_kinds = {str(item["ref_kind"]) for item in advisory_refs}
    route_required = tuple(_dedupe_texts(route_required_ref_kinds))
    missing_route_required = [ref_kind for ref_kind in route_required if ref_kind not in present_ref_kinds]
    expected_ref_kinds = _dedupe_texts([*_DEFAULT_EXPECTED_REF_KINDS, *route_required])
    missing_advisory = [ref_kind for ref_kind in expected_ref_kinds if ref_kind not in present_ref_kinds]
    missing_advisory_ref_kinds = _dedupe_texts([*missing_advisory, *missing_route_required])
    authority_boundary = _authority_boundary()
    typed_blocker_candidate = (
        _typed_blocker_candidate_payload(
            study_id=resolved_study_id,
            work_unit_id=resolved_work_unit_id,
            owner_action=resolved_owner_action,
            stage=resolved_stage,
            missing_ref_kinds=missing_route_required,
            generated_at=generated_at,
            authority_boundary=authority_boundary,
        )
        if hard_gate and missing_route_required
        else None
    )
    bundle_rel = _bundle_ref(resolved_stage)
    typed_blocker_candidate_rel = (
        _typed_blocker_candidate_ref(resolved_stage)
        if typed_blocker_candidate is not None
        else None
    )
    ref_rel_paths = {
        str(item["ref_kind"]): _ref_payload_ref(resolved_stage, str(item["ref_kind"]))
        for item in advisory_refs
    }
    bundle = _bundle_payload(
        study_id=resolved_study_id,
        work_unit_id=resolved_work_unit_id,
        owner_action=resolved_owner_action,
        stage=resolved_stage,
        generated_at=generated_at,
        source_refs=source_ref_payloads,
        advisory_refs=advisory_refs,
        ref_rel_paths=ref_rel_paths,
        missing_advisory_ref_kinds=missing_advisory_ref_kinds,
        typed_blocker_candidate_ref=typed_blocker_candidate_rel,
        typed_blocker_candidate=typed_blocker_candidate,
        payload=payload_mapping,
        authority_boundary=authority_boundary,
    )

    if apply:
        for ref in advisory_refs:
            _write_json(
                resolved_study_root / ref_rel_paths[str(ref["ref_kind"])],
                ref,
            )
        _write_json(resolved_study_root / bundle_rel, bundle)
        if typed_blocker_candidate is not None and typed_blocker_candidate_rel is not None:
            _write_json(resolved_study_root / typed_blocker_candidate_rel, typed_blocker_candidate)

    status = "typed_blocker_candidate" if typed_blocker_candidate is not None else ("materialized" if apply else "dry_run")
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "work_unit_id": resolved_work_unit_id,
        "owner_action": resolved_owner_action,
        "stage": resolved_stage,
        "generated_at": generated_at,
        "apply": bool(apply),
        "bundle_ref": bundle_rel.as_posix(),
        "advisory_ref_paths": {key: path.as_posix() for key, path in ref_rel_paths.items()},
        "advisory_refs": advisory_refs,
        "missing_advisory_ref_kinds": missing_advisory_ref_kinds,
        "typed_blocker_candidate_ref": typed_blocker_candidate_rel.as_posix() if typed_blocker_candidate_rel else None,
        "typed_blocker_candidate": typed_blocker_candidate,
        "typed_blocker_ref": None,
        "typed_blocker": None,
        "progress_first_policy": _progress_first_policy(),
        "authority_boundary": authority_boundary,
        "light_runtime_dependency": False,
        "light_router_dependency": False,
        "light_db09_dependency": False,
    }


def _advisory_ref_payload(
    *,
    ref_kind: str,
    study_id: str,
    work_unit_id: str,
    owner_action: str,
    stage: str,
    generated_at: str,
    source_refs: list[dict[str, Any]],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    section = _payload_section(payload, ref_kind)
    ref_id = f"{ref_kind}:{study_id}:{work_unit_id}:{_fingerprint([source_refs, section])[:16]}"
    result: dict[str, Any] = {
        "surface_kind": "light_external_advisory_ref",
        "schema_version": SCHEMA_VERSION,
        "ref_kind": ref_kind,
        "ref_id": ref_id,
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "owner_action": owner_action,
        "stage_id": stage,
        "stage": stage,
        "recorded_at": generated_at,
        "source_refs": source_refs,
        "source_ref_fingerprint": _fingerprint(source_refs),
        "advisory_payload": section,
        "next_owner_effect": _text(payload.get("next_owner_effect")) or "brief_current_owner_or_reviewer",
        "blocks_current_delta": False,
        "blocks_unrelated_owner_dispatch": False,
        "route_required_only_when_declared_by_current_owner": True,
        "light_runtime_dependency": False,
        "light_router_dependency": False,
        "light_db09_dependency": False,
        "authority_boundary": _authority_boundary(),
    }
    if ref_kind == "verified_asset_ref":
        result["verification_state"] = _verified_asset_state(source_refs=source_refs, payload=section)
    elif ref_kind == "collision_check_ref":
        result["novelty_risk"] = _text(section.get("novelty_risk")) or "unknown_until_owner_review"
    elif ref_kind == "refusal_rehearsal_ref":
        unresolved = section.get("unresolved_critical_refs") or section.get("unresolved_critical_ref") or []
        result["unresolved_critical_ref_count"] = len(unresolved) if isinstance(unresolved, list) else 1
    elif ref_kind == "fresh_evidence_gate_ref":
        result["claim_supported"] = _claim_supported(section)
    elif ref_kind == "source_search_discipline_ref":
        result["source_discipline_state"] = _text(section.get("source_discipline_state")) or "owner_review_required"
        result["ordinary_scout_prisma_blocker"] = False
    elif ref_kind == "data_access_sink_ref":
        result["sink_authorized"] = _explicit_bool(section, "sink_authorized", default=False)
        result["artifact_or_publication_authority"] = False
    elif ref_kind == "citation_edge_retraction_ref":
        result["citation_edge_state"] = _text(section.get("citation_edge_state")) or "unknown"
        result["retraction_check_state"] = _text(section.get("retraction_check_state")) or "not_checked"
    elif ref_kind == "citation_locator_audit_ref":
        result["support_state"] = _support_state(section)
    elif ref_kind == "prisma_flow_reconciliation_ref":
        result["count_reconciled"] = _count_reconciled(section)
        result["systematic_review_only"] = True
    elif ref_kind == "figure_manifest_check_ref":
        result["effective_font_checked"] = _explicit_bool(section, "effective_font_checked", default=False)
        result["publication_package_authority"] = False
    elif ref_kind == "experiment_matrix_backlink_ref":
        result["derived_dataset_backlink_required"] = _explicit_bool(
            section,
            "derived_dataset_backlink_required",
            default=True,
        )
        result["runtime_truth_authority"] = False
    elif ref_kind == "statistical_analysis_triage_ref":
        result["analysis_triage_state"] = _text(section.get("analysis_triage_state")) or "reviewer_hint"
        result["quality_verdict_authority"] = False
    elif ref_kind == "overclaim_lint_warning_ref":
        result["warning_count"] = _warning_count(section)
        result["reviewer_verdict_authority"] = False
    elif ref_kind == "argument_review_hint_ref":
        result["claim_boundary_state"] = _text(section.get("claim_boundary_state")) or "owner_review_required"
    elif ref_kind == "figure_integrity_warning_ref":
        result["warning_count"] = _warning_count(section)
        result["artifact_mutation_authority"] = False
    elif ref_kind == "style_fingerprint_hint_ref":
        result["watch_only"] = True
        result["may_override_evidence_or_reviewer_concerns"] = False
    return result


def _bundle_payload(
    *,
    study_id: str,
    work_unit_id: str,
    owner_action: str,
    stage: str,
    generated_at: str,
    source_refs: list[dict[str, Any]],
    advisory_refs: list[dict[str, Any]],
    ref_rel_paths: Mapping[str, Path],
    missing_advisory_ref_kinds: list[str],
    typed_blocker_candidate_ref: Path | None,
    typed_blocker_candidate: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
    authority_boundary: Mapping[str, bool],
) -> dict[str, Any]:
    return {
        "surface_kind": BUNDLE_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "owner_action": owner_action,
        "stage_id": stage,
        "stage": stage,
        "recorded_at": generated_at,
        "source_refs": source_refs,
        "advisory_ref_paths": {key: value.as_posix() for key, value in ref_rel_paths.items()},
        "advisory_refs": advisory_refs,
        "missing_advisory_ref_kinds": list(missing_advisory_ref_kinds),
        "typed_blocker_candidate_ref": typed_blocker_candidate_ref.as_posix() if typed_blocker_candidate_ref else None,
        "typed_blocker_candidate": dict(typed_blocker_candidate) if typed_blocker_candidate is not None else None,
        "typed_blocker_ref": None,
        "typed_blocker": None,
        "input_payload_fingerprint": _fingerprint(payload),
        "progress_first_policy": _progress_first_policy(),
        "authority_boundary": dict(authority_boundary),
        "refs_only": True,
        "light_runtime_dependency": False,
        "light_router_dependency": False,
        "light_db09_dependency": False,
    }


def _typed_blocker_candidate_payload(
    *,
    study_id: str,
    work_unit_id: str,
    owner_action: str,
    stage: str,
    missing_ref_kinds: list[str],
    generated_at: str,
    authority_boundary: Mapping[str, bool],
) -> dict[str, Any]:
    candidate_id = f"light-advisory-required-ref:{study_id}:{work_unit_id}:{_fingerprint(missing_ref_kinds)[:16]}"
    return {
        "surface_kind": "light_external_advisory_typed_blocker_candidate",
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "candidate_type": "light_advisory_route_required_ref_missing",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "owner_action": owner_action,
        "stage": stage,
        "missing_ref_kinds": list(missing_ref_kinds),
        "recorded_at": generated_at,
        "may_block_current_delta_after_owner_materialization": True,
        "blocks_unrelated_owner_dispatch": False,
        "hard_gate_candidate_requires_owner_or_reviewer_materialization": True,
        "resolution_owner": owner_action,
        "light_runtime_dependency": False,
        "authority_boundary": dict(authority_boundary),
    }


def _payload_section(payload: Mapping[str, Any], ref_kind: str) -> dict[str, Any]:
    key = _PAYLOAD_SECTION_BY_REF_KIND[ref_kind]
    section = payload.get(key)
    return dict(section) if isinstance(section, Mapping) else {}


def _source_ref_payload(*, study_root: Path, source_ref: str) -> dict[str, Any]:
    normalized_ref = _require_text(source_ref, "source_ref")
    path = (study_root / normalized_ref).resolve()
    payload: dict[str, Any] = {
        "ref": normalized_ref,
        "path": str(path),
        "exists": path.exists(),
        "body_included": False,
    }
    if path.is_file():
        stat = path.stat()
        payload.update(
            {
                "bytes": stat.st_size,
                "sha256": _file_sha256(path),
            }
        )
    return payload


def _verified_asset_state(*, source_refs: list[Mapping[str, Any]], payload: Mapping[str, Any]) -> str:
    explicit = _text(payload.get("verification_state"))
    if explicit:
        return explicit
    return "verified_present" if all(ref.get("exists") is True for ref in source_refs) else "advisory_gap"


def _claim_supported(payload: Mapping[str, Any]) -> bool:
    explicit = payload.get("claim_supported")
    if isinstance(explicit, bool):
        return explicit
    return _text(payload.get("verification_exit_state")) in {"passed", "pass", "supported"}


def _support_state(payload: Mapping[str, Any]) -> str:
    explicit = _text(payload.get("support_state") or payload.get("support_verdict"))
    return explicit or "needs_locator_review"


def _count_reconciled(payload: Mapping[str, Any]) -> bool:
    explicit = payload.get("count_reconciled")
    if isinstance(explicit, bool):
        return explicit
    return _text(payload.get("reconciliation_state")) in {"passed", "pass", "reconciled"}


def _warning_count(payload: Mapping[str, Any]) -> int:
    warnings = payload.get("warnings") or payload.get("integrity_warnings") or []
    if isinstance(warnings, list):
        return len(warnings)
    return 1 if warnings else 0


def _explicit_bool(payload: Mapping[str, Any], key: str, *, default: bool) -> bool:
    explicit = payload.get(key)
    if isinstance(explicit, bool):
        return explicit
    return default


def _bundle_ref(stage: str) -> Path:
    return _STAGE_OUTPUTS_ROOT / _safe_segment(stage) / "advisory" / "light_external_pattern_refs.json"


def _ref_payload_ref(stage: str, ref_kind: str) -> Path:
    return _STAGE_OUTPUTS_ROOT / _safe_segment(stage) / "advisory" / "refs" / f"{ref_kind}.json"


def _typed_blocker_candidate_ref(stage: str) -> Path:
    return _STAGE_OUTPUTS_ROOT / _safe_segment(stage) / "advisory" / "typed_blocker_candidate.json"


def _progress_first_policy() -> dict[str, str | bool]:
    return {
        "missing_advisory_behavior": "do_not_block_dispatch",
        "route_required_missing_without_hard_gate": "advisory_gap_only",
        "route_required_missing_with_hard_gate": "typed_blocker_for_current_delta_only",
        "may_block_unrelated_owner_dispatch": False,
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_study_truth": False,
        "can_write_artifact_body": False,
        "can_write_memory_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_source_readiness": False,
        "can_sign_owner_receipt": False,
        "can_admit_route": False,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _dedupe_texts(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _safe_segment(value: str) -> str:
    text = _require_text(value, "path_segment")
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in text)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _require_text(value: object, label: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["SURFACE_KIND", "materialize_light_advisory_refs"]
