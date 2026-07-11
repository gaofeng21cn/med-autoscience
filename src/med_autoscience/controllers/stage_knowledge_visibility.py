from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.opl_domain_pack.state_index_source_refs import normalize_state_index_refs


SCHEMA_VERSION = 2
SURFACE = "stage_knowledge_visibility"


def build_stage_knowledge_visibility(
    *,
    study_id: str,
    stage_refs: Mapping[str, Sequence[Mapping[str, Any]]],
    closeout_refs: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    stages = [
        {
            "stage": stage,
            "status": "available" if refs else "missing",
            "opl_refs": refs,
            "consumed_refs": [ref["source_ref"] for ref in refs],
            "payload_sha256": [ref["payload_sha256"] for ref in refs],
            "missing_reasons": [] if refs else [f"missing_opl_stage_refs:{stage}"],
        }
        for stage, raw_refs in stage_refs.items()
        if (refs := normalize_state_index_refs(raw_refs)) or raw_refs == () or raw_refs == []
    ]
    normalized_closeouts = normalize_state_index_refs(closeout_refs)
    missing = [reason for row in stages for reason in row["missing_reasons"]]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "available" if stages and not missing else "partial" if stages else "missing",
        "study_id": _required_text("study_id", study_id),
        "stage_count": len(stages),
        "stages": stages,
        "consumed_refs": list(dict.fromkeys(
            [ref for row in stages for ref in row["consumed_refs"]]
            + [ref["source_ref"] for ref in normalized_closeouts]
        )),
        "closeout_refs": normalized_closeouts,
        "missing_reasons": list(dict.fromkeys(missing)),
        "authority_boundary": {
            "kind": "opl_refs_only_visibility",
            "body_included": False,
            "local_persistence": "absent",
            "state_index_owner": "one-person-lab",
            "can_authorize_publication_quality": False,
            "can_replace_controller_decision": False,
        },
    }


def _required_text(field: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


__all__ = ["build_stage_knowledge_visibility"]
