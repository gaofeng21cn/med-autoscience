from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from med_autoscience.cli_parts import paper_mission_commands as commands
from med_autoscience.cli_parts.paper_mission_command_parts.drive_readback import (
    build_paper_mission_drive_readback,
    _drive_owner_action_stop_readback,
    _drive_should_submit_direct_next_action,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    opl_runtime_submission,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    materialized_mission_readback as materialized_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    direct_next_action_handoff as direct_handoff,
)
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_drive_still_submits_same_work_unit_after_owner_consumed_route_checkpoint() -> None:
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "owner": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
    }
    readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "canonical_next_action_source": "domain_transition.next_action",
        "next_action": next_action,
        "current_opl_runtime_carrier_readback": {
            "opl_transition_receipt": {
                "work_unit_id": (
                    "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
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
        },
    }
    different_work_unit = {
        **readback,
        "next_action": {
            **next_action,
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
    }

    assert _drive_should_submit_direct_next_action(readback) is True
    assert _drive_should_submit_direct_next_action(different_work_unit) is True


def test_paper_mission_drive_does_not_resubmit_consumed_current_terminal_closeout() -> None:
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
    }
    readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "canonical_next_action_source": "domain_transition.next_action",
        "next_action": next_action,
        "current_opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current",
                "work_unit_id": "medical_prose_write_repair",
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/route_back_evidence_packet.json"
                ),
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/stage_attempt_closeout_packet.json"
                ),
            },
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "route_back_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/route_back_evidence_packet.json"
            ),
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/stage_attempt_closeout_packet.json"
            ),
        },
    }
    different_work_unit = {
        **readback,
        "next_action": {
            **next_action,
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
    }

    assert _drive_should_submit_direct_next_action(readback) is False
    assert _drive_should_submit_direct_next_action(different_work_unit) is True


def test_paper_mission_drive_does_not_resubmit_consumed_runtime_route_readback() -> None:
    readback = {
        "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
        "source": "paper_mission_consumption_ledger",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
            "action_kind": "submit_to_opl_runtime",
            "owner": "one-person-lab",
            "work_unit_id": "medical_prose_write_repair",
            "authority_source": "mas_next_action_compiler",
            "authority_boundary": {
                "can_submit_to_opl_runtime": True,
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current",
                "stage_id": "medical_prose_write_repair",
                "work_unit_id": None,
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/route_back_evidence_packet.json"
                ),
            },
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "owner_consumed_route_checkpoint",
            "route_back_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/route_back_evidence_packet.json"
            ),
        },
    }

    assert _drive_should_submit_direct_next_action(readback) is False


def test_paper_mission_drive_does_not_resubmit_owner_consumed_terminal_closeout() -> None:
    readback = {
        "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
            "action_kind": "submit_to_opl_runtime",
            "owner": "one-person-lab",
            "work_unit_id": "medical_prose_write_repair",
            "authority_source": "mas_next_action_compiler",
            "authority_boundary": {
                "can_submit_to_opl_runtime": True,
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current",
                "work_unit_id": "medical_prose_write_repair",
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/route_back_evidence_packet.json"
                ),
            },
        },
    }

    assert _drive_should_submit_direct_next_action(readback) is False


