from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _medical_prose_story() -> str:
    return "\n\n".join(
        [
            "# Clinically interpretable diabetes phenotypes and recorded medication-coverage gaps in Hunan primary care",
            "## Abstract",
            "**Background:** Primary-care diabetes services need reproducible phenotype summaries.",
            "**Methods:** Phenotype derivation used deterministic clinical rules.",
            "**Results:** Recorded medication-coverage gaps varied across phenotype groups.",
            "**Conclusions:** The findings support regional service review.",
            "## Introduction",
            "Primary-care diabetes management varies across glycemic, adiposity, and cardiometabolic domains.",
            "## Methods",
            "### Phenotype derivation and assignment",
            "Phenotype derivation used a deterministic hierarchy that can be reproduced for a new patient.",
            "### Data quality assessment",
            "Data quality assessment defined the blood-pressure interpretation boundary.",
            "### Statistical analysis",
            "Statistical analysis used descriptive counts, percentages, denominators, and measurement availability.",
            "## Results",
            "The cohort contained six clinically interpretable phenotype groups.",
            "## Discussion",
            "The findings identify service-review priorities in regional primary care.",
            "## Limitations",
            "Medication exposure was limited to recorded primary-care medication fields.",
            "## Conclusion",
            "The deterministic phenotype hierarchy identified recorded medication-coverage gap profiles.",
        ]
    ) + "\n"


def test_quality_repair_batch_evidence_does_not_treat_canonical_story_surface_refs_as_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Clean external validation manuscript story.\n", encoding="utf-8")
    review_manuscript.write_text("Clean review manuscript story.\n", encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_record = _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"schema_version": 1},
    )
    gate_report = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": "publication-eval::002::latest"},
    )
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_from_quality_repair_batch_result(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        source_eval_id="publication-eval::002::latest",
        source_eval_artifact_path=str(gate_report),
        source_summary_id="quality-summary::002",
        source_summary_artifact_path=str(
            _write_json(study_root / "artifacts" / "quality" / "summary.json", {"summary_id": "quality-summary::002"})
        ),
        gate_clearing_result={
            "ok": True,
            "status": "executed",
            "record_path": str(gate_record),
            "selected_publication_work_unit": {
                "unit_id": "manuscript_story_repair",
                "owner": "quality_repair_batch",
                "gate_replay_target": "publication_gate",
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(gate_report),
            },
            "unit_results": [
                {
                    "unit_id": "manuscript_story_repair",
                    "status": "updated",
                    "result": {
                        "changed_artifact_refs": [
                            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
                            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                            {"path": str(review_ledger), "artifact_role": "review_ledger"},
                        ],
                        "canonical_artifact_refs": [
                            str(draft),
                            str(review_manuscript),
                            str(claim_map),
                            str(evidence_ledger),
                            str(review_ledger),
                        ],
                    },
                }
            ],
        },
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    changed_paths = {Path(ref["path"]).resolve() for ref in evidence["changed_artifact_refs"]}
    assert draft.resolve() not in changed_paths
    assert review_manuscript.resolve() not in changed_paths
    assert evidence["manuscript_surface_hygiene"]["status"] == "blocked"
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is False
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
    assert evidence["ai_reviewer_recheck_request_ref"] == str(ai_request.resolve())


def test_medical_prose_write_repair_does_not_count_ai_reviewer_bound_current_manuscript_as_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "003-dpcc"
    story = _medical_prose_story()
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    for path in (draft, review_manuscript):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(story, encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-003"})
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::003"},
    )
    publication_eval_payload = {
        "eval_id": "eval-003",
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(draft.resolve()),
                    "manuscript_digest": _sha256_text(story),
                    "route_target": "write",
                    "route_back_required": True,
                }
            }
        },
    }

    evidence = module.build_repair_execution_evidence(
        study_id="003-dpcc",
        quest_id="quest-003",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "medical_prose_write_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"source_eval_id": "eval-003", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[
            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
            {"path": str(review_ledger), "artifact_role": "review_ledger"},
        ],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        ai_reviewer_recheck_request_ref=str(ai_request),
        publication_eval_payload=publication_eval_payload,
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
    hygiene = evidence["manuscript_surface_hygiene"]
    assert hygiene["story_surface_delta_present"] is False
    assert hygiene["story_surface_delta_refs"] == []


