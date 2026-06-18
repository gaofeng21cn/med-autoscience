from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_effective_current_context_prefers_valid_current_ai_reviewer_record_over_stale_latest() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_current_context")

    context = module.resolve_effective_current_context(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
        current_ai_reviewer_record={
            "eval_id": "eval-current",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "currentness_status": "current",
            "record_current": True,
            "projection_source_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
            "source_fingerprint": "source-current",
        },
        latest_publication_eval={
            "eval_id": "eval-stale",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "currentness_status": "stale",
        },
        current_work_unit={"work_unit_id": "publishability_repair_sprint"},
        owner_route={
            "next_owner": "write",
            "allowed_actions": ["run_quality_repair_batch"],
            "source_fingerprint": "route-source",
            "source_refs": {"work_unit_id": "publishability_repair_sprint"},
        },
        running_state={"state": "running", "stage_attempt_id": "sat-002"},
        closeout_state={"state": "missing"},
    )

    assert context["status"] == "current"
    assert context["effective_eval_id"] == "eval-current"
    assert context["effective_eval_ref"] == "artifacts/publication_eval/ai_reviewer_responses/current.json"
    assert context["stale_latest_eval_id"] == "eval-stale"
    assert context["immutable_dispatch_packet"]["effective_eval_id"] == "eval-current"
    assert context["immutable_dispatch_packet"]["owner_route"]["next_owner"] == "write"
    assert context["source_fingerprint"] == "source-current"


def test_effective_current_context_fails_closed_for_invalid_current_ai_reviewer_record() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_current_context")

    context = module.resolve_effective_current_context(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
        current_ai_reviewer_record={
            "eval_id": "eval-current",
            "study_id": "another-study",
            "currentness_status": "current",
            "record_current": True,
        },
        latest_publication_eval={"eval_id": "eval-stale"},
        current_work_unit={"work_unit_id": "publishability_repair_sprint"},
        owner_route={"next_owner": "write"},
    )

    assert context["status"] == "blocked"
    assert context["blocked_reason"] == "invalid_current_ai_reviewer_record"
    assert context["effective_eval_id"] is None
    assert context["immutable_dispatch_packet"]["dispatchable"] is False


def test_quality_repair_and_gate_clearing_contexts_share_effective_eval_id() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_current_context")

    context = module.resolve_effective_current_context(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
        current_ai_reviewer_record={
            "eval_id": "eval-current",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "currentness_status": "current",
            "record_current": True,
            "projection_source_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
        },
        latest_publication_eval={"eval_id": "eval-stale", "currentness_status": "stale"},
        current_work_unit={"work_unit_id": "publishability_repair_sprint"},
        owner_route={"next_owner": "write", "source_refs": {"work_unit_id": "publishability_repair_sprint"}},
    )

    quality = module.batch_effective_eval_context(context, batch_kind="quality_repair_batch")
    gate = module.batch_effective_eval_context(context, batch_kind="gate_clearing_batch")

    assert quality["effective_eval_id"] == "eval-current"
    assert gate["effective_eval_id"] == "eval-current"
    assert quality["immutable_dispatch_packet"] == gate["immutable_dispatch_packet"]
    assert quality["batch_kind"] == "quality_repair_batch"
    assert gate["batch_kind"] == "gate_clearing_batch"


def test_closeout_first_admission_blocks_new_default_executor_task_when_binding_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_closeout")

    result = module.closeout_first_admission(
        identity={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "work_unit_id": "publishability_repair_sprint",
            "stage_attempt_id": "sat-running",
        },
        immutable_dispatch_packet={
            "packet_id": "packet-002",
            "dispatchable": True,
            "effective_eval_id": "eval-current",
        },
        running_attempt={"state": "running", "stage_attempt_id": "sat-running"},
        owner_receipt=None,
        stage_closeout=None,
        stable_typed_blocker=None,
    )

    assert result["admission_status"] == "blocked"
    assert result["blocked_reason"] == "closeout_required_before_new_default_executor_task"
    assert result["export_new_default_executor_task"] is False
    blocker = result["typed_blocker"]
    assert blocker["surface_kind"] == "mas_domain_typed_blocker"
    assert blocker["reason"] == "closeout_required_before_new_default_executor_task"
    assert blocker["work_unit_id"] == "publishability_repair_sprint"
    assert blocker["next_owner"] == "med-autoscience"


