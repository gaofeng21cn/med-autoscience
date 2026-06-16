from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.domain_owner_action_dispatch_parts.action_execution.ai_reviewer_record_production import (
    build_ai_reviewer_record_production_request,
    build_ai_reviewer_record_worker_handoff,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_LOCAL_CLI = f"PYTHONPATH={REPO_ROOT}/src:{REPO_ROOT} python3 -m med_autoscience.cli"


def _assert_opl_authorization_required(execution: dict[str, object]) -> None:
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_callable_surface"] is None
    assert execution["adapter_kind"] == "opl_authorized_owner_callable_adapter"
    assert execution["target_runtime_owner"] == "one-person-lab"
    assert execution["mas_dispatch_authority"] is False
    assert execution["mas_creates_opl_outbox"] is False
    assert execution["mas_creates_opl_event"] is False
    assert execution["mas_creates_opl_stage_run"] is False


def test_execute_dispatch_hands_off_ai_reviewer_record_production_when_request_record_stale_after_current_manuscript(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    manuscript_path = study_root / "paper" / "draft.md"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
            "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            },
        }
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=route,
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    assert result["codex_dispatch_count"] == 0
    execution = result["executions"][0]
    _assert_opl_authorization_required(execution)
    assert execution["stale_record_ref"] == str(stale_record_path)
    assert execution["required_currentness_refs"] == [str(manuscript_path)]
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["request_kind"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    payload_ref = production_request["owner_callable_payload_ref"]
    assert payload_ref.endswith(
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/"
        "return_to_ai_reviewer_workflow_payload.json"
    )
    assert production_request["owner_callable_command"] == (
        f"{REPO_LOCAL_CLI} publication materialize-ai-reviewer-record --profile <profile.toml> "
        f"--study-id {study_id} --payload-file {payload_ref} --build-production-trace"
    )
    assert production_request["followup_actions"] == [
        "fill owner_callable_payload_ref.record_payload with an AI-reviewer-authored publication eval record",
        "run owner_callable_command exactly as rendered",
        "domain-action-request-materialize",
        "domain-owner-action-dispatch --action-types return_to_ai_reviewer_workflow",
    ]
    assert production_request["reviewer_operating_system_contract"]["production_trace_builder"] == (
        "ai_reviewer_publication_eval_workflow.build_ai_reviewer_publication_eval_record_with_workflow_trace"
    )
    assert production_request["reviewer_operating_system_contract"]["executor_must_not_hand_author_diagnostic_trace"] is True
    assert production_request["record_must_consume_refs"] == [str(manuscript_path)]
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    handoff = execution["ai_reviewer_record_worker_handoff"]
    assert handoff["surface"] == "default_executor_dispatch_request"
    assert handoff["dispatch_status"] == "ready"
    assert handoff["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert handoff["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert handoff["ai_reviewer_record_production_request"] == production_request
    assert handoff["refs"]["owner_callable_payload_ref"] == payload_ref
    assert handoff["prompt_contract"]["owner_callable_payload_ref"] == payload_ref
    assert handoff["prompt_contract"]["owner_callable_command"] == production_request["owner_callable_command"]
    assert handoff["provider_admission_pending"] is False
    assert handoff["provider_admission_requires_opl_runtime_result"] is True
    assert handoff["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )
    assert handoff["prompt_contract"]["record_payload_authoring_target_surface"] == (
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json"
    )
    assert handoff["prompt_contract"]["execution_steps"] == [
        "Read owner_callable_payload_ref and fill only its record_payload field with the AI reviewer publication eval record.",
        "Run owner_callable_command exactly as rendered to let MAS rebuild the production reviewer_operating_system trace and write the record-only archive.",
        "Do not inspect MAS source code to discover alternate CLI spellings or write artifacts/publication_eval/latest.json.",
        "Emit the required typed closeout packet with the materialized record ref.",
    ]
    closeout_contract = handoff["required_closeout_packet"]
    assert closeout_contract["required_user_stage_log_field"] == "paper_stage_log"
    assert set(closeout_contract["required_user_stage_log_fields"]) >= {
        "progress_delta_classification",
        "deliverable_progress_delta",
        "paper_progress_delta",
        "platform_repair_delta",
        "next_forced_delta",
    }
    assert closeout_contract["user_stage_log_policy"]["progress_delta_policy"][
        "platform_repair_delta_does_not_count_as_paper_progress"
    ] is True
    assert "next_forced_delta" in handoff["terminal_output_instruction"]
    assert handoff["owner_route"]["next_owner"] == "ai_reviewer"
    assert handoff["owner_route"]["owner_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert handoff["owner_route"]["source_refs"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert handoff["prompt_contract"]["allowed_write_surfaces"] == [
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]
    assert "artifacts/publication_eval/latest.json" in handoff["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in handoff["forbidden_surfaces"]
    persisted = json.loads(dispatch_path.read_text(encoding="utf-8"))
    assert persisted["action_id"] == f"dispatch::{study_id}::return_to_ai_reviewer_workflow"
    assert persisted.get("dispatch_authority") != "ai_reviewer_record_production_handoff"
    assert "immutable_dispatch_path" not in persisted.get("refs", {})
    assert "stage_packet_path" not in persisted.get("refs", {})
    payload_path = Path(payload_ref)
    assert not payload_path.exists()
    assert "ai_reviewer_record_worker_handoff_path" not in execution
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_record_handoff_renders_executable_owner_callable_with_profile(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)
    profile = profile.__class__(**{**profile.__dict__, "profile_ref": profile_path})
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    production_request = build_ai_reviewer_record_production_request(
        request={"study_id": study_id, "quest_id": study_id},
        required_refs={"manuscript": str(manuscript_path)},
        stale_record_ref=str(
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "stale_publication_eval_record.json"
        ),
        required_currentness_refs=[str(manuscript_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    )
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request={"study_id": study_id, "quest_id": study_id},
        dispatch={
            "owner_route": _owner_route(
                study_id=study_id,
                action_type="return_to_ai_reviewer_workflow",
                owner="ai_reviewer",
            )
        },
        production_request=production_request,
    )

    payload_ref = handoff["refs"]["owner_callable_payload_ref"]
    expected_command = (
        f"{REPO_LOCAL_CLI} publication materialize-ai-reviewer-record "
        f"--profile {profile_path.resolve()} "
        f"--study-id {study_id} "
        f"--payload-file {payload_ref} "
        "--build-production-trace"
    )
    assert handoff["ai_reviewer_record_production_request"]["owner_callable_profile_ref"] == str(
        profile_path.resolve()
    )
    assert handoff["prompt_contract"]["owner_callable_command"] == expected_command
    assert handoff["prompt_contract"]["allowed_write_surfaces"] == [
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]
    assert handoff["prompt_contract"]["execution_steps"][1] == (
        "Run owner_callable_command exactly as rendered to let MAS rebuild the production "
        "reviewer_operating_system trace and write the record-only archive."
    )
    assert handoff["provider_completion_is_domain_completion"] is False
    assert handoff["provider_admission_pending"] is False
    assert handoff["provider_admission_requires_opl_runtime_result"] is True
    assert handoff["authority_boundary"]["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert handoff["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert handoff["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    assert (
        handoff["stage_transition_authority_boundary"]["stage_transition_authority"]
        == "one-person-lab"
    )
    assert (
        handoff["stage_transition_authority_boundary"][
            "provider_completion_counts_as_stage_transition"
        ]
        is False
    )
    assert "provider_admission_identity" not in handoff
    transition_request = handoff["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["action_type"] == "return_to_ai_reviewer_workflow"
    assert transition_request["next_owner"] == "ai_reviewer"
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    assert handoff["prompt_contract"]["authority_boundary"] == handoff["authority_boundary"]
    assert (
        handoff["prompt_contract"]["stage_transition_authority_boundary"]
        == handoff["stage_transition_authority_boundary"]
    )


def test_execute_dispatch_accepts_record_only_handoff_contract_when_selected_from_persisted_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    manuscript_path = study_root / "paper" / "draft.md"
    request_payload = {
        "surface": "supervisor_action_request",
        "study_id": study_id,
        "quest_id": study_id,
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "request_lifecycle": {
            "state": "requested",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "stale_record_ref": str(stale_record_path),
            "required_currentness_refs": [str(manuscript_path)],
        },
        "input_contract": {
            "required_refs": {
                "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                "evidence_ledger": {
                    "path": str(study_root / "paper" / "evidence_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "review_ledger": {
                    "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "study_charter": {
                    "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "present": True,
                    "valid": True,
                },
            },
            "all_required_refs_present": True,
            "missing_or_invalid_refs": [],
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        request_payload,
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
            "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            },
        }
    )
    source_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request_payload,
        required_refs={
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        stale_record_ref=str(stale_record_path),
        required_currentness_refs=[str(manuscript_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    )
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request_payload,
        dispatch=source_dispatch,
        production_request=production_request,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, handoff)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    _assert_opl_authorization_required(execution)
    assert execution["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    enriched_request = execution["ai_reviewer_record_production_request"]
    assert enriched_request["request_kind"] == production_request["request_kind"]
    assert enriched_request["required_currentness_refs"] == production_request["required_currentness_refs"]
    assert "owner_callable_payload_ref" in enriched_request
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_canonicalizes_legacy_record_only_handoff_before_contract_guard(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    request_payload = {
        "surface": "supervisor_action_request",
        "study_id": study_id,
        "quest_id": study_id,
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "request_lifecycle": {
            "state": "requested",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "stale_record_ref": "publication-eval::stale-record",
            "required_currentness_refs": [str(manuscript_path)],
        },
        "input_contract": {
            "required_refs": {
                "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                "evidence_ledger": {
                    "path": str(study_root / "paper" / "evidence_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "review_ledger": {
                    "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "study_charter": {
                    "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "present": True,
                    "valid": True,
                },
            },
            "all_required_refs_present": True,
            "missing_or_invalid_refs": [],
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        request_payload,
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
            "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            },
        }
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request_payload,
        required_refs={
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        stale_record_ref="publication-eval::stale-record",
        required_currentness_refs=[str(manuscript_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    )
    legacy_handoff = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        owner_route=route,
    )
    legacy_handoff.update(
        {
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "ai_reviewer_record_production_request": production_request,
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "paper/submission_minimal/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
                ".ds/**",
            ],
            "allowed_write_surfaces": [
                "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
            ],
        }
    )
    legacy_prompt = dict(legacy_handoff["prompt_contract"])
    legacy_prompt.update(
        {
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "forbidden_surfaces": list(legacy_handoff["forbidden_surfaces"]),
            "allowed_write_surfaces": [
                "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
            ],
            "ai_reviewer_record_production_request": production_request,
        }
    )
    legacy_handoff["prompt_contract"] = legacy_prompt
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, legacy_handoff)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    _assert_opl_authorization_required(execution)
    canonical_prompt = execution["prompt_contract"]
    assert canonical_prompt["owner_callable_payload_ref"].endswith(
        "record_production_payloads/return_to_ai_reviewer_workflow_payload.json"
    )
    assert canonical_prompt["owner_callable_command"].startswith(REPO_LOCAL_CLI)
    assert canonical_prompt["allowed_write_surfaces"] == [
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]


def test_execute_dispatch_canonicalizes_record_only_handoff_with_stale_medautosci_command(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    request_payload = {
        "surface": "supervisor_action_request",
        "study_id": study_id,
        "quest_id": study_id,
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "request_lifecycle": {
            "state": "requested",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "stale_record_ref": "publication-eval::stale-record",
            "required_currentness_refs": [str(manuscript_path)],
        },
        "input_contract": {
            "required_refs": {
                "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                "evidence_ledger": {
                    "path": str(study_root / "paper" / "evidence_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "review_ledger": {
                    "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "study_charter": {
                    "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "present": True,
                    "valid": True,
                },
            },
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        request_payload,
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request_payload,
        required_refs={"manuscript": str(manuscript_path)},
        stale_record_ref="publication-eval::stale-record",
        required_currentness_refs=[str(manuscript_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    )
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request_payload,
        dispatch=_dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=route,
        ),
        production_request=production_request,
    )
    stale_prompt = dict(handoff["prompt_contract"])
    stale_prompt["owner_callable_command"] = (
        "medautosci publication materialize-ai-reviewer-record --profile /stale/profile.toml "
        f"--study-id {study_id} --payload-file {stale_prompt['owner_callable_payload_ref']} "
        "--build-production-trace"
    )
    handoff["prompt_contract"] = stale_prompt
    handoff["ai_reviewer_record_production_request"] = {
        **handoff["ai_reviewer_record_production_request"],
        "owner_callable_command": stale_prompt["owner_callable_command"],
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, handoff)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    _assert_opl_authorization_required(execution)
    assert execution["prompt_contract"]["owner_callable_command"].startswith(REPO_LOCAL_CLI)
    assert execution["ai_reviewer_record_production_request"]["owner_callable_command"].startswith(REPO_LOCAL_CLI)


def test_execute_dispatch_hands_off_ai_reviewer_record_production_when_request_record_stale_after_current_inputs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260527T111037Z_publication_eval_record.json"
    )
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    request_payload = {
        "surface": "supervisor_action_request",
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "request_lifecycle": {
            "state": "requested",
            "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            "stale_record_ref": str(stale_record_path),
            "required_currentness_refs": [str(evidence_path), str(claim_map_path)],
        },
        "input_contract": {
            "required_refs": {
                "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
                "evidence_ledger": {"path": str(evidence_path), "present": True, "valid": True},
                "claim_evidence_map": {"path": str(claim_map_path), "present": True, "valid": True},
                "review_ledger": {
                    "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "present": True,
                    "valid": True,
                },
                "study_charter": {
                    "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "present": True,
                    "valid": True,
                },
            },
            "all_required_refs_present": True,
            "missing_or_invalid_refs": [],
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        request_payload,
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_inputs",
            "owner_reason": "ai_reviewer_record_stale_after_current_inputs",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
        }
    )
    source_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    production_request = build_ai_reviewer_record_production_request(
        request=request_payload,
        required_refs={
            "manuscript": str(study_root / "paper" / "draft.md"),
            "evidence_ledger": str(evidence_path),
            "claim_evidence_map": str(claim_map_path),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        stale_record_ref=str(stale_record_path),
        required_currentness_refs=[str(evidence_path), str(claim_map_path)],
        request_kind="produce_ai_reviewer_publication_eval_record_against_current_inputs",
    )
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request=request_payload,
        dispatch=source_dispatch,
        production_request=production_request,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, handoff)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    _assert_opl_authorization_required(execution)
    enriched_request = execution["ai_reviewer_record_production_request"]
    assert enriched_request["request_kind"] == production_request["request_kind"]
    assert enriched_request["required_currentness_refs"] == production_request["required_currentness_refs"]
    assert "owner_callable_payload_ref" in enriched_request
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_allows_repair_followup_when_opl_authorization_blocker_remains(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "study_id": study_id,
            "quest_id": study_id,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": "publication-eval::stale-record",
                "required_currentness_refs": [str(manuscript_path), str(evidence_path), str(claim_map_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path), "present": True, "valid": True},
                    "claim_evidence_map": {"path": str(claim_map_path), "present": True, "valid": True},
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "return_to_ai_reviewer_workflow",
            "owner_reason": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": work_unit_fingerprint,
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
            },
        }
    )
    source_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    production_request = build_ai_reviewer_record_production_request(
        request={"study_id": study_id, "quest_id": study_id},
        required_refs={
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(evidence_path),
            "claim_evidence_map": str(claim_map_path),
        },
        stale_record_ref="publication-eval::stale-record",
        required_currentness_refs=[str(manuscript_path), str(evidence_path), str(claim_map_path)],
        request_kind=work_unit_id,
    )
    handoff = build_ai_reviewer_record_worker_handoff(
        profile=profile,
        study_id=study_id,
        request={"study_id": study_id, "quest_id": study_id},
        dispatch=source_dispatch,
        production_request=production_request,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, handoff)

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "repair_progress_precedence": {"paper_delta_observed": True},
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    _assert_opl_authorization_required(execution)
