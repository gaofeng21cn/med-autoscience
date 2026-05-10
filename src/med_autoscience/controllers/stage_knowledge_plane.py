from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers import portfolio_memory, workspace_literature


SCHEMA_VERSION = 1
CONTRACT_SURFACE = "stage_knowledge_plane_contract"
KNOWLEDGE_PACKET_SURFACE = "stage_knowledge_packet"
MEMORY_CLOSEOUT_SURFACE = "stage_memory_closeout_packet"
MEMORY_ROUTER_SURFACE = "memory_write_router_receipt"
RECALL_INDEX_SURFACE = "stage_recall_index"

EXPLORATORY_STAGES = ("scout", "idea", "analysis-campaign", "review")
STAGE_KNOWLEDGE_ROOT = Path("artifacts/stage_knowledge")

COMMON_PACKET_FIELDS = (
    "schema_version",
    "study_id",
    "stage",
    "input_refs",
    "source_fingerprint",
    "authority_boundary",
    "idempotency_key",
)

STAGE_OBLIGATIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "scout": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "portfolio_memory.topic_landscape",
            "portfolio_memory.dataset_question_map",
            "portfolio_memory.venue_intelligence",
            "workspace_literature.coverage",
            "literature_provider_runtime.readiness",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "clinical_question_framing",
            "literature_gap",
            "anchor_paper_role",
            "route_recommendation",
        ),
    },
    "idea": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "portfolio_memory.study_recall_index",
            "study_reference_context",
            "prior_candidate_or_failed_lines",
            "journal_neighbor_refs",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "selected_line",
            "rejected_alternatives",
            "selection_rationale",
            "stop_rule",
            "memory_reuse_note",
        ),
    },
    "analysis-campaign": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "failed_path_history",
            "evidence_ledger",
            "citation_gaps",
            "bounded_frontier",
            "reviewer_concerns",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "slice_ledger",
            "negative_or_weak_result_interpretation",
            "route_impact",
            "failed_path_lesson",
        ),
    },
    "review": {
        "knowledge_input_obligations": (
            "stage_knowledge_packet_ref",
            "manuscript",
            "claim_evidence_map",
            "display_to_claim_map",
            "study_reference_context",
            "citation_ledger_refs",
            "ai_reviewer_calibration_memory",
            "prior_reviewer_findings",
        ),
        "memory_closeout_obligations": (
            "stage_memory_closeout_packet",
            "reviewer_action_matrix",
            "evidence_or_citation_repair_request",
            "reusable_critique_lesson",
        ),
    },
}


def stage_knowledge_plane_contract() -> dict[str, Any]:
    return {
        "surface": CONTRACT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "packet_contracts": {
            KNOWLEDGE_PACKET_SURFACE: _packet_contract(KNOWLEDGE_PACKET_SURFACE),
            MEMORY_CLOSEOUT_SURFACE: _packet_contract(MEMORY_CLOSEOUT_SURFACE),
            MEMORY_ROUTER_SURFACE: _packet_contract(MEMORY_ROUTER_SURFACE),
            RECALL_INDEX_SURFACE: _packet_contract(RECALL_INDEX_SURFACE),
        },
        "exploratory_stages": list(EXPLORATORY_STAGES),
        "stage_obligations": {
            stage: {key: list(values) for key, values in obligations.items()}
            for stage, obligations in STAGE_OBLIGATIONS.items()
        },
        "authority_boundary": _authority_boundary(),
    }


def stage_knowledge_packet_path(*, study_root: Path, stage: str) -> Path:
    return Path(study_root).expanduser().resolve() / STAGE_KNOWLEDGE_ROOT / _safe_stage(stage) / "latest.json"


def stage_memory_closeout_packet_path(*, study_root: Path, stage: str, idempotency_key: str) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / STAGE_KNOWLEDGE_ROOT
        / _safe_stage(stage)
        / "closeouts"
        / f"{_safe_key(idempotency_key)}.json"
    )


def memory_write_router_receipt_path(*, study_root: Path, idempotency_key: str) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / STAGE_KNOWLEDGE_ROOT
        / "memory_write_router_receipts"
        / f"{_safe_key(idempotency_key)}.json"
    )


def stage_recall_index_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STAGE_KNOWLEDGE_ROOT / "stage_recall_index" / "latest.json"


