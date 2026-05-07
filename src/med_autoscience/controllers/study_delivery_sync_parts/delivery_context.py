from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref


SYNC_STAGES = ("draft_handoff", "submission_minimal", "finalize")
FORMAL_PAPER_DELIVERY_RELATIVE_PATHS = (
    Path(medical_surface_policy.EVIDENCE_LEDGER_BASENAME),
)


def _normalized_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(Path(path).expanduser().resolve())


def _build_ledger_contract_linkage(
    *,
    ledger_name: str,
    ledger_path: Path | None,
    study_context_status: str,
    charter_id: str | None,
    contract_role: str | None,
) -> dict[str, Any]:
    resolved_ledger_path = Path(ledger_path).expanduser().resolve() if ledger_path is not None else None
    ledger_present = bool(resolved_ledger_path and resolved_ledger_path.exists())
    normalized_role = str(contract_role or "").strip() or None
    if study_context_status == "linked_context":
        if normalized_role and ledger_present:
            status = "linked"
        elif normalized_role:
            status = "ledger_missing"
        else:
            status = "contract_role_missing"
    else:
        status = study_context_status
    return {
        "ledger_name": ledger_name,
        "ledger_path": _normalized_path(resolved_ledger_path),
        "ledger_present": ledger_present,
        "charter_id": charter_id,
        "contract_role_present": bool(normalized_role),
        "contract_role": normalized_role,
        "contract_role_json_pointer": f"/paper_quality_contract/downstream_contract_roles/{ledger_name}",
        "status": status,
    }


def build_charter_contract_linkage(
    *,
    study_root: Path | None,
    evidence_ledger_path: Path | None,
    review_ledger_path: Path | None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    if resolved_study_root is None:
        study_context_status = "study_root_unresolved"
        charter_path = None
        charter_id = None
        paper_quality_contract_present = False
        downstream_contract_roles: dict[str, str] = {}
    else:
        charter_path = resolve_study_charter_ref(study_root=resolved_study_root)
        charter_id = None
        downstream_contract_roles = {}
        if not charter_path.exists():
            study_context_status = "study_charter_missing"
            paper_quality_contract_present = False
        else:
            try:
                charter_payload = read_study_charter(study_root=resolved_study_root, ref=charter_path)
            except (json.JSONDecodeError, ValueError):
                study_context_status = "study_charter_invalid"
                paper_quality_contract_present = False
            else:
                charter_id = str(charter_payload.get("charter_id") or "").strip() or None
                paper_quality_contract = charter_payload.get("paper_quality_contract")
                paper_quality_contract_present = isinstance(paper_quality_contract, dict)
                if paper_quality_contract_present:
                    raw_roles = paper_quality_contract.get("downstream_contract_roles")
                    if isinstance(raw_roles, dict):
                        downstream_contract_roles = {
                            str(key): str(value).strip()
                            for key, value in raw_roles.items()
                            if str(value).strip()
                        }
                study_context_status = "linked_context" if paper_quality_contract_present else "paper_quality_contract_missing"

    ledger_linkages = {
        "evidence_ledger": _build_ledger_contract_linkage(
            ledger_name="evidence_ledger",
            ledger_path=evidence_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("evidence_ledger"),
        ),
        "review_ledger": _build_ledger_contract_linkage(
            ledger_name="review_ledger",
            ledger_path=review_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("review_ledger"),
        ),
    }
    ledger_statuses = {payload["status"] for payload in ledger_linkages.values()}
    if study_context_status != "linked_context":
        status = study_context_status
    elif ledger_statuses == {"linked"}:
        status = "linked"
    elif "linked" in ledger_statuses:
        status = "partially_linked"
    else:
        status = "unlinked"
    return {
        "status": status,
        "study_root": _normalized_path(resolved_study_root),
        "study_charter_ref": {
            "charter_id": charter_id,
            "artifact_path": _normalized_path(charter_path),
        },
        "paper_quality_contract": {
            "present": paper_quality_contract_present,
            "artifact_path": _normalized_path(charter_path),
            "json_pointer": "/paper_quality_contract",
        },
        "ledger_linkages": ledger_linkages,
    }


def can_sync_study_delivery(*, paper_root: Path) -> bool:
    try:
        _resolve_delivery_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    return True


def _resolve_study_owned_paper_context(paper_root: Path) -> tuple[Path, Path, str] | None:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    if resolved_paper_root.name != "paper":
        return None
    study_root = resolved_paper_root.parent
    if study_root.parent.name != "studies":
        return None
    if not (study_root / "study.yaml").exists():
        return None
    return resolved_paper_root, study_root, study_root.name


def _resolve_delivery_context(paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    try:
        context = resolve_paper_root_context(resolved_paper_root)
    except (FileNotFoundError, ValueError):
        direct_context = _resolve_study_owned_paper_context(resolved_paper_root)
        if direct_context is None:
            raise
        resolved_paper_root, study_root, study_id = direct_context
        return {
            "paper_root": resolved_paper_root,
            "worktree_root": study_root,
            "quest_root": None,
            "quest_id": study_id,
            "study_id": study_id,
            "study_root": study_root,
        }
    return {
        "paper_root": context.paper_root,
        "worktree_root": context.worktree_root,
        "quest_root": context.quest_root,
        "quest_id": context.quest_id,
        "study_id": context.study_id,
        "study_root": context.study_root,
    }


def build_submission_source_root(*, paper_root: Path, publication_profile: str) -> Path:
    normalized_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return paper_root / "submission_minimal"
    return paper_root / "journal_submissions" / normalized_profile


def build_authority_source_relative_root(*, paper_root: Path, source_root: Path) -> str:
    return source_root.resolve().relative_to(paper_root.resolve().parent).as_posix()


def resolve_finalize_resume_packet_source(*, paper_root: Path, worktree_root: Path) -> Path:
    candidates = [
        paper_root / "finalize_resume_packet.md",
        worktree_root / "handoffs" / "finalize_resume_packet.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "missing delivery source: no finalize resume packet found in "
        f"{paper_root / 'finalize_resume_packet.md'} or {worktree_root / 'handoffs' / 'finalize_resume_packet.md'}"
    )
