from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.medical_journal_style_corpus import (
    ensure_current_medical_journal_style_corpus,
    stable_medical_journal_style_corpus_path,
)

__all__ = [
    "STABLE_RETROSPECTIVE_MEDICAL_PROSE_AUDIT_RELATIVE_PATH",
    "build_retrospective_medical_prose_audit_request",
    "materialize_retrospective_medical_prose_audit",
    "materialize_retrospective_medical_prose_audit_request",
    "read_retrospective_medical_prose_audit",
    "resolve_retrospective_medical_prose_audit_ref",
    "stable_retrospective_medical_prose_audit_path",
    "stable_retrospective_medical_prose_audit_request_path",
    "validate_retrospective_medical_prose_audit",
    "validate_retrospective_medical_prose_audit_request",
]


STABLE_RETROSPECTIVE_MEDICAL_PROSE_AUDIT_RELATIVE_PATH = Path(
    "artifacts/publication_eval/retrospective_medical_prose_audit.json"
)
STABLE_RETROSPECTIVE_MEDICAL_PROSE_AUDIT_REQUEST_RELATIVE_PATH = Path(
    "artifacts/publication_eval/retrospective_medical_prose_audit_request.json"
)

_REQUIRED_SAMPLE_IDS = (
    "nf-pitnet-003",
    "dpcc-003",
    "dpcc-004",
)
_REQUEST_REQUIRED_FIELDS = (
    "schema_version",
    "surface",
    "audit_owner",
    "audit_policy_id",
    "style_corpus_ref",
    "samples",
    "review_tasks",
    "structured_response_contract",
)
_AUDIT_REQUIRED_FIELDS = (
    "schema_version",
    "surface",
    "assessment_provenance",
    "audit_policy_id",
    "style_corpus_ref",
    "samples",
    "regression_fixture_contract",
)
_SAMPLE_REQUIRED_FIELDS = (
    "sample_id",
    "study_label",
    "source_ref",
    "style_score",
    "overall_style_verdict",
    "work_report_residue",
    "results_subject_information_flow",
    "discussion_restraint",
    "top_three_paragraphs_to_rewrite",
    "route_back_recommendation",
)
_ALLOWED_VERDICTS = {"medical_journal_like", "mixed", "work_report_like", "blocked"}
_ALLOWED_ROUTE_TARGETS = {"none", "blueprint", "analysis", "write", "review"}


def stable_retrospective_medical_prose_audit_path(*, study_root: Path) -> Path:
    return (
        Path(study_root).expanduser().resolve() / STABLE_RETROSPECTIVE_MEDICAL_PROSE_AUDIT_RELATIVE_PATH
    ).resolve()


def stable_retrospective_medical_prose_audit_request_path(*, study_root: Path) -> Path:
    return (
        Path(study_root).expanduser().resolve() / STABLE_RETROSPECTIVE_MEDICAL_PROSE_AUDIT_REQUEST_RELATIVE_PATH
    ).resolve()


def resolve_retrospective_medical_prose_audit_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_retrospective_medical_prose_audit_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("retrospective medical prose audit reader only accepts the eval-owned audit artifact")
    return stable_path


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _default_sample_sources() -> list[dict[str, str]]:
    return [
        {
            "sample_id": "nf-pitnet-003",
            "study_label": "NF-PitNET 003 endocrine burden follow-up",
            "source_ref": "/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper/draft.md",
        },
        {
            "sample_id": "dpcc-003",
            "study_label": "DPCC 003 primary-care phenotype treatment gap",
            "source_ref": "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/manuscript/current_package/review_manuscript.md",
        },
        {
            "sample_id": "dpcc-004",
            "study_label": "DPCC 004 longitudinal care inertia intensification gap",
            "source_ref": "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/004-dpcc-longitudinal-care-inertia-intensification-gap/manuscript/current_package/manuscript_source.md",
        },
    ]


