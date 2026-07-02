from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.publication_eval_record import PublicationEvalRecord

from ..domain_action_request_lifecycle import stable_ai_reviewer_request_path
from ..domain_action_request_lifecycle_parts.ai_reviewer_input_contract import (
    input_contract_with_normalized_refs,
)
from ..stage_outcome_authority_parts.action_execution import ai_reviewer_request_refs
from .common import _mapping, _optional_text


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
    record_payload = _mapping(payload.get("record_payload"))
    if record_payload and (
        "required_input_refs" in payload
        or "required_currentness_refs" in payload
        or "schema_version" in record_payload
    ):
        return record_payload
    return payload


def _is_record_payload_authoring_target(value: Mapping[str, Any] | None) -> bool:
    return _optional_text(_mapping(value).get("surface")) == "ai_reviewer_record_payload_authoring_target"


def _record_materialization_requires_precheck(
    *,
    record: PublicationEvalRecord | dict[str, Any],
    entry_mode: str | None,
    expected_owner: str | None = None,
    expected_action_type: str | None = None,
    expected_work_unit_id: str | None = None,
    expected_work_unit_fingerprint: str | None = None,
    authoring_target_output: Path | None = None,
) -> bool:
    if entry_mode == "owner_consumption_payload_guard":
        return True
    if authoring_target_output is not None:
        return True
    if any(
        _optional_text(value)
        for value in (
            expected_owner,
            expected_action_type,
            expected_work_unit_id,
            expected_work_unit_fingerprint,
        )
    ):
        return True
    payload = record.to_dict() if isinstance(record, PublicationEvalRecord) else dict(record)
    if "required_input_refs" in payload or "required_currentness_refs" in payload or "stale_record_ref" in payload:
        return True
    return _is_record_payload_authoring_target(payload) and bool(_mapping(payload.get("record_payload")))


def _payload_target_current_metadata(
    *,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    required_currentness_refs: list[str],
) -> dict[str, Any]:
    lifecycle = _mapping(request.get("request_lifecycle"))
    stale_record_ref = _optional_text(lifecycle.get("stale_record_ref")) or _optional_text(
        request.get("publication_eval_record_ref")
    )
    return {
        "stale_record_ref": stale_record_ref,
        "required_input_refs": {surface: ref for surface, ref in required_refs.items() if ref is not None},
        "required_currentness_refs": list(required_currentness_refs),
    }


def _normalized_required_currentness_refs(
    *,
    request_refs: list[str],
    required_refs: Mapping[str, str | None],
) -> list[str]:
    if not request_refs:
        return [ref for ref in required_refs.values() if ref is not None]

    replacement_refs = {
        "artifacts/publication_eval/medical_prose_review.json": required_refs.get("medical_prose_review"),
        "artifacts/reports/publishability_gate/latest.json": required_refs.get("publication_gate_projection"),
    }
    normalized: list[str] = []
    for ref in request_refs:
        replacement = next(
            (
                candidate
                for suffix, candidate in replacement_refs.items()
                if candidate is not None and ref.endswith(suffix)
            ),
            ref,
        )
        if replacement not in normalized:
            normalized.append(replacement)
    return normalized


