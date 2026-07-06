from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    align_carrier_readback_with_owner_consumption,
    materialize_receipt_owner_consumption,
)

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def _readback(
    *,
    study_id: str,
    stage_outcome: str,
    transition_kind: str | None,
    package_kind: str,
    can_submit: bool,
    consumption_next_legal_action: str | None = None,
) -> dict[str, object]:
    outcome: dict[str, object] = {
        "kind": stage_outcome,
        "next_legal_action": "record_typed_blocker",
    }
    if transition_kind:
        outcome["transition_kind"] = transition_kind
    if consumption_next_legal_action is None:
        consumption_next_legal_action = (
            "record_typed_blocker"
            if stage_outcome == "typed_blocker"
            else "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        )
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "study_id": study_id,
        "mission_state": "consumed",
        "current_package": {
            "status": "current",
            "package_kind": package_kind,
            "can_submit": can_submit,
            "quality_gate_status": "clear" if can_submit else "blocked",
            "known_blockers": [] if can_submit else ["bundle_build_allowed_false"],
            "root": f"/tmp/{study_id}/manuscript/current_package",
            "zip_path": f"/tmp/{study_id}/manuscript/current_package.zip",
            "zip_exists": True,
        },
        "stage_closure_decision": {
            "decision_ref": f"mas://paper-mission/{study_id}/stage-closure",
            "outcome": outcome,
        },
        "stage_closure_outcome": stage_outcome,
        "durable_mission_stop_guard": {
            "durable_stop_allowed": False,
        },
        "opl_runtime_carrier_readback": {
            "runtime_readback_status": "terminal_closeout_observed",
            "receipt_evidence": {
                "receipt_kind": "opl_transition_receipt",
                "receipt_ref": "opl://stage-attempts/sat-receipt",
                "impact_receipt_kind": "mas_impact_receipt",
                "impact_receipt_ref": "opl://stage-attempts/sat-receipt/mas-impact",
                "runtime_closeout_ref": (
                    "opl://family-runtime/tasks/frt-receipt/terminal-closeout-readback"
                ),
                "can_claim_paper_progress": False,
            },
            "opl_transition_receipt": {
                "surface_kind": "opl_transition_receipt",
                "receipt_status": "terminal_closeout_observed",
                "role": "transport_receipt_only",
                "task_id": "frt-receipt",
                "task_status": "blocked",
                "stage_attempt_id": "sat-receipt",
                "stage_attempt_ref": "opl://stage-attempts/sat-receipt",
                "closeout_receipt_status": "accepted_typed_closeout",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "can_claim_paper_progress": False,
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "next_legal_action": consumption_next_legal_action,
                "forbidden_next_action": "synonymous_route_back_redrive",
                "durable_stop_allowed": False,
                "can_claim_paper_progress": False,
                "can_claim_publication_ready": False,
            },
        },
    }


def test_align_carrier_readback_projects_owner_consumed_status_for_same_attempt() -> None:
    carrier = {
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-current",
            "stage_attempt_ref": "opl://stage-attempts/sat-current",
        },
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-current",
            "runtime_closeout_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/stage_attempt_closeout_packet.json"
            ),
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
        },
    }
    owner_consumption = {
        "status": "owner_consumption_applied",
        "source_ref": "/tmp/receipt_owner_consumption.json",
        "receipt_evidence": {
            "surface_kind": "mas_receipt_evidence",
            "receipt_ref": "opl://stage-attempts/sat-current",
            "stage_attempt_ref": "opl://stage-attempts/sat-current",
            "runtime_closeout_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/stage_attempt_closeout_packet.json"
            ),
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/stage_attempt_closeout_packet.json"
            ),
        },
    }

    aligned = align_carrier_readback_with_owner_consumption(
        carrier_readback=carrier,
        receipt_owner_consumption_readback=owner_consumption,
    )

    assert aligned["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert aligned["owner_consumption_status"] == "owner_consumed_route_checkpoint"
    assert aligned["owner_consumption_readback_ref"] == (
        "/tmp/receipt_owner_consumption.json"
    )


def test_align_carrier_readback_keeps_newer_unconsumed_attempt_pending() -> None:
    carrier = {
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-newer",
            "stage_attempt_ref": "opl://stage-attempts/sat-newer",
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
        },
    }
    owner_consumption = {
        "status": "owner_consumption_applied",
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-consumed",
            "stage_attempt_ref": "opl://stage-attempts/sat-consumed",
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-consumed/stage_attempt_closeout_packet.json"
            ),
        },
    }

    aligned = align_carrier_readback_with_owner_consumption(
        carrier_readback=carrier,
        receipt_owner_consumption_readback=owner_consumption,
    )

    assert aligned["mas_receipt_consumption"]["status"] == (
        "requires_mas_owner_consumption"
    )
    assert "owner_consumption_status" not in aligned


