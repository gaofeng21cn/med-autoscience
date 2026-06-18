from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from med_autoscience.publication_display_contract import load_publication_style_profile


FIGURE_INTENT_BASENAME = "figure_intent.json"
MEDICAL_FIGURE_SPEC_BASENAME = "figure_spec.json"
MEDICAL_FIGURE_SPECS_BASENAME = "figure_specs.json"
PUBLICATION_STYLE_PROFILE_BASENAME = "publication_style_profile.json"
FIGURE_STYLE_REFERENCE_BUNDLE_BASENAME = "figure_style_reference_bundle.json"
FIGURE_VISUAL_AUDIT_RECEIPT_BASENAME = "figure_visual_audit_receipt.json"
FIGURE_RENDER_RECEIPT_BASENAME = "figure_render_receipt.json"
FIGURE_POLISH_LIFECYCLE_BASENAME = "figure_polish_lifecycle.json"
AI_ILLUSTRATION_RECEIPT_BASENAME = "ai_illustration_receipt.json"

VALID_FIGURE_KINDS = frozenset(("evidence_figure", "illustration_shell", "table_shell"))
VALID_REFERENCE_DECISIONS = frozenset(("like", "reject", "adopt"))
VALID_AUDIT_MODES = frozenset(("vlm_visual_verification", "human_visual_review", "hybrid_visual_review"))
VALID_SUSPECTED_LAYERS = frozenset(
    (
        "paper_input",
        "display_override",
        "publication_style_profile",
        "renderer_contract",
        "layout_qc",
        "readability_qc",
        "manuscript_surface",
    )
)
VALID_PROMOTION_DECISIONS = frozenset(
    (
        "paper_local_only",
        "promote_to_contract",
        "promote_to_qc",
        "promote_to_golden_regression",
        "needs_human_decision",
    )
)
VALID_VISUAL_AUDIT_FINAL_STATUS = frozenset(("clear", "findings_open", "blocked"))
VALID_ILLUSTRATION_ACCEPTANCE = frozenset(("ai_recommended", "human_accepted", "human_rejected"))
VALID_RENDER_BACKENDS = frozenset(("python", "r_ggplot2", "html_svg"))
VALID_RENDER_EXECUTION_MODES = frozenset(("python_plugin", "subprocess"))


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return payload


def _require_schema_version(payload: dict[str, Any], *, contract_name: str) -> None:
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError(f"{contract_name}.schema_version must be an integer")
    if schema_version != 1:
        raise ValueError(f"{contract_name}.schema_version must equal 1")


def _require_non_empty_string(item: dict[str, Any], field_name: str, *, context: str) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field_name} must be a non-empty string")
    return value.strip()


def _require_string_list(item: dict[str, Any], field_name: str, *, context: str) -> list[str]:
    value = item.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context}.{field_name} must be a non-empty list of strings")
    normalized: list[str] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{context}.{field_name}[{index}] must be a non-empty string")
        normalized.append(entry.strip())
    return normalized


def _optional_string_list(item: dict[str, Any], field_name: str, *, context: str) -> list[str]:
    value = item.get(field_name)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{context}.{field_name} must be a list of strings when provided")
    normalized: list[str] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{context}.{field_name}[{index}] must be a non-empty string")
        normalized.append(entry.strip())
    return normalized


def _require_object_list(payload: dict[str, Any], field_name: str, *, contract_name: str) -> list[dict[str, Any]]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{contract_name}.{field_name} must be a list")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{contract_name}.{field_name}[{index}] must be a JSON object")
        entries.append(dict(item))
    return entries


def _require_sha256(item: dict[str, Any], field_name: str, *, context: str) -> str:
    value = _require_non_empty_string(item, field_name, context=context)
    if len(value) != 64 or any(character not in "0123456789abcdefABCDEF" for character in value):
        raise ValueError(f"{context}.{field_name} must be a sha256 hex digest")
    return value.lower()


def _ensure_unique(values: list[str], *, field_name: str, contract_name: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"{contract_name}.{field_name} contains duplicate value `{value}`")
        seen.add(value)


