from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


def _canonical_payload() -> dict[str, object]:
    legacy_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "domain_transition",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "legacy-write-repair",
        "work_unit_fingerprint": "legacy-write-repair::fingerprint",
        "action_fingerprint": "legacy-write-repair::fingerprint",
    }
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
            "owner": "one-person-lab",
        },
        "canonical_next_action_source": "paper_mission_next_action_envelope",
        "current_executable_owner_action": legacy_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-write-repair",
            "work_unit_fingerprint": "legacy-write-repair::fingerprint",
            "state": {"source": "current_executable_owner_action"},
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "write",
            "controller_action": "run_quality_repair_batch",
            "work_unit_fingerprint": "legacy-write-repair::fingerprint",
            "next_work_unit": {"unit_id": "legacy-write-repair"},
        },
        "paper_recovery_state": {
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "successor_owner_action": legacy_action,
            },
        },
    }


def test_canonical_next_action_blocks_legacy_current_owner_producers() -> None:
    payload = _canonical_payload()

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")
    assert current_action.build_canonical_owner_action_projection(payload) is None
    assert current_work_unit.build_current_work_unit(progress=payload) == {}
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
        )
        is None
    )
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.domain_transition"
        )
        is None
    )


def test_canonical_next_action_cleanup_does_not_back_project_legacy_owner_action() -> None:
    mission_summary = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary"
    )
    payload = _canonical_payload()
    payload["next_action"] = {
        "surface_kind": "mas_next_action_envelope",
        "action_family": "paper.package.submission_minimal",
        "action_type": "materialize_submission_ready_owner_verdict_or_human_gate",
        "allowed_actions": [
            "materialize_submission_ready_owner_verdict_or_human_gate"
        ],
        "study_id": payload["study_id"],
        "owner": "mas_authority_kernel",
        "work_unit_id": "submission_ready_authority_closeout",
        "work_unit_fingerprint": "sha256:submission-authority",
    }

    cleaned = mission_summary.without_legacy_next_action_authority(payload)

    assert cleaned["next_action"]["surface_kind"] == "mas_next_action_envelope"
    assert "current_executable_owner_action" not in cleaned
    assert "current_work_unit" not in cleaned
    assert cleaned["legacy_next_action_authority_retired"]["authority"] == (
        "NextActionEnvelope"
    )


def test_canonical_next_action_blocks_provider_admission_current_control_candidate() -> None:
    provider_actions = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions"
    )

    assert not hasattr(provider_actions, "_study_current_action_for_provider_admission")


def test_missing_canonical_next_action_does_not_resurrect_legacy_default_owner_action() -> None:
    payload = _canonical_payload()
    payload.pop("next_action")
    payload.pop("canonical_next_action_source")

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    assert current_action.build_canonical_owner_action_projection(payload) is None


def test_missing_canonical_next_action_closes_all_legacy_owner_inputs() -> None:
    legacy_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "legacy_current_executable_owner_action",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "legacy-write-repair",
        "work_unit_fingerprint": "legacy-write-repair::fingerprint",
        "action_fingerprint": "legacy-write-repair::fingerprint",
    }
    payload = {
        "study_id": "legacy-only-study",
        "current_executable_owner_action": legacy_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-current-work-unit",
            "work_unit_fingerprint": "legacy-current-work-unit::fingerprint",
            "state": {"current_executable_owner_action": legacy_action},
        },
        "provider_admission": {
            "surface_kind": "provider_admission",
            "status": "ready",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-provider-admission",
            "request_idempotency_key": "legacy-provider-admission-request",
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "write",
            "controller_action": "run_quality_repair_batch",
            "next_work_unit": {"unit_id": "legacy-domain-transition"},
        },
        "paper_recovery_state": {
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "successor_owner_action": legacy_action,
            },
        },
    }

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")
    provider_actions = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions"
    )

    assert current_action.build_canonical_owner_action_projection(payload) is None
    assert current_work_unit.build_current_work_unit(progress=payload) == {}
    assert not hasattr(provider_actions, "_study_current_action_for_provider_admission")


def test_canonical_next_action_does_not_let_paper_recovery_materialize_owner_action() -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    payload = _canonical_payload()
    payload["paper_recovery_state"] = {
        "phase": "owner_action_ready",
        "current_authority": {
            "obligation": {
                "study_id": payload["study_id"],
                "quest_id": payload["study_id"],
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "paper-recovery-write-repair",
                "work_unit_fingerprint": "paper-recovery-write-repair::fingerprint",
            }
        },
        "supervisor_decision": {"decision": "materialize_recovery_action"},
        "next_safe_action": {
            "kind": "materialize_successor_owner_action",
            "successor_owner_action": {
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "paper-recovery-write-repair",
                "work_unit_fingerprint": "paper-recovery-write-repair::fingerprint",
            },
        },
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(str(payload["study_id"]),),
        scan_payload={"studies": [payload], "action_queue": []},
    )

    assert actions == []
    assert ignored == []


