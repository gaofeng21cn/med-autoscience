from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1

MAS_AUTHORITY_SURFACES = frozenset(
    {
        "study_truth",
        "scientific_quality",
        "medical_writing_quality",
        "publication_readiness",
        "submission_authority",
        "artifact_authority",
        "user_visible_next_action",
    }
)

PROJECTION_ONLY_ROLES = frozenset({"projection", "observability", "entrypoint", "adapter"})
HUB_ROLE_CATEGORIES = frozenset({"authority", "read_model", "adapter", "materializer"})
NON_AUTHORITY_HUB_ROLES = frozenset({"read_model", "adapter"})
MDS_ALLOWED_ROLES = frozenset({"controlled_backend", "behavior_oracle", "upstream_intake_buffer"})
MDS_FORBIDDEN_AUTHORITY_SURFACES = MAS_AUTHORITY_SURFACES | frozenset(
    {
        "publication_gate_state",
        "package_state",
        "delivery_state",
    }
)

OPL_RUNTIME_LIFECYCLE_SURFACES = frozenset(
    {
        "runtime_health",
        "canonical_runtime_action",
        "runtime_lifecycle",
        "stage_attempt",
        "worker_liveness",
        "retry_dead_letter",
        "attempt_ledger",
    }
)

OWNER_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "layer_id": "mas_core",
        "owner": "MedAutoScience",
        "role": "authority",
        "hub_role": "authority",
        "authority_surfaces": [
            "study_truth",
            "user_visible_next_action",
            "artifact_authority",
        ],
        "canonical_surfaces": [
            "study_charter",
            "progress_projection",
            "StudyTruthKernel",
            "controller_decisions/latest.json",
        ],
        "may_replace_authority": True,
    },
    {
        "layer_id": "quality_os",
        "owner": "MedAutoScience",
        "role": "authority",
        "hub_role": "authority",
        "authority_surfaces": [
            "scientific_quality",
            "medical_writing_quality",
            "publication_readiness",
            "submission_authority",
        ],
        "canonical_surfaces": [
            "AI reviewer artifacts",
            "publication_eval/latest.json",
            "evidence_ledger",
            "review_ledger",
        ],
        "may_replace_authority": True,
    },
    {
        "layer_id": "runtime_os",
        "owner": "one-person-lab",
        "role": "runtime_lifecycle_owner",
        "hub_role": "authority",
        "authority_surfaces": sorted(OPL_RUNTIME_LIFECYCLE_SURFACES),
        "canonical_surfaces": [
            "OPL current_control_state",
            "OPL StageRun",
            "OPL transactional outbox",
            "OPL attempt ledger",
            "OPL observability readback",
        ],
        "may_replace_authority": True,
    },
    {
        "layer_id": "mas_runtime_diagnostic_refs",
        "owner": "MedAutoScience",
        "role": "adapter",
        "hub_role": "adapter",
        "authority_surfaces": [],
        "canonical_surfaces": [
            "RuntimeHealthKernel diagnostic snapshot",
            "domain_health_diagnostic refs",
            "runtime_escalation_record.json",
            "progress_projection runtime_health_snapshot",
        ],
        "consumes_authority_from": [
            "runtime_os",
            "mas_core",
            "quality_os",
        ],
        "diagnostic_ref_surfaces": [
            "runtime_health_snapshot",
            "canonical_runtime_action_hint",
            "opl_current_control_readback_ref",
            "opl_stage_run_readback_ref",
        ],
        "may_replace_authority": False,
    },
    {
        "layer_id": "entry_projection",
        "owner": "MedAutoScience",
        "role": "projection",
        "hub_role": "read_model",
        "authority_surfaces": [],
        "canonical_surfaces": [
            "study_progress",
            "workspace-cockpit",
            "product-entry-status",
            "product-entry manifest",
            "MCP surfaces",
        ],
        "consumes_authority_from": [
            "mas_core",
            "quality_os",
            "mas_runtime_diagnostic_refs",
        ],
        "may_replace_authority": False,
    },
    {
        "layer_id": "observability_os",
        "owner": "MedAutoScience",
        "role": "observability",
        "hub_role": "read_model",
        "authority_surfaces": [],
        "canonical_surfaces": [
            "ai_first_feedback",
            "repeat_toil_analytics",
            "runtime trajectory proof",
            "open_auto_research_projection",
        ],
        "consumes_authority_from": [
            "mas_core",
            "quality_os",
            "mas_runtime_diagnostic_refs",
        ],
        "may_replace_authority": False,
    },
    {
        "layer_id": "mds_backend",
        "owner": "MedDeepScientist",
        "role": "controlled_backend",
        "hub_role": "adapter",
        "authority_surfaces": [],
        "canonical_surfaces": [
            "daemon API",
            "quest durable layout",
            "native runtime events",
            "paper_contract_health backend_preflight",
            "manuscript coverage mechanical_oracle",
        ],
        "allowed_roles": [
            "controlled_backend",
            "behavior_oracle",
            "upstream_intake_buffer",
        ],
        "forbidden_authority_surfaces": sorted(MDS_FORBIDDEN_AUTHORITY_SURFACES),
        "may_replace_authority": False,
    },
)

