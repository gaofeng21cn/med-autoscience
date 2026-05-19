from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def build_aris_followup_assurance_surfaces(
    *,
    root: Path,
    study_id: str,
    publication_eval_path: Path,
    task_intake_path: Path,
    analysis_queue_manifest_refs: list[str],
    authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    raw_evidence_paths = (
        resolved_root / "artifacts" / "raw_evidence" / "latest.json",
        resolved_root / "artifacts" / "raw_evidence" / "manifest.json",
        resolved_root / "artifacts" / "evidence" / "raw" / "latest.json",
    )
    evidence_ledger_paths = (
        resolved_root / "paper" / "evidence_ledger.json",
        resolved_root / "manuscript" / "evidence_ledger.json",
    )
    review_ledger_paths = (
        resolved_root / "paper" / "review" / "review_ledger.json",
        resolved_root / "paper" / "review_ledger.json",
        resolved_root / "manuscript" / "review_ledger.json",
    )
    publication_gate_paths = (
        resolved_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        resolved_root / "artifacts" / "publication_gate" / "latest.json",
        publication_eval_path,
    )
    campaign_queue_paths = (
        resolved_root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        resolved_root / "artifacts" / "analysis_campaign" / "latest_manifest.json",
        resolved_root / "artifacts" / "analysis_queue" / "latest.json",
        resolved_root / "paper" / "analysis_queue.json",
    )
    citation_audit_paths = (
        resolved_root / "paper" / "citation_audit.json",
        resolved_root / "artifacts" / "citation_audit" / "latest.json",
        resolved_root / "artifacts" / "citation_integrity" / "latest.json",
    )
    kill_argument_paths = (
        resolved_root / "paper" / "kill_argument.json",
        resolved_root / "paper" / "counterargument_audit.json",
        resolved_root / "artifacts" / "kill_argument" / "latest.json",
        resolved_root / "artifacts" / "counterargument_audit" / "latest.json",
    )
    raw_evidence_payloads = _payloads(raw_evidence_paths)
    evidence_ledger_payloads = _payloads(evidence_ledger_paths)
    review_ledger_payloads = _payloads(review_ledger_paths)
    publication_gate_payloads = _payloads(publication_gate_paths)
    campaign_queue_payloads = _payloads(campaign_queue_paths)
    citation_audit_payloads = _payloads(citation_audit_paths)
    kill_argument_payloads = _payloads(kill_argument_paths)

    raw_evidence_refs = _existing_refs(*raw_evidence_paths)
    evidence_ledger_refs = _existing_refs(*evidence_ledger_paths)
    review_ledger_refs = _existing_refs(*review_ledger_paths)
    publication_gate_refs = _existing_refs(*publication_gate_paths)
    campaign_queue_refs = _unique_refs([*analysis_queue_manifest_refs, *_existing_refs(*campaign_queue_paths)])
    citation_audit_refs = _existing_refs(*citation_audit_paths)
    kill_argument_refs = _existing_refs(*kill_argument_paths)
    raw_evidence_item_refs = _refs_for_keys(
        raw_evidence_payloads,
        (
            "raw_evidence_refs",
            "raw_refs",
            "raw_artifact_refs",
            "source_refs",
            "artifact_refs",
            "items",
        ),
    )
    evidence_item_refs = _unique_refs(
        [
            *_refs_for_keys(
                evidence_ledger_payloads,
                (
                    "evidence_refs",
                    "evidence_items",
                    "supporting_evidence_refs",
                    "source_refs",
                    "items",
                ),
            ),
            *_refs_for_keys(publication_gate_payloads, ("evidence_refs", "source_refs")),
        ]
    )
    review_item_refs = _unique_refs(
        [
            *_refs_for_keys(
                review_ledger_payloads,
                (
                    "review_refs",
                    "reviewer_refs",
                    "review_items",
                    "reviewer_concern_refs",
                    "concern_refs",
                    "items",
                ),
            ),
            *_refs_for_keys(publication_gate_payloads, ("review_refs", "reviewer_refs")),
        ]
    )
    publication_gate_evidence_refs = _refs_for_keys(publication_gate_payloads, ("evidence_refs", "source_refs"))
    mechanism_patch_refs = _unique_refs(
        [
            *_refs_for_keys(review_ledger_payloads, ("mechanism_patch_refs", "patch_refs", "route_back_refs")),
            *_refs_for_keys(publication_gate_payloads, ("mechanism_patch_refs", "patch_refs", "route_back_refs")),
            *_refs_for_keys(campaign_queue_payloads, ("mechanism_patch_refs", "patch_refs", "route_back_refs")),
        ]
    )
    queue_items = _queue_items(campaign_queue_payloads)
    queue_item_refs = _unique_refs([item["ref"] for item in queue_items])
    queue_source_refs = _unique_refs(ref for item in queue_items for ref in item["source_refs"])
    blocked_queue_item_refs = _unique_refs(item["ref"] for item in queue_items if item["state"] == "blocked")
    citation_item_refs = _refs_for_keys(
        citation_audit_payloads,
        (
            "citation_refs",
            "citation_audit_refs",
            "missing_citation_refs",
            "unsupported_citation_refs",
            "items",
        ),
    )
    kill_argument_item_refs = _refs_for_keys(
        kill_argument_payloads,
        (
            "kill_argument_refs",
            "counterargument_refs",
            "strongest_counterargument_refs",
            "unresolved_argument_refs",
            "items",
        ),
    )

    assurance_contract = {
        "surface_kind": "mas_agent_lab_assurance_contract",
        "contract_kind": "body_free_raw_evidence_review_publication_gate_contract",
        "body_included": False,
        "raw_evidence_body_included": False,
        "review_ledger_body_included": False,
        "publication_gate_body_included": False,
        "raw_evidence_refs": raw_evidence_refs,
        "evidence_ledger_refs": evidence_ledger_refs,
        "review_ledger_refs": review_ledger_refs,
        "publication_gate_refs": publication_gate_refs,
        "task_intake_refs": _existing_refs(task_intake_path),
        "raw_evidence_item_refs": raw_evidence_item_refs
        or [f"raw-evidence-ref:mas/{study_id}/body-free-missing"],
        "evidence_item_refs": evidence_item_refs,
        "review_item_refs": review_item_refs,
        "publication_gate_evidence_refs": publication_gate_evidence_refs,
        "mechanism_patch_refs": mechanism_patch_refs,
        "promotion_input_ref_policy": "refs_and_counts_only_no_mas_truth_authority",
        "raw_evidence_ref_count": len(raw_evidence_item_refs),
        "evidence_item_ref_count": len(evidence_item_refs),
        "review_item_ref_count": len(review_item_refs),
        "publication_gate_ref_count": len(publication_gate_refs),
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_action": False,
        "authority_boundary": dict(authority_boundary),
    }
    adversarial_review_gate = {
        "surface_kind": "mas_agent_lab_adversarial_review_gate",
        "gate_kind": "independent_reviewer_body_free_mechanism_gate",
        "body_included": False,
        "independent_ai_reviewer_required": True,
        "executor_context_reuse_allowed": False,
        "reviewer_receipt_required": True,
        "can_promote_mechanism_patch": False,
        "can_authorize_quality_verdict": False,
        "review_ledger_refs": review_ledger_refs,
        "review_ledger_item_refs": review_item_refs,
        "publication_gate_refs": publication_gate_refs,
        "publication_gate_evidence_refs": publication_gate_evidence_refs,
        "raw_evidence_item_refs": raw_evidence_item_refs,
        "mechanism_patch_refs": mechanism_patch_refs,
        "promotion_gate_inputs": [
            f"ai-reviewer-receipt:mas/{study_id}/mechanism-direct-evidence-review",
            f"promotion-gate:mas/{study_id}/high-quality-medical-manuscript",
        ],
        "forbidden_writes": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "manuscript/current_package",
            "paper/submission_minimal",
        ],
        "authority_boundary": dict(authority_boundary),
    }
    experiment_queue_recovery = {
        "surface_kind": "mas_agent_lab_experiment_queue_recovery",
        "recovery_kind": "body_free_analysis_campaign_queue_recovery",
        "queue_kind": "body_free_analysis_campaign_queue_recovery",
        "body_included": False,
        "experiment_queue_recovery_refs": [
            f"experiment-queue-recovery:mas/{study_id}/analysis-campaign-redrive"
        ],
        "campaign_queue_refs": campaign_queue_refs,
        "queue_refs": campaign_queue_refs,
        "state_refs": blocked_queue_item_refs,
        "retry_refs": queue_item_refs,
        "retry_reason_refs": blocked_queue_item_refs,
        "resource_failure_refs": [],
        "wave_gate_refs": [],
        "stale_worker_cleanup_refs": [],
        "crash_recovery_refs": [],
        "budget_guard_refs": [],
        "queue_item_refs": queue_item_refs
        or [f"analysis-campaign-item:mas/{study_id}/body-free-missing"],
        "blocked_queue_item_refs": blocked_queue_item_refs,
        "queue_source_refs": queue_source_refs,
        "raw_evidence_item_refs": raw_evidence_item_refs,
        "review_item_refs": review_item_refs,
        "requires_owner_receipt": True,
        "can_authorize_analysis_completion": False,
        "can_authorize_quality_verdict": False,
        "recovery_route_ref": f"analysis-campaign-recovery:mas/{study_id}/mechanism-evidence-redrive",
        "authority_boundary": dict(authority_boundary),
    }
    citation_audit = {
        "surface_kind": "mas_agent_lab_citation_audit",
        "audit_kind": "body_free_citation_integrity_audit",
        "body_included": False,
        "citation_body_included": False,
        "citation_audit_refs": citation_audit_refs,
        "citation_item_refs": citation_item_refs or [f"citation-audit-ref:mas/{study_id}/body-free-missing"],
        "requires_independent_ai_review": True,
        "can_authorize_bibliography_quality": False,
        "can_authorize_publication_quality": False,
        "authority_boundary": dict(authority_boundary),
    }
    kill_argument = {
        "surface_kind": "mas_agent_lab_kill_argument_audit",
        "audit_kind": "body_free_strongest_counterargument_audit",
        "body_included": False,
        "argument_body_included": False,
        "kill_argument_refs": kill_argument_refs,
        "counterargument_item_refs": kill_argument_item_refs
        or [f"kill-argument-ref:mas/{study_id}/body-free-missing"],
        "requires_independent_ai_review": True,
        "can_authorize_claim": False,
        "can_authorize_quality_verdict": False,
        "authority_boundary": dict(authority_boundary),
    }
    submission_assurance = {
        "surface_kind": "mas_agent_lab_submission_assurance_gate",
        "gate_kind": "body_free_five_layer_submission_assurance",
        "body_included": False,
        "effort_level": "deep_when_publication_gate_or_counterargument_refs_exist",
        "assurance_level": "strict_independent_review_required",
        "layers": [
            "experiment_audit",
            "result_to_claim_audit",
            "paper_claim_audit",
            "citation_audit",
            "kill_argument_audit",
        ],
        "required_ref_groups": [
            "raw_evidence_refs",
            "evidence_item_refs",
            "review_item_refs",
            "citation_item_refs",
            "counterargument_item_refs",
        ],
        "can_authorize_submission_readiness": False,
        "can_authorize_publication_quality": False,
        "authority_boundary": dict(authority_boundary),
    }
    return {
        "assurance_contract": assurance_contract,
        "adversarial_review_gate": adversarial_review_gate,
        "experiment_queue_recovery": experiment_queue_recovery,
        "citation_audit": citation_audit,
        "kill_argument": kill_argument,
        "submission_assurance": submission_assurance,
        "evidence_delta_refs": _unique_refs(
            [
                *raw_evidence_refs,
                *evidence_ledger_refs,
                *review_ledger_refs,
                *publication_gate_refs,
                *campaign_queue_refs,
                *raw_evidence_item_refs,
                *evidence_item_refs,
                *review_item_refs,
                *publication_gate_evidence_refs,
                *mechanism_patch_refs,
                *queue_item_refs,
                *blocked_queue_item_refs,
                *queue_source_refs,
                *citation_audit_refs,
                *citation_item_refs,
                *kill_argument_refs,
                *kill_argument_item_refs,
            ]
        ),
    }


