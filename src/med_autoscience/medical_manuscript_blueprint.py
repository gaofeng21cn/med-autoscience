from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies.medical_manuscript_draft_quality import build_medical_prose_style_contract
from med_autoscience.study_charter import read_study_charter

__all__ = [
    "STABLE_MEDICAL_MANUSCRIPT_BLUEPRINT_RELATIVE_PATH",
    "build_medical_manuscript_blueprint",
    "materialize_medical_manuscript_blueprint",
    "read_medical_manuscript_blueprint",
    "resolve_medical_manuscript_blueprint_ref",
    "stable_medical_manuscript_blueprint_path",
    "validate_medical_manuscript_blueprint",
]


STABLE_MEDICAL_MANUSCRIPT_BLUEPRINT_RELATIVE_PATH = Path("paper/medical_manuscript_blueprint.json")
_REQUIRED_SEQUENCE = (
    "clinical_problem",
    "evidence_gap",
    "study_objective",
    "target_population",
    "study_design",
    "main_findings_by_clinical_importance",
    "clinical_interpretation",
    "discussion_claim_boundary",
    "limitations",
)
_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "surface",
    "argument_sequence",
    "clinical_problem",
    "evidence_gap",
    "study_objective",
    "target_population",
    "study_design",
    "main_findings_by_clinical_importance",
    "clinical_interpretation",
    "claim_evidence_map",
    "figure_table_rhetorical_roles",
    "discussion_claim_boundary",
    "limitations",
    "journal_voice_target",
    "source_refs",
)


def stable_medical_manuscript_blueprint_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_MEDICAL_MANUSCRIPT_BLUEPRINT_RELATIVE_PATH).resolve()


def resolve_medical_manuscript_blueprint_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_medical_manuscript_blueprint_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("medical manuscript blueprint reader only accepts the study paper authority artifact")
    return stable_path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return dict(payload) if isinstance(payload, Mapping) else {}


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


def _first_text(*values: object, default: str) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return default


def _source_ref(path: Path) -> str | None:
    return str(path.resolve()) if path.exists() else None


def _results_sections(results_narrative: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in (results_narrative.get("sections") or []) if isinstance(item, Mapping)]


def _claims(claim_evidence_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in (claim_evidence_map.get("claims") or []) if isinstance(item, Mapping)]


def _figure_roles(figure_semantics: Mapping[str, Any]) -> list[dict[str, Any]]:
    roles: list[dict[str, Any]] = []
    for item in (figure_semantics.get("figures") or []):
        if not isinstance(item, Mapping):
            continue
        figure_id = _text(item.get("figure_id"))
        if not figure_id:
            continue
        roles.append(
            {
                "display_id": figure_id,
                "display_type": "figure",
                "story_role": _first_text(item.get("story_role"), default="unspecified"),
                "rhetorical_role": _first_text(item.get("direct_message"), item.get("clinical_implication"), default="figure supports the main clinical result"),
                "interpretation_boundary": _first_text(item.get("interpretation_boundary"), item.get("recommendation_boundary"), default="interpret as supporting display evidence only"),
            }
        )
    return roles


