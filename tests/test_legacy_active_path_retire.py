from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def contract() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )


def tombstone(contract: dict[str, object], surface_id: str) -> dict[str, object]:
    return {
        item["surface_id"]: item
        for item in contract["tombstoned_surfaces"]
    }[surface_id]


@pytest.mark.parametrize(
    ("surface_id", "classification", "forbidden_claims", "authority_flags"),
    [
        (
            "domain_diagnostic_owner_route_dispatch_paper_recovery_default_paper_mainline",
            "retired_diagnostics_migration_provenance_only",
            {"product_default_mainline", "paper_progress", "runtime_ready", "DM002_complete"},
            (
                "can_write_domain_truth",
                "can_authorize_publication_quality",
                "can_authorize_artifact_mutation",
                "can_authorize_provider_attempt",
                "can_claim_paper_progress",
                "can_claim_runtime_ready",
            ),
        ),
        (
            "legacy_next_action_projection_and_selector_surfaces",
            "retired_next_action_diagnostics_provenance_only",
            {"default_next_action_selector", "provider_attempt_authority", "paper_progress", "runtime_ready"},
            (
                "can_select_default_next_action",
                "can_authorize_provider_attempt",
                "can_write_domain_truth",
                "can_authorize_publication_quality",
                "can_claim_paper_progress",
                "can_claim_runtime_ready",
            ),
        ),
    ],
)
def test_legacy_tombstones_are_diagnostic_only(
    contract: dict[str, object],
    surface_id: str,
    classification: str,
    forbidden_claims: set[str],
    authority_flags: tuple[str, ...],
) -> None:
    item = tombstone(contract, surface_id)

    assert item["classification"] == classification
    assert item["default_caller"] is False
    assert item["authority_boundary"]["read_only"] is True
    assert item["authority_boundary"]["retired_tombstone"] is True
    assert forbidden_claims <= set(item["forbidden_default_claims"])
    for flag in authority_flags:
        assert item["authority_boundary"][flag] is False


def test_legacy_tombstones_point_to_the_current_replacements(
    contract: dict[str, object],
) -> None:
    diagnostic = tombstone(
        contract,
        "domain_diagnostic_owner_route_dispatch_paper_recovery_default_paper_mainline",
    )
    next_action = tombstone(contract, "legacy_next_action_projection_and_selector_surfaces")

    assert diagnostic["replacement_ref"] == "contracts/paper_mission_run_contract.json"
    assert diagnostic["replacement_contract"]["validator"] == "med_autoscience.paper_mission_run.PaperMissionRun"
    assert diagnostic["replacement_parity_proof"]["replacement_action_intent"] == "domain_route/start-or-resume"
    assert next_action["replacement_projection_ref"] == "study_progress.next_action_envelope"
    assert next_action["replacement_contract"]["machine_contract"] == "StageOutcome -> NextActionEnvelope"
    assert next_action["replacement_contract"]["canonical_owner"] == "mas_next_action_compiler"


def test_no_active_default_caller_proof_keeps_legacy_references_non_authoritative(
    contract: dict[str, object],
) -> None:
    proof = contract["no_active_default_caller_proof"]
    legacy_policy = proof["readback_proof"]["legacy_active_caller_allowed_only_when"]

    assert proof["active_default_callers"] == []
    assert proof["default_cli_mcp_product_entry_or_skill_caller_count"] == 0
    assert proof["default_mainline_replacement"]["action_intent"] == "domain_route/start-or-resume"
    assert legacy_policy["default_paper_mission_entry"] is False
    assert legacy_policy["ordinary_schedulable"] is False
    assert legacy_policy["active_public_projection_alias_allowed"] is False
    assert {
        "runtime diagnostic",
        "authority consume/readback",
        "migration diagnostic",
        "history provenance",
    } <= set(proof["allowed_legacy_reference_classes"])
    for boundary in proof["legacy_reference_rigor_policy"]["allowed_reference_claim_boundaries"]:
        assert "paper_progress" in boundary["forbidden_claims"]
        assert boundary["can_select_next_paper_stage"] is False
        assert boundary["counts_as_paper_progress"] is False
        assert boundary["can_claim_runtime_ready"] is False


