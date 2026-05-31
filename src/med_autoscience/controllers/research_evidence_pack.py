from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


SURFACE_KIND = "mas_research_evidence_pack_summary"
VERSION = "mas-research-evidence-pack-summary.v1"
SCHEMA_VALIDATION_VERSION = "mas-research-evidence-pack-schema-validation.v1"


REQUIRED_EVIDENCE_FAMILIES = (
    "run_manifest_ref",
    "negative_failed_path_refs",
    "decision_trace_refs",
    "artifact_lineage_refs",
    "reproducibility_refs",
    "owner_receipt_or_typed_blocker_refs",
)


def build_research_evidence_pack_summary(
    *,
    domain_id: str,
    task_kind: str,
    study_id: str | None = None,
    stage_id: str | None = None,
    input_refs: Sequence[str | Mapping[str, Any]] = (),
    output_refs: Sequence[str | Mapping[str, Any]] = (),
    checksum_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    typed_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
    code_refs: Sequence[str | Mapping[str, Any]] = (),
    source_data_version_refs: Sequence[str | Mapping[str, Any]] = (),
    software_environment_refs: Sequence[str | Mapping[str, Any]] = (),
    parameter_seed_refs: Sequence[str | Mapping[str, Any]] = (),
    claim_impact_refs: Sequence[str | Mapping[str, Any]] = (),
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]] = (),
    decision_trace_refs: Sequence[str | Mapping[str, Any]] = (),
    artifact_lineage_refs: Sequence[str | Mapping[str, Any]] = (),
    reproducibility_refs: Sequence[str | Mapping[str, Any]] = (),
    paper_delta_refs: Sequence[str | Mapping[str, Any]] = (),
    deliverable_delta_refs: Sequence[str | Mapping[str, Any]] = (),
    platform_repair_refs: Sequence[str | Mapping[str, Any]] = (),
    route_switch_refs: Sequence[str | Mapping[str, Any]] = (),
    next_owner_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
    forbidden_write_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_route_match_status: str | None = None,
    owner_route_mismatch_refs: Sequence[str | Mapping[str, Any]] = (),
    body_included: bool = False,
    paper_body_included: bool = False,
) -> dict[str, Any]:
    normalized_domain = _text(domain_id) or "medautoscience"
    normalized_task = _text(task_kind) or "domain_owner"
    normalized_study = _text(study_id)
    normalized_stage = _text(stage_id)
    task_ref = _ref_token(normalized_task)
    scope_ref = _ref_token(normalized_study or normalized_stage or "workspace")
    ref_prefix = f"mas-research-evidence-pack:{normalized_domain}:{task_ref}:{scope_ref}"
    normalized_code_refs = _unique_refs(code_refs)
    normalized_source_data_version_refs = _unique_refs(source_data_version_refs)
    normalized_software_environment_refs = _unique_refs(software_environment_refs)
    normalized_parameter_seed_refs = _unique_refs(parameter_seed_refs)
    normalized_input_refs = _unique_refs(input_refs)
    normalized_output_refs = _unique_refs(output_refs)
    normalized_checksum_refs = _unique_refs(checksum_refs)
    normalized_claim_impact_refs = _unique_refs(claim_impact_refs)
    normalized_negative_failed_path_refs = _unique_refs(negative_failed_path_refs)
    normalized_decision_trace_refs = _unique_refs(decision_trace_refs)
    normalized_artifact_lineage_refs = _unique_refs(artifact_lineage_refs)
    normalized_reproducibility_refs = _unique_refs(reproducibility_refs)
    normalized_owner_receipt_refs = _unique_refs(owner_receipt_refs)
    normalized_typed_blocker_refs = _unique_refs(typed_blocker_refs)
    normalized_deliverable_delta_refs = _unique_refs([*paper_delta_refs, *deliverable_delta_refs])
    normalized_platform_repair_refs = _unique_refs(platform_repair_refs)
    normalized_route_switch_refs = _unique_refs(route_switch_refs)
    normalized_next_owner_blocker_refs = _unique_refs(next_owner_blocker_refs)
    normalized_forbidden_write_refs = _unique_refs(forbidden_write_refs)
    normalized_owner_route_match_status = _text(owner_route_match_status)
    normalized_owner_route_mismatch_refs = _unique_refs(owner_route_mismatch_refs)
    validation = schema_compatible_validation_summary(
        run_manifest_ref=ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-research-run-manifest:",
            1,
        ),
        negative_failed_path_refs=normalized_negative_failed_path_refs,
        decision_trace_refs=normalized_decision_trace_refs,
        artifact_lineage_refs=normalized_artifact_lineage_refs,
        reproducibility_refs=normalized_reproducibility_refs,
        owner_receipt_refs=normalized_owner_receipt_refs,
        typed_blocker_refs=normalized_typed_blocker_refs,
        forbidden_write_refs=normalized_forbidden_write_refs,
        owner_route_match_status=normalized_owner_route_match_status,
        owner_route_mismatch_refs=normalized_owner_route_mismatch_refs,
        body_included=body_included,
        paper_body_included=paper_body_included,
    )
    missing_reproducibility_refs = _missing_reproducibility_refs(
        code_refs=normalized_code_refs,
        source_data_version_refs=normalized_source_data_version_refs,
        software_environment_refs=normalized_software_environment_refs,
        parameter_seed_refs=normalized_parameter_seed_refs,
    )
    progress_delta_summary = {
        "surface_kind": "mas_research_pack_progress_summary",
        "body_included": False,
        "paper_body_included": False,
        "deliverable_progress_delta": {
            "count": len(normalized_deliverable_delta_refs),
            "refs": normalized_deliverable_delta_refs,
        },
        "paper_progress_delta": {
            "count": len(normalized_deliverable_delta_refs),
            "refs": normalized_deliverable_delta_refs,
        },
        "platform_repair_delta": {
            "count": len(normalized_platform_repair_refs),
            "refs": normalized_platform_repair_refs,
            "counts_as_paper_progress": False,
        },
        "negative_result_count": len(normalized_negative_failed_path_refs),
        "negative_failed_path_refs": normalized_negative_failed_path_refs,
        "route_switch_count": len(normalized_route_switch_refs),
        "route_switch_refs": normalized_route_switch_refs,
        "missing_reproducibility_refs": missing_reproducibility_refs,
        "single_next_owner_blocker": _single_next_owner_blocker(
            typed_blocker_refs=normalized_typed_blocker_refs,
            next_owner_blocker_refs=normalized_next_owner_blocker_refs,
        ),
        "authority_boundary": {
            "summary_only": True,
            "body_free": True,
            "is_route_authority": False,
            "can_authorize_route_switch": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_publication_readiness": False,
            "platform_repair_counts_as_paper_progress": False,
        },
    }
    failed_path_consumption = failed_path_consumption_summary(
        domain_id=normalized_domain,
        task_kind=normalized_task,
        study_id=normalized_study,
        stage_id=normalized_stage,
        negative_failed_path_refs=normalized_negative_failed_path_refs,
        decision_trace_refs=normalized_decision_trace_refs,
        route_switch_refs=normalized_route_switch_refs,
        owner_receipt_refs=normalized_owner_receipt_refs,
        typed_blocker_refs=normalized_typed_blocker_refs,
    )
    summary = {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "domain_id": normalized_domain,
        "study_id": normalized_study,
        "stage_id": normalized_stage,
        "task_kind": normalized_task,
        "pack_ref": ref_prefix,
        "run_manifest_ref": ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-research-run-manifest:",
            1,
        ),
        "negative_failed_path_ledger_ref": ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-negative-failed-path-ledger:",
            1,
        ),
        "decision_trace_ref": ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-decision-trace:",
            1,
        ),
        "artifact_lineage_graph_ref": ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-artifact-lineage-graph:",
            1,
        ),
        "reproducibility_bundle_ref": ref_prefix.replace(
            "mas-research-evidence-pack:",
            "mas-reproducibility-bundle:",
            1,
        ),
        "code_refs": normalized_code_refs,
        "source_data_version_refs": normalized_source_data_version_refs,
        "software_environment_refs": normalized_software_environment_refs,
        "parameter_seed_refs": normalized_parameter_seed_refs,
        "input_refs": normalized_input_refs,
        "output_refs": normalized_output_refs,
        "checksum_refs": normalized_checksum_refs,
        "claim_impact_refs": normalized_claim_impact_refs,
        "negative_failed_path_refs": normalized_negative_failed_path_refs,
        "decision_trace_refs": normalized_decision_trace_refs,
        "artifact_lineage_refs": normalized_artifact_lineage_refs,
        "reproducibility_refs": normalized_reproducibility_refs,
        "typed_blocker_refs": normalized_typed_blocker_refs,
        "owner_receipt_refs": normalized_owner_receipt_refs,
        "schema_validation": validation,
        "ref_family_status": validation["ref_family_status"],
        "failed_path_consumption": failed_path_consumption,
        "missing_required_evidence_families": validation["missing_required_evidence_families"],
        "fail_closed_required": bool(validation["fail_closed_reasons"]),
        "progress_summary": progress_delta_summary,
        "authority_boundary": {
            "owner": "med-autoscience",
            "opl_records_refs_only": True,
            "can_read_domain_body": False,
            "can_accept_or_reject_owner_receipt": False,
            "can_sign_domain_receipt": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_publication_readiness": False,
            "domain_ready_claimed": False,
        },
    }
    return summary


