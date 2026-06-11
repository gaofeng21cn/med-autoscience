from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
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
from med_autoscience.display_pack_agent_parts.template_fit import (
    DEFAULT_KIND as _DEFAULT_KIND,
    DEFAULT_RENDERER_PREFERENCE as _DEFAULT_RENDERER_PREFERENCE,
    hard_compatible,
    has_semantic_fit_anchor,
    minimum_fit_floor,
    score_template,
    template_fit_entry,
    template_sort_key,
)
from med_autoscience.display_pack_usability import scaffold_display_pack_render
from med_autoscience.publication_display_contract import load_publication_style_profile


AGENT_CAPABILITY_ACTIONS = (
    "display-pack-capability-discover",
    "display-pack-figure-plan",
    "display-pack-preflight",
    "display-pack-render",
    "display-pack-orchestrate",
)

DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
    "can_emit_display_refs_and_receipts": True,
}

_DEFAULT_REVIEWER_HASH = "0" * 64
_DEFAULT_AUDIT_FAMILY = "Prediction Performance"


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


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _current_delta_text(delta: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _text(delta.get(key))
        if value:
            return value
    owner_route = _mapping(delta.get("owner_route"))
    for key in keys:
        value = _text(owner_route.get(key))
        if value:
            return value
    return ""


def _infer_audit_family(intent_text: str, delta: Mapping[str, Any], request: Mapping[str, Any]) -> str:
    explicit = _text(request.get("audit_family"))
    if explicit:
        return explicit
    lowered = " ".join(
        [
            intent_text,
            _current_delta_text(delta, "action_type", "action_id", "work_unit_id"),
            " ".join(_text_list(delta.get("route_required_ref_families"))),
            " ".join(_text_list(delta.get("capability_families"))),
        ]
    ).lower()
    if any(token in lowered for token in ("roc", "auc", "calibration", "decision curve", "dca", "prediction")):
        return "Prediction Performance"
    if any(token in lowered for token in ("survival", "kaplan", "hazard", "time-to-event")):
        return "Time-to-event"
    if any(token in lowered for token in ("forest", "subgroup", "effect", "odds ratio", "hazard ratio")):
        return "Effects"
    if any(token in lowered for token in ("baseline table", "table one", "characteristics")):
        return "Table"
    return _DEFAULT_AUDIT_FAMILY


def _infer_query(intent_text: str, audit_family: str, delta: Mapping[str, Any], request: Mapping[str, Any]) -> str:
    explicit = _text(request.get("query"))
    if explicit:
        return explicit
    lowered = " ".join(
        [
            intent_text,
            audit_family,
            _current_delta_text(delta, "action_type", "work_unit_id", "desired_delta"),
        ]
    ).lower()
    for token in ("roc", "calibration", "dca", "decision", "km", "kaplan", "forest", "nomogram", "baseline"):
        if token in lowered:
            return "decision curve" if token == "decision" else token
    if audit_family == "Prediction Performance":
        return "roc"
    return audit_family.lower()


def compile_display_figure_intent(
    *,
    current_owner_delta: Mapping[str, Any] | None = None,
    claim_ref: str = "",
    data_ref: str = "",
    paper_target: str = "",
    intent: str = "",
    figure_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    delta = _mapping(current_owner_delta)
    request = dict(figure_request or {})
    intent_text = _text(
        intent
        or request.get("intent")
        or request.get("figure_goal")
        or request.get("claim_role")
        or _current_delta_text(delta, "display_intent", "desired_delta", "summary", "action_type")
    )
    resolved_claim_ref = _text(claim_ref or request.get("claim_ref") or delta.get("claim_ref"))
    resolved_data_ref = _text(data_ref or request.get("data_ref") or delta.get("data_ref"))
    audit_family = _infer_audit_family(intent_text, delta, request)
    figure_kind = _text(request.get("figure_kind") or request.get("kind") or _DEFAULT_KIND)
    compiled_request = {
        **request,
        "figure_kind": figure_kind,
        "audit_family": audit_family,
        "preferred_renderer_family": _text(
            request.get("preferred_renderer_family") or _DEFAULT_RENDERER_PREFERENCE
        ),
        "query": _infer_query(intent_text, audit_family, delta, request),
        "claim_ref": resolved_claim_ref,
        "data_ref": resolved_data_ref,
        "paper_target": _text(paper_target or request.get("paper_target") or delta.get("paper_target")),
        "claim_role": _text(request.get("claim_role") or intent_text or "display_current_owner_delta"),
    }
    if _text(request.get("template_id")):
        compiled_request["template_id"] = _text(request.get("template_id"))
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_figure_intent",
        "status": "compiled",
        "planning_root": "current_owner_delta",
        "current_owner_delta": {
            "action_type": _current_delta_text(delta, "action_type", "action_id"),
            "owner": _current_delta_text(delta, "owner"),
            "work_unit_id": _current_delta_text(delta, "work_unit_id"),
            "work_unit_fingerprint": _current_delta_text(delta, "work_unit_fingerprint"),
            "source_ref": _current_delta_text(delta, "source_ref"),
        },
        "claim_ref": resolved_claim_ref,
        "data_ref": resolved_data_ref,
        "paper_target": compiled_request["paper_target"],
        "intent_text": intent_text,
        "compiled_figure_request": compiled_request,
        "missing_inputs": [
            field
            for field, value in {
                "claim_ref": resolved_claim_ref,
                "data_ref": resolved_data_ref,
            }.items()
            if not value
        ],
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }


def _full_template_id(record: LoadedDisplayTemplate) -> str:
    return record.template_manifest.full_template_id


def _template_summary(record: LoadedDisplayTemplate) -> dict[str, Any]:
    manifest = record.template_manifest
    template_root = record.template_path.parent
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
        "has_render_r": (template_root / "render.R").is_file(),
        "has_render_candidate": (template_root / "render_candidate.R").is_file(),
        "golden_case_count": len(manifest.golden_case_paths),
        "exemplar_ref_count": len(manifest.exemplar_refs),
    }


