from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.controllers import portfolio_memory


EXPLORATORY_STAGES = ("scout", "idea", "analysis-campaign", "review")
PUBLICATION_ROUTE_MEMORY_STAGES = ("scout", "idea", "decision", "analysis-campaign", "review")
REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_FIXTURE = REPO_ROOT / "docs" / "policies" / "study-workflow" / "publication_route_memory_seed_fixture.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


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
        "publication_route_memory_pack",
        "publication_route_memory_apply_receipt",
        "paper_soak_memory_apply_proof",
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
    assert contract["exploratory_stages"] == list(EXPLORATORY_STAGES)
    assert contract["publication_route_memory_stages"] == list(PUBLICATION_ROUTE_MEMORY_STAGES)


@pytest.mark.parametrize("stage", EXPLORATORY_STAGES)
def test_exploratory_route_contracts_require_stage_knowledge_and_closeout(stage: str) -> None:
    payload = importlib.import_module("med_autoscience.agent_entry").load_entry_modes_payload()
    route_contract = payload["route_contracts"][stage]

    assert "knowledge_input_obligations" in route_contract
    assert "memory_closeout_obligations" in route_contract
    assert "stage_knowledge_packet_ref" in route_contract["knowledge_input_obligations"]
    assert "stage_memory_closeout_packet" in route_contract["memory_closeout_obligations"]


def test_decision_route_contract_requires_route_memory_stage_knowledge_and_closeout() -> None:
    payload = importlib.import_module("med_autoscience.agent_entry").load_entry_modes_payload()
    route_contract = payload["route_contracts"]["decision"]

    assert route_contract["knowledge_input_obligations"][:2] == [
        "stage_knowledge_packet_ref",
        "publication_route_memory_refs",
    ]
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


def test_publication_route_memory_seed_apply_builds_workspace_pack_and_stage_entry_refs(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "S1"
    workspace_root = tmp_path / "workspace"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "reference_context" / "latest.json", {"status": "present"})

    receipt = stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )
    replay = stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )
    packet = stage_knowledge_plane.build_stage_knowledge_packet(
        study_id="S1",
        stage="idea",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert receipt["surface"] == "publication_route_memory_apply_receipt"
    assert receipt["status"] == "applied"
    assert replay["idempotent_replay"] is True
    assert receipt["accepted_memory_ids"] == [
        "publication_route_memory_seed__external_validation_rescue",
        "publication_route_memory_seed__negative_result_stoploss",
    ]
    pack_path = stage_knowledge_plane.publication_route_memory_pack_path(workspace_root=workspace_root)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    assert pack["surface"] == "publication_route_memory_pack"
    assert pack["state"] == "workspace_runtime_memory_pack"
    assert pack["card_count"] == 2
    assert [ref["memory_id"] for ref in packet["publication_route_memory_refs"]] == [
        "publication_route_memory_seed__external_validation_rescue",
    ]
    assert packet["publication_route_memory_refs"][0]["authority_boundary"] == (
        "context_only_not_publication_authority"
    )


def test_publication_route_memory_selection_uses_small_stage_relevant_set(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )

    review_refs = stage_knowledge_plane.select_publication_route_memory_refs(
        workspace_root=workspace_root,
        stage="review",
        limit=1,
    )
    decision_refs = stage_knowledge_plane.select_publication_route_memory_refs(
        workspace_root=workspace_root,
        stage="decision",
    )

    assert len(review_refs) == 1
    assert review_refs[0]["memory_id"] == "publication_route_memory_seed__external_validation_rescue"
    assert [ref["memory_id"] for ref in decision_refs] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]


def test_decision_stage_knowledge_packet_reads_publication_route_memory_refs(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )

    packet = stage_knowledge_plane.build_stage_knowledge_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert packet["surface"] == "stage_knowledge_packet"
    assert packet["stage"] == "decision"
    assert packet["status"] == "ready"
    assert packet["missing_reasons"] == []
    assert [ref["memory_id"] for ref in packet["publication_route_memory_refs"]] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert packet["stage_obligations"]["knowledge_input_obligations"][0] == "stage_knowledge_packet_ref"
    assert packet["authority_boundary"]["can_replace_controller_decision"] is False


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
        "portfolio/research_memory/publication_route_memory/writeback_proposals/stage_memory_updates.jsonl"
    )
    assert accepted_by_id["citation-gap-1"]["target_path"].endswith(
        "artifacts/literature_provider/repair_requests/stage_memory_closeout.jsonl"
    )
    assert accepted_by_id["failed-path-1"]["target_path"].endswith(
        "artifacts/controller/failed_path_history.jsonl"
    )
    proposal_path = (
        workspace_root
        / "portfolio"
        / "research_memory"
        / "publication_route_memory"
        / "writeback_proposals"
        / "stage_memory_updates.jsonl"
    )
    pack_receipt_root = workspace_root / "portfolio" / "research_memory" / "publication_route_memory" / "writeback_receipts"
    failed_path = study_root / "artifacts" / "controller" / "failed_path_history.jsonl"
    assert len(proposal_path.read_text(encoding="utf-8").splitlines()) == 1
    assert len(list(pack_receipt_root.glob("*.json"))) == 1
    assert len(failed_path.read_text(encoding="utf-8").splitlines()) == 1