def failed_path_consumption_summary(
    *,
    domain_id: str,
    task_kind: str,
    study_id: str | None = None,
    stage_id: str | None = None,
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]] = (),
    decision_trace_refs: Sequence[str | Mapping[str, Any]] = (),
    route_switch_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    typed_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
) -> dict[str, Any]:
    normalized_domain = _text(domain_id) or "medautoscience"
    normalized_task = _text(task_kind) or "domain_owner"
    normalized_scope = _text(study_id) or _text(stage_id) or "workspace"
    failed_refs = _unique_refs(negative_failed_path_refs)
    decision_refs = _unique_refs(decision_trace_refs)
    switch_refs = _unique_refs(route_switch_refs)
    result_refs = _unique_refs([*owner_receipt_refs, *typed_blocker_refs])
    consumption_evidence_refs = _unique_refs([*decision_refs, *switch_refs, *result_refs])
    consumed = bool(failed_refs and consumption_evidence_refs)
    status = (
        "consumed"
        if consumed
        else "recorded_not_consumed"
        if failed_refs
        else "no_failed_path_refs"
    )
    consumption_key = ":".join(
        [
            "mas-failed-path-consumption",
            _ref_token(normalized_domain),
            _ref_token(normalized_task),
            _ref_token(normalized_scope),
            _ref_token("|".join(failed_refs) or "none"),
        ]
    )
    return {
        "surface_kind": "mas_failed_path_consumption_summary",
        "version": "mas-failed-path-consumption-summary.v1",
        "status": status,
        "consumption_key": consumption_key,
        "negative_failed_path_refs": failed_refs,
        "decision_trace_refs": decision_refs,
        "route_switch_refs": switch_refs,
        "owner_result_refs": result_refs,
        "consumption_evidence_refs": consumption_evidence_refs,
        "duplicate_invalid_attempt_suppression": {
            "enabled": consumed,
            "suppression_basis": "negative_failed_path_refs",
            "same_failed_path_refs_should_not_spawn_same_work_unit": consumed,
            "requires_consumption_evidence": True,
            "requires_new_decision_trace_or_route_switch_ref_for_redrive": consumed,
            "new_attempt_allowed_when_new_decision_trace_or_route_switch_ref": bool(
                failed_refs and (decision_refs or switch_refs)
            ),
            "negative_refs_without_consumption_evidence_are_audit_only": bool(
                failed_refs and not consumed
            ),
        },
        "authority_boundary": {
            "summary_only": True,
            "body_free": True,
            "is_route_authority": False,
            "can_block_owner_route": False,
            "can_authorize_route_switch": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_publication_readiness": False,
        },
    }


