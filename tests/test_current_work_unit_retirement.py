from __future__ import annotations

import importlib
from pathlib import Path


def test_current_work_unit_builder_is_physically_retired() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    assert not hasattr(module, "build_current_work_unit")


def test_current_work_unit_active_sources_do_not_call_retired_builder() -> None:
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in (root / "src").rglob("*.py"):
        if path.name == "current_work_unit.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "build_current_work_unit" in text:
            offenders.append(str(path.relative_to(root)))

    assert offenders == []


def test_current_work_unit_typed_blocker_supersession_is_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    assert (
        module.action_supersedes_typed_blocker(
            action={"action_type": "run_gate_clearing_batch"},
            blocker={"blocker_id": "opl_execution_authorization_required"},
        )
        is False
    )
    assert (
        module.action_supersedes_typed_blocker(
            action={"action_type": "run_gate_clearing_batch"},
            blocker=None,
        )
        is True
    )


def test_current_work_unit_retirement_boundary_is_explicit() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    boundary = module.retired_authority_boundary()

    assert boundary["status"] == "retired"
    assert boundary["replacement_authority"] == "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt"
    assert boundary["can_select_next_action"] is False
    assert boundary["can_authorize_dispatch"] is False
    assert boundary["can_start_provider_attempt"] is False


def test_domain_transition_successor_materializer_is_physically_retired() -> None:
    root = Path(__file__).resolve().parents[1]
    offenders = []
    forbidden = (
        "successor_owner_action_from_domain_transition",
        "consumed_owner_receipt_domain_transition_successor",
    )
    for path in (root / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(str(path.relative_to(root)))

    assert offenders == []
