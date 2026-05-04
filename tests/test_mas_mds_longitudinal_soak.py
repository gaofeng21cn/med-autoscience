from __future__ import annotations

import importlib


def _module():
    return importlib.import_module("med_autoscience.controllers.mas_mds_longitudinal_soak")


def _program_module():
    return importlib.import_module("med_autoscience.controllers.mas_mds_unified_enhancement_program")


def _complete_catalog() -> dict[str, object]:
    return {
        "catalog_id": "real-workspace-longitudinal-soak",
        "latency_threshold_minutes": 90,
        "events": [
            {
                "event_id": "evt-pre-submission",
                "event_type": "pre_submission",
                "study_id": "nf-pitnet-003",
                "paper_line_id": "pitnet-endocrine-burden",
                "occurred_at": "2026-05-01T01:00:00Z",
                "evidence_refs": ["artifacts/medical_paper/readiness.json"],
            },
            {
                "event_id": "evt-revision",
                "event_type": "revision",
                "study_id": "nf-pitnet-003",
                "paper_line_id": "pitnet-endocrine-burden",
                "occurred_at": "2026-05-01T02:00:00Z",
                "evidence_refs": ["artifacts/revision/reviewer_action_matrix.json"],
            },
            {
                "event_id": "evt-reopen",
                "event_type": "reopen_same_paper_line",
                "study_id": "nf-pitnet-003",
                "paper_line_id": "pitnet-endocrine-burden",
                "previous_paper_line_id": "pitnet-endocrine-burden",
                "occurred_at": "2026-05-01T03:00:00Z",
                "evidence_refs": ["artifacts/runtime/reopen_same_line_intake.json"],
            },
            {
                "event_id": "evt-switch",
                "event_type": "route_change_line_switch",
                "study_id": "nf-pitnet-004",
                "paper_line_id": "pitnet-invasive-architecture",
                "previous_paper_line_id": "pitnet-endocrine-burden",
                "route_action": "switch_line",
                "occurred_at": "2026-05-01T04:00:00Z",
                "evidence_refs": ["artifacts/route_decision/latest.json"],
            },
            {
                "event_id": "evt-final-rebuild",
                "event_type": "final_rebuild",
                "study_id": "nf-pitnet-004",
                "paper_line_id": "pitnet-invasive-architecture",
                "occurred_at": "2026-05-01T05:00:00Z",
                "evidence_refs": ["artifacts/build/final_rebuild_manifest.json"],
            },
            {
                "event_id": "evt-draft-to-package",
                "event_type": "draft_authorization_to_submission_package_rebuild_latency",
                "study_id": "nf-pitnet-004",
                "paper_line_id": "pitnet-invasive-architecture",
                "started_at": "2026-05-01T05:00:00Z",
                "finished_at": "2026-05-01T06:05:00Z",
                "evidence_refs": [
                    "artifacts/authoring/full_draft_authorization.json",
                    "artifacts/submission_package/rebuild_manifest.json",
                ],
            },
            {
                "event_id": "evt-failure-replay",
                "event_type": "failure_recovery_replay_evidence",
                "study_id": "nf-pitnet-004",
                "paper_line_id": "pitnet-invasive-architecture",
                "failure_event_id": "run-failed-001",
                "recovery_event_id": "run-recovered-001",
                "replay_evidence_refs": ["artifacts/runtime/replay_evidence.json"],
                "evidence_refs": ["artifacts/runtime/recovery_record.json"],
            },
        ],
    }


