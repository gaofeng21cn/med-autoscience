from __future__ import annotations

import importlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ready_recommendation_payload() -> dict[str, object]:
    return {
        "requires_algorithmic_innovation": True,
        "task_definition_ready": True,
        "data_contract_frozen": True,
        "evaluation_contract_ready": True,
        "compute_budget_available": True,
        "baseline_available": True,
        "reference_paper_available": False,
        "base_repo_available": False,
    }


def full_input_contract() -> dict[str, object]:
    return {
        "problem_anchor": {
            "clinical_question": "Predict early recurrence from CT and pathology.",
            "research_object": "Resected NSCLC cohort",
            "endpoint": "two_year_recurrence",
            "task_type": "multimodal_classifier",
        },
        "data_contract": {
            "dataset_version": "v2026-03-29",
            "modalities": ["ct", "wsi", "ehr"],
            "splits": {"train": "train.csv", "val": "val.csv", "test": "test.csv"},
            "external_validation_required": True,
            "preprocessing_boundary": "locked_v1",
        },
        "evaluation_contract": {
            "primary_metric": "auroc",
            "secondary_metrics": ["auprc", "brier"],
            "required_baselines": ["late_fusion", "clinical_only"],
            "statistics": ["bootstrap_ci"],
            "compute_budget": {"gpu_hours": 48},
        },
        "innovation_scope": {
            "allowed": ["algorithm_design", "fusion_module", "training_strategy"],
            "forbidden": ["endpoint_redefinition", "cohort_redefinition"],
        },
        "writing_questions": [
            "Why do previous methods fail on this task?",
            "What is the core bottleneck for multimodal fusion here?",
            "Why can our method solve this bottleneck?",
            "Which experiments prove the innovation is necessary?",
        ],
        "optional_context": {
            "reference_paper": "arxiv:2401.00001",
            "base_repo": "https://github.com/example/project",
            "failed_attempts": ["plain_concat_underfit"],
        },
    }


def provision_payload() -> dict[str, object]:
    payload = full_input_contract()
    payload["user_confirmation"] = {
        "confirmed": True,
        "confirmed_by": "human",
        "confirmed_at": "2026-03-29T12:00:00+00:00",
    }
    return payload


def populate_handoff(sidecar_root: Path, *, manifest: dict[str, object], aligned_claim_map: bool = True) -> None:
    handoff_root = sidecar_root / "handoff"
    for name in (
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "prior_limitations.md",
        "why_our_method_can_work.md",
    ):
        write_text(handoff_root / name, f"# {name}\n")
    if aligned_claim_map:
        write_text(
            handoff_root / "claim_to_evidence_map.md",
            """---
claim_evidence_pairs:
  - claim_id: claim-1
    evidence_artifacts:
      - experiment_results_summary.md
  - claim_id: claim-2
    evidence_artifacts:
      - review_loop_summary.md
---
# Claim To Evidence Map
""",
        )
    else:
        write_text(
            handoff_root / "claim_to_evidence_map.md",
            """---
claim_evidence_pairs:
  - claim_id: claim-1
    evidence_artifacts:
      - missing_results.md
---
# Claim To Evidence Map
""",
        )
    write_text(
        handoff_root / "sidecar_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )


def test_recommend_aris_sidecar_returns_recommended_when_algorithm_route_is_ready(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    result = module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )

    assert result["status"] == "recommended"
    assert result["recommendation"] == "request_user_confirmation"
    assert result["blockers"] == []
    recommendation = load_json(quest_root / "sidecars" / "aris" / "recommendation.json")
    assert recommendation["status"] == "awaiting_user_confirmation"


def test_recommend_aris_sidecar_returns_not_candidate_with_blockers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    result = module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload={
            "requires_algorithmic_innovation": False,
            "task_definition_ready": False,
            "data_contract_frozen": True,
            "evaluation_contract_ready": False,
            "compute_budget_available": False,
            "baseline_available": False,
            "reference_paper_available": False,
            "base_repo_available": False,
        },
    )

    assert result["status"] == "not_candidate"
    assert "algorithmic_innovation_not_required" in result["blockers"]
    assert "task_definition_not_ready" in result["blockers"]
    assert "evaluation_contract_not_ready" in result["blockers"]
    assert "compute_budget_unavailable" in result["blockers"]
    assert "no_baseline_or_reference_context" in result["blockers"]


def test_provision_aris_sidecar_writes_frozen_contract_and_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )

    result = module.provision_aris_sidecar(
        quest_root=quest_root,
        payload=provision_payload(),
    )

    sidecar_root = quest_root / "sidecars" / "aris"
    state = load_json(sidecar_root / "sidecar_state.json")
    contract = load_json(sidecar_root / "input_contract.json")

    assert result["status"] == "contract_frozen"
    assert result["sidecar_root"] == str(sidecar_root)
    assert contract["problem_anchor"]["task_type"] == "multimodal_classifier"
    assert state["provider"] == "aris"
    assert state["status"] == "contract_frozen"
    assert (sidecar_root / "handoff").is_dir()