def test_domain_action_materializer_blocks_new_default_executor_task_until_running_attempt_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id="quest-002")
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-002",
        "truth_epoch": "truth-epoch-002",
        "runtime_health_epoch": "runtime-health-002",
        "work_unit_fingerprint": "work-unit-progress-first",
        "source_fingerprint": "source-current",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": "owner-route::dm002::progress-first",
        "source_refs": {
            "work_unit_id": "publishability_repair_sprint",
            "source_eval_id": "eval-current",
        },
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-002",
                    "owner_route": owner_route,
                    "running_attempt": {
                        "state": "running",
                        "stage_attempt_id": "sat-running",
                        "immutable_dispatch_packet": {
                            "packet_id": "packet-running",
                            "dispatchable": True,
                            "effective_eval_id": "eval-current",
                        },
                    },
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-002",
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
                    "owner_route": owner_route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "blocked"
    assert dispatch["blocked_reason"] == "closeout_required_before_new_default_executor_task"
    assert dispatch["progress_first_closeout_admission"]["export_new_default_executor_task"] is False
    assert dispatch["progress_first_closeout_admission"]["typed_blocker"]["work_unit_id"] == "publishability_repair_sprint"
    assert result["request_tasks"][0]["surface"] == "supervisor_request_handoff_task_ref"
    assert result["request_tasks"][0]["handoff_packet_body_omitted"] is True
    assert "handoff_packet" not in result["request_tasks"][0]
    assert result["written_files"] == []
    assert result["apply_writes_disabled_reason"] == "opl_domain_progress_transition_runtime_owns_durable_carrier"
    assert result["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert not (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    ).exists()


def test_typed_blocker_repeat_budget_escalates_without_paper_delta() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_blocker_budget")

    second = module.enrich_typed_blocker(
        {
            "reason": "ai_reviewer_record_stale_after_current_inputs",
            "next_owner": "ai_reviewer",
        },
        study_id="002-dm-china-us-mortality-attribution",
        work_unit_id="publishability_repair_sprint",
        eval_id="eval-current",
        source_fingerprint="source-current",
        repeat_count=2,
        first_seen="2026-05-29T00:00:00+00:00",
        last_seen="2026-05-29T00:10:00+00:00",
        deliverable_progress_delta={"count": 0},
        platform_repair_delta={"count": 1},
    )
    third = module.enrich_typed_blocker(
        second,
        study_id="002-dm-china-us-mortality-attribution",
        work_unit_id="publishability_repair_sprint",
        eval_id="eval-current",
        source_fingerprint="source-current",
        repeat_count=3,
        first_seen="2026-05-29T00:00:00+00:00",
        last_seen="2026-05-29T00:20:00+00:00",
        deliverable_progress_delta={"count": 0},
        platform_repair_delta={"count": 2},
    )

    assert second["blocker_family"] == "ai_reviewer_record_stale_after_current_inputs"
    assert second["next_escalation"] == "mechanism_repair_owner"
    assert second["deliverable_progress_delta"] == second["paper_progress_delta"]
    assert second["paper_progress_delta"]["count"] == 0
    assert second["progress_delta_classification"] == "platform_repair"
    assert third["next_escalation"] == "human_gate_or_stop_loss_candidate"
    assert third["deliverable_progress_delta"] == third["paper_progress_delta"]
    assert third["paper_progress_delta"]["count"] == 0
    assert third["platform_repair_delta"]["count"] == 2

    terminal = module.enrich_typed_blocker(
        {"reason": "same_blocker_without_any_delta"},
        study_id="002-dm-china-us-mortality-attribution",
        work_unit_id="publishability_repair_sprint",
        eval_id="eval-current",
        source_fingerprint="source-current",
        repeat_count=3,
        first_seen="2026-05-29T00:00:00+00:00",
        last_seen="2026-05-29T00:30:00+00:00",
        deliverable_progress_delta={"count": 0},
        platform_repair_delta={"count": 0},
    )
    assert terminal["progress_delta_classification"] == "human_gate"


def test_current_owner_ticket_exposes_current_owner_native_jit_affordance_policy() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    projection = module.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "opl_current_control_state_handoff": {
                "owner_route": {
                    "next_owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "source_refs": {
                        "work_unit_id": "publishability_repair_sprint",
                        "source_eval_id": "eval-current",
                        "route_option_board_ref": "refs/route-option-board.json",
                        "opportunistic_prefetch_refs": [
                            "refs/journal-neighbor-prefetch.json",
                            "refs/guideline-prefetch.json",
                        ],
                    },
                }
            },
        }
    )

    ticket = projection["current_owner_ticket"]
    policy = ticket["progress_jit_affordance_policy"]

    assert policy["surface_kind"] == "mas_progress_jit_affordance_policy"
    assert policy["mechanisms"] == [
        "next_delta_tournament",
        "bounded_micro_candidate_generation",
        "critique_as_repair_hint",
        "reusable_lesson_extraction",
        "triggered_meta_review",
        "opportunistic_knowledge_prefetch",
    ]
    assert policy["default_posture"] == "current_owner_native_jit_affordance"
    assert policy["default_invocation"] == "none"
    assert policy["default_design"] == "ordinary_progress_has_no_extra_advisory_stage"
    assert policy["invocation_trigger"] == "current_delta_declares_or_implies_affordance_need"
    assert (
        policy["invocation_only_when"]
        == (
            "current_owner_action_or_gate_explicitly_declares_or_current_delta_shape_implies_"
            "named_ref_family_repair_context_briefing_or_arbitration_need"
        )
    )
    assert policy["route_option_board_ref"] == "refs/route-option-board.json"
    assert policy["next_delta_tournament"]["selects"] == "one_next_attempt"
    assert policy["bounded_micro_candidates"]["max_candidates_per_attempt"] == 3
    assert policy["bounded_micro_candidates"]["unselected_candidates_do_not_block"] is True
    assert policy["critique_as_repair_hint"]["can_close_quality_gate"] is False
    assert policy["reusable_lesson_extraction"]["max_reusable_lesson_refs_per_invocation"] == 1
    assert policy["reusable_lesson_extraction"]["missing_lesson_blocks_route"] is False
    assert policy["triggered_meta_review"]["runs_every_attempt"] is False
    assert policy["triggered_meta_review"]["trigger_reasons"] == [
        "stop_loss_candidate",
        "repeated_failure",
        "human_gate_pressure",
        "claim_boundary_drift",
        "no_loop_budget_exhausted",
    ]
    assert policy["opportunistic_knowledge_prefetch"]["refs"] == [
        "refs/journal-neighbor-prefetch.json",
        "refs/guideline-prefetch.json",
    ]
    assert policy["opportunistic_knowledge_prefetch"]["mainline_waits_for_prefetch"] is False
    assert policy["forbidden_authority_claims"] == [
        "admission_gate",
        "quality_closure",
        "publication_readiness",
        "artifact_authority",
        "route_blocking_layer",
        "paper_progress_from_platform_repair_or_prefetch",
    ]
    assert ticket["authority_boundary"] == {
        "ticket_authorizes_next_attempt_only": True,
        "ticket_authorizes_publication_quality": False,
        "ticket_authorizes_artifact_mutation": False,
        "ticket_authorizes_study_truth_write": False,
    }