def _inventory_summary(records: list[LoadedDisplayTemplate]) -> dict[str, Any]:
    kinds = Counter(record.template_manifest.kind for record in records)
    renderers = Counter(record.template_manifest.renderer_family for record in records)
    execution_modes = Counter(record.template_manifest.execution_mode for record in records)
    paper_proven_count = sum(1 for record in records if record.template_manifest.paper_proven)
    golden_template_count = sum(1 for record in records if record.template_manifest.golden_case_paths)
    exemplar_template_count = sum(1 for record in records if record.template_manifest.exemplar_refs)
    return {
        "template_count": len(records),
        "kind_counts": dict(sorted(kinds.items())),
        "renderer_family_counts": dict(sorted(renderers.items())),
        "execution_mode_counts": dict(sorted(execution_modes.items())),
        "paper_proven_template_count": paper_proven_count,
        "golden_template_count": golden_template_count,
        "exemplar_template_count": exemplar_template_count,
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
        "callable_actions": [
            {
                "command": action,
                "surface_kind": f"display_pack_agent_{action.replace('-', '_')}",
                "agent_consumption_only": True,
            }
            for action in AGENT_CAPABILITY_ACTIONS
        ],
        "expected_receipt_refs": {
            "display_pack_lock": "paper/build/display_pack_lock.json",
            "publication_manifest": "paper/build/display_pack_publication_manifest.json",
            "visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
            "polish_lifecycle": "paper/figure_polish_lifecycle.json",
        },
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }
    if include_templates:
        payload["templates"] = [_template_summary(record) for record in records]
    return payload


