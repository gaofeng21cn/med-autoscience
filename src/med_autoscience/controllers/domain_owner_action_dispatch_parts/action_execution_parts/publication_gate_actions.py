from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from ... import gate_clearing_batch, publication_gate


def execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    quest_root: Path | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.run_controller",
            "quest_root": str(quest_root),
        }
    state = publication_gate.build_gate_state(quest_root)
    report = publication_gate.build_gate_report(state)
    json_path, _ = publication_gate.write_gate_files(quest_root, report)
    report_with_refs = _publication_gate_report_with_refs(report=report, state=state, json_path=json_path)
    materialized = publication_gate._materialize_publication_eval_latest(state=state, report=report_with_refs)
    if materialized is None and getattr(state, "study_root", None) is not None:
        decision_module = publication_gate.import_module("med_autoscience.controllers.study_runtime_decision")
        materialized = decision_module._materialize_publication_eval_from_gate_report(
            study_root=state.study_root,
            study_id=study_id,
            quest_root=quest_root,
            quest_id=quest_root.name,
            publication_gate_report=report_with_refs,
        )
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        "quest_root": str(quest_root),
        "owner_result": {
            "report_json": str(json_path),
            "status": report.get("status"),
            "blockers": list(report.get("blockers") or []),
            "publication_eval": materialized,
        },
    }


def execute_current_package_freshness(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    quest_root: Path | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "quest_root": str(quest_root),
        }
    try:
        owner_result = _run_current_package_gate_clearing_batch(profile=profile, study_id=study_id, quest_root=quest_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return _blocked_current_package_freshness(exc=exc, quest_root=quest_root)
    executed = bool(owner_result.get("ok")) if isinstance(owner_result, Mapping) else False
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(_mapping(owner_result).get("status")) or "gate_clearing_batch_not_applied",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(quest_root),
    }


def execute_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    quest_root: Path | None,
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    authority_route_context = _gate_clearing_authority_route_context(dispatch)
    if authority_route_context is None:
        return {
            "execution_status": "blocked",
            "blocked_reason": "gate_clearing_batch_work_unit_missing",
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "quest_root": str(quest_root),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "quest_root": str(quest_root),
            "authority_route_context": authority_route_context,
        }
    try:
        owner_result = _run_gate_clearing_batch(
            profile=profile,
            study_id=study_id,
            quest_root=quest_root,
            authority_route_context=authority_route_context,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return _blocked_gate_clearing_batch(exc=exc, quest_root=quest_root)
    executed = bool(owner_result.get("ok")) if isinstance(owner_result, Mapping) else False
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(_mapping(owner_result).get("status")) or "gate_clearing_batch_not_applied",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(quest_root),
    }


def _publication_gate_report_with_refs(*, report: Mapping[str, Any], state: Any, json_path: Path) -> dict[str, Any]:
    return {
        **dict(report),
        "latest_gate_path": str(json_path),
        "main_result_path": str(state.main_result_path) if getattr(state, "main_result_path", None) else None,
        "paper_root": str(state.paper_root) if getattr(state, "paper_root", None) else None,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path)
            if getattr(state, "submission_minimal_manifest_path", None)
            else None
        ),
        "force_publication_gate_specificity_refresh": True,
    }


def _run_current_package_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_root: Path,
) -> Mapping[str, Any]:
    return gate_clearing_batch.run_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        study_root=profile.studies_root / study_id,
        quest_id=quest_root.name,
        source="domain_owner_action_dispatch",
        authority_route_context={
            "controller_route_context": {
                "control_surface": "gate_clearing_batch",
                "controller_action_type": "run_gate_clearing_batch",
                "work_unit_id": "submission_minimal_refresh",
                "requires_human_confirmation": False,
            }
        },
    )


def _run_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_root: Path,
    authority_route_context: dict[str, Any],
) -> Mapping[str, Any]:
    return gate_clearing_batch.run_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        study_root=profile.studies_root / study_id,
        quest_id=quest_root.name,
        source="domain_owner_action_dispatch",
        authority_route_context=authority_route_context,
    )


def _blocked_current_package_freshness(*, exc: Exception, quest_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "current_package_freshness_workflow_failed",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "next_owner": "artifact_os",
        "error": str(exc),
        "quest_root": str(quest_root),
    }


def _blocked_gate_clearing_batch(*, exc: Exception, quest_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "gate_clearing_batch_workflow_failed",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "next_owner": "gate_clearing_batch",
        "error": str(exc),
        "quest_root": str(quest_root),
    }


def _gate_clearing_authority_route_context(dispatch: Mapping[str, Any] | None) -> dict[str, Any] | None:
    dispatch_payload = _mapping(dispatch)
    prompt_contract = _mapping(dispatch_payload.get("prompt_contract"))
    owner_route = _mapping(dispatch_payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = (
        _mapping(_mapping(owner_route.get("currentness_contract")).get("basis"))
        or _mapping(prompt_contract.get("owner_route_currentness_basis"))
        or _mapping(source_refs.get("owner_route_currentness_basis"))
    )
    work_unit_id = _first_text(
        _materialized_publication_owner_work_unit_id(source_refs),
        source_refs.get("work_unit_id"),
        currentness_basis.get("work_unit_id"),
        _mapping(dispatch_payload.get("source_action")).get("next_work_unit"),
    )
    if work_unit_id is None:
        return None
    controller_route_context: dict[str, Any] = {
        "control_surface": "gate_clearing_batch",
        "controller_action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "requires_human_confirmation": False,
    }
    for key in ("source_eval_id", "gate_fingerprint", "work_unit_fingerprint"):
        if text := _first_text(source_refs.get(key), currentness_basis.get(key)):
            controller_route_context[key] = text
    return {"controller_route_context": controller_route_context}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _materialized_publication_owner_work_unit_id(source_refs: Mapping[str, Any]) -> str | None:
    if _text(source_refs.get("bridge_authority")) != "domain_action_request_materializer_publication_owner_bridge":
        return None
    if _text(source_refs.get("blocked_reason")) not in {
        "current_package_freshness_required",
        "publication_owner_materialization_required",
    }:
        return None
    materialized_work_unit_id = _text(source_refs.get("materialized_work_unit_id"))
    if materialized_work_unit_id == "current_package_freshness_required":
        return "submission_minimal_refresh"
    return materialized_work_unit_id


__all__ = [
    "execute_current_package_freshness",
    "execute_gate_clearing_batch",
    "execute_publication_gate_specificity",
]
