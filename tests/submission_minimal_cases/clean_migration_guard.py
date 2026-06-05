from __future__ import annotations

import importlib
import shutil
from pathlib import Path

from .shared import dump_json, make_paper_workspace, write_text


def _open_bundle_route_context() -> dict[str, object]:
    return {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": [],
            },
            "route_authorization": {
                "authorized": True,
                "paper_write_allowed": True,
                "bundle_build_allowed": True,
                "runtime_recovery_allowed": True,
            },
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
        },
        "controller_route_context": {
            "control_surface": "gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
            "work_unit_id": "submission_minimal_refresh",
            "requires_human_confirmation": False,
        },
    }


def test_create_submission_minimal_package_blocks_pending_clean_paper_authority_cutover(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    study_root = paper_root.parent
    shutil.rmtree(paper_root / "submission_minimal", ignore_errors=True)
    receipt_path = study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "latest.json"
    dump_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_root.name,
        },
    )

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=_open_bundle_route_context(),
    )

    assert result["status"] == "paper_authority_clean_migration_pending"
    assert result["blocked_reason"] == "paper_authority_clean_migration_required"
    assert result["next_owner"] == "ai_reviewer"
    assert result["paper_authority_cutover_ref"] == str(receipt_path)
    assert not (paper_root / "submission_minimal").exists()


def test_create_submission_minimal_package_blocks_pending_cutover_for_runtime_paper_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_paper_root = make_paper_workspace(tmp_path / "source")
    workspace_root = tmp_path / "runtime-workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-002"
    study_root = workspace_root / "studies" / study_id
    paper_root = (
        workspace_root
        / "runtime"
        / "quests"
        / quest_id
        / ".ds"
        / "worktrees"
        / "paper-run-002"
        / "paper"
    )
    shutil.copytree(source_paper_root, paper_root)
    write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    write_text(
        paper_root.parent / "quest.yaml",
        f"quest_id: {quest_id}\nruntime_reentry_gate:\n  study_id: {study_id}\n",
    )
    shutil.rmtree(paper_root / "submission_minimal", ignore_errors=True)
    receipt_path = study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "latest.json"
    dump_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=_open_bundle_route_context(),
    )

    assert result["status"] == "paper_authority_clean_migration_pending"
    assert result["paper_authority_cutover_ref"] == str(receipt_path)
    assert not (paper_root / "submission_minimal").exists()