def test_paper_mission_drive_stops_instead_of_repackaging_consumed_terminal_closeout(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile = SimpleNamespace(
        name="DM-CVD",
        studies_root=tmp_path / "workspace" / "studies",
    )
    (Path(profile.studies_root) / study_id).mkdir(parents=True)
    payload = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
        output_root=tmp_path / "workspace" / "ops" / "medautoscience" / "drive",
        source="test",
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::domain-transition",
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_type": "request_opl_stage_attempt",
                "action_family": "paper.write.prose_repair",
                "owner": "write",
                "work_unit_id": "medical_prose_write_repair",
            },
            "current_opl_runtime_carrier_readback": {
                "terminal_closeout": {
                    "stage_attempt_id": "sat-current",
                    "work_unit_id": "medical_prose_write_repair",
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "route_back_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current/route_back_evidence_packet.json"
                    ),
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current/stage_attempt_closeout_packet.json"
                    ),
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/route_back_evidence_packet.json"
                ),
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/stage_attempt_closeout_packet.json"
                ),
            },
        },
    )

    assert payload is not None
    assert payload["drive_mode"] == "owner_action_ready_no_redrive"
    assert payload["drive_result"]["reason"] == (
        "current_opl_route_back_checkpoint_already_owner_consumed_no_redrive"
    )
    assert payload["drive_result"]["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )


def test_paper_mission_drive_stops_on_consumed_terminal_closeout_from_transaction_readback(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile = SimpleNamespace(
        name="DM-CVD",
        studies_root=tmp_path / "workspace" / "studies",
    )
    (Path(profile.studies_root) / study_id).mkdir(parents=True)
    payload = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
        output_root=tmp_path / "workspace" / "ops" / "medautoscience" / "drive",
        source="test",
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::domain-transition",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": "medical_prose_write_repair",
                "authority_source": "mas_next_action_compiler",
                "authority_boundary": {
                    "can_submit_to_opl_runtime": True,
                },
            },
            "opl_runtime_carrier_readback": {
                "terminal_closeout": {
                    "stage_attempt_id": "sat-current",
                    "work_unit_id": "medical_prose_write_repair",
                },
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "route_back_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current/route_back_evidence_packet.json"
                    ),
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/route_back_evidence_packet.json"
                ),
            },
        },
    )

    assert payload is not None
    assert payload["drive_mode"] == "owner_action_ready_no_redrive"


def test_direct_next_action_transaction_uses_domain_transition_mission_identity() -> None:
    transaction = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={
            "mission_id": (
                "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
            ),
        },
        next_action={
            "stage_id": "write",
            "owner": "write",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
            ),
            "action_type": "request_opl_stage_attempt",
            "action_family": "paper.write.prose_repair",
        },
    )

    assert transaction["mission_id"] == (
        "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::write::"
        "dm003-bounded-prose-repair-after-post-sync-reviewer-record"
    )
    assert transaction["transaction_id"].endswith(
        "::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::write::"
        "dm003-bounded-prose-repair-after-post-sync-reviewer-record"
    )


def test_direct_next_action_transaction_rotates_idempotency_after_owner_consumed_route_checkpoint() -> None:
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
    }
    base_readback = {"mission_id": "paper-mission::dm003::domain-transition"}
    owner_consumed_readback = {
        **base_readback,
        "current_opl_runtime_carrier_readback": {
            "owner_consumption_readback_ref": (
                "/tmp/receipt_owner_consumption.json"
            ),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
                "route_checkpoint_evidence_ref": (
                    "/tmp/stage_attempt_closeout_packet.json"
                ),
            },
        },
    }

    initial = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback=base_readback,
        next_action=next_action,
    )
    successor = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback=owner_consumed_readback,
        next_action=next_action,
    )

    assert initial["transaction_id"] == successor["transaction_id"]
    assert initial["idempotency"]["idempotency_key"] != successor["idempotency"][
        "idempotency_key"
    ]
    assert successor["idempotency"]["idempotency_key"].endswith(
        f"::successor::{direct_handoff._stable_sha256('/tmp/receipt_owner_consumption.json')[:12]}"
    )


