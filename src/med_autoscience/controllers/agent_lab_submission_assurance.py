from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def build_submission_assurance_surfaces(
    *,
    root: Path,
    study_id: str,
    authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    citation_paths = (
        resolved_root / "paper" / "citation_audit.json",
        resolved_root / "artifacts" / "citation_audit" / "latest.json",
        resolved_root / "paper" / "references" / "citation_audit.json",
    )
    counterargument_paths = (
        resolved_root / "paper" / "kill_argument_review.json",
        resolved_root / "paper" / "strongest_counterargument.json",
        resolved_root / "artifacts" / "counterargument_review" / "latest.json",
        resolved_root / "paper" / "review" / "review_ledger.json",
    )
    submission_gate_paths = (
        resolved_root / "artifacts" / "submission_assurance" / "latest.json",
        resolved_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        resolved_root / "artifacts" / "publication_gate" / "latest.json",
        resolved_root / "artifacts" / "submission_targets" / "latest.json",
        resolved_root / "paper" / "anonymity_check.json",
    )
    effort_paths = (
        resolved_root / "artifacts" / "analysis_queue" / "latest.json",
        resolved_root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        resolved_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        resolved_root / "artifacts" / "runtime" / "provider_state.json",
    )
    citation_payloads = _payloads(citation_paths)
    counterargument_payloads = _payloads(counterargument_paths)
    submission_gate_payloads = _payloads(submission_gate_paths)
    effort_payloads = _payloads(effort_paths)

    citation_audit_refs = _existing_refs(*citation_paths)
    counterargument_review_refs = _existing_refs(*counterargument_paths)
    submission_assurance_refs = _existing_refs(*submission_gate_paths)
    effort_source_refs = _existing_refs(*effort_paths)
    citation_refs = _refs_for_keys(
        citation_payloads,
        (
            "citation_refs",
            "reference_refs",
            "bibliography_refs",
            "source_refs",
            "evidence_refs",
            "items",
        ),
    )
    missing_citation_refs = _refs_for_keys(
        citation_payloads,
        ("missing_citation_refs", "unsupported_claim_refs", "citation_gap_refs", "gap_refs"),
    )
    kill_argument_refs = _refs_for_keys(
        counterargument_payloads,
        ("kill_argument_refs", "fatal_objection_refs", "disqualifying_argument_refs"),
    )
    strongest_counterargument_refs = _refs_for_keys(
        counterargument_payloads,
        ("strongest_counterargument_refs", "counterargument_refs", "reviewer_concern_refs", "review_refs"),
    )
    gate_layers = _submission_assurance_layers(
        payloads=submission_gate_payloads,
        study_id=study_id,
    )
    assurance_refs = _unique_refs(
        [
            *citation_audit_refs,
            *counterargument_review_refs,
            *submission_assurance_refs,
            *citation_refs,
            *missing_citation_refs,
            *kill_argument_refs,
            *strongest_counterargument_refs,
            *[ref for layer in gate_layers for ref in layer["source_refs"]],
        ]
    )
    effort_refs = _unique_refs(
        [
            *effort_source_refs,
            *_refs_for_keys(
                effort_payloads,
                (
                    "queue_ref",
                    "task_refs",
                    "work_unit_refs",
                    "items",
                    "retry_refs",
                    "budget_refs",
                    "provider_refs",
                    "source_refs",
                ),
            ),
        ]
    )
    citation_audit = {
        "surface_kind": "mas_agent_lab_citation_audit",
        "audit_kind": "body_free_citation_audit_refs",
        "body_included": False,
        "citation_body_included": False,
        "can_authorize_citation_correctness": False,
        "can_authorize_quality_verdict": False,
        "citation_audit_refs": citation_audit_refs,
        "citation_refs": citation_refs or [f"citation-ref:mas/{study_id}/body-free-missing"],
        "missing_citation_refs": missing_citation_refs,
        "citation_ref_count": len(citation_refs),
        "missing_citation_ref_count": len(missing_citation_refs),
        "authority_boundary": dict(authority_boundary),
    }
    kill_argument_review = {
        "surface_kind": "mas_agent_lab_kill_argument_review",
        "review_kind": "body_free_kill_argument_and_strongest_counterargument_refs",
        "body_included": False,
        "claim_body_included": False,
        "review_body_included": False,
        "can_authorize_claim": False,
        "can_authorize_quality_verdict": False,
        "counterargument_review_refs": counterargument_review_refs,
        "kill_argument_refs": kill_argument_refs
        or [f"kill-argument-ref:mas/{study_id}/body-free-missing"],
        "strongest_counterargument_refs": strongest_counterargument_refs
        or [f"strongest-counterargument-ref:mas/{study_id}/body-free-missing"],
        "authority_boundary": dict(authority_boundary),
    }
    submission_assurance_gate = {
        "surface_kind": "mas_agent_lab_submission_assurance_gate",
        "gate_kind": "body_free_five_layer_submission_assurance_gate",
        "body_included": False,
        "can_authorize_publication_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mutate_submission_package": False,
        "gate_refs": submission_assurance_refs,
        "gate_layers": gate_layers,
        "required_layer_count": 5,
        "layer_count": len(gate_layers),
        "authority_boundary": dict(authority_boundary),
    }
    effort_assurance_axes = {
        "surface_kind": "mas_agent_lab_effort_assurance_axes",
        "axis_kind": "body_free_effort_assurance_mechanism_inputs",
        "body_included": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "effort_refs": effort_refs or [f"effort-ref:mas/{study_id}/body-free-missing"],
        "assurance_refs": assurance_refs or [f"assurance-ref:mas/{study_id}/body-free-missing"],
        "axis_input_refs": _unique_refs([*effort_refs, *assurance_refs]),
        "authority_boundary": dict(authority_boundary),
    }
    evidence_delta_refs = _unique_refs(
        [
            *citation_audit_refs,
            *counterargument_review_refs,
            *submission_assurance_refs,
            *effort_source_refs,
            *citation_refs,
            *missing_citation_refs,
            *kill_argument_refs,
            *strongest_counterargument_refs,
            *[ref for layer in gate_layers for ref in layer["source_refs"]],
            *effort_refs,
            *assurance_refs,
        ]
    )
    return {
        "citation_audit": citation_audit,
        "kill_argument_review": kill_argument_review,
        "submission_assurance_gate": submission_assurance_gate,
        "effort_assurance_axes": effort_assurance_axes,
        "evidence_delta_refs": evidence_delta_refs,
    }


def _submission_assurance_layers(
    *,
    payloads: list[dict[str, Any]],
    study_id: str,
) -> list[dict[str, Any]]:
    layer_names = (
        "citation_audit",
        "kill_argument_review",
        "evidence_claim_alignment",
        "submission_hygiene",
        "independent_reviewer_assurance",
    )
    layer_refs = {
        name: _refs_for_keys(
            payloads,
            (
                f"{name}_refs",
                f"{name}_ref",
                "gate_refs",
                "check_refs",
                "source_refs",
                "items",
            ),
        )
        for name in layer_names
    }
    return [
        {
            "layer_id": f"submission-assurance-layer:mas/{study_id}/{name}",
            "layer_name": name,
            "body_included": False,
            "source_refs": refs or [f"submission-assurance-ref:mas/{study_id}/{name}/body-free-missing"],
            "can_authorize_submission_readiness": False,
            "can_authorize_quality_verdict": False,
        }
        for name, refs in layer_refs.items()
    ]


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
        item_ref = _item_ref(value)
        if item_ref:
            refs.append(item_ref)
        for key in (
            "refs",
            "items",
            "source_refs",
            "evidence_refs",
            "review_refs",
            "reviewer_refs",
            "citation_refs",
            "reference_refs",
            "claim_refs",
            "gate_refs",
            "check_refs",
        ):
            refs.extend(_refs_from_value(value.get(key)))
        return _unique_refs(refs)
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_refs_from_value(item))
        return _unique_refs(refs)
    ref = _text(value)
    return [ref] if ref and ":" in ref else []


def _item_ref(item: Mapping[str, Any]) -> str:
    for key in (
        "ref",
        "id",
        "citation_ref",
        "reference_ref",
        "source_ref",
        "evidence_ref",
        "review_ref",
        "reviewer_ref",
        "claim_ref",
        "gate_ref",
        "check_ref",
        "layer_ref",
        "task_ref",
        "work_unit_ref",
        "queue_ref",
        "provider_ref",
    ):
        value = _text(item.get(key))
        if value:
            return value
    return ""


def _text(value: object) -> str:
    return str(value or "").strip()


def _unique_refs(refs: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        text = str(ref).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


__all__ = ["build_submission_assurance_surfaces"]
