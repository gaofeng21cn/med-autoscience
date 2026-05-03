from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_ai_first_feedback import _progress_snapshot


def _feedback_state(tmp_path: Path) -> dict[str, object]:
    feedback = importlib.import_module("med_autoscience.controllers.ai_first_feedback")
    return feedback.build_ai_first_feedback_state(progress_snapshot=_progress_snapshot(tmp_path))


def test_action_dispatch_projection_tracks_open_actions_without_quality_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_action_dispatch")

    projection = module.build_action_dispatch_projection(
        feedback_state=_feedback_state(tmp_path),
        dispatch_owner="operator-session",
        observed_at="2026-05-03T00:00:00+00:00",
    )

    assert projection["surface"] == "ai_first_action_dispatch_ledger"
    assert projection["authority"] == "operations_governance_only"
    assert projection["counts"]["open"] >= 1
    assert projection["user_view"]["open_action_count"] == projection["counts"]["open"]
    first = projection["dispatches"][0]
    assert first["dispatch_owner"] == "operator-session"
    assert first["status"] == "open"
    assert first["closure_evidence"] == []
    assert first["authority_contract"]["dispatch_can_authorize_quality"] is False
    assert first["authority_contract"]["dispatch_can_authorize_submission"] is False
    assert projection["authority_contract"]["dispatch_can_authorize_finalize"] is False


def test_action_dispatch_closed_status_requires_closure_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_action_dispatch")

    try:
        module.build_action_dispatch_projection(
            feedback_state=_feedback_state(tmp_path),
            status="closed",
            observed_at="2026-05-03T00:00:00+00:00",
        )
    except ValueError as exc:
        assert "closure_evidence" in str(exc)
    else:
        raise AssertionError("closed dispatch without closure evidence should fail")

    closed = module.build_action_dispatch_projection(
        feedback_state=_feedback_state(tmp_path),
        status="closed",
        closure_evidence=["artifacts/publication_eval/latest.json"],
        observed_at="2026-05-03T00:00:00+00:00",
    )

    assert closed["counts"]["closed"] == closed["counts"]["total"]
    assert closed["user_view"]["closed_action_count"] == closed["counts"]["closed"]


def test_action_dispatch_materialization_preserves_lifecycle_and_redacts_low_level_fields(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_action_dispatch")
    study_root = tmp_path / "studies" / "001-risk"
    state = _feedback_state(tmp_path)

    opened = module.materialize_action_dispatch_ledger(
        study_root=study_root,
        feedback_state=state,
        dispatch_owner="operator-session",
        status="accepted",
        observed_at="2026-05-03T00:00:00+00:00",
    )
    closed = module.materialize_action_dispatch_ledger(
        study_root=study_root,
        feedback_state=state,
        dispatch_owner="operator-session",
        status="closed",
        closure_evidence=["artifacts/controller_decisions/latest.json"],
        observed_at="2026-05-03T01:00:00+00:00",
    )

    assert opened["counts"]["accepted"] == opened["counts"]["total"]
    assert closed["counts"]["closed"] == closed["counts"]["total"]
    assert all(item["created_at"] == "2026-05-03T00:00:00+00:00" for item in closed["dispatches"])
    assert all(item["updated_at"] == "2026-05-03T01:00:00+00:00" for item in closed["dispatches"])
    assert module.read_action_dispatch_ledger(study_root=study_root)["counts"]["closed"] == closed["counts"]["total"]
    rendered = str(closed)
    assert "internal prompt" not in rendered
    assert "token_count" not in rendered
    assert "/tmp/internal.log" not in rendered
