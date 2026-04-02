from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers import (
    journal_shortlist as journal_shortlist_controller,
    medical_analysis_contract as medical_analysis_contract_controller,
    medical_reporting_contract as medical_reporting_contract_controller,
    quest_hydration as quest_hydration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_hydration_validation as startup_hydration_validation_controller,
    startup_data_readiness as startup_data_readiness_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.submission_targets import resolve_submission_target_contract
from med_autoscience.workspace_contracts import inspect_workspace_contracts


SUPPORTED_STARTUP_CONTRACT_PROFILES = {"paper_required_autonomous"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required YAML file: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _resolve_study(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> tuple[str, Path, dict[str, Any]]:
    if study_id is None and study_root is None:
        raise ValueError("study_id or study_root is required")
    if study_root is not None:
        resolved_study_root = Path(study_root).expanduser().resolve()
    else:
        resolved_study_root = (profile.studies_root / str(study_id)).resolve()
    study_payload = _load_yaml_dict(resolved_study_root / "study.yaml")
    resolved_study_id = str(study_payload.get("study_id") or study_id or resolved_study_root.name).strip()
    if not resolved_study_id:
        raise ValueError(f"could not resolve study_id from {resolved_study_root / 'study.yaml'}")
    if study_id is not None and str(study_id).strip() != resolved_study_id:
        raise ValueError(f"study_id mismatch: expected {study_id}, got {resolved_study_id}")
    return resolved_study_id, resolved_study_root, study_payload


def _execution_payload(study_payload: dict[str, Any]) -> dict[str, Any]:
    execution = study_payload.get("execution")
    if not isinstance(execution, dict):
        return {}
    return dict(execution)


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


def _study_paths(*, profile: WorkspaceProfile, study_id: str, study_root: Path, quest_id: str) -> dict[str, Path]:
    layout = build_workspace_runtime_layout_for_profile(profile)
    return {
        "quest_root": layout.quest_root(quest_id),
        "runtime_binding_path": study_root / "runtime_binding.yaml",
        "startup_payload_root": layout.startup_payload_root(study_id),
        "launch_report_path": study_root / "artifacts" / "runtime" / "last_launch_report.json",
    }


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

    if not boundary_gate["allow_compute_stage"]:
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
        "custom_profile": boundary_gate["effective_custom_profile"],
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
        "required_first_anchor": boundary_gate["required_first_anchor"],
        "legacy_code_execution_allowed": boundary_gate["legacy_code_execution_allowed"],
        "startup_boundary_gate": boundary_gate,
        "runtime_reentry_gate": runtime_reentry_gate,
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
    return {
        "title": title,
        "goal": goal,
        "quest_id": str(execution.get("quest_id") or study_id).strip() or study_id,
        "source": "med_autoscience.study_runtime_router",
        "auto_start": bool(
            (
                (
                    startup_contract.get("startup_boundary_gate")
                    if isinstance(startup_contract.get("startup_boundary_gate"), dict)
                    else {}
                ).get("allow_compute_stage")
            )
            and (
                (
                    startup_contract.get("runtime_reentry_gate")
                    if isinstance(startup_contract.get("runtime_reentry_gate"), dict)
                    else {}
                ).get("allow_runtime_entry", True)
            )
        ),
        "startup_contract": startup_contract,
    }


def _build_hydration_payload(*, create_payload: dict[str, Any]) -> dict[str, object]:
    startup_contract = create_payload.get("startup_contract")
    if not isinstance(startup_contract, dict):
        raise ValueError("create payload missing startup_contract")
    medical_analysis_contract = startup_contract.get("medical_analysis_contract_summary")
    if not isinstance(medical_analysis_contract, dict):
        raise ValueError("startup_contract missing medical_analysis_contract_summary")
    medical_reporting_contract = startup_contract.get("medical_reporting_contract_summary")
    if not isinstance(medical_reporting_contract, dict):
        raise ValueError("startup_contract missing medical_reporting_contract_summary")
    entry_state_summary = startup_contract.get("entry_state_summary")
    if not isinstance(entry_state_summary, str) or not entry_state_summary.strip():
        raise ValueError("startup_contract missing entry_state_summary")
    return {
        "medical_analysis_contract": dict(medical_analysis_contract),
        "medical_reporting_contract": dict(medical_reporting_contract),
        "entry_state_summary": entry_state_summary.strip(),
    }


def _validate_startup_contract_resolution(*, startup_contract: dict[str, Any]) -> dict[str, Any]:
    def validate_contract(
        *,
        payload: object,
        missing_blocker: str,
        invalid_blocker: str,
        unsupported_blocker: str,
        unresolved_blocker: str,
    ) -> tuple[str | None, str | None, str | None]:
        if payload is None:
            return None, missing_blocker, None
        if not isinstance(payload, dict):
            return None, invalid_blocker, None
        status = str(payload.get("status") or "").strip()
        reason_code = str(payload.get("reason_code") or "").strip() or None
        if status == "resolved":
            return status, None, reason_code
        if status == "unsupported":
            return status, unsupported_blocker, reason_code
        return status or None, unresolved_blocker, reason_code

    blockers: list[str] = []
    analysis_status, analysis_blocker, analysis_reason = validate_contract(
        payload=startup_contract.get("medical_analysis_contract_summary"),
        missing_blocker="missing_medical_analysis_contract",
        invalid_blocker="invalid_medical_analysis_contract",
        unsupported_blocker="unsupported_medical_analysis_contract",
        unresolved_blocker="unresolved_medical_analysis_contract",
    )
    reporting_status, reporting_blocker, reporting_reason = validate_contract(
        payload=startup_contract.get("medical_reporting_contract_summary"),
        missing_blocker="missing_medical_reporting_contract",
        invalid_blocker="invalid_medical_reporting_contract",
        unsupported_blocker="unsupported_medical_reporting_contract",
        unresolved_blocker="unresolved_medical_reporting_contract",
    )
    if analysis_blocker is not None:
        blockers.append(analysis_blocker)
    if reporting_blocker is not None:
        blockers.append(reporting_blocker)
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "contract_statuses": {
            "medical_analysis_contract": analysis_status,
            "medical_reporting_contract": reporting_status,
        },
        "reason_codes": {
            "medical_analysis_contract": analysis_reason,
            "medical_reporting_contract": reporting_reason,
        },
    }


def _recover_invalid_partial_quest_root(*, quest_root: Path, runtime_root: Path) -> dict[str, Any] | None:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_yaml_path = resolved_quest_root / "quest.yaml"
    if not resolved_quest_root.exists() or quest_yaml_path.exists():
        return None

    recovery_root = Path(runtime_root).expanduser().resolve() / "recovery" / "invalid_partial_quest_roots"
    archive_root = recovery_root / f"{resolved_quest_root.name}-{_timestamp_slug()}"
    recovery_root.mkdir(parents=True, exist_ok=True)
    if archive_root.exists():
        raise FileExistsError(f"invalid partial quest recovery target already exists: {archive_root}")
    resolved_quest_root.rename(archive_root)
    return {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": str(resolved_quest_root),
        "archived_root": str(archive_root),
        "missing_required_files": ["quest.yaml"],
    }


def _runtime_reentry_requires_startup_hydration(runtime_reentry_gate: dict[str, Any]) -> bool:
    return runtime_reentry_gate.get("require_startup_hydration") is True


def _runtime_reentry_requires_managed_skill_audit(runtime_reentry_gate: dict[str, Any]) -> bool:
    return runtime_reentry_gate.get("require_managed_skill_audit") is True


def _run_startup_hydration(
    *,
    quest_root: Path,
    create_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    hydration_payload = _build_hydration_payload(create_payload=create_payload)
    hydration_result = quest_hydration_controller.run_hydration(
        quest_root=quest_root,
        hydration_payload=hydration_payload,
    )
    validation_result = startup_hydration_validation_controller.run_validation(quest_root=quest_root)
    return hydration_result, validation_result


def _should_refresh_startup_hydration_while_blocked(status: dict[str, Any]) -> bool:
    if status.get("decision") != "blocked" or not bool(status.get("quest_exists")):
        return False
    quest_status = str(status.get("quest_status") or "").strip()
    if quest_status not in {"created", "idle", "paused"}:
        return False
    return str(status.get("reason") or "").strip() in {
        "startup_boundary_not_ready_for_resume",
        "runtime_reentry_not_ready_for_resume",
        "quest_paused_but_auto_resume_disabled",
        "quest_initialized_but_auto_resume_disabled",
    }


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    entry_mode: str | None,
) -> dict[str, Any]:
    execution = _execution_payload(study_payload)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    paths = _study_paths(profile=profile, study_id=study_id, study_root=study_root, quest_id=quest_id)
    quest_root = paths["quest_root"]
    runtime_binding_path = paths["runtime_binding_path"]
    quest_exists = (quest_root / "quest.yaml").exists()
    quest_status_value = quest_state.quest_status(quest_root) if quest_exists else ""
    contracts = inspect_workspace_contracts(profile)
    readiness = startup_data_readiness_controller.startup_data_readiness(workspace_root=profile.workspace_root)
    startup_boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_root=quest_root if quest_exists else None,
        enforce_startup_hydration=quest_status_value in {"running", "active"},
    )

    result: dict[str, Any] = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "entry_mode": selected_entry_mode,
        "execution": execution,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_exists": quest_exists,
        "quest_status": quest_status_value or None,
        "runtime_binding_path": str(runtime_binding_path),
        "runtime_binding_exists": runtime_binding_path.exists(),
        "workspace_contracts": contracts,
        "startup_data_readiness": readiness,
        "startup_boundary_gate": startup_boundary_gate,
        "runtime_reentry_gate": runtime_reentry_gate,
        "controller_first_policy_summary": render_controller_first_summary(),
        "automation_ready_summary": render_automation_ready_summary(),
    }

    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        result["decision"] = "lightweight"
        result["reason"] = "study_execution_not_med_deepscientist"
        return result

    auto_entry = str(execution.get("auto_entry") or "").strip()
    default_entry_mode = str(execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    if auto_entry != "on_managed_research_intent":
        result["decision"] = "lightweight"
        result["reason"] = "study_execution_not_managed"
        return result
    if selected_entry_mode != default_entry_mode:
        result["decision"] = "lightweight"
        result["reason"] = "entry_mode_not_managed"
        return result

    if not bool(contracts.get("overall_ready")):
        result["decision"] = "blocked"
        result["reason"] = "workspace_contract_not_ready"
        return result

    study_summary = readiness.get("study_summary") if isinstance(readiness.get("study_summary"), dict) else {}
    unresolved_contract_study_ids = study_summary.get("unresolved_contract_study_ids")
    if isinstance(unresolved_contract_study_ids, list) and study_id in unresolved_contract_study_ids:
        result["decision"] = "blocked"
        result["reason"] = "study_data_readiness_blocked"
        return result

    startup_contract_validation = _validate_startup_contract_resolution(
        startup_contract=_build_startup_contract(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            study_payload=study_payload,
            execution=execution,
        )
    )
    result["startup_contract_validation"] = startup_contract_validation
    if str(startup_contract_validation.get("status")) != "clear":
        result["decision"] = "blocked"
        result["reason"] = "startup_contract_resolution_failed"
        return result

    if not quest_exists:
        if startup_boundary_gate["allow_compute_stage"]:
            if runtime_reentry_gate["allow_runtime_entry"]:
                result["decision"] = "create_and_start"
                result["reason"] = "quest_missing"
            else:
                result["decision"] = "blocked"
                result["reason"] = "runtime_reentry_not_ready_for_auto_start"
        else:
            result["decision"] = "create_only"
            result["reason"] = "startup_boundary_not_ready_for_auto_start"
        return result

    if quest_status_value in {"running", "active"}:
        bash_session_audit = med_deepscientist_transport.inspect_quest_live_bash_sessions(
            runtime_root=profile.med_deepscientist_runtime_root,
            quest_id=quest_id,
        )
        result["bash_session_audit"] = bash_session_audit
        audit_status = str(bash_session_audit.get("status") or "").strip()
        if audit_status == "unknown":
            result["decision"] = "blocked"
            result["reason"] = "running_quest_live_session_audit_failed"
        elif audit_status == "live":
            if not startup_boundary_gate["allow_compute_stage"]:
                result["decision"] = "pause"
                result["reason"] = "startup_boundary_not_ready_for_running_quest"
            elif not runtime_reentry_gate["allow_runtime_entry"]:
                result["decision"] = "pause"
                result["reason"] = "runtime_reentry_not_ready_for_running_quest"
            else:
                result["decision"] = "noop"
                result["reason"] = "quest_already_running"
        elif not startup_boundary_gate["allow_compute_stage"]:
            result["decision"] = "blocked"
            result["reason"] = "startup_boundary_not_ready_for_resume"
        elif not runtime_reentry_gate["allow_runtime_entry"]:
            result["decision"] = "blocked"
            result["reason"] = "runtime_reentry_not_ready_for_resume"
        elif execution.get("auto_resume") is True:
            result["decision"] = "resume"
            result["reason"] = "quest_marked_running_but_no_live_session"
        else:
            result["decision"] = "blocked"
            result["reason"] = "quest_marked_running_but_auto_resume_disabled"
        return result

    if quest_status_value in {"paused", "idle", "created"}:
        if not startup_boundary_gate["allow_compute_stage"]:
            result["decision"] = "blocked"
            result["reason"] = "startup_boundary_not_ready_for_resume"
            return result
        if not runtime_reentry_gate["allow_runtime_entry"]:
            result["decision"] = "blocked"
            result["reason"] = "runtime_reentry_not_ready_for_resume"
            return result
        if execution.get("auto_resume") is True:
            result["decision"] = "resume"
            result["reason"] = (
                "quest_paused" if quest_status_value == "paused" else "quest_initialized_waiting_to_start"
            )
        else:
            result["decision"] = "blocked"
            result["reason"] = (
                "quest_paused_but_auto_resume_disabled"
                if quest_status_value == "paused"
                else "quest_initialized_but_auto_resume_disabled"
            )
        return result

    result["decision"] = "blocked"
    result["reason"] = "quest_exists_with_non_resumable_state"
    return result


def study_runtime_status(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    return _status_payload(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    )


def _write_runtime_binding(
    *,
    runtime_binding_path: Path,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    last_action: str,
    source: str,
) -> None:
    _write_yaml(
        runtime_binding_path,
        {
            "schema_version": 1,
            "engine": "med-deepscientist",
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "runtime_root": str(profile.runtime_root),
            "med_deepscientist_runtime_root": str(profile.med_deepscientist_runtime_root),
            "last_action": last_action,
            "last_action_at": _utc_now(),
            "last_source": source,
        },
    )


def _write_launch_report(
    *,
    launch_report_path: Path,
    status: dict[str, Any],
    source: str,
    force: bool,
    startup_payload_path: Path | None,
    daemon_result: dict[str, Any] | None,
) -> None:
    report = dict(status)
    report.update(
        {
            "source": source,
            "force": force,
            "recorded_at": _utc_now(),
            "startup_payload_path": str(startup_payload_path) if startup_payload_path is not None else None,
            "daemon_result": daemon_result,
        }
    )
    _write_json(launch_report_path, report)


def ensure_study_runtime(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    force: bool = False,
    source: str = "med_autoscience",
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = _status_payload(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    )
    execution = _execution_payload(study_payload)
    quest_id = str(execution.get("quest_id") or resolved_study_id).strip() or resolved_study_id
    paths = _study_paths(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
    )
    layout = build_workspace_runtime_layout_for_profile(profile)
    runtime_binding_path = paths["runtime_binding_path"]
    launch_report_path = paths["launch_report_path"]
    startup_payload_path: Path | None = None
    daemon_result: dict[str, Any] | None = None
    analysis_bundle_result: dict[str, Any] | None = None
    runtime_overlay_result: dict[str, Any] | None = None

    if status["decision"] in {"create_and_start", "create_only", "resume"}:
        runtime_reentry_gate = (
            dict(status["runtime_reentry_gate"])
            if isinstance(status.get("runtime_reentry_gate"), dict)
            else {}
        )
        analysis_bundle_result = analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        status["analysis_bundle"] = analysis_bundle_result
        if not bool(analysis_bundle_result.get("ready")):
            status["decision"] = "blocked"
            status["reason"] = "study_runtime_analysis_bundle_not_ready"
        elif _runtime_reentry_requires_managed_skill_audit(runtime_reentry_gate) and not profile.enable_medical_overlay:
            status["decision"] = "blocked"
            status["reason"] = "managed_skill_audit_not_available"
        elif profile.enable_medical_overlay and status["decision"] == "resume":
            runtime_overlay_result = _prepare_runtime_overlay(
                profile=profile,
                quest_root=Path(status["quest_root"]),
            )
            status["runtime_overlay"] = runtime_overlay_result
            audit = runtime_overlay_result["audit"]
            if not bool(audit.get("all_roots_ready")):
                status["decision"] = "blocked"
                status["reason"] = "runtime_overlay_not_ready"
    elif profile.enable_medical_overlay and status["quest_exists"]:
        runtime_overlay_result = {"audit": _audit_runtime_overlay(profile=profile, quest_root=Path(status["quest_root"]))}
        status["runtime_overlay"] = runtime_overlay_result
        audit = runtime_overlay_result["audit"]
        if status["quest_status"] in {"running", "active"} and not bool(audit.get("all_roots_ready")):
            status["decision"] = "pause"
            status["reason"] = "runtime_overlay_audit_failed_for_running_quest"

    if status["decision"] in {"create_and_start", "create_only"}:
        planned_decision = str(status["decision"])
        create_payload = _build_create_payload(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            study_payload=study_payload,
            execution=execution,
        )
        startup_contract_validation = _validate_startup_contract_resolution(
            startup_contract=dict(create_payload.get("startup_contract") or {})
        )
        status["startup_contract_validation"] = startup_contract_validation
        if str(startup_contract_validation.get("status")) != "clear":
            status["decision"] = "blocked"
            status["reason"] = "startup_contract_resolution_failed"
        partial_quest_recovery = _recover_invalid_partial_quest_root(
            quest_root=layout.quest_root(str(create_payload["quest_id"])),
            runtime_root=profile.med_deepscientist_runtime_root,
        )
        if partial_quest_recovery is not None:
            status["partial_quest_recovery"] = partial_quest_recovery
        create_payload["auto_start"] = False
        if status["decision"] in {"create_and_start", "create_only"}:
            startup_payload_path = paths["startup_payload_root"] / f"{_timestamp_slug()}.json"
            _write_json(startup_payload_path, create_payload)
            create_result = med_deepscientist_transport.create_quest(
                runtime_root=profile.med_deepscientist_runtime_root,
                payload=create_payload,
            )
            daemon_result = {"create": create_result}
            status["quest_id"] = str(create_payload["quest_id"])
            status["quest_root"] = str(layout.quest_root(status["quest_id"]))
            status["quest_exists"] = True
            snapshot = create_result.get("snapshot") if isinstance(create_result.get("snapshot"), dict) else {}
            fallback_status = "created"
            status["quest_status"] = str(snapshot.get("status") or fallback_status)
            quest_root = Path(status["quest_root"])
            if profile.enable_medical_overlay:
                runtime_overlay_result = _prepare_runtime_overlay(
                    profile=profile,
                    quest_root=quest_root,
                )
                status["runtime_overlay"] = runtime_overlay_result
                audit = runtime_overlay_result["audit"]
                if not bool(audit.get("all_roots_ready")):
                    status["decision"] = "blocked"
                    status["reason"] = "runtime_overlay_not_ready"
            if status["decision"] == "blocked":
                _write_runtime_binding(
                    runtime_binding_path=runtime_binding_path,
                    profile=profile,
                    study_id=resolved_study_id,
                    study_root=resolved_study_root,
                    quest_id=status["quest_id"],
                    last_action="blocked",
                    source=source,
                )
            else:
                hydration_result, validation_result = _run_startup_hydration(
                    quest_root=quest_root,
                    create_payload=create_payload,
                )
                status["startup_hydration"] = hydration_result
                status["startup_hydration_validation"] = validation_result
                if str(validation_result.get("status")) != "clear":
                    status["decision"] = "blocked"
                    status["reason"] = "hydration_validation_failed"
                    _write_runtime_binding(
                        runtime_binding_path=runtime_binding_path,
                        profile=profile,
                        study_id=resolved_study_id,
                        study_root=resolved_study_root,
                        quest_id=status["quest_id"],
                        last_action="blocked",
                        source=source,
                    )
                elif planned_decision == "create_and_start":
                    resume_result = med_deepscientist_transport.resume_quest(
                        runtime_root=profile.med_deepscientist_runtime_root,
                        quest_id=str(status["quest_id"]),
                        source=source,
                    )
                    daemon_result["resume"] = resume_result
                    status["quest_status"] = str(resume_result.get("status") or "running")
                    _write_runtime_binding(
                        runtime_binding_path=runtime_binding_path,
                        profile=profile,
                        study_id=resolved_study_id,
                        study_root=resolved_study_root,
                        quest_id=status["quest_id"],
                        last_action="create_and_start",
                        source=source,
                    )
                else:
                    _write_runtime_binding(
                        runtime_binding_path=runtime_binding_path,
                        profile=profile,
                        study_id=resolved_study_id,
                        study_root=resolved_study_root,
                        quest_id=status["quest_id"],
                        last_action="create_only",
                        source=source,
                    )
    elif status["decision"] == "resume":
        quest_root = Path(status["quest_root"])
        create_payload = _build_create_payload(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            study_payload=study_payload,
            execution=execution,
        )
        hydration_result, validation_result = _run_startup_hydration(
            quest_root=quest_root,
            create_payload=create_payload,
        )
        status["startup_hydration"] = hydration_result
        status["startup_hydration_validation"] = validation_result
        if str(validation_result.get("status")) != "clear":
            status["decision"] = "blocked"
            status["reason"] = "hydration_validation_failed"
            _write_runtime_binding(
                runtime_binding_path=runtime_binding_path,
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                quest_id=str(status["quest_id"]),
                last_action="blocked",
                source=source,
            )
        else:
            daemon_result = med_deepscientist_transport.resume_quest(
                runtime_root=profile.med_deepscientist_runtime_root,
                quest_id=str(status["quest_id"]),
                source=source,
            )
            status["quest_status"] = str(daemon_result.get("status") or "running")
            _write_runtime_binding(
                runtime_binding_path=runtime_binding_path,
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                quest_id=str(status["quest_id"]),
                    last_action="resume",
                    source=source,
                )
    elif _should_refresh_startup_hydration_while_blocked(status):
        quest_root = Path(status["quest_root"])
        create_payload = _build_create_payload(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            study_payload=study_payload,
            execution=execution,
        )
        startup_contract_validation = _validate_startup_contract_resolution(
            startup_contract=dict(create_payload.get("startup_contract") or {})
        )
        status["startup_contract_validation"] = startup_contract_validation
        if str(startup_contract_validation.get("status")) != "clear":
            status["reason"] = "startup_contract_resolution_failed"
        else:
            hydration_result, validation_result = _run_startup_hydration(
                quest_root=quest_root,
                create_payload=create_payload,
            )
            status["startup_hydration"] = hydration_result
            status["startup_hydration_validation"] = validation_result
            if str(validation_result.get("status")) != "clear":
                status["reason"] = "hydration_validation_failed"
        _write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            quest_id=str(status["quest_id"]),
            last_action="blocked",
            source=source,
        )
    elif status["decision"] == "pause":
        daemon_result = med_deepscientist_transport.pause_quest(
            runtime_root=profile.med_deepscientist_runtime_root,
            quest_id=str(status["quest_id"]),
            source=source,
        )
        status["quest_status"] = str(daemon_result.get("status") or "paused")
        _write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            quest_id=str(status["quest_id"]),
            last_action="pause",
            source=source,
        )
    elif status["decision"] == "noop":
        _write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            quest_id=str(status["quest_id"]),
            last_action="noop",
            source=source,
        )
    elif status["decision"] == "blocked" and status["quest_exists"]:
        _write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            quest_id=str(status["quest_id"]),
            last_action="blocked",
            source=source,
        )

    _write_launch_report(
        launch_report_path=launch_report_path,
        status=status,
        source=source,
        force=force,
        startup_payload_path=startup_payload_path,
        daemon_result=daemon_result,
    )
    status["runtime_binding_path"] = str(runtime_binding_path)
    status["launch_report_path"] = str(launch_report_path)
    if startup_payload_path is not None:
        status["startup_payload_path"] = str(startup_payload_path)
    return status
