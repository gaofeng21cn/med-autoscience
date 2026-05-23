from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)
from med_autoscience.publication_eval_latest import (
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.controllers import paper_authority_migration
from med_autoscience.controllers.ai_reviewer_story_provenance_guard import (
    MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS,
    reject_manuscript_story_provenance_leakage,
)
from med_autoscience.medical_prose_review_request import (
    materialize_medical_prose_review_request,
    stable_medical_prose_review_request_path,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord

__all__ = [
    "build_ai_reviewer_publication_eval_workflow_trace",
    "run_ai_reviewer_publication_eval_workflow",
]


_SURFACE = "ai_reviewer_publication_eval_workflow"
_SCHEMA_VERSION = 1
_REF_ALIASES = {
    "manuscript_ref": "manuscript",
    "evidence_ref": "evidence_ledger",
    "review_ref": "review_ledger",
    "charter_ref": "study_charter",
}
_REQUIRED_TRACE_INPUTS = (
    "manuscript",
    "study_charter",
    "evidence_ledger",
    "review_ledger",
)
_MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS = MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"AI reviewer publication eval workflow ref is not a JSON object: {path}")
    return dict(payload)


def _resolve_ref(*, study_root: Path, ref: str | Path) -> Path:
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (study_root / candidate).resolve()


def _refs_match(*, study_root: Path, left: str, right: str) -> bool:
    return _resolve_ref(study_root=study_root, ref=left) == _resolve_ref(
        study_root=study_root,
        ref=right,
    )


def _sha256_file(path: Path) -> str:
    if not path.exists():
        raise ValueError("medical_prose_review_live_manuscript_missing")
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _record_payload(record: PublicationEvalRecord | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, PublicationEvalRecord):
        return record.to_dict()
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("AI reviewer publication eval workflow record must be a mapping or PublicationEvalRecord")


def _normalize_ref_bundle(
    *,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    additional_refs: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    refs: dict[str, str] = {}
    for field_name, surface in _REF_ALIASES.items():
        raw_value = {
            "manuscript_ref": manuscript_ref,
            "evidence_ref": evidence_ref,
            "review_ref": review_ref,
            "charter_ref": charter_ref,
        }[field_name]
        value = _text(raw_value)
        if not value:
            raise ValueError(f"AI reviewer publication eval workflow missing {field_name}")
        refs[surface] = value
    for key, value in _mapping(additional_refs).items():
        surface = _text(key)
        ref = _text(value)
        if surface and ref:
            refs[surface] = ref
    return refs


def _quality_assessment(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        raise ValueError("AI reviewer publication eval workflow record missing quality_assessment")
    return quality_assessment


def _dimension_payloads(record_payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    quality_assessment = _quality_assessment(record_payload)
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    dimensions: dict[str, Mapping[str, Any]] = {}
    for dimension in contract["rubric_dimensions"]:
        payload = quality_assessment.get(dimension)
        if not isinstance(payload, Mapping):
            raise ValueError(f"AI reviewer publication eval workflow record missing quality dimension {dimension}")
        dimensions[dimension] = payload
    return dimensions


def _dimension_evidence_refs(
    *,
    dimension_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
) -> list[str]:
    refs = [_text(item) for item in _list(dimension_payload.get("evidence_refs")) if _text(item)]
    if refs:
        return refs
    return [ref_bundle[surface] for surface in _REQUIRED_TRACE_INPUTS if surface in ref_bundle]


def _reject_manuscript_story_provenance_leakage(*, field_path: str, text: str) -> None:
    reject_manuscript_story_provenance_leakage(field_path=field_path, text=text)


def _rubric_scores_and_decision_matrix(
    *,
    dimensions: Mapping[str, Mapping[str, Any]],
    ref_bundle: Mapping[str, str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rubric_scores: dict[str, dict[str, Any]] = {}
    decision_matrix: list[dict[str, Any]] = []
    for dimension, payload in dimensions.items():
        status = _text(payload.get("status"))
        summary = _text(payload.get("summary"))
        rationale = _text(payload.get("reviewer_reason")) or summary
        if not status:
            raise ValueError(f"AI reviewer publication eval workflow quality dimension {dimension} missing status")
        if not rationale:
            raise ValueError(f"AI reviewer publication eval workflow quality dimension {dimension} missing rationale")
        if dimension in _MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS:
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.summary",
                text=summary,
            )
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.reviewer_reason",
                text=rationale,
            )
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.reviewer_revision_advice",
                text=_text(payload.get("reviewer_revision_advice")),
            )
        evidence_refs = _dimension_evidence_refs(dimension_payload=payload, ref_bundle=ref_bundle)
        rubric_scores[dimension] = {
            "status": status,
            "rationale": rationale,
            "evidence_refs": evidence_refs,
        }
        decision_matrix.append(
            {
                "dimension": dimension,
                "status": status,
                "rationale": rationale,
            }
        )
    return rubric_scores, decision_matrix


def _route_back_decision(record_payload: Mapping[str, Any]) -> dict[str, str]:
    recommended_action = "continue_same_line"
    route_rationale = "AI reviewer publication eval workflow trace is complete."
    actions = [item for item in _list(record_payload.get("recommended_actions")) if isinstance(item, Mapping)]
    if actions:
        recommended_action = _text(actions[0].get("action_type")) or _text(actions[0].get("action_id")) or recommended_action
        route_rationale = _text(actions[0].get("reason")) or route_rationale
    return {
        "recommended_action": recommended_action,
        "rationale": route_rationale,
    }


def _record_routes_back_before_delivery(record_payload: Mapping[str, Any]) -> bool:
    for action in _list(record_payload.get("recommended_actions")):
        if not isinstance(action, Mapping):
            continue
        action_type = _text(action.get("action_type"))
        route_target = _text(action.get("route_target"))
        if action_type in {"route_back_same_line", "bounded_analysis", "stop_loss"}:
            return True
        if route_target in {"analysis-campaign", "review", "controller", "stop"}:
            return True
    return False


def _record_route_target(record_payload: Mapping[str, Any]) -> str | None:
    for action in _list(record_payload.get("recommended_actions")):
        if not isinstance(action, Mapping):
            continue
        if route_target := _text(action.get("route_target")):
            return route_target
    return None


def _publication_quality_readiness(
    *,
    record_payload: Mapping[str, Any],
    trace: Mapping[str, Any],
) -> dict[str, Any]:
    currentness = _mapping(trace.get("currentness_checks"))
    prose_currentness = _mapping(currentness.get("medical_prose_review"))
    evidence_ledger = _mapping(record_payload.get("quality_assessment"))
    evidence_digest = "sha256:" + hashlib.sha256(
        json.dumps(evidence_ledger, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    eval_id = _text(record_payload.get("eval_id")) or "unknown-eval"
    manuscript_digest = _text(prose_currentness.get("manuscript_digest"))
    request_digest = _text(prose_currentness.get("request_digest"))
    missing = [
        field
        for field, value in (
            ("current_manuscript_digest", manuscript_digest),
            ("review_request_digest", request_digest),
            ("evidence_ledger_digest", evidence_digest),
        )
        if not value
    ]
    return {
        "surface_kind": "publication_quality_authority_kernel_v1",
        "status": "ready" if not missing else "blocked",
        "current_manuscript_digest": manuscript_digest,
        "review_request_digest": request_digest,
        "evidence_ledger_digest": evidence_digest,
        "rubric_version": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
        "owner_attempt_id": f"ai-reviewer-publication-eval::{eval_id}",
        "fail_closed_when_missing": True,
        "missing_required_fields": missing,
    }


def _future_facing_limitations_plan(record_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_plan = record_payload.get("future_facing_limitations_plan")
    if not isinstance(raw_plan, list) or not raw_plan:
        raise ValueError("AI reviewer publication eval workflow missing future_facing_limitations_plan")
    plan: list[dict[str, Any]] = []
    for index, raw_item in enumerate(raw_plan):
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"AI reviewer publication eval workflow future_facing_limitations_plan[{index}] must be an object")
        item = dict(raw_item)
        for field in (
            "limitation",
            "impact_on_claim",
            "required_future_analysis_data_or_design",
        ):
            if not _text(item.get(field)):
                raise ValueError(
                    "AI reviewer publication eval workflow "
                    f"future_facing_limitations_plan[{index}].{field} missing"
                )
        if "current_manuscript_wording_must_be_restrained" not in item:
            raise ValueError(
                "AI reviewer publication eval workflow "
                "future_facing_limitations_plan"
                f"[{index}].current_manuscript_wording_must_be_restrained missing"
            )
        for field in (
            "limitation",
            "impact_on_claim",
            "required_future_analysis_data_or_design",
        ):
            _reject_manuscript_story_provenance_leakage(
                field_path=f"future_facing_limitations_plan[{index}].{field}",
                text=_text(item.get(field)),
            )
        plan.append(item)
    return plan


def _medical_prose_review_currentness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    if paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return _clean_migration_medical_prose_review_request_currentness(
            study_root=study_root,
            ref_bundle=ref_bundle,
        )
    if _record_embeds_ai_reviewer_output(workflow_currentness_mode):
        return _record_bound_medical_prose_review_currentness(
            study_root=study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
        )
    prose_ref = _text(ref_bundle.get("medical_prose_review"))
    if not prose_ref:
        raise ValueError("AI reviewer publication eval workflow missing medical_prose_review")
    prose_path = _resolve_ref(study_root=study_root, ref=prose_ref)
    prose_payload = _read_json(prose_path)
    provenance = _mapping(prose_payload.get("assessment_provenance"))
    request_digest = _text(provenance.get("request_digest"))
    manuscript_ref = _text(provenance.get("manuscript_ref"))
    manuscript_digest = _text(provenance.get("manuscript_digest"))
    if not request_digest:
        raise ValueError("medical_prose_review_request_digest_missing")
    if not manuscript_ref:
        raise ValueError("medical_prose_review_manuscript_ref_missing")
    if not manuscript_digest:
        raise ValueError("medical_prose_review_manuscript_digest_missing")

    request_ref = _text(provenance.get("request_ref")) or str(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    )
    request_payload = _read_json(_resolve_ref(study_root=study_root, ref=request_ref))
    current_request_digest = _text(request_payload.get("request_digest"))
    if current_request_digest and current_request_digest != request_digest:
        raise ValueError("medical_prose_review_request_digest_mismatch")
    request_manuscript = _mapping(request_payload.get("manuscript"))
    request_manuscript_ref = _text(request_manuscript.get("path"))
    request_manuscript_digest = _text(request_manuscript.get("digest"))
    if request_manuscript_ref and not _refs_match(
        study_root=study_root,
        left=request_manuscript_ref,
        right=manuscript_ref,
    ):
        raise ValueError("medical_prose_review_manuscript_ref_mismatch")
    if request_manuscript_digest and request_manuscript_digest != manuscript_digest:
        raise ValueError("medical_prose_review_manuscript_digest_mismatch")
    manuscript_input_ref = _text(ref_bundle.get("manuscript"))
    if manuscript_input_ref and not _refs_match(
        study_root=study_root,
        left=manuscript_input_ref,
        right=manuscript_ref,
    ):
        raise ValueError("medical_prose_review_reviewer_os_manuscript_ref_mismatch")
    live_manuscript_path = _resolve_ref(study_root=study_root, ref=manuscript_input_ref or manuscript_ref)
    if _sha256_file(live_manuscript_path) != manuscript_digest:
        raise ValueError("medical_prose_review_live_manuscript_digest_mismatch")

    quality = _mapping(prose_payload.get("medical_journal_prose_quality"))
    route_back = _mapping(quality.get("route_back_recommendation"))

    return {
        "status": "current",
        "ref": str(prose_path),
        "request_ref": str(_resolve_ref(study_root=study_root, ref=request_ref)),
        "request_digest": request_digest,
        "manuscript_ref": manuscript_ref,
        "manuscript_digest": manuscript_digest,
        "prose_status": _text(quality.get("status")),
        "overall_style_verdict": _text(quality.get("overall_style_verdict")),
        "route_back_required": route_back.get("required") is True,
        "route_target": _text(route_back.get("route_target")),
    }


def _record_embeds_ai_reviewer_output(workflow_currentness_mode: str | None) -> bool:
    return workflow_currentness_mode == "request_bound_ai_reviewer_record"


def _record_bound_medical_prose_review_currentness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
) -> dict[str, Any]:
    if _record_routes_back_before_delivery(record_payload):
        return _route_back_record_medical_prose_review_currentness(
            study_root=study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
        )
    currentness = _medical_prose_review_currentness(
        study_root=study_root,
        record_payload=record_payload,
        ref_bundle=ref_bundle,
        workflow_currentness_mode=None,
    )
    route_back_required = currentness.get("route_back_required") is True or _record_routes_back_before_delivery(
        record_payload
    )
    route_target = _text(currentness.get("route_target")) or _record_route_target(record_payload)
    return {
        **currentness,
        "route_back_required": route_back_required,
        "route_target": route_target,
        "authority_source_signature": "ai_reviewer_request_record",
    }


def _route_back_record_medical_prose_review_currentness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
) -> dict[str, Any]:
    prose_ref = _text(ref_bundle.get("medical_prose_review"))
    if not prose_ref:
        raise ValueError("AI reviewer publication eval workflow missing medical_prose_review")
    prose_path = _resolve_ref(study_root=study_root, ref=prose_ref)
    prose_payload = _read_json(prose_path)
    provenance = _mapping(prose_payload.get("assessment_provenance"))
    request_digest = _text(provenance.get("request_digest"))
    manuscript_ref = _text(provenance.get("manuscript_ref")) or _text(ref_bundle.get("manuscript"))
    manuscript_digest = _text(provenance.get("manuscript_digest"))
    if not request_digest:
        raise ValueError("medical_prose_review_request_digest_missing")
    if not manuscript_ref:
        raise ValueError("medical_prose_review_manuscript_ref_missing")
    if not manuscript_digest:
        raise ValueError("medical_prose_review_manuscript_digest_missing")

    request_ref = _text(provenance.get("request_ref")) or str(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    )
    request_path = _resolve_ref(study_root=study_root, ref=request_ref)
    request_payload = _read_json(request_path)
    current_request_digest = _text(request_payload.get("request_digest"))
    if current_request_digest and current_request_digest != request_digest:
        raise ValueError("medical_prose_review_request_digest_mismatch")
    request_manuscript = _mapping(request_payload.get("manuscript"))
    request_manuscript_ref = _text(request_manuscript.get("path"))
    request_manuscript_digest = _text(request_manuscript.get("digest"))
    if request_manuscript_ref and not _refs_match(
        study_root=study_root,
        left=request_manuscript_ref,
        right=manuscript_ref,
    ):
        raise ValueError("medical_prose_review_manuscript_ref_mismatch")
    if request_manuscript_digest and request_manuscript_digest != manuscript_digest:
        raise ValueError("medical_prose_review_manuscript_digest_mismatch")

    quality_assessment = _mapping(record_payload.get("quality_assessment"))
    record_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    prose_quality = _mapping(prose_payload.get("medical_journal_prose_quality"))
    prose_route_back = _mapping(prose_quality.get("route_back_recommendation"))
    route_target = _record_route_target(record_payload) or _text(prose_route_back.get("route_target"))
    return {
        "status": "current",
        "ref": str(prose_path),
        "request_ref": str(request_path),
        "request_digest": request_digest,
        "manuscript_ref": manuscript_ref,
        "manuscript_digest": manuscript_digest,
        "prose_status": _text(record_quality.get("status")) or _text(prose_quality.get("status")),
        "overall_style_verdict": _text(prose_quality.get("overall_style_verdict")),
        "route_back_required": True,
        "route_target": route_target,
        "authority_source_signature": "ai_reviewer_request_record",
    }


def _clean_migration_medical_prose_review_request_currentness(
    *,
    study_root: Path,
    ref_bundle: Mapping[str, str],
) -> dict[str, Any]:
    request_path = stable_medical_prose_review_request_path(study_root=study_root)
    materialize_medical_prose_review_request(study_root=study_root)
    request_payload = _read_json(request_path)
    request_digest = _text(request_payload.get("request_digest"))
    if not request_digest:
        raise ValueError("medical_prose_review_request_digest_missing")
    request_manuscript = _mapping(request_payload.get("manuscript"))
    manuscript_ref = _text(request_manuscript.get("path"))
    manuscript_digest = _text(request_manuscript.get("digest"))
    if not manuscript_ref:
        raise ValueError("medical_prose_review_request_manuscript_ref_missing")
    if not manuscript_digest:
        raise ValueError("medical_prose_review_request_manuscript_digest_missing")
    manuscript_input_ref = _text(ref_bundle.get("manuscript"))
    if manuscript_input_ref and not _refs_match(
        study_root=study_root,
        left=manuscript_input_ref,
        right=manuscript_ref,
    ):
        raise ValueError("medical_prose_review_request_manuscript_ref_mismatch")
    return {
        "status": "requested",
        "ref": _text(ref_bundle.get("medical_prose_review")),
        "request_ref": str(request_path.resolve()),
        "request_digest": request_digest,
        "manuscript_ref": manuscript_ref,
        "manuscript_digest": manuscript_digest,
        "prose_status": "underdefined",
        "overall_style_verdict": "review_required",
        "route_back_required": True,
        "route_target": "review",
        "authority_source_signature": "paper_authority_clean_migration",
    }


def _current_package_freshness(
    *,
    study_root: Path,
    eval_id: str,
    delivery_downstream_only: bool = False,
) -> dict[str, Any]:
    path = study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    if paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return {
            "status": "fresh",
            "ref": str(paper_authority_migration.paper_authority_cutover_latest_path(study_root=study_root)),
            "source_eval_id": eval_id,
            "current_package_root": None,
            "current_package_zip": None,
            "source_signature": None,
            "authority_source_signature": "paper_authority_clean_migration",
        }
    if delivery_downstream_only:
        return {
            "status": "downstream_pending",
            "ref": str(path.resolve()),
            "source_eval_id": eval_id,
            "current_package_root": None,
            "current_package_zip": None,
            "source_signature": None,
            "authority_source_signature": "ai_reviewer_route_back_delivery_downstream_only",
        }
    if not path.exists():
        raise ValueError("current_package_freshness_missing")
    payload = _read_json(path)
    if _text(payload.get("status")) != "fresh":
        raise ValueError("current_package_freshness_not_fresh")
    source_eval_id = _text(payload.get("source_eval_id"))
    if source_eval_id != eval_id:
        raise ValueError("current_package_freshness_source_eval_id_mismatch")
    if not (_text(payload.get("current_package_root")) or _text(payload.get("current_package_zip"))):
        raise ValueError("current_package_freshness_missing_package_ref")
    return {
        "status": "fresh",
        "ref": str(path.resolve()),
        "source_eval_id": source_eval_id,
        "current_package_root": _text(payload.get("current_package_root")),
        "current_package_zip": _text(payload.get("current_package_zip")),
        "source_signature": _text(payload.get("source_signature")),
        "authority_source_signature": _text(payload.get("authority_source_signature")),
    }


def _currentness_checks(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    eval_id = _text(record_payload.get("eval_id"))
    if not eval_id:
        raise ValueError("AI reviewer publication eval workflow record missing eval_id")
    return {
        "medical_prose_review": _medical_prose_review_currentness(
            study_root=study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
            workflow_currentness_mode=workflow_currentness_mode,
        ),
        "current_package_freshness": _current_package_freshness(
            study_root=study_root,
            eval_id=eval_id,
            delivery_downstream_only=_record_routes_back_before_delivery(record_payload),
        ),
    }


def _record_payload_without_workflow_only_fields(record_payload: Mapping[str, Any]) -> dict[str, Any]:
    return dict(record_payload)


def build_ai_reviewer_publication_eval_workflow_trace(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    record_payload = _record_payload(record)
    ref_bundle = _normalize_ref_bundle(
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        additional_refs=additional_refs,
    )
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    dimensions = _dimension_payloads(record_payload)
    for surface in contract["required_input_surfaces"]:
        if surface not in ref_bundle:
            raise ValueError(f"AI reviewer publication eval workflow missing input ref for {surface}")

    rubric_scores, decision_matrix = _rubric_scores_and_decision_matrix(
        dimensions=dimensions,
        ref_bundle=ref_bundle,
    )

    trace = {
        "contract_id": contract["contract_id"],
        "input_bundle": ref_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": decision_matrix,
        "currentness_checks": _currentness_checks(
            study_root=resolved_study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
            workflow_currentness_mode=workflow_currentness_mode,
        ),
        "future_facing_limitations_plan": _future_facing_limitations_plan(record_payload),
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": _route_back_decision(record_payload),
    }
    trace["publication_quality_readiness"] = _publication_quality_readiness(
        record_payload=record_payload,
        trace=trace,
    )
    errors = validate_ai_reviewer_operating_system_trace(trace)
    if errors:
        raise ValueError("AI reviewer publication eval workflow reviewer OS trace invalid: " + "; ".join(errors))
    return trace


def _record_with_trace(
    *,
    record: PublicationEvalRecord | Mapping[str, Any],
    trace: Mapping[str, Any],
    emitted_at: str | None = None,
) -> dict[str, Any]:
    payload = _record_payload_without_workflow_only_fields(_record_payload(record))
    if emitted_at is not None:
        payload["emitted_at"] = emitted_at
    payload["reviewer_operating_system"] = dict(trace)
    provenance = dict(_mapping(payload.get("assessment_provenance")))
    provenance["owner"] = "ai_reviewer"
    provenance["source_kind"] = "publication_eval_ai_reviewer"
    provenance["policy_id"] = DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]
    provenance["ai_reviewer_required"] = False
    payload["assessment_provenance"] = provenance
    workflow_ref = _mapping(payload.get("reviewer_operating_system")).get("input_bundle")
    publication_gate_projection_ref = _text(_mapping(workflow_ref).get("publication_gate_projection"))
    if publication_gate_projection_ref:
        provenance["source_refs"] = list(
            dict.fromkeys([*(_list(provenance.get("source_refs"))), publication_gate_projection_ref])
        )
    return payload


def run_ai_reviewer_publication_eval_workflow(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    trace = build_ai_reviewer_publication_eval_workflow_trace(
        study_root=resolved_study_root,
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        record=record,
        additional_refs=additional_refs,
        workflow_currentness_mode=workflow_currentness_mode,
    )
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=_record_with_trace(record=record, trace=trace, emitted_at=_utc_now()),
    )
    paper_authority_migration.mark_cutover_new_mas_authority_established(
        study_root=resolved_study_root,
        publication_eval_ref=materialized["artifact_path"],
        eval_id=materialized["eval_id"],
    )
    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "status": "materialized",
        "study_root": str(resolved_study_root),
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
        "artifact_path": materialized["artifact_path"],
        "eval_id": materialized["eval_id"],
        "reviewer_operating_system": trace,
    }
