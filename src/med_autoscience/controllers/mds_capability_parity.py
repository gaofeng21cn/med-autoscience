from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1
CUTOVER_REQUIRED_GATES: tuple[str, ...] = (
    "mas_side_contract_exists",
    "mds_oracle_fixture_exists",
    "quality_gate_not_relaxed",
    "rollback_surface_exists",
    "old_mds_authority_surface_retired_or_marked_oracle",
)
PROVENANCE_REF = "docs/references/med-deepscientist/source_provenance.json"

CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "runtime_execution",
        "title": "Runtime execution",
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


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _capability_with_cutover_readiness(capability: Mapping[str, Any]) -> dict[str, Any]:
    capability_projection = dict(capability)
    parity_proof = capability.get("parity_proof")
    proof = parity_proof if isinstance(parity_proof, Mapping) else {}
    capability_projection["cutover_readiness"] = {
        "cutover_status": "blocked_pending_cutover_proofs",
        "owner_switch_allowed": False,
        "required_gates": list(CUTOVER_REQUIRED_GATES),
        "mas_side_contract": _text(proof.get("mas_contract")),
        "mds_oracle_fixture": _text(proof.get("mds_oracle")),
        "oracle_fixture_ref": _text(capability.get("oracle_fixture_ref")),
        "provenance_ref": _text(capability.get("provenance_ref")),
        "quality_gate_not_relaxed": True,
        "rollback_surface": _text(capability.get("rollback_surface")),
        "old_mds_authority_surface_status": _text(capability.get("old_mds_authority_surface_status")),
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
        capability_projection["quality_authority_allowed"] = False
        capability_projection["publication_ready_authority_allowed"] = False
        capability_projection["parity_status"] = _text(capability.get("parity_status")) or "oracle_fixture_defined"
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
        "quality_authority_allowed": False,
        "publication_ready_authority_allowed": False,
    }


