from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.domain_route_profile import (
    TASK_KIND_NORMALIZATION,
    build_domain_route_handoff_intake_readback,
    build_domain_route_profile,
    build_domain_route_runtime_request,
    canonical_domain_task_kind,
)


def _handoff(candidate_ref: str) -> dict[str, object]:
    transaction_ref = "paper-mission-transaction::study-001"
    return {
        "paper_mission_transaction_ref": transaction_ref,
        "ai_route_context_ref": f"{transaction_ref}#ai_route_context",
        "route_command_kind": "route_back",
        "route_target": "review_and_quality_gate",
        "declarative_target_stage_id": "review_and_quality_gate",
        "request_idempotency_key": f"{transaction_ref}::request",
        "candidate_ref": candidate_ref,
        "ai_route_context": {
            "command_kind": "route_back",
            "target": "review_and_quality_gate",
            "declarative_target_stage_id": "review_and_quality_gate",
        },
    }


def test_domain_route_profile_owns_legacy_mapping_before_generic_opl_intake() -> None:
    profile = build_domain_route_profile()

    assert profile["agent_id"] == "mas"
    assert profile["domain_id"] == "mas"
    assert profile["legacy_domain_ids"] == ["medautoscience", "med-autoscience"]
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


def test_tracked_domain_route_profile_matches_canonical_builder() -> None:
    contract_path = Path(__file__).resolve().parents[1] / "contracts" / "domain_route_profile.json"

    assert json.loads(contract_path.read_text(encoding="utf-8")) == (
        build_domain_route_profile()
    )


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
    assert request["domain_id"] == "mas"
    assert request["command_kind"] == "route_back"
    assert request["route_target"] == "review_and_quality_gate"
    assert request["declarative_target_stage_id"] == (
        "review_and_quality_gate"
    )
    assert request["domain_route_transaction_ref"] == (
        "paper-mission-transaction::study-001"
    )
    assert request["domain_route_command_ref"].endswith("#ai_route_context")
    assert request["route_identity"]["route_identity_key"].endswith("::route")
    assert request["attempt_identity"]["attempt_idempotency_key"].endswith("::attempt")
    assert request["authority_boundary"]["writes_runtime_queue"] is False
    rendered = json.dumps(request, ensure_ascii=False)
    assert "paper_mission_transaction_ref" not in rendered
    assert "ai_route_context" not in request
    assert "study_id" not in request


def test_runtime_request_uses_explicit_stage_and_content_bound_dedupe(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"version": 1}), encoding="utf-8")
    first = build_domain_route_runtime_request(_handoff(str(candidate)))
    candidate.write_text(json.dumps({"version": 2}), encoding="utf-8")
    second = build_domain_route_runtime_request(_handoff(str(candidate)))

    assert first is not None and second is not None
    assert first["domain_id"] == "mas"
    assert first["surface_kind"] == "opl_domain_route_runtime_request"
    assert first["declarative_target_stage_id"] == "review_and_quality_gate"
    assert first["route_identity"]["dedupe_key"] != second["route_identity"][
        "dedupe_key"
    ]


def test_runtime_request_rejects_missing_explicit_stage_without_route_target_inference(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"version": 1}), encoding="utf-8")
    handoff = _handoff(str(candidate))
    handoff.pop("declarative_target_stage_id")
    handoff["ai_route_context"].pop("declarative_target_stage_id")

    readback = build_domain_route_handoff_intake_readback(handoff)

    assert readback["status"] == "rejected"
    assert readback["runtime_request"] is None
    assert {
        blocker["field"] for blocker in readback["blockers"]
    } == {"declarative_target_stage_id"}


def test_runtime_request_rejects_conflicting_explicit_stage_identity(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"version": 1}), encoding="utf-8")
    handoff = _handoff(str(candidate))
    handoff["ai_route_context"]["declarative_target_stage_id"] = (
        "06-manuscript_authoring"
    )

    readback = build_domain_route_handoff_intake_readback(handoff)

    assert readback["status"] == "rejected"
    assert readback["runtime_request"] is None
    assert readback["blockers"][-1] == {
        "reason": "domain_route_stage_identity_mismatch",
        "field": "declarative_target_stage_id",
    }


def test_terminal_domain_route_discriminators_are_generic() -> None:
    typed_blocker = _handoff("candidate.json")
    typed_blocker["route_command_kind"] = "stop_with_typed_blocker"
    typed_blocker["ai_route_context"] = {
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
    complete["ai_route_context"] = {
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
