from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PAPERSPINE_SURFACE_KIND = "mas_paperspine_manuscript_advisory"
PAPERORCHESTRA_SURFACE_KIND = "mas_paperorchestra_authoring_advisory"
PAPERSPINE_FRAMEWORK_ID = "paperspine"
PAPERORCHESTRA_FRAMEWORK_ID = "paperorchestra"
PAPERSPINE_REQUIRED_REF_FAMILIES = (
    "motivation_spine_refs",
    "writing_rationale_matrix_refs",
    "evidence_blueprint_refs",
    "latex_safe_audit_refs",
)
PAPERORCHESTRA_REQUIRED_REF_FAMILIES = (
    "authoring_dag_refs",
    "outline_plot_refs",
    "literature_section_refs",
    "autorater_refs",
)
FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/**",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
)


def build_paperspine_manuscript_advisory(
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return _build_authoring_advisory(
        dispatch=dispatch,
        surface_kind=PAPERSPINE_SURFACE_KIND,
        framework_id=PAPERSPINE_FRAMEWORK_ID,
        source_project="WUBING2023/PaperSpine",
        source_project_role="external_pattern_source_only",
        required_ref_families=PAPERSPINE_REQUIRED_REF_FAMILIES,
    )


def build_paperorchestra_authoring_advisory(
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return _build_authoring_advisory(
        dispatch=dispatch,
        surface_kind=PAPERORCHESTRA_SURFACE_KIND,
        framework_id=PAPERORCHESTRA_FRAMEWORK_ID,
        source_project="Ar9av/PaperOrchestra",
        source_project_role="external_pattern_source_only",
        required_ref_families=PAPERORCHESTRA_REQUIRED_REF_FAMILIES,
    )


def _build_authoring_advisory(
    *,
    dispatch: Mapping[str, Any] | None,
    surface_kind: str,
    framework_id: str,
    source_project: str,
    source_project_role: str,
    required_ref_families: tuple[str, ...],
) -> dict[str, Any]:
    dispatch_payload = _mapping(dispatch)
    refs = _mapping(dispatch_payload.get("refs"))
    ref_families = {family: _string_list(refs.get(family)) for family in required_ref_families}
    missing = [family for family, values in ref_families.items() if not values]
    return {
        "surface_kind": surface_kind,
        "framework_id": framework_id,
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "status": "fail_open_advisory_gap" if missing else "advisory_ready",
        "advisory_gap": bool(missing),
        "source_project": source_project,
        "source_project_role": source_project_role,
        "current_owner_action": _current_owner_action(dispatch_payload),
        **ref_families,
        "required_ref_families": list(required_ref_families),
        "missing_ref_families": missing,
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "can_block_current_owner_action": False,
        "authority_boundary": _authority_boundary(framework_id=framework_id),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _text(dispatch.get("action_type")),
        "action_id": _text(dispatch.get("action_id")),
        "owner": _text(owner_route.get("owner")) or _text(dispatch.get("owner")),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _authority_boundary(*, framework_id: str) -> dict[str, Any]:
    return {
        "surface_role": "refs_only_manuscript_authoring_advisory_worker",
        "framework_id": framework_id,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_authorize_owner_action": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_quality": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        items: list[object] = [value]
    elif isinstance(value, list | tuple):
        items = list(value)
    else:
        items = []
    return [text for item in items if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "FORBIDDEN_WRITES",
    "PAPERORCHESTRA_FRAMEWORK_ID",
    "PAPERORCHESTRA_REQUIRED_REF_FAMILIES",
    "PAPERORCHESTRA_SURFACE_KIND",
    "PAPERSPINE_FRAMEWORK_ID",
    "PAPERSPINE_REQUIRED_REF_FAMILIES",
    "PAPERSPINE_SURFACE_KIND",
    "build_paperorchestra_authoring_advisory",
    "build_paperspine_manuscript_advisory",
]
