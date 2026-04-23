from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from med_autoscience import display_registry

TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN = [
    {
        "display_id": "cohort_flow",
        "display_kind": "figure",
        "requirement_key": "cohort_flow_figure",
        "catalog_id": "F1",
    },
    {
        "display_id": "discrimination_calibration",
        "display_kind": "figure",
        "requirement_key": "time_to_event_discrimination_calibration_panel",
        "catalog_id": "F2",
    },
    {
        "display_id": "km_risk_stratification",
        "display_kind": "figure",
        "requirement_key": "time_to_event_risk_group_summary",
        "catalog_id": "F3",
    },
    {
        "display_id": "decision_curve",
        "display_kind": "figure",
        "requirement_key": "time_to_event_decision_curve",
        "catalog_id": "F4",
    },
    {
        "display_id": "multicenter_generalizability",
        "display_kind": "figure",
        "requirement_key": "multicenter_generalizability_overview",
        "catalog_id": "F5",
    },
    {
        "display_id": "baseline_characteristics",
        "display_kind": "table",
        "requirement_key": "table1_baseline_characteristics",
        "catalog_id": "T1",
    },
    {
        "display_id": "time_to_event_performance_summary",
        "display_kind": "table",
        "requirement_key": "table2_time_to_event_performance_summary",
        "catalog_id": "T2",
    },
]

CHARTER_EXPECTATION_FIXTURES: dict[str, dict[str, str]] = {
    "minimum_sci_ready_evidence_package": {
        "ledger_name": "evidence_ledger",
        "expectation_text": "External validation evidence package is durably archived for the manuscript route.",
    },
    "scientific_followup_questions": {
        "ledger_name": "review_ledger",
        "expectation_text": "Residual-risk framing is defended against calibration drift before submission.",
    },
    "manuscript_conclusion_redlines": {
        "ledger_name": "review_ledger",
        "expectation_text": "Conclusion stays inside internal validation and avoids treatment-facing escalation.",
    },
}


def _canonicalize_registry_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return normalized
    if display_registry.is_evidence_figure_template(normalized):
        return display_registry.get_evidence_figure_spec(normalized).template_id
    if display_registry.is_illustration_shell(normalized):
        return display_registry.get_illustration_shell_spec(normalized).shell_id
    if display_registry.is_table_shell(normalized):
        return display_registry.get_table_shell_spec(normalized).shell_id
    return normalized


def full_id(value: str) -> str:
    return _canonicalize_registry_id(value)


def _normalize_namespaced_ids(payload: Any) -> Any:
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = _normalize_namespaced_ids(value)
            if key in {"requirement_key", "template_id", "shell_id", "table_shell_id"} and isinstance(
                normalized_value, str
            ):
                normalized_value = _canonicalize_registry_id(normalized_value)
            normalized[key] = normalized_value
        return normalized
    if isinstance(payload, list):
        return [_normalize_namespaced_ids(item) for item in payload]
    return payload


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_payload = _normalize_namespaced_ids(payload)
    path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_review_ledger(path: Path, *, summary: str = "Clarify the endpoint boundary in Results.") -> None:
    dump_json(
        path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer_1",
                    "summary": summary,
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
    )


def _charter_expectation_record(
    expectation_key: str,
    *,
    status: str = "closed",
    closed_at: str | None = "2026-04-21T08:30:00+00:00",
    note: str | None = None,
) -> dict[str, Any]:
    expectation = CHARTER_EXPECTATION_FIXTURES[expectation_key]
    return {
        "expectation_key": expectation_key,
        "expectation_text": expectation["expectation_text"],
        "status": status,
        "closed_at": closed_at,
        "note": note or f"{expectation_key} closure recorded on the ledger.",
    }


