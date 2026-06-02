from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import claim_evidence_map_payload, evidence_ledger_payload
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os
from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from med_autoscience.controllers.domain_owner_action_dispatch_parts.action_execution_parts.ai_reviewer_record_production import (
    build_ai_reviewer_record_production_request,
    build_ai_reviewer_record_worker_handoff,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_LOCAL_CLI = f"{REPO_ROOT}/scripts/run-python-clean.sh -m med_autoscience.cli"


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

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
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
    immutable_dispatch_path = Path(persisted["refs"]["immutable_dispatch_path"])
    assert persisted["refs"]["stage_packet_path"] == str(immutable_dispatch_path)
    assert immutable_dispatch_path.is_file()
    assert immutable_dispatch_path.parent.name == "return_to_ai_reviewer_workflow"
    assert immutable_dispatch_path.parent.parent.name == "immutable"
    immutable_dispatch = json.loads(immutable_dispatch_path.read_text(encoding="utf-8"))
    assert immutable_dispatch["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert immutable_dispatch["owner_route"] == persisted["owner_route"]
    payload_path = Path(payload_ref)
    assert payload_path.is_file()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "ai_reviewer_record_payload_authoring_target"
    assert payload["request_kind"] == production_request["request_kind"]
    assert payload["study_id"] == study_id
    assert payload["stale_record_ref"] == str(stale_record_path)
    assert payload["required_currentness_refs"] == [str(manuscript_path)]
    assert payload["record_payload"] is None
    assert payload["allowed_write_surfaces"] == [
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]
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

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert execution["dispatch_contract_valid"] is True
    assert execution["dispatch_contract_blocked_reason"] is None
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
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

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["dispatch_contract_valid"] is True
    assert execution["dispatch_contract_blocked_reason"] is None
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
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
        dispatch={
            "owner_route": route,
            "prompt_contract": {"owner_route": route},
        },
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
    assert execution["dispatch_contract_valid"] is True
    assert execution["execution_status"] == "handoff_ready"
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

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
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


def test_execute_dispatch_routes_claim_evidence_alignment_blocker_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    paper_root = study_root / "paper"
    manuscript_path = paper_root / "draft.md"
    manuscript_text = "# Manuscript\n\nCurrent claim text.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    evidence_path = paper_root / "evidence_ledger.json"
    claim_map_path = paper_root / "claim_evidence_map.json"
    _write_json(claim_map_path, claim_evidence_map_payload(evidence_ledger_ref=str(evidence_path)))
    _write_json(evidence_path, evidence_ledger_payload(evidence_ledger_ref=str(evidence_path), evidence_id="renamed"))
    _write_json(paper_root / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_gate" / "latest.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested", "blocked_reason": None},
                "ai_reviewer_record": {
                    "schema_version": 1,
                    "eval_id": "publication-eval::dm002::2026-05-24T20:09:53+00:00",
                    "evaluation_scope": "publication",
                    "assessment_provenance": {
                        "owner": "ai_reviewer",
                        "source_kind": "publication_eval_ai_reviewer",
                        "policy_id": "medical_publication_critique_v1",
                        "source_refs": [str(manuscript_path), str(evidence_path), str(claim_map_path)],
                        "ai_reviewer_required": False,
                    },
                    "quality_assessment": {
                        key: {"status": "ready", "summary": "ready", "evidence_refs": [str(manuscript_path)]}
                    for key in (
                        "clinical_significance",
                        "evidence_strength",
                        "novelty_positioning",
                        "medical_journal_prose_quality",
                        "human_review_readiness",
                        )
                    },
                    "future_facing_limitations_plan": [
                        {
                            "limitation": "Recorded treatment coverage may be incomplete.",
                            "impact_on_claim": "Coverage claims remain documentation-aware.",
                            "required_future_analysis_data_or_design": "Link dispensing records.",
                            "current_manuscript_wording_must_be_restrained": True,
                        }
                    ],
                    "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
                        study_root=study_root,
                        manuscript_path=manuscript_path,
                        manuscript_text=manuscript_text,
                        eval_id="publication-eval::dm002::2026-05-24T20:09:53+00:00",
                    ),
                },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path)},
                    "evidence_ledger": {"path": str(evidence_path)},
                    "review_ledger": {"path": str(paper_root / "review" / "review_ledger.json")},
                    "study_charter": {"path": str(study_root / "artifacts" / "controller" / "study_charter.json")},
                    "medical_manuscript_blueprint": {"path": str(paper_root / "medical_manuscript_blueprint.json")},
                    "claim_evidence_map": {"path": str(claim_map_path)},
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_gate" / "latest.json")
                    },
                }
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
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        lambda **_: (_ for _ in ()).throw(ValueError("claim_evidence_alignment.status must be ready")),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "claim_evidence_alignment_required"
    assert execution["next_owner"] == "write"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["owner_result"]["claim_evidence_alignment"]["status"] == "blocked"
    assert execution["owner_result"]["missing_evidence_item_refs"] == ["evidence-primary"]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
