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


def test_paper_mission_drive_submits_domain_transition_next_action_without_candidate_package(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    output_root = workspace_root / "ops" / "medautoscience" / "drive"
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl-direct.py"
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
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_write_repair',",
                "        'work_unit_id': payload.get('work_unit_id'),",
                "        'work_unit_fingerprint': payload.get('work_unit_fingerprint'),",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "            'work_unit_id': payload.get('work_unit_id'),",
                "            'work_unit_fingerprint': payload.get('work_unit_fingerprint'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_write_repair','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    task = {'task_id':'frt_write_repair','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':[running_attempt(payload)]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    task = {'task_id':'frt_write_repair','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[running_attempt(payload)]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)
    builder_calls: list[str] = []

    def fake_readback_builder(**kwargs):
        command = kwargs["paper_mission_command"]
        builder_calls.append(command)
        assert command == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Route medical methods and registry reporting repair.",
            "study_id": study_id,
            "next_action": {
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
            },
            "canonical_next_action_source": "domain_transition.next_action",
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=output_root,
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=fake_opl,
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert builder_calls == ["inspect"]
    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert not (output_root / "candidate_package").exists()
    assert not (output_root / "consumption_ledger").exists()
    assert payload["opl_route_handoff"]["route_target"] == "write"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_runtime_carrier"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_runtime_carrier_readback"]["running_attempt"]["stage_id"] == (
        "write"
    )
    assert payload["opl_runtime_carrier_readback"]["running_attempt"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )


def test_paper_mission_drive_submits_current_paper_mission_next_action_envelope_without_candidate_package(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    work_unit_fingerprint = (
        "domain-transition::route_back_same_line::"
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )

    def fake_readback_builder(**kwargs):
        command = kwargs["paper_mission_command"]
        assert command == "inspect"
        return {
            "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Resume the current write repair work unit.",
            "study_id": study_id,
            "canonical_next_action_source": "paper_mission_next_action_envelope",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-current-write",
                "study_id": study_id,
                "stage_id": "write",
                "outcome_ref": work_unit_fingerprint,
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "authority_boundary": {
                    "projection_only": True,
                    "can_write_runtime_queue": False,
                    "can_write_provider_attempt": False,
                    "can_submit_to_opl_runtime": True,
                },
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=False,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["inspect_readback"]["canonical_next_action_source"] == (
        "paper_mission_next_action_envelope"
    )
    assert payload["drive_result"]["status"] == "opl_runtime_submission_pending"
    assert payload["drive_result"]["route_target"] == "write"
    assert payload["drive_result"]["work_unit_id"] == work_unit_id
    assert payload["opl_route_handoff"]["route_target"] == "write"
    assert payload["opl_route_handoff"]["work_unit_id"] == work_unit_id
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_submits_authoritative_runtime_route_after_route_checkpoint(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Resume the current write repair work unit.",
            "study_id": study_id,
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "selected_outcome": "accepted_submission_milestone_candidate",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "transaction_state": "accepted_submission_milestone_candidate",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-current-write",
                "study_id": study_id,
                "stage_id": "write",
                "outcome_ref": "route-back:paper-mission-terminal-owner-gate",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                ),
                "authority_source": "mas_next_action_compiler",
                "authority_boundary": {
                    "projection_only": True,
                    "next_action_authority": True,
                    "action_family_authority": True,
                    "can_submit_to_opl_runtime": True,
                    "can_write_runtime_queue": False,
                    "can_write_provider_attempt": False,
                },
            },
            "stage_closure_decision": {
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                }
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["drive_result"]["can_submit_to_opl_runtime"] is True
    assert payload["drive_result"]["reason"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_kind"] == "submit_to_opl_runtime"
    assert payload["opl_route_handoff"]["route_target"] == "write"
    assert payload["opl_route_handoff"]["work_unit_id"] == work_unit_id
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None


def test_paper_mission_drive_submits_domain_transition_owner_workflow_after_route_back_checkpoint(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    output_root = workspace_root / "ops" / "medautoscience" / "drive"

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "outcome_ref": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "ai_reviewer_medical_prose_quality_review"
                ),
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "ai_reviewer_medical_prose_quality_review"
                ),
            },
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "stage_closure_decision": {
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                }
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=output_root,
        run_id=None,
        submit_opl_runtime=False,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["opl_route_handoff"]["route_target"] == "review"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert payload["mutation_policy"]["writes_runtime"] is False


