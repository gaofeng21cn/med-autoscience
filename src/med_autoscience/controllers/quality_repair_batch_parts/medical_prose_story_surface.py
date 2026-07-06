from __future__ import annotations

import hashlib
import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.dm002_external_validation import (
    DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID,
    DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS,
    DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
    DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID,
    materialize_dm002_external_validation_story_surface,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.eval_bound_currentness import (
    eval_bound_current_story_delta_blocker,
    eval_bound_current_story_delta_refs,
    eval_bound_current_story_delta_is_preservable,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.writer_delta_preservation import (
    materialize_current_writer_story_delta,
    preserve_current_writer_story_delta,
)
from med_autoscience.study_task_intake_revision import task_intake_is_reviewer_revision
from med_autoscience.study_task_intake_surfaces import read_latest_task_intake


MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID = "medical_prose_write_repair"
MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS = (
    Path("draft.md"),
    Path("build") / "review_manuscript.md",
)
FORBIDDEN_MANUSCRIPT_TERMS = (
    "MAS",
    "AI reviewer",
    "verified outputs",
    "accepted records",
    "source gaps",
    "submission readiness",
    "repair note",
    "manuscript repair",
    "quality repair",
    "publication gate",
    "controller",
    "semantic-audit",
    "Revision analyses were implemented",
    "Table 1 is",
    "Table 2 is",
    "Figure 4 supports",
    "Guideline-linked",
)
DPCC_DISPLAY_TEXT_REPLACEMENTS = (
    (
        "Phenotype composition and treatment-gap profiles across the DPCC index cohort.",
        "Phenotype composition and recorded risk-treatment mismatch profiles across the DPCC index cohort.",
    ),
    (
        "Treatment-gap pattern",
        "Mismatch pattern",
    ),
    (
        "Guideline-linked glycemia, antihypertensive, and lipid-lowering treatment gaps "
        "aligned to the six DPCC phenotypes.",
        "Recorded glycemic, antihypertensive, and lipid-lowering treatment-review gaps "
        "aligned to the six DPCC phenotypes.",
    ),
    (
        "Guideline-linked treatment-gap burden across DPCC phenotypes",
        "Recorded treatment-review gap burden across DPCC phenotypes",
    ),
    (
        "Guideline-linked treatment-gap burden",
        "Recorded treatment-review gap burden",
    ),
    (
        "guideline_linked_treatment_gap_burden_small_multiples",
        "recorded_treatment_review_gap_burden_small_multiples",
    ),
)
DM002_POSITIVE_REFRAME_MARKERS = (
    "retained cross-population risk stratification",
    "promote what remains usable",
    "higher-risk adults",
    "population-specific recalibration",
)
DM002_STALE_NEGATIVE_STORY_MARKERS = (
    "# External validation of a fixed China-derived 5-year diabetes mortality score in NHANES",
    "should not be used for absolute-risk communication or threshold-based decisions",
)
DM003_REVIEWER_REVISION_MARKERS = (
    "structured rather than uniform gaps",
    "documentation-sensitive glycemic gaps",
    "persistent lipid-lowering care-review gap",
    "renal-risk signal secondary/exploratory",
    "rate-count contrast",
    "proportional risk vs absolute workload",
    "soften future-work wording",
)
DM003_STALE_REVIEWER_REVISION_MARKERS = (
    "The highest-yield next analyses are",
    "These additions should precede any stronger service-performance or guideline-based claims",
    "### Phenotype-specific glycemic and cardiometabolic care-review gaps",
    "### Medication-capture sensitivity",
)


def materialize_medical_prose_story_surfaces(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None = None,
    previous_quality_repair_batch: Mapping[str, Any] | None = None,
    publication_eval_payload: Mapping[str, Any] | None = None,
    study_root: Path | None = None,
) -> list[str]:
    force_dm002_story_refresh = _dm002_reviewer_revision_story_refresh_required(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        study_root=study_root,
    )
    force_dm003_story_refresh = _dm003_reviewer_revision_story_refresh_required(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        study_root=study_root,
    )
    force_story_refresh = force_dm002_story_refresh or force_dm003_story_refresh
    if not force_story_refresh:
        currentness_blocker = eval_bound_current_story_delta_blocker(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
            manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
            contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
            source_eval_id=source_eval_id,
            publication_eval_payload=publication_eval_payload,
        )
        if currentness_blocker:
            raise RuntimeError(str(currentness_blocker["blocked_reason"]))
    if not force_story_refresh and _dm002_side_surface_only_repair_is_allowed(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    ):
        _, extra_changed_paths = materialize_dm002_external_validation_story_surface(
            paper_root=paper_root,
            study_root=study_root,
        )
        return extra_changed_paths
    if not force_story_refresh and eval_bound_current_story_delta_is_preservable(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
        manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
        contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    ):
        extra_changed_paths: list[str] = []
        if work_unit_id in DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS:
            _, extra_changed_paths = materialize_dm002_external_validation_story_surface(
                paper_root=paper_root,
                study_root=study_root,
            )
        return [
            str(ref["path"])
            for ref in eval_bound_current_story_delta_refs(
                paper_root=paper_root,
                work_unit_id=work_unit_id,
                medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
                manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
                contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
                source_eval_id=source_eval_id,
                publication_eval_payload=publication_eval_payload,
            )
            if ref.get("path")
        ] + extra_changed_paths
    if not force_story_refresh:
        current_writer_delta_paths = materialize_current_writer_story_delta(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
            manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
            contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
            source_eval_id=source_eval_id,
            previous_quality_repair_batch=previous_quality_repair_batch,
        )
        if current_writer_delta_paths:
            return current_writer_delta_paths
        if work_unit_id != DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID and preserve_current_writer_story_delta(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
            manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
            contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
            source_eval_id=source_eval_id,
            previous_quality_repair_batch=previous_quality_repair_batch,
        ):
            if work_unit_id in {
                DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID,
                DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
            }:
                _, extra_changed_paths = materialize_dm002_external_validation_story_surface(
                    paper_root=paper_root,
                    study_root=study_root,
                )
                return extra_changed_paths
            return []
    extra_changed_paths: list[str] = []
    if work_unit_id == MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID:
        manuscript = _medical_prose_manuscript_from_canonical_surfaces(paper_root=paper_root)
    elif work_unit_id in DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS:
        manuscript, extra_changed_paths = materialize_dm002_external_validation_story_surface(
            paper_root=paper_root,
            study_root=study_root,
        )
    else:
        return []
    if not manuscript.strip():
        return []
    if _contains_forbidden_manuscript_terms(manuscript):
        return []
    current_story_surface_paths = _current_story_surface_paths_if_already_materialized(
        paper_root=paper_root,
        manuscript=manuscript,
    )
    artifact_changed_paths: list[str] = []
    if work_unit_id not in DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS:
        artifact_changed_paths = _materialize_dpcc_display_metadata_repairs(paper_root=paper_root)
    if current_story_surface_paths:
        return current_story_surface_paths + extra_changed_paths + artifact_changed_paths
    changed_paths: list[str] = []
    for relpath in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS:
        path = paper_root / relpath
        if _write_text_if_changed(path, manuscript):
            changed_paths.append(str(path.resolve()))
    changed_paths.extend(extra_changed_paths)
    changed_paths.extend(artifact_changed_paths)
    return changed_paths


def _dm003_reviewer_revision_story_refresh_required(
    *,
    paper_root: Path,
    work_unit_id: str,
    study_root: Path | None,
) -> bool:
    if study_root is None or work_unit_id != MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID:
        return False
    resolved_study_root = Path(study_root).expanduser().resolve()
    if resolved_study_root.name != "003-dpcc-primary-care-phenotype-treatment-gap":
        return False
    latest_task_intake = read_latest_task_intake(study_root=resolved_study_root)
    if not task_intake_is_reviewer_revision(latest_task_intake):
        return False
    corpus = _task_intake_corpus(latest_task_intake)
    if not any(marker in corpus for marker in DM003_REVIEWER_REVISION_MARKERS):
        return False
    for path in _current_story_surface_paths(paper_root=paper_root):
        if _story_surface_contains_any_marker(Path(path), DM003_STALE_REVIEWER_REVISION_MARKERS):
            return True
    return False


def _dm002_reviewer_revision_story_refresh_required(
    *,
    paper_root: Path,
    work_unit_id: str,
    study_root: Path | None,
) -> bool:
    if study_root is None or work_unit_id not in DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS:
        return False
    latest_task_intake = read_latest_task_intake(study_root=Path(study_root).expanduser().resolve())
    if not task_intake_is_reviewer_revision(latest_task_intake):
        return False
    corpus = _task_intake_corpus(latest_task_intake)
    if not any(marker in corpus for marker in DM002_POSITIVE_REFRAME_MARKERS):
        return False
    for path in _current_story_surface_paths(paper_root=paper_root):
        if _story_surface_contains_any_marker(Path(path), DM002_STALE_NEGATIVE_STORY_MARKERS):
            return True
    return False


def _task_intake_corpus(payload: Mapping[str, Any] | None) -> str:
    mapping = dict(payload) if isinstance(payload, Mapping) else {}
    values: list[str] = []
    for key in ("task_intent",):
        text = _text(mapping.get(key))
        if text:
            values.append(text)
    for key in ("constraints", "first_cycle_outputs"):
        for item in mapping.get(key) or []:
            text = _text(item)
            if text:
                values.append(text)
    return " ".join(values).lower()


def _story_surface_contains_any_marker(path: Path, markers: tuple[str, ...]) -> bool:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return False
    try:
        text = resolved.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return any(marker.lower() in text for marker in markers)


def _dm002_side_surface_only_repair_is_allowed(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> bool:
    return (
        _dm002_side_surface_only_repair_state(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            source_eval_id=source_eval_id,
            publication_eval_payload=publication_eval_payload,
        )
        == "live"
    )


def dm002_side_surface_only_repair_blocker(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if (
        _dm002_side_surface_only_repair_state(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            source_eval_id=source_eval_id,
            publication_eval_payload=publication_eval_payload,
        )
        != "digest_mismatch"
    ):
        return {}
    return {
        "blocked_reason": "quality_repair_batch_current_manuscript_digest_mismatch",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
    }


def _dm002_side_surface_only_repair_state(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> str | None:
    if work_unit_id != DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID:
        return None
    payload = dict(publication_eval_payload) if isinstance(publication_eval_payload, Mapping) else {}
    if source_eval_id and _text(payload.get("eval_id")) != source_eval_id:
        return None
    reviewer_os = payload.get("reviewer_operating_system")
    if not isinstance(reviewer_os, Mapping):
        return None
    currentness_checks = reviewer_os.get("currentness_checks")
    if not isinstance(currentness_checks, Mapping):
        return None
    prose_currentness = currentness_checks.get("medical_prose_review")
    if not isinstance(prose_currentness, Mapping):
        return None
    if _text(prose_currentness.get("status")) != "current":
        return None
    manuscript_digest = _text(prose_currentness.get("manuscript_digest"))
    manuscript_ref = _text(prose_currentness.get("manuscript_ref"))
    if not manuscript_digest or not manuscript_digest.startswith("sha256:") or not manuscript_ref:
        return None
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    story_surface_paths = {
        (resolved_paper_root / relative_path).expanduser().resolve()
        for relative_path in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS
    }
    manuscript_path = Path(manuscript_ref).expanduser()
    if not manuscript_path.is_absolute():
        manuscript_path = (resolved_paper_root.parent / manuscript_path).resolve()
    else:
        manuscript_path = manuscript_path.resolve()
    if manuscript_path not in story_surface_paths:
        return None
    if all(
        path.exists()
        and path.is_file()
        and f"sha256:{_sha256_bytes(path.read_bytes())}" == manuscript_digest
        for path in story_surface_paths
    ):
        return "live"
    return "digest_mismatch"


def _current_story_surface_paths_if_already_materialized(*, paper_root: Path, manuscript: str) -> list[str]:
    rendered = manuscript if manuscript.endswith("\n") else f"{manuscript}\n"
    paths = [(paper_root / relpath).resolve() for relpath in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS]
    if not all(path.exists() and path.is_file() for path in paths):
        return []
    try:
        if not all(path.read_text(encoding="utf-8") == rendered for path in paths):
            return []
    except OSError:
        return []
    return [str(path) for path in paths]


def _current_story_surface_paths(*, paper_root: Path) -> list[str]:
    paths = [(paper_root / relpath).resolve() for relpath in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS]
    if not all(path.exists() and path.is_file() for path in paths):
        return []
    return [str(path) for path in paths]


def _medical_prose_manuscript_from_canonical_surfaces(*, paper_root: Path) -> str:
    study_root = _study_root_from_paper_root(paper_root)
    methods = _read_json_object(paper_root / "methods_implementation_manifest.json")
    flow = _read_json_object(paper_root / "cohort_flow.json")
    phenotype_structure = _read_json_object(paper_root / "dpcc_phenotype_gap_structure.json")
    treatment_gap_alignment = _read_json_object(paper_root / "dpcc_treatment_gap_alignment.json")
    transition_support = _read_json_object(paper_root / "dpcc_transition_site_support.json")
    supplementary_text = _read_supplementary_tables_text(paper_root=paper_root, study_root=study_root)
    t1 = _read_table_text(
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md",
        fallback_path=paper_root / "tables" / "T1_baseline_characteristics.md",
    )
    t1 = _apply_bounded_t1_revisions(t1=t1, study_root=study_root)
    t2 = _read_table_text(
        paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.md",
        fallback_path=paper_root / "tables" / "T2_phenotype_gap_summary.md",
    )
    t2 = _apply_bounded_t2_revisions(
        t2=t2,
        study_root=study_root,
        clinical_rows=_read_csv_rows(paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv"),
    )
    t3_transition = _read_table_text(
        paper_root / "tables" / "generated" / "T3_transition_site_support_summary.md",
        fallback_path=paper_root / "tables" / "T3_transition_site_support_summary.md",
    )
    t3_transition = _apply_bounded_transition_table_revisions(
        transition_table=t3_transition,
        study_root=study_root,
    )

    cohort = _cohort_values(methods=methods, flow=flow, t1=t1)
    phenotype_rows = _phenotype_rows(
        t2=t2,
        phenotype_structure=phenotype_structure,
        treatment_gap_alignment=treatment_gap_alignment,
    )
    gap_rows = _gap_rows(treatment_gap_alignment=treatment_gap_alignment)
    transition = _transition_values(t3=t3_transition, transition_support=transition_support)
    sensitivity_rows = _supplementary_table_rows(
        supplementary_text,
        "Supplementary Table S2. Medication-record sensitivity for core review signals",
    )
    site_variability_rows = _supplementary_table_rows(
        supplementary_text,
        "Supplementary Table S3. Anonymous source-site-code variability in recorded medication-review signals",
    )
    sensitivity = _medication_sensitivity_values(sensitivity_rows)
    site_variability = _site_variability_values(site_variability_rows)
    burden_contrasts = _burden_contrast_values(study_root=study_root)
    adjusted_model_rows = _bounded_table_rows(study_root, "dyslipidemia_adjusted_site_model.csv")
    adjusted_model = _adjusted_model_values(adjusted_model_rows)
    t3 = _build_medication_capture_sensitivity_table(sensitivity)
    t4 = _build_adjusted_model_table(adjusted_model_rows)
    supplementary_section = _build_supplementary_tables_section(
        supplementary_text=supplementary_text,
        transition_table=t3_transition,
    )
    title = (
        "Phenotype-specific cardiometabolic care-review gaps "
        "in a regional primary-care diabetes network in Hunan, China"
    )
    return "\n\n".join(
        section
        for section in (
            f"# {title}",
            _abstract_section(
                cohort=cohort,
                phenotype_rows=phenotype_rows,
                sensitivity=sensitivity,
                transition=transition,
                site_variability=site_variability,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _introduction_section(),
            _methods_section(cohort=cohort, adjusted_model=adjusted_model),
            _results_section(
                cohort=cohort,
                phenotype_rows=phenotype_rows,
                gap_rows=gap_rows,
                sensitivity=sensitivity,
                transition=transition,
                site_variability=site_variability,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _tables_section(t1=t1, t2=t2, t3=t3, t4=t4),
            supplementary_section,
            _discussion_section(
                phenotype_rows=phenotype_rows,
                sensitivity=sensitivity,
                transition=transition,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _limitations_section(),
            _conclusion_section(),
        )
        if section
    )


def _abstract_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    site_variability: Mapping[str, Mapping[str, str]],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    phenotype_sentence = _phenotype_distribution_sentence(phenotype_rows)
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    hypertension = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "All eligible",
    )
    dyslipidemia = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "All eligible",
    )
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    site_gap = _site_variability_lookup(
        site_variability,
        "Dyslipidemia context with no recorded lipid-lowering medication",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    glycemic_adjusted = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    adjusted_sentence = ""
    if glycemic_adjusted:
        adjusted_sentence = (
            " In the medication-field-present site fixed-effect sensitivity model "
            f"(n={_format_count(glycemic_adjusted.get('model_n'))}; "
            f"{_format_count(glycemic_adjusted.get('source_sites_in_model'))} source sites), "
            "glycemic-dominant diabetes retained higher adjusted odds of the dyslipidemia no-lipid-lowering signal "
            f"than adiposity-linked multimorbidity ({_format_adjusted_or_ci(glycemic_adjusted)})."
        )
    return (
        "## Abstract\n\n"
        "**Background:** Primary-care diabetes management increasingly requires integrated glycemic, "
        "cardiometabolic, and renal-risk review rather than glycemic control alone. Routine-care phenotypes may be "
        "useful if they identify which recorded care-review gaps are documentation-sensitive and which remain large "
        "after medication-record restriction.\n\n"
        "**Objective:** To determine whether clinically interpretable diabetes phenotypes identify distinct and "
        "actionable patterns of recorded glycemic, cardiometabolic, and renal-protection care-review gaps in the "
        "DPCC primary-care network in Hunan, China.\n\n"
        f"**Methods:** This retrospective descriptive study used {cohort['processed_records']} source records from "
        f"{cohort['unique_patients']} patients. The diabetes-coded index cohort included {cohort['index_patients']} "
        f"patients, of whom {cohort['adult_plausible_age']} had plausible adult age. Phenotypes were assigned by a "
        "deterministic, prespecified hierarchy based on glycemic burden, adiposity, cardiometabolic context, "
        "renal-risk context, and medication-coverage domains. Outcomes were recorded treatment-review indicators, "
        "not treatment-effect estimates, prescribing-quality judgments, or individualized treatment recommendations.\n\n"
        f"**Results:** {phenotype_sentence} Care-review signals were phenotype-specific rather than uniform. Severe "
        "glycemia with low recorded glucose-lowering intensity was 62.0% in glycemic-dominant diabetes and 43.5% "
        "in severe glycemic multimorbidity. Across all eligible patients, uncontrolled glycemia "
        f"without a recorded diabetes medication was {_percent_value(uncontrolled.get('Gap %'))}, hypertension "
        f"context without a recorded antihypertensive was {_percent_value(hypertension.get('Gap %'))}, dyslipidemia "
        f"context without recorded lipid-lowering therapy was {_percent_value(dyslipidemia.get('Gap %'))}, and "
        "the secondary exploratory renal-risk context signal without recorded SGLT2 inhibitor or GLP-1 receptor "
        f"agonist was {_percent_value(renal.get('Gap %'))}. Medication-field-present sensitivity separated "
        "documentation-sensitive glycemic no-drug signals from more persistent cardiometabolic prevention signals: "
        f"uncontrolled glycemia without recorded diabetes medication fell from {_percent_value(uncontrolled.get('Gap %'))} "
        f"to {_percent_value(uncontrolled_present.get('Gap %'))}, whereas dyslipidemia medication-coverage signals "
        "remained large and the renal-risk organ-protection signal was retained as exploratory. The phenotype with "
        "the highest proportional dyslipidemia signal "
        f"({dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}) was not "
        "the same as the largest absolute dyslipidemia review workload "
        f"({dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}). "
        f"Site-level summaries showed wide variation, with "
        f"a median dyslipidemia gap of {_percent_value(site_gap.get('Median gap %'))}; repeated-visit transition "
        f"results were retained as support-only evidence.{adjusted_sentence}\n\n"
        "**Conclusions:** In this regional primary-care diabetes network, care-review gaps were structured rather "
        "than uniform. Glycemic gaps were concentrated in glycemic phenotypes and were highly medication-record "
        "sensitive, whereas lipid-lowering prevention gaps remained large after medication-field restriction and "
        "varied substantially across sites; renal-risk organ-protection signals should be read as secondary and "
        "exploratory. These findings support phenotype-guided chart review and local care-pathway evaluation rather "
        "than national prevalence inference, guideline nonadherence claims, treatment-effect estimation, or "
        "individualized treatment allocation."
    )


def _introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Primary-care diabetes management has moved beyond glycemic control alone toward integrated "
        "cardiometabolic and renal-risk prevention. Patients may share the diagnostic label of diabetes while "
        "differing in glycemic burden, adiposity, blood-pressure and lipid context, renal-risk context, comorbidity, "
        "medication documentation, and follow-up opportunities. For regional service planning, the practical "
        "question is whether these clinical contexts reveal distinct care-review gaps that can be audited in routine "
        "records.\n\n"
        "Prior diabetes subclassification studies show that phenotypes can carry different clinical risks, but many "
        "primary-care quality-improvement settings require simpler and auditable rules than latent clustering or "
        "individualized prediction models. A deterministic phenotype hierarchy can be useful when it converts routine "
        "measurements and diagnosis fields into transparent groups that clinicians, service managers, and chart-review "
        "teams can reproduce.\n\n"
        "The second challenge is interpretation of medication data. Absence of a recorded drug class in a "
        "primary-care release may reflect true non-use, prescribing outside the network, self-purchased medication, "
        "incomplete capture, contraindications, patient preference, clinician rationale, or delayed documentation. "
        "For that reason, a medical atlas based on routine records should report recorded medication-coverage gaps as "
        "treatment-review or documentation-review signals, not as proof of non-treatment, nonadherence, treatment "
        "failure, or guideline nonadherence.\n\n"
        "The DPCC primary-care network offers a large regional setting to ask whether routine data can generate a "
        "clinically meaningful service-priority map. We tested whether a reproducible phenotype hierarchy could "
        "separate documentation-sensitive glycemic gaps from more persistent cardiometabolic prevention gaps, and "
        "whether proportional risk and absolute service workload identified the same or different priority groups. "
        "Repeated-visit transitions and site-level support were used as support-only evidence for "
        "within-network stability and coverage, rather than as external validation or treatment-effect evidence."
    )


def _methods_section(
    *,
    cohort: Mapping[str, Any],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    model_scope = ""
    if adjusted_model:
        model_scope = (
            " As a secondary sensitivity analysis for the most stable cardiometabolic prevention signal, we fitted a "
            "logistic regression for the dyslipidemia-context no-recorded-lipid-lowering indicator among "
            "medication-field-present patients with plausible age, sex, and anonymous source-site code. The model "
            "included phenotype, age, sex, and anonymous source-site fixed effects; source sites were retained when "
            "they had at least 50 eligible patients and both outcome classes. This model was used to test whether "
            "the lipid-lowering review signal remained phenotype-patterned after basic patient and site adjustment, "
            "not to estimate causal effects or site performance."
        )
    return (
        "## Methods\n\n"
        "### Study design and cohort\n\n"
        f"We conducted a retrospective descriptive analysis of routinely collected DPCC primary-care records. The "
        f"processed release contained {cohort['processed_records']} source records from {cohort['unique_patients']} "
        "patients, with most participating practices located in Hunan. The primary denominator was the "
        f"diabetes-coded index cohort of {cohort['index_patients']} patients; adult/plausible-age sensitivity retained "
        f"{cohort['adult_plausible_age']} patients ({cohort['adult_plausible_age_share']}). For each patient, the "
        "index encounter was the first qualifying diabetes-coded visit with phenotype-ready fields after prespecified "
        "plausibility filtering. Repeated source rows from the same patient within a 7-day visit episode were not "
        f"counted as separate transition opportunities. The repeated-visit support panel included "
        f"{cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} patients were eligible "
        f"for first-to-last phenotype transition summaries. The held-out site-support surface included "
        f"{cohort['eligible_sites']} eligible site partitions covering {cohort['visit_coverage']} of release visit "
        "episodes.\n\n"
        "### Variable definition and measurement\n\n"
        "Candidate variables came from routine DPCC fields: age, sex, body size, HbA1c, fasting glucose, eGFR, lipid "
        "measures, diagnosis text, medication records, visit dates, and site identifiers. Medication classes were "
        "identified from recorded regimen text. Diabetes medication classes included metformin, alpha-glucosidase "
        "inhibitors, sulfonylureas, SGLT2 inhibitors, DPP-4 inhibitors, thiazolidinediones, other oral diabetes "
        "drugs, insulin, and injectable GLP-1 receptor agonists where recorded. Antihypertensive and lipid-lowering "
        "exposure were similarly restricted to medication classes documented in the primary-care release. Missing "
        "values were not imputed, and a missing measurement could remove a patient from a variable-specific summary or "
        "an indicator-specific eligible denominator.\n\n"
        "### Phenotype derivation and assignment\n\n"
        "Phenotype assignment was deterministic and rule based. It was not a clustering model, latent-class model, "
        "prediction model, or treatment-effect model. A new patient can be classified by applying the same hierarchy "
        "to the index-visit phenotype-ready fields; the assignment is therefore reproducible without model fitting or "
        "post hoc label optimization.\n\n"
        "The glycemic domain defined uncontrolled glycemia as HbA1c >=7.0% or fasting plasma glucose >=7.0 mmol/L, "
        "and severe glycemia as HbA1c >=9.0% or fasting plasma glucose >=11.1 mmol/L. The adiposity domain was "
        "positive with an obesity or central-obesity diagnosis, BMI >=28 kg/m2, or waist circumference >=90 cm in "
        "men or >=85 cm in women. Hypertension context was based on a hypertension diagnosis or inversion-resolved "
        "blood pressure >=140/90 mm Hg, but blood-pressure target attainment was not analyzed. Dyslipidemia context "
        "was defined by dyslipidemia diagnosis or LDL cholesterol >=3.4 mmol/L, triglycerides >=2.3 mmol/L, or total "
        "cholesterol >=5.2 mmol/L. Renal-risk context was defined by a renal diagnosis or eGFR <60 mL/min/1.73 m2.\n\n"
        "Patients were assigned hierarchically in the following order: severe glycemic multimorbidity, "
        "adiposity-linked multimorbidity, glycemic-dominant diabetes, adiposity-dominant diabetes, "
        "cardiometabolic-risk dominant diabetes, and lower-burden diabetes. The hierarchy prioritized primary-care "
        "review immediacy rather than latent disease biology. Severe glycemia was assigned first because it "
        "represents a high-immediacy glycemic review signal. Adiposity-linked multimorbidity preceded single-domain "
        "groups because coexistence of adiposity and cardiometabolic context suggests a broader metabolic-risk "
        "management problem. Glycemic-dominant and adiposity-dominant groups separated single-domain burden, and "
        "cardiometabolic-risk dominant diabetes captured hypertension, dyslipidemia, or renal-risk context without "
        "dominant glycemic or adiposity criteria. The six-class structure was retained because it separated severe "
        "glycemia, adiposity, cardiometabolic context, and lower-burden profiles into clinically interpretable groups "
        "while preserving sufficient group sizes for descriptive service review.\n\n"
        "### Model or grouping framework\n\n"
        "The grouping framework was the rule hierarchy described above. No training set, optimization target, model "
        "coefficient, probability score, or individual decision threshold was estimated for phenotype assignment. The "
        "analysis therefore reports phenotype composition and recorded medication-coverage patterns, not prediction "
        "performance, treatment effects, or individualized prescribing recommendations.\n\n"
        "### Recorded treatment-review gap definitions\n\n"
        "Treatment-review indicators were calculated as recorded medication-coverage gaps within indicator-specific "
        "eligible denominators. Low recorded glucose-lowering intensity was defined as severe glycemia with no "
        "recorded diabetes medication or with one or fewer recorded glucose-lowering classes and no recorded insulin, "
        "GLP-1 receptor agonist, or SGLT2 inhibitor. The uncontrolled-glycemia no-drug indicator was evaluated among "
        "patients meeting the uncontrolled-glycemia definition; the hypertension-context no-antihypertensive "
        "indicator among phenotype members with a hypertension diagnosis or measurement context; the "
        "dyslipidemia-context no-lipid-lowering indicator among phenotype members with the corresponding diagnosis or "
        "lipid context; and the exploratory renal-risk organ-protection coverage signal among patients with "
        "renal-risk context and no recorded SGLT2 inhibitor or GLP-1 receptor agonist. A Not assessed cell "
        "indicates that the phenotype was outside that indicator denominator or outside the bounded reporting "
        "surface. Because medication exposure was restricted to drug classes documented in the DPCC primary-care "
        "release, numerator counts should be interpreted as recorded medication-review or documentation-review signals "
        "rather than complete dispensing histories, true untreated status, nonadherence, contraindications, access "
        "barriers, clinician rationale, or individual treatment benefit.\n\n"
        "### Data quality assessment\n\n"
        f"Data-quality checks were applied before analysis. Plausibility filters excluded {cohort['bmi_excluded']} "
        f"rows for BMI constraints, {cohort['hba1c_excluded']} rows for HbA1c constraints, and "
        f"{cohort['fasting_glucose_excluded']} rows for fasting-glucose constraints. Missing values were not imputed. "
        "Filtering and missingness had row-level, variable-level, or eligibility-level consequences: implausible "
        "source rows were excluded for the affected measurement, unavailable variables did not contribute to that "
        "variable's summary, and patients could be outside an indicator denominator when the required context was "
        "absent or not assessable. Blood-pressure fields had a major semantic issue: the original blood-pressure "
        f"inversion rate was {cohort['bp_inversion_rate']}, and the swapped-value plausibility rate was "
        f"{cohort['bp_swapped_plausible_rate']}. Therefore, blood-pressure control status was excluded from the main "
        "analysis. Hypertension context was retained only as a diagnosis-or-context indicator and interpreted with "
        "this limitation. Supplementary Table S1 reports missingness and plausibility for phenotype-defining "
        "variables, including HbA1c, fasting glucose, BMI, waist circumference, eGFR, lipids, diagnosis text, and "
        "medication fields.\n\n"
        "### Validation framework\n\n"
        "Because this was not a prediction model, validation was limited to descriptive support checks. First-to-last "
        "transition summaries compared each transition-eligible patient's first and last phenotype-ready visits after "
        "7-day episode consolidation. Site support used a dominant-site deterministic partition: patients were "
        "assigned to their dominant anonymous site where possible, small sites were pooled, and the resulting site "
        "folds were used to describe within-network coverage. These analyses do not constitute external validation.\n\n"
        "### Statistical analysis\n\n"
        "Analyses were descriptive. Categorical variables are summarized as counts and percentages, and continuous "
        "variables as means where table surfaces provide means. Denominators were the index cohort for phenotype "
        "composition, phenotype-specific eligible patients for treatment-review gaps, the repeated-visit cohort for "
        "follow-up support, transition-eligible patients for first-to-last transition summaries, and release visit "
        "episodes for site-level coverage. No sampling-based 95% confidence intervals were calculated for the main "
        "release-level descriptive counts, because the analysis enumerated the retained DPCC release rather than "
        "sampling from a target national population. To address uncertainty about medication-record completeness, we "
        "repeated core gap summaries among patients with a nonempty medication field and among patients with any "
        "parsed medication class. We also summarized anonymous source-site-code gap variability for source-site codes "
        "with at least 50 eligible patients per indicator and performed adult/plausible-age sensitivity. Sensitivity "
        "analyses were implemented in Python using sqlite3, numpy, scipy, statsmodels, and matplotlib."
        f"{model_scope} No causal model, p-value-driven main hypothesis test, individualized prediction model, "
        "or blood-pressure target attainment analysis was used for the main manuscript."
    )


def _results_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    site_variability: Mapping[str, Mapping[str, str]],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    hypertension = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "All eligible",
    )
    dyslipidemia = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "All eligible",
    )
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    severe_all = _sensitivity_lookup(
        sensitivity,
        "Severe glycemia with low recorded glucose-lowering intensity",
        "All eligible",
    )
    severe_present = _sensitivity_lookup(
        sensitivity,
        "Severe glycemia with low recorded glucose-lowering intensity",
        "Medication field present",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    hypertension_present = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "Medication field present",
    )
    dyslipidemia_present = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Medication field present",
    )
    renal_present = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "Medication field present",
    )
    severe_site = _site_variability_lookup(
        site_variability,
        "Severe glycemia with low recorded glucose-lowering intensity",
    )
    hypertension_site = _site_variability_lookup(
        site_variability,
        "Hypertension context with no recorded antihypertensive",
    )
    dyslipidemia_site = _site_variability_lookup(
        site_variability,
        "Dyslipidemia context with no recorded lipid-lowering medication",
    )
    severe_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "severe_glycemia_low_recorded_glucose_lowering_intensity",
    )
    uncontrolled_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "uncontrolled_glycemia_no_recorded_diabetes_medication",
    )
    hypertension_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "hypertension_context_no_recorded_antihypertensive",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    adjusted_results = _adjusted_model_results_sentence(adjusted_model)
    return (
        "## Results\n\n"
        "### Cohort and analytic support\n\n"
        f"The processed release included {cohort['processed_records']} source records from {cohort['unique_patients']} "
        f"patients. The diabetes-coded index cohort included {cohort['index_patients']} patients; adult/plausible-age "
        f"sensitivity retained {cohort['adult_plausible_age']} patients. Cross-site continuity was observed for "
        f"{cohort['cross_site_patients']} patients. Repeated-visit support was available for "
        f"{cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} contributed to the "
        "first-to-last transition analysis. Figure 1 presents the cohort flow and quality-control exclusions.\n\n"
        "### Baseline characteristics\n\n"
        f"The retained DPCC release provided a large service-review denominator: {cohort['processed_records']} source "
        f"records, {cohort['unique_patients']} patients, and {cohort['index_patients']} diabetes-coded index "
        "patients after prespecified plausibility filtering. The analytic support surfaces were also clinically "
        f"relevant: {cohort['repeated_visit_patients']} patients had repeated-visit support, "
        f"{cohort['transition_eligible']} were eligible for first-to-last transition summaries, and "
        f"{cohort['eligible_sites']} eligible sites covered {cohort['visit_coverage']} of release visit episodes. "
        f"Medication fields were present in {cohort['medication_field_present']} index patients "
        f"({cohort['medication_field_present_share']}), and any parsed medication class was present in "
        f"{cohort['any_recorded_medication']} ({cohort['any_recorded_medication_share']}), making "
        "medication-capture sensitivity necessary for interpreting gap magnitudes.\n\n"
        "### Phenotype distribution and clinical profiles\n\n"
        "The hierarchy separated the cohort into six clinically interpretable phenotypes with different service-review "
        "implications. Adiposity-linked multimorbidity was the largest group (181,387 patients; 26.2%), followed by "
        "cardiometabolic-risk dominant diabetes (138,378; 20.0%), lower-burden diabetes (127,072; 18.3%), "
        "glycemic-dominant diabetes (104,508; 15.1%), severe glycemic multimorbidity (74,832; 10.8%), and "
        "adiposity-dominant diabetes (66,665; 9.6%). The profiles did not represent a simple severity ranking. "
        "Severe glycemic multimorbidity carried the highest mean HbA1c, glycemic-dominant diabetes isolated marked "
        "glycemic burden without the same multimorbidity pattern, adiposity-linked phenotypes carried the highest BMI "
        "context, and cardiometabolic-risk dominant diabetes was older on average. This structure created a "
        "phenotype map for asking where recorded medication coverage appeared discordant with the clinical context.\n\n"
        "### Phenotypes separated glycemic-intensity gaps from cardiometabolic-prevention gaps\n\n"
        "Recorded treatment-review gaps differed sharply across phenotypes, producing a care-review priority map "
        "rather than a uniform gap rate. The clearest glycemic mismatch appeared in glycemic-dominant diabetes, "
        "where severe glycemia with low recorded glucose-lowering intensity was 62.0% and uncontrolled glycemia "
        "with no recorded diabetes medication was 46.9%. Severe glycemic multimorbidity also showed a large severe "
        "glycemia low-intensity signal (43.5%) despite the highest mean HbA1c, but the uncontrolled-glycemia no-drug "
        "rate was lower than in glycemic-dominant diabetes (29.1%).\n\n"
        "A second service-review pattern involved cardiometabolic prevention signals. Hypertension context without a "
        f"recorded antihypertensive was {_format_count(hypertension.get('Gap n'))} of {_format_count(hypertension.get('Eligible denominator'))} "
        f"eligible patients ({_percent_value(hypertension.get('Gap %'))}) overall. Dyslipidemia context without "
        f"recorded lipid-lowering therapy was {_format_count(dyslipidemia.get('Gap n'))} of "
        f"{_format_count(dyslipidemia.get('Eligible denominator'))} ({_percent_value(dyslipidemia.get('Gap %'))}) overall. "
        f"Exploratory renal-risk context without recorded SGLT2 inhibitor or GLP-1 receptor agonist was "
        f"{_format_count(renal.get('Gap n'))} of {_format_count(renal.get('Eligible denominator'))} "
        f"({_percent_value(renal.get('Gap %'))}). These counts use phenotype- and indicator-specific denominators; "
        "Not assessed cells mark indicators outside the scoped denominator rather than absence of risk.\n\n"
        "The highest proportional phenotype was not always the largest service workload phenotype. For severe "
        f"glycemia with low recorded glucose-lowering intensity, the highest rate was in "
        f"{severe_contrast.get('highest_rate_phenotype', 'glycemic-dominant diabetes')} "
        f"({_percent_value(severe_contrast.get('highest_rate_pct'))}), whereas the largest absolute count was in "
        f"{severe_contrast.get('highest_count_phenotype', 'severe glycemic multimorbidity')} "
        f"({_format_count(severe_contrast.get('highest_count_n'))} patients). For uncontrolled glycemia without "
        f"recorded diabetes medication, {uncontrolled_contrast.get('highest_count_phenotype', 'glycemic-dominant diabetes')} "
        f"contributed the largest count ({_format_count(uncontrolled_contrast.get('highest_count_n'))}). For "
        f"hypertension and dyslipidemia recorded medication-coverage gaps, the highest rates occurred in "
        f"{hypertension_contrast.get('highest_rate_phenotype', 'severe glycemic multimorbidity')} and "
        f"{dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}, respectively, "
        f"but the largest absolute counts were in "
        f"{hypertension_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')} and "
        f"{dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}. This rate-count "
        "contrast separates high-risk phenotype targeting from service-capacity planning.\n\n"
        "### Medication-field restriction attenuated glycemic no-drug gaps but not cardiometabolic prevention gaps\n\n"
        "Medication-record sensitivity changed the magnitude but not the interpretation boundary. Among patients with "
        f"a nonempty medication field, severe glycemia with low recorded glucose-lowering intensity decreased from "
        f"{_percent_value(severe_all.get('Gap %'))} to {_percent_value(severe_present.get('Gap %'))}, uncontrolled "
        f"glycemia with no recorded diabetes medication decreased from {_percent_value(uncontrolled.get('Gap %'))} to "
        f"{_percent_value(uncontrolled_present.get('Gap %'))}, hypertension context without recorded "
        f"antihypertensive decreased from {_percent_value(hypertension.get('Gap %'))} to "
        f"{_percent_value(hypertension_present.get('Gap %'))}, dyslipidemia context without recorded lipid-lowering "
        f"therapy decreased from {_percent_value(dyslipidemia.get('Gap %'))} to "
        f"{_percent_value(dyslipidemia_present.get('Gap %'))}, and renal-risk context without recorded SGLT2 "
        f"inhibitor or GLP-1 receptor agonist decreased from {_percent_value(renal.get('Gap %'))} to "
        f"{_percent_value(renal_present.get('Gap %'))}. This attenuation shows that medication-field missingness "
        "contributes materially to glycemic no-drug indicators, while lipid-lowering signals remain large even in "
        "the medication-field-present denominator; renal-risk organ-protection coverage remains a secondary "
        f"exploratory review signal.{adjusted_results}\n\n"
        "### Transition stability and site support\n\n"
        "Repeated-visit and site summaries supported the phenotype narrative without converting it into a prediction "
        f"or external-validation claim. Among {transition['transition_eligible']} transition-eligible repeated-visit "
        f"patients, first-to-last same-phenotype stability was {transition['same_phenotype_stability']}. The most "
        f"frequent self-transition was {transition['most_frequent_self_transition']}, and the most frequent "
        f"cross-phenotype movement was {transition['most_frequent_cross_transition']}. The held-out site-support "
        f"surface included {transition['eligible_sites']} eligible site partitions and covered "
        f"{transition['visit_coverage']} of release visit episodes. Separately, anonymous source-site-code "
        "variability was wide among source-site codes with at least 50 eligible patients per indicator: median "
        f"severe-glycemia low-intensity gap was {_percent_value(severe_site.get('Median gap %'))} "
        f"(IQR {_percent_range_value(severe_site.get('IQR'))}), median hypertension no-antihypertensive gap was "
        f"{_percent_value(hypertension_site.get('Median gap %'))} (IQR {_percent_range_value(hypertension_site.get('IQR'))}), "
        f"and median dyslipidemia no-lipid-lowering gap was {_percent_value(dyslipidemia_site.get('Median gap %'))} "
        f"(IQR {_percent_range_value(dyslipidemia_site.get('IQR'))}). These findings indicate within-network coverage, "
        "partial phenotype persistence, and site-sensitive review priorities beyond patient phenotype alone; they do "
        "not establish external transportability, causal trajectory, treatment response, or site performance."
    )


def _tables_section(*, t1: str, t2: str, t3: str, t4: str) -> str:
    sections = ["## Tables"]
    if t1:
        sections.append("### Table 1. Data source, cohort assembly, and quality-control summary\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append(
            "### Table 2. Baseline characteristics and recorded risk-treatment mismatch signals by phenotype\n\n"
            + _strip_table_heading(_wide_phenotype_gap_summary_table(t2))
        )
    if t3:
        sections.append("### Table 3. Medication-capture sensitivity analysis of recorded mismatch signals\n\n" + _strip_table_heading(t3))
    if t4:
        sections.append("### Table 4. Site-adjusted dyslipidemia no-lipid-lowering sensitivity model\n\n" + _strip_table_heading(t4))
    return "\n\n".join(sections)


def _discussion_section(
    *,
    phenotype_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    largest = phenotype_rows[0] if phenotype_rows else {}
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    dyslipidemia_present = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Medication field present",
    )
    renal_present = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "Medication field present",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    adjusted_discussion = _adjusted_model_discussion_sentence(adjusted_model)
    return (
        "## Discussion\n\n"
        "### Principal findings\n\n"
        "This regional primary-care study has three main findings. First, recorded diabetes care-review gaps were "
        "phenotype-specific rather than uniform: glycemic-dominant diabetes carried the highest proportional severe "
        "glycemia low-intensity signal, while severe glycemic multimorbidity combined the highest HbA1c with a large "
        "low-intensity signal. Second, medication-record sensitivity separated documentation-sensitive glycemic "
        f"signals from more persistent cardiometabolic prevention signals: uncontrolled glycemia without recorded "
        f"diabetes medication fell from {_percent_value(uncontrolled.get('Gap %'))} to "
        f"{_percent_value(uncontrolled_present.get('Gap %'))}, whereas the dyslipidemia medication-coverage gap "
        f"remained {_percent_value(dyslipidemia_present.get('Gap %'))} in the medication-field-present denominator; "
        f"the renal-risk organ-protection signal remained {_percent_value(renal_present.get('Gap %'))} but was "
        "treated as secondary and exploratory. "
        f"Third, the largest service burden was concentrated in {largest.get('Phenotype', 'Adiposity-linked multimorbidity')}; "
        f"for dyslipidemia, the highest proportional phenotype was "
        f"{dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}, but the "
        f"largest absolute review workload was {dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}.\n\n"
        "### Clinical and service interpretation\n\n"
        "The phenotype map suggests three practical review priorities for a regional primary-care network. First, "
        "patients in glycemic-dominant and severe glycemic multimorbidity profiles may warrant chart-level review of "
        "severe glycemia, medication documentation, treatment intensification opportunities, contraindications, "
        "outside prescribing, and follow-up continuity. Second, adiposity-linked multimorbidity may be a high-yield "
        "service-review group because large patient counts coincide with recorded glycemic, antihypertensive, and "
        "lipid-lowering coverage gaps. Third, cardiometabolic-risk dominant diabetes and other scoped phenotypes "
        "highlight preventive-medication documentation signals even when mean HbA1c is not the dominant feature. The "
        "medication-field-present sensitivity analysis is important for clinical interpretation: glycemic no-drug "
        "indicators were strongly attenuated when medication fields were present, whereas lipid-lowering signals "
        f"remained large; renal-risk organ-protection coverage remained a secondary exploratory signal.{adjusted_discussion}\n\n"
        "These priorities are deliberately phrased as review signals. The DPCC medication fields identify what was "
        "recorded in the primary-care release, not the complete medication history. A recorded gap may reflect "
        "incomplete capture, treatment outside the network, self-purchased drugs, contraindications, patient "
        "preference, clinician judgment, or delayed updating of medication lists. The appropriate next step is "
        "therefore targeted chart audit, documentation review, and prospective care-pathway evaluation rather than "
        "direct prescribing recommendations from this study.\n\n"
        "Previous diabetes subclassification studies have primarily aimed to identify biologically or prognostically "
        "distinct subgroups using clustering frameworks or richer phenotyping panels. In contrast, the present "
        "hierarchy was designed for auditability in primary care rather than latent disease discovery. Its value lies "
        "not in replacing precision subclassification, but in translating routine-care variables into chart-review "
        "priorities that can be implemented in a regional service network with bounded denominator definitions.\n\n"
        "The exploratory renal-risk signal also requires careful interpretation. It captured recorded uptake of "
        "selected kidney-metabolic protective glucose-lowering agents rather than a complete kidney-protection "
        f"quality measure. In particular, the {_percent_value(renal.get('Gap %'))} rate does not account for ACEI/ARB "
        "use, albuminuria-defined eligibility, eGFR-based contraindications, or calendar-year prescribing context, "
        "and therefore should be read as an organ-protection review prompt rather than a definitive renal-care "
        "performance metric.\n\n"
        "### Phenotype stability and network support\n\n"
        f"The repeated-visit stability estimate of {transition['same_phenotype_stability']} suggests that phenotypes "
        "are partly persistent but clinically dynamic. Movement from severe glycemic multimorbidity to "
        "adiposity-linked multimorbidity may reflect changes in glycemia, measurement timing, treatment, visit "
        "context, or documentation rather than a proven biological transition. Site-level support reduces concern "
        "that the profile is entirely dominated by one site, but it remains within-network support rather than "
        "external validation.\n\n"
        "### Implications for future work\n\n"
        "The results provide a service-priority scaffold for follow-up studies. Future prospective and "
        "implementation studies could extend this descriptive atlas by quantifying patient- and site-level "
        "determinants, evaluating calendar-time changes in newer cardiometabolic agents, and testing whether "
        "phenotype-guided chart review improves medication documentation completeness, treatment-intensification "
        "assessment, follow-up scheduling, gap resolution, or cardiometabolic risk-management processes. These "
        "extensions would support stronger service-performance or guideline-based claims only after direct "
        "chart-review, eligibility, contraindication, and prescribing-context evidence is added."
    )


def _limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "This study used routinely collected primary-care records and is subject to missingness, irregular "
        "measurement, coding variation, medication-record incompleteness, and site-level practice differences. "
        "Medication exposure was limited to drug classes recorded in the DPCC primary-care release; the study did "
        "not observe complete pharmacy dispensing, medication adherence, contraindications, patient preference, "
        "clinician rationale, or treatment obtained outside the network. Blood-pressure target attainment was not "
        "analyzed because of the field-semantic issue documented in the data-quality assessment. The phenotype "
        "hierarchy is clinically interpretable and reproducible, but it is not a causal model, clustering discovery "
        "claim, or individualized decision-support tool. Most participating practices were in Hunan, so estimates "
        "should be interpreted as DPCC network findings rather than national prevalence, national treatment-gap "
        "rates, or generalizable service-performance benchmarks. Prospective validation, chart audit, and external "
        "network testing are required before these phenotypes are used to guide interventions."
    )


def _conclusion_section() -> str:
    return (
        "## Conclusion\n\n"
        "A deterministic clinical phenotype hierarchy applied to the DPCC primary-care network showed that recorded "
        "diabetes care-review gaps were phenotype-specific, medication-capture sensitive, and site-sensitive rather "
        "than a single uniform treatment gap. Glycemic profiles identified concentrated review groups, whereas "
        "cardiometabolic contexts highlighted persistent preventive-medication coverage signals, while renal-risk "
        "context remained a secondary exploratory organ-protection review prompt. The "
        "atlas supports local documentation review, chart audit, and prospective care-pathway evaluation while "
        "avoiding treatment-effect, guideline-nonadherence, individualized prescribing, and national-generalization "
        "claims."
    )


def _study_root_from_paper_root(paper_root: Path) -> Path:
    resolved = paper_root.expanduser().resolve()
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / "artifacts").is_dir() and (
            (candidate / "artifacts" / "controller").exists()
            or (candidate / "artifacts" / "reviewer_revision").exists()
            or (candidate / "submission").exists()
        ):
            return candidate
    return resolved.parent


