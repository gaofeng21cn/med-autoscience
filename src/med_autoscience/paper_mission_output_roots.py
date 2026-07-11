from __future__ import annotations

from pathlib import Path

YANG_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang")
PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
)
PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_candidate_package"
)
PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_consumption_ledger"
)
PAPER_MISSION_RECEIPT_OWNER_CONSUMPTION_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_receipt_owner_consumption"
)
PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_typed_blocker_resolution"
)


def _assert_safe_candidate_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=None,
    )


def _assert_safe_one_shot_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH,
    )


def _assert_safe_candidate_package_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    )


def _assert_safe_consumption_ledger_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH,
    )


def _assert_safe_receipt_owner_consumption_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_RECEIPT_OWNER_CONSUMPTION_RELPATH,
    )


def _assert_safe_typed_blocker_resolution_output_root(path: Path) -> None:
    _assert_safe_non_authority_output_root(
        path,
        allowed_yang_relpath=PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH,
    )


def _assert_safe_non_authority_output_root(
    path: Path,
    *,
    allowed_yang_relpath: Path | None,
) -> None:
    normalized_path = path.expanduser().resolve()
    normalized = normalized_path.as_posix()
    forbidden_parts = (
        "/studies/",
        "/runtime/",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "owner_receipt",
        "typed_blocker",
        "human_gate",
        "current_package",
        "runtime/queue",
        "provider_attempt",
    )
    if (
        _is_under_yang_workspace(normalized_path)
        and allowed_yang_relpath is not None
        and not _is_yang_ops_root(normalized_path, allowed_yang_relpath)
    ):
        raise ValueError(f"forbidden paper mission output root: {path}")
    if (
        _is_under_yang_workspace(normalized_path)
        and allowed_yang_relpath is None
        and not _is_yang_ops_non_authority_candidate_root(normalized_path)
    ):
        raise ValueError(f"forbidden paper mission output root: {path}")
    for forbidden in forbidden_parts:
        if (
            forbidden == "typed_blocker"
            and allowed_yang_relpath == PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH
        ):
            continue
        if forbidden in normalized:
            raise ValueError(f"forbidden paper mission output root: {path}")


def _is_yang_ops_candidate_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH)


def _is_yang_ops_candidate_package_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH)


def _is_yang_ops_non_authority_candidate_root(path: str | Path | None) -> bool:
    return (
        _is_yang_ops_candidate_root(path)
        or _is_yang_ops_candidate_package_root(path)
        or _is_yang_ops_consumption_ledger_root(path)
        or _is_yang_ops_receipt_owner_consumption_root(path)
        or _is_yang_ops_typed_blocker_resolution_root(path)
    )


def _is_yang_ops_consumption_ledger_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH)


def _is_yang_ops_receipt_owner_consumption_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_RECEIPT_OWNER_CONSUMPTION_RELPATH)


def _is_yang_ops_typed_blocker_resolution_root(path: str | Path | None) -> bool:
    return _is_yang_ops_root(path, PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH)


def _is_yang_ops_root(path: str | Path | None, relpath: Path) -> bool:
    if path is None:
        return False
    normalized = Path(path).expanduser().resolve()
    try:
        relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    except ValueError:
        return False
    parts = relative.parts
    if len(parts) < len(relpath.parts) + 1:
        return False
    return Path(*parts[1 : 1 + len(relpath.parts)]) == relpath


def _is_under_yang_workspace(path: Path) -> bool:
    try:
        path.relative_to(YANG_WORKSPACE_ROOT)
    except ValueError:
        return False
    return True