def test_paper_mission_drive_prefers_domain_next_action_over_current_opl_consumption(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "route_back_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/route_back_evidence_packet.json"
                    ),
                    "can_claim_paper_progress": False,
                }
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_family"] == "paper.review.ai_reviewer"
    assert payload["opl_route_handoff"]["route_target"] == "review"
    assert payload["opl_route_handoff"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["mutation_policy"]["writes_runtime"] is False


@pytest.mark.parametrize(
    "stale_next_legal_action",
    [
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        "record_typed_blocker",
    ],
)
def test_paper_mission_drive_ignores_stale_current_opl_consumption_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    stale_next_legal_action: str,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-review/route_back_evidence_packet.json"
    )
    receipt_ref = "opl://stage-attempts/sat-review"

    def fake_readback_builder(**kwargs):
        assert kwargs["paper_mission_command"] == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::reviewer-revision",
            "objective": "Re-run AI reviewer after manuscript revision.",
            "study_id": study_id,
            "canonical_next_action_source": "domain_transition.next_action",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "requires_mas_owner_consumption",
                    "next_legal_action": stale_next_legal_action,
                    "receipt_evidence_ref": receipt_ref,
                    "route_back_evidence_ref": route_back_ref,
                    "typed_runtime_blocker_ref": (
                        "opl://stage-attempts/sat-review/runtime-blockers/"
                        "closeout-not-materialized"
                    ),
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "can_claim_paper_progress": False,
                }
            },
            "receipt_owner_consumption_readback": {
                "status": "owner_consumption_applied",
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "owner_consumed_route_checkpoint",
                    "next_legal_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "receipt_evidence_ref": receipt_ref,
                    "route_back_evidence_ref": route_back_ref,
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/stage_attempt_closeout_packet.json"
                    ),
                    "typed_runtime_blocker_ref": (
                        "opl://stage-attempts/sat-review/runtime-blockers/"
                        "closeout-not-materialized"
                    ),
                    "forbidden_next_action": "synonymous_route_back_redrive",
                    "can_claim_paper_progress": False,
                },
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "obesity.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=False,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert payload["drive_mode"] == "domain_transition_direct_stage_attempt"
    assert payload["drive_result"]["reason"] == "domain_transition_direct_stage_attempt"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert payload["mutation_policy"]["writes_runtime"] is False


def test_paper_mission_drive_halts_after_owner_apply_receipt_consumed(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    (studies_root / study_id).mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    builder_calls: list[str] = []

    def fake_readback_builder(**kwargs):
        command = kwargs["paper_mission_command"]
        builder_calls.append(command)
        assert command == "inspect"
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "mission_id": f"paper-mission::{study_id}::medical_prose_write_repair",
            "objective": "Honor a MAS owner repair receipt before any redrive.",
            "study_id": study_id,
            "domain_transition": {
                "decision_type": "owner_apply_receipt_consumed",
                "route_target": "finalize",
                "controller_action": "paper_autonomy_guarded_apply",
                "owner": "med-autoscience",
                "next_work_unit": {
                    "unit_id": "provider_hosted_guarded_apply",
                    "lane": "finalize",
                },
            },
            "receipt_owner_consumption_readback": {
                "status": "owner_consumption_applied",
                "apply_mode": "mas_owner_repair_receipt",
                "authority_materialized": True,
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "schema_version": 1,
                    "status": "owner_consumed_mas_repair_delta",
                    "receipt_kind": "mas_owner_apply_receipt",
                    "next_legal_action": "honor_paper_story_repair_owner_receipt",
                    "can_claim_paper_progress": True,
                    "can_claim_submission_ready": False,
                    "can_claim_publication_ready": False,
                },
            },
            "stage_closure_decision": {
                "surface_kind": "mas_stage_closure_decision",
                "authority_materialized": True,
                "outcome": {
                    "kind": "owner_receipt",
                    "next_action": "honor_paper_story_repair_owner_receipt",
                    "can_submit": False,
                },
            },
        }

    payload = build_paper_mission_drive_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        output_root=workspace_root / "ops" / "medautoscience" / "drive",
        run_id=None,
        submit_opl_runtime=True,
        opl_bin=tmp_path / "missing-opl",
        source="test",
        consume_candidate_readback_builder=fake_readback_builder,
        consumption_ledger_forbidden_authority_writes=(
            commands.CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=commands.FORBIDDEN_AUTHORITY_CLAIMS,
    )

    assert builder_calls == ["inspect"]
    assert payload["drive_mode"] == "domain_transition_auto_redrive_halted"
    assert payload["drive_result"]["status"] == "domain_transition_auto_redrive_halted"
    assert payload["drive_result"]["domain_transition_decision_type"] == (
        "owner_apply_receipt_consumed"
    )
    assert payload["drive_result"]["domain_transition_route_target"] == "finalize"
    assert payload["output_manifest"]["candidate_package"] is None
    assert payload["output_manifest"]["consumption_ledger"] is None
    assert payload["mutation_policy"]["writes_runtime"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

