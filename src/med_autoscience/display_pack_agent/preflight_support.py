from __future__ import annotations

from collections.abc import Mapping
import shutil
import subprocess
from typing import Any

from med_autoscience.display_pack_agent.figure_contract import figure_contract_policy
from med_autoscience.display_pack_dependency_environment import dependency_requirements_for_records
from med_autoscience.display_pack_loader import LoadedDisplayTemplate


DISPLAY_PACK_AGENT_AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
    "can_emit_display_refs_and_receipts": True,
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def route_for_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
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


def quality_floor(
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


def required_r_packages(records: list[LoadedDisplayTemplate]) -> tuple[str, ...]:
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


def r_runtime_status(records: list[LoadedDisplayTemplate], *, check_runtime_dependencies: bool) -> dict[str, Any]:
    requires_r = bool(required_r_packages(records))
    if not requires_r:
        return {"required": False, "status": "not_required", "binary": "Rscript", "packages": {}}
    rscript_path = shutil.which("Rscript")
    if rscript_path is None:
        return {"required": True, "status": "missing", "binary": "Rscript", "packages": {}}
    packages = required_r_packages(records)
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
