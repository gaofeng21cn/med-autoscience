from __future__ import annotations

from pathlib import Path

from med_autoscience.agent_entry.renderers import render_stage_route_contract_payload
from med_autoscience.stage_surface_contract import (
    MAIN_STAGE_ROUTE_IDS,
    build_stage_surface_contract,
    render_stage_skill_surface_block,
    render_stage_surfaces_markdown,
)


EXPECTED_ROUTE_IDS = (
    "scout",
    "idea",
    "baseline",
    "experiment",
    "analysis-campaign",
    "write",
    "review",
    "finalize",
    "decision",
    "journal-resolution",
)
STAGE_ROUTE_CONTRACT_REF = "agent/stages/stage_route_contract.yaml"


def test_stage_surface_contract_builds_cards_from_canonical_route_contracts() -> None:
    payload = render_stage_route_contract_payload()
    route_contracts = payload["route_contracts"]
    assert isinstance(route_contracts, dict)

    surface = build_stage_surface_contract()

    assert MAIN_STAGE_ROUTE_IDS == EXPECTED_ROUTE_IDS
    assert surface["surface_kind"] == "mas_stage_surface_contract"
    assert surface["machine_boundary"]["markdown_is_truth"] is False
    assert surface["machine_boundary"]["canonical_route_contract"] == (
        STAGE_ROUTE_CONTRACT_REF
    )
    assert surface["authority_boundary"]["opl_allowed"] == [
        "projection",
        "dispatch",
        "read_refs",
    ]
    assert surface["authority_boundary"]["mas_authority"] == [
        "domain_truth",
        "quality_verdict",
        "artifact_authority",
        "runtime_owner",
    ]
    assert surface["human_review_policy"]["mode"] == "optional_human_review_annotation"
    assert surface["human_review_policy"]["default_blocks_auto_advance"] is False
    assert surface["human_review_policy"]["blocking_only_when"] == "route_contract.human_gate_boundary_triggered"
    assert surface["human_review_policy"]["annotation_can_authorize_quality_verdict"] is False
    assert surface["human_review_policy"]["annotation_can_authorize_submission_readiness"] is False

    cards = surface["stage_cards"]
    assert isinstance(cards, list)
    assert [card["route_id"] for card in cards] == list(EXPECTED_ROUTE_IDS)

    for card in cards:
        route_id = card["route_id"]
        assert card["machine_source_refs"]["route_contract"] == (
            f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}"
        )
        assert card["purpose"] == route_contracts[route_id]["goal"]
        assert card["entry"] == route_contracts[route_id]["enter_conditions"]
        assert card["outputs"] == route_contracts[route_id]["durable_outputs_minimum"]
        assert card["quality"]["route_success_gate"] == route_contracts[route_id]["hard_success_gate"]
        assert card["route_back"] == route_contracts[route_id]["route_back_triggers"]
        assert card["human_gate"] == route_contracts[route_id]["human_gate_boundary"]
        assert card["opl_boundary"]["may"] == ["project", "dispatch", "read source refs"]
        assert card["opl_boundary"]["must_not"] == [
            "write MAS domain truth",
            "authorize quality verdicts",
            "own canonical artifacts",
            "accept memory writeback",
        ]
        assert "publication_eval/latest.json" in card["quality"]["machine_source_refs"]
        assert "stage_knowledge_packet" in card["knowledge"]["machine_source_refs"]
        assert "stage_memory_closeout_packet" in card["closeout"]["machine_source_refs"]


