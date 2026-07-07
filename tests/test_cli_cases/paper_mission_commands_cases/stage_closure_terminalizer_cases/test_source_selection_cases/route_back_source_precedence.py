from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_commands_cases.stage_closure_terminalizer import (
    _write_consumption_ledger,
)
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_terminalize_stage_route_back_autodiscovery_reads_nested_attempt_packets(
    tmp_path: Path,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )
    packets_root = workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    work_unit_id = "submission_milestone_candidate::followthrough::followthrough-01"

    def write_packet(root: Path, attempt_id: str, mtime: float) -> None:
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            "ops/medautoscience/paper_mission_stage_attempts/"
            f"{attempt_id}/{study_id}/route_back_evidence_packet.json"
        )
        route_path = workspace_root / route_ref
        route_path.parent.mkdir(parents=True, exist_ok=True)
        route_path.write_text(
            json.dumps(
                {
                    "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": work_unit_id,
                    "work_unit_id": work_unit_id,
                }
            ),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "owner_answer_candidate_materialized",
                    "study_id": study_id,
                    "stage_id": work_unit_id,
                    "work_unit_id": work_unit_id,
                    "stage_attempt_id": attempt_id,
                    "route_back_evidence_ref": route_ref,
                    "owner_answer_kind": "route_back_evidence_ref",
                    "provider_completion_is_domain_completion": False,
                    "provider_completion_is_domain_ready": False,
                }
            ),
            encoding="utf-8",
        )
        os.utime(packet_path, (mtime, mtime))

    write_packet(packets_root / "sat-old", "sat-old", 1_000.0)
    write_packet(packets_root / "sat-new" / study_id, "sat-new", 2_000.0)

    readback = commands._latest_stage_attempt_route_back_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source_readback={
            "stage_terminal_decision": {
                "next_work_unit": work_unit_id,
            },
        },
        source="test",
    )

    assert readback is not None
    assert readback["source_ref"].endswith(
        f"paper_mission_stage_attempts/sat-new/{study_id}/stage_attempt_closeout_packet.json"
    )
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new"

def test_terminalize_stage_prefers_latest_route_back_packet_over_old_live_write_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    packets_root = (
        workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    )

    def write_packet(
        attempt_id: str,
        *,
        stage_id: str,
        work_unit_id: str | None,
        mtime: float,
        rich_historical_context: bool = False,
    ) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        route_payload = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "study_id": study_id,
            "stage_id": stage_id,
            "owner_answer_kind": "route_back_evidence_ref",
        }
        if work_unit_id is not None:
            route_payload["work_unit_id"] = work_unit_id
        if rich_historical_context:
            route_payload.update(
                {
                    "paper_facing_delta_ref": (
                        f"ops/medautoscience/paper_mission_stage_attempts/"
                        f"{attempt_id}/paper_facing_write_repair_candidate.json"
                    ),
                    "progress_events_ref": (
                        f"ops/medautoscience/paper_mission_stage_attempts/"
                        f"{attempt_id}/progress_events.jsonl"
                    ),
                    "owner_gate_verdict": "historical write candidate",
                    "remaining_blocker": "owner consumption pending",
                    "source_evidence": {"legacy_attempt": attempt_id},
                }
            )
        (workspace_root / route_ref).write_text(
            json.dumps(route_payload),
            encoding="utf-8",
        )
        packet_payload = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "route_back_evidence_candidate_materialized",
            "study_id": study_id,
            "stage_id": stage_id,
            "stage_attempt_id": attempt_id,
            "route_back_evidence_ref": route_ref,
            "owner_answer_kind": "route_back_evidence_ref",
        }
        if work_unit_id is not None:
            packet_payload["work_unit_id"] = work_unit_id
        if rich_historical_context:
            packet_payload.update(
                {
                    "paper_facing_delta_ref": route_payload["paper_facing_delta_ref"],
                    "progress_events_ref": route_payload["progress_events_ref"],
                    "route_impact": {
                        "stage_log_summary": "historical write closeout",
                        "user_stage_log": "historical write closeout",
                    },
                }
            )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    old_packet = write_packet(
        "sat-a293",
        stage_id="write",
        work_unit_id="medical_prose_write_repair",
        mtime=1_000.0,
        rich_historical_context=True,
    )
    latest_packet = write_packet(
        "sat-a924",
        stage_id="dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        work_unit_id=None,
        mtime=2_000.0,
    )
    source_readback = {
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::terminalize-test",
        "mission_state": "route_back",
        "consume_candidate_status": "route_back",
        "paper_mission_transaction": {
            "transaction_id": (
                "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
                "submission_milestone_candidate::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
            ),
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        },
        "next_action": {
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "stage_attempt_id": "sat-a293",
                "closeout_ref": (
                    "opl://family-runtime/tasks/frt-a293/terminal-closeout-readback"
                ),
                "runtime_readback_source": "opl_family_runtime_queue_inspect",
                "closeout_refs": [str(old_packet)],
            }
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

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(latest_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-a924"

def test_terminalize_stage_prefers_current_transaction_stage_closure_over_stale_direct(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    transaction_id = (
        "paper-mission-transaction::002::submission_milestone_candidate::"
        "followthrough-02"
    )
    source_readback = {
        "study_id": study_id,
        "mission_id": "paper-mission::002",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "study_id": study_id,
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-02",
        },
        "consume_candidate_status": "accepted_submission_milestone_candidate",
        "transaction_state": "accepted_submission_milestone_candidate",
        "stage_closure_decision": {
            "surface_kind": "mas_stage_closure_decision",
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "identity": {"paper_mission_transaction_ref": transaction_id},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-current-followthrough",
                "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            },
        },
        "domain_transition": {
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            }
        },
        "current_package": {"status": "current", "can_submit": False},
        "opl_runtime_carrier_readback": {
            "carrier_status": "opl_runtime_terminal_readback_observed",
            "terminal_closeout": {
                "stage_attempt_id": "sat-current-followthrough",
                "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
                "closeout_refs": [
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-followthrough/"
                    f"{study_id}/stage_attempt_closeout_packet.json"
                ],
            },
        },
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
    }
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )

    def fail_if_stale_direct_is_used(**_: object) -> None:
        raise AssertionError("stale domain-transition direct closeout should not win")

    monkeypatch.setattr(
        commands,
        "_domain_transition_direct_terminal_source_readback",
        fail_if_stale_direct_is_used,
    )

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )
    decision = commands._terminalize_stage_closure_from_readback(readback)

    assert readback is source_readback
    assert decision["stage_id"] == (
        "submission_milestone_candidate::followthrough::followthrough-01"
    )
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-current-followthrough"

