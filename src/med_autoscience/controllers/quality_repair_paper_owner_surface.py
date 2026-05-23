from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.medical_manuscript_blueprint import validate_medical_manuscript_blueprint
from med_autoscience.medical_prose_review import validate_medical_prose_review
from med_autoscience.profiles import WorkspaceProfile


_CANONICAL_PAPER_OWNER_REQUIRED_SURFACES = (
    Path("paper_bundle_manifest.json"),
    Path("draft.md"),
    Path("medical_manuscript_blueprint.json"),
    Path("medical_prose_review.json"),
    Path("claim_evidence_map.json"),
    Path("display_registry.json"),
    Path("results_narrative_map.json"),
    Path("figure_semantics_manifest.json"),
    Path("figures/figure_catalog.json"),
    Path("tables/table_catalog.json"),
)
_CANONICAL_PAPER_OWNER_PROJECTION_INPUT_SURFACES = tuple(
    relpath for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES if relpath != Path("display_registry.json")
)
_AI_AUTHORIZED_CANONICAL_PAPER_SURFACES = frozenset(
    {
        Path("medical_manuscript_blueprint.json"),
        Path("medical_prose_review.json"),
    }
)
_DERIVED_CANONICAL_PAPER_SURFACES = frozenset(
    {
        Path("results_narrative_map.json"),
        Path("figure_semantics_manifest.json"),
    }
)
_HYDRATION_PAPER_OWNER_INPUT_SURFACES = (
    Path("medical_analysis_contract.json"),
    Path("medical_reporting_contract.json"),
    Path("display_registry.json"),
    Path("reference_coverage_report.json"),
    Path("references.bib"),
)
_HYDRATION_PAPER_OWNER_INPUT_GLOBS = (
    "figures/*.shell.json",
    "tables/*.shell.json",
)


def prepare_canonical_paper_owner_surface_for_upstream_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    gate_state: Any,
    authority_route_gate: Mapping[str, Any],
) -> dict[str, Any]:
    if _non_empty_text(authority_route_gate.get("action")) != "paper_write":
        return {"status": "not_applicable", "reason": "route_action_not_paper_write"}

    canonical_paper_root = Path(study_root).expanduser().resolve() / "paper"
    if getattr(gate_state, "paper_root", None) is not None:
        existing_paper_root = Path(getattr(gate_state, "paper_root"))
        surface_results = [
            _copy_or_initialize_canonical_paper_surface(
                source_root=existing_paper_root,
                target_root=canonical_paper_root,
                relpath=relpath,
                study_id=study_id,
                quest_id=quest_id,
            )
            for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES
            if not (canonical_paper_root / relpath).exists()
        ]
        return {
            "status": "repaired_existing" if surface_results else "already_complete",
            "paper_root": str(canonical_paper_root),
            "surface_results": surface_results,
        }

    if _canonical_paper_owner_surface_complete(canonical_paper_root):
        return {"status": "already_complete", "paper_root": str(canonical_paper_root)}

    quest_root = profile.managed_runtime_quests_root / quest_id
    projected_paper_root = quest_root / "paper"
    canonical_projection_inputs = [
        projected_paper_root / relpath
        for relpath in _CANONICAL_PAPER_OWNER_PROJECTION_INPUT_SURFACES
        if (projected_paper_root / relpath).is_file()
    ]
    hydration_projection_inputs = _hydration_paper_owner_projection_inputs(projected_paper_root)
    if not canonical_projection_inputs and not hydration_projection_inputs:
        return {
            "status": "blocked_missing_projection",
            "paper_root": str(canonical_paper_root),
            "quest_projection_root": str(projected_paper_root.resolve()),
            "missing_reason": "quest paper projection has no canonical owner-surface inputs",
        }
    projection_input_status = (
        "canonical_projection_present"
        if canonical_projection_inputs
        else "hydration_projection_present"
    )
    surface_results = [
        _copy_or_initialize_canonical_paper_surface(
            source_root=projected_paper_root,
            target_root=canonical_paper_root,
            relpath=relpath,
            study_id=study_id,
            quest_id=quest_id,
        )
        for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES
    ]
    for dirname in ("build", "review", "submission_minimal"):
        (canonical_paper_root / dirname).mkdir(parents=True, exist_ok=True)

    manifest_payload = _read_json_object(canonical_paper_root / "paper_bundle_manifest.json")
    paper_branch = _non_empty_text(manifest_payload.get("paper_branch")) or "paper/main"
    paper_line_state_path = canonical_paper_root / "paper_line_state.json"
    if not paper_line_state_path.exists():
        _write_json(
            paper_line_state_path,
            {
                "schema_version": 1,
                "paper_branch": paper_branch,
                "paper_root": str(canonical_paper_root),
                "surface_owner": "study_canonical_paper_owner_surface",
                "controller": "quality_repair_batch",
                "study_id": study_id,
                "quest_id": quest_id,
            },
        )
        surface_results.append({"relative_path": "paper_line_state.json", "status": "initialized_owner_state"})

    missing_surfaces = _canonical_paper_owner_missing_surfaces(canonical_paper_root)
    blocked_source_surfaces = _blocked_canonical_source_surfaces(surface_results)
    blocked_authorized_inputs = bool(blocked_source_surfaces) or any(
        relative_path
        in {
            "paper/medical_manuscript_blueprint.json",
            "paper/medical_prose_review.json",
            "paper/results_narrative_map.json",
            "paper/figure_semantics_manifest.json",
        }
        for relative_path in missing_surfaces
    )
    status = (
        "blocked_missing_authorized_canonical_inputs"
        if blocked_authorized_inputs
        else "materialized"
        if _canonical_paper_owner_routable(canonical_paper_root)
        else "blocked_missing_authorized_canonical_inputs"
    )
    return {
        "status": status,
        "paper_root": str(canonical_paper_root),
        "quest_projection_root": str(projected_paper_root.resolve()),
        "projection_input_status": projection_input_status,
        "projection_input_count": len(canonical_projection_inputs) + len(hydration_projection_inputs),
        "missing_canonical_surfaces": missing_surfaces,
        "blocked_canonical_source_surfaces": blocked_source_surfaces,
        "surface_results": surface_results,
    }


