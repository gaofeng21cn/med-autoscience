from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import (
    DM_CANARY_FIXTURE_ROOT,
    FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
    _assert_forbidden_authority_untouched,
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_candidate_manifest,
    _write_matching_domain_gate_closeout,
    _write_paper_source_fixture,
    _write_profile_with_study,
    _write_submission_milestone_package,
)
from tests.test_cli_cases.paper_mission_command_cases.materialized_readback_cases.test_direct_stage_attempt_and_inspect import (
    test_direct_stage_attempt_handoff_reads_owner_consumption_from_top_level_receipt,
    test_direct_terminal_closeout_can_override_next_action_source,
    test_direct_terminal_closeout_does_not_override_after_owner_consumed_route_checkpoint,
    test_paper_mission_inspect_projects_receipt_owner_consumption_without_materialized_mission,
    test_thin_legacy_stage_closure_keeps_owner_consumption_visible,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_consumed_route_checkpoint_suppresses_same_work_unit_domain_redrive() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    stage_closure_decision = {
        "authority_materialized": True,
        "stage_id": "write",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        },
    }
    owner_consumption_action = {
        "action_family": "paper.stage_closure.owner_consumption",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "stage_id": "write",
    }
    stale_domain_transition_action = {
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "stage_id": "write",
    }

    assert materialized_readback._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=stale_domain_transition_action,
    )
    assert paper_mission_commands._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=stale_domain_transition_action,
    )


def test_owner_repair_receipt_readback_exposes_story_surface_semantic_delta(
    tmp_path: Path,
) -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    terminalizer = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.stage_closure_terminalizer"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "study"
    stale_stage_ref = study_root / "ops" / "stage_closure_decision.json"
    stale_stage_ref.parent.mkdir(parents=True)
    stale_stage_ref.write_text("{}", encoding="utf-8")
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text("# repaired\n", encoding="utf-8")
    story_ref = {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"}
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "execution_status": "progress_delta_candidate",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "canonical_artifact_delta_refs": [story_ref],
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [story_ref],
            },
            "changed_artifact_refs": [story_ref],
        },
    )
    os.utime(stale_stage_ref, (4_000_000_000, 4_000_000_000))

    readback = materialized_readback._owner_repair_receipt_consumption_readback(
        study_root=study_root,
        study_id=study_id,
    )
    assert readback is not None
    assert readback["status"] == "owner_consumption_applied"
    assert readback["mas_receipt_consumption"]["status"] == "owner_consumed_mas_repair_delta"
    assert readback["stage_closure_decision"]["outcome"]["kind"] == "owner_receipt"
    assert readback["stage_closure_decision"]["semantic_delta"]["paper_delta_refs"] == [str(draft)]
    output_stage_readback = materialized_readback._stage_closure_ledger_readback_for_output(
        stage_closure_ledger_readback={
            "source_ref": str(stale_stage_ref),
            "semantic_delta": {"paper_delta_refs": []},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        receipt_owner_consumption_readback=readback,
    )
    assert output_stage_readback["semantic_delta"]["paper_delta_refs"] == [str(draft)]

    semantic_delta = terminalizer.stage_closure_semantic_delta(
        {"receipt_owner_consumption_readback": readback}
    )
    assert semantic_delta["paper_delta_refs"] == [str(draft)]
    assert semantic_delta["owner_decision_refs"]


def test_terminalizer_source_keeps_owner_repair_readback_over_stage_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    terminalizer_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.stage_closure_terminalizer_readback"
    )
    owner_repair_readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mas_receipt_consumption": {"status": "owner_consumed_mas_repair_delta"},
        "stage_closure_decision": {
            "source": "study_controller_owner_repair_receipt",
            "outcome": {"kind": "owner_receipt"},
        },
    }
    stale_stage_packet_readback = {
        "surface_kind": "paper_mission_stage_attempt_closeout_readback",
        "stage_closure_decision": {},
    }
    monkeypatch.setattr(
        terminalizer_readback,
        "_build_materialized_mission_readback_if_available",
        lambda **_: owner_repair_readback,
    )
    monkeypatch.setattr(
        terminalizer_readback,
        "_latest_stage_attempt_route_back_source_readback",
        lambda **_: stale_stage_packet_readback,
    )

    readback = terminalizer_readback._build_terminalizer_source_readback(
        profile=SimpleNamespace(
            workspace_root=tmp_path / "workspace",
            studies_root=tmp_path / "workspace" / "studies",
        ),
        profile_ref=tmp_path / "profile.toml",
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        source="test",
    )

    assert readback is owner_repair_readback