def _payloads(paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    return [payload for payload in (_read_json_object(path) for path in paths) if payload]


def _existing_refs(*paths: Path) -> list[str]:
    return _unique_refs([str(path) for path in paths if path.exists()])


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _refs_for_keys(payloads: list[dict[str, Any]], keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        for key in keys:
            refs.extend(_refs_from_value(payload.get(key)))
    return _unique_refs(refs)


def _refs_from_value(value: object) -> list[str]:
    if isinstance(value, Mapping):
        refs: list[str] = []
        ref = _item_ref(value)
        if ref:
            refs.append(ref)
        for key in (
            "refs",
            "items",
            "source_refs",
            "evidence_refs",
            "review_refs",
            "reviewer_refs",
            "raw_evidence_refs",
            "artifact_refs",
            "claims",
            "events",
        ):
            refs.extend(_refs_from_value(value.get(key)))
        return _unique_refs(refs)
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_refs_from_value(item))
        return _unique_refs(refs)
    ref = _text(value)
    return [ref] if ref else []


def _queue_items(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for payload in payloads:
        for key in ("items", "queue_items", "analysis_items"):
            value = payload.get(key)
            if not isinstance(value, list):
                continue
            for item in value:
                if not isinstance(item, Mapping):
                    continue
                ref = _item_ref(item)
                if not ref:
                    continue
                items.append(
                    {
                        "ref": ref,
                        "state": _text(item.get("state") or item.get("status")) or "blocked",
                        "source_refs": _refs_from_value(item.get("source_refs")),
                    }
                )
    return _unique_queue_items(items)


def _item_ref(item: Mapping[str, Any]) -> str:
    for key in (
        "ref",
        "id",
        "item_ref",
        "queue_item_ref",
        "evidence_ref",
        "review_ref",
        "claim_ref",
        "artifact_ref",
        "source_ref",
    ):
        value = _text(item.get(key))
        if value:
            return value
    return ""


def _text(value: object) -> str:
    text = str(value or "").strip()
    return text


def _unique_refs(refs: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        text = str(ref).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


def _unique_queue_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        ref = str(item["ref"])
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(item)
    return unique