DUPLICATION_RISK_CLASSES: tuple[dict[str, Any], ...] = (
    {
        "risk_id": "entry_projection_as_authority",
        "current_risk": "controlled_by_contract",
        "trigger": "study_progress, workspace-cockpit, product-entry-status, MCP, or product-entry starts deciding next action independently",
        "required_guard": "projection surfaces must consume StudyTruthKernel, MAS diagnostic runtime refs, publication_eval, and controller_decisions",
        "repair_lane": "keep entrypoints thin and add reducer-backed projection tests",
    },
    {
        "risk_id": "mds_oracle_as_quality_owner",
        "current_risk": "controlled_by_contract",
        "trigger": "paper_contract_health, coverage, prompt stage wording, or MDS artifact state authorizes manuscript quality",
        "required_guard": "MDS paper surfaces stay backend_preflight or mechanical_oracle; AI reviewer-backed publication_eval owns quality",
        "repair_lane": "promote only stable runtime protocol surfaces; keep paper-quality authority in MAS",
    },
    {
        "risk_id": "observability_as_control",
        "current_risk": "controlled_by_contract",
        "trigger": "analytics, trajectory replay, rubric score, or feedback ledger directly drives submission/finalize decisions",
        "required_guard": "observability and calibration outputs remain evidence-only and route through controller_decisions",
        "repair_lane": "mark projections observability_only and test they cannot authorize quality",
    },
    {
        "risk_id": "runtime_status_double_parse",
        "current_risk": "partially_mitigated",
        "trigger": "modules reparse active_run_id, live worker, or recovery action outside RuntimeHealthKernel/control-plane facts",
        "required_guard": "runtime liveness and recovery decisions use OPL current-control / StageRun readback; MAS RuntimeHealthKernel remains diagnostic-only",
        "repair_lane": "continue replacing local parsing with OPL-owned readback and MAS body-free diagnostic refs",
    },
)

REPAIR_PROGRAM = (
    {
        "step_id": "freeze_authority_matrix",
        "status": "landed_in_this_contract",
        "description": "Record one MAS/MDS owner matrix with authority, projection, observability, backend, and oracle roles.",
        "verification": "tests/test_architecture_owner_boundary.py",
    },
    {
        "step_id": "guard_projection_surfaces",
        "status": "active",
        "description": "Keep study_progress, workspace-cockpit, product-entry-status, product-entry, and MCP as thin projections.",
        "verification": "meta tests plus reducer-backed entry-surface tests",
    },
    {
        "step_id": "strangle_mds_authority_residue",
        "status": "active",
        "description": "Keep MDS as controlled backend, behavior oracle, and upstream intake buffer until parity proof supports promotion or absorption.",
        "verification": "MDS strangler registry plus MAS capability parity matrix",
    },
    {
        "step_id": "block_big_bang_absorb",
        "status": "active",
        "description": "Use capability-by-capability parity, rollback surface, and quality-not-relaxed gates before any physical absorb.",
        "verification": "mds_capability_cutover_gate",
    },
)

