from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from med_autoscience.developer_supervisor_mode import (
    EXPECTED_DEVELOPER_GITHUB_LOGIN,
    SUPPORTED_DEVELOPER_SUPERVISOR_MODES,
)
from med_autoscience.overlay.constants import (
    DEFAULT_MEDICAL_OVERLAY_SKILL_IDS,
    SUPPORTED_MEDICAL_OVERLAY_BOOTSTRAP_MODES,
)
from med_autoscience.policies.research_route_bias import DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID
from med_autoscience.policies.study_archetypes import DEFAULT_STUDY_ARCHETYPE_IDS
from med_autoscience.opl_runtime_contract import (
    EXTERNAL_MDS_ALLOWED_USES,
    OPL_HOSTED_STAGE_RUNTIME_ID,
    engine_id_for_runtime_ref,
    opl_runtime_default_operation_contract,
)

SUPPORTED_STARTUP_ANCHOR_POLICIES = (
    "scout_first_for_continue_existing_state",
    "intake_audit_first_for_continue_existing_state",
)
SUPPORTED_LEGACY_CODE_EXECUTION_POLICIES = (
    "forbid_without_user_approval",
    "audit_only",
    "allow_with_decision",
)
SUPPORTED_PUBLIC_DATA_DISCOVERY_POLICIES = (
    "required_for_scout_route_selection",
)
SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS = (
    "paper_framing",
    "journal_shortlist",
    "evidence_package",
)
NFPITNET_PROFILE_NAME = "nfpitnet"
NFPITNET_CANONICAL_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang/NF-PitNET")
NFPITNET_STALE_ALIAS_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    workspace_root: Path
    runtime_root: Path
    studies_root: Path
    portfolio_root: Path
    med_deepscientist_runtime_root: Path
    med_deepscientist_repo_root: Path | None
    default_publication_profile: str
    default_citation_style: str
    enable_medical_overlay: bool
    medical_overlay_scope: str
    medical_overlay_skills: tuple[str, ...]
    research_route_bias_policy: str
    preferred_study_archetypes: tuple[str, ...]
    default_submission_targets: tuple[dict[str, object], ...]
    hermes_agent_repo_root: Path | None = None
    hermes_home_root: Path = field(default_factory=lambda: (Path.home() / ".hermes").resolve())
    opl_runtime_ref: str = OPL_HOSTED_STAGE_RUNTIME_ID
    medical_overlay_bootstrap_mode: str = "ensure_ready"
    default_startup_anchor_policy: str = "scout_first_for_continue_existing_state"
    legacy_code_execution_policy: str = "forbid_without_user_approval"
    public_data_discovery_policy: str = "required_for_scout_route_selection"
    startup_boundary_requirements: tuple[str, ...] = SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS
    developer_supervisor_mode: str = "internal_only"
    developer_supervisor_mode_explicit: bool = False
    github_username: str | None = None
    mas_developer_github_usernames: tuple[str, ...] = (EXPECTED_DEVELOPER_GITHUB_LOGIN,)

    @property
    def managed_runtime_home(self) -> Path:
        return self.runtime_root.parent

    @property
    def managed_runtime_quests_root(self) -> Path:
        return self.runtime_root