def test_non_submit_owner_receipt_suppresses_transaction_next_action() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )

    assert materialized_readback._stage_closure_owner_receipt_suppresses_transaction_next_action(
        stage_closure_decision={
            "outcome": {
                "kind": "owner_receipt",
                "can_submit": False,
                "next_action": "honor_paper_story_repair_owner_receipt",
            }
        },
        next_action_override=None,
    )
    assert not materialized_readback._stage_closure_owner_receipt_suppresses_transaction_next_action(
        stage_closure_decision={
            "outcome": {
                "kind": "owner_receipt",
                "package_kind": "submission_ready_package",
                "can_submit": True,
            }
        },
        next_action_override=None,
    )


def test_owner_consumed_route_checkpoint_yields_to_domain_transition_action() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    stage_closure_decision = {
        "authority_materialized": True,
        "stage_id": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current-write/stage_attempt_closeout_packet.json"
            ),
        },
    }
    owner_consumption_action = {
        "action_family": "paper.stage_closure.owner_consumption",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "stage_id": "write",
    }
    domain_transition_action = {
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "stage_id": "write",
    }
    receipt_owner_consumption = {
        "status": "owner_consumption_applied",
        "mas_receipt_consumption": {"status": "owner_consumed_route_checkpoint"},
    }

    assert not materialized_readback._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )
    assert not paper_mission_commands._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )


def test_stage_closure_next_action_suppresses_consumed_same_route_checkpoint() -> None:
    stage_closure_next_action = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.stage_closure_next_action"
    )
    stage_closure_decision = {
        "stage_id": "finalize",
        "work_unit_id": "provider_hosted_guarded_apply",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        },
    }
    receipt_owner_consumption = {
        "status": "owner_consumption_applied",
        "stage_closure_decision": {
            "stage_id": "finalize",
            "work_unit_id": "provider_hosted_guarded_apply",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        "mas_receipt_consumption": {"status": "owner_consumed_route_checkpoint"},
    }

    assert (
        stage_closure_next_action.next_action_for_stage_closure_decision(
            stage_closure_decision=stage_closure_decision,
            transaction_readback={"paper_mission_transaction": {}},
            receipt_owner_consumption_readback=receipt_owner_consumption,
        )
        is None
    )


def test_consumed_route_checkpoint_suppresses_stale_transaction_owner_consumption() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    fields = {
        "next_action": {
            "action_family": "paper.stage_closure.owner_consumption",
            "work_unit_id": "medical_prose_write_repair",
        },
        "canonical_next_action_source": "paper_mission_next_action_envelope",
        "paper_mission_transaction_readback": {
            "next_action": {"action_family": "paper.stage_closure.owner_consumption"}
        },
    }

    suppressed = (
        materialized_readback.suppress_consumed_route_checkpoint_transaction_next_action(
            transaction_output_fields=fields,
            receipt_owner_consumption_readback={
                "status": "owner_consumption_applied",
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint"
                },
            },
        )
    )

    assert "next_action" not in suppressed
    assert "canonical_next_action_source" not in suppressed
    assert "next_action" not in suppressed["paper_mission_transaction_readback"]


