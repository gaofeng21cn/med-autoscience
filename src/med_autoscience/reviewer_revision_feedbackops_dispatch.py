from __future__ import annotations

import json
import subprocess
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
            result["ai_reviewer_evaluation_ref"] = ai_reviewer_evaluation_ref
            result["ai_reviewer_evaluation_status"] = "valid"
            result["status"] = "ready_for_oma_work_order_materialization"
            result["next_owner"] = "opl-meta-agent"
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
    provenance = payload.get("provenance")
    return isinstance(provenance, dict) and bool(provenance)


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
    return compact


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
