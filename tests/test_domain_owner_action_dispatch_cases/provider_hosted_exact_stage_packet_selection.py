from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import domain_owner_action_dispatch
from med_autoscience.controllers.domain_owner_action_dispatch_parts import persisted_dispatches
from tests.study_runtime_test_helpers import make_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _transition_request_projection(dispatch: dict[str, object]) -> dict[str, object]:
    prompt_contract = dict(dispatch["prompt_contract"])  # type: ignore[arg-type]
    prompt_contract["dispatch_status"] = "transition_request_pending"
    prompt_contract["provider_admission_pending"] = False
    prompt_contract["provider_admission_requires_opl_runtime_result"] = True
    return {
        **dispatch,
        "surface": "mas_domain_progress_transition_request_projection",
        "legacy_surface": "default_executor_dispatch_request",
        "projection_only": True,
        "owner_callable_carrier_projection_only": True,
        "dispatch_status": "transition_request_pending",
        "blocked_reason": "opl_execution_authorization_required",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "prompt_contract": prompt_contract,
        "opl_domain_progress_transition_request": {
            "surface": "opl_domain_progress_transition_request",
            "target_runtime_kind": "DomainProgressTransitionRuntime",
        },
    }


def _bind_provider_hosted_stage_packet(
    monkeypatch,
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    dispatch_path: Path,
) -> None:
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", action_type)
    monkeypatch.setenv("OPL_WORK_UNIT_ID", work_unit_id)
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "temporal://attempt/sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_REF", "temporal://lease/sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://execution-authorizations/sat_2d9f8f3b252de25a6103779f",
    )


def test_provider_hosted_exact_stage_packet_selects_dispatch_despite_blocking_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_root = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    dispatch_path = dispatch_root / action_type / "33abc53e0c18295f5fa03738.json"
    latest_path = dispatch_root / f"{action_type}.json"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": fingerprint,
        "runtime_health_epoch": fingerprint,
        "route_epoch": fingerprint,
        "current_owner": "MedAutoScience",
        "next_owner": "write",
        "owner_reason": work_unit_id,
        "allowed_actions": [action_type],
        "source_fingerprint": fingerprint,
        "work_unit_fingerprint": fingerprint,
        "source_refs": {
            "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
            "owner_route_currentness_basis": {
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
    }
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-successor::{study_id}::{action_type}::{work_unit_id}",
        "dispatch_status": "ready",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "repeat_suppression_key": fingerprint,
        "idempotency_key": owner_route["idempotency_key"],
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "allowed_write_surfaces": [
                "studies/<study_id>/artifacts/supervision/requests/quality_repair_batch/latest.json"
            ],
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
        "refs": {
            "dispatch_path": str(latest_path),
            "immutable_dispatch_path": str(dispatch_path),
            "stage_packet_path": str(dispatch_path),
        },
    }
    stale_dispatch = {
        **dispatch,
        "action_type": "complete_medical_paper_readiness_surface",
        "action_id": f"paper-recovery-successor::{study_id}::complete_medical_paper_readiness_surface::medical_readiness",
        "work_unit_id": "medical_readiness",
        "owner_route": {
            **owner_route,
            "allowed_actions": ["complete_medical_paper_readiness_surface"],
            "owner_reason": "medical_readiness",
            "source_refs": {
                **owner_route["source_refs"],
                "work_unit_id": "medical_readiness",
                "owner_route_currentness_basis": {
                    **owner_route["source_refs"]["owner_route_currentness_basis"],
                    "work_unit_id": "medical_readiness",
                },
            },
        },
        "prompt_contract": {
            **dispatch["prompt_contract"],
            "action_type": "complete_medical_paper_readiness_surface",
        },
        "refs": {
            "dispatch_path": str(
                dispatch_root / "complete_medical_paper_readiness_surface.json"
            ),
            "immutable_dispatch_path": str(
                dispatch_root
                / "immutable"
                / "complete_medical_paper_readiness_surface"
                / "stale.json"
            ),
            "stage_packet_path": str(
                dispatch_root
                / "immutable"
                / "complete_medical_paper_readiness_surface"
                / "stale.json"
            ),
        },
    }
    _write_json(dispatch_path, dispatch)
    _write_json(latest_path, dispatch)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "consumer_projection",
            "owner_callable_adapters": [stale_dispatch],
        },
    )
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "owner": "write",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                }
            ],
            "action_queue": [],
        },
    )
    _write_json(
        profile.studies_root / study_id / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_type": action_type,
            "action_id": f"stage-native-next-action::{action_type}",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "stage_transition_authority_boundary": {
                "stage_transition_authority": "one-person-lab",
                "intent_can_write_stage_current_pointer": False,
                "intent_can_write_stage_run_terminal_state": False,
                "intent_can_publish_current_owner_delta": False,
            },
            "current_work_unit_binding": {
                "source": "canonical_current_work_unit",
                "work_unit_id": action_type,
                "work_unit_fingerprint": "stage-native-next-action::08-publication_package_handoff::run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json",
            },
        },
    )
    monkeypatch.setattr(
        persisted_dispatches.stage_native_dispatch_selection,
        "read_fresh_study_progress",
        lambda **_: {
            "study_id": study_id,
            "active_run_id": None,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "blocked:domain_owner_action_dispatch_execution_count_zero",
                    "owner": "write",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "state": {
                    "typed_blocker": {
                        "blocker_type": "blocked:domain_owner_action_dispatch_execution_count_zero"
                    }
                },
            },
            "paper_recovery_state": {
                "phase": "domain_blocked",
                "next_safe_action": {
                    "kind": "resolve_typed_blocker",
                    "provider_admission_allowed": False,
                },
            },
        },
    )
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", action_type)
    monkeypatch.setenv("OPL_WORK_UNIT_ID", work_unit_id)
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "temporal://attempt/sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_REF", "temporal://lease/sat_2d9f8f3b252de25a6103779f")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://execution-authorizations/sat_2d9f8f3b252de25a6103779f",
    )

    selected = persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=(action_type,),
        consumer_payload=None,
        consumer_latest_path=(
            profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
        ),
        scan_payload=persisted_dispatches.scan_latest_payload(profile),
        supported_action_types=frozenset({action_type}),
        dispatch_relative_root=Path("artifacts/supervision/consumer/default_executor_dispatches"),
    )

    assert [Path(item["refs"]["immutable_dispatch_path"]) for item in selected] == [dispatch_path]


