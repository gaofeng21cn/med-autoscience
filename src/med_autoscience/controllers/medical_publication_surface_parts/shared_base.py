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
from med_autoscience.controllers.statistical_discipline_runtime import validate_statistical_reviewer_audit
from med_autoscience.policies import medical_disclosure_contract
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
    statistical_reviewer_audit_path: Path
    structured_disclosure_audit_path: Path
    medical_manuscript_blueprint_path: Path
    medical_prose_review_path: Path
    results_narrative_map_path: Path
    figure_semantics_manifest_path: Path
    claim_evidence_map_path: Path
    numeric_trace_path: Path
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


from .charter_contracts import (
    CHARTER_EXPECTATION_CLOSURE_ALLOWED_STATUSES,
    CHARTER_EXPECTATION_CLOSURE_SPECS,
    _build_ledger_contract_linkage,
    _normalize_charter_expectation_closure_records,
    _normalized_charter_expectation_items,
    _normalized_path,
    build_charter_contract_linkage,
    build_charter_expectation_closure_summary,
)



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
    medical_prose_review_path = resolve_medical_prose_review_path(
        paper_root=paper_root,
        study_root=study_root,
    )
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
        statistical_reviewer_audit_path=paper_root / "review" / medical_surface_policy.STATISTICAL_REVIEWER_AUDIT_BASENAME,
        structured_disclosure_audit_path=paper_root / "review" / medical_disclosure_contract.STRUCTURED_DISCLOSURE_AUDIT_BASENAME,
        medical_manuscript_blueprint_path=(
            study_root / "paper" / medical_surface_policy.MEDICAL_MANUSCRIPT_BLUEPRINT_BASENAME
            if study_root is not None
            else paper_root / medical_surface_policy.MEDICAL_MANUSCRIPT_BLUEPRINT_BASENAME
        ),
        medical_prose_review_path=medical_prose_review_path,
        results_narrative_map_path=paper_root / medical_surface_policy.RESULTS_NARRATIVE_MAP_BASENAME,
        figure_semantics_manifest_path=paper_root / medical_surface_policy.FIGURE_SEMANTICS_MANIFEST_BASENAME,
        claim_evidence_map_path=paper_root / medical_surface_policy.CLAIM_EVIDENCE_MAP_BASENAME,
        numeric_trace_path=paper_root / medical_surface_policy.NUMERIC_TRACE_BASENAME,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        derived_analysis_manifest_path=paper_root / medical_surface_policy.DERIVED_ANALYSIS_MANIFEST_BASENAME,
        reproducibility_supplement_path=paper_root / medical_surface_policy.REPRODUCIBILITY_SUPPLEMENT_BASENAME,
        endpoint_provenance_note_path=paper_root / medical_surface_policy.ENDPOINT_PROVENANCE_NOTE_BASENAME,
    )


def resolve_medical_prose_review_path(*, paper_root: Path, study_root: Path | None) -> Path:
    candidates: list[Path] = []
    if study_root is not None:
        candidates.append(study_root / "artifacts" / "publication_eval" / medical_surface_policy.MEDICAL_PROSE_REVIEW_BASENAME)
        candidates.append(study_root / "paper" / medical_surface_policy.MEDICAL_PROSE_REVIEW_BASENAME)
    candidates.extend(
        [
            paper_root / medical_surface_policy.MEDICAL_PROSE_REVIEW_BASENAME,
            paper_root / "review" / medical_surface_policy.MEDICAL_PROSE_REVIEW_BASENAME,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


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
    workspace_root: Path | None = None
    if len(resolved_quest_root.parents) >= 3:
        candidate = resolved_quest_root.parents[2]
        layout = build_workspace_runtime_layout(workspace_root=candidate)
        if (
            candidate.parent.name != "ops"
            and resolved_quest_root.parent == layout.quests_root
            and resolved_quest_root.parent.parent == layout.runtime_root
        ):
            workspace_root = layout.workspace_root
    if workspace_root is None and (
        len(resolved_quest_root.parents) >= 5
        and resolved_quest_root.parent.name == "quests"
        and resolved_quest_root.parent.parent.name == "runtime"
        and resolved_quest_root.parents[3].name == "ops"
    ):
        workspace_root = resolved_quest_root.parents[4]
    if workspace_root is None:
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
