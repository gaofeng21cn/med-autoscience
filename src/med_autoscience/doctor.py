from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import platform

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.overlay import describe_medical_overlay
from med_autoscience.workspace_contracts import inspect_workspace_contracts


@dataclass(frozen=True)
class DoctorReport:
    python_version: str
    profile: WorkspaceProfile
    workspace_exists: bool
    runtime_exists: bool
    studies_exists: bool
    portfolio_exists: bool
    deepscientist_runtime_exists: bool
    medical_overlay_enabled: bool
    medical_overlay_ready: bool
    runtime_contract: dict[str, object] = field(default_factory=dict)
    launcher_contract: dict[str, object] = field(default_factory=dict)
    behavior_gate: dict[str, object] = field(default_factory=dict)


def overlay_request_from_profile(profile: WorkspaceProfile) -> dict[str, object]:
    if profile.medical_overlay_scope not in {"global", "workspace"}:
        raise ValueError(f"unsupported medical_overlay_scope: {profile.medical_overlay_scope}")
    return {
        "quest_root": profile.workspace_root if profile.medical_overlay_scope == "workspace" else None,
        "skill_ids": profile.medical_overlay_skills,
        "policy_id": profile.research_route_bias_policy,
        "archetype_ids": profile.preferred_study_archetypes,
        "default_submission_targets": profile.default_submission_targets,
        "default_publication_profile": profile.default_publication_profile,
        "default_citation_style": profile.default_citation_style,
    }


def build_doctor_report(profile: WorkspaceProfile) -> DoctorReport:
    workspace_contracts = inspect_workspace_contracts(profile)
    overlay_status = (
        describe_medical_overlay(**overlay_request_from_profile(profile))
        if profile.enable_medical_overlay
        else {"all_targets_ready": False}
    )
    return DoctorReport(
        python_version=platform.python_version(),
        profile=profile,
        workspace_exists=profile.workspace_root.exists(),
        runtime_exists=profile.runtime_root.exists(),
        studies_exists=profile.studies_root.exists(),
        portfolio_exists=profile.portfolio_root.exists(),
        deepscientist_runtime_exists=profile.deepscientist_runtime_root.exists(),
        medical_overlay_enabled=profile.enable_medical_overlay,
        medical_overlay_ready=bool(overlay_status.get("all_targets_ready")),
        runtime_contract=dict(workspace_contracts["runtime_contract"]),
        launcher_contract=dict(workspace_contracts["launcher_contract"]),
        behavior_gate=dict(workspace_contracts["behavior_gate"]),
    )


def render_doctor_report(report: DoctorReport) -> str:
    lines = [
        f"profile: {report.profile.name}",
        f"python_version: {report.python_version}",
        f"workspace_root: {report.profile.workspace_root}",
        f"runtime_root: {report.profile.runtime_root}",
        f"studies_root: {report.profile.studies_root}",
        f"portfolio_root: {report.profile.portfolio_root}",
        f"deepscientist_runtime_root: {report.profile.deepscientist_runtime_root}",
        f"deepscientist_repo_root: {report.profile.deepscientist_repo_root or '<unset>'}",
        f"default_publication_profile: {report.profile.default_publication_profile}",
        f"default_citation_style: {report.profile.default_citation_style}",
        (
            "default_submission_targets: "
            + ", ".join(
                str(item.get("publication_profile") or item.get("journal_name") or "<unresolved>")
                for item in report.profile.default_submission_targets
            )
            if report.profile.default_submission_targets
            else "default_submission_targets: <none>"
        ),
        f"enable_medical_overlay: {str(report.profile.enable_medical_overlay).lower()}",
        f"medical_overlay_scope: {report.profile.medical_overlay_scope}",
        f"medical_overlay_skills: {', '.join(report.profile.medical_overlay_skills)}",
        f"medical_overlay_bootstrap_mode: {report.profile.medical_overlay_bootstrap_mode}",
        f"research_route_bias_policy: {report.profile.research_route_bias_policy}",
        f"preferred_study_archetypes: {', '.join(report.profile.preferred_study_archetypes)}",
        f"workspace_exists: {str(report.workspace_exists).lower()}",
        f"runtime_exists: {str(report.runtime_exists).lower()}",
        f"studies_exists: {str(report.studies_exists).lower()}",
        f"portfolio_exists: {str(report.portfolio_exists).lower()}",
        f"deepscientist_runtime_exists: {str(report.deepscientist_runtime_exists).lower()}",
        f"medical_overlay_ready: {str(report.medical_overlay_ready).lower()}",
        f"runtime_contract: {json.dumps(report.runtime_contract, ensure_ascii=False, sort_keys=True)}",
        f"launcher_contract: {json.dumps(report.launcher_contract, ensure_ascii=False, sort_keys=True)}",
        f"behavior_gate: {json.dumps(report.behavior_gate, ensure_ascii=False, sort_keys=True)}",
    ]
    return "\n".join(lines) + "\n"


def render_profile(profile: WorkspaceProfile) -> str:
    lines = [
        f"name: {profile.name}",
        f"workspace_root: {profile.workspace_root}",
        f"runtime_root: {profile.runtime_root}",
        f"studies_root: {profile.studies_root}",
        f"portfolio_root: {profile.portfolio_root}",
        f"deepscientist_runtime_root: {profile.deepscientist_runtime_root}",
        f"deepscientist_repo_root: {profile.deepscientist_repo_root or '<unset>'}",
        f"default_publication_profile: {profile.default_publication_profile}",
        f"default_citation_style: {profile.default_citation_style}",
        (
            "default_submission_targets: "
            + ", ".join(
                str(item.get("publication_profile") or item.get("journal_name") or "<unresolved>")
                for item in profile.default_submission_targets
            )
            if profile.default_submission_targets
            else "default_submission_targets: <none>"
        ),
        f"enable_medical_overlay: {str(profile.enable_medical_overlay).lower()}",
        f"medical_overlay_scope: {profile.medical_overlay_scope}",
        f"medical_overlay_skills: {', '.join(profile.medical_overlay_skills)}",
        f"medical_overlay_bootstrap_mode: {profile.medical_overlay_bootstrap_mode}",
        f"research_route_bias_policy: {profile.research_route_bias_policy}",
        f"preferred_study_archetypes: {', '.join(profile.preferred_study_archetypes)}",
    ]
    return "\n".join(lines) + "\n"
