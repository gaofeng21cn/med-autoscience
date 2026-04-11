from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience import reference_papers
from med_autoscience import startup_literature
from med_autoscience.controllers import workspace_literature as workspace_literature_controller


STUDY_REFERENCE_CONTEXT_SCHEMA_VERSION = 1
_ROLE_PRIORITY = {
    "framing_anchor": 0,
    "claim_support": 1,
    "journal_fit_neighbor": 2,
    "adjacent_inspiration": 3,
}


def _reference_context_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / "artifacts" / "reference_context" / "latest.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _study_role_from_record(record: dict[str, object]) -> str:
    relevance_role = str(record.get("relevance_role") or "").strip()
    claim_support_scope = {
        str(item).strip()
        for item in list(record.get("claim_support_scope") or [])
        if isinstance(item, str) and item.strip()
    }
    if relevance_role == "anchor_paper":
        return "framing_anchor"
    if relevance_role == "closest_competitor":
        return "claim_support"
    if "journal_fit_neighbor" in claim_support_scope:
        return "journal_fit_neighbor"
    return "adjacent_inspiration"


def _claim_support_scope(record: dict[str, object]) -> list[str]:
    scope = [
        str(item).strip()
        for item in list(record.get("claim_support_scope") or [])
        if isinstance(item, str) and item.strip()
    ]
    return list(dict.fromkeys(scope))


def _merge_claim_support_scope(existing: list[str], incoming: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *incoming]))


def build_study_reference_context(
    *,
    study_root: Path,
    workspace_root: Path,
    startup_contract: dict[str, Any],
) -> dict[str, object]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()

    startup_records = startup_literature.resolve_startup_literature_records(startup_contract=startup_contract)
    reference_contract = reference_papers.resolve_reference_paper_contract_from_payload(
        anchor_root=resolved_study_root,
        payload={"reference_papers": startup_contract.get("reference_papers")},
    )
    reference_records = (
        reference_papers.export_reference_papers_to_literature_records(contract=reference_contract)
        if reference_contract is not None
        else []
    )
    combined_records = [*startup_records, *reference_records]
    if combined_records:
        workspace_literature_controller.sync_workspace_literature(
            workspace_root=resolved_workspace_root,
            records=combined_records,
        )
    else:
        workspace_literature_controller.init_workspace_literature(workspace_root=resolved_workspace_root)
    workspace_status = workspace_literature_controller.workspace_literature_status(workspace_root=resolved_workspace_root)

    selections_by_id: dict[str, dict[str, str]] = {}
    records_by_id: dict[str, dict[str, object]] = {}
    ordered_ids: list[str] = []
    source_rows = [
        *[(record, "startup_contract") for record in startup_records],
        *[(record, "reference_papers") for record in reference_records],
    ]
    for raw_record, source_layer in source_rows:
        canonical = workspace_literature_controller.canonicalize_record_payload(raw_record=raw_record)
        record_id = str(canonical["record_id"])
        study_role = _study_role_from_record(raw_record)
        materialized_record = dict(canonical)
        materialized_record["relevance_role"] = study_role
        materialized_record["claim_support_scope"] = _claim_support_scope(raw_record)

        if record_id not in selections_by_id:
            ordered_ids.append(record_id)
            selections_by_id[record_id] = {
                "record_id": record_id,
                "study_role": study_role,
                "source_layer": source_layer,
            }
            records_by_id[record_id] = materialized_record
            continue

        existing_role = selections_by_id[record_id]["study_role"]
        if _ROLE_PRIORITY[study_role] < _ROLE_PRIORITY[existing_role]:
            selections_by_id[record_id] = {
                "record_id": record_id,
                "study_role": study_role,
                "source_layer": source_layer,
            }
            records_by_id[record_id]["relevance_role"] = study_role
        records_by_id[record_id]["claim_support_scope"] = _merge_claim_support_scope(
            list(records_by_id[record_id].get("claim_support_scope") or []),
            list(materialized_record.get("claim_support_scope") or []),
        )

    selected_record_ids = ordered_ids
    selections = [selections_by_id[record_id] for record_id in selected_record_ids]
    records = [records_by_id[record_id] for record_id in selected_record_ids]
    mandatory_anchor_record_ids = [
        selection["record_id"] for selection in selections if selection["study_role"] == "framing_anchor"
    ]
    optional_neighbor_record_ids = [
        selection["record_id"]
        for selection in selections
        if selection["study_role"] in {"journal_fit_neighbor", "adjacent_inspiration"}
    ]

    artifact_path = _reference_context_path(resolved_study_root)
    payload = {
        "schema_version": STUDY_REFERENCE_CONTEXT_SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "workspace_root": str(resolved_workspace_root),
        "workspace_registry_path": workspace_status["registry_path"],
        "record_count": len(records),
        "selected_record_ids": selected_record_ids,
        "mandatory_anchor_record_ids": mandatory_anchor_record_ids,
        "optional_neighbor_record_ids": optional_neighbor_record_ids,
        "selections": selections,
        "records": records,
        "artifact_path": str(artifact_path),
    }
    _write_json(artifact_path, payload)
    return payload