EXTERNAL_ENGINEERING_BASIS = (
    {
        "basis_id": "strangler_fig",
        "source": "Martin Fowler / Microsoft Azure Architecture Center",
        "url": "https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig",
        "applied_rule": "replace or absorb MDS surfaces incrementally through explicit promotion gates instead of big-bang rewrite",
    },
    {
        "basis_id": "architecture_fitness_functions",
        "source": "Thoughtworks evolutionary architecture",
        "url": "https://www.thoughtworks.com/insights/articles/fitness-function-driven-development",
        "applied_rule": "turn owner-boundary decisions into automated tests and structure gates",
    },
    {
        "basis_id": "team_topologies_cognitive_load",
        "source": "Team Topologies",
        "url": "https://teamtopologies.com/key-concepts-content/groupings",
        "applied_rule": "keep MAS product owners from carrying MDS backend/UI/prompt cognitive load by using clear platform/backend contracts",
    },
    {
        "basis_id": "private_owned_data",
        "source": "microservices.io database per service",
        "url": "https://microservices.io/patterns/data/database-per-service.html",
        "applied_rule": "treat durable truth surfaces as owner-private state consumed only through stable APIs/projections",
    },
)


def build_architecture_owner_boundary_report() -> dict[str, Any]:
    return {
        "surface": "mas_mds_architecture_owner_boundary_report",
        "schema_version": SCHEMA_VERSION,
        "verdict": "structural_risk_confirmed_and_guarded",
        "assessment": {
            "has_duplicate_authority_risk": True,
            "current_system_failure_mode": (
                "many modules project adjacent runtime, progress, publication, artifact, and quality facts; "
                "without hard owner rules they can drift into parallel authority"
            ),
            "recommended_strategy": "owner_matrix_plus_strangler_refactor_plus_architecture_fitness_functions",
            "hub_role_guard_strategy": "authority_read_model_adapter_materializer_roles_with_blocking_non_authority_drift",
            "big_bang_rewrite_allowed": False,
        },
        "owner_layers": [dict(layer) for layer in OWNER_LAYERS],
        "duplication_risk_classes": [dict(risk) for risk in DUPLICATION_RISK_CLASSES],
        "repair_program": [dict(step) for step in REPAIR_PROGRAM],
        "external_engineering_basis": [dict(item) for item in EXTERNAL_ENGINEERING_BASIS],
    }


