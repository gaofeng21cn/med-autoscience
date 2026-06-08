from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.test_quality_repair_batch_cases.medical_prose_write_repair import (
    _paper_write_supervisor_route_context,
)
from tests.test_quality_repair_batch_cases.dm002_external_validation_table_consistency import (
    _write_dm002_rerun_evidence,
)
from med_autoscience.claim_evidence_alignment import build_claim_evidence_alignment_gate


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_story_repair_executor_consumes_writer_handoff_into_canonical_story_delta(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_story_repair_executor")
    story_surface = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    paper_root = study_root / "paper"
    old_draft = "# Draft\n\nOld manuscript surface.\n"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(old_draft, encoding="utf-8")
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Current manuscript claim is supported by the regenerated story surface.",
                    "status": "supported_with_limitations",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["Results"],
                    "evidence_items": [
                        {
                            "item_id": "C1_story_surface_delta",
                            "support_level": "primary",
                            "source_paths": ["paper/draft.md", "paper/build/review_manuscript.md"],
                            "summary": "Regenerated manuscript story surface supports the current claim wording.",
                        }
                    ],
                }
            ],
        },
    )
    source_eval_path = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "eval-current",
            "recommended_actions": [
                {
                    "next_work_unit": {
                        "unit_id": "medical_prose_write_repair",
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
            "ok": True,
            "source_eval_id": "eval-current",
            "writer_worker_handoff": {
                "next_executable_owner": "write",
                "owner_route": {"work_unit_fingerprint": "fingerprint-current"},
                "source_action": {"blocked_reason": "manuscript_story_surface_delta_missing"},
                "refs": {"source_eval_path": str(source_eval_path)},
            },
            "repair_execution_evidence_path": str(
                study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
            ),
        },
    )

    def fake_materialize(**kwargs: Any) -> list[str]:
        assert kwargs["paper_root"] == paper_root.resolve()
        assert kwargs["work_unit_id"] == "medical_prose_write_repair"
        new_text = "# Current manuscript\n\nStory repair body.\n"
        changed = []
        for relpath in (Path("draft.md"), Path("build/review_manuscript.md")):
            path = paper_root / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path.resolve()))
        return changed

    monkeypatch.setattr(story_surface, "materialize_medical_prose_story_surfaces", fake_materialize)

    result = module.run_story_repair(
        study_id="003-dpcc",
        quest_id="quest-003",
        study_root=study_root,
        source="test",
        route_context=_paper_write_supervisor_route_context(),
    )

    assert result["ok"] is True
    assert result["status"] == "progress_delta_candidate"
    assert result["work_unit_id"] == "medical_prose_write_repair"
    assert "Story repair body" in (paper_root / "draft.md").read_text(encoding="utf-8")
    evidence = json.loads(
        (study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["progress_delta_candidate"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
    assert evidence["ai_reviewer_recheck_done"] is True
    assert not evidence["blockers"]
    review = json.loads((paper_root / "review" / "review_ledger.json").read_text(encoding="utf-8"))
    assert review["reviews_count"] == 1
    assert review["concerns"][0]["status"] == "resolved"
    alignment = build_claim_evidence_alignment_gate(
        study_root=study_root,
        claim_evidence_map_ref="paper/claim_evidence_map.json",
        evidence_ledger_ref="paper/evidence_ledger.json",
    )
    assert alignment["status"] == "ready"
    assert alignment["claim_count"] == 1
    assert alignment["aligned_claim_count"] == 1
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()


def test_story_repair_executor_blocks_without_handoff_or_work_unit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_story_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-current"})

    result = module.run_story_repair(
        study_id="003-dpcc",
        quest_id="quest-003",
        study_root=study_root,
        source="test",
    )

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["typed_blocker"] == "manuscript_story_surface_delta_missing"
    assert result["changed_artifact_refs"] == []


def test_story_repair_executor_accepts_idempotent_dm002_story_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_story_repair_executor")
    story_surface = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.medical_prose_story_surface"
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
    assert extra_paths == [
        str((paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md").resolve())
    ]
    assert "manuscript_story_surface_delta_missing" not in result["repair_execution_evidence"]["blockers"]
