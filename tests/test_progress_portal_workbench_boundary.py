from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.progress_portal_cases.helpers import progress_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


def _study_workbench_payload() -> dict[str, object]:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    return parts.build_study_workbench_payload(
        progress=progress_payload(),
        cockpit={
            "studies": [
                {
                    "study_id": "001-risk",
                    "next_system_action": "legacy cockpit action summary",
                    "monitoring": {"health_status": "recovering"},
                }
            ]
        },
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )


def _runtime_workbench_projection(study_workbench: dict[str, object]) -> dict[str, object]:
    module = importlib.import_module(
        "med_autoscience.controllers.progress_portal_parts.runtime_workbench_projection"
    )
    progress = progress_payload()
    return module.build_runtime_workbench_projection(
        workspace_root=REPO_ROOT,
        profile_ref=None,
        profile_name="test-profile",
        generated_at="2026-06-18T00:00:00+08:00",
        study_id="001-risk",
        workspace_overview_mode=False,
        page_scope="study",
        workspace_study_rows=[
            {
                "study_id": "001-risk",
                "next_system_action": "row action summary",
                "operator_focus": "operator focus summary",
            }
        ],
        user_visible=progress["user_visible_projection"],
        progress=progress,
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        freshness=progress["progress_freshness"],
        source_refs=["studies/001-risk/progress_projection.json"],
        conditions={"missing": [], "stale": [], "conflict": []},
        study_workbench=study_workbench,
    )


def test_study_workbench_next_system_action_is_read_only_owner_delta_summary() -> None:
    payload = _study_workbench_payload()

    assert payload["tabs"][0] == {
        "id": "current_owner_delta",
        "label": "Current Owner Delta",
        "status": "available",
    }
    default_read = payload["current_owner_delta"]
    assert default_read["surface_kind"] == "mas_progress_portal_current_owner_delta_default_read"
    assert default_read["read_surface_role"] == "ordinary_default_current_owner_delta"
    assert default_read["default_read_priority"] == 0
    assert default_read["owner"] == "ai_reviewer"
    assert default_read["action_type"] == "run_quality_repair_batch"
    assert default_read["work_unit_id"] == "quality-repair-001"
    assert default_read["required_delta_kind"] == "owner_receipt_or_typed_blocker"
    assert default_read["typed_blocker_ref"] == "studies/001-risk/artifacts/owner/typed_blocker.json"
    assert {"raw_worklist", "provider_trace", "queue_counts", "legacy_dispatch"} <= set(
        default_read["audit_plane_exclusions"]
    )
    assert default_read["authority"]["projection_only"] is True
    assert default_read["authority"]["can_generate_action"] is False
    assert default_read["authority"]["can_authorize_provider_admission"] is False

    boundary = payload["overview_action_boundary"]
    assert payload["overview"]["next_system_action_boundary"] == boundary
    assert boundary["surface_kind"] == "mas_progress_portal_study_workbench_overview_action_boundary"
    assert boundary["next_system_action_role"] == "read_only_owner_delta_summary"
    assert boundary["projection_only"] is True
    assert boundary["can_generate_action"] is False
    assert boundary["can_execute"] is False
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["can_authorize_worker_attempt"] is False
    assert boundary["requires_opl_current_control_readback"] is True
    assert boundary["must_not_be_used_as_provider_admission"] is True
    assert boundary["must_not_be_used_as_next_action_authority"] is True
    assert boundary["must_not_be_used_as_publication_ready"] is True
    assert boundary["must_not_be_used_as_paper_progress"] is True


def test_study_workbench_renders_current_owner_delta_before_diagnostics() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal_parts.study_workbench")
    html = module.render_study_workbench_sections(_study_workbench_payload())

    assert html.index("Current Owner Delta") < html.index("运行")
    assert "run_quality_repair_batch" in html
    assert "provider_trace" in html


def test_action_owner_routing_policy_cannot_dispatch_or_admit_provider() -> None:
    policy = _study_workbench_payload()["action_owner_routing_policy"]

    assert policy["routing_role"] == "display_and_owner_route_projection"
    assert policy["can_generate_action"] is False
    assert policy["can_execute"] is False
    assert policy["can_authorize_provider_admission"] is False
    assert policy["can_authorize_worker_attempt"] is False
    assert policy["must_not_be_used_as_next_action_authority"] is True
    assert policy["must_not_be_used_as_provider_admission"] is True
    assert policy["authority"]["writes_authority_surface"] is False
    assert policy["authority"]["can_execute_controller_actions"] is False
    assert policy["authority"]["can_authorize_provider_admission"] is False
    assert policy["authority"]["can_authorize_worker_attempt"] is False
    assert policy["authority"]["can_authorize_publication_readiness"] is False


