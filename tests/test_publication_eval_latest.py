from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.publication_eval_latest"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_payload(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "results" / "main_result.json"),
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                ],
                "requires_controller_decision": True,
            }
        ],
    }


def test_resolve_publication_eval_latest_ref_defaults_to_eval_owned_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_publication_eval_latest_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "publication_eval" / "latest.json").resolve()


def test_read_publication_eval_latest_reads_typed_latest_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved == payload


def test_resolve_publication_eval_latest_ref_rejects_med_deepscientist_runtime_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    runtime_ref = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=runtime_ref)


def test_resolve_publication_eval_latest_ref_rejects_cross_repo_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "repo-a" / "studies" / "001-risk"
    cross_repo_ref = tmp_path / "repo-b" / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=cross_repo_ref)


def test_read_publication_eval_latest_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_publication_eval_latest(study_root=study_root)
