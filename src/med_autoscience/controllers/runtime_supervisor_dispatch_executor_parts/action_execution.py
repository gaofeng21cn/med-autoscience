from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from .. import (
    ai_reviewer_publication_eval_workflow,
    gate_clearing_batch,
    paper_authority_migration,
    publication_gate,
    quest_hydration,
    study_runtime_router,
)
from ..supervisor_action_request_lifecycle import stable_ai_reviewer_request_path


PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
_AI_REVIEWER_REQUIRED_RECORD_FIELDS = (
    "quality_assessment",
    "future_facing_limitations_plan",
)
_AI_REVIEWER_REQUIRED_REVIEWER_OS_FIELDS = (
    "input_bundle",
    "rubric_scores",
    "decision_matrix",
    "provenance_checks",
    "route_back_decision",
    "future_facing_limitations_plan",
)


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


def _run_current_package_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_root: Path,
) -> Mapping[str, Any]:
    return gate_clearing_batch.run_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        study_root=_study_root(profile, study_id),
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


def _blocked_current_package_freshness(*, exc: Exception, quest_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "current_package_freshness_workflow_failed",
        "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        "next_owner": "artifact_os",
        "error": str(exc),
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
        return _blocked_display_materialization(exc=exc, paper_root=paper_root)
    gate_result = execute_current_package_freshness(profile=profile, study_id=study_id, apply=apply)
    owner_result = _mapping(gate_result.get("owner_result"))
    executed = gate_result.get("execution_status") == "executed"
    return _display_materialization_result(
        gate_result=gate_result,
        owner_result=owner_result,
        stub_result=stub_result,
        executed=executed,
        paper_root=paper_root,
    )


def _blocked_display_materialization(*, exc: Exception, paper_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "display_contract_stub_materialization_failed",
        "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
        "next_owner": "artifact_os",
        "error": str(exc),
        "paper_root": str(paper_root),
    }


def _display_materialization_result(
    *,
    gate_result: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    stub_result: Mapping[str, Any],
    executed: bool,
    paper_root: Path,
) -> dict[str, Any]:
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
    record, record_blocker = _ai_reviewer_record_for_execution(request=request, study_root=study_root)
    if record_blocker:
        payload = _blocked_ai_reviewer_execution(apply=apply, reason=record_blocker["reason"], request_path=request_path)
        payload.update(record_blocker["payload"])
        return payload
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
                for surface, ref in {**required_refs, **_ai_reviewer_optional_refs(request)}.items()
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


def _ai_reviewer_record_for_execution(
    *,
    request: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    current_record = _mapping(_read_json_object(_publication_eval_latest_path(study_root)))
    request_record = _mapping(request.get("ai_reviewer_record") or request.get("publication_eval_record") or request.get("record"))

    if paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root) and not request_record:
        request_record = _clean_migration_request_record(study_root=study_root, request=request)

    if (
        current_record
        and _ai_reviewer_owned_record(current_record)
        and not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root)
    ):
        missing_fields = _missing_ai_reviewer_record_fields(current_record)
        if missing_fields:
            return {}, {
                "reason": "ai_reviewer_record_incomplete",
                "payload": {
                    "missing_record_fields": missing_fields,
                    "owner_record_requirements": _ai_reviewer_record_requirements(),
                },
            }
        return current_record, None

    if request_record:
        if not _request_record_owner_acceptable(request_record):
            return {}, {
                "reason": "ai_reviewer_record_missing",
                "payload": {
                    "owner_record_requirements": _ai_reviewer_record_requirements(),
                },
            }
        missing_fields = _missing_ai_reviewer_record_fields(request_record)
        if missing_fields:
            return {}, {
                "reason": "ai_reviewer_record_incomplete",
                "payload": {
                    "missing_record_fields": missing_fields,
                    "owner_record_requirements": _ai_reviewer_record_requirements(),
                },
            }
        return request_record, None

    return {}, {
        "reason": "ai_reviewer_record_missing",
        "payload": {
            "owner_record_requirements": _ai_reviewer_record_requirements(),
        },
    }


