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


def test_canonical_next_action_blocks_provider_admission_current_control_candidate() -> None:
    payload = _canonical_payload()
    provider_actions = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions"
    )

    assert provider_actions._study_current_action_for_provider_admission(payload) is None


def test_missing_canonical_next_action_does_not_resurrect_legacy_default_owner_action() -> None:
    payload = _canonical_payload()
    payload.pop("next_action")
    payload.pop("canonical_next_action_source")

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection"
    )

    assert current_action.build_canonical_owner_action_projection(payload) is None


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