def load_figure_intent(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="figure_intent")
    figures = _require_object_list(payload, "figures", contract_name="figure_intent")
    normalized_figures: list[dict[str, Any]] = []
    for index, item in enumerate(figures):
        context = f"figure_intent.figures[{index}]"
        figure_id = _require_non_empty_string(item, "figure_id", context=context)
        claim_ref = _require_non_empty_string(item, "claim_ref", context=context)
        data_ref = _require_non_empty_string(item, "data_ref", context=context)
        template_id = _require_non_empty_string(item, "template_id", context=context)
        figure_kind = _require_non_empty_string(item, "figure_kind", context=context)
        if figure_kind not in VALID_FIGURE_KINDS:
            raise ValueError(f"{context}.figure_kind must be one of {sorted(VALID_FIGURE_KINDS)!r}")
        normalized_figures.append(
            {
                **item,
                "figure_id": figure_id,
                "claim_ref": claim_ref,
                "data_ref": data_ref,
                "template_id": template_id,
                "figure_kind": figure_kind,
            }
        )
    _ensure_unique(
        [str(item["figure_id"]) for item in normalized_figures],
        field_name="figures[].figure_id",
        contract_name="figure_intent",
    )
    return {**payload, "figures": normalized_figures}


def load_figure_style_reference_bundle(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="figure_style_reference_bundle")
    bundle_id = _require_non_empty_string(payload, "bundle_id", context="figure_style_reference_bundle")
    references = _require_object_list(payload, "references", contract_name="figure_style_reference_bundle")
    normalized_refs: list[dict[str, Any]] = []
    for index, item in enumerate(references):
        context = f"figure_style_reference_bundle.references[{index}]"
        reference_id = _require_non_empty_string(item, "reference_id", context=context)
        source_ref = _require_non_empty_string(item, "source_ref", context=context)
        decision = _require_non_empty_string(item, "decision", context=context)
        if decision not in VALID_REFERENCE_DECISIONS:
            raise ValueError(f"{context}.decision must be one of {sorted(VALID_REFERENCE_DECISIONS)!r}")
        applies_to = _require_string_list(item, "applies_to", context=context)
        style_notes = _require_string_list(item, "style_notes", context=context)
        normalized_refs.append(
            {
                **item,
                "reference_id": reference_id,
                "source_ref": source_ref,
                "decision": decision,
                "applies_to": applies_to,
                "style_notes": style_notes,
            }
        )
    _ensure_unique(
        [str(item["reference_id"]) for item in normalized_refs],
        field_name="references[].reference_id",
        contract_name="figure_style_reference_bundle",
    )
    return {**payload, "bundle_id": bundle_id, "references": normalized_refs}


