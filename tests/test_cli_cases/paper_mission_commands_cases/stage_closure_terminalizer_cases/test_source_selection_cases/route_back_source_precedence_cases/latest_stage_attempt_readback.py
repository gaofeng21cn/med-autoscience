from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_latest_stage_attempt_route_back_source_readback_prefers_current_terminal_attempt_over_newer_stale_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    packets_root = (
        workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    transaction_id = "paper-mission-transaction::dm003::write::current"

    def write_packet(attempt_id: str, stage_id: str, mtime: float) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        (workspace_root / route_ref).write_text(
            json.dumps(
                {
                    "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": "write",
                    "work_unit_id": work_unit_id,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "route_back_evidence_candidate",
                    "study_id": study_id,
                    "stage_id": stage_id,
                    "stage_attempt_id": attempt_id,
                    "route_back_evidence_ref": route_ref,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    current_packet = write_packet("sat-current", work_unit_id, 1_000.0)
    stale_packet = write_packet("sat-stale", work_unit_id, 2_000.0)
    source_readback = {
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::terminalize-test",
        "mission_state": "route_back",
        "consume_candidate_status": "route_back",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "stage_closure_decision": {
            "identity": {
                "paper_mission_transaction_ref": transaction_id,
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-stale",
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "stage_attempt_id": "sat-current",
                "closeout_ref": "opl://family-runtime/tasks/frt-current/terminal-closeout-readback",
                "runtime_readback_source": "opl_family_runtime_queue_inspect",
                "closeout_refs": [str(current_packet)],
            }
        },
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
    }
    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    readback = commands._latest_stage_attempt_route_back_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source_readback=source_readback,
        source="test",
    )

    assert readback is not None
    assert readback["source_ref"] == str(current_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-current"
    assert stale_packet.stat().st_mtime > current_packet.stat().st_mtime


def test_latest_stage_attempt_route_back_source_readback_prefers_new_successor_after_consumed_current(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    packets_root = (
        workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    transaction_id = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::write::dm003-bounded-prose-repair-after-post-sync-reviewer-record"
    )

    def write_packet(
        attempt_id: str,
        *,
        mtime: float,
        include_stage_packet_ref: bool,
    ) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        (workspace_root / route_ref).write_text(
            json.dumps(
                {
                    "surface_kind": "route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": "write",
                    "work_unit_id": work_unit_id,
                    "stage_attempt_id": attempt_id,
                    "owner_answer_kind": "route_back_evidence_ref",
                    "route_back_evidence_ref": route_ref,
                    "progress_events_ref": (
                        f"ops/medautoscience/paper_mission_stage_attempts/"
                        f"{attempt_id}/progress_events.jsonl"
                    ),
                }
            ),
            encoding="utf-8",
        )
        packet = {
            "surface_kind": "stage_attempt_closeout_packet",
            "study_id": study_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
            "stage_attempt_id": attempt_id,
            "owner_answer_kind": "route_back_evidence_ref",
            "route_back_evidence_ref": route_ref,
            "progress_events_ref": (
                f"ops/medautoscience/paper_mission_stage_attempts/"
                f"{attempt_id}/progress_events.jsonl"
            ),
        }
        if include_stage_packet_ref:
            packet["stage_packet_ref"] = transaction_id
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(json.dumps(packet), encoding="utf-8")
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    consumed_packet = write_packet(
        "sat-consumed",
        mtime=1_000.0,
        include_stage_packet_ref=True,
    )
    successor_packet = write_packet(
        "sat-successor",
        mtime=2_000.0,
        include_stage_packet_ref=False,
    )
    source_readback = {
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::terminalize-test",
        "mission_state": "route_back",
        "consume_candidate_status": "accepted_submission_milestone_candidate",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "current_opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": "sat-consumed",
                "closeout_ref": str(consumed_packet),
            },
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
        },
    }
    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    readback = commands._latest_stage_attempt_route_back_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source_readback=source_readback,
        source="test",
    )

    assert readback is not None
    assert readback["source_ref"] == str(successor_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-successor"