def test_stage_memory_closeout_router_rejects_free_text_only_closeout(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"

    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "free-text-closeout",
            "source_refs": ["review:turn-1"],
            "summary": "Need a guideline citation and stricter claim boundary.",
        },
    )
    receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=packet,
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert packet["proposed_writes"] == []
    assert receipt["status"] == "blocked"
    assert {item["blocker_id"] for item in receipt["typed_blockers"]} == {
        "typed_closeout_missing",
        "free_text_field:summary",
    }
    assert not (
        workspace_root
        / "portfolio"
        / "research_memory"
        / "publication_route_memory"
        / "writeback_proposals"
        / "stage_memory_updates.jsonl"
    ).exists()


def test_stage_memory_closeout_router_assigns_owner_targets_for_repair_and_decision_surfaces(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"

    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "owner-targets",
            "source_refs": ["review:matrix-1"],
            "citation_gaps": [{"write_id": "citation-gap-1", "gap": "Missing pivotal trial citation."}],
            "failed_paths": [{"write_id": "failed-path-1", "reason": "Reviewer route was exhausted."}],
            "reference_role_updates": [{"write_id": "reference-role-1", "pmid": "123", "role": "anchor"}],
            "claim_boundary_decisions": [
                {"write_id": "claim-boundary-1", "decision": "Keep subgroup claim exploratory only."}
            ],
            "controller_decision_requests": [{"write_id": "controller-decision-1", "request": "Confirm route."}],
        },
    )
    receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=packet,
        study_root=study_root,
        workspace_root=workspace_root,
    )

    accepted_by_id = {item["write_id"]: item for item in receipt["accepted_writes"]}
    assert accepted_by_id["citation-gap-1"]["owner_target"] == "literature_provider"
    assert accepted_by_id["citation-gap-1"]["target_path"].endswith(
        "artifacts/literature_provider/repair_requests/stage_memory_closeout.jsonl"
    )
    assert accepted_by_id["failed-path-1"]["owner_target"] == "mas_controller"
    assert accepted_by_id["reference-role-1"]["owner_target"] == "reference_context_owner"
    assert accepted_by_id["reference-role-1"]["target_path"].endswith(
        "artifacts/reference_context/update_requests.jsonl"
    )
    assert accepted_by_id["claim-boundary-1"]["owner_target"] == "mas_controller"
    assert accepted_by_id["claim-boundary-1"]["target_path"].endswith(
        "artifacts/controller_decisions/claim_boundary_requests.jsonl"
    )
    assert accepted_by_id["controller-decision-1"]["owner_target"] == "mas_controller"
    assert accepted_by_id["controller-decision-1"]["target_path"].endswith(
        "artifacts/controller_decisions/stage_closeout_requests.jsonl"
    )

    claim_boundary_rows = (
        study_root / "artifacts" / "controller_decisions" / "claim_boundary_requests.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["write_id"] for line in claim_boundary_rows] == ["claim-boundary-1"]


def test_paper_soak_memory_apply_proof_projects_controlled_readonly_receipt_refs(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)
    stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )
    stage_knowledge_plane.materialize_stage_knowledge_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
    )
    closeout = stage_knowledge_plane.materialize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "paper-soak-closeout",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "route-memory-lesson",
                    "scope": "workspace_reusable",
                    "lesson": "Stop-loss was appropriate after route evidence stayed weak.",
                }
            ],
            "failed_paths": [{"write_id": "route-failed-path", "reason": "Endpoint evidence remained thin."}],
        },
    )
    router_receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=closeout,
        study_root=study_root,
        workspace_root=workspace_root,
    )
    sidecar_receipt = workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / "r1.json"
    _write_json(
        sidecar_receipt,
        {
            "surface_kind": "mas_family_sidecar_dispatch_receipt",
            "accepted": True,
            "task_id": "task-1",
            "task_kind": "study_progress/read",
            "dispatch": {"study_id": "S1"},
        },
    )

    proof = stage_knowledge_plane.materialize_paper_soak_memory_apply_proof(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert proof["surface"] == "paper_soak_memory_apply_proof"
    assert proof["status"] == "ready"
    assert proof["missing_reasons"] == []
    assert proof["stage_entry"]["route_memory_ref_count"] == 1
    assert proof["stage_entry"]["publication_route_memory_refs"][0]["memory_id"] == (
        "publication_route_memory_seed__negative_result_stoploss"
    )
    assert proof["typed_closeout_writeback_proposals"][0]["proposed_write_refs"][0] == {
        "write_id": "route-memory-lesson",
        "source_category": "reusable_lessons",
        "destination": "workspace_research_memory_proposal",
        "owner_target": "workspace_memory_owner",
    }
    assert proof["mas_router_receipt_refs"][0]["status"] == "applied"
    assert proof["mas_router_receipt_refs"][0]["accepted_write_refs"][0]["write_id"] == "route-memory-lesson"
    assert proof["mas_router_receipt_refs"][0]["rejected_write_refs"] == []
    assert proof["workspace_writeback_receipt_refs"][0]["accepted_count"] == 2
    assert {ref["ref_kind"] for ref in proof["opl_aion_readonly_receipt_refs"]} == {
        "memory_write_router_receipt",
        "publication_route_memory_writeback_receipt",
        "mas_family_sidecar_dispatch_receipt",
    }
    assert all(ref["body_included"] is False for ref in proof["opl_aion_readonly_receipt_refs"])
    assert proof["read_only_display_policy"]["repo_tracks_real_paper_artifacts"] is False
    assert proof["read_only_display_policy"]["repo_tracks_memory_body"] is False
    assert proof["read_only_display_policy"]["can_write_artifact_authority"] is False
    assert proof["authority_boundary"]["can_authorize_publication_quality"] is False
    rendered = json.dumps(proof, ensure_ascii=False)
    assert "Stop-loss was appropriate" not in rendered
    assert router_receipt["receipt_ref"] in rendered
