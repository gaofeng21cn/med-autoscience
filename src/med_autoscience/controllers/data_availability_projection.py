from __future__ import annotations

from typing import Any


AUTHORITY_SCOPE = "submission_compliance_reviewer_input"
FAIR_KEYS = ("findable", "accessible", "interoperable", "reusable")
DATACITE_REQUIRED_FIELDS = (
    "identifier",
    "identifier_type",
    "creators",
    "title",
    "publisher",
    "publication_year",
    "resource_type",
)


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _has_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def project_release_data_availability(
    *,
    release: dict[str, object] | None,
    dataset_id: str,
    family_id: str | None,
    version_id: str | None,
    source_path: str | None = None,
) -> dict[str, Any]:
    release_payload = release or {}
    contract = _dict(release_payload.get("declared_release_contract"))
    availability = _dict(contract.get("data_availability"))
    datacite = _dict(availability.get("datacite"))
    fair = _dict(availability.get("fair_checklist"))
    restricted_data = availability.get("restricted_data") is True
    access_route = _string(availability.get("access_route"))
    repository_identifier = _string(availability.get("repository_identifier"))
    repository_url = _string(availability.get("repository_url"))

    required = bool(availability)
    blockers: list[str] = []
    if not required:
        return {
            "authority_scope": AUTHORITY_SCOPE,
            "can_authorize_study_truth": False,
            "can_authorize_publication_verdict": False,
            "can_authorize_artifact_authority": False,
            "required": False,
            "dataset_location": {
                "dataset_id": dataset_id,
                "family_id": family_id,
                "version_id": version_id,
                "source_path": source_path,
                "data_root": (
                    release_payload.get("data_root")
                    if isinstance(release_payload.get("data_root"), str)
                    else None
                ),
                "main_outputs": (
                    release_payload.get("main_outputs")
                    if isinstance(release_payload.get("main_outputs"), dict)
                    else {}
                ),
            },
            "access": {
                "restricted_data": False,
                "route": None,
            },
            "repository": {
                "identifier": None,
                "url": None,
            },
            "datacite": {},
            "fair_checklist": {key: False for key in FAIR_KEYS},
            "blockers": [],
            "ready": True,
        }
    if restricted_data and access_route is None:
        blockers.append("restricted_data_missing_access_route")
    if repository_identifier is None:
        blockers.append("missing_repository_identifier")
    for field in DATACITE_REQUIRED_FIELDS:
        if not _has_value(datacite.get(field)):
            blockers.append(f"datacite_missing_{field}")
    for field in FAIR_KEYS:
        if fair.get(field) is not True:
            blockers.append(f"fair_{field}_not_confirmed")

    return {
        "authority_scope": AUTHORITY_SCOPE,
        "can_authorize_study_truth": False,
        "can_authorize_publication_verdict": False,
        "can_authorize_artifact_authority": False,
        "required": True,
        "dataset_location": {
            "dataset_id": dataset_id,
            "family_id": family_id,
            "version_id": version_id,
            "source_path": source_path,
            "data_root": (
                release_payload.get("data_root")
                if isinstance(release_payload.get("data_root"), str)
                else None
            ),
            "main_outputs": (
                release_payload.get("main_outputs")
                if isinstance(release_payload.get("main_outputs"), dict)
                else {}
            ),
        },
        "access": {
            "restricted_data": restricted_data,
            "route": access_route,
        },
        "repository": {
            "identifier": repository_identifier,
            "url": repository_url,
        },
        "datacite": datacite,
        "fair_checklist": {key: fair.get(key) is True for key in FAIR_KEYS},
        "blockers": blockers,
        "ready": not blockers,
    }


def summarize_release_data_availability(releases: list[dict[str, object]]) -> dict[str, Any]:
    blocked: list[dict[str, Any]] = []
    ready_count = 0
    for release in releases:
        projection = project_release_data_availability(
            release=release,
            dataset_id=str(release.get("dataset_id") or ""),
            family_id=release.get("family_id") if isinstance(release.get("family_id"), str) else None,
            version_id=release.get("version_id") if isinstance(release.get("version_id"), str) else None,
        )
        if projection["ready"]:
            ready_count += 1
            continue
        blocked.append(
            {
                "family_id": release.get("family_id"),
                "version_id": release.get("version_id"),
                "dataset_id": release.get("dataset_id"),
                "blockers": projection["blockers"],
            }
        )
    return {
        "release_count": len(releases),
        "ready_release_count": ready_count,
        "blocked_release_count": len(blocked),
        "blocked_releases": blocked,
    }
