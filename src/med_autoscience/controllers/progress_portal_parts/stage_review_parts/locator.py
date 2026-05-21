from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.progress_portal_parts.source_refs import source_ref_allowed


def stage_review_locator_projection(
    progress: Mapping[str, Any],
    *,
    study_id: str,
    study_root: str | Path | None,
) -> dict[str, Any]:
    explicit = _explicit_stage_review(progress)
    explicit_locator = _mapping(explicit.get("artifact_locator"))
    explicit_index_ref = _non_empty_text(explicit.get("deliverable_index_ref"))
    resolved_study_root = _study_root(progress, study_root)
    index_ref = (
        _non_empty_text(explicit_locator.get("stage_deliverable_index"))
        or _non_empty_text(explicit_locator.get("stage_deliverable_index_ref"))
        or explicit_index_ref
        or "artifacts/stage_reviews/index.json"
    )
    index_path = _resolve_locator_path(index_ref, study_root=resolved_study_root, study_id=study_id)
    if index_path is None or not index_path.is_file():
        return {}
    try:
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(index_payload, Mapping):
        return {}
    index = dict(index_payload)
    index_study_id = _non_empty_text(index.get("study_id"))
    if index_study_id and index_study_id != study_id:
        return {
            "study_id": index_study_id,
            "deliverable_index_ref": _workspace_ref(index_path, study_root=resolved_study_root),
            "paper_line_index_proof": _paper_line_index_proof(
                index,
                index_path=index_path,
                study_root=resolved_study_root,
                status="conflict",
            ),
        }
    latest_review_page_ref = review_page_ref(index) or _non_empty_text(
        _mapping(index.get("artifact_locator")).get("latest_review_page")
    )
    latest_review_page_path = _resolve_locator_path(
        latest_review_page_ref,
        study_root=resolved_study_root,
        study_id=study_id,
    )
    paper_line_workspace_proof = _paper_line_workspace_proof(
        _mapping(index.get("paper_line_workspace_proof")),
        study_root=resolved_study_root,
        study_id=study_id,
    )
    normalized_source_refs = _dedupe_refs(
        [
            *_string_list(index.get("source_refs")),
            _workspace_ref(index_path, study_root=resolved_study_root),
            _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
            if latest_review_page_path is not None
            else latest_review_page_ref,
            *paper_line_workspace_proof_refs(paper_line_workspace_proof),
        ]
    )
    normalized: dict[str, Any] = {
        **index,
        "stage": _non_empty_text(index.get("stage")) or _non_empty_text(index.get("current_stage")),
        "review_page_ref": _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
        if latest_review_page_path is not None
        else latest_review_page_ref,
        "deliverable_index_ref": _workspace_ref(index_path, study_root=resolved_study_root),
        "source_refs": normalized_source_refs,
        "paper_line_index_proof": _paper_line_index_proof(
            index,
            index_path=index_path,
            study_root=resolved_study_root,
            status="available",
        ),
        "latest_review_page_proof": _latest_review_page_proof(
            latest_review_page_path,
            latest_review_page_ref=latest_review_page_ref,
            study_root=resolved_study_root,
        ),
        "artifact_locator": {
            "study_root": str(resolved_study_root) if resolved_study_root is not None else None,
            "stage_deliverable_index": _workspace_ref(index_path, study_root=resolved_study_root),
            "latest_review_page": _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
            if latest_review_page_path is not None
            else latest_review_page_ref,
            "body_included": False,
            "read_only": True,
        },
    }
    if paper_line_workspace_proof:
        normalized["paper_line_workspace_proof"] = paper_line_workspace_proof
    return normalized


def paper_line_workspace_proof_refs(proof: Mapping[str, Any]) -> list[str]:
    locators = _mapping(proof.get("locators"))
    if locators:
        return [
            ref
            for locator in locators.values()
            for ref in [_non_empty_text(_mapping(locator).get("ref"))]
            if ref is not None
        ]
    return _string_list(proof.get("source_refs"))


def paper_line_workspace_proof_available(proof: Mapping[str, Any]) -> bool:
    return _non_empty_text(proof.get("status")) == "available" and not _string_list(proof.get("missing"))


def review_page_ref(value: Mapping[str, Any]) -> str | None:
    latest = _mapping(value.get("latest_review_page"))
    return (
        _non_empty_text(value.get("review_page_ref"))
        or _non_empty_text(value.get("latest_review_page_ref"))
        or _non_empty_text(latest.get("ref"))
    )


def _explicit_stage_review(progress: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "stage_deliverable_review",
        "stage_review_index",
        "stage_review_page",
    ):
        value = _mapping(progress.get(key))
        if value:
            return value
    return {}


