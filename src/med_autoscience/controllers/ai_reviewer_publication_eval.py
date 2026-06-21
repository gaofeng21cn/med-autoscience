from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.publication_eval_latest import (
    canonicalize_ai_reviewer_publication_eval_record,
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord
from med_autoscience.medical_prose_review import stable_medical_prose_review_path

from . import ai_reviewer_publication_eval_workflow, domain_status_projection
from .domain_owner_action_dispatch_parts.action_execution import ai_reviewer_request_refs
from .domain_action_request_lifecycle import read_ai_reviewer_request, stable_ai_reviewer_request_path
from .study_progress_parts import projection as study_progress_projection
from .study_runtime_resolution import _execution_payload, _resolve_study

__all__ = [
    "materialize_ai_reviewer_publication_eval",
    "materialize_ai_reviewer_publication_eval_record",
    "plan_ai_reviewer_publication_eval_record_materialization",
]


AI_REVIEWER_RESPONSE_RECORD_DIR = Path("artifacts") / "publication_eval" / "ai_reviewer_responses"
AI_REVIEWER_RESPONSE_RECORD_SURFACE = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
PUBLICATION_EVAL_LATEST_SURFACE = "artifacts/publication_eval/latest.json"
CONTROLLER_DECISIONS_LATEST_SURFACE = "artifacts/controller_decisions/latest.json"


def _mapping_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise TypeError("study runtime status must be a mapping or expose to_dict()")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


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


def _record_timestamp(record_payload: Mapping[str, Any]) -> str:
    emitted_at = _optional_text(record_payload.get("emitted_at"))
    if emitted_at:
        try:
            parsed = datetime.fromisoformat(emitted_at.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _materialize_ai_reviewer_publication_eval_record(
    *,
    study_root: Path,
    record: PublicationEvalRecord,
) -> Path:
    payload = record.to_dict()
    record_dir = study_root / AI_REVIEWER_RESPONSE_RECORD_DIR
    record_dir.mkdir(parents=True, exist_ok=True)
    record_path = record_dir / f"{_record_timestamp(payload)}_publication_eval_record.json"
    record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record_path.resolve()


def _normalize_publication_eval_record(record: PublicationEvalRecord | dict[str, Any]) -> PublicationEvalRecord:
    return record if isinstance(record, PublicationEvalRecord) else PublicationEvalRecord.from_payload(record)


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"AI reviewer request must be a JSON object: {path}")
    return dict(payload)


def _payload_record(value: PublicationEvalRecord | dict[str, Any]) -> dict[str, Any]:
    payload = value.to_dict() if isinstance(value, PublicationEvalRecord) else dict(value)
    if _optional_text(payload.get("surface")) == "ai_reviewer_record_payload_authoring_target":
        record_payload = _mapping(payload.get("record_payload"))
        if not record_payload:
            raise ValueError("AI reviewer record payload authoring target missing record_payload")
        return record_payload
    return payload


def _record_payload_missing_blocker(
    *,
    payload: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    if _optional_text(payload.get("surface")) != "ai_reviewer_record_payload_authoring_target":
        return None
    if _mapping(payload.get("record_payload")):
        return None
    study_id = (
        _optional_text(status_payload.get("study_id"))
        or _optional_text(payload.get("study_id"))
        or _optional_text(Path(str(status_payload.get("study_root") or "")).name)
    )
    return {
        "status": "blocked",
        "blocked_reason": "ai_reviewer_record_payload_missing",
        "source": source,
        "study_id": study_id,
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(payload.get("quest_id")),
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "not_written",
        "publication_eval_record_surface": "not_written",
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "owner_callable_payload_ref": _optional_text(payload.get("owner_callable_payload_ref")),
        "payload_surface": "ai_reviewer_record_payload_authoring_target",
        "required_payload_field": "record_payload",
        "next_owner": "ai_reviewer",
        "next_required_actions": [
            _optional_text(payload.get("request_kind")) or "produce_ai_reviewer_publication_eval_record",
            "fill_record_payload_with_ai_reviewer_publication_eval_record",
            "rerun_publication_materialize_ai_reviewer_record_build_production_trace",
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
    }


def _refs_from_record_and_request(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    request = _read_json_object(request_path) if request_path.exists() else {}
    required_refs = ai_reviewer_request_refs.required_refs(request)
    optional_refs = ai_reviewer_request_refs.optional_refs(request)
    input_bundle = _mapping(_mapping(record_payload.get("reviewer_operating_system")).get("input_bundle"))
    for surface in (
        "manuscript",
        "evidence_ledger",
        "review_ledger",
        "study_charter",
        "medical_manuscript_blueprint",
        "claim_evidence_map",
        "medical_prose_review",
        "publication_gate_projection",
    ):
        if required_refs.get(surface) is None:
            required_refs[surface] = _optional_text(input_bundle.get(surface))
    for surface in ("reporting_guideline", "calibration_refs"):
        if optional_refs.get(surface) is None:
            optional_refs[surface] = _optional_text(input_bundle.get(surface))
    stable_prose_review = stable_medical_prose_review_path(study_root=study_root)
    if stable_prose_review.exists():
        required_refs["medical_prose_review"] = str(stable_prose_review)
    return required_refs, optional_refs


def _compact_current_work_unit(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(status_payload.get("current_work_unit"))
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(current_work_unit.get("typed_blocker"))
    compact = {
        "status": _optional_text(current_work_unit.get("status")),
        "owner": _optional_text(current_work_unit.get("owner")),
        "action_type": _optional_text(current_work_unit.get("action_type")),
        "work_unit_id": _optional_text(current_work_unit.get("work_unit_id")),
        "work_unit_fingerprint": _optional_text(current_work_unit.get("work_unit_fingerprint"))
        or _optional_text(current_work_unit.get("action_fingerprint")),
        "phase": _optional_text(current_work_unit.get("phase")),
        "typed_blocker": {
            "reason": _optional_text(typed_blocker.get("reason"))
            or _optional_text(typed_blocker.get("blocked_reason"))
            or _optional_text(typed_blocker.get("blocker_id")),
            "ref": _optional_text(typed_blocker.get("ref")) or _optional_text(typed_blocker.get("typed_blocker_ref")),
        }
        if typed_blocker
        else None,
    }
    if any(compact.get(key) for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint")):
        return compact
    return _compact_current_work_unit_from_intervention_lane(status_payload)


def _compact_current_work_unit_from_intervention_lane(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    lane = _mapping(status_payload.get("intervention_lane"))
    checklist = _mapping(lane.get("route_back_checklist"))
    recovery_identity = _recovery_obligation_identity(lane)
    blockers = [
        str(item).strip()
        for item in checklist.get("blockers") or []
        if str(item).strip()
    ]
    blocker_reason = next((item for item in blockers if item.startswith("ai_reviewer_record_")), None)
    return {
        "status": "typed_blocker" if blocker_reason else _optional_text(lane.get("severity")),
        "owner": _optional_text(lane.get("authority_owner")),
        "action_type": recovery_identity.get("action_type"),
        "work_unit_id": recovery_identity.get("work_unit_id"),
        "work_unit_fingerprint": recovery_identity.get("work_unit_fingerprint"),
        "phase": _optional_text(lane.get("paper_recovery_phase")),
        "typed_blocker": {
            "reason": blocker_reason,
            "ref": None,
        }
        if blocker_reason
        else None,
    }


def _recovery_obligation_identity(lane: Mapping[str, Any]) -> dict[str, str | None]:
    raw = _optional_text(lane.get("recovery_obligation_id"))
    if raw is None:
        return {"action_type": None, "work_unit_id": None, "work_unit_fingerprint": None}
    prefix = "paper-recovery::"
    if not raw.startswith(prefix):
        return {"action_type": None, "work_unit_id": None, "work_unit_fingerprint": None}
    parts = raw[len(prefix) :].split("::", 3)
    if len(parts) != 4:
        return {"action_type": None, "work_unit_id": None, "work_unit_fingerprint": None}
    return {
        "action_type": _optional_text(parts[1]),
        "work_unit_id": _optional_text(parts[2]),
        "work_unit_fingerprint": _optional_text(parts[3]),
    }


def _record_request_kind(request: Mapping[str, Any]) -> str | None:
    lifecycle = _mapping(request.get("request_lifecycle"))
    return (
        _optional_text(request.get("request_kind"))
        or _optional_text(lifecycle.get("work_unit_id"))
        or _optional_text(lifecycle.get("blocked_reason"))
    )


def _text_refs(value: object) -> list[str]:
    if isinstance(value, Mapping):
        values = value.values()
    elif isinstance(value, list | tuple | set):
        values = value
    else:
        return []
    return [text for item in values if (text := _optional_text(item)) is not None]


def _payload_currentness_guard_result(
    *,
    record: Mapping[str, Any] | None,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    required_currentness_refs: list[str],
) -> dict[str, Any]:
    if record is None:
        return {
            "enabled": False,
            "matched": None,
            "reason": None,
            "mismatches": [],
            "missing_observed_fields": [],
        }

    record_payload = _payload_record(record)
    payload_required_refs = {
        surface: ref
        for surface, ref in {
            key: _optional_text(value)
            for key, value in _mapping(record.get("required_input_refs")).items()
        }.items()
        if ref is not None
    }
    input_bundle = _mapping(_mapping(record_payload.get("reviewer_operating_system")).get("input_bundle"))
    observed_input_refs = {
        surface: ref
        for surface, ref in {
            **{key: _optional_text(value) for key, value in input_bundle.items()},
            **payload_required_refs,
        }.items()
        if ref is not None
    }
    expected_input_refs = {
        surface: ref for surface, ref in required_refs.items() if ref is not None
    }
    mismatches: list[dict[str, str | None]] = []
    missing_observed: list[str] = []
    for surface, expected_ref in expected_input_refs.items():
        observed_ref = observed_input_refs.get(surface)
        if observed_ref is None:
            missing_observed.append(f"required_input_refs.{surface}")
            continue
        if observed_ref != expected_ref:
            mismatches.append({"surface": surface, "expected": expected_ref, "observed": observed_ref})

    expected_required_ref_values = {ref for ref in expected_input_refs.values() if ref is not None}
    observed_currentness_refs = set(_text_refs(record.get("required_currentness_refs")))
    observed_currentness_refs.update(observed_input_refs.values())
    for expected_ref in required_currentness_refs:
        if expected_ref in expected_required_ref_values:
            continue
        if expected_ref not in observed_currentness_refs:
            missing_observed.append(f"required_currentness_refs:{expected_ref}")

    request_lifecycle = _mapping(request.get("request_lifecycle"))
    expected_stale_record_ref = _optional_text(request_lifecycle.get("stale_record_ref")) or _optional_text(
        request.get("publication_eval_record_ref")
    )
    observed_stale_record_ref = _optional_text(record.get("stale_record_ref"))
    if expected_stale_record_ref and observed_stale_record_ref and observed_stale_record_ref != expected_stale_record_ref:
        mismatches.append(
            {
                "surface": "stale_record_ref",
                "expected": expected_stale_record_ref,
                "observed": observed_stale_record_ref,
            }
        )

    common = {
        "enabled": True,
        "mismatches": mismatches,
        "missing_observed_fields": missing_observed,
        "expected_input_refs": expected_input_refs,
        "observed_input_refs": observed_input_refs,
        "expected_required_currentness_refs": required_currentness_refs,
        "observed_currentness_refs": sorted(observed_currentness_refs),
    }
    if mismatches:
        return {
            **common,
            "matched": False,
            "reason": "payload_currentness_mismatch",
        }
    if missing_observed:
        return {
            **common,
            "matched": False,
            "reason": "payload_currentness_refs_unavailable_for_guard",
        }
    return {
        **common,
        "matched": True,
        "reason": None,
    }


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
    request = read_ai_reviewer_request(study_root=resolved_study_root) or {}
    lifecycle = _mapping(request.get("request_lifecycle"))
    request_required_currentness_refs = [
        str(item).strip()
        for item in lifecycle.get("required_currentness_refs") or []
        if str(item).strip()
    ]
    required_refs = ai_reviewer_request_refs.required_refs(request)
    optional_refs = ai_reviewer_request_refs.optional_refs(request)
    required_currentness_refs = request_required_currentness_refs or [
        ref for ref in required_refs.values() if ref is not None
    ]
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
    payload_guard = _payload_currentness_guard_result(
        record=record_payload,
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
    )
    status = "blocked" if False in (identity_guard.get("matched"), payload_guard.get("matched")) else "dry_run"
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
        "owner_callable_mode": "record_only_build_production_trace",
        "owner_callable_precheck": {
            "required_payload_field": "record_payload",
            "payload_may_be_absent_for_precheck": True,
            "payload_will_not_be_materialized": True,
            "payload_currentness_guard_enabled": payload_guard.get("enabled") is True,
        },
        "current_work_unit": current_work_unit,
        "expected_current_work_unit": expected_identity if any(expected_identity.values()) else None,
        "identity_guard": identity_guard,
        "payload_guard": payload_guard,
        "request": {
            "request_path": str(stable_ai_reviewer_request_path(study_root=resolved_study_root)),
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
        "required_currentness_refs_source": "request_lifecycle"
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
        "written_files": [],
        "next_required_actions": [
            "author_ai_reviewer_record_payload_against_current_input_refs",
            "rerun_publication_materialize_ai_reviewer_record_with_build_production_trace_without_dry_run",
            "consume_current_record_through_mas_owner_path",
        ],
    }
    if status == "blocked":
        result["status"] = "blocked"
        result["blocked_reason"] = (
            _optional_text(identity_guard.get("reason"))
            if identity_guard.get("matched") is False
            else _optional_text(payload_guard.get("reason"))
        ) or "current_owner_identity_guard_failed"
        result["publication_eval_surface"] = "not_written"
        result["publication_eval_record_surface"] = "not_written"
    return result


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
    normalized_record = canonicalize_ai_reviewer_publication_eval_record(
        _normalize_publication_eval_record(record)
    )
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=normalized_record,
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
    }
