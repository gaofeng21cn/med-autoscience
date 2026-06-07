from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience import medical_manuscript_blueprint

from ... import (
    ai_reviewer_publication_eval_workflow,
    paper_authority_migration,
)
from ...ai_reviewer_story_provenance_guard import ai_reviewer_record_story_provenance_leakage_dispatch_blocker
from ...domain_action_request_lifecycle import stable_ai_reviewer_request_path
from . import claim_evidence_alignment
from . import ai_reviewer_request_refs
from .ai_reviewer_clean_migration_record import build_clean_migration_request_record
from .ai_reviewer_medical_prose_review_production import (
    currentness_blocker_or_handoff,
    try_rehydrate_medical_prose_review_request,
)
from .ai_reviewer_record_production import (
    attach_incomplete_ai_reviewer_record_handoff,
    attach_invalid_ai_reviewer_record_handoff,
    record_production_handoff_execution,
)
from .ai_reviewer_record_validation import (
    ai_reviewer_owned_record,
    ai_reviewer_record_blocker,
    ai_reviewer_record_requirements,
    missing_ai_reviewer_record_fields,
)
from .ai_reviewer_routeback_record import build_current_medical_prose_routeback_record
from .ai_reviewer_stale_record_handoff import stale_ai_reviewer_record_handoff


PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}

def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None

def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _publication_eval_latest_path(study_root: Path) -> Path:
    return study_root / PUBLICATION_EVAL_LATEST_RELATIVE_PATH


def _ai_reviewer_workflow_output_error(*, study_root: Path, owner_result: object) -> str | None:
    if not isinstance(owner_result, Mapping):
        return "owner_result_missing_or_invalid"
    latest_path = _publication_eval_latest_path(study_root)
    artifact_path_text = _text(owner_result.get("artifact_path"))
    if artifact_path_text is None:
        return "artifact_path_missing"
    artifact_path = Path(artifact_path_text).expanduser()
    if not artifact_path.is_absolute():
        artifact_path = study_root / artifact_path
    if artifact_path.resolve() != latest_path.resolve():
        return "artifact_path_not_publication_eval_latest"
    if not artifact_path.is_file():
        return "artifact_path_not_written"
    surface = _text(owner_result.get("publication_eval_surface"))
    if surface is not None and surface != str(PUBLICATION_EVAL_LATEST_RELATIVE_PATH):
        return "publication_eval_surface_mismatch"
    return None


def _paper_authority_clean_migration_blocker(*, study_root: Path, exc: Exception, request_path: Path) -> dict[str, Any] | None:
    if not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return None
    error = str(exc)
    if "medical_manuscript_blueprint" in error:
        return _blocked_ai_reviewer_execution(
            apply=True,
            reason="canonical_paper_inputs_rehydrate_required",
            request_path=request_path,
            next_owner="write",
            owner_callable_surface="medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            required_input_surface=str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            error=error,
            owner_result={
                "surface_kind": "canonical_paper_inputs_rehydrate_blocker",
                "authority_source_signature": "paper_authority_clean_migration",
                "canonical_surface": "paper/medical_manuscript_blueprint.json",
                "mechanical_blueprint_as_canonical_allowed": False,
                "legacy_artifact_reader_allowed": False,
                "quality_verdict_written": False,
                "submission_package_regenerated": False,
                "next_owner": "write",
                "next_required_actions": [
                    "materialize_or_authorize_medical_manuscript_blueprint",
                    "materialize_medical_prose_review_request",
                    "return_to_ai_reviewer_workflow",
                ],
            },
        )
    if "medical_prose_review_request" in error:
        rehydrate = try_rehydrate_medical_prose_review_request(study_root=study_root)
        return _blocked_ai_reviewer_execution(
            apply=True,
            reason="medical_prose_review_request_rehydrate_required",
            request_path=request_path,
            next_owner="ai_reviewer",
            required_input_surface=str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
            error=error,
            owner_result={
                "surface_kind": "medical_prose_review_currentness_blocker",
                "authority_source_signature": "paper_authority_clean_migration",
                "currentness_error": error,
                "stale_medical_prose_review_reuse_allowed": False,
                "medical_prose_review_request_rehydrated": rehydrate["status"] == "materialized",
                "rehydrated_request_ref": rehydrate.get("artifact_path"),
                "quality_verdict_written": False,
                "submission_package_regenerated": False,
                "next_owner": "ai_reviewer",
                "next_required_actions": [
                    "produce_ai_reviewer_medical_prose_review_against_current_manuscript",
                    "produce_ai_reviewer_medical_prose_review_against_current_request",
                    "return_to_ai_reviewer_workflow",
                ],
                "rehydrate_result": rehydrate,
            },
        )
    return None


