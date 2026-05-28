from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def build_progress_portal_hosted_package(
    *,
    profile: WorkspaceProfile,
    payload: Mapping[str, Any],
    payload_path: Path,
    html_path: Path,
    hosted_package_path: Path,
    refs: Mapping[str, str],
    surface_kind: str,
    profile_ref: str | Path | None = None,
    study_pages: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root
    progress_payload_ref = refs["progress_payload"]
    progress_html_ref = refs["progress_html"]
    hosted_package_ref = refs["hosted_package"]
    return {
        "schema_version": 1,
        "surface_kind": surface_kind,
        "owner": "MedAutoScience",
        "packaging_owner": "MedAutoScience",
        "package_role": "read_model_projection_package",
        "truth_role": "projection_only_no_workspace_runtime_truth",
        "generated_at": payload.get("generated_at"),
        "read_only": True,
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "mds_webui_dependency_allowed": False,
        "default_webui": "mas_progress_portal",
        "authority": {
            "kind": "hosted_read_model_package",
            "writes_authority_surface": False,
            "forbidden_authority": [
                "study_truth",
                "publication_judgment",
                "quality_verdict",
                "runtime_authority",
                "artifact_authority",
                "controller_decision_authority",
            ],
        },
        "workspace": {
            "profile_name": profile.name,
            "workspace_root": str(workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        "package_refs": {
            "hosted_package": str(hosted_package_path),
            "hosted_package_ref": hosted_package_ref,
            "progress_payload": str(payload_path),
            "progress_payload_ref": progress_payload_ref,
            "html": str(html_path),
            "html_ref": progress_html_ref,
            "workspace_relative": {
                "hosted_package": workspace_relative(hosted_package_path, workspace_root),
                "progress_payload": workspace_relative(payload_path, workspace_root),
                "html": workspace_relative(html_path, workspace_root),
            },
            "study_pages": {
                study_id: {
                    "payload": workspace_relative(Path(str(page.get("payload_path"))), workspace_root),
                    "html": workspace_relative(Path(str(page.get("html_path"))), workspace_root),
                }
                for study_id, page in (study_pages or {}).items()
            },
        },
        "entrypoints": {
            "opl_hosted_workbench_consumer": "OPL App/workbench consumes MAS progress payload refs",
            "progress_payload_ref": progress_payload_ref,
        },
        "read_model_materializer_boundary": {
            "surface_kind": "mas_progress_portal_read_model_materializer_boundary",
            "status": "domain_owned_read_model_materializer_no_active_workspace_helper",
            "hosted_package_role": "read_model_projection_package",
            "hosted_package_truth_role": "projection_only_no_workspace_runtime_truth",
            "materializer_owner": "MedAutoScience",
            "materializer_scope": "domain_owned_payload_html_and_hosted_package_projection",
            "physical_module": (
                "src/med_autoscience/controllers/progress_portal_parts/"
                "read_model_materializer.py"
            ),
            "active_callers": [],
            "does_not_claim": [
                "workspace_workbench_owner",
                "status_wrapper_owner",
                "generic_runtime_owner",
                "local_http_service_owner",
                "runtime_control_owner",
            ],
            "domain_repo_physical_delete_authorized": False,
            "retention_reason": "MAS retains only the read-model materializer needed to publish domain-owned progress payload, static HTML evidence, and hosted package refs for OPL consumers.",
            "writes_only": [
                progress_payload_ref,
                hosted_package_ref,
                "artifacts/runtime/progress_portal/studies/<study_id>/latest.json",
                progress_html_ref,
                "ops/mas/progress/studies/<study_id>/index.html",
            ],
            "allowed_carriers": [
                "OPL Runtime Manager family-level projection consumer",
                "OPL App hosted workbench",
            ],
            "must_consume": [
                progress_payload_ref,
            ],
            "must_not_consume": [
                "MDS WebUI state",
                "external MedDeepScientist runtime root",
                "upstream DeepScientist UI state",
            ],
            "must_not_write": [
                "progress_projection",
                "domain_health_diagnostic",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "study_macro_state/latest.json",
                "domain_authority_refs.sqlite",
                "manuscript/current_package",
            ],
        },
        "source_refs": _string_list(payload.get("source_refs")),
        "source_payloads": _mapping(payload.get("source_payloads")),
        "conditions": _mapping(payload.get("conditions")),
        "opl_handoff": _mapping(payload.get("opl_handoff")),
    }


def workspace_relative(path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(path)


def materialized_opl_handoff(
    value: object,
    *,
    payload_path: Path,
    html_path: Path,
) -> dict[str, Any]:
    handoff = _mapping(value)
    handoff["payload_ref"] = str(payload_path)
    handoff["deep_link"] = str(html_path)
    payload_refs = _mapping(handoff.get("payload_refs"))
    payload_refs["progress_portal"] = str(payload_path)
    handoff["payload_refs"] = payload_refs
    return handoff


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


__all__ = [
    "build_progress_portal_hosted_package",
    "materialized_opl_handoff",
    "workspace_relative",
]
