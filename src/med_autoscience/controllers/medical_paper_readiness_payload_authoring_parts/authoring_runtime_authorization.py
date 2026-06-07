from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.ai_reviewer_journal_loop import (
    build_authoring_runtime_authorization,
)
from med_autoscience.policies import publication_critique


DEFAULT_CALIBRATION_CASE_REFS = (
    "ai_reviewer_calibration_corpus#thin_first_draft",
    "ai_reviewer_calibration_corpus#overstrong_claim",
)


def payload_from_authoring_runtime_authorization_sources(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    target_layer_path = publication_critique.stable_target_journal_writing_layer_path(study_root=root)
    target_layer = _read_target_layer(root)
    if not target_layer:
        return {}
    publication_eval_path = root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = _read_json(publication_eval_path)
    if not publication_eval:
        return {}
    evidence_ledger_ref = _first_existing_ref(_evidence_ledger_candidates(root), root=root)
    review_ledger_ref = _first_existing_ref(_review_ledger_candidates(root), root=root)
    if not evidence_ledger_ref or not review_ledger_ref:
        return {}
    claim_map = _claim_to_paragraph_map(
        target_layer,
        evidence_ledger_ref=evidence_ledger_ref,
        review_ledger_ref=review_ledger_ref,
    )
    display_map = _display_to_claim_map(
        target_layer,
        evidence_ledger_ref=evidence_ledger_ref,
    )
    restrained_strategy = _mapping(target_layer.get("restrained_language_strategy"))
    if not claim_map.get("claims") or not display_map.get("links") or not restrained_strategy:
        return {}
    payload = {
        "target_journal_writing_layer": dict(target_layer),
        "claim_to_paragraph_map": claim_map,
        "display_to_claim_map": display_map,
        "restrained_language_strategy": restrained_strategy,
        "evidence_ledger_ref": evidence_ledger_ref,
        "review_ledger_ref": review_ledger_ref,
        "publication_eval": dict(publication_eval),
        "calibration_case_refs": list(DEFAULT_CALIBRATION_CASE_REFS),
        "payload_source": source,
        "source_basis": "target_journal_layer_publication_eval_and_ledgers",
        "source_refs": [
            str(target_layer_path),
            str(publication_eval_path),
            _absolute_ref(root=root, ref=evidence_ledger_ref),
            _absolute_ref(root=root, ref=review_ledger_ref),
        ],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    try:
        build_authoring_runtime_authorization(**_payload_without_authoring_metadata(payload))
    except (TypeError, ValueError):
        return {}
    return payload


def _read_target_layer(root: Path) -> dict[str, Any]:
    try:
        return dict(publication_critique.read_target_journal_writing_layer(study_root=root))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _claim_to_paragraph_map(
    target_layer: Mapping[str, Any],
    *,
    evidence_ledger_ref: str,
    review_ledger_ref: str,
) -> dict[str, list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    for index, item in enumerate(_mapping_list(target_layer.get("claim_to_paragraph_map"))):
        claim_id = _text(item.get("claim_id")) or f"claim-{index + 1}"
        paragraph_id = _text(item.get("paragraph_id")) or _paragraph_id(item, claim_id=claim_id)
        evidence_refs = _ledger_refs(
            item.get("evidence_refs"),
            ledger_ref=evidence_ledger_ref,
            fallback_id=claim_id,
        )
        reviewer_refs = _ledger_refs(
            item.get("reviewer_concern_refs"),
            ledger_ref=review_ledger_ref,
            fallback_id=_text(item.get("reviewer_concern_id")) or claim_id,
        )
        if not claim_id or not paragraph_id or not evidence_refs or not reviewer_refs:
            continue
        claims.append(
            {
                "claim_id": claim_id,
                "paragraph_id": paragraph_id,
                "evidence_refs": evidence_refs,
                "reviewer_concern_refs": reviewer_refs,
            }
        )
    return {"claims": claims}


def _display_to_claim_map(
    target_layer: Mapping[str, Any],
    *,
    evidence_ledger_ref: str,
) -> dict[str, list[dict[str, Any]]]:
    links_by_display: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(_mapping_list(target_layer.get("display_to_claim_map"))):
        display_id = _text(item.get("display_id")) or f"display-{index + 1}"
        claim_ids = _claim_ids(item)
        evidence_fallback_id = _text(item.get("evidence_id")) or display_id
        evidence_refs = _ledger_refs(
            item.get("evidence_refs"),
            ledger_ref=evidence_ledger_ref,
            fallback_id=evidence_fallback_id,
        )
        if not display_id or not claim_ids or not evidence_refs:
            continue
        existing = links_by_display.get(display_id)
        if existing is None:
            links_by_display[display_id] = {
                "display_id": display_id,
                "claim_ids": claim_ids,
                "evidence_refs": evidence_refs,
            }
            continue
        existing["claim_ids"] = _dedupe([*existing["claim_ids"], *claim_ids])
        existing["evidence_refs"] = _dedupe([*existing["evidence_refs"], *evidence_refs])
    return {"links": list(links_by_display.values())}


def _paragraph_id(item: Mapping[str, Any], *, claim_id: str) -> str:
    section = _slug(_text(item.get("section")) or "results")
    role = _slug(_text(item.get("paragraph_role")) or "claim")
    return f"{section}-{role}-{_slug(claim_id)}"


def _claim_ids(item: Mapping[str, Any]) -> list[str]:
    claim_ids = _text_list(item.get("claim_ids"))
    claim_id = _text(item.get("claim_id"))
    if claim_id:
        claim_ids.append(claim_id)
    return _dedupe(claim_ids)


def _ledger_refs(value: object, *, ledger_ref: str, fallback_id: str) -> list[str]:
    refs = [ref for ref in _text_list(value) if _ref_targets_ledger(ref, ledger_ref)]
    if not refs:
        refs = [f"{ledger_ref}#{_slug(fallback_id)}"]
    return _dedupe(refs)


def _ref_targets_ledger(ref: str, ledger_ref: str) -> bool:
    return ref == ledger_ref or ref.startswith(f"{ledger_ref}#")


def _first_existing_ref(paths: tuple[Path, ...], *, root: Path) -> str:
    for path in paths:
        if _read_json(path):
            return str(path.relative_to(root))
    return ""


def _evidence_ledger_candidates(root: Path) -> tuple[Path, ...]:
    return (
        root / "paper" / "evidence_ledger.json",
        root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "evidence_ledger.json",
        root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "manuscript"
        / "audit"
        / "evidence_ledger.json",
        root / "artifacts" / "evidence_ledger.json",
    )


def _review_ledger_candidates(root: Path) -> tuple[Path, ...]:
    return (
        root / "paper" / "review" / "review_ledger.json",
        root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "review"
        / "review_ledger.json",
        root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "manuscript"
        / "review"
        / "review_ledger.json",
        root / "artifacts" / "review_ledger.json",
    )


def _absolute_ref(*, root: Path, ref: str) -> str:
    path = Path(ref)
    if path.is_absolute():
        return str(path)
    return str(root / path)


def _payload_without_authoring_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata_keys = {
        "payload_source",
        "source_basis",
        "source_refs",
        "quality_claim_authorized",
        "mechanical_projection_can_authorize_quality",
    }
    return {key: value for key, value in dict(payload).items() if key not in metadata_keys}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text_list(value: object) -> list[str]:
    return [_text(item) for item in value if _text(item)] if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _slug(value: object) -> str:
    text = _text(value).lower()
    rendered = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    while "--" in rendered:
        rendered = rendered.replace("--", "-")
    return rendered or "ref"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = ["payload_from_authoring_runtime_authorization_sources"]