def build_stage_knowledge_packet(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_stage = _validate_stage(stage)
    input_refs = _stage_input_refs(
        study_root=resolved_study_root,
        workspace_root=resolved_workspace_root,
        quest_root=quest_root,
    )
    missing = _missing_reasons(input_refs=input_refs, stage=resolved_stage)
    source_fingerprint = _fingerprint({"input_refs": input_refs, "stage": resolved_stage})
    return {
        "surface": KNOWLEDGE_PACKET_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": resolved_stage,
        "status": "ready" if not missing else "missing",
        "input_refs": input_refs,
        "missing_reasons": missing,
        "stage_obligations": _stage_obligations(resolved_stage),
        "high_signal_memory": _high_signal_memory(input_refs=input_refs),
        "literature_gaps": _literature_gaps(input_refs=input_refs),
        "failed_paths": _failed_paths(input_refs=input_refs),
        "citation_readiness": _citation_readiness(input_refs=input_refs),
        "current_claim_boundary": _claim_boundary(input_refs=input_refs),
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "idempotency_key": f"stage_knowledge_packet:{_required_text('study_id', study_id)}:{resolved_stage}:{source_fingerprint}",
    }


def materialize_stage_knowledge_packet(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    packet = build_stage_knowledge_packet(
        study_id=study_id,
        stage=stage,
        study_root=study_root,
        workspace_root=workspace_root,
        quest_root=quest_root,
    )
    packet_path = stage_knowledge_packet_path(study_root=Path(study_root), stage=stage)
    _write_json(packet_path, packet)
    return {**packet, "artifact_path": str(packet_path)}


def normalize_stage_memory_closeout_packet(
    *,
    study_id: str,
    stage: str,
    closeout_payload: Mapping[str, Any],
    study_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    resolved_stage = _validate_stage(stage)
    normalized = {
        "reusable_lessons": _mapping_list(closeout_payload.get("reusable_lessons")),
        "citation_gaps": _mapping_list(closeout_payload.get("citation_gaps")),
        "failed_paths": _mapping_list(closeout_payload.get("failed_paths")),
        "reference_role_updates": _mapping_list(closeout_payload.get("reference_role_updates")),
        "evidence_ledger_updates": _mapping_list(closeout_payload.get("evidence_ledger_updates")),
        "review_ledger_updates": _mapping_list(closeout_payload.get("review_ledger_updates")),
        "controller_decision_requests": _mapping_list(closeout_payload.get("controller_decision_requests")),
        "human_gate_requests": _mapping_list(closeout_payload.get("human_gate_requests")),
    }
    source_refs = _dedupe_text(
        [
            *_text_list(closeout_payload.get("source_refs")),
            *[
                ref
                for rows in normalized.values()
                for row in rows
                for ref in _text_list(row.get("source_refs"))
            ],
        ]
    )
    source_fingerprint = _fingerprint({"stage": resolved_stage, "closeout": normalized, "source_refs": source_refs})
    idempotency_key = (
        _text(closeout_payload.get("idempotency_key"))
        or f"stage_memory_closeout:{_required_text('study_id', study_id)}:{resolved_stage}:{source_fingerprint}"
    )
    packet = {
        "surface": MEMORY_CLOSEOUT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": resolved_stage,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "workspace_root": str(Path(workspace_root).expanduser().resolve()),
        "input_refs": source_refs,
        "source_refs": source_refs,
        "proposed_writes": _proposed_writes(normalized),
        "normalized_closeout": normalized,
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "idempotency_key": idempotency_key,
    }
    return packet


def materialize_stage_memory_closeout_packet(
    *,
    study_id: str,
    stage: str,
    closeout_payload: Mapping[str, Any],
    study_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    packet = normalize_stage_memory_closeout_packet(
        study_id=study_id,
        stage=stage,
        closeout_payload=closeout_payload,
        study_root=study_root,
        workspace_root=workspace_root,
    )
    path = stage_memory_closeout_packet_path(
        study_root=Path(study_root),
        stage=stage,
        idempotency_key=packet["idempotency_key"],
    )
    _write_json(path, packet)
    return {**packet, "artifact_path": str(path)}


def route_stage_memory_closeout(
    *,
    closeout_packet: Mapping[str, Any],
    study_root: Path,
    workspace_root: Path,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    idempotency_key = _required_text("idempotency_key", closeout_packet.get("idempotency_key"))
    receipt_path = memory_write_router_receipt_path(
        study_root=resolved_study_root,
        idempotency_key=idempotency_key,
    )
    if apply and receipt_path.exists():
        existing = _read_json(receipt_path)
        if existing:
            return {**existing, "idempotent_replay": True, "receipt_ref": str(receipt_path)}

    proposed = _mapping_list(closeout_packet.get("proposed_writes"))
    accepted, rejected = _route_proposed_writes(
        proposed_writes=proposed,
        study_root=resolved_study_root,
        workspace_root=resolved_workspace_root,
        apply=apply,
    )
    source_fingerprint = _fingerprint({"idempotency_key": idempotency_key, "accepted": accepted, "rejected": rejected})
    receipt = {
        "surface": MEMORY_ROUTER_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", closeout_packet.get("study_id")),
        "stage": _validate_stage(_text(closeout_packet.get("stage"))),
        "input_refs": _text_list(closeout_packet.get("source_refs")) or _text_list(closeout_packet.get("input_refs")),
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "idempotency_key": idempotency_key,
        "apply": apply,
        "accepted_writes": accepted,
        "rejected_writes": rejected,
        "status": "applied" if apply else "dry_run",
    }
    if apply:
        _write_json(receipt_path, receipt)
    return {**receipt, "receipt_ref": str(receipt_path)}


def build_stage_recall_index(*, study_id: str, study_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    root = resolved_study_root / STAGE_KNOWLEDGE_ROOT
    packet_refs = [str(path) for path in sorted(root.glob("*/latest.json")) if path.is_file()]
    receipt_refs = [str(path) for path in sorted((root / "memory_write_router_receipts").glob("*.json"))]
    source_fingerprint = _fingerprint({"packet_refs": packet_refs, "receipt_refs": receipt_refs})
    return {
        "surface": RECALL_INDEX_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": "all",
        "input_refs": [*packet_refs, *receipt_refs],
        "stage_knowledge_packet_refs": packet_refs,
        "memory_write_router_receipt_refs": receipt_refs,
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "idempotency_key": f"stage_recall_index:{_required_text('study_id', study_id)}:{source_fingerprint}",
    }


def materialize_stage_recall_index(*, study_id: str, study_root: Path) -> dict[str, Any]:
    index = build_stage_recall_index(study_id=study_id, study_root=study_root)
    path = stage_recall_index_path(study_root=Path(study_root))
    _write_json(path, index)
    return {**index, "artifact_path": str(path)}


def _packet_contract(surface: str) -> dict[str, Any]:
    return {
        "surface": surface,
        "required_fields": list(COMMON_PACKET_FIELDS),
        "authority_boundary": _authority_boundary(),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "role": "stage_context_or_router_contract",
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_replace_controller_decision": False,
        "can_replace_evidence_ledger": False,
        "can_promote_quest_local_literature_to_workspace_authority": False,
        "can_use_chat_as_authority": False,
    }


def _stage_input_refs(*, study_root: Path, workspace_root: Path, quest_root: Path | None) -> list[dict[str, Any]]:
    refs = [
        _file_ref("study_charter", study_root / "artifacts" / "controller" / "study_charter.json"),
        _file_ref("controller_decision", study_root / "artifacts" / "controller_decisions" / "latest.json"),
        _file_ref("evidence_ledger", study_root / "paper" / "evidence_ledger.json"),
        _first_existing_file_ref(
            "review_ledger",
            (
                study_root / "paper" / "review" / "review_ledger.json",
                study_root / "paper" / "review_ledger.json",
            ),
        ),
        _file_ref("claim_evidence_map", study_root / "paper" / "claim_evidence_map.json"),
        _file_ref("display_to_claim_map", study_root / "paper" / "display_to_claim_map.json"),
        _file_ref("study_reference_context", study_root / "artifacts" / "reference_context" / "latest.json"),
        _status_ref("portfolio_memory", portfolio_memory.portfolio_memory_status(workspace_root=workspace_root)),
        _status_ref("workspace_literature", workspace_literature.workspace_literature_status(workspace_root=workspace_root)),
        _file_ref("literature_provider_runtime", study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json"),
        _file_ref("literature_intelligence_os", study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json"),
    ]
    if quest_root is not None:
        resolved_quest_root = Path(quest_root).expanduser().resolve()
        refs.extend(
            [
                _dir_ref("quest_literature", resolved_quest_root / "literature"),
                _file_ref("quest_references_bib", resolved_quest_root / "paper" / "references.bib"),
                _file_ref(
                    "quest_reference_coverage_report",
                    resolved_quest_root / "paper" / "reference_coverage_report.json",
                ),
            ]
        )
    return refs


def _file_ref(ref_id: str, path: Path) -> dict[str, Any]:
    payload = _read_json(path) if path.exists() and path.suffix == ".json" else {}
    return {
        "ref_id": ref_id,
        "path": str(path),
        "exists": path.exists(),
        "kind": "file",
        "status": _status_from_payload(payload) if payload else ("present" if path.exists() else "missing"),
    }


def _first_existing_file_ref(ref_id: str, paths: Sequence[Path]) -> dict[str, Any]:
    for path in paths:
        if path.exists():
            return _file_ref(ref_id, path)
    return _file_ref(ref_id, paths[0])


def _dir_ref(ref_id: str, path: Path) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "path": str(path),
        "exists": path.exists(),
        "kind": "directory",
        "status": "present" if path.exists() else "missing",
    }


def _status_ref(ref_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "path": _text(payload.get("portfolio_memory_root"))
        or _text(payload.get("workspace_literature_root"))
        or _text(payload.get("workspace_root")),
        "exists": bool(payload.get("portfolio_memory_exists") or payload.get("workspace_literature_exists")),
        "kind": "read_model",
        "status": "present" if payload else "missing",
        "payload": dict(payload),
    }


def _missing_reasons(*, input_refs: Sequence[Mapping[str, Any]], stage: str) -> list[str]:
    required_by_stage = {
        "scout": ("portfolio_memory", "workspace_literature"),
        "idea": ("portfolio_memory", "workspace_literature", "study_reference_context"),
        "analysis-campaign": ("evidence_ledger", "review_ledger", "controller_decision"),
        "review": ("evidence_ledger", "review_ledger", "claim_evidence_map", "study_reference_context"),
    }
    refs_by_id = {_text(ref.get("ref_id")): ref for ref in input_refs}
    missing = []
    for ref_id in required_by_stage.get(stage, ()):
        ref = refs_by_id.get(ref_id, {})
        if ref.get("exists") is not True:
            missing.append(f"missing_ref:{ref_id}")
    return missing


def _stage_obligations(stage: str) -> dict[str, list[str]]:
    return {key: list(value) for key, value in STAGE_OBLIGATIONS.get(stage, {}).items()}


def _high_signal_memory(*, input_refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    portfolio_ref = next((ref for ref in input_refs if ref.get("ref_id") == "portfolio_memory"), {})
    payload = portfolio_ref.get("payload") if isinstance(portfolio_ref.get("payload"), Mapping) else {}
    assets = payload.get("assets") if isinstance(payload, Mapping) else []
    return [
        {
            "asset_id": _text(asset.get("asset_id")),
            "status": _text(asset.get("status")),
            "path": _text(asset.get("absolute_path")),
        }
        for asset in _mapping_list(assets)
    ]


def _literature_gaps(*, input_refs: Sequence[Mapping[str, Any]]) -> list[str]:
    literature_ref = next((ref for ref in input_refs if ref.get("ref_id") == "workspace_literature"), {})
    payload = literature_ref.get("payload") if isinstance(literature_ref.get("payload"), Mapping) else {}
    if not payload:
        return ["workspace_literature_status_missing"]
    gaps = []
    if int(payload.get("record_count") or 0) == 0:
        gaps.append("workspace_literature_registry_empty")
    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), Mapping) else {}
    gaps.extend(_text_list(coverage.get("high_priority_missing")))
    return _dedupe_text(gaps)


def _failed_paths(*, input_refs: Sequence[Mapping[str, Any]]) -> list[str]:
    decision_ref = next((ref for ref in input_refs if ref.get("ref_id") == "controller_decision"), {})
    payload = _read_json(Path(_text(decision_ref.get("path"))))
    refs = _text_list(payload.get("failed_path_refs"))
    analysis_decision = payload.get("analysis_direction_decision") if isinstance(payload, Mapping) else {}
    if isinstance(analysis_decision, Mapping):
        refs.extend(_text_list(analysis_decision.get("failed_path_evidence_refs")))
    return _dedupe_text(refs)


def _citation_readiness(*, input_refs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    provider_ref = next((ref for ref in input_refs if ref.get("ref_id") == "literature_provider_runtime"), {})
    provider_payload = _read_json(Path(_text(provider_ref.get("path"))))
    return {
        "provider_runtime_status": _status_from_payload(provider_payload) or _text(provider_ref.get("status")),
        "citation_ledger_refs": _text_list(provider_payload.get("citation_ledger_refs")),
        "stale_refs": _text_list(provider_payload.get("stale_refs")),
    }


def _claim_boundary(*, input_refs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    charter_ref = next((ref for ref in input_refs if ref.get("ref_id") == "study_charter"), {})
    charter = _read_json(Path(_text(charter_ref.get("path"))))
    boundary = charter.get("claim_boundary") if isinstance(charter.get("claim_boundary"), Mapping) else {}
    return dict(boundary)


def _proposed_writes(normalized: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    destinations = {
        "reusable_lessons": "workspace_research_memory_proposal",
        "citation_gaps": "literature_provider_repair_request",
        "failed_paths": "failed_path_history_or_controller_decision",
        "reference_role_updates": "study_reference_context_update_request",
        "evidence_ledger_updates": "evidence_ledger_repair_request",
        "review_ledger_updates": "review_ledger_repair_request",
        "controller_decision_requests": "controller_decision_request",
        "human_gate_requests": "human_gate_request",
    }
    proposed: list[dict[str, Any]] = []
    for key, destination in destinations.items():
        for index, item in enumerate(normalized.get(key, [])):
            proposed.append(
                {
                    "write_id": _text(item.get("write_id")) or f"{key}:{index + 1}:{_fingerprint(item)}",
                    "source_category": key,
                    "destination": destination,
                    "payload": dict(item),
                    "source_refs": _text_list(item.get("source_refs")),
                }
            )
    return proposed


def _route_proposed_writes(
    *,
    proposed_writes: Sequence[Mapping[str, Any]],
    study_root: Path,
    workspace_root: Path,
    apply: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for write in proposed_writes:
        destination = _text(write.get("destination"))
        payload = _mapping(write.get("payload"))
        write_id = _text(write.get("write_id")) or _fingerprint(write)
        if destination == "workspace_research_memory_proposal" and _text(payload.get("scope")) == "study_specific_claim":
            rejected.append({**dict(write), "reason": "study_specific_claim_not_workspace_memory"})
            continue
        target_path = _target_path_for_destination(destination, study_root=study_root, workspace_root=workspace_root)
        if not target_path:
            rejected.append({**dict(write), "reason": "unsupported_destination"})
            continue
        accepted_item = {**dict(write), "target_path": str(target_path)}
        accepted.append(accepted_item)
        if apply:
            _append_jsonl_once(target_path, {**accepted_item, "write_id": write_id}, identity=write_id)
    return accepted, rejected


def _target_path_for_destination(destination: str, *, study_root: Path, workspace_root: Path) -> Path | None:
    targets = {
        "workspace_research_memory_proposal": workspace_root
        / "portfolio"
        / "research_memory"
        / "proposals"
        / "stage_memory_updates.jsonl",
        "literature_provider_repair_request": study_root
        / "artifacts"
        / "literature_provider"
        / "repair_requests"
        / "stage_memory_closeout.jsonl",
        "failed_path_history_or_controller_decision": study_root
        / "artifacts"
        / "controller"
        / "failed_path_history.jsonl",
        "study_reference_context_update_request": study_root
        / "artifacts"
        / "reference_context"
        / "update_requests.jsonl",
        "evidence_ledger_repair_request": study_root / "artifacts" / "controller" / "evidence_ledger_repair_requests.jsonl",
        "review_ledger_repair_request": study_root / "artifacts" / "controller" / "review_ledger_repair_requests.jsonl",
        "controller_decision_request": study_root / "artifacts" / "controller_decisions" / "stage_closeout_requests.jsonl",
        "human_gate_request": study_root / "artifacts" / "controller" / "human_gate_requests.jsonl",
    }
    return targets.get(destination)


def _append_jsonl_once(path: Path, payload: Mapping[str, Any], *, identity: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            existing = json.loads(raw_line)
            if isinstance(existing, dict) and _text(existing.get("write_id")) == identity:
                return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _validate_stage(stage: str) -> str:
    resolved = _text(stage)
    if resolved not in EXPLORATORY_STAGES and resolved != "all":
        raise ValueError(f"unsupported stage for stage knowledge plane: {resolved}")
    return resolved


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_text(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys([item for item in items if item]))


def _status_from_payload(payload: Mapping[str, Any]) -> str:
    return _text(payload.get("status") or payload.get("readiness_status") or payload.get("state"))


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _safe_stage(stage: str) -> str:
    return _text(stage).replace("/", "_")


def _safe_key(key: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in key)[:180]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = [
    "EXPLORATORY_STAGES",
    "STAGE_OBLIGATIONS",
    "build_stage_knowledge_packet",
    "build_stage_recall_index",
    "materialize_stage_knowledge_packet",
    "materialize_stage_memory_closeout_packet",
    "materialize_stage_recall_index",
    "memory_write_router_receipt_path",
    "normalize_stage_memory_closeout_packet",
    "route_stage_memory_closeout",
    "stage_knowledge_packet_path",
    "stage_knowledge_plane_contract",
    "stage_memory_closeout_packet_path",
    "stage_recall_index_path",
]
