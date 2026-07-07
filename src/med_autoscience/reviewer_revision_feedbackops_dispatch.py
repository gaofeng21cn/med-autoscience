from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from med_autoscience.reviewer_revision_oma_materialization import write_oma_materialization_request


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

    submit = _run_json([opl_bin, "feedback", "submit", *_strings(request["opl_feedback_submit"]["argv"])])
    result["feedbackops_submit"] = submit
    if submit["returncode"] != 0:
        result.update({"status": "blocked_opl_feedbackops_submit_failed"})
        return _write_readback(request_path, result)

    result["feedbackops_read"] = _run_json([opl_bin, "feedback", "read", "--json"])
    result["feedbackops_reconcile"] = _run_json([opl_bin, "feedback", "reconcile", "--json"])

    suite_path = _text(request.get("suite_path")) or _text(request.get("external_suite_ref"))
    if run_agent_lab and suite_path:
        result["agent_lab_run"] = _run_json([opl_bin, "agent-lab", "run", "--suite", suite_path, "--json"])

    if result.get("agent_lab_run", {}).get("returncode") not in (None, 0):
        result["status"] = "blocked_agent_lab_run_failed"
    else:
        ai_reviewer_evaluation_ref = _resolve_ai_reviewer_evaluation_ref(
            request=request,
            request_path=request_path,
            suite_path=suite_path,
        )
        if ai_reviewer_evaluation_ref:
            oma_request_path, oma_request = write_oma_materialization_request(
                request=request,
                request_path=request_path,
                suite_path=suite_path,
                ai_reviewer_evaluation_ref=ai_reviewer_evaluation_ref,
                opl_bin=opl_bin,
            )
            result["ai_reviewer_evaluation_ref"] = ai_reviewer_evaluation_ref
            result["ai_reviewer_evaluation_status"] = "valid"
            result["oma_materialization_request_ref"] = str(oma_request_path)
            result["oma_materialization_request_status"] = oma_request.get("status")
            result["target_owner_closeout_ref"] = oma_request.get("target_owner_closeout_ref")
            result["skill_writeback_status"] = oma_request.get("skill_writeback_status")
            result["target_skill_refs"] = list(oma_request.get("target_skill_refs") or [])
            result["status"] = oma_request.get("status") or "ready_for_oma_work_order_materialization"
            result["next_owner"] = "opl-meta-agent"
            if result["status"] != "ready_for_oma_work_order_materialization":
                result["blocked_reason"] = oma_request.get("blocked_reason")
        else:
            request_packet = _write_structured_ai_reviewer_evaluation_request(
                request=request,
                request_path=request_path,
                suite_path=suite_path,
            )
            result["structured_ai_reviewer_evaluation_request_ref"] = str(request_packet)
            result["status"] = "blocked_missing_structured_ai_reviewer_evaluation"
            result["next_owner"] = "opl-meta-agent"
            result["blocked_reason"] = (
                "OPL FeedbackOps and Agent Lab consumed the MAS suite, but OMA work-order "
                "materialization requires a structured independent AI reviewer evaluation ref."
            )
    return _write_readback(request_path, result)


def _resolve_ai_reviewer_evaluation_ref(
    *,
    request: dict[str, Any],
    request_path: Path,
    suite_path: str | None,
) -> str | None:
    explicit = _text(request.get("ai_reviewer_evaluation_ref"))
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    base_dirs = [Path(request_path).expanduser().resolve().parent]
    if suite_path:
        base_dirs.append(Path(suite_path).expanduser().resolve().parent)
    for base in base_dirs:
        candidates.extend(sorted(base.glob("ai_reviewer_evaluation*.json")))
        candidates.extend(sorted(base.glob("*ai_reviewer*evaluation*.json")))
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        payload = _read_json(resolved)
        if _valid_ai_reviewer_evaluation(payload):
            return str(resolved)
    normalized_ref = _materialize_suite_ai_reviewer_evaluation(
        request=request,
        request_path=request_path,
        suite_path=suite_path,
    )
    if normalized_ref is not None:
        return str(normalized_ref)
    return None


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


def _materialize_suite_ai_reviewer_evaluation(
    *,
    request: dict[str, Any],
    request_path: Path,
    suite_path: str | None,
) -> Path | None:
    if suite_path is None:
        return None
    suite_ref = Path(suite_path).expanduser().resolve()
    if not suite_ref.exists():
        return None
    suite = _read_json(suite_ref)
    structured = _find_structured_independent_ai_reviewer_evaluation(suite)
    if structured is None:
        return None
    normalized = _normalize_structured_ai_reviewer_evaluation(
        request=request,
        request_path=request_path,
        suite_path=suite_ref,
        suite=suite,
        structured=structured,
    )
    if not _valid_ai_reviewer_evaluation(normalized):
        return None
    output_path = Path(request_path).expanduser().resolve().with_name(
        "ai_reviewer_evaluation_independent.json"
    )
    output_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def _find_structured_independent_ai_reviewer_evaluation(payload: dict[str, Any]) -> dict[str, Any] | None:
    direct = payload.get("structured_independent_ai_reviewer_evaluation")
    if _is_structured_independent_ai_reviewer_evaluation(direct):
        return dict(direct)
    for task in payload.get("tasks") or []:
        if not isinstance(task, dict):
            continue
        task_direct = task.get("structured_independent_ai_reviewer_evaluation")
        if _is_structured_independent_ai_reviewer_evaluation(task_direct):
            return dict(task_direct)
        candidate = task.get("improvement_candidate")
        if isinstance(candidate, dict):
            nested = candidate.get("structured_independent_ai_reviewer_evaluation")
            if _is_structured_independent_ai_reviewer_evaluation(nested):
                return dict(nested)
    return None


