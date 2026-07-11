from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.publication_eval_latest import (
    canonicalize_ai_reviewer_publication_eval_record,
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord

from med_autoscience.controllers import (
    ai_reviewer_publication_eval_workflow,
    domain_status_projection,
    paper_authority_migration,
)
from .common import _mapping, _optional_text
from .planning_helpers import (
    _ai_reviewer_record_authoring_target_payload,
    _compact_current_work_unit,
    _normalized_required_currentness_refs,
    _payload_currentness_guard_result,
    _payload_record,
    _record_materialization_requires_precheck,
    _record_payload_missing_blocker,
    _record_request_kind,
    _refresh_record_payload_target_metadata,
    _refs_from_record_and_request,
    _request_with_normalized_input_refs,
    _write_authoring_target_output,
)
from .record_materialization import (
    AI_REVIEWER_RESPONSE_RECORD_DIR,
    AI_REVIEWER_RESPONSE_RECORD_SURFACE,
    CONTROLLER_DECISIONS_LATEST_SURFACE,
    PUBLICATION_EVAL_LATEST_SURFACE,
    _materialize_ai_reviewer_publication_eval_record,
    _normalize_publication_eval_record,
)
from .input_contract import (
    ai_reviewer_request_path,
    read_ai_reviewer_request,
)
from med_autoscience.controllers.stage_outcome_authority.action_execution import (
    ai_reviewer_request_refs,
)
from med_autoscience.controllers.study_progress import projection as study_progress_projection
from med_autoscience.controllers.study_runtime_resolution import _execution_payload, _resolve_study

__all__ = [
    "materialize_ai_reviewer_publication_eval",
    "materialize_ai_reviewer_publication_eval_record",
    "plan_ai_reviewer_publication_eval_record_materialization",
]


def _mapping_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise TypeError("study runtime status must be a mapping or expose to_dict()")


def _resolved_study_root(status_payload: Mapping[str, Any]) -> Path:
    raw_study_root = _optional_text(status_payload.get("study_root"))
    if raw_study_root is None:
        raise ValueError("Unable to resolve study_root for AI reviewer publication eval")
    return Path(raw_study_root).expanduser().resolve()


def _record_only_status_payload(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    execution = _execution_payload(study_payload)
    return {
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": _optional_text(execution.get("quest_id")) or resolved_study_id,
    }


def _precheck_status_payload(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
) -> dict[str, Any]:
    return _mapping_payload(
        study_progress_projection.read_study_progress(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    )


def plan_ai_reviewer_publication_eval_record_materialization(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
    source: str,
    record: PublicationEvalRecord | dict[str, Any] | None = None,
    expected_owner: str | None = None,
    expected_action_type: str | None = None,
    expected_work_unit_id: str | None = None,
    expected_work_unit_fingerprint: str | None = None,
    authoring_target_output: Path | None = None,
    build_production_trace: bool = False,
) -> dict[str, Any]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")

    status_payload = _precheck_status_payload(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        entry_mode=entry_mode,
    )
    resolved_study_root = _resolved_study_root(status_payload)
    resolved_study_id = _optional_text(status_payload.get("study_id")) or resolved_study_root.name
    request = _request_with_normalized_input_refs(
        study_root=resolved_study_root,
        request=read_ai_reviewer_request(study_root=resolved_study_root) or {},
    )
    lifecycle = _mapping(request.get("record_requirements"))
    request_required_currentness_refs = [
        str(item).strip()
        for item in lifecycle.get("required_currentness_refs") or []
        if str(item).strip()
    ]
    required_refs = ai_reviewer_request_refs.required_refs(request)
    optional_refs = ai_reviewer_request_refs.optional_refs(request)
    required_currentness_refs = _normalized_required_currentness_refs(
        request_refs=request_required_currentness_refs,
        required_refs=required_refs,
    )
    expected_record_glob = str((resolved_study_root / AI_REVIEWER_RESPONSE_RECORD_DIR).resolve() / "*_publication_eval_record.json")
    current_work_unit = _compact_current_work_unit(status_payload)
    expected_identity = {
        "owner": _optional_text(expected_owner),
        "action_type": _optional_text(expected_action_type),
        "work_unit_id": _optional_text(expected_work_unit_id),
        "work_unit_fingerprint": _optional_text(expected_work_unit_fingerprint),
    }
    identity_guard = _identity_guard_result(
        current_work_unit=current_work_unit,
        expected_identity=expected_identity,
    )
    record_payload = record.to_dict() if isinstance(record, PublicationEvalRecord) else record
    record_payload, payload_target_metadata_refresh = _refresh_record_payload_target_metadata(
        record=record_payload,
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
        enabled=entry_mode == "owner_consumption_payload_guard",
    )
    payload_guard = _payload_currentness_guard_result(
        record=record_payload,
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
    )
    record_schema_guard = _record_schema_guard_result(
        study_root=resolved_study_root,
        record=record_payload,
        enabled=payload_guard.get("matched") is True,
        build_production_trace=build_production_trace,
    )
    status = (
        "blocked"
        if False
        in (
            identity_guard.get("matched"),
            payload_guard.get("matched"),
            record_schema_guard.get("matched"),
        )
        else "dry_run"
    )
    authoring_target_payload = _ai_reviewer_record_authoring_target_payload(
        record=record_payload,
        status_payload=status_payload,
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
    )
    written_files: list[str] = []
    authoring_target_output_ref: str | None = None
    if authoring_target_output is not None:
        output_ref = _write_authoring_target_output(
            output_path=authoring_target_output,
            study_root=resolved_study_root,
            payload=authoring_target_payload,
        )
        authoring_target_output_ref = str(output_ref)
        written_files.append(str(output_ref))
    result = {
        "status": "dry_run",
        "dry_run": True,
        "observe_only": True,
        "source": source,
        "study_id": resolved_study_id,
        "quest_id": _optional_text(status_payload.get("quest_id"))
        or _optional_text(request.get("quest_id"))
        or resolved_study_id,
        "study_root": str(resolved_study_root),
        "owner": "ai_reviewer",
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "owner_callable_mode": (
            "record_only_build_production_trace"
            if build_production_trace
            else "record_only_raw_payload"
        ),
        "owner_callable_precheck": {
            "required_payload_field": "record_payload",
            "payload_may_be_absent_for_precheck": True,
            "payload_will_not_be_materialized": True,
            "payload_currentness_guard_enabled": payload_guard.get("enabled") is True,
            "payload_target_metadata_refresh_enabled": payload_target_metadata_refresh.get("enabled") is True,
        },
        "current_work_unit": current_work_unit,
        "expected_current_work_unit": expected_identity if any(expected_identity.values()) else None,
        "identity_guard": identity_guard,
        "payload_guard": payload_guard,
        "record_schema_guard": record_schema_guard,
        "payload_target_metadata_refresh": payload_target_metadata_refresh,
        "authoring_target": {
            "surface": "ai_reviewer_record_payload_authoring_target",
            "output_ref": authoring_target_output_ref,
            "record_payload_preserved": authoring_target_payload.get("record_payload")
            == _mapping(_mapping(record_payload).get("record_payload")),
            "record_payload_prefilled_by_mas": False,
            "writes_authority_surfaces": False,
        },
        "request": {
            "request_path": str(ai_reviewer_request_path(study_root=resolved_study_root)),
            "request_kind": _record_request_kind(request),
            "request_owner": _optional_text(request.get("request_owner")),
            "lifecycle_state": _optional_text(lifecycle.get("state")),
            "blocked_reason": _optional_text(lifecycle.get("blocked_reason")),
            "stale_record_ref": _optional_text(lifecycle.get("stale_record_ref"))
            or _optional_text(request.get("publication_eval_record_ref")),
        },
        "required_input_refs": {
            surface: ref for surface, ref in required_refs.items() if ref is not None
        },
        "optional_input_refs": {
            surface: ref for surface, ref in optional_refs.items() if ref is not None
        },
        "required_currentness_refs": required_currentness_refs,
        "required_currentness_refs_source": "record_requirements"
        if request_required_currentness_refs
        else "request_input_refs",
        "expected_write_surfaces": [AI_REVIEWER_RESPONSE_RECORD_SURFACE],
        "expected_record_glob": expected_record_glob,
        "forbidden_surfaces": [
            PUBLICATION_EVAL_LATEST_SURFACE,
            CONTROLLER_DECISIONS_LATEST_SURFACE,
            "owner_receipts/**",
            "typed_blockers/**",
            "human_gates/**",
            "runtime_queues/**",
            "provider_attempts/**",
            "provider_leases/**",
            "provider_admission/**",
        ],
        "authority_boundary": {
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "record_only_surface": True,
        },
        "publication_eval_surface": "not_written",
        "publication_eval_record_surface": "not_written",
        "written_files": written_files,
        "next_required_actions": [
            "author_ai_reviewer_record_payload_against_current_input_refs",
            (
                "rerun_publication_materialize_ai_reviewer_record_with_build_production_trace_without_dry_run"
                if build_production_trace
                else "rerun_publication_materialize_ai_reviewer_record_without_dry_run"
            ),
            "consume_current_record_through_mas_owner_path",
        ],
    }
    if status == "blocked":
        result["status"] = "blocked"
        result["blocked_reason"] = (
            _optional_text(identity_guard.get("reason"))
            if identity_guard.get("matched") is False
            else (
                _optional_text(payload_guard.get("reason"))
                if payload_guard.get("matched") is False
                else _optional_text(record_schema_guard.get("reason"))
            )
        ) or "current_owner_identity_guard_failed"
        result["publication_eval_surface"] = "not_written"
        result["publication_eval_record_surface"] = "not_written"
    return result


def _record_schema_guard_result(
    *,
    study_root: Path,
    record: Mapping[str, Any] | None,
    enabled: bool,
    build_production_trace: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "enabled": False,
            "matched": None,
            "reason": None,
            "error": None,
        }
    if record is None:
        return {
            "enabled": False,
            "matched": None,
            "reason": None,
            "error": None,
        }
    record_payload = _payload_record(record)
    if "schema_version" not in record_payload:
        return {
            "enabled": False,
            "matched": None,
            "reason": None,
            "error": None,
        }
    try:
        guarded_record = (
            _record_with_production_trace(study_root=study_root, record=dict(record))
            if build_production_trace
            else record_payload
        )
        canonicalize_ai_reviewer_publication_eval_record(
            _normalize_publication_eval_record(guarded_record)
        )
    except (TypeError, ValueError) as exc:
        return {
            "enabled": True,
            "matched": False,
            "reason": "record_payload_schema_invalid",
            "error": str(exc),
        }
    return {
        "enabled": True,
        "matched": True,
        "reason": None,
        "error": None,
    }


def _identity_guard_result(
    *,
    current_work_unit: Mapping[str, Any],
    expected_identity: Mapping[str, str | None],
) -> dict[str, Any]:
    expected = {key: value for key, value in expected_identity.items() if value is not None}
    if not expected:
        return {"enabled": False, "matched": None, "reason": None, "mismatches": []}
    mismatches: list[dict[str, str | None]] = []
    missing_observed: list[str] = []
    for key, expected_value in expected.items():
        observed_value = _optional_text(current_work_unit.get(key))
        if observed_value is None:
            missing_observed.append(key)
            continue
        if observed_value != expected_value:
            mismatches.append({"field": key, "expected": expected_value, "observed": observed_value})
    if mismatches:
        return {
            "enabled": True,
            "matched": False,
            "reason": "current_owner_identity_mismatch",
            "mismatches": mismatches,
            "missing_observed_fields": missing_observed,
        }
    if missing_observed:
        return {
            "enabled": True,
            "matched": False,
            "reason": "current_owner_identity_unavailable_for_guard",
            "mismatches": [],
            "missing_observed_fields": missing_observed,
        }
    return {
        "enabled": True,
        "matched": True,
        "reason": None,
        "mismatches": [],
        "missing_observed_fields": [],
    }


def _record_with_production_trace(
    *,
    study_root: Path,
    record: PublicationEvalRecord | dict[str, Any],
) -> dict[str, Any]:
    record_payload = _payload_record(record)
    required_refs, optional_refs = _refs_from_record_and_request(
        study_root=study_root,
        record_payload=record_payload,
    )
    missing_refs = [
        surface
        for surface in (
            "manuscript",
            "evidence_ledger",
            "review_ledger",
            "study_charter",
        )
        if required_refs.get(surface) is None
    ]
    if missing_refs:
        raise ValueError("AI reviewer publication eval record production missing input refs: " + ", ".join(missing_refs))
    additional_refs = {
        surface: ref
        for surface, ref in {**required_refs, **optional_refs}.items()
        if surface not in {"manuscript", "evidence_ledger", "review_ledger", "study_charter"}
        and ref is not None
    }
    return ai_reviewer_publication_eval_workflow.build_ai_reviewer_publication_eval_record_with_workflow_trace(
        study_root=study_root,
        manuscript_ref=required_refs["manuscript"] or "",
        evidence_ref=required_refs["evidence_ledger"] or "",
        review_ref=required_refs["review_ledger"] or "",
        charter_ref=required_refs["study_charter"] or "",
        record=record_payload,
        additional_refs=additional_refs,
        workflow_currentness_mode="request_bound_ai_reviewer_record",
    )


def materialize_ai_reviewer_publication_eval_record(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
    record: PublicationEvalRecord | dict[str, Any],
    source: str,
    build_production_trace: bool = False,
) -> dict[str, Any]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")

    requires_precheck = _record_materialization_requires_precheck(
        record=record,
        entry_mode=entry_mode,
    )
    if requires_precheck:
        guard = plan_ai_reviewer_publication_eval_record_materialization(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
            source=source,
            record=record,
            build_production_trace=build_production_trace,
        )
        if _optional_text(guard.get("status")) == "blocked":
            return guard

    status_payload = _record_only_status_payload(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    resolved_study_root = _resolved_study_root(status_payload)
    record_input_payload = record.to_dict() if isinstance(record, PublicationEvalRecord) else dict(record)
    missing_payload_blocker = _record_payload_missing_blocker(
        payload=record_input_payload,
        status_payload=status_payload,
        source=source,
    )
    if missing_payload_blocker is not None:
        return missing_payload_blocker
    if build_production_trace:
        record = _record_with_production_trace(
            study_root=resolved_study_root,
            record=record,
        )
    else:
        record = _payload_record(record)
    normalized_record = canonicalize_ai_reviewer_publication_eval_record(
        _normalize_publication_eval_record(record)
    )
    record_path = _materialize_ai_reviewer_publication_eval_record(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    record_payload = normalized_record.to_dict()
    resolved_study_id = (
        _optional_text(status_payload.get("study_id"))
        or _optional_text(record_payload.get("study_id"))
        or resolved_study_root.name
    )
    return {
        "status": "materialized",
        "source": source,
        "study_id": resolved_study_id,
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(record_payload.get("quest_id")),
        "eval_id": record_payload["eval_id"],
        "publication_eval_record_ref": str(record_path),
        "publication_eval_record_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "not_written",
    }


def materialize_ai_reviewer_publication_eval(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
    record: PublicationEvalRecord | dict[str, Any],
    source: str,
    build_production_trace: bool = False,
) -> dict[str, Any]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")

    status_payload = _mapping_payload(
        domain_status_projection.progress_projection(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
        )
    )
    resolved_study_root = _resolved_study_root(status_payload)
    if build_production_trace:
        record = _record_with_production_trace(
            study_root=resolved_study_root,
            record=record,
        )
    normalized_record = canonicalize_ai_reviewer_publication_eval_record(
        _normalize_publication_eval_record(record)
    )
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    cutover_receipt = paper_authority_migration.mark_cutover_new_mas_authority_established(
        study_root=resolved_study_root,
        publication_eval_ref=materialized["artifact_path"],
        eval_id=materialized["eval_id"],
    )
    cutover_ref = (
        str(paper_authority_migration.paper_authority_cutover_latest_path(study_root=resolved_study_root))
        if cutover_receipt is not None
        else None
    )
    record_path = _materialize_ai_reviewer_publication_eval_record(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    record_payload = normalized_record.to_dict()
    resolved_study_id = (
        _optional_text(status_payload.get("study_id"))
        or _optional_text(record_payload.get("study_id"))
        or resolved_study_root.name
    )

    return {
        "status": "materialized",
        "source": source,
        "study_id": resolved_study_id,
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(record_payload.get("quest_id")),
        "eval_id": materialized["eval_id"],
        "artifact_path": materialized["artifact_path"],
        "publication_eval_record_ref": str(record_path),
        "publication_eval_record_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
        "paper_authority_cutover_status": _optional_text((cutover_receipt or {}).get("status")),
        "paper_authority_cutover_ref": cutover_ref,
    }
