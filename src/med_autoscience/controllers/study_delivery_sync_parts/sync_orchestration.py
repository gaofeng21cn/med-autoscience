from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.authority_route_gate import attach_authority_route_gate
from med_autoscience.controllers.authority_write_route import (
    blocked_authority_write_payload,
    resolve_authority_write_route_context,
)
from med_autoscience.controllers.authority_write_route_context import with_study_authority_route_context
from med_autoscience.controllers import paper_authority_delivery_guard
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)

from .delivery_context import SYNC_STAGES, _resolve_delivery_context
from .delivery_stage_sync import (
    _sync_current_package_mirror_delivery,
    sync_draft_handoff_delivery,
    sync_general_delivery,
    sync_journal_specific_delivery,
    sync_promoted_journal_delivery,
)


def _known_submission_authority_blockers(gate: Mapping[str, Any]) -> tuple[str, ...]:
    blockers: list[str] = []
    for reason in gate.get("blocking_reasons") or []:
        text = str(reason or "").strip()
        if text and text not in blockers:
            blockers.append(text)
    return tuple(blockers)


def _explicit_submission_authority_blocked(gate: Mapping[str, Any]) -> bool:
    return any(
        reason in {"bundle_build_allowed_false", "bundle_build_allowed_missing"}
        for reason in _known_submission_authority_blockers(gate)
    )


def _submission_authority_allowed(gate: Mapping[str, Any]) -> bool:
    return bool(gate.get("allowed")) and bool(gate.get("authorized")) and not _known_submission_authority_blockers(gate)


def _mirror_authority_gate(*, submission_authority_gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(submission_authority_gate),
        "authorized": True,
        "allowed": True,
        "blocking_reasons": [],
        "route_authorization_flag": "current_package_mirror_source_signature",
        "submission_authority_blockers": _known_submission_authority_blockers(submission_authority_gate),
        "package_authority": {
            "package_kind": "current_package",
            "can_submit": False,
            "submission_authority_required": False,
        },
    }


def sync_study_delivery(
    *,
    paper_root: Path,
    stage: str,
    publication_profile: str = "general_medical_journal",
    promote_to_final: bool = False,
    authority_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip()
    if normalized_stage not in SYNC_STAGES:
        raise ValueError(f"unsupported sync stage: {stage}")
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    context = _resolve_delivery_context(paper_root.resolve())
    paper_root, worktree_root = context["paper_root"], context["worktree_root"]
    quest_id, study_id, study_root = context["quest_id"], context["study_id"], context["study_root"]
    provided_route_context = authority_route_context or route_context
    write_route_context = with_study_authority_route_context(
        study_root=study_root,
        context=dict(provided_route_context) if provided_route_context is not None else None,
    )
    resolved_route_context, authority_route_gate = resolve_authority_write_route_context(
        action="delivery_sync",
        context=write_route_context,
        default_paths=[study_root / "manuscript" / "current_package"],
    )
    submission_authority_blocked = _explicit_submission_authority_blocked(authority_route_gate)
    requires_submission_authority = promote_to_final
    if bool(authority_route_gate.get("projection_only")) or (
        requires_submission_authority and submission_authority_blocked
    ):
        return blocked_authority_write_payload(
            gate=authority_route_gate,
            stage=normalized_stage,
            paper_root=str(paper_root),
            study_root=str(study_root),
        )
    mirror_authority_gate = _mirror_authority_gate(submission_authority_gate=authority_route_gate)
    known_submission_authority_blockers = _known_submission_authority_blockers(authority_route_gate)
    submission_authority_allowed = _submission_authority_allowed(authority_route_gate)
    clean_migration_blocker = paper_authority_delivery_guard.pending_clean_migration_blocker(
        study_root=study_root,
    )
    if clean_migration_blocker is not None:
        return {
            **clean_migration_blocker,
            "stage": normalized_stage,
            "paper_root": str(paper_root),
            "study_root": str(study_root),
            "authority_route_gate": mirror_authority_gate if not requires_submission_authority else authority_route_gate,
            "submission_authority_gate": authority_route_gate,
        }

    if normalized_stage == "draft_handoff":
        if normalized_publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
            raise ValueError("draft_handoff only supports the general_medical_journal profile")
        result = sync_draft_handoff_delivery(
            paper_root=paper_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            known_blockers=known_submission_authority_blockers,
        )
        result["submission_authority_gate"] = authority_route_gate
        return attach_authority_route_gate(result, mirror_authority_gate)

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE and not submission_authority_allowed:
        result = sync_general_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
            known_blockers=known_submission_authority_blockers,
        )
        result["submission_authority_gate"] = authority_route_gate
        return attach_authority_route_gate(result, mirror_authority_gate)

    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {normalized_publication_profile}")

    if submission_authority_blocked:
        result = _sync_current_package_mirror_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
            publication_profile=normalized_publication_profile,
            known_blockers=known_submission_authority_blockers,
        )
        result["submission_authority_gate"] = authority_route_gate
        return attach_authority_route_gate(result, mirror_authority_gate)

    sync_journal_delivery = (
        sync_promoted_journal_delivery
        if promote_to_final or submission_authority_allowed
        else sync_journal_specific_delivery
    )
    result = sync_journal_delivery(
        paper_root=paper_root,
        worktree_root=worktree_root,
        quest_id=quest_id,
        study_id=study_id,
        study_root=study_root,
        normalized_stage=normalized_stage,
        publication_profile=normalized_publication_profile,
    )
    result["submission_authority_gate"] = authority_route_gate
    return attach_authority_route_gate(result, authority_route_gate)


from .sync_cli import main, parse_args  # noqa: E402
