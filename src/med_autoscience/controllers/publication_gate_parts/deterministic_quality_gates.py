from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import artifact_runtime_proof


GATE_KEYS: tuple[str, ...] = (
    "citation_grounding",
    "numeric_grounding",
    "display_grounding",
    "internal_language_leakage",
    "artifact_rebuild_proof",
)

_CITATION_BLOCKERS = frozenset(
    {
        "claim_evidence_consistency_failed",
        "claim_evidence_map_missing_or_incomplete",
        "claim_evidence_map_missing",
        "evidence_ledger_missing_or_incomplete",
        "missing_claim_evidence_map",
    }
)
_NUMERIC_BLOCKERS = frozenset(
    {
        "claim_evidence_consistency_failed",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "derived_analysis_manifest_missing_or_incomplete",
        "results_narrative_map_missing_or_incomplete",
        "undefined_methodology_labels_present",
    }
)
_DISPLAY_BLOCKERS = frozenset(
    {
        "figure_catalog_missing_or_incomplete",
        "figure_semantics_manifest_missing_or_incomplete",
        "figure_layout_sidecar_missing_or_incomplete",
        "required_display_catalog_coverage_incomplete",
        "results_display_surface_incomplete",
        "submission_grade_active_figure_floor_unmet",
        "submission_surface_qc_failure_present",
        "display_registry_contract_missing",
        "display_registry_missing",
        "invalid_display_registry",
        "medical_display_registry_missing",
        "display_reporting_contract_missing",
        "registry_contract_mismatch",
    }
)
_INTERNAL_LANGUAGE_BLOCKERS = frozenset(
    {
        "forbidden_manuscript_terminology",
        "forbidden_manuscript_terms_present",
        "analysis_plane_jargon_present_on_manuscript_surface",
    }
)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _selected_blockers(*blockers: list[str], selected: frozenset[str]) -> list[str]:
    matched: list[str] = []
    for blocker in blockers:
        if blocker in selected:
            _append_unique(matched, blocker)
    return matched


def _checklist_blockers(
    checklist: Mapping[str, Any] | None,
    *,
    selected_keys: frozenset[str],
) -> list[str]:
    if checklist is None:
        return []
    blockers: list[str] = []
    for key, value in checklist.items():
        if key not in selected_keys or not isinstance(value, Mapping):
            continue
        status = _text(value.get("status"))
        if status and status not in {"pass", "passed", "clear", "ready"}:
            blockers.append(key)
    return blockers


