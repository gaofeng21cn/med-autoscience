from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


def _fingerprint(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"size": len(data), "content_sha256": hashlib.sha256(data).hexdigest()}


def test_medical_prose_write_repair_uses_explicit_route_context_when_gate_result_lacks_selection(
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
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nPrimary-care treatment-gap draft surface.\n", encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_json(
        paper_root / "dpcc_treatment_gap_alignment.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "treatment_gap_alignment",
                    "rows": [
                        {
                            "phenotype_label": "Adiposity-linked multimorbidity",
                            "index_patients": 181306,
                            "severe_glycemia_low_intensity_gap_patients": 0,
                            "uncontrolled_glycemia_no_drug_gap_patients": 71370,
                            "hypertension_no_antihypertensive_gap_patients": 104900,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 151579,
                        },
                        {
                            "phenotype_label": "Glycemic-dominant diabetes",
                            "index_patients": 104029,
                            "severe_glycemia_low_intensity_gap_patients": 89578,
                            "uncontrolled_glycemia_no_drug_gap_patients": 52071,
                            "hypertension_no_antihypertensive_gap_patients": 74416,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 88999,
                        },
                        {
                            "phenotype_label": "Severe glycemic multimorbidity",
                            "index_patients": 73203,
                            "severe_glycemia_low_intensity_gap_patients": 55480,
                            "uncontrolled_glycemia_no_drug_gap_patients": 24532,
                            "hypertension_no_antihypertensive_gap_patients": 53950,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 55607,
                        },
                    ],
                }
            ],
        },
    )
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "T2_phenotype_gap_summary.md").write_text(
        "\n".join(
            [
                "# T2",
                "",
                "| Phenotype | Index patients | Share of index cohort | Mean age, y | Mean BMI | Mean HbA1c | Severe glycemia low-intensity gap | Uncontrolled glycemia with no diabetes drug | Hypertension with no antihypertensive | Dyslipidemia with no lipid-lowering |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Adiposity-linked multimorbidity | 181306 | 26.17% | 64.99 | 26.69 | 6.59 | NA | 39.36% | 57.86% | 83.60% |",
                "| Glycemic-dominant diabetes | 104029 | 15.02% | 64.44 | 23.05 | 8.04 | 86.11% | 50.05% | 71.52% | 85.55% |",
                "| Severe glycemic multimorbidity | 73203 | 10.57% | 61.21 | 24.91 | 10.69 | 75.79% | 33.51% | 73.68% | 75.96% |",
            ]
        ),
        encoding="utf-8",
    )
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
            "work_unit_id": "medical_prose_write_repair",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "medical-prose-routeback::write::current",
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
    if result["status"] == "handoff_ready":
        handoff = result["writer_worker_handoff"]
        assert handoff["next_executable_owner"] == "write"
        assert handoff["prompt_contract"]["next_work_unit"]["unit_id"] in {
            "medical_prose_write_repair",
            "manuscript_story_repair",
        }
    else:
        assert "writer_worker_handoff" not in result
    evidence = result["repair_execution_evidence"]
    assert evidence["repair_work_unit"]["unit_id"] in {
        "medical_prose_write_repair",
        "manuscript_story_repair",
    }
    assert "story_surface_delta_present" in evidence["manuscript_surface_hygiene"]
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in evidence["canonical_artifact_delta"]["artifact_refs"]
    }
    assert {
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/review_ledger.json",
    }.issubset(changed_paths)
    if "paper/draft.md" in changed_paths:
        assert "paper/build/review_manuscript.md" in changed_paths
        story_text = (paper_root / "draft.md").read_text(encoding="utf-8")
        assert "Phenotype derivation and assignment" in story_text
        assert "recorded treatment-review gap" in story_text


