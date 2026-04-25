from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import data_assets


STARTUP_READINESS_SCHEMA_VERSION = 1
STARTUP_READINESS_BASENAME = "latest_startup_data_readiness.json"
STANDARDIZED_ACCESS_TIERS = {"analysis_ready_standardized", "publication_ready_standardized"}
STANDARDIZATION_SENSITIVE_TERMS = {
    "medication",
    "drug",
    "treatment",
    "therapy",
    "gap",
    "attainment",
    "用药",
    "药物",
    "治疗",
    "达标",
    "缺口",
}


def _startup_root(workspace_root: Path) -> Path:
    return data_assets._data_assets_root(workspace_root) / "startup"


def _startup_report_path(workspace_root: Path) -> Path:
    return _startup_root(workspace_root) / STARTUP_READINESS_BASENAME


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    data_assets._write_json(path, payload)


def _latest_private_releases_by_family(releases: list[dict[str, object]]) -> list[dict[str, object]]:
    latest_versions = data_assets._latest_versions_by_family(releases)
    latest_releases: list[dict[str, object]] = []
    for family_id in sorted(latest_versions):
        version_id = latest_versions[family_id]
        release = next(
            item
            for item in releases
            if item.get("family_id") == family_id and item.get("version_id") == version_id
        )
        latest_releases.append(
            {
                "family_id": family_id,
                "version_id": version_id,
                "dataset_id": release.get("dataset_id"),
                "raw_snapshot": release.get("raw_snapshot"),
                "generated_by": release.get("generated_by"),
                "contract_status": release.get("contract_status"),
            }
        )
    return latest_releases


def _dataset_has_actionable_public_match(
    *,
    dataset_input: dict[str, Any],
    actionable_public_datasets: list[dict[str, Any]],
) -> bool:
    dataset_id = dataset_input.get("dataset_id")
    family_id = dataset_input.get("family_id")
    if not isinstance(dataset_id, str) and not isinstance(family_id, str):
        return False
    for item in actionable_public_datasets:
        target_dataset_ids = item.get("target_dataset_ids") or []
        target_families = item.get("target_families") or []
        if isinstance(dataset_id, str) and dataset_id in target_dataset_ids:
            return True
        if isinstance(family_id, str) and family_id in target_families:
            return True
    return False


def _study_declares_standardization_sensitive_scope(study_id: str, dataset_inputs: list[dict[str, Any]]) -> bool:
    haystack_parts = [study_id]
    for dataset in dataset_inputs:
        for key in ("dataset_id", "source_path", "family_id"):
            value = dataset.get(key)
            if isinstance(value, str):
                haystack_parts.append(value)
    haystack = " ".join(haystack_parts).lower()
    return any(term.lower() in haystack for term in STANDARDIZATION_SENSITIVE_TERMS)


def _release_lacks_standardized_contract(dataset: dict[str, Any]) -> bool:
    status = data_assets._normalize_dict(dataset.get("standardization_status"))
    access_tier = status.get("access_tier")
    return access_tier not in STANDARDIZED_ACCESS_TIERS


