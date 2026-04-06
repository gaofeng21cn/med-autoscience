from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from med_autoscience.publication_profiles import (
    default_citation_style_for_publication_profile,
    exporter_family_for_publication_profile,
    is_generic_publication_profile,
    publication_profile_supports_citation_style,
    is_supported_publication_profile,
    normalize_publication_profile,
)

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


@dataclass(frozen=True)
class SubmissionTarget:
    publication_profile: str | None
    exporter_profile: str | None
    exporter_family: str | None
    journal_name: str | None
    journal_family: str | None
    citation_style: str | None
    official_guidelines_url: str | None
    template_url: str | None
    story_surface: str | None
    narrative_emphasis: tuple[str, ...]
    package_required: bool
    primary: bool
    source: str
    resolution_status: str
    exporter_status: str
    generic_export_allowed: bool | None
    decision_kind: str | None
    decision_source: str | None
    target_key: str


@dataclass(frozen=True)
class SubmissionTargetContract:
    targets: tuple[SubmissionTarget, ...]
    primary_target: SubmissionTarget
    unresolved_targets: tuple[SubmissionTarget, ...]
    export_publication_profiles: tuple[str, ...]


@dataclass(frozen=True)
class _TargetLayer:
    mode: str
    targets: tuple[SubmissionTarget, ...]


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _target_key(
    *,
    publication_profile: str | None,
    journal_name: str | None,
    official_guidelines_url: str | None,
    decision_kind: str | None,
) -> str:
    if journal_name:
        return f"journal:{journal_name.strip().lower()}"
    if official_guidelines_url:
        return f"url:{official_guidelines_url.strip()}"
    if publication_profile:
        return f"profile:{normalize_publication_profile(publication_profile)}"
    if decision_kind:
        return f"decision:{decision_kind.strip().lower()}"
    raise ValueError("submission target requires publication_profile, journal_name, official_guidelines_url, or decision_kind")


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _resolve_generic_export_allowed(
    *,
    payload: dict[str, Any],
    source: str,
    exporter_profile: str | None,
    decision_kind: str | None,
) -> bool | None:
    if "generic_export_allowed" in payload:
        return bool(payload.get("generic_export_allowed"))
    if decision_kind == "generic_export_authorized_without_unique_journal":
        return True
    if exporter_profile is None or not is_generic_publication_profile(exporter_profile):
        return None
    if source == "quest_paper_resolved":
        return False
    return True


def _resolve_exporter_status(
    *,
    exporter_profile: str | None,
    citation_style: str | None,
    generic_export_allowed: bool | None,
) -> str:
    if exporter_profile is None:
        return "missing_exporter_profile"
    if not is_supported_publication_profile(exporter_profile):
        return "unsupported_exporter_profile"
    if is_generic_publication_profile(exporter_profile) and generic_export_allowed is not True:
        return "blocked_generic_export_requires_explicit_controller_decision"
    if not publication_profile_supports_citation_style(exporter_profile, citation_style):
        return "unsupported_citation_style"
    return "ready"


