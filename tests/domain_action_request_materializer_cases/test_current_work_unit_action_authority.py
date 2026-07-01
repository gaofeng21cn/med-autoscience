from __future__ import annotations

import importlib
import importlib.util


def _selection_module():
    return importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )


def _next_action_envelope(
    *,
    study_id: str,
    action_type: str,
    action_family: str = "runtime.opl_route",
    output_kind: str = "opl_transition_receipt",
    owner: str = "one-person-lab",
    work_unit_id: str | None = None,
) -> dict[str, object]:
    resolved_work_unit_id = work_unit_id or action_type
    return {
        "surface_kind": "mas_next_action_envelope",
        "action_id": f"next-action::{study_id}::{resolved_work_unit_id}",
        "idempotency_key": f"next-action::{study_id}::{resolved_work_unit_id}",
        "action_family": action_family,
        "action_type": action_type,
        "owner": owner,
        "work_unit_id": resolved_work_unit_id,
        "expected_output_contract": {"output_kind": output_kind},
    }


def test_fresh_progress_current_action_reads_without_live_provider_probe(monkeypatch) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.fresh_progress_current_action"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    observed: dict[str, object] = {}

    def read_study_progress(**kwargs):
        observed.update(kwargs)
        return {"study_id": kwargs["study_id"]}

    monkeypatch.setattr(study_progress, "read_study_progress", read_study_progress)

    payload = module._read_fresh_study_progress(profile=object(), study_id="001-risk")

    assert payload == {"study_id": "001-risk"}
    assert observed["sync_runtime_summary"] is False
    assert observed["materialize_read_model_artifacts"] is False
    assert observed["enable_opl_live_provider_attempt_probe"] is False


def test_current_action_selection_retires_legacy_next_action_without_canonical_envelope() -> None:
    selection = _selection_module()

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(),
        scan_payload={
            "action_queue": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_id": "legacy-stage-native-write",
                    "action_type": "run_quality_repair_batch",
                    "authority": "stage_native_workspace_next_action",
                    "next_action": {
                        "surface_kind": "mas_next_action_envelope",
                        "action_id": "incomplete-next-action",
                    },
                }
            ]
        },
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "action_id": "legacy-stage-native-write",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_current_action_selection_retires_legacy_carrier_even_with_complete_next_action_envelope() -> None:
    selection = _selection_module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "action_id": "legacy-stage-native-runtime-route",
        "action_type": "run_gate_clearing_batch",
        "authority": "stage_native_workspace_next_action",
        "next_action": _next_action_envelope(study_id=study_id, action_type="run_gate_clearing_batch"),
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(),
        scan_payload={"action_queue": [action]},
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "action_id": "legacy-stage-native-runtime-route",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_legacy_guard_keeps_non_legacy_canonical_owner_action_envelope() -> None:
    legacy = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts."
        "legacy_next_action_authority"
    )
    study_id = "004-synthetic-new-study"
    action = {
        "study_id": study_id,
        "action_id": "canonical-paper-write",
        "action_type": "run_quality_repair_batch",
        "authority": "mas_next_action_envelope",
        "next_action": _next_action_envelope(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            action_family="paper.write.prose_repair",
            output_kind="paper_facing_delta_or_owner_receipt",
            owner="write",
            work_unit_id="story_surface_repair",
        ),
    }

    selected, ignored = legacy.retire_incomplete_authority_actions([action], [])

    assert selected == [action]
    assert ignored == []


def test_queue_attaches_non_opl_canonical_envelope_from_study_payload() -> None:
    queue = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_queue"
    )
    study_id = "004-synthetic-new-study"
    next_action = _next_action_envelope(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        action_family="paper.write.prose_repair",
        output_kind="paper_facing_delta_or_owner_receipt",
        owner="write",
        work_unit_id="story_surface_repair",
    )

    action = queue.attach_canonical_next_action_if_missing(
        {"study_id": study_id, "action_type": "run_quality_repair_batch"},
        {"study_id": study_id, "next_action": next_action},
    )

    assert action["next_action"] == next_action