def test_domain_owner_dispatch_enriches_repeat_suppressed_typed_blocker_lineage(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-002")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-002",
        "truth_epoch": "truth-epoch-002",
        "runtime_health_epoch": "runtime-health-002",
        "work_unit_fingerprint": "work-unit-progress-first",
        "source_fingerprint": "source-current",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": "owner-route::dm002::progress-first",
        "source_refs": {
            "work_unit_id": "publishability_repair_sprint",
            "source_eval_id": "eval-current",
        },
    }
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "study_id": study_id,
        "quest_id": "quest-002",
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-progress-first",
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
        "owner_route": owner_route,
        "idempotency_key": owner_route["idempotency_key"],
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": "quest-002",
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
            "owner_route": owner_route,
            "idempotency_key": owner_route["idempotency_key"],
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/run_quality_repair_batch.json",
            "do_not_repeat": True,
            "repeat_suppression_key": "work-unit-progress-first",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "allowed_write_surfaces": ["artifacts/supervision/**"],
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
        },
        "progress_first_closeout_admission": {
            "admission_status": "blocked",
            "blocked_reason": "closeout_required_before_new_default_executor_task",
            "typed_blocker": {
                "reason": "closeout_required_before_new_default_executor_task",
                "next_owner": "med-autoscience",
            },
        },
        "refs": {"dispatch_path": str(dispatch_path)},
    }
    _write_json(dispatch_path, dispatch)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [{**dispatch, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": "quest-002", "owner_route": owner_route}],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "closeout_required_before_new_default_executor_task"
    blocker = execution["progress_first_typed_blocker"]
    assert blocker["blocker_family"] == "closeout_required_before_new_default_executor_task"
    assert blocker["work_unit_id"] == "publishability_repair_sprint"
    assert blocker["eval_id"] == "eval-current"
    assert blocker["next_escalation"] == "same_owner_retry_budget"
