from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.paper_progress_reconciler import (
    build_paper_progress_reconcile_receipt,
)
from med_autoscience.controllers.paper_progress_transition_refs import (
    read_transition_refs,
)
from tests.stage_outcome_authority_helpers import owner_route
from tests.study_runtime_test_helpers import make_profile, write_study


STUDY_ID = "002-dm-china-us-mortality-attribution"
ACTION_TYPE = "request_opl_stage_attempt"


def test_reconciler_records_only_opl_transition_ref_after_executed_dispatch(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, STUDY_ID, quest_id=f"quest-{STUDY_ID}")
    route = owner_route(
        study_id=STUDY_ID,
        action_type=ACTION_TYPE,
        owner="one-person-lab",
    )
    scan = {
        "studies": [
            {
                "study_id": STUDY_ID,
                "quest_id": f"quest-{STUDY_ID}",
                "study_macro_state": {
                    "writer_state": "live",
                    "user_next": "watch",
                    "reason": "runtime",
                    "details": {"package_delivered": False},
                },
                "owner_route": route,
                "progress_freshness": {
                    "meaningful_artifact_delta_freshness": {"status": "missing"},
                },
            }
        ]
    }
    executed = {
        "executions": [
            {
                "study_id": STUDY_ID,
                "action_type": ACTION_TYPE,
                "execution_status": "executed",
            }
        ]
    }

    receipt = build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=(STUDY_ID,),
        resolved_study_ids=(STUDY_ID,),
        before_scan=scan,
        consumed={},
        executed=executed,
        after_scan=scan,
        apply=True,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    action_receipt = decision["action_receipt"]
    assert decision["decision"] == "opl_stage_attempt_admission"
    assert decision["apply_eligible"] is True
    assert receipt["action_receipt_count"] == 1
    assert action_receipt["receipt_status"] == "transition_request_pending_opl_runtime_required"
    assert action_receipt["refs_only"] is True
    assert action_receipt["transition_runtime_owner"] == "one-person-lab"
    assert {
        "started_worker",
        "worker_start_ref",
        "outbox_item_id",
        "event_id",
        "stage_run_id",
        "stage_run_identity",
    }.isdisjoint(action_receipt)
    assert len(read_transition_refs(study_root=profile.studies_root / STUDY_ID)) == 1


def test_reconciler_does_not_record_transition_without_executed_dispatch(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    scan = {
        "studies": [
            {
                "study_id": STUDY_ID,
                "owner_route": owner_route(
                    study_id=STUDY_ID,
                    action_type=ACTION_TYPE,
                    owner="one-person-lab",
                ),
            }
        ]
    }

    receipt = build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=(STUDY_ID,),
        resolved_study_ids=(STUDY_ID,),
        before_scan=scan,
        consumed={},
        executed={},
        after_scan=scan,
        apply=True,
        generated_at="2026-05-10T00:00:00+00:00",
    )

    decision = receipt["decisions"][0]
    assert decision["apply_eligible"] is False
    assert decision["action_receipt"]["receipt_status"] == "not_executed"
    assert receipt["action_receipt_count"] == 0
    assert read_transition_refs(study_root=profile.studies_root / STUDY_ID) == []
