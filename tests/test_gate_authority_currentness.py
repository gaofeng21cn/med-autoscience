from __future__ import annotations

import importlib


def test_stale_submission_authority_signatures_match_routes_to_gate_replay() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    currentness = importlib.import_module("med_autoscience.controllers.gate_authority_currentness")

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_submission_minimal_authority"],
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "gate_fingerprint": "publication-gate::authority",
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.stale_submission_authority_current is True
    assert result["actionability_status"] == "controller_gate_replay_required"
    assert result["next_work_unit"]["unit_id"] == "publication_gate_replay"
    assert result["gate_fingerprint"] == "publication-gate::authority"


def test_delivery_mirror_stale_but_package_current_routes_to_sync_then_replay() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    currentness = importlib.import_module("med_autoscience.controllers.gate_authority_currentness")

    gate_report = {
        "status": "blocked",
        "current_required_action": "complete_bundle_stage",
        "blockers": ["stale_study_delivery_mirror"],
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "current_package_status": "fresh",
        "current_package_source_signature": "source::abc",
        "current_package_authority_source_signature": "source::abc",
        "gate_fingerprint": "publication-gate::delivery",
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.delivery_sync_required is True
    assert result["actionability_status"] == "controller_sync_closure_required"
    assert result["next_work_unit"] == {
        "unit_id": "submission_delivery_sync_closure",
        "lane": "controller",
        "summary": "Refresh the study delivery mirror from the current package, then replay the publication gate.",
        "control_surface": "gate_clearing_batch",
    }


def test_label_only_blocker_requires_specificity_before_long_repair() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = publication_work_units.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        }
    )

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_true_current_blocker_with_artifact_ref_keeps_repair_unit() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = publication_work_units.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "artifact_path": "/tmp/study/paper/claim_evidence_map.json",
                }
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
