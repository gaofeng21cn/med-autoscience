from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
KERNEL_OWNER = "artifact_lifecycle_authority_kernel"
ARTIFACT_ROLES = (
    "canonical_source",
    "runtime_ephemeral",
    "derived_projection",
    "human_handoff_mirror",
    "data_release",
    "cold_archive",
    "audit_log",
)
LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
GENERATED_AUTHORITY_SURFACE_NAMES = frozenset(
    {
        "current_package",
        "current_package.zip",
        "submission_minimal",
    }
)
GENERATED_AUTHORITY_SUFFIXES = frozenset({".zip", ".pdf", ".docx"})


class ArtifactLifecycleAuthorityKernel:
    def __init__(
        self,
        *,
        study_root: Path,
        quest_root: Path | None = None,
        manifest: Mapping[str, Any] | None = None,
        runtime_status: Mapping[str, Any] | None = None,
    ) -> None:
        self.study_root = _resolve_path(study_root)
        self.quest_root = _resolve_path(quest_root) if quest_root is not None else None
        self.runtime_status = runtime_status
        self._manifest_index = _manifest_index(manifest)

    def classify(self, path: Path) -> dict[str, Any]:
        resolved_path = _resolve_path(path)
        manifest_record = self._manifest_index.get(resolved_path, {})
        role = classify_artifact_role(
            path=resolved_path,
            study_root=self.study_root,
            quest_root=self.quest_root,
        )
        lifecycle = lifecycle_for_artifact(role=role, path=resolved_path)
        authority_allowed = authority_allowed_for_artifact(role=role)
        cleanup_candidate = cleanup_action_for_artifact(
            role=role,
            lifecycle=lifecycle,
            runtime_status=self.runtime_status,
        )
        cleanup_blockers = cleanup_blockers_for_artifact(role=role, runtime_status=self.runtime_status)
        projection_currentness = projection_currentness_for_artifact(role=role)
        return {
            "path": str(resolved_path),
            "role": role,
            "lifecycle": lifecycle,
            "owner": _record_text(manifest_record, "owner") or KERNEL_OWNER,
            "subtype": subtype_for_path(resolved_path),
            "source_refs": _mapping_value(manifest_record.get("source_refs")),
            "fingerprint": _record_text(manifest_record, "fingerprint"),
            "authority_allowed": authority_allowed,
            "cleanup_candidate": cleanup_candidate,
            "cleanup_blockers": cleanup_blockers,
            "restore_gate": restore_gate_for_artifact(role=role),
            "projection_currentness": projection_currentness,
            "edit_source_allowed": authority_allowed["edit"],
            "quality_authority_allowed": authority_allowed["quality"],
            "dispatch_authority_allowed": authority_allowed["dispatch"],
            "authority_blockers": authority_blockers_for_artifact(
                path=resolved_path,
                authority_allowed=authority_allowed,
            ),
            "cleanup_candidate_action": cleanup_candidate,
        }


def classify_artifact_role(
    *,
    path: Path,
    study_root: Path,
    quest_root: Path | None = None,
) -> str:
    resolved_path = _resolve_path(path)
    resolved_study_root = _resolve_path(study_root)
    resolved_quest_root = _resolve_path(quest_root) if quest_root is not None else None
    relative_context = ArtifactRolePathContext(
        path=resolved_path,
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
    )
    return _classify_artifact_role_from_context(relative_context)


def _classify_artifact_role_from_context(context: "ArtifactRolePathContext") -> str:
    if context.is_cold_archive:
        return "cold_archive"
    if context.is_runtime_ephemeral:
        return "runtime_ephemeral"
    if context.is_data_release:
        return "data_release"
    if context.is_audit_log:
        return "audit_log"
    if context.is_generated_projection:
        return "derived_projection"
    if context.is_human_handoff:
        return "human_handoff_mirror"
    return "canonical_source" if context.is_study_paper_surface else "audit_log"


class ArtifactRolePathContext:
    def __init__(self, *, path: Path, study_root: Path, quest_root: Path | None) -> None:
        self.path = path
        self.study_root = study_root
        self.quest_root = quest_root
        self.parts = path.parts

    @property
    def is_cold_archive(self) -> bool:
        return _path_contains(self.parts, (".ds", "cold_archive"))

    @property
    def is_runtime_ephemeral(self) -> bool:
        return self.quest_root is not None and _is_relative_to(self.path, self.quest_root / ".ds")

    @property
    def is_data_release(self) -> bool:
        return is_raw_intake_path(self.path) or _path_contains(self.parts, ("datasets",))

    @property
    def is_audit_log(self) -> bool:
        return _path_contains(self.parts, ("artifacts", "runtime")) or _path_contains(
            self.parts,
            ("artifacts", "publication_eval"),
        )

    @property
    def is_generated_projection(self) -> bool:
        return is_generated_authority_surface_path(self.path) or is_generated_authority_suffix(self.path)

    @property
    def is_human_handoff(self) -> bool:
        return _path_contains(self.parts, ("manuscript",))

    @property
    def is_study_paper_surface(self) -> bool:
        return _is_relative_to(self.path, self.study_root / "paper")