def test_dm002_publication_hardening_work_unit_requires_story_surface_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("Current DM002 manuscript story.\n", encoding="utf-8")
    review_manuscript.write_text("Current DM002 review manuscript story.\n", encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_record = _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"schema_version": 1},
    )
    gate_report = _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": "publication-eval::002::latest"},
    )
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_from_quality_repair_batch_result(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        source_eval_id="publication-eval::002::latest",
        source_eval_artifact_path=str(gate_report),
        source_summary_id="quality-summary::002",
        source_summary_artifact_path=str(
            _write_json(study_root / "artifacts" / "quality" / "summary.json", {"summary_id": "quality-summary::002"})
        ),
        gate_clearing_result={
            "ok": True,
            "status": "executed",
            "record_path": str(gate_record),
            "selected_publication_work_unit": {
                "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
                "owner": "quality_repair_batch",
                "gate_replay_target": "publication_gate",
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(gate_report),
            },
            "unit_results": [
                {
                    "unit_id": "analysis_claim_evidence_repair",
                    "status": "updated",
                    "result": {
                        "changed_artifact_refs": [
                            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
                            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                            {"path": str(review_ledger), "artifact_role": "review_ledger"},
                        ],
                    },
                },
                {"unit_id": "repair_paper_live_paths", "status": "current", "result": {}},
                {"unit_id": "materialize_display_surface", "status": "materialized", "result": {}},
            ],
        },
    )

    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["manuscript_surface_hygiene"]["required"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is False
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"] == []
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
    assert evidence["ai_reviewer_recheck_request_ref"] == str(ai_request.resolve())


def test_dm002_publication_hardening_consumes_writer_story_delta_since_previous_blocker(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "002-dm"
    draft = study_root / "paper" / "draft.md"
    review_manuscript = study_root / "paper" / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    old_text = "# External validation draft\n\nOlder reviewer-blocked story surface.\n"
    draft.write_text(old_text, encoding="utf-8")
    review_manuscript.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str(path.resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": {
                "size": len(path.read_bytes()),
                "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
        }
        for path in (draft, review_manuscript)
    ]
    current_text = "\n\n".join(
        [
            "# External validation of a China-derived diabetes mortality score in NHANES",
            "## Abstract",
            "A fixed China-derived Cox mortality score was externally validated in a NHANES validation cohort of adults with diagnosed diabetes. Discrimination, calibration, observed 5-year mortality, predicted risk, and 95% CI uncertainty were reported.",
            "## Introduction",
            "External validation tests transportability before absolute-risk use.",
            "## Methods",
            "The validation analysis used NHANES participants and the original development cohort coefficients without refitting or recalibration. Statistical analysis reported c-index discrimination, calibration intercept and slope, Brier score, observed-to-expected ratio, and bootstrap 95% CI estimates.",
            "## Results",
            "The score retained risk ordering with a c-index of 0.734 (95% CI 0.714-0.757) but underestimated observed 5-year mortality. Calibration results showed severe absolute underprediction.",
            "## Discussion",
            "The findings support recalibration and independent evaluation before use.",
            "## Limitations",
            "The NHANES analysis used complete cases and unweighted validation estimates.",
            "## Conclusion",
            "The fixed score should not be used for absolute-risk decisions without recalibration.",
        ]
    ) + "\n"
    draft.write_text(current_text, encoding="utf-8")
    review_manuscript.write_text(current_text, encoding="utf-8")
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-002"})
    ai_request = _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {"request_id": "ai-reviewer-recheck::002"},
    )

    evidence = module.build_repair_execution_evidence(
        study_id="002-dm",
        quest_id="quest-002",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "dm002_current_publication_hardening_after_ai_reviewer_eval",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"source_eval_id": "eval-002", "finding_id": "medical-prose", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[
            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
            {"path": str(review_ledger), "artifact_role": "review_ledger"},
        ],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        ai_reviewer_recheck_request_ref=str(ai_request),
        previous_quality_repair_batch={
            "source_eval_id": "eval-002",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "surface_refs": old_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                },
            },
        },
    )

    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["progress_delta_candidate"] is True
    assert "manuscript_story_surface_delta_missing" not in evidence["blockers"]
    story_refs = evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"]
    assert {Path(ref["path"]).relative_to(study_root).as_posix() for ref in story_refs} == {
        "paper/draft.md",
        "paper/build/review_manuscript.md",
    }
    assert {ref["reason"] for ref in story_refs} == {"surface_changed_since_previous_blocked_batch"}