def test_owner_consumed_route_checkpoint_yields_to_same_stage_new_work_unit() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    stage_closure_decision = {
        "authority_materialized": True,
        "stage_id": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current-write/stage_attempt_closeout_packet.json"
            ),
        },
    }
    owner_consumption_action = {
        "action_family": "paper.stage_closure.owner_consumption",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "stage_id": "write",
    }
    domain_transition_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
        "stage_id": "write",
    }
    receipt_owner_consumption = {
        "status": "owner_consumption_applied",
        "mas_receipt_consumption": {"status": "owner_consumed_route_checkpoint"},
    }

    assert not materialized_readback._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )
    assert not paper_mission_commands._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )


def test_owner_consumed_route_checkpoint_yields_to_next_stage_work_unit() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    stage_closure_decision = {
        "authority_materialized": True,
        "stage_id": "submission_milestone_candidate",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        },
    }
    owner_consumption_action = {
        "action_family": "paper.stage_closure.owner_consumption",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "stage_id": "submission_milestone_candidate",
    }
    domain_transition_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "stage_id": "write",
    }
    receipt_owner_consumption = {
        "status": "owner_consumption_applied",
        "mas_receipt_consumption": {"status": "owner_consumed_route_checkpoint"},
    }

    assert not materialized_readback._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )
    assert not paper_mission_commands._stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=owner_consumption_action,
        domain_transition_next_action=domain_transition_action,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )


def test_owner_consumption_alignment_updates_top_level_and_current_carriers() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    stale_closeout_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-stale-write/stage_attempt_closeout_packet.json"
    )
    current_closeout_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current-write/stage_attempt_closeout_packet.json"
    )

    def build_fields() -> dict[str, object]:
        return {
            "opl_runtime_carrier_readback": {
                "opl_transition_receipt": {
                    "stage_attempt_id": "sat-stale-write",
                    "stage_attempt_ref": "opl://stage-attempts/sat-stale-write",
                    "work_unit_id": work_unit_id,
                },
                "receipt_evidence": {
                    "receipt_ref": "opl://stage-attempts/sat-stale-write",
                    "stage_attempt_ref": "opl://stage-attempts/sat-stale-write",
                    "runtime_closeout_ref": stale_closeout_ref,
                },
                "terminal_closeout": {
                    "stage_attempt_id": "sat-stale-write",
                    "work_unit_id": work_unit_id,
                    "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                    "closeout_ref": stale_closeout_ref,
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                },
            },
            "current_opl_runtime_carrier_readback": {
                "opl_transition_receipt": {
                    "stage_attempt_id": "sat-current-write",
                    "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
                    "work_unit_id": work_unit_id,
                },
                "receipt_evidence": {
                    "receipt_ref": "opl://stage-attempts/sat-current-write",
                    "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
                    "runtime_closeout_ref": current_closeout_ref,
                },
                "terminal_closeout": {
                    "stage_attempt_id": "sat-current-write",
                    "work_unit_id": work_unit_id,
                    "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                    "closeout_ref": current_closeout_ref,
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                },
            },
            "domain_transition_direct_stage_attempt": {
                "opl_runtime_carrier_readback": {
                    "terminal_closeout": {
                        "stage_attempt_id": "sat-current-write",
                        "work_unit_id": work_unit_id,
                        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                        "closeout_ref": current_closeout_ref,
                    }
                }
            },
            "paper_mission_transaction_readback": {
                "paper_mission_transaction": {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "mission_id": "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::write",
                    "stage_id": "write",
                    "transaction_id": "paper-mission-transaction::dm003::write",
                    "artifact_delta_refs": [],
                    "paper_audit_pack_refs": {
                        family: [
                            {
                                "ref_id": f"{family}::1",
                                "ref_kind": "paper_audit_pack_ref",
                                "uri": f"submission-milestone-package:{family}",
                            }
                        ]
                        for family in (
                            "analysis_rationale_log",
                            "decision_trace",
                            "evidence_ledger_delta",
                            "review_ledger_delta",
                            "revision_log_delta",
                            "failed_path_ledger",
                            "artifact_lineage",
                            "reproducibility_refs",
                        )
                    },
                },
                "opl_runtime_carrier_readback": {
                    "terminal_closeout": {
                        "stage_attempt_id": "sat-stale-write",
                        "work_unit_id": work_unit_id,
                        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                        "closeout_ref": stale_closeout_ref,
                    },
                    "mas_receipt_consumption": {
                        "surface_kind": "mas_receipt_consumption_projection",
                        "status": "requires_mas_owner_consumption",
                    },
                }
            },
        }

    receipt_owner_consumption = {
        "status": "owner_consumption_applied",
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-current-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
            "runtime_closeout_ref": current_closeout_ref,
        },
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-current-write",
            "stage_attempt_ref": "opl://stage-attempts/sat-current-write",
            "work_unit_id": work_unit_id,
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
            "route_checkpoint_evidence_ref": current_closeout_ref,
        },
    }

    for module in (materialized_readback, paper_mission_commands):
        aligned = module._align_current_carrier_owner_consumption(
            transaction_output_fields=build_fields(),
            receipt_owner_consumption_readback=receipt_owner_consumption,
        )
        assert (
            aligned["opl_runtime_carrier_readback"]["terminal_closeout"]["stage_attempt_id"]
            == "sat-current-write"
        )
        assert (
            aligned["current_opl_runtime_carrier_readback"]["terminal_closeout"][
                "stage_attempt_id"
            ]
            == "sat-current-write"
        )
        assert (
            aligned["domain_transition_direct_stage_attempt"][
                "opl_runtime_carrier_readback"
            ]["terminal_closeout"]["stage_attempt_id"]
            == "sat-current-write"
        )
        assert (
            aligned["paper_mission_transaction_readback"]["opl_runtime_carrier_readback"][
                "terminal_closeout"
            ]["stage_attempt_id"]
            == "sat-current-write"
        )
        assert aligned["terminal_owner_gate"]["stage_attempt_id"] == "sat-current-write"
        assert (
            aligned["terminal_owner_gate_authority_readback"]["terminal_owner_gate"][
                "stage_attempt_id"
            ]
            == "sat-current-write"
        )
        assert (
            aligned["terminal_owner_gate_owner_answer_readback"]["terminal_owner_gate"][
                "stage_attempt_id"
            ]
            == "sat-current-write"
        )
        assert (
            aligned["opl_runtime_carrier_readback"]["mas_receipt_consumption"]["status"]
            == "owner_consumed_route_checkpoint"
        )


def test_successor_runtime_readback_is_not_replaced_by_previous_owner_consumption() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    owner_consumption_ref = "/tmp/receipt_owner_consumption.json"
    successor_readback = {
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-successor",
            "stage_attempt_ref": "opl://stage-attempts/sat-successor",
            "work_unit_id": "medical_prose_write_repair",
        },
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-successor",
            "stage_attempt_ref": "opl://stage-attempts/sat-successor",
            "runtime_closeout_ref": "/tmp/sat-successor-closeout.json",
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
        },
    }
    fields = {
        "current_opl_runtime_carrier_readback": dict(successor_readback),
        "domain_transition_direct_stage_attempt": {
            "opl_route_handoff": {
                "owner_consumption_readback_ref": owner_consumption_ref,
            },
            "opl_runtime_carrier_readback": dict(successor_readback),
        },
    }
    owner_consumption = {
        "source_ref": owner_consumption_ref,
        "status": "owner_consumption_applied",
        "mas_receipt_consumption": {
            "status": "owner_consumed_route_checkpoint",
            "route_checkpoint_evidence_ref": "/tmp/old-closeout.json",
        },
        "receipt_evidence": {
            "stage_attempt_ref": "opl://stage-attempts/sat-old",
            "receipt_ref": "opl://stage-attempts/sat-old",
            "runtime_closeout_ref": "/tmp/old-closeout.json",
        },
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-old",
            "stage_attempt_ref": "opl://stage-attempts/sat-old",
            "work_unit_id": "medical_prose_write_repair",
        },
        "stage_closure_decision": {
            "work_unit_id": "medical_prose_write_repair",
        },
    }

    for module in (materialized_readback, paper_mission_commands):
        aligned = module._align_current_carrier_owner_consumption(
            transaction_output_fields=fields,
            receipt_owner_consumption_readback=owner_consumption,
        )
        assert (
            aligned["current_opl_runtime_carrier_readback"]["opl_transition_receipt"][
                "stage_attempt_id"
            ]
            == "sat-successor"
        )
        assert (
            aligned["domain_transition_direct_stage_attempt"][
                "opl_runtime_carrier_readback"
            ]["opl_transition_receipt"]["stage_attempt_id"]
            == "sat-successor"
        )


