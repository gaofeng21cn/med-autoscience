from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


AI_REVIEWER_REQUIRED_INPUT_SURFACES = (
    "manuscript",
    "evidence_ledger",
    "review_ledger",
    "study_charter",
    "medical_manuscript_blueprint",
    "claim_evidence_map",
    "medical_prose_review",
    "publication_gate_projection",
)
AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES = (
    Path("paper/draft.md"),
    Path("paper/manuscript.md"),
    Path("paper/build/review_manuscript.md"),
)
AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES = (
    Path("artifacts/publication_eval/medical_prose_review.json"),
    Path("paper/medical_prose_review.json"),
    Path("paper/review/medical_prose_review.json"),
)
_STAGE_NATIVE_BODY_ROOT_RELPATH = (
    Path("artifacts")
    / "stage_outputs"
    / "_body_authority"
    / "paper_authority_cutover"
    / "current_body"
)


def default_ai_reviewer_request_input_refs(*, study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    manuscript_relative_path = _first_existing_relative_path(
        study_root=resolved_study_root,
        candidates=AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES,
    )
    medical_prose_review_relative_path = _first_existing_relative_path(
        study_root=resolved_study_root,
        candidates=AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES,
    )
    return {
        "manuscript": _ref_payload(
            study_root=resolved_study_root,
            surface="manuscript",
            relative_path=manuscript_relative_path,
        ),
        "evidence_ledger": _ref_payload(
            study_root=resolved_study_root,
            surface="evidence_ledger",
            relative_path=Path("paper/evidence_ledger.json"),
        ),
        "review_ledger": _ref_payload(
            study_root=resolved_study_root,
            surface="review_ledger",
            relative_path=Path("paper/review/review_ledger.json"),
        ),
        "study_charter": _ref_payload(
            study_root=resolved_study_root,
            surface="study_charter",
            relative_path=Path("artifacts/controller/study_charter.json"),
        ),
        "medical_manuscript_blueprint": _ref_payload(
            study_root=resolved_study_root,
            surface="medical_manuscript_blueprint",
            relative_path=Path("paper/medical_manuscript_blueprint.json"),
        ),
        "claim_evidence_map": _ref_payload(
            study_root=resolved_study_root,
            surface="claim_evidence_map",
            relative_path=Path("paper/claim_evidence_map.json"),
        ),
        "medical_prose_review": _ref_payload(
            study_root=resolved_study_root,
            surface="medical_prose_review",
            relative_path=medical_prose_review_relative_path,
        ),
        "publication_gate_projection": _ref_payload(
            study_root=resolved_study_root,
            surface="publication_gate_projection",
            relative_path=Path("artifacts/publication_eval/latest.json"),
        ),
    }


def required_inputs(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_input_contract(packet).get("required_refs"))


def input_contract_with_normalized_refs(
    packet: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    contract = dict(_input_contract(packet))
    refs = normalized_required_inputs(packet, study_root=study_root)
    missing = [
        surface
        for surface, ref in refs.items()
        if not _ref_has_target(ref) or ref.get("present") is False or ref.get("valid") is False
    ]
    contract["required_refs"] = refs
    contract["required_surfaces"] = list(dict.fromkeys([*AI_REVIEWER_REQUIRED_INPUT_SURFACES, *refs.keys()]))
    contract["all_required_refs_present"] = not missing
    contract["missing_or_invalid_refs"] = missing
    return contract


def packet_with_normalized_input_contract(
    *,
    study_root: Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(packet)
    payload["input_contract"] = input_contract_with_normalized_refs(
        payload,
        study_root=study_root,
    )
    return payload


def input_blockers(packet: Mapping[str, Any], *, study_root: Path) -> list[str]:
    blockers: list[str] = []
    refs = normalized_required_inputs(packet, study_root=study_root)
    for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES:
        ref = _mapping(refs.get(surface))
        if not ref:
            blockers.append(f"{surface}_ref_missing")
            continue
        if not _ref_has_target(ref):
            blockers.append(f"{surface}_ref_missing")
        elif ref.get("present") is False:
            blockers.append(f"{surface}_missing")
        elif ref.get("valid") is False:
            blockers.append(f"{surface}_invalid")
    return blockers


def normalized_required_inputs(
    packet: Mapping[str, Any],
    *,
    study_root: Path,
) -> dict[str, dict[str, Any]]:
    refs = required_inputs(packet)
    default_refs = default_ai_reviewer_request_input_refs(study_root=study_root)
    normalized: dict[str, dict[str, Any]] = {}
    for surface in AI_REVIEWER_REQUIRED_INPUT_SURFACES:
        ref = dict(_mapping(refs.get(surface)))
        if surface == "medical_prose_review":
            ref = _normalize_medical_prose_review_ref(study_root=study_root, ref=ref)
        if (
            not ref
            or not _ref_has_target(ref)
            or ref.get("present") is False
            or ref.get("valid") is False
        ):
            default_ref = dict(_mapping(default_refs.get(surface)))
            if any(path.exists() for path in _candidate_ref_paths(study_root=study_root, ref=default_ref)):
                ref = default_ref
        normalized[surface] = ref
    for surface, ref in refs.items():
        if surface not in normalized:
            normalized[surface] = dict(_mapping(ref))
    return normalized


def _input_contract(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(packet.get("input_contract"))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _ref_payload(*, study_root: Path, surface: str, relative_path: Path) -> dict[str, Any]:
    path = _resolve_authority_ref(study_root=study_root, relative_path=relative_path)
    try:
        resolved_relative_path = path.relative_to(study_root).as_posix()
    except ValueError:
        resolved_relative_path = relative_path.as_posix()
    return {
        "surface": surface,
        "relative_path": resolved_relative_path,
        "path": str(path),
        "required": True,
        "present": path.exists(),
        "valid": path.exists(),
    }


def _first_existing_relative_path(*, study_root: Path, candidates: tuple[Path, ...]) -> Path:
    for root in (study_root / _STAGE_NATIVE_BODY_ROOT_RELPATH, study_root):
        for candidate in candidates:
            if (root / candidate).exists():
                return candidate
    return candidates[0]


def _resolve_authority_ref(*, study_root: Path, relative_path: Path) -> Path:
    staged = study_root / _STAGE_NATIVE_BODY_ROOT_RELPATH / relative_path
    if staged.exists():
        return staged.resolve()
    return (study_root / relative_path).resolve()


def _ref_has_target(ref: Mapping[str, Any]) -> bool:
    return bool(_text(ref.get("path")) or _text(ref.get("relative_path")) or _text(ref.get("ref")))


def _candidate_ref_paths(*, study_root: Path, ref: Mapping[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for key in ("path", "relative_path", "ref"):
        target = _text(ref.get(key))
        if not target:
            continue
        candidate = Path(target).expanduser()
        if not candidate.is_absolute():
            candidate = study_root / candidate
        if not candidate.exists():
            try:
                legacy_relative_path = candidate.resolve().relative_to(study_root.resolve())
            except ValueError:
                legacy_relative_path = None
            if legacy_relative_path is not None:
                staged = study_root / _STAGE_NATIVE_BODY_ROOT_RELPATH / legacy_relative_path
                if staged.exists():
                    candidate = staged
        paths.append(candidate.resolve())
    return paths


def _existing_medical_prose_review_ref_payload(*, study_root: Path) -> dict[str, Any] | None:
    for relative_path in AI_REVIEWER_MEDICAL_PROSE_REVIEW_REF_CANDIDATES:
        if (study_root / relative_path).exists():
            return _ref_payload(
                study_root=study_root,
                surface="medical_prose_review",
                relative_path=relative_path,
            )
    return None


def _normalize_medical_prose_review_ref(
    *,
    study_root: Path,
    ref: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(ref)
    existing_targets = [path for path in _candidate_ref_paths(study_root=study_root, ref=payload) if path.exists()]
    if existing_targets:
        path = existing_targets[0]
        try:
            relative_path = path.relative_to(study_root).as_posix()
        except ValueError:
            relative_path = _text(payload.get("relative_path"))
        payload.update(
            {
                "surface": "medical_prose_review",
                "path": str(path),
                "present": True,
                "valid": True,
            }
        )
        if relative_path:
            payload["relative_path"] = relative_path
        return payload

    existing_payload = _existing_medical_prose_review_ref_payload(study_root=study_root)
    if existing_payload is not None:
        return existing_payload
    return payload


__all__ = [
    "AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES",
    "AI_REVIEWER_REQUIRED_INPUT_SURFACES",
    "default_ai_reviewer_request_input_refs",
    "input_blockers",
    "input_contract_with_normalized_refs",
    "normalized_required_inputs",
    "packet_with_normalized_input_contract",
    "required_inputs",
]