def _write_charter_expectation_closures(path: Path, records: list[dict[str, Any]]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["charter_expectation_closures"] = records
    dump_json(path, payload)


def _write_study_charter(study_root: Path, *, study_id: str = "002-early-residual-risk") -> Path:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    dump_json(
        charter_path,
        {
            "schema_version": 1,
            "charter_id": f"charter::{study_id}::v1",
            "study_id": study_id,
            "publication_objective": "Deliver a manuscript-safe residual-risk paper package.",
            "minimum_sci_ready_evidence_package": [],
            "scientific_followup_questions": [],
            "manuscript_conclusion_redlines": [],
            "paper_quality_contract": {
                "frozen_at_startup": True,
                "evidence_expectations": {
                    "minimum_sci_ready_evidence_package": [],
                },
                "review_expectations": {
                    "scientific_followup_questions": [],
                    "manuscript_conclusion_redlines": [],
                },
                "downstream_contract_roles": {
                    "evidence_ledger": "records evidence against evidence expectations",
                    "review_ledger": "records review closure against review expectations",
                    "final_audit": "audits readiness against the charter contract",
                },
            },
        },
    )
    return charter_path


def _paper_root_from_quest(quest_root: Path) -> Path:
    return quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"


def _attach_study_charter_context(
    monkeypatch,
    module,
    tmp_path: Path,
    quest_root: Path,
    *,
    include_charter_expectations: bool = False,
) -> Path:
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 002-early-residual-risk\n", encoding="utf-8")
    _write_study_charter(study_root)
    if include_charter_expectations:
        charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
        payload = json.loads(charter_path.read_text(encoding="utf-8"))
        minimum_sci_ready_evidence_package = [
            CHARTER_EXPECTATION_FIXTURES["minimum_sci_ready_evidence_package"]["expectation_text"]
        ]
        scientific_followup_questions = [
            CHARTER_EXPECTATION_FIXTURES["scientific_followup_questions"]["expectation_text"]
        ]
        manuscript_conclusion_redlines = [
            CHARTER_EXPECTATION_FIXTURES["manuscript_conclusion_redlines"]["expectation_text"]
        ]
        payload["minimum_sci_ready_evidence_package"] = minimum_sci_ready_evidence_package
        payload["scientific_followup_questions"] = scientific_followup_questions
        payload["manuscript_conclusion_redlines"] = manuscript_conclusion_redlines
        payload["paper_quality_contract"]["evidence_expectations"]["minimum_sci_ready_evidence_package"] = (
            minimum_sci_ready_evidence_package
        )
        payload["paper_quality_contract"]["review_expectations"]["scientific_followup_questions"] = (
            scientific_followup_questions
        )
        payload["paper_quality_contract"]["review_expectations"]["manuscript_conclusion_redlines"] = (
            manuscript_conclusion_redlines
        )
        dump_json(charter_path, payload)

    paper_root = _paper_root_from_quest(quest_root)
    monkeypatch.setattr(
        module,
        "resolve_paper_root_context",
        lambda _: SimpleNamespace(
            paper_root=paper_root,
            worktree_root=paper_root.parent,
            quest_root=quest_root,
            study_id="002-early-residual-risk",
            study_root=study_root,
        ),
        raising=False,
    )
    return study_root


def _attach_public_anchor_study_context(monkeypatch, module, tmp_path: Path, quest_root: Path) -> Path:
    study_root = tmp_path / "studies" / "004-public-anchor-route"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        "study_id: 004-public-anchor-route\n"
        "public_data_anchors:\n"
        "  - dataset_id: mapping-pituitary\n"
        "    role: anatomy_anchor\n"
        "  - dataset_id: geo-gse169498\n"
        "    role: biology_anchor\n",
        encoding="utf-8",
    )
    _write_study_charter(study_root, study_id="004-public-anchor-route")

    paper_root = _paper_root_from_quest(quest_root)

    monkeypatch.setattr(
        module,
        "resolve_paper_root_context",
        lambda _: SimpleNamespace(
            paper_root=paper_root,
            worktree_root=paper_root.parent,
            quest_root=quest_root,
            study_id="004-public-anchor-route",
            study_root=study_root,
        ),
        raising=False,
    )
    return study_root


def _inject_public_data_surface_mentions(quest_root: Path) -> None:
    paper_root = _paper_root_from_quest(quest_root)
    review_path = paper_root / "build" / "review_manuscript.md"
    review_path.write_text(
        review_path.read_text(encoding="utf-8")
        + "\nPublic MRI and omics datasets remain appendix-grade anatomy and biology anchors.\n",
        encoding="utf-8",
    )
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8")
        + "\nPublic anatomy and biology anchors were retained for the manuscript-facing route.\n",
        encoding="utf-8",
    )
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"][0]["title"] = "Public anatomy and biology anchors remain appendix-grade contextual support"
    dump_json(figure_catalog_path, figure_catalog)


def _write_public_evidence_decisions(quest_root: Path, decisions: list[dict[str, Any]]) -> None:
    derived_manifest_path = _paper_root_from_quest(quest_root) / "derived_analysis_manifest.json"
    payload = json.loads(derived_manifest_path.read_text(encoding="utf-8"))
    payload["public_evidence_decisions"] = decisions
    dump_json(derived_manifest_path, payload)