def test_dm002_publication_hardening_work_unit_is_registered_as_upstream_repair() -> None:
    gate_work_units = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_work_units")
    story_work_units = importlib.import_module("med_autoscience.controllers.story_surface_work_units")

    assert {
        "dm002_current_publication_hardening_after_ai_reviewer_eval",
        "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        "dm002_current_manuscript_reporting_consistency_write_repair",
        "dm002_same_line_publication_paper_repair",
    }.issubset(gate_work_units.UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS)
    assert story_work_units.is_story_surface_delta_write_work_unit("dm002_same_line_publication_paper_repair")
    assert story_work_units.is_story_surface_delta_write_work_unit(
        "dm002_current_manuscript_reporting_consistency_write_repair"
    )


def test_medical_prose_currentness_delta_requires_synchronized_journal_story_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_repair_execution_evidence")
    study_root = tmp_path / "studies" / "003-dpcc"
    paper_root = study_root / "paper"
    draft = paper_root / "draft.md"
    review_manuscript = paper_root / "build" / "review_manuscript.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript.parent.mkdir(parents=True, exist_ok=True)
    old_text = "# Draft\n\nOld DPCC story surface.\n"
    draft.write_text(old_text, encoding="utf-8")
    review_manuscript.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str(path.resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": {
                "size": len(path.read_bytes()),
                "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
        }
        for path in (draft, review_manuscript)
    ]
    draft.write_text(
        "\n\n".join(
            [
                "# Clinically interpretable diabetes phenotypes and recorded treatment-review gaps",
                "## Abstract",
                "The study describes DPCC diabetes phenotypes and recorded treatment-review gap patterns.",
                "## Introduction",
                "The clinical problem is primary-care diabetes heterogeneity.",
                "## Methods",
                "### Phenotype derivation and assignment",
                "Phenotype derivation used deterministic rules.",
                "### Data quality assessment",
                "Data quality checks defined the blood-pressure boundary.",
                "### Statistical analysis",
                "Analyses were descriptive.",
                "## Results",
                "The cohort included adults with diabetes.",
                "## Discussion",
                "The findings support service review.",
                "## Limitations",
                "Medication capture was limited to recorded fields.",
                "## Conclusion",
                "Recorded treatment-review gap patterns varied by phenotype.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    claim_map = _write_json(study_root / "paper" / "claim_evidence_map.json", {"schema_version": 1})
    evidence_ledger = _write_json(study_root / "paper" / "evidence_ledger.json", {"schema_version": 1})
    review_ledger = _write_json(study_root / "paper" / "review" / "review_ledger.json", {"schema_version": 1})
    gate_replay = _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-003"})

    evidence = module.build_repair_execution_evidence(
        study_id="003-dpcc",
        quest_id="quest-003",
        study_root=study_root,
        repair_work_unit={
            "unit_id": "medical_prose_write_repair",
            "owner": "quality_repair_batch",
            "gate_replay_target": "publication_gate",
        },
        review_finding={"source_eval_id": "eval-003", "finding_id": "medical-prose", "severity": "must_fix"},
        source_refs=[str(gate_replay)],
        changed_artifact_refs=[
            {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
            {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
            {"path": str(review_ledger), "artifact_role": "review_ledger"},
        ],
        revision_log_ref=str(review_ledger),
        evidence_ledger_ref=str(evidence_ledger),
        review_ledger_ref=str(review_ledger),
        gate_replay_refs=[str(gate_replay)],
        previous_quality_repair_batch={
            "source_eval_id": "eval-003",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "surface_refs": old_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                },
            },
        },
    )

    assert evidence["status"] == "blocked"
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is False
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"] == []
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
