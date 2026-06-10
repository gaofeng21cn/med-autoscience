from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "stage_route_reconcile_contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_stage_route_reconcile_contract_declares_single_planning_root() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "mas_opl_stage_route_reconcile_contract"
    assert contract["version"] == "stage-route-reconcile.v1"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith("This contract defines route/currentness")

    root = contract["ordinary_planning_root"]
    assert root["root"] == "current_owner_delta"
    assert {
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "provider_admission_current_control",
    } <= set(root["derived_operator_surfaces"])
    assert {
        "raw_worklist",
        "OPL queue history",
        "attempt ledger",
        "sidecar advisory refs",
        "runtime observability traces",
    } <= set(root["audit_only_surfaces"])
    assert {
        "active_run_id",
        "transport_status",
        "zero_open_worklist",
        "old_route_back_packet",
        "advisory_score_or_ranking",
    } <= set(root["forbidden_default_roots"])
    assert root["no_second_truth"] is True


def test_stage_route_reconcile_contract_requires_strong_identity_and_closeout_sequence() -> None:
    contract = _contract()

    identity = contract["identity_policy"]
    assert {
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "idempotency_key",
        "target_surface",
    } <= set(identity["required_owner_identity_fields"])
    assert identity["minimum_match_for_provider_running"] == [
        "same_study_id",
        "same_action_type",
        "same_work_unit_id_or_fingerprint",
        "same_dispatch_ref_or_stage_attempt_id",
        "no_terminal_closeout_for_stage_attempt",
    ]
    assert identity["missing_identity_policy"] == "fail_closed_to_diagnostic_or_typed_blocker_candidate"
    assert identity["weak_label_match_can_authorize_route"] is False

    handshake = contract["closeout_handshake"]
    assert handshake["required_sequence"] == [
        "OPL attempt reaches terminal state",
        "terminal closeout packet exists for the same stage attempt or work-unit identity",
        "MAS consumes closeout through domain-health-diagnostic apply or equivalent authority consumer",
        "fresh study progress/read-model is regenerated",
        "if provider_admission_pending remains for a new identity, OPL scoped tick/hydrate may start the next attempt",
        "if the same identity remains pending, classify as closeout consumption/currentness bug",
    ]
    assert handshake["dry_run_semantics"] == {
        "starts_llm_or_provider": False,
        "observe_only_for_runtime_execution": True,
        "may_refresh_diagnostic_evidence": True,
        "must_not_be_called_no_write": False,
    }
    assert "record_only_archive" in handshake["terminal_closeout_status_prefixes"]
    assert "running" in handshake["non_terminal_statuses"]


def test_stage_route_reconcile_contract_orders_currentness_and_blocks_transport_as_domain_closeout() -> None:
    contract = _contract()

    precedence = contract["currentness_precedence"]
    assert [item["signal"] for item in precedence[:4]] == [
        "terminal_closeout_for_same_stage_attempt",
        "strict_live_provider_attempt_for_current_identity",
        "accepted_typed_closeout_for_same_identity",
        "fresh_current_owner_action",
    ]
    assert precedence[0]["effect"] == "suppress_running_projection"
    assert precedence[1]["allowed_output"] == "running_provider_attempt"
    assert precedence[-1]["allowed_output"] == "ignored_diagnostic"

    lifecycle = contract["lifecycle_state_machine"]
    assert lifecycle["main_chain"] == [
        "DesiredOwnerDelta",
        "ProviderAdmissionRequested",
        "OPLStageRunAdmitted",
        "ProviderRunning",
        "ProviderTerminalCloseoutObserved",
        "MASCloseoutConsumed",
        "DomainAcceptedOrTypedBlocked",
        "NextOwnerDeltaProjected",
    ]
    assert lifecycle["provider_completion_counts_as_domain_accepted"] is False
    assert lifecycle["queue_completion_counts_as_next_owner_delta"] is False
    assert lifecycle["active_run_id_counts_as_paper_progress"] is False


