from __future__ import annotations

import importlib


def _module():
    return importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_authority"
    )


def _stage_native_repair_action() -> dict[str, object]:
    return {
        "action_type": "run_quality_repair_batch",
        "authority": "stage_native_workspace_next_action",
        "default_dispatch_allowed": True,
        "stage_native_next_action_admission": {
            "default_dispatch_allowed": True,
        },
        "current_work_unit_binding": {
            "source": "canonical_current_work_unit",
            "work_unit_id": "medical_publication_surface_blocked_write_repair",
            "work_unit_fingerprint": (
                "stage-native-next-action::08-publication_package_handoff::"
                "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
            ),
        },
    }


def _readiness_barrier(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "action_type": "current_execution_envelope_typed_blocker",
        "reason": "medical_paper_readiness_missing",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "current_work_unit_status": "typed_blocker",
        "current_work_unit_state_kind": "typed_blocker",
        "current_work_unit_id": "complete_medical_paper_readiness_surface",
        "current_work_unit_stale_queue_or_handoff_can_override": False,
    }
    payload.update(overrides)
    return payload


def test_stage_native_action_derives_only_from_current_readiness_barrier() -> None:
    assert (
        _module().stage_native_action_derives_from_readiness_barrier(
            fresh_action=_readiness_barrier(),
            action=_stage_native_repair_action(),
        )
        is True
    )


def test_stage_native_action_does_not_derive_from_stale_readiness_barrier() -> None:
    assert (
        _module().stage_native_action_derives_from_readiness_barrier(
            fresh_action=_readiness_barrier(
                current_work_unit_stale_queue_or_handoff_can_override=True
            ),
            action=_stage_native_repair_action(),
        )
        is False
    )


def test_stage_native_action_does_not_derive_without_current_work_unit_readiness_identity() -> None:
    assert (
        _module().stage_native_action_derives_from_readiness_barrier(
            fresh_action=_readiness_barrier(
                current_work_unit_status=None,
                current_work_unit_state_kind=None,
                current_work_unit_id=None,
            ),
            action=_stage_native_repair_action(),
        )
        is False
    )
