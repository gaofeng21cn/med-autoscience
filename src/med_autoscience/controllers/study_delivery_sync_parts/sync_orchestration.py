from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_plane_route_gate import attach_control_plane_route_gate
from med_autoscience.controllers.control_plane_write_route import (
    blocked_control_plane_write_payload,
    resolve_control_plane_write_route_context,
)
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)

from .delivery_context import SYNC_STAGES, _resolve_delivery_context
from .delivery_stage_sync import (
    sync_draft_handoff_delivery,
    sync_general_delivery,
    sync_journal_specific_delivery,
    sync_promoted_journal_delivery,
)
def sync_study_delivery(
    *,
    paper_root: Path,
    stage: str,
    publication_profile: str = "general_medical_journal",
    promote_to_final: bool = False,
    control_plane_route_context: Mapping[str, Any] | None = None,
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
    resolved_route_context, control_plane_route_gate = resolve_control_plane_write_route_context(
        action="delivery_sync",
        context=control_plane_route_context or route_context,
        default_paths=[study_root / "manuscript" / "current_package"],
    )
    if not bool(control_plane_route_gate.get("authorized")):
        return blocked_control_plane_write_payload(
            gate=control_plane_route_gate,
            stage=normalized_stage,
            paper_root=str(paper_root),
            study_root=str(study_root),
        )

    if normalized_stage == "draft_handoff":
        if normalized_publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
            raise ValueError("draft_handoff only supports the general_medical_journal profile")
        result = sync_draft_handoff_delivery(
            paper_root=paper_root, quest_id=quest_id, study_id=study_id, study_root=study_root
        )
        return attach_control_plane_route_gate(result, control_plane_route_gate)

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        result = sync_general_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
        )
        return attach_control_plane_route_gate(result, control_plane_route_gate)

    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {normalized_publication_profile}")

    sync_journal_delivery = sync_promoted_journal_delivery if promote_to_final else sync_journal_specific_delivery
    result = sync_journal_delivery(
        paper_root=paper_root,
        worktree_root=worktree_root,
        quest_id=quest_id,
        study_id=study_id,
        study_root=study_root,
        normalized_stage=normalized_stage,
        publication_profile=normalized_publication_profile,
    )
    return attach_control_plane_route_gate(result, control_plane_route_gate)


from .sync_cli import main, parse_args  # noqa: E402