def _medical_prose_review_currentness_blocker(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    exc: Exception,
    request_path: Path,
    dispatch: Mapping[str, Any] | None,
    apply: bool,
) -> dict[str, Any] | None:
    return currentness_blocker_or_handoff(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        error=str(exc),
        request_path=request_path,
        dispatch=dispatch,
        apply=apply,
        blocked_execution_builder=_blocked_ai_reviewer_execution,
    )


def _claim_evidence_alignment_blocker(*, study_root: Path, exc: Exception, request_path: Path) -> dict[str, Any] | None:
    owner_result = claim_evidence_alignment.blocker_from_workflow_exception(
        study_root=study_root,
        error=str(exc),
    )
    if owner_result is None:
        return None
    return _blocked_ai_reviewer_execution(
        apply=True,
        reason=claim_evidence_alignment.BLOCKED_REASON,
        request_path=request_path,
        next_owner="write",
        owner_callable_surface=claim_evidence_alignment.OWNER_CALLABLE_SURFACE,
        required_input_surface=claim_evidence_alignment.REQUIRED_INPUT_SURFACE,
        error=str(exc),
        owner_result=owner_result,
    )

def execute_ai_reviewer_workflow(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
    controller_decision_refresh,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    closeout_binding = _ai_reviewer_closeout_binding(dispatch)
    request = _read_json_object(request_path)
    if request is None or _text(_mapping(request).get("surface_kind")) == "legacy_control_surface_tombstone":
        return _blocked_ai_reviewer_execution(
            apply=apply,
            reason="ai_reviewer_request_missing",
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
    request = _complete_ai_reviewer_request_packet(study_root=study_root, request=request, request_path=request_path)
    record, record_blocker = _ai_reviewer_record_for_execution(request=request, study_root=study_root)
    if record_blocker:
        handoff = record_production_handoff_execution(
            profile=profile,
            study_id=study_id,
            request=request,
            dispatch=dispatch,
            record_blocker=record_blocker,
            apply=apply,
        )
        if handoff is not None:
            return handoff
        payload = _blocked_ai_reviewer_execution(
            apply=apply,
            reason=record_blocker["reason"],
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
        payload.update(record_blocker["payload"])
        return payload
    if not record:
        return _blocked_ai_reviewer_execution(
            apply=apply,
            reason="ai_reviewer_record_missing",
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
    required_refs = ai_reviewer_request_refs.required_refs(request)
    missing_refs = [surface for surface, ref in required_refs.items() if ref is None]
    if missing_refs:
        payload = _blocked_ai_reviewer_execution(
            apply=apply,
            reason="ai_reviewer_required_refs_missing",
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
        payload["missing_refs"] = missing_refs
        return payload
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "request_path": str(request_path),
        }
    additional_refs = {
        surface: ref
        for surface, ref in {**required_refs, **ai_reviewer_request_refs.optional_refs(request)}.items()
        if surface not in {"manuscript", "evidence_ledger", "review_ledger", "study_charter"}
        and ref is not None
    }
    try:
        owner_result = ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=required_refs["manuscript"],
            evidence_ref=required_refs["evidence_ledger"],
            review_ref=required_refs["review_ledger"],
            charter_ref=required_refs["study_charter"],
            record=record,
            additional_refs=additional_refs,
            workflow_currentness_mode="request_bound_ai_reviewer_record",
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        clean_migration_blocker = _paper_authority_clean_migration_blocker(
            study_root=study_root,
            exc=exc,
            request_path=request_path,
        )
        if clean_migration_blocker is not None:
            return clean_migration_blocker
        currentness_blocker = _medical_prose_review_currentness_blocker(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            exc=exc,
            request_path=request_path,
            dispatch=dispatch,
            apply=apply,
        )
        if currentness_blocker is not None:
            return currentness_blocker
        alignment_blocker = _claim_evidence_alignment_blocker(
            study_root=study_root,
            exc=exc,
            request_path=request_path,
        )
        if alignment_blocker is not None:
            return alignment_blocker
        payload = _blocked_ai_reviewer_execution(
            apply=True,
            reason="ai_reviewer_workflow_failed",
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
        payload["error"] = str(exc)
        return payload
    output_error = _ai_reviewer_workflow_output_error(study_root=study_root, owner_result=owner_result)
    if output_error is not None:
        payload = _blocked_ai_reviewer_execution(
            apply=True,
            reason="ai_reviewer_workflow_output_missing",
            request_path=request_path,
            closeout_binding=closeout_binding,
        )
        payload["error"] = output_error
        if isinstance(owner_result, Mapping):
            payload["owner_result"] = dict(owner_result)
        return payload
    refresh = controller_decision_refresh(profile=profile, study_id=study_id, study_root=study_root)
    if isinstance(owner_result, Mapping):
        owner_result = {**dict(owner_result), "controller_decision_refresh": refresh}
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        "owner_result": owner_result,
        "request_path": str(request_path),
    }


def _complete_ai_reviewer_request_packet(
    *,
    study_root: Path,
    request: Mapping[str, Any],
    request_path: Path,
) -> dict[str, Any]:
    completed = {**dict(request)}
    input_contract = _mapping(completed.get("input_contract"))
    required_refs = _mapping(input_contract.get("required_refs"))
    changed = False
    for surface, path in _canonical_ai_reviewer_ref_paths(study_root=study_root).items():
        existing = _mapping(required_refs.get(surface))
        existing_path = _text(existing.get("path")) or _text(existing.get("ref")) or _text(existing.get("relative_path"))
        existing_target = _existing_ref_path(study_root=study_root, ref=existing_path)
        if (
            existing_target is not None
            and existing_target.is_file()
            and existing.get("present") is not False
            and existing.get("valid") is not False
        ):
            continue
        if not path.is_file():
            continue
        required_refs[surface] = {"path": str(path.resolve()), "present": True, "valid": True}
        changed = True
    required_inputs, required_inputs_changed = _ai_reviewer_required_inputs_from_refs(
        existing=_mapping(completed.get("required_inputs")),
        required_refs=required_refs,
    )
    changed = changed or required_inputs_changed
    lifecycle = _mapping(completed.get("request_lifecycle"))
    completed_for_ref_check = {
        **completed,
        "input_contract": {**input_contract, "required_refs": required_refs},
    }
    all_required_refs_present = all(
        ref is not None for ref in ai_reviewer_request_refs.required_refs(completed_for_ref_check).values()
    )
    lifecycle_updates = {
        "request_packet_materialized": True,
        "all_required_refs_present": all_required_refs_present,
    }
    for key, value in lifecycle_updates.items():
        if lifecycle.get(key) != value:
            lifecycle[key] = value
            changed = True
    if all_required_refs_present is True and _text(lifecycle.get("blocked_reason")) in {
        "paper_authority_clean_migration_required",
        "ai_reviewer_required_refs_missing",
    }:
        lifecycle["blocked_reason"] = None
        changed = True
    if not changed:
        return completed
    input_contract["required_refs"] = required_refs
    completed["input_contract"] = input_contract
    completed["required_inputs"] = required_inputs
    completed["request_lifecycle"] = lifecycle
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(completed, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return completed


def _ai_reviewer_required_inputs_from_refs(
    *,
    existing: Mapping[str, Any],
    required_refs: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    required_inputs = dict(existing)
    changed = False
    for surface, ref_payload in required_refs.items():
        ref = _mapping(ref_payload)
        ref_path = _text(ref.get("path")) or _text(ref.get("ref")) or _text(ref.get("relative_path"))
        if ref_path is None:
            continue
        key = f"{surface}_ref"
        if _text(required_inputs.get(key)) == ref_path:
            continue
        required_inputs[key] = ref_path
        changed = True
    return required_inputs, changed


def _canonical_ai_reviewer_ref_paths(*, study_root: Path) -> dict[str, Path]:
    return {
        "manuscript": study_root / "paper" / "draft.md",
        "evidence_ledger": study_root / "paper" / "evidence_ledger.json",
        "review_ledger": study_root / "paper" / "review" / "review_ledger.json",
        "study_charter": study_root / "artifacts" / "controller" / "study_charter.json",
        "medical_manuscript_blueprint": medical_manuscript_blueprint.current_medical_manuscript_blueprint_path(
            study_root=study_root
        ),
        "claim_evidence_map": study_root / "paper" / "claim_evidence_map.json",
        "medical_prose_review": study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        "publication_gate_projection": study_root / "artifacts" / "publication_eval" / "latest.json",
    }


def _existing_ref_path(*, study_root: Path, ref: str | None) -> Path | None:
    if ref is None:
        return None
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (study_root / candidate).resolve()


def execute_canonical_paper_inputs_rehydrate(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    if not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "paper_authority_clean_migration_not_pending",
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "next_owner": "ai_reviewer",
            "required_input_surface": str(
                paper_authority_migration.paper_authority_cutover_latest_path(study_root=study_root)
            ),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
            "next_owner": "write",
        }
    try:
        owner_result = medical_manuscript_blueprint.materialize_medical_manuscript_blueprint(study_root=study_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "next_owner": "write",
            "error": str(exc),
            "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
        }
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
        "next_owner": "write",
        "owner_result": {
            **dict(owner_result),
            "canonical_ready": False,
            "canonical_surface_written": False,
            "next_required_actions": [
                "AI author/reviewer must authorize paper/medical_manuscript_blueprint.json",
                "materialize medical prose review request",
                "return to AI reviewer workflow",
            ],
        },
    }

def _blocked_ai_reviewer_execution(
    *,
    apply: bool,
    reason: str,
    request_path: Path,
    next_owner: str = "ai_reviewer",
    owner_callable_surface: str = "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
    required_input_surface: str | None = None,
    error: str | None = None,
    owner_result: Mapping[str, Any] | None = None,
    closeout_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    typed_blocker = _ai_reviewer_typed_blocker(reason=reason)
    payload: dict[str, Any] = {
        "execution_status": "blocked" if apply else "dry_run",
        "blocked_reason": reason,
        "owner_callable_surface": owner_callable_surface,
        "next_owner": next_owner,
        "required_input_surface": required_input_surface or str(request_path),
        "typed_blocker": typed_blocker,
        "owner_delta_result": _ai_reviewer_owner_delta_result(
            reason=reason,
            request_path=request_path,
            typed_blocker=typed_blocker,
            closeout_binding=closeout_binding,
        ),
    }
    if error is not None:
        payload["error"] = error
    if owner_result is not None:
        payload["owner_result"] = dict(owner_result)
    return payload


def _ai_reviewer_typed_blocker(*, reason: str) -> dict[str, Any]:
    return {
        "blocker_id": reason,
        "owner": "ai_reviewer",
        "reason": reason,
        "required_owner_surface": "return_to_ai_reviewer_workflow owner surface",
        "write_permitted": False,
    }


def _ai_reviewer_owner_delta_result(
    *,
    reason: str,
    request_path: Path,
    typed_blocker: Mapping[str, Any],
    closeout_binding: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "surface_kind": "mas_current_owner_delta_result",
        "owner": "ai_reviewer",
        "result_kind": "stable_typed_blocker",
        "required_return_shape_satisfied": True,
        "owner_receipt_refs": [],
        "quality_gate_receipt_refs": [],
        "stable_typed_blocker_refs": [str(request_path)],
        "quality_gate_receipt": None,
        "typed_blocker": dict(typed_blocker),
        "body_included": False,
        "blocked_reason": reason,
        "authority_boundary": {
            "owner": "med-autoscience",
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_paper_or_package": False,
            "writes_memory_body": False,
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    }
    if closeout_binding:
        binding = dict(closeout_binding)
        result["closeout_binding"] = binding
        result["stage_run_id"] = _text(binding.get("stage_run_id"))
        result["stage_manifest_ref"] = _text(binding.get("stage_manifest_ref"))
        result["current_pointer_ref"] = _text(binding.get("current_pointer_ref"))
        result["source_fingerprint"] = _text(binding.get("source_fingerprint"))
        result["idempotency_key"] = _text(binding.get("idempotency_key"))
    return result


def _ai_reviewer_closeout_binding(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _mapping(dispatch)
    prompt_contract = _mapping(source.get("prompt_contract"))
    dispatch_binding = _mapping(source.get("closeout_binding")) or _mapping(prompt_contract.get("closeout_binding"))
    env_binding = _env_ai_reviewer_closeout_binding()
    binding = {**dispatch_binding, **env_binding}
    required = (
        _text(binding.get("stage_run_id")),
        _text(binding.get("stage_manifest_ref")),
        _text(binding.get("current_pointer_ref")),
        _text(binding.get("source_fingerprint")),
        _text(binding.get("idempotency_key")),
    )
    if not all(required):
        return {}
    return {key: value for key, value in binding.items() if value not in (None, [], "")}


def _env_ai_reviewer_closeout_binding() -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    if raw := _text(os.environ.get("OPL_CLOSEOUT_BINDING_JSON")):
        try:
            candidate = json.loads(raw)
            if isinstance(candidate, Mapping):
                parsed = dict(candidate)
        except json.JSONDecodeError:
            parsed = {}
    aliases = {
        "stage_run_id": os.environ.get("OPL_STAGE_RUN_ID"),
        "stage_manifest_ref": os.environ.get("OPL_STAGE_MANIFEST_REF"),
        "current_pointer_ref": os.environ.get("OPL_CURRENT_POINTER_REF"),
        "provider_attempt_ref": os.environ.get("OPL_PROVIDER_ATTEMPT_REF"),
        "attempt_lease_ref": os.environ.get("OPL_ATTEMPT_LEASE_REF"),
        "attempt_lease_status": os.environ.get("OPL_ATTEMPT_LEASE_STATUS"),
        "execution_authorization_decision_ref": os.environ.get("OPL_EXECUTION_AUTHORIZATION_DECISION_REF"),
        "source_fingerprint": os.environ.get("OPL_SOURCE_FINGERPRINT"),
        "idempotency_key": os.environ.get("OPL_IDEMPOTENCY_KEY"),
    }
    return {**parsed, **{key: text for key, value in aliases.items() if (text := _text(value))}}


def _ai_reviewer_record_for_execution(
    *,
    request: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    current_record = _mapping(_read_json_object(_publication_eval_latest_path(study_root)))
    request_record = _mapping(request.get("ai_reviewer_record") or request.get("publication_eval_record") or request.get("record"))
    lifecycle = _mapping(request.get("request_lifecycle"))
    stale_record_handoff = stale_ai_reviewer_record_handoff(
        request=request,
        required_refs=ai_reviewer_request_refs.required_refs(request),
        lifecycle=lifecycle,
    )
    if stale_record_handoff is not None:
        return {}, stale_record_handoff
    story_leakage_blocker = ai_reviewer_record_story_provenance_leakage_dispatch_blocker(lifecycle)
    if story_leakage_blocker is not None:
        return {}, story_leakage_blocker

    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            attach_incomplete_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            return {}, record_blocker
        return request_record, None

    request_record = build_current_medical_prose_routeback_record(
        study_root=study_root,
        request=request,
        required_refs=ai_reviewer_request_refs.required_refs(request),
    )
    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            attach_incomplete_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            return {}, record_blocker
        return request_record, None

    cutover_requires_ai_reviewer = paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root)
    if cutover_requires_ai_reviewer and not request_record:
        request_record = _clean_migration_request_record(study_root=study_root, request=request)

    if (
        current_record
        and ai_reviewer_owned_record(current_record)
        and not cutover_requires_ai_reviewer
    ):
        missing_fields = missing_ai_reviewer_record_fields(current_record)
        if missing_fields:
            record_blocker = {
                "reason": "ai_reviewer_record_incomplete",
                "payload": {
                    "missing_record_fields": missing_fields,
                    "owner_record_requirements": ai_reviewer_record_requirements(),
                },
            }
            attach_incomplete_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=current_record,
            )
            return {}, record_blocker
        return current_record, None

    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            if cutover_requires_ai_reviewer:
                attach_incomplete_ai_reviewer_record_handoff(
                    record_blocker=record_blocker,
                    request=request,
                    required_refs=ai_reviewer_request_refs.required_refs(request),
                    record=request_record,
                )
            return {}, record_blocker
        return request_record, None

    return {}, {
        "reason": "ai_reviewer_record_missing",
        "payload": {
            "owner_record_requirements": ai_reviewer_record_requirements(),
        },
    }

def _clean_migration_request_record(*, study_root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    refs = ai_reviewer_request_refs.required_refs(request)
    return build_clean_migration_request_record(study_root=study_root, request=request, refs=refs)



__all__ = [
    "execute_ai_reviewer_workflow",
    "execute_canonical_paper_inputs_rehydrate",
]
