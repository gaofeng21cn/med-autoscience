from __future__ import annotations

from typing import Any, Iterable, Mapping

from med_autoscience.controllers import mainline_status

from .shared_labels import _non_empty_text


ALLOWED_PHYSICAL_ABSORB_STATUSES = {
    "landed_no_history_default_dependency_retired",
}


def _normalized_strings(values: Iterable[object]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return tuple(normalized)


def _single_project_boundary_payload(source: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(source or {})
    if not payload:
        payload = dict(mainline_status._single_project_boundary())
    return payload


def _capability_owner_boundary_payload(source: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(source or {})
    if not payload:
        payload = dict(mainline_status._capability_owner_boundary())
    return payload


def _require_mapping(payload: Mapping[str, Any], field: str, *, context: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} 缺少合法 mapping 字段: {field}")
    return value


def _require_nonempty_string_from_mapping(payload: Mapping[str, Any], field: str, *, context: str) -> str:
    value = payload.get(field)
    text = _non_empty_text(value)
    if text is None:
        raise ValueError(f"{context} 缺少合法字符串字段: {field}")
    return text


def _validate_single_project_boundary(value: object, *, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} 缺少合法 mapping 字段: single_project_boundary")
    payload = dict(value)
    surface_kind = _require_nonempty_string_from_mapping(payload, "surface_kind", context=context)
    if surface_kind != "single_project_boundary":
        raise ValueError(f"{context}.surface_kind 必须是 single_project_boundary，当前为 {surface_kind}。")
    summary = _require_nonempty_string_from_mapping(payload, "summary", context=context)
    mas_owner_modules = _normalized_strings(payload.get("mas_owner_modules") or [])
    if not mas_owner_modules:
        raise ValueError(f"{context}.mas_owner_modules 不能为空。")
    raw_roles = payload.get("mds_retained_roles") or []
    if not isinstance(raw_roles, list) or not raw_roles:
        raise ValueError(f"{context}.mds_retained_roles 不能为空。")
    normalized_roles: list[dict[str, str]] = []
    for index, item in enumerate(raw_roles):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.mds_retained_roles[{index}] 必须是 mapping。")
        role = dict(item)
        normalized_roles.append(
            {
                "role_id": _require_nonempty_string_from_mapping(
                    role,
                    "role_id",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
                "title": _require_nonempty_string_from_mapping(
                    role,
                    "title",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
                "summary": _require_nonempty_string_from_mapping(
                    role,
                    "summary",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
            }
        )
    land_now = _normalized_strings(payload.get("land_now") or [])
    post_gate_only = _normalized_strings(payload.get("post_gate_only") or [])
    not_now = _normalized_strings(payload.get("not_now") or [])
    if not post_gate_only:
        raise ValueError(f"{context}.post_gate_only 不能为空。")
    if not not_now:
        raise ValueError(f"{context}.not_now 不能为空。")
    return {
        "surface_kind": surface_kind,
        "summary": summary,
        "mas_owner_modules": mas_owner_modules,
        "mds_retained_roles": normalized_roles,
        "land_now": land_now,
        "post_gate_only": post_gate_only,
        "not_now": not_now,
    }


def _validate_capability_owner_boundary(value: object, *, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} 缺少合法 mapping 字段: capability_owner_boundary")
    payload = dict(value)
    surface_kind = _require_nonempty_string_from_mapping(payload, "surface_kind", context=context)
    if surface_kind != "mas_capability_owner_boundary":
        raise ValueError(
            f"{context}.surface_kind 必须是 mas_capability_owner_boundary，当前为 {surface_kind}。"
        )
    owner = _require_nonempty_string_from_mapping(payload, "owner", context=context)
    if owner != "MedAutoScience":
        raise ValueError(f"{context}.owner 必须是 MedAutoScience，当前为 {owner}。")
    mas_owned_capabilities = list(payload.get("mas_owned_capabilities") or [])
    if not mas_owned_capabilities:
        raise ValueError(f"{context}.mas_owned_capabilities 不能为空。")
    normalized_capabilities: list[dict[str, Any]] = []
    for index, item in enumerate(mas_owned_capabilities):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.mas_owned_capabilities[{index}] 必须是 mapping。")
        capability = dict(item)
        if _require_nonempty_string_from_mapping(
            capability,
            "owner",
            context=f"{context}.mas_owned_capabilities[{index}]",
        ) != "MedAutoScience":
            raise ValueError(f"{context}.mas_owned_capabilities[{index}].owner 必须是 MedAutoScience。")
        normalized_capabilities.append(
            {
                "capability_id": _require_nonempty_string_from_mapping(
                    capability,
                    "capability_id",
                    context=f"{context}.mas_owned_capabilities[{index}]",
                ),
                "owner": "MedAutoScience",
                "truth_surface": _require_nonempty_string_from_mapping(
                    capability,
                    "truth_surface",
                    context=f"{context}.mas_owned_capabilities[{index}]",
                ),
                "summary": _require_nonempty_string_from_mapping(
                    capability,
                    "summary",
                    context=f"{context}.mas_owned_capabilities[{index}]",
                ),
            }
        )
    mds_roles = list(payload.get("mds_migration_only_roles") or [])
    if not mds_roles:
        raise ValueError(f"{context}.mds_migration_only_roles 不能为空。")
    normalized_roles: list[dict[str, Any]] = []
    for index, item in enumerate(mds_roles):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.mds_migration_only_roles[{index}] 必须是 mapping。")
        role = dict(item)
        if role.get("migration_only") is not True:
            raise ValueError(f"{context}.mds_migration_only_roles[{index}].migration_only 必须是 true。")
        normalized_roles.append(
            {
                "role_id": _require_nonempty_string_from_mapping(
                    role,
                    "role_id",
                    context=f"{context}.mds_migration_only_roles[{index}]",
                ),
                "migration_only": True,
                "summary": _require_nonempty_string_from_mapping(
                    role,
                    "summary",
                    context=f"{context}.mds_migration_only_roles[{index}]",
                ),
            }
        )
    proof_boundary = _require_mapping(payload, "proof_and_absorb_boundary", context=context)
    physical_absorb_status = _require_nonempty_string_from_mapping(
        proof_boundary,
        "physical_absorb_status",
        context=f"{context}.proof_and_absorb_boundary",
    )
    if physical_absorb_status not in ALLOWED_PHYSICAL_ABSORB_STATUSES:
        raise ValueError(
            f"{context}.proof_and_absorb_boundary.physical_absorb_status 必须是 no-history absorb landed 状态。"
        )
    return {
        "surface_kind": surface_kind,
        "owner": owner,
        "summary": _require_nonempty_string_from_mapping(payload, "summary", context=context),
        "mas_owned_capabilities": normalized_capabilities,
        "mds_migration_only_roles": normalized_roles,
        "proof_and_absorb_boundary": {
            "surface_kind": _non_empty_text(proof_boundary.get("surface_kind")) or "proof_and_absorb_boundary",
            "parity_status": _require_nonempty_string_from_mapping(
                proof_boundary,
                "parity_status",
                context=f"{context}.proof_and_absorb_boundary",
            ),
            "parity_proof_sources": _normalized_strings(proof_boundary.get("parity_proof_sources") or []),
            "physical_absorb_status": physical_absorb_status,
            "physical_absorb_gate": _normalized_strings(proof_boundary.get("physical_absorb_gate") or []),
            "platform_maturation_status": _non_empty_text(proof_boundary.get("platform_maturation_status")),
        },
        "not_authority": _normalized_strings(payload.get("not_authority") or []),
    }


def _render_single_project_boundary_markdown_lines(single_project_boundary: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Single-Project Boundary",
        "",
        f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
        f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
    ]
    for item in single_project_boundary.get("land_now") or []:
        lines.append(f"- 当前 tranche 收口: {item}")
    for item in single_project_boundary.get("mds_retained_roles") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- MDS 保留 `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    for item in single_project_boundary.get("post_gate_only") or []:
        lines.append(f"- post-gate only: {item}")
    for item in single_project_boundary.get("not_now") or []:
        lines.append(f"- 当前不允许: {item}")
    return lines


def _render_capability_owner_boundary_markdown_lines(capability_owner_boundary: Mapping[str, Any]) -> list[str]:
    proof_boundary = dict(capability_owner_boundary.get("proof_and_absorb_boundary") or {})
    lines = [
        "## Capability Owner Boundary",
        "",
        f"- 当前摘要: {capability_owner_boundary.get('summary') or 'none'}",
        f"- owner: {capability_owner_boundary.get('owner') or 'none'}",
    ]
    for item in capability_owner_boundary.get("mas_owned_capabilities") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- MAS capability `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    for item in capability_owner_boundary.get("mds_migration_only_roles") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- MDS migration-only `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    lines.append(f"- parity proof: {proof_boundary.get('parity_status') or 'none'}")
    lines.append(f"- physical absorb: {proof_boundary.get('physical_absorb_status') or 'none'}")
    return lines
