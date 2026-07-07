from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile

import pytest
from pypdf import PdfWriter

from med_autoscience.controllers import study_truth_kernel
from med_autoscience.controllers.submission_minimal_parts import package_builder
from med_autoscience.controllers.submission_minimal_parts.package_builder import (
    create_submission_minimal_package,
)
from med_autoscience.runtime_status_summary import (
    build_runtime_status_summary,
    materialize_runtime_status_summary,
)
from tests.submission_minimal_cases.package_core_and_authority import (
    make_paper_workspace,
    remove_authority_snapshots,
)
from tests.test_study_delivery_sync_cases.shared import make_delivery_workspace
from med_autoscience.controllers.study_delivery_sync_parts.delivery_descriptions import (
    _submission_source_relative_paths,
    _submission_source_signature,
)
from med_autoscience.controllers.study_delivery_sync_parts.sync_orchestration import (
    sync_study_delivery,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_pdf_bytes() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return output.getvalue()


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()


def _write_placeholder_export(
    *,
    output_docx_path: Path | None = None,
    output_pdf_path: Path | None = None,
    **_: Any,
) -> None:
    output_path = output_docx_path or output_pdf_path
    assert output_path is not None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_pdf_path is not None:
        output_path.write_bytes(_minimal_pdf_bytes())
    else:
        output_path.write_bytes(b"test export placeholder")


def _write_runtime_authority_snapshots(
    study_root: Path,
    *,
    blocking_reasons: list[str] | None = None,
) -> None:
    _write_json(
        study_root / "artifacts" / "truth" / "latest.json",
        {
            "surface": "study_truth_snapshot",
            "study_id": study_root.name,
            "truth_epoch": "truth-1",
            "canonical_next_action": "resume_same_study_line",
            "allowed_controller_actions": ["direct_study_execution", "direct_paper_line_write"],
            "blocking_reasons": list(blocking_reasons or []),
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "surface": "runtime_health_snapshot",
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "runtime_health_epoch": "runtime-1",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
    )


def _snapshot(
    *,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "surface": "authority_snapshot",
        "control_state": "ready",
        "canonical_next_action": "continue_bundle_stage",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {
            "state": "open",
            "blocking_reasons": [],
        },
        "route_authorization": {
            "authorized": paper_write_allowed and bundle_build_allowed,
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": True,
        },
    }


def test_submission_minimal_without_snapshot_is_blocked_before_writing(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    remove_authority_snapshots(paper_root.parent)
    submission_root = paper_root / "submission_minimal"
    _remove_tree(submission_root)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert "authority_snapshot_missing" in result["authority_route_gate"]["blocking_reasons"]
    assert result["authority_route_gate"]["allowed"] is False
    assert result["submission_materialization_status"] == {
        "package_role": "audit_source_package",
        "can_submit": False,
        "quality_gate_status": "blocked",
        "known_blockers": ["authority_snapshot_missing"],
    }
    assert (submission_root / "audit" / "submission_manifest.json").exists()


def test_projection_only_submission_minimal_does_not_materialize(tmp_path: Path) -> None:
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"
    _remove_tree(submission_root)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context={"projection_only": True, "paths": [submission_root]},
    )

    assert result["status"] == "authority_route_blocked"
    assert "projection_only_write_blocked" in result["authority_route_gate"]["blocking_reasons"]
    assert not submission_root.exists()


def test_delivery_sync_without_snapshot_still_writes_non_submit_current_package(tmp_path: Path) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is False
    assert "authority_snapshot_missing" in result["submission_authority_gate"]["blocking_reasons"]
    assert (study_root / "submission").exists()
    assert (study_root / "submission.zip").exists()


def test_submission_minimal_derives_snapshot_from_study_authority_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        paper_root.parent,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )

    monkeypatch.setattr(package_builder, "export_docx", _write_placeholder_export)
    monkeypatch.setattr(package_builder, "export_pdf", _write_placeholder_export)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["route_authorization_flag"] == "paper_write_allowed"
    assert result["authority_route_gate"]["snapshot_ref"]["study_truth_epoch"] == "truth-1"
    assert "authority_snapshot_missing" not in result["authority_route_gate"]["blocking_reasons"]
    assert (paper_root / "submission_minimal" / "audit" / "submission_manifest.json").exists()


def test_delivery_sync_derives_snapshot_but_does_not_require_bundle_gate_for_current_package(tmp_path: Path) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert "authority_snapshot_missing" not in result["authority_route_gate"]["blocking_reasons"]
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is False
    assert "bundle_build_allowed_false" in result["submission_authority_gate"]["blocking_reasons"]
    assert (study_root / "submission").exists()


def test_delivery_sync_derives_snapshot_from_current_projection_surfaces_when_latest_files_are_stale(
    tmp_path: Path,
) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    study_truth_kernel.append_truth_event(
        study_root=study_root,
        study_id=study_root.name,
        event_type="opl_runtime_owner_handoff",
        payload={
            "publication_supervisor_state": {"bundle_tasks_downstream_only": True},
        },
        recorded_at="2026-07-07T08:00:00+00:00",
    )
    study_truth_kernel.append_truth_event(
        study_root=study_root,
        study_id=study_root.name,
        event_type="submission_authority_closeout",
        payload={
            "intervention_intent": "submission_authority_closeout",
            "submission_authority_closeout": {
                "status": "submission_ready_authority_closeout_recorded",
                "authority_materialized": True,
            },
        },
        recorded_at="2026-07-07T08:05:00+00:00",
    )
    study_truth_kernel.materialize_truth_snapshot(study_root=study_root, study_id=study_root.name)
    materialize_runtime_status_summary(
        study_root=study_root,
        summary=build_runtime_status_summary(
            study_id=study_root.name,
            quest_id=study_root.name,
            generated_at="2026-07-07T08:10:00+00:00",
            runtime_status_ref=str(
                study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
            ),
            runtime_artifact_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            runtime_escalation_record_ref=None,
            runtime_readback_report_ref=None,
            health_status="unknown",
            runtime_decision="create_and_start",
            runtime_reason="quest_missing",
            recovery_action_mode="inspect_progress",
            supervisor_tick_status="not_required",
            current_required_action=None,
            controller_stage_note=None,
            status_summary="Runtime is not live.",
            next_action_summary="Use current projection surfaces for authority routing.",
            needs_human_intervention=False,
        ),
    )
    _write_json(
        study_root.parent.parent
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": study_root.name,
            "quest_status": "waiting_for_user",
            "active_run_id": None,
        },
    )
    (study_root / "artifacts" / "runtime" / "health" / "latest.json").unlink(missing_ok=True)

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is True
    assert "authority_snapshot_missing" not in result["submission_authority_gate"]["blocking_reasons"]
    assert "bundle_build_allowed_false" not in result["submission_authority_gate"]["blocking_reasons"]
    assert result["package_kind"] == "submission_ready_package"
    assert result["can_submit"] is True


def test_submission_ready_delivery_uses_v2_submission_audit_evidence_when_paper_root_ledger_is_missing(
    tmp_path: Path,
) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    source_root = study_root / "submission"
    shutil.copytree(paper_root / "submission_minimal", source_root)
    _write_json(
        source_root / "audit" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C-v2",
                    "status": "supported",
                    "evidence": [{"evidence_id": "EV-v2"}],
                }
            ],
        },
    )
    _write_json(source_root / "figure_visual_audit_receipt.json", {"schema_version": 1, "status": "clear"})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::v2-source",
        },
    )
    (paper_root / "evidence_ledger.json").unlink()

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile="general_medical_journal",
        authority_route_context={"authority_snapshot": _snapshot()},
    )

    assert result["package_kind"] == "submission_ready_package"
    assert result["can_submit"] is True
    assert result["current_package_freshness_proof"]["status"] == "fresh"
    assert result["charter_contract_linkage"]["ledger_linkages"]["evidence_ledger"]["status"] == "linked"
    assert result["charter_contract_linkage"]["ledger_linkages"]["review_ledger"]["status"] == "linked"
    assert (study_root / "manuscript" / "audit" / "evidence_ledger.json").exists()
    assert (study_root / "manuscript" / "audit" / "review_ledger.json").exists()
    assert (study_root / "manuscript" / "current_package" / "audit" / "evidence_ledger.json").exists()
    assert (study_root / "manuscript" / "current_package" / "audit" / "review_ledger.json").exists()
    assert (
        study_root / "manuscript" / "current_package" / "figure_visual_audit_receipt.json"
    ).stat().st_mtime_ns >= (study_root / "manuscript" / "current_package" / "paper.pdf").stat().st_mtime_ns
    assert (study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json").exists()
    assert (
        study_root
        / "manuscript"
        / "journal_package_mirrors"
        / "general_medical_journal"
        / "audit"
        / "evidence_ledger.json"
    ).exists()


def test_submission_ready_delivery_refreshes_legacy_submission_zip(tmp_path: Path) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    source_root = study_root / "submission"
    shutil.copytree(paper_root / "submission_minimal", source_root)
    (source_root / "manuscript_submission.md").write_text(
        "Fresh recorded care-review gap wording.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(study_root / "submission.zip", "w") as archive:
        archive.writestr("manuscript_submission.md", "stale mismatch treatment-gap wording\n")

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile="general_medical_journal",
        authority_route_context={"authority_snapshot": _snapshot()},
    )

    assert result["package_kind"] == "submission_ready_package"
    assert result["can_submit"] is True
    with zipfile.ZipFile(study_root / "submission.zip") as archive:
        assert archive.read("manuscript_submission.md").decode("utf-8") == (
            "Fresh recorded care-review gap wording.\n"
        )
        assert "audit/submission_manifest.json" in archive.namelist()


def test_delivery_sync_adopts_current_runtime_gate_clear_for_bundle_route(tmp_path: Path) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=[
            "publication_supervisor_state.bundle_tasks_downstream_only",
            "runtime_recovery_retry_budget_exhausted",
        ],
    )
    source_root = paper_root / "submission_minimal"
    source_signature = _submission_source_signature(
        paper_root=paper_root,
        source_root=source_root,
        relative_paths=_submission_source_relative_paths(paper_root=paper_root, source_root=source_root),
    )
    quest_root = study_root.parent.parent / "runtime" / "quests" / study_root.name
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(
        f"quest_id: {study_root.name}\nruntime_reentry_gate:\n  study_id: {study_root.name}\n",
        encoding="utf-8",
    )
    gate_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(
            {
                "status": "clear",
                "blockers": [],
                "bundle_tasks_downstream_only": False,
                "authority_source_signature": source_signature,
                "paper_root": str(paper_root),
                "latest_gate_path": str(gate_path),
                "gate_fingerprint": "gate::clear",
                "work_unit_fingerprint": "work-unit::submission-minimal",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "submission_ready_package"
    assert result["can_submit"] is True
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["controller_route_gate"]["action_family"] == (
        "paper.package.submission_minimal"
    )
    assert result["submission_authority_gate"]["controller_route_gate"]["work_unit_id"] == (
        "submission_minimal_refresh"
    )
    assert "bundle_build_allowed_false" not in result["submission_authority_gate"]["blocking_reasons"]


def test_delivery_sync_does_not_adopt_gate_clear_with_stale_source_signature(tmp_path: Path) -> None:
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )
    quest_root = study_root.parent.parent / "runtime" / "quests" / study_root.name
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(
        f"quest_id: {study_root.name}\nruntime_reentry_gate:\n  study_id: {study_root.name}\n",
        encoding="utf-8",
    )
    gate_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(
            {
                "status": "clear",
                "blockers": [],
                "bundle_tasks_downstream_only": False,
                "authority_source_signature": "source::stale",
                "latest_gate_path": str(gate_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert result["submission_authority_gate"]["allowed"] is False
    assert "bundle_build_allowed_false" in result["submission_authority_gate"]["blocking_reasons"]


def test_fresh_snapshot_authorizes_submission_minimal_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    monkeypatch.setattr(package_builder, "export_docx", _write_placeholder_export)
    monkeypatch.setattr(package_builder, "export_pdf", _write_placeholder_export)

    result = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        authority_route_context={"authority_snapshot": _snapshot(paper_write_allowed=True)},
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert (paper_root / "submission_minimal" / "audit" / "submission_manifest.json").exists()
