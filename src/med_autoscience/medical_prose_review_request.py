from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.medical_journal_style_corpus import (
    materialize_medical_journal_style_corpus,
    read_medical_journal_style_corpus,
    stable_medical_journal_style_corpus_path,
)
from med_autoscience.medical_manuscript_blueprint import (
    read_medical_manuscript_blueprint,
    stable_medical_manuscript_blueprint_path,
)
from med_autoscience.medical_prose_review import (
    materialize_medical_prose_review,
    validate_medical_prose_review,
)

__all__ = [
    "STABLE_MEDICAL_PROSE_REVIEW_REQUEST_RELATIVE_PATH",
    "build_medical_prose_review_request",
    "materialize_ai_medical_prose_review_from_response",
    "materialize_medical_prose_review_request",
    "read_medical_prose_review_request",
    "resolve_medical_prose_review_request_ref",
    "stable_medical_prose_review_request_path",
    "validate_ai_medical_prose_review_response",
    "validate_medical_prose_review_request",
]


STABLE_MEDICAL_PROSE_REVIEW_REQUEST_RELATIVE_PATH = Path("artifacts/publication_eval/medical_prose_review_request.json")

_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "surface",
    "request_id",
    "review_owner",
    "review_policy_id",
    "required_inputs",
    "style_corpus",
    "blueprint",
    "manuscript",
    "mechanical_safety_flags",
    "review_tasks",
    "structured_response_contract",
)
_ALLOWED_VERDICTS = {"clear", "revise", "block"}
_ALLOWED_ROUTE_TARGETS = {"none", "blueprint", "analysis", "write", "review"}
_RESPONSE_REQUIRED_FIELDS = (
    "overall_style_verdict",
    "summary",
    "section_level_diagnosis",
    "representative_bad_sentences",
    "representative_rewrites",
    "route_back_recommendation",
)


def stable_medical_prose_review_request_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_MEDICAL_PROSE_REVIEW_REQUEST_RELATIVE_PATH).resolve()


def resolve_medical_prose_review_request_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_medical_prose_review_request_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("medical prose review request reader only accepts the eval-owned request artifact")
    return stable_path


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _source_ref(path: Path) -> str | None:
    return str(path.resolve()) if path.exists() else None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _existing_input_refs(*, study_root: Path, paper_root: Path, manuscript_path: Path) -> dict[str, str]:
    refs: dict[str, str] = {}
    candidates = {
        "manuscript_ref": manuscript_path,
        "medical_manuscript_blueprint_ref": stable_medical_manuscript_blueprint_path(study_root=study_root),
        "medical_journal_style_corpus_ref": stable_medical_journal_style_corpus_path(study_root=study_root),
        "claim_evidence_map_ref": paper_root / "claim_evidence_map.json",
        "results_narrative_map_ref": paper_root / "results_narrative_map.json",
        "figure_semantics_ref": paper_root / "figure_semantics_manifest.json",
        "review_ledger_ref": paper_root / "review" / "review_ledger.json",
    }
    for key, path in candidates.items():
        ref = _source_ref(path)
        if ref:
            refs[key] = ref
    return refs


