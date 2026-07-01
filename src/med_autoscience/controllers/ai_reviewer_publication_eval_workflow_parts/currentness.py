from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import paper_authority_migration
from med_autoscience.controllers.ai_reviewer_story_provenance_guard import (
    reject_manuscript_story_provenance_leakage,
)
from med_autoscience.medical_prose_review_request import (
    materialize_medical_prose_review_request,
    stable_medical_prose_review_request_path,
)
from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)

_CURRENT_MANUSCRIPT_RECORD_WORK_UNITS = frozenset(
    {
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    }
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


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


def _reject_manuscript_story_provenance_leakage(*, field_path: str, text: str) -> None:
    reject_manuscript_story_provenance_leakage(field_path=field_path, text=text)


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


def _record_current_manuscript_payload(record_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    reviewer_os = _mapping(record_payload.get("reviewer_operating_system"))
    currentness = _mapping(reviewer_os.get("currentness_checks"))
    current_manuscript = _mapping(currentness.get("current_manuscript"))
    if _text(current_manuscript.get("status")) != "current":
        return {}
    return current_manuscript


def _record_is_current_manuscript_review(record_payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(record_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer" or provenance.get("ai_reviewer_required") is not False:
        return False
    if _text(provenance.get("source_kind")) == "publication_eval_ai_reviewer_current_manuscript_record":
        return True
    owner_route_basis = _mapping(provenance.get("owner_route_currentness_basis"))
    work_unit_id = _text(provenance.get("work_unit_id")) or _text(owner_route_basis.get("work_unit_id"))
    return work_unit_id in _CURRENT_MANUSCRIPT_RECORD_WORK_UNITS


def _record_publication_quality_readiness(record_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    reviewer_os = _mapping(record_payload.get("reviewer_operating_system"))
    return _mapping(reviewer_os.get("publication_quality_readiness"))


def _sci_clinical_registry_review(record_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_review = record_payload.get("sci_clinical_registry_review")
    if not isinstance(raw_review, list) or not raw_review:
        raise ValueError("AI reviewer publication eval workflow missing sci_clinical_registry_review")
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    review_contract = _mapping(contract.get("sci_clinical_registry_review"))
    required_fields = tuple(_text(item) for item in _list(review_contract.get("required_fields")) if _text(item))
    required_domains = {_text(item) for item in _list(review_contract.get("required_domains")) if _text(item)}
    review: list[dict[str, Any]] = []
    covered_domains: set[str] = set()
    for index, raw_item in enumerate(raw_review):
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"AI reviewer publication eval workflow sci_clinical_registry_review[{index}] must be an object")
        item = dict(raw_item)
        for field in required_fields:
            if field == "evidence_refs":
                if not _list(item.get(field)):
                    raise ValueError(
                        "AI reviewer publication eval workflow "
                        f"sci_clinical_registry_review[{index}].{field} missing"
                    )
                continue
            if not _text(item.get(field)):
                raise ValueError(
                    "AI reviewer publication eval workflow "
                    f"sci_clinical_registry_review[{index}].{field} missing"
                )
        domain = _text(item.get("domain"))
        if domain:
            covered_domains.add(domain)
        review.append(item)
    missing_domains = sorted(required_domains - covered_domains)
    if missing_domains:
        raise ValueError(
            "AI reviewer publication eval workflow sci_clinical_registry_review missing domains: "
            + ", ".join(missing_domains)
        )
    return review


def _sci_registry_review_blockers(review: list[Mapping[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for item in review:
        severity = _text(item.get("severity"))
        status = _text(item.get("status"))
        if severity in {"blocker", "major"} or status in {"blocked", "major_concern"}:
            concern_id = _text(item.get("concern_id")) or _text(item.get("domain")) or "sci_clinical_registry_review"
            blockers.append(f"sci_clinical_registry_review::{concern_id}")
    return blockers


def _current_manuscript_currentness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any] | None:
    record_current_manuscript = _record_current_manuscript_payload(record_payload)
    if _record_embeds_ai_reviewer_output(workflow_currentness_mode) and record_current_manuscript:
        manuscript_ref = _text(record_current_manuscript.get("manuscript_ref"))
        manuscript_input_ref = _text(ref_bundle.get("manuscript"))
        if manuscript_ref and manuscript_input_ref and not _refs_match(
            study_root=study_root,
            left=manuscript_input_ref,
            right=manuscript_ref,
        ):
            raise ValueError("ai_reviewer_record_current_manuscript_ref_mismatch")
        return _live_manuscript_currentness(study_root=study_root, ref_bundle=ref_bundle) | {
            "authority_source_signature": "request_bound_ai_reviewer_record_live_manuscript"
        }
    if not record_current_manuscript and _record_is_current_manuscript_review(record_payload):
        return _live_manuscript_currentness(study_root=study_root, ref_bundle=ref_bundle) | {
            "authority_source_signature": "ai_reviewer_current_manuscript_record"
        }
    if not record_current_manuscript:
        return None
    manuscript_ref = _text(record_current_manuscript.get("manuscript_ref")) or _text(ref_bundle.get("manuscript"))
    manuscript_digest = _text(record_current_manuscript.get("manuscript_digest"))
    if not manuscript_ref:
        raise ValueError("ai_reviewer_record_current_manuscript_ref_missing")
    if not manuscript_digest:
        raise ValueError("ai_reviewer_record_current_manuscript_digest_missing")
    manuscript_input_ref = _text(ref_bundle.get("manuscript"))
    if manuscript_input_ref and not _refs_match(
        study_root=study_root,
        left=manuscript_input_ref,
        right=manuscript_ref,
    ):
        raise ValueError("ai_reviewer_record_current_manuscript_ref_mismatch")
    live_manuscript_path = _resolve_ref(study_root=study_root, ref=manuscript_ref)
    if _sha256_file(live_manuscript_path) != manuscript_digest:
        raise ValueError("ai_reviewer_record_current_manuscript_digest_mismatch")
    result = dict(record_current_manuscript)
    result["status"] = "current"
    result["manuscript_ref"] = manuscript_ref
    result["manuscript_digest"] = manuscript_digest
    result["authority_source_signature"] = _text(
        result.get("authority_source_signature")
    ) or "ai_reviewer_record_current_manuscript"
    return result


def _live_manuscript_currentness(
    *,
    study_root: Path,
    ref_bundle: Mapping[str, str],
) -> dict[str, Any]:
    manuscript_ref = _text(ref_bundle.get("manuscript"))
    if not manuscript_ref:
        raise ValueError("AI reviewer publication eval workflow missing manuscript")
    manuscript_path = _resolve_ref(study_root=study_root, ref=manuscript_ref)
    return {
        "status": "current",
        "manuscript_ref": manuscript_ref,
        "manuscript_digest": _sha256_file(manuscript_path),
        "authority_source_signature": "ai_reviewer_workflow_live_manuscript",
    }


def _live_input_currentness(
    *,
    study_root: Path,
    ref_bundle: Mapping[str, str],
    surface: str,
) -> dict[str, Any]:
    ref = _text(ref_bundle.get(surface))
    if not ref:
        raise ValueError(f"AI reviewer publication eval workflow missing {surface}")
    path = _resolve_ref(study_root=study_root, ref=ref)
    return {
        "status": "current",
        "ref": ref,
        "digest": _sha256_file(path),
        "authority_source_signature": "ai_reviewer_workflow_live_input",
    }


def _generic_live_ref_currentness(
    *,
    study_root: Path,
    surface: str,
    ref: object,
) -> dict[str, Any] | None:
    text_ref = _text(ref)
    if not text_ref:
        return None
    path = _resolve_ref(study_root=study_root, ref=text_ref)
    if not path.exists():
        return None
    return {
        "status": "current",
        "ref": text_ref,
        "digest": _sha256_file(path),
        "authority_source_signature": f"ai_reviewer_workflow_live_input:{surface}",
    }


def _publication_quality_readiness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
    trace: Mapping[str, Any],
) -> dict[str, Any]:
    currentness = _mapping(trace.get("currentness_checks"))
    prose_currentness = _mapping(currentness.get("medical_prose_review"))
    current_manuscript = _mapping(currentness.get("current_manuscript"))
    input_bundle = _mapping(trace.get("input_bundle"))
    evidence_ref = _text(input_bundle.get("evidence_ledger"))
    if not evidence_ref:
        raise ValueError("ai_reviewer_record_evidence_ledger_ref_missing")
    evidence_digest = _sha256_file(_resolve_ref(study_root=study_root, ref=evidence_ref))
    claim_alignment = _mapping(trace.get("claim_evidence_alignment"))
    claim_alignment_digest = "sha256:" + hashlib.sha256(
        json.dumps(claim_alignment, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    eval_id = _text(record_payload.get("eval_id")) or "unknown-eval"
    manuscript_digest = _text(current_manuscript.get("manuscript_digest")) or _text(
        prose_currentness.get("manuscript_digest")
    )
    request_digest = _text(prose_currentness.get("request_digest"))
    computed_required_fields = {
        "current_manuscript_digest": manuscript_digest,
        "review_request_digest": request_digest,
        "evidence_ledger_digest": evidence_digest,
        "claim_evidence_alignment_digest": claim_alignment_digest if _text(claim_alignment.get("status")) == "ready" else "",
    }
    base_missing = [field for field, value in computed_required_fields.items() if not value]
    computed_present_fields = {
        field
        for field, value in computed_required_fields.items()
        if value
    }
    record_readiness = _record_publication_quality_readiness(record_payload)
    record_missing = [
        _text(item)
        for item in _list(record_readiness.get("missing_required_fields"))
        if _text(item) and _text(item) not in computed_present_fields
    ]
    sci_registry_review = [
        dict(item) for item in _list(trace.get("sci_clinical_registry_review")) if isinstance(item, Mapping)
    ]
    sci_registry_blockers = _sci_registry_review_blockers(sci_registry_review)
    missing = list(dict.fromkeys([*base_missing, *record_missing, *sci_registry_blockers]))
    record_status = _text(record_readiness.get("status"))
    status = "ready" if not missing else "blocked"
    if record_status == "blocked":
        status = "blocked"
    elif record_status == "ready" and base_missing:
        status = "blocked"
    if status == "blocked" and not missing:
        missing.append("claim_evidence_alignment_digest")
    return {
        "surface_kind": "publication_quality_authority_kernel_v1",
        "status": status,
        "current_manuscript_digest": manuscript_digest,
        "review_request_digest": request_digest,
        "evidence_ledger_digest": evidence_digest,
        "claim_evidence_alignment_digest": claim_alignment_digest,
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
            record_payload=record_payload,
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
    current_manuscript = _current_manuscript_currentness(
        study_root=study_root,
        record_payload=record_payload,
        ref_bundle=ref_bundle,
        workflow_currentness_mode="request_bound_ai_reviewer_record",
    )
    request_manuscript_ref = _text(provenance.get("manuscript_ref")) or _text(ref_bundle.get("manuscript"))
    request_manuscript_digest = _text(provenance.get("manuscript_digest"))
    if not request_digest:
        raise ValueError("medical_prose_review_request_digest_missing")
    if not request_manuscript_ref:
        raise ValueError("medical_prose_review_manuscript_ref_missing")
    if not request_manuscript_digest:
        raise ValueError("medical_prose_review_manuscript_digest_missing")

    request_ref = _text(provenance.get("request_ref")) or str(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    )
    request_path = _resolve_ref(study_root=study_root, ref=request_ref)
    request_payload = _read_json(request_path)
    current_request_digest = _text(request_payload.get("request_digest"))
    current_manuscript_payload = _mapping(current_manuscript)
    durable_review_status: str | None = None
    if current_request_digest and current_request_digest != request_digest:
        if not current_manuscript_payload:
            raise ValueError("medical_prose_review_request_digest_mismatch")
        durable_review_status = "stale_for_current_request"
    request_manuscript = _mapping(request_payload.get("manuscript"))
    request_payload_manuscript_ref = _text(request_manuscript.get("path"))
    request_payload_manuscript_digest = _text(request_manuscript.get("digest"))
    current_record_manuscript_ref = _text(current_manuscript_payload.get("manuscript_ref"))
    current_record_manuscript_digest = _text(current_manuscript_payload.get("manuscript_digest"))
    if current_manuscript_payload:
        if request_payload_manuscript_ref and current_record_manuscript_ref and not _refs_match(
            study_root=study_root,
            left=request_payload_manuscript_ref,
            right=current_record_manuscript_ref,
        ):
            raise ValueError("medical_prose_review_request_current_manuscript_ref_mismatch")
        if (
            request_payload_manuscript_digest
            and current_record_manuscript_digest
            and request_payload_manuscript_digest != current_record_manuscript_digest
        ):
            durable_review_status = durable_review_status or "stale_for_live_manuscript"
    else:
        if request_payload_manuscript_ref and not _refs_match(
            study_root=study_root,
            left=request_payload_manuscript_ref,
            right=request_manuscript_ref,
        ):
            raise ValueError("medical_prose_review_manuscript_ref_mismatch")
        if request_payload_manuscript_digest and request_payload_manuscript_digest != request_manuscript_digest:
            raise ValueError("medical_prose_review_manuscript_digest_mismatch")

    quality_assessment = _mapping(record_payload.get("quality_assessment"))
    record_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    prose_quality = _mapping(prose_payload.get("medical_journal_prose_quality"))
    prose_route_back = _mapping(prose_quality.get("route_back_recommendation"))
    route_target = _record_route_target(record_payload) or _text(prose_route_back.get("route_target"))
    manuscript_ref = current_record_manuscript_ref or request_manuscript_ref
    manuscript_digest = current_record_manuscript_digest or request_manuscript_digest
    result = {
        "status": "current",
        "ref": str(prose_path),
        "request_ref": str(request_path),
        "request_digest": current_request_digest or request_digest,
        "manuscript_ref": manuscript_ref,
        "manuscript_digest": manuscript_digest,
        "review_request_manuscript_ref": request_manuscript_ref,
        "review_request_manuscript_digest": request_manuscript_digest,
        "prose_status": _text(record_quality.get("status")) or _text(prose_quality.get("status")),
        "overall_style_verdict": _text(prose_quality.get("overall_style_verdict")),
        "route_back_required": True,
        "route_target": route_target,
        "authority_source_signature": "ai_reviewer_record_current_manuscript"
        if current_manuscript is not None
        else "ai_reviewer_request_record",
    }
    if durable_review_status is not None:
        result["durable_medical_prose_review_status"] = durable_review_status
        result["review_request_digest"] = request_digest
    return result


def _clean_migration_medical_prose_review_request_currentness(
    *,
    study_root: Path,
    record_payload: Mapping[str, Any],
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
    route_target = "review"
    if _record_routes_back_before_delivery(record_payload):
        route_target = _record_route_target(record_payload) or route_target
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
        "route_target": route_target,
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
    checks: dict[str, Any] = {
        "medical_prose_review": _medical_prose_review_currentness(
            study_root=study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
            workflow_currentness_mode=workflow_currentness_mode,
        ),
        "source_eval": {
            "status": "current",
            "eval_id": eval_id,
        },
        "current_package_freshness": _current_package_freshness(
            study_root=study_root,
            eval_id=eval_id,
            delivery_downstream_only=_record_routes_back_before_delivery(record_payload),
        ),
        "evidence_ledger": _live_input_currentness(
            study_root=study_root,
            ref_bundle=ref_bundle,
            surface="evidence_ledger",
        ),
        "claim_evidence_map": _live_input_currentness(
            study_root=study_root,
            ref_bundle=ref_bundle,
            surface="claim_evidence_map",
        ),
    }
    for surface, ref in ref_bundle.items():
        if surface in checks:
            continue
        if surface in {"owner_route_currentness_basis"}:
            continue
        if generic_check := _generic_live_ref_currentness(
            study_root=study_root,
            surface=surface,
            ref=ref,
        ):
            checks[surface] = generic_check
    current_manuscript = _current_manuscript_currentness(
        study_root=study_root,
        record_payload=record_payload,
        ref_bundle=ref_bundle,
        workflow_currentness_mode=workflow_currentness_mode,
    )
    if current_manuscript is not None:
        checks["current_manuscript"] = current_manuscript
    else:
        checks["current_manuscript"] = _live_manuscript_currentness(
            study_root=study_root,
            ref_bundle=ref_bundle,
        )
    return checks