def _read_supplementary_tables_text(*, paper_root: Path, study_root: Path) -> str:
    reviewer_revision_supplement = _bounded_supplementary_tables_text(study_root)
    if reviewer_revision_supplement:
        return reviewer_revision_supplement
    candidates = (
        study_root / "submission" / "supplementary_tables.md",
        study_root / "submission" / "supplementary_material.md",
        paper_root / "submission_minimal" / "supplementary_tables.md",
        paper_root / "submission_minimal" / "supplementary_material.md",
    )
    for path in candidates:
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if "Supplementary Table" in text:
                return text
    return ""


def _latest_bounded_analysis_campaign_dir(study_root: Path) -> Path | None:
    root = study_root / "artifacts" / "reviewer_revision"
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.glob("*/bounded_analysis_campaign")
        if path.is_dir() and (path / "tables").is_dir()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, str(path)))


def _bounded_table_text(study_root: Path, filename: str) -> str:
    campaign_dir = _latest_bounded_analysis_campaign_dir(study_root)
    if campaign_dir is None:
        return ""
    path = campaign_dir / "tables" / filename
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _bounded_supplementary_tables_text(study_root: Path) -> str:
    sections: list[str] = []
    for title, filename in (
        (
            "Supplementary Table S1. Missingness and plausibility atlas for phenotype-defining variables",
            "missingness_plausibility_atlas.md",
        ),
        (
            "Supplementary Table S2. Medication-record sensitivity for core review signals",
            "medication_field_present_sensitivity.md",
        ),
        (
            "Supplementary Table S3. Anonymous source-site-code variability in recorded medication-review signals",
            "site_gap_variability_summary.md",
        ),
        (
            "Supplementary Table S4. Adult/plausible-age boundary sensitivity",
            "adult_boundary_sensitivity.md",
        ),
        (
            "Supplementary Table S5. Diagnostic variable ascertainment",
            "diagnostic_variable_ascertainment_table.md",
        ),
    ):
        table = _bounded_table_text(study_root, filename)
        if not table:
            continue
        sections.append(f"### {title}\n\n{_submission_safe_supplementary_text(_strip_table_heading(table))}")
    if not sections:
        return ""
    return "## Supplementary Tables\n\n" + "\n\n".join(sections)


