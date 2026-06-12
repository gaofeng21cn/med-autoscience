from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_repair_progress_projection_carries_recheck_and_gate_done_flags(tmp_path: Path) -> None:
    repair_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.repair_progress_projection"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    draft = paper_root / "draft.md"
    review = paper_root / "build" / "review_manuscript.md"
    for path in (draft, review):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    gate_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "eval-current",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "gate_replay_done": True,
            "gate_replay_refs": [str(gate_request)],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_request),
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "medical_prose_write_repair",
            "execution_status": "progress_delta_candidate",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "repair_execution_evidence_ref": str(evidence_path),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )

    repair_progress = repair_projection.build_repair_progress_projection(study_root=study_root)

    assert repair_progress["paper_delta_observed"] is True
    assert repair_progress["ai_reviewer_recheck_required"] is True
    assert repair_progress["ai_reviewer_recheck_done"] is True
    assert repair_progress["gate_replay_done"] is True
    assert repair_progress["gate_replay_refs"] == [str(gate_request)]
