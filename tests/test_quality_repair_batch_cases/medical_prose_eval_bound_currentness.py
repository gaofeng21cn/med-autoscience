from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_medical_prose_write_repair_preserves_current_ai_reviewer_bound_story_surface(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    writer_story = "\n\n".join(
        [
            "# Clinically interpretable diabetes phenotypes and recorded medication-coverage gaps in Hunan primary care",
            "## Abstract",
            "**Background:** Primary-care diabetes services need reproducible phenotype summaries that connect clinical burden with documented medication coverage.",
            "**Methods:** The study used DPCC index patients. Phenotype derivation used a deterministic hierarchy, not fitted clustering.",
            "**Results:** Recorded medication-coverage gaps were reported with phenotype-specific denominators.",
            "**Conclusions:** The findings support regional service review and prospective validation.",
            "## Introduction",
            "The clinical problem is diabetes heterogeneity in primary care.",
            "## Methods",
            "### Phenotype derivation and assignment",
            "Phenotype derivation used a deterministic hierarchy that can be reproduced for a new patient.",
            "### Data quality assessment",
            "Data quality checks defined the blood-pressure interpretation boundary.",
            "### Statistical analysis",
            "Statistical analysis used descriptive counts, percentages, denominators, and uncertainty boundaries.",
            "## Results",
            "Recorded medication-coverage gaps varied across the six phenotypes.",
            "## Discussion",
            "The clinical interpretation is service review, not treatment-effect estimation.",
            "## Limitations",
            "Medication capture was limited to recorded primary-care medication fields.",
            "## Conclusion",
            "A deterministic DPCC phenotype hierarchy identified recorded medication-coverage gap profiles.",
        ]
    ) + "\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(writer_story, encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current AI reviewer medical-prose findings.",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current medical-prose findings.",
            },
        }
    )
    manuscript_digest = _sha256_text(writer_story)
    publication_eval_payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {"manuscript": str((paper_root / "draft.md").resolve())},
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_ref": str(
                    (
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "medical_prose_review_request.json"
                    ).resolve()
                ),
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": str((paper_root / "draft.md").resolve()),
                "manuscript_digest": manuscript_digest,
                "route_back_required": True,
                "route_target": "write",
            }
        },
        "route_back_decision": {
            "recommended_action": "route_back_same_line",
            "rationale": "Medical prose still needs write-owner repair.",
        },
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::stale",
            "status": "executed",
            "ok": True,
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "surface_refs": [],
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "story_surface_delta_refs": [],
                },
            },
        },
    )

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
            "gate_fingerprint": "publication-gate::medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "medical_prose_write_repair"},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story
    evidence = result["repair_execution_evidence"]
    assert evidence["status"] == "progress_delta_candidate"
    story_refs = evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"]
    assert {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in story_refs
    } == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert {ref["fingerprint"]["content_sha256"] for ref in story_refs} == {
        manuscript_digest.removeprefix("sha256:")
    }
    assert {
        ref.get("reason")
        for ref in story_refs
    } == {"ai_reviewer_eval_bound_current_manuscript_preserved"}