def build_mds_capability_parity_matrix() -> dict[str, Any]:
    capabilities = [_capability_with_cutover_readiness(capability) for capability in CAPABILITIES]
    oracle_fixtures = [_oracle_fixture_projection(capability) for capability in capabilities]
    return {
        "surface": "mds_capability_parity_matrix",
        "schema_version": SCHEMA_VERSION,
        "mds_role": "replaceable_backend_oracle",
        "mds_quality_authority": "none",
        "mas_owner": "MedAutoScience",
        "physical_absorb_allowed": "after_parity_and_owner_cutover_only",
        "capabilities": capabilities,
        "retained_capability_oracle_fixtures": oracle_fixtures,
        "capability_ids": [str(capability["capability_id"]) for capability in capabilities],
        "parity_summary": {
            "capability_count": len(capabilities),
            "proof_count": sum(1 for capability in capabilities if capability.get("parity_proof")),
            "oracle_fixture_count": len(oracle_fixtures),
            "quality_owner": "MedAutoScience",
            "mds_role": "replaceable_backend_oracle",
            "medical_quality_authority": "blocked_for_mds",
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
            capability["proof_bundle_status"] = "missing"
            capability["owner_switch_allowed"] = False
    owner_switch_allowed_count = sum(1 for capability in capabilities if capability.get("owner_switch_allowed") is True)
    return {
        "surface": "mds_capability_cutover_gate",
        "schema_version": SCHEMA_VERSION,
        "mds_role": matrix["mds_role"],
        "mds_quality_authority": matrix["mds_quality_authority"],
        "quality_authority_rule": "mds_can_never_authorize_medical_quality",
        "owner_switch_allowed": proof_bundle_complete,
        "cutover_status": "blocked_pending_capability_proofs",
        "proof_bundle_status": "complete" if proof_bundle_complete else "missing",
        "required_gates": list(CUTOVER_REQUIRED_GATES),
        "capabilities": capabilities,
        "summary": {
            "capability_count": len(capabilities),
            "owner_switch_allowed_count": owner_switch_allowed_count,
            "blocked_capability_count": len(capabilities) - owner_switch_allowed_count,
            "medical_quality_authority": "blocked_for_mds",
        },
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
        if capability.get("quality_authority_allowed") is not False:
            issues.append({"code": "capability_quality_authority_allowed", "capability_id": capability_id})
        if capability.get("publication_ready_authority_allowed") is not False:
            issues.append({"code": "capability_publication_ready_authority_allowed", "capability_id": capability_id})
        if not _text(capability.get("oracle_fixture_ref")):
            issues.append({"code": "capability_missing_oracle_fixture_ref", "capability_id": capability_id})
        if not _text(capability.get("rollback_surface")):
            issues.append({"code": "capability_missing_rollback_surface", "capability_id": capability_id})
        if not _text(capability.get("provenance_ref")):
            issues.append({"code": "capability_missing_provenance_ref", "capability_id": capability_id})
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
        cutover_readiness = capability.get("cutover_readiness")
        if not isinstance(cutover_readiness, Mapping):
            issues.append({"code": "capability_missing_cutover_readiness", "capability_id": capability_id})
            continue
        if _text(cutover_readiness.get("cutover_status")) != "blocked_pending_cutover_proofs":
            issues.append({"code": "capability_cutover_status_drift", "capability_id": capability_id})
        if cutover_readiness.get("owner_switch_allowed") is not False:
            issues.append({"code": "capability_owner_switch_unblocked", "capability_id": capability_id})
        if list(cutover_readiness.get("required_gates") or []) != list(CUTOVER_REQUIRED_GATES):
            issues.append({"code": "capability_required_cutover_gates_drift", "capability_id": capability_id})
        for field in ("mas_side_contract", "mds_oracle_fixture", "rollback_surface"):
            if not _text(cutover_readiness.get(field)):
                issues.append(
                    {
                        "code": "capability_incomplete_cutover_readiness",
                        "capability_id": capability_id,
                        "field": field,
                    }
                )
        if cutover_readiness.get("quality_gate_not_relaxed") is not True:
            issues.append({"code": "quality_gate_relaxation_drift", "capability_id": capability_id})
        if _text(cutover_readiness.get("old_mds_authority_surface_status")) not in {"marked_oracle", "retired"}:
            issues.append({"code": "old_mds_authority_surface_not_retired_or_oracle", "capability_id": capability_id})
    return {
        "surface": "mds_capability_parity_matrix_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


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
        capability_id = _text(capability.get("capability_id"))
        observed_ids.add(capability_id)
        if not _text(capability.get("oracle_fixture_ref")):
            issues.append({"code": "proof_bundle_missing_oracle_fixture_ref", "capability_id": capability_id})
        if capability.get("quality_authority_allowed") is not False:
            issues.append({"code": "proof_bundle_quality_authority_allowed", "capability_id": capability_id})
        if capability.get("publication_ready_authority_allowed") is not False:
            issues.append({"code": "proof_bundle_publication_ready_authority_allowed", "capability_id": capability_id})
        if not _text(capability.get("rollback_surface")):
            issues.append({"code": "proof_bundle_missing_rollback_surface", "capability_id": capability_id})
        if not _text(capability.get("provenance_ref")):
            issues.append({"code": "proof_bundle_missing_provenance_ref", "capability_id": capability_id})
        if not _text(capability.get("proof_ref")):
            issues.append({"code": "proof_bundle_missing_proof_ref", "capability_id": capability_id})
        if _text(capability.get("parity_status")) != "passed":
            issues.append({"code": "proof_bundle_parity_not_passed", "capability_id": capability_id})
    missing_ids = sorted(expected_ids - observed_ids)
    for capability_id in missing_ids:
        issues.append({"code": "proof_bundle_missing_capability", "capability_id": capability_id})
    return {
        "surface": "mds_capability_proof_bundle_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _proof_bundle_capabilities_by_id(proof_bundle: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(proof_bundle, Mapping):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for capability in _list(proof_bundle.get("capabilities")):
        if isinstance(capability, Mapping):
            result[_text(capability.get("capability_id"))] = capability
    return result
