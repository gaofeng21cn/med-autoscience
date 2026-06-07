from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.controllers import portfolio_memory
from med_autoscience.stage_route_contract import route_obligations_descriptor
from med_autoscience.stage_knowledge_contract import STAGE_OBLIGATIONS


EXPLORATORY_STAGES = ("scout", "idea", "analysis-campaign", "review")
PUBLICATION_ROUTE_MEMORY_STAGES = ("scout", "idea", "decision", "analysis-campaign", "review")
STAGE_OBLIGATION_GAP_REQUIREMENTS = {
    "baseline": {
        "knowledge_input_obligations": {
            "data_source_contract",
            "cohort_definition_and_inclusion_exclusion",
            "endpoint_definition_and_measurement_window",
            "comparator_definition_and_reference_baseline",
            "startup_run_context",
            "prior_result_lineage",
            "failed_comparator_history",
        },
        "memory_closeout_obligations": {
            "baseline_cohort_endpoint_comparator_snapshot",
            "baseline_effect_size_or_feasibility_readout",
            "failed_comparator_lesson",
            "continue_reroute_or_stop_recommendation",
        },
    },
    "experiment": {
        "knowledge_input_obligations": {
            "approved_experiment_protocol",
            "data_contract_and_cohort_lock",
            "endpoint_and_comparator_lock",
            "statistical_analysis_plan",
            "startup_run_context",
            "prior_result_lineage",
            "failed_comparator_history",
        },
        "memory_closeout_obligations": {
            "primary_result_with_run_context",
            "result_lineage_update",
            "endpoint_or_comparator_deviation",
            "negative_or_failed_comparator_lesson",
        },
    },
    "write": {
        "knowledge_input_obligations": {
            "claim_evidence_map",
            "reporting_guideline_pack",
            "journal_neighbor_refs",
            "display_to_claim_map",
        },
        "memory_closeout_obligations": {
            "writing_experience_lesson",
            "claim_wording_boundary_decision",
            "reporting_guideline_gap",
            "display_to_claim_repair_request",
            "journal_neighbor_positioning_lesson",
        },
    },
    "finalize": {
        "knowledge_input_obligations": {
            "publication_eval_latest",
            "controller_decision_latest",
            "package_freshness_proof",
            "declarations_and_ethics_checklist",
            "human_gate_status",
        },
        "memory_closeout_obligations": {
            "package_readiness_decision",
            "package_freshness_or_staleness_lesson",
            "declaration_or_ethics_blocker",
            "human_gate_request_or_clearance",
        },
    },
    "journal-resolution": {
        "knowledge_input_obligations": {
            "official_author_guideline",
            "outlet_profile",
            "exporter_profile_constraints",
            "blocked_profile_evidence",
        },
        "memory_closeout_obligations": {
            "selected_outlet_or_profile_rationale",
            "exporter_constraint_lesson",
            "blocked_profile_decision",
            "reporting_guideline_delta",
        },
    },
}
REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_FIXTURE = REPO_ROOT / "docs" / "policies" / "study-workflow" / "publication_route_memory_seed_fixture.json"
SEED_LIBRARY = REPO_ROOT / "docs" / "policies" / "study-workflow" / "publication_route_memory_library.md"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_publication_route_memory_seed_fixture_is_markdown_first_index() -> None:
    fixture = json.loads(SEED_FIXTURE.read_text(encoding="utf-8"))
    fixture_text = json.dumps(fixture, ensure_ascii=False)

    assert fixture["canonical_body_ref"] == "docs/policies/study-workflow/publication_route_memory_library.md"
    assert "seed_cards" not in fixture
    assert "prose_summary" not in fixture_text
    assert "best_fit" not in fixture_text
    assert "minimum_evidence_package" not in fixture_text
    assert SEED_LIBRARY.exists()


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
    payload = importlib.import_module("med_autoscience.stage_route_contract").load_stage_route_contract_payload()
    route_contract = payload["route_contracts"][stage]

    assert "knowledge_input_obligations" in route_contract
    assert "memory_closeout_obligations" in route_contract
    assert "stage_knowledge_packet_ref" in route_contract["knowledge_input_obligations"]
    assert "stage_memory_closeout_packet" in route_contract["memory_closeout_obligations"]


def test_decision_route_contract_requires_route_memory_stage_knowledge_and_closeout() -> None:
    payload = importlib.import_module("med_autoscience.stage_route_contract").load_stage_route_contract_payload()
    route_contract = payload["route_contracts"]["decision"]

    assert route_contract["knowledge_input_obligations"][:2] == [
        "stage_knowledge_packet_ref",
        "publication_route_memory_refs",
    ]
    assert "stage_memory_closeout_packet" in route_contract["memory_closeout_obligations"]


