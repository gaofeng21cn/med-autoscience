from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.medical_manuscript_blueprint import read_medical_manuscript_blueprint

__all__ = [
    "STABLE_MEDICAL_PROSE_REVIEW_RELATIVE_PATH",
    "build_medical_prose_review",
    "materialize_medical_prose_review",
    "read_medical_prose_review",
    "resolve_medical_prose_review_ref",
    "stable_medical_prose_review_path",
    "validate_medical_prose_review",
]


STABLE_MEDICAL_PROSE_REVIEW_RELATIVE_PATH = Path("artifacts/publication_eval/medical_prose_review.json")
_ALLOWED_VERDICTS = {"clear", "revise", "block"}
_ALLOWED_ROUTE_BACK_TARGETS = {"none", "blueprint", "analysis", "write", "review"}
_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "surface",
    "assessment_provenance",
    "medical_journal_prose_quality",
    "mechanical_safety_flags",
    "source_refs",
)


def stable_medical_prose_review_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_MEDICAL_PROSE_REVIEW_RELATIVE_PATH).resolve()


def resolve_medical_prose_review_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_medical_prose_review_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("medical prose review reader only accepts the eval-owned AI prose review artifact")
    return stable_path


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _source_ref(path: Path) -> str | None:
    return str(path.resolve()) if path.exists() else None


def _review_quality_from_verdict(
    *,
    verdict: str,
    style_diagnosis: str,
    route_back_target: str,
    representative_bad_sentences: list[str],
    representative_rewrites: list[dict[str, str]],
) -> dict[str, Any]:
    status = "ready" if verdict == "clear" else "partial" if verdict == "revise" else "blocked"
    return {
        "status": status,
        "overall_style_verdict": verdict,
        "summary": style_diagnosis,
        "section_level_diagnosis": {
            "introduction": "AI reviewer must judge whether the opening moves from clinical problem to evidence gap and objective.",
            "results": "AI reviewer must judge whether findings, not displays or controller artifacts, carry the sentence subjects.",
            "discussion": "AI reviewer must judge whether interpretation is restrained and limitation-aware.",
        },
        "representative_bad_sentences": representative_bad_sentences,
        "representative_rewrites": representative_rewrites,
        "route_back_recommendation": {
            "required": verdict != "clear",
            "route_target": route_back_target,
            "reason": style_diagnosis,
        },
    }


