from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch import _write_blocked_publication_eval, _write_quality_summary


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_missing_canonical_delta_blocks_meaningful_artifact_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "001-risk"
    source_ref = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-1"})
    revision_log = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})

    evidence = module.build_repair_execution_evidence(
        study_id="001-risk",
        quest_id="quest-001",
        study_root=study_root,
        repair_work_unit={"unit_id": "manuscript_story_repair", "gate_replay_target": "publication_gate"},
        review_finding={"finding_id": "gap-001", "severity": "must_fix"},
        source_refs=[str(source_ref)],
        changed_artifact_refs=[],
        revision_log_ref=str(revision_log),
    )

    assert evidence["surface"] == "repair_execution_evidence"
    assert evidence["status"] == "blocked"
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert evidence["canonical_artifact_delta"]["status"] == "missing"
    assert evidence["changed_artifact_refs"] == []
    assert evidence["gate_replay_required"] is False
    assert evidence["ai_reviewer_recheck_required"] is False
    assert "canonical_artifact_delta_missing" in evidence["blockers"]
    assert evidence["quality_authorized"] is False
    assert evidence["submission_authorized"] is False
    assert evidence["current_package_write_authorized"] is False


def test_delta_with_gate_replay_projects_progress_delta_candidate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "003-dpcc"
    draft = (study_root / "paper" / "draft.md")
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Updated manuscript story.\n", encoding="utf-8")
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-2"})
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::003"},
    )

    evidence = module.build_repair_execution_evidence(
        study_id="003-dpcc",
        quest_id="quest-003",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "manuscript_story_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"finding_id": "reviewer-first-concern", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[{"path": "paper/draft.md", "artifact_role": "canonical_manuscript"}],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        ai_reviewer_recheck_request_ref=str(ai_request),
    )

    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is True
    assert evidence["changed_artifact_refs"][0]["path"] == str(draft.resolve())
    assert evidence["revision_log_ref"] == str(review_ledger.resolve())
    assert evidence["evidence_ledger_update_required"] is True
    assert evidence["evidence_ledger_update_done"] is True
    assert evidence["review_ledger_update_required"] is True
    assert evidence["review_ledger_update_done"] is True
    assert evidence["gate_replay_target"] == "publication_gate"
    assert evidence["gate_replay_required"] is True
    assert evidence["gate_replay_done"] is True
    assert evidence["ai_reviewer_recheck_required"] is True
    assert evidence["ai_reviewer_recheck_done"] is True
    assert evidence["progress_delta_candidate"] is True
    assert evidence["quality_authorized"] is False
    assert evidence["submission_authorized"] is False
    assert evidence["blockers"] == []
    assert evidence["idempotency_key"].startswith("paper-repair-execution::003-dpcc::quest-003::")
    assert evidence["source_fingerprint"].startswith("sha256:")


