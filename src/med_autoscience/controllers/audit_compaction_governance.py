from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from med_autoscience.controllers.boundary_fitness import (
    BoundaryFinding,
    BoundaryFitnessReport,
    PROGRAM_BOUNDARIES,
    audit_boundary_fitness,
    build_program_boundary_map,
)


SCHEMA_VERSION = 1
SURFACE = "mas_l5_audit_compaction_governance"
L5_LANE_ID = "L5_natural_boundary_and_audit_compaction"
AUTHORITY_MODE = "maintainability_only"
READ_MODEL_ONLY_TRUTH_WRITES: tuple[str, ...] = ()
TRUTH_SURFACES_OUT_OF_SCOPE = (
    "study_truth",
    "runtime_truth",
    "publication_truth",
    "delivery_truth",
)
REQUIRED_COMPACTION_GATES = ("restore", "index", "provenance")
REQUIRED_COMPACTION_PROOF_REFS = (
    "restore_index_ref",
    "provenance_ref",
    "lifecycle_export_ref",
)
L5_BRANCHES = frozenset(
    {
        "codex/mas-l5-compaction-structure",
        "codex/mas-structure-audit-compaction",
    }
)


@dataclass(frozen=True)
class WorktreeRecord:
    path: str
    branch: str | None = None
    commit: str | None = None
    detached: bool = False


def build_audit_compaction_governance_report(
    repo_root: Path | str | None = None,
    *,
    worktrees: Sequence[Mapping[str, Any] | WorktreeRecord] | None = None,
    boundary_report: BoundaryFitnessReport | None = None,
    tracked_files: Sequence[str] | None = None,
    audit_compaction_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    records = _worktree_records(root, worktrees)
    fitness_report = boundary_report if boundary_report is not None else audit_boundary_fitness(root)
    tracked = tuple(tracked_files) if tracked_files is not None else tuple(_finding_paths(fitness_report))
    boundary_map = build_program_boundary_map(tracked_files=tracked, findings=fitness_report)
    compaction_contract = _build_compaction_contract_read_model(audit_compaction_contract)

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "lane_id": L5_LANE_ID,
        "authority_mode": AUTHORITY_MODE,
        "projection_only": True,
        "maintainability_only": True,
        "truth_writes": list(READ_MODEL_ONLY_TRUTH_WRITES),
        "truth_surfaces_out_of_scope": list(TRUTH_SURFACES_OUT_OF_SCOPE),
        "authority_boundary": (
            "L5 exposes maintainability read models only; it cannot write study, runtime, "
            "publication, delivery, controller, or artifact truth."
        ),
        "worktree_ownership_audit": _build_worktree_ownership_audit(records),
        "structure_target_list": _build_structure_target_list(fitness_report, boundary_map),
        "audit_compaction_pre_contract": compaction_contract,
        "compaction_implementation_allowed": _compaction_implementation_allowed(compaction_contract),
    }