def _refresh_record_payload_target_metadata(
    *,
    record: Mapping[str, Any] | None,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    required_currentness_refs: list[str],
    enabled: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if record is None or not _is_record_payload_authoring_target(record):
        return (
            dict(record) if isinstance(record, Mapping) else None,
            {
                "enabled": False,
                "refreshed_in_memory": False,
                "written_files": [],
                "reason": None,
                "changed_fields": [],
            },
        )
    current_metadata = _payload_target_current_metadata(
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
    )
    if not enabled:
        return (
            dict(record),
            {
                "enabled": False,
                "refreshed_in_memory": False,
                "written_files": [],
                "reason": "payload_target_metadata_refresh_not_requested",
                "changed_fields": [],
                "current_metadata": current_metadata,
            },
        )
    refreshed = dict(record)
    changed_fields: list[str] = []
    for field, value in current_metadata.items():
        observed = refreshed.get(field)
        if observed != value:
            changed_fields.append(field)
        refreshed[field] = value
    return (
        refreshed,
        {
            "enabled": True,
            "refreshed_in_memory": True,
            "written_files": [],
            "reason": None,
            "changed_fields": changed_fields,
            "current_metadata": current_metadata,
            "record_payload_preserved": refreshed.get("record_payload") == record.get("record_payload"),
            "record_payload_prefilled_by_mas": False,
        },
    )


def _ai_reviewer_record_authoring_target_payload(
    *,
    record: Mapping[str, Any] | None,
    status_payload: Mapping[str, Any],
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    required_currentness_refs: list[str],
) -> dict[str, Any]:
    metadata = _payload_target_current_metadata(
        request=request,
        required_refs=required_refs,
        required_currentness_refs=required_currentness_refs,
    )
    source = dict(record) if _is_record_payload_authoring_target(record) else {}
    return {
        "surface": "ai_reviewer_record_payload_authoring_target",
        "study_id": _optional_text(status_payload.get("study_id")) or _optional_text(request.get("study_id")),
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(request.get("quest_id")),
        "request_kind": _record_request_kind(request),
        "request_owner": _optional_text(request.get("request_owner")),
        "owner_callable_surface": "publication materialize-ai-reviewer-record",
        "owner_callable_mode": "record_only_build_production_trace",
        "record_payload": _mapping(source.get("record_payload")),
        **metadata,
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


def _write_authoring_target_output(
    *,
    output_path: Path,
    study_root: Path,
    payload: Mapping[str, Any],
) -> Path:
    resolved_output = output_path.expanduser().resolve()
    resolved_study_root = study_root.expanduser().resolve()
    if resolved_output == resolved_study_root or resolved_study_root in resolved_output.parents:
        raise ValueError("AI reviewer authoring target output must not be inside the study root")
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resolved_output


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


def _request_with_normalized_input_refs(
    *,
    study_root: Path,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    if not request:
        return {}
    normalized = dict(request)
    normalized["input_contract"] = input_contract_with_normalized_refs(
        normalized,
        study_root=study_root,
    )
    return normalized


def _refs_from_record_and_request(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    request = _request_with_normalized_input_refs(
        study_root=study_root,
        request=_read_json_object(request_path) if request_path.exists() else {},
    )
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
    next_action_compact = _compact_current_work_unit_from_next_action(status_payload)
    if any(
        next_action_compact.get(key)
        for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint")
    ):
        return next_action_compact
    return _compact_current_work_unit_from_intervention_lane(status_payload)


def _compact_current_work_unit_from_next_action(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _mapping(status_payload.get("next_action"))
    if _optional_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    return {
        "status": "canonical_next_action",
        "owner": _optional_text(next_action.get("owner"))
        or _optional_text(next_action.get("next_owner")),
        "action_type": _optional_text(next_action.get("action_type"))
        or _optional_text(next_action.get("action_kind")),
        "work_unit_id": _optional_text(next_action.get("work_unit_id")),
        "work_unit_fingerprint": _optional_text(next_action.get("work_unit_fingerprint"))
        or _optional_text(next_action.get("action_fingerprint")),
        "phase": _optional_text(next_action.get("stage_id")),
        "typed_blocker": None,
    }


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

    record_is_authoring_target = _is_record_payload_authoring_target(record)
    record_payload = _mapping(record.get("record_payload")) if record_is_authoring_target else _payload_record(record)
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

    record_payload_mismatches: list[dict[str, str | None]] = []
    record_payload_missing_observed: list[str] = []
    if record_is_authoring_target:
        if not record_payload:
            record_payload_missing_observed.append("record_payload")
        else:
            for surface, expected_ref in expected_input_refs.items():
                observed_ref = _optional_text(input_bundle.get(surface))
                if observed_ref is None:
                    record_payload_missing_observed.append(
                        f"record_payload.reviewer_operating_system.input_bundle.{surface}"
                    )
                    continue
                if observed_ref != expected_ref:
                    record_payload_mismatches.append(
                        {"surface": surface, "expected": expected_ref, "observed": observed_ref}
                    )
            for expected_ref in required_currentness_refs:
                if expected_ref in expected_required_ref_values:
                    continue
                if expected_ref not in set(input_bundle.values()):
                    record_payload_missing_observed.append(f"record_payload.required_currentness_refs:{expected_ref}")

    common = {
        "enabled": True,
        "mismatches": mismatches,
        "missing_observed_fields": missing_observed,
        "expected_input_refs": expected_input_refs,
        "observed_input_refs": observed_input_refs,
        "expected_required_currentness_refs": required_currentness_refs,
        "observed_currentness_refs": sorted(observed_currentness_refs),
        "record_payload_mismatches": record_payload_mismatches,
        "record_payload_missing_observed_fields": record_payload_missing_observed,
    }
    if mismatches:
        return {
            **common,
            "matched": False,
            "reason": "payload_currentness_mismatch",
        }
    if record_payload_mismatches:
        return {
            **common,
            "matched": False,
            "reason": "record_payload_currentness_mismatch",
        }
    if record_payload_missing_observed:
        return {
            **common,
            "matched": False,
            "reason": "record_payload_currentness_refs_unavailable_for_guard",
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
