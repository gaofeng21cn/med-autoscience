from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers import portfolio_memory, workspace_literature
from med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_cards import (
    normalize_publication_route_card as _normalize_publication_route_card,
)
from med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_cards import (
    publication_seed_blockers as _publication_seed_blockers,
)
from med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_writeback import sync_accepted_publication_route_memory_cards as _sync_route_memory_cards
from med_autoscience.stage_knowledge_contract import (
    EXPLORATORY_STAGES,
    KNOWLEDGE_PACKET_SURFACE,
    MEMORY_CLOSEOUT_SURFACE,
    MEMORY_ROUTER_SURFACE,
    PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE,
    PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
    PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
    PUBLICATION_ROUTE_MEMORY_STAGES,
    RECALL_INDEX_SURFACE,
    SCHEMA_VERSION,
    STAGE_KNOWLEDGE_ROOT,
    STAGE_OBLIGATIONS,
    TYPED_CLOSEOUT_CATEGORIES,
    authority_boundary,
    stage_knowledge_plane_contract,
)

PUBLICATION_ROUTE_MEMORY_ROOT = Path("portfolio/research_memory/publication_route_memory")
PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF = Path(
    "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
)
PUBLICATION_ROUTE_MEMORY_SELECTION_LIMIT = 3


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


def paper_soak_memory_apply_proof_path(*, study_root: Path) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / STAGE_KNOWLEDGE_ROOT
        / "paper_soak_memory_apply_proof"
        / "latest.json"
    )