def test_legacy_owner_action_selector_has_no_callable_diagnostic_escape_hatch() -> None:
    payload = _canonical_payload()
    payload.pop("next_action")
    payload.pop("canonical_next_action_source")

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    assert current_action.build_canonical_owner_action_projection(payload) is None
    assert not hasattr(current_action, "legacy_current_executable_owner_action_diagnostic")


def test_terminal_next_forced_delta_owner_successor_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.terminal_next_forced_delta"
        )
        is None
    )


def test_legacy_owner_successor_producers_declare_noncanonical_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    producer_dir = (
        root
        / "src"
        / "med_autoscience"
        / "controllers"
        / "study_progress_parts"
        / "owner_action_diagnostics"
    )

    missing: list[str] = []
    for path in sorted(producer_dir.glob("*.py")):
        text = path.read_text()
        if '"authority_boundary": _authority_boundary()' not in text:
            continue
        if '"canonical_next_action_authority": False' not in text:
            missing.append(path.name)
        if '"projection_role": "superseded_successor_diagnostic"' not in text:
            missing.append(path.name)

    assert missing == []


def test_stage_artifact_index_current_owner_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.stage_artifact_index"
        )
        is None
    )


def test_repair_progress_owner_successor_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.repair_progress"
        )
        is None
    )


def test_non_advancing_terminal_closeout_diagnostic_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.non_advancing_terminal_closeout"
        )
        is None
    )


def test_owner_action_diagnostic_action_types_are_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.action_types"
        )
        is None
    )


def test_paper_recovery_owner_successor_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.study_progress_parts."
            "owner_action_diagnostics.paper_recovery"
        )
        is None
    )


def test_stage_outcome_authority_has_no_paper_recovery_legacy_bridge() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root
        / "src"
        / "med_autoscience"
        / "controllers"
        / "stage_outcome_authority_parts"
        / "owner_route_selection.py"
    ).read_text()

    retired_terms = [
        "domain_action_request_materializer_paper_recovery_owner_callable",
        "paper_recovery_successor_legacy_bridge",
    ]

    assert [term for term in retired_terms if term in source] == []


def test_current_work_unit_paper_recovery_successor_accepts_mas_owner_callable() -> None:
    successor = importlib.import_module(
        "med_autoscience.controllers.current_work_unit_parts.paper_recovery_successor"
    )

    assert successor.paper_recovery_successor_action_ready(
        {
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": "readiness::fingerprint",
            "paper_recovery_successor": {
                "source_next_safe_action_kind": "run_mas_owner_callable",
            },
        }
    ) is True


def test_current_execution_refresh_does_not_resurrect_legacy_successor_actions() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root
        / "src"
        / "med_autoscience"
        / "controllers"
        / "study_progress_parts"
        / "projection_payload_assembly_parts"
        / "current_execution_surfaces.py"
    ).read_text()

    retired_resurrection_terms = [
        "owner_action_from_terminal_next_forced_delta",
        "_current_work_unit_paper_recovery_successor_action",
        "paper_recovery_successor_action_ready",
        "_with_paper_recovery_successor_execution_surfaces",
        "_paper_recovery_successor_action_for_owner_receipt_handoff",
    ]

    assert [term for term in retired_resurrection_terms if term in source] == []


def test_materializer_retires_legacy_current_action_even_with_complete_next_action_identity() -> None:
    legacy = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts."
        "legacy_next_action_authority"
    )

    selected, ignored = legacy.retire_incomplete_authority_actions(
        [
            {
                "study_id": "synthetic-study",
                "action_type": "request_opl_stage_attempt",
                "action_id": "legacy-current-action",
                "authority": "study_progress.current_executable_owner_action",
                "source_surface": "study_progress.current_executable_owner_action",
                "next_action": {
                    "surface_kind": "mas_next_action_envelope",
                    "action_id": "canonical-action",
                    "idempotency_key": "canonical-idempotency",
                    "action_family": "runtime.opl_route",
                    "expected_output_contract": {"output_kind": "opl_transition_receipt"},
                },
            }
        ],
        [],
    )

    assert selected == []
    assert ignored[0]["reason"] == legacy.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON


def test_missing_canonical_next_action_does_not_promote_bare_action_queue() -> None:
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")

    work_unit = current_work_unit.build_current_work_unit(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:legacy-queue-action",
                "action_fingerprint": "sha256:legacy-queue-action",
            }
        ],
        blocked_reason="domain_transition_ai_reviewer_re_eval",
        next_owner="ai_reviewer",
    )

    assert work_unit == {}