def test_align_carrier_readback_projects_owner_consumed_current_attempt() -> None:
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    carrier = {
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "runtime_readback_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-stale-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale-write",
            "work_unit_id": work_unit_id,
        },
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-stale-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-stale-write",
            "runtime_closeout_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-stale-write/stage_attempt_closeout_packet.json"
            ),
        },
        "terminal_closeout": {
            "stage_attempt_id": "sat-stale-write",
            "work_unit_id": work_unit_id,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
        },
    }
    current_closeout_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-write/stage_attempt_closeout_packet.json"
    )
    owner_consumption = {
        "status": "owner_consumption_applied",
        "source_ref": "/tmp/receipt_owner_consumption.json",
        "receipt_evidence": {
            "receipt_ref": "temporal://attempt/sat-current-write",
            "stage_attempt_ref": "temporal://attempt/sat-current-write",
            "runtime_closeout_ref": current_closeout_ref,
        },
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-current-write",
            "stage_attempt_ref": "temporal://attempt/sat-current-write",
        },
        "stage_closure_decision": {
            "work_unit_id": work_unit_id,
            "opl_closeout": {
                "stage_attempt_id": "sat-current-write",
                "work_unit_id": work_unit_id,
            },
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "runtime_closeout_ref": current_closeout_ref,
            "route_checkpoint_evidence_ref": current_closeout_ref,
        },
    }

    aligned = align_carrier_readback_with_owner_consumption(
        carrier_readback=carrier,
        receipt_owner_consumption_readback=owner_consumption,
    )

    assert aligned["owner_consumption_status"] == "owner_consumed_route_checkpoint"
    assert aligned["owner_consumption_aligned_current_readback"] is True
    assert aligned["owner_consumed_stage_attempt_id"] == "sat-current-write"
    assert aligned["superseded_terminal_stage_attempt_id"] == "sat-stale-write"
    assert aligned["opl_transition_receipt"]["stage_attempt_id"] == "sat-current-write"
    assert aligned["receipt_evidence"]["runtime_closeout_ref"] == current_closeout_ref
    assert aligned["terminal_closeout"]["stage_attempt_id"] == "sat-current-write"
    assert aligned["terminal_closeout"]["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )


def test_materialize_receipt_owner_consumption_prefers_current_carrier_route_back_closeout(
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    current_closeout_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-followthrough/stage_attempt_closeout_packet.json"
    )
    readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "study_id": study_id,
        "next_action": {
            "action_family": "paper.stage_closure.owner_consumption",
            "outcome_ref": "/tmp/stale-stage-closure.json",
        },
        "stage_closure_decision": {
            "decision_ref": "/tmp/stale-stage-closure.json",
            "stage_id": "write",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "opl_closeout": {
                "stage_attempt_id": "sat-stale-write",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        "current_package": {
            "status": "missing",
            "can_submit": False,
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-stale-write",
                "closeout_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-stale-write/stage_attempt_closeout_packet.json"
                ),
            },
        },
        "current_opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current-followthrough",
                "closeout_ref": current_closeout_ref,
                "stage_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "receipt_evidence": {
                "receipt_ref": "opl://stage-attempts/sat-current-followthrough",
                "stage_attempt_ref": "opl://stage-attempts/sat-current-followthrough",
                "runtime_closeout_ref": current_closeout_ref,
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-followthrough/route_back_evidence_packet.json"
                ),
            },
            "opl_transition_receipt": {
                "surface_kind": "opl_transition_receipt",
                "receipt_status": "route_back_evidence_closeout_observed",
                "stage_attempt_id": "sat-current-followthrough",
                "stage_attempt_ref": "opl://stage-attempts/sat-current-followthrough",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-followthrough/route_back_evidence_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "can_claim_paper_progress": False,
                "can_claim_publication_ready": False,
            },
        },
    }

    applied = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref="/tmp/profile.toml",
        apply_mode="route_checkpoint",
        source="test",
    )

    assert applied["status"] == "owner_consumption_applied"
    assert applied["receipt_evidence"]["runtime_closeout_ref"] == current_closeout_ref
    assert applied["opl_transition_receipt"]["stage_attempt_id"] == (
        "sat-current-followthrough"
    )
    assert applied["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current-followthrough"
    )
    assert applied["mas_receipt_consumption"]["route_checkpoint_evidence_ref"] == (
        current_closeout_ref
    )


