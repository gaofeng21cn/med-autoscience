from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Any

from med_autoscience.overlay.constants import DEFAULT_MEDICAL_OVERLAY_SKILL_IDS
from med_autoscience.policies.research_route_bias import (
    DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID,
    get_policy,
    render_policy_block,
)
from med_autoscience.policies.study_archetypes import (
    DEFAULT_STUDY_ARCHETYPE_IDS,
    get_archetype,
    render_archetype_block,
)
from med_autoscience.submission_targets import render_submission_target_overlay_block


SCHEMA_VERSION = 1
OVERLAY_NAME = "med_autoscience_medical_deepscientist_overlay"
MANIFEST_NAME = ".med_autoscience_overlay.json"
ROUTE_BIAS_TOKEN = "{{MED_AUTOSCIENCE_ROUTE_BIAS}}"
STUDY_ARCHETYPES_TOKEN = "{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}"
SUBMISSION_TARGETS_TOKEN = "{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}"
FRONTLOAD_STAGE_IDS = frozenset({"scout", "idea", "decision"})
SKILL_TEMPLATE_MAP = {
    "scout": "deepscientist-scout.SKILL.md",
    "idea": "deepscientist-idea.SKILL.md",
    "decision": "deepscientist-decision.SKILL.md",
    "write": "deepscientist-write.SKILL.md",
    "finalize": "deepscientist-finalize.SKILL.md",
    "journal-resolution": "deepscientist-journal-resolution.SKILL.md",
}