def test_direct_next_action_runtime_request_carries_owner_consumption_successor_delta() -> None:
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
    }
    no_epoch_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root="/tmp/dm003"),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )
    successor_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root="/tmp/dm003"),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={
            "mission_id": "paper-mission::dm003::domain-transition",
            "current_opl_runtime_carrier_readback": {
                "owner_consumption_readback_ref": (
                    "/tmp/receipt_owner_consumption.json"
                ),
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint",
                    "route_checkpoint_evidence_ref": (
                        "/tmp/stage_attempt_closeout_packet.json"
                    ),
                },
            },
        },
        next_action=next_action,
    )

    initial_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            no_epoch_handoff
        )
    )
    successor_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            successor_handoff
        )
    )

    assert initial_request is not None
    assert successor_request is not None
    assert initial_request["dedupe_key"] != successor_request["dedupe_key"]
    assert initial_request["payload"]["request_idempotency_key"] != successor_request[
        "payload"
    ]["request_idempotency_key"]
    assert successor_request["payload"]["owner_consumption_readback_ref"] == (
        "/tmp/receipt_owner_consumption.json"
    )
    assert successor_request["payload"]["advancing_delta_identity"][
        "owner_consumption_readback_ref"
    ] == "/tmp/receipt_owner_consumption.json"
    assert successor_request["payload"]["advancing_delta_identity"][
        "route_checkpoint_evidence_ref"
    ] == "/tmp/stage_attempt_closeout_packet.json"


def test_direct_next_action_runtime_request_carries_latest_task_intake_scope(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    task_intake_root = study_root / "artifacts" / "controller" / "task_intake"
    task_intake_root.mkdir(parents=True)
    task_intake_path = task_intake_root / "latest.json"
    task_intake_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "study-task::dm003::20260705T064542Z",
                "emitted_at": "2026-07-05T06:45:42+00:00",
                "study_id": study_id,
                "task_intake_kind": "reviewer_revision",
                "task_intent": (
                    "Revise DM003 through MAS canonical paper surfaces, including "
                    "Figure 4 count/% repair, medication-field-present Table 3, "
                    "Figure 1 cohort/support surfaces, Discussion literature dialogue, "
                    "abstract compression, renal-risk exploratory framing, and "
                    "supplementary retention."
                ),
                "constraints": [
                    "Do not change the main phenotype-atlas narrative.",
                    "Do not bypass MAS/OPL canonical owner routes.",
                ],
                "evidence_boundary": [
                    "Age/calendar-year/HbA1c-threshold sensitivity must route back if missing."
                ],
                "trusted_inputs": ["/tmp/reviewer-advice.txt"],
                "first_cycle_outputs": [
                    "new canonical manuscript and package",
                    "reviewer coverage audit",
                ],
                "revision_intake": {
                    "kind": "reviewer_revision",
                    "status": "active",
                    "checklist": [
                        "text_revisions",
                        "tables_figures",
                        "follow_up_evidence",
                    ],
                    "checklist_items": [
                        {
                            "id": "text_revisions",
                            "label": "text revisions",
                            "status": "pending",
                            "requirement": "Revise abstract and discussion.",
                        },
                        {
                            "id": "tables_figures",
                            "label": "tables/figures",
                            "status": "pending",
                            "requirement": "Repair Figure 1/Figure 4 and promote sensitivity Table 3.",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "outcome_ref": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
    }
    plain_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root=tmp_path / "plain-workspace"),
        study_id=study_id,
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )

    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root=workspace_root),
        study_id=study_id,
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )
    plain_runtime_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            plain_handoff
        )
    )
    runtime_request = opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
        handoff
    )

    assert plain_runtime_request is not None
    assert runtime_request is not None
    assert handoff["task_intake_kind"] == "reviewer_revision"
    assert handoff["task_intake_ref"]["artifact_path"] == str(task_intake_path)
    assert "Figure 4 count/% repair" in handoff["task_intake_summary"]["task_intent"]
    assert {
        "ref_id": "study_task_intake::latest",
        "ref_kind": "study_task_intake",
        "uri": str(task_intake_path),
    } in handoff["paper_mission_transaction"]["paper_audit_pack_refs"][
        "review_ledger_delta"
    ]
    assert runtime_request["payload"]["task_intake_kind"] == "reviewer_revision"
    assert runtime_request["payload"]["task_intake_ref"]["artifact_path"] == str(
        task_intake_path
    )
    assert "Figure 4 count/% repair" in runtime_request["payload"][
        "task_intake_summary"
    ]["task_intent"]
    assert "Figure 4 count/% repair" in runtime_request["payload"]["user_stage_log"][
        "stage_goal"
    ]
    assert str(task_intake_path) in runtime_request["payload"]["user_stage_log"][
        "evidence_refs"
    ]
    assert "text_revisions" in runtime_request["payload"]["user_stage_log"][
        "task_scope"
    ]["revision_checklist"]
    assert "tables_figures" in runtime_request["payload"]["user_stage_log"][
        "task_scope"
    ]["revision_checklist"]
    assert plain_runtime_request["dedupe_key"] != runtime_request["dedupe_key"]