def test_receipt_owner_consumption_classifies_dm002_typed_blocker_without_authority_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="typed_blocker",
                transition_kind=None,
                package_kind="current_package",
                can_submit=False,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_evidence_materialized"
    assert payload["write_permitted"] is False
    assert payload["authority_materialized"] is False
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "record_typed_blocker_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["required_authority_surface_exists"] is True
    assert payload["owner_consumption_verdict"]["implemented_surface_role"] == (
        "mas_owner_consumption_authority_apply_surface"
    )
    assert payload["owner_consumption_verdict"]["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert payload["current_package"]["can_submit"] is False
    assert payload["submission_ready_claim_authorized"] is False
    assert "publication_eval/latest.json" in payload["forbidden_authority_writes"]


def test_receipt_owner_consumption_prefers_current_direct_stage_carrier_over_legacy(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
    )
    legacy_carrier = readback["opl_runtime_carrier_readback"]
    legacy_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-old"
    legacy_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    legacy_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    legacy_carrier["receipt_evidence"]["runtime_closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
        "stage_attempt_closeout_packet.json"
    )
    legacy_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    legacy_carrier["receipt_evidence"]["typed_runtime_blocker_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
        "stage_attempt_closeout_packet.json"
    )
    legacy_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    legacy_carrier["mas_receipt_consumption"]["typed_runtime_blocker_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
        "stage_attempt_closeout_packet.json"
    )
    current_carrier = json.loads(json.dumps(legacy_carrier))
    current_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-current"
    current_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["runtime_closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-current/"
        "stage_attempt_closeout_packet.json"
    )
    current_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["typed_runtime_blocker_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-current/"
        "stage_attempt_closeout_packet.json"
    )
    current_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["mas_receipt_consumption"]["typed_runtime_blocker_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-current/"
        "stage_attempt_closeout_packet.json"
    )
    readback["current_opl_runtime_carrier_readback"] = current_carrier

    payload = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref="profile.toml",
        output_root=tmp_path / "receipt_owner_consumption",
        apply_mode="typed_blocker",
        source="test",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current"
    )
    assert payload["stage_closure"]["typed_blocker_evidence_ref"] == (
        "ops/medautoscience/paper_mission_stage_attempts/sat-current/"
        "stage_attempt_closeout_packet.json"
    )
    assert payload["owner_consumption_verdict"]["receipt_ref"] == (
        "opl://stage-attempts/sat-current"
    )


