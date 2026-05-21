from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers.domain_route_scan_parts import ai_reviewer_actions


def completed_ai_reviewer_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    result_path = analysis_harmonization_owner_result.result_path(study_root=study_root)
    result = _read_json_object(result_path)
    if not analysis_harmonization_owner_result.result_satisfies_required_output(result):
        return None
    if result.get("unit_harmonized_rerun_completed") is not True:
        return None
    if _text(result.get("next_owner")) != "ai_reviewer":
        return None
    next_work_unit = _text(result.get("next_work_unit"))
    if next_work_unit != "ai_reviewer_medical_prose_quality_review":
        return None
    required_refs = currentness_refs(
        study_root=study_root,
        result_path=result_path,
        result=result,
    )
    if not required_refs:
        return None
    if publication_eval_covers_currentness_refs(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        required_refs=required_refs,
    ):
        return None
    action = ai_reviewer_actions.ai_reviewer_required_action(
        reason=ai_reviewer_actions.ANALYSIS_HARMONIZATION_COMPLETED_REVIEW_REASON
    )
    action.update(
        {
            "summary": (
                "Analysis harmonization completed a unit-harmonized external-validation rerun; "
                "request AI reviewer-owned publication_eval against the current rerun evidence."
            ),
            "next_work_unit": next_work_unit,
            "source_ref": str(result_path),
            "required_currentness_refs": required_refs,
            "paper_package_mutation_allowed": False,
            "medical_claim_authoring_allowed": False,
        }
    )
    return action


def currentness_refs(
    *,
    study_root: Path,
    result_path: Path,
    result: Mapping[str, Any],
) -> list[str]:
    refs = [str(Path(result_path).expanduser().resolve())]
    rerun_ref = _resolved_ref(study_root=study_root, value=result.get("rerun_evidence_ref"))
    if rerun_ref is not None:
        refs.append(str(rerun_ref))
    return list(dict.fromkeys(refs))


def publication_eval_covers_currentness_refs(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    required_refs: list[str],
) -> bool:
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return False
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return False
    if provenance.get("ai_reviewer_required") is not False:
        return False
    refs = publication_eval_source_refs(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    return all(ref in refs for ref in required_refs)


def publication_eval_source_refs(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> set[str]:
    refs: set[str] = set()
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    candidates = [
        *_string_items(provenance.get("source_refs")),
        *_string_items(publication_eval_payload.get("source_refs")),
        *_string_items(publication_eval_payload.get("evidence_refs")),
    ]
    quality_assessment = publication_eval_payload.get("quality_assessment")
    if isinstance(quality_assessment, Mapping):
        for dimension_payload in quality_assessment.values():
            candidates.extend(_string_items(_mapping(dimension_payload).get("evidence_refs")))
    for item in candidates:
        resolved = _resolved_ref(study_root=study_root, value=item)
        if resolved is not None:
            refs.add(str(resolved))
    return refs


def _resolved_ref(*, study_root: Path, value: object) -> Path | None:
    text = _text(value)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = Path(study_root).expanduser().resolve() / path
    return path.resolve()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "completed_ai_reviewer_action",
    "currentness_refs",
    "publication_eval_covers_currentness_refs",
    "publication_eval_source_refs",
]
