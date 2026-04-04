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
from med_autoscience.policies.automation_ready import render_automation_ready_block
from med_autoscience.policies.controller_first import render_controller_first_block
from med_autoscience.policies.study_archetypes import (
    DEFAULT_STUDY_ARCHETYPE_IDS,
    get_archetype,
    render_archetype_block,
)
from med_autoscience.reference_papers import render_reference_paper_overlay_block
from med_autoscience.submission_targets import render_submission_target_overlay_block


SCHEMA_VERSION = 1
OVERLAY_NAME = "med_autoscience_med_deepscientist_overlay"
MANIFEST_NAME = ".med_autoscience_overlay.json"
ROUTE_BIAS_TOKEN = "{{MED_AUTOSCIENCE_ROUTE_BIAS}}"
STUDY_ARCHETYPES_TOKEN = "{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}"
SUBMISSION_TARGETS_TOKEN = "{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}"
REFERENCE_PAPERS_TOKEN = "{{MED_AUTOSCIENCE_REFERENCE_PAPERS}}"
CONTROLLER_FIRST_TOKEN = "{{MED_AUTOSCIENCE_CONTROLLER_FIRST}}"
AUTOMATION_READY_TOKEN = "{{MED_AUTOSCIENCE_AUTOMATION_READY}}"
MEDICAL_RUNTIME_CONTRACT_TOKEN = "{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}"
FORBIDDEN_SYSTEM_PROMPT_SNIPPETS = (
    "Publication-grade figure refinement is recommended with AutoFigure-Edit",
)
FRONTLOAD_STAGE_IDS = frozenset(
    {"intake-audit", "scout", "baseline", "idea", "decision", "experiment", "analysis-campaign"}
)
FULL_TEMPLATE_MAP = {
    "scout": "med-deepscientist-scout.SKILL.md",
    "idea": "med-deepscientist-idea.SKILL.md",
    "decision": "med-deepscientist-decision.SKILL.md",
    "figure-polish": "med-deepscientist-figure-polish.SKILL.md",
    "write": "med-deepscientist-write.SKILL.md",
    "finalize": "med-deepscientist-finalize.SKILL.md",
    "journal-resolution": "med-deepscientist-journal-resolution.SKILL.md",
}
APPEND_BLOCK_TEMPLATE_MAP = {
    "intake-audit": "med-deepscientist-intake-audit.block.md",
    "baseline": "med-deepscientist-baseline.block.md",
    "experiment": "med-deepscientist-experiment.block.md",
    "analysis-campaign": "med-deepscientist-analysis-campaign.block.md",
    "review": "med-deepscientist-review.block.md",
    "rebuttal": "med-deepscientist-rebuttal.block.md",
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


def _append_marker(skill_id: str) -> str:
    return f"<!-- MED_AUTOSCIENCE_APPEND_BLOCK:{skill_id} -->"


def render_medical_runtime_contract_block() -> str:
    return (
        "## Medical runtime contract\n\n"
        "- Read `paper/medical_analysis_contract.json` before deciding follow-up analyses, manuscript rewrites, or review responses.\n"
        "- Treat `paper/cohort_flow.json`, `paper/baseline_characteristics_schema.json`, and `paper/reporting_guideline_checklist.json` as required truth sources when present.\n"
        "- If `paper/display_registry.json` declares official shells such as `cohort_flow_figure` or `table1_baseline_characteristics`, materialize them through `medautosci materialize-display-surface --paper-root paper` before polishing captions or exporting submission assets.\n"
        "- If the runtime contract calls for calibration, transportability, cohort flow, or baseline characteristics evidence, do not treat ablation-heavy follow-up as sufficient.\n"
        "- Keep TRIPOD / STROBE / CONSORT family requirements explicit in durable manuscript-facing artifacts.\n"
    )


def _load_template_text(template_name: str) -> str:
    template_path = resources.files("med_autoscience.overlay.templates").joinpath(template_name)
    return template_path.read_text(encoding="utf-8")


def _render_overlay_text_from_template(
    template: str,
    *,
    skill_id: str,
    policy_id: str | None,
    archetype_ids: tuple[str, ...] | list[str] | None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None,
    default_publication_profile: str | None,
    default_citation_style: str | None,
) -> str:
    rendered = template
    if skill_id in {"experiment", "analysis-campaign", "write", "review"}:
        if MEDICAL_RUNTIME_CONTRACT_TOKEN not in rendered:
            raise ValueError(f"Overlay template for {skill_id} is missing medical runtime contract token")
    if MEDICAL_RUNTIME_CONTRACT_TOKEN in rendered:
        rendered = rendered.replace(
            MEDICAL_RUNTIME_CONTRACT_TOKEN,
            render_medical_runtime_contract_block().rstrip(),
        )
    if skill_id in {"scout", "idea", "write"}:
        if REFERENCE_PAPERS_TOKEN not in rendered:
            raise ValueError(f"Overlay template for {skill_id} is missing reference paper token")
        rendered = rendered.replace(
            REFERENCE_PAPERS_TOKEN,
            render_reference_paper_overlay_block(stage_id=skill_id).rstrip(),
        )
    if skill_id in {"write", "finalize", "journal-resolution"}:
        if SUBMISSION_TARGETS_TOKEN not in rendered:
            raise ValueError(f"Overlay template for {skill_id} is missing submission target token")
        rendered = rendered.replace(
            SUBMISSION_TARGETS_TOKEN,
            render_submission_target_overlay_block(
                default_submission_targets=default_submission_targets,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            ).rstrip(),
        )
    if CONTROLLER_FIRST_TOKEN in rendered:
        rendered = rendered.replace(CONTROLLER_FIRST_TOKEN, render_controller_first_block().rstrip())
    if AUTOMATION_READY_TOKEN in rendered:
        rendered = rendered.replace(AUTOMATION_READY_TOKEN, render_automation_ready_block().rstrip())
    if skill_id not in FRONTLOAD_STAGE_IDS:
        return rendered

    normalized_policy_id = _normalize_policy_id(policy_id)
    normalized_archetype_ids = _normalize_archetype_ids(archetype_ids)
    if ROUTE_BIAS_TOKEN not in rendered or STUDY_ARCHETYPES_TOKEN not in rendered:
        raise ValueError(f"Overlay template for {skill_id} is missing dynamic policy tokens")
    rendered = rendered.replace(
        ROUTE_BIAS_TOKEN,
        render_policy_block(stage_id=skill_id, policy_id=normalized_policy_id).rstrip(),
    )
    rendered = rendered.replace(
        STUDY_ARCHETYPES_TOKEN,
        render_archetype_block(archetype_ids=normalized_archetype_ids).rstrip(),
    )
    return rendered


def _normalize_skill_ids(skill_ids: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    normalized = DEFAULT_MEDICAL_OVERLAY_SKILL_IDS if skill_ids is None else tuple(skill_ids)
    if ("write" in normalized or "finalize" in normalized) and "journal-resolution" not in normalized:
        normalized = normalized + ("journal-resolution",)
    supported_skill_ids = set(FULL_TEMPLATE_MAP) | set(APPEND_BLOCK_TEMPLATE_MAP)
    invalid = [skill_id for skill_id in normalized if skill_id not in supported_skill_ids]
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
            target_root=skills_root / f"med-deepscientist-{skill_id}",
            skill_path=skills_root / f"med-deepscientist-{skill_id}" / "SKILL.md",
            manifest_path=skills_root / f"med-deepscientist-{skill_id}" / MANIFEST_NAME,
        )
        for skill_id in normalized_skill_ids
    ]
    return scope, resolved_quest_root, targets