def test_receipt_owner_consumption_prefers_unconsumed_terminal_over_consumed_current(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    terminal_carrier = readback["opl_runtime_carrier_readback"]
    terminal_closeout_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-new/"
        "stage_attempt_closeout_packet.json"
    )
    terminal_carrier["terminal_closeout"] = {
        "stage_attempt_id": "sat-new",
        "work_unit_id": "medical_prose_write_repair",
        "closeout_ref": terminal_closeout_ref,
    }
    terminal_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-new"
    terminal_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-new"
    )
    terminal_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-new"
    )
    terminal_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-new"
    )
    terminal_carrier["receipt_evidence"]["runtime_closeout_ref"] = terminal_closeout_ref
    terminal_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-new"
    )
    terminal_carrier["mas_receipt_consumption"][
        "route_back_evidence_ref"
    ] = "ops/medautoscience/paper_mission_stage_attempts/sat-new/route_back_evidence_packet.json"
    terminal_carrier["mas_receipt_consumption"][
        "route_checkpoint_evidence_ref"
    ] = terminal_closeout_ref

    current_carrier = json.loads(json.dumps(terminal_carrier))
    current_carrier["terminal_closeout"]["stage_attempt_id"] = "sat-old"
    current_carrier["terminal_closeout"]["closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
        "stage_attempt_closeout_packet.json"
    )
    current_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-old"
    current_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    current_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    current_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-old"
    )
    current_carrier["receipt_evidence"]["runtime_closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
        "stage_attempt_closeout_packet.json"
    )
    current_carrier["mas_receipt_consumption"].update(
        {
            "status": "owner_consumed_route_checkpoint",
            "receipt_evidence_ref": "opl://stage-attempts/sat-old",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/sat-old/"
                "stage_attempt_closeout_packet.json"
            ),
        }
    )
    readback["current_opl_runtime_carrier_readback"] = current_carrier

    payload = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref="profile.toml",
        output_root=tmp_path / "receipt_owner_consumption",
        apply_mode="route_checkpoint",
        source="test",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == "opl://stage-attempts/sat-new"
    assert payload["opl_transition_receipt"]["stage_attempt_id"] == "sat-new"
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-new"
    )
    assert payload["mas_receipt_consumption"]["route_checkpoint_evidence_ref"] == (
        terminal_closeout_ref
    )


def test_receipt_owner_consumption_prefers_newer_unconsumed_terminal_over_unconsumed_current(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    old_closeout = tmp_path / "sat-current" / "stage_attempt_closeout_packet.json"
    new_closeout = tmp_path / "sat-terminal" / "stage_attempt_closeout_packet.json"
    old_closeout.parent.mkdir(parents=True)
    new_closeout.parent.mkdir(parents=True)
    old_closeout.write_text("{}", encoding="utf-8")
    new_closeout.write_text("{}", encoding="utf-8")
    os.utime(old_closeout, (1_000, 1_000))
    os.utime(new_closeout, (2_000, 2_000))

    terminal_carrier = readback["opl_runtime_carrier_readback"]
    terminal_carrier["terminal_closeout"] = {
        "stage_attempt_id": "sat-terminal",
        "closeout_ref": str(new_closeout),
    }
    terminal_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-terminal"
    terminal_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["receipt_evidence"]["runtime_closeout_ref"] = str(new_closeout)
    terminal_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["mas_receipt_consumption"][
        "route_checkpoint_evidence_ref"
    ] = str(new_closeout)

    current_carrier = json.loads(json.dumps(terminal_carrier))
    current_carrier["terminal_closeout"]["stage_attempt_id"] = "sat-current"
    current_carrier["terminal_closeout"]["closeout_ref"] = str(old_closeout)
    current_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-current"
    current_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["receipt_evidence"]["runtime_closeout_ref"] = str(old_closeout)
    current_carrier["mas_receipt_consumption"]["receipt_evidence_ref"] = (
        "opl://stage-attempts/sat-current"
    )
    current_carrier["mas_receipt_consumption"][
        "route_checkpoint_evidence_ref"
    ] = str(old_closeout)
    readback["current_opl_runtime_carrier_readback"] = current_carrier

    payload = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref="profile.toml",
        output_root=tmp_path / "receipt_owner_consumption",
        apply_mode="route_checkpoint",
        source="test",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-terminal"
    )
    assert payload["opl_transition_receipt"]["stage_attempt_id"] == "sat-terminal"
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-terminal"
    )
    assert payload["mas_receipt_consumption"]["route_checkpoint_evidence_ref"] == str(
        new_closeout
    )


