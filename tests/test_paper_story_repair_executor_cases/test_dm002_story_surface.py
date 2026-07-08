from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_paper_story_repair_executor import _write_json
from tests.test_quality_repair_batch_cases.dm002_external_validation_table_consistency import (
    _write_dm002_rerun_evidence,
)


def test_story_repair_executor_accepts_idempotent_dm002_story_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_story_repair_executor")
    story_surface = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    paper_root = study_root / "paper"
    _write_dm002_rerun_evidence(study_root)
    manuscript, extra_paths = story_surface.materialize_dm002_external_validation_story_surface(
        paper_root=paper_root,
    )
    assert manuscript
    for relpath in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manuscript if manuscript.endswith("\n") else f"{manuscript}\n", encoding="utf-8")
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "DM002-C1",
                    "statement": "The fixed China-derived score retained risk ranking but underpredicted NHANES absolute mortality.",
                    "status": "supported_with_limitations",
                    "paper_role": "main_text",
                    "evidence_items": [
                        {
                            "item_id": "DM002-C1-performance",
                            "support_level": "primary",
                            "source_paths": [
                                "paper/draft.md",
                                "paper/tables/generated/T2_time_to_event_performance_summary.md",
                            ],
                            "summary": "The external-validation manuscript and performance table report c-index and calibration.",
                        }
                    ],
                }
            ],
        },
    )
    source_eval_path = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "eval-dm002-current",
            "recommended_actions": [
                {
                    "next_work_unit": {
                        "unit_id": "manuscript_story_repair",
                        "lane": "write",
                    },
                }
            ],
        },
    )
    story_refs = [
        {"path": str((paper_root / "draft.md").resolve()), "artifact_role": "canonical_manuscript_story_surface"},
        {
            "path": str((paper_root / "build/review_manuscript.md").resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
        },
    ]
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "ok": True,
            "source_eval_id": "eval-dm002-current",
            "repair_execution_evidence_path": str(
                study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
            ),
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "surface_refs": story_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "story_surface_delta_refs": story_refs,
                },
            },
        },
    )

    result = module.run_story_repair(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
        study_root=study_root,
        source="test",
    )

    assert result["ok"] is True
    assert result["status"] == "progress_delta_candidate"
    assert result["work_unit_id"] == "dm002_same_line_publication_paper_repair"
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in result["changed_artifact_refs"]
    }
    assert "paper/draft.md" in changed_paths
    assert "paper/build/review_manuscript.md" in changed_paths
    assert "paper/evidence_ledger.json" in changed_paths
    assert "paper/review/review_ledger.json" in changed_paths
    assert {
        str((paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md").resolve()),
        str((paper_root / "tables" / "generated" / "T3_grouped_calibration.md").resolve()),
    }.issubset(set(extra_paths))
    assert "manuscript_story_surface_delta_missing" not in result["repair_execution_evidence"]["blockers"]


def test_dm002_story_surface_carries_archived_fixed_equation_and_clinical_boundary(
    tmp_path: Path,
) -> None:
    story_surface = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    paper_root = study_root / "paper"
    _write_dm002_rerun_evidence(study_root)

    manuscript, extra_paths = story_surface.materialize_dm002_external_validation_story_surface(
        paper_root=paper_root,
    )

    assert manuscript
    assert extra_paths
    assert (
        "# A China-derived diabetes mortality score identifies higher-risk adults in NHANES "
        "but requires recalibration for absolute risk estimation"
    ) in manuscript
    assert "The source model was a fixed Cox risk equation derived in the China diabetes cohort" in manuscript
    assert "Cross-population transport is especially relevant for diabetes risk models" in manuscript
    assert "the model still identified higher-risk adults after cross-population transport" in manuscript
    assert (
        "The source model was available as a locked archived risk equation with preserved coefficients "
        "and 5-year baseline survival"
    ) in manuscript
    assert "may support transported higher-risk identification" in manuscript
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert [item["figure_id"] for item in figure_catalog["figures"]] == ["F1", "F2", "F3"]
    assert [item["table_id"] for item in table_catalog["tables"]] == ["T1", "T2", "T3"]


def test_story_repair_executor_uses_study_root_dm002_evidence_for_body_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_story_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    authority_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    _write_dm002_rerun_evidence(study_root)
    _write_json(
        authority_paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "DM002-C1",
                    "statement": "The fixed China-derived score retained risk ranking but underpredicted NHANES absolute mortality.",
                    "status": "supported_with_limitations",
                    "paper_role": "main_text",
                    "evidence_items": [
                        {
                            "item_id": "DM002-C1-performance",
                            "support_level": "primary",
                            "source_paths": [
                                "paper/draft.md",
                                "paper/tables/generated/T2_time_to_event_performance_summary.md",
                            ],
                            "summary": "The external-validation manuscript and performance table report c-index and calibration.",
                        }
                    ],
                }
            ],
        },
    )
    (authority_paper_root / "draft.md").write_text("# Stale DM002 manuscript\n\nBefore repair.\n", encoding="utf-8")
    (authority_paper_root / "build" / "review_manuscript.md").parent.mkdir(parents=True, exist_ok=True)
    (authority_paper_root / "build" / "review_manuscript.md").write_text(
        "# Stale DM002 review manuscript\n\nBefore repair.\n",
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "eval-dm002-current",
            "recommended_actions": [
                {
                    "next_work_unit": {
                        "unit_id": "consume_current_ai_reviewer_record_then_replay_publication_gate",
                        "lane": "write",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "handoff_ready",
            "source_eval_id": "eval-dm002-current",
            "gate_clearing_batch_followthrough": {
                "work_unit_id": "consume_current_ai_reviewer_record_then_replay_publication_gate",
            },
            "source_action": {"blocked_reason": "manuscript_story_surface_delta_missing"},
        },
    )

    result = module.run_story_repair(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
        study_root=study_root,
        source="test",
    )

    assert result["ok"] is True
    assert result["status"] == "progress_delta_candidate"
    assert result["work_unit_id"] == "dm002_same_line_publication_paper_repair"
    changed_paths = {
        Path(ref["path"]).relative_to(authority_paper_root).as_posix()
        for ref in result["changed_artifact_refs"]
        if Path(ref["path"]).is_relative_to(authority_paper_root)
    }
    assert "draft.md" in changed_paths
    assert "build/review_manuscript.md" in changed_paths
    assert "tables/generated/T2_time_to_event_performance_summary.md" in changed_paths
    assert "tables/generated/T3_grouped_calibration.md" in changed_paths
    assert result["repair_execution_evidence"]["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
