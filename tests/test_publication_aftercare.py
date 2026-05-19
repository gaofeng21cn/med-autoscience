from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str = "ref-only fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _populate_ready_aftercare_refs(study_root: Path, quest_root: Path) -> None:
    aris_root = quest_root / "artifacts" / "algorithm_research" / "aris"
    for name in (
        "input_contract.json",
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "prior_limitations.md",
        "why_our_method_can_work.md",
        "claim_to_evidence_map.md",
    ):
        if name.endswith(".json"):
            _write_json(aris_root / name, {"ref": f"aris-ref:{name}"})
        else:
            _write_text(aris_root / name)
    _write_json(aris_root / "sidecar_manifest.json", {"provider": "aris", "status": "result_ready"})
    _write_json(
        study_root / "artifacts" / "analysis_queue" / "latest.json",
        {
            "queue_ref": "analysis-queue:dm002/reviewer-repair",
            "items": [
                {
                    "item_ref": "analysis-queue-item:hdl-harmonization",
                    "state": "ready",
                    "source_refs": ["review-ref:hdl-harmonization"],
                }
            ],
            "reviewer_refs": ["review-ref:hdl-harmonization"],
            "experiment_refs": ["experiment-ref:external-validation-rerun"],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer"},
            "review_refs": ["review-ref:publication-eval"],
            "source_refs": ["paper-ref:current-manuscript"],
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {"review_refs": ["review-ref:ledger"]},
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {"claim_refs": ["claim-ref:main"], "evidence_refs": ["evidence-ref:main"]},
    )


def test_publication_aftercare_plan_projects_aris_analysis_queue_and_reviewer_refresh_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)

    result = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    assert result["surface_kind"] == "mas_publication_aftercare_plan"
    assert result["refs_only"] is True
    assert result["body_included"] is False
    assert result["analysis_queue_entry"]["status"] == "ready"
    assert result["analysis_queue_entry"]["recommended_task_kind"] == (
        "publication_aftercare/analysis-queue-progress"
    )
    assert any("algorithm_research/aris/final_method_proposal.md" in ref for ref in result["analysis_queue_entry"]["research_pipeline_refs"])
    assert any("review_loop_summary.md" in ref for ref in result["analysis_queue_entry"]["auto_review_loop_refs"])
    assert "analysis-queue:dm002/reviewer-repair" in result["analysis_queue_entry"]["experiment_queue_refs"]
    assert result["reviewer_refresh_entry"]["status"] == "ready"
    assert result["reviewer_refresh_entry"]["reviewer_refresh_policy"]["separate_invocation_required"] is True
    assert result["reviewer_refresh_entry"]["recommended_task_kind"] == "publication_aftercare/reviewer-refresh"
    assert result["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert result["runtime_progression_policy"]["quality_gate_bypass_allowed"] is False
    assert result["runtime_progression_policy"]["direct_publication_eval_write_allowed"] is False
    assert "not projected" not in json.dumps(result, ensure_ascii=False)


def test_publication_aftercare_pending_tasks_are_runtime_owner_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)
    projection = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    tasks = module.build_publication_aftercare_pending_tasks(
        profile_name="nfpitnet",
        profile_ref=tmp_path / "profile.local.toml",
        study_id="DM002",
        projection=projection,
    )

    assert [task["task_kind"] for task in tasks] == [
        "publication_aftercare/analysis-queue-progress",
        "publication_aftercare/reviewer-refresh",
    ]
    assert all(task["dispatch_owner"] == "med-autoscience" for task in tasks)
    assert all(task["payload"]["authority_boundary"] == "mas_owner_runtime_progression_only" for task in tasks)
    assert all(task["source_fingerprint"] for task in tasks)
    assert all(ref["body_included"] is False for task in tasks for ref in task["source_refs"])