def test_fresh_progress_uses_canonical_envelope_without_legacy_current_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.fresh_progress_current_action"
    )
    study_id = "004-synthetic-new-study"
    next_action = _next_action_envelope(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        action_family="paper.write.prose_repair",
        output_kind="paper_facing_delta_or_owner_receipt",
        owner="write",
        work_unit_id="story_surface_repair",
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-epoch::canonical-envelope",
        "route_epoch": "truth-epoch::canonical-envelope",
        "runtime_health_epoch": "runtime-health::canonical-envelope",
        "work_unit_fingerprint": "story-surface-repair::fingerprint",
        "source_fingerprint": "story-surface-repair::source",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "story_surface_repair",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "work_unit_id": "story_surface_repair",
            "work_unit_fingerprint": "story-surface-repair::fingerprint",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch::canonical-envelope",
                "runtime_health_epoch": "runtime-health::canonical-envelope",
                "work_unit_id": "story_surface_repair",
                "work_unit_fingerprint": "story-surface-repair::fingerprint",
            },
        },
        "idempotency_key": "owner-route::canonical-envelope",
    }

    action = module._fresh_progress_current_action(
        study_id=study_id,
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "next_action": next_action,
            "owner_route": owner_route,
        },
        domain_transition_actions=lambda _study: [],
        explicit_readiness_action=lambda _progress: {},
    )

    assert action is not None
    assert action["authority"] == "mas_next_action_envelope"
    assert action["source_surface"] == "mas_next_action_envelope"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["next_action"] == next_action
    assert action["owner_route"]["idempotency_key"] == "owner-route::canonical-envelope"
    assert "current_action_source" not in action