def _canonical_paper_owner_surface_complete(paper_root: Path) -> bool:
    return all((paper_root / relpath).exists() for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES)


def _canonical_paper_owner_routable(paper_root: Path) -> bool:
    return (paper_root / "paper_bundle_manifest.json").exists() and (paper_root / "draft.md").exists()


def _canonical_paper_owner_missing_surfaces(paper_root: Path) -> list[str]:
    return [
        f"paper/{relpath.as_posix()}"
        for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES
        if not (paper_root / relpath).exists()
    ]


def _blocked_canonical_source_surfaces(surface_results: list[Mapping[str, Any]]) -> list[str]:
    return [
        f"paper/{relative_path}"
        for item in surface_results
        if _non_empty_text(item.get("status")) == "blocked_invalid_canonical_source"
        and (relative_path := _non_empty_text(item.get("relative_path"))) is not None
    ]


def _hydration_paper_owner_projection_inputs(projected_paper_root: Path) -> list[Path]:
    inputs = [projected_paper_root / relpath for relpath in _HYDRATION_PAPER_OWNER_INPUT_SURFACES]
    for pattern in _HYDRATION_PAPER_OWNER_INPUT_GLOBS:
        inputs.extend(sorted(projected_paper_root.glob(pattern)))
    return [path for path in inputs if path.is_file()]


def _default_canonical_paper_json_surface(
    *,
    relpath: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Any]:
    if relpath == Path("paper_bundle_manifest.json"):
        return {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "owner_surface": {
                "status": "initialized_for_controller_quality_repair",
                "controller": "quality_repair_batch",
                "study_id": study_id,
                "quest_id": quest_id,
            },
        }
    if relpath == Path("claim_evidence_map.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "claims": []}
    if relpath == Path("display_registry.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "displays": []}
    if relpath == Path("figures/figure_catalog.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "figures": []}
    if relpath == Path("tables/table_catalog.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "tables": []}
    return {"schema_version": 1, "status": "owner_surface_initialized"}


def _copy_or_initialize_canonical_paper_surface(
    *,
    source_root: Path,
    target_root: Path,
    relpath: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Any]:
    target_path = target_root / relpath
    if target_path.exists():
        return {"relative_path": relpath.as_posix(), "status": "already_present"}
    source_path = source_root / relpath
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.exists() and source_path.is_file():
        if validation_errors := _canonical_source_validation_errors(source_path=source_path, relpath=relpath):
            return {
                "relative_path": relpath.as_posix(),
                "status": "blocked_invalid_canonical_source",
                "source_path": str(source_path.resolve()),
                "validation_errors": validation_errors,
            }
        shutil.copy2(source_path, target_path)
        return {
            "relative_path": relpath.as_posix(),
            "status": "copied_from_quest_projection",
            "source_path": str(source_path.resolve()),
        }
    if relpath in _AI_AUTHORIZED_CANONICAL_PAPER_SURFACES:
        return {
            "relative_path": relpath.as_posix(),
            "status": "blocked_ai_authorized_canonical_surface_required",
            "target_path": str(target_path),
        }
    if relpath in _DERIVED_CANONICAL_PAPER_SURFACES:
        return {
            "relative_path": relpath.as_posix(),
            "status": "blocked_canonical_projection_required",
            "target_path": str(target_path),
        }
    if relpath == Path("draft.md"):
        target_path.write_text(
            "# Manuscript Draft\n\nCanonical paper owner surface initialized for controller-owned quality repair.\n",
            encoding="utf-8",
        )
        return {"relative_path": relpath.as_posix(), "status": "initialized_owner_shell"}
    _write_json(
        target_path,
        _default_canonical_paper_json_surface(relpath=relpath, study_id=study_id, quest_id=quest_id),
    )
    return {"relative_path": relpath.as_posix(), "status": "initialized_owner_shell"}


def _canonical_source_validation_errors(*, source_path: Path, relpath: Path) -> list[str]:
    if relpath == Path("medical_manuscript_blueprint.json"):
        return validate_medical_manuscript_blueprint(_read_json_object(source_path))
    if relpath == Path("medical_prose_review.json"):
        return validate_medical_prose_review(_read_json_object(source_path))
    return []


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["prepare_canonical_paper_owner_surface_for_upstream_repair"]
