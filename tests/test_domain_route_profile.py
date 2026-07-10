from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission_domain import opl_runtime_submission
from med_autoscience.domain_route_profile import (
    TASK_KIND_NORMALIZATION,
    build_domain_route_handoff_intake_readback,
    build_domain_route_profile,
    canonical_domain_task_kind,
)


def _handoff(candidate_ref: str) -> dict[str, object]:
    transaction_ref = "paper-mission-transaction::study-001"
    return {
        "paper_mission_transaction_ref": transaction_ref,
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "route_command_kind": "route_back",
        "route_target": "review_and_quality_gate",
        "request_idempotency_key": f"{transaction_ref}::request",
        "candidate_ref": candidate_ref,
        "opl_route_command": {
            "command_kind": "route_back",
            "target": "review_and_quality_gate",
        },
    }


def test_domain_route_profile_owns_legacy_mapping_before_generic_opl_intake() -> None:
    profile = build_domain_route_profile()

    assert profile["agent_id"] == "mas"
    assert profile["domain_id"] == "medautoscience"
    assert profile["legacy_domain_ids"] == ["med-autoscience"]
    assert profile["canonical_task_kind"] == "domain_route/stage-route"
    assert profile["handoff_intake_surface_kind"] == (
        "opl_domain_route_handoff_intake_readback"
    )
    assert profile["runtime_request_surface_kind"] == "opl_domain_route_runtime_request"
    assert profile["legacy_compatibility"]["normalization_owner"] == "MedAutoScience"
    assert profile["task_kind_normalization"] == TASK_KIND_NORMALIZATION
    assert profile["terminal_sync_contract"]["primary_discriminator"] == "status"
    assert "writes_runtime_queue" in profile["forbidden_writes"]
    assert "typed_blocker_ref" in profile["receipt_labels"]["typed_blocker"]
    assert profile["authority_boundary"]["writes_domain_truth"] is False


def test_domain_task_kinds_normalize_only_at_the_mas_owned_profile_boundary() -> None:
    assert canonical_domain_task_kind("paper_mission/start_or_resume") == (
        "domain_route/start-or-resume"
    )
    assert canonical_domain_task_kind("paper_mission/stage-route") == (
        "domain_route/stage-route"
    )
    assert canonical_domain_task_kind("paper_autonomy/guarded-apply") == (
        "domain_autonomy/guarded-apply"
    )
    assert canonical_domain_task_kind(
        "publication_aftercare/reviewer-refresh"
    ) == "domain_route/reviewer-refresh"
    assert canonical_domain_task_kind("domain_route/custom") == "domain_route/custom"
    assert canonical_domain_task_kind(None) is None


def test_paper_mission_handoff_is_normalized_to_generic_domain_route(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"version": 1}), encoding="utf-8")

    readback = build_domain_route_handoff_intake_readback(_handoff(str(candidate)))
    request = readback["runtime_request"]

    assert readback["surface_kind"] == "opl_domain_route_handoff_intake_readback"
    assert readback["status"] == "accepted_for_provider_projection"
    assert request["surface_kind"] == "opl_domain_route_runtime_request"
    assert request["task_kind"] == "domain_route/stage-route"
    assert request["domain_id"] == "medautoscience"
    assert request["command_kind"] == "route_back"
    assert request["route_target"] == "review_and_quality_gate"
    assert request["domain_route_transaction_ref"] == (
        "paper-mission-transaction::study-001"
    )
    assert request["domain_route_command_ref"].endswith("#opl_route_command")
    assert request["route_identity"]["route_identity_key"].endswith("::route")
    assert request["attempt_identity"]["attempt_idempotency_key"].endswith("::attempt")
    assert request["authority_boundary"]["writes_runtime_queue"] is False
    rendered = json.dumps(request, ensure_ascii=False)
    assert "paper_mission_transaction_ref" not in rendered
    assert "opl_route_command" not in request
    assert "study_id" not in request


def test_runtime_submission_uses_generic_task_and_content_bound_dedupe(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"version": 1}), encoding="utf-8")
    first = opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
        _handoff(str(candidate))
    )
    candidate.write_text(json.dumps({"version": 2}), encoding="utf-8")
    second = opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
        _handoff(str(candidate))
    )

    assert first is not None and second is not None
    assert first["domainId"] == "medautoscience"
    assert first["taskKind"] == "domain_route/stage-route"
    assert first["payload"]["surface_kind"] == "opl_domain_route_runtime_request"
    assert first["dedupe_key"] != second["dedupe_key"]


def test_terminal_domain_route_discriminators_are_generic() -> None:
    typed_blocker = _handoff("candidate.json")
    typed_blocker["route_command_kind"] = "stop_with_typed_blocker"
    typed_blocker["opl_route_command"] = {
        "command_kind": "stop_with_typed_blocker",
        "target": "current_owner_resolution",
    }
    typed_readback = build_domain_route_handoff_intake_readback(typed_blocker)

    assert typed_readback["status"] == "typed_wait"
    assert typed_readback["wait_kind"] == "typed_blocker_authority"
    assert typed_readback["runtime_request"] is None
    assert "typed_blocker_ref" in typed_readback["terminal_sync"][
        "required_receipt_labels"
    ]

    complete = _handoff("candidate.json")
    complete["route_command_kind"] = "complete_mission"
    complete["opl_route_command"] = {
        "command_kind": "complete_mission",
        "target": "mission_complete",
    }
    complete_readback = build_domain_route_handoff_intake_readback(complete)

    assert complete_readback["status"] == "terminal_no_runtime"
    assert complete_readback["wait_kind"] == "mission_complete"
    assert complete_readback["runtime_request"] is None
    assert complete_readback["terminal_sync"]["primary_discriminator"] == (
        "terminal_no_runtime"
    )
