from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.profiles import WorkspaceProfile


def _normalized_string_list(raw_value: object) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return ()
    normalized: list[str] = []
    for item in raw_value:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return tuple(normalized)


def _non_empty_string(raw_value: object) -> str:
    if not isinstance(raw_value, str):
        return ""
    return raw_value.strip()


def _study_level_shortlist(study_payload: dict[str, Any]) -> tuple[str, ...]:
    shortlist = _normalized_string_list(study_payload.get("journal_shortlist"))
    if shortlist:
        return shortlist
    submission_targets = study_payload.get("submission_targets")
    if not isinstance(submission_targets, list):
        return ()
    normalized: list[str] = []
    for item in submission_targets:
        if isinstance(item, str) and item.strip():
            normalized.append(item.strip())
            continue
        if isinstance(item, dict):
            journal_name = _non_empty_string(item.get("journal_name"))
            publication_profile = _non_empty_string(item.get("publication_profile"))
            official_guidelines_url = _non_empty_string(item.get("official_guidelines_url"))
            if journal_name:
                normalized.append(journal_name)
            elif publication_profile:
                normalized.append(publication_profile)
            elif official_guidelines_url:
                normalized.append(official_guidelines_url)
    return tuple(normalized)


def _paper_framing_ready(study_payload: dict[str, Any]) -> bool:
    framing_summary = _non_empty_string(study_payload.get("paper_framing_summary"))
    literature_anchor_summary = _non_empty_string(study_payload.get("literature_anchor_summary"))
    paper_urls = _normalized_string_list(study_payload.get("paper_urls"))
    return bool(framing_summary and (paper_urls or literature_anchor_summary))


def _evidence_package_ready(study_payload: dict[str, Any]) -> bool:
    return bool(_normalized_string_list(study_payload.get("minimum_sci_ready_evidence_package")))


def _legacy_code_execution_allowed(profile: WorkspaceProfile, study_payload: dict[str, Any]) -> bool:
    if profile.legacy_code_execution_policy == "audit_only":
        return False
    approved = study_payload.get("legacy_code_execution_approved") is True
    if profile.legacy_code_execution_policy == "allow_with_decision":
        return approved
    return approved


def _required_first_anchor(profile: WorkspaceProfile, requested_launch_profile: str) -> str:
    if requested_launch_profile != "continue_existing_state":
        return "scout"
    if profile.default_startup_anchor_policy == "intake_audit_first_for_continue_existing_state":
        return "intake-audit"
    return "scout"


def effective_custom_profile(
    *,
    profile: WorkspaceProfile,
    requested_launch_profile: str,
    allow_compute_stage: bool | None = None,
) -> str:
    if allow_compute_stage is False:
        required_first_anchor = _required_first_anchor(profile, requested_launch_profile)
        if required_first_anchor == "intake-audit":
            return "continue_existing_state"
        return "freeform"
    if requested_launch_profile != "continue_existing_state":
        return requested_launch_profile
    if profile.default_startup_anchor_policy == "intake_audit_first_for_continue_existing_state":
        return "continue_existing_state"
    return "freeform"


def evaluate_startup_boundary(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    requested_launch_profile = str(execution.get("launch_profile") or "continue_existing_state").strip()
    requested_launch_profile = requested_launch_profile or "continue_existing_state"
    required_first_anchor = _required_first_anchor(profile, requested_launch_profile)
    missing_requirements: list[str] = []
    blockers: list[str] = []

    paper_framing_ready = _paper_framing_ready(study_payload)
    journal_shortlist_ready = bool(_study_level_shortlist(study_payload))
    evidence_package_ready = _evidence_package_ready(study_payload)
    readiness_by_requirement = {
        "paper_framing": paper_framing_ready,
        "journal_shortlist": journal_shortlist_ready,
        "evidence_package": evidence_package_ready,
    }
    blocker_messages = {
        "paper_framing": "paper_framing_missing_or_has_no_literature_anchor",
        "journal_shortlist": "journal_shortlist_missing",
        "evidence_package": "minimum_sci_ready_evidence_package_missing",
    }

    for requirement in profile.startup_boundary_requirements:
        if readiness_by_requirement.get(requirement) is True:
            continue
        missing_requirements.append(requirement)
        blockers.append(blocker_messages[requirement])

    allow_compute_stage = not missing_requirements
    legacy_code_execution_allowed = _legacy_code_execution_allowed(profile, study_payload)
    resolved_custom_profile = effective_custom_profile(
        profile=profile,
        requested_launch_profile=requested_launch_profile,
        allow_compute_stage=allow_compute_stage,
    )
    advisories = [
        f"required_first_anchor:{required_first_anchor}",
        f"effective_custom_profile:{resolved_custom_profile}",
    ]
    if not legacy_code_execution_allowed:
        advisories.append(
            "legacy_code_execution_blocked_until_user_approval"
            if profile.legacy_code_execution_policy == "forbid_without_user_approval"
            else "legacy_code_execution_not_enabled_by_policy"
        )

    return {
        "status": "ready_for_compute_stage" if allow_compute_stage else "scout_first_required",
        "study_root": str(study_root),
        "requested_launch_profile": requested_launch_profile,
        "effective_custom_profile": resolved_custom_profile,
        "required_first_anchor": required_first_anchor,
        "allow_compute_stage": allow_compute_stage,
        "missing_requirements": missing_requirements,
        "blockers": blockers,
        "advisories": advisories,
        "legacy_code_execution_policy": profile.legacy_code_execution_policy,
        "legacy_code_execution_allowed": legacy_code_execution_allowed,
        "paper_framing_ready": paper_framing_ready,
        "journal_shortlist_ready": journal_shortlist_ready,
        "evidence_package_ready": evidence_package_ready,
    }


def render_boundary_custom_brief(
    *,
    existing_brief: str,
    boundary_gate: dict[str, Any],
) -> str:
    required_first_anchor = str(boundary_gate.get("required_first_anchor") or "scout")
    legacy_code_execution_allowed = bool(boundary_gate.get("legacy_code_execution_allowed"))
    allow_compute_stage = bool(boundary_gate.get("allow_compute_stage"))
    missing_requirements = boundary_gate.get("missing_requirements") or []

    sections = [
        f"Startup boundary gate status: {'ready' if allow_compute_stage else 'not ready'}.",
        f"Treat this startup as `{required_first_anchor}`-first. `continue_existing_state` does not authorize automatic baseline continuation.",
    ]
    if allow_compute_stage:
        sections.append(
            "Normalize the current study framing first, then decide whether any baseline reuse is still justified under the explicit paper framing, journal shortlist, and evidence package."
        )
    else:
        sections.extend(
            [
                "Before any compute-heavy work, explicitly lock the paper framing, literature anchors, journal shortlist, and minimum SCI-ready evidence package.",
                "Do not enter baseline, experiment, or analysis-campaign until the startup boundary blockers are cleared.",
            ]
        )
        if missing_requirements:
            sections.append(f"Missing startup requirements: {', '.join(str(item) for item in missing_requirements)}.")
    if legacy_code_execution_allowed:
        sections.append("Legacy implementation reuse is allowed because the workspace carries explicit approval.")
    else:
        sections.append(
            "Do not execute legacy implementation code from `refs/` or historical project directories unless the user has explicitly approved that reuse."
        )
    if existing_brief:
        sections.append("Existing startup brief context:")
        sections.append(existing_brief)
    sections.append(render_controller_first_summary())
    sections.append(render_automation_ready_summary())
    return "\n\n".join(sections).strip()
