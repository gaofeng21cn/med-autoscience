from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "ai_first_external_lane_registry"
PROTECTION_SURFACE = "ai_first_external_lane_cleanup_protection"
SAFETY_SURFACE = "ai_first_closeout_cleanup_safety_check"
AUTHORITY = "governance_cleanup_protection_only"
DEFAULT_PROTECTED_PATTERNS = (
    "paper-orchestra-*",
    "mas-gate-*",
    "mas-progress-*",
    "mas-runtime-*",
)
LOW_LEVEL_FIELD_HINTS = (
    "raw",
    "log",
    "prompt",
    "token",
    "secret",
)


def _text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _bool(value: object, default: bool = True) -> bool:
    return value if isinstance(value, bool) else default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _realpath_text(value: object) -> str:
    text = _text(value)
    if not text:
        return ""
    return str(Path(text).expanduser().resolve(strict=False))


def _lane_name_candidates(*, worktree_path: object = None, branch: object = None) -> list[str]:
    candidates: list[str] = []
    worktree = _text(worktree_path)
    if worktree:
        candidates.append(Path(worktree).name)
    branch_text = _text(branch)
    if branch_text:
        candidates.append(branch_text)
        candidates.append(branch_text.split("/")[-1])
    return [item for item in candidates if item]


def _matches_default_pattern(*, worktree_path: object = None, branch: object = None) -> bool:
    return any(
        fnmatchcase(candidate, pattern)
        for candidate in _lane_name_candidates(worktree_path=worktree_path, branch=branch)
        for pattern in DEFAULT_PROTECTED_PATTERNS
    )


def _is_low_level_key(key: object) -> bool:
    normalized = str(key).lower()
    return any(hint in normalized for hint in LOW_LEVEL_FIELD_HINTS)


def _safe_refs(value: object) -> tuple[dict[str, str], list[str]]:
    refs: dict[str, str] = {}
    redacted: list[str] = []
    for key, item in _mapping(value).items():
        key_text = _text(key)
        if not key_text:
            continue
        if _is_low_level_key(key_text):
            redacted.append(f"refs.{key_text}")
            continue
        item_text = _text(item)
        if item_text:
            refs[key_text] = item_text
    return refs, redacted


def _authority_contract() -> dict[str, Any]:
    return {
        "authority": AUTHORITY,
        "purpose": "repo_level_external_lane_governance_and_cleanup_protection",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
        "can_create_study_truth": False,
        "can_override_publication_eval": False,
        "payload_exposes_raw_logs_prompts_or_tokens": False,
    }


def _public_lane(entry: Mapping[str, Any]) -> dict[str, Any]:
    refs, ref_redactions = _safe_refs(entry.get("refs"))
    redacted_fields = sorted(
        {
            str(key)
            for key in entry
            if _is_low_level_key(key) and str(key) != "refs"
        }
        | set(ref_redactions)
    )
    worktree_path = _realpath_text(entry.get("worktree_path"))
    branch = _text(entry.get("branch"))
    protected = _matches_default_pattern(worktree_path=worktree_path, branch=branch)
    if not protected:
        protected = _bool(entry.get("active"), default=True)
    return {
        "session_id": _text(entry.get("session_id"), "unknown"),
        "worktree_path": worktree_path,
        "branch": branch,
        "study_id": _text(entry.get("study_id"), "unknown"),
        "study_line": _text(entry.get("study_line"), "unknown"),
        "active": _bool(entry.get("active"), default=True),
        "protected": protected,
        "protection_reason": "matches_default_external_lane_pattern"
        if _matches_default_pattern(worktree_path=worktree_path, branch=branch)
        else "registered_external_active_lane",
        "refs": refs,
        "redacted_fields": redacted_fields,
    }


def build_external_lane_registry(*, entries: list[Mapping[str, Any]]) -> dict[str, Any]:
    lanes = [_public_lane(entry) for entry in entries]
    protected_lanes = [item for item in lanes if item["protected"]]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "default_protected_patterns": list(DEFAULT_PROTECTED_PATTERNS),
        "lanes": lanes,
        "counts": {
            "registered_lane_count": len(lanes),
            "active_lane_count": sum(1 for item in lanes if item["active"]),
            "protected_lane_count": len(protected_lanes),
        },
        "authority_contract": _authority_contract(),
    }


def _registry_lanes(registry: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(registry, Mapping):
        return []
    lanes = registry.get("lanes")
    if not isinstance(lanes, list):
        return []
    return [item for item in lanes if isinstance(item, Mapping)]


def _match_registered_lane(
    *,
    worktree_path: str,
    branch: str,
    registry: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    for lane in _registry_lanes(registry):
        if lane.get("active") is not True:
            continue
        if worktree_path and _text(lane.get("worktree_path")) == worktree_path:
            return lane
        if branch and _text(lane.get("branch")) == branch:
            return lane
    return None


def assess_external_lane_cleanup_protection(
    *,
    worktree_path: str | Path,
    branch: str,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_worktree = _realpath_text(worktree_path)
    branch_text = _text(branch)
    matched_lane = _match_registered_lane(
        worktree_path=resolved_worktree,
        branch=branch_text,
        registry=registry,
    )
    if matched_lane is not None:
        protected = True
        reason = "registered_external_active_lane"
    elif _matches_default_pattern(worktree_path=resolved_worktree, branch=branch_text):
        protected = True
        reason = "matches_default_external_lane_pattern"
    else:
        protected = False
        reason = "not_registered_or_default_protected"
    return {
        "surface": PROTECTION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "worktree_path": resolved_worktree,
        "branch": branch_text,
        "protected": protected,
        "reason": reason,
        "matched_lane": dict(matched_lane) if matched_lane is not None else None,
        "default_protected_patterns": list(DEFAULT_PROTECTED_PATTERNS),
        "authority_contract": _authority_contract(),
    }


def build_closeout_cleanup_safety_check(
    *,
    worktree_path: str | Path,
    branch: str,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    protection = assess_external_lane_cleanup_protection(
        worktree_path=worktree_path,
        branch=branch,
        registry=registry,
    )
    protected = protection["protected"] is True
    return {
        "surface": SAFETY_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "worktree_path": protection["worktree_path"],
        "branch": protection["branch"],
        "allowed_to_cleanup": not protected,
        "must_preserve": protected,
        "decision_reason": protection["reason"],
        "external_lane_protection": protection,
        "authority_contract": _authority_contract(),
    }