def test_stage_knowledge_contract_covers_stage_surface_program_obligation_gaps() -> None:
    contract = stage_knowledge_plane.stage_knowledge_plane_contract()
    obligations = contract["stage_obligations"]

    assert set(STAGE_OBLIGATION_GAP_REQUIREMENTS).issubset(obligations)
    for stage, expected_by_field in STAGE_OBLIGATION_GAP_REQUIREMENTS.items():
        stage_obligations = obligations[stage]
        assert stage_obligations["knowledge_input_obligations"][0] == "stage_knowledge_packet_ref"
        assert stage_obligations["memory_closeout_obligations"][0] == "stage_memory_closeout_packet"
        for field, expected_items in expected_by_field.items():
            assert expected_items.issubset(set(stage_obligations[field]))
            assert set(stage_obligations[field]) == set(STAGE_OBLIGATIONS[stage][field])


def test_stage_knowledge_obligations_match_route_obligations_descriptor() -> None:
    descriptor = route_obligations_descriptor()
    contract = stage_knowledge_plane.stage_knowledge_plane_contract()

    assert descriptor["status"] == "present"
    assert set(contract["stage_obligations"]) == set(descriptor["routes"])
    for stage, obligations in contract["stage_obligations"].items():
        route_descriptor = descriptor["routes"][stage]
        assert obligations["knowledge_input_obligations"] == route_descriptor[
            "knowledge_input_obligations"
        ]["items"]
        assert obligations["memory_closeout_obligations"] == route_descriptor[
            "memory_closeout_obligations"
        ]["items"]


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
    assert len(receipt["accepted_memory_ids"]) >= 9
    assert "publication_route_memory_seed__clinical_classifier" in receipt["accepted_memory_ids"]
    assert "publication_route_memory_seed__external_validation_rescue" in receipt["accepted_memory_ids"]
    assert "publication_route_memory_seed__negative_result_stoploss" in receipt["accepted_memory_ids"]
    pack_path = stage_knowledge_plane.publication_route_memory_pack_path(workspace_root=workspace_root)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    assert pack["surface"] == "publication_route_memory_pack"
    assert pack["state"] == "workspace_runtime_memory_pack"
    assert pack["card_count"] == len(receipt["accepted_memory_ids"])
    clinical_classifier_card = next(
        card for card in pack["cards"] if card["memory_id"] == "publication_route_memory_seed__clinical_classifier"
    )
    assert "best_fit" in clinical_classifier_card
    assert "minimum_evidence_package" in clinical_classifier_card
    assert "table_figure_pattern" in clinical_classifier_card
    assert "claim_boundary" in clinical_classifier_card
    assert [ref["memory_id"] for ref in packet["publication_route_memory_refs"]] == [
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
        "publication_route_memory_seed__external_validation_model_update",
    ]
    assert packet["publication_route_memory_refs"][0]["authority_boundary"] == (
        "context_only_not_publication_authority"
    )
    assert "route_memory_summary" in packet["publication_route_memory_refs"][0]
    assert "best_fit" not in packet["publication_route_memory_refs"][0]


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
    assert review_refs[0]["memory_id"] == "publication_route_memory_seed__clinical_classifier"
    assert [ref["memory_id"] for ref in decision_refs] == [
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
        "publication_route_memory_seed__negative_result_stoploss",
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
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
        "publication_route_memory_seed__negative_result_stoploss",
    ]
    assert packet["stage_obligations"]["knowledge_input_obligations"][0] == "stage_knowledge_packet_ref"
    assert packet["authority_boundary"]["can_replace_controller_decision"] is False


def test_publication_route_memory_seed_rejects_thin_cards(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    thin_fixture = tmp_path / "thin_publication_route_seed.json"
    thin_library = tmp_path / "thin_publication_route_library.md"
    _write_json(
        thin_fixture,
        {
            "surface_kind": "publication_route_memory_seed_fixture",
            "schema_version": 1,
            "memory_family": "publication_route_memory",
            "canonical_body_ref": str(thin_library),
        },
    )
    thin_library.write_text(
        "\n".join(
            [
                "# Thin Publication Route Memory Library",
                "",
                "## publication_route_memory_seed__thin_route",
                "",
                "Status: draft_seed",
                "Route family: thin",
                "Stage applicability: idea",
                "Title: Too thin",
                "",
                "### Summary",
                "",
                "A name and two sentences are not enough.",
                "",
                "### Failure Modes",
                "",
                "- thin_card",
                "",
            ]
        ),
        encoding="utf-8",
    )

    receipt = stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=thin_fixture,
    )

    assert receipt["status"] == "blocked"
    blocker_ids = {item["blocker_id"] for item in receipt["typed_blockers"]}
    assert "seed_card:1:best_fit_missing" in blocker_ids
    assert "seed_card:1:minimum_evidence_package_missing" in blocker_ids
    assert not stage_knowledge_plane.publication_route_memory_pack_path(workspace_root=workspace_root).exists()


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