def test_quality_repair_batch_consumes_publication_gate_replay_as_controller_progress_delta(
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
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent story surface.\n", encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "review" / "review_ledger.json", {"schema_version": 1, "concerns": []})
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["verdict"]["overall_verdict"] = "promising"
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "finalize",
            "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
            "next_work_unit": {
                "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "lane": "finalize",
                "summary": "Replay the publication gate and package/currentness checks.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    freshness_path = study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_root.mkdir(parents=True)
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    current_package_zip.write_text("zip-placeholder", encoding="utf-8")
    _write_json(
        freshness_path,
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": publication_eval_payload["eval_id"],
            "current_package_root": str(current_package_root.resolve()),
            "current_package_zip": str(current_package_zip.resolve()),
            "proof_path": str(freshness_path.resolve()),
        },
    )
    gate_batch_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"

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
            "blockers": ["stale_study_delivery_mirror", "submission_hardening_incomplete"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::003",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(gate_batch_path),
            "explicit_publication_work_unit": {
                "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "lane": "finalize",
            },
            "selected_publication_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "status": "skipped",
                "lifecycle_status": "skipped",
            },
            "current_publication_work_unit": {
                "unit_id": "submission_delivery_terminal_blocker",
                "control_surface": "gate_clearing_batch",
                "controller_work_unit_executable": False,
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "reports" / "publication_gate" / "latest.json"),
            },
            "current_package_freshness_proof": {
                "schema_version": 1,
                "status": "fresh",
                "source_eval_id": publication_eval_payload["eval_id"],
                "proof_path": str(freshness_path.resolve()),
            },
            "unit_results": [],
        },
    )
    route_context = {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "control_state": "supervisor_gated",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {"study_truth": {"epoch": "truth-1"}, "runtime_health": {"epoch": "runtime-1"}},
            "dispatch_gate": {"state": "open", "blocking_reasons": []},
            "route_authorization": {
                "paper_write_allowed": True,
                "bundle_build_allowed": True,
                "runtime_recovery_allowed": True,
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
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

    assert result["status"] == "executed"
    assert result["ok"] is True
    assert result.get("typed_blocker") != "controller_route_work_unit_unsupported"
    evidence = result["repair_execution_evidence"]
    assert evidence["status"] == "controller_progress_delta_candidate"
    assert evidence["controller_progress_delta_candidate"] is True
    assert evidence["repair_work_unit"]["unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    controller_refs = {
        Path(ref).relative_to(study_root).as_posix()
        for ref in evidence["controller_progress_delta"]["artifact_refs"]
    }
    assert "artifacts/controller/current_package_freshness/latest.json" in controller_refs


def test_medical_prose_write_repair_preserves_descriptive_registry_writer_delta_with_stale_review_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "obesity-registry"
    paper_root = study_root / "paper"
    old_text = "# Draft\n\nEarlier registry draft.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]
    registry_story = "\n\n".join(
        [
            "# Multicenter obesity registry phenotype atlas",
            "## Abstract",
            "A descriptive registry phenotype atlas can define denominator, missingness, and source-specific clinical measurement before inferential studies.",
            "## Introduction",
            "The clinical problem is how a regional obesity registry captures BMI, waist circumference, metabolic fields, PHQ-9, GAD-7, and psychobehavioral measurements.",
            "## Materials and Methods",
            "### Study design and cohort",
            "This descriptive registry study used source-layer accounting, available-record denominators, and observed registry data.",
            "### Statistical analysis",
            "Statistical analysis used counts, medians, denominators, and available-record percentages.",
            "## Results",
            "The phenotype atlas described source-layer structure, BMI-waist central obesity, waist circumference, and PHQ-9/GAD-7 psychobehavioral co-occurrence.",
            "## Discussion",
            "The registry atlas separates clinical phenotype description from population inference.",
            "### Limitations",
            "Registry-field summaries are not as disease prevalence, and the study does not establish population burden.",
            "### Conclusions",
            "The descriptive atlas supports registry improvement and future obesity care research.",
        ]
    ) + "\n"
    (paper_root / "draft.md").write_text(registry_story, encoding="utf-8")

    changed_paths = module.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id="medical_prose_write_repair",
        source_eval_id="eval-obesity",
        previous_quality_repair_batch={
            "schema_version": 1,
            "source_eval_id": "eval-obesity",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "surface_refs": old_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "story_surface_delta_refs": [],
                },
            },
        },
        publication_eval_payload={"eval_id": "eval-obesity"},
        study_root=study_root,
    )

    relative_changed_paths = {
        Path(path).relative_to(study_root).as_posix()
        for path in changed_paths
    }
    assert "paper/build/review_manuscript.md" in relative_changed_paths
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == registry_story