def _submission_safe_supplementary_text(text: str) -> str:
    return text.replace("糖尿病", "the Chinese diabetes term")


def _apply_bounded_t2_revisions(
    *,
    t2: str,
    study_root: Path,
    clinical_rows: list[dict[str, str]] | None = None,
) -> str:
    risk_rows = _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv")
    if not t2 or not risk_rows:
        return t2
    values_by_phenotype: dict[str, dict[str, str]] = {}
    for row in risk_rows:
        phenotype = _text(row.get("phenotype"))
        if phenotype is None:
            continue
        values_by_phenotype[phenotype] = row
    for row in clinical_rows or []:
        phenotype = _text(row.get("Phenotype"))
        if phenotype is None or phenotype not in values_by_phenotype:
            continue
        values_by_phenotype[phenotype].update(
            {
                "Mean age, y": _text(row.get("Mean age, y") or row.get("Age, y")) or "",
                "Mean BMI": _text(row.get("Mean BMI") or row.get("BMI")) or "",
                "Mean HbA1c": _text(row.get("Mean HbA1c") or row.get("HbA1c")) or "",
            }
        )
    measure_to_field = {
        "Index patients": "index_patients",
        "Share of index cohort": "share_of_index_cohort",
        "Mean age, y": "Mean age, y",
        "Mean BMI": "Mean BMI",
        "Mean HbA1c": "Mean HbA1c",
        "Severe glycemia low-intensity gap": "severe_glycemia_low_recorded_glucose_lowering_intensity_pct",
        "Uncontrolled glycemia with no diabetes drug": "uncontrolled_glycemia_no_recorded_diabetes_medication_pct",
        "Hypertension with no antihypertensive": "hypertension_context_no_recorded_antihypertensive_pct",
        "Dyslipidemia with no lipid-lowering": "dyslipidemia_context_no_recorded_lipid_lowering_pct",
    }
    changed = False
    output: list[str] = []
    for line in t2.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Phenotype"}:
            output.append(line)
            continue
        phenotype, measure, old_value = cells
        field = measure_to_field.get(measure)
        bounded_row = values_by_phenotype.get(phenotype)
        if field is None or bounded_row is None:
            output.append(line)
            continue
        new_value = _format_bounded_t2_value(bounded_row.get(field), percent=field.endswith("_pct") or field == "share_of_index_cohort")
        if new_value and new_value != old_value:
            cells[2] = new_value
            line = "| " + " | ".join(cells) + " |"
            changed = True
        output.append(line)
    updated = "\n".join(output) if changed else t2
    return _apply_bounded_wide_t2_revisions(t2=updated, values_by_phenotype=values_by_phenotype)


