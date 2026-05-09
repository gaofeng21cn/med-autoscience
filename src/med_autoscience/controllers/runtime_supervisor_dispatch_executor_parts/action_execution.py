from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from .. import ai_reviewer_publication_eval_workflow, gate_clearing_batch, publication_gate, quest_hydration, study_runtime_router
from ..supervisor_action_request_lifecycle import stable_ai_reviewer_request_path


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


def quest_root_from_status(profile: WorkspaceProfile, study_id: str) -> Path | None:
    try:
        status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=None, entry_mode=None)
    except Exception:
        return None
    status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    quest_root = _text(status_payload.get("quest_root"))
    return Path(quest_root).expanduser().resolve() if quest_root is not None else None


def execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    quest_root = quest_root_from_status(profile, study_id)
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


def execute_runtime_platform_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    supported_mode: str,
) -> dict[str, Any]:
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "runtime supervisor-scan --apply-runtime-platform-repair",
        }
    from .. import runtime_supervisor_scan

    result = runtime_supervisor_scan.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode=supported_mode,
        persist_surfaces=False,
    )
    study_payload = next(
        (study for study in result.get("studies", []) if isinstance(study, Mapping) and _text(study.get("study_id")) == study_id),
        {},
    )
    apply_result = _mapping(study_payload.get("runtime_platform_repair_apply"))
    executed = _text(apply_result.get("dispatch_status")) == "applied"
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(apply_result.get("reason")) or "runtime_platform_repair_not_applied",
        "owner_callable_surface": "runtime_supervisor_scan.supervisor_scan(apply_runtime_platform_repair=True)",
        "owner_result": apply_result or result,
    }


def execute_current_package_freshness(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    quest_root = quest_root_from_status(profile, study_id)
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    study_root = _study_root(profile, study_id)
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "quest_root": str(quest_root),
        }
    try:
        owner_result = gate_clearing_batch.run_gate_clearing_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_root.name,
            source="runtime_supervisor_dispatch_executor",
            control_plane_route_context={
                "controller_route_context": {
                    "control_surface": "gate_clearing_batch",
                    "controller_action_type": "run_gate_clearing_batch",
                    "work_unit_id": "submission_minimal_refresh",
                    "requires_human_confirmation": False,
                }
            },
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "current_package_freshness_workflow_failed",
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "next_owner": "artifact_os",
            "error": str(exc),
            "quest_root": str(quest_root),
        }
    executed = bool(owner_result.get("ok")) if isinstance(owner_result, Mapping) else False
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(_mapping(owner_result).get("status")) or "gate_clearing_batch_not_applied",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(quest_root),
    }


def execute_artifact_display_materialization(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    paper_root = study_root / "paper"
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "medical_reporting_contract_missing",
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
            "next_owner": "artifact_os",
            "required_input_surface": str(reporting_contract_path),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
            "paper_root": str(paper_root),
        }
    try:
        stub_result = quest_hydration.materialize_display_contract_stubs(paper_root=paper_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "display_contract_stub_materialization_failed",
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
            "next_owner": "artifact_os",
            "error": str(exc),
            "paper_root": str(paper_root),
        }
    gate_result = execute_current_package_freshness(profile=profile, study_id=study_id, apply=apply)
    owner_result = _mapping(gate_result.get("owner_result"))
    executed = gate_result.get("execution_status") == "executed"
    return {
        **gate_result,
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else gate_result.get("blocked_reason"),
        "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": {
            "display_contract_stubs": stub_result,
            "gate_clearing_batch": owner_result or gate_result.get("owner_result"),
        },
        "paper_root": str(paper_root),
    }


def execute_ai_reviewer_workflow(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    controller_decision_refresh,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    request = _read_json_object(request_path)
    if request is None:
        return _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_request_missing", request_path=request_path)
    record = _mapping(_read_json_object(_publication_eval_latest_path(study_root)))
    if not record:
        record = _mapping(request.get("ai_reviewer_record") or request.get("publication_eval_record") or request.get("record"))
    if not record:
        return _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_record_missing", request_path=request_path)
    required_refs = _ai_reviewer_required_refs(request)
    missing_refs = [surface for surface, ref in required_refs.items() if ref is None]
    if missing_refs:
        payload = _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_required_refs_missing", request_path=request_path)
        payload["missing_refs"] = missing_refs
        return payload
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "request_path": str(request_path),
        }
    try:
        owner_result = ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=required_refs["manuscript"],
            evidence_ref=required_refs["evidence_ledger"],
            review_ref=required_refs["review_ledger"],
            charter_ref=required_refs["study_charter"],
            record=record,
            additional_refs={
                surface: ref
                for surface, ref in required_refs.items()
                if surface not in {"manuscript", "evidence_ledger", "review_ledger", "study_charter"}
                and ref is not None
            },
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = _blocked_ai_reviewer_execution(apply=True, reason="ai_reviewer_workflow_failed", request_path=request_path)
        payload["error"] = str(exc)
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


def _blocked_ai_reviewer_execution(*, apply: bool, reason: str, request_path: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked" if apply else "dry_run",
        "blocked_reason": reason,
        "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        "next_owner": "ai_reviewer",
        "required_input_surface": str(request_path),
    }


def _ai_reviewer_required_refs(request: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        surface: _ref_path(request, surface)
        for surface in (
            "manuscript",
            "evidence_ledger",
            "review_ledger",
            "study_charter",
            "medical_manuscript_blueprint",
            "claim_evidence_map",
            "medical_prose_review",
            "publication_gate_projection",
        )
    }


def _ref_path(packet: Mapping[str, Any], surface: str) -> str | None:
    ref = _mapping(_mapping(_mapping(packet.get("input_contract")).get("required_refs")).get(surface))
    return _text(ref.get("path")) or _text(ref.get("ref")) or _text(ref.get("relative_path"))


__all__ = [
    "execute_ai_reviewer_workflow",
    "execute_artifact_display_materialization",
    "execute_current_package_freshness",
    "execute_publication_gate_specificity",
    "execute_runtime_platform_repair",
    "quest_root_from_status",
]
