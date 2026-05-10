from __future__ import annotations

import importlib

import pytest

from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.controllers import portfolio_memory


EXPLORATORY_STAGES = ("scout", "idea", "analysis-campaign", "review")


def test_stage_knowledge_plane_contract_exposes_required_packet_surfaces() -> None:
    module = importlib.import_module("med_autoscience.controllers.stage_knowledge_plane")

    contract = module.stage_knowledge_plane_contract()

    assert contract["schema_version"] == 1
    assert contract["surface"] == "stage_knowledge_plane_contract"
    assert set(contract["packet_contracts"]) == {
        "stage_knowledge_packet",
        "stage_memory_closeout_packet",
        "memory_write_router_receipt",
        "stage_recall_index",
    }
    for packet in contract["packet_contracts"].values():
        assert {
            "schema_version",
            "study_id",
            "stage",
            "input_refs",
            "source_fingerprint",
            "authority_boundary",
            "idempotency_key",
        }.issubset(packet["required_fields"])
        assert packet["authority_boundary"]["can_authorize_publication_quality"] is False
        assert packet["authority_boundary"]["can_replace_controller_decision"] is False
        assert packet["authority_boundary"]["can_use_chat_as_authority"] is False


@pytest.mark.parametrize("stage", EXPLORATORY_STAGES)
def test_exploratory_route_contracts_require_stage_knowledge_and_closeout(stage: str) -> None:
    payload = importlib.import_module("med_autoscience.agent_entry").load_entry_modes_payload()
    route_contract = payload["route_contracts"][stage]

    assert "knowledge_input_obligations" in route_contract
    assert "memory_closeout_obligations" in route_contract
    assert "stage_knowledge_packet_ref" in route_contract["knowledge_input_obligations"]
    assert "stage_memory_closeout_packet" in route_contract["memory_closeout_obligations"]


def test_non_exploratory_write_route_does_not_force_open_exploration_memory_loop() -> None:
    payload = importlib.import_module("med_autoscience.agent_entry").load_entry_modes_payload()
    route_contract = payload["route_contracts"]["write"]

    assert "knowledge_input_obligations" not in route_contract
    assert "memory_closeout_obligations" not in route_contract


def test_stage_knowledge_packet_reports_stage_specific_missing_reasons(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)

    scout_packet = stage_knowledge_plane.build_stage_knowledge_packet(
        study_id="S1",
        stage="scout",
        study_root=study_root,
        workspace_root=workspace_root,
    )
    review_packet = stage_knowledge_plane.build_stage_knowledge_packet(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert scout_packet["status"] == "ready"
    assert scout_packet["missing_reasons"] == []
    assert review_packet["status"] == "missing"
    assert set(review_packet["missing_reasons"]) == {
        "missing_ref:evidence_ledger",
        "missing_ref:review_ledger",
        "missing_ref:claim_evidence_map",
        "missing_ref:study_reference_context",
    }


def test_stage_memory_closeout_router_writes_typed_destinations_and_rejects_cross_study_claim(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"
    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="analysis-campaign",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "closeout-1",
            "source_refs": ["analysis:slice-1"],
            "reusable_lessons": [
                {
                    "write_id": "claim-specific",
                    "scope": "study_specific_claim",
                    "lesson": "Only valid for this line.",
                },
                {
                    "write_id": "workspace-lesson",
                    "scope": "workspace_reusable",
                    "lesson": "Baseline subgroup contrast was repeatedly underpowered.",
                },
            ],
            "citation_gaps": [{"write_id": "citation-gap-1", "gap": "Need recent guideline citation."}],
            "failed_paths": [{"write_id": "failed-path-1", "reason": "Endpoint too sparse."}],
        },
    )

    receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=packet,
        study_root=study_root,
        workspace_root=workspace_root,
    )
    replay = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=packet,
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert receipt["status"] == "applied"
    assert replay["idempotent_replay"] is True
    assert [item["write_id"] for item in receipt["rejected_writes"]] == ["claim-specific"]
    accepted_by_id = {item["write_id"]: item for item in receipt["accepted_writes"]}
    assert accepted_by_id["workspace-lesson"]["target_path"].endswith(
        "portfolio/research_memory/proposals/stage_memory_updates.jsonl"
    )
    assert accepted_by_id["citation-gap-1"]["target_path"].endswith(
        "artifacts/literature_provider/repair_requests/stage_memory_closeout.jsonl"
    )
    assert accepted_by_id["failed-path-1"]["target_path"].endswith(
        "artifacts/controller/failed_path_history.jsonl"
    )