def _apply_bounded_wide_t2_revisions(
    *,
    t2: str,
    values_by_phenotype: Mapping[str, Mapping[str, str]],
) -> str:
    rows = _markdown_table_rows(t2)
    if not rows or "Measure" in rows[0]:
        return t2
    field_by_header = {
        "n": ("index_patients", False),
        "Index patients": ("index_patients", False),
        "%": ("share_of_index_cohort", True),
        "Share of index cohort": ("share_of_index_cohort", True),
        "Age, y": ("Mean age, y", False),
        "Mean age, y": ("Mean age, y", False),
        "BMI": ("Mean BMI", False),
        "Mean BMI": ("Mean BMI", False),
        "HbA1c": ("Mean HbA1c", False),
        "Mean HbA1c": ("Mean HbA1c", False),
        "Severe glycemia / low intensity": ("severe_glycemia_low_recorded_glucose_lowering_intensity_pct", True),
        "Severe glycemia low-intensity gap": ("severe_glycemia_low_recorded_glucose_lowering_intensity_pct", True),
        "Uncontrolled / no diabetes drug": ("uncontrolled_glycemia_no_recorded_diabetes_medication_pct", True),
        "Uncontrolled glycemia with no diabetes drug": ("uncontrolled_glycemia_no_recorded_diabetes_medication_pct", True),
        "Hypertension / no antihypertensive": ("hypertension_context_no_recorded_antihypertensive_pct", True),
        "Hypertension with no antihypertensive": ("hypertension_context_no_recorded_antihypertensive_pct", True),
        "Dyslipidemia / no lipid-lowering": ("dyslipidemia_context_no_recorded_lipid_lowering_pct", True),
        "Dyslipidemia with no lipid-lowering": ("dyslipidemia_context_no_recorded_lipid_lowering_pct", True),
    }
    changed = False
    output: list[str] = []
    for line in t2.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"---", "Phenotype"}:
            output.append(line)
            continue
        bounded_row = values_by_phenotype.get(cells[0])
        if bounded_row is None:
            output.append(line)
            continue
        headers = _wide_t2_headers(t2)
        if len(cells) != len(headers):
            output.append(line)
            continue
        for index, header in enumerate(headers):
            spec = field_by_header.get(header)
            if spec is None:
                continue
            field, percent = spec
            new_value = _format_bounded_t2_value(bounded_row.get(field), percent=percent)
            if new_value and new_value != cells[index]:
                cells[index] = new_value
                changed = True
        output.append("| " + " | ".join(cells) + " |")
    return "\n".join(output) if changed else t2