def test_provider_hosted_projection_executes_canonical_stage_packet_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_root = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    latest_path = dispatch_root / f"{action_type}.json"
    immutable_path = dispatch_root / "immutable" / action_type / "33abc53e0c18295f5fa03738.json"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": fingerprint,
        "runtime_health_epoch": fingerprint,
        "route_epoch": fingerprint,
        "current_owner": "MedAutoScience",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "allowed_actions": [action_type],
        "source_fingerprint": fingerprint,
        "work_unit_fingerprint": fingerprint,
        "source_refs": {
            "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
            "owner_route_currentness_basis": {
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
    }
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-successor::{study_id}::{action_type}::{work_unit_id}",
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "next_executable_owner": "write",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "target_runtime_owner": "one-person-lab",
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "repeat_suppression_key": fingerprint,
        "idempotency_key": owner_route["idempotency_key"],
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/compact_evidence_packets/{action_type}.json"
            ),
            "do_not_repeat": True,
            "repeat_suppression_key": fingerprint,
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "allowed_write_surfaces": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
                "paper/review/**",
            ],
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
        },
        "refs": {
            "dispatch_path": str(latest_path),
            "immutable_dispatch_path": str(immutable_path),
            "stage_packet_path": str(immutable_path),
        },
    }
    _write_json(latest_path, dispatch)
    _write_json(immutable_path, dispatch)
    _bind_provider_hosted_stage_packet(
        monkeypatch,
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        dispatch_path=immutable_path,
    )
    monkeypatch.setattr(
        domain_owner_action_dispatch.action_execution,
        "quest_root_from_status",
        lambda profile, study_id: profile.runtime_root / study_id,
    )

    execution = domain_owner_action_dispatch._execute_dispatch(
        profile=profile,
        study_id=study_id,
        dispatch_payload=_transition_request_projection(dispatch),
        developer_mode_payload={"mode": "developer_apply_safe", "safe_actions_enabled": True},
        apply=False,
        scan_payload={"studies": [{"study_id": study_id}]},
        fresh_progress={
            "study_id": study_id,
            "current_work_unit": {
                "status": "typed_blocker",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    )

    assert execution["dispatch_contract_valid"] is True
    assert execution["dispatch_contract_blocked_reason"] is None
    assert execution["execution_status"] == "dry_run"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["dispatch_status"] == "ready"
    assert execution["opl_execution_authorization_present"] is True


def test_transition_projection_without_exact_stage_packet_remains_non_executable(
    tmp_path: Path,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_root = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "owner_route": {
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "prompt_contract": {},
        "refs": {
            "dispatch_path": str(dispatch_root / f"{action_type}.json"),
            "immutable_dispatch_path": str(dispatch_root / "immutable" / action_type / "33abc53e0c18295f5fa03738.json"),
            "stage_packet_path": str(dispatch_root / "immutable" / action_type / "33abc53e0c18295f5fa03738.json"),
        },
    }

    execution = domain_owner_action_dispatch._execute_dispatch(
        profile=profile,
        study_id=study_id,
        dispatch_payload=_transition_request_projection(dispatch),
        developer_mode_payload={"mode": "developer_apply_safe", "safe_actions_enabled": True},
        apply=False,
        scan_payload={"studies": [{"study_id": study_id}]},
        fresh_progress={"study_id": study_id},
    )

    assert execution["dispatch_contract_valid"] is False
    assert execution["dispatch_contract_blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert execution["execution_status"] == "blocked"
