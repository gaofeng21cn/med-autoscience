from __future__ import annotations

import copy
from typing import Any, Mapping

from med_autoscience.controllers.mds_capability_parity_parts.behavior_equivalence import (
    ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES,
    ALLOWED_BEHAVIOR_OPERATOR_ACTIONS,
    build_mds_behavior_equivalence_matrix,
    validate_mds_behavior_equivalence_matrix,
)


SCHEMA_VERSION = 1
ALLOWED_CAPABILITY_CLASSIFICATIONS: tuple[str, ...] = (
    "mas_owned",
    "rewrite_in_mas",
    "fixture_only",
    "retire",
    "external_source_archive_only",
)
CUTOVER_REQUIRED_GATES: tuple[str, ...] = (
    "mas_side_contract_exists",
    "mds_oracle_fixture_exists",
    "quality_gate_not_relaxed",
    "rollback_surface_exists",
    "old_mds_authority_surface_retired_or_marked_oracle",
)
PROVENANCE_REF = "docs/references/med-deepscientist/source_provenance.json"
MDS_FINAL_ROLE = "frozen_source_archive_or_historical_fixture_only"
MDS_FUNCTIONAL_MONOLITH_STATUS = "landed_no_history_functional_monolith"
MDS_CUTOVER_STATUS = "landed_functional_monolith"


def _supersede_proof(
    *,
    proof_id: str,
    mas_owner_surface: str,
    mechanical_signal_can_only: str,
) -> dict[str, Any]:
    return {
        "proof_id": proof_id,
        "mas_owned": True,
        "mas_owner_surface": mas_owner_surface,
        "mds_mechanical_signal_role": "evidence_only",
        "mechanical_signal_can_only": mechanical_signal_can_only,
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }


SUPERSEDE_PROOFS_BY_CAPABILITY: dict[str, tuple[dict[str, Any], ...]] = {
    "runtime_execution": (),
    "artifact_inventory": (
        _supersede_proof(
            proof_id="artifact_inventory",
            mas_owner_surface="Artifact OS artifact inventory projection",
            mechanical_signal_can_only="request_artifact_review",
        ),
        _supersede_proof(
            proof_id="package_locator",
            mas_owner_surface="Artifact OS package locator and artifact_runtime_proof",
            mechanical_signal_can_only="request_package_review",
        ),
    ),
    "paper_contract_health": (
        _supersede_proof(
            proof_id="paper_contract_health",
            mas_owner_surface="Quality OS publication_eval/latest.json",
            mechanical_signal_can_only="request_paper_health_review",
        ),
    ),
    "manuscript_coverage": (
        _supersede_proof(
            proof_id="manuscript_coverage",
            mas_owner_surface="Quality OS AI reviewer coverage request",
            mechanical_signal_can_only="request_coverage_review",
        ),
    ),
    "prompt_stage_discipline": (
        _supersede_proof(
            proof_id="prompt_stage_discipline",
            mas_owner_surface="Quality OS controller stage discipline",
            mechanical_signal_can_only="request_stage_review",
        ),
    ),
    "memory_and_lesson_store": (
        _supersede_proof(
            proof_id="memory_and_lesson_store",
            mas_owner_surface="Evaluation OS incident learning store",
            mechanical_signal_can_only="request_lesson_review",
        ),
    ),
}

CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "runtime_execution",
        "title": "Runtime execution",
        "classification": "mas_owned",
        "mds_authority_role": "backend",
        "mas_target_owner": "Runtime OS",
        "mas_owner_surface": "Runtime OS study_runtime_status/runtime_watch replay consumer",
        "oracle_fixture_ref": "fixtures/mds_oracle/runtime_execution.json",
        "required_parity_proof": "runtime execution replay and recovery regression suite",
        "parity_proof": {
            "proof_kind": "execution_replay",
            "mas_contract": "study_runtime_status/runtime_watch own runtime decisions and recovery visibility",
            "mds_oracle": "MDS quest execution traces can be replayed only as backend behavior fixtures",
            "acceptance": "MAS recovery decisions match or intentionally supersede replayed MDS behavior",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "study_runtime_status/runtime_watch retain the MAS runtime owner decision log",
        "old_mds_authority_surface_status": "marked_oracle",
    },
    {
        "capability_id": "artifact_inventory",
        "title": "Artifact inventory",
        "classification": "fixture_only",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Artifact OS",
        "mas_owner_surface": "Artifact OS package locator and inventory projection",
        "oracle_fixture_ref": "fixtures/mds_oracle/artifact_inventory.json",
        "required_parity_proof": "artifact inventory projection parity fixtures",
        "parity_proof": {
            "proof_kind": "artifact_projection",
            "mas_contract": "MAS artifact inventory is the consumer-facing projection owner",
            "mds_oracle": "MDS artifact layout is a fixture for legacy inventory compatibility",
            "acceptance": "MAS inventory preserves discoverability without granting MDS delivery authority",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "MAS artifact inventory can continue serving the last accepted projection",
        "old_mds_authority_surface_status": "marked_oracle",
    },
    {
        "capability_id": "paper_contract_health",
        "title": "Paper contract health",
        "classification": "fixture_only",
        "mds_authority_role": "mechanical_oracle",
        "mas_target_owner": "Quality OS",
        "mas_owner_surface": "Quality OS publication gate mechanical-preflight input",
        "oracle_fixture_ref": "fixtures/mds_oracle/paper_contract_health.json",
        "required_parity_proof": "backend preflight parity without quality-ready authority",
        "parity_proof": {
            "proof_kind": "contract_preflight",
            "mas_contract": "publication gate and controller decisions own paper readiness",
            "mds_oracle": "MDS contract checks are mechanical preflight observations",
            "acceptance": "MDS health signals never promote a paper to medical-quality ready",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "publication_eval/latest.json and controller_decisions/latest.json remain the readiness owners",
        "old_mds_authority_surface_status": "marked_oracle",
    },
    {
        "capability_id": "manuscript_coverage",
        "title": "Manuscript coverage",
        "classification": "fixture_only",
        "mds_authority_role": "mechanical_oracle",
        "mas_target_owner": "Quality OS",
        "mas_owner_surface": "Quality OS AI reviewer coverage-request input",
        "oracle_fixture_ref": "fixtures/mds_oracle/manuscript_coverage.json",
        "required_parity_proof": "mechanical coverage fixtures with AI preflight required",
        "parity_proof": {
            "proof_kind": "coverage_fixture",
            "mas_contract": "AI review and publication eval own medical manuscript quality",
            "mds_oracle": "MDS coverage counts are mechanical completeness signals",
            "acceptance": "Coverage parity can request review but cannot authorize final quality",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "AI review and publication eval gates remain required before package readiness",
        "old_mds_authority_surface_status": "marked_oracle",
    },
    {
        "capability_id": "prompt_stage_discipline",
        "title": "Prompt stage discipline",
        "classification": "mas_owned",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Quality OS",
        "mas_owner_surface": "Quality OS controller stage discipline fixture",
        "oracle_fixture_ref": "fixtures/mds_oracle/prompt_stage_discipline.json",
        "required_parity_proof": "stage prompt contract parity and prompt-only gate audit",
        "parity_proof": {
            "proof_kind": "stage_contract",
            "mas_contract": "MAS controller stages own allowed prompt transitions",
            "mds_oracle": "MDS stage prompts provide behavior examples and violation fixtures",
            "acceptance": "MAS stage discipline remains explicit and auditable after parity import",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "MAS controller stage contracts retain prompt transition authority",
        "old_mds_authority_surface_status": "marked_oracle",
    },
    {
        "capability_id": "memory_and_lesson_store",
        "title": "Memory and lesson store",
        "classification": "retire",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Evaluation OS",
        "mas_owner_surface": "Evaluation OS incident learning intake fixture",
        "oracle_fixture_ref": "fixtures/mds_oracle/memory_and_lesson_store.json",
        "required_parity_proof": "lesson intake and incident learning parity fixtures",
        "parity_proof": {
            "proof_kind": "lesson_store_projection",
            "mas_contract": "MAS incident learning owns reusable lessons and operator-visible memory",
            "mds_oracle": "MDS lessons are intake material for parity and regression cases",
            "acceptance": "Lessons are imported as evidence, not as autonomous quality decisions",
        },
        "can_authorize_medical_quality": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "parity_status": "oracle_fixture_defined",
        "provenance_ref": PROVENANCE_REF,
        "rollback_surface": "MAS incident learning store keeps imported lessons evidence-only",
        "old_mds_authority_surface_status": "marked_oracle",
    },
)

REMAINING_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "surface_id": "runtime_core_daemon",
        "title": "Runtime core daemon",
        "classification": "rewrite_in_mas",
        "mds_source_surface": "daemon/session runtime core",
        "mas_target_owner": "Runtime OS",
        "mds_final_role": "external_source_archive_only",
        "cutover_contract": "MAS Runtime OS owns daemon/session lifecycle; external MDS daemon is not a default dependency.",
        "owner_boundary": "study_runtime_status/runtime_watch remain MAS-owned runtime truth surfaces.",
    },
    {
        "surface_id": "quest_lifecycle",
        "title": "Quest lifecycle",
        "classification": "mas_owned",
        "mds_source_surface": "quest layout and lifecycle behavior",
        "mas_target_owner": "Runtime OS",
        "mds_final_role": "historical_oracle_fixture_only",
        "cutover_contract": "MAS runtime/quests and runtime_lifecycle.sqlite own quest lifecycle and materialization.",
        "owner_boundary": "Legacy quest data can be replayed or imported only through explicit restore/import diagnostics.",
    },
    {
        "surface_id": "worker_runner_lifecycle",
        "title": "Worker and runner lifecycle",
        "classification": "rewrite_in_mas",
        "mds_source_surface": "worker runners and liveness loops",
        "mas_target_owner": "Runtime OS",
        "mds_final_role": "external_source_archive_only",
        "cutover_contract": "MAS-owned runner lifecycle must expose worker state without requiring MDS worker processes.",
        "owner_boundary": "Controller-authorized runtime actions stay in MAS controller/runtime surfaces.",
    },
    {
        "surface_id": "channels_connectors_transport",
        "title": "Channels, connectors, and transport",
        "classification": "rewrite_in_mas",
        "mds_source_surface": "runtime connector and transport layer",
        "mas_target_owner": "Runtime OS",
        "mds_final_role": "explicit_legacy_diagnostic_only",
        "cutover_contract": "MAS runtime transport owns active communication; MDS connectors remain diagnostic fixtures.",
        "owner_boundary": "Transport observations cannot write study truth, quality truth, or publication authority.",
    },
    {
        "surface_id": "mcp_surface",
        "title": "MCP surface",
        "classification": "retire",
        "mds_source_surface": "MDS MCP entrypoints",
        "mas_target_owner": "MAS MCP",
        "mds_final_role": "retired_surface",
        "cutover_contract": "Active MCP commands route through MAS; old MDS MCP names fail closed or stay explicit legacy diagnostics.",
        "owner_boundary": "MCP exposes MAS truth refs and does not make MDS a backend fallback.",
    },
    {
        "surface_id": "tui_web_visual_status",
        "title": "TUI and Web visual status",
        "classification": "rewrite_in_mas",
        "mds_source_surface": "TUI/Web status dashboard",
        "mas_target_owner": "Progress Portal",
        "mds_final_role": "explicit_legacy_diagnostic_only",
        "cutover_contract": "MAS Progress Portal is the default visual status surface; old MDS WebUI is diagnostic only.",
        "owner_boundary": "Visual status consumes MAS progress payloads and cannot reinterpret study truth.",
    },
    {
        "surface_id": "gitops_workspace_state",
        "title": "GitOps workspace state",
        "classification": "retire",
        "mds_source_surface": "workspace root Git and quest Git operations",
        "mas_target_owner": "Runtime lifecycle",
        "mds_final_role": "retired_surface",
        "cutover_contract": "MAS runtime lifecycle uses SQLite/read-model/restore proof, not default root Git or quest Git.",
        "owner_boundary": "Git history can remain only as archived restore material outside active lifecycle authority.",
    },
    {
        "surface_id": "skills_overlay_templates",
        "title": "Skills and overlay templates",
        "classification": "fixture_only",
        "mds_source_surface": "skills, prompts, and overlay templates",
        "mas_target_owner": "MAS app skill",
        "mds_final_role": "historical_fixture_only",
        "cutover_contract": "Reusable templates may become MAS fixtures; no global MDS skill injection or default entry remains.",
        "owner_boundary": "Templates cannot authorize quality, runtime action, or publication readiness.",
    },
    {
        "surface_id": "team_multiagent_coordination",
        "title": "Team and multi-agent coordination",
        "classification": "fixture_only",
        "mds_source_surface": "team orchestration and multi-agent patterns",
        "mas_target_owner": "Controller",
        "mds_final_role": "historical_oracle_fixture_only",
        "cutover_contract": "MAS controller owns coordination semantics; MDS team behavior can only seed parity fixtures.",
        "owner_boundary": "Coordination fixtures cannot write user-visible next action or controller decisions.",
    },
    {
        "surface_id": "upstream_source_archive",
        "title": "Upstream source archive",
        "classification": "external_source_archive_only",
        "mds_source_surface": "full external MDS source snapshot",
        "mas_target_owner": "Governance",
        "mds_final_role": "external_source_archive_only",
        "cutover_contract": "Full source history stays outside MAS default branch and contributor graph.",
        "owner_boundary": "Archive refs are provenance only and cannot be imported as runtime, WebUI, or quality authority.",
    },
)

def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str:
    return str(value or "").strip()


def _supersede_proofs_for_capability(capability_id: str) -> list[dict[str, Any]]:
    return [copy.deepcopy(proof) for proof in SUPERSEDE_PROOFS_BY_CAPABILITY.get(capability_id, ())]


def _supersede_proof_ids(capabilities: list[Mapping[str, Any]]) -> list[str]:
    proof_ids: list[str] = []
    for capability in capabilities:
        for proof in _list(capability.get("supersede_proofs")):
            if not isinstance(proof, Mapping):
                continue
            proof_id = _text(proof.get("proof_id"))
            if proof_id and proof_id not in proof_ids:
                proof_ids.append(proof_id)
    return proof_ids


def _capability_with_cutover_readiness(capability: Mapping[str, Any]) -> dict[str, Any]:
    capability_projection = dict(capability)
    capability_id = _text(capability.get("capability_id"))
    capability_projection["quality_ready_authority_allowed"] = False
    capability_projection["quality_authority_allowed"] = False
    capability_projection["publication_ready_authority_allowed"] = False
    capability_projection["submission_ready_authority_allowed"] = False
    capability_projection["supersede_proofs"] = _supersede_proofs_for_capability(capability_id)
    parity_proof = capability.get("parity_proof")
    proof = parity_proof if isinstance(parity_proof, Mapping) else {}
    capability_projection["cutover_readiness"] = {
        "cutover_status": MDS_CUTOVER_STATUS,
        "owner_switch_allowed": True,
        "required_gates": list(CUTOVER_REQUIRED_GATES),
        "mas_side_contract": _text(proof.get("mas_contract")),
        "mds_oracle_fixture": _text(proof.get("mds_oracle")),
        "oracle_fixture_ref": _text(capability.get("oracle_fixture_ref")),
        "provenance_ref": _text(capability.get("provenance_ref")),
        "quality_gate_not_relaxed": True,
        "rollback_surface": _text(capability.get("rollback_surface")),
        "old_mds_authority_surface_status": _text(capability.get("old_mds_authority_surface_status")),
        "quality_ready_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "submission_ready_authority_allowed": False,
    }
    return capability_projection


def _build_cutover_capabilities(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    cutover_capabilities: list[dict[str, Any]] = []
    for capability in _list(matrix.get("capabilities")):
        if not isinstance(capability, Mapping):
            continue
        readiness = capability.get("cutover_readiness")
        if isinstance(readiness, Mapping):
            capability_projection = dict(readiness)
        else:
            capability_projection = dict(_capability_with_cutover_readiness(capability)["cutover_readiness"])
        capability_projection["capability_id"] = _text(capability.get("capability_id"))
        capability_projection["title"] = _text(capability.get("title"))
        capability_projection["can_authorize_medical_quality"] = False
        capability_projection["quality_ready_authority_allowed"] = False
        capability_projection["quality_authority_allowed"] = False
        capability_projection["publication_ready_authority_allowed"] = False
        capability_projection["submission_ready_authority_allowed"] = False
        capability_projection["classification"] = _text(capability.get("classification"))
        capability_projection["parity_status"] = _text(capability.get("parity_status")) or "oracle_fixture_defined"
        capability_projection["supersede_proofs"] = _supersede_proofs_for_capability(
            _text(capability.get("capability_id"))
        )
        cutover_capabilities.append(capability_projection)
    return cutover_capabilities


def _oracle_fixture_projection(capability: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "capability_id": _text(capability.get("capability_id")),
        "mas_owner_surface": _text(capability.get("mas_owner_surface")),
        "oracle_fixture_ref": _text(capability.get("oracle_fixture_ref")),
        "parity_status": _text(capability.get("parity_status")),
        "rollback_surface": _text(capability.get("rollback_surface")),
        "provenance_ref": _text(capability.get("provenance_ref")),
        "classification": _text(capability.get("classification")),
        "quality_ready_authority_allowed": False,
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
        "submission_ready_authority_allowed": False,
    }


def _remaining_surface_projection(surface: Mapping[str, Any]) -> dict[str, Any]:
    projection = dict(surface)
    projection["provenance_ref"] = PROVENANCE_REF
    projection["authority_claims"] = []
    projection["imports_upstream_history"] = False
    projection["default_runtime_dependency_allowed"] = False
    projection["quality_authority_allowed"] = False
    projection["publication_ready_authority_allowed"] = False
    projection["required_cutover_gates"] = list(CUTOVER_REQUIRED_GATES)
    return projection


def _remaining_surface_summary(surfaces: list[Mapping[str, Any]]) -> dict[str, int]:
    summary = {"surface_count": len(surfaces)}
    for classification in ALLOWED_CAPABILITY_CLASSIFICATIONS:
        summary[classification] = sum(1 for surface in surfaces if _text(surface.get("classification")) == classification)
    return summary


def build_mds_remaining_surface_inventory() -> dict[str, Any]:
    surfaces = [_remaining_surface_projection(surface) for surface in REMAINING_SURFACES]
    return {
        "surface": "mds_remaining_surface_inventory",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "mds_final_role": MDS_FINAL_ROLE,
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "upstream_history_import_allowed": False,
        "allowed_classifications": list(ALLOWED_CAPABILITY_CLASSIFICATIONS),
        "remaining_surfaces": surfaces,
        "classification_summary": _remaining_surface_summary(surfaces),
    }

def build_mds_capability_parity_matrix() -> dict[str, Any]:
    capabilities = [_capability_with_cutover_readiness(capability) for capability in CAPABILITIES]
    oracle_fixtures = [_oracle_fixture_projection(capability) for capability in capabilities]
    remaining_surface_inventory = build_mds_remaining_surface_inventory()
    behavior_equivalence_matrix = build_mds_behavior_equivalence_matrix()
    return {
        "surface": "mds_capability_parity_matrix",
        "schema_version": SCHEMA_VERSION,
        "mds_role": MDS_FINAL_ROLE,
        "mds_quality_authority": "none",
        "mas_owner": "MedAutoScience",
        "physical_absorb_allowed": MDS_FUNCTIONAL_MONOLITH_STATUS,
        "allowed_capability_classifications": list(ALLOWED_CAPABILITY_CLASSIFICATIONS),
        "capabilities": capabilities,
        "retained_capability_oracle_fixtures": oracle_fixtures,
        "remaining_surface_inventory": remaining_surface_inventory["remaining_surfaces"],
        "behavior_equivalence_inventory": behavior_equivalence_matrix["behavior_surfaces"],
        "capability_ids": [str(capability["capability_id"]) for capability in capabilities],
        "supersede_proof_ids": _supersede_proof_ids(capabilities),
        "parity_summary": {
            "capability_count": len(capabilities),
            "proof_count": sum(1 for capability in capabilities if capability.get("parity_proof")),
            "oracle_fixture_count": len(oracle_fixtures),
            "remaining_surface_count": len(remaining_surface_inventory["remaining_surfaces"]),
            "behavior_surface_count": len(behavior_equivalence_matrix["behavior_surfaces"]),
            "quality_owner": "MedAutoScience",
            "mds_role": MDS_FINAL_ROLE,
            "medical_quality_authority": "blocked_for_mds",
            "fully_equivalent_to_mds_daemon": False,
        },
        "cutover_gates": [
            *CUTOVER_REQUIRED_GATES,
        ],
    }


def build_mds_capability_cutover_gate(proof_bundle: Mapping[str, Any] | None = None) -> dict[str, Any]:
    matrix = build_mds_capability_parity_matrix()
    capabilities = _build_cutover_capabilities(matrix)
    bundle_validation = validate_mds_capability_proof_bundle(proof_bundle, matrix) if proof_bundle is not None else None
    proof_bundle_complete = bool(bundle_validation and bundle_validation["ok"])
    proof_capabilities = _proof_bundle_capabilities_by_id(proof_bundle) if proof_bundle_complete else {}
    for capability in capabilities:
        proof_capability = proof_capabilities.get(str(capability["capability_id"]))
        if proof_capability is not None:
            capability["proof_bundle_status"] = "complete"
            capability["owner_switch_allowed"] = True
            capability["parity_status"] = _text(proof_capability.get("parity_status")) or "passed"
        else:
            capability["proof_bundle_status"] = "landed_from_retained_capability_contract"
            capability["owner_switch_allowed"] = True
            capability["parity_status"] = _text(capability.get("parity_status")) or "mas_superseded_or_fixture_retained"
        capability["cutover_status"] = MDS_CUTOVER_STATUS
    owner_switch_allowed_count = sum(1 for capability in capabilities if capability.get("owner_switch_allowed") is True)
    return {
        "surface": "mds_capability_cutover_gate",
        "schema_version": SCHEMA_VERSION,
        "mds_role": matrix["mds_role"],
        "mds_quality_authority": matrix["mds_quality_authority"],
        "quality_authority_rule": "mds_can_never_authorize_medical_quality",
        "owner_switch_allowed": True,
        "cutover_status": MDS_CUTOVER_STATUS,
        "proof_bundle_status": (
            "complete" if proof_bundle_complete else "landed_from_retained_capability_contract"
        ),
        "required_gates": list(CUTOVER_REQUIRED_GATES),
        "capabilities": capabilities,
        "summary": {
            "capability_count": len(capabilities),
            "owner_switch_allowed_count": owner_switch_allowed_count,
            "blocked_capability_count": 0,
            "medical_quality_authority": "blocked_for_mds",
        },
    }


def validate_mds_capability_parity_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    _validate_capability_parity_header(matrix, issues)
    _append_remaining_inventory_issues(matrix, issues)
    _append_behavior_equivalence_issues(matrix, issues)
    for capability in _list(matrix.get("capabilities")):
        if not isinstance(capability, Mapping):
            issues.append({"code": "invalid_capability"})
            continue
        _validate_capability_parity_capability(capability, issues)
    return {
        "surface": "mds_capability_parity_matrix_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_capability_parity_header(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _text(matrix.get("mds_role")) != MDS_FINAL_ROLE:
        issues.append({"code": "mds_role_not_frozen_archive_or_fixture"})
    if _text(matrix.get("mds_quality_authority")) != "none":
        issues.append({"code": "mds_quality_authority_drift"})
    if _text(matrix.get("mas_owner")) != "MedAutoScience":
        issues.append({"code": "mas_owner_drift"})


def _append_remaining_inventory_issues(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    remaining_inventory_validation = validate_mds_remaining_surface_inventory(
        {
            "surface": "mds_remaining_surface_inventory",
            "schema_version": SCHEMA_VERSION,
            "owner": "MedAutoScience",
            "mds_final_role": MDS_FINAL_ROLE,
            "default_operation_requires_external_mds": False,
            "default_diagnostic_requires_external_mds": False,
            "upstream_history_import_allowed": False,
            "allowed_classifications": list(ALLOWED_CAPABILITY_CLASSIFICATIONS),
            "remaining_surfaces": _list(matrix.get("remaining_surface_inventory")),
        }
    )
    for issue in _list(remaining_inventory_validation.get("issues")):
        if isinstance(issue, Mapping):
            issues.append(dict(issue))


def _append_behavior_equivalence_issues(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    behavior_validation = validate_mds_behavior_equivalence_matrix(
        {
            "surface": "mds_behavior_equivalence_matrix",
            "schema_version": SCHEMA_VERSION,
            "owner": "MedAutoScience",
            "mds_final_role": MDS_FINAL_ROLE,
            "default_operation_requires_external_mds": False,
            "default_diagnostic_requires_external_mds": False,
            "default_supervision_owner": "hermes_gateway_cron",
            "default_tick_interval_seconds": 300,
            "default_tick_max_ticks": 1,
            "mas_default_runtime_is_resident_daemon": False,
            "mds_daemon_was_resident_http_websocket_server": True,
            "completion_claim": "default_independence_not_full_behavior_equivalence",
            "allowed_equivalence_classes": list(ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES),
            "allowed_operator_actions": list(ALLOWED_BEHAVIOR_OPERATOR_ACTIONS),
            "behavior_surfaces": _list(matrix.get("behavior_equivalence_inventory")),
        }
    )
    for issue in _list(behavior_validation.get("issues")):
        if isinstance(issue, Mapping):
            issues.append(dict(issue))


def _validate_capability_parity_capability(capability: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    capability_id = _text(capability.get("capability_id"))
    _validate_capability_authority_fields(capability, capability_id, issues)
    _validate_capability_required_refs(capability, capability_id, issues)
    _validate_capability_parity_proof(capability, capability_id, issues)
    _validate_capability_cutover_readiness(capability, capability_id, issues)


def _validate_capability_authority_fields(
    capability: Mapping[str, Any],
    capability_id: str,
    issues: list[dict[str, Any]],
) -> None:
    if capability.get("can_authorize_medical_quality") is not False:
        issues.append({"code": "mds_quality_authority_drift", "capability_id": capability_id})
    if capability.get("quality_ready_authority_allowed") is not False:
        issues.append({"code": "capability_quality_ready_authority_allowed", "capability_id": capability_id})
    if capability.get("quality_authority_allowed") is not False:
        issues.append({"code": "capability_quality_authority_allowed", "capability_id": capability_id})
    if capability.get("publication_ready_authority_allowed") is not False:
        issues.append({"code": "capability_publication_ready_authority_allowed", "capability_id": capability_id})
    if capability.get("submission_ready_authority_allowed") is not False:
        issues.append({"code": "capability_submission_ready_authority_allowed", "capability_id": capability_id})
    _validate_supersede_proofs(
        capability.get("supersede_proofs"),
        issues,
        issue_prefix="capability",
        capability_id=capability_id,
    )


def _validate_capability_required_refs(
    capability: Mapping[str, Any],
    capability_id: str,
    issues: list[dict[str, Any]],
) -> None:
    if not _text(capability.get("oracle_fixture_ref")):
        issues.append({"code": "capability_missing_oracle_fixture_ref", "capability_id": capability_id})
    if not _text(capability.get("rollback_surface")):
        issues.append({"code": "capability_missing_rollback_surface", "capability_id": capability_id})
    if not _text(capability.get("provenance_ref")):
        issues.append({"code": "capability_missing_provenance_ref", "capability_id": capability_id})
    if not _text(capability.get("required_parity_proof")):
        issues.append({"code": "capability_missing_parity_proof", "capability_id": capability_id})
    if _text(capability.get("classification")) not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
        issues.append(
            {
                "code": "invalid_capability_classification",
                "capability_id": capability_id,
                "classification": _text(capability.get("classification")),
            }
        )


def _validate_capability_parity_proof(
    capability: Mapping[str, Any],
    capability_id: str,
    issues: list[dict[str, Any]],
) -> None:
    parity_proof = capability.get("parity_proof")
    if not isinstance(parity_proof, Mapping):
        issues.append({"code": "capability_missing_parity_proof_detail", "capability_id": capability_id})
        return
    for field in ("proof_kind", "mas_contract", "mds_oracle", "acceptance"):
        if not _text(parity_proof.get(field)):
            issues.append(
                {
                    "code": "capability_incomplete_parity_proof_detail",
                    "capability_id": capability_id,
                    "field": field,
                }
            )


def _validate_capability_cutover_readiness(
    capability: Mapping[str, Any],
    capability_id: str,
    issues: list[dict[str, Any]],
) -> None:
    cutover_readiness = capability.get("cutover_readiness")
    if not isinstance(cutover_readiness, Mapping):
        issues.append({"code": "capability_missing_cutover_readiness", "capability_id": capability_id})
        return
    if _text(cutover_readiness.get("cutover_status")) != MDS_CUTOVER_STATUS:
        issues.append({"code": "capability_cutover_status_drift", "capability_id": capability_id})
    if cutover_readiness.get("owner_switch_allowed") is not True:
        issues.append({"code": "capability_owner_switch_not_landed", "capability_id": capability_id})
    if list(cutover_readiness.get("required_gates") or []) != list(CUTOVER_REQUIRED_GATES):
        issues.append({"code": "capability_required_cutover_gates_drift", "capability_id": capability_id})
    _validate_capability_cutover_refs(cutover_readiness, capability_id, issues)
    if cutover_readiness.get("quality_gate_not_relaxed") is not True:
        issues.append({"code": "quality_gate_relaxation_drift", "capability_id": capability_id})
    if _text(cutover_readiness.get("old_mds_authority_surface_status")) not in {"marked_oracle", "retired"}:
        issues.append({"code": "old_mds_authority_surface_not_retired_or_oracle", "capability_id": capability_id})


def _validate_capability_cutover_refs(
    cutover_readiness: Mapping[str, Any],
    capability_id: str,
    issues: list[dict[str, Any]],
) -> None:
    for field in ("mas_side_contract", "mds_oracle_fixture", "rollback_surface"):
        if not _text(cutover_readiness.get(field)):
            issues.append(
                {
                    "code": "capability_incomplete_cutover_readiness",
                    "capability_id": capability_id,
                    "field": field,
                }
            )


def validate_mds_remaining_surface_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(inventory.get("surface")) != "mds_remaining_surface_inventory":
        issues.append({"code": "wrong_surface"})
    if _text(inventory.get("owner")) != "MedAutoScience":
        issues.append({"code": "owner_drift"})
    if _text(inventory.get("mds_final_role")) != MDS_FINAL_ROLE:
        issues.append({"code": "mds_final_role_drift"})
    if inventory.get("default_operation_requires_external_mds") is not False:
        issues.append({"code": "default_operation_requires_external_mds"})
    if inventory.get("default_diagnostic_requires_external_mds") is not False:
        issues.append({"code": "default_diagnostic_requires_external_mds"})
    if inventory.get("upstream_history_import_allowed") is not False:
        issues.append({"code": "upstream_history_import_allowed"})
    if list(inventory.get("allowed_classifications") or []) != list(ALLOWED_CAPABILITY_CLASSIFICATIONS):
        issues.append({"code": "allowed_classifications_drift"})
    for surface in _list(inventory.get("remaining_surfaces")):
        if not isinstance(surface, Mapping):
            issues.append({"code": "invalid_remaining_surface"})
            continue
        _validate_remaining_surface(surface, issues)
    return {
        "surface": "mds_remaining_surface_inventory_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_remaining_surface(surface: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    surface_id = _text(surface.get("surface_id"))
    classification = _text(surface.get("classification"))
    if not surface_id:
        issues.append({"code": "remaining_surface_missing_id"})
    if classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
        issues.append(
            {
                "code": "invalid_remaining_surface_classification",
                "surface_id": surface_id,
                "classification": classification,
            }
        )
    for field in ("mas_target_owner", "mds_final_role", "cutover_contract", "owner_boundary", "provenance_ref"):
        if not _text(surface.get(field)):
            issues.append({"code": f"remaining_surface_missing_{field}", "surface_id": surface_id})
    if _strings(surface.get("authority_claims")):
        issues.append(
            {
                "code": "remaining_surface_claims_mas_authority",
                "surface_id": surface_id,
                "authority_claims": list(_strings(surface.get("authority_claims"))),
            }
        )
    if surface.get("imports_upstream_history") is not False:
        issues.append({"code": "remaining_surface_imports_upstream_history", "surface_id": surface_id})
    if surface.get("default_runtime_dependency_allowed") is not False:
        issues.append({"code": "remaining_surface_default_runtime_dependency_allowed", "surface_id": surface_id})
    if surface.get("quality_authority_allowed") is not False:
        issues.append({"code": "remaining_surface_quality_authority_allowed", "surface_id": surface_id})
    if surface.get("publication_ready_authority_allowed") is not False:
        issues.append({"code": "remaining_surface_publication_ready_authority_allowed", "surface_id": surface_id})

def validate_mds_capability_proof_bundle(
    proof_bundle: Mapping[str, Any] | None,
    matrix: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not isinstance(proof_bundle, Mapping):
        return {
            "surface": "mds_capability_proof_bundle_validation",
            "schema_version": SCHEMA_VERSION,
            "ok": False,
            "issue_count": 1,
            "issues": [{"code": "missing_proof_bundle"}],
        }
    if _text(proof_bundle.get("surface")) != "mds_capability_parity_proof_bundle":
        issues.append({"code": "wrong_surface"})
    expected_ids = set((matrix or build_mds_capability_parity_matrix()).get("capability_ids") or [])
    observed_ids: set[str] = set()
    for capability in _list(proof_bundle.get("capabilities")):
        if not isinstance(capability, Mapping):
            issues.append({"code": "invalid_proof_bundle_capability"})
            continue
        observed_ids.add(_text(capability.get("capability_id")))
        _validate_proof_bundle_capability(capability, issues)
    _append_missing_proof_bundle_capabilities(expected_ids, observed_ids, issues)
    return {
        "surface": "mds_capability_proof_bundle_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_proof_bundle_capability(capability: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    capability_id = _text(capability.get("capability_id"))
    if not _text(capability.get("oracle_fixture_ref")):
        issues.append({"code": "proof_bundle_missing_oracle_fixture_ref", "capability_id": capability_id})
    if capability.get("quality_authority_allowed") is not False:
        issues.append({"code": "proof_bundle_quality_authority_allowed", "capability_id": capability_id})
    if capability.get("publication_ready_authority_allowed") is not False:
        issues.append({"code": "proof_bundle_publication_ready_authority_allowed", "capability_id": capability_id})
    if capability.get("submission_ready_authority_allowed") is not False:
        issues.append({"code": "proof_bundle_submission_ready_authority_allowed", "capability_id": capability_id})
    _validate_supersede_proofs(
        capability.get("supersede_proofs"),
        issues,
        issue_prefix="proof_bundle",
        capability_id=capability_id,
    )
    for field in ("rollback_surface", "provenance_ref", "proof_ref"):
        if not _text(capability.get(field)):
            issues.append({"code": f"proof_bundle_missing_{field}", "capability_id": capability_id})
    if _text(capability.get("parity_status")) != "passed":
        issues.append({"code": "proof_bundle_parity_not_passed", "capability_id": capability_id})


def _append_missing_proof_bundle_capabilities(
    expected_ids: set[str],
    observed_ids: set[str],
    issues: list[dict[str, Any]],
) -> None:
    for capability_id in sorted(expected_ids - observed_ids):
        issues.append({"code": "proof_bundle_missing_capability", "capability_id": capability_id})


def _validate_supersede_proofs(
    proofs: object,
    issues: list[dict[str, Any]],
    *,
    issue_prefix: str,
    capability_id: str,
) -> None:
    proof_list = _list(proofs)
    if not proof_list and capability_id != "runtime_execution":
        issues.append({"code": f"{issue_prefix}_missing_supersede_proof", "capability_id": capability_id})
        return
    for proof in proof_list:
        if not isinstance(proof, Mapping):
            issues.append({"code": f"{issue_prefix}_invalid_supersede_proof", "capability_id": capability_id})
            continue
        if proof.get("mas_owned") is not True:
            issues.append({"code": f"{issue_prefix}_supersede_proof_owner_drift", "capability_id": capability_id})
        if _text(proof.get("mds_mechanical_signal_role")) != "evidence_only":
            issues.append({"code": f"{issue_prefix}_supersede_proof_signal_role_drift", "capability_id": capability_id})
        if not _text(proof.get("mechanical_signal_can_only")).startswith("request_"):
            issues.append({"code": f"{issue_prefix}_supersede_proof_signal_role_drift", "capability_id": capability_id})
        for field in (
            "quality_ready_authorized",
            "publication_ready_authorized",
            "submission_ready_authorized",
        ):
            if proof.get(field) is not False:
                issues.append(
                    {
                        "code": f"{issue_prefix}_supersede_proof_ready_authority_drift",
                        "capability_id": capability_id,
                        "field": field,
                    }
                )


def _proof_bundle_capabilities_by_id(proof_bundle: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(proof_bundle, Mapping):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for capability in _list(proof_bundle.get("capabilities")):
        if isinstance(capability, Mapping):
            result[_text(capability.get("capability_id"))] = capability
    return result
