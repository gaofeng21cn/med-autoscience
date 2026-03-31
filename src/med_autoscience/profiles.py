from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from med_autoscience.overlay.constants import (
    DEFAULT_MEDICAL_OVERLAY_SKILL_IDS,
    SUPPORTED_MEDICAL_OVERLAY_BOOTSTRAP_MODES,
)
from med_autoscience.policies.research_route_bias import DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID
from med_autoscience.policies.study_archetypes import DEFAULT_STUDY_ARCHETYPE_IDS

SUPPORTED_STARTUP_ANCHOR_POLICIES = (
    "scout_first_for_continue_existing_state",
    "intake_audit_first_for_continue_existing_state",
)
SUPPORTED_LEGACY_CODE_EXECUTION_POLICIES = (
    "forbid_without_user_approval",
    "audit_only",
    "allow_with_decision",
)
SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS = (
    "paper_framing",
    "journal_shortlist",
    "evidence_package",
)


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    workspace_root: Path
    runtime_root: Path
    studies_root: Path
    portfolio_root: Path
    deepscientist_runtime_root: Path
    deepscientist_repo_root: Path | None
    default_publication_profile: str
    default_citation_style: str
    enable_medical_overlay: bool
    medical_overlay_scope: str
    medical_overlay_skills: tuple[str, ...]
    research_route_bias_policy: str
    preferred_study_archetypes: tuple[str, ...]
    default_submission_targets: tuple[dict[str, object], ...]
    medical_overlay_bootstrap_mode: str = "ensure_ready"
    default_startup_anchor_policy: str = "scout_first_for_continue_existing_state"
    legacy_code_execution_policy: str = "forbid_without_user_approval"
    startup_boundary_requirements: tuple[str, ...] = SUPPORTED_STARTUP_BOUNDARY_REQUIREMENTS


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


def load_profile(path: str | Path) -> WorkspaceProfile:
    profile_path = Path(path).expanduser().resolve()
    payload = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    profile_dir = profile_path.parent
    deepscientist_repo_root = _optional_path(payload, "deepscientist_repo_root", profile_dir=profile_dir)
    return WorkspaceProfile(
        name=_require_string(payload, "name"),
        workspace_root=_resolve_profile_path(_require_string(payload, "workspace_root"), profile_dir=profile_dir),
        runtime_root=_resolve_profile_path(_require_string(payload, "runtime_root"), profile_dir=profile_dir),
        studies_root=_resolve_profile_path(_require_string(payload, "studies_root"), profile_dir=profile_dir),
        portfolio_root=_resolve_profile_path(_require_string(payload, "portfolio_root"), profile_dir=profile_dir),
        deepscientist_runtime_root=_resolve_profile_path(
            _require_string(payload, "deepscientist_runtime_root"),
            profile_dir=profile_dir,
        ),
        deepscientist_repo_root=deepscientist_repo_root,
        default_publication_profile=_require_string(payload, "default_publication_profile"),
        default_citation_style=_require_string(payload, "default_citation_style"),
        enable_medical_overlay=_optional_bool(payload, "enable_medical_overlay", default=True),
        medical_overlay_scope=_optional_string_with_default(payload, "medical_overlay_scope", default="global"),
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
        startup_boundary_requirements=_optional_startup_boundary_requirements(payload),
    )


def profile_to_dict(profile: WorkspaceProfile) -> dict[str, object]:
    default_submission_targets = [dict(item) for item in profile.default_submission_targets]
    return {
        "name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "studies_root": str(profile.studies_root),
        "portfolio_root": str(profile.portfolio_root),
        "deepscientist_runtime_root": str(profile.deepscientist_runtime_root),
        "deepscientist_repo_root": str(profile.deepscientist_repo_root) if profile.deepscientist_repo_root else None,
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
            "startup_boundary_requirements": list(profile.startup_boundary_requirements),
        },
        "archetype": {
            "preferred_study_archetypes": list(profile.preferred_study_archetypes),
        },
    }
