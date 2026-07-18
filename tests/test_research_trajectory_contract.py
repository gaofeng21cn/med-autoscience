from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts/schemas/v2"
FIXTURE_DIR = ROOT / "tests/fixtures/research_trajectory"
STAGE_IDS = [
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
]
V2_TOP_LEVEL_FIELDS = {
    "surface_kind",
    "version",
    "study_id",
    "study_ref",
    "revision",
    "status",
    "summary",
    "current_focus",
    "active_branch",
    "current_focus_node_refs",
    "active_branch_node_refs",
    "nodes",
    "edges",
    "medical_narrative",
    "source_refs",
    "conditions",
}
USER_VISIBLE_KEYS = {
    "title",
    "research_question",
    "current_hypothesis",
    "validation_method",
    "main_findings",
    "evidence_judgment",
    "route_adjustment",
    "next_research_step",
    "limitations",
    "sources_and_basis",
    "primary_hypothesis",
    "latest_finding",
    "current_judgment",
    "label",
    "summary",
    "reason",
    "message",
    "details",
    "medical_narrative",
}
FORMAT_CHECKER = FormatChecker()
RFC3339_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


@FORMAT_CHECKER.checks("date-time", raises=ValueError)
def _is_timezone_aware_iso_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if RFC3339_DATETIME.fullmatch(value) is None:
        return False
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized).tzinfo is not None