def test_stage_surface_contract_exposes_deliverable_index_for_human_audit_and_opl_projection() -> None:
    surface = build_stage_surface_contract()

    assert surface["stage_deliverable_index"]["role"] == "human_audit_and_opl_locator"
    assert surface["stage_deliverable_index"]["authority_boundary"]["can_write_mas_truth"] is False
    assert surface["stage_deliverable_index"]["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert surface["stage_deliverable_index"]["human_review_policy"]["default_blocks_auto_advance"] is False
    assert surface["stage_deliverable_index"]["review_page_policy"]["paper_asset_delta_policy"][
        "allowed_delta_types"
    ] == [
        "manuscript",
        "table",
        "figure",
        "supplement",
        "reference",
        "response_letter",
        "analysis_record",
        "review_record",
        "package_or_delivery",
        "no_paper_asset_body_delta",
    ]
    assert surface["stage_deliverable_index"]["review_page_policy"]["claim_trace_policy"]["allowed_impact_states"] == [
        "strengthened",
        "weakened",
        "rewritten",
        "removed",
        "unsupported",
        "newly_blocked",
        "no_claim_change",
    ]
    assert surface["stage_deliverable_index"]["review_page_policy"]["freshness_signal_policy"]["status_kind"] == (
        "traffic_light"
    )
    assert len(surface["stage_deliverable_index"]["human_review_page_refs"]) == len(surface["stage_cards"])

    for card in surface["stage_cards"]:
        route_id = card["route_id"]
        deliverable_index = card["deliverable_index"]

        assert deliverable_index["surface_kind"] == "mas_stage_deliverable_index_entry"
        assert deliverable_index["stage"] == route_id
        assert deliverable_index["input_refs"][0]["role"] == "stage_knowledge_packet"
        assert deliverable_index["input_refs"][0]["ref"] == f"artifacts/stage_knowledge/{route_id}/latest.json"
        assert any(item["role"] == "active_study_charter" for item in deliverable_index["input_refs"])
        assert any(item["role"] == "durable_outputs_minimum" for item in deliverable_index["output_refs"])
        assert any(item["role"] == "stage_memory_closeout_packet" for item in deliverable_index["output_refs"])
        assert any(item["role"] == "evidence_ledger" for item in deliverable_index["ledger_refs"])
        assert deliverable_index["quality_gate_ref"]["owner"] == "MedAutoScience"
        assert deliverable_index["quality_gate_ref"]["publication_readiness_authority"] is False
        assert deliverable_index["package_artifact_delta_ref"]["owner"] == "MedAutoScience"
        assert deliverable_index["next_owner"]["owner"] == "MedAutoScience"
        assert deliverable_index["next_owner"]["next_routes"] == card["next_routes"]
        assert deliverable_index["human_review_page_ref"] == f"/stage_cards/{route_id}/human_review_page"
        assert deliverable_index["human_review_policy_ref"] == "/human_review_policy"
        assert deliverable_index["review_page_policy_ref"] == "/stage_deliverable_index/review_page_policy"
        assert deliverable_index["authority_boundary"]["human_review_blocks_auto_advance_by_default"] is False
        assert deliverable_index["source_map_ref"]["role"] == "source_map"
        assert deliverable_index["source_map_ref"]["body_included"] is False
        assert deliverable_index["page_block_anchor_ref"]["role"] == "page_block_anchors"
        assert deliverable_index["figure_near_claim_ref"]["role"] == "figure_near_claim_refs"
        presentation = deliverable_index["paper_presentation_note"]
        assert presentation["mode"] == "optional_deliverable_note"
        assert presentation["projection_kind"] == "evidence_spine_presentation"
        assert presentation["can_authorize_quality_verdict"] is False
        assert presentation["can_authorize_publication_readiness"] is False
        assert presentation["can_authorize_submission_readiness"] is False


def test_stage_surface_contract_exposes_one_page_paper_review_template() -> None:
    surface = build_stage_surface_contract()

    for card in surface["stage_cards"]:
        review_page = card["human_review_page"]
        section_ids = [section["section_id"] for section in review_page["sections"]]

        assert review_page["surface_kind"] == "mas_stage_human_review_page"
        assert review_page["stage"] == card["route_id"]
        assert review_page["role"] == "one_page_paper_audit_surface"
        assert review_page["deliverable_index_ref"] == f"/stage_cards/{card['route_id']}/deliverable_index"
        assert review_page["review_annotation_policy"]["mode"] == "optional_human_review_annotation"
        assert review_page["review_annotation_policy"]["default_blocks_auto_advance"] is False
        assert review_page["review_annotation_policy"]["blocking_state"] == "human_gate_required"
        assert review_page["review_annotation_policy"]["blocking_only_when"] == (
            "route_contract.human_gate_boundary_triggered"
        )
        assert review_page["review_annotation_policy"]["annotation_can_authorize_quality_verdict"] is False
        assert review_page["review_annotation_policy"]["annotation_can_authorize_submission_readiness"] is False
        assert review_page["review_annotation_policy"]["annotation_can_mark_publication_ready"] is False
        assert review_page["paper_asset_delta_policy"]["allowed_delta_types"] == [
            "manuscript",
            "table",
            "figure",
            "supplement",
            "reference",
            "response_letter",
            "analysis_record",
            "review_record",
            "package_or_delivery",
            "no_paper_asset_body_delta",
        ]
        assert review_page["paper_asset_delta_policy"]["body_included"] is False
        assert review_page["paper_asset_delta_policy"]["can_authorize_artifact_authority"] is False
        assert review_page["source_grounding_policy"]["requires_source_map"] is True
        assert review_page["source_grounding_policy"]["requires_page_block_anchors"] is True
        assert review_page["source_grounding_policy"]["requires_figure_near_claim_refs"] is True
        assert review_page["source_grounding_policy"]["can_write_mas_truth"] is False
        assert review_page["paper_presentation_policy"]["mode"] == "optional_deliverable_note"
        assert review_page["paper_presentation_policy"]["evidence_spine_required"] is True
        assert review_page["paper_presentation_policy"]["can_authorize_publication_readiness"] is False
        assert review_page["claim_trace_policy"]["cross_stage_trace"] is True
        assert review_page["claim_trace_policy"]["can_authorize_quality_verdict"] is False
        assert review_page["freshness_signal_policy"]["status_kind"] == "traffic_light"
        assert review_page["freshness_signal_policy"]["freshness_signal_blocks_auto_advance_by_default"] is False
        assert review_page["freshness_signal_policy"]["freshness_signal_can_authorize_submission_readiness"] is False
        states = {item["state"]: item for item in review_page["review_annotation_policy"]["allowed_states"]}
        assert set(states) == {
            "accept_for_next_stage",
            "needs_revision",
            "route_back",
            "stop_or_pivot",
            "human_gate_required",
        }
        assert states["human_gate_required"]["blocks_auto_advance"] is True
        assert all(
            state["blocks_auto_advance"] is False
            for state_id, state in states.items()
            if state_id != "human_gate_required"
        )
        assert section_ids == [
            "paper_question",
            "stage_inputs",
            "work_completed",
            "manuscript_or_artifact_delta",
            "claim_trace",
            "evidence_and_citation_basis",
            "quality_judgment",
            "freshness_signal",
            "advance_decision",
            "route_back_or_human_gate",
        ]
        assert {section["human_judgment"] for section in review_page["sections"]} == {"optional_annotation"}
        assert {section["blocks_auto_advance"] for section in review_page["sections"]} == {False}
        assert review_page["authority_boundary"]["can_authorize_quality_verdict"] is False
        assert review_page["authority_boundary"]["can_authorize_submission_readiness"] is False
        assert review_page["authority_boundary"]["can_mark_publication_ready"] is False
        assert review_page["authority_boundary"]["can_override_auto_advance"] is False


def test_render_stage_surfaces_markdown_is_generated_from_contract() -> None:
    surface = build_stage_surface_contract()
    markdown = render_stage_surfaces_markdown(surface)

    assert markdown.startswith("# MAS Stage Surfaces\n")
    assert f"Canonical route source: `{STAGE_ROUTE_CONTRACT_REF}`." in markdown
    assert "Markdown is a generated human-reading surface; it is not machine truth." in markdown
    assert "OPL may only project, dispatch, and read refs." in markdown
    assert "MAS keeps domain truth, quality verdict, runtime owner, and artifact authority." in markdown

    for route_id in EXPECTED_ROUTE_IDS:
        assert f"## {route_id}" in markdown
        assert (
            f"- Machine source: `{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}`"
            in markdown
        )
        assert "### Purpose" in markdown
        assert "### Entry" in markdown
        assert "### Allowed Tools" in markdown
        assert "### Knowledge" in markdown
        assert "### Outputs" in markdown
        assert "### Quality" in markdown
        assert "### Closeout" in markdown
        assert "### Deliverable Index" in markdown
        assert "### One-Page Paper Review" in markdown
        assert "### OPL Boundary" in markdown


def test_render_stage_skill_surface_block_is_machine_derived() -> None:
    block = render_stage_skill_surface_block("baseline")

    assert block.startswith("## MAS stage surface\n")
    assert "- Stage: `baseline` / Baseline" in block
    assert (
        f"- Route contract ref: `{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/baseline`"
        in block
    )
    assert "- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#baseline`" in block
    assert "data_source_contract" in block
    assert "baseline_cohort_endpoint_comparator_snapshot" in block
    assert "statistical_analysis_pack" in block
    assert "stop_loss_pack" in block
    assert "human_gate_pack" in block
    assert "- Publication readiness authority: `false`" in block
    assert "- Quality verdict authority: `false`" in block
    assert "Markdown/Skill role: generated human-readable operating surface only; it is not machine truth." in block
    assert "Do not treat OPL/provider completion as paper closure." in block


def test_render_stage_skill_surface_block_rejects_non_main_stage() -> None:
    try:
        render_stage_skill_surface_block("rebuttal")
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "unsupported main stage id: rebuttal" in message


def test_repo_stage_surfaces_doc_matches_renderer() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    expected = render_stage_surfaces_markdown(build_stage_surface_contract())

    assert (repo_root / "docs" / "runtime" / "contracts" / "stage_surfaces.md").read_text(
        encoding="utf-8"
    ) == expected
