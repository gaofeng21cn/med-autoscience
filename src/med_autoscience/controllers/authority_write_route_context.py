from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.next_action_envelope import FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL
from med_autoscience.controllers import domain_authority_snapshot
from med_autoscience.runtime_protocol.topology import resolve_study_root_from_quest_root


def route_context_from_study_authority_surfaces(*, study_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    truth_snapshot = _read_json_object(resolved_study_root / "artifacts" / "truth" / "latest.json")
    runtime_health_snapshot = _read_json_object(
        resolved_study_root / "artifacts" / "runtime" / "health" / "latest.json"
    )
    publication_eval = _read_json_object(
        resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    )
    if not truth_snapshot or not runtime_health_snapshot:
        return {}
    context = {
        "authority_snapshot": domain_authority_snapshot.build_authority_snapshot(
            {
                "study_id": resolved_study_root.name,
                "study_truth_snapshot": truth_snapshot,
                "runtime_health_snapshot": runtime_health_snapshot,
                "publication_eval": publication_eval,
            }
        )
    }
    gate_context = _gate_clear_delivery_route_context(study_root=resolved_study_root)
    if gate_context is not None:
        context["controller_route_context"] = gate_context
    return context


def with_study_authority_route_context(
    *,
    study_root: Path,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if context is not None and context.get("authority_snapshot"):
        return context
    derived = route_context_from_study_authority_surfaces(study_root=study_root)
    if not derived:
        return context
    return {**derived, **(context or {})}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _gate_clear_delivery_route_context(*, study_root: Path) -> dict[str, Any] | None:
    gate = _current_runtime_publishability_gate(study_root=study_root)
    if gate is None:
        return None
    if str(gate.get("status") or "").strip() != "clear":
        return None
    if gate.get("blockers"):
        return None
    if gate.get("bundle_tasks_downstream_only") is not False:
        return None
    if not _gate_signature_matches_delivery(study_root=study_root, gate=gate):
        return None
    return {
        "control_surface": "gate_clearing_batch",
        "controller_action_type": "run_gate_clearing_batch",
        "work_unit_id": "submission_minimal_refresh",
        "action_family": FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
        "requires_human_confirmation": False,
        "gate_fingerprint": _text(gate.get("gate_fingerprint")),
        "work_unit_fingerprint": _text(gate.get("work_unit_fingerprint")),
        "source_eval_id": _text(gate.get("source_eval_id")),
        "publishability_gate_report_ref": _text(gate.get("latest_gate_path")),
        "authority_basis": "current_publishability_gate_clear",
    }


def _current_runtime_publishability_gate(*, study_root: Path) -> dict[str, Any] | None:
    resolved_study_root = study_root.resolve()
    workspace_root = resolved_study_root.parent.parent
    for quest_root in sorted((workspace_root / "runtime" / "quests").glob("*")):
        if not quest_root.is_dir():
            continue
        binding = resolve_study_root_from_quest_root(quest_root)
        if binding is None:
            continue
        _, bound_study_root = binding
        if bound_study_root.resolve() != resolved_study_root:
            continue
        gate = _read_json_object(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
        if gate:
            return gate
    return None


def _gate_signature_matches_delivery(*, study_root: Path, gate: dict[str, Any]) -> bool:
    gate_signature = _text(gate.get("authority_source_signature"))
    if gate_signature is None:
        return False
    if _gate_signature_matches_current_source(gate=gate, gate_signature=gate_signature):
        return True
    candidate_paths = (
        study_root / "manuscript" / "delivery_manifest.json",
        study_root / "manuscript" / "current_package" / "audit" / "submission_manifest.json",
        _paper_root_from_gate(gate) / "submission_minimal" / "audit" / "submission_manifest.json",
        study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
    )
    for path in candidate_paths:
        payload = _read_json_object(path)
        if not payload:
            continue
        for key in ("authority_source_signature", "source_signature", "delivery_source_signature"):
            if _text(payload.get(key)) == gate_signature:
                return True
    return False


def _gate_signature_matches_current_source(*, gate: dict[str, Any], gate_signature: str) -> bool:
    from med_autoscience.controllers.study_delivery_sync_parts.submission_delivery_descriptions import (
        _submission_source_relative_paths,
        _submission_source_signature,
    )

    paper_root = _paper_root_from_gate(gate)
    if not paper_root.is_absolute():
        return False
    source_root = paper_root / "submission_minimal"
    if not source_root.is_dir():
        return False
    try:
        relative_paths = _submission_source_relative_paths(paper_root=paper_root, source_root=source_root)
        source_signature = _submission_source_signature(
            paper_root=paper_root,
            source_root=source_root,
            relative_paths=relative_paths,
        )
    except (OSError, ValueError):
        return False
    return source_signature == gate_signature


def _paper_root_from_gate(gate: dict[str, Any]) -> Path:
    paper_root = _text(gate.get("paper_root"))
    return Path(paper_root) if paper_root is not None else Path()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "route_context_from_study_authority_surfaces",
    "with_study_authority_route_context",
]
