from __future__ import annotations

from pathlib import Path

from med_autoscience.agent_entry.renderers import render_entry_modes_payload
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


def test_stage_surface_contract_builds_cards_from_canonical_route_contracts() -> None:
    payload = render_entry_modes_payload()
    route_contracts = payload["route_contracts"]
    assert isinstance(route_contracts, dict)

    surface = build_stage_surface_contract()

    assert MAIN_STAGE_ROUTE_IDS == EXPECTED_ROUTE_IDS
    assert surface["surface_kind"] == "mas_stage_surface_contract"
    assert surface["machine_boundary"]["markdown_is_truth"] is False
    assert surface["machine_boundary"]["canonical_route_contract"] == (
        "src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml"
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

    cards = surface["stage_cards"]
    assert isinstance(cards, list)
    assert [card["route_id"] for card in cards] == list(EXPECTED_ROUTE_IDS)

    for card in cards:
        route_id = card["route_id"]
        assert card["machine_source_refs"]["route_contract"] == (
            f"src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/route_contracts/{route_id}"
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


def test_render_stage_surfaces_markdown_is_generated_from_contract() -> None:
    surface = build_stage_surface_contract()
    markdown = render_stage_surfaces_markdown(surface)

    assert markdown.startswith("# MAS Stage Surfaces\n")
    assert "Canonical route source: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`." in markdown
    assert "Markdown is a generated human-reading surface; it is not machine truth." in markdown
    assert "OPL may only project, dispatch, and read refs." in markdown
    assert "MAS keeps domain truth, quality verdict, runtime owner, and artifact authority." in markdown

    for route_id in EXPECTED_ROUTE_IDS:
        assert f"## {route_id}" in markdown
        assert (
            f"- Machine source: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/route_contracts/{route_id}`"
            in markdown
        )
        assert "### Purpose" in markdown
        assert "### Entry" in markdown
        assert "### Allowed Tools" in markdown
        assert "### Knowledge" in markdown
        assert "### Outputs" in markdown
        assert "### Quality" in markdown
        assert "### Closeout" in markdown
        assert "### OPL Boundary" in markdown


def test_render_stage_skill_surface_block_is_machine_derived() -> None:
    block = render_stage_skill_surface_block("baseline")

    assert block.startswith("## MAS stage surface\n")
    assert "- Stage: `baseline` / Baseline" in block
    assert (
        "- Route contract ref: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/route_contracts/baseline`"
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