def test_runtime_workbench_projection_actions_and_summaries_remain_read_only_refs() -> None:
    projection = _runtime_workbench_projection(_study_workbench_payload())
    selected = next(item for item in projection["studies"] if item["study_id"] == "001-risk")

    assert projection["projection_boundary"]["projection_only"] is True
    assert projection["projection_boundary"]["next_summary_role"] == "read_only_drilldown_summary"
    assert projection["projection_boundary"]["actions_role"] == "operator_intent_projection_refs"
    assert projection["projection_boundary"]["operator_intent_refs_are_inert"] is True
    assert projection["projection_boundary"]["must_not_be_used_as_next_action_authority"] is True
    assert projection["projection_boundary"]["must_not_be_used_as_provider_admission"] is True
    assert projection["projection_boundary"]["must_not_be_used_as_publication_ready"] is True
    assert projection["projection_boundary"]["can_generate_next_action_authority"] is False
    assert projection["projection_boundary"]["can_execute_controller_action"] is False
    assert projection["projection_boundary"]["can_authorize_provider_admission"] is False
    assert projection["projection_boundary"]["can_authorize_worker_attempt"] is False
    assert projection["projection_boundary"]["can_transport_operator_action"] is False
    assert projection["projection_boundary"]["can_emit_runtime_command"] is False
    assert projection["projection_boundary"]["can_open_runtime_endpoint"] is False
    assert projection["authority"]["claims_publication_ready"] is False
    assert projection["authority"]["writes_mas_truth"] is False
    assert projection["authority"]["opl_role"] == "workbench_readback_projection_consumer_only"
    assert projection["authority"]["can_transport_operator_action"] is False
    assert projection["authority"]["can_emit_runtime_command"] is False
    assert projection["authority"]["operator_intent_refs_are_inert"] is True

    assert selected["next_action_summary_role"] == "read_only_drilldown_summary"
    assert selected["next_action_summary_is_controller_action"] is False
    assert selected["next_action_summary_can_generate_action"] is False
    assert selected["next_action_summary_requires_opl_current_control_readback"] is True
    assert selected["actions_role"] == "operator_intent_projection_refs"
    assert selected["actions_can_execute"] is False
    assert selected["actions_authority"] is False
    for action in selected["operator_intent_projection"].values():
        assert action["surface_kind"] == "workbench_operator_intent_projection_ref"
        assert action["authority"] is False
        assert action["allowed"] is False
        assert action["command"] is None
        assert action["can_execute"] is False
        assert action["can_generate_action"] is False
        assert action["can_authorize_provider_admission"] is False
        assert action["execute_authority"] is False
        assert action["controller_action"] is False
        assert action["projection_only"] is True
        assert action["intent_ref_only"] is True
        assert action["transport_authority"] is False
        assert action["runtime_endpoint_ref"] is None
        assert action["can_transport_operator_action"] is False
        assert action["can_emit_runtime_command"] is False
        assert action["display_command_ref_only"] is True
        assert action["requires_opl_current_control_readback"] is True
        assert action["handled_by_external_opl_workbench_shell"] is True


def test_retirement_inventory_tracks_workbench_read_only_action_projection() -> None:
    inventory = json.loads(
        (REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {item["surface_id"]: item for item in inventory["surfaces"]}
    surface = surfaces["progress_portal_study_workbench_overview_action_projection"]

    assert surface["current_disposition"] == "read_only_workbench_projection"
    assert surface["retained_mas_role"] == "body_free_workbench_read_model_projection"
    assert surface["generic_runtime_owner"] == "one-person-lab"
    assert surface["mas_owner_claim_allowed"] is False
    assert surface["compatibility_alias_allowed"] is False
    assert set(surface["forbidden_claims"]) >= {
        "workbench_next_system_action_as_controller_action",
        "workbench_operator_intent_as_provider_admission",
        "workbench_summary_as_next_action_authority",
        "workbench_projection_clean_as_runtime_ready",
        "workbench_action_summary_as_paper_progress",
        "workbench_action_summary_as_publication_ready",
    }
    assert surface["projection_boundary"] == {
        "next_system_action_role": "read_only_owner_delta_summary",
        "projection_only": True,
        "can_generate_action": False,
            "can_execute": False,
            "can_emit_runtime_command": False,
            "can_authorize_provider_admission": False,
            "can_authorize_worker_attempt": False,
            "can_open_runtime_endpoint": False,
            "can_transport_operator_action": False,
            "operator_intent_refs_are_inert": True,
            "requires_opl_current_control_readback": True,
            "must_not_be_used_as_provider_admission": True,
            "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_publication_ready": True,
        "must_not_be_used_as_paper_progress": True,
    }
