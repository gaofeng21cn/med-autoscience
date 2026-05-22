from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_quality_repair_batch_evidence_does_not_treat_canonical_story_surface_refs_as_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Clean external validation manuscript story.\n", encoding="utf-8")
    review_manuscript.write_text("Clean review manuscript story.\n", encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_record = _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"schema_version": 1},
    )
    gate_report = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": "publication-eval::002::latest"},
    )
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_from_quality_repair_batch_result(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        source_eval_id="publication-eval::002::latest",
        source_eval_artifact_path=str(gate_report),
        source_summary_id="quality-summary::002",
        source_summary_artifact_path=str(
            _write_json(study_root / "artifacts" / "quality" / "summary.json", {"summary_id": "quality-summary::002"})
        ),
        gate_clearing_result={
            "ok": True,
            "status": "executed",
            "record_path": str(gate_record),
            "selected_publication_work_unit": {
                "unit_id": "manuscript_story_repair",
                "owner": "quality_repair_batch",
                "gate_replay_target": "publication_gate",
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(gate_report),
            },
            "unit_results": [
                {
                    "unit_id": "manuscript_story_repair",
                    "status": "updated",
                    "result": {
                        "changed_artifact_refs": [
                            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
                            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                            {"path": str(review_ledger), "artifact_role": "review_ledger"},
                        ],
                        "canonical_artifact_refs": [
                            str(draft),
                            str(review_manuscript),
                            str(claim_map),
                            str(evidence_ledger),
                            str(review_ledger),
                        ],
                    },
                }
            ],
        },
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    changed_paths = {Path(ref["path"]).resolve() for ref in evidence["changed_artifact_refs"]}
    assert draft.resolve() not in changed_paths
    assert review_manuscript.resolve() not in changed_paths
    assert evidence["manuscript_surface_hygiene"]["status"] == "blocked"
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is False
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
    assert evidence["ai_reviewer_recheck_request_ref"] == str(ai_request.resolve())
