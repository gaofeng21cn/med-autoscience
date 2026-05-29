from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


SURFACE_KIND = "mas_research_evidence_pack_summary"
VERSION = "mas-research-evidence-pack-summary.v1"


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
) -> dict[str, Any]:
    normalized_domain = _text(domain_id) or "medautoscience"
    normalized_task = _text(task_kind) or "domain_owner"
    normalized_study = _text(study_id)
    normalized_stage = _text(stage_id)
    task_ref = _ref_token(normalized_task)
    scope_ref = _ref_token(normalized_study or normalized_stage or "workspace")
    ref_prefix = f"mas-research-evidence-pack:{normalized_domain}:{task_ref}:{scope_ref}"
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
        "negative_failed_path_refs": _unique_refs(negative_failed_path_refs),
        "decision_trace_refs": _unique_refs(decision_trace_refs),
        "typed_blocker_refs": _unique_refs(typed_blocker_refs),
        "owner_receipt_refs": _unique_refs(owner_receipt_refs),
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
    "SURFACE_KIND",
    "VERSION",
    "build_research_evidence_pack_summary",
]
