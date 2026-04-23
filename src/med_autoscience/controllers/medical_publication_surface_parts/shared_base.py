from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience import display_registry
from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.policies.medical_reporting_contract import display_story_role_for_requirement_key
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout, resolve_runtime_root_from_quest_root
from med_autoscience.runtime_protocol import (
    paper_artifacts,
    quest_state,
    report_store as runtime_protocol_report_store,
    resolve_paper_root_context,
    user_message,
)
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref


managed_runtime_backend = runtime_backend_contract.get_managed_runtime_backend(
    runtime_backend_contract.DEFAULT_MANAGED_RUNTIME_BACKEND_ID
)
managed_runtime_transport = managed_runtime_backend
med_deepscientist_transport = managed_runtime_transport


@dataclass
class SurfaceState:
    quest_root: Path
    runtime_state: dict[str, Any]
    paper_root: Path
    study_root: Path | None
    review_defaults_path: Path
    ama_csl_path: Path
    paper_pdf_path: Path
    draft_path: Path
    review_manuscript_path: Path
    figure_catalog_path: Path
    table_catalog_path: Path
    methods_implementation_manifest_path: Path
    review_ledger_path: Path
    results_narrative_map_path: Path
    figure_semantics_manifest_path: Path
    claim_evidence_map_path: Path
    evidence_ledger_path: Path
    derived_analysis_manifest_path: Path
    reproducibility_supplement_path: Path
    endpoint_provenance_note_path: Path


@dataclass(frozen=True)
class MarkdownHeadingBlock:
    level: int
    heading: str
    start_line: int
    end_line: int
    body: str


def _controller_override(name: str, default: Any) -> Any:
    controller_module = sys.modules.get("med_autoscience.controllers.medical_publication_surface")
    if controller_module is None:
        return default
    return getattr(controller_module, name, default)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _paper_claim_submission_scope(paper_role: str) -> str:
    normalized_role = str(paper_role or "").strip() or "main_text"
    return "main_text" if normalized_role == "main_text" else "appendix"


def _paper_claim_evidence_kind(source_paths: list[str], support_level: str) -> str:
    joined_paths = " ".join(str(path).lower() for path in source_paths)
    if "literature" in joined_paths or "pubmed" in joined_paths or "evidence_tables" in joined_paths:
        return "literature"
    if any(token in joined_paths for token in ("figure", "table", "curve", "calibration", "decision")):
        return "display"
    if support_level == "boundary":
        return "boundary_analysis"
    return "result"