def test_manuscript_story_repair_with_invalid_analysis_history_residue_cannot_claim_progress(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "The raw-scale sensitivity check remained a unit-harmonization lesson.\n",
        encoding="utf-8",
    )
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-2"})
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_repair_execution_evidence(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "manuscript_story_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"finding_id": "medical-prose", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[{"path": str(claim_map), "artifact_role": "claim_evidence_map"}],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        ai_reviewer_recheck_request_ref=str(ai_request),
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert evidence["canonical_artifact_delta"]["status"] == "blocked"
    assert "invalid_analysis_history_residue_present" in evidence["blockers"]
    hygiene = evidence["manuscript_surface_hygiene"]
    assert hygiene["required"] is True
    assert hygiene["status"] == "blocked"
    assert hygiene["hits"][0]["pattern_id"] == "invalid_analysis_history_residue"
    assert hygiene["hits"][0]["path"] == str(draft.resolve())


def test_analysis_claim_evidence_repair_with_invalid_analysis_history_residue_cannot_claim_progress(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "An earlier raw-scale application used incompatible high-density lipoprotein cholesterol units "
        "and is treated only as preprocessing-error provenance.\n",
        encoding="utf-8",
    )
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-2"})
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_repair_execution_evidence(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"finding_id": "claim-evidence", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[{"path": str(claim_map), "artifact_role": "claim_evidence_map"}],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        ai_reviewer_recheck_request_ref=str(ai_request),
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert evidence["canonical_artifact_delta"]["status"] == "blocked"
    assert "invalid_analysis_history_residue_present" in evidence["blockers"]
    hygiene = evidence["manuscript_surface_hygiene"]
    assert hygiene["required"] is True
    assert hygiene["status"] == "blocked"
    assert hygiene["hits"][0]["pattern_id"] == "invalid_analysis_history_residue"
    assert hygiene["hits"][0]["path"] == str(draft.resolve())


def test_current_package_delta_and_quality_override_are_not_accepted(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "004-obesity"
    current_package_file = study_root / "manuscript" / "current_package" / "draft.docx"
    current_package_file.parent.mkdir(parents=True, exist_ok=True)
    current_package_file.write_bytes(b"derived package")

    evidence = module.build_repair_execution_evidence(
        study_id="004-obesity",
        quest_id="quest-004",
        study_root=study_root,
        repair_work_unit={"unit_id": "current_package_patch", "gate_replay_target": "publication_gate"},
        review_finding={"finding_id": "gap-004"},
        source_refs=[],
        changed_artifact_refs=[{"path": str(current_package_file)}],
        authority_claims={
            "quality_authorized": True,
            "submission_authorized": True,
            "current_package_write_authorized": True,
        },
    )

    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert evidence["changed_artifact_refs"] == []
    assert evidence["excluded_artifact_refs"][0]["path"] == str(current_package_file.resolve())
    assert "current_package_ref_not_canonical_delta" in evidence["blockers"]
    assert "quality_override_not_allowed" in evidence["blockers"]
    assert "submission_override_not_allowed" in evidence["blockers"]
    assert "current_package_write_not_allowed" in evidence["blockers"]
    assert evidence["quality_authorized"] is False
    assert evidence["submission_authorized"] is False
    assert evidence["current_package_write_authorized"] is False


def test_publication_gate_replay_delivery_progress_is_not_canonical_paper_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    gate_record = _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"schema_version": 1},
    )
    gate_report = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": "publication-eval::002::latest"},
    )
    freshness = _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "fresh"},
    )
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_root.mkdir(parents=True, exist_ok=True)

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
                "unit_id": "publication_gate_replay",
                "gate_replay_target": "publication_gate",
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(gate_report),
            },
            "current_package_freshness_proof": {
                "status": "fresh",
                "proof_path": str(freshness),
            },
            "unit_results": [
                {
                    "unit_id": "sync_submission_minimal_delivery",
                    "status": "synced",
                    "result": {"current_package_root": str(current_package_root)},
                }
            ],
        },
    )

    assert evidence["status"] == "controller_progress_delta_candidate"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert evidence["changed_artifact_refs"] == []
    assert evidence["controller_progress_delta_candidate"] is True
    assert evidence["controller_progress_delta"]["status"] == "fresh"
    assert str(freshness.resolve()) in evidence["controller_progress_delta"]["artifact_refs"]
    assert str(gate_record.resolve()) in evidence["controller_progress_delta"]["artifact_refs"]
    assert "canonical_artifact_delta_missing" not in evidence["blockers"]
    assert "current_package_ref_not_canonical_delta" not in evidence["blockers"]


def test_quality_repair_batch_writes_repair_execution_evidence(monkeypatch, tmp_path: Path) -> None:
    quality_module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    evidence_module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    _write_blocked_publication_eval(study_root, quest_id="quest-003")
    _write_quality_summary(study_root)
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Updated canonical draft.\n", encoding="utf-8")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::003"},
    )
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "selected_publication_work_unit": {
            "unit_id": "manuscript_story_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        "gate_replay": {
            "status": "blocked",
            "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "unit_results": [
            {
                "unit_id": "manuscript_story_repair",
                "status": "updated",
                "result": {
                    "changed_artifact_refs": [
                        {"path": str(draft), "artifact_role": "canonical_manuscript"}
                    ],
                    "authority_claims": {"quality_authorized": True},
                },
            }
        ],
        "execution_summary": {
            "parallel_wave_count": 0,
            "parallel_unit_count": 0,
            "sequential_unit_count": 1,
            "skipped_dependency_unit_count": 0,
        },
    }
    monkeypatch.setattr(quality_module.gate_clearing_batch, "run_gate_clearing_batch", lambda **_: gate_result)

    result = quality_module.run_quality_repair_batch(
        profile=profile,
        study_id="003-dpcc",
        study_root=study_root,
        quest_id="quest-003",
        source="test-source",
    )

    evidence = result["repair_execution_evidence"]
    assert evidence["progress_delta_candidate"] is True
    assert evidence["quality_authorized"] is False
    assert "quality_override_not_allowed" in evidence["blockers"]
    evidence_path = evidence_module.stable_repair_execution_evidence_path(study_root=study_root)
    assert result["repair_execution_evidence_path"] == str(evidence_path)
    assert json.loads(evidence_path.read_text(encoding="utf-8")) == evidence
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["repair_execution_evidence"] == evidence