def build_medical_prose_review_request(
    *,
    study_root: Path,
    manuscript_path: Path | None = None,
    paper_root: Path | None = None,
    mechanical_safety_flags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else resolved_study_root / "paper"
    resolved_manuscript_path = (
        Path(manuscript_path).expanduser().resolve()
        if manuscript_path is not None
        else resolved_paper_root / "draft.md"
    )
    blueprint = read_medical_manuscript_blueprint(study_root=resolved_study_root)
    corpus_path = stable_medical_journal_style_corpus_path(study_root=resolved_study_root)
    if not corpus_path.exists():
        materialize_medical_journal_style_corpus(study_root=resolved_study_root)
    style_corpus = read_medical_journal_style_corpus(study_root=resolved_study_root)
    claim_evidence_map = _read_json(resolved_paper_root / "claim_evidence_map.json")
    results_narrative_map = _read_json(resolved_paper_root / "results_narrative_map.json")
    figure_semantics = _read_json(resolved_paper_root / "figure_semantics_manifest.json")
    review_ledger = _read_json(resolved_paper_root / "review" / "review_ledger.json")
    manuscript_text = _read_text(resolved_manuscript_path)
    required_inputs = _existing_input_refs(
        study_root=resolved_study_root,
        paper_root=resolved_paper_root,
        manuscript_path=resolved_manuscript_path,
    )
    return {
        "schema_version": 1,
        "surface": "medical_prose_review_request",
        "request_id": f"medical-prose-review::{resolved_study_root.name}::latest",
        "study_id": str(blueprint.get("study_id") or resolved_study_root.name),
        "review_owner": "ai_reviewer",
        "review_policy_id": "medical_publication_critique_v1",
        "required_inputs": required_inputs,
        "style_corpus": {
            "corpus_id": style_corpus["corpus_id"],
            "target_voice": style_corpus["style_profile"]["target_voice"],
            "source_refs": style_corpus["source_refs"],
            "principles": style_corpus["principles"],
            "reviewer_questions": style_corpus["reviewer_questions"],
        },
        "blueprint": {
            "argument_sequence": blueprint["argument_sequence"],
            "clinical_problem": blueprint["clinical_problem"],
            "evidence_gap": blueprint["evidence_gap"],
            "study_objective": blueprint["study_objective"],
            "main_findings_by_clinical_importance": blueprint["main_findings_by_clinical_importance"],
            "discussion_claim_boundary": blueprint["discussion_claim_boundary"],
            "journal_voice_target": blueprint["journal_voice_target"],
        },
        "claim_evidence_map": claim_evidence_map,
        "results_narrative_map": results_narrative_map,
        "figure_semantics": figure_semantics,
        "review_ledger": review_ledger,
        "manuscript": {
            "path": str(resolved_manuscript_path),
            "character_count": len(manuscript_text),
            "text": manuscript_text,
        },
        "mechanical_safety_flags": list(mechanical_safety_flags or []),
        "review_tasks": [
            "Judge whether the manuscript sounds like a medical original research article rather than a work report.",
            "Assess Introduction clinical problem -> evidence gap -> objective flow.",
            "Assess Results subject choice and old-to-new information flow.",
            "Assess Discussion restraint, claim boundary, and limitation integration.",
            "Return representative bad sentences and concrete rewrite examples for the writer.",
            "Route back to blueprint, analysis, write, or review when the prose issue cannot be repaired by surface editing alone.",
        ],
        "structured_response_contract": {
            "owner": "ai_reviewer",
            "required_fields": list(_RESPONSE_REQUIRED_FIELDS),
            "allowed_overall_style_verdicts": sorted(_ALLOWED_VERDICTS),
            "allowed_route_targets": sorted(_ALLOWED_ROUTE_TARGETS),
            "mechanical_flags_role": "evidence_snippets_only",
        },
    }


def validate_medical_prose_review_request(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "medical_prose_review_request":
        return ["surface must be medical_prose_review_request"]
    if payload.get("review_owner") != "ai_reviewer":
        return ["review_owner must be ai_reviewer"]
    if payload.get("review_policy_id") != "medical_publication_critique_v1":
        return ["review_policy_id must be medical_publication_critique_v1"]
    required_inputs = payload.get("required_inputs")
    if not isinstance(required_inputs, Mapping):
        return ["required_inputs must be an object"]
    for key in ("manuscript_ref", "medical_manuscript_blueprint_ref", "medical_journal_style_corpus_ref"):
        if not _text(required_inputs.get(key)):
            return [f"required_inputs.{key} must be non-empty"]
    style_corpus = payload.get("style_corpus")
    if not isinstance(style_corpus, Mapping) or _text(style_corpus.get("corpus_id")) != "general_medical_journal_style_corpus_v1":
        return ["style_corpus.corpus_id must be general_medical_journal_style_corpus_v1"]
    blueprint = payload.get("blueprint")
    if not isinstance(blueprint, Mapping) or not _text(blueprint.get("clinical_problem")):
        return ["blueprint.clinical_problem must be non-empty"]
    manuscript = payload.get("manuscript")
    if not isinstance(manuscript, Mapping) or not _text(manuscript.get("text")):
        return ["manuscript.text must be non-empty"]
    if not isinstance(payload.get("mechanical_safety_flags"), list):
        return ["mechanical_safety_flags must be a list"]
    response_contract = payload.get("structured_response_contract")
    if not isinstance(response_contract, Mapping) or response_contract.get("owner") != "ai_reviewer":
        return ["structured_response_contract.owner must be ai_reviewer"]
    return []


def read_medical_prose_review_request(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    path = resolve_medical_prose_review_request_ref(study_root=study_root, ref=ref)
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    errors = validate_medical_prose_review_request(payload)
    if errors:
        raise ValueError(f"medical prose review request is invalid: {'; '.join(errors)}")
    return dict(payload)


def materialize_medical_prose_review_request(
    *,
    study_root: Path,
    manuscript_path: Path | None = None,
    paper_root: Path | None = None,
    mechanical_safety_flags: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    payload = build_medical_prose_review_request(
        study_root=study_root,
        manuscript_path=manuscript_path,
        paper_root=paper_root,
        mechanical_safety_flags=mechanical_safety_flags,
    )
    errors = validate_medical_prose_review_request(payload)
    if errors:
        raise ValueError(f"medical prose review request is invalid: {'; '.join(errors)}")
    path = stable_medical_prose_review_request_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "medical_prose_review_request",
        "artifact_path": str(path),
    }


def validate_ai_medical_prose_review_response(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _RESPONSE_REQUIRED_FIELDS if field not in payload]
    if missing:
        return [f"missing AI response keys: {', '.join(missing)}"]
    verdict = _text(payload.get("overall_style_verdict"))
    if verdict not in _ALLOWED_VERDICTS:
        return ["overall_style_verdict is invalid"]
    if not _text(payload.get("summary")):
        return ["summary must be non-empty"]
    if not isinstance(payload.get("section_level_diagnosis"), Mapping):
        return ["section_level_diagnosis must be an object"]
    if not isinstance(payload.get("representative_bad_sentences"), list):
        return ["representative_bad_sentences must be a list"]
    rewrites = payload.get("representative_rewrites")
    if not isinstance(rewrites, list):
        return ["representative_rewrites must be a list"]
    for item in rewrites:
        if not isinstance(item, Mapping) or not _text(item.get("before")) or not _text(item.get("after")):
            return ["representative_rewrites entries must include before and after"]
    route = payload.get("route_back_recommendation")
    if not isinstance(route, Mapping):
        return ["route_back_recommendation must be an object"]
    route_target = _text(route.get("route_target")) or "none"
    if route_target not in _ALLOWED_ROUTE_TARGETS:
        return ["route_back_recommendation.route_target is invalid"]
    if verdict == "clear" and route_target != "none":
        return ["clear AI prose response must route to none"]
    if verdict != "clear" and route_target == "none":
        return ["non-clear AI prose response must include a route target"]
    return []


def materialize_ai_medical_prose_review_from_response(
    *,
    study_root: Path,
    response_payload: Mapping[str, Any],
    request_ref: str | Path | None = None,
) -> dict[str, str]:
    request = read_medical_prose_review_request(study_root=study_root, ref=request_ref)
    errors = validate_ai_medical_prose_review_response(response_payload)
    if errors:
        raise ValueError(f"AI medical prose review response is invalid: {'; '.join(errors)}")
    route_back = dict(response_payload.get("route_back_recommendation") or {})
    source_refs = [
        ref
        for ref in [
            str(stable_medical_prose_review_request_path(study_root=study_root)),
            *[str(item) for item in dict(request.get("required_inputs") or {}).values() if str(item).strip()],
        ]
        if ref
    ]
    review_payload = {
        "schema_version": 1,
        "surface": "medical_prose_review",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "medical_prose_review",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "request_ref": str(stable_medical_prose_review_request_path(study_root=study_root)),
        },
        "medical_journal_prose_quality": {
            "status": "ready" if response_payload["overall_style_verdict"] == "clear" else "partial"
            if response_payload["overall_style_verdict"] == "revise"
            else "blocked",
            "overall_style_verdict": response_payload["overall_style_verdict"],
            "summary": response_payload["summary"],
            "section_level_diagnosis": dict(response_payload["section_level_diagnosis"]),
            "representative_bad_sentences": list(response_payload["representative_bad_sentences"]),
            "representative_rewrites": [dict(item) for item in response_payload["representative_rewrites"]],
            "route_back_recommendation": {
                "required": response_payload["overall_style_verdict"] != "clear",
                "route_target": _text(route_back.get("route_target")) or "none",
                "reason": _text(route_back.get("reason")) or response_payload["summary"],
            },
        },
        "mechanical_safety_flags": list(request.get("mechanical_safety_flags") or []),
        "source_refs": source_refs,
        "manuscript_character_count": int((request.get("manuscript") or {}).get("character_count") or 0),
    }
    review_errors = validate_medical_prose_review(review_payload)
    if review_errors:
        raise ValueError(f"AI medical prose review response produced invalid review: {'; '.join(review_errors)}")
    return materialize_medical_prose_review(study_root=study_root, payload=review_payload)
