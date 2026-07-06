from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.dm002_writer_delta_preservation import (
    DM002_AFTER_STORY_REPAIR_WORK_UNIT,
    _dm002_writer_story,
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_dm002_template_inputs,
    _write_json,
    _write_minimal_paper_surfaces,
    _write_quality_summary,
)


def test_quality_repair_batch_accepts_dm002_after_story_repair_medical_prose_route(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="mortality_attribution",
    )
    quest_id = "quest-002"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    writer_story = _dm002_writer_story()
    (paper_root / "draft.md").write_text(writer_story, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "review_manuscript.md").write_text(writer_story, encoding="utf-8")
    _write_minimal_paper_surfaces(paper_root)
    _write_dm002_template_inputs(study_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::dm002-after-story-repair",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "explicit_publication_work_unit": {"unit_id": DM002_AFTER_STORY_REPAIR_WORK_UNIT, "lane": "write"},
            "selected_publication_work_unit": {"unit_id": DM002_AFTER_STORY_REPAIR_WORK_UNIT},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )
    route_context = {
        **_paper_write_supervisor_route_context(),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": DM002_AFTER_STORY_REPAIR_WORK_UNIT,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::after_story_repair_current_inputs",
        },
    }

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=route_context,
    )

    assert result["ok"] is True
    assert result["status"] in {"executed", "handoff_ready"}
    assert result.get("typed_blocker") != "controller_route_work_unit_unsupported"
    evidence = result["repair_execution_evidence"]
    assert evidence["repair_work_unit"]["unit_id"] == DM002_AFTER_STORY_REPAIR_WORK_UNIT
    assert evidence["ai_reviewer_recheck_done"] is True
