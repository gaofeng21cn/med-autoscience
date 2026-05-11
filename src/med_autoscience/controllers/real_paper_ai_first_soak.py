from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers.ai_reviewer_calibration import REAL_STUDY_SOAK_STAGES
from med_autoscience.stage_knowledge_contract import PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE


SCHEMA_VERSION = 1
SURFACE = "real_paper_ai_first_soak"
OBSERVATION_SURFACE = "real_paper_ai_first_soak_observation"
MATRIX_EVIDENCE_SURFACE = "real_study_soak_matrix_evidence"

CANONICAL_ARTIFACT_REBUILD_SOURCE = "canonical_sources_and_ai_reviewer_quality_decision"
QUALITY_AUTHORIZATION_SOURCE = "ai_reviewer_backed_publication_eval_or_manual_gate"
STRUCTURED_ROUTE_BACK_TAXONOMY = "structured_rework_taxonomy"
AI_REVIEWER_TRACE_SOURCE = "reviewer_operating_system_trace"
MANUAL_GATE_SOURCE = "explicit_human_decision"
MISSING_AI_REVIEWER_QUALITY_AUTHORIZATION = "missing_ai_reviewer_quality_authorization"
MISSING_CANONICAL_ARTIFACT_REBUILD_SOURCE = "missing_canonical_artifact_rebuild_source"
MISSING_DURABLE_EVIDENCE_REF = "missing_durable_evidence_ref"

STUDY_ROOT_SOAK_EVIDENCE_REFS: tuple[Path, ...] = (
    Path("artifacts/real_study_soak_matrix/evidence.json"),
)

PAPER_LINES: tuple[dict[str, Any], ...] = (
    {
        "paper_id": "nf-pitnet-003",
        "soak_role": "manual-finishing-to-ai-first-regression",
        "expected_evidence": "route_back_and_artifact_rebuild_trace",
    },
    {
        "paper_id": "dpcc-003",
        "soak_role": "large-real-world-primary-care-paper",
        "expected_evidence": "pre_draft_ai_reviewer_intervention_trace",
    },
    {
        "paper_id": "dpcc-004",
        "soak_role": "parallel-real-paper-generalization",
        "expected_evidence": "quality_authorization_and_manual_gate_trace",
    },
)

EVIDENCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "paper_id",
    "quality_authorization_source",
    "artifact_rebuild_source",
    "route_back_count",
    "route_back_reasons",
    "ai_reviewer_intervention_points",
    "mechanical_ready_overreach_detected",
    "final_blockers",
    "manual_gate",
)

