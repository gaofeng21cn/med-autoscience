from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers.medical_prose_story_surface.common import (
    FORBIDDEN_MANUSCRIPT_TERMS,
    _contains_forbidden_manuscript_terms,
    _mapping,
    _sha256_bytes,
    _text,
    _write_json_if_changed,
    _write_text_if_changed,
)
from med_autoscience.controllers.medical_prose_story_surface.dpcc_display_repairs import (
    DPCC_DISPLAY_TEXT_REPLACEMENTS,
    _materialize_dpcc_display_metadata_repairs,
)
from med_autoscience.controllers.medical_prose_story_surface.dpcc_manuscript import (
    _medical_prose_manuscript_from_canonical_surfaces,
)
from med_autoscience.controllers.medical_prose_story_surface.dpcc_tables import (
    _adjusted_model_values,
    _apply_bounded_t2_revisions,
    _bounded_table_rows,
    _build_adjusted_model_table,
    _format_adjusted_or_ci,
    _medication_sensitivity_values,
    _read_supplementary_tables_text,
    _study_root_from_paper_root,
    _supplementary_table_rows,
    _wide_phenotype_gap_summary_table,
)
from med_autoscience.controllers.medical_prose_story_surface.dm002_external_validation import (
    DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID,
    DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS,
    DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
    DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID,
    materialize_dm002_external_validation_story_surface,
)
from med_autoscience.controllers.medical_prose_story_surface.eval_bound_currentness import (
    eval_bound_current_story_delta_blocker,
    eval_bound_current_story_delta_refs,
    eval_bound_current_story_delta_is_preservable,
)
from med_autoscience.controllers.medical_prose_story_surface.writer_delta_preservation import (
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
    "lipid-lowering prevention gap persistence",
    "lipid-lowering prevention gap remained large",
    "renal-risk signal secondary/exploratory",
    "reduce renal-risk prominence",
    "rate-count contrast",
    "rate-count priority map",
    "proportional risk vs absolute workload",
    "effect-size caveat",
    "modest effect-size caveat",
    "site fixed-effect model",
    "soften future-work wording",
    "shorten abstract",
)
DM003_REVIEWER_REVISION_CURRENT_MARKERS = (
    "lipid-lowering prevention gaps remained large after medication-field restriction",
    "A 2025 index-year sensitivity analysis still showed a large exploratory renal-risk",
    "Effect sizes were modest",
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
    reviewer_revision_context: Mapping[str, Any] | None = None,
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
            artifact_changed_paths = _materialize_dpcc_display_metadata_repairs(paper_root=paper_root)
            return [
                str((paper_root / relpath).resolve())
                for relpath in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS
                if (paper_root / relpath).exists()
            ] + artifact_changed_paths
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
    reviewer_revision_context: Mapping[str, Any] | None = None,
) -> bool:
    if study_root is None or work_unit_id != MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID:
        return False
    resolved_study_root = Path(study_root).expanduser().resolve()
    if resolved_study_root.name != "003-dpcc-primary-care-phenotype-treatment-gap":
        return False
    latest_task_intake = _task_intake_payload_from_context(
        reviewer_revision_context=reviewer_revision_context,
        study_root=resolved_study_root,
    )
    if not task_intake_is_reviewer_revision(latest_task_intake):
        return False
    corpus = _task_intake_corpus(latest_task_intake, reviewer_revision_context=reviewer_revision_context)
    if not _dm003_reviewer_revision_requests_story_refresh(corpus):
        return False
    for path in _current_story_surface_paths(paper_root=paper_root):
        if _story_surface_missing_any_marker(Path(path), DM003_REVIEWER_REVISION_CURRENT_MARKERS):
            return True
        if _story_surface_contains_any_marker(Path(path), DM003_STALE_REVIEWER_REVISION_MARKERS):
            return True
    return False


def _task_intake_payload_from_context(
    *,
    reviewer_revision_context: Mapping[str, Any] | None,
    study_root: Path,
) -> dict[str, Any]:
    context = dict(reviewer_revision_context) if isinstance(reviewer_revision_context, Mapping) else {}
    payload = read_latest_task_intake(study_root=study_root)
    if payload:
        return payload
    if not context:
        return {}
    return {
        "task_intake_kind": context.get("task_intake_kind"),
        "task_id": context.get("task_id"),
        "task_intent": context.get("task_intent"),
        "trusted_inputs": context.get("trusted_inputs") or [],
    }


def _dm003_reviewer_revision_requests_story_refresh(corpus: str) -> bool:
    if any(marker in corpus for marker in DM003_REVIEWER_REVISION_MARKERS):
        return True
    token_groups = (
        ("abstract", ("shorten", "compress", "tighten", "15%", "20%")),
        ("renal-risk", ("de-emphasis", "downgrade", "secondary", "exploratory", "prominence")),
        ("figure 4", ("rate-count", "priority map")),
        ("effect", ("modest", "supportive")),
        ("lipid-lowering", ("medication-field", "site adjustment", "site-adjusted", "persistent")),
    )
    return any(anchor in corpus and any(token in corpus for token in tokens) for anchor, tokens in token_groups)


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


def _task_intake_corpus(
    payload: Mapping[str, Any] | None,
    *,
    reviewer_revision_context: Mapping[str, Any] | None = None,
) -> str:
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
    trusted_inputs = [*_text_list(mapping.get("trusted_inputs"))]
    context = dict(reviewer_revision_context) if isinstance(reviewer_revision_context, Mapping) else {}
    trusted_inputs.extend(_text_list(context.get("trusted_inputs")))
    for path_text in _dedupe_text(trusted_inputs):
        path = Path(path_text).expanduser()
        if path.exists() and path.is_file():
            try:
                values.append(path.read_text(encoding="utf-8")[:12000])
            except OSError:
                continue
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


def _story_surface_missing_any_marker(path: Path, markers: tuple[str, ...]) -> bool:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return True
    try:
        text = resolved.read_text(encoding="utf-8").lower()
    except OSError:
        return True
    return any(marker.lower() not in text for marker in markers)


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _dedupe_text(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


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






























































































































































































__all__ = [
    "DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID",
    "DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID",
    "MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS",
    "MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID",
    "dm002_side_surface_only_repair_blocker",
    "materialize_medical_prose_story_surfaces",
]