def validate_architecture_owner_boundary_report(report: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(report.get("surface")) != "mas_mds_architecture_owner_boundary_report":
        issues.append({"code": "wrong_surface"})
    if _text(report.get("verdict")) != "structural_risk_confirmed_and_guarded":
        issues.append({"code": "wrong_verdict"})

    assessment = report.get("assessment")
    if not isinstance(assessment, Mapping):
        issues.append({"code": "missing_assessment"})
    else:
        if assessment.get("has_duplicate_authority_risk") is not True:
            issues.append({"code": "duplicate_authority_risk_not_acknowledged"})
        if assessment.get("big_bang_rewrite_allowed") is not False:
            issues.append({"code": "big_bang_rewrite_unblocked"})

    for layer in _list(report.get("owner_layers")):
        if not isinstance(layer, Mapping):
            issues.append({"code": "invalid_owner_layer"})
            continue
        _validate_owner_layer(layer, issues)

    risk_ids = {_text(risk.get("risk_id")) for risk in _list(report.get("duplication_risk_classes")) if isinstance(risk, Mapping)}
    required_risks = {
        "entry_projection_as_authority",
        "mds_oracle_as_quality_owner",
        "observability_as_control",
        "runtime_status_double_parse",
    }
    missing_risks = sorted(required_risks - risk_ids)
    for risk_id in missing_risks:
        issues.append({"code": "missing_duplication_risk_class", "risk_id": risk_id})

    basis_ids = {
        _text(item.get("basis_id"))
        for item in _list(report.get("external_engineering_basis"))
        if isinstance(item, Mapping)
    }
    for basis_id in ("strangler_fig", "architecture_fitness_functions", "team_topologies_cognitive_load"):
        if basis_id not in basis_ids:
            issues.append({"code": "missing_external_engineering_basis", "basis_id": basis_id})

    return {
        "surface": "mas_mds_architecture_owner_boundary_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_owner_layer(layer: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    layer_id = _text(layer.get("layer_id"))
    owner = _text(layer.get("owner"))
    role = _text(layer.get("role"))
    hub_role = _text(layer.get("hub_role"))
    authority_surfaces = set(_strings(layer.get("authority_surfaces")))

    if not layer_id:
        issues.append({"code": "layer_missing_id"})
    if not owner:
        issues.append({"code": "layer_missing_owner", "layer_id": layer_id})
    if not _strings(layer.get("canonical_surfaces")):
        issues.append({"code": "layer_missing_canonical_surfaces", "layer_id": layer_id})
    if hub_role not in HUB_ROLE_CATEGORIES:
        issues.append({"code": "hub_role_missing_or_unknown", "layer_id": layer_id, "hub_role": hub_role})

    if role in PROJECTION_ONLY_ROLES and authority_surfaces:
        issues.append({"code": "projection_layer_claims_authority", "layer_id": layer_id})
    if role in PROJECTION_ONLY_ROLES and layer.get("may_replace_authority") is not False:
        issues.append({"code": "projection_layer_can_replace_authority", "layer_id": layer_id})
    if hub_role in NON_AUTHORITY_HUB_ROLES:
        if authority_surfaces:
            issues.append({"code": "non_authority_hub_claims_authority", "layer_id": layer_id})
        if layer.get("may_replace_authority") is not False:
            issues.append({"code": "non_authority_hub_can_replace_authority", "layer_id": layer_id})
    if hub_role == "authority" and not authority_surfaces:
        issues.append({"code": "authority_hub_missing_authority_surface", "layer_id": layer_id})

    if owner == "MedDeepScientist":
        if role not in MDS_ALLOWED_ROLES:
            issues.append({"code": "mds_role_not_backend_oracle", "layer_id": layer_id})
        forbidden_claims = sorted(authority_surfaces & MDS_FORBIDDEN_AUTHORITY_SURFACES)
        if forbidden_claims:
            issues.append(
                {
                    "code": "mds_claims_mas_authority",
                    "layer_id": layer_id,
                    "authority_surfaces": forbidden_claims,
                }
            )
        if layer.get("may_replace_authority") is not False:
            issues.append({"code": "mds_can_replace_authority", "layer_id": layer_id})

    if owner == "MedAutoScience" and role == "authority":
        if not authority_surfaces:
            issues.append({"code": "mas_authority_layer_missing_authority", "layer_id": layer_id})
        if layer.get("may_replace_authority") is not True:
            issues.append({"code": "mas_authority_layer_not_marked_authoritative", "layer_id": layer_id})

    if owner == "MedAutoScience":
        forbidden_runtime = sorted(authority_surfaces & OPL_RUNTIME_LIFECYCLE_SURFACES)
        if forbidden_runtime:
            issues.append(
                {
                    "code": "mas_claims_opl_runtime_lifecycle_authority",
                    "layer_id": layer_id,
                    "authority_surfaces": forbidden_runtime,
                }
            )


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str:
    return str(value or "").strip()