def test_accepted_workspace_reusable_lessons_are_promoted_to_route_memory_pack(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"
    stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )
    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "decision-route-memory-writeback",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "decision-stoploss-lesson",
                    "scope": "workspace_reusable",
                    "route_family": "negative_result_stoploss",
                    "stage_applicability": ["decision"],
                    "title": "Decision stop-loss route lesson",
                    "lesson": "If endpoint evidence remains thin after bounded checks, preserve the stop-loss decision rather than expanding claims.",
                    "best_fit": ["bounded repair has already been attempted"],
                    "minimum_evidence_package": ["failed-path evidence", "controller decision request"],
                    "table_figure_pattern": ["failed-path matrix"],
                    "claim_boundary": "Do not expand positive claims after weak endpoint evidence.",
                    "failure_modes": ["claim_expansion_after_weak_endpoint_evidence"],
                    "source_refs": ["stage:decision:turn-1"],
                }
            ],
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

    pack_path = stage_knowledge_plane.publication_route_memory_pack_path(workspace_root=workspace_root)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    memory_ids = [card["memory_id"] for card in pack["cards"]]
    assert memory_ids.count("publication_route_memory_writeback__decision-stoploss-lesson") == 1
    assert "publication_route_memory_seed__negative_result_stoploss" in memory_ids
    writeback_card = next(
        card
        for card in pack["cards"]
        if card["memory_id"] == "publication_route_memory_writeback__decision-stoploss-lesson"
    )
    assert writeback_card["prose_summary"].startswith("If endpoint evidence remains thin")
    assert writeback_card["best_fit"] == ["bounded repair has already been attempted"]
    assert writeback_card["minimum_evidence_package"] == ["failed-path evidence", "controller decision request"]
    assert writeback_card["table_figure_pattern"] == ["failed-path matrix"]
    assert writeback_card["claim_boundary"] == "Do not expand positive claims after weak endpoint evidence."
    assert writeback_card["source_receipt_ref"] == receipt["receipt_ref"]
    assert writeback_card["authority_boundary"] == "context_only_not_publication_authority"
    assert replay["idempotent_replay"] is True
    assert len([card for card in pack["cards"] if card["memory_id"].startswith("publication_route_memory_writeback__")]) == 1

    selected = stage_knowledge_plane.select_publication_route_memory_refs(
        workspace_root=workspace_root,
        stage="decision",
        route_family_tags=["negative_result_stoploss"],
        limit=5,
    )
    assert "publication_route_memory_writeback__decision-stoploss-lesson" in [
        ref["memory_id"] for ref in selected
    ]


