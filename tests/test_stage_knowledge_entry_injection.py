from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import portfolio_memory
from med_autoscience.controllers import stage_knowledge_entry
from med_autoscience.controllers.owner_route_reconcile_parts import request_packets


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_stage_knowledge_entry_returns_stage_specific_packet_refs_and_missing_reasons(tmp_path: Path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "S1"
    workspace_root = tmp_path / "workspace"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "reference_context" / "latest.json", {"status": "present"})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"status": "present"})
    _write_json(study_root / "paper" / "evidence_ledger.json", {"status": "present"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"status": "present"})

    entries = {
        stage: stage_knowledge_entry.materialize_stage_knowledge_entry(
            study_id="S1",
            stage=stage,
            study_root=study_root,
            workspace_root=workspace_root,
        )
        for stage in ("scout", "idea", "analysis-campaign", "review")
    }

    assert {
        entry["stage_knowledge_packet_ref"]
        for entry in entries.values()
    } == {
        "artifacts/stage_knowledge/scout/latest.json",
        "artifacts/stage_knowledge/idea/latest.json",
        "artifacts/stage_knowledge/analysis-campaign/latest.json",
        "artifacts/stage_knowledge/review/latest.json",
    }
    assert entries["scout"]["status"] == "ready"
    assert entries["idea"]["status"] == "ready"
    assert entries["analysis-campaign"]["status"] == "ready"
    assert entries["review"]["status"] == "missing"
    assert entries["review"]["missing_reasons"] == ["missing_ref:claim_evidence_map"]
    assert (study_root / "artifacts" / "stage_knowledge" / "review" / "latest.json").is_file()


def test_stage_knowledge_entry_fails_closed_without_required_registry_or_context(tmp_path: Path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "S1"
    workspace_root = tmp_path / "workspace"

    scout = stage_knowledge_entry.materialize_stage_knowledge_entry(
        study_id="S1",
        stage="scout",
        study_root=study_root,
        workspace_root=workspace_root,
    )
    idea = stage_knowledge_entry.materialize_stage_knowledge_entry(
        study_id="S1",
        stage="idea",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    assert scout["status"] == "missing"
    assert set(scout["missing_reasons"]) == {
        "missing_ref:portfolio_memory",
        "missing_ref:workspace_literature",
    }
    assert idea["status"] == "missing"
    assert set(idea["missing_reasons"]) == {
        "missing_ref:portfolio_memory",
        "missing_ref:workspace_literature",
        "missing_ref:study_reference_context",
    }


def test_ai_reviewer_request_packet_injects_review_stage_knowledge_ref(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "reference_context" / "latest.json", {"status": "present"})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"status": "present"})
    _write_json(study_root / "paper" / "evidence_ledger.json", {"status": "present"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"status": "present"})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"status": "present"})

    request_packets.materialize_request_packets(
        study_root=study_root,
        workspace_root=workspace_root,
        study_id="S1",
        quest_id="quest-S1",
        publication_eval_payload={"assessment_provenance": {"owner": "mechanical_projection"}},
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "reason": "ai_reviewer_assessment_required",
                "owner": "ai_reviewer",
            }
        ],
    )

    packet_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["stage_knowledge_packet_ref"] == "artifacts/stage_knowledge/review/latest.json"
    assert packet["stage_knowledge_status"] == "ready"
    assert packet["stage_knowledge_missing_reasons"] == []
    assert packet["stage_knowledge_entry"]["surface"] == "stage_knowledge_entry_read_model"
    stage_ref = packet["input_contract"]["required_refs"]["stage_knowledge_packet"]
    assert stage_ref["relative_path"] == "artifacts/stage_knowledge/review/latest.json"
    assert stage_ref["present"] is True
    assert stage_ref["valid"] is True
    assert (study_root / "artifacts" / "stage_knowledge" / "review" / "latest.json").is_file()


def test_stage_knowledge_entry_injection_marks_missing_packet_as_invalid(tmp_path: Path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "S1"
    workspace_root = tmp_path / "workspace"
    entry = stage_knowledge_entry.materialize_stage_knowledge_entry(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
    )

    injected = stage_knowledge_entry.inject_stage_knowledge_entry(
        {"input_contract": {"required_refs": {}, "required_surfaces": []}},
        stage_entry=entry,
    )

    assert injected["stage_knowledge_status"] == "missing"
    assert "stage_knowledge_packet" in injected["input_contract"]["missing_or_invalid_refs"]
    assert injected["input_contract"]["all_required_refs_present"] is False
    stage_ref = injected["input_contract"]["required_refs"]["stage_knowledge_packet"]
    assert stage_ref["present"] is False
    assert stage_ref["valid"] is False
    assert set(stage_ref["missing_reasons"]) == {
        "missing_ref:evidence_ledger",
        "missing_ref:review_ledger",
        "missing_ref:claim_evidence_map",
        "missing_ref:study_reference_context",
    }
