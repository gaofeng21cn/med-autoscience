from __future__ import annotations

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
from tests.test_paper_mission_opl_readback_cases.shared import (
    _carrier,
    _opl_queue_with_list_closeout_summary_payload,
    _opl_queue_with_many_matching_terminal_tasks_payload,
    _opl_queue_with_matching_tasks_without_closeout_summary_payload,
    _opl_queue_with_stale_and_current_tasks_without_summary_payload,
    _opl_queue_with_terminal_and_running_successor_payload,
    _opl_route_carrier,
    _opl_running_task_completed_attempt_payload,
    _opl_runtime_task_payload,
    _opl_running_task_running_attempt_payload,
    _write_closeout,
)


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


def test_opl_runtime_readback_accepts_same_route_identity_legacy_receipt_command_kind(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    carrier["command_kind"] = "resume_stage"
    carrier["opl_route_command"]["command_kind"] = "resume_stage"
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["payload"]["command_kind"] = "resume_stage"
    receipt = runtime_task["events"][0]["payload"]["opl_transition_receipt"]
    receipt["command_kind"] = "route_back"

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    terminal_closeout = readback["terminal_closeout"]
    assert terminal_closeout["stage_attempt_id"] == "sat-terminal"
    assert terminal_closeout["opl_transition_receipt"]["command_kind"] == "route_back"
    assert terminal_closeout["opl_transition_receipt"]["can_claim_paper_progress"] is False
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_readback_accepts_legacy_command_kind_on_task_identity(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    carrier["command_kind"] = "resume_stage"
    carrier["opl_route_command"]["command_kind"] = "resume_stage"
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["payload"]["command_kind"] = "route_back"
    receipt = runtime_task["events"][0]["payload"]["opl_transition_receipt"]
    receipt["command_kind"] = "route_back"

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["task_id"] == "frt-stage-route"
    assert readback["terminal_closeout"]["opl_transition_receipt"]["command_kind"] == (
        "route_back"
    )
    assert readback["mas_receipt_consumption"]["next_legal_action"] == (
        "record_typed_blocker"
    )
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_readback_accepts_legacy_command_kind_on_stage_attempt_identity(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    carrier["command_kind"] = "resume_stage"
    carrier["opl_route_command"]["command_kind"] = "resume_stage"
    payload = _opl_running_task_completed_attempt_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["payload"]["command_kind"] = "resume_stage"
    terminal_attempt = runtime_task["stage_attempts"][1]
    terminal_attempt["workspace_locator"]["command_kind"] = "route_back"
    terminal_attempt["opl_transition_receipt"]["command_kind"] = "route_back"

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-completed"
    assert readback["terminal_closeout"]["opl_transition_receipt"]["command_kind"] == (
        "route_back"
    )
    assert readback["mas_receipt_consumption"]["next_legal_action"] == (
        "record_typed_blocker"
    )
    assert readback["can_claim_paper_progress"] is False


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


def test_opl_runtime_live_probe_prefers_running_successor_over_old_closeout(
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

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-successor"
    assert "terminal_closeout" not in readback


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


def test_opl_runtime_live_probe_budget_covers_large_terminal_receipt_inspect(
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
            return _opl_queue_with_matching_tasks_without_closeout_summary_payload()
        if args[:3] == ("family-runtime", "queue", "inspect"):
            assert timeout_seconds >= 20.0
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
    assert readback["opl_transition_receipt"]["receipt_status"] == (
        "terminal_closeout_observed"
    )
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_inspect"
    )


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