def test_provision_aris_sidecar_rejects_contract_drift(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )
    payload = provision_payload()
    module.provision_aris_sidecar(quest_root=quest_root, payload=payload)

    drifted_payload = provision_payload()
    drifted_payload["evaluation_contract"]["primary_metric"] = "dice"

    try:
        module.provision_aris_sidecar(quest_root=quest_root, payload=drifted_payload)
    except ValueError as exc:
        assert "contract drift" in str(exc)
    else:
        raise AssertionError("Expected ValueError for ARIS sidecar contract drift")


def test_provision_aris_sidecar_requires_confirmed_user_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    try:
        module.provision_aris_sidecar(quest_root=quest_root, payload=provision_payload())
    except ValueError as exc:
        assert "awaiting_user_confirmation" in str(exc)
    else:
        raise AssertionError("Expected ValueError when provisioning without a recorded recommendation gate")

    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )
    unconfirmed_payload = full_input_contract()
    try:
        module.provision_aris_sidecar(quest_root=quest_root, payload=unconfirmed_payload)
    except ValueError as exc:
        assert "user_confirmation" in str(exc)
    else:
        raise AssertionError("Expected ValueError when provisioning without explicit user confirmation")


def test_import_aris_sidecar_result_copies_handoff_artifacts_to_audit_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )
    provision = module.provision_aris_sidecar(quest_root=quest_root, payload=provision_payload())
    sidecar_root = Path(provision["sidecar_root"])
    manifest = {
        "schema_version": 1,
        "sidecar_id": "aris",
        "provider": "aris",
        "status": "result_ready",
        "input_contract_hash": provision["input_contract_hash"],
        "selected_method_id": "fusionformer_v1",
        "primary_metric": "auroc",
        "best_result": {"value": 0.912, "split": "test"},
        "artifacts_generated": [
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
        ],
    }
    populate_handoff(sidecar_root, manifest=manifest)

    result = module.import_aris_sidecar_result(quest_root=quest_root)

    artifact_root = quest_root / "artifacts" / "algorithm_research" / "aris"
    imported_manifest = load_json(artifact_root / "sidecar_manifest.json")
    assert result["status"] == "imported"
    assert (artifact_root / "input_contract.json").exists()
    assert (artifact_root / "claim_to_evidence_map.md").exists()
    assert imported_manifest["provider"] == "aris"
    assert imported_manifest["input_contract_hash"] == provision["input_contract_hash"]


def test_import_aris_sidecar_result_rejects_manifest_without_aligned_claim_evidence_pairs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )
    provision = module.provision_aris_sidecar(quest_root=quest_root, payload=provision_payload())
    sidecar_root = Path(provision["sidecar_root"])
    manifest = {
        "schema_version": 1,
        "sidecar_id": "aris",
        "provider": "aris",
        "status": "result_ready",
        "input_contract_hash": provision["input_contract_hash"],
        "selected_method_id": "fusionformer_v1",
        "primary_metric": "auroc",
        "best_result": {"value": 0.912, "split": "test"},
        "artifacts_generated": [
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
        ],
    }
    populate_handoff(sidecar_root, manifest=manifest, aligned_claim_map=False)

    try:
        module.import_aris_sidecar_result(quest_root=quest_root)
    except ValueError as exc:
        assert "claim_to_evidence_map" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unaligned claim_evidence_pairs")


def test_resolve_aris_sidecar_artifacts_reads_only_imported_audit_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.aris_sidecar")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    module.recommend_aris_sidecar(
        quest_root=quest_root,
        payload=ready_recommendation_payload(),
    )
    provision = module.provision_aris_sidecar(quest_root=quest_root, payload=provision_payload())
    sidecar_root = Path(provision["sidecar_root"])
    manifest = {
        "schema_version": 1,
        "sidecar_id": "aris",
        "provider": "aris",
        "status": "result_ready",
        "input_contract_hash": provision["input_contract_hash"],
        "selected_method_id": "fusionformer_v1",
        "primary_metric": "auroc",
        "best_result": {"value": 0.912, "split": "test"},
        "artifacts_generated": [
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
        ],
    }
    populate_handoff(sidecar_root, manifest=manifest)
    module.import_aris_sidecar_result(quest_root=quest_root)

    write_text(sidecar_root / "handoff" / "final_method_proposal.md", "# stale sidecar draft\n")
    resolved = module.resolve_aris_sidecar_artifacts(quest_root=quest_root)

    assert resolved["status"] == "imported"
    assert resolved["artifacts"]["final_method_proposal.md"].endswith(
        "artifacts/algorithm_research/aris/final_method_proposal.md"
    )