@pytest.mark.parametrize(
    ("reference_class", "required_evidence"),
    [
        ("runtime diagnostic", {"fresh_diagnostic_readback", "same_identity_boundary_or_explicit_stale_marker"}),
        (
            "authority consume/readback",
            {"consume_readback_payload", "written_files_empty_or_authority_surface_receipt_ref", "authority_materialized_flag"},
        ),
        (
            "migration diagnostic",
            {"legacy_truth_import_pack", "replacement_paper_mission_run_ref", "legacy_blocker_is_default_execution_state_false"},
        ),
        ("history provenance", {"tombstone_ref", "history_or_provenance_ref"}),
    ],
)
def test_allowed_legacy_references_cannot_make_live_claims(
    contract: dict[str, object],
    reference_class: str,
    required_evidence: set[str],
) -> None:
    policy = contract["no_active_default_caller_proof"]["legacy_reference_rigor_policy"]
    boundaries = {item["reference_class"]: item for item in policy["allowed_reference_claim_boundaries"]}
    boundary = boundaries[reference_class]

    assert set(boundary["required_evidence"]) == required_evidence
    assert "paper_progress" in boundary["forbidden_claims"]
    assert boundary["can_select_next_paper_stage"] is False
    assert boundary["counts_as_paper_progress"] is False
    assert boundary["can_claim_runtime_ready"] is False


def test_current_wording_and_receipt_markers_cannot_resurrect_authority(
    contract: dict[str, object],
) -> None:
    wording = contract["current_surface_wording_policy"]
    marker_policy = contract["legacy_control_receipt_exclusion_policy"]

    assert "docs/history/**" in wording["excluded_scope"]
    assert {"paper progress", "runtime-ready", "compatibility route"} <= set(wording["forbidden_claims"])
    assert wording["docs_or_tests_can_close_live_acceptance"] is False
    for flag in (
        "can_select_default_next_action",
        "can_claim_paper_progress",
        "can_claim_runtime_ready",
        "can_claim_submission_ready",
        "can_claim_current_package_ready",
    ):
        assert wording[flag] is False
    for flag in (
        "legacy_markers_are_active_aliases",
        "legacy_markers_are_default_entrypoints",
        "legacy_markers_are_public_projection_aliases",
        "legacy_markers_can_claim_no_active_caller",
        "legacy_markers_can_satisfy_runtime_readiness",
        "legacy_markers_can_satisfy_paper_progress",
    ):
        assert marker_policy["marker_alias_policy"][flag] is False


def test_domain_handler_default_mainline_has_no_legacy_dispatch_active_caller(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_route_handoff import domain_handler_export

    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        quest_id="002-dm-china-us-mortality-attribution",
    )
    export = domain_handler_export.export_family_domain_handler(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    assert export["dispatch"]["default_action_intent"] == "domain_route/start-or-resume"
    assert export["dispatch"]["default_queue_source"] == "/paper_mission_default_tasks"
    assert "stage_outcome/opl-handoff" not in export["dispatch"]["allowed_task_kinds"]
    assert [task["task_kind"] for task in export["paper_mission_default_tasks"]] == [
        "domain_route/start-or-resume"
    ]
    default_task = export["paper_mission_default_tasks"][0]
    assert default_task["payload"]["declarative_target_stage_id"] == (
        "direction_and_route_selection"
    )
    assert not [
        task
        for task in export["pending_family_tasks"]
        if task.get("default_paper_mission_entry") is True
    ]


def test_domain_handler_dispatch_rejects_legacy_owner_callable_adapter_task_kind(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_route_handoff import dispatch_orchestration

    task_path = tmp_path / "legacy-owner-callable-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "legacy-dispatch-001",
                "domain_id": "medautoscience",
                "task_kind": "domain_owner/owner-callable-adapter",
                "payload": {"profile": str(tmp_path / "profile.toml"), "study_id": "001-paper"},
            }
        ),
        encoding="utf-8",
    )

    receipt = dispatch_orchestration.dispatch_family_domain_handler_task(task_path=task_path)

    assert {
        "accepted": False,
        "reason": "legacy_owner_callable_dispatch_tombstoned",
        "task_kind": "domain_owner/owner-callable-adapter",
        "retired_diagnostic_task_kind": True,
        "default_paper_mission_entry": False,
        "migration_diagnostic_only": True,
        "ordinary_schedulable": False,
        "active_caller_class": "diagnostic_only",
        "replacement_task_kind": "domain_route/start-or-resume",
        "diagnostic_role": "retired_default_paper_dispatch",
    }.items() <= receipt.items()