def _resolve_authoritative_target_root(*, authoritative_root: Path | None, skill_id: str) -> Path | None:
    if authoritative_root is None:
        return None
    return Path(authoritative_root).expanduser().resolve() / ".codex" / "skills" / f"med-deepscientist-{skill_id}"


def _copy_authoritative_target_seed(*, target: OverlayTarget, authoritative_root: Path | None) -> None:
    source_target_root = _resolve_authoritative_target_root(authoritative_root=authoritative_root, skill_id=target.skill_id)
    if source_target_root is None:
        return
    if source_target_root == target.target_root:
        return
    source_skill_path = source_target_root / "SKILL.md"
    if not source_skill_path.exists():
        return
    target.target_root.mkdir(parents=True, exist_ok=True)
    target.skill_path.write_text(source_skill_path.read_text(encoding="utf-8"), encoding="utf-8")
    source_manifest_path = source_target_root / MANIFEST_NAME
    if source_manifest_path.exists():
        target.manifest_path.write_text(source_manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    elif target.manifest_path.exists():
        target.manifest_path.unlink()


def load_overlay_skill_text(
    skill_id: str,
    *,
    base_text: str | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> str:
    if skill_id in FULL_TEMPLATE_MAP:
        return _render_overlay_text_from_template(
            _load_template_text(FULL_TEMPLATE_MAP[skill_id]),
            skill_id=skill_id,
            policy_id=policy_id,
            archetype_ids=archetype_ids,
            default_submission_targets=default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )

    if skill_id not in APPEND_BLOCK_TEMPLATE_MAP:
        supported = ", ".join(sorted(set(FULL_TEMPLATE_MAP) | set(APPEND_BLOCK_TEMPLATE_MAP)))
        raise ValueError(f"Unsupported medical overlay skill id: {skill_id}. Supported: {supported}")

    if base_text is None:
        raise ValueError(f"Overlay skill `{skill_id}` requires base_text")

    marker = _append_marker(skill_id)
    if marker in base_text:
        return base_text

    block = _render_overlay_text_from_template(
        _load_template_text(APPEND_BLOCK_TEMPLATE_MAP[skill_id]),
        skill_id=skill_id,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )
    return base_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def _describe_target(
    target: OverlayTarget,
    *,
    quest_root: Path | None,
    policy_id: str,
    archetype_ids: tuple[str, ...],
    default_submission_targets: tuple[dict[str, object], ...],
    default_publication_profile: str | None,
    default_citation_style: str | None,
) -> dict[str, Any]:
    manifest = _load_json(target.manifest_path)
    current_text = target.skill_path.read_text(encoding="utf-8") if target.skill_path.exists() else None
    source_text_before_overlay = manifest.get("source_text_before_overlay_text")
    if not isinstance(source_text_before_overlay, str):
        source_text_before_overlay = current_text
    overlay_text = None
    overlay_fingerprint = None
    can_render_overlay = target.skill_id not in APPEND_BLOCK_TEMPLATE_MAP or source_text_before_overlay is not None
    if can_render_overlay:
        overlay_text = load_overlay_skill_text(
            target.skill_id,
            base_text=source_text_before_overlay if target.skill_id in APPEND_BLOCK_TEMPLATE_MAP else None,
            policy_id=policy_id,
            archetype_ids=archetype_ids,
            default_submission_targets=default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )
        overlay_fingerprint = _fingerprint(overlay_text)
    current_fingerprint = None
    source_fingerprint_before_overlay = manifest.get("source_fingerprint_before_overlay")
    manifest_present = bool(manifest)
    manifest_target_root = manifest.get("target_root")
    manifest_skill_path = manifest.get("skill_path")
    manifest_quest_root = manifest.get("quest_root")
    resolved_quest_root = str(quest_root) if quest_root is not None else None
    manifest_path_drift = manifest_present and (
        isinstance(manifest_target_root, str) and manifest_target_root != str(target.target_root)
        or isinstance(manifest_skill_path, str) and manifest_skill_path != str(target.skill_path)
        or (resolved_quest_root is not None and isinstance(manifest_quest_root, str) and manifest_quest_root != resolved_quest_root)
    )

    if target.skill_path.exists():
        current_fingerprint = _fingerprint(current_text or "")
        if manifest_path_drift:
            status = "drifted"
            needs_reapply = True
        elif manifest_present:
            if overlay_fingerprint and current_fingerprint == overlay_fingerprint:
                status = "overlay_applied"
                needs_reapply = False
            elif source_fingerprint_before_overlay and current_fingerprint == source_fingerprint_before_overlay:
                status = "overwritten_by_upstream"
                needs_reapply = True
            else:
                status = "drifted"
                needs_reapply = True
        else:
            if overlay_fingerprint and current_fingerprint == overlay_fingerprint:
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
    med_deepscientist_repo_root: Path | None = None,
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
            quest_root=resolved_quest_root,
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
    if target.skill_path.exists():
        return target.skill_path.read_text(encoding="utf-8")
    if target.skill_id in FULL_TEMPLATE_MAP:
        target.target_root.mkdir(parents=True, exist_ok=True)
        return ""
    raise FileNotFoundError(f"MedDeepScientist skill target missing: {target.target_root}")


def _resolve_runtime_repo_skill_path(*, med_deepscientist_repo_root: Path | None, skill_id: str) -> Path | None:
    if med_deepscientist_repo_root is None:
        return None
    return Path(med_deepscientist_repo_root).expanduser().resolve() / "src" / "skills" / skill_id / "SKILL.md"


def _seed_workspace_target_from_runtime_repo(
    *,
    target: OverlayTarget,
    med_deepscientist_repo_root: Path | None,
) -> None:
    if target.scope != "quest" or target.skill_path.exists():
        return
    if target.skill_id in FULL_TEMPLATE_MAP:
        return
    source_skill_path = _resolve_runtime_repo_skill_path(
        med_deepscientist_repo_root=med_deepscientist_repo_root,
        skill_id=target.skill_id,
    )
    if source_skill_path is None or not source_skill_path.exists():
        expected = (
            str(source_skill_path)
            if source_skill_path is not None
            else "<unset med_deepscientist_repo_root>/src/skills/<skill-id>/SKILL.md"
        )
        raise FileNotFoundError(
            "Workspace-local overlay target missing and no authoritative med-deepscientist skill seed "
            f"found for `{target.skill_id}` at {expected}"
        )
    target.target_root.mkdir(parents=True, exist_ok=True)
    target.skill_path.write_text(source_skill_path.read_text(encoding="utf-8"), encoding="utf-8")


def _write_manifest(
    *,
    target: OverlayTarget,
    quest_root: Path | None,
    overlay_fingerprint: str,
    source_fingerprint_before_overlay: str,
    source_text_before_overlay: str,
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
        "source_text_before_overlay_text": source_text_before_overlay,
        "policy_id": policy_id,
        "archetype_ids": list(archetype_ids),
        "applied_at": _utc_now(),
    }
    _dump_json(target.manifest_path, payload)


def _install_for_target(
    *,
    target: OverlayTarget,
    quest_root: Path | None,
    authoritative_root: Path | None,
    med_deepscientist_repo_root: Path | None,
    force: bool,
    policy_id: str,
    archetype_ids: tuple[str, ...],
    default_submission_targets: tuple[dict[str, object], ...],
    default_publication_profile: str | None,
    default_citation_style: str | None,
) -> dict[str, Any]:
    _copy_authoritative_target_seed(target=target, authoritative_root=authoritative_root)
    _seed_workspace_target_from_runtime_repo(
        target=target,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
    )
    current_text = _ensure_target_ready(target)
    current_fingerprint = _fingerprint(current_text)
    manifest = _load_json(target.manifest_path)
    previous_source_text = manifest.get("source_text_before_overlay_text")
    if not isinstance(previous_source_text, str) or not previous_source_text:
        previous_source_text = None
    source_text_before_overlay = previous_source_text or current_text
    overlay_text = load_overlay_skill_text(
        target.skill_id,
        base_text=source_text_before_overlay if target.skill_id in APPEND_BLOCK_TEMPLATE_MAP else None,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )
    overlay_fingerprint = _fingerprint(overlay_text)
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
        source_text_before_overlay=source_text_before_overlay,
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
    authoritative_root: Path | None = None,
    med_deepscientist_repo_root: Path | None = None,
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
            authoritative_root=authoritative_root,
            med_deepscientist_repo_root=med_deepscientist_repo_root,
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
    authoritative_root: Path | None = None,
    med_deepscientist_repo_root: Path | None = None,
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
        authoritative_root=authoritative_root,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
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
    authoritative_root: Path | None = None,
    med_deepscientist_repo_root: Path | None = None,
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
        authoritative_root=authoritative_root,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
        skill_ids=skill_ids,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        force=True,
    )


def ensure_medical_overlay(
    *,
    quest_root: Path | None = None,
    home: Path | None = None,
    authoritative_root: Path | None = None,
    med_deepscientist_repo_root: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    mode: str = "ensure_ready",
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    pre_status = describe_medical_overlay(
        quest_root=quest_root,
        home=home,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
        skill_ids=skill_ids,
        policy_id=policy_id,
        archetype_ids=archetype_ids,
        default_submission_targets=default_submission_targets,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )
    action_result: dict[str, Any] | None = None
    selected_action = "noop"

    if mode == "status_only":
        selected_action = "status_only"
        post_status = pre_status
    else:
        if mode == "install":
            selected_action = "install"
        elif mode == "reapply":
            selected_action = "reapply"
        elif mode == "ensure_ready":
            if pre_status["all_targets_ready"]:
                selected_action = "noop"
            elif any(item["status"] in {"drifted", "overwritten_by_upstream"} for item in pre_status["targets"]):
                selected_action = "reapply"
            else:
                selected_action = "install"
        else:
            raise ValueError(f"Unsupported medical overlay bootstrap mode: {mode}")

        if selected_action == "install":
            action_result = install_medical_overlay(
                quest_root=quest_root,
                home=home,
                authoritative_root=authoritative_root,
                med_deepscientist_repo_root=med_deepscientist_repo_root,
                skill_ids=skill_ids,
                policy_id=policy_id,
                archetype_ids=archetype_ids,
                default_submission_targets=default_submission_targets,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            )
        elif selected_action == "reapply":
            action_result = reapply_medical_overlay(
                quest_root=quest_root,
                home=home,
                authoritative_root=authoritative_root,
                med_deepscientist_repo_root=med_deepscientist_repo_root,
                skill_ids=skill_ids,
                policy_id=policy_id,
                archetype_ids=archetype_ids,
                default_submission_targets=default_submission_targets,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            )
        post_status = (
            describe_medical_overlay(
                quest_root=quest_root,
                home=home,
                skill_ids=skill_ids,
                policy_id=policy_id,
                archetype_ids=archetype_ids,
                default_submission_targets=default_submission_targets,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            )
            if selected_action != "noop"
            else pre_status
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "overlay_name": OVERLAY_NAME,
        "mode": mode,
        "selected_action": selected_action,
        "pre_status": pre_status,
        "post_status": post_status,
        "action_result": action_result,
    }


def _runtime_materialization_roots(*, quest_root: Path) -> list[Path]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    roots = [resolved_quest_root]
    worktrees_root = resolved_quest_root / ".ds" / "worktrees"
    if worktrees_root.exists():
        roots.extend(sorted(path.resolve() for path in worktrees_root.iterdir() if path.is_dir()))
    return roots


def _runtime_system_prompt_path(*, runtime_root: Path) -> Path:
    return runtime_root / ".codex" / "prompts" / "system.md"


def _sanitize_runtime_system_prompt(*, runtime_root: Path) -> dict[str, Any]:
    prompt_path = _runtime_system_prompt_path(runtime_root=runtime_root)
    if not prompt_path.exists():
        return {
            "path": str(prompt_path),
            "exists": False,
            "action": "missing",
            "removed_line_count": 0,
        }

    original_text = prompt_path.read_text(encoding="utf-8")
    original_lines = original_text.splitlines()
    kept_lines = [
        line
        for line in original_lines
        if not any(snippet in line for snippet in FORBIDDEN_SYSTEM_PROMPT_SNIPPETS)
    ]
    removed_line_count = len(original_lines) - len(kept_lines)
    if removed_line_count:
        sanitized_text = "\n".join(kept_lines)
        if original_text.endswith("\n"):
            sanitized_text += "\n"
        prompt_path.write_text(sanitized_text, encoding="utf-8")

    return {
        "path": str(prompt_path),
        "exists": True,
        "action": "sanitized" if removed_line_count else "unchanged",
        "removed_line_count": removed_line_count,
    }


def _audit_runtime_system_prompt(*, runtime_root: Path) -> dict[str, Any]:
    prompt_path = _runtime_system_prompt_path(runtime_root=runtime_root)
    if not prompt_path.exists():
        return {
            "path": str(prompt_path),
            "exists": False,
            "ready": True,
            "violations": [],
        }

    prompt_text = prompt_path.read_text(encoding="utf-8")
    violations = [snippet for snippet in FORBIDDEN_SYSTEM_PROMPT_SNIPPETS if snippet in prompt_text]
    return {
        "path": str(prompt_path),
        "exists": True,
        "ready": not violations,
        "violations": violations,
    }


def materialize_runtime_medical_overlay(
    *,
    quest_root: Path,
    authoritative_root: Path,
    home: Path | None = None,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_authoritative_root = Path(authoritative_root).expanduser().resolve()
    results = []
    for root in _runtime_materialization_roots(quest_root=resolved_quest_root):
        overlay_result = reapply_medical_overlay(
            quest_root=root,
            home=home,
            authoritative_root=resolved_authoritative_root,
            skill_ids=skill_ids,
            policy_id=policy_id,
            archetype_ids=archetype_ids,
            default_submission_targets=default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )
        system_prompt = _sanitize_runtime_system_prompt(runtime_root=root)
        results.append(
            {
                "runtime_root": str(root),
                "surface": "quest" if root == resolved_quest_root else "worktree",
                "overlay": overlay_result,
                "system_prompt": system_prompt,
            }
        )
    return {
        "quest_root": str(resolved_quest_root),
        "authoritative_root": str(resolved_authoritative_root),
        "surfaces": results,
        "materialized_surface_count": len(results),
    }


def audit_runtime_medical_overlay(
    *,
    quest_root: Path,
    skill_ids: tuple[str, ...] | list[str] | None = None,
    policy_id: str | None = None,
    archetype_ids: tuple[str, ...] | list[str] | None = None,
    default_submission_targets: tuple[dict[str, object], ...] | list[dict[str, object]] | None = None,
    default_publication_profile: str | None = None,
    default_citation_style: str | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    surfaces = []
    for root in _runtime_materialization_roots(quest_root=resolved_quest_root):
        status = describe_medical_overlay(
            quest_root=root,
            skill_ids=skill_ids,
            policy_id=policy_id,
            archetype_ids=archetype_ids,
            default_submission_targets=default_submission_targets,
            default_publication_profile=default_publication_profile,
            default_citation_style=default_citation_style,
        )
        system_prompt_audit = _audit_runtime_system_prompt(runtime_root=root)
        all_surface_ready = bool(status["all_targets_ready"]) and bool(system_prompt_audit["ready"])
        surfaces.append(
            {
                "runtime_root": str(root),
                "surface": "quest" if root == resolved_quest_root else "worktree",
                "all_targets_ready": bool(status["all_targets_ready"]),
                "system_prompt_ready": bool(system_prompt_audit["ready"]),
                "all_surface_ready": all_surface_ready,
                "status": status,
                "system_prompt": system_prompt_audit,
            }
        )
    return {
        "quest_root": str(resolved_quest_root),
        "surface_count": len(surfaces),
        "all_roots_ready": all(item["all_surface_ready"] for item in surfaces),
        "surfaces": surfaces,
    }