def test_missing_canonical_next_action_does_not_resurrect_current_execution_envelope() -> None:
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")

    work_unit = current_work_unit.build_current_work_unit(
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "legacy-envelope-work-unit",
        },
        blocked_reason="current_work_unit_unresolved",
        next_owner="write",
    )

    assert work_unit == {}


def test_residual_current_work_unit_projection_does_not_default_owner_without_envelope() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.current_work_unit_parts.projection"
    )

    work_unit = projection.current_work_unit(
        status="diagnostic_residual",
        owner=None,
        action_type=None,
        work_unit_id=None,
        work_unit_fingerprint=None,
        action_fingerprint=None,
        input_refs=[],
        required_output_contract={},
        acceptance_refs=[],
        currentness_basis={},
        state={"source": "legacy_current_work_unit_residual"},
        status_payload={"study_id": "legacy-residual-study"},
        progress_payload={"study_id": "legacy-residual-study"},
        action=None,
    )

    assert work_unit["owner"] is None
    assert work_unit["action_type"] is None
    assert work_unit["state"] == {"source": "legacy_current_work_unit_residual"}


def test_current_execution_envelope_barriers_are_diagnostic_only() -> None:
    current_action = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.fresh_progress_current_action"
    )

    typed_blocker = current_action._fresh_progress_current_action(
        study_id="legacy-envelope-study",
        progress={
            "quest_id": "legacy-envelope-study",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "same_transaction_opl_runtime_live_readback_required",
                    "source_ref": "controller/current_execution_envelope.json",
                },
            },
        },
        domain_transition_actions=lambda _study: [],
        explicit_readiness_action=lambda _progress: {},
    )

    assert typed_blocker is not None
    assert typed_blocker["authority"] == "legacy_current_execution_envelope_diagnostic_blocker"
    assert typed_blocker["authority_scope"] == "legacy_queue_blocker_diagnostic_only"
    assert typed_blocker["source_surface"] == "study_progress.current_execution_envelope"
    assert typed_blocker["diagnostic_only"] is True
    assert typed_blocker["default_dispatch_allowed"] is False
    assert typed_blocker["default_dispatch_blocked_reason"] == (
        "legacy_current_execution_envelope_is_diagnostic_only"
    )

    owner_receipt_recorded = current_action._fresh_progress_current_action(
        study_id="legacy-envelope-study",
        progress={
            "quest_id": "legacy-envelope-study",
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "MedAutoScience",
                "owner_receipt_ref": "controller/owner_receipt.json",
            },
        },
        domain_transition_actions=lambda _study: [],
        explicit_readiness_action=lambda _progress: {},
    )

    assert owner_receipt_recorded is not None
    assert owner_receipt_recorded["authority"] == "legacy_current_execution_envelope_diagnostic_blocker"
    assert owner_receipt_recorded["diagnostic_only"] is True
    assert owner_receipt_recorded["default_dispatch_allowed"] is False


def test_missing_canonical_next_action_retires_per_study_top_level_fallback() -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    study_id = "004-legacy-top-level-fallback"
    action = {
        "study_id": study_id,
        "action_id": "legacy-top-level-write",
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "legacy-top-level-write",
        "work_unit_fingerprint": "legacy-top-level-write::fingerprint",
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(study_id,),
        scan_payload={
            "studies": [{"study_id": study_id, "quest_id": study_id}],
            "action_queue": [action],
        },
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": study_id,
            "action_type": "run_quality_repair_batch",
            "action_id": "legacy-top-level-write",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_paper_recovery_ignores_monitoring_summary_legacy_current_action() -> None:
    recovery = importlib.import_module(
        "med_autoscience.controllers.paper_recovery_state_parts.successor_owner_resolution"
    )

    progress = {
        "progress_first_monitoring_summary": {
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "legacy_monitoring_summary",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "legacy-monitoring-write",
                "work_unit_fingerprint": "legacy-monitoring-write::fingerprint",
            }
        }
    }

    assert recovery.current_executable_owner_action(progress) == {}


def test_paper_recovery_obligation_does_not_resurrect_legacy_owner_without_canonical_next_action() -> None:
    recovery = importlib.import_module("med_autoscience.controllers.paper_recovery_state")

    state = recovery.build_paper_recovery_state(
        {
            "study_id": "legacy-only-study",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "legacy-action-unit",
                "work_unit_fingerprint": "legacy-action-unit::fingerprint",
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "next_work_unit": "legacy-envelope-unit",
            },
        }
    )

    obligation = state["current_authority"]["obligation"]
    assert obligation["owner"] is None
    assert obligation["action_type"] is None
    assert obligation["work_unit_id"] is None
    assert obligation["recovery_obligation_id"].startswith(
        "paper-recovery::legacy-only-study::unknown-action::unknown-work-unit::"
    )