def load_figure_visual_audit_receipt(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="figure_visual_audit_receipt")
    receipt_id = _require_non_empty_string(payload, "receipt_id", context="figure_visual_audit_receipt")
    audit_mode = _require_non_empty_string(payload, "audit_mode", context="figure_visual_audit_receipt")
    if audit_mode not in VALID_AUDIT_MODES:
        raise ValueError(f"figure_visual_audit_receipt.audit_mode must be one of {sorted(VALID_AUDIT_MODES)!r}")
    final_status = _require_non_empty_string(payload, "final_status", context="figure_visual_audit_receipt")
    if final_status not in VALID_VISUAL_AUDIT_FINAL_STATUS:
        raise ValueError(
            "figure_visual_audit_receipt.final_status must be one of "
            f"{sorted(VALID_VISUAL_AUDIT_FINAL_STATUS)!r}"
        )

    inspected_artifacts = _require_object_list(
        payload,
        "inspected_artifacts",
        contract_name="figure_visual_audit_receipt",
    )
    normalized_artifacts: list[dict[str, Any]] = []
    for index, item in enumerate(inspected_artifacts):
        context = f"figure_visual_audit_receipt.inspected_artifacts[{index}]"
        normalized_artifacts.append(
            {
                **item,
                "figure_id": _require_non_empty_string(item, "figure_id", context=context),
                "artifact_path": _require_non_empty_string(item, "artifact_path", context=context),
                "artifact_sha256": _require_sha256(item, "artifact_sha256", context=context),
            }
        )

    findings = _require_object_list(payload, "findings", contract_name="figure_visual_audit_receipt")
    normalized_findings: list[dict[str, Any]] = []
    for index, item in enumerate(findings):
        context = f"figure_visual_audit_receipt.findings[{index}]"
        suspected_layer = _require_string_list(item, "suspected_layer", context=context)
        unknown_layers = [layer for layer in suspected_layer if layer not in VALID_SUSPECTED_LAYERS]
        if unknown_layers:
            raise ValueError(f"{context}.suspected_layer contains unknown layer `{unknown_layers[0]}`")
        promotion_decision = _require_non_empty_string(item, "promotion_decision", context=context)
        if promotion_decision not in VALID_PROMOTION_DECISIONS:
            raise ValueError(f"{context}.promotion_decision must be one of {sorted(VALID_PROMOTION_DECISIONS)!r}")
        normalized_findings.append(
            {
                **item,
                "figure_id": _require_non_empty_string(item, "figure_id", context=context),
                "observed_issue": _require_non_empty_string(item, "observed_issue", context=context),
                "paper_facing_impact": _require_non_empty_string(item, "paper_facing_impact", context=context),
                "suspected_layer": suspected_layer,
                "proposed_action": _require_non_empty_string(item, "proposed_action", context=context),
                "promotion_decision": promotion_decision,
                "verification_plan": _require_non_empty_string(item, "verification_plan", context=context),
            }
        )

    reviewer = payload.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValueError("figure_visual_audit_receipt.reviewer must be a JSON object")
    normalized_reviewer = {
        **reviewer,
        "provider": _require_non_empty_string(reviewer, "provider", context="figure_visual_audit_receipt.reviewer"),
        "model": _require_non_empty_string(reviewer, "model", context="figure_visual_audit_receipt.reviewer"),
        "prompt_hash": _require_sha256(reviewer, "prompt_hash", context="figure_visual_audit_receipt.reviewer"),
    }
    return {
        **payload,
        "receipt_id": receipt_id,
        "audit_mode": audit_mode,
        "inspected_artifacts": normalized_artifacts,
        "findings": normalized_findings,
        "reviewer": normalized_reviewer,
        "final_status": final_status,
    }


def load_ai_illustration_receipt(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="ai_illustration_receipt")
    receipt_id = _require_non_empty_string(payload, "receipt_id", context="ai_illustration_receipt")
    illustrations = _require_object_list(payload, "illustrations", contract_name="ai_illustration_receipt")
    normalized_illustrations: list[dict[str, Any]] = []
    for index, item in enumerate(illustrations):
        context = f"ai_illustration_receipt.illustrations[{index}]"
        scientific_claim_carried = item.get("scientific_claim_carried")
        if scientific_claim_carried is not False:
            raise ValueError(f"{context}.scientific_claim_carried must be false")
        acceptance = _require_non_empty_string(item, "acceptance", context=context)
        if acceptance not in VALID_ILLUSTRATION_ACCEPTANCE:
            raise ValueError(f"{context}.acceptance must be one of {sorted(VALID_ILLUSTRATION_ACCEPTANCE)!r}")
        normalized_illustrations.append(
            {
                **item,
                "figure_id": _require_non_empty_string(item, "figure_id", context=context),
                "template_id": _require_non_empty_string(item, "template_id", context=context),
                "prompt_hash": _require_sha256(item, "prompt_hash", context=context),
                "provider": _require_non_empty_string(item, "provider", context=context),
                "model": _require_non_empty_string(item, "model", context=context),
                "review_log_ref": _require_non_empty_string(item, "review_log_ref", context=context),
                "acceptance": acceptance,
                "final_export_path": _require_non_empty_string(item, "final_export_path", context=context),
                "scientific_claim_carried": False,
            }
        )
        _optional_string_list(item, "candidate_refs", context=context)
    return {**payload, "receipt_id": receipt_id, "illustrations": normalized_illustrations}


def _require_false(item: dict[str, Any], field_name: str, *, context: str) -> None:
    if item.get(field_name) is not False:
        raise ValueError(f"{context}.{field_name} must be false")


def _require_authority_boundary(item: dict[str, Any], *, context: str) -> dict[str, Any]:
    value = item.get("authority_boundary")
    if not isinstance(value, dict):
        raise ValueError(f"{context}.authority_boundary must be a JSON object")
    normalized = dict(value)
    for field_name in (
        "can_authorize_publication_readiness",
        "can_authorize_quality_verdict",
        "can_mutate_data_or_statistics",
    ):
        _require_false(normalized, field_name, context=f"{context}.authority_boundary")
    return normalized


