from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref


def _normalized_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(Path(path).expanduser().resolve())


def _build_ledger_contract_linkage(
    *,
    ledger_name: str,
    ledger_path: Path | None,
    study_context_status: str,
    charter_id: str | None,
    contract_role: str | None,
) -> dict[str, Any]:
    resolved_ledger_path = Path(ledger_path).expanduser().resolve() if ledger_path is not None else None
    ledger_present = bool(resolved_ledger_path and resolved_ledger_path.exists())
    normalized_role = str(contract_role or "").strip() or None
    if study_context_status == "linked_context":
        if normalized_role and ledger_present:
            status = "linked"
        elif normalized_role:
            status = "ledger_missing"
        else:
            status = "contract_role_missing"
    else:
        status = study_context_status
    return {
        "ledger_name": ledger_name,
        "ledger_path": _normalized_path(resolved_ledger_path),
        "ledger_present": ledger_present,
        "charter_id": charter_id,
        "contract_role_present": bool(normalized_role),
        "contract_role": normalized_role,
        "contract_role_json_pointer": f"/paper_quality_contract/downstream_contract_roles/{ledger_name}",
        "status": status,
    }


CHARTER_EXPECTATION_CLOSURE_SPECS: tuple[dict[str, str], ...] = (
    {
        "expectation_key": "minimum_sci_ready_evidence_package",
        "ledger_name": "evidence_ledger",
        "contract_collection": "evidence_expectations",
        "label": "minimum_sci_ready_evidence_package",
    },
    {
        "expectation_key": "scientific_followup_questions",
        "ledger_name": "review_ledger",
        "contract_collection": "review_expectations",
        "label": "scientific_followup_questions",
    },
    {
        "expectation_key": "manuscript_conclusion_redlines",
        "ledger_name": "review_ledger",
        "contract_collection": "review_expectations",
        "label": "manuscript_conclusion_redlines",
    },
)
CHARTER_EXPECTATION_CLOSURE_ALLOWED_STATUSES = {"closed", "open", "in_progress", "blocked"}


def _normalized_charter_expectation_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _normalize_charter_expectation_closure_records(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    raw_records = payload.get("charter_expectation_closures")
    if not isinstance(raw_records, list):
        return []
    records: list[dict[str, Any]] = []
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, dict):
            continue
        expectation_key = str(raw_record.get("expectation_key") or "").strip()
        expectation_text = str(raw_record.get("expectation_text") or "").strip()
        status = str(raw_record.get("status") or "").strip().lower()
        if not expectation_key or not expectation_text:
            continue
        records.append(
            {
                "record_index": index,
                "expectation_key": expectation_key,
                "expectation_text": expectation_text,
                "status": status,
                "closed_at": str(raw_record.get("closed_at") or "").strip() or None,
                "note": str(raw_record.get("note") or "").strip() or None,
            }
        )
    return records


def build_charter_expectation_closure_summary(
    *,
    charter_contract_linkage: dict[str, Any],
    evidence_ledger_payload: object,
    review_ledger_payload: object,
    evidence_ledger_path: Path,
    review_ledger_path: Path,
) -> dict[str, Any]:
    quality_expectations = charter_contract_linkage.get("quality_expectations") or {}
    ledger_records = {
        "evidence_ledger": _normalize_charter_expectation_closure_records(evidence_ledger_payload),
        "review_ledger": _normalize_charter_expectation_closure_records(review_ledger_payload),
    }
    ledger_paths = {
        "evidence_ledger": evidence_ledger_path,
        "review_ledger": review_ledger_path,
    }
    categories: list[dict[str, Any]] = []
    blocking_items: list[dict[str, Any]] = []
    advisory_items: list[dict[str, Any]] = []
    declared_record_count = 0
    closed_item_count = 0
    for spec in CHARTER_EXPECTATION_CLOSURE_SPECS:
        expectation_key = spec["expectation_key"]
        ledger_name = spec["ledger_name"]
        contract_collection = spec["contract_collection"]
        charter_items = _normalized_charter_expectation_items(quality_expectations.get(expectation_key))
        matching_records: dict[str, list[dict[str, Any]]] = {}
        for record in ledger_records[ledger_name]:
            if record["expectation_key"] != expectation_key:
                continue
            matching_records.setdefault(record["expectation_text"], []).append(record)
        items: list[dict[str, Any]] = []
        category_declared_count = 0
        category_closed_count = 0
        category_blocker_count = 0
        category_advisory_count = 0
        for expectation_text in charter_items:
            base_payload = {
                "expectation_key": expectation_key,
                "expectation_text": expectation_text,
                "ledger_name": ledger_name,
                "ledger_path": _normalized_path(ledger_paths[ledger_name]),
                "contract_json_pointer": f"/paper_quality_contract/{contract_collection}/{expectation_key}",
            }
            matched_records = matching_records.get(expectation_text, [])
            if not matched_records:
                advisory_payload = {
                    **base_payload,
                    "closure_status": "not_recorded",
                    "recorded": False,
                    "record_count": 0,
                    "blocker": False,
                    "closed_at": None,
                    "note": None,
                }
                items.append(advisory_payload)
                advisory_items.append(advisory_payload)
                category_advisory_count += 1
                continue
            category_declared_count += 1
            declared_record_count += 1
            if len(matched_records) > 1:
                blocker_payload = {
                    **base_payload,
                    "closure_status": "duplicate_records",
                    "recorded": True,
                    "record_count": len(matched_records),
                    "blocker": True,
                    "closed_at": None,
                    "note": None,
                }
                items.append(blocker_payload)
                blocking_items.append(blocker_payload)
                category_blocker_count += 1
                continue
            record = matched_records[0]
            raw_status = str(record.get("status") or "").strip().lower()
            closure_status = (
                raw_status if raw_status in CHARTER_EXPECTATION_CLOSURE_ALLOWED_STATUSES else "invalid_status"
            )
            blocker = closure_status != "closed"
            item_payload = {
                **base_payload,
                "closure_status": closure_status,
                "recorded": True,
                "record_count": 1,
                "blocker": blocker,
                "closed_at": record.get("closed_at"),
                "note": record.get("note"),
            }
            items.append(item_payload)
            if blocker:
                blocking_items.append(item_payload)
                category_blocker_count += 1
            else:
                category_closed_count += 1
                closed_item_count += 1
        categories.append(
            {
                "expectation_key": expectation_key,
                "label": spec["label"],
                "ledger_name": ledger_name,
                "charter_item_count": len(charter_items),
                "declared_count": category_declared_count,
                "closed_count": category_closed_count,
                "blocker_count": category_blocker_count,
                "advisory_count": category_advisory_count,
                "items": items,
            }
        )
    return {
        "status": "blocked" if blocking_items else ("advisory" if advisory_items else "clear"),
        "declared_record_count": declared_record_count,
        "closed_item_count": closed_item_count,
        "blocking_items": blocking_items,
        "advisory_items": advisory_items,
        "categories": categories,
    }


