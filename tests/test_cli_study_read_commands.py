from __future__ import annotations

from med_autoscience.cli.study_read_commands import _progress_first_status_payload


def test_progress_first_payload_removes_canonical_owner_successor_action_from_default_view() -> None:
    action = {
        "surface_kind": "current_executable_owner_action",
        "source": "paper_mission.next_action.owner_successor",
        "action_type": "consume_submission_ready_package_authority_or_human_gate",
        "allowed_actions": ["consume_submission_ready_package_authority_or_human_gate"],
        "next_owner": "mas_authority_kernel",
        "work_unit_id": "submission_authority_owner_verdict",
    }
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
        },
        "current_executable_owner_action": action,
        "current_work_unit": {"surface_kind": "current_work_unit"},
    }

    filtered = _progress_first_status_payload(payload)

    assert "current_executable_owner_action" not in filtered
    assert filtered["next_action"] == payload["next_action"]
    assert "current_work_unit" not in filtered


def test_progress_first_payload_removes_legacy_owner_action() -> None:
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "source": "domain_transition",
            "action_type": "run_quality_repair_batch",
        },
    }

    filtered = _progress_first_status_payload(payload)

    assert "current_executable_owner_action" not in filtered