def _load(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _validator(filename: str) -> Draft202012Validator:
    schemas = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in SCHEMA_DIR.glob("mas-*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(item for item in schemas if item["$id"].endswith(f"/{filename}"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FORMAT_CHECKER,
    )


def _fixture() -> dict[str, Any]:
    return _load(
        "tests/fixtures/research_trajectory/hypothesis_inconclusive_pivot.json"
    )


def _collect_user_visible_strings(value: Any, visible: bool = False) -> list[str]:
    collected: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_visible = visible or key in USER_VISIBLE_KEYS
            if isinstance(item, str) and child_visible:
                collected.append(item)
            elif isinstance(item, (dict, list)) and child_visible:
                collected.extend(_collect_user_visible_strings(item, True))
            elif isinstance(item, (dict, list)):
                collected.extend(_collect_user_visible_strings(item, False))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and visible:
                collected.append(item)
            elif isinstance(item, (dict, list)):
                collected.extend(_collect_user_visible_strings(item, visible))
    return collected


def test_v2_snapshot_has_exact_lightweight_shape_and_valid_fixture() -> None:
    schema = _load(
        "contracts/schemas/v2/mas-research-trajectory-snapshot-v2.schema.json"
    )
    snapshot = _fixture()["snapshot"]

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == V2_TOP_LEVEL_FIELDS
    assert set(schema["properties"]) == V2_TOP_LEVEL_FIELDS
    assert set(snapshot) == V2_TOP_LEVEL_FIELDS
    assert snapshot["surface_kind"] == "mas_research_trajectory_snapshot"
    assert snapshot["version"] == "mas-research-trajectory-snapshot.v2"
    _validator("mas-research-trajectory-snapshot-v2.schema.json").validate(snapshot)


def test_v2_identity_is_explicit_and_machine_only() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    snapshot = _fixture()["snapshot"]
    binding = contract["snapshot_contract"]["study_identity_binding"]

    assert binding == {
        "study_id_must_equal_work_item_id": True,
        "study_ref_kind": "mas_study",
        "study_ref_value_template": "mas-study:{study_id}",
        "study_ref_must_exactly_match_template": True,
        "study_ref_is_machine_only": True,
    }
    assert snapshot["study_ref"] == {
        "kind": "mas_study",
        "ref": f"mas-study:{snapshot['study_id']}",
    }

    invalid_kind = deepcopy(snapshot)
    invalid_kind["study_ref"]["kind"] = "artifact"
    assert list(
        _validator("mas-research-trajectory-snapshot-v2.schema.json").iter_errors(
            invalid_kind
        )
    )


def test_v2_omits_checkpoint_acceptance_and_event_control_fields() -> None:
    schema = _load(
        "contracts/schemas/v2/mas-research-trajectory-snapshot-v2.schema.json"
    )
    forbidden = {
        "working_checkpoints",
        "accepted_event_count",
        "accepted_event_refs",
        "event_set_sha256",
        "latest_event_id",
        "projector_version",
        "generation",
        "checkpoint_manifest_ref",
        "owner_receipt_ref",
    }
    assert not (forbidden & set(schema["properties"]))

    contract = _load("contracts/research_trajectory_contract.json")
    write_policy = contract["write_policy"]
    assert write_policy["mode"] == "ai_first_direct_artifact_update"
    assert write_policy["framework_checkpoint_submission_required"] is False
    assert write_policy["candidate_acceptance_required"] is False
    assert write_policy["receipt_required_for_progress_update"] is False
    assert write_policy["event_log_required_for_v2_write"] is False
    assert write_policy["working_checkpoint_layer_allowed"] is False


def test_legacy_v1_event_is_readable_but_not_a_v2_write_path() -> None:
    fixture = _fixture()
    validator = _validator("mas-research-trajectory-event.schema.json")
    for event in fixture["events"]:
        validator.validate(event)

    compatibility = _load("contracts/research_trajectory_contract.json")[
        "legacy_v1_read_compatibility"
    ]
    assert compatibility["new_v1_writes_allowed"] is False
    assert compatibility["accepted_event_materialization_is_v2_write_path"] is False
    assert compatibility["legacy_receipts_are_historical_read_context_only"] is True


def test_graph_is_drawable_and_current_route_refs_are_explicit() -> None:
    snapshot = _fixture()["snapshot"]
    node_ids = [node["id"] for node in snapshot["nodes"]]
    edge_ids = [edge["id"] for edge in snapshot["edges"]]
    snapshot_contract = _load("contracts/research_trajectory_contract.json")[
        "snapshot_contract"
    ]

    assert len(node_ids) == len(set(node_ids))
    assert len(edge_ids) == len(set(edge_ids))
    assert snapshot["current_focus"]["node_id"] in node_ids
    assert snapshot["current_focus"]["node_id"] in snapshot[
        "current_focus_node_refs"
    ]
    assert set(snapshot["current_focus_node_refs"]) <= set(node_ids)
    assert set(snapshot["active_branch_node_refs"]) <= set(node_ids)
    nodes_by_id = {node["id"]: node for node in snapshot["nodes"]}
    for node_ref in snapshot["active_branch_node_refs"]:
        assert nodes_by_id[node_ref]["branch_id"] == snapshot["active_branch"][
            "branch_id"
        ]
    for edge in snapshot["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
        assert edge["source_refs"]
    assert any(node["status"] in {"inconclusive", "does_not_support"} for node in snapshot["nodes"])
    assert any(edge["kind"] == "revises" for edge in snapshot["edges"])
    assert snapshot_contract["node_ids_must_be_unique"] is True
    assert snapshot_contract["edge_ids_must_be_unique"] is True
    assert snapshot_contract[
        "current_focus_node_id_must_reference_existing_node"
    ] is True
    assert snapshot_contract[
        "current_focus_node_id_must_be_listed_in_current_focus_node_refs"
    ] is True
    assert snapshot_contract[
        "current_route_membership_must_reference_existing_nodes"
    ] is True
    assert snapshot_contract[
        "active_branch_node_refs_must_match_active_branch_branch_id"
    ] is True
    assert snapshot_contract["edges_must_reference_existing_nodes"] is True


def test_snapshot_date_times_are_format_checked() -> None:
    for invalid_value in (
        "not-a-date",
        "2026-07-17 04:00:00+00:00",
        "2026-W29-5T04:00:00+00:00",
    ):
        invalid = deepcopy(_fixture()["snapshot"])
        invalid["nodes"][0]["occurred_at"] = invalid_value
        errors = list(
            _validator(
                "mas-research-trajectory-snapshot-v2.schema.json"
            ).iter_errors(invalid)
        )
        assert errors


def test_contract_distinguishes_failure_non_support_and_insufficient_evidence() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    semantics = contract["scientific_semantics"]
    assert semantics[
        "execution_outcome_evidence_interpretation_and_route_decision_are_independent"
    ] is True
    assert semantics["execution_failure_is_not_evidence_against_hypothesis"] is True
    assert semantics["execution_failure_user_wording"] != semantics[
        "does_not_support_user_wording"
    ]
    assert semantics["does_not_support_user_wording"] != semantics[
        "insufficient_evidence_user_wording"
    ]
    assert semantics["unsuccessful_routes_must_remain_in_graph"] is True
    assert semantics["route_change_requires_reader_facing_reason"] is True

    statuses = set(
        _load(
            "contracts/schemas/v2/mas-research-trajectory-snapshot-v2.schema.json"
        )["$defs"]["map_node"]["properties"]["status"]["enum"]
    )
    assert {"execution_failed", "not_assessed", "does_not_support", "inconclusive"} <= statuses


def test_fixed_dual_file_update_policy_is_declared_by_all_six_stages() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    paths = contract["write_policy"]["same_semantic_update_outputs"]
    assert paths == [
        "artifacts/research_trajectory/snapshot.json",
        "artifacts/research_trajectory/TRAJECTORY.md",
    ]
    assert contract["write_policy"]["same_semantic_update_required"] is True
    assert contract["meaningful_change_policy"][
        "activity_without_meaningful_scientific_change_must_not_increment_revision"
    ] is True

    manifest = _load("agent/stages/manifest.json")
    assert [stage["stage_id"] for stage in manifest["stages"]] == STAGE_IDS
    for stage in manifest["stages"]:
        trajectory = stage["stage_contract_extension"]["research_trajectory"]
        assert trajectory["version"] == "mas-stage-research-trajectory-obligation.v2"
        assert trajectory["fixed_artifact_paths"] == list(reversed(paths))
        assert trajectory["write_mode"] == (
            "current_mas_attempt_direct_same_semantic_update"
        )
        assert trajectory["update_when"]
        assert trajectory[
            "tool_call_heartbeat_or_retry_without_scientific_change_updates_trajectory"
        ] is False
        assert trajectory["independent_reviewer_is_write_prerequisite"] is False
        assert trajectory["current_v2_stage_output_value"] is None
        assert trajectory["new_required_stage_output_fields"] == []

        prompt = (ROOT / stage["prompt_ref"]).read_text(encoding="utf-8")
        normalized = " ".join(prompt.split())
        assert "## Research Trajectory" in prompt
        assert "artifacts/research_trajectory/TRAJECTORY.md" in prompt
        assert "artifacts/research_trajectory/snapshot.json" in prompt
        assert "does not start or wait for an independent reviewer" in normalized or (
            "neither starts nor waits for independent review" in normalized
        ) or "requires no separate acceptance receipt" in normalized
        assert "not the v2 write gate" in normalized
        assert "current v2 Stage output returns it as `null`" in normalized


def test_stage_output_v1_gets_no_new_required_trajectory_field() -> None:
    schema = _load("contracts/schemas/v2/mas-stage-action.output.schema.json")
    trajectory_fields = {
        field for field in schema["required"] if "research_trajectory" in field
    }
    assert trajectory_fields == {"research_trajectory_delta_ref"}
    assert "research_trajectory_checkpoint_manifest_ref" not in schema["properties"]
    compatibility = _load("contracts/research_trajectory_contract.json")[
        "stage_output_compatibility"
    ]
    assert compatibility["new_required_stage_output_fields"] == []
    assert compatibility["legacy_nullable_field"] == "research_trajectory_delta_ref"
    assert compatibility["current_v2_stage_output_value"] is None


def test_descriptor_and_projection_publish_exact_v2_payload() -> None:
    descriptor = _load("contracts/domain_descriptor.json")
    assert descriptor["standard_agent_interface"]["domain_detail_views"] == [
        {
            "view_id": "scientific-reasoning",
            "view_kind": "scientific_reasoning_map",
            "schema_version": "scientific-reasoning-map.v2",
            "source_kind": "work_item_relative_json",
            "relative_path": "artifacts/research_trajectory/snapshot.json",
        }
    ]
    projection = _load("contracts/domain_projection_profile.json")[
        "domain_detail_view_projection"
    ]
    assert set(projection["full_payload_fields"]) == V2_TOP_LEVEL_FIELDS
    assert projection["current_route_membership_source"] == (
        "current_focus_node_refs_and_active_branch_node_refs_exact"
    )
    assert projection["working_checkpoint_layer_allowed"] is False


def test_markdown_and_fixture_visible_text_have_no_selected_machine_leakage() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    snapshot = _fixture()["snapshot"]
    markdown = (FIXTURE_DIR / "TRAJECTORY.md").read_text(encoding="utf-8")
    for heading in contract["human_readable_contract"][
        "required_user_headings_zh_CN"
    ]:
        assert f"## {heading}" in markdown

    user_text = "\n".join(_collect_user_visible_strings(snapshot)) + "\n" + markdown
    lowered = user_text.lower()
    forbidden_tokens = {
        "code_path",
        "file_path",
        "node_id",
        "event_id",
        "attempt_id",
        "stage_run",
        "payload",
        "sha256",
        "provider",
        "runtime_queue",
        "checkpoint",
        "artifacts/",
        "/users/",
        "代码路径",
        "文件路径",
        "哈希",
        "载荷",
        "内部推理",
    }
    assert not {token for token in forbidden_tokens if token in lowered}
    assert re.search(r"\b[a-f0-9]{64}\b", lowered) is None

    assert snapshot["summary"]["primary_hypothesis"] in markdown
    assert "效应估计接近无效值" in snapshot["summary"]["latest_finding"]
    assert "效应估计接近无效值" in markdown
    assert "现有证据尚不足" in snapshot["medical_narrative"]["evidence_judgment"] or (
        "现有结果不足" in snapshot["medical_narrative"]["evidence_judgment"]
    )
    assert "现有证据尚不足" in markdown
    assert "完成高危亚组和持续性血糖波动分析" in snapshot[
        "summary"
    ]["next_research_step"]
    assert "完成高危亚组和持续性血糖波动分析" in markdown


def test_tests_are_declared_as_structural_not_medical_quality_proof() -> None:
    boundary = _load("contracts/research_trajectory_contract.json")[
        "testing_boundary"
    ]
    assert boundary["tests_prove_medical_prose_quality"] is False
    assert boundary["tests_prove_scientific_conclusion_correctness"] is False

    knowledge = (
        ROOT / "agent/knowledge/research_trajectory_medical_narrative.md"
    ).read_text(encoding="utf-8")
    assert "Do not wait for an independent reviewer" in knowledge
    assert "It does not prove" in knowledge
    assert "tool call" in knowledge
    assert "heartbeat" in knowledge
