from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers import (
    canonical_manuscript_package_loop,
    domain_owner_action_dispatch,
    paper_repair_execution_evidence,
    quality_repair_batch,
)
from med_autoscience.controllers.domain_action_request_materializer import (
    FORBIDDEN_SURFACES,
    SUPPORTED_MODE,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    default_ai_reviewer_request_input_refs,
    materialize_ai_reviewer_request,
    stable_ai_reviewer_request_path,
)
from med_autoscience.controllers.paper_repair_executor_parts.owner_callable_results import (
    owner_result_blocker,
    owner_result_executed,
    owner_result_handoff_ready,
)
from med_autoscience.controllers.runtime_ai_repair_policy import default_executor_policy
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import repeat_suppression


SURFACE = "paper_repair_executor"
SCHEMA_VERSION = 1
SUPPORTED_AUTO_WORK_UNITS = {
    "analysis_repair",
    "text_repair",
    "evidence_ledger_repair",
    "review_ledger_repair",
    "claim_downgrade",
    "route_decision",
}
TYPED_BLOCKER_BY_WORK_UNIT = {
    "display_rebuild": "owner_callable_surface_missing",
    "package_refresh": "owner_callable_surface_missing",
}
STRUCTURED_PATCH_BLOCKER = "owner_callable_surface_missing"
QUALITY_REPAIR_BATCH_CALLABLE = "quality_repair_batch.run_quality_repair_batch"
AI_REVIEWER_PUBLICATION_EVAL_CALLABLE = (
    "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
)


def dispatch_repair_work_unit(
    *,
    profile: WorkspaceProfile | None = None,
    study_id: str,
    quest_id: str,
    study_root: str | Path,
    repair_work_unit: Mapping[str, Any],
    review_finding: Mapping[str, Any] | None = None,
    control_plane_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    work_unit = dict(repair_work_unit)
    work_unit_type = _text(work_unit.get("work_unit_type")) or "unknown"
    generated_at = _utc_now()
    if not apply:
        return {
            "surface": SURFACE,
            "schema_version": SCHEMA_VERSION,
            "accepted": True,
            "execution_status": "dry_run",
            "typed_blocker": None,
            "study_id": study_id,
            "quest_id": quest_id,
            "repair_work_unit": work_unit,
            "would_write": _would_write(work_unit_type),
            "authority_boundary": _authority_boundary(),
        }

    callable_surface = _text(work_unit.get("callable_surface"))
    if callable_surface == QUALITY_REPAIR_BATCH_CALLABLE:
        return _dispatch_quality_repair_batch_callable(
            profile=profile,
            study_id=study_id,
            quest_id=quest_id,
            study_root=resolved_study_root,
            work_unit=work_unit,
            generated_at=generated_at,
            control_plane_route_context=control_plane_route_context,
            route_context=route_context,
        )
    if callable_surface == AI_REVIEWER_PUBLICATION_EVAL_CALLABLE:
        return _dispatch_ai_reviewer_callable(
            profile=profile,
            study_id=study_id,
            quest_id=quest_id,
            study_root=resolved_study_root,
            work_unit=work_unit,
            generated_at=generated_at,
            control_plane_route_context=control_plane_route_context,
            route_context=route_context,
        )

    preflight_blocker = _preflight_blocker(work_unit=work_unit, work_unit_type=work_unit_type)
    if work_unit_type not in SUPPORTED_AUTO_WORK_UNITS or preflight_blocker is not None:
        return _blocked_result(
            generated_at=generated_at,
            study_id=study_id,
            quest_id=quest_id,
            study_root=resolved_study_root,
            work_unit=work_unit,
            review_finding=review_finding,
            typed_blocker=preflight_blocker
            or TYPED_BLOCKER_BY_WORK_UNIT.get(work_unit_type, "owner_callable_surface_missing"),
        )

    changed_refs = _execute_supported_work_unit(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        work_unit=work_unit,
        work_unit_type=work_unit_type,
        generated_at=generated_at,
    )
    gate_replay_ref = _write_gate_replay_request(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=quest_id,
        work_unit=work_unit,
        changed_refs=changed_refs,
        generated_at=generated_at,
    )
    ai_request = _write_ai_reviewer_recheck_request(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=quest_id,
        work_unit=work_unit,
        gate_replay_ref=gate_replay_ref,
        generated_at=generated_at,
    )
    evidence = paper_repair_execution_evidence.build_repair_execution_evidence(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        repair_work_unit=work_unit,
        review_finding=review_finding,
        source_refs=work_unit.get("source_refs") or [],
        changed_artifact_refs=changed_refs,
        revision_log_ref=str(_revision_log_path(resolved_study_root)),
        evidence_ledger_ref=str(_evidence_ledger_path(resolved_study_root)),
        review_ledger_ref=str(_review_ledger_path(resolved_study_root)),
        gate_replay_target=_text(work_unit.get("gate_replay_target")) or "publication_eval/latest.json",
        gate_replay_refs=[str(gate_replay_ref)],
        ai_reviewer_recheck_request_ref=str(stable_ai_reviewer_request_path(study_root=resolved_study_root)),
    )
    evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=resolved_study_root,
        evidence=evidence,
    )
    owner_receipt = _owner_receipt(
        generated_at=generated_at,
        accepted=True,
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        work_unit=work_unit,
        execution_status="executed",
        typed_blocker=None,
        changed_refs=changed_refs,
        evidence_path=evidence_path,
        gate_replay_ref=gate_replay_ref,
        ai_reviewer_request=ai_request,
    )
    canonical_package_loop = canonical_manuscript_package_loop.materialize_canonical_package_loop_proofs(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=quest_id,
        source_refs=[ref["path"] for ref in evidence["changed_artifact_refs"]],
    )
    receipt_path = _write_owner_receipt(study_root=resolved_study_root, receipt=owner_receipt)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "accepted": True,
        "execution_status": "executed",
        "typed_blocker": None,
        "study_id": study_id,
        "quest_id": quest_id,
        "repair_work_unit": work_unit,
        "owner_receipt": owner_receipt,
        "owner_receipt_ref": str(receipt_path),
        "canonical_artifact_delta": evidence["canonical_artifact_delta"],
        "repair_execution_evidence": evidence,
        "repair_execution_evidence_ref": str(evidence_path),
        "canonical_package_loop": canonical_package_loop,
        "gate_replay_request_ref": str(gate_replay_ref),
        "ai_reviewer_recheck_request_ref": str(stable_ai_reviewer_request_path(study_root=resolved_study_root)),
        "authority_boundary": _authority_boundary(),
    }


