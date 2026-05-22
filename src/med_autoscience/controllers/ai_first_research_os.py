from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1


OPERATING_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "layer_id": "mas_core",
        "owner": "MedAutoScience",
        "authority_surfaces": (
            "study_charter",
            "StudyTruthKernel",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
        ),
        "purpose": "single research, quality, publication, artifact, and user-visible truth owner",
    },
    {
        "layer_id": "quality_os",
        "owner": "MedAutoScience AI reviewer artifacts",
        "authority_surfaces": (
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "paper/pre_draft_writing_readiness.json",
            "artifacts/publication_eval/latest.json",
        ),
        "purpose": "AI-first medical quality and publishability authority",
    },
    {
        "layer_id": "runtime_os",
        "owner": "MedAutoScience Runtime OS",
        "authority_surfaces": (
            "RuntimeHealthKernel",
            "domain_health_diagnostic",
            "runtime_escalation_record.json",
            "artifacts/runtime/health/latest.json",
        ),
        "purpose": "durable long-running execution, recovery, retry, and human-gate control",
    },
    {
        "layer_id": "artifact_os",
        "owner": "MedAutoScience Artifact OS",
        "authority_surfaces": (
            "canonical paper source",
            "paper_bundle_manifest.json",
            "delivery_manifest.json",
        ),
        "purpose": "canonical-source-first manuscript, figure, table, and submission package rebuild",
    },
    {
        "layer_id": "evaluation_os",
        "owner": "MedAutoScience eval_hygiene",
        "authority_surfaces": (
            "ai_first_drift_audit",
            "ai_reviewer_calibration_corpus",
            "quality regression suite",
        ),
        "purpose": "calibration, regression, and AI-first drift prevention",
    },
    {
        "layer_id": "observability_os",
        "owner": "MedAutoScience operator projection",
        "authority_surfaces": (
            "doctor",
            "study-progress",
            "workspace-cockpit",
            "product-entry-status",
        ),
        "purpose": "operator-visible quality, runtime, artifact, and drift status without becoming authority",
    },
    {
        "layer_id": "mds_deconstruction",
        "owner": "MedAutoScience with MedDeepScientist oracle",
        "authority_surfaces": (
            "mds_capability_parity_matrix",
            "behavior_equivalence_gate",
            "runtime_backend_interface_contract",
        ),
        "purpose": "capability-by-capability parity and owner cutover before physical absorb",
    },
)

EXTERNAL_ENGINEERING_BASIS: tuple[dict[str, str], ...] = (
    {
        "basis_id": "iso_42010_architecture_description",
        "role": "stakeholder concern, viewpoint, and decision-record discipline",
        "url": "https://www.iso.org/standard/74393.html",
    },
    {
        "basis_id": "nist_ai_rmf",
        "role": "govern, map, measure, and manage loop for AI risk surfaces",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
    },
    {
        "basis_id": "equator_reporting_guidelines",
        "role": "reporting obligations before writing rather than after package assembly",
        "url": "https://www.equator-network.org/reporting-guidelines/",
    },
    {
        "basis_id": "fair_data_principles",
        "role": "findable, accessible, interoperable, reusable evidence asset discipline",
        "url": "https://www.nature.com/articles/sdata201618",
    },
    {
        "basis_id": "durable_execution",
        "role": "recoverable workflow and replay design for long-running studies",
        "url": "https://docs.temporal.io/",
    },
    {
        "basis_id": "opentelemetry_observability",
        "role": "trace, metric, and log separation for operator visibility",
        "url": "https://opentelemetry.io/docs/what-is-opentelemetry/",
    },
    {
        "basis_id": "g_eval_structured_reviewer",
        "role": "structured rubric-backed AI reviewer judgment",
        "url": "https://arxiv.org/abs/2303.16634",
    },
    {
        "basis_id": "sre_toil_elimination",
        "role": "repeated paper repair treated as reliability toil to remove by design",
        "url": "https://sre.google/sre-book/eliminating-toil/",
    },
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def build_ai_first_research_os_contract() -> dict[str, Any]:
    return {
        "surface": "ai_first_research_os_architecture_contract",
        "schema_version": SCHEMA_VERSION,
        "target_state": {
            "research_owner": "MedAutoScience",
            "quality_owner": "MedAutoScience AI reviewer artifacts",
            "mds_role": "frozen_source_archive_or_historical_fixture_only",
            "mechanical_system_role": "evidence_status_completeness_replay",
            "quality_gate_relaxation_allowed": False,
        },
        "operating_layers": [dict(layer) for layer in OPERATING_LAYERS],
        "authority_rules": {
            "submission_readiness_requires_ai_reviewer_provenance": True,
            "subjective_medical_quality_requires_ai_reviewer": True,
            "mechanical_projection_can_authorize_quality": False,
            "runtime_health_can_override_study_truth": False,
            "current_package_can_be_edit_source": False,
        },
        "migration_strategy": {
            "mode": "contract_first_strangler",
            "physical_monorepo_absorb": "landed_no_history_functional_monolith",
            "capability_cutover_rule": "mas_owned_capability_or_historical_fixture_only",
            "rollback_surface_required": True,
        },
        "external_engineering_basis": [dict(item) for item in EXTERNAL_ENGINEERING_BASIS],
    }


def validate_ai_first_research_os_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    target_state = _mapping(contract.get("target_state"))
    authority_rules = _mapping(contract.get("authority_rules"))
    if _text(target_state.get("research_owner")) != "MedAutoScience":
        issues.append({"code": "wrong_research_owner"})
    if _text(target_state.get("quality_owner")) != "MedAutoScience AI reviewer artifacts":
        issues.append({"code": "quality_owner_not_ai_reviewer_artifacts"})
    if _text(target_state.get("mds_role")) != "frozen_source_archive_or_historical_fixture_only":
        issues.append({"code": "mds_role_not_frozen_archive_or_fixture"})
    if _text(target_state.get("mechanical_system_role")) != "evidence_status_completeness_replay":
        issues.append({"code": "mechanical_system_role_not_projection_replay"})
    if target_state.get("quality_gate_relaxation_allowed") is not False:
        issues.append({"code": "quality_gate_relaxation_allowed"})
    if authority_rules.get("mechanical_projection_can_authorize_quality") is not False:
        issues.append({"code": "mechanical_projection_authorizes_quality"})
    if authority_rules.get("submission_readiness_requires_ai_reviewer_provenance") is not True:
        issues.append({"code": "submission_readiness_not_ai_reviewer_backed"})
    if authority_rules.get("subjective_medical_quality_requires_ai_reviewer") is not True:
        issues.append({"code": "subjective_quality_not_ai_reviewer_backed"})
    for layer in _list(contract.get("operating_layers")):
        if not isinstance(layer, Mapping):
            issues.append({"code": "invalid_layer"})
            continue
        if not _text(layer.get("layer_id")):
            issues.append({"code": "layer_missing_id"})
        if not _list(layer.get("authority_surfaces")):
            issues.append({"code": "layer_missing_authority_surfaces", "layer_id": _text(layer.get("layer_id"))})
    return {
        "surface": "ai_first_research_os_architecture_contract_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