def build_charter_contract_linkage(
    *,
    study_root: Path | None,
    evidence_ledger_path: Path | None,
    review_ledger_path: Path | None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    if resolved_study_root is None:
        study_context_status = "study_root_unresolved"
        charter_path = None
        charter_id = None
        paper_quality_contract_present = False
        downstream_contract_roles: dict[str, str] = {}
        quality_expectations = {spec["expectation_key"]: [] for spec in CHARTER_EXPECTATION_CLOSURE_SPECS}
    else:
        charter_path = resolve_study_charter_ref(study_root=resolved_study_root)
        charter_id = None
        downstream_contract_roles = {}
        quality_expectations = {spec["expectation_key"]: [] for spec in CHARTER_EXPECTATION_CLOSURE_SPECS}
        if not charter_path.exists():
            study_context_status = "study_charter_missing"
            paper_quality_contract_present = False
        else:
            try:
                charter_payload = read_study_charter(study_root=resolved_study_root, ref=charter_path)
            except (json.JSONDecodeError, ValueError):
                study_context_status = "study_charter_invalid"
                paper_quality_contract_present = False
            else:
                charter_id = str(charter_payload.get("charter_id") or "").strip() or None
                paper_quality_contract = charter_payload.get("paper_quality_contract")
                paper_quality_contract_present = isinstance(paper_quality_contract, dict)
                if paper_quality_contract_present:
                    raw_roles = paper_quality_contract.get("downstream_contract_roles")
                    if isinstance(raw_roles, dict):
                        downstream_contract_roles = {
                            str(key): str(value).strip()
                            for key, value in raw_roles.items()
                            if str(value).strip()
                        }
                    raw_evidence_expectations = paper_quality_contract.get("evidence_expectations")
                    if isinstance(raw_evidence_expectations, dict):
                        quality_expectations["minimum_sci_ready_evidence_package"] = (
                            _normalized_charter_expectation_items(
                                raw_evidence_expectations.get("minimum_sci_ready_evidence_package")
                            )
                        )
                    raw_review_expectations = paper_quality_contract.get("review_expectations")
                    if isinstance(raw_review_expectations, dict):
                        quality_expectations["scientific_followup_questions"] = (
                            _normalized_charter_expectation_items(
                                raw_review_expectations.get("scientific_followup_questions")
                            )
                        )
                        quality_expectations["manuscript_conclusion_redlines"] = (
                            _normalized_charter_expectation_items(
                                raw_review_expectations.get("manuscript_conclusion_redlines")
                            )
                        )
                study_context_status = "linked_context" if paper_quality_contract_present else "paper_quality_contract_missing"

    ledger_linkages = {
        "evidence_ledger": _build_ledger_contract_linkage(
            ledger_name="evidence_ledger",
            ledger_path=evidence_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("evidence_ledger"),
        ),
        "review_ledger": _build_ledger_contract_linkage(
            ledger_name="review_ledger",
            ledger_path=review_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("review_ledger"),
        ),
    }
    ledger_statuses = {payload["status"] for payload in ledger_linkages.values()}
    if study_context_status != "linked_context":
        status = study_context_status
    elif ledger_statuses == {"linked"}:
        status = "linked"
    elif "linked" in ledger_statuses:
        status = "partially_linked"
    else:
        status = "unlinked"
    return {
        "status": status,
        "study_root": _normalized_path(resolved_study_root),
        "study_charter_ref": {
            "charter_id": charter_id,
            "artifact_path": _normalized_path(charter_path),
        },
        "paper_quality_contract": {
            "present": paper_quality_contract_present,
            "artifact_path": _normalized_path(charter_path),
            "json_pointer": "/paper_quality_contract",
        },
        "quality_expectations": quality_expectations,
        "ledger_linkages": ledger_linkages,
    }
