from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
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
MAP_PAYLOAD_FIELDS = {
    "study_id",
    "status",
    "summary",
    "current_focus",
    "active_branch",
    "nodes",
    "edges",
    "source_refs",
    "conditions",
}
USER_VISIBLE_SCALAR_FIELDS = {
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
    "display_label",
    "medical_summary",
    "label",
    "message",
    "reason",
    "primary_hypothesis",
    "latest_finding",
    "current_judgment",
}


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
    return Draft202012Validator(schema, registry=registry)


def _fixture() -> dict[str, Any]:
    return _load(
        "tests/fixtures/research_trajectory/hypothesis_inconclusive_pivot.json"
    )


def _collect_user_visible_strings(value: Any) -> list[str]:
    collected: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in USER_VISIBLE_SCALAR_FIELDS:
                if isinstance(item, str):
                    collected.append(item)
                elif isinstance(item, list):
                    collected.extend(entry for entry in item if isinstance(entry, str))
                elif isinstance(item, dict):
                    collected.extend(_collect_user_visible_strings(item))
            elif isinstance(item, (dict, list)):
                collected.extend(_collect_user_visible_strings(item))
    elif isinstance(value, list):
        for item in value:
            collected.extend(_collect_user_visible_strings(item))
    return collected


def test_medical_fixture_validates_event_and_snapshot_schemas() -> None:
    fixture = _fixture()
    event_validator = _validator("mas-research-trajectory-event.schema.json")
    snapshot_validator = _validator("mas-research-trajectory-snapshot.schema.json")

    assert fixture["study_id"] == "DM-CVD-TRAJECTORY-001"
    assert len(fixture["events"]) == 4
    for event in fixture["events"]:
        event_validator.validate(event)
        assert event["study_id"] == fixture["study_id"]
        assert event["lifecycle_status"] == "accepted"
        assert event["acceptance"]["acceptance_ref"]["sha256"].startswith("sha256:")

    snapshot_validator.validate(fixture["snapshot"])
    assert MAP_PAYLOAD_FIELDS <= set(fixture["snapshot"])
    assert fixture["snapshot"]["accepted_event_count"] == len(fixture["events"])


def test_acceptance_is_exact_and_basis_kind_coherent() -> None:
    validator = _validator("mas-research-trajectory-event.schema.json")
    owner_event = deepcopy(_fixture()["events"][0])
    owner_event["acceptance"]["acceptance_ref"].pop("sha256")
    assert list(validator.iter_errors(owner_event))

    wrong_owner_kind = deepcopy(_fixture()["events"][0])
    wrong_owner_kind["acceptance"]["acceptance_ref"]["kind"] = (
        "mas_reviewer_receipt"
    )
    assert list(validator.iter_errors(wrong_owner_kind))

    wrong_reviewer_kind = deepcopy(_fixture()["events"][2])
    wrong_reviewer_kind["acceptance"]["acceptance_ref"]["kind"] = (
        "owner_receipt"
    )
    assert list(validator.iter_errors(wrong_reviewer_kind))


def test_fixture_preserves_inconclusive_null_result_and_route_evolution() -> None:
    events = _fixture()["events"]
    assert [event["event_type"] for event in events] == [
        "hypothesis_proposed",
        "test_planned",
        "result_observed",
        "hypothesis_refined",
    ]

    result = events[2]
    assert result["execution_outcome"]["status"] == "completed"
    assert result["evidence_interpretation"]["status"] == "inconclusive"
    assert result["evidence_interpretation"]["finding_kind"] == "null"
    assert result["route_decision"]["status"] == "refine"
    assert result["node"]["status"] == "inconclusive"

    revised = events[3]
    assert revised["route_decision"]["status"] == "pivot"
    assert revised["edges"][0]["relation"] == "revises"
    assert revised["projection_hints"]["current_focus"]["node_id"] == (
        "hypothesis-high-risk-v2"
    )


def test_negative_null_inconclusive_and_design_invalid_findings_are_recordable() -> None:
    validator = _validator("mas-research-trajectory-event.schema.json")
    null_inconclusive = deepcopy(_fixture()["events"][2])
    validator.validate(null_inconclusive)

    negative = deepcopy(null_inconclusive)
    negative["event_id"] = "trajectory-event-negative"
    negative["node"]["status"] = "does_not_support"
    negative["edges"][0]["relation"] = "does_not_support"
    negative["evidence_interpretation"]["status"] = (
        "does_not_support_current_hypothesis"
    )
    negative["evidence_interpretation"]["finding_kind"] = "negative"
    validator.validate(negative)

    design_invalid = deepcopy(null_inconclusive)
    design_invalid["event_id"] = "trajectory-event-design-invalid"
    design_invalid["node"]["status"] = "design_invalid"
    design_invalid["edges"][0]["relation"] = "requires"
    design_invalid["evidence_interpretation"]["status"] = "design_invalid"
    design_invalid["evidence_interpretation"]["finding_kind"] = "not_applicable"
    validator.validate(design_invalid)