def publication_route_memory_pack_root(*, workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / PUBLICATION_ROUTE_MEMORY_ROOT


def publication_route_memory_pack_path(*, workspace_root: Path) -> Path:
    return publication_route_memory_pack_root(workspace_root=workspace_root) / "memory_pack.json"


def publication_route_memory_apply_receipt_path(*, workspace_root: Path, idempotency_key: str) -> Path:
    return (
        publication_route_memory_pack_root(workspace_root=workspace_root)
        / "migration_receipts"
        / f"{_safe_key(idempotency_key)}.json"
    )


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
        "publication_route_memory_refs": select_publication_route_memory_refs(
            workspace_root=resolved_workspace_root,
            stage=resolved_stage,
        ),
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


def apply_publication_route_memory_seed_fixture(
    *,
    workspace_root: Path,
    seed_fixture_path: Path,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_fixture_path = Path(seed_fixture_path).expanduser().resolve()
    fixture = _read_json(resolved_fixture_path)
    seed_cards = _mapping_list(fixture.get("seed_cards"))
    source_fingerprint = _fingerprint({"fixture_path": str(resolved_fixture_path), "seed_cards": seed_cards})
    idempotency_key = f"publication_route_memory_seed_apply:{source_fingerprint}"
    receipt_path = publication_route_memory_apply_receipt_path(
        workspace_root=resolved_workspace_root,
        idempotency_key=idempotency_key,
    )
    receipt_ref = str(receipt_path)
    if apply and receipt_path.exists():
        existing = _read_json(receipt_path)
        if existing:
            return {**existing, "idempotent_replay": True, "receipt_ref": str(receipt_path)}

    pack_path = publication_route_memory_pack_path(workspace_root=resolved_workspace_root)
    typed_blockers = _publication_seed_blockers(fixture=fixture, seed_cards=seed_cards)
    accepted_cards = [] if typed_blockers else [_normalize_publication_route_card(card) for card in seed_cards]
    receipt = {
        "surface": PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": "workspace",
        "stage": "all",
        "memory_family": "publication_route_memory",
        "status": "blocked" if typed_blockers else ("applied" if apply else "dry_run"),
        "apply": apply,
        "input_refs": [str(resolved_fixture_path)],
        "source_refs": [
            {
                "ref_kind": "repo_path",
                "ref": str(PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF),
                "resolved_path": str(resolved_fixture_path),
                "role": "repo_source_seed_fixture",
            }
        ],
        "source_fingerprint": source_fingerprint,
        "idempotency_key": idempotency_key,
        "accepted_memory_ids": [card["memory_id"] for card in accepted_cards],
        "rejected_cards": [],
        "typed_blockers": typed_blockers,
        "memory_pack_ref": str(pack_path),
        "receipt_ref": receipt_ref,
        "authority_boundary": _authority_boundary(),
    }
    if apply:
        if not typed_blockers:
            pack = _publication_route_memory_pack(cards=accepted_cards, receipt=receipt)
            receipt["memory_pack_fingerprint"] = pack["source_fingerprint"]
            _write_json(pack_path, pack)
        _write_json(receipt_path, receipt)
    return {**receipt, "receipt_ref": str(receipt_path)}


def select_publication_route_memory_refs(
    *,
    workspace_root: Path,
    stage: str,
    route_family_tags: Sequence[str] | None = None,
    limit: int = PUBLICATION_ROUTE_MEMORY_SELECTION_LIMIT,
) -> list[dict[str, Any]]:
    resolved_stage = _validate_publication_route_memory_stage(stage)
    pack_path = publication_route_memory_pack_path(workspace_root=workspace_root)
    pack = _read_json(pack_path)
    cards = _mapping_list(pack.get("cards"))
    route_tags = set(_text_list(list(route_family_tags or [])))
    selected: list[dict[str, Any]] = []
    for card in cards:
        stages = set(_text_list(card.get("stage_applicability")))
        route_family = _text(card.get("route_family"))
        if resolved_stage not in stages:
            continue
        if route_tags and route_family not in route_tags:
            continue
        selected.append(
            {
                "ref_kind": "workspace_memory_card_ref",
                "memory_id": _text(card.get("memory_id")),
                "route_family": route_family,
                "title": _text(card.get("title")),
                "route_memory_summary": _text(card.get("prose_summary")),
                "stage_applicability": _text_list(card.get("stage_applicability")),
                "memory_pack_ref": str(pack_path),
                "source_receipt_ref": _text(card.get("source_receipt_ref")),
                "authority_boundary": "context_only_not_publication_authority",
            }
        )
        if len(selected) >= limit:
            break
    return selected


def normalize_stage_memory_closeout_packet(
    *,
    study_id: str,
    stage: str,
    closeout_payload: Mapping[str, Any],
    study_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    resolved_stage = _validate_stage(stage)
    normalized, typed_blockers = _normalize_typed_closeout(closeout_payload)
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
        "typed_blockers": typed_blockers,
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
    memory_pack_receipt_path = (
        publication_route_memory_pack_root(workspace_root=resolved_workspace_root)
        / "writeback_receipts"
        / f"{_safe_key(idempotency_key)}.json"
    )
    if apply and receipt_path.exists():
        existing = _read_json(receipt_path)
        if existing:
            return {**existing, "idempotent_replay": True, "receipt_ref": str(receipt_path)}

    receipt_refs = [str(receipt_path), str(memory_pack_receipt_path)]
    typed_blockers = _mapping_list(closeout_packet.get("typed_blockers"))
    if typed_blockers:
        receipt = _memory_router_receipt(
            closeout_packet=closeout_packet,
            idempotency_key=idempotency_key,
            apply=apply,
            accepted=[],
            rejected=[],
            typed_blockers=typed_blockers,
            status="blocked",
        )
        receipt["receipt_refs"] = receipt_refs
        if apply:
            _write_json(receipt_path, receipt)
            _write_json(memory_pack_receipt_path, receipt)
        return {**receipt, "receipt_ref": str(receipt_path)}

    proposed = _mapping_list(closeout_packet.get("proposed_writes"))
    accepted, rejected = _route_proposed_writes(
        proposed_writes=proposed,
        study_root=resolved_study_root,
        workspace_root=resolved_workspace_root,
        router_receipt_path=receipt_path,
        apply=apply,
    )
    receipt = _memory_router_receipt(
        closeout_packet=closeout_packet,
        idempotency_key=idempotency_key,
        apply=apply,
        accepted=accepted,
        rejected=rejected,
        typed_blockers=[],
        status="applied" if apply else "dry_run",
    )
    receipt["receipt_refs"] = receipt_refs
    if apply:
        _sync_route_memory_cards(receipt=receipt, pack_path=publication_route_memory_pack_path(workspace_root=resolved_workspace_root), receipt_ref=str(receipt_path), apply=apply)
        _write_json(receipt_path, receipt)
        _write_json(memory_pack_receipt_path, receipt)
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


def build_paper_soak_memory_apply_proof(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_stage = _validate_publication_route_memory_stage(stage)
    stage_packet_path = stage_knowledge_packet_path(study_root=resolved_study_root, stage=resolved_stage)
    stage_packet = _read_json(stage_packet_path)
    route_memory_refs = _readonly_route_memory_refs(
        stage_packet.get("publication_route_memory_refs")
        or select_publication_route_memory_refs(workspace_root=resolved_workspace_root, stage=resolved_stage)
    )
    closeout_proposal_refs = _closeout_proposal_refs(study_root=resolved_study_root)
    router_receipt_refs = _router_receipt_refs(study_root=resolved_study_root)
    writeback_receipt_refs = _workspace_writeback_receipt_refs(workspace_root=resolved_workspace_root)
    sidecar_receipt_refs = _sidecar_dispatch_receipt_refs(
        workspace_root=resolved_workspace_root,
        study_id=_required_text("study_id", study_id),
    )
    opl_aion_refs = _opl_aion_readonly_receipt_refs(
        router_receipt_refs=router_receipt_refs,
        writeback_receipt_refs=writeback_receipt_refs,
        sidecar_receipt_refs=sidecar_receipt_refs,
    )
    missing = _paper_soak_proof_missing_reasons(
        route_memory_refs=route_memory_refs,
        closeout_proposal_refs=closeout_proposal_refs,
        router_receipt_refs=router_receipt_refs,
        opl_aion_refs=opl_aion_refs,
    )
    input_refs = _dedupe_text(
        [
            str(stage_packet_path),
            *[ref["ref"] for ref in closeout_proposal_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in router_receipt_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in writeback_receipt_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in sidecar_receipt_refs if _text(ref.get("ref"))],
        ]
    )
    source_fingerprint = _fingerprint(
        {
            "stage": resolved_stage,
            "route_memory_refs": route_memory_refs,
            "closeout_proposal_refs": closeout_proposal_refs,
            "router_receipt_refs": router_receipt_refs,
            "writeback_receipt_refs": writeback_receipt_refs,
            "sidecar_receipt_refs": sidecar_receipt_refs,
        }
    )
    return {
        "surface": PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": resolved_stage,
        "status": "ready" if not missing else "missing",
        "input_refs": input_refs,
        "missing_reasons": missing,
        "stage_entry": {
            "stage_knowledge_packet_ref": str(stage_packet_path),
            "publication_route_memory_refs": route_memory_refs,
            "route_memory_ref_count": len(route_memory_refs),
        },
        "typed_closeout_writeback_proposals": closeout_proposal_refs,
        "mas_router_receipt_refs": router_receipt_refs,
        "workspace_writeback_receipt_refs": writeback_receipt_refs,
        "opl_aion_readonly_receipt_refs": opl_aion_refs,
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "read_only_display_policy": {
            "projection_owner": "MedAutoScience",
            "consumer_role": "OPL/Aion read-only display",
            "repo_tracks_real_paper_artifacts": False,
            "repo_tracks_memory_body": False,
            "repo_tracks_receipt_instances": False,
            "can_authorize_publication_quality": False,
            "can_write_memory_body": False,
            "can_write_study_truth": False,
            "can_write_artifact_authority": False,
        },
        "idempotency_key": (
            f"paper_soak_memory_apply_proof:{_required_text('study_id', study_id)}:"
            f"{resolved_stage}:{source_fingerprint}"
        ),
    }


def materialize_paper_soak_memory_apply_proof(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    proof = build_paper_soak_memory_apply_proof(
        study_id=study_id,
        stage=stage,
        study_root=study_root,
        workspace_root=workspace_root,
    )
    path = paper_soak_memory_apply_proof_path(study_root=Path(study_root))
    _write_json(path, proof)
    return {**proof, "artifact_path": str(path)}


def _authority_boundary() -> dict[str, Any]:
    return authority_boundary()


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


def _normalize_typed_closeout(closeout_payload: Mapping[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    normalized = {category: _mapping_list(closeout_payload.get(category)) for category in TYPED_CLOSEOUT_CATEGORIES}
    typed_count = sum(len(items) for items in normalized.values())
    blockers: list[dict[str, Any]] = []
    if typed_count == 0:
        blockers.append(
            {
                "blocker_id": "typed_closeout_missing",
                "reason": "stage closeout requires typed category arrays",
                "owner_target": "stage_closeout_author",
            }
        )
    for key, value in closeout_payload.items():
        if key in TYPED_CLOSEOUT_CATEGORIES:
            continue
        if key in {"idempotency_key", "source_refs"}:
            continue
        if isinstance(value, str) and _text(value):
            blockers.append(
                {
                    "blocker_id": f"free_text_field:{key}",
                    "reason": "free-text-only closeout fields are not parsed by memory router",
                    "field": key,
                    "owner_target": "stage_closeout_author",
                }
            )
    return normalized, blockers


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
        "claim_boundary_decisions": "claim_boundary_controller_decision_request",
    }
    proposed: list[dict[str, Any]] = []
    for key, destination in destinations.items():
        for index, item in enumerate(normalized.get(key, [])):
            owner_target = _owner_target_for_destination(destination)
            proposed.append(
                {
                    "write_id": _text(item.get("write_id")) or f"{key}:{index + 1}:{_fingerprint(item)}",
                    "source_category": key,
                    "destination": destination,
                    "owner_target": owner_target,
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
    router_receipt_path: Path,
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
        accepted_item = {
            **dict(write),
            "owner_target": _text(write.get("owner_target")) or _owner_target_for_destination(destination),
            "target_path": str(target_path),
        }
        if destination == "workspace_research_memory_proposal":
            accepted_item["proposal_ref"] = str(target_path)
            accepted_item["receipt_ref"] = str(router_receipt_path)
        accepted.append(accepted_item)
        if apply:
            _append_jsonl_once(target_path, {**accepted_item, "write_id": write_id}, identity=write_id)
    return accepted, rejected

def _target_path_for_destination(destination: str, *, study_root: Path, workspace_root: Path) -> Path | None:
    targets = {
        "workspace_research_memory_proposal": publication_route_memory_pack_root(workspace_root=workspace_root)
        / "writeback_proposals"
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
        "claim_boundary_controller_decision_request": study_root
        / "artifacts"
        / "controller_decisions"
        / "claim_boundary_requests.jsonl",
        "human_gate_request": study_root / "artifacts" / "controller" / "human_gate_requests.jsonl",
    }
    return targets.get(destination)


def _owner_target_for_destination(destination: str) -> str:
    owner_targets = {
        "workspace_research_memory_proposal": "workspace_memory_owner",
        "literature_provider_repair_request": "literature_provider",
        "failed_path_history_or_controller_decision": "mas_controller",
        "study_reference_context_update_request": "reference_context_owner",
        "evidence_ledger_repair_request": "evidence_ledger_owner",
        "review_ledger_repair_request": "review_ledger_owner",
        "controller_decision_request": "mas_controller",
        "claim_boundary_controller_decision_request": "mas_controller",
        "human_gate_request": "human_gate_owner",
    }
    return owner_targets.get(destination, "unsupported_owner")


def _memory_router_receipt(
    *,
    closeout_packet: Mapping[str, Any],
    idempotency_key: str,
    apply: bool,
    accepted: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
    typed_blockers: Sequence[Mapping[str, Any]],
    status: str,
) -> dict[str, Any]:
    source_fingerprint = _fingerprint(
        {
            "idempotency_key": idempotency_key,
            "accepted": list(accepted),
            "rejected": list(rejected),
            "typed_blockers": list(typed_blockers),
        }
    )
    return {
        "surface": MEMORY_ROUTER_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", closeout_packet.get("study_id")),
        "stage": _validate_stage(_text(closeout_packet.get("stage"))),
        "memory_family": "publication_route_memory",
        "input_refs": _text_list(closeout_packet.get("source_refs")) or _text_list(closeout_packet.get("input_refs")),
        "source_fingerprint": source_fingerprint,
        "authority_boundary": _authority_boundary(),
        "idempotency_key": idempotency_key,
        "apply": apply,
        "accepted_writes": [dict(item) for item in accepted],
        "rejected_writes": [dict(item) for item in rejected],
        "typed_blockers": [dict(item) for item in typed_blockers],
        "status": status,
        "writeback_receipt_locator_ref": "portfolio/research_memory/publication_route_memory/writeback_receipts",
    }


def _readonly_route_memory_refs(refs: object) -> list[dict[str, Any]]:
    sanitized = []
    for ref in _mapping_list(refs):
        sanitized.append(
            {
                "ref_kind": _text(ref.get("ref_kind")) or "workspace_memory_card_ref",
                "memory_id": _text(ref.get("memory_id")),
                "route_family": _text(ref.get("route_family")),
                "route_memory_summary": _text(ref.get("route_memory_summary")),
                "stage_applicability": _text_list(ref.get("stage_applicability")),
                "memory_pack_ref": _text(ref.get("memory_pack_ref")),
                "source_receipt_ref": _text(ref.get("source_receipt_ref")),
                "authority_boundary": _text(ref.get("authority_boundary"))
                or "context_only_not_publication_authority",
            }
        )
    return sanitized


def _closeout_proposal_refs(*, study_root: Path) -> list[dict[str, Any]]:
    refs = []
    root = study_root / STAGE_KNOWLEDGE_ROOT
    for path in sorted(root.glob("*/closeouts/*.json")):
        payload = _read_json(path)
        proposed = _mapping_list(payload.get("proposed_writes"))
        refs.append(
            {
                "ref_kind": "stage_memory_closeout_packet",
                "ref": str(path),
                "stage": _text(payload.get("stage")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "source_fingerprint": _text(payload.get("source_fingerprint")),
                "proposed_write_count": len(proposed),
                "proposed_write_refs": [
                    {
                        "write_id": _text(item.get("write_id")),
                        "source_category": _text(item.get("source_category")),
                        "destination": _text(item.get("destination")),
                        "owner_target": _text(item.get("owner_target")),
                    }
                    for item in proposed
                ],
                "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
                "body_included": False,
            }
        )
    return refs


def _router_receipt_refs(*, study_root: Path) -> list[dict[str, Any]]:
    refs = []
    receipt_root = study_root / STAGE_KNOWLEDGE_ROOT / "memory_write_router_receipts"
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        refs.append(
            {
                "ref_kind": "memory_write_router_receipt",
                "ref": str(path),
                "stage": _text(payload.get("stage")),
                "status": _text(payload.get("status")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "accepted_write_refs": _receipt_write_refs(payload.get("accepted_writes")),
                "rejected_write_refs": _receipt_write_refs(payload.get("rejected_writes")),
                "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
                "body_included": False,
            }
        )
    return refs


def _receipt_write_refs(value: object) -> list[dict[str, Any]]:
    return [
        {
            "write_id": _text(item.get("write_id")),
            "destination": _text(item.get("destination")),
            "owner_target": _text(item.get("owner_target")),
            "status": "rejected" if _text(item.get("reason")) else "accepted",
            "reason": _text(item.get("reason")),
            "proposal_ref": _text(item.get("proposal_ref")),
            "receipt_ref": _text(item.get("receipt_ref")),
        }
        for item in _mapping_list(value)
    ]


def _workspace_writeback_receipt_refs(*, workspace_root: Path) -> list[dict[str, Any]]:
    refs = []
    receipt_root = publication_route_memory_pack_root(workspace_root=workspace_root) / "writeback_receipts"
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        refs.append(
            {
                "ref_kind": "publication_route_memory_writeback_receipt",
                "ref": str(path),
                "status": _text(payload.get("status")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "accepted_count": len(_mapping_list(payload.get("accepted_writes"))),
                "rejected_count": len(_mapping_list(payload.get("rejected_writes"))),
                "body_included": False,
            }
        )
    return refs


def _sidecar_dispatch_receipt_refs(*, workspace_root: Path, study_id: str) -> list[dict[str, Any]]:
    refs = []
    receipt_root = workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts"
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        dispatch = payload.get("dispatch") if isinstance(payload.get("dispatch"), Mapping) else {}
        receipt_study_id = _text(dispatch.get("study_id"))
        if receipt_study_id and receipt_study_id != study_id:
            continue
        refs.append(
            {
                "ref_kind": "mas_family_sidecar_dispatch_receipt",
                "ref": str(path),
                "task_id": _text(payload.get("task_id")),
                "task_kind": _text(payload.get("task_kind")),
                "accepted": payload.get("accepted") is True,
                "reason": _text(payload.get("reason")),
                "study_id": receipt_study_id,
                "body_included": False,
            }
        )
    return refs


def _opl_aion_readonly_receipt_refs(
    *,
    router_receipt_refs: Sequence[Mapping[str, Any]],
    writeback_receipt_refs: Sequence[Mapping[str, Any]],
    sidecar_receipt_refs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    refs = []
    for source in (*router_receipt_refs, *writeback_receipt_refs, *sidecar_receipt_refs):
        ref = _text(source.get("ref"))
        if not ref:
            continue
        refs.append(
            {
                "ref_kind": _text(source.get("ref_kind")),
                "ref": ref,
                "status": _text(source.get("status")) or ("accepted" if source.get("accepted") is True else ""),
                "display_role": "receipt_ref_only",
                "consumer": "OPL/Aion",
                "body_included": False,
                "authority_boundary": "read_only_display_not_mas_truth_authority",
            }
        )
    return refs


def _paper_soak_proof_missing_reasons(
    *,
    route_memory_refs: Sequence[Mapping[str, Any]],
    closeout_proposal_refs: Sequence[Mapping[str, Any]],
    router_receipt_refs: Sequence[Mapping[str, Any]],
    opl_aion_refs: Sequence[Mapping[str, Any]],
) -> list[str]:
    missing = []
    if not route_memory_refs:
        missing.append("missing_stage_entry_route_memory_refs")
    if not closeout_proposal_refs:
        missing.append("missing_typed_closeout_writeback_proposal")
    if not router_receipt_refs:
        missing.append("missing_mas_memory_router_receipt_ref")
    if not opl_aion_refs:
        missing.append("missing_opl_aion_readonly_receipt_refs")
    return missing


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


def _publication_route_memory_pack(
    *,
    cards: Sequence[Mapping[str, Any]],
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_ref = _text(receipt.get("receipt_ref"))
    normalized_cards = []
    for card in cards:
        normalized_cards.append(
            {
                **dict(card),
                "source_receipt_ref": receipt_ref,
                "authority_boundary": "context_only_not_publication_authority",
            }
        )
    return {
        "surface": PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": "workspace",
        "stage": "all",
        "memory_family": "publication_route_memory",
        "owner": "MedAutoScience",
        "state": "workspace_runtime_memory_pack",
        "input_refs": [receipt_ref] if receipt_ref else [],
        "cards": normalized_cards,
        "card_count": len(normalized_cards),
        "source_apply_receipt_ref": receipt_ref,
        "idempotency_key": _text(receipt.get("idempotency_key")) or f"publication_route_memory_pack:{_fingerprint(normalized_cards)}",
        "source_fingerprint": _fingerprint(normalized_cards),
        "authority_boundary": _authority_boundary(),
    }

def _validate_stage(stage: str) -> str:
    resolved = _text(stage)
    if resolved not in PUBLICATION_ROUTE_MEMORY_STAGES and resolved != "all":
        raise ValueError(f"unsupported stage for stage knowledge plane: {resolved}")
    return resolved


def _validate_publication_route_memory_stage(stage: str) -> str:
    resolved = _text(stage)
    if resolved not in PUBLICATION_ROUTE_MEMORY_STAGES:
        raise ValueError(f"unsupported publication route memory stage: {resolved}")
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
    "PUBLICATION_ROUTE_MEMORY_ROOT",
    "PUBLICATION_ROUTE_MEMORY_STAGES",
    "STAGE_OBLIGATIONS",
    "apply_publication_route_memory_seed_fixture",
    "build_paper_soak_memory_apply_proof",
    "build_stage_knowledge_packet",
    "build_stage_recall_index",
    "materialize_paper_soak_memory_apply_proof",
    "materialize_stage_knowledge_packet",
    "materialize_stage_memory_closeout_packet",
    "materialize_stage_recall_index",
    "memory_write_router_receipt_path",
    "normalize_stage_memory_closeout_packet",
    "paper_soak_memory_apply_proof_path",
    "publication_route_memory_apply_receipt_path",
    "publication_route_memory_pack_path",
    "publication_route_memory_pack_root",
    "route_stage_memory_closeout",
    "select_publication_route_memory_refs",
    "stage_knowledge_packet_path",
    "stage_knowledge_plane_contract",
    "stage_memory_closeout_packet_path",
    "stage_recall_index_path",
]
