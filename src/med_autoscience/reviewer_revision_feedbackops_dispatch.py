from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def dispatch_reviewer_revision_feedbackops(
    *,
    request_path: Path,
    opl_bin: str = "opl",
    run_agent_lab: bool = True,
) -> dict[str, Any]:
    request = _read_json(request_path)
    if request.get("surface_kind") != "mas_reviewer_revision_feedbackops_dispatch_request":
        raise ValueError(f"not a reviewer revision FeedbackOps dispatch request: {request_path}")

    result: dict[str, Any] = {
        "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_readback",
        "schema_version": 1,
        "request_path": str(Path(request_path).expanduser().resolve()),
        "study_id": request.get("study_id"),
        "authority_boundary": request.get("authority_boundary", {}),
        "writes_study_truth": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
    }
    if request.get("status") != "ready_for_opl_feedbackops":
        result.update({"status": "skipped", "reason": request.get("status")})
        return _write_readback(request_path, result)

    suite_path = _text(request.get("suite_path")) or _text(request.get("external_suite_ref"))
    result.update(
        {
            "status": "opl_execution_handoff_required",
            "next_owner": "one-person-lab",
            "blocked_reason": None,
            "execution_handoff": {
                "surface_kind": "mas_reviewer_revision_feedbackops_execution_handoff",
                "runtime_owner": "one-person-lab",
                "feedback_submit": dict(request.get("opl_feedback_submit") or {}),
                "feedback_read_required": True,
                "feedback_reconcile_required": True,
                "agent_lab_suite_ref": suite_path,
                "agent_lab_run_requested": bool(run_agent_lab and suite_path),
                "opl_bin_ref": opl_bin,
                "mas_executes_feedbackops": False,
                "mas_executes_agent_lab": False,
                "mas_executes_oma": False,
            },
        }
    )
    return _write_readback(request_path, result)


def _valid_ai_reviewer_evaluation(payload: dict[str, Any]) -> bool:
    required_strings = (
        "reviewer_kind",
        "model_or_provider",
        "run_ref",
        "execution_attempt_ref",
        "review_attempt_ref",
        "critique",
        "verdict",
        "predicted_impact",
    )
    if any(_text(payload.get(key)) is None for key in required_strings):
        return False
    if payload.get("no_shared_context") is not True or payload.get("independent_attempt") is not True:
        return False
    if _text(payload.get("execution_attempt_ref")) == _text(payload.get("review_attempt_ref")):
        return False
    for key in ("suggestions", "source_refs", "direct_evidence_refs"):
        value = payload.get(key)
        if not isinstance(value, list) or not value or any(_text(item) is None for item in value):
            return False
        if key in {"source_refs", "direct_evidence_refs"} and all(
            _suite_or_scaffold_only_ref(str(item)) for item in value
        ):
            return False
    provenance = payload.get("provenance")
    return isinstance(provenance, dict) and bool(provenance)


def _suite_or_scaffold_only_ref(ref: str) -> bool:
    normalized = ref.lower()
    return "suite" in normalized or "scaffold" in normalized


def reviewer_revision_feedbackops_execution_readback_path(*, study_root: Path) -> Path:
    return (
        Path(study_root)
        / "artifacts"
        / "agent_lab"
        / "medical_manuscript_quality"
        / "feedbackops_execution_readback.json"
    )