def _clean_migration_request_record(*, study_root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(request.get("study_id")) or study_root.name
    quest_id = _text(request.get("quest_id")) or study_id
    emitted_at = _text(request.get("generated_at")) or "2026-05-17T00:00:00+00:00"
    refs = _ai_reviewer_required_refs(request)
    manuscript_ref = refs.get("manuscript") or str(study_root / "paper" / "manuscript.md")
    evidence_ref = refs.get("evidence_ledger") or str(study_root / "paper" / "evidence_ledger.json")
    review_ref = refs.get("review_ledger") or str(study_root / "paper" / "review" / "review_ledger.json")
    charter_ref = refs.get("study_charter") or str(study_root / "artifacts" / "controller" / "study_charter.json")
    return {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::{quest_id}::{emitted_at}",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": emitted_at,
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": charter_ref,
            "charter_id": f"charter::{study_id}::paper-authority-clean-migration",
            "publication_objective": "Re-establish publication authority after clean paper-authority migration.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"),
            "main_result_ref": evidence_ref,
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [manuscript_ref, evidence_ref, review_ref, charter_ref],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Clean migration requires a fresh AI reviewer pass before quality closure or delivery.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": _clean_migration_quality_assessment(
            manuscript_ref=manuscript_ref,
            evidence_ref=evidence_ref,
            review_ref=review_ref,
            charter_ref=charter_ref,
        ),
        "gaps": [
            {
                "gap_id": "paper-authority-clean-migration",
                "gap_type": "delivery",
                "severity": "must_fix",
                "summary": "Legacy publication and delivery authority surfaces were archived; new MAS owners must rebuild them.",
                "evidence_refs": [
                    str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json")
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "paper-authority-clean-migration-rebuild",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "After AI reviewer writeback, rerun publication gate and delivery sync.",
                "route_key_question": "Rebuild publication and current-package authority under new MAS.",
                "route_rationale": "Legacy active paper surfaces are provenance only after clean migration.",
                "evidence_refs": [
                    str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json")
                ],
                "requires_controller_decision": True,
            }
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "This clean-migration assessment only re-establishes authority; it does not repair manuscript scientific gaps by itself.",
                "impact_on_claim": "Publication claims remain provisional until publication gate and delivery owners rerun on the new eval.",
                "required_future_analysis_data_or_design": "Rerun publication gate, delivery sync, and any study-specific analysis owner routes required by the new AI reviewer result.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }


def _clean_migration_quality_assessment(
    *,
    manuscript_ref: str,
    evidence_ref: str,
    review_ref: str,
    charter_ref: str,
) -> dict[str, Any]:
    return {
        "clinical_significance": {
            "status": "underdefined",
            "summary": "Clinical significance requires fresh review under the new paper-authority surface.",
            "evidence_refs": [charter_ref, manuscript_ref],
        },
        "evidence_strength": {
            "status": "underdefined",
            "summary": "Evidence strength requires fresh review under the new paper-authority surface.",
            "evidence_refs": [evidence_ref],
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "Novelty positioning requires fresh review under the new paper-authority surface.",
            "evidence_refs": [charter_ref],
        },
        "medical_journal_prose_quality": {
            "status": "underdefined",
            "summary": "Medical journal prose must be reviewed by the AI reviewer before quality closure.",
            "evidence_refs": [manuscript_ref, review_ref],
            "reviewer_reason": "Legacy prose and package authority were archived by clean migration.",
            "reviewer_revision_advice": "Use the current manuscript, evidence ledger, review ledger, and prose review inputs to produce a new AI-reviewer-backed quality judgment.",
            "reviewer_next_round_focus": "Methods completeness, results numeric sufficiency, tables/figures, clinical context, and restrained journal prose.",
        },
        "human_review_readiness": {
            "status": "blocked",
            "summary": "Human review readiness cannot be claimed until new MAS delivery is rebuilt.",
            "evidence_refs": [review_ref],
        },
    }


def _ai_reviewer_owned_record(record: Mapping[str, Any]) -> bool:
    provenance = _mapping(record.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "ai_reviewer"
        and _text(provenance.get("source_kind")) == "publication_eval_ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
    )


def _request_record_owner_acceptable(record: Mapping[str, Any]) -> bool:
    provenance = _mapping(record.get("assessment_provenance"))
    if not provenance:
        return True
    return _ai_reviewer_owned_record(record)


def _missing_ai_reviewer_record_fields(record: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    quality_assessment = record.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        missing.append("quality_assessment")
    future_plan = record.get("future_facing_limitations_plan")
    if not isinstance(future_plan, list) or not future_plan:
        missing.append("future_facing_limitations_plan")
    return missing


def _ai_reviewer_record_requirements() -> dict[str, list[str]]:
    return {
        "required_record_fields": list(_AI_REVIEWER_REQUIRED_RECORD_FIELDS),
        "required_reviewer_operating_system_fields": list(_AI_REVIEWER_REQUIRED_REVIEWER_OS_FIELDS),
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


def _ai_reviewer_optional_refs(request: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        surface: _ref_path(request, surface)
        for surface in (
            "reporting_guideline",
            "calibration_refs",
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