def _normalize_target(
    raw_target: str | dict[str, Any],
    *,
    source: str,
    default_citation_style: str | None,
) -> SubmissionTarget:
    if isinstance(raw_target, str):
        payload: dict[str, Any] = {"publication_profile": raw_target}
    elif isinstance(raw_target, dict):
        payload = raw_target
    else:
        raise ValueError(f"unsupported submission target payload from {source}: {raw_target!r}")

    legacy_publication_profile_raw = payload.get("publication_profile")
    legacy_publication_profile = (
        normalize_publication_profile(str(legacy_publication_profile_raw))
        if isinstance(legacy_publication_profile_raw, str) and legacy_publication_profile_raw.strip()
        else None
    )
    exporter_profile_raw = payload.get("exporter_profile")
    exporter_profile = (
        normalize_publication_profile(str(exporter_profile_raw))
        if isinstance(exporter_profile_raw, str) and exporter_profile_raw.strip()
        else legacy_publication_profile
    )
    if (
        legacy_publication_profile is not None
        and exporter_profile is not None
        and legacy_publication_profile != exporter_profile
    ):
        raise ValueError("publication_profile legacy alias must match exporter_profile when both are present")

    publication_profile = legacy_publication_profile or exporter_profile
    decision_kind = _optional_text(payload.get("decision_kind"))
    decision_source = _optional_text(payload.get("decision_source"))
    journal_name = _optional_text(payload.get("journal_name"))
    official_guidelines_url = (
        _optional_text(payload.get("official_guidelines_url"))
    )
    citation_style = (
        _optional_text(payload.get("citation_style"))
        or default_citation_style_for_publication_profile(exporter_profile)
        or default_citation_style
    )
    story_surface = _optional_text(payload.get("story_surface"))
    emphasis_raw = payload.get("narrative_emphasis") or []
    if not isinstance(emphasis_raw, list):
        emphasis_raw = []
    narrative_emphasis = tuple(str(item) for item in emphasis_raw if str(item).strip())
    generic_export_allowed = _resolve_generic_export_allowed(
        payload=payload,
        source=source,
        exporter_profile=exporter_profile,
        decision_kind=decision_kind,
    )
    exporter_status = _resolve_exporter_status(
        exporter_profile=exporter_profile,
        citation_style=citation_style,
        generic_export_allowed=generic_export_allowed,
    )
    resolution_status = "resolved_profile" if is_supported_publication_profile(exporter_profile) else "needs_journal_resolution"
    if decision_kind == "blocked_no_unique_journal_target":
        resolution_status = "blocked_no_unique_journal_target"
    elif source == "quest_paper_resolved" and resolution_status == "needs_journal_resolution" and (
        journal_name or official_guidelines_url or decision_kind
    ):
        resolution_status = "resolved_target"
    return SubmissionTarget(
        publication_profile=publication_profile,
        exporter_profile=exporter_profile,
        exporter_family=_optional_text(payload.get("exporter_family"))
        or exporter_family_for_publication_profile(exporter_profile),
        journal_name=journal_name,
        journal_family=_optional_text(payload.get("journal_family")),
        citation_style=citation_style,
        official_guidelines_url=official_guidelines_url,
        template_url=_optional_text(payload.get("template_url")),
        story_surface=story_surface,
        narrative_emphasis=narrative_emphasis,
        package_required=bool(payload.get("package_required", True)),
        primary=bool(payload.get("primary", False)),
        source=source,
        resolution_status=resolution_status,
        exporter_status=exporter_status,
        generic_export_allowed=generic_export_allowed,
        decision_kind=decision_kind,
        decision_source=decision_source,
        target_key=_target_key(
            publication_profile=exporter_profile,
            journal_name=journal_name,
            official_guidelines_url=official_guidelines_url,
            decision_kind=decision_kind,
        ),
    )


def _targets_from_payload(
    payloads: list[Any] | tuple[Any, ...],
    *,
    source: str,
    default_citation_style: str | None,
) -> tuple[SubmissionTarget, ...]:
    return tuple(
        _normalize_target(raw_target, source=source, default_citation_style=default_citation_style)
        for raw_target in payloads
    )


def _load_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _profile_layer(profile: WorkspaceProfile | None) -> _TargetLayer:
    if profile is None:
        return _TargetLayer(mode="append", targets=tuple())
    if profile.default_submission_targets:
        return _TargetLayer(
            mode="append",
            targets=_targets_from_payload(
                profile.default_submission_targets,
                source="workspace_profile",
                default_citation_style=profile.default_citation_style,
            ),
        )
    return _TargetLayer(
        mode="append",
        targets=(
            SubmissionTarget(
                publication_profile=normalize_publication_profile(profile.default_publication_profile),
                exporter_profile=normalize_publication_profile(profile.default_publication_profile),
                exporter_family=exporter_family_for_publication_profile(profile.default_publication_profile),
                journal_name=None,
                journal_family=None,
                citation_style=profile.default_citation_style,
                official_guidelines_url=None,
                template_url=None,
                story_surface="general_medical_journal",
                narrative_emphasis=tuple(),
                package_required=True,
                primary=True,
                source="workspace_profile_fallback",
                resolution_status="resolved_profile",
                exporter_status="ready",
                generic_export_allowed=True,
                decision_kind=None,
                decision_source=None,
                target_key=f"profile:{normalize_publication_profile(profile.default_publication_profile)}",
            ),
        ),
    )