def _study_root(progress: Mapping[str, Any], study_root: str | Path | None) -> Path | None:
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    refs = _mapping(progress.get("refs"))
    for value in (
        progress.get("study_root"),
        refs.get("study_root"),
        refs.get("quest_root"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            return Path(text).expanduser().resolve()
    return None


def _resolve_locator_path(
    ref: str | None,
    *,
    study_root: Path | None,
    study_id: str,
) -> Path | None:
    if ref is None:
        return None
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    if study_root is None:
        return None
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "studies" and parts[1] == study_id:
        return (study_root.parent.parent / path).resolve()
    if parts and parts[0] == "artifacts":
        return (study_root / path).resolve()
    return (study_root / path).resolve()


def _workspace_ref(path: Path | None, *, study_root: Path | None) -> str | None:
    if path is None:
        return None
    if study_root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(study_root.parent.parent.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(study_root.resolve()))
        except ValueError:
            return str(path)


def _paper_line_index_proof(
    index: Mapping[str, Any],
    *,
    index_path: Path,
    study_root: Path | None,
    status: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_deliverable_index_locator_proof",
        "status": status,
        "index_ref": _workspace_ref(index_path, study_root=study_root),
        "index_surface_kind": _non_empty_text(index.get("surface_kind")),
        "stage": _non_empty_text(index.get("stage")) or _non_empty_text(index.get("current_stage")),
        "source_refs": _dedupe_refs(_string_list(index.get("source_refs"))),
        "body_included": False,
        "read_only": True,
        "writes_authority_surface": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def _latest_review_page_proof(
    latest_review_page_path: Path | None,
    *,
    latest_review_page_ref: str | None,
    study_root: Path | None,
) -> dict[str, Any]:
    ref = (
        _workspace_ref(latest_review_page_path, study_root=study_root)
        if latest_review_page_path is not None
        else latest_review_page_ref
    )
    return {
        "surface_kind": "mas_stage_deliverable_review_page_locator_proof",
        "status": "available" if latest_review_page_path is not None and latest_review_page_path.is_file() else "missing",
        "latest_review_page_ref": ref,
        "body_included": False,
        "read_only": True,
        "writes_authority_surface": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def _paper_line_workspace_proof(
    proof: Mapping[str, Any],
    *,
    study_root: Path | None,
    study_id: str,
) -> dict[str, Any]:
    if not proof:
        return {}
    locators = {
        "evidence_ledger": _proof_locator(proof, "evidence_ledger_ref", study_root=study_root, study_id=study_id),
        "review_ledger": _proof_locator(proof, "review_ledger_ref", study_root=study_root, study_id=study_id),
        "publication_eval": _proof_locator(proof, "publication_eval_ref", study_root=study_root, study_id=study_id),
        "controller_decision": _proof_locator(proof, "controller_decision_ref", study_root=study_root, study_id=study_id),
        "artifact_freshness": _proof_locator(proof, "artifact_freshness_ref", study_root=study_root, study_id=study_id),
        "package_proof": _proof_locator(proof, "package_proof_ref", study_root=study_root, study_id=study_id),
    }
    missing = [role for role, locator in locators.items() if locator["status"] != "available"]
    return {
        "surface_kind": "mas_paper_line_workspace_locator_proof",
        "schema_version": 1,
        "status": "available" if not missing else "missing",
        "missing": missing,
        "locators": locators,
        "source_refs": _dedupe_refs(locator["ref"] for locator in locators.values()),
        "body_included": False,
        "read_only": True,
        "authority": _authority_boundary(),
    }


def _proof_locator(
    proof: Mapping[str, Any],
    key: str,
    *,
    study_root: Path | None,
    study_id: str,
) -> dict[str, Any]:
    ref = _non_empty_text(proof.get(key))
    path = _resolve_locator_path(ref, study_root=study_root, study_id=study_id)
    normalized_ref = _workspace_ref(path, study_root=study_root) if path is not None else ref
    return {
        "ref": normalized_ref,
        "status": "available" if path is not None and path.is_file() else "missing",
        "body_included": False,
        "read_only": True,
        "writes_authority_surface": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "kind": "read_only_stage_review_projection",
        "writes_authority_surface": False,
        "truth_owner": "MedAutoScience",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
        "can_authorize_artifact_authority": False,
        "human_review_blocks_auto_advance_by_default": False,
    }


def _dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _non_empty_text(value)
        if text is None or text in seen or not source_ref_allowed(text):
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None:
            result.append(text)
    return result


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "paper_line_workspace_proof_available",
    "paper_line_workspace_proof_refs",
    "review_page_ref",
    "stage_review_locator_projection",
]