def test_longitudinal_soak_proof_is_ready_for_complete_real_workspace_timeline() -> None:
    projection = _module().build_longitudinal_soak_proof(catalog_payload=_complete_catalog())

    assert projection["surface"] == "mas_mds_longitudinal_soak_proof"
    assert projection["read_model"] == "mas_mds_longitudinal_soak_read_model"
    assert projection["overall_status"] == "ready"
    assert projection["next_action"] == "continue_l1_longitudinal_soak"
    assert projection["coverage"]["missing_events"] == []
    assert projection["read_model_projection"] == {
        "covered_events": [
            "pre_submission",
            "revision",
            "reopen_same_paper_line",
            "route_change_line_switch",
            "final_rebuild",
            "draft_authorization_to_submission_package_rebuild_latency",
            "failure_recovery_replay_evidence",
        ],
        "paper_lines": [
            {
                "paper_line_id": "pitnet-endocrine-burden",
                "study_ids": ["nf-pitnet-003"],
                "event_count": 3,
            },
            {
                "paper_line_id": "pitnet-invasive-architecture",
                "study_ids": ["nf-pitnet-004"],
                "event_count": 4,
            },
        ],
        "route_changes": [
            {
                "event_id": "evt-switch",
                "from_paper_line_id": "pitnet-endocrine-burden",
                "to_paper_line_id": "pitnet-invasive-architecture",
                "route_action": "switch_line",
            }
        ],
        "same_line_reopens": [
            {
                "event_id": "evt-reopen",
                "paper_line_id": "pitnet-endocrine-burden",
                "study_id": "nf-pitnet-003",
            }
        ],
        "latency_acceptance": {
            "threshold_minutes": 90,
            "accepted": True,
            "measurements": [
                {
                    "event_id": "evt-draft-to-package",
                    "latency_minutes": 65,
                    "accepted": True,
                    "evidence_refs": [
                        "artifacts/authoring/full_draft_authorization.json",
                        "artifacts/submission_package/rebuild_manifest.json",
                    ],
                }
            ],
        },
        "failure_recovery_replay": [
            {
                "event_id": "evt-failure-replay",
                "failure_event_id": "run-failed-001",
                "recovery_event_id": "run-recovered-001",
                "replay_evidence_refs": ["artifacts/runtime/replay_evidence.json"],
            }
        ],
        "authority": {
            "mode": "evidence_only",
            "writes_live_study": False,
            "writes_current_package": False,
            "writes_publication_eval": False,
            "writes_controller_decisions": False,
            "writes_delivery_truth": False,
            "can_authorize_submission": False,
            "can_authorize_quality": False,
        },
    }


def test_longitudinal_soak_proof_fails_closed_without_latency_or_replay_evidence() -> None:
    catalog = _complete_catalog()
    catalog["events"] = [
        event
        for event in catalog["events"]  # type: ignore[index]
        if event["event_type"]
        not in {
            "draft_authorization_to_submission_package_rebuild_latency",
            "failure_recovery_replay_evidence",
        }
    ]

    projection = _module().build_longitudinal_soak_proof(catalog_payload=catalog)

    assert projection["overall_status"] == "partial"
    assert projection["next_action"] == (
        "materialize_draft_authorization_to_submission_package_rebuild_latency"
    )
    assert projection["coverage"]["missing_events"] == [
        "draft_authorization_to_submission_package_rebuild_latency",
        "failure_recovery_replay_evidence",
    ]
    assert projection["blocking_gaps"] == []
    assert projection["read_model_projection"]["latency_acceptance"] == {
        "threshold_minutes": 90,
        "accepted": False,
        "measurements": [],
    }
    assert projection["read_model_projection"]["failure_recovery_replay"] == []


def test_longitudinal_soak_proof_blocks_authority_writes() -> None:
    catalog = _complete_catalog()
    catalog["events"] = [
        *catalog["events"],  # type: ignore[list-item]
        {
            "event_id": "evt-authority-write",
            "event_type": "final_rebuild",
            "study_id": "nf-pitnet-004",
            "paper_line_id": "pitnet-invasive-architecture",
            "evidence_refs": ["artifacts/build/final_rebuild_manifest.json"],
            "writes": ["publication_eval/latest.json"],
        },
    ]

    projection = _module().build_longitudinal_soak_proof(catalog_payload=catalog)

    assert projection["overall_status"] == "blocked"
    assert projection["next_action"] == "remove_authority_write_from_longitudinal_soak_proof"
    assert projection["blocking_gaps"] == [
        {
            "event_id": "evt-authority-write",
            "code": "authority_write_prohibited",
            "surface": "publication_eval/latest.json",
        }
    ]
    assert projection["authority_contract"]["can_authorize_submission"] is False


def test_unified_program_board_projects_l1_longitudinal_outputs() -> None:
    proof = _module().build_longitudinal_soak_proof(catalog_payload=_complete_catalog())

    board = _program_module().build_unified_enhancement_program_board(
        {"l1_longitudinal_soak_proof": proof}
    )

    l1 = next(
        lane for lane in board["lanes"] if lane["lane_id"] == "L1_real_workspace_longitudinal_soak"
    )
    assert l1["status"] == "completed"
    assert l1["blocks_usable_target"] is False
    assert l1["outputs"] == {
        "surface": "mas_mds_longitudinal_soak_proof",
        "read_model": "mas_mds_longitudinal_soak_read_model",
        "overall_status": "ready",
        "covered_events": [
            "pre_submission",
            "revision",
            "reopen_same_paper_line",
            "route_change_line_switch",
            "final_rebuild",
            "draft_authorization_to_submission_package_rebuild_latency",
            "failure_recovery_replay_evidence",
        ],
        "authority_mode": "evidence_only",
    }
    assert board["status_summary"]["l1_longitudinal_soak_status"] == "ready"