def _study_summary(impact_report: dict[str, Any], *, actionable_public_datasets: list[dict[str, Any]]) -> dict[str, Any]:
    studies = impact_report.get("studies") or []
    review_needed_study_ids: list[str] = []
    clear_study_ids: list[str] = []
    outdated_private_release_study_ids: list[str] = []
    unresolved_contract_study_ids: list[str] = []
    standardization_blocked_study_ids: list[str] = []
    public_extension_study_ids: list[str] = []

    for item in studies:
        if not isinstance(item, dict):
            continue
        study_id = item.get("study_id")
        if not isinstance(study_id, str):
            continue
        dataset_inputs = item.get("dataset_inputs") or []
        has_outdated_private_release = any(
            dataset.get("private_version_status") == "older_than_latest"
            for dataset in dataset_inputs
            if isinstance(dataset, dict)
        )
        has_unresolved_contract = any(
            dataset.get("private_version_status") in {"unversioned_path", "family_not_registered"}
            or dataset.get("private_contract_status") in {"directory_scan_only", "release_not_registered"}
            for dataset in dataset_inputs
            if isinstance(dataset, dict)
        )
        has_standardization_blocker = (
            _study_declares_standardization_sensitive_scope(study_id, dataset_inputs)
            and any(
                _release_lacks_standardized_contract(dataset)
                for dataset in dataset_inputs
                if isinstance(dataset, dict) and dataset.get("private_version_status") != "public_registry_backed"
            )
        )
        if has_outdated_private_release or has_unresolved_contract or has_standardization_blocker:
            review_needed_study_ids.append(study_id)
        else:
            clear_study_ids.append(study_id)
        if has_outdated_private_release:
            outdated_private_release_study_ids.append(study_id)
        if has_unresolved_contract:
            unresolved_contract_study_ids.append(study_id)
        if has_standardization_blocker:
            standardization_blocked_study_ids.append(study_id)
        if any(
            _dataset_has_actionable_public_match(
                dataset_input=dataset,
                actionable_public_datasets=actionable_public_datasets,
            )
            for dataset in dataset_inputs
            if isinstance(dataset, dict)
        ):
            public_extension_study_ids.append(study_id)

    return {
        "study_count": len([item for item in studies if isinstance(item, dict)]),
        "review_needed_count": len(review_needed_study_ids),
        "clear_count": len(clear_study_ids),
        "review_needed_study_ids": sorted(review_needed_study_ids),
        "clear_study_ids": sorted(clear_study_ids),
        "outdated_private_release_study_ids": sorted(outdated_private_release_study_ids),
        "unresolved_contract_study_ids": sorted(unresolved_contract_study_ids),
        "standardization_blocked_study_ids": sorted(standardization_blocked_study_ids),
        "public_extension_study_ids": sorted(public_extension_study_ids),
    }


def _sorted_string_set(values: list[str]) -> list[str]:
    return sorted({item for item in values if item})


def _actionable_public_datasets(public_validation_report: dict[str, Any]) -> list[dict[str, Any]]:
    datasets = public_validation_report.get("datasets") or []
    return [
        item
        for item in datasets
        if isinstance(item, dict)
        if item.get("validation", {}).get("is_valid")
        if item.get("status") != "rejected"
    ]


def _public_opportunities(public_validation_report: dict[str, Any]) -> dict[str, Any]:
    valid_datasets = _actionable_public_datasets(public_validation_report)

    by_family: dict[str, dict[str, Any]] = {}
    by_role: dict[str, dict[str, Any]] = {}
    by_study_archetype: dict[str, dict[str, Any]] = {}
    by_target_dataset_id: dict[str, dict[str, Any]] = {}

    for item in valid_datasets:
        dataset_id = item.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id:
            continue
        roles = _sorted_string_set(list(item.get("roles") or []))
        study_archetypes = _sorted_string_set(list(item.get("target_study_archetypes") or []))
        target_families = _sorted_string_set(list(item.get("target_families") or []))
        target_dataset_ids = _sorted_string_set(list(item.get("target_dataset_ids") or []))

        for family_id in target_families:
            entry = by_family.setdefault(
                family_id,
                {"family_id": family_id, "dataset_ids": set(), "roles": set(), "study_archetypes": set()},
            )
            entry["dataset_ids"].add(dataset_id)
            entry["roles"].update(roles)
            entry["study_archetypes"].update(study_archetypes)

        for role in roles:
            entry = by_role.setdefault(role, {"role": role, "dataset_ids": set()})
            entry["dataset_ids"].add(dataset_id)

        for archetype in study_archetypes:
            entry = by_study_archetype.setdefault(archetype, {"study_archetype": archetype, "dataset_ids": set()})
            entry["dataset_ids"].add(dataset_id)

        for target_dataset_id in target_dataset_ids:
            entry = by_target_dataset_id.setdefault(
                target_dataset_id,
                {"target_dataset_id": target_dataset_id, "dataset_ids": set(), "roles": set()},
            )
            entry["dataset_ids"].add(dataset_id)
            entry["roles"].update(roles)

    def render_family_groups() -> list[dict[str, Any]]:
        rendered: list[dict[str, Any]] = []
        for family_id in sorted(by_family):
            entry = by_family[family_id]
            dataset_ids = sorted(entry["dataset_ids"])
            rendered.append(
                {
                    "family_id": family_id,
                    "dataset_count": len(dataset_ids),
                    "dataset_ids": dataset_ids,
                    "roles": sorted(entry["roles"]),
                    "study_archetypes": sorted(entry["study_archetypes"]),
                }
            )
        return rendered

    def render_simple_groups(groups: dict[str, dict[str, Any]], *, key_name: str) -> list[dict[str, Any]]:
        rendered: list[dict[str, Any]] = []
        for key in sorted(groups):
            entry = groups[key]
            dataset_ids = sorted(entry["dataset_ids"])
            payload = {
                key_name: entry[key_name],
                "dataset_count": len(dataset_ids),
                "dataset_ids": dataset_ids,
            }
            if "roles" in entry:
                payload["roles"] = sorted(entry["roles"])
            rendered.append(payload)
        return rendered

    return {
        "by_family": render_family_groups(),
        "by_role": render_simple_groups(by_role, key_name="role"),
        "by_study_archetype": render_simple_groups(by_study_archetype, key_name="study_archetype"),
        "by_target_dataset_id": render_simple_groups(by_target_dataset_id, key_name="target_dataset_id"),
    }