def _gate(
    *,
    gate_key: str,
    blockers: list[str],
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    compact_evidence = [item for item in evidence_refs if item]
    return {
        "gate_key": gate_key,
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "evidence_refs": compact_evidence,
    }


def _artifact_rebuild_gate(*, study_root: Path | None) -> dict[str, Any]:
    if study_root is None:
        return _gate(
            gate_key="artifact_rebuild_proof",
            blockers=["study_root_unresolved"],
            evidence_refs=[],
        )
    proof = artifact_runtime_proof.build_artifact_runtime_proof(study_root)
    proof_blockers = [
        code
        for item in proof.get("blockers") or []
        if isinstance(item, Mapping) and (code := _text(item.get("code")))
    ]
    refs = proof.get("refs") if isinstance(proof.get("refs"), Mapping) else {}
    evidence_refs = [
        {
            "surface": proof.get("surface"),
            "rebuild_status": proof.get("rebuild_status"),
            "delivery_manifest_path": refs.get("delivery_manifest_path"),
            "source_signature": refs.get("source_signature"),
            "authority_source_signature": refs.get("authority_source_signature"),
            "authority": proof.get("authority"),
        }
    ]
    return _gate(
        gate_key="artifact_rebuild_proof",
        blockers=proof_blockers,
        evidence_refs=evidence_refs,
    )


def build_deterministic_quality_gate_projection(
    *,
    blockers: list[str],
    medical_publication_surface: dict[str, Any] | None,
    medical_publication_surface_named_blockers: list[str],
    publication_reporting_checklist: dict[str, Any] | None,
    submission_surface_qc_failures: list[dict[str, Any]],
    manuscript_terminology_violations: list[dict[str, Any]],
    blocking_artifact_refs: list[dict[str, Any]],
    active_figure_count: int | None,
    prebundle_display_advisories: list[str],
    study_root: Path | None,
) -> dict[str, Any]:
    surface_blockers = _string_list((medical_publication_surface or {}).get("blockers"))
    combined_blockers = [*blockers, *surface_blockers, *medical_publication_surface_named_blockers]
    structured_checklist = publication_reporting_checklist or {}

    citation_blockers = _selected_blockers(*combined_blockers, selected=_CITATION_BLOCKERS)
    citation_checklist_blockers = _checklist_blockers(
        structured_checklist,
        selected_keys=frozenset({"claim_evidence_alignment", "citation_grounding"}),
    )
    citation_gate = _gate(
        gate_key="citation_grounding",
        blockers=[*citation_blockers, *citation_checklist_blockers],
        evidence_refs=[
            {
                "medical_publication_surface_path": (medical_publication_surface or {}).get("report_path"),
                "claim_evidence_map_valid": (medical_publication_surface or {}).get("claim_evidence_map_valid"),
                "evidence_ledger_valid": (medical_publication_surface or {}).get("evidence_ledger_valid"),
                "blocking_artifact_refs": [
                    item
                    for item in blocking_artifact_refs
                    if str(item.get("artifact_role") or "") in {"claim_evidence_map", "evidence_ledger"}
                ],
            }
        ],
    )

    numeric_blockers = _selected_blockers(*combined_blockers, selected=_NUMERIC_BLOCKERS)
    numeric_checklist_blockers = _checklist_blockers(
        structured_checklist,
        selected_keys=frozenset({"statistical_reporting", "results_numeric_grounding"}),
    )
    numeric_gate = _gate(
        gate_key="numeric_grounding",
        blockers=[*numeric_blockers, *numeric_checklist_blockers],
        evidence_refs=[
            {
                "structured_reporting_checklist_keys": sorted(structured_checklist),
                "medical_publication_surface_status": (medical_publication_surface or {}).get("status"),
            }
        ],
    )

    display_blockers = _selected_blockers(*combined_blockers, selected=_DISPLAY_BLOCKERS)
    if submission_surface_qc_failures:
        _append_unique(display_blockers, "submission_surface_qc_failure_present")
    for advisory in prebundle_display_advisories:
        if advisory in _DISPLAY_BLOCKERS:
            _append_unique(display_blockers, advisory)
    display_gate = _gate(
        gate_key="display_grounding",
        blockers=display_blockers,
        evidence_refs=[
            {
                "active_manuscript_figure_count": active_figure_count,
                "prebundle_display_advisories": list(prebundle_display_advisories),
                "submission_surface_qc_failures": list(submission_surface_qc_failures),
                "display_artifact_refs": [
                    item
                    for item in blocking_artifact_refs
                    if "figure" in str(item.get("artifact_role") or "")
                    or "display" in str(item.get("artifact_role") or "")
                    or "submission_surface_qc" == str(item.get("artifact_role") or "")
                ],
            }
        ],
    )

    internal_language_blockers = _selected_blockers(*combined_blockers, selected=_INTERNAL_LANGUAGE_BLOCKERS)
    if manuscript_terminology_violations:
        _append_unique(internal_language_blockers, "forbidden_manuscript_terminology")
    internal_language_gate = _gate(
        gate_key="internal_language_leakage",
        blockers=internal_language_blockers,
        evidence_refs=[
            {
                "manuscript_terminology_violations": list(manuscript_terminology_violations),
            }
        ],
    )

    gates = [
        citation_gate,
        numeric_gate,
        display_gate,
        internal_language_gate,
        _artifact_rebuild_gate(study_root=study_root),
    ]
    blocker_summary = {
        str(gate["gate_key"]): list(gate["blockers"])
        for gate in gates
        if gate.get("status") == "blocked"
    }
    return {
        "schema_version": 1,
        "surface": "deterministic_quality_gate_projection",
        "authority": {
            "deterministic_projection_can_replace_ai_reviewer": False,
            "scientific_quality_authority": "publication_eval_and_controller_decisions",
        },
        "status": "blocked" if blocker_summary else "clear",
        "gates": {str(gate["gate_key"]): gate for gate in gates},
        "blocking_gate_keys": list(blocker_summary),
        "blockers": blocker_summary,
    }