def build_retrospective_medical_prose_audit_request(
    *,
    study_root: Path,
    samples: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    corpus_path = stable_medical_journal_style_corpus_path(study_root=resolved_study_root)
    style_corpus = ensure_current_medical_journal_style_corpus(study_root=resolved_study_root)
    resolved_samples: list[dict[str, Any]] = []
    for sample in samples or _default_sample_sources():
        source_ref = _text(sample.get("source_ref"))
        source_path = Path(source_ref).expanduser() if source_ref else None
        manuscript_text = _read_text(source_path)
        resolved_samples.append(
            {
                "sample_id": _text(sample.get("sample_id")),
                "study_label": _text(sample.get("study_label")),
                "source_ref": source_ref,
                "source_available": bool(source_path is not None and source_path.exists()),
                "manuscript_text": manuscript_text,
                "manuscript_character_count": len(manuscript_text),
            }
        )
    return {
        "schema_version": 1,
        "surface": "retrospective_medical_prose_audit_request",
        "audit_owner": "ai_reviewer",
        "audit_policy_id": "medical_journal_prose_retrospective_audit_v1",
        "style_corpus_ref": str(corpus_path),
        "style_corpus": {
            "corpus_id": style_corpus["corpus_id"],
            "style_version": style_corpus["style_version"],
            "source_set_id": style_corpus["source_set_id"],
            "style_digest": style_corpus["style_digest"],
            "style_currentness": dict(style_corpus["style_currentness"]),
            "principles": style_corpus["principles"],
            "reviewer_questions": style_corpus["reviewer_questions"],
        },
        "samples": resolved_samples,
        "review_tasks": [
            "For each sample, judge medical-journal voice as a subjective AI reviewer assessment.",
            "Score style quality on a 0-100 scale with rationale.",
            "Identify work-report residue without making regex the authority.",
            "Assess Results subject choice and information flow.",
            "Assess Discussion restraint and limitation integration.",
            "Name the three paragraphs that should be rewritten first.",
            "Return route-back recommendations for MAS/MDS pipeline regression use.",
        ],
        "structured_response_contract": {
            "owner": "ai_reviewer",
            "required_sample_ids": list(_REQUIRED_SAMPLE_IDS),
            "sample_required_fields": list(_SAMPLE_REQUIRED_FIELDS),
            "allowed_overall_style_verdicts": sorted(_ALLOWED_VERDICTS),
            "allowed_route_targets": sorted(_ALLOWED_ROUTE_TARGETS),
            "manual_study_patch_allowed": False,
        },
    }


def validate_retrospective_medical_prose_audit_request(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _REQUEST_REQUIRED_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "retrospective_medical_prose_audit_request":
        return ["surface must be retrospective_medical_prose_audit_request"]
    if payload.get("audit_owner") != "ai_reviewer":
        return ["audit_owner must be ai_reviewer"]
    samples = payload.get("samples")
    if not isinstance(samples, list):
        return ["samples must be a list"]
    sample_ids = {str(item.get("sample_id") or "").strip() for item in samples if isinstance(item, Mapping)}
    missing_sample_ids = [sample_id for sample_id in _REQUIRED_SAMPLE_IDS if sample_id not in sample_ids]
    if missing_sample_ids:
        return [f"samples missing required sample_id: {missing_sample_ids[0]}"]
    contract = payload.get("structured_response_contract")
    if not isinstance(contract, Mapping) or contract.get("owner") != "ai_reviewer":
        return ["structured_response_contract.owner must be ai_reviewer"]
    if contract.get("manual_study_patch_allowed") is not False:
        return ["structured_response_contract.manual_study_patch_allowed must be false"]
    return []


def materialize_retrospective_medical_prose_audit_request(
    *,
    study_root: Path,
    samples: list[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    payload = build_retrospective_medical_prose_audit_request(study_root=study_root, samples=samples)
    errors = validate_retrospective_medical_prose_audit_request(payload)
    if errors:
        raise ValueError(f"retrospective medical prose audit request is invalid: {'; '.join(errors)}")
    path = stable_retrospective_medical_prose_audit_request_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "retrospective_medical_prose_audit_request",
        "artifact_path": str(path),
    }


def validate_retrospective_medical_prose_audit(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _AUDIT_REQUIRED_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "retrospective_medical_prose_audit":
        return ["surface must be retrospective_medical_prose_audit"]
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return ["assessment_provenance must be an object"]
    if provenance.get("owner") != "ai_reviewer":
        return ["assessment_provenance.owner must be ai_reviewer"]
    if provenance.get("ai_reviewer_required") is not False:
        return ["assessment_provenance.ai_reviewer_required must be false"]
    samples = payload.get("samples")
    if not isinstance(samples, list):
        return ["samples must be a list"]
    sample_ids = {str(item.get("sample_id") or "").strip() for item in samples if isinstance(item, Mapping)}
    missing_sample_ids = [sample_id for sample_id in _REQUIRED_SAMPLE_IDS if sample_id not in sample_ids]
    if missing_sample_ids:
        return [f"samples missing required sample_id: {missing_sample_ids[0]}"]
    for sample in samples:
        if not isinstance(sample, Mapping):
            return ["samples entries must be objects"]
        missing_fields = [field for field in _SAMPLE_REQUIRED_FIELDS if field not in sample]
        if missing_fields:
            return [f"sample {sample.get('sample_id') or '<unknown>'} missing {missing_fields[0]}"]
        score = sample.get("style_score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 100:
            return [f"sample {sample.get('sample_id') or '<unknown>'} style_score must be 0-100 int"]
        if sample.get("overall_style_verdict") not in _ALLOWED_VERDICTS:
            return [f"sample {sample.get('sample_id') or '<unknown>'} overall_style_verdict is invalid"]
        if not isinstance(sample.get("top_three_paragraphs_to_rewrite"), list) or len(sample["top_three_paragraphs_to_rewrite"]) != 3:
            return [f"sample {sample.get('sample_id') or '<unknown>'} must include top_three_paragraphs_to_rewrite"]
        route = sample.get("route_back_recommendation")
        if not isinstance(route, Mapping):
            return [f"sample {sample.get('sample_id') or '<unknown>'} route_back_recommendation must be an object"]
        route_target = _text(route.get("route_target")) or "none"
        if route_target not in _ALLOWED_ROUTE_TARGETS:
            return [f"sample {sample.get('sample_id') or '<unknown>'} route_back target is invalid"]
    regression_contract = payload.get("regression_fixture_contract")
    if not isinstance(regression_contract, Mapping) or regression_contract.get("manual_study_patch_allowed") is not False:
        return ["regression_fixture_contract.manual_study_patch_allowed must be false"]
    return []


def materialize_retrospective_medical_prose_audit(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, str]:
    resolved_payload = dict(payload)
    if "assessment_provenance" not in resolved_payload:
        resolved_payload["assessment_provenance"] = {
            "owner": "ai_reviewer",
            "source_kind": "retrospective_medical_prose_audit",
            "policy_id": "medical_journal_prose_retrospective_audit_v1",
            "ai_reviewer_required": False,
            "request_ref": str(stable_retrospective_medical_prose_audit_request_path(study_root=study_root)),
        }
    if "regression_fixture_contract" not in resolved_payload:
        resolved_payload["regression_fixture_contract"] = {
            "mode": "repo_level_pipeline_regression_fixture",
            "manual_study_patch_allowed": False,
            "used_for": [
                "medical prose review regression",
                "MDS write preflight prompt regression",
                "publication gate AI-first boundary regression",
            ],
        }
    errors = validate_retrospective_medical_prose_audit(resolved_payload)
    if errors:
        raise ValueError(f"retrospective medical prose audit is invalid: {'; '.join(errors)}")
    path = stable_retrospective_medical_prose_audit_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolved_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "retrospective_medical_prose_audit",
        "artifact_path": str(path),
    }


def read_retrospective_medical_prose_audit(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    path = resolve_retrospective_medical_prose_audit_ref(study_root=study_root, ref=ref)
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    errors = validate_retrospective_medical_prose_audit(payload)
    if errors:
        raise ValueError(f"retrospective medical prose audit is invalid: {'; '.join(errors)}")
    return dict(payload)