def test_medical_prose_write_repair_recovers_divergent_registry_story_surface_without_old_anchor(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "obesity-registry"
    paper_root = study_root / "paper"
    stale_review = "# Draft\n\nThis analytic surface is an earlier internal registry draft.\n"
    registry_story = "\n\n".join(
        [
            "# Multicenter obesity registry phenotype atlas",
            "## Abstract",
            "A descriptive registry phenotype atlas can define denominator, missingness, and source-specific measurement before inferential studies.",
            "## Introduction",
            "The clinical problem is how a regional obesity registry captures BMI, waist circumference, metabolic fields, PHQ-9, GAD-7, and psychobehavioral measurements.",
            "## Materials and Methods",
            "### Study design and cohort",
            "This descriptive registry study used source-layer accounting, available-record denominators, and observed registry data.",
            "### Statistical analysis",
            "Statistical analysis used counts, medians, denominators, and available-record percentages.",
            "## Results",
            "The phenotype atlas described source-layer structure, BMI-waist central obesity, waist circumference, and PHQ-9/GAD-7 psychobehavioral co-occurrence.",
            "## Discussion",
            "The registry atlas separates clinical phenotype description from population inference.",
            "### Limitations",
            "Registry-field summaries are not as disease prevalence, and the study does not establish population burden.",
            "### Conclusions",
            "The descriptive atlas supports registry improvement and future obesity care research.",
        ]
    ) + "\n"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(registry_story, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "review_manuscript.md").write_text(stale_review, encoding="utf-8")

    changed_paths = module.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id="medical_prose_write_repair",
        source_eval_id="eval-obesity",
        previous_quality_repair_batch={
            "schema_version": 1,
            "source_eval_id": "eval-obesity",
            "status": "blocked",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["controller_route_work_unit_unsupported"],
            },
        },
        publication_eval_payload={"eval_id": "eval-obesity"},
        study_root=study_root,
    )

    relative_changed_paths = {
        Path(path).relative_to(study_root).as_posix()
        for path in changed_paths
    }
    assert "paper/build/review_manuscript.md" in relative_changed_paths
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == registry_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == registry_story


def test_medical_prose_write_repair_recovers_divergent_registry_story_surface_after_anchor_overwrite(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "obesity-registry"
    paper_root = study_root / "paper"
    registry_story = "\n\n".join(
        [
            "# Multicenter obesity registry phenotype atlas",
            "## Abstract",
            "A descriptive registry phenotype atlas can define denominator, missingness, and source-specific measurement before inferential studies.",
            "## Introduction",
            "The clinical problem is how a regional obesity registry captures BMI, waist circumference, metabolic fields, PHQ-9, GAD-7, and psychobehavioral measurements.",
            "## Materials and Methods",
            "### Study design and cohort",
            "This descriptive registry study used source-layer accounting, available-record denominators, and observed registry data.",
            "### Statistical analysis",
            "Statistical analysis used counts, medians, denominators, and available-record percentages.",
            "## Results",
            "The phenotype atlas described source-layer structure, BMI-waist central obesity, waist circumference, and PHQ-9/GAD-7 psychobehavioral co-occurrence.",
            "## Discussion",
            "The registry atlas separates clinical phenotype description from population inference.",
            "### Limitations",
            "Registry-field summaries are not as disease prevalence, and the study does not establish population burden.",
            "### Conclusions",
            "The descriptive atlas supports registry improvement and future obesity care research.",
        ]
    ) + "\n"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(registry_story, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "review_manuscript.md").write_text(
        "# Draft\n\nThis analytic surface is an earlier internal registry draft.\n",
        encoding="utf-8",
    )
    current_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]

    changed_paths = module.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id="medical_methods_and_registry_reporting_repair",
        source_eval_id="eval-obesity",
        previous_quality_repair_batch={
            "schema_version": 1,
            "source_eval_id": "eval-obesity",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "surface_refs": current_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "story_surface_delta_refs": [],
                },
            },
        },
        publication_eval_payload={"eval_id": "eval-obesity"},
        study_root=study_root,
    )

    relative_changed_paths = {
        Path(path).relative_to(study_root).as_posix()
        for path in changed_paths
    }
    assert "paper/build/review_manuscript.md" in relative_changed_paths
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == registry_story
