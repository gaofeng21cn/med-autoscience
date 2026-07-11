from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.opl_domain_pack.state_index_source_refs import normalize_state_index_refs


SCHEMA_VERSION = 2
SURFACE = "stage_knowledge_refs_entry"


def build_stage_knowledge_entry(
    *,
    study_id: str,
    stage: str,
    stage_folder_refs: Sequence[Mapping[str, Any]] = (),
    state_index_refs: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    refs = normalize_state_index_refs([*stage_folder_refs, *state_index_refs])
    missing_reasons = [] if refs else ["missing_opl_stage_folder_or_state_index_refs"]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": _required_text("stage", stage),
        "status": "ready" if refs else "missing",
        "opl_refs": refs,
        "consumed_refs": [ref["source_ref"] for ref in refs],
        "payload_sha256": [ref["payload_sha256"] for ref in refs],
        "missing_reasons": missing_reasons,
        "authority_boundary": {
            "refs_only": True,
            "body_included": False,
            "local_persistence": "absent",
            "state_index_owner": "one-person-lab",
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
        },
    }


def inject_stage_knowledge_entry(
    payload: dict[str, Any],
    *,
    stage_entry: dict[str, Any],
) -> dict[str, Any]:
    injected = dict(payload)
    input_contract = dict(injected.get("input_contract") or {})
    required_refs = dict(input_contract.get("required_refs") or {})
    required_refs["opl_stage_folder_state_index_refs"] = _stage_knowledge_input_ref(stage_entry)
    input_contract["required_refs"] = required_refs
    input_contract["required_surfaces"] = list(
        dict.fromkeys([*list(input_contract.get("required_surfaces") or []), "opl_stage_folder_state_index_refs"])
    )
    missing = list(input_contract.get("missing_or_invalid_refs") or [])
    if stage_entry.get("status") != "ready":
        missing.append("opl_stage_folder_state_index_refs")
    input_contract["missing_or_invalid_refs"] = list(dict.fromkeys(missing))
    input_contract["all_required_refs_present"] = not input_contract["missing_or_invalid_refs"]
    injected["input_contract"] = input_contract
    injected["stage_knowledge_entry"] = dict(stage_entry)
    injected["stage_knowledge_refs"] = list(stage_entry.get("opl_refs") or [])
    injected["stage_knowledge_status"] = stage_entry.get("status")
    injected["stage_knowledge_missing_reasons"] = list(stage_entry.get("missing_reasons") or [])
    return injected


def _stage_knowledge_input_ref(stage_entry: Mapping[str, Any]) -> dict[str, Any]:
    ready = stage_entry.get("status") == "ready"
    return {
        "surface": "opl_stage_folder_state_index_refs",
        "refs": list(stage_entry.get("opl_refs") or []),
        "required": True,
        "present": ready,
        "valid": ready,
        "status": stage_entry.get("status"),
        "missing_reasons": list(stage_entry.get("missing_reasons") or []),
    }


def _required_text(field: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


__all__ = ["build_stage_knowledge_entry", "inject_stage_knowledge_entry"]
