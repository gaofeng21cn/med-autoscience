from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.medical_prose_review_request import materialize_medical_prose_review_request
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


REVIEW_OUTPUT_SURFACE = "artifacts/publication_eval/medical_prose_review.json"
ACTION_TYPE = "return_to_ai_reviewer_workflow"
DISPATCH_AUTHORITY = "ai_reviewer_medical_prose_review_production_handoff"
ALLOWED_WRITE_SURFACES = [REVIEW_OUTPUT_SURFACE]
FORBIDDEN_SURFACES = [
    "paper/**",
    "manuscript/**",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    ".ds/**",
]
CURRENTNESS_ERRORS = frozenset(
    {
        "medical_prose_review_request_digest_missing",
        "medical_prose_review_request_digest_mismatch",
        "medical_prose_review_manuscript_ref_missing",
        "medical_prose_review_manuscript_digest_missing",
        "medical_prose_review_manuscript_ref_mismatch",
        "medical_prose_review_manuscript_digest_mismatch",
        "medical_prose_review_reviewer_os_manuscript_ref_mismatch",
        "medical_prose_review_live_manuscript_missing",
        "medical_prose_review_live_manuscript_digest_mismatch",
    }
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_ai_reviewer_medical_prose_review_production_request(
    *,
    study_id: str,
    request_path: Path,
    rehydrate: Mapping[str, Any],
    currentness_error: str,
    request_kind: str,
) -> dict[str, Any]:
    request_ref = _text(rehydrate.get("artifact_path")) or str(request_path)
    return {
        "surface": "ai_reviewer_medical_prose_review_production_request",
        "schema_version": 1,
        "request_kind": request_kind,
        "request_owner": "ai_reviewer",
        "study_id": study_id,
        "quest_id": study_id,
        "currentness_error": currentness_error,
        "required_input_refs": {
            "medical_prose_review_request": request_ref,
        },
        "required_output_surface": REVIEW_OUTPUT_SURFACE,
        "owner_callable_surface": "publication materialize-ai-medical-prose-review",
        "review_must_consume_refs": [request_ref],
        "followup_actions": [
            "domain-action-request-materialize",
            "domain-owner-action-dispatch --action-types return_to_ai_reviewer_workflow",
        ],
        "authority_contract": {
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "medical_prose_review_only_surface": True,
        },
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
    }


def build_ai_reviewer_medical_prose_review_worker_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any] | None,
    production_request: Mapping[str, Any],
) -> dict[str, Any]:
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(_mapping(dispatch).get("owner_route"))
        or _mapping(_mapping(_mapping(dispatch).get("prompt_contract")).get("owner_route"))
    )
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    closeout_contract = default_executor_typed_closeout_contract(action_type=ACTION_TYPE)
    repeat_key = _text(owner_route.get("work_unit_fingerprint")) if owner_route else None
    if repeat_key is None and owner_route:
        repeat_key = _text(owner_route.get("idempotency_key"))
    prompt_contract = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": ACTION_TYPE,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": REVIEW_OUTPUT_SURFACE,
        "owner_route": owner_route or None,
        "idempotency_key": _text(owner_route.get("idempotency_key")) if owner_route else None,
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{ACTION_TYPE}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "ai_reviewer_medical_prose_review_production_request": dict(production_request),
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        **default_executor_policy(),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": ACTION_TYPE,
        "action_id": f"ai-reviewer-medical-prose-review-production::{study_id}",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": REVIEW_OUTPUT_SURFACE,
        "dispatch_status": "ready",
        "dispatch_authority": DISPATCH_AUTHORITY,
        "owner_route": owner_route or None,
        "idempotency_key": _text(owner_route.get("idempotency_key")) if owner_route else None,
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": repeat_key,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": closeout_contract,
        "terminal_output_instruction": closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "ai_reviewer_medical_prose_review_production_request": dict(production_request),
        "source_action": {
            "surface": "ai_reviewer_medical_prose_review_production_request",
            "request_kind": _text(production_request.get("request_kind")),
            "required_input_refs": dict(production_request.get("required_input_refs") or {}),
            "medical_prose_review_only_surface": True,
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "request_path": _text(_mapping(production_request.get("required_input_refs")).get("medical_prose_review_request")),
        },
        "handoff_semantics": {
            "status": "ai_reviewer_medical_prose_review_production_handoff_ready",
            "terminal_blocker": False,
            "expected_next_effect": "ai_reviewer emits a current medical prose review response",
        },
        "generated_at": _utc_now(),
    }


def materialize_ai_reviewer_medical_prose_review_worker_handoff(
    *,
    handoff: Mapping[str, Any],
) -> str:
    dispatch_path_text = _text(_mapping(handoff.get("refs")).get("dispatch_path"))
    if dispatch_path_text is None:
        raise ValueError("ai_reviewer_medical_prose_review_worker_handoff_dispatch_path_missing")
    dispatch_path = Path(dispatch_path_text).expanduser()
    _write_json(dispatch_path, handoff)
    return str(dispatch_path)


