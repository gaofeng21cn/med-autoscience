from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json
from typing import Any

from . import preflight_support as _preflight_support

from med_autoscience.display_layout_qc.router import QC_PROFILE_RUNNERS
from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
from med_autoscience.display_pack_loader import (
    LoadedDisplayTemplate,
    load_enabled_local_display_template_records,
)
from med_autoscience.display_pack_opl_adapter import (
    build_display_pack_opl_adapter_contract,
    write_enabled_opl_generic_pack_descriptors,
)
from .figure_contract import (
    compile_display_figure_intent,
    figure_contract_policy,
    figure_policy_surfaces,
)
from .figure_workflow import (
    build_planning_figure_workflow_packet,
    display_pack_agent_receipt_refs,
)
from .composition_recipe_projection import composition_recipe_discovery_payload
from .analysis_boundary import (
    analysis_blocker_for_template_summary,
    analysis_finding_from_blocker,
    analysis_template_surface_policy_flags,
    missing_input_repair_routes,
)
from .template_fit import (
    hard_compatible,
    has_semantic_fit_anchor,
    minimum_fit_floor,
    score_template,
    template_fit_entry,
    template_sort_key,
)
from .visual_audit import default_visual_audit_review
from .template_inventory import (
    catalogs_by_pack_root as _catalogs_by_pack_root,
    canonical_entry as _canonical_entry,
    full_template_id as _full_template_id,
    inventory_summary as _inventory_summary,
    migration_index_from_catalogs as _migration_index_from_catalogs,
    template_summary as _template_summary,
)
from .preflight_support import (
    quality_floor as _quality_floor,
    route_for_finding as _route_for_finding,
)
from med_autoscience.display_pack_renderer_policy import (
    default_surface_renderer_policy,
)
from med_autoscience.display_pack_dependency_environment import (
    dependency_environment_finding,
    dependency_environment_status,
)
from med_autoscience.display_pack_usability import scaffold_display_pack_render
from med_autoscience.publication_display_contract import load_publication_style_profile


AGENT_CAPABILITY_ACTIONS = tuple(
    f"display-pack-{name}"
    for name in ("capability-discover", "figure-plan", "preflight", "render", "orchestrate")
)


# Keep these module attributes for existing tests and monkeypatch-based runtime probes.
shutil = _preflight_support.shutil
subprocess = _preflight_support.subprocess
_r_runtime_status = _preflight_support.r_runtime_status


DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
    "can_emit_display_refs_and_receipts": True,
}



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




def display_pack_capability_discover(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    include_templates: bool = False,
    opl_descriptor_output_dir: Path | str | None = None,
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
        "opl_pack_descriptor_adapter": build_display_pack_opl_adapter_contract(),
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }
    normalized_descriptor_output_dir = _normal_optional_path(opl_descriptor_output_dir)
    if normalized_descriptor_output_dir is not None:
        payload["opl_pack_descriptor_refs"] = write_enabled_opl_generic_pack_descriptors(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            output_dir=normalized_descriptor_output_dir,
        )
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