def test_same_attempt_direct_readback_is_aligned_with_owner_consumption() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    owner_consumption_ref = "/tmp/receipt_owner_consumption.json"
    consumed_attempt_readback = {
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-consumed",
            "stage_attempt_ref": "opl://stage-attempts/sat-consumed",
            "work_unit_id": "medical_prose_write_repair",
        },
        "receipt_evidence": {
            "receipt_ref": "opl://stage-attempts/sat-consumed",
            "stage_attempt_ref": "opl://stage-attempts/sat-consumed",
            "runtime_closeout_ref": "/tmp/sat-consumed-closeout.json",
        },
        "terminal_closeout": {
            "stage_attempt_id": "sat-consumed",
            "work_unit_id": "medical_prose_write_repair",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
            "closeout_ref": "/tmp/sat-consumed-closeout.json",
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
        },
    }
    fields = {
        "current_opl_runtime_carrier_readback": dict(consumed_attempt_readback),
        "domain_transition_direct_stage_attempt": {
            "opl_route_handoff": {
                "owner_consumption_readback_ref": owner_consumption_ref,
            },
            "opl_runtime_carrier_readback": dict(consumed_attempt_readback),
        },
    }
    owner_consumption = {
        "source_ref": owner_consumption_ref,
        "status": "owner_consumption_applied",
        "mas_receipt_consumption": {
            "status": "owner_consumed_route_checkpoint",
            "receipt_evidence_ref": "opl://stage-attempts/sat-consumed",
            "route_checkpoint_evidence_ref": "/tmp/sat-consumed-closeout.json",
        },
        "receipt_evidence": {
            "stage_attempt_ref": "opl://stage-attempts/sat-consumed",
            "receipt_ref": "opl://stage-attempts/sat-consumed",
            "runtime_closeout_ref": "/tmp/sat-consumed-closeout.json",
        },
        "opl_transition_receipt": {
            "stage_attempt_id": "sat-consumed",
            "stage_attempt_ref": "opl://stage-attempts/sat-consumed",
            "work_unit_id": "medical_prose_write_repair",
        },
        "stage_closure_decision": {
            "work_unit_id": "medical_prose_write_repair",
            "opl_closeout": {
                "stage_attempt_id": "sat-consumed",
            },
        },
    }

    for module in (materialized_readback, paper_mission_commands):
        aligned = module._align_current_carrier_owner_consumption(
            transaction_output_fields=fields,
            receipt_owner_consumption_readback=owner_consumption,
        )
        assert (
            aligned["current_opl_runtime_carrier_readback"]["mas_receipt_consumption"][
                "status"
            ]
            == "owner_consumed_route_checkpoint"
        )
        assert (
            aligned["domain_transition_direct_stage_attempt"][
                "opl_runtime_carrier_readback"
            ]["mas_receipt_consumption"]["status"]
            == "owner_consumed_route_checkpoint"
        )
