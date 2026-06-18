from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers.domain_owner_action_dispatch_parts.execution_surfaces import (
    ACCEPTED_EXECUTION_LATEST_SURFACES,
    LEGACY_EXECUTION_STUDY_LATEST_SURFACE,
    LEGACY_EXECUTION_SURFACE,
    OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE,
    OWNER_CALLABLE_RECEIPT_SURFACE,
)


EXECUTED_STATUSES = frozenset({"executed"})
EXECUTION_REF = Path("artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json")
LEGACY_EXECUTION_REF = Path("artifacts/supervision/consumer/default_executor_execution/latest.json")
CLOSEOUT_ROOT_REFS = (
    Path("artifacts/supervision/consumer/default_executor_execution"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
    Path("paper/review"),
    Path("paper/review/default_executor_closeouts"),
)
CLOSEOUT_SURFACES = frozenset(
    {
        "stage_attempt_closeout_packet",
        "domain_stage_closeout_packet",
    }
)


def default_executor_execution_candidates(
    *,
    study_root: Path,
    allow_legacy_fallback: bool = False,
) -> list[tuple[Mapping[str, Any], str]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    receipt, receipt_ref = _latest_execution_receipt(
        resolved_study_root,
        allow_legacy_fallback=allow_legacy_fallback,
    )
    candidates: list[tuple[Mapping[str, Any], str]] = []
    if _accepted_execution_receipt(receipt):
        candidates.extend(
            (_execution_from_receipt(execution), str(receipt_ref))
            for execution in reversed(_mapping_list(receipt.get("executions")))
        )
        candidates.extend(
            (_execution_from_receipt(execution), f"{receipt_ref}#execution_ledger")
            for execution in reversed(_mapping_list(receipt.get("execution_ledger")))
        )
    candidates.extend(_stage_closeout_candidates(study_root=resolved_study_root))
    return candidates


def latest_owner_callable_adapter_receipt_payload(
    *,
    study_root: Path,
    allow_legacy_fallback: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    receipt, receipt_ref = _latest_execution_receipt(
        resolved_study_root,
        allow_legacy_fallback=allow_legacy_fallback,
    )
    if not _accepted_execution_receipt(receipt):
        return None, str(receipt_ref)
    payload = dict(receipt)
    payload["executions"] = [
        _execution_from_receipt(execution)
        for execution in _mapping_list(receipt.get("executions"))
    ]
    payload["execution_ledger"] = [
        _execution_from_receipt(execution)
        for execution in _mapping_list(receipt.get("execution_ledger"))
    ]
    payload.setdefault("canonical_surface", OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE)
    payload.setdefault("owner_callable_receipt_projection", True)
    payload.setdefault("projection_authority", False)
    payload.setdefault("execution_ledger_authority", False)
    payload.setdefault("attempt_lifecycle_authority", False)
    payload.setdefault("queue_authority", False)
    if receipt_ref == LEGACY_EXECUTION_REF:
        payload.setdefault("legacy_surface_alias", "default_executor_dispatch_execution_study_latest")
        payload.setdefault("legacy_wire_surface", "default_executor_dispatch_execution_study_latest")
    return payload, str(receipt_ref)


def latest_owner_callable_adapter_receipt_candidates(
    *,
    study_root: Path,
    allow_legacy_fallback: bool = False,
) -> list[tuple[Mapping[str, Any], str]]:
    receipt, receipt_ref = latest_owner_callable_adapter_receipt_payload(
        study_root=study_root,
        allow_legacy_fallback=allow_legacy_fallback,
    )
    if receipt is None:
        return []
    candidates: list[tuple[Mapping[str, Any], str]] = []
    candidates.extend(
        (execution, receipt_ref)
        for execution in _mapping_list(receipt.get("executions"))
    )
    candidates.extend(
        (execution, f"{receipt_ref}#execution_ledger")
        for execution in _mapping_list(receipt.get("execution_ledger"))
    )
    return candidates


def _execution_from_receipt(execution: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _canonical_owner_callable_receipt(execution)
    route = _receipt_execution_owner_route(execution)
    route_source_refs = _mapping(route.get("source_refs"))
    route_currentness_basis = _mapping(route_source_refs.get("owner_route_currentness_basis"))
    work_unit_id = (
        _text(execution.get("work_unit_id"))
        or _text(route_currentness_basis.get("work_unit_id"))
        or _text(route_source_refs.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(execution.get("work_unit_fingerprint"))
        or _text(execution.get("action_fingerprint"))
        or _text(route_currentness_basis.get("work_unit_fingerprint"))
        or _text(route_source_refs.get("work_unit_fingerprint"))
        or _text(route.get("work_unit_fingerprint"))
    )
    source_eval_id = (
        _text(execution.get("source_eval_id"))
        or _text(route_currentness_basis.get("source_eval_id"))
        or _text(route_source_refs.get("source_eval_id"))
        or _text(route.get("source_eval_id"))
    )
    canonical_work_unit_identity = route_currentness_basis or {
        key: value
        for key, value in {
            "source_eval_id": source_eval_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "work_unit_id": work_unit_id,
        }.items()
        if value
    }
    if work_unit_id:
        normalized["work_unit_id"] = work_unit_id
    if work_unit_fingerprint:
        normalized["work_unit_fingerprint"] = work_unit_fingerprint
        normalized["action_fingerprint"] = work_unit_fingerprint
    if source_eval_id:
        normalized["source_eval_id"] = source_eval_id
    if route:
        normalized.setdefault("current_owner_route", route)
        normalized.setdefault("owner_route", route)
    if route_currentness_basis:
        normalized["owner_route_currentness_basis"] = route_currentness_basis
    if canonical_work_unit_identity:
        normalized["canonical_work_unit_identity"] = canonical_work_unit_identity
    return normalized


def _latest_execution_receipt(
    study_root: Path,
    *,
    allow_legacy_fallback: bool = False,
) -> tuple[dict[str, Any] | None, Path]:
    canonical = _read_json_object(study_root / EXECUTION_REF)
    if canonical is not None:
        return canonical, EXECUTION_REF
    if not allow_legacy_fallback:
        return None, EXECUTION_REF
    legacy = _read_json_object(study_root / LEGACY_EXECUTION_REF)
    if legacy is not None and not _text(legacy.get("surface")):
        legacy = {
            **legacy,
            "surface": LEGACY_EXECUTION_STUDY_LATEST_SURFACE,
            "legacy_wire_surface": LEGACY_EXECUTION_STUDY_LATEST_SURFACE,
            "canonical_surface": OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE,
            "projection_authority": False,
            "attempt_lifecycle_authority": False,
            "queue_authority": False,
        }
    return legacy, LEGACY_EXECUTION_REF


def _accepted_execution_receipt(receipt: Mapping[str, Any] | None) -> bool:
    if receipt is None:
        return False
    return (
        _text(receipt.get("surface")) in ACCEPTED_EXECUTION_LATEST_SURFACES
        or _text(receipt.get("canonical_surface")) == OWNER_CALLABLE_RECEIPT_STUDY_LATEST_SURFACE
    )


def _canonical_owner_callable_receipt(execution: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(execution)
    surface = _text(normalized.get("surface"))
    canonical_surface = _text(normalized.get("canonical_surface"))
    if surface == OWNER_CALLABLE_RECEIPT_SURFACE:
        normalized["canonical_surface"] = OWNER_CALLABLE_RECEIPT_SURFACE
        return normalized
    if surface == LEGACY_EXECUTION_SURFACE or canonical_surface == OWNER_CALLABLE_RECEIPT_SURFACE:
        normalized["surface"] = OWNER_CALLABLE_RECEIPT_SURFACE
        normalized["canonical_surface"] = OWNER_CALLABLE_RECEIPT_SURFACE
        normalized.setdefault("legacy_surface_alias", LEGACY_EXECUTION_SURFACE)
        normalized.setdefault("legacy_wire_surface", LEGACY_EXECUTION_SURFACE)
    return normalized


def _receipt_execution_owner_route(execution: Mapping[str, Any]) -> Mapping[str, Any]:
    return (
        _mapping(execution.get("current_owner_route"))
        or _mapping(execution.get("owner_route"))
        or _mapping(_mapping(execution.get("prompt_contract")).get("owner_route"))
    )


def _stage_closeout_candidates(*, study_root: Path) -> list[tuple[Mapping[str, Any], str]]:
    candidates: list[tuple[Mapping[str, Any], str]] = []
    seen: set[str] = set()
    for closeout_root_ref in CLOSEOUT_ROOT_REFS:
        closeout_root = study_root / closeout_root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in sorted(closeout_root.glob("*.json"), reverse=True):
            resolved = str(closeout_path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            closeout = _read_json_object(closeout_path)
            if closeout is None:
                continue
            execution = _execution_from_stage_closeout(
                closeout=closeout,
                study_root=study_root,
                closeout_ref=Path(_study_relative_ref(study_root=study_root, path=closeout_path)),
            )
            if execution is not None:
                candidates.append((execution, str(execution["receipt_ref"])))
    return candidates


def _execution_from_stage_closeout(
    *,
    closeout: Mapping[str, Any],
    study_root: Path,
    closeout_ref: Path,
) -> dict[str, Any] | None:
    if _text(closeout.get("surface_kind")) not in CLOSEOUT_SURFACES:
        return None
    if _text(closeout.get("stage_id")) != "domain_owner/default-executor-dispatch":
        return None
    action_type = _text(closeout.get("action_type"))
    if not action_type:
        return None
    route, route_source = _stage_closeout_owner_route(closeout=closeout, study_root=study_root)
    route_source_refs = _mapping(route.get("source_refs"))
    route_currentness_basis = _mapping(route_source_refs.get("owner_route_currentness_basis"))
    work_unit_id = (
        _text(closeout.get("work_unit_id"))
        or _text(route_currentness_basis.get("work_unit_id"))
        or _text(route_source_refs.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(closeout.get("work_unit_fingerprint"))
        or _text(closeout.get("action_fingerprint"))
        or _text(route_currentness_basis.get("work_unit_fingerprint"))
        or _text(route_source_refs.get("work_unit_fingerprint"))
        or _text(route.get("work_unit_fingerprint"))
    )
    source_eval_id = (
        _text(closeout.get("source_eval_id"))
        or _text(route_currentness_basis.get("source_eval_id"))
        or _text(route_source_refs.get("source_eval_id"))
        or _text(route.get("source_eval_id"))
    )
    repair_evidence = _stage_closeout_repair_evidence(closeout)
    owner_receipt = _mapping(closeout.get("owner_receipt"))
    domain_execution = _mapping(closeout.get("domain_execution"))
    closeout_blocked_reason = _stage_closeout_blocked_reason(
        closeout=closeout,
        owner_receipt=owner_receipt,
        domain_execution=domain_execution,
    )
    explicit_user_stage_log = _stage_closeout_user_stage_log(closeout)
    user_stage_log = explicit_user_stage_log or _fallback_stage_closeout_user_stage_log(
        closeout=closeout,
        action_type=action_type,
        owner_receipt=owner_receipt,
        domain_execution=domain_execution,
        repair_evidence=repair_evidence,
        blocked_reason=closeout_blocked_reason,
    )
    missing_user_stage_log_fields = _missing_user_stage_log_fields(
        action_type=action_type,
        user_stage_log=user_stage_log,
    )
    incomplete_user_stage_log_reason = (
        "domain_closeout_provided_incomplete_user_stage_log"
        if missing_user_stage_log_fields
        else ""
    )
    stage_packet_ref = _text(closeout.get("stage_packet_ref")) or _text(closeout.get("stage_packet_path"))
    stage_packet_refs = _stage_closeout_stage_packet_refs(closeout)
    dispatch_ref = _text(closeout.get("dispatch_ref")) or stage_packet_ref
    return {
        "surface": OWNER_CALLABLE_RECEIPT_SURFACE,
        "canonical_surface": OWNER_CALLABLE_RECEIPT_SURFACE,
        "legacy_surface_alias": LEGACY_EXECUTION_SURFACE,
        "legacy_wire_surface": LEGACY_EXECUTION_SURFACE,
        "schema_version": 1,
        "study_id": _text(closeout.get("study_id")),
        "quest_id": _text(closeout.get("quest_id")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "raw_closeout_work_unit_fingerprint_present": bool(_text(closeout.get("work_unit_fingerprint"))),
        "raw_closeout_action_fingerprint_present": bool(_text(closeout.get("action_fingerprint"))),
        "source_eval_id": source_eval_id,
        "execution_status": _stage_closeout_execution_status(closeout),
        "execution_id": _text(closeout.get("execution_id"))
        or _text(closeout.get("closeout_id"))
        or _text(closeout.get("stage_attempt_id")),
        "source_fingerprint": _text(closeout.get("source_fingerprint"))
        or _text(route.get("source_fingerprint")),
        "idempotency_key": _text(closeout.get("idempotency_key")) or _text(route.get("idempotency_key")),
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": stage_packet_refs,
        "current_owner_route": route or None,
        "owner_route": route or None,
        "owner_route_currentness_basis": route_currentness_basis or None,
        "canonical_work_unit_identity": route_currentness_basis or {
            key: value
            for key, value in {
                "source_eval_id": source_eval_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": work_unit_id,
            }.items()
            if value
        },
        "owner_route_currentness_source": route_source,
        "stage_closeout_surface_kind": _text(closeout.get("surface_kind")),
        "stage_closeout_status": _text(closeout.get("status")),
        "stage_closeout_refs": _text_list(closeout.get("closeout_refs")),
        "stage_closeout_outcome": (
            "typed_blocker" if incomplete_user_stage_log_reason else _stage_closeout_outcome(closeout)
        ),
        "typed_blocker_reason": (
            _text(closeout.get("typed_blocker_reason"))
            or incomplete_user_stage_log_reason
            or _stage_closeout_gate_replay_blocked_reason(closeout)
        ),
        "typed_blocker_ref": (
            _text(closeout.get("typed_blocker_ref"))
            or (str(closeout_ref) if incomplete_user_stage_log_reason else "")
            or _stage_closeout_gate_replay_report_ref(closeout)
        ),
        "owner_receipt_ref": _text(closeout.get("owner_receipt_ref")),
        "stage_closeout_required_ref_field": _text(
            _mapping(closeout.get("required_closeout_packet")).get("required_ref_field")
        )
        or "closeout_refs",
        "stage_attempt_id": _text(closeout.get("stage_attempt_id")),
        "typed_blocker": _mapping(closeout.get("typed_blocker")),
        "paper_stage_log": user_stage_log or {},
        "missing_user_stage_log_fields": missing_user_stage_log_fields,
        "missing_domain_fields": missing_user_stage_log_fields,
        "semantic_gap": (
            {
                "reason": incomplete_user_stage_log_reason,
                "missing_domain_fields": missing_user_stage_log_fields,
                "source": "paper_stage_log",
                "owner": "MedAutoScience",
            }
            if incomplete_user_stage_log_reason
            else {}
        ),
        "owner_result": {
            "status": (
                "blocked"
                if incomplete_user_stage_log_reason
                else (
                    _text(owner_receipt.get("status"))
                    or _text(closeout.get("route_outcome"))
                    or _stage_closeout_owner_result_status(closeout)
                    or _text(closeout.get("status"))
                )
            ),
            "owner": _text(owner_receipt.get("owner")),
            "owner_receipt_ref": _text(closeout.get("owner_receipt_ref")),
            "owner_callable_surface": _text(owner_receipt.get("owner_callable_surface")),
            "publication_eval_record_ref": _text(owner_receipt.get("publication_eval_record_ref")),
            "record_only_surface": owner_receipt.get("record_only_surface"),
            "publication_eval_surface": _text(owner_receipt.get("publication_eval_surface")),
            "publication_eval_latest_write_authorized": owner_receipt.get("publication_eval_latest_write_authorized"),
            "controller_decision_write_authorized": owner_receipt.get("controller_decision_write_authorized"),
            "ok": _stage_closeout_has_story_surface_delta(closeout),
            "blocked_reason": incomplete_user_stage_log_reason or closeout_blocked_reason,
            "blocked_reasons": list(owner_receipt.get("blocked_reasons") or []),
            "dispatcher_result": _mapping(domain_execution.get("dispatcher_result")),
            "repair_execution_evidence": _repair_evidence_with_user_stage_log_gap(
                repair_evidence=repair_evidence,
                reason=incomplete_user_stage_log_reason,
                missing_fields=missing_user_stage_log_fields,
            ),
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
        "receipt_ref": str(closeout_ref),
    }


def _stage_closeout_user_stage_log(closeout: Mapping[str, Any]) -> Mapping[str, Any]:
    for field in ("paper_stage_log", "user_stage_log", "stage_log_summary"):
        value = _mapping(closeout.get(field))
        if value:
            return value
    route_impact = _mapping(closeout.get("route_impact"))
    for field in ("paper_stage_log", "user_stage_log", "stage_log_summary"):
        value = _mapping(route_impact.get(field))
        if value:
            return value
    return {}


def _fallback_stage_closeout_user_stage_log(
    *,
    closeout: Mapping[str, Any],
    action_type: str,
    owner_receipt: Mapping[str, Any],
    domain_execution: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
    blocked_reason: str,
) -> dict[str, Any]:
    changed_surfaces = [
        _text(item.get("path"))
        for item in _mapping_list(repair_evidence.get("changed_artifact_refs"))
        if _text(item.get("path"))
    ]
    status = _text(owner_receipt.get("status")) or _text(closeout.get("route_outcome")) or _text(closeout.get("status"))
    outcome = "typed_blocker" if blocked_reason else status
    deliverable_count = 1 if changed_surfaces else 0
    platform_repair_count = 0 if changed_surfaces else (1 if blocked_reason else 0)
    return {
        "surface_kind": "mas_paper_facing_stage_log_summary",
        "schema_version": 1,
        "status": "available",
        "stage_name": _text(closeout.get("work_unit_id")) or action_type,
        "problem_summary": (
            f"{action_type} ended with typed blocker {blocked_reason}."
            if blocked_reason
            else f"{action_type} produced closeout refs for the current owner route."
        ),
        "stage_goal": _text(owner_receipt.get("required_output_surface"))
        or _text(domain_execution.get("required_output_surface"))
        or f"Complete the owner-authorized {action_type} work unit or return a typed blocker.",
        "stage_work_done": [
            _text(owner_receipt.get("publication_eval_record_ref"))
            or _text(owner_receipt.get("owner_callable_surface"))
            or _text(repair_evidence.get("status"))
            or _text(closeout.get("route_outcome"))
            or _text(closeout.get("status"))
            or "terminal closeout observed"
        ],
        "paper_work_done": [
            _text(owner_receipt.get("publication_eval_record_ref"))
            or _text(owner_receipt.get("owner_callable_surface"))
            or _text(repair_evidence.get("status"))
            or _text(closeout.get("route_outcome"))
            or _text(closeout.get("status"))
            or "terminal closeout observed"
        ],
        "changed_stage_surfaces": changed_surfaces,
        "changed_paper_surfaces": changed_surfaces,
        "outcome": outcome,
        "remaining_blockers": [blocked_reason] if blocked_reason else [],
        "duration": {"status": "missing", "value": None},
        "token_usage": {"status": "missing", "value": None, "total_tokens": None},
        "cost": {"status": "missing", "value": None, "total_cost": None},
        "usage_refs": [],
        "cost_refs": [],
        "progress_delta_classification": (
            "deliverable_progress"
            if changed_surfaces
            else ("typed_blocker" if blocked_reason else "platform_repair")
        ),
        "deliverable_progress_delta": {"count": deliverable_count, "token_usage_total": None},
        "paper_progress_delta": {"count": deliverable_count, "token_usage_total": None},
        "platform_repair_delta": {"count": platform_repair_count, "token_usage_total": None},
        "next_forced_delta": {
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "work_unit_id": _text(closeout.get("work_unit_id")) or action_type,
            "owner_action": {
                "next_owner": _text(closeout.get("next_owner")) or _text(owner_receipt.get("owner")),
                "action_type": action_type,
                "work_unit_id": _text(closeout.get("work_unit_id")) or action_type,
            },
            "reason": f"typed_blocker::{blocked_reason}" if blocked_reason else "terminal_closeout_observed",
        },
        "evidence_refs": _text_list(closeout.get("closeout_refs")),
        "fallback_source": "stage_closeout_structured_fields",
    }


def _missing_user_stage_log_fields(
    *,
    action_type: str,
    user_stage_log: Mapping[str, Any],
) -> list[str]:
    required = default_executor_typed_closeout_contract(action_type=action_type)[
        "required_user_stage_log_fields"
    ]
    return [
        field
        for field in required
        if _user_stage_log_field_missing(user_stage_log, field)
    ]


def _user_stage_log_field_missing(user_stage_log: Mapping[str, Any], field: str) -> bool:
    if field not in user_stage_log:
        return True
    if field in {
        "changed_stage_surfaces",
        "changed_paper_surfaces",
        "remaining_blockers",
        "usage_refs",
        "cost_refs",
        "evidence_refs",
    }:
        return False
    value = user_stage_log.get(field)
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, list | tuple | set):
        return False if field in {"deliverable_progress_delta", "paper_progress_delta", "platform_repair_delta"} else not value
    return value in (None, "")


def _repair_evidence_with_user_stage_log_gap(
    *,
    repair_evidence: Mapping[str, Any],
    reason: str,
    missing_fields: list[str],
) -> dict[str, Any]:
    if not reason:
        return dict(repair_evidence)
    blockers = _text_list(repair_evidence.get("blockers"))
    if reason not in blockers:
        blockers.append(reason)
    payload = dict(repair_evidence)
    payload["status"] = "typed_blocker"
    payload["blocked_reason"] = reason
    payload["blockers"] = blockers
    payload["missing_domain_fields"] = list(missing_fields)
    payload["semantic_gap"] = {
        "reason": reason,
        "missing_domain_fields": list(missing_fields),
        "source": "paper_stage_log",
        "owner": "MedAutoScience",
    }
    return payload


def _stage_closeout_owner_result_status(closeout: Mapping[str, Any]) -> str | None:
    if _stage_closeout_outcome(closeout) == "typed_blocker":
        return "blocked"
    return None


def _stage_closeout_outcome(closeout: Mapping[str, Any]) -> str:
    return _text(closeout.get("outcome")) or ("typed_blocker" if _stage_closeout_gate_replay_blocked_reason(closeout) else "")


def _stage_closeout_blocked_reason(
    *,
    closeout: Mapping[str, Any],
    owner_receipt: Mapping[str, Any],
    domain_execution: Mapping[str, Any],
) -> str:
    return (
        _text(domain_execution.get("blocked_reason"))
        or _text(owner_receipt.get("typed_blocker"))
        or _text(closeout.get("typed_blocker_reason"))
        or _stage_closeout_gate_replay_blocked_reason(closeout)
        or _text(closeout.get("blocked_reason"))
    )


def _stage_closeout_gate_replay_blocked_reason(closeout: Mapping[str, Any]) -> str:
    if _text(closeout.get("action_type")) != "run_gate_clearing_batch":
        return ""
    domain_execution = _mapping(closeout.get("domain_execution"))
    gate_replay = _mapping(closeout.get("gate_replay"))
    if (
        _text(domain_execution.get("gate_replay_status")) == "blocked"
        or _text(domain_execution.get("publication_work_unit_lifecycle_status")) == "blocked"
        or _text(gate_replay.get("status")) == "blocked"
    ):
        return "publication_gate_replay_blocked"
    return ""


def _stage_closeout_gate_replay_report_ref(closeout: Mapping[str, Any]) -> str:
    domain_execution = _mapping(closeout.get("domain_execution"))
    gate_replay = _mapping(closeout.get("gate_replay"))
    return _text(domain_execution.get("publication_gate_report_json")) or _text(gate_replay.get("report_json"))


def _stage_closeout_execution_status(closeout: Mapping[str, Any]) -> str:
    domain_execution_status = _text(_mapping(closeout.get("domain_execution")).get("execution_status"))
    if domain_execution_status in EXECUTED_STATUSES:
        return domain_execution_status
    if _text(closeout.get("execution_status")) in EXECUTED_STATUSES:
        return _text(closeout.get("execution_status"))
    if _text(closeout.get("route_outcome")) == "write_repair_delta_recorded" and _stage_closeout_has_story_surface_delta(
        closeout
    ):
        return "executed"
    return domain_execution_status or "executed"


def _stage_closeout_owner_route(*, closeout: Mapping[str, Any], study_root: Path) -> tuple[dict[str, Any], str]:
    basis = (
        _mapping(closeout.get("owner_route_basis"))
        or _mapping(closeout.get("owner_route_currentness"))
        or _mapping(closeout.get("owner_route_currentness_basis"))
    )
    if not basis:
        basis = {
            "truth_epoch": _text(closeout.get("truth_epoch")),
            "source_eval_id": _text(closeout.get("source_eval_id")),
            "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint")),
            "work_unit_id": _text(closeout.get("work_unit_id")),
            "owner_reason": _text(closeout.get("owner_reason")),
        }
    stage_packet_route = _stage_closeout_stage_packet_owner_route(closeout=closeout, study_root=study_root)
    if stage_packet_route and _stage_closeout_basis_missing_required_currentness(basis):
        return stage_packet_route, "stage_packet_ref_recovered"
    if any(_text(basis.get(key)) for key in ("truth_epoch", "work_unit_fingerprint", "work_unit_id", "owner_reason")):
        action_type = _text(closeout.get("action_type"))
        owner = (
            _text(closeout.get("owner"))
            or _text(_mapping(closeout.get("domain_execution")).get("domain_owner"))
            or _stage_closeout_default_owner(action_type)
        )
        return {
            "truth_epoch": _text(basis.get("truth_epoch")),
            "route_epoch": _text(basis.get("truth_epoch")),
            "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
            "source_eval_id": _text(basis.get("source_eval_id")),
            "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
            "source_fingerprint": _text(stage_packet_route.get("source_fingerprint")),
            "idempotency_key": _text(stage_packet_route.get("idempotency_key")),
            "next_owner": "write" if owner in {"quality_repair_batch", "write"} else owner,
            "owner_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
            "allowed_actions": [action_type] if action_type else [],
            "source_refs": {
                "owner_route_currentness_basis": {
                    "truth_epoch": _text(basis.get("truth_epoch")),
                    "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
                    "source_eval_id": _text(basis.get("source_eval_id")),
                    "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
                    "work_unit_id": _text(basis.get("work_unit_id")),
                    "owner_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
                },
                "study_truth_epoch": _text(basis.get("truth_epoch")),
                "runtime_health_epoch": _text(basis.get("runtime_health_epoch")),
                "source_eval_id": _text(basis.get("source_eval_id")),
                "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint")),
                "work_unit_id": _text(basis.get("work_unit_id")),
                "blocked_reason": _text(basis.get("owner_reason")) or _text(closeout.get("blocked_reason")),
            },
        }, "embedded_currentness_basis"
    if stage_packet_route:
        return stage_packet_route, "stage_packet_ref_recovered"
    return {}, "missing"


def _stage_closeout_basis_missing_required_currentness(basis: Mapping[str, Any]) -> bool:
    if not basis:
        return True
    return not (
        _text(basis.get("truth_epoch"))
        and _text(basis.get("work_unit_fingerprint"))
        and _text(basis.get("work_unit_id"))
    )


def _stage_closeout_default_owner(action_type: str | None) -> str | None:
    if action_type == "run_quality_repair_batch":
        return "write"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "current_package_freshness_required":
        return "artifact_os"
    return None


def _stage_closeout_stage_packet_owner_route(*, closeout: Mapping[str, Any], study_root: Path) -> dict[str, Any]:
    stage_packet_ref = _text(closeout.get("stage_packet_ref"))
    if not stage_packet_ref:
        return {}
    stage_packet = _stage_closeout_resolved_stage_packet(
        closeout=closeout,
        study_root=study_root,
        stage_packet_ref=stage_packet_ref,
    )
    if stage_packet is None:
        return {}
    if _text(stage_packet.get("action_type")) != _text(closeout.get("action_type")):
        return {}
    if _text(stage_packet.get("study_id")) != _text(closeout.get("study_id")):
        return {}
    return dict(_mapping(stage_packet.get("owner_route")) or _mapping(_mapping(stage_packet.get("prompt_contract")).get("owner_route")))


def _stage_closeout_resolved_stage_packet(
    *,
    closeout: Mapping[str, Any],
    study_root: Path,
    stage_packet_ref: str,
) -> dict[str, Any] | None:
    if _stage_packet_ref_has_immutable_owner_route_identity(stage_packet_ref):
        return _read_json_object(_resolve_study_workspace_ref(study_root=study_root, ref=stage_packet_ref))
    for immutable_ref in _stage_closeout_immutable_dispatch_refs(closeout):
        stage_packet = _read_json_object(_resolve_study_workspace_ref(study_root=study_root, ref=immutable_ref))
        if stage_packet is None:
            continue
        if _text(stage_packet.get("action_type")) != _text(closeout.get("action_type")):
            continue
        if _text(stage_packet.get("study_id")) != _text(closeout.get("study_id")):
            continue
        return stage_packet
    return None


def _stage_closeout_immutable_dispatch_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = _text_list(closeout.get("closeout_refs"))
    refs.extend(_text_list(closeout.get("evidence_refs")))
    refs.extend(_text_list(_mapping(closeout.get("domain_execution")).get("closeout_refs")))
    return [ref for ref in refs if _stage_packet_ref_has_immutable_owner_route_identity(ref)]


def _stage_closeout_stage_packet_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = _text_list(closeout.get("stage_packet_refs"))
    for ref in (
        _text(closeout.get("stage_packet_ref")),
        _text(closeout.get("stage_packet_path")),
        *_stage_closeout_immutable_dispatch_refs(closeout),
    ):
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def _stage_packet_ref_has_immutable_owner_route_identity(stage_packet_ref: str) -> bool:
    parts = Path(stage_packet_ref).parts
    if "default_executor_dispatches" not in parts:
        return False
    dispatch_index = parts.index("default_executor_dispatches")
    return len(parts) > dispatch_index + 1 and parts[dispatch_index + 1] == "immutable"


def _stage_closeout_repair_evidence(closeout: Mapping[str, Any]) -> dict[str, Any]:
    artifact_delta = _mapping(closeout.get("artifact_delta"))
    domain_owner_evidence = _mapping(closeout.get("domain_owner_evidence"))
    changed_refs = _stage_closeout_changed_artifact_refs(artifact_delta.get("changed_artifact_refs"))
    story_delta_present = _stage_closeout_has_story_surface_delta(closeout)
    return {
        "status": (
            _text(domain_owner_evidence.get("repair_execution_status"))
            or _text(artifact_delta.get("status"))
            or _text(closeout.get("route_outcome"))
            or _text(closeout.get("status"))
        ),
        "changed_artifact_refs": changed_refs,
        "manuscript_surface_hygiene": {
            "status": _text(domain_owner_evidence.get("manuscript_surface_hygiene_status"))
            or _text(_mapping(artifact_delta.get("manuscript_surface_hygiene")).get("status")),
            "story_surface_delta_required": _text(closeout.get("action_type")) == "run_quality_repair_batch",
            "story_surface_delta_present": story_delta_present,
            "blockers": _mapping(artifact_delta.get("manuscript_surface_hygiene")).get("blockers") or [],
        },
        "gate_replay_done": domain_owner_evidence.get("gate_replay_done"),
        "ai_reviewer_recheck_required": domain_owner_evidence.get("ai_reviewer_recheck_required"),
        "ai_reviewer_recheck_done": domain_owner_evidence.get("ai_reviewer_recheck_done"),
    }


def _stage_closeout_changed_artifact_refs(value: object) -> list[Mapping[str, Any]]:
    refs: list[Mapping[str, Any]] = []
    for item in value or []:
        if isinstance(item, Mapping):
            refs.append(item)
        elif text := _text(item):
            refs.append({"path": text})
    return refs


def _stage_closeout_has_story_surface_delta(closeout: Mapping[str, Any]) -> bool:
    artifact_delta = _mapping(closeout.get("artifact_delta"))
    domain_owner_evidence = _mapping(closeout.get("domain_owner_evidence"))
    if domain_owner_evidence.get("story_surface_delta_present") is True:
        return True
    if artifact_delta.get("story_surface_delta_present") is True:
        return True
    return bool(_story_surface_changed_refs(_stage_closeout_changed_artifact_refs(artifact_delta.get("changed_artifact_refs"))))


def _story_surface_changed_refs(value: object) -> list[Mapping[str, Any]]:
    return [
        ref
        for ref in _mapping_list(value)
        if _is_story_surface_path(_text(ref.get("path")))
    ]


def _is_story_surface_path(path_text: str) -> bool:
    path = Path(path_text).expanduser()
    parts = path.parts
    return (
        len(parts) >= 2
        and parts[-2:] == ("paper", "draft.md")
        or len(parts) >= 3
        and parts[-3:] == ("paper", "build", "review_manuscript.md")
    )


def _resolve_study_workspace_ref(*, study_root: Path, ref: str) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "studies":
        workspace_root = _workspace_root_from_study_root(study_root)
        if workspace_root is not None:
            return workspace_root / path
    return study_root / path


def _workspace_root_from_study_root(study_root: Path) -> Path | None:
    resolved = study_root.expanduser().resolve()
    if resolved.parent.name == "studies":
        return resolved.parent.parent
    return None


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return str(resolved_path.relative_to(study_root.expanduser().resolve()))
    except ValueError:
        return str(resolved_path)


def _read_json_object(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "EXECUTION_REF",
    "LEGACY_EXECUTION_REF",
    "default_executor_execution_candidates",
    "latest_owner_callable_adapter_receipt_candidates",
    "latest_owner_callable_adapter_receipt_payload",
]
