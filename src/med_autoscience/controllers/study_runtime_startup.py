from __future__ import annotations

from dataclasses import asdict
from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    journal_shortlist as journal_shortlist_controller,
    medical_analysis_contract as medical_analysis_contract_controller,
    medical_reporting_contract as medical_reporting_contract_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeReentryGate,
    StudyRuntimeStartupBoundaryGate,
    StudyRuntimeStatus,
)
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.submission_targets import resolve_submission_target_contract


SUPPORTED_STARTUP_CONTRACT_PROFILES = {"paper_required_autonomous"}


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _read_optional_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _resolve_optional_path(*, anchor: Path, raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (anchor / candidate).resolve()
    return candidate


def _serialize_submission_targets(profile: WorkspaceProfile, study_root: Path) -> list[dict[str, Any]]:
    contract = resolve_submission_target_contract(profile=profile, study_root=study_root)
    return [asdict(target) for target in contract.targets]


def _has_explicit_submission_targets(study_payload: dict[str, Any]) -> bool:
    raw_targets = study_payload.get("submission_targets")
    return isinstance(raw_targets, list) and bool(raw_targets)


def _overlay_request_kwargs(profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "skill_ids": profile.medical_overlay_skills,
        "policy_id": profile.research_route_bias_policy,
        "archetype_ids": profile.preferred_study_archetypes,
        "default_submission_targets": profile.default_submission_targets,
        "default_publication_profile": profile.default_publication_profile,
        "default_citation_style": profile.default_citation_style,
    }


def _prepare_runtime_overlay(*, profile: WorkspaceProfile, quest_root: Path) -> dict[str, Any]:
    overlay_kwargs = _overlay_request_kwargs(profile)
    authority = overlay_installer.ensure_medical_overlay(
        quest_root=profile.workspace_root,
        mode="ensure_ready",
        **overlay_kwargs,
    )
    materialization = overlay_installer.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=profile.workspace_root,
        **overlay_kwargs,
    )
    audit = overlay_installer.audit_runtime_medical_overlay(
        quest_root=quest_root,
        **overlay_kwargs,
    )
    return {
        "authority": authority,
        "materialization": materialization,
        "audit": audit,
    }


def _audit_runtime_overlay(*, profile: WorkspaceProfile, quest_root: Path) -> dict[str, Any]:
    return overlay_installer.audit_runtime_medical_overlay(
        quest_root=quest_root,
        **_overlay_request_kwargs(profile),
    )


def _build_startup_contract(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    startup_contract_profile = str(execution.get("startup_contract_profile") or "").strip()
    if startup_contract_profile not in SUPPORTED_STARTUP_CONTRACT_PROFILES:
        raise ValueError(f"unsupported startup_contract_profile: {startup_contract_profile}")

    startup_brief_path = _resolve_optional_path(anchor=study_root, raw_path=study_payload.get("startup_brief"))
    primary_question = str(study_payload.get("primary_question") or "").strip()
    title = str(study_payload.get("title") or study_id).strip()
    objectives = [primary_question] if primary_question else [f"advance study {study_id} toward submission"]
    boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    startup_boundary_gate = StudyRuntimeStartupBoundaryGate.from_payload(boundary_gate)
    runtime_reentry_gate_result = StudyRuntimeReentryGate.from_payload(
        runtime_reentry_gate,
        default_allow_runtime_entry=True,
    )
    journal_shortlist = journal_shortlist_controller.resolve_journal_shortlist(study_root=study_root)
    requested_launch_profile = str(execution.get("launch_profile") or "continue_existing_state").strip()
    requested_launch_profile = requested_launch_profile or "continue_existing_state"
    existing_brief = _read_optional_text(startup_brief_path)
    medical_analysis_contract_summary = medical_analysis_contract_controller.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    medical_reporting_contract_summary = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )

    if not startup_boundary_gate.allow_compute_stage:
        scope = "full_research"
        baseline_mode = "stop_if_insufficient"
        baseline_execution_policy = "skip_unless_blocking"
        resource_policy = "conservative"
        research_intensity = "light"
        time_budget_hours = 8
        runtime_constraints = (
            "Honor workspace data contracts. Treat the startup boundary as a hard gate: do not enter baseline, "
            "experiment, or analysis-campaign until paper framing, journal shortlist, and the minimum SCI-ready "
            "evidence package are explicit."
        )
    elif requested_launch_profile == "continue_existing_state":
        scope = "full_research"
        baseline_mode = "reuse_existing_only"
        baseline_execution_policy = "reuse_existing_only"
        resource_policy = "balanced"
        research_intensity = "balanced"
        time_budget_hours = 24
        runtime_constraints = (
            "Honor workspace data contracts and only reuse existing baseline assets after paper framing is explicit."
        )
    else:
        scope = "baseline_plus_direction"
        baseline_mode = "existing"
        baseline_execution_policy = "auto"
        resource_policy = "balanced"
        research_intensity = "balanced"
        time_budget_hours = 24
        runtime_constraints = "Honor workspace data contracts and prepare a submission-ready study."

    return {
        "schema_version": 4,
        "user_language": str(study_payload.get("user_language") or "zh").strip() or "zh",
        "need_research_paper": True,
        "research_intensity": research_intensity,
        "decision_policy": str(execution.get("decision_policy") or "autonomous").strip() or "autonomous",
        "launch_mode": "custom",
        "custom_profile": startup_boundary_gate.effective_custom_profile,
        "scope": scope,
        "baseline_mode": baseline_mode,
        "baseline_execution_policy": baseline_execution_policy,
        "resource_policy": resource_policy,
        "time_budget_hours": time_budget_hours,
        "git_strategy": "semantic_head_plus_controlled_integration",
        "runtime_constraints": runtime_constraints,
        "objectives": objectives,
        "baseline_urls": [],
        "paper_urls": list(study_payload.get("paper_urls") or []),
        "entry_state_summary": f"Study root: {study_root}",
        "review_summary": "",
        "controller_first_policy_summary": render_controller_first_summary(),
        "automation_ready_summary": render_automation_ready_summary(),
        "custom_brief": startup_boundary_gate_controller.render_boundary_custom_brief(
            existing_brief=existing_brief,
            boundary_gate=boundary_gate,
        ),
        "required_first_anchor": startup_boundary_gate.required_first_anchor,
        "legacy_code_execution_allowed": startup_boundary_gate.legacy_code_execution_allowed,
        "startup_boundary_gate": startup_boundary_gate.to_dict(),
        "runtime_reentry_gate": runtime_reentry_gate_result.to_dict(),
        "journal_shortlist": journal_shortlist,
        "medical_analysis_contract_summary": medical_analysis_contract_summary,
        "medical_reporting_contract_summary": medical_reporting_contract_summary,
        "reporting_guideline_family": medical_reporting_contract_summary.get("reporting_guideline_family")
        if medical_reporting_contract_summary.get("status") == "resolved"
        else None,
        "submission_targets": _serialize_submission_targets(profile, study_root)
        if _has_explicit_submission_targets(study_payload)
        else [],
    }