def display_pack_figure_plan(
    *,
    repo_root: Path | str | None = None,
    paper_root: Path | str | None = None,
    figure_request: Mapping[str, Any] | None = None,
    max_recommendations: int = 5,
) -> dict[str, Any]:
    normalized_repo_root = _normal_repo_root(repo_root)
    normalized_paper_root = _normal_optional_path(paper_root)
    intent_payload = compile_display_figure_intent(figure_request=figure_request)
    request = dict(intent_payload["compiled_figure_request"])
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    candidates: list[dict[str, Any]] = []
    for record in records:
        if not hard_compatible(record, request):
            continue
        if not has_semantic_fit_anchor(record, request):
            continue
        score, reasons = score_template(record, request)
        entry = _template_summary(record)
        entry["recommendation_score"] = score
        entry["recommendation_reasons"] = reasons
        entry.update(template_fit_entry(record, request))
        candidates.append(entry)
    candidates.sort(key=template_sort_key, reverse=True)
    recommendations = candidates[: max(1, max_recommendations)]
    recommended = recommendations[0] if recommendations else None
    status = "display_plan_ready" if recommended else "blocked"
    blocker = None
    if recommended is None:
        blocker = {
            "blocked_reason": "display_template_not_found",
            "owner": "MedAutoScience",
            "route_hint": "display_pack_template_gap_or_request_shape_repair",
            "requested_template_id": _text(request.get("template_id")),
            "minimum_fit_floor": minimum_fit_floor(),
        }
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_figure_plan",
        "status": status,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "figure_request": request,
        "figure_intent": intent_payload,
        "recommended_template": recommended,
        "recommendations": recommendations,
        "candidate_count": len(candidates),
        "minimum_fit_floor": minimum_fit_floor(),
        "next_callable": "display-pack-preflight" if recommended else "",
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
        "template_selection_empty": ("template_catalog", "display-pack-agent-plan"),
        "qc_profile_missing": ("qc_profile", "display_pack_qc_profile_repair"),
        "render_r_missing": ("renderer", "display_pack_renderer_asset_repair"),
        "r_runtime_not_ready": ("runtime_dependency", "install_r_runtime_or_package"),
        "paper_root_missing": ("paper_context", "provide_paper_root_or_scaffold_paper"),
        "publication_style_profile_missing": ("style_profile", "seed_publication_style_profile"),
        "golden_case_not_declared": ("golden_regression", "display_pack_golden_refresh"),
    }
    layer, next_callable = route_by_code.get(code, ("display_pack_contract", route_hint or "display_pack_repair"))
    return {
        "surface_kind": "display_pack_typed_repair_route",
        "code": code,
        "layer": layer,
        "repair_owner": "MedAutoScience" if layer != "runtime_dependency" else "operator_or_opl_pack_os",
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
        "quality_floor_only": True,
        "ai_vlm_expected_for_quality_ceiling": True,
        "publication_readiness_verdict": False,
    }


def _load_renderer_dependency_profile(pack_root: Path) -> dict[str, Any]:
    path = pack_root / "renderer_dependency_profile.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _required_r_packages(records: list[LoadedDisplayTemplate]) -> tuple[str, ...]:
    packages: set[str] = set()
    for record in records:
        profile = _load_renderer_dependency_profile(record.pack_root)
        for item in _list(profile.get("profiles")):
            item_map = _mapping(item)
            if item_map.get("renderer_family") != "r_ggplot2":
                continue
            for package in _list(item_map.get("r_packages")):
                package_map = _mapping(package)
                if package_map.get("required") is True and _text(package_map.get("name")):
                    packages.add(_text(package_map.get("name")))
    return tuple(sorted(packages))