def _require_string(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _optional_string(payload: dict[str, object], key: str, *, empty_as_none: bool = False) -> str | None:
    if key not in payload:
        return None
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string when provided")
    if not value.strip():
        if empty_as_none:
            return None
        raise TypeError(f"{key} must be a non-empty string when provided")
    return value


def _optional_string_with_default(payload: dict[str, object], key: str, *, default: str) -> str:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{key} must be a non-empty string")
    return value


def _optional_overlay_bootstrap_mode(payload: dict[str, object]) -> str:
    mode = _optional_string_with_default(
        payload,
        "medical_overlay_bootstrap_mode",
        default="ensure_ready",
    )
    if mode not in SUPPORTED_MEDICAL_OVERLAY_BOOTSTRAP_MODES:
        supported = ", ".join(SUPPORTED_MEDICAL_OVERLAY_BOOTSTRAP_MODES)
        raise TypeError(f"medical_overlay_bootstrap_mode must be one of: {supported}")
    return mode


def _optional_startup_anchor_policy(payload: dict[str, object]) -> str:
    policy = _optional_string_with_default(
        payload,
        "default_startup_anchor_policy",
        default="scout_first_for_continue_existing_state",
    )
    if policy not in SUPPORTED_STARTUP_ANCHOR_POLICIES:
        supported = ", ".join(SUPPORTED_STARTUP_ANCHOR_POLICIES)
        raise TypeError(f"default_startup_anchor_policy must be one of: {supported}")
    return policy


def _optional_legacy_code_execution_policy(payload: dict[str, object]) -> str:
    policy = _optional_string_with_default(
        payload,
        "legacy_code_execution_policy",
        default="forbid_without_user_approval",
    )
    if policy not in SUPPORTED_LEGACY_CODE_EXECUTION_POLICIES:
        supported = ", ".join(SUPPORTED_LEGACY_CODE_EXECUTION_POLICIES)
        raise TypeError(f"legacy_code_execution_policy must be one of: {supported}")
    return policy


def _optional_public_data_discovery_policy(payload: dict[str, object]) -> str:
    policy = _optional_string_with_default(
        payload,
        "public_data_discovery_policy",
        default="required_for_scout_route_selection",
    )
    if policy not in SUPPORTED_PUBLIC_DATA_DISCOVERY_POLICIES:
        supported = ", ".join(SUPPORTED_PUBLIC_DATA_DISCOVERY_POLICIES)
        raise TypeError(f"public_data_discovery_policy must be one of: {supported}")
    return policy


def _optional_startup_boundary_requirements(payload: dict[str, object]) -> tuple[str, ...]:
    requirements = _optional_string_list(
        payload,
        "startup_boundary_requirements",
        default=SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS,
    )
    unsupported = sorted(set(requirements).difference(SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS))
    if unsupported:
        supported = ", ".join(SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS)
        raise TypeError(f"startup_boundary_requirements items must be drawn from: {supported}")
    return requirements


def _optional_non_empty_string_list(
    payload: dict[str, object],
    key: str,
    *,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    values = _optional_string_list(payload, key, default=default)
    if any(not item.strip() for item in values):
        raise TypeError(f"{key} must be an array of non-empty strings")
    return values


def _optional_developer_supervisor_mode(payload: dict[str, object]) -> str:
    mode = _optional_string_with_default(
        payload,
        "developer_supervisor_mode",
        default="internal_only",
    )
    if mode not in SUPPORTED_DEVELOPER_SUPERVISOR_MODES:
        supported = ", ".join(SUPPORTED_DEVELOPER_SUPERVISOR_MODES)
        raise TypeError(f"developer_supervisor_mode must be one of: {supported}")
    return mode


def _optional_opl_runtime_ref(payload: dict[str, object]) -> str:
    runtime_ref = _optional_string_with_default(
        payload,
        "opl_runtime_ref",
        default=OPL_HOSTED_STAGE_RUNTIME_ID,
    )
    _reject_legacy_default_backend(runtime_ref=runtime_ref)
    engine_id_for_runtime_ref(runtime_ref)
    return runtime_ref


def _reject_legacy_default_backend(*, runtime_ref: str) -> None:
    if runtime_ref == "med_deepscientist":
        allowed = ", ".join(EXTERNAL_MDS_ALLOWED_USES)
        raise TypeError(
            "opl_runtime_ref cannot be med_deepscientist; "
            f"MDS is retained only for frozen source provenance or historical fixture references: {allowed}"
        )


def _optional_bool(payload: dict[str, object], key: str, *, default: bool) -> bool:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a boolean")
    return value


def _optional_path(payload: dict[str, object], key: str, *, profile_dir: Path) -> Path | None:
    value = _optional_string(payload, key, empty_as_none=True)
    if value is None:
        return None
    return _resolve_profile_path(value, profile_dir=profile_dir)


def _optional_reference_payload(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be a table when provided")
    return dict(value)


def _optional_historical_runtime_root(
    payload: dict[str, object],
    *,
    source_provenance: dict[str, object],
    historical_fixture_ref: dict[str, object],
    explicit_archive_import_ref: dict[str, object],
    profile_dir: Path,
    default: Path,
) -> Path:
    for table in (historical_fixture_ref, source_provenance, explicit_archive_import_ref):
        value = table.get("runtime_root")
        if isinstance(value, str) and value.strip():
            return _resolve_profile_path(value, profile_dir=profile_dir)
    value = _optional_string(payload, "med_deepscientist_runtime_root", empty_as_none=True)
    if value is not None:
        return _resolve_profile_path(value, profile_dir=profile_dir)
    return default


def _optional_archive_import_repo_root(
    payload: dict[str, object],
    *,
    source_provenance: dict[str, object],
    explicit_archive_import_ref: dict[str, object],
    profile_dir: Path,
) -> Path | None:
    for table in (explicit_archive_import_ref, source_provenance):
        value = table.get("controlled_backend_repo_root")
        if isinstance(value, str) and value.strip():
            return _resolve_profile_path(value, profile_dir=profile_dir)
    return _optional_path(payload, "med_deepscientist_repo_root", profile_dir=profile_dir)


def _optional_string_list(payload: dict[str, object], key: str, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be an array of strings")
    if any(not isinstance(item, str) for item in value):
        raise TypeError(f"{key} must be an array of strings")
    return tuple(value)


def _optional_dict_list(payload: dict[str, object], key: str) -> tuple[dict[str, object], ...]:
    if key not in payload:
        return ()
    value = payload[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be an array of tables")
    if any(not isinstance(item, dict) for item in value):
        raise TypeError(f"{key} must be an array of tables")
    return tuple(dict(item) for item in value)


def _resolve_profile_path(raw_path: str, *, profile_dir: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = profile_dir / candidate
    return candidate.resolve()


def _reject_stale_workspace_alias(*, profile_name: str, workspace_root: Path) -> None:
    if profile_name == NFPITNET_PROFILE_NAME and workspace_root == NFPITNET_STALE_ALIAS_WORKSPACE_ROOT:
        raise ValueError(
            "nfpitnet workspace_root points to stale local alias/scaffold "
            f"{NFPITNET_STALE_ALIAS_WORKSPACE_ROOT}; use canonical workspace "
            f"{NFPITNET_CANONICAL_WORKSPACE_ROOT}"
        )


def load_profile(path: str | Path) -> WorkspaceProfile:
    profile_path = Path(path).expanduser().resolve()
    payload = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    profile_dir = profile_path.parent
    profile_name = _require_string(payload, "name")
    workspace_root = _resolve_profile_path(_require_string(payload, "workspace_root"), profile_dir=profile_dir)
    _reject_stale_workspace_alias(profile_name=profile_name, workspace_root=workspace_root)
    runtime_root = _resolve_profile_path(_require_string(payload, "runtime_root"), profile_dir=profile_dir)
    managed_runtime_home = _optional_path(payload, "managed_runtime_home", profile_dir=profile_dir) or runtime_root.parent
    source_provenance = _optional_reference_payload(payload, "source_provenance")
    historical_fixture_ref = _optional_reference_payload(payload, "historical_fixture_ref")
    explicit_archive_import_ref = _optional_reference_payload(payload, "explicit_archive_import_ref")
    med_deepscientist_runtime_root = _optional_historical_runtime_root(
        payload,
        source_provenance=source_provenance,
        historical_fixture_ref=historical_fixture_ref,
        explicit_archive_import_ref=explicit_archive_import_ref,
        profile_dir=profile_dir,
        default=managed_runtime_home,
    )
    med_deepscientist_repo_root = _optional_archive_import_repo_root(
        payload,
        source_provenance=source_provenance,
        explicit_archive_import_ref=explicit_archive_import_ref,
        profile_dir=profile_dir,
    )
    hermes_agent_repo_root = _optional_path(payload, "hermes_agent_repo_root", profile_dir=profile_dir)
    hermes_home_root = _optional_path(payload, "hermes_home_root", profile_dir=profile_dir)
    opl_runtime_ref = _optional_opl_runtime_ref(payload)
    return WorkspaceProfile(
        name=profile_name,
        workspace_root=workspace_root,
        runtime_root=runtime_root,
        studies_root=_resolve_profile_path(_require_string(payload, "studies_root"), profile_dir=profile_dir),
        portfolio_root=_resolve_profile_path(_require_string(payload, "portfolio_root"), profile_dir=profile_dir),
        med_deepscientist_runtime_root=med_deepscientist_runtime_root,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root or (Path.home() / ".hermes").resolve(),
        opl_runtime_ref=opl_runtime_ref,
        default_publication_profile=_require_string(payload, "default_publication_profile"),
        default_citation_style=_require_string(payload, "default_citation_style"),
        enable_medical_overlay=_optional_bool(payload, "enable_medical_overlay", default=True),
        medical_overlay_scope=_optional_string_with_default(payload, "medical_overlay_scope", default="workspace"),
        medical_overlay_skills=_optional_string_list(
            payload,
            "medical_overlay_skills",
            default=DEFAULT_MEDICAL_OVERLAY_SKILL_IDS,
        ),
        research_route_bias_policy=_optional_string_with_default(
            payload,
            "research_route_bias_policy",
            default=DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID,
        ),
        preferred_study_archetypes=_optional_string_list(
            payload,
            "preferred_study_archetypes",
            default=DEFAULT_STUDY_ARCHETYPE_IDS,
        ),
        default_submission_targets=_optional_dict_list(payload, "default_submission_targets"),
        medical_overlay_bootstrap_mode=_optional_overlay_bootstrap_mode(payload),
        default_startup_anchor_policy=_optional_startup_anchor_policy(payload),
        legacy_code_execution_policy=_optional_legacy_code_execution_policy(payload),
        public_data_discovery_policy=_optional_public_data_discovery_policy(payload),
        startup_boundary_requirements=_optional_startup_boundary_requirements(payload),
        developer_supervisor_mode=_optional_developer_supervisor_mode(payload),
        developer_supervisor_mode_explicit="developer_supervisor_mode" in payload,
        github_username=_optional_string(payload, "github_username", empty_as_none=True),
        mas_developer_github_usernames=_optional_non_empty_string_list(
            payload,
            "mas_developer_github_usernames",
            default=(EXPECTED_DEVELOPER_GITHUB_LOGIN,),
        ),
    )


def profile_to_dict(profile: WorkspaceProfile) -> dict[str, object]:
    default_submission_targets = [dict(item) for item in profile.default_submission_targets]
    explicit_archive_import_ref = {
        "surface_kind": "explicit_archive_import_ref",
        "runtime_root": str(profile.med_deepscientist_runtime_root),
        "controlled_backend_repo_root": (
            str(profile.med_deepscientist_repo_root) if profile.med_deepscientist_repo_root else None
        ),
        "read_only": True,
    }
    return {
        "name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "managed_runtime_home": str(profile.managed_runtime_home),
        "managed_runtime_quests_root": str(profile.managed_runtime_quests_root),
        "studies_root": str(profile.studies_root),
        "portfolio_root": str(profile.portfolio_root),
        "source_provenance": {
            "surface_kind": "source_provenance",
            "source_role": "frozen_source_archive_or_historical_fixture",
            "runtime_root": str(profile.med_deepscientist_runtime_root),
            "controlled_backend_repo_root": explicit_archive_import_ref["controlled_backend_repo_root"],
            "read_only": True,
        },
        "historical_fixture_ref": {
            "surface_kind": "historical_fixture_ref",
            "runtime_root": str(profile.med_deepscientist_runtime_root),
            "runtime_root_exists": profile.med_deepscientist_runtime_root.exists(),
            "read_only": True,
        },
        "explicit_archive_import_ref": explicit_archive_import_ref,
        "hermes_agent_repo_root": str(profile.hermes_agent_repo_root) if profile.hermes_agent_repo_root else None,
        "hermes_home_root": str(profile.hermes_home_root),
        "opl_runtime_ref": profile.opl_runtime_ref,
        "opl_runtime_contract": opl_runtime_default_operation_contract(profile.opl_runtime_ref),
        "publication": {
            "default_publication_profile": profile.default_publication_profile,
            "default_citation_style": profile.default_citation_style,
            "default_submission_targets": default_submission_targets,
        },
        "overlay": {
            "enable_medical_overlay": profile.enable_medical_overlay,
            "medical_overlay_scope": profile.medical_overlay_scope,
            "medical_overlay_skills": list(profile.medical_overlay_skills),
            "medical_overlay_bootstrap_mode": profile.medical_overlay_bootstrap_mode,
        },
        "policy": {
            "research_route_bias_policy": profile.research_route_bias_policy,
            "default_startup_anchor_policy": profile.default_startup_anchor_policy,
            "legacy_code_execution_policy": profile.legacy_code_execution_policy,
            "public_data_discovery_policy": profile.public_data_discovery_policy,
            "startup_boundary_requirements": list(profile.startup_boundary_requirements),
            "developer_supervisor_mode": profile.developer_supervisor_mode,
            "developer_supervisor_mode_explicit": profile.developer_supervisor_mode_explicit,
            "github_username": profile.github_username,
            "mas_developer_github_usernames": list(profile.mas_developer_github_usernames),
        },
        "archetype": {
            "preferred_study_archetypes": list(profile.preferred_study_archetypes),
        },
    }
