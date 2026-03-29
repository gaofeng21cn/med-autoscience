from __future__ import annotations

import importlib
from pathlib import Path


def test_sidecar_layout_roots_are_derived_from_quest_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    assert module.sidecar_root(quest_root) == quest_root / "sidecars" / "aris"
    assert module.handoff_root(quest_root) == quest_root / "sidecars" / "aris" / "handoff"
    assert module.artifact_root(quest_root) == quest_root / "artifacts" / "algorithm_research" / "aris"


def test_contract_hash_is_stable_for_same_payload() -> None:
    module = importlib.import_module("med_autoscience.adapters.aris_sidecar")
    payload = {
        "problem_anchor": {
            "clinical_question": "Predict recurrence.",
            "research_object": "Post-operative cohort",
            "endpoint": "two_year_recurrence",
            "task_type": "multimodal_classifier",
        },
        "data_contract": {"dataset_version": "v2026-03-29", "modalities": ["ct", "ehr"], "splits": "locked"},
    }

    assert module.build_contract_hash(payload) == module.build_contract_hash(payload)


def test_required_handoff_files_are_complete() -> None:
    module = importlib.import_module("med_autoscience.adapters.aris_sidecar")

    assert module.required_handoff_files() == (
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "prior_limitations.md",
        "why_our_method_can_work.md",
        "claim_to_evidence_map.md",
        "sidecar_manifest.json",
    )