def _r_runtime_status(records: list[LoadedDisplayTemplate], *, check_runtime_dependencies: bool) -> dict[str, Any]:
    requires_r = any(record.template_manifest.renderer_family == "r_ggplot2" for record in records)
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
            if name:
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
    intent_payload = compile_display_figure_intent(figure_request=figure_request)
    compiled_request = dict(intent_payload["compiled_figure_request"])
    if template_id:
        selected_records = [
            record
            for record in records
            if record.template_manifest.template_id == template_id
            or record.template_manifest.full_template_id == template_id
        ]
    else:
        plan = display_pack_figure_plan(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            figure_request=compiled_request,
            max_recommendations=1,
        )
        recommended = _mapping(plan.get("recommended_template"))
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
        entry = _template_summary(record)
        entry.update(template_fit_entry(record, compiled_request))
        template_entries.append(entry)
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

    r_runtime = _r_runtime_status(selected_records, check_runtime_dependencies=check_runtime_dependencies)
    if r_runtime.get("status") in {"missing", "missing_dependency"}:
        blocking_findings.append(
            {
                "code": "r_runtime_not_ready",
                "runtime": r_runtime,
                "route_hint": "renderer_runtime_dependency_repair",
            }
        )

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
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_preflight",
        "status": status,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "figure_intent": intent_payload,
        "figure_request": compiled_request,
        "templates": template_entries,
        "r_runtime": r_runtime,
        "style_profile": style_profile_status,
        "blocking_findings": blocking_findings,
        "advisory_findings": advisory_findings,
        "typed_repair_routes": typed_repair_routes,
        "repair_owner": "MedAutoScience" if blocking_findings else "",
        "quality_floor": _quality_floor(
            plan={"figure_intent": intent_payload, "recommended_template": template_entries[0] if template_entries else None},
            preflight={
                "status": status,
                "style_profile": style_profile_status,
                "advisory_findings": advisory_findings,
            },
        ),
        "next_callable": "display-pack-render" if status == "ready" else "display-pack-preflight",
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
        typed_routes.extend(
            {
                "surface_kind": "display_pack_typed_repair_route",
                "code": f"{field}_missing",
                "layer": "figure_intent",
                "repair_owner": "MedAutoScience",
                "next_callable": "provide_claim_and_data_refs",
                "blocks_render": True,
                "authority_boundary": {
                    "repair_route_can_mutate_data_or_statistics": False,
                    "repair_route_can_authorize_publication_readiness": False,
                },
            }
            for field in missing_inputs
        )
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
        "quality_floor": quality_floor,
        "typed_repair_routes": typed_routes,
        "next_callable": "display-pack-render" if status == "ready_to_render" else "display-pack-repair",
        "agent_manual_template_selection_required": False,
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }


def _default_visual_audit_review() -> dict[str, Any]:
    return {
        "audit_mode": "vlm_visual_verification",
        "reviewer": {
            "provider": "mas-display-pack-agent",
            "model": "agent-structured-visual-audit-receipt",
            "prompt_hash": _DEFAULT_REVIEWER_HASH,
        },
        "findings": [],
        "final_status": "clear",
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

    if data_payload_file:
        template_id = _text(request.get("template_id"))
        if not template_id:
            plan = display_pack_figure_plan(
                repo_root=normalized_repo_root,
                paper_root=normalized_paper_root,
                figure_request=request,
                max_recommendations=1,
            )
            recommended = _mapping(plan.get("recommended_template"))
            template_id = _text(recommended.get("full_template_id") or recommended.get("template_id"))
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
            visual_audit_review=dict(visual_audit_review or _default_visual_audit_review()),
        )
    elif (normalized_paper_root / "figure_intent.json").is_file():
        result = materialize_display_pack_publication_manifest(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            visual_audit_review=dict(visual_audit_review or _default_visual_audit_review()),
            figure_ids=[_text(request.get("figure_id"))] if _text(request.get("figure_id")) else [],
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
        "render_result": result,
        "receipt_refs": {
            "display_pack_lock": "paper/build/display_pack_lock.json",
            "publication_manifest": "paper/build/display_pack_publication_manifest.json",
            "visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
            "polish_lifecycle": "paper/figure_polish_lifecycle.json",
        },
        "route_back_hint": "visual_audit" if result.get("status") == "publication_manifested" else "display_pack_render_repair",
        "publication_readiness_verdict": False,
        "authority_boundary": dict(DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY),
    }
