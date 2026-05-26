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


def _blocked_current_package_freshness(*, exc: Exception, quest_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "current_package_freshness_workflow_failed",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "next_owner": "artifact_os",
        "error": str(exc),
        "quest_root": str(quest_root),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["execute_current_package_freshness", "execute_publication_gate_specificity"]
