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
) -> dict[str, Any]:
    normalized_domain = _text(domain_id) or "medautoscience"
    normalized_task = _text(task_kind) or "domain_owner"
    normalized_study = _text(study_id)
    normalized_stage = _text(stage_id)
    task_ref = _ref_token(normalized_task)
    scope_ref = _ref_token(normalized_study or normalized_stage or "workspace")
    ref_prefix = f"mas-research-evidence-pack:{normalized_domain}:{task_ref}:{scope_ref}"
    normalized_negative_failed_path_refs = _unique_refs(negative_failed_path_refs)
    normalized_decision_trace_refs = _unique_refs(decision_trace_refs)
    normalized_artifact_lineage_refs = _unique_refs(artifact_lineage_refs)
    normalized_reproducibility_refs = _unique_refs(reproducibility_refs)
    normalized_owner_receipt_refs = _unique_refs(owner_receipt_refs)
    normalized_typed_blocker_refs = _unique_refs(typed_blocker_refs)
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
        "code_refs": _unique_refs(code_refs),
        "source_data_version_refs": _unique_refs(source_data_version_refs),
        "software_environment_refs": _unique_refs(software_environment_refs),
        "parameter_seed_refs": _unique_refs(parameter_seed_refs),
        "input_refs": _unique_refs(input_refs),
        "output_refs": _unique_refs(output_refs),
        "checksum_refs": _unique_refs(checksum_refs),
        "claim_impact_refs": _unique_refs(claim_impact_refs),
        "negative_failed_path_refs": normalized_negative_failed_path_refs,
        "decision_trace_refs": normalized_decision_trace_refs,
        "artifact_lineage_refs": normalized_artifact_lineage_refs,
        "reproducibility_refs": normalized_reproducibility_refs,
        "typed_blocker_refs": normalized_typed_blocker_refs,
        "owner_receipt_refs": normalized_owner_receipt_refs,
        "schema_validation": validation,
        "missing_required_evidence_families": validation["missing_required_evidence_families"],
        "fail_closed_required": bool(validation["missing_required_evidence_families"]),
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


def schema_compatible_validation_summary(
    *,
    run_manifest_ref: str | None,
    negative_failed_path_refs: Sequence[str | Mapping[str, Any]] = (),
    decision_trace_refs: Sequence[str | Mapping[str, Any]] = (),
    artifact_lineage_refs: Sequence[str | Mapping[str, Any]] = (),
    reproducibility_refs: Sequence[str | Mapping[str, Any]] = (),
    owner_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    typed_blocker_refs: Sequence[str | Mapping[str, Any]] = (),
) -> dict[str, Any]:
    missing = missing_required_evidence_families(
        run_manifest_ref=run_manifest_ref,
        negative_failed_path_refs=negative_failed_path_refs,
        decision_trace_refs=decision_trace_refs,
        artifact_lineage_refs=artifact_lineage_refs,
        reproducibility_refs=reproducibility_refs,
        owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
    )
    return {
        "surface_kind": "mas_research_evidence_pack_schema_validation",
        "version": SCHEMA_VALIDATION_VERSION,
        "status": "schema_compatible_refs_ready" if not missing else "fail_closed_missing_required_refs",
        "opl_schema_family": "research_evidence_pack.v1",
        "required_evidence_families": list(REQUIRED_EVIDENCE_FAMILIES),
        "missing_required_evidence_families": missing,
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
    "missing_required_evidence_families",
    "schema_compatible_validation_summary",
]