def _dispatch_quality_repair_batch_callable(
    *,
    profile: WorkspaceProfile | None,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    generated_at: str,
    control_plane_route_context: Mapping[str, Any] | None,
    route_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if profile is None:
        return _blocked_result(
            generated_at=generated_at,
            study_id=study_id,
            quest_id=quest_id,
            study_root=study_root,
            work_unit=work_unit,
            review_finding=None,
            typed_blocker="owner_callable_context_missing",
        )
    owner_result = quality_repair_batch.run_quality_repair_batch(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=quest_id,
        source=SURFACE,
        control_plane_route_context=control_plane_route_context,
        route_context=route_context,
    )
    return _owner_callable_result(
        generated_at=generated_at,
        accepted=owner_result_executed(owner_result),
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        work_unit=work_unit,
        owner_callable_surface=QUALITY_REPAIR_BATCH_CALLABLE,
        owner_result=owner_result,
    )


def _dispatch_ai_reviewer_callable(
    *,
    profile: WorkspaceProfile | None,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    generated_at: str,
    control_plane_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if profile is None:
        return _blocked_result(
            generated_at=generated_at,
            study_id=study_id,
            quest_id=quest_id,
            study_root=study_root,
            work_unit=work_unit,
            review_finding=None,
            typed_blocker="owner_callable_context_missing",
        )
    owner_result = domain_owner_action_dispatch.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        consumer_payload=_ai_reviewer_owner_consumer_payload(
            study_id=study_id,
            quest_id=quest_id,
            study_root=study_root,
            work_unit=work_unit,
            generated_at=generated_at,
            control_plane_route_context=control_plane_route_context,
            route_context=route_context,
        ),
    )
    return _owner_callable_result(
        generated_at=generated_at,
        accepted=owner_result_executed(owner_result),
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        work_unit=work_unit,
        owner_callable_surface=AI_REVIEWER_PUBLICATION_EVAL_CALLABLE,
        owner_result=owner_result,
    )


def _ai_reviewer_owner_consumer_payload(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    generated_at: str,
    control_plane_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    action_type = "return_to_ai_reviewer_workflow"
    owner_route = _ai_reviewer_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        work_unit=work_unit,
        action_type=action_type,
        route_context=control_plane_route_context or route_context,
    )
    request = _write_ai_reviewer_recheck_request(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        work_unit={**dict(work_unit), "owner_route": owner_route},
        gate_replay_ref=_ai_reviewer_recheck_gate_replay_ref(study_root=study_root),
        generated_at=generated_at,
        owner_route=owner_route,
    )
    dispatch_path = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches" / f"{action_type}.json"
    dispatch = _ai_reviewer_default_executor_dispatch(
        study_id=study_id,
        quest_id=quest_id,
        work_unit=work_unit,
        action_type=action_type,
        owner_route=owner_route,
        dispatch_path=dispatch_path,
        request=request,
    )
    _write_json(dispatch_path, dispatch)
    return {
        "surface": "paper_repair_inline_consumer_payload",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "default_executor_dispatches": [dispatch],
    }


def _ai_reviewer_owner_route(
    *,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    action_type: str,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    route_context_mapping = _mapping(route_context)
    controller_context = _mapping(route_context_mapping.get("controller_route_context"))
    current_owner_route = _mapping(route_context_mapping.get("current_owner_route"))
    fingerprint = (
        _text(controller_context.get("work_unit_fingerprint"))
        or _text(current_owner_route.get("work_unit_fingerprint"))
        or _text(work_unit.get("source_fingerprint"))
        or hashlib.sha256(_work_unit_id(work_unit).encode("utf-8")).hexdigest()
    )
    runtime_health_epoch = (
        _text(controller_context.get("runtime_health_epoch"))
        or _text(current_owner_route.get("runtime_health_epoch"))
        or _text(work_unit.get("runtime_health_epoch"))
    )
    route_epoch = (
        _text(current_owner_route.get("truth_epoch"))
        or _text(controller_context.get("truth_epoch"))
        or f"paper-repair::{study_id}::{_work_unit_id(work_unit)}"
    )
    work_unit_id = _text(controller_context.get("work_unit_id")) or _work_unit_id(work_unit)
    return owner_route_part.ensure_owner_route_v2(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": quest_id,
            "truth_epoch": route_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_fingerprint": fingerprint,
            "failure_signature": action_type,
            "route_epoch": route_epoch,
            "source_fingerprint": fingerprint,
            "current_owner": "paper_repair_executor",
            "next_owner": "ai_reviewer",
            "owner_reason": action_type,
            "active_run_id": None,
            "allowed_actions": [action_type],
            "blocked_actions": [
                "runtime_platform_repair",
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "artifact_display_surface_materialization_required",
                "canonical_paper_inputs_rehydrate_required",
            ],
            "idempotency_key": f"paper-repair::{study_id}::{action_type}::{fingerprint}",
            "source_refs": {
                "paper_repair_work_unit": _work_unit_id(work_unit),
                "work_unit_id": work_unit_id,
                "runtime_health_epoch": runtime_health_epoch,
                "callable_surface": AI_REVIEWER_PUBLICATION_EVAL_CALLABLE,
            },
        }
    )


def _ai_reviewer_default_executor_dispatch(
    *,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    action_type: str,
    owner_route: Mapping[str, Any],
    dispatch_path: Path,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    repeat_key = repeat_suppression.repeat_key(owner_route)
    prompt_contract = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": dict(owner_route),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
        "source": SURFACE,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": ["artifacts/supervision/**"],
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": SCHEMA_VERSION,
        **default_executor_policy(),
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"paper-repair::{study_id}::{action_type}::{_work_unit_id(work_unit)}",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "dispatch_status": "ready",
        "dispatch_authority": "paper_repair_executor_inline_owner_dispatch",
        "owner_route": dict(owner_route),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": repeat_key,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "prompt_contract": prompt_contract,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "source_action": {
            "surface": SURFACE,
            "work_unit_id": _work_unit_id(work_unit),
            "work_unit_type": _text(work_unit.get("work_unit_type")),
            "callable_surface": AI_REVIEWER_PUBLICATION_EVAL_CALLABLE,
            "request_path": _text(request.get("path")),
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "request_packet_path": _text(request.get("path")),
        },
    }


def _ai_reviewer_recheck_gate_replay_ref(*, study_root: Path) -> Path:
    return study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"


def _owner_callable_result(
    *,
    generated_at: str,
    accepted: bool,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    owner_callable_surface: str,
    owner_result: Mapping[str, Any],
) -> dict[str, Any]:
    handoff_ready = owner_result_handoff_ready(owner_result)
    execution_status = "handoff_ready" if handoff_ready else ("executed" if accepted else "blocked")
    typed_blocker = None if accepted else owner_result_blocker(owner_result)
    changed_refs = _changed_refs_from_owner_result(owner_result)
    evidence_path = _owner_result_evidence_path(study_root=study_root, owner_result=owner_result)
    receipt = _owner_receipt(
        generated_at=generated_at,
        accepted=accepted,
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        work_unit=work_unit,
        execution_status=execution_status,
        typed_blocker=typed_blocker,
        changed_refs=changed_refs,
        evidence_path=evidence_path,
        gate_replay_ref=None,
        ai_reviewer_request=None,
    )
    receipt["owner_callable_surface"] = owner_callable_surface
    receipt["owner_result_status"] = _text(owner_result.get("status"))
    if handoff_ready:
        receipt["writer_worker_handoff"] = dict(_mapping(owner_result.get("writer_worker_handoff")))
    receipt_path = _write_owner_receipt(study_root=study_root, receipt=receipt)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "accepted": accepted,
        "execution_status": execution_status,
        "typed_blocker": typed_blocker,
        "study_id": study_id,
        "quest_id": quest_id,
        "repair_work_unit": dict(work_unit),
        "owner_callable_surface": owner_callable_surface,
        "owner_result": dict(owner_result),
        "owner_receipt": receipt,
        "owner_receipt_ref": str(receipt_path),
        "repair_execution_evidence_ref": str(evidence_path),
        "canonical_artifact_delta": _mapping(_mapping(owner_result.get("repair_execution_evidence")).get("canonical_artifact_delta")),
        **({"writer_worker_handoff": dict(_mapping(owner_result.get("writer_worker_handoff")))} if handoff_ready else {}),
        "authority_boundary": _authority_boundary(),
    }


def _owner_result_evidence_path(*, study_root: Path, owner_result: Mapping[str, Any]) -> Path:
    evidence_path = _text(owner_result.get("repair_execution_evidence_path"))
    if evidence_path:
        return Path(evidence_path).expanduser().resolve()
    return study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"


def _changed_refs_from_owner_result(owner_result: Mapping[str, Any]) -> list[dict[str, str]]:
    evidence = _mapping(owner_result.get("repair_execution_evidence"))
    refs = evidence.get("changed_artifact_refs")
    if isinstance(refs, list):
        changed: list[dict[str, str]] = []
        for ref in refs:
            path = _text(_mapping(ref).get("path")) or _text(ref)
            if path:
                changed.append({"path": path, "artifact_role": _text(_mapping(ref).get("artifact_role")) or "canonical_paper_artifact"})
        return changed
    return []


def _execute_supported_work_unit(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    work_unit_type: str,
    generated_at: str,
) -> list[dict[str, str]]:
    changed: list[Path] = []
    if _work_unit_updates_manuscript(work_unit=work_unit, work_unit_type=work_unit_type):
        changed.append(_update_manuscript(study_root=study_root, work_unit=work_unit, work_unit_type=work_unit_type))
    if work_unit_type in {"analysis_repair", "evidence_ledger_repair", "claim_downgrade", "route_decision"}:
        changed.append(
            _update_json_ledger(
                path=_evidence_ledger_path(study_root),
                entry_key="evidence_updates",
                entry=_repair_entry(
                    study_id=study_id,
                    quest_id=quest_id,
                    work_unit=work_unit,
                    work_unit_type=work_unit_type,
                    generated_at=generated_at,
                ),
            )
        )
    if work_unit_type in {"text_repair", "review_ledger_repair", "claim_downgrade", "route_decision"}:
        changed.append(
            _update_json_ledger(
                path=_review_ledger_path(study_root),
                entry_key="review_updates",
                entry=_repair_entry(
                    study_id=study_id,
                    quest_id=quest_id,
                    work_unit=work_unit,
                    work_unit_type=work_unit_type,
                    generated_at=generated_at,
                ),
            )
        )
    _append_revision_log(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        work_unit=work_unit,
        work_unit_type=work_unit_type,
        changed_paths=changed,
        generated_at=generated_at,
    )
    return [{"path": str(path), "artifact_role": _artifact_role(path)} for path in _dedupe_paths(changed)]


def _blocked_result(
    *,
    generated_at: str,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    review_finding: Mapping[str, Any] | None,
    typed_blocker: str,
) -> dict[str, Any]:
    evidence = paper_repair_execution_evidence.build_repair_execution_evidence(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        repair_work_unit=work_unit,
        review_finding=review_finding,
        source_refs=work_unit.get("source_refs") or [],
        changed_artifact_refs=[],
    )
    evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=study_root,
        evidence=evidence,
    )
    receipt = _owner_receipt(
        generated_at=generated_at,
        accepted=False,
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        work_unit=work_unit,
        execution_status="blocked",
        typed_blocker=typed_blocker,
        changed_refs=[],
        evidence_path=evidence_path,
        gate_replay_ref=None,
        ai_reviewer_request=None,
    )
    receipt_path = _write_owner_receipt(study_root=study_root, receipt=receipt)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "accepted": False,
        "execution_status": "blocked",
        "typed_blocker": typed_blocker,
        "study_id": study_id,
        "quest_id": quest_id,
        "repair_work_unit": dict(work_unit),
        "owner_receipt": receipt,
        "owner_receipt_ref": str(receipt_path),
        "repair_execution_evidence": evidence,
        "repair_execution_evidence_ref": str(evidence_path),
        "authority_boundary": _authority_boundary(),
    }


def _update_manuscript(*, study_root: Path, work_unit: Mapping[str, Any], work_unit_type: str) -> Path:
    path = _manuscript_path(study_root)
    existing = path.read_text(encoding="utf-8") if path.is_file() else "# Manuscript\n"
    target_claim = _text(work_unit.get("target_claim"))
    if work_unit_type == "claim_downgrade":
        replacement = f"{target_claim} [downgraded: current evidence does not support this claim]." if target_claim else None
        if target_claim and target_claim in existing:
            updated = existing.replace(target_claim, replacement or "")
        else:
            updated = existing.rstrip() + "\n\nThe claim is downgraded because current evidence does not support the original claim.\n"
    else:
        updated = _apply_structured_patch(existing=existing, work_unit=work_unit)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated if updated.endswith("\n") else updated + "\n", encoding="utf-8")
    return path


def _preflight_blocker(*, work_unit: Mapping[str, Any], work_unit_type: str) -> str | None:
    if work_unit_type == "text_repair" and not _has_structured_patch(work_unit):
        return STRUCTURED_PATCH_BLOCKER
    return None


def _work_unit_updates_manuscript(*, work_unit: Mapping[str, Any], work_unit_type: str) -> bool:
    if work_unit_type in {"text_repair", "claim_downgrade"}:
        return True
    return work_unit_type == "analysis_repair" and _has_structured_patch(work_unit)


def _has_structured_patch(work_unit: Mapping[str, Any]) -> bool:
    patch = _mapping(work_unit.get("canonical_patch"))
    if _text(patch.get("replacement_text")):
        return True
    if _text(patch.get("append_text")):
        return True
    return bool(_text(work_unit.get("replacement_text")) or _text(work_unit.get("append_text")))


def _apply_structured_patch(*, existing: str, work_unit: Mapping[str, Any]) -> str:
    patch = _mapping(work_unit.get("canonical_patch"))
    replacement_text = _text(patch.get("replacement_text")) or _text(work_unit.get("replacement_text"))
    append_text = _text(patch.get("append_text")) or _text(work_unit.get("append_text"))
    target_text = _text(patch.get("target_text")) or _text(work_unit.get("target_text"))
    target_claim = _text(work_unit.get("target_claim"))
    if replacement_text and target_text and target_text in existing:
        return existing.replace(target_text, replacement_text)
    if replacement_text and target_claim and target_claim in existing:
        return existing.replace(target_claim, replacement_text)
    if append_text:
        return existing.rstrip() + f"\n\n{append_text}\n"
    if replacement_text:
        return existing.rstrip() + f"\n\n{replacement_text}\n"
    return existing


def _update_json_ledger(*, path: Path, entry_key: str, entry: Mapping[str, Any]) -> Path:
    payload = _read_json(path)
    payload.setdefault("schema_version", 1)
    updates = payload.get(entry_key)
    if not isinstance(updates, list):
        updates = []
    updates.append(dict(entry))
    payload[entry_key] = updates
    if entry_key == "evidence_updates" and _mapping(entry.get("claim_policy")):
        claim_updates = payload.get("claim_updates")
        if not isinstance(claim_updates, list):
            claim_updates = []
        claim_updates.append({"claim_policy": dict(_mapping(entry.get("claim_policy"))), "source": SURFACE})
        payload["claim_updates"] = claim_updates
    _write_json(path, payload)
    return path


def _repair_entry(
    *,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    work_unit_type: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "generated_at": generated_at,
        "work_unit_id": _work_unit_id(work_unit),
        "work_unit_type": work_unit_type,
        "source_fingerprint": _text(work_unit.get("source_fingerprint")),
        "source_refs": list(work_unit.get("source_refs") or []),
        "claim_policy": dict(_mapping(work_unit.get("claim_policy"))),
        "gate_replay_target": _text(work_unit.get("gate_replay_target")) or "publication_eval/latest.json",
        "ai_reviewer_recheck_required": True,
    }


def _append_revision_log(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    work_unit_type: str,
    changed_paths: Iterable[Path],
    generated_at: str,
) -> Path:
    path = _revision_log_path(study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "surface": SURFACE,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "work_unit_id": _work_unit_id(work_unit),
        "work_unit_type": work_unit_type,
        "changed_artifact_refs": [str(path) for path in _dedupe_paths(changed_paths)],
        "gate_replay_required": True,
        "ai_reviewer_recheck_required": True,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _write_gate_replay_request(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    changed_refs: list[dict[str, str]],
    generated_at: str,
) -> Path:
    path = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    _write_json(
        path,
        {
            "surface": "paper_repair_gate_replay_request",
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "study_id": study_id,
            "quest_id": quest_id,
            "work_unit_id": _work_unit_id(work_unit),
            "target": _text(work_unit.get("gate_replay_target")) or "publication_eval/latest.json",
            "changed_artifact_refs": changed_refs,
            "authority_boundary": _authority_boundary(),
        },
    )
    return path


def _write_ai_reviewer_recheck_request(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit: Mapping[str, Any],
    gate_replay_ref: Path,
    generated_at: str,
    owner_route: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    refs = default_ai_reviewer_request_input_refs(study_root=study_root)
    packet = {
        "surface": "domain_action_request",
        "schema_version": SCHEMA_VERSION,
        "request_id": f"ai-reviewer-recheck::{study_id}::{_work_unit_id(work_unit)}",
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "repair_work_unit": dict(work_unit),
        "owner_route": dict(owner_route or _mapping(work_unit.get("owner_route"))),
        "input_contract": {
            "required_refs": refs,
            "all_required_refs_present": all(_mapping(ref).get("present") is True for ref in refs.values()),
            "missing_or_invalid_refs": [
                key for key, ref in refs.items() if _mapping(ref).get("present") is not True or _mapping(ref).get("valid") is not True
            ],
        },
        "required_output": {"path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "gate_replay_request_ref": str(gate_replay_ref),
        "request_lifecycle": {"state": "requested", "assigned_to": "ai_reviewer"},
        "authority_boundary": _authority_boundary(),
    }
    return materialize_ai_reviewer_request(study_root=study_root, packet=packet)


def _owner_receipt(
    *,
    generated_at: str,
    accepted: bool,
    study_id: str,
    quest_id: str,
    study_root: Path,
    work_unit: Mapping[str, Any],
    execution_status: str,
    typed_blocker: str | None,
    changed_refs: list[dict[str, str]],
    evidence_path: Path,
    gate_replay_ref: Path | None,
    ai_reviewer_request: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "surface": "paper_repair_owner_receipt",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "accepted": accepted,
        "study_id": study_id,
        "quest_id": quest_id,
        "work_unit_id": _work_unit_id(work_unit),
        "work_unit_type": _text(work_unit.get("work_unit_type")) or "unknown",
        "execution_status": execution_status,
        "typed_blocker": typed_blocker,
        "blocked_reason": typed_blocker,
        "canonical_artifact_delta_refs": changed_refs,
        "repair_execution_evidence_ref": str(evidence_path),
        "gate_replay_request_ref": str(gate_replay_ref) if gate_replay_ref is not None else None,
        "ai_reviewer_recheck_request_ref": (
            str(stable_ai_reviewer_request_path(study_root=study_root)) if ai_reviewer_request is not None else None
        ),
        "direct_current_package_write": False,
        "quality_authorized": False,
        "submission_authorized": False,
        "authority_boundary": _authority_boundary(),
    }


def _write_owner_receipt(*, study_root: Path, receipt: Mapping[str, Any]) -> Path:
    digest = hashlib.sha256(str(receipt.get("work_unit_id") or "repair_work_unit").encode("utf-8")).hexdigest()[:20]
    path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / f"{digest}.json"
    _write_json(path, receipt)
    _write_json(study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json", receipt)
    return path


def _would_write(work_unit_type: str) -> list[str]:
    if work_unit_type == "claim_downgrade":
        return ["paper/draft.md", "paper/evidence_ledger.json", "paper/review/review_ledger.json"]
    if work_unit_type == "text_repair":
        return ["paper/draft.md", "paper/review/review_ledger.json"]
    if work_unit_type == "evidence_ledger_repair":
        return ["paper/evidence_ledger.json"]
    if work_unit_type == "review_ledger_repair":
        return ["paper/review/review_ledger.json"]
    if work_unit_type == "analysis_repair":
        return ["paper/draft.md", "paper/evidence_ledger.json"]
    if work_unit_type == "route_decision":
        return ["paper/evidence_ledger.json", "paper/review/review_ledger.json"]
    return []


def _authority_boundary() -> dict[str, Any]:
    return {
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "writes_current_package": False,
        "quality_authorized": False,
        "submission_authorized": False,
    }


def _manuscript_path(study_root: Path) -> Path:
    draft = study_root / "paper" / "draft.md"
    if draft.exists() or not (study_root / "paper" / "manuscript.md").exists():
        return draft
    return study_root / "paper" / "manuscript.md"


def _evidence_ledger_path(study_root: Path) -> Path:
    return study_root / "paper" / "evidence_ledger.json"


def _review_ledger_path(study_root: Path) -> Path:
    return study_root / "paper" / "review" / "review_ledger.json"


def _revision_log_path(study_root: Path) -> Path:
    return study_root / "paper" / "revision_log.jsonl"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _work_unit_id(work_unit: Mapping[str, Any]) -> str:
    return _text(work_unit.get("unit_id")) or _text(work_unit.get("work_unit_id")) or "repair_work_unit"


def _artifact_role(path: Path) -> str:
    text = path.as_posix()
    if text.endswith("draft.md") or text.endswith("build/review_manuscript.md"):
        return "canonical_manuscript_story_surface"
    if text.endswith("manuscript.md"):
        return "legacy_canonical_manuscript"
    if text.endswith("evidence_ledger.json"):
        return "evidence_ledger"
    if text.endswith("review_ledger.json"):
        return "review_ledger"
    return "canonical_paper_artifact"


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if str(resolved) in seen:
            continue
        seen.add(str(resolved))
        result.append(resolved)
    return result


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = ["dispatch_repair_work_unit"]