def test_contract_fixes_paths_projection_and_no_inference_boundary() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    layout = contract["study_relative_layout"]
    assert layout == {
        "accepted_event_path_template": (
            "artifacts/research_trajectory/events/{event_id}.json"
        ),
        "snapshot_path": "artifacts/research_trajectory/snapshot.json",
        "human_readable_projection_path": (
            "artifacts/research_trajectory/TRAJECTORY.md"
        ),
        "candidate_location": "stage_owned_artifact_or_closeout_packet_ref_only",
        "candidate_must_not_be_written_under_accepted_event_path": True,
    }
    assert contract["snapshot_projection"][
        "same_event_set_and_projector_version_must_produce_identical_bytes"
    ] is True
    assert contract["snapshot_projection"]["wall_clock_build_time_forbidden"] is True
    assert contract["medical_presentation_policy"][
        "framework_must_not_generate_or_infer_medical_wording"
    ] is True
    assert contract["authority_boundary"][
        "private_mas_runtime_controller_or_cli_allowed"
    ] is False

    descriptor = _load("contracts/domain_descriptor.json")
    assert descriptor["standard_agent_interface"]["domain_detail_views"] == [
        {
            "view_id": "scientific-reasoning",
            "view_kind": "scientific_reasoning_map",
            "schema_version": "scientific-reasoning-map.v1",
            "source_kind": "work_item_relative_json",
            "relative_path": "artifacts/research_trajectory/snapshot.json",
        }
    ]
    projection = _load("contracts/domain_projection_profile.json")
    assert set(projection["domain_detail_view_projection"]["full_payload_fields"]) == (
        MAP_PAYLOAD_FIELDS
    )


def test_six_stages_declare_trajectory_delta_and_medical_narrative_policy() -> None:
    manifest = _load("agent/stages/manifest.json")
    assert [stage["stage_id"] for stage in manifest["stages"]] == STAGE_IDS
    for stage in manifest["stages"]:
        trajectory = stage["stage_contract_extension"]["research_trajectory"]
        assert trajectory["stage_id"] == stage["stage_id"]
        assert trajectory["required_output_ref_field"] == (
            "research_trajectory_delta_ref"
        )
        assert trajectory[
            "candidate_requires_owner_or_decisive_reviewer_receipt_before_canonical_event"
        ] is True
        assert trajectory["emit_when"]
        assert "agent/knowledge/research_trajectory_medical_narrative.md" in stage[
            "knowledge_refs"
        ]

        prompt = (ROOT / stage["prompt_ref"]).read_text(encoding="utf-8")
        assert "## Research Trajectory" in prompt
        assert "research_trajectory_delta_ref" in prompt

    semantic_pack = (
        ROOT / "agent/stages/stage_native_semantic_pack.yaml"
    ).read_text(encoding="utf-8")
    assert semantic_pack.count(
        "research_trajectory: *research_trajectory_output_policy"
    ) == 10
    assert "- research_trajectory_delta_ref" in semantic_pack


def test_stage_output_ref_is_required_nullable_and_digest_bound() -> None:
    schema = _load("contracts/schemas/v2/mas-stage-action.output.schema.json")
    assert "research_trajectory_delta_ref" in schema["required"]
    delta = schema["$defs"]["research_trajectory_delta_ref"]
    assert delta["properties"]["kind"]["const"] == "mas_research_trajectory_delta"
    assert set(delta["required"]) == {"kind", "ref", "sha256"}


def test_human_projection_uses_medical_language_without_runtime_leakage() -> None:
    contract = _load("contracts/research_trajectory_contract.json")
    fixture = _fixture()
    markdown = (FIXTURE_DIR / "TRAJECTORY.md").read_text(encoding="utf-8")
    for heading in contract["medical_presentation_policy"][
        "required_user_headings_zh_CN"
    ]:
        assert f"## {heading}" in markdown

    user_text = "\n".join(_collect_user_visible_strings(fixture)) + "\n" + markdown
    forbidden_tokens = {
        "node_id",
        "event_id",
        "attempt_id",
        "stage_run_id",
        "payload",
        "sha256",
        "provider",
        "runtime_queue",
        "代码路径",
        "文件路径",
        "哈希",
        "载荷",
        "脚本失败",
    }
    lowered = user_text.lower()
    assert not {token for token in forbidden_tokens if token.lower() in lowered}
    assert "证据尚不足以确定" in user_text
    assert "调整研究路线" in user_text


def test_edge_kinds_match_frozen_map_abi_without_refutation_language() -> None:
    event_schema = _load(
        "contracts/schemas/v2/mas-research-trajectory-event.schema.json"
    )
    snapshot_schema = _load(
        "contracts/schemas/v2/mas-research-trajectory-snapshot.schema.json"
    )
    expected = {
        "tests",
        "supports",
        "does_not_support",
        "inconclusive",
        "revises",
        "supersedes",
        "routes_to",
        "produces",
        "requires",
    }
    assert set(
        event_schema["$defs"]["trajectory_edge"]["properties"]["relation"][
            "enum"
        ]
    ) == expected
    assert set(
        snapshot_schema["$defs"]["map_edge"]["properties"]["kind"]["enum"]
    ) == expected
    assert "refutes" not in json.dumps(event_schema).lower()
