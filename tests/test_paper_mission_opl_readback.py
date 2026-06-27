from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from med_autoscience.paper_mission_opl_readback import (
    RUNNING_READBACK_STATUS,
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)


def test_opl_terminal_closeout_readback_observes_record_only_terminal_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(study_root, {})

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_paper_progress"] is False
    assert readback["terminal_closeout"]["domain_ready_claimed"] is False


def test_opl_terminal_closeout_readback_ignores_domain_ready_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_ready_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_ignores_domain_completion_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_completion_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_requires_record_only_boundary(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "authority_boundary": {
                "record_only_surface": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


def test_opl_terminal_closeout_readback_ignores_prior_default_executor_closeout_for_next_stage(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "domain_owner/default-executor-dispatch",
            "blocked_reason": "opl_runtime_lifecycle_readback_required",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_accepts_current_route_target_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_id"] == "publication_gate_replay"


def test_opl_terminal_closeout_readback_rejects_unbound_local_closeout_for_route_identity(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_currentness_mismatch_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [
                carrier["stage_terminal_decision_ref"],
                carrier["opl_route_command_ref"],
                "typed-blocker:stage_attempt_currentness_mismatch",
            ],
            "typed_blocker_ref": "local-closeout#domain_blocker",
            "blocked_reason": "stage_attempt_currentness_mismatch",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_retired_stale_opl_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    task = payload["family_runtime_task"]["task"]
    task["last_error"] = (
        "operator_retired_stale_runtime_residue:"
        "mas_paper_mission_current_thread_replaces_stale_stage_route_rows"
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_consumes_matching_opl_runtime_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["dispatch_status"] == "terminal_closeout_observed"
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_provider_running"] is False
    assert readback["can_claim_paper_progress"] is False
    terminal = readback["terminal_closeout"]
    assert terminal["runtime_readback_source"] == "opl_family_runtime_queue_inspect"
    assert terminal["task_id"] == "frt-stage-route"
    assert terminal["task_status"] == "blocked"
    assert terminal["closeout_receipt_status"] == "accepted_typed_closeout"
    assert terminal["stage_id"] == "publication_gate_replay"
    assert terminal["stage_attempt_id"] == "sat-terminal"
    assert terminal["typed_blocker_ref"] == "typed-blocker:opl_runtime_live_readback_required"
    assert terminal["provider_completion_is_domain_ready"] is False


def test_opl_terminal_closeout_readback_rejects_cross_transaction_opl_runtime_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "paper_mission_transaction_ref": "paper-mission-transaction::other",
    }

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_consumes_completed_stage_attempt_when_task_still_running(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_completed_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["dispatch_status"] == "terminal_closeout_observed"
    assert readback["can_claim_provider_running"] is False
    terminal = readback["terminal_closeout"]
    assert terminal["task_id"] == "frt-stage-route"
    assert terminal["task_status"] == "running"
    assert terminal["status"] == "completed"
    assert terminal["stage_attempt_id"] == "sat-completed"
    assert terminal["closeout_receipt_status"] == "accepted_typed_closeout"
    assert terminal["closeout_refs"] == [
        "paper-mission-transaction::dm002#opl_route_command",
        "opl://stage-attempts/sat-completed/runtime-blockers/no_typed_domain_handler_closeout_observed",
    ]
    assert terminal["provider_completion_is_domain_ready"] is False


def test_opl_terminal_closeout_readback_accepts_stage_terminal_ref_binding(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-stage-ref",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [
                "paper-mission-transaction::dm002",
                "paper-mission-transaction::dm002#stage_terminal_decision",
            ],
            "closeout_receipt_status": "accepted_typed_closeout",
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-stage-ref",
            },
        },
    ]
    runtime_task["events"] = []

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-stage-ref"
    assert readback["terminal_closeout"]["closeout_refs"] == [
        "paper-mission-transaction::dm002",
        "paper-mission-transaction::dm002#stage_terminal_decision",
    ]


def test_opl_runtime_readback_reports_same_identity_running_attempt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["dispatch_status"] == "provider_attempt_running"
    assert readback["domain_ready_verdict"] == "opl_runtime_attempt_running"
    assert readback["can_claim_provider_running"] is True
    assert readback["can_claim_paper_progress"] is False
    running = readback["running_attempt"]
    assert running["stage_attempt_id"] == "sat-running"
    assert running["provider_status"] == "running"
    assert running["workflow_id"] == "wf-running"
    assert running["provider_completion_is_domain_ready"] is False


def test_opl_runtime_readback_prefers_live_running_attempt_over_local_terminal_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "study_id": carrier["study_id"],
            "stage_id": "publication_gate_replay",
            "work_unit_id": carrier["work_unit_id"],
            "work_unit_fingerprint": carrier["work_unit_fingerprint"],
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [carrier["opl_route_command_ref"]],
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert "terminal_closeout" not in readback
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-running"
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_live_probe_terminal_readback_overrides_local_terminal_residue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    _write_closeout(
        study_root,
        {
            "study_id": carrier["study_id"],
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-local-stale",
            "work_unit_id": carrier["work_unit_id"],
            "work_unit_fingerprint": carrier["work_unit_fingerprint"],
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [carrier["opl_route_command_ref"]],
            "blocked_reason": "domain_gate_pending",
        },
    )

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_list_closeout_summary_payload()
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-list-terminal"
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_list"
    )


def test_opl_runtime_readback_accepts_current_control_running_on_blocked_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_running_task_running_attempt_payload()
    task = payload["family_runtime_task"]["task"]
    task["status"] = "blocked"
    task["current_control_state"] = {
        "running_provider_attempt": True,
        "current_stage_attempt_id": "sat-running",
    }

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-running"
    assert readback["running_attempt"]["task_status"] == "blocked"
    assert readback["running_attempt"]["provider_status"] == "running"
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_readback_accepts_same_route_identity_with_changed_route_target(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    changed_target = (
        "MAS mission executor consumed terminal route-back and continued the "
        "PaperMission stage."
    )
    task["payload"]["route_target"] = changed_target
    task["current_control_state"]["stage_run_currentness_identity"][
        "stage_id"
    ] = changed_target
    runtime_task["stage_attempts"][0]["stage_id"] = changed_target

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["task_id"] == "frt-stage-route"
    assert readback["terminal_closeout"]["stage_id"] == "publication_gate_replay"
    assert readback["terminal_closeout"]["closeout_refs"] == [
        "paper-mission-transaction::dm002#stage_terminal_decision",
        "typed-blocker:opl_runtime_live_readback_required",
    ]


def test_opl_runtime_readback_prefers_running_terminal_successor_over_old_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_queue_with_terminal_and_running_successor_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["dispatch_status"] == "provider_attempt_running"
    assert readback["can_claim_provider_running"] is True
    assert readback["can_claim_paper_progress"] is False
    assert "terminal_closeout" not in readback
    running = readback["running_attempt"]
    assert running["task_id"] == "frt-successor"
    assert running["stage_attempt_id"] == "sat-successor"
    assert running["workflow_id"] == "wf-successor"
    assert running["provider_status"] == "live"


def test_opl_runtime_list_payload_running_successor_does_not_require_heavy_inspect(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_queue_with_terminal_and_running_successor_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["running_attempt"]["task_id"] == "frt-successor"
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-successor"
    assert "terminal_closeout" not in readback


def test_opl_runtime_live_probe_prefers_queue_list_terminal_closeout_over_liveness(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_terminal_and_running_successor_payload()
        raise AssertionError("heavy queue inspect should not be needed")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-terminal"
    assert "running_attempt" not in readback


def test_opl_runtime_default_readback_does_not_probe_live_queue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    def fail_opl_json(*_args, **_kwargs) -> None:
        raise AssertionError("default readback must not call OPL live queue")

    monkeypatch.setattr(readback_module, "_run_opl_json", fail_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


def test_opl_runtime_live_probe_inspects_matching_task_when_list_lacks_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        calls.append(args)
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_matching_tasks_without_closeout_summary_payload()
        if args[:3] == ("family-runtime", "queue", "inspect"):
            return _opl_runtime_task_payload()
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_inspect"
    )
    assert [call[:3] for call in calls] == [
        ("family-runtime", "queue", "list"),
        ("family-runtime", "queue", "inspect"),
    ]


def test_opl_runtime_list_payload_terminal_closeout_does_not_require_heavy_inspect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_list_closeout_summary_payload()
        raise AssertionError("live probe must not call heavy queue inspect")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-list-terminal"
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_list"
    )


def test_opl_runtime_live_probe_inspects_terminal_list_tasks_without_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    inspected: list[str] = []

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_many_matching_terminal_tasks_payload()
        if args[:3] == ("family-runtime", "queue", "inspect"):
            inspected.append(args[3])
            return _opl_runtime_task_payload()
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_inspect"
    )
    assert inspected == ["frt-stage-route-0"]


def test_opl_runtime_live_probe_inspects_current_domain_gate_before_stale_residue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    inspected: list[str] = []

    def fake_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        assert timeout_seconds > 0
        if args[:3] == ("family-runtime", "queue", "list"):
            return _opl_queue_with_stale_and_current_tasks_without_summary_payload()
        if args[:3] == ("family-runtime", "queue", "inspect"):
            inspected.append(args[3])
            if args[3] == "frt-current":
                return _opl_runtime_task_payload()
            payload = _opl_runtime_task_payload()
            payload["family_runtime_task"]["task"]["task_id"] = args[3]
            payload["family_runtime_task"]["task"]["last_error"] = (
                "operator_retired_stale_runtime_residue:"
                "mas_paper_mission_current_thread_replaces_stale_stage_route_rows"
            )
            return payload
        raise AssertionError(f"unexpected OPL command: {args}")

    monkeypatch.setattr(readback_module, "_ranked_opl_bin_candidates", lambda: [opl_bin])
    monkeypatch.setattr(readback_module, "_run_opl_json", fake_opl_json)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["task_id"] == "frt-stage-route"
    assert inspected == ["frt-current"]


def test_opl_json_timeout_terminates_process_group_without_hanging(
    tmp_path: Path,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    opl_bin = tmp_path / "opl"
    opl_bin.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import subprocess
            import sys
            import time

            subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            time.sleep(30)
            """
        ),
        encoding="utf-8",
    )
    os.chmod(opl_bin, 0o755)

    started = time.monotonic()
    payload = readback_module._run_opl_json(
        opl_bin,
        ("family-runtime", "queue", "list", "--json"),
        timeout_seconds=0.2,
    )
    elapsed = time.monotonic() - started

    assert payload is None
    assert elapsed < 2.0


def _carrier() -> dict[str, str]:
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "dispatch_status": "transition_request_pending",
    }


def _opl_route_carrier() -> dict[str, object]:
    return {
        **_carrier(),
        "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
        "stage_terminal_decision_ref": (
            "paper-mission-transaction::dm002#stage_terminal_decision"
        ),
        "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }


def _opl_runtime_task_payload() -> dict[str, object]:
    return {
        "version": "g2",
        "family_runtime_task": {
            "surface_id": "opl_family_runtime_task",
            "task": {
                "task_id": "frt-stage-route",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/stage-route",
                "payload": {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                    "opl_route_command_ref": (
                        "paper-mission-transaction::dm002#opl_route_command"
                    ),
                    "command_kind": "start_next_stage",
                    "route_target": "publication_gate_replay",
                },
                "status": "blocked",
                "last_error": "paper_mission_stage_route_domain_gate_pending",
                "dead_letter_reason": (
                    "paper_mission_stage_route_domain_gate_pending"
                ),
                "current_control_state": {
                    "current_stage_attempt_id": "sat-terminal",
                    "running_provider_attempt": False,
                    "closeout_refs": [
                        "paper-mission-transaction::dm002#stage_terminal_decision",
                        "typed-blocker:opl_runtime_live_readback_required",
                    ],
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "typed_blocker_refs": [
                        "typed-blocker:opl_runtime_live_readback_required"
                    ],
                    "stage_run_currentness_identity": {
                        "stage_id": "publication_gate_replay",
                    },
                },
            },
            "stage_attempts": [
                {
                    "stage_attempt_id": "sat-terminal",
                    "status": "completed",
                    "stage_id": "publication_gate_replay",
                    "provider_attempt_ref": "temporal://attempt/sat-terminal",
                }
            ],
            "events": [
                {
                    "event_type": "paper_mission_stage_route_terminal_task_reconciled",
                    "payload": {
                        "closeout_refs": [
                            "paper-mission-transaction::dm002#stage_terminal_decision",
                            "typed-blocker:opl_runtime_live_readback_required",
                        ]
                    },
                }
            ],
        },
    }


def _opl_running_task_completed_attempt_payload() -> dict[str, object]:
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["status"] = "running"
    task["last_error"] = "paper_mission_stage_route_temporal_started"
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-stale",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::other",
                "opl_route_command_ref": "paper-mission-transaction::other#opl_route_command",
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": ["stale-closeout"],
            "closeout_receipt_status": "accepted_typed_closeout",
        },
        {
            "stage_attempt_id": "sat-completed",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [
                "paper-mission-transaction::dm002#opl_route_command",
                (
                    "opl://stage-attempts/sat-completed/runtime-blockers/"
                    "no_typed_domain_handler_closeout_observed"
                ),
            ],
            "closeout_receipt_status": "accepted_typed_closeout",
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-completed",
            },
        },
    ]
    runtime_task["events"] = []
    return payload


def _opl_running_task_running_attempt_payload() -> dict[str, object]:
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["status"] = "running"
    task["last_error"] = "paper_mission_stage_route_temporal_started"
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-running",
            "status": "running",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "provider_kind": "temporal",
            "workflow_id": "wf-running",
            "provider_run": {
                "provider_status": "running",
                "workflow_id": "wf-running",
                "last_heartbeat_at": "2026-06-24T09:33:26.074Z",
                "last_runner_event_kind": "command_execution",
            },
        }
    ]
    runtime_task["events"] = []
    return payload


def _opl_queue_with_terminal_and_running_successor_payload() -> dict[str, object]:
    terminal = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    successor = {
        "task_id": "frt-successor",
        "domain_id": "medautoscience",
        "task_kind": "paper_mission/stage-route",
        "payload": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
            "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
            "command_kind": "start_next_stage",
            "route_target": "publication_gate_replay",
            "requeued_from_terminal_task_id": "frt-stage-route",
            "terminal_successor_generation": 1,
        },
        "status": "running",
        "last_error": "paper_mission_stage_route_temporal_started",
        "linked_stage_attempt_liveness": {
            "surface_kind": "opl_queue_task_linked_stage_attempt_liveness",
            "status": "live",
            "stage_attempt_id": "sat-successor",
            "workflow_id": "wf-successor",
            "stage_id": "publication_gate_replay",
            "provider_kind": "temporal",
            "executor_kind": "codex_cli",
            "task_id": "frt-successor",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": "paper-mission-transaction::dm002#opl_route_command",
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [],
        },
    }
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 2,
                "by_status": {
                    "blocked": 1,
                    "running": 1,
                },
            },
            "tasks": [terminal, successor],
        },
    }


def _opl_queue_with_many_matching_terminal_tasks_payload() -> dict[str, object]:
    tasks = []
    for index in range(5):
        task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
        task["task_id"] = f"frt-stage-route-{index}"
        task["current_control_state"] = {}
        tasks.append(task)
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": len(tasks),
                "by_status": {
                    "blocked": len(tasks),
                },
            },
            "tasks": tasks,
        },
    }


def _opl_queue_with_matching_tasks_without_closeout_summary_payload() -> dict[str, object]:
    task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    task["status"] = "blocked"
    task["current_control_state"] = {}
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 1,
                "by_status": {
                    "blocked": 1,
                },
            },
            "tasks": [task],
        },
    }


def _opl_queue_with_stale_and_current_tasks_without_summary_payload() -> dict[str, object]:
    stale = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    stale["task_id"] = "frt-stale"
    stale["status"] = "blocked"
    stale["last_error"] = (
        "operator_retired_stale_runtime_residue:"
        "mas_paper_mission_current_thread_replaces_stale_stage_route_rows"
    )
    stale["current_control_state"] = {}
    current = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    current["task_id"] = "frt-current"
    current["status"] = "blocked"
    current["last_error"] = "paper_mission_stage_route_domain_gate_pending"
    current["current_control_state"] = {}
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 2,
                "by_status": {
                    "blocked": 2,
                },
            },
            "tasks": [stale, current],
        },
    }


def _opl_queue_with_list_closeout_summary_payload() -> dict[str, object]:
    task = _opl_runtime_task_payload()["family_runtime_task"]["task"]
    task["status"] = "blocked"
    task["current_control_state"] = {
        "current_stage_attempt_id": "sat-list-terminal",
        "running_provider_attempt": False,
        "closeout_receipt_status": "accepted_typed_closeout",
        "closeout_refs": [
            "paper-mission-transaction::dm002#opl_route_command",
            "opl://stage-attempts/sat-list-terminal/runtime-blockers/domain_gate_pending",
        ],
        "typed_blocker_refs": [
            "opl://stage-attempts/sat-list-terminal/runtime-blockers/domain_gate_pending"
        ],
        "stage_run_currentness_identity": {
            "stage_id": "publication_gate_replay",
        },
    }
    return {
        "version": "g2",
        "family_runtime_queue": {
            "surface_id": "opl_family_runtime_queue",
            "queue": {
                "total": 1,
                "by_status": {
                    "blocked": 1,
                },
            },
            "tasks": [task],
        },
    }


def _write_closeout(study_root: Path, override: dict[str, object]) -> None:
    closeout_root = (
        study_root / "artifacts" / "supervision" / "consumer" / "stage_attempt_closeouts"
    )
    closeout_root.mkdir(parents=True)
    payload = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "blocked",
        "study_id": "002-dm-china-us-mortality-attribution",
        "stage_id": "gate_clearing_claim_evidence_repair",
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "stage_packet_ref": "opl-stage-run://paper-mission-summary/dm002",
        "provider_attempt_ref": "temporal://attempt/sat-terminal",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "blocked_reason": "domain_gate_pending",
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
    payload.update(override)
    (closeout_root / "sat-terminal.closeout.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
