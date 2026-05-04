from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1

GROUP_IDS = (
    "mas_core",
    "quality_os",
    "runtime_os",
    "artifact_delivery",
    "product_entry_projection",
    "observability_os",
    "mds_backend_oracle",
    "maintainability",
)

AUTHORITY_SURFACES = frozenset(
    {
        "study_truth",
        "quality_truth",
        "runtime_health",
        "scientific_quality",
        "medical_writing_quality",
        "publication_readiness",
        "submission_authority",
        "artifact_authority",
        "user_visible_next_action",
        "canonical_runtime_action",
    }
)

MAS_AUTHORITY_SURFACES = frozenset(
    {
        "study_truth",
        "quality_truth",
        "runtime_health",
        "scientific_quality",
        "medical_writing_quality",
        "publication_readiness",
        "submission_authority",
        "artifact_authority",
        "user_visible_next_action",
        "canonical_runtime_action",
    }
)

PROJECTION_GROUPS = frozenset({"product_entry_projection", "observability_os"})
MDS_FORBIDDEN_AUTHORITY = MAS_AUTHORITY_SURFACES | frozenset({"publication_gate_state", "delivery_state"})
ARTIFACT_FORBIDDEN_STUDY_TRUTH = frozenset(
    {
        "study_truth",
        "quality_truth",
        "runtime_health",
        "scientific_quality",
        "medical_writing_quality",
        "publication_readiness",
        "submission_authority",
        "user_visible_next_action",
        "canonical_runtime_action",
    }
)
MAINTAINABILITY_FORBIDDEN_TRUTH_WRITES = frozenset(
    {
        "study_truth",
        "quality_truth",
        "runtime_health",
        "publication_readiness",
        "submission_authority",
        "artifact_authority",
        "controller_decisions/latest.json",
        "study_runtime_status",
        "runtime_watch",
    }
)

