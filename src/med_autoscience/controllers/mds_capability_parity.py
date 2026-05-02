from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1

CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "runtime_execution",
        "title": "Runtime execution",
        "mds_authority_role": "backend",
        "mas_target_owner": "Runtime OS",
        "required_parity_proof": "runtime execution replay and recovery regression suite",
        "parity_proof": {
            "proof_kind": "execution_replay",
            "mas_contract": "study_runtime_status/runtime_watch own runtime decisions and recovery visibility",
            "mds_oracle": "MDS quest execution traces can be replayed only as backend behavior fixtures",
            "acceptance": "MAS recovery decisions match or intentionally supersede replayed MDS behavior",
        },
        "can_authorize_medical_quality": False,
    },
    {
        "capability_id": "artifact_inventory",
        "title": "Artifact inventory",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Artifact OS",
        "required_parity_proof": "artifact inventory projection parity fixtures",
        "parity_proof": {
            "proof_kind": "artifact_projection",
            "mas_contract": "MAS artifact inventory is the consumer-facing projection owner",
            "mds_oracle": "MDS artifact layout is a fixture for legacy inventory compatibility",
            "acceptance": "MAS inventory preserves discoverability without granting MDS delivery authority",
        },
        "can_authorize_medical_quality": False,
    },
    {
        "capability_id": "paper_contract_health",
        "title": "Paper contract health",
        "mds_authority_role": "mechanical_oracle",
        "mas_target_owner": "Quality OS",
        "required_parity_proof": "backend preflight parity without quality-ready authority",
        "parity_proof": {
            "proof_kind": "contract_preflight",
            "mas_contract": "publication gate and controller decisions own paper readiness",
            "mds_oracle": "MDS contract checks are mechanical preflight observations",
            "acceptance": "MDS health signals never promote a paper to medical-quality ready",
        },
        "can_authorize_medical_quality": False,
    },
    {
        "capability_id": "manuscript_coverage",
        "title": "Manuscript coverage",
        "mds_authority_role": "mechanical_oracle",
        "mas_target_owner": "Quality OS",
        "required_parity_proof": "mechanical coverage fixtures with AI preflight required",
        "parity_proof": {
            "proof_kind": "coverage_fixture",
            "mas_contract": "AI review and publication eval own medical manuscript quality",
            "mds_oracle": "MDS coverage counts are mechanical completeness signals",
            "acceptance": "Coverage parity can request review but cannot authorize final quality",
        },
        "can_authorize_medical_quality": False,
    },
    {
        "capability_id": "prompt_stage_discipline",
        "title": "Prompt stage discipline",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Quality OS",
        "required_parity_proof": "stage prompt contract parity and prompt-only gate audit",
        "parity_proof": {
            "proof_kind": "stage_contract",
            "mas_contract": "MAS controller stages own allowed prompt transitions",
            "mds_oracle": "MDS stage prompts provide behavior examples and violation fixtures",
            "acceptance": "MAS stage discipline remains explicit and auditable after parity import",
        },
        "can_authorize_medical_quality": False,
    },
    {
        "capability_id": "memory_and_lesson_store",
        "title": "Memory and lesson store",
        "mds_authority_role": "behavior_oracle",
        "mas_target_owner": "Evaluation OS",
        "required_parity_proof": "lesson intake and incident learning parity fixtures",
        "parity_proof": {
            "proof_kind": "lesson_store_projection",
            "mas_contract": "MAS incident learning owns reusable lessons and operator-visible memory",
            "mds_oracle": "MDS lessons are intake material for parity and regression cases",
            "acceptance": "Lessons are imported as evidence, not as autonomous quality decisions",
        },
        "can_authorize_medical_quality": False,
    },
)


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def build_mds_capability_parity_matrix() -> dict[str, Any]:
    capabilities = [dict(capability) for capability in CAPABILITIES]
    return {
        "surface": "mds_capability_parity_matrix",
        "schema_version": SCHEMA_VERSION,
        "mds_role": "replaceable_backend_oracle",
        "mds_quality_authority": "none",
        "mas_owner": "MedAutoScience",
        "physical_absorb_allowed": "after_parity_and_owner_cutover_only",
        "capabilities": capabilities,
        "capability_ids": [str(capability["capability_id"]) for capability in capabilities],
        "parity_summary": {
            "capability_count": len(capabilities),
            "proof_count": sum(1 for capability in capabilities if capability.get("parity_proof")),
            "quality_owner": "MedAutoScience",
            "mds_role": "replaceable_backend_oracle",
            "medical_quality_authority": "blocked_for_mds",
        },
        "cutover_gates": [
            "mas_consumer_contract_exists",
            "mds_behavior_oracle_fixture_exists",
            "quality_gate_not_relaxed",
            "rollback_surface_exists",
            "old_mds_authority_surface_retired_or_marked_oracle",
        ],
    }


def validate_mds_capability_parity_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(matrix.get("mds_role")) != "replaceable_backend_oracle":
        issues.append({"code": "mds_role_not_backend_oracle"})
    if _text(matrix.get("mds_quality_authority")) != "none":
        issues.append({"code": "mds_quality_authority_drift"})
    if _text(matrix.get("mas_owner")) != "MedAutoScience":
        issues.append({"code": "mas_owner_drift"})
    for capability in _list(matrix.get("capabilities")):
        if not isinstance(capability, Mapping):
            issues.append({"code": "invalid_capability"})
            continue
        capability_id = _text(capability.get("capability_id"))
        if capability.get("can_authorize_medical_quality") is not False:
            issues.append({"code": "mds_quality_authority_drift", "capability_id": capability_id})
        if not _text(capability.get("required_parity_proof")):
            issues.append({"code": "capability_missing_parity_proof", "capability_id": capability_id})
        parity_proof = capability.get("parity_proof")
        if not isinstance(parity_proof, Mapping):
            issues.append({"code": "capability_missing_parity_proof_detail", "capability_id": capability_id})
            continue
        for field in ("proof_kind", "mas_contract", "mds_oracle", "acceptance"):
            if not _text(parity_proof.get(field)):
                issues.append(
                    {
                        "code": "capability_incomplete_parity_proof_detail",
                        "capability_id": capability_id,
                        "field": field,
                    }
                )
    return {
        "surface": "mds_capability_parity_matrix_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