def test_receipt_owner_consumption_prefers_terminal_receipt_over_running_projection(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
    )
    readback["current_opl_runtime_carrier_readback"] = {
        "carrier_status": "opl_runtime_attempt_running_observed",
        "runtime_readback_status": "running_attempt_observed",
        "running_attempt": {
            "task_id": "frt-running",
            "stage_attempt_id": "sat-running",
        },
    }
    terminal_carrier = readback["opl_runtime_carrier_readback"]
    terminal_carrier["opl_transition_receipt"]["stage_attempt_id"] = "sat-terminal"
    terminal_carrier["opl_transition_receipt"]["stage_attempt_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["receipt_evidence"]["receipt_ref"] = (
        "opl://stage-attempts/sat-terminal"
    )
    terminal_carrier["receipt_evidence"]["runtime_closeout_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-terminal/"
        "stage_attempt_closeout_packet.json"
    )
    terminal_carrier["receipt_evidence"]["typed_runtime_blocker_ref"] = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-terminal/"
        "typed_source_readiness_blocker_packet.json"
    )

    payload = materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref="profile.toml",
        output_root=tmp_path / "receipt_owner_consumption",
        apply_mode="typed_blocker",
        source="test",
    )

    assert payload["status"] == "owner_consumption_applied"
    assert payload["receipt_evidence"]["receipt_ref"] == (
        "opl://stage-attempts/sat-terminal"
    )
    assert payload["stage_closure"]["typed_blocker_evidence_ref"] == (
        "ops/medautoscience/paper_mission_stage_attempts/sat-terminal/"
        "typed_source_readiness_blocker_packet.json"
    )


def test_receipt_owner_consumption_keeps_dm003_submission_ready_mirror_non_terminal(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="submission_ready_package",
                can_submit=True,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(tmp_path / "receipt-owner-consumption"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["can_claim_submission_ready"] is False
    assert payload["owner_consumption_verdict"]["durable_stop_allowed"] is False
    assert payload["output_manifest"]["writes_authority"] is False
    packet_ref = Path(payload["output_manifest"]["packet_ref"])
    assert packet_ref.exists()
    assert json.loads(packet_ref.read_text(encoding="utf-8"))[
        "submission_ready_claim_authorized"
    ] is False


def test_receipt_owner_consumption_fails_closed_without_opl_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "missing-receipt.json"
    readback_file.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_materialized_readback",
                "study_id": study_id,
                "stage_closure_decision": {"outcome": {"kind": "typed_blocker"}},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_missing_consumable_opl_receipt"
    assert payload["readback_validation"]["missing_required_fields"] == [
        "opl_runtime_carrier_readback",
        "opl_runtime_carrier_readback.opl_transition_receipt",
        "opl_runtime_carrier_readback.receipt_evidence",
        "opl_runtime_carrier_readback.mas_receipt_consumption",
    ]
    assert payload["implementation_gap"]["gap_kind"] == (
        "mas_owner_consumption_authority_apply_surface_missing"
    )


def test_receipt_owner_consumption_accepts_top_level_receipt_projection(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
    )
    carrier = readback["opl_runtime_carrier_readback"]
    assert isinstance(carrier, dict)
    readback["receipt_evidence"] = carrier.pop("receipt_evidence")
    readback["opl_transition_receipt"] = carrier.pop("opl_transition_receipt")
    readback["mas_receipt_consumption"] = carrier.pop("mas_receipt_consumption")
    readback_file = tmp_path / "top-level-receipt.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_evidence_materialized"
    assert payload["readback_validation"]["valid"] is True
    assert payload["owner_consumption_verdict"]["required_authority_surface_exists"] is True


def test_receipt_owner_consumption_accepts_already_owner_consumed_route_checkpoint_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-owner-consumed-readback.json"
    readback = _readback(
        study_id=study_id,
        stage_outcome="next_stage_transition",
        transition_kind="route_back_candidate_checkpoint",
        package_kind="current_package",
        can_submit=False,
    )
    carrier = readback["opl_runtime_carrier_readback"]
    checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-receipt/stage_attempt_closeout_packet.json"
    )
    carrier["mas_receipt_consumption"].update(
        {
            "status": "owner_consumed_route_checkpoint",
            "owner_result_kind": "route_checkpoint",
            "route_checkpoint_evidence_ref": checkpoint_ref,
        }
    )
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_already_materialized"
    assert payload["readback_validation"]["valid"] is True
    assert payload["readback_validation"]["observed_consumption_status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert payload["owner_consumption_already_materialized"] is True
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )

    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(output_root),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    applied = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert applied["status"] == "owner_consumption_applied"
    assert applied["apply_mode"] == "route_checkpoint"
    assert applied["readback_validation"]["valid"] is True
    assert applied["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