def schema_compatible_validation_summary(
    *,
    run_manifest_ref: str | None,
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]] = (),
    decision_trace_refs: Sequence[str | Mapping[str, Any]] = (),
    artifact_lineage_refs: Sequence[str | Mapping[str, Any]] = (),
    reproducibility_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    typed_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
    forbidden_write_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_route_match_status: str | None = None,
    owner_route_mismatch_refs: Sequence[str | Mapping[str, Any]] = (),
    body_included: bool = False,
    paper_body_included: bool = False,
) -> dict[str, Any]:
    normalized = _validation_ref_sets(
        run_manifest_ref=run_manifest_ref,
        negative_failed_path_refs=negative_failed_path_refs,
        decision_trace_refs=decision_trace_refs,
        artifact_lineage_refs=artifact_lineage_refs,
        reproducibility_refs=reproducibility_refs,
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
    )
    missing = missing_required_evidence_families(
        run_manifest_ref=run_manifest_ref,
        negative_failed_path_refs=negative_failed_path_refs,
        decision_trace_refs=decision_trace_refs,
        artifact_lineage_refs=artifact_lineage_refs,
        reproducibility_refs=reproducibility_refs,
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
    )
    placeholder_ref_map = _placeholder_ref_map(normalized)
    placeholder_refs = [
        ref
        for refs in placeholder_ref_map.values()
        for ref in refs
    ]
    normalized_forbidden_write_refs = _unique_refs(forbidden_write_refs)
    owner_route_status = _text(owner_route_match_status)
    normalized_owner_route_mismatch_refs = _unique_refs(owner_route_mismatch_refs)
    owner_route_mismatch = bool(normalized_owner_route_mismatch_refs) or owner_route_status in {
        "mismatch",
        "owner_route_mismatch",
        "identity_mismatch",
        "conflict",
    }
    non_body_free_payload = bool(body_included or paper_body_included)
    fail_closed_reasons = []
    if missing:
        fail_closed_reasons.append("missing_required_refs")
    if placeholder_refs:
        fail_closed_reasons.append("placeholder_refs")
    if normalized_forbidden_write_refs:
        fail_closed_reasons.append("forbidden_write_refs")
    if owner_route_mismatch:
        fail_closed_reasons.append("owner_route_mismatch")
    if non_body_free_payload:
        fail_closed_reasons.append("non_body_free_payload")
    return {
        "surface_kind": "mas_research_evidence_pack_schema_validation",
        "version": SCHEMA_VALIDATION_VERSION,
        "status": _validation_status(
            missing_required_families=missing,
            fail_closed_reasons=fail_closed_reasons,
        ),
        "opl_schema_family": "research_evidence_pack.v1",
        "required_evidence_families": list(REQUIRED_EVIDENCE_FAMILIES),
        "ref_family_status": _ref_family_status(
            normalized_refs=normalized,
            missing_required_families=missing,
            typed_blocker_refs=normalized["owner_receipt_or_typed_blocker_refs"]["typed_blocker_refs"],
        ),
        "missing_required_evidence_families": missing,
        "placeholder_ref_families": list(placeholder_ref_map),
        "placeholder_refs": placeholder_refs,
        "forbidden_write_refs": normalized_forbidden_write_refs,
        "owner_route_match_status": owner_route_status,
        "owner_route_mismatch_refs": normalized_owner_route_mismatch_refs,
        "owner_route_mismatch": owner_route_mismatch,
        "body_free_payload": not non_body_free_payload,
        "non_body_free_payload_detected": non_body_free_payload,
        "fail_closed_reasons": fail_closed_reasons,
        "body_included": False,
        "authority_boundary": {
            "mas_validates_refs_shape_only": True,
            "opl_schema_forked_in_mas": False,
            "domain_ready_claimed": False,
            "publication_ready_claimed": False,
            "artifact_mutation_authorized": False,
        },
    }