def _require_text_mapping(item: dict[str, Any], field_name: str, *, context: str) -> dict[str, str]:
    value = item.get(field_name)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{context}.{field_name} must be a non-empty object")
    normalized: dict[str, str] = {}
    for key, entry in value.items():
        key_text = str(key or "").strip()
        entry_text = str(entry or "").strip()
        if not key_text or not entry_text:
            raise ValueError(f"{context}.{field_name} must map non-empty strings")
        normalized[key_text] = entry_text
    return normalized


def _normalize_backend(value: str, *, context: str) -> str:
    normalized = value.strip()
    if normalized not in VALID_RENDER_BACKENDS:
        raise ValueError(f"{context} must be one of {sorted(VALID_RENDER_BACKENDS)!r}")
    return normalized


def load_figure_render_receipt(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="figure_render_receipt")
    receipt_id = _require_non_empty_string(payload, "receipt_id", context="figure_render_receipt")
    figures = _require_object_list(payload, "figures", contract_name="figure_render_receipt")
    normalized_figures: list[dict[str, Any]] = []
    for index, item in enumerate(figures):
        context = f"figure_render_receipt.figures[{index}]"
        selected_backend = _normalize_backend(
            _require_non_empty_string(item, "selected_backend", context=context),
            context=f"{context}.selected_backend",
        )
        execution_mode = _require_non_empty_string(item, "execution_mode", context=context)
        if execution_mode not in VALID_RENDER_EXECUTION_MODES:
            raise ValueError(f"{context}.execution_mode must be one of {sorted(VALID_RENDER_EXECUTION_MODES)!r}")
        exclusivity = item.get("backend_exclusivity_proof")
        if not isinstance(exclusivity, dict):
            raise ValueError(f"{context}.backend_exclusivity_proof must be a JSON object")
        normalized_exclusivity = dict(exclusivity)
        exclusivity_selected_backend = _normalize_backend(
            _require_non_empty_string(
                normalized_exclusivity,
                "selected_backend",
                context=f"{context}.backend_exclusivity_proof",
            ),
            context=f"{context}.backend_exclusivity_proof.selected_backend",
        )
        observed_renderer_family = _normalize_backend(
            _require_non_empty_string(
                normalized_exclusivity,
                "observed_renderer_family",
                context=f"{context}.backend_exclusivity_proof",
            ),
            context=f"{context}.backend_exclusivity_proof.observed_renderer_family",
        )
        if exclusivity_selected_backend != selected_backend:
            raise ValueError(f"{context}.backend_exclusivity_proof.selected_backend must match selected_backend")
        _require_false(
            normalized_exclusivity,
            "cross_backend_visual_fallback_used",
            context=f"{context}.backend_exclusivity_proof",
        )
        non_selected = _optional_string_list(
            normalized_exclusivity,
            "non_selected_backend_rendered_artifacts",
            context=f"{context}.backend_exclusivity_proof",
        )
        if non_selected:
            raise ValueError(
                f"{context}.backend_exclusivity_proof.non_selected_backend_rendered_artifacts must be empty"
            )
        if observed_renderer_family != selected_backend:
            raise ValueError(f"{context}.backend_exclusivity_proof.observed_renderer_family must match selected_backend")
        source_data_refs = _require_string_list(item, "source_data_refs", context=context)
        source_data_digests = _require_text_mapping(item, "source_data_digests", context=context)
        missing_digest_refs = [ref for ref in source_data_refs if ref not in source_data_digests]
        if missing_digest_refs:
            raise ValueError(f"{context}.source_data_digests missing source data ref `{missing_digest_refs[0]}`")
        editable_text_required = item.get("editable_text_required")
        if editable_text_required is not True:
            raise ValueError(f"{context}.editable_text_required must be true")
        normalized_figures.append(
            {
                **item,
                "figure_id": _require_non_empty_string(item, "figure_id", context=context),
                "template_id": _require_non_empty_string(item, "template_id", context=context),
                "selected_backend": selected_backend,
                "execution_mode": execution_mode,
                "backend_exclusivity_proof": {
                    **normalized_exclusivity,
                    "selected_backend": selected_backend,
                    "observed_renderer_family": observed_renderer_family,
                    "cross_backend_visual_fallback_used": False,
                    "non_selected_backend_rendered_artifacts": [],
                },
                "export_formats": _require_string_list(item, "export_formats", context=context),
                "editable_text_required": True,
                "editable_text_check_ref": _require_non_empty_string(item, "editable_text_check_ref", context=context),
                "source_data_refs": source_data_refs,
                "source_data_digests": source_data_digests,
                "statistics_refs": _require_string_list(item, "statistics_refs", context=context),
                "rendered_artifact_refs": _require_string_list(item, "rendered_artifact_refs", context=context),
                "visual_qa_ref": _require_non_empty_string(item, "visual_qa_ref", context=context),
                "authority_boundary": _require_authority_boundary(item, context=context),
            }
        )
    _ensure_unique(
        [str(item["figure_id"]) for item in normalized_figures],
        field_name="figures[].figure_id",
        contract_name="figure_render_receipt",
    )
    return {
        **payload,
        "receipt_id": receipt_id,
        "figures": normalized_figures,
        "authority_boundary": _require_authority_boundary(payload, context="figure_render_receipt"),
    }