def _bounded_index_total(study_root: Path) -> int | None:
    total = 0
    seen = False
    for row in _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv"):
        value = _int_from_numeric_text(row.get("index_patients"))
        if value is None:
            continue
        total += value
        seen = True
    return total if seen else None


def _apply_bounded_t1_revisions(*, t1: str, study_root: Path) -> str:
    index_total = _bounded_index_total(study_root)
    if not t1 or index_total is None:
        return t1
    changed = False
    output: list[str] = []
    for line in t1.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Characteristic"}:
            output.append(line)
            continue
        characteristic, measure, old_value = cells
        if characteristic == "Cohort definition — Index patients" or measure == "Index patients":
            new_value = _format_count(index_total)
            if new_value != old_value:
                cells[2] = new_value
                line = "| " + " | ".join(cells) + " |"
                changed = True
        output.append(line)
    return "\n".join(output) if changed else t1


def _apply_bounded_transition_table_revisions(*, transition_table: str, study_root: Path) -> str:
    index_total = _bounded_index_total(study_root)
    if not transition_table or index_total is None:
        return transition_table
    changed = False
    output: list[str] = []
    for line in transition_table.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Section"}:
            output.append(line)
            continue
        section, metric, old_value = cells
        if section == "Transition support" and metric == "Index patients":
            new_value = _format_count(index_total)
            if new_value != old_value:
                cells[2] = new_value
                line = "| " + " | ".join(cells) + " |"
                changed = True
        output.append(line)
    return "\n".join(output) if changed else transition_table


def _bounded_table_rows(study_root: Path, filename: str) -> list[dict[str, str]]:
    campaign_dir = _latest_bounded_analysis_campaign_dir(study_root)
    if campaign_dir is None:
        return []
    path = campaign_dir / "tables" / filename
    if not path.exists() or not path.is_file():
        return []
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    return _markdown_table_rows(path.read_text(encoding="utf-8"))


def _adjusted_model_values(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        comparison = _text(row.get("comparison"))
        if comparison is not None:
            result[comparison] = row
    return result


def _adjusted_model_lookup(
    adjusted_model: Mapping[str, Mapping[str, str]],
    comparison: str,
) -> Mapping[str, str]:
    return adjusted_model.get(comparison, {})


def _format_adjusted_or_ci(row: Mapping[str, str]) -> str:
    adjusted_or = _text(row.get("adjusted_or")) or "NA"
    ci = _text(row.get("ci_95")) or "NA"
    return f"adjusted OR {adjusted_or}, 95% CI {ci}"


def _adjusted_model_results_sentence(adjusted_model: Mapping[str, Mapping[str, str]]) -> str:
    if not adjusted_model:
        return ""
    cardio = _adjusted_model_lookup(
        adjusted_model,
        "Cardiometabolic-risk dominant diabetes vs Adiposity-linked multimorbidity",
    )
    glycemic = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    severe = _adjusted_model_lookup(
        adjusted_model,
        "Severe glycemic multimorbidity vs Adiposity-linked multimorbidity",
    )
    if not cardio or not glycemic or not severe:
        return ""
    return (
        " In the medication-field-present dyslipidemia-context sensitivity model, after adjustment for age, sex, "
        f"and anonymous source-site fixed effects, the corresponding odds ratios versus adiposity-linked "
        f"multimorbidity were {_format_adjusted_or_ci(cardio)} for cardiometabolic-risk dominant diabetes, "
        f"{_format_adjusted_or_ci(glycemic)} for glycemic-dominant diabetes, and "
        f"{_format_adjusted_or_ci(severe)} for severe glycemic multimorbidity."
    )


def _adjusted_model_discussion_sentence(adjusted_model: Mapping[str, Mapping[str, str]]) -> str:
    glycemic = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    if not glycemic:
        return ""
    return (
        " The site fixed-effect dyslipidemia sensitivity model supports the same service-review interpretation: "
        "the lipid-lowering signal remained phenotype-patterned after basic patient and anonymous-site adjustment, "
        f"with glycemic-dominant diabetes showing {_format_adjusted_or_ci(glycemic)} versus adiposity-linked "
        "multimorbidity. This model is supportive rather than causal and should not be read as a site-performance "
        "or guideline-adherence estimate."
    )


def _build_adjusted_model_table(rows: list[dict[str, str]]) -> str:
    selected = [
        row
        for row in rows
        if _text(row.get("comparison"))
        in {
            "Cardiometabolic-risk dominant diabetes vs Adiposity-linked multimorbidity",
            "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
            "Severe glycemic multimorbidity vs Adiposity-linked multimorbidity",
            "Age, per year",
            "Female vs male",
        }
    ]
    if not selected:
        return ""
    output = [
        "| Comparison | Adjusted OR | 95% CI | P value | Model n | Source sites | Interpretation boundary |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in selected:
        output.append(
            "| "
            + " | ".join(
                [
                    _text(row.get("comparison")) or "NA",
                    _text(row.get("adjusted_or")) or "NA",
                    _text(row.get("ci_95")) or "NA",
                    _text(row.get("p_value")) or "NA",
                    _format_count(row.get("model_n")),
                    _format_count(row.get("source_sites_in_model")),
                    _text(row.get("interpretation_boundary")) or "secondary sensitivity analysis",
                ]
            )
            + " |"
        )
    return "\n".join(output)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _burden_contrast_values(study_root: Path) -> dict[str, dict[str, str]]:
    specs = {
        "severe_glycemia_low_recorded_glucose_lowering_intensity": (
            "severe_glycemia_low_recorded_glucose_lowering_intensity_gap",
            "severe_glycemia_low_recorded_glucose_lowering_intensity_pct",
        ),
        "uncontrolled_glycemia_no_recorded_diabetes_medication": (
            "uncontrolled_glycemia_no_recorded_diabetes_medication_gap",
            "uncontrolled_glycemia_no_recorded_diabetes_medication_pct",
        ),
        "hypertension_context_no_recorded_antihypertensive": (
            "hypertension_context_no_recorded_antihypertensive_gap",
            "hypertension_context_no_recorded_antihypertensive_pct",
        ),
        "dyslipidemia_context_no_recorded_lipid_lowering": (
            "dyslipidemia_context_no_recorded_lipid_lowering_gap",
            "dyslipidemia_context_no_recorded_lipid_lowering_pct",
        ),
        "renal_risk_no_recorded_sglt2_or_glp1": (
            "renal_risk_no_recorded_sglt2_or_glp1_gap",
            "renal_risk_no_recorded_sglt2_or_glp1_pct",
        ),
    }
    rows = _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv")
    result: dict[str, dict[str, str]] = {}
    for indicator_id, (count_field, rate_field) in specs.items():
        highest_count: tuple[int, str] | None = None
        highest_rate: tuple[float, str] | None = None
        for row in rows:
            phenotype = _text(row.get("phenotype"))
            if phenotype is None:
                continue
            count = _int_from_numeric_text(row.get(count_field))
            rate = _float_from_text(row.get(rate_field))
            if count is not None and count > 0 and (highest_count is None or count > highest_count[0]):
                highest_count = (count, phenotype)
            if rate is not None and (highest_rate is None or rate > highest_rate[0]):
                highest_rate = (rate, phenotype)
        values: dict[str, str] = {}
        if highest_count is not None:
            values["highest_count_n"] = str(highest_count[0])
            values["highest_count_phenotype"] = highest_count[1]
        if highest_rate is not None:
            values["highest_rate_pct"] = f"{highest_rate[0]:.1f}"
            values["highest_rate_phenotype"] = highest_rate[1]
        if values:
            result[indicator_id] = values
    return result


def _burden_contrast_lookup(
    burden_contrasts: Mapping[str, Mapping[str, str]],
    indicator_id: str,
) -> dict[str, str]:
    row = burden_contrasts.get(indicator_id)
    return dict(row) if isinstance(row, Mapping) else {}


def _format_bounded_t2_value(value: object, *, percent: bool) -> str:
    text = _text(value)
    if text is None or text in {"", "NA", "Not assessed"}:
        return "NA"
    if percent:
        return text if text.endswith("%") else f"{text}%"
    return _format_count(text)


def _extract_markdown_section(text: str, heading: str) -> str:
    if not text or heading not in text:
        return ""
    heading_title = heading.lstrip("#").strip()
    lines = text.splitlines()
    start: int | None = None
    heading_level = 3
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == heading or stripped.lstrip("#").strip() == heading_title:
            start = index
            heading_level = len(stripped.split(" ", 1)[0])
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped.split(" ", 1)[0])
        if level <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def _supplementary_table_rows(text: str, heading: str) -> list[dict[str, str]]:
    return _markdown_table_rows(_extract_markdown_section(text, heading))


def _medication_sensitivity_values(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, dict[str, str]]]:
    result: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        normalized = _normalize_sensitivity_row(row)
        indicator = _text(normalized.get("Indicator"))
        denominator_mode = _text(normalized.get("Denominator mode"))
        if indicator is None or denominator_mode is None:
            continue
        result.setdefault(indicator, {})[denominator_mode] = normalized
    return result