def build_medical_prose_review(
    *,
    study_root: Path,
    manuscript_text: str,
    mechanical_safety_flags: list[dict[str, Any]] | None = None,
    verdict: str,
    style_diagnosis: str,
    representative_bad_sentences: list[str],
    representative_rewrites: list[dict[str, str]],
    route_back_target: str,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    normalized_verdict = _text(verdict) or ""
    if normalized_verdict not in _ALLOWED_VERDICTS:
        raise ValueError(f"medical prose review verdict must be one of: {', '.join(sorted(_ALLOWED_VERDICTS))}")
    normalized_route = _text(route_back_target) or "none"
    if normalized_route not in _ALLOWED_ROUTE_BACK_TARGETS:
        raise ValueError(
            f"medical prose review route_back_target must be one of: {', '.join(sorted(_ALLOWED_ROUTE_BACK_TARGETS))}"
        )
    resolved_study_root = Path(study_root).expanduser().resolve()
    blueprint_path = resolved_study_root / "paper" / "medical_manuscript_blueprint.json"
    source_ref_values = list(source_refs or [])
    for ref in (str(blueprint_path) if blueprint_path.exists() else None,):
        if ref and ref not in source_ref_values:
            source_ref_values.append(ref)
    if not source_ref_values:
        source_ref_values.append(str(resolved_study_root))
    return {
        "schema_version": 1,
        "surface": "medical_prose_review",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "medical_prose_review",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "medical_journal_prose_quality": _review_quality_from_verdict(
            verdict=normalized_verdict,
            style_diagnosis=style_diagnosis,
            route_back_target=normalized_route,
            representative_bad_sentences=representative_bad_sentences,
            representative_rewrites=representative_rewrites,
        ),
        "mechanical_safety_flags": list(mechanical_safety_flags or []),
        "source_refs": source_ref_values,
        "manuscript_character_count": len(manuscript_text),
    }


def validate_medical_prose_review(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "medical_prose_review":
        return ["surface must be medical_prose_review"]
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return ["assessment_provenance must be an object"]
    if provenance.get("owner") != "ai_reviewer":
        return ["assessment_provenance.owner must be ai_reviewer"]
    if provenance.get("ai_reviewer_required") is not False:
        return ["assessment_provenance.ai_reviewer_required must be false"]
    quality = payload.get("medical_journal_prose_quality")
    if not isinstance(quality, Mapping):
        return ["medical_journal_prose_quality must be an object"]
    verdict = _text(quality.get("overall_style_verdict"))
    if verdict not in _ALLOWED_VERDICTS:
        return ["medical_journal_prose_quality.overall_style_verdict is invalid"]
    if not _text(quality.get("summary")):
        return ["medical_journal_prose_quality.summary must be non-empty"]
    route = quality.get("route_back_recommendation")
    if not isinstance(route, Mapping):
        return ["medical_journal_prose_quality.route_back_recommendation must be an object"]
    route_target = _text(route.get("route_target")) or "none"
    if route_target not in _ALLOWED_ROUTE_BACK_TARGETS:
        return ["medical_journal_prose_quality.route_back_recommendation.route_target is invalid"]
    if not isinstance(payload.get("mechanical_safety_flags"), list):
        return ["mechanical_safety_flags must be a list"]
    if not _text_list(payload.get("source_refs")):
        return ["source_refs must be a non-empty list"]
    return []


def read_medical_prose_review(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    path = resolve_medical_prose_review_ref(study_root=study_root, ref=ref)
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    errors = validate_medical_prose_review(payload)
    if errors:
        raise ValueError(f"medical prose review is invalid: {'; '.join(errors)}")
    return dict(payload)


def materialize_medical_prose_review(
    *,
    study_root: Path,
    manuscript_path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    mechanical_safety_flags: list[dict[str, Any]] | None = None,
    verdict: str | None = None,
    style_diagnosis: str | None = None,
    representative_bad_sentences: list[str] | None = None,
    representative_rewrites: list[dict[str, str]] | None = None,
    route_back_target: str | None = None,
) -> dict[str, str]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    if payload is None:
        if manuscript_path is None:
            manuscript_path = resolved_study_root / "paper" / "draft.md"
        manuscript_text = _read_text(Path(manuscript_path).expanduser())
        read_medical_manuscript_blueprint(study_root=resolved_study_root)
        resolved_payload = build_medical_prose_review(
            study_root=resolved_study_root,
            manuscript_text=manuscript_text,
            mechanical_safety_flags=mechanical_safety_flags,
            verdict=verdict or "block",
            style_diagnosis=style_diagnosis or "AI reviewer prose judgment is required before quality closure.",
            representative_bad_sentences=representative_bad_sentences or [],
            representative_rewrites=representative_rewrites or [],
            route_back_target=route_back_target or "write",
            source_refs=[
                ref
                for ref in (
                    _source_ref(Path(manuscript_path).expanduser()),
                    _source_ref(resolved_study_root / "paper" / "medical_manuscript_blueprint.json"),
                    _source_ref(resolved_study_root / "paper" / "claim_evidence_map.json"),
                    _source_ref(resolved_study_root / "paper" / "results_narrative_map.json"),
                    _source_ref(resolved_study_root / "paper" / "figure_semantics_manifest.json"),
                    _source_ref(resolved_study_root / "paper" / "review" / "review_ledger.json"),
                )
                if ref
            ],
        )
    else:
        resolved_payload = dict(payload)
    errors = validate_medical_prose_review(resolved_payload)
    if errors:
        raise ValueError(f"medical prose review is invalid: {'; '.join(errors)}")
    path = stable_medical_prose_review_path(study_root=resolved_study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolved_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "medical_prose_review",
        "artifact_path": str(path),
    }