def missing_required_evidence_families(
    *,
    run_manifest_ref: str | None,
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]] = (),
    decision_trace_refs: Sequence[str | Mapping[str, Any]] = (),
    artifact_lineage_refs: Sequence[str | Mapping[str, Any]] = (),
    reproducibility_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    typed_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
) -> list[str]:
    missing: list[str] = []
    if not _text(run_manifest_ref):
        missing.append("run_manifest_ref")
    if not _unique_refs(negative_failed_path_refs):
        missing.append("negative_failed_path_refs")
    if not _unique_refs(decision_trace_refs):
        missing.append("decision_trace_refs")
    if not _unique_refs(artifact_lineage_refs):
        missing.append("artifact_lineage_refs")
    if not _unique_refs(reproducibility_refs):
        missing.append("reproducibility_refs")
    if not (_unique_refs(owner_receipt_refs) or _unique_refs(typed_blocker_refs)):
        missing.append("owner_receipt_or_typed_blocker_refs")
    return missing


def _validation_ref_sets(
    *,
    run_manifest_ref: str | None,
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]],
    decision_trace_refs: Sequence[str | Mapping[str, Any]],
    artifact_lineage_refs: Sequence[str | Mapping[str, Any]],
    reproducibility_refs: Sequence[str | Mapping[str, Any]],
    owner_receipt_refs: Sequence[str | Mapping[str, Any]],
    typed_blocker_refs: Sequence[str | Mapping[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    owner_refs = _unique_refs(owner_receipt_refs)
    blocker_refs = _unique_refs(typed_blocker_refs)
    return {
        "run_manifest_ref": {"refs": [_text(run_manifest_ref)] if _text(run_manifest_ref) else []},
        "negative_failed_path_refs": {"refs": _unique_refs(negative_failed_path_refs)},
        "decision_trace_refs": {"refs": _unique_refs(decision_trace_refs)},
        "artifact_lineage_refs": {"refs": _unique_refs(artifact_lineage_refs)},
        "reproducibility_refs": {"refs": _unique_refs(reproducibility_refs)},
        "owner_receipt_or_typed_blocker_refs": {
            "refs": _unique_refs([*owner_refs, *blocker_refs]),
            "owner_receipt_refs": owner_refs,
            "typed_blocker_refs": blocker_refs,
        },
    }


def _ref_family_status(
    *,
    normalized_refs: Mapping[str, Mapping[str, list[str]]],
    missing_required_families: Sequence[str],
    typed_blocker_refs: Sequence[str],
) -> dict[str, dict[str, Any]]:
    missing = set(missing_required_families)
    result: dict[str, dict[str, Any]] = {}
    for family in REQUIRED_EVIDENCE_FAMILIES:
        family_refs = normalized_refs.get(family, {})
        refs = list(family_refs.get("refs", []))
        status = "present" if refs else "missing"
        if family == "owner_receipt_or_typed_blocker_refs" and family_refs.get("typed_blocker_refs"):
            status = "blocker"
        elif family in missing and typed_blocker_refs:
            status = "blocker"
        result[family] = {
            "status": status,
            "ref_count": len(refs),
            "refs": refs,
            "body_included": False,
        }
    return result


def _placeholder_ref_map(
    normalized_refs: Mapping[str, Mapping[str, list[str]]]
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for family, payload in normalized_refs.items():
        refs = [
            ref
            for ref in payload.get("refs", [])
            if _is_placeholder_ref(ref)
        ]
        if refs:
            result[family] = refs
    return result


def _is_placeholder_ref(value: str) -> bool:
    text = value.strip().lower()
    if not text:
        return True
    if text.startswith("<") or text.endswith(">"):
        return True
    return text in {
        "todo",
        "tbd",
        "n/a",
        "na",
        "none",
        "null",
        "placeholder",
        "example",
        "sample",
    } or text.startswith(("placeholder:", "todo:", "tbd:"))


def _validation_status(
    *,
    missing_required_families: Sequence[str],
    fail_closed_reasons: Sequence[str],
) -> str:
    if not fail_closed_reasons:
        return "schema_compatible_refs_ready"
    if missing_required_families:
        return "fail_closed_missing_required_refs"
    return "fail_closed_schema_violation"


def _missing_reproducibility_refs(
    *,
    code_refs: Sequence[str],
    source_data_version_refs: Sequence[str],
    software_environment_refs: Sequence[str],
    parameter_seed_refs: Sequence[str],
) -> list[str]:
    missing: list[str] = []
    if not code_refs:
        missing.append("code_refs")
    if not source_data_version_refs:
        missing.append("source_data_version_refs")
    if not software_environment_refs:
        missing.append("software_environment_refs")
    if not parameter_seed_refs:
        missing.append("parameter_seed_refs")
    return missing


def _single_next_owner_blocker(
    *,
    typed_blocker_refs: Sequence[str],
    next_owner_blocker_refs: Sequence[str],
) -> dict[str, Any]:
    refs = _unique_refs([*next_owner_blocker_refs, *typed_blocker_refs])
    return {
        "status": "blocked" if refs else "clear",
        "ref": refs[0] if refs else None,
        "candidate_count": len(refs),
        "body_included": False,
        "is_route_authority": False,
    }


def _unique_refs(values: Sequence[str | Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, Mapping):
            text = _text(value.get("ref"))
        else:
            text = _text(value)
        if text and text not in refs:
            refs.append(text)
    return refs


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _ref_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_")
    return token[:160] or "workspace"


__all__ = [
    "REQUIRED_EVIDENCE_FAMILIES",
    "SCHEMA_VALIDATION_VERSION",
    "SURFACE_KIND",
    "VERSION",
    "build_research_evidence_pack_summary",
    "failed_path_consumption_summary",
    "missing_required_evidence_families",
    "schema_compatible_validation_summary",
]