def test_terminalize_stage_prefers_newer_workspace_stage_packet_over_matching_source_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
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

    old_packet = write_packet("sat-old", "write", 1_000.0)
    new_packet = write_packet("sat-new", work_unit_id, 2_000.0)
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
                "stage_attempt_id": "sat-old",
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": "sat-old",
                "closeout_refs": [str(old_packet)],
            }
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

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(new_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new"

def test_terminalize_stage_prefers_route_back_identity_when_closeout_packet_fields_are_sparse(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
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
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration::"
        "followthrough::89b46ab394eb"
    )

    def write_packet(
        attempt_id: str,
        *,
        packet_stage_id: str,
        route_stage_id: str,
        route_work_unit_id: str | None,
        route_transaction_ref: str | None,
        mtime: float,
    ) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        route_payload = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "study_id": study_id,
            "stage_id": route_stage_id,
            "owner_answer_kind": "route_back_evidence_ref",
        }
        if route_work_unit_id is not None:
            route_payload["work_unit_id"] = route_work_unit_id
        if route_transaction_ref is not None:
            route_payload["stage_packet_ref"] = route_transaction_ref
            route_payload["source_evidence"] = {
                "paper_mission_transaction_ref": route_transaction_ref,
            }
        (workspace_root / route_ref).write_text(
            json.dumps(route_payload),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_payload = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "route_back_evidence_candidate",
            "study_id": study_id,
            "stage_id": packet_stage_id,
            "stage_attempt_id": attempt_id,
            "route_back_evidence_ref": route_ref,
            "owner_answer_kind": "route_back_evidence_ref",
        }
        packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    old_packet = write_packet(
        "sat-old",
        packet_stage_id="write",
        route_stage_id="write",
        route_work_unit_id=work_unit_id,
        route_transaction_ref=transaction_id,
        mtime=1_000.0,
    )
    new_packet = write_packet(
        "sat-new",
        packet_stage_id=work_unit_id,
        route_stage_id=work_unit_id,
        route_work_unit_id=work_unit_id,
        route_transaction_ref=transaction_id,
        mtime=2_000.0,
    )
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
                "stage_attempt_id": "sat-old",
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": "sat-old",
                "closeout_refs": [str(old_packet)],
            }
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

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(new_packet)
    assert readback["paper_mission_transaction"]["transaction_id"] == transaction_id
    assert readback["paper_mission_transaction"]["stage_id"] == "write"
    assert readback["paper_mission_transaction"]["work_unit_id"] == work_unit_id
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new"