def _backfill_evidence_ledger_claims_from_claim_map(
    ledger_payload: object,
    claim_map_payload: object,
) -> Any:
    if not isinstance(ledger_payload, dict):
        return ledger_payload
    existing_claims = [dict(claim) for claim in (ledger_payload.get("claims") or []) if isinstance(claim, dict)]
    if existing_claims:
        return ledger_payload
    claim_map_claims = claim_map_payload.get("claims") if isinstance(claim_map_payload, dict) else None
    if not isinstance(claim_map_claims, list):
        return ledger_payload

    normalized = copy.deepcopy(ledger_payload)
    backfilled_claims: list[dict[str, Any]] = []
    for raw_claim in claim_map_claims:
        if not isinstance(raw_claim, dict):
            continue
        claim_id = str(raw_claim.get("claim_id") or "").strip()
        statement = str(raw_claim.get("statement") or raw_claim.get("claim_text") or "").strip()
        if not claim_id or not statement:
            continue
        paper_role = str(raw_claim.get("paper_role") or "").strip() or "main_text"
        submission_scope = _paper_claim_submission_scope(paper_role)
        evidence_items = raw_claim.get("evidence_items") if isinstance(raw_claim.get("evidence_items"), list) else []
        evidence_entries: list[dict[str, Any]] = []
        for index, evidence_item in enumerate(evidence_items, start=1):
            if not isinstance(evidence_item, dict):
                continue
            source_paths = [str(path).strip() for path in (evidence_item.get("source_paths") or []) if str(path).strip()]
            support_level = str(evidence_item.get("support_level") or "").strip() or "primary"
            evidence_entries.append(
                {
                    "evidence_id": str(evidence_item.get("item_id") or f"{claim_id}-evidence-{index}").strip()
                    or f"{claim_id}-evidence-{index}",
                    "kind": _paper_claim_evidence_kind(source_paths, support_level),
                    "source_paths": source_paths,
                    "support_level": support_level,
                    "summary": str(evidence_item.get("summary") or statement).strip() or statement,
                }
            )
        if not evidence_entries:
            continue
        risks = [
            str(item).strip()
            for item in (raw_claim.get("risks") or raw_claim.get("limitations") or [])
            if str(item).strip()
        ]
        gaps = [
            {
                "gap_id": f"{claim_id}-gap-{index}",
                "description": risk,
                "submission_impact": "Keep the submission-facing claim inside the current evidence boundary.",
            }
            for index, risk in enumerate(risks, start=1)
        ]
        if not gaps:
            gaps = [
                {
                    "gap_id": f"{claim_id}-gap-1",
                    "description": "This claim should remain bounded to the currently mapped evidence surface.",
                    "submission_impact": "Avoid extending the claim beyond the mapped cohort, displays, and current validation scope.",
                }
            ]
        backfilled_claims.append(
            {
                **copy.deepcopy(raw_claim),
                "claim_id": claim_id,
                "statement": statement,
                "status": str(raw_claim.get("status") or "").strip() or "supported",
                "submission_scope": submission_scope,
                "evidence": evidence_entries,
                "gaps": gaps,
                "recommended_actions": [
                    {
                        "action_id": f"{claim_id}-action-1",
                        "priority": "required" if submission_scope == "main_text" else "recommended",
                        "description": "Keep the manuscript wording aligned with the mapped evidence and current interpretation boundary.",
                    }
                ],
            }
        )
    if backfilled_claims:
        normalized["claims"] = backfilled_claims
    return normalized


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


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def build_surface_state(quest_root: Path) -> SurfaceState:
    runtime_state = _controller_override("quest_state", quest_state).load_runtime_state(quest_root) or {}
    paper_root = paper_artifacts.resolve_latest_paper_root(quest_root)
    study_root: Path | None = None
    try:
        paper_context = _controller_override("resolve_paper_root_context", resolve_paper_root_context)(paper_root)
    except (FileNotFoundError, ValueError):
        paper_context = None
    if paper_context is not None:
        study_root = paper_context.study_root
    if study_root is None:
        study_root = resolve_study_root_from_live_quest_root(quest_root, runtime_state)
    return SurfaceState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        paper_root=paper_root,
        study_root=study_root,
        review_defaults_path=paper_root / "latex" / "review_defaults.yaml",
        ama_csl_path=paper_root / "latex" / "american-medical-association.csl",
        paper_pdf_path=paper_root / "paper.pdf",
        draft_path=paper_root / "draft.md",
        review_manuscript_path=paper_root / "build" / "review_manuscript.md",
        figure_catalog_path=paper_root / "figures" / "figure_catalog.json",
        table_catalog_path=paper_root / "tables" / "table_catalog.json",
        methods_implementation_manifest_path=paper_root / medical_surface_policy.METHODS_IMPLEMENTATION_MANIFEST_BASENAME,
        review_ledger_path=paper_root / "review" / medical_surface_policy.REVIEW_LEDGER_BASENAME,
        results_narrative_map_path=paper_root / medical_surface_policy.RESULTS_NARRATIVE_MAP_BASENAME,
        figure_semantics_manifest_path=paper_root / medical_surface_policy.FIGURE_SEMANTICS_MANIFEST_BASENAME,
        claim_evidence_map_path=paper_root / medical_surface_policy.CLAIM_EVIDENCE_MAP_BASENAME,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        derived_analysis_manifest_path=paper_root / medical_surface_policy.DERIVED_ANALYSIS_MANIFEST_BASENAME,
        reproducibility_supplement_path=paper_root / medical_surface_policy.REPRODUCIBILITY_SUPPLEMENT_BASENAME,
        endpoint_provenance_note_path=paper_root / medical_surface_policy.ENDPOINT_PROVENANCE_NOTE_BASENAME,
    )


def excerpt_around(text: str, start: int, end: int, *, width: int = 96) -> str:
    left = max(0, start - width // 2)
    right = min(len(text), end + width // 2)
    excerpt = text[left:right].replace("\n", " ").strip()
    return excerpt


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def resolve_study_root_from_live_quest_root(quest_root: Path, runtime_state: dict[str, Any]) -> Path | None:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    try:
        workspace_root = resolved_quest_root.parents[4]
    except IndexError:
        return None
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    if resolved_quest_root.parent != layout.quests_root or resolved_quest_root.parent.parent != layout.runtime_root:
        return None
    quest_id = str(runtime_state.get("quest_id") or resolved_quest_root.name).strip()
    if not quest_id:
        return None
    direct_study_root = (workspace_root / "studies" / quest_id).resolve()
    if (direct_study_root / "study.yaml").exists():
        return direct_study_root
    studies_root = workspace_root / "studies"
    if not studies_root.exists():
        return None
    for runtime_binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        payload = load_yaml_mapping(runtime_binding_path)
        if str(payload.get("quest_id") or "").strip() != quest_id:
            continue
        study_root = runtime_binding_path.parent.resolve()
        if (study_root / "study.yaml").exists():
            return study_root
    return None



def unique_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for hit in hits:
        key = (hit["path"], hit["location"], hit["pattern_id"], hit["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique

