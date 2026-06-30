from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import json
import shutil
import subprocess
from typing import Any

from med_autoscience.display_layout_qc.router import QC_PROFILE_RUNNERS
from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
from med_autoscience.display_pack_loader import (
    LoadedDisplayTemplate,
    load_enabled_local_display_template_records,
)
from med_autoscience.display_pack_canonical_catalog import (
    CanonicalTemplateCatalog,
    CanonicalTemplateEntry,
    canonical_catalog_entry_for_template,
    load_canonical_template_catalog,
)
from med_autoscience.display_pack_agent_parts.figure_contract import (
    compile_display_figure_intent,
    figure_contract_policy,
    figure_policy_surfaces,
)
from med_autoscience.display_pack_agent_parts.figure_workflow import (
    build_planning_figure_workflow_packet,
    display_pack_agent_receipt_refs,
)
from med_autoscience.display_pack_agent_parts.composition_recipe_projection import composition_recipe_discovery_payload
from med_autoscience.display_pack_agent_parts.analysis_boundary import (
    analysis_blocker_for_template_summary,
    analysis_finding_from_blocker,
    analysis_template_surface_policy_flags,
    missing_input_repair_routes,
)
from med_autoscience.display_pack_agent_parts.template_fit import (
    hard_compatible,
    has_semantic_fit_anchor,
    minimum_fit_floor,
    score_template,
    template_fit_entry,
    template_sort_key,
)
from med_autoscience.display_pack_agent_parts.visual_audit import default_visual_audit_review
from med_autoscience.display_pack_renderer_policy import (
    default_surface_renderer_policy,
    renderer_policy_completion,
    renderer_policy_payload,
)
from med_autoscience.display_pack_analysis_responsibility import (
    analysis_boundary_payload,
)
from med_autoscience.display_pack_dependency_environment import (
    dependency_requirements_for_records,
    dependency_environment_finding,
    dependency_environment_status,
)
from med_autoscience.display_pack_usability import scaffold_display_pack_render
from med_autoscience.publication_display_contract import load_publication_style_profile


AGENT_CAPABILITY_ACTIONS = tuple(
    f"display-pack-{name}"
    for name in ("capability-discover", "figure-plan", "preflight", "render", "orchestrate")
)

DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
    "can_emit_display_refs_and_receipts": True,
}

@dataclass(frozen=True)
class _RendererPolicyProjection:
    kind: str
    renderer_family: str
    default_visible: bool
    canonical_family_id: str
    canonical_template_id: str
    template_id: str


def _normal_repo_root(repo_root: Path | str | None) -> Path:
    return Path(repo_root or ".").expanduser().resolve()


def _normal_optional_path(value: Path | str | None) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    return Path(text).expanduser().resolve() if text else None


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


_PURPOSE_BRIEF_ANCHOR_KEYS = (
    "intent",
    "figure_goal",
    "claim_role",
    "core_conclusion",
    "query",
    "audit_family",
    "medical_figure_family_id",
    "input_schema_ref",
)


def _full_template_id(record: LoadedDisplayTemplate) -> str:
    return record.template_manifest.full_template_id


def _catalogs_by_pack_root(records: list[LoadedDisplayTemplate]) -> dict[Path, CanonicalTemplateCatalog | None]:
    catalogs: dict[Path, CanonicalTemplateCatalog | None] = {}
    for record in records:
        if record.pack_root not in catalogs:
            catalogs[record.pack_root] = load_canonical_template_catalog(record.pack_root)
    return catalogs


def _migration_index_from_catalogs(
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None],
) -> dict[str, CanonicalTemplateEntry]:
    entries: dict[str, CanonicalTemplateEntry] = {}
    for catalog in catalogs.values():
        if catalog is None:
            continue
        entries.update(catalog.entries_by_template_id)
    return entries


def _canonical_entry(
    record: LoadedDisplayTemplate,
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None] | None = None,
) -> CanonicalTemplateEntry:
    manifest = record.template_manifest
    catalog = catalogs.get(record.pack_root) if catalogs is not None else load_canonical_template_catalog(record.pack_root)
    return canonical_catalog_entry_for_template(
        catalog=catalog,
        template_id=manifest.template_id,
        category=manifest.audit_family,
        title=manifest.display_name,
    )


def _renderer_policy_projection(
    record: LoadedDisplayTemplate,
    canonical: CanonicalTemplateEntry,
) -> _RendererPolicyProjection:
    manifest = record.template_manifest
    return _RendererPolicyProjection(
        kind=manifest.kind,
        renderer_family=manifest.renderer_family,
        default_visible=canonical.default_visible,
        canonical_family_id=canonical.family_id,
        canonical_template_id=canonical.canonical_template_id,
        template_id=manifest.template_id,
    )


def _template_summary(
    record: LoadedDisplayTemplate,
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None] | None = None,
    request: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    manifest = record.template_manifest
    template_root = record.template_path.parent
    canonical = _canonical_entry(record, catalogs)
    request_payload = dict(request or {})
    return {
        "pack_id": record.pack_manifest.pack_id,
        "pack_version": record.pack_manifest.version,
        "template_id": manifest.template_id,
        "full_template_id": manifest.full_template_id,
        "kind": manifest.kind,
        "display_name": manifest.display_name,
        "display_class_id": manifest.display_class_id,
        "audit_family": manifest.audit_family,
        "paper_family_ids": list(manifest.paper_family_ids),
        "renderer_family": manifest.renderer_family,
        "execution_mode": manifest.execution_mode,
        "entrypoint": manifest.entrypoint,
        "input_schema_ref": manifest.input_schema_ref,
        "qc_profile_ref": manifest.qc_profile_ref,
        "required_exports": list(manifest.required_exports),
        "allowed_paper_roles": list(manifest.allowed_paper_roles),
        "paper_proven": manifest.paper_proven,
        "canonical_family_id": canonical.family_id,
        "canonical_family_title": canonical.family_title,
        "canonical_family_category": canonical.family_category,
        "canonical_template_id": canonical.canonical_template_id,
        "figure_archetype": canonical.figure_archetype,
        "analysis_responsibility": canonical.analysis_responsibility,
        "analysis_input_state": canonical.analysis_input_state,
        "medical_family_ids": list(canonical.medical_family_ids),
        "publication_quality_profile": dict(canonical.publication_quality_profile),
        "analysis_boundary": analysis_boundary_payload(
            mode=canonical.analysis_responsibility,
            input_state=canonical.analysis_input_state,
            request=request_payload,
        ),
        "migration_status": canonical.migration_status,
        "default_visible": canonical.default_visible,
        "migrated_alias_template_ids": list(canonical.aliases) if canonical.migration_status == "canonical" else [],
        "migration_reason": canonical.migration_reason,
        "renderer_policy": renderer_policy_payload(_renderer_policy_projection(record, canonical)),
        "dependency_requirements": dependency_requirements_for_records(
            repo_root=repo_root or record.pack_root,
            records=[record],
        ),
        "has_render_r": (template_root / "render.R").is_file(),
        "has_render_candidate": (template_root / "render_candidate.R").is_file(),
        "golden_case_count": len(manifest.golden_case_paths),
        "exemplar_ref_count": len(manifest.exemplar_refs),
    }


def _inventory_summary(records: list[LoadedDisplayTemplate]) -> dict[str, Any]:
    kinds = Counter(record.template_manifest.kind for record in records)
    renderers = Counter(record.template_manifest.renderer_family for record in records)
    execution_modes = Counter(record.template_manifest.execution_mode for record in records)
    catalogs = _catalogs_by_pack_root(records)
    canonical_entries = [_canonical_entry(record, catalogs) for record in records]
    renderer_policy_records = [
        _renderer_policy_projection(record, canonical)
        for record, canonical in zip(records, canonical_entries, strict=True)
    ]
    canonical_template_count = sum(1 for entry in canonical_entries if entry.migration_status == "canonical")
    legacy_alias_count = sum(1 for entry in canonical_entries if entry.migration_status == "migrated_alias")
    default_visible_count = sum(1 for entry in canonical_entries if entry.default_visible)
    paper_proven_count = sum(1 for record in records if record.template_manifest.paper_proven)
    golden_template_count = sum(1 for record in records if record.template_manifest.golden_case_paths)
    exemplar_template_count = sum(1 for record in records if record.template_manifest.exemplar_refs)
    return {
        "template_count": len(records),
        "active_template_count": len(records),
        "canonical_template_count": canonical_template_count,
        "legacy_alias_template_count": legacy_alias_count,
        "default_visible_template_count": default_visible_count,
        "canonical_family_count": len({entry.family_id for entry in canonical_entries if entry.default_visible}),
        "kind_counts": dict(sorted(kinds.items())),
        "renderer_family_counts": dict(sorted(renderers.items())),
        "execution_mode_counts": dict(sorted(execution_modes.items())),
        "paper_proven_template_count": paper_proven_count,
        "golden_template_count": golden_template_count,
        "exemplar_template_count": exemplar_template_count,
        "analysis_responsibility_counts": dict(
            sorted(Counter(entry.analysis_responsibility for entry in canonical_entries).items())
        ),
        "renderer_policy_completion": renderer_policy_completion(renderer_policy_records),
    }


def display_pack_capability_discover(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    include_templates: bool = False,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = _normal_optional_path(paper_root)
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    payload = {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_capability",
        "status": "available",
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "inventory": _inventory_summary(records),
        "renderer_policy": default_surface_renderer_policy(),
        "figure_contract_policy": figure_contract_policy(),
        "composition_recipe_surface": composition_recipe_discovery_payload(include_recipes=include_templates),
        "callable_actions": [
            {
                "command": action,
                "surface_kind": f"display_pack_agent_{action.replace('-', '_')}",
                "agent_consumption_only": True,
            }
            for action in AGENT_CAPABILITY_ACTIONS
        ],
        "expected_receipt_refs": display_pack_agent_receipt_refs(),
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }
    if include_templates:
        catalogs = _catalogs_by_pack_root(records)
        payload["templates"] = [
            _template_summary(record, catalogs, repo_root=normalized_repo_root)
            for record in records
            if _canonical_entry(record, catalogs).default_visible
        ]
        payload["template_surface_policy"] = {
            "default_templates_are_canonical_only": True,
            "active_inventory_is_canonical_only": True,
            "evidence_figures_default_to_r_ggplot2": True,
            "python_evidence_templates_not_retained_without_advantage_proof": True,
            "python_illustration_shells_may_be_default_visible": True,
            "legacy_alias_templates_hidden_from_default_discover": True,
            "composition_recipe_routing_required": True,
            **analysis_template_surface_policy_flags(),
            "migration_inventory_template_count": sum(
                len(catalog.entries_by_template_id)
                for catalog in catalogs.values()
                if catalog is not None
            )
            or len(records),
            "returned_template_count": len(payload["templates"]),
        }
    return payload


def _canonicalized_request(
    request: Mapping[str, Any],
    records: list[LoadedDisplayTemplate],
    catalogs: Mapping[Path, CanonicalTemplateCatalog | None],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    updated = dict(request)
    requested_template_id = _text(updated.get("template_id"))
    if not requested_template_id:
        return updated, None
    migration_entry = _migration_index_from_catalogs(catalogs).get(requested_template_id)
    if migration_entry is None and "::" in requested_template_id:
        migration_entry = _migration_index_from_catalogs(catalogs).get(requested_template_id.split("::")[-1])
    if migration_entry is not None and migration_entry.migration_status == "migrated_alias":
        updated["template_id"] = migration_entry.canonical_template_id
        return updated, {
            "status": "migrated_alias_to_canonical",
            "requested_template_id": requested_template_id,
            "canonical_template_id": migration_entry.canonical_template_id,
            "canonical_family_id": migration_entry.family_id,
            "canonical_family_title": migration_entry.family_title,
            "migration_reason": migration_entry.migration_reason,
        }
    for record in records:
        manifest = record.template_manifest
        if requested_template_id not in {manifest.template_id, manifest.full_template_id}:
            continue
        canonical = _canonical_entry(record, catalogs)
        if canonical.migration_status != "migrated_alias":
            return updated, None
        updated["template_id"] = canonical.canonical_template_id
        return updated, {
            "status": "migrated_alias_to_canonical",
            "requested_template_id": requested_template_id,
            "canonical_template_id": canonical.canonical_template_id,
            "canonical_family_id": canonical.family_id,
            "canonical_family_title": canonical.family_title,
            "migration_reason": canonical.migration_reason,
        }
    return updated, None


def _has_purpose_brief_anchor(raw_request: Mapping[str, Any]) -> bool:
    return any(_text(raw_request.get(key)) for key in _PURPOSE_BRIEF_ANCHOR_KEYS)


def _purpose_visual_primitives(request: Mapping[str, Any]) -> list[str]:
    tokens = " ".join(
        _text(request.get(key))
        for key in (
            "query",
            "claim_role",
            "audit_family",
            "medical_figure_family_id",
            "medical_figure_family_title",
        )
    ).lower()
    if any(token in tokens for token in ("transportability", "generalizability", "external validation")):
        primitives = [
            "center_or_cohort_metric_estimates",
            "uncertainty_interval_or_reference_line",
            "center_or_cohort_labels",
        ]
        if any(token in tokens for token in ("governance", "calibration", "slope", "o/e", "observed")):
            primitives.append("calibration_governance_metric_marks")
        return primitives
    if any(token in tokens for token in ("roc", "auc", "discrimination")):
        return ["discrimination_curve", "reference_line", "model_or_cohort_labels"]
    if any(token in tokens for token in ("calibration", "slope", "observed", "predicted")):
        return ["observed_vs_predicted_marks", "calibration_reference", "sample_or_bin_context"]
    if any(token in tokens for token in ("decision curve", "dca", "utility")):
        return ["net_benefit_curve", "threshold_axis", "treat_all_or_none_reference"]
    if any(token in tokens for token in ("forest", "subgroup", "effect")):
        return ["effect_estimate_marks", "confidence_intervals", "null_reference_line"]
    return ["claim_bearing_evidence_marks", "source_data_or_statistics_refs", "readable_labels"]


def _purpose_first_selection_gate(
    *,
    raw_request: Mapping[str, Any],
    request: Mapping[str, Any],
    figure_intent: Mapping[str, Any],
    recommended_template: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = _mapping(figure_intent.get("figure_contract"))
    purpose_anchor_present = _has_purpose_brief_anchor(raw_request)
    template = _mapping(recommended_template)
    selected_template_id = _text(template.get("template_id") or template.get("full_template_id"))
    template_supports_visual_evidence = bool(
        not template
        or template.get("kind") != "evidence_figure"
        or (
            _text(template.get("analysis_responsibility")) != "illustration_shell"
            and _text(template.get("figure_archetype"))
            and (template.get("medical_family_ids") or template.get("canonical_family_id"))
        )
    )
    status = "pass" if purpose_anchor_present and template_supports_visual_evidence else "blocked"
    missing_items: list[str] = []
    if not purpose_anchor_present:
        missing_items.append("figure_purpose_brief")
    if not template_supports_visual_evidence:
        missing_items.append("template_visual_evidence_mapping")
    return {
        "surface_kind": "display_pack_purpose_first_selection_gate",
        "status": status,
        "required_before_template_scoring": True,
        "purpose_brief_present": purpose_anchor_present,
        "missing_items": missing_items,
        "core_conclusion": _text(contract.get("core_conclusion")),
        "medical_question": _text(request.get("query") or request.get("claim_role")),
        "medical_figure_family_id": _text(request.get("medical_figure_family_id")),
        "medical_figure_family_title": _text(request.get("medical_figure_family_title")),
        "mandatory_visual_evidence_primitives": _purpose_visual_primitives(request),
        "selected_template_id": selected_template_id,
        "selected_template_figure_archetype": _text(template.get("figure_archetype")),
        "selected_template_medical_family_ids": list(template.get("medical_family_ids") or []),
        "selected_template_can_render_required_evidence_as_marks": template_supports_visual_evidence,
        "selection_basis": [
            "figure_purpose_brief",
            "medical_figure_family_catalog",
            "template_semantic_fit",
            "renderer_contract",
            "layout_qc_profile",
        ],
        "forbidden_shortcuts": [
            "select_template_by_name_without_purpose_brief",
            "replace_claim_bearing_metrics_with_text_cards",
            "use_decorative_panel_for_required_evidence",
            "treat_template_gallery_style_as_publication_verdict",
        ],
        "blocks_render": status != "pass",
    }


def display_pack_figure_plan(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    figure_request: Mapping[str, Any] | None = None,
    max_recommendations: int = 5,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = _normal_optional_path(paper_root)
    raw_request = dict(figure_request or {})
    explicit_audit_family = bool(_text((figure_request or {}).get("audit_family")))
    intent_payload = compile_display_figure_intent(figure_request=figure_request)
    request = dict(intent_payload["compiled_figure_request"])
    pre_selection_gate = _purpose_first_selection_gate(
        raw_request=raw_request,
        request=request,
        figure_intent=intent_payload,
    )
    if pre_selection_gate["status"] != "pass":
        blocker = {
            "blocked_reason": "purpose_first_figure_brief_required",
            "owner": "MedAutoScience",
            "route_hint": "provide_figure_purpose_brief_before_template_selection",
            "minimum_fit_floor": minimum_fit_floor(),
            "purpose_first_selection_gate": pre_selection_gate,
        }
        return {
            "schema_version": 1,
            "surface_kind": "display_pack_agent_figure_plan",
            "status": "blocked",
            "repo_root": str(normalized_repo_root),
            "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
            "figure_request": request,
            "figure_intent": intent_payload,
            "purpose_first_selection_gate": pre_selection_gate,
            "figure_workflow_packet": build_planning_figure_workflow_packet(
                request=request,
                figure_intent=intent_payload,
                recommended_template=None,
                status="blocked",
            ),
            "recommended_template": None,
            "recommendations": [],
            "candidate_count": 0,
            "requested_template_migration": None,
            "minimum_fit_floor": minimum_fit_floor(),
            **figure_policy_surfaces(),
            "next_callable": "",
            "typed_blocker": blocker,
            "agent_manual_template_selection_required": False,
            "template_fit_policy": "",
            "publication_readiness_verdict": False,
            "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
        }
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    catalogs = _catalogs_by_pack_root(records)
    request, template_migration = _canonicalized_request(request, records, catalogs)
    if not _text(request.get("template_id")):
        seed_ids = {
            _text(item)
            for item in _list(request.get("medical_figure_template_seed_ids"))
            if _text(item)
        }
        if seed_ids:
            matching_records = [
                record
                for record in records
                if record.template_manifest.template_id in seed_ids
                or record.template_manifest.full_template_id in seed_ids
            ]
            if matching_records and not explicit_audit_family:
                request["audit_family"] = matching_records[0].template_manifest.audit_family
    candidates: list[dict[str, Any]] = []
    for record in records:
        canonical = _canonical_entry(record, catalogs)
        if not _text(request.get("template_id")) and not canonical.default_visible:
            continue
        if not hard_compatible(record, request):
            continue
        if not has_semantic_fit_anchor(record, request):
            continue
        score, reasons = score_template(record, request)
        if canonical.default_visible:
            score += 30
            reasons.append("canonical_default_visible")
        entry = _template_summary(record, catalogs, request=request, repo_root=normalized_repo_root)
        entry["recommendation_score"] = score
        entry["recommendation_reasons"] = reasons
        entry.update(template_fit_entry(record, request))
        candidates.append(entry)
    candidates.sort(key=template_sort_key, reverse=True)
    recommendations = candidates[: max(1, max_recommendations)]
    recommended = recommendations[0] if recommendations else None
    purpose_first_gate = _purpose_first_selection_gate(
        raw_request=raw_request,
        request=request,
        figure_intent=intent_payload,
        recommended_template=recommended,
    )
    analysis_blocker = analysis_blocker_for_template_summary(recommended, request)
    status = (
        "display_plan_ready"
        if recommended and analysis_blocker is None and purpose_first_gate["status"] == "pass"
        else "blocked"
    )
    if purpose_first_gate["status"] != "pass":
        blocker = {
            "blocked_reason": "purpose_first_template_mapping_failed",
            "owner": "MedAutoScience",
            "route_hint": "revise_figure_purpose_or_template_semantic_mapping",
            "minimum_fit_floor": minimum_fit_floor(),
            "purpose_first_selection_gate": purpose_first_gate,
        }
    elif analysis_blocker is not None:
        blocker = analysis_blocker
    elif recommended is None:
        blocker = {
            "blocked_reason": "display_template_not_found",
            "owner": "MedAutoScience",
            "route_hint": "display_pack_template_gap_or_request_shape_repair",
            "requested_template_id": _text(request.get("template_id")),
            "minimum_fit_floor": minimum_fit_floor(),
        }
    else:
        blocker = None
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_figure_plan",
        "status": status,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "figure_request": request,
        "figure_intent": intent_payload,
        "purpose_first_selection_gate": purpose_first_gate,
        "figure_workflow_packet": build_planning_figure_workflow_packet(
            request=request,
            figure_intent=intent_payload,
            recommended_template=recommended,
            status=status,
        ),
        "recommended_template": recommended,
        "recommendations": recommendations,
        "candidate_count": len(candidates),
        "template_surface_policy": {
            "default_recommendations_are_canonical_only": True,
            "evidence_figures_default_to_r_ggplot2": True,
            "python_evidence_templates_not_retained_without_advantage_proof": True,
            "python_illustration_shells_may_be_default_visible": True,
            "legacy_alias_templates_hidden_unless_explicit": True,
            "explicit_alias_requests_migrate_to_canonical": True,
            "nature_skills_backend_question_not_used_on_default_mas_evidence_path": True,
            "figure_contract_required_before_paper_facing_render": True,
            "medical_figure_family_mapping_required": True,
            "starter_recipe_profile_required": True,
            "style_palette_qa_profile_required": True,
            "composition_recipe_routing_required": True,
            **analysis_template_surface_policy_flags(),
        },
        "requested_template_migration": template_migration,
        "minimum_fit_floor": minimum_fit_floor(),
        **figure_policy_surfaces(),
        "next_callable": "display-pack-preflight" if status == "display_plan_ready" else "",
        "typed_blocker": blocker,
        "agent_manual_template_selection_required": False,
        "template_fit_policy": _text(recommended.get("template_fit_policy")) if isinstance(recommended, Mapping) else "",
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }


def _route_for_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    code = _text(finding.get("code"))
    route_hint = _text(finding.get("route_hint"))
    route_by_code = {
        "analysis_summary_required_before_display_render": (
            "analysis_materialization",
            "materialize_validated_analysis_summary_before_display_render",
        ),
        "template_selection_empty": ("template_catalog", "display-pack-agent-plan"),
        "qc_profile_missing": ("qc_profile", "display_pack_qc_profile_repair"),
        "render_r_missing": ("renderer", "display_pack_renderer_asset_repair"),
        "r_runtime_not_ready": ("runtime_dependency", "opl_runtime_env_doctor"),
        "dependency_environment_not_prepared": ("dependency_environment", route_hint or "opl_runtime_env_doctor"),
        "paper_root_missing": ("paper_context", "provide_paper_root_or_scaffold_paper"),
        "publication_style_profile_missing": ("style_profile", "seed_publication_style_profile"),
        "golden_case_not_declared": ("golden_regression", "display_pack_golden_refresh"),
    }
    layer, next_callable = route_by_code.get(code, ("display_pack_contract", route_hint or "display_pack_repair"))
    return {
        "surface_kind": "display_pack_typed_repair_route",
        "code": code,
        "layer": layer,
        "repair_owner": "OPL Framework" if layer in {"runtime_dependency", "dependency_environment"} else "MedAutoScience",
        "next_callable": next_callable,
        "route_hint": route_hint,
        "blocks_render": code != "golden_case_not_declared",
        "authority_boundary": {
            "repair_route_can_mutate_data_or_statistics": False,
            "repair_route_can_authorize_publication_readiness": False,
        },
    }


def _quality_floor(
    *,
    plan: Mapping[str, Any] | None = None,
    preflight: Mapping[str, Any] | None = None,
    render_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    plan_payload = _mapping(plan)
    preflight_payload = _mapping(preflight)
    render_payload = _mapping(render_receipt)
    checks = {
        "intent_compiled": bool(_mapping(plan_payload.get("figure_intent"))),
        "template_selected": bool(plan_payload.get("recommended_template")),
        "preflight_ready": preflight_payload.get("status") == "ready",
        "style_profile_present": _mapping(preflight_payload.get("style_profile")).get("status") == "present",
        "golden_declared": not any(
            _text(item.get("code")) == "golden_case_not_declared"
            for item in list(preflight_payload.get("advisory_findings") or [])
            if isinstance(item, Mapping)
        ),
        "render_manifested": render_payload.get("status") == "publication_manifested",
    }
    score = sum(1 for value in checks.values() if value)
    status = "strong_floor" if score >= 5 else "minimum_floor" if score >= 3 else "needs_repair"
    return {
        "surface_kind": "display_pack_quality_floor",
        "score": score,
        "max_score": len(checks),
        "status": status,
        "checks": checks,
        "figure_contract_policy": figure_contract_policy(),
        "quality_floor_only": True,
        "ai_vlm_expected_for_quality_ceiling": True,
        "publication_readiness_verdict": False,
    }


def _required_r_packages(records: list[LoadedDisplayTemplate]) -> tuple[str, ...]:
    packages: set[str] = set()
    for record in records:
        template_id = record.template_manifest.template_id
        full_template_id = record.template_manifest.full_template_id
        for item in dependency_requirements_for_records(
            repo_root=record.pack_root,
            records=[record],
        ):
            item_map = _mapping(item)
            r_packages = [
                package
                for package in _list(item_map.get("language_package_requirements"))
                if _text(_mapping(package).get("language")) == "r"
            ]
            for package in r_packages:
                package_map = _mapping(package)
                template_ids = tuple(_text(value) for value in _list(package_map.get("template_ids")) if _text(value))
                if template_ids and template_id not in template_ids and full_template_id not in template_ids:
                    continue
                if package_map.get("required") is True and _text(package_map.get("name")):
                    packages.add(_text(package_map.get("name")))
    return tuple(sorted(packages))


def _r_runtime_status(records: list[LoadedDisplayTemplate], *, check_runtime_dependencies: bool) -> dict[str, Any]:
    requires_r = bool(_required_r_packages(records))
    if not requires_r:
        return {"required": False, "status": "not_required", "binary": "Rscript", "packages": {}}
    rscript_path = shutil.which("Rscript")
    if rscript_path is None:
        return {"required": True, "status": "missing", "binary": "Rscript", "packages": {}}
    packages = _required_r_packages(records)
    package_status: dict[str, Any] = {}
    status = "present"
    if check_runtime_dependencies and packages:
        expr = "; ".join(
            f'cat("{package} ", requireNamespace("{package}", quietly=TRUE), "\\n", sep="")'
            for package in packages
        )
        completed = subprocess.run(
            [rscript_path, "-e", expr],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        for line in completed.stdout.splitlines():
            name, _, value = line.partition(" ")
            if name in packages:
                package_status[name] = value.strip() == "TRUE"
        for package in packages:
            package_status.setdefault(package, False)
        if completed.returncode != 0 or not all(package_status.values()):
            status = "missing_dependency"
    elif packages:
        package_status = {package: "not_checked" for package in packages}
    return {
        "required": True,
        "status": status,
        "binary": "Rscript",
        "binary_path": rscript_path,
        "packages": package_status,
    }


def display_pack_preflight(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    template_id: str | None = None,
    figure_request: Mapping[str, Any] | None = None,
    check_runtime_dependencies: bool = True,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = _normal_optional_path(paper_root)
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    catalogs = _catalogs_by_pack_root(records)
    intent_payload = compile_display_figure_intent(figure_request=figure_request)
    compiled_request = dict(intent_payload["compiled_figure_request"])
    if template_id:
        selected_request, template_migration = _canonicalized_request(
            {"template_id": template_id},
            records,
            catalogs,
        )
        selected_template_id = _text(selected_request.get("template_id"))
        selected_records = [
            record
            for record in records
            if record.template_manifest.template_id == selected_template_id
            or record.template_manifest.full_template_id == selected_template_id
        ]
    else:
        plan = display_pack_figure_plan(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            figure_request=compiled_request,
            max_recommendations=1,
        )
        if plan.get("status") != "display_plan_ready":
            plan_blocker = _mapping(plan.get("typed_blocker"))
            return {
                "schema_version": 1,
                "surface_kind": "display_pack_agent_preflight",
                "status": "blocked",
                "repo_root": str(normalized_repo_root),
                "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
                "figure_intent": intent_payload,
                "figure_request": compiled_request,
                "templates": [],
                "requested_template_migration": _mapping(plan.get("requested_template_migration")) or None,
                "r_runtime": {"required": False, "status": "not_checked"},
                "style_profile": {"required": True, "status": "not_checked"},
                **figure_policy_surfaces(),
                "blocking_findings": [analysis_finding_from_blocker(plan_blocker)] if plan_blocker else [],
                "advisory_findings": [],
                "typed_repair_routes": [_route_for_finding(analysis_finding_from_blocker(plan_blocker))]
                if plan_blocker
                else [],
                "repair_owner": "MedAutoScience",
                "quality_floor": _quality_floor(plan=plan, preflight={"status": "blocked"}),
                "next_callable": "display-pack-repair",
                "publication_readiness_verdict": False,
                "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
            }
        recommended = _mapping(plan.get("recommended_template"))
        template_migration = _mapping(plan.get("requested_template_migration")) or None
        selected_template = _text(recommended.get("full_template_id") or recommended.get("template_id"))
        selected_records = [
            record
            for record in records
            if record.template_manifest.template_id == selected_template
            or record.template_manifest.full_template_id == selected_template
        ]

    blocking_findings: list[dict[str, Any]] = []
    advisory_findings: list[dict[str, Any]] = []
    template_entries: list[dict[str, Any]] = []

    for record in selected_records:
        manifest = record.template_manifest
        template_root = record.template_path.parent
        entry = _template_summary(record, catalogs, request=compiled_request, repo_root=normalized_repo_root)
        entry.update(template_fit_entry(record, compiled_request))
        template_entries.append(entry)
        analysis_blocker = analysis_blocker_for_template_summary(entry, compiled_request)
        if analysis_blocker is not None:
            blocking_findings.append(analysis_finding_from_blocker(analysis_blocker))
        if manifest.qc_profile_ref not in QC_PROFILE_RUNNERS:
            blocking_findings.append(
                {
                    "code": "qc_profile_missing",
                    "template_id": manifest.full_template_id,
                    "qc_profile_ref": manifest.qc_profile_ref,
                    "route_hint": "qc_profile_contract_repair",
                }
            )
        if manifest.execution_mode == "subprocess" and manifest.renderer_family == "r_ggplot2":
            if not (template_root / "render.R").is_file():
                blocking_findings.append(
                    {
                        "code": "render_r_missing",
                        "template_id": manifest.full_template_id,
                        "route_hint": "renderer_asset_repair",
                    }
                )
        if not manifest.golden_case_paths:
            advisory_findings.append(
                {
                    "code": "golden_case_not_declared",
                    "template_id": manifest.full_template_id,
                    "route_hint": "golden_coverage_promotion",
                }
            )

    if not selected_records:
        blocking_findings.append(
            {
                "code": "template_selection_empty",
                "route_hint": "display_pack_figure_plan_or_template_gap_repair",
            }
        )

    dependency_environment = dependency_environment_status(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
        records=selected_records,
    )
    dependency_finding = dependency_environment_finding(dependency_environment)
    dependency_environment_prepared = dependency_environment.get("status") == "prepared"
    r_runtime = _r_runtime_status(
        selected_records,
        check_runtime_dependencies=check_runtime_dependencies and not dependency_environment_prepared,
    )
    if dependency_environment_prepared and r_runtime.get("required") is True:
        r_runtime = {
            **r_runtime,
            "status": "delegated_to_opl_dependency_environment",
            "doctor_status": dependency_environment.get("doctor_status"),
            "run_context_ref": dependency_environment.get("run_context_ref"),
        }
    if r_runtime.get("status") in {"missing", "missing_dependency"}:
        blocking_findings.append(
            {
                "code": "r_runtime_not_ready",
                "runtime": r_runtime,
                "route_hint": "opl_runtime_env_doctor",
            }
        )
    if dependency_finding is not None and check_runtime_dependencies:
        blocking_findings.append(dependency_finding)

    style_profile_status = {"required": True, "status": "missing_paper_root"}
    if normalized_paper_root is None:
        blocking_findings.append(
            {
                "code": "paper_root_missing",
                "route_hint": "provide_paper_root_or_scaffold_paper",
            }
        )
    else:
        style_path = normalized_paper_root / "publication_style_profile.json"
        if not style_path.is_file():
            style_profile_status = {"required": True, "status": "missing", "path": str(style_path)}
            blocking_findings.append(
                {
                    "code": "publication_style_profile_missing",
                    "path": str(style_path),
                    "route_hint": "publication_style_profile_seed_or_apply",
                }
            )
        else:
            load_publication_style_profile(style_path)
            style_profile_status = {"required": True, "status": "present", "path": str(style_path)}

    status = "ready" if not blocking_findings else "blocked"
    typed_repair_routes = [_route_for_finding(item) for item in blocking_findings + advisory_findings]
    next_callable = "display-pack-render" if status == "ready" else (
        _text(typed_repair_routes[0].get("next_callable")) if typed_repair_routes else "display-pack-repair"
    )
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_preflight",
        "status": status,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "figure_intent": intent_payload,
        "figure_request": compiled_request,
        "templates": template_entries,
        "requested_template_migration": template_migration,
        "dependency_environment": dependency_environment,
        "r_runtime": r_runtime,
        "style_profile": style_profile_status,
        **figure_policy_surfaces(),
        "blocking_findings": blocking_findings,
        "advisory_findings": advisory_findings,
        "typed_repair_routes": typed_repair_routes,
        "repair_owner": "OPL Framework" if dependency_finding is not None and check_runtime_dependencies else (
            "MedAutoScience" if blocking_findings else ""
        ),
        "quality_floor": _quality_floor(
            plan={"figure_intent": intent_payload, "recommended_template": template_entries[0] if template_entries else None},
            preflight={
                "status": status,
                "style_profile": style_profile_status,
                "advisory_findings": advisory_findings,
            },
        ),
        "next_callable": next_callable,
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }


def display_pack_orchestrate(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    current_owner_delta: Mapping[str, Any] | None = None,
    claim_ref: str = "",
    data_ref: str = "",
    paper_target: str = "",
    intent: str = "",
    figure_request: Mapping[str, Any] | None = None,
    max_recommendations: int = 5,
    check_runtime_dependencies: bool = True,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = _normal_optional_path(paper_root)
    figure_intent = compile_display_figure_intent(
        current_owner_delta=current_owner_delta,
        claim_ref=claim_ref,
        data_ref=data_ref,
        paper_target=paper_target,
        intent=intent,
        figure_request=figure_request,
    )
    compiled_request = dict(figure_intent["compiled_figure_request"])
    plan = display_pack_figure_plan(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
        figure_request=compiled_request,
        max_recommendations=max_recommendations,
    )
    recommended = _mapping(plan.get("recommended_template"))
    template_id = _text(recommended.get("full_template_id") or recommended.get("template_id"))
    if plan.get("status") != "display_plan_ready":
        plan_blocker = _mapping(plan.get("typed_blocker"))
        typed_routes = [_route_for_finding(analysis_finding_from_blocker(plan_blocker))] if plan_blocker else []
        missing_inputs = list(figure_intent.get("missing_inputs") or [])
        if missing_inputs:
            typed_routes.extend(missing_input_repair_routes(missing_inputs))
        return {
            "schema_version": 1,
            "surface_kind": "display_pack_agent_orchestration",
            "status": "needs_repair",
            "repo_root": str(normalized_repo_root),
            "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
            "figure_intent": figure_intent,
            "figure_request": compiled_request,
            "plan": plan,
            "preflight": {
                "schema_version": 1,
                "surface_kind": "display_pack_agent_preflight",
                "status": "blocked",
                "typed_blocker": plan_blocker,
            },
            **figure_policy_surfaces(),
            "quality_floor": _quality_floor(plan=plan, preflight={"status": "blocked"}),
            "typed_repair_routes": typed_routes,
            "next_callable": "display-pack-repair",
            "agent_manual_template_selection_required": False,
            "publication_readiness_verdict": False,
            "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
        }
    preflight = display_pack_preflight(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
        template_id=template_id,
        figure_request=compiled_request,
        check_runtime_dependencies=check_runtime_dependencies,
    )
    quality_floor = _quality_floor(plan=plan, preflight=preflight)
    missing_inputs = list(figure_intent.get("missing_inputs") or [])
    typed_routes = list(preflight.get("typed_repair_routes") or [])
    if missing_inputs:
        typed_routes.extend(missing_input_repair_routes(missing_inputs))
    status = "ready_to_render" if preflight.get("status") == "ready" and not missing_inputs else "needs_repair"
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_orchestration",
        "status": status,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "figure_intent": figure_intent,
        "figure_request": compiled_request,
        "plan": plan,
        "preflight": preflight,
        **figure_policy_surfaces(),
        "quality_floor": quality_floor,
        "typed_repair_routes": typed_routes,
        "next_callable": "display-pack-render" if status == "ready_to_render" else "display-pack-repair",
        "agent_manual_template_selection_required": False,
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }


def display_pack_render(
    *,
    paper_root: Path | str,
    repo_root: Path | str | None = None,
    figure_request: Mapping[str, Any] | None = None,
    visual_audit_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    request = dict(figure_request or {})
    data_payload_file = _text(request.get("data_payload_file"))
    render_dependency_environment: dict[str, Any] | None = None

    if data_payload_file:
        template_id = _text(request.get("template_id"))
        records = load_enabled_local_display_template_records(
            normalized_repo_root,
            paper_root=normalized_paper_root,
        )
        catalogs = _catalogs_by_pack_root(records)
        if not template_id:
            plan = display_pack_figure_plan(
                repo_root=normalized_repo_root,
                paper_root=normalized_paper_root,
                figure_request=request,
                max_recommendations=1,
            )
            if plan.get("status") != "display_plan_ready":
                return {
                    "schema_version": 1,
                    "surface_kind": "display_pack_agent_render_receipt",
                    "status": "blocked",
                    "typed_blocker": _mapping(plan.get("typed_blocker")),
                    "plan": plan,
                    "next_callable": "display-pack-repair",
                    "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
                }
            recommended = _mapping(plan.get("recommended_template"))
            template_id = _text(recommended.get("full_template_id") or recommended.get("template_id"))
        else:
            template_request, _template_migration = _canonicalized_request(
                {"template_id": template_id},
                records,
                catalogs,
            )
            template_id = _text(template_request.get("template_id"))
        selected_records = [
            record
            for record in records
            if record.template_manifest.template_id == template_id
            or record.template_manifest.full_template_id == template_id
        ]
        if selected_records:
            entry = _template_summary(selected_records[0], catalogs, request=request, repo_root=normalized_repo_root)
            analysis_blocker = analysis_blocker_for_template_summary(entry, request)
            if analysis_blocker is not None:
                return {
                    "schema_version": 1,
                    "surface_kind": "display_pack_agent_render_receipt",
                    "status": "blocked",
                    "typed_blocker": analysis_blocker,
                    "next_callable": "display-pack-repair",
                    "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
                }
        render_dependency_environment = dependency_environment_status(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            records=selected_records,
        )
        dependency_finding = dependency_environment_finding(render_dependency_environment)
        if dependency_finding is not None:
            return {
                "schema_version": 1,
                "surface_kind": "display_pack_agent_render_receipt",
                "status": "blocked",
                "dependency_environment": render_dependency_environment,
                "typed_blocker": dependency_finding,
                "receipt_refs": display_pack_agent_receipt_refs(),
                "next_callable": dependency_finding["route_hint"],
                "publication_readiness_verdict": False,
                "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
            }
        if not template_id:
            return {
                "schema_version": 1,
                "surface_kind": "display_pack_agent_render_receipt",
                "status": "blocked",
                "typed_blocker": {
                    "blocked_reason": "display_template_not_selected",
                    "owner": "MedAutoScience",
                    "route_hint": "display_pack_figure_plan_or_template_gap_repair",
                },
                "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
            }
        result = scaffold_display_pack_render(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            template_id=template_id,
            data_payload_file=Path(data_payload_file),
            figure_id=_text(request.get("figure_id")) or "F1",
            claim_ref=_text(request.get("claim_ref")) or "claim:display-pack-agent",
            cohort_ref=_text(request.get("cohort_ref")) or "cohort:display-pack-agent",
            endpoint_ref=_text(request.get("endpoint_ref")) or "endpoint:display-pack-agent",
            risk_horizon=_text(request.get("risk_horizon")) or "unspecified",
            visual_audit_review=dict(visual_audit_review or default_visual_audit_review()),
            dependency_environment=render_dependency_environment,
        )
    elif (normalized_paper_root / "figure_intent.json").is_file():
        records = load_enabled_local_display_template_records(
            normalized_repo_root,
            paper_root=normalized_paper_root,
        )
        render_dependency_environment = dependency_environment_status(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            records=records,
        )
        dependency_finding = dependency_environment_finding(render_dependency_environment)
        if dependency_finding is not None:
            return {
                "schema_version": 1,
                "surface_kind": "display_pack_agent_render_receipt",
                "status": "blocked",
                "dependency_environment": render_dependency_environment,
                "typed_blocker": dependency_finding,
                "receipt_refs": display_pack_agent_receipt_refs(),
                "next_callable": dependency_finding["route_hint"],
                "publication_readiness_verdict": False,
                "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
            }
        result = materialize_display_pack_publication_manifest(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            visual_audit_review=dict(visual_audit_review or default_visual_audit_review()),
            figure_ids=[_text(request.get("figure_id"))] if _text(request.get("figure_id")) else [],
            dependency_environment=render_dependency_environment,
        )
    else:
        return {
            "schema_version": 1,
            "surface_kind": "display_pack_agent_render_receipt",
            "status": "blocked",
            "typed_blocker": {
                "blocked_reason": "display_pack_render_inputs_missing",
                "owner": "MedAutoScience",
                "route_hint": "provide_paper_figure_intent_or_data_payload_file",
            },
            "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
        }

    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_render_receipt",
        "status": result.get("status", "rendered"),
        "dependency_environment": render_dependency_environment or result.get("dependency_environment") or {},
        "render_result": result,
        "receipt_refs": display_pack_agent_receipt_refs(),
        **figure_policy_surfaces(),
        "figure_workflow_packet": result.get("figure_workflow_packet") or {},
        "route_back_hint": "visual_audit" if result.get("status") == "publication_manifested" else "display_pack_render_repair",
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }
