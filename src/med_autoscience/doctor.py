from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
import platform

from med_autoscience.ai_first_drift_audit import run_ai_first_drift_audit
from med_autoscience.controllers.ai_first_observability import build_doctor_ai_first_observability_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.scholarskills_required_package import (
    build_scholarskills_required_package_template,
    query_scholarskills_required_package_readback,
)
from med_autoscience.workspace_contracts import inspect_workspace_contracts, legacy_external_runtime_tombstone_contract


@dataclass(frozen=True)
class DoctorReport:
    python_version: str
    profile: WorkspaceProfile
    workspace_exists: bool
    runtime_exists: bool
    studies_exists: bool
    portfolio_exists: bool
    med_deepscientist_runtime_exists: bool
    runtime_contract: dict[str, object] = field(default_factory=dict)
    launcher_contract: dict[str, object] = field(default_factory=dict)
    behavior_gate: dict[str, object] = field(default_factory=dict)
    external_runtime_contract: dict[str, object] = field(default_factory=dict)
    workspace_domain_route_contract: dict[str, object] = field(default_factory=dict)
    scholarskills_required_package: dict[str, object] = field(default_factory=dict)
    ai_first_drift_audit: dict[str, object] = field(default_factory=dict)
    ai_first_observability: dict[str, object] = field(default_factory=dict)


def build_doctor_report(
    profile: WorkspaceProfile,
    *,
    scholarskills_required_package: Mapping[str, object] | None = None,
) -> DoctorReport:
    workspace_contracts = inspect_workspace_contracts(profile)
    ai_first_drift_audit = dict(
        run_ai_first_drift_audit()
    )
    return DoctorReport(
        python_version=platform.python_version(),
        profile=profile,
        workspace_exists=profile.workspace_root.exists(),
        runtime_exists=profile.runtime_root.exists(),
        studies_exists=profile.studies_root.exists(),
        portfolio_exists=profile.portfolio_root.exists(),
        med_deepscientist_runtime_exists=profile.med_deepscientist_runtime_root.exists(),
        runtime_contract=dict(workspace_contracts["runtime_contract"]),
        launcher_contract=dict(workspace_contracts["launcher_contract"]),
        behavior_gate=dict(workspace_contracts["behavior_gate"]),
        external_runtime_contract=dict(
            workspace_contracts.get(
                "external_runtime_contract",
                legacy_external_runtime_tombstone_contract(),
            )
        ),
        workspace_domain_route_contract={
            "schema_version": 1,
            "surface_kind": "opl_current_control_state_handoff",
            "loaded": True,
            "owner": "one-person-lab",
            "effect": "refs_only",
            "summary": "generic runtime supervision is owned by OPL current_control_state",
            "mas_runtime_supervision_read_model_removed": True,
            "workspace_root": str(profile.workspace_root),
        },
        scholarskills_required_package=(
            dict(scholarskills_required_package)
            if scholarskills_required_package is not None
            else query_scholarskills_required_package_readback(
                workspace_root=profile.workspace_root
            )
        ),
        ai_first_drift_audit=ai_first_drift_audit,
        ai_first_observability=dict(
            build_doctor_ai_first_observability_summary(drift_audit=ai_first_drift_audit)
        ),
    )


def render_doctor_report(report: DoctorReport) -> str:
    lines = [
        f"profile: {report.profile.name}",
        f"python_version: {report.python_version}",
        f"workspace_root: {report.profile.workspace_root}",
        f"opl_runtime_locator: {report.profile.runtime_root}",
        f"mas_runtime_home: {report.profile.managed_runtime_home}",
        f"studies_root: {report.profile.studies_root}",
        f"portfolio_root: {report.profile.portfolio_root}",
        f"historical_fixture_runtime_root: {report.profile.med_deepscientist_runtime_root}",
        f"controlled_backend_audit_repo_root: {report.profile.med_deepscientist_repo_root or '<unset>'}",
        f"hermes_agent_repo_root: {report.profile.hermes_agent_repo_root or '<unset>'}",
        f"hermes_home_root: {report.profile.hermes_home_root}",
        f"default_publication_profile: {report.profile.default_publication_profile}",
        f"default_citation_style: {report.profile.default_citation_style}",
        (
            "default_submission_targets: "
            + ", ".join(
                str(item.get("exporter_profile") or item.get("journal_name") or "<unresolved>")
                for item in report.profile.default_submission_targets
            )
            if report.profile.default_submission_targets
            else "default_submission_targets: <none>"
        ),
        f"research_route_bias_policy: {report.profile.research_route_bias_policy}",
        f"preferred_study_archetypes: {', '.join(report.profile.preferred_study_archetypes)}",
        f"workspace_exists: {str(report.workspace_exists).lower()}",
        f"runtime_exists: {str(report.runtime_exists).lower()}",
        f"studies_exists: {str(report.studies_exists).lower()}",
        f"portfolio_exists: {str(report.portfolio_exists).lower()}",
        f"historical_fixture_runtime_exists: {str(report.med_deepscientist_runtime_exists).lower()}",
        f"runtime_contract: {json.dumps(report.runtime_contract, ensure_ascii=False, sort_keys=True)}",
        f"launcher_contract: {json.dumps(report.launcher_contract, ensure_ascii=False, sort_keys=True)}",
        f"behavior_gate: {json.dumps(report.behavior_gate, ensure_ascii=False, sort_keys=True)}",
        f"external_runtime_contract: {json.dumps(report.external_runtime_contract, ensure_ascii=False, sort_keys=True)}",
        (
            "workspace_domain_route_contract: "
            + json.dumps(report.workspace_domain_route_contract, ensure_ascii=False, sort_keys=True)
        ),
        (
            "scholarskills_required_package: "
            + json.dumps(report.scholarskills_required_package, ensure_ascii=False, sort_keys=True)
        ),
        f"ai_first_drift_audit: {json.dumps(report.ai_first_drift_audit, ensure_ascii=False, sort_keys=True)}",
        f"ai_first_observability: {json.dumps(report.ai_first_observability, ensure_ascii=False, sort_keys=True)}",
    ]
    return "\n".join(lines) + "\n"


def render_profile(profile: WorkspaceProfile) -> str:
    lines = [
        f"name: {profile.name}",
        f"workspace_root: {profile.workspace_root}",
        f"opl_runtime_locator: {profile.runtime_root}",
        f"mas_runtime_home: {profile.managed_runtime_home}",
        f"studies_root: {profile.studies_root}",
        f"portfolio_root: {profile.portfolio_root}",
        f"historical_fixture_runtime_root: {profile.med_deepscientist_runtime_root}",
        f"controlled_backend_audit_repo_root: {profile.med_deepscientist_repo_root or '<unset>'}",
        f"hermes_agent_repo_root: {profile.hermes_agent_repo_root or '<unset>'}",
        f"hermes_home_root: {profile.hermes_home_root}",
        f"default_publication_profile: {profile.default_publication_profile}",
        f"default_citation_style: {profile.default_citation_style}",
        (
            "default_submission_targets: "
            + ", ".join(
                str(item.get("exporter_profile") or item.get("journal_name") or "<unresolved>")
                for item in profile.default_submission_targets
            )
            if profile.default_submission_targets
            else "default_submission_targets: <none>"
        ),
        f"research_route_bias_policy: {profile.research_route_bias_policy}",
        f"preferred_study_archetypes: {', '.join(profile.preferred_study_archetypes)}",
        (
            "scholarskills_required_package: "
            + json.dumps(build_scholarskills_required_package_template(), ensure_ascii=False, sort_keys=True)
        ),
    ]
    return "\n".join(lines) + "\n"