def _is_structured_independent_ai_reviewer_evaluation(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if _text(value.get("surface_kind")) != "mas_structured_independent_ai_reviewer_evaluation":
        return False
    return (
        _non_empty_items(value.get("critique"))
        and _non_empty_items(value.get("suggestions"))
        and _non_empty_items(value.get("direct_evidence_refs"))
        and isinstance(value.get("provenance"), dict)
        and bool(value.get("provenance"))
    )


def _normalize_structured_ai_reviewer_evaluation(
    *,
    request: dict[str, Any],
    request_path: Path,
    suite_path: Path,
    suite: dict[str, Any],
    structured: dict[str, Any],
) -> dict[str, Any]:
    study_id = _text(structured.get("study_id")) or _text(request.get("study_id")) or "unknown-study"
    evaluation_ref = _text(structured.get("evaluation_ref")) or (
        f"structured-ai-reviewer-evaluation:mas/{study_id}/publication_eval_latest"
    )
    source_refs = _unique_texts(
        [
            _text(structured.get("source_publication_eval_ref")),
            *_strings(structured.get("direct_evidence_refs")),
            _text(request.get("feedback_ref")),
            _text(request.get("delivery_ref")),
            _text(request.get("source_trigger_ref")),
            str(suite_path),
        ]
    )
    direct_refs = _unique_texts(
        [
            *_strings(structured.get("direct_evidence_refs")),
            _text(structured.get("source_publication_eval_ref")),
        ]
    )
    provenance = dict(structured.get("provenance") or {})
    provenance.update(
        {
            "normalized_by": "med_autoscience.reviewer_revision_feedbackops_dispatch",
            "normalized_from_surface_kind": structured.get("surface_kind"),
            "source_suite_ref": str(suite_path),
            "source_request_ref": str(Path(request_path).expanduser().resolve()),
            "refs_only": True,
            "candidate_is_authority": False,
        }
    )
    return {
        "reviewer_kind": "independent_ai_medical_manuscript_quality_reviewer",
        "model_or_provider": _text(provenance.get("source_kind")) or "mas_publication_eval_ai_reviewer_projection",
        "run_ref": _text(structured.get("evaluation_ref")) or f"run:mas/{study_id}/publication-eval-latest",
        "execution_attempt_ref": _text(suite.get("suite_id")) or f"agent-lab-suite:mas/{study_id}",
        "review_attempt_ref": evaluation_ref,
        "no_shared_context": True,
        "independent_attempt": True,
        "critique": _summarize_structured_items(structured.get("critique")),
        "suggestions": _summarize_structured_list(structured.get("suggestions")),
        "source_refs": source_refs,
        "direct_evidence_refs": direct_refs,
        "verdict": "valid_refs_only_independent_reviewer_input",
        "predicted_impact": (
            "Routes MAS AI-reviewer manuscript critique into OMA work-order materialization "
            "without granting OMA manuscript, study-truth, or quality-verdict authority."
        ),
        "provenance": provenance,
    }


def _summarize_structured_items(value: object) -> str:
    summaries = _summarize_structured_list(value)
    return " ".join(summaries)


def _summarize_structured_list(value: object) -> list[str]:
    if isinstance(value, list):
        summaries: list[str] = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                label = _text(item.get("critique_id")) or _text(item.get("suggestion_id")) or f"item:{index}"
                summary = _text(item.get("summary")) or _text(item.get("rationale"))
                if summary is not None:
                    summaries.append(f"{label}: {summary}")
            elif (text := _text(item)) is not None:
                summaries.append(text)
        if summaries:
            return summaries
    if text := _text(value):
        return [text]
    return ["MAS structured reviewer evaluation did not provide prose details."]


def _non_empty_items(value: object) -> bool:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and (
                _text(item.get("summary")) is not None or _text(item.get("rationale")) is not None
            ):
                return True
            if _text(item) is not None:
                return True
        return False
    return _text(value) is not None


def _suite_or_scaffold_only_ref(ref: str) -> bool:
    normalized = ref.lower()
    return "suite" in normalized or "scaffold" in normalized


def _write_structured_ai_reviewer_evaluation_request(
    *,
    request: dict[str, Any],
    request_path: Path,
    suite_path: str | None,
) -> Path:
    output_path = Path(request_path).expanduser().resolve().with_name(
        "structured_ai_reviewer_evaluation_request.json"
    )
    source_refs = _unique_texts(
        [
            suite_path,
            request.get("feedback_ref"),
            request.get("external_suite_ref"),
            request.get("delivery_ref"),
            request.get("source_trigger_ref"),
            *_strings(request.get("required_packet_refs")),
        ]
    )
    payload = {
        "surface_kind": "mas_structured_ai_reviewer_evaluation_request",
        "schema_version": 1,
        "status": "needs_independent_ai_reviewer_evaluation",
        "study_id": request.get("study_id"),
        "target_agent_id": request.get("target_agent_id") or "med-autoscience",
        "suite_path": suite_path,
        "source_request_ref": str(Path(request_path).expanduser().resolve()),
        "required_fields": [
            "reviewer_kind",
            "model_or_provider",
            "run_ref",
            "execution_attempt_ref",
            "review_attempt_ref",
            "no_shared_context",
            "independent_attempt",
            "critique",
            "suggestions",
            "source_refs",
            "direct_evidence_refs",
            "verdict",
            "predicted_impact",
            "provenance",
        ],
        "minimum_requirements": {
            "no_shared_context": True,
            "independent_attempt": True,
            "execution_attempt_ref_must_differ_from_review_attempt_ref": True,
            "suggestions": "non_empty_string_array",
            "source_refs": "non_empty_string_array_with_reviewer_evidence_beyond_suite_only_refs",
            "direct_evidence_refs": "non_empty_string_array_with_direct_manuscript_or_review_evidence",
            "provenance": "non_empty_object",
        },
        "source_refs": source_refs,
        "direct_evidence_ref_candidates": source_refs,
        "oma_consumer": "opl-meta-agent.improve-from-external-agent-lab-suite",
        "authority_boundary": {
            "writes_domain_truth": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_runtime_queue_or_provider_attempt": False,
            "writes_manuscript_or_current_package": False,
            "can_authorize_publication_ready": False,
            "can_authorize_submission_ready": False,
        },
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def _unique_texts(values: list[object]) -> list[str]:
    items: list[str] = []
    for value in values:
        text = _text(value)
        if text is not None and text not in items:
            items.append(text)
    return items


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


def _run_json(argv: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return {"argv": argv, "returncode": 127, "stdout_json": None, "stderr": str(exc)}
    payload = _parse_json(completed.stdout)
    stdout = completed.stdout or ""
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stdout_json": payload if len(stdout) <= 50000 else None,
        "stdout_summary": _summarize_stdout_payload(payload),
        "stderr": completed.stderr.strip(),
    }


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


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        return None


def _strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


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


def _summarize_stdout_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    summary: dict[str, Any] = {"top_level_keys": sorted(str(key) for key in payload.keys())}
    for key in ("status", "state", "version", "surface_kind"):
        if key not in payload:
            continue
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            summary[key] = value
    for key in ("feedbackops_submit", "feedbackops", "feedbackops_reconcile", "agent_lab", "agent_lab_run"):
        child = payload.get(key)
        if isinstance(child, dict):
            summary[key] = _compact_mapping(child)
    return summary


def _compact_mapping(value: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in (
        "surface_kind",
        "status",
        "state",
        "event_id",
        "read_model_id",
        "suite_id",
        "summary",
        "status_buckets",
        "ref_summary",
        "promotion_eligibility",
        "domain_summary",
        "longline_summary",
    ):
        item = value.get(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            compact[key] = item
        elif isinstance(item, dict):
            compact[key] = _bounded_dict(item)
        elif isinstance(item, list):
            compact[key] = _bounded_list(item)
    event = value.get("event")
    if isinstance(event, dict):
        compact["event"] = {
            key: event.get(key)
            for key in (
                "event_id",
                "target_agent_id",
                "status",
                "external_suite_ref",
                "developer_work_order_candidate_ref",
                "blocker_ref",
            )
            if key in event
        }
    return compact


def _bounded_dict(value: dict[str, Any], *, limit: int = 12) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            compact["..."] = f"{len(value) - limit} more keys"
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            compact[str(key)] = item
        elif isinstance(item, list):
            compact[str(key)] = _bounded_list(item)
        elif isinstance(item, dict):
            compact[str(key)] = _bounded_dict(item, limit=6)
    return compact


def _bounded_list(value: list[Any], *, limit: int = 8) -> list[Any]:
    items: list[Any] = []
    for item in value[:limit]:
        if isinstance(item, (str, int, float, bool)) or item is None:
            items.append(item)
        elif isinstance(item, dict):
            items.append(_bounded_dict(item, limit=6))
        else:
            items.append(str(item))
    if len(value) > limit:
        items.append(f"... {len(value) - limit} more items")
    return items
