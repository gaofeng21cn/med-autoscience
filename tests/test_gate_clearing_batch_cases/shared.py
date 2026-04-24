from __future__ import annotations

import importlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_blocked_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-21T12:42:39+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-21T12:42:39+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Return to bounded analysis before write continues.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "medical_publication_surface_blocked",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::bounded_analysis::2026-04-21T12:42:39+00:00",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Run the narrowest bounded analysis first.",
                "route_target": "analysis-campaign",
                "route_key_question": "当前论文线继续前还差哪一个最窄的补充分析？",
                "route_rationale": "The publication gate remains blocked.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_bundle_stage_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T01:05:42+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T01:05:42+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "bundle-stage publishability repair",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Bundle-stage blockers are on the critical path.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "delivery",
                "severity": "must_fix",
                "summary": "submission_surface_qc_failure_present",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::2026-04-22T01:05:42+00:00",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Bundle-stage blockers should route back to the controller.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_submission_minimal_fingerprint_inputs(paper_root: Path) -> None:
    _write_text(paper_root / "build" / "compiled_manuscript.md", "# Results\n\nStable content.\n")
    _write_text(paper_root / "build" / "compiled_paper.pdf", "%PDF-1.4\n")
    _write_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/build/compiled_manuscript.md",
            "output_pdf": "paper/build/compiled_paper.pdf",
        },
    )
    _write_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    _write_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "compiled_markdown_path": "paper/build/compiled_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "pdf_path": "paper/build/compiled_paper.pdf",
        },
    )






