def validate_audit_compaction_governance_report(report: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    _validate_l5_identity(report, issues)
    _validate_l5_truth_boundaries(report, issues)
    _validate_worktree_ownership_audit(report, issues)
    _validate_structure_target_list(report, issues)
    _validate_compaction_pre_contract(report, issues)
    return {
        "surface": "mas_l5_audit_compaction_governance_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_l5_identity(report: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _text(report.get("surface")) != SURFACE:
        issues.append({"code": "invalid_surface"})
    if _text(report.get("lane_id")) != L5_LANE_ID:
        issues.append({"code": "invalid_lane"})
    if _text(report.get("authority_mode")) != AUTHORITY_MODE:
        issues.append({"code": "l5_claims_non_maintainability_authority"})
    if report.get("projection_only") is not True or report.get("maintainability_only") is not True:
        issues.append({"code": "l5_not_read_model_only"})


def _validate_l5_truth_boundaries(report: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _list(report.get("truth_writes")):
        issues.append({"code": "l5_declares_truth_writes", "truth_writes": list(_list(report.get("truth_writes")))})

    out_of_scope = set(_strings(report.get("truth_surfaces_out_of_scope")))
    for surface in TRUTH_SURFACES_OUT_OF_SCOPE:
        if surface not in out_of_scope:
            issues.append({"code": "missing_truth_surface_exclusion", "surface": surface})


def _validate_worktree_ownership_audit(report: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    ownership_audit = _mapping(report.get("worktree_ownership_audit"))
    for bucket in ("main", "current_l5_worktree", "external_active_worktree", "unknown_owner"):
        if bucket not in ownership_audit:
            issues.append({"code": "missing_worktree_owner_bucket", "bucket": bucket})
    for candidate in _list(ownership_audit.get("cleanup_candidates")):
        if not isinstance(candidate, Mapping):
            issues.append({"code": "invalid_cleanup_candidate"})
            continue
        if candidate.get("cleanup_allowed") is not False:
            issues.append({"code": "cleanup_allowed_without_absorb_authority", "path": candidate.get("path")})


def _validate_structure_target_list(report: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    target_list = _mapping(report.get("structure_target_list"))
    if _text(target_list.get("source")) != "Sentrux structure lane + line budget + boundary fitness":
        issues.append({"code": "invalid_structure_target_source"})
    for target in _list(target_list.get("top_targets")):
        if not isinstance(target, Mapping):
            issues.append({"code": "invalid_structure_target"})
            continue
        if _text(target.get("action_kind")) != "natural_boundary_split":
            issues.append({"code": "structure_target_not_natural_boundary", "path": target.get("path")})


def _validate_compaction_pre_contract(report: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    pre_contract = _mapping(report.get("audit_compaction_pre_contract"))
    gates = {_text(gate.get("gate_id")) for gate in _list(pre_contract.get("gates")) if isinstance(gate, Mapping)}
    for gate in REQUIRED_COMPACTION_GATES:
        if gate not in gates:
            issues.append({"code": "missing_compaction_pre_contract_gate", "gate": gate})

    gate_statuses = _compaction_gate_statuses(pre_contract)
    all_required_gates_passed = all(gate_statuses.get(gate) == "passed" for gate in REQUIRED_COMPACTION_GATES)
    if all_required_gates_passed:
        _validate_required_compaction_proofs(pre_contract, issues)

    contract_passed = _compaction_contract_passed(pre_contract)
    if report.get("compaction_implementation_allowed") is not contract_passed:
        if report.get("compaction_implementation_allowed") is True:
            issues.append({"code": "compaction_allowed_before_contract_passes"})
        else:
            issues.append({"code": "compaction_blocked_after_contract_passes"})
    if pre_contract.get("contract_passed") not in (None, contract_passed):
        issues.append({"code": "compaction_contract_passed_flag_drift"})
    expected_status = "contract_passed" if contract_passed else "blocked_until_contract_passes"
    if _text(pre_contract.get("implementation_status")) not in (None, expected_status):
        issues.append({"code": "invalid_compaction_contract_status", "expected": expected_status})


def _validate_required_compaction_proofs(contract: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    for proof_ref in REQUIRED_COMPACTION_PROOF_REFS:
        if not _has_compaction_proof(contract, proof_ref):
            issues.append({"code": f"missing_{proof_ref}"})


def _build_compaction_contract_read_model(contract: Mapping[str, Any] | None) -> dict[str, Any]:
    if contract is None:
        return _build_compaction_pre_contract()

    read_model = dict(contract)
    read_model.setdefault("surface", "mas_l5_audit_compaction_pre_contract")
    read_model.setdefault("gates", _build_compaction_pre_contract()["gates"])
    contract_passed = _compaction_contract_passed(read_model)
    read_model["implementation_status"] = "contract_passed" if contract_passed else "blocked_until_contract_passes"
    read_model["contract_passed"] = contract_passed
    read_model["required_proof_refs"] = list(REQUIRED_COMPACTION_PROOF_REFS)
    read_model.setdefault(
        "forbidden_until_passed",
        _build_compaction_pre_contract()["forbidden_until_passed"],
    )
    return read_model


def _compaction_contract_passed(contract: Mapping[str, Any]) -> bool:
    gate_statuses = _compaction_gate_statuses(contract)
    if not all(gate_statuses.get(gate) == "passed" for gate in REQUIRED_COMPACTION_GATES):
        return False
    return all(_has_compaction_proof(contract, proof_ref) for proof_ref in REQUIRED_COMPACTION_PROOF_REFS)


def _compaction_gate_statuses(contract: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        _text(gate.get("gate_id")) or "": _text(gate.get("status"))
        for gate in _list(contract.get("gates"))
        if isinstance(gate, Mapping)
    }


def _has_compaction_proof(contract: Mapping[str, Any], proof_ref: str) -> bool:
    if _proof_value_present(contract.get(proof_ref)):
        return True
    proofs = _mapping(contract.get("proofs"))
    if _proof_value_present(proofs.get(proof_ref)):
        return True
    return any(
        isinstance(gate, Mapping)
        and _proof_value_present(_mapping(gate.get("proofs")).get(proof_ref) or gate.get(proof_ref))
        for gate in _list(contract.get("gates"))
    )


def _proof_value_present(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_text(value.get(key)) for key in ("ref", "uri", "path", "digest", "evidence_ref"))
    return _text(value) is not None


def _build_compaction_pre_contract() -> dict[str, Any]:
    return {
        "surface": "mas_l5_audit_compaction_pre_contract",
        "implementation_status": "blocked_until_contract_passes",
        "contract_passed": False,
        "required_proof_refs": list(REQUIRED_COMPACTION_PROOF_REFS),
        "gates": [
            {
                "gate_id": "restore",
                "status": "contract_required",
                "required_proof": "compacted audit buckets can be restored to byte-addressable source records",
            },
            {
                "gate_id": "index",
                "status": "contract_required",
                "required_proof": "compacted buckets publish a deterministic restore index before deletion or archive movement",
            },
            {
                "gate_id": "provenance",
                "status": "contract_required",
                "required_proof": "compacted records preserve source path, original digest, compacted digest, and compaction timestamp",
            },
        ],
        "forbidden_until_passed": [
            "delete_audit_bucket",
            "rewrite_audit_log",
            "move_runtime_truth",
            "rewrite_publication_or_delivery_artifacts",
        ],
    }


def _compaction_implementation_allowed(contract: Mapping[str, Any]) -> bool:
    return _compaction_contract_passed(contract)


def _finding_paths(report: BoundaryFitnessReport) -> tuple[str, ...]:
    return tuple(finding.path for finding in report.findings)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _worktree_records(
    repo_root: Path,
    worktrees: Sequence[Mapping[str, Any] | WorktreeRecord] | None,
) -> tuple[WorktreeRecord, ...]:
    if worktrees is not None:
        return tuple(_coerce_worktree_record(item) for item in worktrees)
    return _git_worktree_records(repo_root)


def _git_worktree_records(repo_root: Path) -> tuple[WorktreeRecord, ...]:
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    records: list[WorktreeRecord] = []
    current: dict[str, Any] = {}
    for line in result.stdout.splitlines():
        if not line:
            if current:
                records.append(_coerce_worktree_record(current))
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key == "HEAD":
            current["commit"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["detached"] = True
    if current:
        records.append(_coerce_worktree_record(current))
    return tuple(records)


def _coerce_worktree_record(value: Mapping[str, Any] | WorktreeRecord) -> WorktreeRecord:
    if isinstance(value, WorktreeRecord):
        return value
    return WorktreeRecord(
        path=str(value.get("path") or value.get("worktree") or ""),
        branch=_text(value.get("branch")),
        commit=_text(value.get("commit") or value.get("HEAD")),
        detached=bool(value.get("detached")),
    )


def _build_worktree_ownership_audit(records: Sequence[WorktreeRecord]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "main": [],
        "current_l5_worktree": [],
        "external_active_worktree": [],
        "unknown_owner": [],
    }
    for record in records:
        bucket = _worktree_bucket(record)
        buckets[bucket].append(
            {
                "path": record.path,
                "branch": record.branch,
                "commit": record.commit,
                "detached": record.detached,
                "cleanup_allowed": False,
                "cleanup_gate": "requires explicit absorbed-owner evidence outside this read model",
            }
        )
    return {
        "surface": "mas_l5_worktree_ownership_audit",
        "cleanup_policy": "no automatic cleanup; cleanup requires explicit owner and absorbed evidence",
        **buckets,
        "cleanup_candidates": [],
    }


def _worktree_bucket(record: WorktreeRecord) -> str:
    branch = record.branch or ""
    if branch in {"main", "master"}:
        return "main"
    if branch in L5_BRANCHES:
        return "current_l5_worktree"
    if branch.startswith("codex/") or branch:
        return "external_active_worktree"
    return "unknown_owner"


def _build_structure_target_list(
    fitness_report: BoundaryFitnessReport,
    boundary_map: Mapping[str, Any],
) -> dict[str, Any]:
    findings = tuple(fitness_report.blocking_findings or fitness_report.oversized_findings)
    return {
        "surface": "mas_l5_structure_top_target_list",
        "source": "Sentrux structure lane + line budget + boundary fitness",
        "selection_policy": "top blocking findings first, sorted by severity and size; split only by natural responsibility boundary",
        "program_boundary_priorities": list(boundary_map.get("priorities") or []),
        "top_targets": [_structure_target(finding) for finding in findings[:10]],
    }


def _structure_target(finding: BoundaryFinding) -> dict[str, Any]:
    return {
        **asdict(finding),
        "boundary_id": _program_boundary_id(finding.path),
        "action_kind": "natural_boundary_split",
        "truth_impact": "maintainability_only",
    }


def _program_boundary_id(relative_path: str) -> str | None:
    for boundary in PROGRAM_BOUNDARIES:
        markers = boundary["path_markers"]
        if isinstance(markers, tuple) and any(marker in relative_path for marker in markers):
            return str(boundary["boundary_id"])
    return None