def _study_layer(study_root: Path | None, *, default_citation_style: str | None) -> _TargetLayer:
    if study_root is None:
        return _TargetLayer(mode="append", targets=tuple())
    payload = _load_yaml_dict(study_root / "study.yaml")
    raw_targets = payload.get("submission_targets") or []
    if not isinstance(raw_targets, list):
        raw_targets = []
    return _TargetLayer(
        mode=str(payload.get("submission_targets_mode", "append")).strip() or "append",
        targets=_targets_from_payload(raw_targets, source="study_yaml", default_citation_style=default_citation_style),
    )


def _quest_layer(quest_root: Path | None, *, default_citation_style: str | None) -> _TargetLayer:
    if quest_root is None:
        return _TargetLayer(mode="append", targets=tuple())
    payload = _load_yaml_dict(quest_root / "quest.yaml")
    startup_contract = payload.get("startup_contract") if isinstance(payload.get("startup_contract"), dict) else {}
    raw_targets = startup_contract.get("submission_targets")
    if not isinstance(raw_targets, list):
        raw_targets = payload.get("submission_targets") or []
    if not isinstance(raw_targets, list):
        raw_targets = []
    mode = startup_contract.get("submission_targets_mode")
    if not isinstance(mode, str) or not mode.strip():
        mode = payload.get("submission_targets_mode", "append")
    return _TargetLayer(
        mode=str(mode).strip() or "append",
        targets=_targets_from_payload(raw_targets, source="quest_yaml", default_citation_style=default_citation_style),
    )


def _quest_paper_resolved_layer(quest_root: Path | None, *, default_citation_style: str | None) -> _TargetLayer:
    if quest_root is None:
        return _TargetLayer(mode="append", targets=tuple())
    payload = _load_json_dict(quest_root / "paper" / "submission_targets.resolved.json")
    primary_target = payload.get("primary_target")
    if not isinstance(primary_target, dict):
        return _TargetLayer(mode="append", targets=tuple())
    decision_kind = _optional_text(primary_target.get("decision_kind")) or _optional_text(payload.get("decision_kind"))
    decision_source = _optional_text(primary_target.get("decision_source")) or _optional_text(payload.get("decision_source"))
    resolution_status = str(primary_target.get("resolution_status") or "").strip().lower()
    if resolution_status not in {"resolved", "resolved_profile"} and decision_kind is None:
        return _TargetLayer(mode="append", targets=tuple())
    normalized_target = dict(primary_target)
    normalized_target["primary"] = True
    if decision_kind is not None:
        normalized_target["decision_kind"] = decision_kind
    if decision_source is not None:
        normalized_target["decision_source"] = decision_source
    if "generic_export_allowed" not in normalized_target and "generic_export_allowed" in payload:
        normalized_target["generic_export_allowed"] = payload.get("generic_export_allowed")
    return _TargetLayer(
        mode="replace",
        targets=_targets_from_payload(
            [normalized_target],
            source="quest_paper_resolved",
            default_citation_style=default_citation_style,
        ),
    )


def _apply_layer(current_targets: list[SubmissionTarget], layer: _TargetLayer) -> list[SubmissionTarget]:
    if layer.mode == "replace":
        current_targets = []
    elif layer.mode != "append":
        raise ValueError(f"unsupported submission_targets_mode: {layer.mode}")

    by_key = {target.target_key: index for index, target in enumerate(current_targets)}
    for target in layer.targets:
        existing_index = by_key.get(target.target_key)
        if existing_index is None:
            by_key[target.target_key] = len(current_targets)
            current_targets.append(target)
        else:
            current_targets[existing_index] = target
    return current_targets


