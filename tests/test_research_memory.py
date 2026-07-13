from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import research_memory
from med_autoscience.controllers.research_memory.publication_route_memory_cards import (
    publication_route_cards_from_markdown,
    publication_seed_blockers,
)


def test_research_memory_contract_keeps_domain_memory_and_opl_refs_separate() -> None:
    contract = research_memory.research_memory_contract()

    assert contract["schema_version"] == 2
    assert set(contract["packet_contracts"]) == {
        "opl_stage_folder_state_index_refs",
        "publication_route_memory_pack",
        "publication_route_memory_apply_receipt",
        "publication_route_memory_closeout",
        "publication_route_memory_acceptance_receipt",
    }
    boundary = contract["authority_boundary"]
    assert boundary["opl_stage_state_owner"] == "one-person-lab"
    assert boundary["body_included_in_opl_refs"] is False
    assert boundary["local_generic_persistence"] == "absent"


def test_computational_biomechanics_publication_route_seed_is_complete() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    policy_root = repo_root / "docs" / "policies" / "study-workflow"
    fixture = json.loads(
        (policy_root / "publication_route_memory_seed_fixture.json").read_text(encoding="utf-8")
    )
    cards = publication_route_cards_from_markdown(
        (policy_root / "publication_route_memory_library.md").read_text(encoding="utf-8")
    )
    card_by_id = {card["memory_id"]: card for card in cards}
    memory_id = "publication_route_memory_seed__computational_biomechanics"
    fixture_card = next(
        item for item in fixture["seed_memory_refs"] if item["memory_id"] == memory_id
    )

    assert fixture_card["route_family"] == "computational_biomechanics"
    assert publication_seed_blockers(fixture=fixture, seed_cards=[card_by_id[memory_id]]) == []


def test_publication_route_memory_closeout_accepts_only_domain_memory_destination(tmp_path: Path) -> None:
    closeout = research_memory.normalize_publication_route_memory_closeout(
        study_id="S1",
        stage="review",
        closeout_payload={
            "source_refs": ["owner-ref:review"],
            "reusable_lessons": [
                {
                    "write_id": "accepted",
                    "destination": "publication_route_memory",
                    "title": "Reviewer risk",
                    "prose_summary": "Keep the claim boundary narrow.",
                },
                {
                    "write_id": "delegated",
                    "destination": "evidence_ledger",
                },
            ],
        },
    )
    receipt = research_memory.apply_publication_route_memory_closeout(
        closeout=closeout,
        workspace_root=tmp_path,
        apply=False,
    )

    assert receipt["status"] == "dry_run"
    assert [row["write_id"] for row in receipt["accepted_writes"]] == ["accepted"]
    assert receipt["rejected_writes"][0]["reason"] == "non_publication_memory_destination_requires_domain_owner"
    assert not list(tmp_path.rglob("*.json"))


def test_publication_route_memory_apply_writes_only_natural_memory_package(tmp_path: Path) -> None:
    closeout = research_memory.normalize_publication_route_memory_closeout(
        study_id="S1",
        stage="decision",
        closeout_payload={
            "idempotency_key": "decision-memory",
            "reusable_lessons": [
                {
                    "write_id": "route-card",
                    "destination": "publication_route_memory",
                    "title": "Transportability boundary",
                    "prose_summary": "Require explicit target-population fit.",
                }
            ],
        },
    )
    receipt = research_memory.apply_publication_route_memory_closeout(
        closeout=closeout,
        workspace_root=tmp_path,
    )

    receipt_path = Path(receipt["receipt_ref"])
    assert receipt_path.is_file()
    assert "memory/portfolio/research_memory/publication_route_memory" in str(receipt_path)
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["surface"] == (
        "publication_route_memory_acceptance_receipt"
    )
    assert not (tmp_path / "artifacts").exists()