def test_terminalize_stage_prefers_richer_followthrough_closeout_over_newer_sparse_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
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
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration::"
        "followthrough::89b46ab394eb"
    )

    def write_packet(
        attempt_id: str,
        *,
        mtime: float,
        include_paper_delta: bool,
        include_progress_events: bool,
    ) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        route_payload = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "study_id": study_id,
            "stage_id": work_unit_id,
            "work_unit_id": work_unit_id,
            "stage_packet_ref": transaction_id,
            "owner_answer_kind": "route_back_evidence_ref",
        }
        if include_paper_delta:
            route_payload["paper_facing_delta_ref"] = (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "paper_facing_write_repair_candidate.json"
            )
        if include_progress_events:
            route_payload["progress_events_ref"] = (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "progress_events.jsonl"
            )
        (workspace_root / route_ref).write_text(
            json.dumps(route_payload),
            encoding="utf-8",
        )
        packet_payload = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "route_back_evidence_candidate",
            "study_id": study_id,
            "stage_id": work_unit_id,
            "stage_attempt_id": attempt_id,
            "route_back_evidence_ref": route_ref,
            "owner_answer_kind": "route_back_evidence_ref",
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": route_ref,
                "user_stage_log": "route-back candidate",
            },
        }
        if include_paper_delta:
            packet_payload["paper_facing_delta_ref"] = (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "paper_facing_write_repair_candidate.json"
            )
            packet_payload["route_impact"]["paper_facing_delta_ref"] = packet_payload[
                "paper_facing_delta_ref"
            ]
        if include_progress_events:
            packet_payload["progress_events_ref"] = (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "progress_events.jsonl"
            )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    richer_packet = write_packet(
        "sat-richer",
        mtime=1_000.0,
        include_paper_delta=True,
        include_progress_events=True,
    )
    write_packet(
        "sat-sparse",
        mtime=2_000.0,
        include_paper_delta=False,
        include_progress_events=False,
    )
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

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(richer_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-richer"

def test_terminalize_stage_prefers_route_back_with_owner_gate_context_over_newer_plain_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
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
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration::"
        "followthrough::89b46ab394eb"
    )

    def write_packet(
        attempt_id: str,
        *,
        mtime: float,
        enriched_route_back: bool,
    ) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        route_payload = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "study_id": study_id,
            "stage_id": work_unit_id,
            "work_unit_id": work_unit_id,
            "stage_packet_ref": transaction_id,
            "owner_answer_kind": "route_back_evidence_ref",
            "paper_facing_delta_ref": (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "paper_facing_write_repair_candidate.json"
            ),
        }
        if enriched_route_back:
            route_payload.update(
                {
                    "owner_gate_verdict": "Route-back evidence candidate only.",
                    "next_forced_paper_action": "MAS owner should consume this delta.",
                    "remaining_blocker": "MAS owner consumption remains unresolved.",
                    "source_evidence": {
                        "paper_mission_candidate_package_ref": (
                            "ops/medautoscience/paper_mission_candidate_package/"
                            "candidate/package_manifest.json"
                        )
                    },
                }
            )
        (workspace_root / route_ref).write_text(
            json.dumps(route_payload),
            encoding="utf-8",
        )
        packet_payload = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "route_back_evidence_candidate",
            "study_id": study_id,
            "stage_id": work_unit_id,
            "stage_attempt_id": attempt_id,
            "route_back_evidence_ref": route_ref,
            "owner_answer_kind": "route_back_evidence_ref",
            "paper_facing_delta_ref": (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "paper_facing_write_repair_candidate.json"
            ),
            "progress_events_ref": (
                f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                "progress_events.jsonl"
            ),
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": route_ref,
                "paper_facing_delta_ref": (
                    f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
                    "paper_facing_write_repair_candidate.json"
                ),
                "user_stage_log": "route-back candidate",
            },
        }
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(json.dumps(packet_payload), encoding="utf-8")
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    richer_packet = write_packet(
        "sat-owner-gate-context",
        mtime=1_000.0,
        enriched_route_back=True,
    )
    write_packet(
        "sat-plain-newer",
        mtime=2_000.0,
        enriched_route_back=False,
    )
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

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(richer_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-owner-gate-context"

def test_latest_stage_attempt_route_back_source_readback_prefers_current_terminal_attempt_over_newer_stale_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
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
        "med_autoscience.cli_parts.paper_mission_commands"
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