def read_reviewer_revision_feedbackops_execution_readback(*, study_root: Path) -> dict[str, Any] | None:
    path = reviewer_revision_feedbackops_execution_readback_path(study_root=study_root)
    if not path.exists():
        return None
    payload = _read_json(path)
    return _compact_execution_readback(payload, path=path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def _write_readback(request_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    output_path = Path(request_path).expanduser().resolve().with_name("feedbackops_execution_readback.json")
    payload["readback_path"] = str(output_path)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _compact_execution_readback(payload: dict[str, Any], *, path: Path) -> dict[str, Any]:
    compact = {
        "surface_kind": payload.get("surface_kind"),
        "schema_version": payload.get("schema_version"),
        "status": payload.get("status"),
        "study_id": payload.get("study_id"),
        "next_owner": payload.get("next_owner"),
        "blocked_reason": payload.get("blocked_reason"),
        "execution_handoff": dict(payload.get("execution_handoff") or {}),
        "ai_reviewer_evaluation_ref": payload.get("ai_reviewer_evaluation_ref"),
        "ai_reviewer_evaluation_status": payload.get("ai_reviewer_evaluation_status"),
        "oma_materialization_request_ref": payload.get("oma_materialization_request_ref"),
        "oma_materialization_request_status": payload.get("oma_materialization_request_status"),
        "target_owner_closeout_ref": payload.get("target_owner_closeout_ref"),
        "skill_writeback_status": payload.get("skill_writeback_status"),
        "target_skill_refs": list(payload.get("target_skill_refs") or []),
        "structured_ai_reviewer_evaluation_request_ref": payload.get(
            "structured_ai_reviewer_evaluation_request_ref"
        ),
        "readback_path": str(path),
        "writes_study_truth": payload.get("writes_study_truth") is True,
        "writes_owner_receipt": payload.get("writes_owner_receipt") is True,
        "writes_typed_blocker": payload.get("writes_typed_blocker") is True,
        "authority_boundary": dict(payload.get("authority_boundary") or {}),
        "commands": {},
    }
    commands = compact["commands"]
    for key in ("feedbackops_submit", "feedbackops_read", "feedbackops_reconcile", "agent_lab_run"):
        command = payload.get(key)
        if isinstance(command, dict):
            commands[key] = {
                "argv": list(command.get("argv") or []),
                "returncode": command.get("returncode"),
                "stdout_bytes": command.get("stdout_bytes"),
                "stdout_summary": dict(command.get("stdout_summary") or {}),
                "stderr": command.get("stderr"),
            }
    if compact["status"] in {
        "blocked_missing_structured_ai_reviewer_evaluation",
        "ready_for_oma_work_order_materialization",
    }:
        superseding = _newer_oma_work_order_or_receipt(path)
        if superseding is not None:
            compact.update(
                {
                    "status": superseding.pop(
                        "superseding_status",
                        "superseded_by_oma_work_order_materialization",
                    ),
                    "superseded_status": compact["status"],
                    "blocked_reason": None,
                    "next_owner": "opl-meta-agent",
                    **superseding,
                }
            )
    return compact


def _newer_oma_work_order_or_receipt(path: Path) -> dict[str, Any] | None:
    path = Path(path).expanduser().resolve()
    try:
        readback_mtime = path.stat().st_mtime
    except OSError:
        return None
    candidates: list[tuple[int, float, Path, dict[str, Any]]] = []
    for pattern in (
        "oma_external_suite_*/developer-patch-work-order.json",
        "oma_external_suite_*/meta-agent-improvement-receipt.json",
        "oma_external_suite_*/external-work-order-delegation.json",
        "oma_external_suite_*/opl_work_order_execute/work-order-execution-receipt.json",
    ):
        for candidate in path.parent.glob(pattern):
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if mtime <= readback_mtime:
                continue
            payload = _read_json(candidate)
            ai_ref = _candidate_ai_reviewer_evaluation_ref(payload, candidate)
            if ai_ref is None:
                continue
            try:
                ai_payload = _read_json(Path(ai_ref))
            except OSError:
                continue
            if not _valid_ai_reviewer_evaluation(ai_payload):
                continue
            candidates.append((_oma_candidate_rank(candidate), mtime, candidate, payload))
    if not candidates:
        return None
    _, _, candidate, payload = max(candidates, key=lambda item: (item[0], item[1], str(item[2])))
    return _oma_candidate_readback(candidate, payload)


def _oma_candidate_rank(candidate: Path) -> int:
    if candidate.name == "work-order-execution-receipt.json":
        return 3
    if candidate.name == "external-work-order-delegation.json":
        return 2
    return 1


def _candidate_ai_reviewer_evaluation_ref(payload: dict[str, Any], candidate: Path) -> str | None:
    direct = _text(payload.get("ai_reviewer_evaluation_ref"))
    if direct is not None:
        return direct
    for key in ("source_work_order_path", "work_order_path"):
        work_order_path = _text(payload.get(key))
        if work_order_path is None:
            continue
        try:
            work_order = _read_json(Path(work_order_path))
        except OSError:
            continue
        work_order_ref = _text(work_order.get("ai_reviewer_evaluation_ref"))
        if work_order_ref is not None:
            return work_order_ref
    sibling_work_order = candidate.parent / "developer-patch-work-order.json"
    if not sibling_work_order.exists() and candidate.parent.name == "opl_work_order_execute":
        sibling_work_order = candidate.parent.parent / "developer-patch-work-order.json"
    if not sibling_work_order.exists():
        return None
    try:
        work_order = _read_json(sibling_work_order)
    except OSError:
        return None
    return _text(work_order.get("ai_reviewer_evaluation_ref"))


def _oma_candidate_readback(candidate: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = {
        "oma_work_order_or_receipt_ref": str(candidate),
        "oma_work_order_or_receipt_status": payload.get("status"),
        "oma_work_order_or_receipt_surface_kind": payload.get("surface_kind"),
        "ai_reviewer_evaluation_ref": _candidate_ai_reviewer_evaluation_ref(payload, candidate),
        "ai_reviewer_evaluation_status": "valid",
    }
    work_order_id = _text(payload.get("work_order_id")) or _text(payload.get("work_order_ref"))
    if work_order_id is not None:
        result["oma_work_order_id"] = work_order_id
    if candidate.name == "work-order-execution-receipt.json":
        absorption = payload.get("absorption") if isinstance(payload.get("absorption"), dict) else {}
        cleanup = payload.get("cleanup") if isinstance(payload.get("cleanup"), dict) else {}
        target_owner = (
            payload.get("target_owner_receipt_or_typed_blocker")
            if isinstance(payload.get("target_owner_receipt_or_typed_blocker"), dict)
            else {}
        )
        result.update(
            {
                "superseding_status": "superseded_by_oma_work_order_execution",
                "oma_patch_absorbed": absorption.get("absorbed") is True,
                "oma_absorbed_head": absorption.get("absorbed_head"),
                "oma_worktree_removed": cleanup.get("worktree_removed") is True,
                "oma_branch_removed": cleanup.get("branch_removed") is True,
                "oma_target_owner_result_status": target_owner.get("status"),
            }
        )
    elif candidate.name == "external-work-order-delegation.json":
        result["superseding_status"] = "superseded_by_oma_work_order_delegation"
    return result