def lifecycle_for_artifact(*, role: str, path: Path) -> str:
    if role == "data_release" and is_raw_intake_lifecycle_path(path):
        return "raw_intake"
    mapping = {
        "canonical_source": "active_authority",
        "runtime_ephemeral": "runtime_transient",
        "derived_projection": "rebuildable_projection",
        "human_handoff_mirror": "human_handoff",
        "data_release": "retained_release",
        "cold_archive": "archived_restore_candidate",
        "audit_log": "audit_retained",
    }
    if role not in mapping:
        raise ValueError(f"unknown artifact role: {role}")
    return mapping[role]


def lifecycle_for_role(role: str) -> str:
    return lifecycle_for_artifact(role=role, path=Path(""))


def authority_allowed_for_artifact(*, role: str) -> dict[str, bool]:
    allowed = role == "canonical_source"
    return {"edit": allowed, "quality": allowed, "dispatch": allowed}


def cleanup_action_for_artifact(
    *,
    role: str,
    lifecycle: str,
    runtime_status: Mapping[str, Any] | None = None,
) -> str:
    if role == "runtime_ephemeral" and _runtime_is_live(runtime_status):
        return "audit-only"
    if role == "runtime_ephemeral":
        return "archive-compress"
    if role in {"canonical_source", "data_release", "audit_log", "human_handoff_mirror"}:
        return "keep-online"
    if lifecycle == "rebuildable_projection":
        return "rebuildable"
    if role == "cold_archive":
        return "restore-gated"
    return "audit-only"


def cleanup_blockers_for_artifact(*, role: str, runtime_status: Mapping[str, Any] | None = None) -> list[str]:
    if role == "runtime_ephemeral" and _runtime_is_live(runtime_status):
        return ["live_runtime_active"]
    return []


def restore_gate_for_artifact(*, role: str) -> dict[str, Any]:
    if role == "cold_archive":
        return {"required": True, "status": "restore_metadata_required"}
    return {"required": False, "status": "not_required"}


def projection_currentness_for_artifact(*, role: str) -> str:
    if role == "derived_projection":
        return "projection_only"
    if role == "canonical_source":
        return "authority_source"
    return "not_projection"


def authority_blockers_for_artifact(*, path: Path, authority_allowed: Mapping[str, bool]) -> list[str]:
    if authority_allowed.get("edit") and authority_allowed.get("quality") and authority_allowed.get("dispatch"):
        return []
    if not (is_generated_authority_surface_path(path) or is_generated_authority_suffix(path)):
        return []
    return [
        "generated_delivery_surface_cannot_be_edit_source",
        "generated_delivery_surface_cannot_be_quality_authority",
        "generated_delivery_surface_cannot_be_dispatch_authority",
    ]


def subtype_for_path(path: Path) -> str | None:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or None


def is_raw_intake_path(path: Path) -> bool:
    parts = path.parts
    return (
        _path_contains(parts, ("inbox",))
        or (_path_contains(parts, ("datasets",)) and path.suffix.lower() == ".zip")
        or _path_contains(parts, ("raw", "restricted"))
    )


def is_raw_intake_lifecycle_path(path: Path) -> bool:
    return is_raw_intake_path(path)


def is_generated_authority_surface_path(path: Path) -> bool:
    parts = path.parts
    return (
        any(part in GENERATED_AUTHORITY_SURFACE_NAMES for part in parts)
        or path.name in GENERATED_AUTHORITY_SURFACE_NAMES
    )


def is_generated_authority_suffix(path: Path) -> bool:
    return path.suffix.lower() in GENERATED_AUTHORITY_SUFFIXES


def _manifest_index(manifest: Mapping[str, Any] | None) -> dict[Path, Mapping[str, Any]]:
    if not isinstance(manifest, Mapping):
        return {}
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        return {}
    indexed: dict[Path, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        raw_path = _record_text(record, "path")
        if raw_path is None:
            continue
        indexed[_resolve_path(Path(raw_path))] = record
    return indexed


def _mapping_value(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _record_text(record: Mapping[str, Any], key: str) -> str | None:
    value = record.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _runtime_is_live(runtime_status: Mapping[str, Any] | None) -> bool:
    if not isinstance(runtime_status, Mapping):
        return False
    status = str(runtime_status.get("status") or "").strip().lower()
    active_run_id = str(runtime_status.get("active_run_id") or "").strip()
    return status in LIVE_RUNTIME_STATUSES and bool(active_run_id)


def _resolve_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    return Path(path).expanduser().resolve()


def _path_contains(parts: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    if not expected:
        return False
    if len(expected) == 1:
        return expected[0] in parts
    limit = len(parts) - len(expected) + 1
    return any(parts[index : index + len(expected)] == expected for index in range(max(0, limit)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


__all__ = [
    "ARTIFACT_ROLES",
    "KERNEL_OWNER",
    "SCHEMA_VERSION",
    "ArtifactLifecycleAuthorityKernel",
    "authority_allowed_for_artifact",
    "authority_blockers_for_artifact",
    "classify_artifact_role",
    "cleanup_action_for_artifact",
    "cleanup_blockers_for_artifact",
    "is_generated_authority_suffix",
    "is_generated_authority_surface_path",
    "is_raw_intake_lifecycle_path",
    "is_raw_intake_path",
    "lifecycle_for_artifact",
    "lifecycle_for_role",
    "projection_currentness_for_artifact",
    "restore_gate_for_artifact",
    "subtype_for_path",
]