def test_publication_route_memory_inventory_projects_body_free_receipts_across_paper_lines(tmp_path) -> None:
    inventory_module = importlib.import_module(
        "med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_inventory"
    )
    workspace_root = tmp_path / "workspace"
    stage_knowledge_plane.apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=SEED_FIXTURE,
    )

    first_study_root = workspace_root / "studies" / "S1"
    first_packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=first_study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "decision-route-memory-s1",
            "source_refs": ["stage:decision:s1"],
            "reusable_lessons": [
                {
                    "write_id": "s1-route-back-lesson",
                    "scope": "workspace_reusable",
                    "route_family": "route_back_repair",
                    "stage_applicability": ["decision", "review"],
                    "title": "Route-back repair lesson",
                    "lesson": "Route back before rebuilding claims when reviewer evidence is underpowered.",
                    "source_refs": ["stage:decision:s1"],
                },
                {
                    "write_id": "s1-local-claim",
                    "scope": "study_specific_claim",
                    "lesson": "This claim only applies to S1.",
                },
            ],
        },
    )
    first_receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=first_packet,
        study_root=first_study_root,
        workspace_root=workspace_root,
    )
    second_study_root = workspace_root / "studies" / "S2"
    second_packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S2",
        stage="review",
        study_root=second_study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "review-route-memory-s2",
            "source_refs": ["stage:review:s2"],
            "reusable_lessons": [
                {
                    "write_id": "s2-review-lesson",
                    "scope": "workspace_reusable",
                    "route_family": "review_response_repair",
                    "stage_applicability": ["review"],
                    "title": "Review repair lesson",
                    "lesson": "Keep response evidence scoped to the accepted analysis line.",
                    "source_refs": ["stage:review:s2"],
                }
            ],
        },
    )
    second_receipt = stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=second_packet,
        study_root=second_study_root,
        workspace_root=workspace_root,
    )

    inventory = inventory_module.build_publication_route_memory_inventory(workspace_root=workspace_root)

    receipt_inventory = inventory["opl_aion_receipt_inventory"]
    assert receipt_inventory["body_included"] is False
    assert receipt_inventory["consumer"] == "OPL/Aion"
    assert receipt_inventory["receipt_count"] == 3
    by_ref = {receipt["ref"]: receipt for receipt in receipt_inventory["receipts"]}
    seed_receipt = next(receipt for receipt in by_ref.values() if receipt["receipt_kind"] == "migration_receipt")
    accepted_seed_refs = {
        ref["memory_id"]: ref
        for ref in seed_receipt["accepted_refs"]
    }
    assert len(accepted_seed_refs) >= 9
    assert accepted_seed_refs["publication_route_memory_seed__external_validation_rescue"] == {
        "memory_id": "publication_route_memory_seed__external_validation_rescue",
        "reason": "",
        "status": "accepted",
    }
    assert accepted_seed_refs["publication_route_memory_seed__negative_result_stoploss"] == {
        "memory_id": "publication_route_memory_seed__negative_result_stoploss",
        "reason": "",
        "status": "accepted",
    }
    first_projection = by_ref[first_receipt["receipt_refs"][1]]
    assert first_projection["receipt_kind"] == "writeback_receipt"
    assert first_projection["study_id"] == "S1"
    assert first_projection["stage"] == "decision"
    assert first_projection["receipt_status"] == "applied"
    assert first_projection["freshness"]["exists"] is True
    assert first_projection["accepted_refs"] == [
        {
            "write_id": "s1-route-back-lesson",
            "memory_id": "publication_route_memory_writeback__s1-route-back-lesson",
            "destination": "workspace_research_memory_proposal",
            "owner_target": "workspace_memory_owner",
            "reason": "",
            "status": "accepted",
        }
    ]
    assert first_projection["rejected_refs"] == [
        {
            "write_id": "s1-local-claim",
            "destination": "workspace_research_memory_proposal",
            "owner_target": "workspace_memory_owner",
            "reason": "study_specific_claim_not_workspace_memory",
            "status": "rejected",
        }
    ]
    second_projection = by_ref[second_receipt["receipt_refs"][1]]
    assert second_projection["study_id"] == "S2"
    assert second_projection["accepted_refs"][0]["memory_id"] == "publication_route_memory_writeback__s2-review-lesson"
    rendered = json.dumps(inventory, ensure_ascii=False)
    assert "Route back before rebuilding claims" not in rendered
    assert "Keep response evidence scoped" not in rendered


def test_route_memory_writeback_fails_closed_on_corrupt_existing_pack(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"
    pack_path = stage_knowledge_plane.publication_route_memory_pack_path(workspace_root=workspace_root)
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_text("{", encoding="utf-8")
    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "decision-route-memory-corrupt-pack",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "decision-corrupt-pack-lesson",
                    "scope": "workspace_reusable",
                    "lesson": "A reusable route lesson should not overwrite a corrupt memory pack.",
                }
            ],
        },
    )

    with pytest.raises(json.JSONDecodeError):
        stage_knowledge_plane.route_stage_memory_closeout(
            closeout_packet=packet,
            study_root=study_root,
            workspace_root=workspace_root,
        )

    assert pack_path.read_text(encoding="utf-8") == "{"
    assert not stage_knowledge_plane.memory_write_router_receipt_path(
        study_root=study_root,
        idempotency_key="decision-route-memory-corrupt-pack",
    ).exists()


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
    domain_handler_receipt = workspace_root / "runtime" / "artifacts" / "opl_family_domain_handler" / "dispatch_receipts" / "r1.json"
    _write_json(
        domain_handler_receipt,
        {
            "surface_kind": "mas_family_domain_handler_dispatch_receipt",
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
    assert proof["stage_entry"]["route_memory_ref_count"] == 3
    assert [ref["memory_id"] for ref in proof["stage_entry"]["publication_route_memory_refs"]] == [
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
        "publication_route_memory_seed__negative_result_stoploss",
    ]
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
        "mas_family_domain_handler_dispatch_receipt",
    }
    assert all(ref["body_included"] is False for ref in proof["opl_aion_readonly_receipt_refs"])
    assert proof["read_only_display_policy"]["repo_tracks_real_paper_artifacts"] is False
    assert proof["read_only_display_policy"]["repo_tracks_memory_body"] is False
    assert proof["read_only_display_policy"]["can_write_artifact_authority"] is False
    assert proof["authority_boundary"]["can_authorize_publication_quality"] is False
    rendered = json.dumps(proof, ensure_ascii=False)
    assert "Stop-loss was appropriate" not in rendered
    assert router_receipt["receipt_ref"] in rendered
