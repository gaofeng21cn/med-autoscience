from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _opl_auth(label: str = "test") -> dict[str, object]:
    return {
        "owner": "one-person-lab",
        "stage_attempt_id": f"stage-attempt::{label}",
        "lease_id": f"lease::{label}",
    }


def test_canonical_manuscript_package_loop_writes_rebuild_and_freshness_proofs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_manuscript_package_loop")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    manuscript = _write(study_root / "paper" / "manuscript.md", "## Discussion\nRestrained clinical interpretation.\n")
    evidence = _write(study_root / "paper" / "evidence_ledger.json", '{"schema_version":1}\n')
    review = _write(study_root / "paper" / "review" / "review_ledger.json", '{"schema_version":1}\n')

    result = module.materialize_canonical_package_loop_proofs(
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        source_refs=[manuscript, evidence, review],
    )

    assert result["surface"] == "canonical_manuscript_package_loop"
    assert result["status"] == "ready_for_controller_authorized_package_refresh"
    assert result["current_package_write_authorized"] is False
    assert result["manuscript_native_prose_gate"]["status"] == "passed"
    assert result["current_package_freshness_proof"]["freshness_state"] == "controller_rebuild_required"
    assert result["delivery_manifest"]["source_refs"] == [str(manuscript), str(evidence), str(review)]
    assert Path(result["rebuild_proof_ref"]).is_file()
    assert Path(result["current_package_freshness_proof_ref"]).is_file()
    assert Path(result["delivery_manifest_ref"]).is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_canonical_manuscript_package_loop_blocks_controller_prose_in_manuscript(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.canonical_manuscript_package_loop")
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    manuscript = _write(study_root / "paper" / "manuscript.md", "Reviewer-facing label: TODO fix package anchor.\n")

    result = module.materialize_canonical_package_loop_proofs(
        study_root=study_root,
        study_id="002-risk",
        quest_id="quest-002",
        source_refs=[manuscript],
    )

    assert result["status"] == "blocked"
    assert result["manuscript_native_prose_gate"]["status"] == "blocked"
    assert set(result["manuscript_native_prose_gate"]["blockers"]) == {
        "author_todo_or_placeholder_in_manuscript",
        "package_anchor_in_manuscript",
        "reviewer_facing_label_in_manuscript",
    }
    assert result["current_package_write_authorized"] is False
    assert not (study_root / "manuscript" / "current_package").exists()


def test_paper_repair_executor_attaches_canonical_package_loop_proof(tmp_path: Path) -> None:
    repair = importlib.import_module("med_autoscience.controllers.paper_repair_executor")
    study_root = tmp_path / "workspace" / "studies" / "003-risk"
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")

    result = repair.dispatch_repair_work_unit(
        study_id="003-risk",
        quest_id="quest-003",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "unit-3",
            "work_unit_type": "claim_downgrade",
            "source_refs": ["artifacts/publication_eval/latest.json"],
            "claim_policy": {"claim_id": "claim.primary", "supported": False, "allowed_status": "downgraded"},
        },
        opl_execution_authorization=_opl_auth("canonical-package-loop"),
        apply=True,
    )

    package_loop = result["canonical_package_loop"]
    assert package_loop["status"] == "ready_for_controller_authorized_package_refresh"
    assert Path(package_loop["current_package_freshness_proof_ref"]).is_file()
    assert json.loads(Path(package_loop["delivery_manifest_ref"]).read_text(encoding="utf-8"))["source_kind"] == (
        "canonical_manuscript_package_loop"
    )