@dataclass(frozen=True)
class OverlayTarget:
    skill_id: str
    scope: str
    target_root: Path
    skill_path: Path
    manifest_path: Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fingerprint(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_skill_ids(skill_ids: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    normalized = DEFAULT_MEDICAL_OVERLAY_SKILL_IDS if skill_ids is None else tuple(skill_ids)
    if ("write" in normalized or "finalize" in normalized) and "journal-resolution" not in normalized:
        normalized = normalized + ("journal-resolution",)
    invalid = [skill_id for skill_id in normalized if skill_id not in SKILL_TEMPLATE_MAP]
    if invalid:
        raise ValueError(f"Unsupported medical overlay skill ids: {', '.join(invalid)}")
    return normalized


def _normalize_policy_id(policy_id: str | None) -> str:
    normalized = DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID if policy_id is None else str(policy_id)
    return get_policy(normalized).policy_id


def _normalize_archetype_ids(archetype_ids: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    normalized = DEFAULT_STUDY_ARCHETYPE_IDS if archetype_ids is None else tuple(archetype_ids)
    for archetype_id in normalized:
        get_archetype(archetype_id)
    return normalized


def _resolve_targets(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
) -> tuple[str, Path | None, list[OverlayTarget]]:
    if quest_root is not None:
        resolved_quest_root = Path(quest_root).expanduser().resolve()
        scope = "quest"
        skills_root = resolved_quest_root / ".codex" / "skills"
    else:
        resolved_quest_root = None
        scope = "global"
        resolved_home = (Path(home) if home is not None else Path.home()).expanduser().resolve()
        skills_root = resolved_home / ".codex" / "skills"

    normalized_skill_ids = _normalize_skill_ids(skill_ids)
    targets = [
        OverlayTarget(
            skill_id=skill_id,
            scope=scope,
            target_root=skills_root / f"deepscientist-{skill_id}",
            skill_path=skills_root / f"deepscientist-{skill_id}" / "SKILL.md",
            manifest_path=skills_root / f"deepscientist-{skill_id}" / MANIFEST_NAME,
        )
        for skill_id in normalized_skill_ids
    ]
    return scope, resolved_quest_root, targets


def load_overlay_skill_text(
    skill_id: str,
    *,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> str:
    template_name = SKILL_TEMPLATE_MAP[skill_id]
    template_path = resources.files("med_autoscience.overlay.templates").joinpath(template_name)
    template = template_path.read_text(encoding="utf-8")
    if skill_id in {"write", "finalize", "journal-resolution"}:
        if SUBMISSION_TARGETS_TOKEN not in template:
            raise ValueError(f"Overlay template for {skill_id} is missing submission target token")
        template = template.replace(
            SUBMISSION_TARGETS_TOKEN,
            render_submission_target_overlay_block(
                default_submission_targets=default_submission_targets,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            ).rstrip(),
        )
    if skill_id not in FRONTLOAD_STAGE_IDS:
        return template

    normalized_policy_id = _normalize_policy_id(policy_id)
    normalized_archetype_ids = _normalize_archetype_ids(archetype_ids)
    if ROUTE_BIAS_TOKEN not in template or STUDY_ARCHETYPES_TOKEN not in template:
        raise ValueError(f"Overlay template for {skill_id} is missing dynamic policy tokens")
    rendered = template.replace(
        ROUTE_BIAS_TOKEN,
        render_policy_block(stage_id=skill_id, policy_id=normalized_policy_id).rstrip(),
    )
    rendered = rendered.replace(
        STUDY_ARCHETYPES_TOKEN,
        render_archetype_block(archetype_ids=normalized_archetype_ids).rstrip(),
    )
    return rendered


def _describe_target(
    target: OverlayTarget,
    *,
    policy_id: str,
    archetype_ids: tuple[str, ...],
    default_submission_targets: tuple[dict[str, object], ...],
    default_publication_profile: str | None,
    default_citation_style: str | None,
) -> dict[str, Any]:
    overlay_text = load_overlay_skill_text(
        target.skill_id,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )
    overlay_fingerprint = _fingerprint(overlay_text)
    manifest = _load_json(target.manifest_path)
    current_fingerprint = None
    source_fingerprint_before_overlay = manifest.get("source_fingerprint_before_overlay")
    manifest_present = bool(manifest)

    if target.skill_path.exists():
        current_fingerprint = _fingerprint(target.skill_path.read_text(encoding="utf-8"))
        if manifest_present:
            if current_fingerprint == overlay_fingerprint:
                status = "overlay_applied"
                needs_reapply = False
            elif source_fingerprint_before_overlay and current_fingerprint == source_fingerprint_before_overlay:
                status = "overwritten_by_upstream"
                needs_reapply = True
            else:
                status = "drifted"
                needs_reapply = True
        else:
            if current_fingerprint == overlay_fingerprint:
                status = "overlay_present_unmanaged"
            else:
                status = "not_installed"
            needs_reapply = status != "overlay_applied"
    else:
        status = "missing_target"
        needs_reapply = True

    return {
        "skill_id": target.skill_id,
        "scope": target.scope,
        "target_root": str(target.target_root),
        "skill_path": str(target.skill_path),
        "manifest_path": str(target.manifest_path),
        "status": status,
        "needs_reapply": needs_reapply,
        "manifest_present": manifest_present,
        "current_fingerprint": current_fingerprint,
        "overlay_fingerprint": overlay_fingerprint,
        "source_fingerprint_before_overlay": source_fingerprint_before_overlay,
        "policy_id": policy_id,
        "archetype_ids": list(archetype_ids),
    }


def describe_medical_overlay(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    normalized_skill_ids = _normalize_skill_ids(skill_ids)
    normalized_policy_id = _normalize_policy_id(policy_id)
    normalized_archetype_ids = _normalize_archetype_ids(archetype_ids)
    normalized_default_submission_targets = tuple(
        item for item in (default_submission_targets or ()) if isinstance(item, dict)
    )
    scope, resolved_quest_root, targets = _resolve_targets(quest_root=quest_root, home=home, skill_ids=normalized_skill_ids)
    described_targets = [
        _describe_target(
            target,
            policy_id=normalized_policy_id,
            archetype_ids=normalized_archetype_ids,
            default_submission_targets=normalized_default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )
        for target in targets
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "overlay_name": OVERLAY_NAME,
        "scope": scope,
        "quest_root": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "skill_ids": list(normalized_skill_ids),
        "policy_id": normalized_policy_id,
        "archetype_ids": list(normalized_archetype_ids),
        "default_submission_targets": list(normalized_default_submission_targets),
        "default_publication_profile": default_publication_profile,
        "default_citation_style": default_citation_style,
        "targets": described_targets,
        "all_targets_ready": all(item["status"] == "overlay_applied" for item in described_targets),
    }


def _ensure_target_ready(target: OverlayTarget) -> str:
    if not target.target_root.exists() or not target.skill_path.exists():
        raise FileNotFoundError(f"DeepScientist skill target missing: {target.target_root}")
    return target.skill_path.read_text(encoding="utf-8")


def _seed_workspace_target_from_home(*, target: OverlayTarget, home: Path | None) -> None:
    if target.scope != "quest":
        return
    if target.skill_path.exists():
        return
    resolved_home = (Path(home) if home is not None else Path.home()).expanduser().resolve()
    source_skill_path = resolved_home / ".codex" / "skills" / f"deepscientist-{target.skill_id}" / "SKILL.md"
    if not source_skill_path.exists():
        raise FileNotFoundError(
            f"Workspace-local overlay target missing and no upstream DeepScientist skill found at {source_skill_path}"
        )
    target.target_root.mkdir(parents=True, exist_ok=True)
    target.skill_path.write_text(source_skill_path.read_text(encoding="utf-8"), encoding="utf-8")


def _write_manifest(
    *,
    target: OverlayTarget,
    quest_root: Path | None,
    overlay_fingerprint: str,
    source_fingerprint_before_overlay: str,
    policy_id: str,
    archetype_ids: tuple[str, ...],
) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overlay_name": OVERLAY_NAME,
        "skill_id": target.skill_id,
        "scope": target.scope,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "target_root": str(target.target_root),
        "skill_path": str(target.skill_path),
        "overlay_fingerprint": overlay_fingerprint,
        "source_fingerprint_before_overlay": source_fingerprint_before_overlay,
        "policy_id": policy_id,
        "archetype_ids": list(archetype_ids),
        "applied_at": _utc_now(),
    }
    _dump_json(target.manifest_path, payload)


def _install_for_target(
    *,
    target: OverlayTarget,
    quest_root: Path | None,
    home: Path | None,
    force: bool,
    policy_id: str,
    archetype_ids: tuple[str, ...],
    default_submission_targets: tuple[dict[str, object], ...],
    default_publication_profile: str | None,
    default_citation_style: str | None,
) -> dict[str, Any]:
    _seed_workspace_target_from_home(target=target, home=home)
    current_text = _ensure_target_ready(target)
    current_fingerprint = _fingerprint(current_text)
    overlay_text = load_overlay_skill_text(
        target.skill_id,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )
    overlay_fingerprint = _fingerprint(overlay_text)
    manifest = _load_json(target.manifest_path)
    previous_source_fingerprint = str(manifest.get("source_fingerprint_before_overlay") or "").strip() or None

    already_managed = (
        manifest.get("overlay_name") == OVERLAY_NAME
        and manifest.get("overlay_fingerprint") == overlay_fingerprint
        and current_fingerprint == overlay_fingerprint
    )
    if already_managed and not force:
        return {
            "skill_id": target.skill_id,
            "action": "already_installed",
            "target_root": str(target.target_root),
            "skill_path": str(target.skill_path),
            "manifest_path": str(target.manifest_path),
        }

    source_fingerprint_before_overlay = previous_source_fingerprint or current_fingerprint
    target.skill_path.write_text(overlay_text, encoding="utf-8")
    _write_manifest(
        target=target,
        quest_root=quest_root,
        overlay_fingerprint=overlay_fingerprint,
        source_fingerprint_before_overlay=source_fingerprint_before_overlay,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
    )
    return {
        "skill_id": target.skill_id,
        "action": "reapplied" if force else "installed",
        "target_root": str(target.target_root),
        "skill_path": str(target.skill_path),
        "manifest_path": str(target.manifest_path),
        "policy_id": policy_id,
        "archetype_ids": list(archetype_ids),
    }


def _install_overlay(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
    force: bool,
) -> dict[str, Any]:
    normalized_skill_ids = _normalize_skill_ids(skill_ids)
    normalized_policy_id = _normalize_policy_id(policy_id)
    normalized_archetype_ids = _normalize_archetype_ids(archetype_ids)
    normalized_default_submission_targets = tuple(
        item for item in (default_submission_targets or ()) if isinstance(item, dict)
    )
    scope, resolved_quest_root, targets = _resolve_targets(
        quest_root=quest_root,
        home=home,
        skill_ids=normalized_skill_ids,
    )
    installed_targets = [
        _install_for_target(
            target=target,
            quest_root=resolved_quest_root,
            home=home,
            force=force,
            policy_id=normalized_policy_id,
            archetype_ids=normalized_archetype_ids,
            default_submission_targets=normalized_default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )
        for target in targets
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "overlay_name": OVERLAY_NAME,
        "scope": scope,
        "quest_root": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "skill_ids": list(normalized_skill_ids),
        "policy_id": normalized_policy_id,
        "archetype_ids": list(normalized_archetype_ids),
        "default_submission_targets": list(normalized_default_submission_targets),
        "default_publication_profile": default_publication_profile,
        "default_citation_style": default_citation_style,
        "targets": installed_targets,
        "installed_count": sum(1 for item in installed_targets if item["action"] != "already_installed"),
    }


def install_medical_overlay(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    return _install_overlay(
        quest_root=quest_root,
        home=home,
        skill_ids=skill_ids,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        force=False,
    )


def reapply_medical_overlay(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    return _install_overlay(
        quest_root=quest_root,
        home=home,
        skill_ids=skill_ids,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        force=True,
    )