MODULE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "group_id": "mas_core",
        "layer": "authority",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/study_truth_kernel.py",
            "src/med_autoscience/controllers/study_control_plane_kernel.py",
            "src/med_autoscience/controllers/control_plane_facts.py",
            "src/med_autoscience/controllers/control_intent.py",
        ],
        "allowed_dependencies": ["quality_os", "runtime_os", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["product_entry_projection", "mds_backend_oracle"],
        "writable_authority_surfaces": [
            "study_truth",
            "user_visible_next_action",
        ],
        "projection_only": False,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": True,
        "modifies_runtime_or_study_truth": True,
    },
    {
        "group_id": "quality_os",
        "layer": "authority",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/medical_quality_operating_system.py",
            "src/med_autoscience/controllers/ai_reviewer_publication_eval_workflow.py",
            "src/med_autoscience/controllers/quality_ledger_enforcer.py",
            "src/med_autoscience/controllers/publication_gate.py",
        ],
        "allowed_dependencies": ["mas_core", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["product_entry_projection", "mds_backend_oracle"],
        "writable_authority_surfaces": [
            "quality_truth",
            "scientific_quality",
            "medical_writing_quality",
            "publication_readiness",
            "submission_authority",
        ],
        "projection_only": False,
        "may_control_runtime": False,
        "may_authorize_publication": True,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
    {
        "group_id": "runtime_os",
        "layer": "authority",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/runtime_health_kernel.py",
            "src/med_autoscience/controllers/runtime_watch.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_router.py",
        ],
        "allowed_dependencies": ["mas_core", "quality_os", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["product_entry_projection", "mds_backend_oracle"],
        "writable_authority_surfaces": [
            "runtime_health",
            "canonical_runtime_action",
        ],
        "projection_only": False,
        "may_control_runtime": True,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": True,
    },
    {
        "group_id": "artifact_delivery",
        "layer": "delivery",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/artifact_runtime_proof.py",
            "src/med_autoscience/controllers/artifact_lifecycle_authority_kernel.py",
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/delivery_legacy_visibility.py",
            "src/med_autoscience/controllers/delivery_visibility_projection.py",
            "src/med_autoscience/controllers/submission_package_layout.py",
        ],
        "allowed_dependencies": ["mas_core", "quality_os", "runtime_os"],
        "forbidden_dependencies": ["product_entry_projection", "observability_os", "mds_backend_oracle"],
        "writable_authority_surfaces": ["artifact_authority"],
        "projection_only": False,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
    {
        "group_id": "product_entry_projection",
        "layer": "projection",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/study_progress.py",
            "src/med_autoscience/controllers/study_progress_parts/",
            "src/med_autoscience/controllers/product_entry_parts/",
            "src/med_autoscience/controllers/workspace_entry_rendering.py",
        ],
        "allowed_dependencies": ["mas_core", "quality_os", "runtime_os", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["mds_backend_oracle"],
        "writable_authority_surfaces": [],
        "projection_only": True,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
    {
        "group_id": "observability_os",
        "layer": "observability",
        "owner": "MedAutoScience",
        "repo_targets": [
            "src/med_autoscience/controllers/ai_first_observability.py",
            "src/med_autoscience/controllers/ai_first_feedback.py",
            "src/med_autoscience/controllers/runtime_trajectory_proof.py",
            "src/med_autoscience/controllers/quality_regression_projection.py",
            "src/med_autoscience/controllers/literature_provider_runtime.py",
            "src/med_autoscience/controllers/outcome_provider_ops_projection.py",
        ],
        "allowed_dependencies": ["mas_core", "quality_os", "runtime_os", "artifact_delivery"],
        "forbidden_dependencies": ["product_entry_projection", "mds_backend_oracle"],
        "writable_authority_surfaces": [],
        "projection_only": True,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
    {
        "group_id": "mds_backend_oracle",
        "layer": "backend_oracle",
        "owner": "MedDeepScientist",
        "repo_targets": [
            "src/med_autoscience/controllers/mds_capability_parity.py",
            "src/med_autoscience/controllers/med_deepscientist_upgrade_check.py",
            "src/med_autoscience/controllers/study_runtime_transport.py",
        ],
        "allowed_dependencies": ["runtime_os", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["product_entry_projection"],
        "writable_authority_surfaces": [],
        "projection_only": True,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
    {
        "group_id": "maintainability",
        "layer": "maintainability",
        "owner": "MedAutoScience",
        "repo_targets": [
            "scripts/line_budget.py",
            "scripts/run-structure-quality-gate.sh",
            "src/med_autoscience/controllers/boundary_fitness.py",
            "src/med_autoscience/controllers/module_boundary_audit.py",
        ],
        "allowed_dependencies": ["mas_core", "quality_os", "runtime_os", "artifact_delivery", "observability_os"],
        "forbidden_dependencies": ["product_entry_projection", "mds_backend_oracle"],
        "writable_authority_surfaces": [],
        "projection_only": True,
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_be_study_truth": False,
        "modifies_runtime_or_study_truth": False,
    },
)

BOUNDARY_RULES: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "projection_layers_cannot_claim_authority",
        "applies_to": ["product_entry_projection", "observability_os"],
        "requirement": "projection-only groups must expose writable_authority_surfaces=[] and cannot be study truth",
    },
    {
        "rule_id": "observability_cannot_control",
        "applies_to": ["observability_os"],
        "requirement": "observability evidence, calibration, and provider health cannot call itself controller action authority",
    },
    {
        "rule_id": "mds_backend_oracle_cannot_claim_mas_authority",
        "applies_to": ["mds_backend_oracle"],
        "requirement": "MDS can remain backend, native event source, behavior oracle, and upstream intake buffer only",
    },
    {
        "rule_id": "artifact_delivery_cannot_be_study_truth",
        "applies_to": ["artifact_delivery"],
        "requirement": "artifact proof can support delivery authority but cannot become study truth or publication readiness",
    },
    {
        "rule_id": "maintainability_cannot_modify_truth",
        "applies_to": ["maintainability"],
        "requirement": "structure, audit, compaction, and worktree cleanup lanes cannot write runtime or study truth",
    },
)

TRUTH_BOUNDARIES: tuple[dict[str, Any], ...] = (
    {
        "boundary_id": "study_truth",
        "authority_owner": "StudyTruthKernel",
        "projection_consumers": ["study-progress", "workspace-cockpit", "product-frontdesk"],
    },
    {
        "boundary_id": "runtime_truth",
        "authority_owner": "RuntimeHealthKernel",
        "projection_consumers": ["study_runtime_status", "runtime_watch", "mainline-status"],
    },
    {
        "boundary_id": "quality_truth",
        "authority_owner": "publication_eval/latest.json + publication_gate",
        "projection_consumers": ["mainline-status", "AI reviewer calibration reports"],
    },
    {
        "boundary_id": "delivery_truth",
        "authority_owner": "controller-authorized artifact sync/apply",
        "projection_consumers": ["delivery inspection", "legacy upgrade visibility"],
    },
    {
        "boundary_id": "maintainability_truth",
        "authority_owner": "Sentrux structure lane + line budget + owner-boundary tests",
        "projection_consumers": ["module boundary audit", "structure target list"],
    },
)


def build_module_boundary_audit_report() -> dict[str, Any]:
    return {
        "surface": "mas_mds_module_boundary_audit_report",
        "schema_version": SCHEMA_VERSION,
        "verdict": "module_boundaries_declared_and_guarded",
        "target_architecture": {
            "dependency_direction": "authority_kernels_to_thin_projection_read_models",
            "high_aggregation_low_coupling_acceptance": {
                "all_repo_targets_grouped": True,
                "cross_group_dependencies_must_be_declared": True,
                "projection_authority_claims_allowed": False,
                "observability_direct_control_allowed": False,
                "mds_mas_authority_claims_allowed": False,
                "artifact_delivery_as_study_truth_allowed": False,
                "maintainability_truth_writes_allowed": False,
            },
        },
        "module_groups": [dict(group) for group in MODULE_GROUPS],
        "boundary_rules": [dict(rule) for rule in BOUNDARY_RULES],
        "truth_boundaries": [dict(boundary) for boundary in TRUTH_BOUNDARIES],
    }


def validate_module_boundary_audit_report(report: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(report.get("surface")) != "mas_mds_module_boundary_audit_report":
        issues.append({"code": "wrong_surface"})
    if _text(report.get("verdict")) != "module_boundaries_declared_and_guarded":
        issues.append({"code": "wrong_verdict"})

    groups = [_mapping(item) for item in _list(report.get("module_groups"))]
    by_group = {_text(group.get("group_id")): group for group in groups if _text(group.get("group_id"))}
    for group_id in GROUP_IDS:
        if group_id not in by_group:
            issues.append({"code": "missing_module_group", "group_id": group_id})

    for group in groups:
        _validate_group(group, by_group, issues)

    acceptance = _mapping(_mapping(report.get("target_architecture")).get("high_aggregation_low_coupling_acceptance"))
    required_false_flags = {
        "projection_authority_claims_allowed",
        "observability_direct_control_allowed",
        "mds_mas_authority_claims_allowed",
        "artifact_delivery_as_study_truth_allowed",
        "maintainability_truth_writes_allowed",
    }
    for key in required_false_flags:
        if acceptance.get(key) is not False:
            issues.append({"code": "acceptance_flag_not_fail_closed", "flag": key})
    for key in ("all_repo_targets_grouped", "cross_group_dependencies_must_be_declared"):
        if acceptance.get(key) is not True:
            issues.append({"code": "acceptance_flag_not_enforced", "flag": key})

    return {
        "surface": "mas_mds_module_boundary_audit_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_group(
    group: Mapping[str, Any],
    by_group: Mapping[str, Mapping[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    group_id = _text(group.get("group_id"))
    writable = set(_strings(group.get("writable_authority_surfaces")))
    allowed_dependencies = set(_strings(group.get("allowed_dependencies")))
    forbidden_dependencies = set(_strings(group.get("forbidden_dependencies")))

    if not group_id:
        issues.append({"code": "group_missing_id"})
    if not _strings(group.get("repo_targets")):
        issues.append({"code": "group_missing_repo_targets", "group_id": group_id})
    if not _text(group.get("owner")):
        issues.append({"code": "group_missing_owner", "group_id": group_id})
    if allowed_dependencies & forbidden_dependencies:
        issues.append(
            {
                "code": "dependency_allowed_and_forbidden",
                "group_id": group_id,
                "dependencies": sorted(allowed_dependencies & forbidden_dependencies),
            }
        )
    for dependency in allowed_dependencies | forbidden_dependencies:
        if dependency not in by_group:
            issues.append({"code": "unknown_dependency_group", "group_id": group_id, "dependency": dependency})

    if group_id in PROJECTION_GROUPS and writable:
        issues.append(
            {
                "code": "projection_layer_claims_authority",
                "group_id": group_id,
                "authority_surfaces": sorted(writable),
            }
        )
    if group_id in PROJECTION_GROUPS and group.get("may_be_study_truth") is not False:
        issues.append({"code": "projection_layer_can_be_study_truth", "group_id": group_id})

    if group_id == "observability_os":
        if group.get("may_control_runtime") is not False or group.get("may_authorize_publication") is not False:
            issues.append({"code": "observability_direct_control", "group_id": group_id})

    if group_id == "mds_backend_oracle":
        forbidden = sorted(writable & MDS_FORBIDDEN_AUTHORITY)
        if forbidden:
            issues.append({"code": "mds_claims_mas_authority", "group_id": group_id, "authority_surfaces": forbidden})
        if group.get("may_control_runtime") is not False or group.get("may_authorize_publication") is not False:
            issues.append({"code": "mds_claims_runtime_or_publication_authority", "group_id": group_id})

    if group_id == "artifact_delivery":
        forbidden = sorted(writable & ARTIFACT_FORBIDDEN_STUDY_TRUTH)
        if forbidden or group.get("may_be_study_truth") is not False:
            issues.append(
                {
                    "code": "artifact_delivery_becomes_study_truth",
                    "group_id": group_id,
                    "authority_surfaces": forbidden,
                }
            )

    if group_id == "maintainability":
        forbidden = sorted(writable & MAINTAINABILITY_FORBIDDEN_TRUTH_WRITES)
        if forbidden or group.get("modifies_runtime_or_study_truth") is not False:
            issues.append(
                {
                    "code": "maintainability_modifies_runtime_or_study_truth",
                    "group_id": group_id,
                    "authority_surfaces": forbidden,
                }
            )

    unknown_authority = sorted(writable - AUTHORITY_SURFACES)
    if unknown_authority:
        issues.append(
            {"code": "unknown_authority_surface", "group_id": group_id, "authority_surfaces": unknown_authority}
        )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str:
    return str(value or "").strip()