def medical_prose_review_production_handoff_execution(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any] | None,
    request_path: Path,
    rehydrate: Mapping[str, Any],
    currentness_error: str,
    apply: bool,
) -> dict[str, Any] | None:
    if _text(rehydrate.get("status")) != "materialized":
        return None
    request_kind = (
        "produce_ai_reviewer_medical_prose_review_against_current_manuscript"
        if "manuscript" in currentness_error
        else "produce_ai_reviewer_medical_prose_review_against_current_request"
    )
    production_request = build_ai_reviewer_medical_prose_review_production_request(
        study_id=study_id,
        request_path=request_path,
        rehydrate=rehydrate,
        currentness_error=currentness_error,
        request_kind=request_kind,
    )
    handoff = build_ai_reviewer_medical_prose_review_worker_handoff(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        production_request=production_request,
    )
    owner_result = {
        "surface_kind": "medical_prose_review_currentness_handoff",
        "authority_source_signature": "ai_reviewer_publication_eval_workflow",
        "currentness_error": currentness_error,
        "stale_medical_prose_review_reuse_allowed": False,
        "medical_prose_review_request_rehydrated": True,
        "rehydrated_request_ref": rehydrate.get("artifact_path"),
        "quality_verdict_written": False,
        "submission_package_regenerated": False,
        "next_owner": "ai_reviewer",
        "next_required_actions": [
            request_kind,
            "return_to_ai_reviewer_workflow",
        ],
        "rehydrate_result": dict(rehydrate),
    }
    result = {
        "execution_status": "handoff_ready" if apply else "dry_run",
        "blocked_reason": None,
        "owner_callable_surface": "publication materialize-ai-medical-prose-review",
        "next_owner": "ai_reviewer",
        "required_input_surface": str(request_path),
        "error": currentness_error,
        "owner_result": owner_result,
        "ai_reviewer_medical_prose_review_production_request": production_request,
        "ai_reviewer_medical_prose_review_worker_handoff": handoff,
        "next_required_actions": list(owner_result["next_required_actions"]),
    }
    if apply:
        result["ai_reviewer_medical_prose_review_worker_handoff_path"] = (
            materialize_ai_reviewer_medical_prose_review_worker_handoff(handoff=handoff)
        )
    return result


def try_rehydrate_medical_prose_review_request(*, study_root: Path) -> dict[str, Any]:
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    try:
        result = materialize_medical_prose_review_request(study_root=study_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "surface_kind": "medical_prose_review_request_rehydrate_receipt",
            "status": "blocked",
            "blocked_reason": "medical_prose_review_request_rehydrate_failed",
            "error": str(exc),
            "artifact_path": str(request_path),
        }
    return {
        "surface_kind": "medical_prose_review_request_rehydrate_receipt",
        "status": "materialized",
        "artifact_path": str(result.get("artifact_path") or request_path),
    }


def currentness_blocker_or_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    error: str,
    request_path: Path,
    dispatch: Mapping[str, Any] | None,
    apply: bool,
    blocked_execution_builder,
) -> dict[str, Any] | None:
    if error not in CURRENTNESS_ERRORS:
        return None
    prose_request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    rehydrate = try_rehydrate_medical_prose_review_request(study_root=study_root)
    handoff = medical_prose_review_production_handoff_execution(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        request_path=prose_request_path,
        rehydrate=rehydrate,
        currentness_error=error,
        apply=apply,
    )
    if handoff is not None:
        return handoff
    return blocked_execution_builder(
        apply=True,
        reason="medical_prose_review_request_rehydrate_required",
        request_path=request_path,
        next_owner="ai_reviewer",
        required_input_surface=str(prose_request_path),
        error=error,
        owner_result={
            "surface_kind": "medical_prose_review_currentness_blocker",
            "authority_source_signature": "ai_reviewer_publication_eval_workflow",
            "currentness_error": error,
            "stale_medical_prose_review_reuse_allowed": False,
            "medical_prose_review_request_rehydrated": rehydrate["status"] == "materialized",
            "rehydrated_request_ref": rehydrate.get("artifact_path"),
            "quality_verdict_written": False,
            "submission_package_regenerated": False,
            "next_owner": "ai_reviewer",
            "next_required_actions": [
                "materialize_current_medical_prose_review_request",
                "produce_ai_reviewer_medical_prose_review_against_current_manuscript",
                "produce_ai_reviewer_medical_prose_review_against_current_request",
                "return_to_ai_reviewer_workflow",
            ],
            "rehydrate_result": rehydrate,
        },
    )


__all__ = [
    "build_ai_reviewer_medical_prose_review_production_request",
    "build_ai_reviewer_medical_prose_review_worker_handoff",
    "currentness_blocker_or_handoff",
    "materialize_ai_reviewer_medical_prose_review_worker_handoff",
    "medical_prose_review_production_handoff_execution",
    "try_rehydrate_medical_prose_review_request",
]