def _main_findings(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for index, section in enumerate(sections, start=1):
        findings.append(
            {
                "rank": index,
                "section_id": _first_text(section.get("section_id"), default=f"result-{index}"),
                "clinical_finding": _first_text(section.get("direct_answer"), section.get("section_title"), default="The main result needs clinical prose interpretation."),
                "quantitative_support": _text_list(section.get("key_quantitative_findings")),
                "clinical_meaning": _first_text(section.get("clinical_meaning"), default="Clinical meaning must be written from the evidence surface."),
                "interpretation_boundary": _first_text(section.get("boundary"), default="Do not extend beyond the mapped claim-evidence support."),
                "supporting_display_items": _text_list(section.get("supporting_display_items")),
            }
        )
    return findings


def _claim_map_summary(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = _first_text(claim.get("claim_id"), default="claim")
        summaries.append(
            {
                "claim_id": claim_id,
                "statement": _first_text(claim.get("statement"), claim.get("claim_text"), default="Claim statement is not yet explicit."),
                "status": _first_text(claim.get("status"), default="underdefined"),
                "paper_role": _first_text(claim.get("paper_role"), default="main_text"),
                "evidence_item_count": len([item for item in (claim.get("evidence_items") or []) if isinstance(item, Mapping)]),
                "display_bindings": _text_list(claim.get("display_bindings")),
                "limitations": _text_list(claim.get("limitations") or claim.get("risks")),
            }
        )
    return summaries


def _limitations(*, claims: list[dict[str, Any]], sections: list[dict[str, Any]], charter_payload: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    for claim in claims:
        items.extend(_text_list(claim.get("limitations") or claim.get("risks")))
    for section in sections:
        boundary = _text(section.get("boundary"))
        if boundary:
            items.append(boundary)
    items.extend(_text_list(charter_payload.get("manuscript_conclusion_redlines")))
    if not items:
        items.append("State limitations from the claim-evidence map before extending clinical interpretation.")
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def build_medical_manuscript_blueprint(
    *,
    study_root: Path,
    paper_root: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else resolved_study_root / "paper"
    charter_payload = read_study_charter(study_root=resolved_study_root)
    paper_quality_contract = (
        dict(charter_payload.get("paper_quality_contract") or {})
        if isinstance(charter_payload.get("paper_quality_contract"), Mapping)
        else {}
    )
    reporting_expectations = (
        dict(paper_quality_contract.get("reporting_expectations") or {})
        if isinstance(paper_quality_contract.get("reporting_expectations"), Mapping)
        else {}
    )
    style_contract = (
        dict(paper_quality_contract.get("medical_prose_style_contract") or {})
        if isinstance(paper_quality_contract.get("medical_prose_style_contract"), Mapping)
        else build_medical_prose_style_contract()
    )
    results_path = resolved_paper_root / "results_narrative_map.json"
    claim_path = resolved_paper_root / "claim_evidence_map.json"
    figure_semantics_path = resolved_paper_root / "figure_semantics_manifest.json"
    methods_path = resolved_paper_root / "methods_implementation_manifest.json"
    evidence_ledger_path = resolved_paper_root / "evidence_ledger.json"
    review_ledger_path = resolved_paper_root / "review" / "review_ledger.json"
    results_narrative = _read_json(results_path)
    claim_evidence_map = _read_json(claim_path)
    figure_semantics = _read_json(figure_semantics_path)
    methods_manifest = _read_json(methods_path)
    study_design = (
        dict(methods_manifest.get("study_design") or {})
        if isinstance(methods_manifest.get("study_design"), Mapping)
        else {}
    )
    sections = _results_sections(results_narrative)
    claims = _claims(claim_evidence_map)
    limitations = _limitations(claims=claims, sections=sections, charter_payload=charter_payload)
    source_refs = [
        ref
        for ref in (
            _source_ref(resolved_study_root / "artifacts" / "controller" / "study_charter.json"),
            _source_ref(results_path),
            _source_ref(claim_path),
            _source_ref(figure_semantics_path),
            _source_ref(methods_path),
            _source_ref(evidence_ledger_path),
            _source_ref(review_ledger_path),
        )
        if ref
    ]
    return {
        "schema_version": 1,
        "surface": "medical_manuscript_blueprint",
        "study_id": _first_text(charter_payload.get("study_id"), default=resolved_study_root.name),
        "argument_sequence": list(_REQUIRED_SEQUENCE),
        "clinical_problem": _first_text(
            reporting_expectations.get("paper_framing_summary"),
            charter_payload.get("paper_framing_summary"),
            charter_payload.get("publication_objective"),
            default="Define the clinical problem before drafting the full manuscript.",
        ),
        "evidence_gap": _first_text(
            "; ".join(_text_list(charter_payload.get("scientific_followup_questions"))),
            "; ".join(_text_list(charter_payload.get("explanation_targets"))),
            default="State the evidence gap that explains why the study was necessary.",
        ),
        "study_objective": _first_text(charter_payload.get("publication_objective"), charter_payload.get("primary_question"), default="State the study objective in clinical original-research language."),
        "target_population": _first_text(study_design.get("cohort_definition"), study_design.get("inclusion_criteria"), default="Target population must be specified before full drafting."),
        "study_design": _first_text(study_design.get("study_design"), methods_manifest.get("study_design"), default="Study design must be specified before full drafting."),
        "main_findings_by_clinical_importance": _main_findings(sections),
        "clinical_interpretation": _first_text(
            "; ".join([text for section in sections if (text := _text(section.get("clinical_meaning")))]),
            reporting_expectations.get("paper_framing_summary"),
            default="Interpret findings by clinical importance without upgrading claims.",
        ),
        "claim_evidence_map": _claim_map_summary(claims),
        "figure_table_rhetorical_roles": _figure_roles(figure_semantics),
        "discussion_claim_boundary": _first_text(
            "; ".join(limitations),
            default="Discussion must keep conclusions inside mapped evidence and limitation boundaries.",
        ),
        "limitations": limitations,
        "journal_voice_target": {
            "voice": _first_text(style_contract.get("target_voice"), default="neutral_clinical_original_research"),
            "reader_expectation": "clinical problem -> evidence gap -> objective -> main findings -> clinical interpretation -> limitations",
            "style_sources": list(style_contract.get("source_basis") or []),
        },
        "source_refs": source_refs,
    }


def validate_medical_manuscript_blueprint(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["payload must be a JSON object"]
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    if payload.get("schema_version") != 1:
        return ["schema_version must be 1"]
    if payload.get("surface") != "medical_manuscript_blueprint":
        return ["surface must be medical_manuscript_blueprint"]
    argument_sequence = payload.get("argument_sequence")
    if argument_sequence != list(_REQUIRED_SEQUENCE):
        return ["argument_sequence must follow the clinical problem -> evidence gap -> objective -> findings -> interpretation -> limitations order"]
    for field in ("clinical_problem", "evidence_gap", "study_objective", "target_population", "study_design", "clinical_interpretation", "discussion_claim_boundary"):
        if not _text(payload.get(field)):
            return [f"{field} must be non-empty"]
    for field in ("main_findings_by_clinical_importance", "claim_evidence_map", "figure_table_rhetorical_roles", "limitations", "source_refs"):
        value = payload.get(field)
        if not isinstance(value, list) or not value:
            return [f"{field} must be a non-empty list"]
    journal_voice_target = payload.get("journal_voice_target")
    if not isinstance(journal_voice_target, Mapping) or not _text(journal_voice_target.get("voice")):
        return ["journal_voice_target.voice must be non-empty"]
    return []


def read_medical_manuscript_blueprint(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    path = resolve_medical_manuscript_blueprint_ref(study_root=study_root, ref=ref)
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    errors = validate_medical_manuscript_blueprint(payload)
    if errors:
        raise ValueError(f"medical manuscript blueprint is invalid: {'; '.join(errors)}")
    return dict(payload)


def materialize_medical_manuscript_blueprint(
    *,
    study_root: Path,
    paper_root: Path | None = None,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    resolved_payload = dict(payload) if isinstance(payload, Mapping) else build_medical_manuscript_blueprint(
        study_root=study_root,
        paper_root=paper_root,
    )
    errors = validate_medical_manuscript_blueprint(resolved_payload)
    if errors:
        raise ValueError(f"medical manuscript blueprint is invalid: {'; '.join(errors)}")
    path = stable_medical_manuscript_blueprint_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resolved_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "surface": "medical_manuscript_blueprint",
        "artifact_path": str(path),
    }
