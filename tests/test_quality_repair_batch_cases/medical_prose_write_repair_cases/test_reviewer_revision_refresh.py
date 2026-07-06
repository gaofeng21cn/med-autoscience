from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def test_dm003_reviewer_revision_forces_story_refresh_from_latest_intake(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    stale_story = "\n\n".join(
        [
            "# Phenotype-specific cardiometabolic care-review gaps",
            "## Results",
            "### Phenotype-specific glycemic and cardiometabolic care-review gaps",
            "### Medication-capture sensitivity",
            "## Discussion",
            "The highest-yield next analyses are a patient-phenotype plus site model.",
            "These additions should precede any stronger service-performance or guideline-based claims.",
        ]
    )
    refreshed_story = "\n\n".join(
        [
            "# Phenotype-specific cardiometabolic care-review gaps",
            "## Abstract",
            "Care-review gaps were structured rather than uniform, with renal-risk organ-protection signals read as secondary and exploratory.",
            "## Introduction",
            "We tested whether a reproducible phenotype hierarchy could separate documentation-sensitive glycemic gaps from persistent cardiometabolic prevention gaps.",
            "## Results",
            "### Phenotypes separated glycemic-intensity gaps from cardiometabolic-prevention gaps",
            "### Medication-field restriction attenuated glycemic no-drug gaps but not cardiometabolic prevention gaps",
            "## Discussion",
            "Future prospective and implementation studies could extend this descriptive atlas by quantifying patient- and site-level determinants.",
        ]
    )
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stale_story, encoding="utf-8")
    task_path = study_root / "artifacts" / "controller" / "task_intake" / "latest.json"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        json.dumps(
            {
                "task_intake_kind": "reviewer_revision",
                "task_intent": (
                    "structured rather than uniform gaps; documentation-sensitive glycemic gaps; "
                    "persistent lipid-lowering care-review gap; renal-risk signal secondary/exploratory; "
                    "rate-count contrast; soften future-work wording"
                ),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "_medical_prose_manuscript_from_canonical_surfaces",
        lambda *, paper_root: refreshed_story,
    )
    monkeypatch.setattr(module, "_materialize_dpcc_display_metadata_repairs", lambda *, paper_root: [])

    changed_paths = module.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id="medical_prose_write_repair",
        source_eval_id="eval-dm003",
        previous_quality_repair_batch={
            "schema_version": 1,
            "source_eval_id": "eval-dm003",
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {"story_surface_delta_present": True},
            },
        },
        publication_eval_payload={"eval_id": "eval-dm003"},
        study_root=study_root,
    )

    relative_changed_paths = {Path(path).relative_to(study_root).as_posix() for path in changed_paths}
    assert relative_changed_paths == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert (paper_root / "draft.md").read_text(encoding="utf-8").startswith(
        "# Phenotype-specific cardiometabolic care-review gaps"
    )
    assert "The highest-yield next analyses are" not in (paper_root / "draft.md").read_text(encoding="utf-8")
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == (
        paper_root / "draft.md"
    ).read_text(encoding="utf-8")


def test_dm003_latest_reviewer_tightening_refreshes_without_legacy_stale_markers(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.medical_prose_story_surface"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    previous_story = "\n\n".join(
        [
            "# Phenotype-specific cardiometabolic care-review gaps",
            "## Abstract",
            "lipid-lowering prevention gaps remained large after medication-field restriction and varied across sites.",
            "## Discussion",
            "The site fixed-effect dyslipidemia sensitivity model supports the same service-review interpretation.",
        ]
    )
    refreshed_story = previous_story + "\n\nEffect sizes were modest.\n\nA 2025 index-year sensitivity analysis still showed a large exploratory renal-risk signal.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(previous_story, encoding="utf-8")
    task_path = study_root / "artifacts" / "controller" / "task_intake" / "latest.json"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        json.dumps(
            {
                "task_intake_kind": "reviewer_revision",
                "task_intent": (
                    "shorten Abstract; reduce renal-risk prominence; focus strongest finding on "
                    "lipid-lowering prevention gap persistence after medication-field restriction and site "
                    "adjustment; add modest effect-size caveat for site fixed-effect model; update Figure 4 "
                    "title/legend to rate-count priority map"
                ),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "_medical_prose_manuscript_from_canonical_surfaces",
        lambda *, paper_root: refreshed_story,
    )
    monkeypatch.setattr(module, "_materialize_dpcc_display_metadata_repairs", lambda *, paper_root: [])

    changed_paths = module.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id="medical_prose_write_repair",
        source_eval_id="eval-dm003-latest",
        previous_quality_repair_batch={
            "schema_version": 1,
            "source_eval_id": "eval-dm003-latest",
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {"story_surface_delta_present": True},
            },
        },
        publication_eval_payload={"eval_id": "eval-dm003-latest"},
        study_root=study_root,
    )

    relative_changed_paths = {Path(path).relative_to(study_root).as_posix() for path in changed_paths}
    assert relative_changed_paths == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert "Effect sizes were modest" in (paper_root / "draft.md").read_text(encoding="utf-8")