def _load_medical_figure_spec(path: Path) -> dict[str, Any]:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    return load_medical_figure_spec(path)


def _load_medical_figure_specs(path: Path) -> dict[str, Any]:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_specs

    return load_medical_figure_specs(path)


def _load_figure_polish_lifecycle(path: Path) -> dict[str, Any]:
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle

    return load_figure_polish_lifecycle(path)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_to_workspace(path: Path, *, paper_root: Path) -> str:
    workspace_root = paper_root.resolve().parent
    return path.resolve().relative_to(workspace_root).as_posix()


def _surface_ref(
    *,
    paper_root: Path,
    basename: str,
    loader: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    path = paper_root / basename
    ref: dict[str, Any] = {
        "path": f"paper/{basename}",
        "status": "missing",
    }
    if not path.exists():
        return ref
    loader(path)
    ref["status"] = "present"
    ref["path"] = _relative_to_workspace(path, paper_root=paper_root)
    ref["sha256"] = _sha256_file(path)
    return ref


def collect_publication_figure_quality_refs(*, paper_root: Path) -> dict[str, dict[str, Any]]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    return {
        "figure_intent": _surface_ref(
            paper_root=resolved_paper_root,
            basename=FIGURE_INTENT_BASENAME,
            loader=load_figure_intent,
        ),
        "medical_figure_spec": _surface_ref(
            paper_root=resolved_paper_root,
            basename=MEDICAL_FIGURE_SPEC_BASENAME,
            loader=_load_medical_figure_spec,
        ),
        "medical_figure_specs": _surface_ref(
            paper_root=resolved_paper_root,
            basename=MEDICAL_FIGURE_SPECS_BASENAME,
            loader=_load_medical_figure_specs,
        ),
        "publication_style_profile": _surface_ref(
            paper_root=resolved_paper_root,
            basename=PUBLICATION_STYLE_PROFILE_BASENAME,
            loader=load_publication_style_profile,
        ),
        "figure_style_reference_bundle": _surface_ref(
            paper_root=resolved_paper_root,
            basename=FIGURE_STYLE_REFERENCE_BUNDLE_BASENAME,
            loader=load_figure_style_reference_bundle,
        ),
        "figure_visual_audit_receipt": _surface_ref(
            paper_root=resolved_paper_root,
            basename=FIGURE_VISUAL_AUDIT_RECEIPT_BASENAME,
            loader=load_figure_visual_audit_receipt,
        ),
        "figure_render_receipt": _surface_ref(
            paper_root=resolved_paper_root,
            basename=FIGURE_RENDER_RECEIPT_BASENAME,
            loader=load_figure_render_receipt,
        ),
        "figure_polish_lifecycle": _surface_ref(
            paper_root=resolved_paper_root,
            basename=FIGURE_POLISH_LIFECYCLE_BASENAME,
            loader=_load_figure_polish_lifecycle,
        ),
        "ai_illustration_receipt": _surface_ref(
            paper_root=resolved_paper_root,
            basename=AI_ILLUSTRATION_RECEIPT_BASENAME,
            loader=load_ai_illustration_receipt,
        ),
    }
