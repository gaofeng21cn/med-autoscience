from __future__ import annotations

import importlib
from pathlib import Path


def test_control_intent_lifecycle_is_run_scoped_for_live_delivery(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "001-risk"
    identity = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="analysis_claim_evidence_repair",
        blocker_authority_fingerprint="publication-blockers::cf23017195411212",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )
    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"active_run_id": "run-old", "message_id": "msg-old"},
        recorded_at="2026-05-12T05:00:27+00:00",
    )
    module.append_skipped_duplicate_if_needed(
        study_root=study_root,
        identity=identity,
        payload={"active_run_id": "run-new", "reason": "same_fingerprint_no_artifact_delta"},
        recorded_at="2026-05-12T05:09:03+00:00",
    )

    all_runs = module.lifecycle_state(study_root=study_root, identity=identity)
    new_run = module.lifecycle_state(study_root=study_root, identity=identity, active_run_id="run-new")

    assert all_runs["delivery_blocked"] is True
    assert all_runs["latest_event_type"] == "skipped_duplicate"
    assert new_run["lifecycle_state"] == "new"
    assert new_run["delivery_blocked"] is False