def _recommendations(*, private_release_count: int, study_summary: dict[str, Any], valid_public_dataset_count: int) -> list[str]:
    recommendations: list[str] = []
    if private_release_count == 0:
        recommendations.append("register_private_releases_before_launch")
    if study_summary["unresolved_contract_study_ids"]:
        recommendations.append("repair_study_dataset_contracts")
    if study_summary.get("standardization_blocked_study_ids"):
        recommendations.append("materialize_standardized_analysis_release")
    if study_summary["outdated_private_release_study_ids"]:
        recommendations.append("reassess_studies_against_latest_private_release")
    if valid_public_dataset_count > 0:
        recommendations.append("screen_and_materialize_valid_public_datasets_for_extension")
    if not recommendations:
        recommendations.append("startup_data_ready")
    return recommendations


def startup_data_readiness(*, workspace_root: Path) -> dict[str, Any]:
    data_assets.init_data_assets(workspace_root=workspace_root)
    public_validation = data_assets.validate_public_registry(workspace_root=workspace_root)
    impact_report = data_assets.assess_data_asset_impact(workspace_root=workspace_root)
    private_payload = data_assets._load_json(
        data_assets._private_registry_path(workspace_root),
        default={"schema_version": 2, "releases": []},
    )
    releases = [
        item
        for item in private_payload.get("releases", [])
        if isinstance(item, dict)
    ]

    actionable_public_datasets = _actionable_public_datasets(public_validation)
    study_summary = _study_summary(impact_report, actionable_public_datasets=actionable_public_datasets)
    public_summary = {
        "dataset_count": public_validation["dataset_count"],
        "valid_dataset_count": public_validation["valid_dataset_count"],
        "invalid_dataset_count": public_validation["invalid_dataset_count"],
        "actionable_dataset_count": len(actionable_public_datasets),
        "rejected_dataset_count": sum(
            1
            for item in public_validation.get("datasets", [])
            if isinstance(item, dict) and item.get("validation", {}).get("is_valid") and item.get("status") == "rejected"
        ),
    }
    recommendations = _recommendations(
        private_release_count=len(releases),
        study_summary=study_summary,
        valid_public_dataset_count=public_summary["actionable_dataset_count"],
    )
    report = {
        "schema_version": STARTUP_READINESS_SCHEMA_VERSION,
        "workspace_root": str(workspace_root),
        "status": (
            "attention_needed"
            if len(releases) == 0
            or bool(study_summary["unresolved_contract_study_ids"])
            or bool(study_summary["outdated_private_release_study_ids"])
            or bool(study_summary.get("standardization_blocked_study_ids"))
            else "clear"
        ),
        "private_release_count": len(releases),
        "latest_private_releases_by_family": _latest_private_releases_by_family(releases),
        "study_summary": study_summary,
        "public_summary": public_summary,
        "public_opportunities": _public_opportunities(public_validation),
        "recommendations": recommendations,
    }
    report_path = _startup_report_path(workspace_root)
    report["report_path"] = str(report_path)
    _write_json(report_path, report)
    return report