def resolve_submission_target_contract(
    *,
    profile: WorkspaceProfile | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
) -> SubmissionTargetContract:
    default_citation_style = profile.default_citation_style if profile is not None else None
    targets: list[SubmissionTarget] = []
    for layer in (
        _profile_layer(profile),
        _study_layer(study_root, default_citation_style=default_citation_style),
        _quest_layer(quest_root, default_citation_style=default_citation_style),
        _quest_paper_resolved_layer(quest_root, default_citation_style=default_citation_style),
    ):
        targets = _apply_layer(targets, layer)

    if not targets:
        raise ValueError("no submission targets resolved")

    primary_index = 0
    for index, target in enumerate(targets):
        if target.primary:
            primary_index = index

    final_targets: list[SubmissionTarget] = []
    for index, target in enumerate(targets):
        final_targets.append(
            SubmissionTarget(
                publication_profile=target.publication_profile,
                exporter_profile=target.exporter_profile,
                exporter_family=target.exporter_family,
                journal_name=target.journal_name,
                journal_family=target.journal_family,
                citation_style=target.citation_style,
                official_guidelines_url=target.official_guidelines_url,
                template_url=target.template_url,
                story_surface=target.story_surface,
                narrative_emphasis=target.narrative_emphasis,
                package_required=target.package_required,
                primary=index == primary_index,
                source=target.source,
                resolution_status=target.resolution_status,
                exporter_status=target.exporter_status,
                generic_export_allowed=target.generic_export_allowed,
                decision_kind=target.decision_kind,
                decision_source=target.decision_source,
                target_key=target.target_key,
            )
        )

    unresolved_targets = tuple(target for target in final_targets if target.resolution_status != "resolved_profile")
    export_publication_profiles = tuple(
        target.exporter_profile
        for target in final_targets
        if target.package_required and target.exporter_profile and target.exporter_status == "ready"
    )
    return SubmissionTargetContract(
        targets=tuple(final_targets),
        primary_target=final_targets[primary_index],
        unresolved_targets=unresolved_targets,
        export_publication_profiles=export_publication_profiles,
    )


def render_submission_target_overlay_block(
    *,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> str:
    resolved_lines: list[str] = []
    raw_defaults = tuple(default_submission_targets or ())
    if raw_defaults:
        resolved_lines.append("Workspace default submission targets baked into this overlay:")
        for item in raw_defaults:
            publication_profile = str(item.get("publication_profile") or "").strip() or "<unresolved>"
            story_surface = str(item.get("story_surface") or "").strip() or "unspecified"
            primary = " [primary]" if bool(item.get("primary")) else ""
            resolved_lines.append(f"- `{publication_profile}`{primary}; story_surface=`{story_surface}`")
    else:
        resolved_lines.append(
            "No explicit workspace default submission targets were injected into this overlay."
        )
        if default_publication_profile:
            resolved_lines.append(
                f"- Fallback publication profile: `{normalize_publication_profile(default_publication_profile)}`"
            )
        if default_citation_style:
            resolved_lines.append(f"- Fallback citation style: `{default_citation_style}`")

    return (
        "## Submission target contract\n\n"
        "This contract exists for venue-specific writing, finalization, and package export after a journal has already been selected.\n\n"
        "Do not use submission targets as a venue-discovery or shortlist-generation workflow.\n\n"
        "Before venue-specific writing, finalization, or package export, resolve active submission targets in this order:\n"
        "1. `quest.yaml -> startup_contract.submission_targets`\n"
        "2. `study.yaml -> submission_targets`\n"
        "3. workspace profile `default_submission_targets`\n\n"
        "Use the primary target to shape title framing, abstract emphasis, result section ordering, discussion emphasis, "
        "figure legends, and journal-facing terminology.\n\n"
        "If the research is still deciding which journals are realistic, first use the journal shortlist evidence workflow rather than this contract.\n\n"
        "If a target does not already map to a supported `publication_profile`, open `journal-resolution/SKILL.md`, use "
        "only official journal sources, and write both:\n"
        "- `paper/submission_target_resolution.md`\n"
        "- `paper/submission_targets.resolved.json`\n\n"
        "Do not infer journal requirements from memory. Do not export a venue-specific package for unresolved targets.\n\n"
        "Package-root contract:\n"
        "- Do not invent ad-hoc package roots such as `paper/submission_<journal>`.\n"
        "- Generic package roots are limited to `paper/submission_minimal`.\n"
        "- Venue-specific package roots are limited to `paper/journal_submissions/<publication_profile>`.\n"
        "- If journal resolution is still unresolved, keep the output as research state and do not treat it as a user-facing delivery surface.\n"
        "- The runtime quest tree is the build surface. The user-facing audit surface is `studies/<study-id>/manuscript` after delivery sync.\n\n"
        + "\n".join(resolved_lines)
        + "\n"
    )
