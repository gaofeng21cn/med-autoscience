from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform

from med_autoscience.profiles import WorkspaceProfile


@dataclass(frozen=True)
class DoctorReport:
    python_version: str
    profile: WorkspaceProfile
    workspace_exists: bool
    runtime_exists: bool
    studies_exists: bool
    portfolio_exists: bool
    deepscientist_runtime_exists: bool


def build_doctor_report(profile: WorkspaceProfile) -> DoctorReport:
    return DoctorReport(
        python_version=platform.python_version(),
        profile=profile,
        workspace_exists=profile.workspace_root.exists(),
        runtime_exists=profile.runtime_root.exists(),
        studies_exists=profile.studies_root.exists(),
        portfolio_exists=profile.portfolio_root.exists(),
        deepscientist_runtime_exists=profile.deepscientist_runtime_root.exists(),
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
        f"default_publication_profile: {report.profile.default_publication_profile}",
        f"default_citation_style: {report.profile.default_citation_style}",
        f"workspace_exists: {str(report.workspace_exists).lower()}",
        f"runtime_exists: {str(report.runtime_exists).lower()}",
        f"studies_exists: {str(report.studies_exists).lower()}",
        f"portfolio_exists: {str(report.portfolio_exists).lower()}",
        f"deepscientist_runtime_exists: {str(report.deepscientist_runtime_exists).lower()}",
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
        f"default_publication_profile: {profile.default_publication_profile}",
        f"default_citation_style: {profile.default_citation_style}",
    ]
    return "\n".join(lines) + "\n"