def test_stage_route_reconcile_contract_declares_anti_loop_budget_and_owner_split() -> None:
    contract = _contract()

    anti_loop = contract["anti_loop_policy"]
    assert anti_loop["budget_scope"] == (
        "study_id + action_type + work_unit_id + work_unit_fingerprint + source_eval_id"
    )
    assert anti_loop["max_same_identity_terminal_without_progress"] == 2
    assert anti_loop["max_same_identity_noop_or_owner_output_current"] == 1
    assert {
        "same_work_unit_terminal_closeout_without_domain_consumption",
        "provider_admission_pending_for_consumed_identity",
        "idempotent_noop_without_new_owner_delta",
        "repeated_gate_replay_same_blockers",
        "queue_dead_letter_without_mas_typed_blocker_or_next_owner",
    } <= set(anti_loop["no_progress_signals"])
    assert anti_loop["budget_exhaustion_action"] == (
        "stop_redrive_and_emit_mas_typed_blocker_candidate_or_route_back_evidence"
    )
    assert anti_loop["automatic_redrive_after_budget_exhaustion_allowed"] is False

    split = contract["opl_substrate_optimization"]
    assert "StageRun Kernel" in split["opl_owns"]
    assert "durable queue" in split["opl_owns"]
    assert "current_owner_delta" in split["mas_owns"]
    assert "owner receipt" in split["mas_owns"]
    assert "typed blocker" in split["mas_owns"]
    assert {
        "publication_ready_claim",
        "quality_verdict",
        "artifact_authority",
        "owner_receipt_signing",
    } <= set(split["forbidden_opl_authority"])
    assert {
        "private_scheduler",
        "worker_residency_owner",
        "second_route_table",
        "second_active_backlog",
    } <= set(split["forbidden_mas_runtime_residue"])


def test_stage_route_reconcile_contract_tracks_opl_follow_through_and_external_practice_mapping() -> None:
    contract = _contract()

    follow_through = contract["required_opl_follow_through"]
    assert follow_through["source"] == "one-person-lab read-only substrate audit 2026-06-11"
    assert {
        "current_owner_delta ordinary planning root",
        "StageRun launch and closeout admission boundary",
        "attempt ledger terminal observation",
        "worker_source_stale supervised restart guard",
    } <= set(follow_through["already_supported"])

    capabilities = {
        item["capability"]: item
        for item in follow_through["must_be_promoted_to_contract_and_tests"]
    }
    assert capabilities["terminal_closeout_precedes_live_projection"][
        "identity_mismatch_effect"
    ] == "fail_closed_currentness_blocker"
    assert {
        "stage_run_id",
        "stage_run_generation",
        "stage_manifest_ref",
        "current_pointer_ref",
        "source_fingerprint",
        "domain_source_fingerprint",
        "idempotency_key",
        "provider_attempt_ref",
        "active_lease_ref",
        "execution_authorization_ref",
        "workflow_id",
        "task_id",
    } <= set(capabilities["stage_run_currentness_identity"]["required_fields"])
    assert "automatic-redrive stop" in capabilities["no_progress_budget_contract"][
        "required_effect"
    ]
    assert "no active attempt exists" in capabilities["worker_source_stale_supervisor_projection"][
        "required_effect"
    ]
    assert "without entering ordinary planning" in capabilities["trace_span_correlation_refs"][
        "required_effect"
    ]

    practices = contract["mature_engineering_practice_mapping"]
    assert practices["kubernetes_controller"]["reject"] == (
        "status, queue, or worklist deriving domain truth"
    )
    assert practices["temporal"]["reject"] == (
        "provider completion counting as MAS domain acceptance"
    )
    assert practices["argo_workflows"]["reject"] == (
        "workflow archive, memoized step result, or retry success replacing MAS owner receipt, typed blocker, or evidence body"
    )
    assert practices["airflow"]["reject"] == (
        "small task metadata becoming artifact body, memory body, study truth, or publication verdict"
    )
    assert practices["aws_step_functions"]["reject"] == (
        "transport idempotency replacing owner receipt or typed blocker"
    )
    assert practices["durable_functions"]["reject"] == (
        "open-ended LLM medical judgment or non-idempotent artifact mutation inside deterministic orchestration"
    )
    assert practices["openlineage"]["reject"] == (
        "lineage proving medical validity, quality closure, or publication readiness"
    )
    assert practices["opentelemetry"]["reject"] == (
        "observability traces closing quality gate or publication verdict"
    )