def test_current_action_selection_ignores_bare_queue_action_before_it_can_preempt_canonical_candidate() -> None:
    selection = _selection_module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-epoch::canonical-route",
        "route_epoch": "truth-epoch::canonical-route",
        "runtime_health_epoch": "runtime-health::canonical-route",
        "work_unit_fingerprint": "publication-gate-replay::current",
        "source_fingerprint": "publication-gate-replay::current",
        "current_owner": "mas_controller",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "publication_gate_replay",
        "active_run_id": None,
        "allowed_actions": ["run_gate_clearing_batch"],
        "blocked_actions": [],
        "idempotency_key": "owner-route::canonical-route",
    }
    canonical_action = {
        "study_id": study_id,
        "action_id": "canonical-runtime-route",
        "action_type": "run_gate_clearing_batch",
        "authority": "mas_next_action_envelope",
        "next_action": _next_action_envelope(
            study_id=study_id,
            action_type="run_gate_clearing_batch",
        ),
    }
    bare_queue_action = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_id": "legacy-current-owner-route-queue",
        "action_type": "run_gate_clearing_batch",
        "authority": "observability_only",
        "owner": "gate_clearing_batch",
        "reason": "publication_gate_replay",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "publication-gate-replay::current",
        "owner_route": owner_route,
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(study_id,),
        scan_payload={
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": owner_route,
                    "action_queue": [bare_queue_action],
                }
            ],
            "action_queue": [canonical_action],
        },
    )

    assert actions == [canonical_action]
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "action_id": "legacy-current-owner-route-queue",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_current_action_selection_retires_bare_top_level_action_queue_without_study_envelope() -> None:
    selection = _selection_module()
    action = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_id": "bare-top-level-gate-replay",
        "action_type": "run_gate_clearing_batch",
        "owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:bare-top-level-gate-replay",
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(),
        scan_payload={"action_queue": [action]},
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "action_type": "run_gate_clearing_batch",
            "action_id": "bare-top-level-gate-replay",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_current_action_selection_fails_closed_for_routed_queue_without_canonical_envelope() -> None:
    selection = _selection_module()
    study_id = "004-synthetic-new-study"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-epoch::legacy-route",
        "route_epoch": "truth-epoch::legacy-route",
        "runtime_health_epoch": "runtime-health::legacy-route",
        "work_unit_fingerprint": "legacy-route::fingerprint",
        "source_fingerprint": "legacy-route::fingerprint",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "legacy_queue_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": "owner-route::legacy-route",
    }
    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_id": "legacy-routed-queue-action",
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "legacy-work-unit",
        "work_unit_fingerprint": "legacy-route::fingerprint",
        "owner_route": owner_route,
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(study_id,),
        scan_payload={
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": owner_route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [],
        },
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "run_quality_repair_batch",
            "action_id": "legacy-routed-queue-action",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_current_action_selection_retires_queue_carrier_that_borrows_study_envelope() -> None:
    selection = _selection_module()
    study_id = "004-synthetic-new-study"
    next_action = _next_action_envelope(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id="ai_reviewer_current_inputs",
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-epoch::canonical-route",
        "route_epoch": "truth-epoch::canonical-route",
        "runtime_health_epoch": "runtime-health::canonical-route",
        "work_unit_fingerprint": "ai-reviewer-current-inputs::fingerprint",
        "source_fingerprint": "ai-reviewer-current-inputs::fingerprint",
        "current_owner": "mas_controller",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_current_inputs",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "idempotency_key": "owner-route::ai-reviewer-current-inputs",
    }
    queue_action = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_id": "legacy-ai-reviewer-queue",
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "work_unit_id": "ai_reviewer_current_inputs",
        "work_unit_fingerprint": "ai-reviewer-current-inputs::fingerprint",
        "owner_route": owner_route,
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(study_id,),
        scan_payload={
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "next_action": next_action,
                    "owner_route": owner_route,
                    "action_queue": [queue_action],
                }
            ],
            "action_queue": [],
        },
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "action_id": "legacy-ai-reviewer-queue",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_next_action_identity_mismatch_includes_action_family_and_output_kind() -> None:
    legacy = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts."
        "legacy_next_action_authority"
    )
    study_id = "004-synthetic-new-study"
    action = {
        "study_id": study_id,
        "action_id": "legacy-family-carrier",
        "action_type": "return_to_ai_reviewer_workflow",
        "action_family": "paper.review.ai_reviewer",
        "expected_output_contract": {"output_kind": "ai_reviewer_record"},
        "authority": "observability_only",
        "work_unit_id": "ai_reviewer_current_inputs",
        "next_action": _next_action_envelope(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            action_family="runtime.opl_route",
            output_kind="opl_transition_receipt",
            work_unit_id="ai_reviewer_current_inputs",
        ),
    }

    selected, ignored = legacy.retire_incomplete_authority_actions([action], [])

    assert selected == []
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "action_id": "legacy-family-carrier",
            "reason": legacy.NEXT_ACTION_ENVELOPE_IDENTITY_MISMATCH_REASON,
        }
    ]


def test_current_work_unit_action_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
        )
        is None
    )


def test_current_action_selection_does_not_let_typed_blocker_barrier_preempt_identity_different_action(
    monkeypatch,
) -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    monkeypatch.setattr(
        selection.fresh_progress_current_action,
        "current_actions",
        lambda **_: [],
    )

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=("002-dm-china-us-mortality-attribution",),
        scan_payload={
            "studies": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "ai_reviewer_record_gate_consumption"
                        ),
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_id": "stage_packet_not_current_selected_dispatch",
                                "owner": "one-person-lab",
                                "work_unit_id": "publication_gate_replay",
                            },
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "next_owner": "analysis-campaign",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": "analysis_claim_evidence_repair",
                        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                        "target_surface": {
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
                        },
                    },
                    "action_queue": [
                        {
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "action_type": "run_gate_clearing_batch",
                            "action_id": "stale-gate-replay",
                            "owner": "one-person-lab",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": (
                                "domain-transition::route_back_same_line::"
                                "ai_reviewer_record_gate_consumption"
                            ),
                        }
                    ],
                }
            ],
        },
    )

    assert actions is not None
    assert [action["action_type"] for action in actions] == ["current_execution_envelope_typed_blocker"]
    assert actions[0]["reason"] == "stage_packet_not_current_selected_dispatch"
    assert actions[0]["owner"] == "one-person-lab"


def test_current_action_selection_has_no_paper_recovery_callable_selector() -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )

    assert not hasattr(selection, "paper_recovery_owner_callable")
