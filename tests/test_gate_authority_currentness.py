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


def test_delivery_mirror_stale_requires_current_package_freshness_proof_before_sync() -> None:
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

    assert resolution.current_package_fresh is False
    assert resolution.delivery_sync_required is False
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_delivery_mirror_stale_rejects_status_fresh_without_proof_path() -> None:
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
        "current_package_freshness": {
            "status": "fresh",
            "source_signature": "source::abc",
            "authority_source_signature": "source::abc",
            "submission_manifest_path": "/tmp/quest/paper/submission_minimal/submission_manifest.json",
            "current_package_root": "/tmp/study/manuscript/current_package",
        },
        "gate_fingerprint": "publication-gate::delivery",
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.current_package_fresh is False
    assert resolution.delivery_sync_required is False
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_delivery_mirror_stale_with_package_freshness_proof_routes_to_sync_then_replay() -> None:
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
        "current_package_freshness": {
            "status": "fresh",
            "source_unit_id": "sync_submission_minimal_delivery",
            "source_signature": "source::abc",
            "authority_source_signature": "source::abc",
            "submission_manifest_path": "/tmp/quest/paper/submission_minimal/submission_manifest.json",
            "current_package_root": "/tmp/study/manuscript/current_package",
            "proof_path": "/tmp/study/artifacts/controller/current_package_freshness/latest.json",
        },
        "gate_fingerprint": "publication-gate::delivery",
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.current_package_fresh is True
    assert resolution.delivery_sync_required is True
    assert result["actionability_status"] == "controller_sync_closure_required"
    assert result["next_work_unit"] == {
        "unit_id": "submission_delivery_sync_closure",
        "lane": "controller",
        "summary": "Refresh the study delivery mirror from the current package, then replay the publication gate.",
        "control_surface": "gate_clearing_batch",
    }


def test_control_plane_blocked_delivery_sync_does_not_count_as_closed() -> None:
    currentness = importlib.import_module("med_autoscience.controllers.gate_authority_currentness")

    result = currentness.sync_completed_current_package(
        [
            {
                "unit_id": "sync_submission_minimal_delivery",
                "status": "control_plane_route_blocked",
                "result": {
                    "status": "control_plane_route_blocked",
                    "source_signature": "source::abc",
                    "authority_source_signature": "source::abc",
                },
            }
        ]
    )

    assert result is None


def test_missing_submission_authority_signature_routes_to_controller_sync_not_long_repair() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    currentness = importlib.import_module("med_autoscience.controllers.gate_authority_currentness")

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_submission_minimal_authority"],
        "submission_minimal_authority_status": "stale_source_changed",
        "submission_minimal_evaluated_source_signature": "source::new",
        "submission_minimal_authority_source_signature": None,
        "gate_fingerprint": "publication-gate::missing-authority",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_submission_minimal_authority",
                "artifact_path": "/tmp/quest/paper/submission_minimal/submission_manifest.json",
            }
        ],
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.submission_authority_sync_required is True
    assert result["actionability_status"] == "controller_authority_sync_required"
    assert result["next_work_unit"] == {
        "unit_id": "submission_authority_sync_closure",
        "lane": "controller",
        "summary": "Regenerate submission authority signatures, then replay the publication gate.",
        "control_surface": "gate_clearing_batch",
    }


def test_delivery_manifest_sources_missing_without_paths_requires_specificity() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    currentness = importlib.import_module("med_autoscience.controllers.gate_authority_currentness")

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_study_delivery_mirror"],
        "study_delivery_status": "stale_source_missing",
        "study_delivery_stale_reason": "delivery_manifest_sources_missing",
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "current_package_status": "fresh",
        "current_package_source_signature": "source::abc",
        "current_package_authority_source_signature": "source::abc",
        "gate_fingerprint": "publication-gate::delivery-missing",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": "/tmp/study/manuscript/delivery_manifest.json",
                "stale_reason": "delivery_manifest_sources_missing",
            }
        ],
    }

    resolution = currentness.resolve_gate_authority_currentness(gate_report)
    result = publication_work_units.derive_publication_work_units(gate_report)

    assert resolution.delivery_missing_sources_need_specificity is True
    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


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


def test_true_current_generic_blocker_with_only_artifact_ref_requires_specificity() -> None:
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

    assert result["actionability_status"] == "blocked_by_non_actionable_gate"
    assert result["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_true_current_blocker_with_specific_source_ref_keeps_repair_unit() -> None:
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = publication_work_units.derive_publication_work_units(
        {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "artifact_path": "/tmp/study/paper/claim_evidence_map.json",
                    "source_path": "/tmp/study/paper/claim_evidence_map.json#/claims/C5",
                }
            ],
        }
    )

    assert result["actionability_status"] == "actionable"
    assert result["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