def test_paper_mission_drive_does_not_redrive_same_work_unit_after_owner_consumed_opl_transition_receipt() -> None:
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "owner": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
    }
    readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "canonical_next_action_source": "domain_transition.next_action",
        "next_action": next_action,
        "current_opl_runtime_carrier_readback": {
            "opl_transition_receipt": {
                "work_unit_id": (
                    "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                ),
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_opl_transition_receipt",
                "receipt_evidence_ref": "opl://stage-attempts/sat-current",
            },
        },
    }
    different_work_unit = {
        **readback,
        "next_action": {
            **next_action,
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
    }

    assert _drive_should_submit_direct_next_action(readback) is False
    assert _drive_should_submit_direct_next_action(different_work_unit) is True


def test_paper_mission_inspect_projects_domain_transition_running_attempt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-write-repair",
        "study_id": study_id,
        "stage_id": "write",
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
        "action_family": "paper.write.prose_repair",
        "action_kind": "paper_write",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
    }
    fake_opl = tmp_path / "fake-opl-running-list.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                    "args = sys.argv[1:]",
                    "if args[:3] != ['family-runtime', 'queue', 'list']:",
                    "    raise SystemExit('unexpected args: ' + ' '.join(args))",
                    f"study_id = {study_id!r}",
                    "transaction_ref = ('paper-mission-transaction::' + study_id + '::write::'"
                    "                   'paper-mission::' + study_id + '::domain-transition::write::'"
                    "                   'medical-methods-and-registry-reporting-repair')",
                    "route_ref = transaction_ref + '#opl_route_command'",
                "payload = {",
                "    'study_id': study_id,",
                "    'paper_mission_transaction_ref': transaction_ref,",
                "    'opl_route_command_ref': route_ref,",
                "    'command_kind': 'resume_stage',",
                "    'route_target': 'write',",
                "    'work_unit_id': 'medical_methods_and_registry_reporting_repair',",
                "    'work_unit_fingerprint': 'domain-transition::route_back_same_line::medical_methods_and_registry_reporting_repair',",
                "}",
                "linked = {",
                "    'stage_attempt_id': 'sat-write-repair',",
                "    'status': 'live',",
                "    'stage_id': 'write',",
                "    'provider_kind': 'temporal',",
                "    'workflow_id': 'wf-write-repair',",
                "    'provider_run': {'provider_status': 'running', 'last_heartbeat_at': '2026-07-02T03:49:04.038Z'},",
                "    'workspace_locator': payload,",
                "}",
                "task = {",
                "    'task_id': 'frt-write-repair',",
                "    'domain_id': 'medautoscience',",
                "    'task_kind': 'paper_mission/stage-route',",
                "    'status': 'running',",
                "    'payload': payload,",
                "    'linked_stage_attempt_liveness': linked,",
                "}",
                "print(json.dumps({'version': 'g2', 'family_runtime_queue': {'tasks': [task]}}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    readback = materialized_readback._domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::paper_mission_import::one-shot-migration",
        },
        next_action=next_action,
        canonical_next_action_source="domain_transition.next_action",
        enable_opl_live_probe=True,
        opl_bin=fake_opl,
    )

    assert readback["transaction_state"] == "domain_transition_direct_stage_attempt"
    assert readback["opl_runtime_readback_status"] == (
        "opl_runtime_attempt_running_observed"
    )
    running = readback["opl_runtime_carrier_readback"]["running_attempt"]
    assert running["stage_attempt_id"] == "sat-write-repair"
    assert running["stage_id"] == "write"
    assert running["work_unit_id"] == "medical_methods_and_registry_reporting_repair"
    assert readback["authority_boundary"]["writes_paper_body"] is False