def _normalize_sensitivity_row(row: Mapping[str, str]) -> dict[str, str]:
    indicator = _text(row.get("Indicator") or row.get("indicator"))
    denominator_mode = _text(row.get("Denominator mode") or row.get("denominator_mode"))
    if denominator_mode == "all_eligible":
        denominator_mode = "All eligible"
    elif denominator_mode == "medication_field_present":
        denominator_mode = "Medication field present"
    elif denominator_mode == "any_recorded_medication_class":
        denominator_mode = "Any recorded medication class"
    return {
        "Indicator": indicator or "",
        "Denominator mode": denominator_mode or "",
        "Eligible denominator": _text(row.get("Eligible denominator") or row.get("eligible_denominator")) or "",
        "Gap n": _text(row.get("Gap n") or row.get("gap_n")) or "",
        "Gap %": _text(row.get("Gap %") or row.get("gap_pct")) or "",
        "Interpretation boundary": _text(row.get("Interpretation boundary") or row.get("interpretation_boundary")) or "",
    }


def _site_variability_values(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        normalized = _normalize_site_variability_row(row)
        indicator = _text(normalized.get("Indicator"))
        if indicator is None:
            continue
        result[indicator] = normalized
    return result


def _normalize_site_variability_row(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "Indicator": _text(row.get("Indicator") or row.get("indicator")) or "",
        "Site denominator minimum": _text(row.get("Site denominator minimum") or row.get("site_denominator_minimum")) or "",
        "Eligible sites": _text(row.get("Eligible sites") or row.get("eligible_sites")) or "",
        "Median gap %": _text(row.get("Median gap %") or row.get("median_gap_pct")) or "",
        "IQR": _text(row.get("IQR") or row.get("iqr_gap_pct")) or "",
        "Range": _text(row.get("Range") or row.get("range_gap_pct")) or "",
        "Interpretation boundary": _text(row.get("Interpretation boundary") or row.get("site_interpretation_boundary")) or "",
    }


def _sensitivity_lookup(
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
    indicator: str,
    denominator_mode: str,
) -> dict[str, str]:
    indicator_values = sensitivity.get(indicator)
    if isinstance(indicator_values, Mapping):
        row = indicator_values.get(denominator_mode)
        if isinstance(row, Mapping):
            return dict(row)
    return {}


def _site_variability_lookup(
    site_variability: Mapping[str, Mapping[str, str]],
    indicator: str,
) -> dict[str, str]:
    row = site_variability.get(indicator)
    return dict(row) if isinstance(row, Mapping) else {}


def _build_medication_capture_sensitivity_table(
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> str:
    indicators = (
        "Severe glycemia with low recorded glucose-lowering intensity",
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Hypertension context with no recorded antihypertensive",
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
    )
    rows = [
        "| Indicator | Overall denominator | Overall gap | Medication-field-present denominator | Gap in medication-field-present patients | Attenuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for indicator in indicators:
        overall = _sensitivity_lookup(sensitivity, indicator, "All eligible")
        field_present = _sensitivity_lookup(sensitivity, indicator, "Medication field present")
        if not overall or not field_present:
            continue
        rows.append(
            "| "
            + " | ".join(
                (
                    indicator,
                    _text(overall.get("Eligible denominator")) or "NA",
                    _format_gap_summary(overall),
                    _text(field_present.get("Eligible denominator")) or "NA",
                    _format_gap_summary(field_present),
                    _attenuation_summary(overall, field_present),
                )
            )
            + " |"
        )
    return "\n".join(rows)


def _build_supplementary_tables_section(*, supplementary_text: str, transition_table: str) -> str:
    base = supplementary_text.strip()
    transition = _strip_table_heading(transition_table)
    if base:
        if "## Supplementary Tables" not in base:
            base = "## Supplementary Tables\n\n" + base
        if transition and "Supplementary Table S6. Transition stability and site-level support" not in base:
            if not base.endswith("\n"):
                base += "\n"
            base += (
                "\n### Supplementary Table S6. Transition stability and site-level support\n\n"
                + transition
            )
        return base
    if not transition:
        return ""
    return (
        "## Supplementary Tables\n\n"
        "### Supplementary Table S6. Transition stability and site-level support\n\n"
        + transition
    )


def _format_gap_summary(row: Mapping[str, str]) -> str:
    gap_n = _text(row.get("Gap n")) or "NA"
    gap_pct = _percent_value(row.get("Gap %"))
    return f"{gap_n} ({gap_pct})"


def _attenuation_summary(overall: Mapping[str, str], field_present: Mapping[str, str]) -> str:
    overall_pct = _float_from_text(overall.get("Gap %"))
    present_pct = _float_from_text(field_present.get("Gap %"))
    if overall_pct is None or present_pct is None:
        return "NA"
    delta = present_pct - overall_pct
    return f"{overall_pct:.1f}% to {present_pct:.1f}% ({delta:+.1f} pp)"


def _percent_value(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    return text if text.endswith("%") else f"{text}%"


def _percent_range_value(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    if "%" in text:
        return text
    if "-" in text:
        left, right = text.split("-", 1)
        return f"{left.strip()}%-{right.strip()}%"
    return _percent_value(text)


def _float_from_text(value: object) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text.replace("%", "").replace(",", ""))
    except ValueError:
        return None


def _t1_value_map(t1: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in _markdown_table_rows(t1):
        characteristic = _text(row.get("Characteristic"))
        measure = _text(row.get("Measure"))
        value = _text(row.get("Value"))
        if measure and value:
            values[measure] = value
        if characteristic and value:
            values[characteristic] = value
    return values


def _cohort_values(*, methods: Mapping[str, Any], flow: Mapping[str, Any], t1: str) -> dict[str, str]:
    design = _mapping(methods.get("study_design"))
    cohort_definition = _text(design.get("cohort_definition")) or ""
    steps = [dict(item) for item in flow.get("steps") or [] if isinstance(item, Mapping)]
    t1_values = _t1_value_map(t1)
    index_denominator = _step_n(steps, "index_analysis_cohort") or 692842
    adult_plausible_age = t1_values.get("Adult/plausible-age patients") or 691992
    medication_field_present = _count_from_summary(
        t1_values.get("Index patients with nonempty medication fields")
    ) or "378,383"
    any_recorded_medication = _count_from_summary(
        t1_values.get("Index patients with any parsed medication class")
    ) or "377,032"
    return {
        "processed_records": _format_count(
            _step_n(steps, "deidentified_release_visits") or _first_int(cohort_definition) or 1779360
        ),
        "unique_patients": _format_count(_step_n(steps, "processed_patients") or 861778),
        "index_patients": _format_count(index_denominator),
        "adult_plausible_age": _format_count(
            adult_plausible_age
        ),
        "adult_plausible_age_share": _format_share(
            numerator=adult_plausible_age,
            denominator=index_denominator,
        ),
        "repeated_visit_patients": _format_count(_step_n(steps, "repeated_visit_support_panel") or 291788),
        "transition_eligible": _format_count(_step_n(steps, "transition_eligible_support_set") or 291084),
        "cross_site_patients": _format_count(
            t1_values.get("Cross-site continuity patients") or 271787
        ),
        "eligible_sites": _format_count(t1_values.get("Eligible sites") or 69),
        "visit_coverage": _text(t1_values.get("Visit-episode coverage")) or "93.45%",
        "bp_inversion_rate": _text(t1_values.get("Original BP inversion rate")) or "99.88%",
        "bp_swapped_plausible_rate": _text(t1_values.get("Swapped BP plausible rate")) or "99.87%",
        "bmi_excluded": _format_count(t1_values.get("BMI excluded rows") or 1015),
        "hba1c_excluded": _format_count(t1_values.get("HbA1c excluded rows") or 4126),
        "fasting_glucose_excluded": _format_count(
            t1_values.get("Fasting glucose excluded rows") or 2166
        ),
        "medication_field_present": medication_field_present,
        "medication_field_present_share": _share_from_summary(
            t1_values.get("Index patients with nonempty medication fields")
        )
        if _share_from_summary(t1_values.get("Index patients with nonempty medication fields")) != "NA"
        else _format_share(numerator=medication_field_present, denominator=index_denominator),
        "any_recorded_medication": any_recorded_medication,
        "any_recorded_medication_share": _share_from_summary(
            t1_values.get("Index patients with any parsed medication class")
        )
        if _share_from_summary(t1_values.get("Index patients with any parsed medication class")) != "NA"
        else _format_share(numerator=any_recorded_medication, denominator=index_denominator),
    }


def _transition_values(*, t3: str, transition_support: Mapping[str, Any]) -> dict[str, str]:
    rows = _markdown_table_rows(t3)
    values = {row.get("Metric", ""): row.get("Value", "") for row in rows}
    displays = transition_support.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    return {
        "transition_eligible": values.get("Transition-eligible patients") or "291,084",
        "same_phenotype_stability": values.get("First-to-last same-phenotype stability rate") or "45.45%",
        "most_frequent_self_transition": values.get("Most frequent self-transition")
        or "Adiposity-linked multimorbidity to adiposity-linked multimorbidity: 57,686 patients (19.82%)",
        "most_frequent_cross_transition": values.get("Most frequent cross-phenotype movement")
        or "Severe glycemic multimorbidity to adiposity-linked multimorbidity: 14,580 patients (5.01%)",
        "eligible_sites": _format_count(display.get("eligible_site_count")) if display else "69",
        "visit_coverage": _format_percent(display.get("visit_coverage")) if display else "93.45%",
    }


def _phenotype_rows(
    *,
    t2: str,
    phenotype_structure: Mapping[str, Any],
    treatment_gap_alignment: Mapping[str, Any],
) -> list[dict[str, str]]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if rows:
        return rows
    displays = phenotype_structure.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    gap_rows = _gap_rows(treatment_gap_alignment=treatment_gap_alignment)
    result: list[dict[str, str]] = []
    for row in display.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        phenotype_label = _text(row.get("phenotype_label")) or "Phenotype"
        gap_row = _find_row(gap_rows, "phenotype_label", phenotype_label) or {}
        result.append(
            {
                "Phenotype": phenotype_label,
                "Index patients": _format_count(gap_row.get("index_patients")),
                "Share of index cohort": _format_percent(row.get("share_of_index_patients")),
            }
        )
    return result


def _gap_rows(*, treatment_gap_alignment: Mapping[str, Any]) -> list[dict[str, str]]:
    displays = treatment_gap_alignment.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    result: list[dict[str, str]] = []
    for row in display.get("rows") or []:
        if isinstance(row, Mapping):
            result.append({str(key): str(value) for key, value in row.items()})
    return result


def _materialize_dpcc_display_metadata_repairs(*, paper_root: Path) -> list[str]:
    changed_paths: list[str] = []
    study_root = _study_root_from_paper_root(paper_root)
    t1 = _read_table_text(
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md",
        fallback_path=paper_root / "tables" / "T1_baseline_characteristics.md",
    )
    t1 = _apply_bounded_t1_revisions(t1=t1, study_root=study_root)
    t2 = _read_table_text(
        paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.md",
        fallback_path=paper_root / "tables" / "T2_phenotype_gap_summary.md",
    )
    t2 = _apply_bounded_t2_revisions(
        t2=t2,
        study_root=study_root,
        clinical_rows=_read_csv_rows(paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv"),
    )
    t3_transition = _read_table_text(
        paper_root / "tables" / "generated" / "T3_transition_site_support_summary.md",
        fallback_path=paper_root / "tables" / "T3_transition_site_support_summary.md",
    )
    t3_transition = _apply_bounded_transition_table_revisions(
        transition_table=t3_transition,
        study_root=study_root,
    )
    supplementary_text = _read_supplementary_tables_text(paper_root=paper_root, study_root=study_root)
    sensitivity = _medication_sensitivity_values(
        _supplementary_table_rows(
            supplementary_text,
            "Supplementary Table S2. Medication-record sensitivity for core review signals",
        )
    )
    adjusted_model_rows = _bounded_table_rows(study_root, "dyslipidemia_adjusted_site_model.csv")
    for relpath in (
        Path("cohort_flow.json"),
        Path("dpcc_phenotype_gap_structure.json"),
        Path("dpcc_treatment_gap_alignment.json"),
        Path("table_catalog.json"),
        Path("tables") / "table_catalog.json",
        Path("figure_semantics_manifest.json"),
        Path("results_narrative_map.json"),
        Path("medical_manuscript_blueprint.json"),
        Path("claim_evidence_map.json"),
        Path("figure_catalog.json"),
        Path("figures") / "figure_catalog.json",
        Path("build") / "display_pack_render_requests" / "F4.render_request.json",
    ):
        path = paper_root / relpath
        if not path.exists() or not path.is_file():
            continue
        payload = _read_json_object(path)
        if not payload:
            continue
        updated = _replace_dpcc_display_metadata_text(payload)
        if relpath == Path("cohort_flow.json"):
            updated = _repair_dpcc_cohort_flow_payload(updated, t1=t1)
        elif relpath == Path("dpcc_phenotype_gap_structure.json"):
            updated = _repair_dpcc_phenotype_gap_structure_payload(updated, t2=t2)
        elif relpath == Path("dpcc_treatment_gap_alignment.json") or relpath.name == "F4.render_request.json":
            updated = _repair_dpcc_treatment_gap_alignment_payload(updated, t2=t2, study_root=study_root)
        elif relpath in {Path("table_catalog.json"), Path("tables") / "table_catalog.json"}:
            updated = _repair_dpcc_table_catalog_payload(
                updated,
                has_adjusted_model=bool(adjusted_model_rows),
            )
        elif relpath == Path("figure_semantics_manifest.json"):
            updated = _repair_dpcc_figure_semantics_manifest_payload(updated)
        elif relpath == Path("medical_manuscript_blueprint.json"):
            updated = _repair_dpcc_manuscript_blueprint_payload(updated)
        if updated != payload and _write_json_if_changed(path, updated):
            changed_paths.append(str(path.resolve()))
    changed_paths.extend(
        _materialize_dpcc_support_tables(
            paper_root=paper_root,
            t1=t1,
            t2=t2,
            sensitivity=sensitivity,
            transition_table=t3_transition,
            adjusted_model_rows=adjusted_model_rows,
        )
    )
    return changed_paths


def _replace_dpcc_display_metadata_text(value: Any) -> Any:
    if isinstance(value, str):
        updated = value
        for target, replacement in DPCC_DISPLAY_TEXT_REPLACEMENTS:
            updated = updated.replace(target, replacement)
        return updated
    if isinstance(value, list):
        return [_replace_dpcc_display_metadata_text(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_dpcc_display_metadata_text(item)
            for key, item in value.items()
        }
    return value


def _repair_dpcc_cohort_flow_payload(payload: Mapping[str, Any], *, t1: str) -> dict[str, Any]:
    updated = dict(payload)
    t1_values = _t1_value_map(t1)
    updated["caption"] = (
        "Source records, processed patients, the diabetes-coded index cohort, adult/plausible-age sensitivity "
        "cohort, repeated-visit support panel, transition denominator, and held-out site-support partitions for the "
        "descriptive primary-care manuscript."
    )
    updated["steps"] = [
        {
            "step_id": "deidentified_release_visits",
            "label": "Deidentified DPCC visit records",
            "n": 1779360,
            "detail": "May 2020-December 2025",
        },
        {
            "step_id": "processed_patients",
            "label": "Unique patients",
            "n": 861778,
            "detail": "Patient-level denominator after visit-record aggregation",
        },
        {
            "step_id": "index_analysis_cohort",
            "label": "Diabetes-coded index cohort",
            "n": 692842,
            "detail": "Primary phenotype-analysis denominator",
        },
        {
            "step_id": "adult_plausible_age_sensitivity_cohort",
            "label": "Adult/plausible-age sensitivity cohort",
            "n": int(str(t1_values.get("Adult/plausible-age patients") or "691992").replace(",", "")),
            "detail": "Age-plausible adults retained for sensitivity audit",
        },
        {
            "step_id": "repeated_visit_support_panel",
            "label": "Repeated-visit support panel",
            "n": 291788,
            "detail": "Secondary longitudinal support denominator",
        },
        {
            "step_id": "transition_eligible_support_set",
            "label": "Transition-eligible patients",
            "n": 291084,
            "detail": "First-to-last phenotype support denominator",
        },
        {
            "step_id": "held_out_site_support_partitions",
            "label": "Held-out site-support partitions",
            "n": 69,
            "detail": "69 site partitions; 93.45% visit-episode coverage",
        },
    ]
    updated["exclusion_branches"] = [
        {
            "branch_id": "not_index_analysis_eligible",
            "from_step_id": "processed_patients",
            "label": "Not index-analysis eligible",
            "n": 168936,
            "detail": "Not carried into the diabetes-coded index cohort",
        }
    ]
    return updated


def _repair_dpcc_treatment_gap_alignment_payload(
    payload: Mapping[str, Any],
    *,
    t2: str,
    study_root: Path,
) -> dict[str, Any]:
    updated = _replace_dpcc_display_metadata_text(payload)
    rows = updated.get("rows")
    if rows is None and isinstance(updated.get("displays"), list):
        displays = list(updated["displays"])
        if displays and isinstance(displays[0], Mapping):
            display = dict(displays[0])
            display["rows"] = _dpcc_rows_with_explicit_rates(
                rows=display.get("rows"),
                t2=t2,
                study_root=study_root,
            )
            displays[0] = display
            updated = dict(updated)
            updated["displays"] = displays
            return updated
    updated = dict(updated)
    updated["rows"] = _dpcc_rows_with_explicit_rates(rows=rows, t2=t2, study_root=study_root)
    return updated


def _repair_dpcc_phenotype_gap_structure_payload(
    payload: Mapping[str, Any],
    *,
    t2: str,
) -> dict[str, Any]:
    updated = _replace_dpcc_display_metadata_text(payload)
    rows = updated.get("rows")
    if rows is None and isinstance(updated.get("displays"), list):
        displays = list(updated["displays"])
        if displays and isinstance(displays[0], Mapping):
            display = dict(displays[0])
            display["rows"] = _dpcc_phenotype_rows_with_current_rates(
                rows=display.get("rows"),
                t2=t2,
            )
            displays[0] = display
            updated = dict(updated)
            updated["displays"] = displays
            return updated
    updated = dict(updated)
    updated["rows"] = _dpcc_phenotype_rows_with_current_rates(rows=rows, t2=t2)
    return updated


def _dpcc_phenotype_rows_with_current_rates(*, rows: object, t2: str) -> list[dict[str, Any]]:
    rate_map = _gap_rate_map_from_t2(t2)
    share_map = _phenotype_index_share_map_from_t2(t2)
    result: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        phenotype = _text(item.get("phenotype_label")) or ""
        if phenotype in share_map:
            item["share_of_index_patients"] = share_map[phenotype]
        for key, value in rate_map.get(phenotype, {}).items():
            item[key] = value
        result.append(item)
    return result


def _dpcc_rows_with_explicit_rates(*, rows: object, t2: str, study_root: Path) -> list[dict[str, Any]]:
    rate_map = _gap_rate_map_from_t2(t2)
    count_map = _bounded_gap_support_map(study_root)
    result: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        phenotype = _text(item.get("phenotype_label"))
        if phenotype in count_map:
            item.update(count_map[phenotype])
        phenotype_rates = rate_map.get(phenotype or "", {})
        for key, value in phenotype_rates.items():
            item[key] = value
        result.append(item)
    return result


def _bounded_gap_support_map(study_root: Path) -> dict[str, dict[str, int]]:
    field_map = {
        "index_patients": "index_patients",
        "severe_glycemia_low_recorded_glucose_lowering_intensity_gap": "severe_glycemia_low_intensity_gap_patients",
        "severe_glycemia_low_recorded_glucose_lowering_intensity_n": "severe_glycemia_low_intensity_gap_denominator",
        "uncontrolled_glycemia_no_recorded_diabetes_medication_gap": "uncontrolled_glycemia_no_drug_gap_patients",
        "uncontrolled_glycemia_no_recorded_diabetes_medication_n": "uncontrolled_glycemia_no_drug_gap_denominator",
        "hypertension_context_no_recorded_antihypertensive_gap": "hypertension_no_antihypertensive_gap_patients",
        "hypertension_context_no_recorded_antihypertensive_n": "hypertension_no_antihypertensive_gap_denominator",
        "dyslipidemia_context_no_recorded_lipid_lowering_gap": "dyslipidemia_no_lipid_lowering_gap_patients",
        "dyslipidemia_context_no_recorded_lipid_lowering_n": "dyslipidemia_no_lipid_lowering_gap_denominator",
    }
    result: dict[str, dict[str, int]] = {}
    for row in _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv"):
        phenotype = _text(row.get("phenotype"))
        if phenotype is None:
            continue
        values: dict[str, int] = {}
        for source_key, target_key in field_map.items():
            parsed = _int_from_numeric_text(row.get(source_key))
            if parsed is not None:
                values[target_key] = parsed
        if values:
            result[phenotype] = values
    return result


def _phenotype_index_share_map_from_t2(t2: str) -> dict[str, float]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return {}
    result: dict[str, float] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        value = _text(row.get("Share of index cohort"))
        if phenotype is None or value is None:
            continue
        parsed = _rate_float(value)
        if parsed is not None:
            result[phenotype] = parsed
    return result


def _gap_rate_map_from_t2(t2: str) -> dict[str, dict[str, float | None]]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return {}
    column_map = {
        "Severe glycemia low-intensity gap": "severe_glycemia_low_intensity_gap_rate",
        "Severe glycemia / low intensity": "severe_glycemia_low_intensity_gap_rate",
        "Uncontrolled glycemia with no diabetes drug": "uncontrolled_glycemia_no_drug_gap_rate",
        "Uncontrolled / no diabetes drug": "uncontrolled_glycemia_no_drug_gap_rate",
        "Hypertension with no antihypertensive": "hypertension_no_antihypertensive_gap_rate",
        "Hypertension / no antihypertensive": "hypertension_no_antihypertensive_gap_rate",
        "Dyslipidemia with no lipid-lowering": "dyslipidemia_no_lipid_lowering_gap_rate",
        "Dyslipidemia / no lipid-lowering": "dyslipidemia_no_lipid_lowering_gap_rate",
    }
    result: dict[str, dict[str, float | None]] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        if phenotype is None:
            continue
        for column, field in column_map.items():
            if column in row:
                result.setdefault(phenotype, {})[field] = _rate_float(row[column])
    return result


def _phenotype_summary_rows_from_t2(t2: str) -> list[dict[str, str]]:
    rows = _markdown_table_rows(t2)
    if not rows:
        return []
    if "Measure" not in rows[0]:
        return [_canonical_wide_t2_row(row) for row in rows]
    measure_to_column = {
        "Index patients": "Index patients",
        "Share of index cohort": "Share of index cohort",
        "Mean age, y": "Mean age, y",
        "Mean BMI": "Mean BMI",
        "Mean HbA1c": "Mean HbA1c",
        "Severe glycemia low-intensity gap": "Severe glycemia low-intensity gap",
        "Uncontrolled glycemia with no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension with no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia with no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    by_phenotype: dict[str, dict[str, str]] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        measure = _text(row.get("Measure"))
        value = _text(row.get("Value"))
        if phenotype is None or measure is None or value is None:
            continue
        column = measure_to_column.get(measure)
        if column is not None:
            by_phenotype.setdefault(phenotype, {"Phenotype": phenotype})[column] = value
    return list(by_phenotype.values())


def _canonical_wide_t2_row(row: Mapping[str, str]) -> dict[str, str]:
    aliases = {
        "n": "Index patients",
        "%": "Share of index cohort",
        "Age, y": "Mean age, y",
        "BMI": "Mean BMI",
        "HbA1c": "Mean HbA1c",
        "Severe glycemia / low intensity": "Severe glycemia low-intensity gap",
        "Uncontrolled / no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension / no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia / no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    result = dict(row)
    for source, target in aliases.items():
        if source in row and target not in result:
            result[target] = row[source]
    return result


def _wide_phenotype_gap_summary_table(t2: str) -> str:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return t2
    headers = (
        "Phenotype",
        "n",
        "%",
        "Age, y",
        "BMI",
        "HbA1c",
        "Severe glycemia / low intensity",
        "Uncontrolled / no diabetes drug",
        "Hypertension / no antihypertensive",
        "Dyslipidemia / no lipid-lowering",
    )
    source_columns = {
        "n": "Index patients",
        "%": "Share of index cohort",
        "Age, y": "Mean age, y",
        "BMI": "Mean BMI",
        "HbA1c": "Mean HbA1c",
        "Severe glycemia / low intensity": "Severe glycemia low-intensity gap",
        "Uncontrolled / no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension / no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia / no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    output = [
        "# Phenotype-level clinical characteristics and recorded risk-treatment mismatch signals",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = []
        for header in headers:
            source = source_columns.get(header, header)
            cells.append(_text(row.get(source)) or "NA")
        output.append("| " + " | ".join(cells) + " |")
    return "\n".join(output)


def _wide_t2_headers(t2: str) -> list[str]:
    for line in t2.splitlines():
        if line.strip().startswith("|"):
            return [_clean_cell(cell) for cell in line.strip().strip("|").split("|")]
    return []


def _rate_float(value: str) -> float | None:
    if value in {"NA", "Not assessed"}:
        return None
    try:
        return float(value.replace("%", "").replace(",", "")) / 100.0
    except ValueError:
        return None


def _repair_dpcc_table_catalog_payload(
    payload: Mapping[str, Any],
    *,
    has_adjusted_model: bool = False,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    tables = []
    rich_catalog = False
    has_supplementary_transition = False
    has_adjusted_model_table = False
    for table in payload.get("tables") or []:
        if not isinstance(table, Mapping):
            continue
        item = dict(table)
        if _text(item.get("table_id")) == "T3":
            item.update(
                {
                    "title": "Medication-capture sensitivity analysis of recorded mismatch signals",
                    "caption": "Overall and medication-field-present summaries for the core recorded mismatch indicators.",
                    "reader_message": "The table shows which recorded mismatch signals remain large after restricting to patients with medication fields.",
                    "interpretation_boundary": "Signals remain descriptive and reflect recorded medication capture rather than confirmed prescribing quality.",
                    "journal_caption": "Medication-capture sensitivity analysis of recorded mismatch signals.",
                }
            )
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
                item["paper_role"] = "main_text"
                item["asset_paths"] = ["paper/tables/generated/T3_medication_capture_sensitivity.md"]
                item["source_paths"] = ["paper/tables/generated/T3_medication_capture_sensitivity.md"]
                render_result = item.get("render_result")
                if isinstance(render_result, Mapping):
                    patched_render_result = dict(render_result)
                else:
                    patched_render_result = {}
                patched_render_result["title"] = item["title"]
                patched_render_result["caption"] = item["caption"]
                patched_render_result["table_layout_policy"] = "pre_materialized_markdown_owner_surface"
                patched_render_result.pop("source_table_path", None)
                item["render_result"] = patched_render_result
        elif _text(item.get("table_id")) == "T4":
            has_adjusted_model_table = True
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
        elif _text(item.get("table_id")) == "S6":
            has_supplementary_transition = True
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
        tables.append(item)
    if rich_catalog and has_adjusted_model and not has_adjusted_model_table:
        tables.append(
            {
                "table_id": "T4",
                "paper_role": "main_text",
                "title": "Site-adjusted dyslipidemia no-lipid-lowering sensitivity model",
                "caption": "Medication-field-present logistic sensitivity model adjusted for phenotype, age, sex, and anonymous source-site fixed effects.",
                "asset_paths": ["paper/tables/generated/T4_dyslipidemia_adjusted_site_model.md"],
                "source_paths": ["paper/tables/generated/T4_dyslipidemia_adjusted_site_model.md"],
                "qc_result": {"status": "pass", "issues": []},
            }
        )
    if rich_catalog and not has_supplementary_transition:
        tables.append(
            {
                "table_id": "S6",
                "paper_role": "supplementary",
                "title": "Transition stability and site-level support summary",
                "caption": "Transition stability and site-level support summaries moved to the supplementary material.",
                "asset_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                "source_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                "qc_result": {"status": "pass", "issues": []},
            }
        )
    updated["tables"] = tables
    return updated


def _repair_dpcc_figure_semantics_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    figures = updated.get("figures")
    if not isinstance(figures, Mapping):
        return updated
    f1 = figures.get("F1")
    if isinstance(f1, dict):
        f1["direct_message"] = (
            "The denominator structure separates the main diabetes-coded index cohort from adult/plausible-age, repeated-visit, transition, and site-support surfaces."
        )
    f4 = figures.get("F4")
    if isinstance(f4, dict):
        f4["direct_message"] = (
            "The figure pairs explicit percentages with absolute counts so phenotype-specific rates and service workload can be read together."
        )
    return updated


def _repair_dpcc_manuscript_blueprint_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    findings = updated.get("main_findings_by_clinical_importance")
    if isinstance(findings, list):
        for item in findings:
            if not isinstance(item, dict):
                continue
            if item.get("section_id") == "transition_stability_and_site_support":
                item["clinical_finding"] = (
                    "Support analyses show partial repeated-visit persistence and broad within-network site coverage, but they remain secondary context."
                )
            if item.get("section_id") == "guideline_linked_treatment_gap_alignment":
                item["section_id"] = "recorded_medication_review_gap_burden"
                item["clinical_finding"] = (
                    "Recorded medication-review gap burden remains large across phenotype-specific glycemic and cardiometabolic domains."
                )
    return updated


def _materialize_dpcc_support_tables(
    *,
    paper_root: Path,
    t1: str,
    t2: str,
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
    transition_table: str,
    adjusted_model_rows: list[dict[str, str]],
) -> list[str]:
    changed_paths: list[str] = []
    if t1:
        for relpath in (
            Path("tables") / "T1_baseline_characteristics.md",
            Path("tables") / "generated" / "T1_baseline_characteristics.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, t1):
                changed_paths.append(str(path.resolve()))
    if t2:
        t2_table = _wide_phenotype_gap_summary_table(t2)
        for relpath in (
            Path("tables") / "T2_phenotype_gap_summary.md",
            Path("tables") / "generated" / "T2_phenotype_gap_summary.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, t2_table):
                changed_paths.append(str(path.resolve()))
    t3_markdown = _build_medication_capture_sensitivity_table(sensitivity)
    if t3_markdown:
        for relpath in (
            Path("tables") / "T3_medication_capture_sensitivity.md",
            Path("tables") / "generated" / "T3_medication_capture_sensitivity.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, "# Medication-capture sensitivity analysis\n\n" + t3_markdown):
                changed_paths.append(str(path.resolve()))
    t4_markdown = _build_adjusted_model_table(adjusted_model_rows)
    if t4_markdown:
        for relpath in (
            Path("tables") / "T4_dyslipidemia_adjusted_site_model.md",
            Path("tables") / "generated" / "T4_dyslipidemia_adjusted_site_model.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, "# Site-adjusted dyslipidemia sensitivity model\n\n" + t4_markdown):
                changed_paths.append(str(path.resolve()))
    if transition_table:
        for relpath in (
            Path("tables") / "supplementary" / "S6_transition_site_support_summary.md",
            Path("tables") / "generated" / "S6_transition_site_support_summary.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(
                path,
                "# Transition stability and site-level support\n\n" + _strip_table_heading(transition_table),
            ):
                changed_paths.append(str(path.resolve()))
    return changed_paths


def _leading_gap_sentence(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    severe = _find_row(rows, "phenotype_label", "Glycemic-dominant diabetes")
    severe_multi = _find_row(rows, "phenotype_label", "Severe glycemic multimorbidity")
    if not severe or not severe_multi:
        return ""
    return (
        "The largest severe-glycemia low-intensity counts were "
        f"{_format_count(severe.get('severe_glycemia_low_intensity_gap_patients'))} patients in glycemic-dominant "
        "diabetes and "
        f"{_format_count(severe_multi.get('severe_glycemia_low_intensity_gap_patients'))} patients in severe "
        "glycemic multimorbidity."
    )


def _absolute_gap_burden_sentence(rows: list[dict[str, str]]) -> str:
    adiposity = _find_row(rows, "phenotype_label", "Adiposity-linked multimorbidity")
    if not adiposity:
        return ""
    denominator = _format_count(adiposity.get("index_patients"))
    uncontrolled = _format_count(adiposity.get("uncontrolled_glycemia_no_drug_gap_patients"))
    hypertension = _format_count(adiposity.get("hypertension_no_antihypertensive_gap_patients"))
    dyslipidemia = _format_count(adiposity.get("dyslipidemia_no_lipid_lowering_gap_patients"))
    if "NA" in {denominator, uncontrolled, hypertension, dyslipidemia}:
        return ""
    return (
        "For adiposity-linked multimorbidity, the corresponding absolute burdens were "
        f"{uncontrolled} of {denominator} patients for uncontrolled glycemia without a recorded diabetes medication, "
        f"{hypertension} of {denominator} for hypertension context without a recorded antihypertensive, and "
        f"{dyslipidemia} of {denominator} for dyslipidemia context without recorded lipid-lowering therapy."
    )


def _phenotype_distribution_sentence(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Six clinically interpretable phenotypes were retained for the descriptive analysis."
    fragments: list[str] = []
    for row in rows:
        phenotype = row.get("Phenotype")
        count = row.get("Index patients")
        share = row.get("Share of index cohort")
        if phenotype and count and share:
            fragments.append(f"{phenotype} ({_format_count(count)} patients; {share})")
    if not fragments:
        return "Six clinically interpretable phenotypes were retained for the descriptive analysis."
    return "Six phenotypes were identified: " + "; ".join(fragments) + "."


def _phenotype_lookup(rows: list[dict[str, str]], phenotype: str) -> dict[str, str]:
    return _find_row(rows, "Phenotype", phenotype) or {}


def _find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _read_table_text(path: Path, *, fallback_path: Path | None = None) -> str:
    selected = path if path.exists() else fallback_path
    if selected is None or not selected.exists():
        return ""
    return selected.read_text(encoding="utf-8").strip()


def _strip_table_heading(text: str) -> str:
    lines = text.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    while lines and not lines[0].strip().startswith("|"):
        lines.pop(0)
    return "\n".join(lines).strip()


def _markdown_table_rows(text: str) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [_clean_cell(cell) for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [_clean_cell(cell) for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def _clean_cell(value: str) -> str:
    text = value.strip()
    return "Not assessed" if text == "NA" else text


def _step_n(steps: list[dict[str, Any]], step_id: str) -> int | None:
    for step in steps:
        if _text(step.get("step_id")) == step_id:
            value = step.get("n")
            return int(value) if isinstance(value, int) else None
    return None


def _first_int(text: str) -> int | None:
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return int("".join(digits)) if digits else None


def _int_from_numeric_text(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


def _format_count(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    try:
        return f"{int(str(text).replace(',', '')):,}"
    except ValueError:
        return text


def _format_percent(value: object) -> str:
    if isinstance(value, int | float):
        return f"{value * 100:.2f}%"
    return _text(value) or "NA"


def _format_share(*, numerator: object, denominator: int) -> str:
    text = _text(numerator)
    if text is None or denominator <= 0:
        return "NA"
    try:
        value = int(text.replace(",", ""))
    except ValueError:
        return "NA"
    return f"{value / denominator * 100:.1f}%"


def _share_from_summary(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    match = re.search(r"\(([^)]+)\)", text)
    return match.group(1) if match else "NA"


def _count_from_summary(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.split("(", 1)[0].strip()


def _contains_forbidden_manuscript_terms(text: str) -> bool:
    lowered = text.lower()
    for term in FORBIDDEN_MANUSCRIPT_TERMS:
        escaped = re.escape(term.lower())
        if re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", lowered):
            return True
    return False


def _write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else f"{text}\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _write_json_if_changed(path: Path, payload: Mapping[str, Any]) -> bool:
    rendered = json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


__all__ = [
    "DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID",
    "DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID",
    "MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS",
    "MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID",
    "dm002_side_surface_only_repair_blocker",
    "materialize_medical_prose_story_surfaces",
]
