from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _work_unit(work_unit_type: str, *, unit_id: str = "unit-1") -> dict[str, object]:
    unit: dict[str, object] = {
        "unit_id": unit_id,
        "work_unit_type": work_unit_type,
        "owner": "quality_repair_batch",
        "callable_surface": "paper_repair_executor.dispatch_repair_work_unit",
        "source_fingerprint": f"sha256:{work_unit_type}",
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "gate_replay_target": "publication_eval/latest.json",
        "target_claim": "The original claim is supported.",
        "repair_instruction": "Use restrained association language and close the review ledger.",
    }
    if work_unit_type == "text_repair":
        unit["canonical_patch"] = {
            "target_text": "The original claim is supported.",
            "replacement_text": "The association is directionally consistent but requires restrained interpretation.",
        }
    return unit


def test_paper_repair_executor_executes_text_repair_on_canonical_sources(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    manuscript = study_root / "paper" / "manuscript.md"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-1"})
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")

    result = module.dispatch_repair_work_unit(
        study_id="001-risk",
        quest_id="quest-001",
        study_root=study_root,
        repair_work_unit=_work_unit("text_repair"),
        apply=True,
    )

    assert result["accepted"] is True
    assert result["execution_status"] == "executed"
    assert result["typed_blocker"] is None
    text = manuscript.read_text(encoding="utf-8")
    assert "restrained interpretation" in text
    assert "Repair note" not in text
    assert result["owner_receipt"]["work_unit_type"] == "text_repair"
    assert result["owner_receipt"]["direct_current_package_write"] is False
    assert result["canonical_artifact_delta"]["meaningful_artifact_delta"] is True
    assert result["repair_execution_evidence"]["progress_delta_candidate"] is True
    assert (study_root / "paper" / "review" / "review_ledger.json").is_file()
    assert (study_root / "paper" / "revision_log.jsonl").is_file()
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_downgrades_claim_and_updates_evidence_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "002-negative"
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")

    result = module.dispatch_repair_work_unit(
        study_id="002-negative",
        quest_id="quest-002",
        study_root=study_root,
        repair_work_unit={
            **_work_unit("claim_downgrade"),
            "claim_policy": {
                "claim_id": "claim.primary",
                "supported": False,
                "allowed_status": "downgraded",
                "reason": "negative_result_cannot_support_original_claim",
            },
        },
        apply=True,
    )

    ledger = json.loads((study_root / "paper" / "evidence_ledger.json").read_text(encoding="utf-8"))
    assert result["execution_status"] == "executed"
    assert ledger["claim_updates"][0]["claim_policy"]["supported"] is False
    assert "downgraded" in manuscript.read_text(encoding="utf-8")
    assert result["repair_execution_evidence"]["canonical_artifact_delta"]["meaningful_artifact_delta"] is True


def test_paper_repair_executor_returns_typed_blocker_for_missing_owner_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")

    result = module.dispatch_repair_work_unit(
        study_id="003-risk",
        quest_id="quest-003",
        study_root=tmp_path / "workspace" / "studies" / "003-risk",
        repair_work_unit=_work_unit("display_rebuild"),
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "owner_callable_surface_missing"
    assert result["owner_receipt"]["blocked_reason"] == "owner_callable_surface_missing"
    assert result["repair_execution_evidence"]["status"] == "blocked"


def test_paper_repair_executor_blocks_unstructured_text_repair(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "003b-risk"
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")
    work_unit = _work_unit("text_repair")
    work_unit.pop("canonical_patch")

    result = module.dispatch_repair_work_unit(
        study_id="003b-risk",
        quest_id="quest-003b",
        study_root=study_root,
        repair_work_unit=work_unit,
        apply=True,
    )

    assert result["accepted"] is False
    assert result["execution_status"] == "blocked"
    assert result["typed_blocker"] == "owner_callable_surface_missing"
    assert manuscript.read_text(encoding="utf-8") == "The original claim is supported.\n"


def test_paper_repair_executor_dry_run_does_not_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "004-dry-run"

    result = module.dispatch_repair_work_unit(
        study_id="004-dry-run",
        quest_id="quest-004",
        study_root=study_root,
        repair_work_unit=_work_unit("text_repair"),
        apply=False,
    )

    assert result["execution_status"] == "dry_run"
    assert result["typed_blocker"] is None
    assert not (study_root / "paper" / "manuscript.md").exists()
    assert not (study_root / "artifacts" / "controller" / "repair_execution_receipts").exists()