def test_paper_mission_inspect_projects_ai_reviewer_direct_stage_attempt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }

    readback = materialized_readback._domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        inspect_readback={
            "mission_id": f"paper-mission::{study_id}::paper_mission_import::one-shot-migration",
        },
        next_action=next_action,
        canonical_next_action_source="domain_transition.next_action",
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert readback["transaction_state"] == "domain_transition_direct_stage_attempt"
    assert readback["opl_runtime_carrier"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert readback["opl_runtime_carrier"]["work_unit_fingerprint"].endswith(
        "::source::fresh"
    )
    assert readback["opl_runtime_readback_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )


def test_paper_mission_drive_can_submit_opl_stage_route_via_public_enqueue(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrive"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::drive"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM003 consumed candidate into OPL stage-route.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "accepted"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "submission_milestone_candidate",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "submission_milestone_candidate",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "accepted_candidate",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm003-drive",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "records = []",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_test_drive',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_test_drive','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[running_attempt(payload)]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrive",
            "--opl-bin",
            str(fake_opl),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert capture_path.exists()
    handoff = payload["opl_route_handoff"]
    assert handoff["route_identity_key"]
    assert handoff["attempt_idempotency_key"]
    assert handoff["candidate_ref"]
    submission = payload["opl_runtime_submission"]
    assert submission["status"] in {"submitted", "running", "terminal_readback_observed"}
    assert submission["writes_runtime"] is True
    assert submission["can_claim_provider_running"] is False
    assert submission["can_claim_paper_progress"] is False
    assert payload["mutation_policy"]["writes_runtime"] is True
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["drive_result"]["status"] in {
        "opl_stage_route_running",
        "submitted",
        "submitted_to_opl_runtime",
        "terminal_readback_observed",
    }
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_followthroughs_terminal_route_back_into_fresh_stage_route(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrivefollowthrough"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::drive-followthrough"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    transaction["stage_terminal_decision"]["target_stage_id"] = (
        "paper_mission_stage_route_domain_gate_pending"
    )
    transaction["stage_terminal_decision"]["repair_scope"] = (
        "MAS authority kernel observed a domain gate terminal closeout; mission "
        "executor must revise the paper mission candidate or submit a concrete "
        "owner answer shape before OPL can advance."
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM002 route-back through MAS followthrough.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back",
                "artifact_ref": "mission://dm002/route-back",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-followthrough",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl-followthrough.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def payloads():",
                "    return [r['payload'] for r in records if 'payload' in r]",
                "def current_payload():",
                "    ps = payloads()",
                "    return ps[-1] if ps else {}",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_terminal_followthrough',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_running_followthrough',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_followthrough','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':[attempt]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[attempt]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrivefollowthrough",
            "--opl-bin",
            str(fake_opl),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert capture_path.exists()
    assert payload["followthrough"]["attempted"] is False
    assert payload["followthrough"]["round_count"] == 0
    assert payload["followthrough"]["stop_reason"] == "mas_owned_executor_delta_ready"
    assert payload["drive_result"]["status"] != "stage_closure_decision_missing"
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    followthrough_transaction = payload["consume_readback"][
        "paper_mission_transaction_readback"
    ][
        "paper_mission_transaction"
    ]
    assert followthrough_transaction["mission_id"] == mission_id
    assert (
        followthrough_transaction["transaction_id"]
        != payload["mission_id"]
    )
    assert payload["consume_readback"]["contract_validation"]["status"] == "validated"
    assert payload["output_manifest"]["followthrough_round_count"] == 0
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