def _build_create_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    title = str(study_payload.get("title") or study_id).strip() or study_id
    goal = str(study_payload.get("primary_question") or title).strip() or title
    startup_contract = _build_startup_contract(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    startup_boundary_gate = StudyRuntimeStartupBoundaryGate.from_payload(
        startup_contract.get("startup_boundary_gate")
        if isinstance(startup_contract.get("startup_boundary_gate"), dict)
        else {}
    )
    runtime_reentry_gate = StudyRuntimeReentryGate.from_payload(
        startup_contract.get("runtime_reentry_gate")
        if isinstance(startup_contract.get("runtime_reentry_gate"), dict)
        else {},
        default_allow_runtime_entry=True,
    )
    return {
        "title": title,
        "goal": goal,
        "quest_id": str(execution.get("quest_id") or study_id).strip() or study_id,
        "source": "med_autoscience.study_runtime_router",
        "auto_start": startup_boundary_gate.allow_compute_stage and runtime_reentry_gate.allow_runtime_entry,
        "startup_contract": startup_contract,
    }


def _runtime_reentry_requires_startup_hydration(runtime_reentry_gate: dict[str, Any]) -> bool:
    return StudyRuntimeReentryGate.from_payload(runtime_reentry_gate).require_startup_hydration


def _runtime_reentry_requires_managed_skill_audit(runtime_reentry_gate: dict[str, Any]) -> bool:
    return StudyRuntimeReentryGate.from_payload(runtime_reentry_gate).require_managed_skill_audit


def _run_startup_hydration(
    *,
    quest_root: Path,
    create_payload: dict[str, Any],
) -> tuple[
    study_runtime_protocol.StartupHydrationReport,
    study_runtime_protocol.StartupHydrationValidationReport,
]:
    router = _router_module()
    hydration_payload = study_runtime_protocol.build_hydration_payload(create_payload=create_payload)
    hydration_result = router.quest_hydration_controller.run_hydration(
        quest_root=quest_root,
        hydration_payload=hydration_payload,
    )
    validation_result = router.startup_hydration_validation_controller.run_validation(quest_root=quest_root)
    return (
        study_runtime_protocol.StartupHydrationReport.from_payload(
            StudyRuntimeStatus._require_dict_field("startup_hydration", hydration_result)
        ),
        study_runtime_protocol.StartupHydrationValidationReport.from_payload(
            StudyRuntimeStatus._require_dict_field("startup_hydration_validation", validation_result)
        ),
    )


def _sync_existing_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    create_payload: dict[str, Any],
) -> dict[str, Any]:
    startup_contract = create_payload.get("startup_contract")
    if not isinstance(startup_contract, dict):
        raise ValueError("create payload missing startup_contract")
    return med_deepscientist_transport.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        startup_contract=dict(startup_contract),
    )