DERIVED_ARTIFACT_AUTHORITY_MARKERS: tuple[str, ...] = (
    "current_package",
    "submission_minimal",
    "artifacts/final",
    "manuscript/current_package",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _contains_derived_artifact_marker(value: object) -> bool:
    text = _text(value)
    return any(marker in text for marker in DERIVED_ARTIFACT_AUTHORITY_MARKERS)


def _durable_refs(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            ref = _text(item.get("ref") or item.get("path") or item.get("uri"))
        else:
            ref = _text(item)
        if ref:
            refs.append(ref)
    return refs


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return _mapping(payload)


def _merge_stage_evidence(
    target: dict[str, list[str]],
    evidence: Mapping[str, Any],
) -> None:
    stage_evidence = _mapping(evidence.get("stage_evidence")) or evidence
    for stage in REAL_STUDY_SOAK_STAGES:
        refs = _durable_refs(stage_evidence.get(stage))
        if refs:
            target.setdefault(stage, []).extend(refs)


def _study_root_stage_evidence(
    study_roots: Iterable[str | Path] | None,
) -> tuple[dict[str, list[str]], list[str]]:
    stage_evidence: dict[str, list[str]] = {}
    evidence_sources: list[str] = []
    for root_value in study_roots or []:
        root = _path(root_value)
        for relative_ref in STUDY_ROOT_SOAK_EVIDENCE_REFS:
            evidence_path = root / relative_ref
            if not evidence_path.is_file():
                continue
            evidence_sources.append(str(evidence_path))
            _merge_stage_evidence(stage_evidence, _read_json_mapping(evidence_path))
    return stage_evidence, evidence_sources


def _runtime_snapshot_sections(
    *,
    runtime_snapshot_bundle: Mapping[str, Any] | None,
    operations_dashboard_summary: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    bundle = _mapping(runtime_snapshot_bundle)
    summary = _mapping(operations_dashboard_summary or bundle.get("operations_dashboard_summary"))
    return (
        _mapping(bundle.get("progress_snapshot")),
        _mapping(bundle.get("quality_snapshot")),
        _mapping(bundle.get("artifact_snapshot")),
        summary,
    )


def _dashboard_views(
    summary: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    return _mapping(summary.get("user_view")), _mapping(summary.get("maintainer_view"))


def _quality_authorization_source(
    quality_snapshot: Mapping[str, Any],
    maintainer_view: Mapping[str, Any],
) -> str:
    source = _text(quality_snapshot.get("quality_authorization_source"))
    if source:
        return source
    trace_complete = _bool(_mapping(maintainer_view.get("ai_reviewer_trace")).get("complete"))
    if trace_complete:
        return QUALITY_AUTHORIZATION_SOURCE
    return MISSING_AI_REVIEWER_QUALITY_AUTHORIZATION


def _artifact_rebuild_source(
    artifact_snapshot: Mapping[str, Any],
    maintainer_view: Mapping[str, Any],
) -> str:
    source = _text(artifact_snapshot.get("artifact_rebuild_source"))
    if source:
        return source
    canonical_source = _bool(artifact_snapshot.get("current_package_from_canonical_source"))
    if canonical_source is None:
        canonical_source = _bool(
            _mapping(maintainer_view.get("artifact_stale")).get("current_package_from_canonical_source")
        )
    if canonical_source is True:
        return CANONICAL_ARTIFACT_REBUILD_SOURCE
    return MISSING_CANONICAL_ARTIFACT_REBUILD_SOURCE


def _route_back_count(
    *,
    route_back_reasons: list[str],
    quality_snapshot: Mapping[str, Any],
    maintainer_view: Mapping[str, Any],
) -> int:
    if route_back_reasons:
        return len(route_back_reasons)
    snapshot_count = _int(quality_snapshot.get("route_back_count"))
    dashboard_count = _int(_mapping(maintainer_view.get("route_back")).get("count"))
    return max(snapshot_count, dashboard_count)


def _manual_gate(
    *,
    progress_snapshot: Mapping[str, Any],
    user_view: Mapping[str, Any],
) -> Mapping[str, Any]:
    manual_gate = _mapping(progress_snapshot.get("manual_gate"))
    if manual_gate:
        return manual_gate
    human_review_required = _bool(user_view.get("human_review_required"))
    if human_review_required is True:
        return {"required": True, "state": "human_review_required"}
    if human_review_required is False:
        return {"required": False, "state": "not_required"}
    return {}


def build_real_paper_ai_first_soak_contract() -> dict[str, Any]:
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "purpose": "measure_ai_first_flow_rework_and_quality",
        "manual_study_artifact_patch_allowed": False,
        "canonical_flow_only": True,
        "observational_evidence_only": True,
        "quality_gate_relaxation_allowed": False,
        "mechanical_ready_can_authorize_quality": False,
        "artifact_patch_targets": [],
        "paper_lines": [dict(line) for line in PAPER_LINES],
        "evidence_schema": {
            "required_fields": list(EVIDENCE_REQUIRED_FIELDS),
            "field_contracts": {
                "paper_id": "stable_real_paper_line_id",
                "quality_authorization_source": QUALITY_AUTHORIZATION_SOURCE,
                "artifact_rebuild_source": CANONICAL_ARTIFACT_REBUILD_SOURCE,
                "route_back_count": "count_of_quality_os_route_backs",
                "route_back_reasons": STRUCTURED_ROUTE_BACK_TAXONOMY,
                "ai_reviewer_intervention_points": AI_REVIEWER_TRACE_SOURCE,
                "mechanical_ready_overreach_detected": "boolean_quality_authority_overreach_flag",
                "final_blockers": "remaining_blockers_without_relaxing_gates",
                "manual_gate": MANUAL_GATE_SOURCE,
            },
        },
        "authority_requirements": {
            "quality_authorization_source": QUALITY_AUTHORIZATION_SOURCE,
            "artifact_rebuild_source": CANONICAL_ARTIFACT_REBUILD_SOURCE,
            "route_back_reasons": STRUCTURED_ROUTE_BACK_TAXONOMY,
            "ai_reviewer_intervention_points": AI_REVIEWER_TRACE_SOURCE,
            "manual_gate": MANUAL_GATE_SOURCE,
        },
        "forbidden_modes": [
            "manual_artifact_patch",
            "derived_artifact_as_quality_authority",
            "derived_artifact_as_rebuild_source",
            "mechanical_ready_as_quality_authority",
            "quality_gate_relaxation",
            "study_workspace_patch",
        ],
    }


def build_real_study_soak_matrix_evidence(
    *,
    evidence_map: Mapping[str, Any] | None = None,
    study_roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    stage_evidence, evidence_sources = _study_root_stage_evidence(study_roots)
    if evidence_map is not None:
        _merge_stage_evidence(stage_evidence, evidence_map)

    required_stages: list[dict[str, Any]] = []
    missing_stage_gaps: list[dict[str, str]] = []
    complete_count = 0
    for stage in REAL_STUDY_SOAK_STAGES:
        refs = stage_evidence.get(stage, [])
        is_complete = bool(refs)
        if is_complete:
            complete_count += 1
        else:
            missing_stage_gaps.append(
                {
                    "stage": stage,
                    "missing_reason": MISSING_DURABLE_EVIDENCE_REF,
                }
            )
        required_stages.append(
            {
                "stage": stage,
                "status": "complete" if is_complete else "missing",
                "evidence_refs": refs,
                "missing_reason": "" if is_complete else MISSING_DURABLE_EVIDENCE_REF,
            }
        )

    if complete_count == len(required_stages):
        overall_status = "complete"
    elif complete_count:
        overall_status = "partial"
    else:
        overall_status = "missing"

    return {
        "surface": MATRIX_EVIDENCE_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "overall_status": overall_status,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "required_stages": required_stages,
        "missing_stage_gaps": missing_stage_gaps,
        "evidence_sources": evidence_sources,
    }


def build_real_paper_ai_first_soak_observation(
    *,
    paper_id: str,
    quality_authorization_source: str,
    artifact_rebuild_source: str,
    route_back_reasons: list[str],
    ai_reviewer_intervention_points: list[str],
    mechanical_ready_overreach_detected: bool,
    final_blockers: list[str],
    manual_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": OBSERVATION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "paper_id": paper_id,
        "quality_authorization_source": quality_authorization_source,
        "artifact_rebuild_source": artifact_rebuild_source,
        "route_back_count": len(route_back_reasons),
        "route_back_reasons": list(route_back_reasons),
        "ai_reviewer_intervention_points": list(ai_reviewer_intervention_points),
        "mechanical_ready_overreach_detected": bool(mechanical_ready_overreach_detected),
        "final_blockers": list(final_blockers),
        "manual_gate": dict(manual_gate),
        "manual_study_artifact_patch_allowed": False,
        "canonical_flow_only": True,
        "observational_evidence_only": True,
        "artifact_write_paths": [],
    }


def build_real_paper_ai_first_soak_observation_from_runtime_snapshot(
    *,
    paper_id: str,
    operations_dashboard_summary: Mapping[str, Any] | None = None,
    runtime_snapshot_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress_snapshot, quality_snapshot, artifact_snapshot, summary = _runtime_snapshot_sections(
        runtime_snapshot_bundle=runtime_snapshot_bundle,
        operations_dashboard_summary=operations_dashboard_summary,
    )
    user_view, maintainer_view = _dashboard_views(summary)

    route_back_reasons = (
        _text_list(quality_snapshot.get("route_back_reasons"))
        or _text_list(_mapping(maintainer_view.get("route_back")).get("reasons"))
    )
    ai_reviewer_intervention_points = (
        _text_list(quality_snapshot.get("ai_reviewer_intervention_points"))
        or _text_list(_mapping(maintainer_view.get("ai_reviewer_trace")).get("intervention_points"))
    )

    observation = build_real_paper_ai_first_soak_observation(
        paper_id=paper_id,
        quality_authorization_source=_quality_authorization_source(quality_snapshot, maintainer_view),
        artifact_rebuild_source=_artifact_rebuild_source(artifact_snapshot, maintainer_view),
        route_back_reasons=route_back_reasons,
        ai_reviewer_intervention_points=ai_reviewer_intervention_points,
        mechanical_ready_overreach_detected=bool(
            quality_snapshot.get("mechanical_ready_overreach_detected")
        ),
        final_blockers=(
            _text_list(quality_snapshot.get("final_blockers"))
            or _text_list(progress_snapshot.get("current_blockers"))
            or _text_list(user_view.get("blockers"))
        ),
        manual_gate=_manual_gate(progress_snapshot=progress_snapshot, user_view=user_view),
    )
    observation["route_back_count"] = _route_back_count(
        route_back_reasons=route_back_reasons,
        quality_snapshot=quality_snapshot,
        maintainer_view=maintainer_view,
    )
    return observation


def validate_real_paper_ai_first_soak_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    allowed_paper_ids = {_text(line["paper_id"]) for line in PAPER_LINES}

    if observation.get("surface") != OBSERVATION_SURFACE:
        issues.append({"code": "observation_surface_invalid"})
    if observation.get("schema_version") != SCHEMA_VERSION:
        issues.append({"code": "schema_version_invalid"})

    for field in EVIDENCE_REQUIRED_FIELDS:
        if field not in observation:
            issues.append({"code": "required_field_missing", "field": field})

    paper_id = _text(observation.get("paper_id"))
    if paper_id not in allowed_paper_ids:
        issues.append({"code": "paper_id_not_in_soak_contract", "paper_id": paper_id})

    if observation.get("manual_study_artifact_patch_allowed") is not False:
        issues.append({"code": "manual_artifact_patching_enabled"})
    if observation.get("canonical_flow_only") is not True:
        issues.append({"code": "canonical_flow_not_required"})
    if observation.get("observational_evidence_only") is not True:
        issues.append({"code": "observational_evidence_not_enforced"})
    if _list(observation.get("artifact_write_paths")):
        issues.append({"code": "artifact_write_path_present"})

    if _contains_derived_artifact_marker(observation.get("quality_authorization_source")):
        issues.append({"code": "quality_authority_uses_derived_artifact"})
    if _text(observation.get("quality_authorization_source")) in {
        "",
        MISSING_AI_REVIEWER_QUALITY_AUTHORIZATION,
    }:
        issues.append({"code": "quality_authorization_source_missing"})
    if _text(observation.get("artifact_rebuild_source")) != CANONICAL_ARTIFACT_REBUILD_SOURCE:
        issues.append({"code": "artifact_rebuild_source_not_canonical"})

    route_back_reasons = _list(observation.get("route_back_reasons"))
    if not route_back_reasons:
        issues.append({"code": "route_back_reasons_missing"})
    elif observation.get("route_back_count") != len(route_back_reasons):
        issues.append({"code": "route_back_count_mismatch"})

    if not _list(observation.get("ai_reviewer_intervention_points")):
        issues.append({"code": "ai_reviewer_intervention_points_missing"})
    if not _mapping(observation.get("manual_gate")):
        issues.append({"code": "manual_gate_missing"})

    return {
        "surface": "real_paper_ai_first_soak_observation_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def build_paper_soak_memory_apply_proof(
    *,
    opl_attempt: Mapping[str, Any],
    sidecar_task: Mapping[str, Any],
    typed_closeout: Mapping[str, Any],
    mas_receipt: Mapping[str, Any],
    progress_delta: Mapping[str, Any] | None = None,
    human_gate: Mapping[str, Any] | None = None,
    stop_loss: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage_closeout_ok = _text(typed_closeout.get("surface")) == "stage_memory_closeout_packet"
    receipt_ok = (
        _text(mas_receipt.get("surface")) == "memory_write_router_receipt"
        and _text(mas_receipt.get("status")) in {"applied", "blocked", "dry_run"}
    )
    attempt_ref = _text(opl_attempt.get("attempt_id"))
    sidecar_task_id = _text(sidecar_task.get("task_id"))
    progress = _mapping(progress_delta)
    gate = _mapping(human_gate)
    stop = _mapping(stop_loss)
    proof_steps = [
        _proof_step(
            "opl_attempt",
            bool(attempt_ref),
            attempt_ref or "missing_opl_attempt_id",
            "OPL attempt is a provider/runtime receipt ref only.",
        ),
        _proof_step(
            "codex_or_domain_sidecar",
            bool(sidecar_task_id),
            sidecar_task_id or "missing_sidecar_task_id",
            "Sidecar task carries refs to MAS owner surface.",
        ),
        _proof_step(
            "typed_stage_closeout",
            stage_closeout_ok,
            _text(typed_closeout.get("idempotency_key")) or "missing_closeout_idempotency_key",
            "Stage closeout proposes typed writes; it is not a publication verdict.",
        ),
        _proof_step(
            "mas_memory_router_receipt",
            receipt_ok,
            _text(mas_receipt.get("idempotency_key")) or "missing_mas_receipt_idempotency_key",
            "MAS accepts, rejects, or blocks writeback through owner receipt.",
        ),
        _proof_step(
            "progress_delta_or_guard",
            bool(progress or gate or stop),
            _text(progress.get("delta_id") or gate.get("gate_id") or stop.get("decision_id"))
            or "missing_progress_delta_human_gate_or_stop_loss",
            "Proof must end in progress delta, human gate, or stop-loss.",
        ),
    ]
    complete = all(step["status"] == "present" for step in proof_steps)
    return {
        "surface": PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _text(sidecar_task.get("study_id") or _mapping(sidecar_task.get("payload")).get("study_id") or "unknown"),
        "stage": _text(typed_closeout.get("stage") or "all"),
        "input_refs": _paper_soak_memory_source_refs(
            opl_attempt=opl_attempt,
            sidecar_task=sidecar_task,
            typed_closeout=typed_closeout,
            mas_receipt=mas_receipt,
            progress_delta=progress,
            human_gate=gate,
            stop_loss=stop,
        ),
        "source_fingerprint": _text(mas_receipt.get("source_fingerprint")) or _text(typed_closeout.get("source_fingerprint")),
        "idempotency_key": _text(mas_receipt.get("idempotency_key")) or _text(typed_closeout.get("idempotency_key")),
        "proof_mode": "read_only_or_guarded_apply",
        "overall_status": "complete" if complete else "partial",
        "proof_steps": proof_steps,
        "source_refs": _paper_soak_memory_source_refs(
            opl_attempt=opl_attempt,
            sidecar_task=sidecar_task,
            typed_closeout=typed_closeout,
            mas_receipt=mas_receipt,
            progress_delta=progress,
            human_gate=gate,
            stop_loss=stop,
        ),
        "progress_delta": dict(progress),
        "human_gate": dict(gate),
        "stop_loss": dict(stop),
        "authority_boundary": {
            "opl_role": "attempt_transport_and_refs_only",
            "mas_role": "memory_write_router_and_medical_truth_owner",
            "can_write_real_paper_package": False,
            "can_authorize_publication_quality": False,
            "can_replace_publication_gate": False,
        },
    }


def _proof_step(step: str, present: bool, ref: str, role: str) -> dict[str, Any]:
    return {
        "step": step,
        "status": "present" if present else "missing",
        "ref": ref,
        "role": role,
    }


def _paper_soak_memory_source_refs(
    *,
    opl_attempt: Mapping[str, Any],
    sidecar_task: Mapping[str, Any],
    typed_closeout: Mapping[str, Any],
    mas_receipt: Mapping[str, Any],
    progress_delta: Mapping[str, Any],
    human_gate: Mapping[str, Any],
    stop_loss: Mapping[str, Any],
) -> list[dict[str, str]]:
    candidates = (
        ("opl_attempt", opl_attempt.get("attempt_id") or opl_attempt.get("attempt_ref")),
        ("sidecar_task", sidecar_task.get("task_id") or sidecar_task.get("task_ref")),
        ("typed_stage_closeout", typed_closeout.get("idempotency_key") or typed_closeout.get("artifact_path")),
        ("mas_memory_router_receipt", mas_receipt.get("receipt_ref") or mas_receipt.get("idempotency_key")),
        ("progress_delta", progress_delta.get("delta_id") or progress_delta.get("ref")),
        ("human_gate", human_gate.get("gate_id") or human_gate.get("ref")),
        ("stop_loss", stop_loss.get("decision_id") or stop_loss.get("ref")),
    )
    return [
        {"role": role, "ref": _text(ref)}
        for role, ref in candidates
        if _text(ref)
    ]
