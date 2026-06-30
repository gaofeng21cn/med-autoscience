from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_candidate_package import (
    SUBMISSION_MILESTONE_KIND,
)


CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND = "concrete_non_authority_paper_delta"

PAPER_SOURCE_MARKDOWN_RELPATHS = (
    Path("paper") / "draft.md",
    Path("paper") / "build" / "review_manuscript.md",
)
PAPER_SOURCE_JSON_RELPATHS = (
    Path("paper") / "claim_evidence_map.json",
    Path("paper") / "evidence_ledger.json",
    Path("paper") / "tables" / "table_catalog.json",
    Path("paper") / "figures" / "figure_catalog.json",
    Path("paper") / "review" / "review_ledger.json",
    Path("paper") / "results_narrative_map.json",
)


def adopted_external_paper_delta_authority_boundary() -> dict[str, bool]:
    return {
        "candidate_is_authority": False,
        "authority_materialized": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
    }


def materialized_paper_facing_candidate_artifact_payload(
    *,
    kind: str,
    path: Path,
    paper_facing_candidate_delta: Mapping[str, Any],
    mission_executor_handoff: Mapping[str, Any],
    forbidden_authority_writes: Sequence[str],
    forbidden_authority_claims: Sequence[str],
) -> dict[str, Any]:
    adopted_external_delta = _adopted_external_paper_delta(
        paper_facing_candidate_delta
    )
    return {
        "surface_kind": f"paper_mission_{kind}",
        "schema_version": 1,
        "artifact_kind": kind,
        "artifact_ref": str(path),
        "study_id": paper_facing_candidate_delta.get("study_id"),
        "mission_id": paper_facing_candidate_delta.get("mission_id"),
        "status": "candidate",
        "milestone_kind": SUBMISSION_MILESTONE_KIND,
        "candidate_is_authority": False,
        "authority_materialized": False,
        "counts_as_paper_progress": True,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "route_back_evidence_ref": paper_facing_candidate_delta.get(
            "route_back_evidence_ref"
        ),
        "repair_scope": paper_facing_candidate_delta.get("repair_scope"),
        "target_stage_id": paper_facing_candidate_delta.get("target_stage_id"),
        "mission_executor_materialized": True,
        "candidate_content_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
        "source_document_refs": paper_facing_candidate_delta.get(
            "source_document_refs", []
        ),
        "source_snapshot": paper_facing_candidate_delta.get("paper_source_snapshot"),
        **adopted_external_delta,
        "candidate_content": _paper_facing_candidate_content(
            kind=kind,
            paper_facing_candidate_delta=paper_facing_candidate_delta,
            mission_executor_handoff=mission_executor_handoff,
        ),
        "authority_boundary": {
            "candidate_is_authority": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_update_current_package": False,
            "can_claim_paper_progress": False,
        },
        "forbidden_authority_writes": list(forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def materialized_paper_facing_candidate_delta(
    *,
    readback: Mapping[str, Any],
    candidate_artifact_delta: Mapping[str, Any],
    owner_decision_packet: Mapping[str, Any],
    mission_executor_handoff: Mapping[str, Any],
    forbidden_authority_writes: Sequence[str],
    forbidden_authority_claims: Sequence[str],
) -> dict[str, Any]:
    expected_outputs = [
        _mapping(item)
        for item in mission_executor_handoff.get("expected_paper_facing_outputs", [])
        if isinstance(item, Mapping)
    ]
    output_kinds = [_optional_text(item.get("kind")) for item in expected_outputs]
    output_kinds = [kind for kind in output_kinds if kind]
    handoff_status = _optional_text(mission_executor_handoff.get("status"))
    route_back_ready = handoff_status == "ready_for_mission_executor"
    owner_blocker_context = _optional_text(readback.get("consume_candidate_status")) in {
        "typed_blocker",
        "human_gate",
    }
    source_snapshot = _paper_source_snapshot(readback)
    return {
        "surface_kind": "paper_mission_paper_facing_candidate_delta",
        "schema_version": 1,
        "milestone_kind": SUBMISSION_MILESTONE_KIND,
        "study_id": readback.get("study_id"),
        "mission_id": readback.get("mission_id"),
        "delta_id": _first_text(
            candidate_artifact_delta.get("delta_id"),
            f"paper-facing-delta::{readback.get('study_id') or 'unknown-study'}",
        ),
        "status": "submission_milestone_candidate_ready"
        if not owner_blocker_context
        else "submission_milestone_candidate_ready_with_owner_blocker_context",
        "candidate_is_authority": False,
        "authority_materialized_by_this_delta": False,
        "counts_as_paper_progress": True,
        "counts_as_candidate_artifact_delta": True,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "route_back_evidence_ref": mission_executor_handoff.get(
            "route_back_evidence_ref"
        ),
        "repair_scope": mission_executor_handoff.get("repair_scope"),
        "target_stage_id": mission_executor_handoff.get("target_stage_id"),
        "mission_executor_materialized": True,
        "candidate_content_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
        "source_document_refs": source_snapshot["source_document_refs"],
        "paper_source_snapshot": source_snapshot,
        "source_candidate_artifact_delta_ref": candidate_artifact_delta.get(
            "artifact_ref"
        ),
        "owner_decision_packet_id": owner_decision_packet.get("packet_id"),
        "paper_facing_outputs": [
            _paper_facing_candidate_output(
                kind=kind,
                study_id=str(readback.get("study_id") or "unknown-study"),
                route_back_ready=route_back_ready,
            )
            for kind in output_kinds
        ],
        "consume_path": {
            "surface": "MAS authority consume path",
            "candidate_manifest_ref_required": True,
            "authority_materialized_by_this_delta": False,
            "allowed_results": [
                "accepted_owner_decision_packet",
                "route_back",
                "human_gate",
                "stable_typed_blocker",
            ],
        },
        "authority_boundary": {
            "candidate_is_authority": False,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_update_current_package": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
        "forbidden_authority_writes": list(forbidden_authority_writes),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def _paper_facing_candidate_content(
    *,
    kind: str,
    paper_facing_candidate_delta: Mapping[str, Any],
    mission_executor_handoff: Mapping[str, Any],
) -> dict[str, Any]:
    base = {
        "route_back_evidence_ref": paper_facing_candidate_delta.get(
            "route_back_evidence_ref"
        ),
        "repair_scope": paper_facing_candidate_delta.get("repair_scope"),
        "handoff_reason": mission_executor_handoff.get("handoff_reason"),
        "candidate_content_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
        "mission_executor_materialized": True,
        "source_document_refs": paper_facing_candidate_delta.get(
            "source_document_refs", []
        ),
        **_adopted_external_paper_delta(paper_facing_candidate_delta),
    }
    source_snapshot = _mapping(paper_facing_candidate_delta.get("paper_source_snapshot"))
    markdown_sources = [
        item
        for item in source_snapshot.get("markdown_sources", [])
        if isinstance(item, Mapping)
    ]
    json_sources = {
        _optional_text(item.get("relative_path")): _mapping(item)
        for item in source_snapshot.get("json_sources", [])
        if isinstance(item, Mapping) and _optional_text(item.get("relative_path"))
    }
    if kind == "manuscript_patch_plan":
        return {
            **base,
            "patch_targets": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
            ],
            "source_headings": [
                {
                    "source_ref": item.get("source_ref"),
                    "relative_path": item.get("relative_path"),
                    "headings": item.get("headings", []),
                }
                for item in markdown_sources
            ],
            "candidate_patch_operations": _candidate_patch_operations(
                paper_facing_candidate_delta=paper_facing_candidate_delta,
                markdown_sources=markdown_sources,
            ),
        }
    if kind == "claim_evidence_ledger_delta":
        return {
            **base,
            "delta_targets": [
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
            ],
            "claim_evidence_rows": _claim_evidence_candidate_rows(json_sources),
            "source_claim_count": json_sources.get(
                "paper/claim_evidence_map.json", {}
            ).get("top_level_item_count"),
            "source_evidence_count": json_sources.get(
                "paper/evidence_ledger.json", {}
            ).get("top_level_item_count"),
        }
    if kind == "figure_table_caption_delta":
        return {
            **base,
            "delta_targets": [
                "paper/display_refs.json",
                "paper/table_refs.json",
                "paper/figure_caption_plan.json",
            ],
            "table_candidates": _display_candidate_rows(
                json_sources.get("paper/tables/table_catalog.json"),
                artifact_type="table",
            ),
            "figure_candidates": _display_candidate_rows(
                json_sources.get("paper/figures/figure_catalog.json"),
                artifact_type="figure",
            ),
        }
    if kind == "reviewer_gate_response_draft":
        return {
            **base,
            "delta_targets": [
                "paper/review/reviewer_response_draft.json",
                "paper/review/gate_response_draft.json",
            ],
            "response_draft_items": _reviewer_response_items(
                paper_facing_candidate_delta=paper_facing_candidate_delta,
                json_sources=json_sources,
            ),
        }
    if kind == "owner_decision_packet":
        return {
            **base,
            "delta_targets": ["owner_decision_packet.json"],
            "owner_ballot": {
                "recommended_owner": "MAS authority consume path",
                "decision_options": [
                    "accept_candidate_delta_for_authority_review",
                    "route_back_with_specific_missing_evidence",
                    "record_human_gate_request",
                    "record_stable_typed_blocker",
                ],
                "candidate_refs": paper_facing_candidate_delta.get(
                    "paper_facing_artifact_refs", {}
                ),
                **(
                    {
                        "adopted_external_paper_delta": paper_facing_candidate_delta[
                            "adopted_external_paper_delta_ref"
                        ]
                    }
                    if paper_facing_candidate_delta.get(
                        "adopted_external_paper_delta_ref"
                    )
                    else {}
                ),
                "source_document_refs": paper_facing_candidate_delta.get(
                    "source_document_refs", []
                ),
            },
        }
    return {
        **base,
        "delta_targets": [],
        "required_delta": "Candidate paper-facing artifact content pending.",
    }


def _adopted_external_paper_delta(
    paper_facing_candidate_delta: Mapping[str, Any],
) -> dict[str, Any]:
    adopted_external_ref = _optional_text(
        paper_facing_candidate_delta.get("adopted_external_paper_delta_ref")
    ) or _optional_text(paper_facing_candidate_delta.get("source_paper_facing_delta_ref"))
    if adopted_external_ref is None:
        return {}
    return {
        "adopted_external_paper_delta_ref": adopted_external_ref,
        "source_paper_facing_delta_ref": adopted_external_ref,
        "adopted_external_paper_delta_authority_boundary": (
            adopted_external_paper_delta_authority_boundary()
        ),
    }


def _paper_source_snapshot(readback: Mapping[str, Any]) -> dict[str, Any]:
    study_root_text = _optional_text(readback.get("study_root"))
    study_root = Path(study_root_text).expanduser().resolve() if study_root_text else None
    markdown_sources = [
        source
        for relative_path in PAPER_SOURCE_MARKDOWN_RELPATHS
        if (
            source := _markdown_source_snapshot(
                study_root=study_root,
                relative_path=relative_path,
            )
        )
        is not None
    ]
    json_sources = [
        source
        for relative_path in PAPER_SOURCE_JSON_RELPATHS
        if (
            source := _json_source_snapshot(
                study_root=study_root,
                relative_path=relative_path,
            )
        )
        is not None
    ]
    source_document_refs = [
        *_source_refs(markdown_sources),
        *_source_refs(json_sources),
    ]
    expected_refs = [
        str(path)
        for path in [*PAPER_SOURCE_MARKDOWN_RELPATHS, *PAPER_SOURCE_JSON_RELPATHS]
    ]
    observed_refs = {
        _optional_text(source.get("relative_path"))
        for source in [*markdown_sources, *json_sources]
        if isinstance(source, Mapping)
    }
    return {
        "surface_kind": "paper_mission_paper_source_snapshot",
        "schema_version": 1,
        "study_root": str(study_root) if study_root is not None else None,
        "source_document_refs": source_document_refs,
        "markdown_sources": markdown_sources,
        "json_sources": json_sources,
        "expected_relative_paths": expected_refs,
        "missing_relative_paths": [
            relative_path
            for relative_path in expected_refs
            if relative_path not in observed_refs
        ],
        "source_snapshot_complete": not any(
            relative_path not in observed_refs for relative_path in expected_refs
        ),
    }


def _source_refs(sources: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for source in sources:
        source_ref = _optional_text(source.get("source_ref"))
        if source_ref is not None:
            refs.append(source_ref)
    return refs


def _markdown_source_snapshot(
    *,
    study_root: Path | None,
    relative_path: Path,
) -> dict[str, Any] | None:
    if study_root is None:
        return None
    path = study_root / relative_path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return {
        "source_kind": "markdown",
        "relative_path": str(relative_path),
        "source_ref": str(path),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "byte_count": len(text.encode("utf-8")),
        "heading_count": len(_markdown_headings(text)),
        "headings": _markdown_headings(text)[:12],
        "lead_snippet": _compact_text(text, limit=360),
    }


def _json_source_snapshot(
    *,
    study_root: Path | None,
    relative_path: Path,
) -> dict[str, Any] | None:
    if study_root is None:
        return None
    path = study_root / relative_path
    try:
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return None
    return {
        "source_kind": "json",
        "relative_path": str(relative_path),
        "source_ref": str(path),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "byte_count": len(text.encode("utf-8")),
        "top_level_type": type(payload).__name__,
        "top_level_item_count": _json_item_count(payload),
        "sample_records": _json_sample_records(payload),
    }


def _markdown_headings(text: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match is None:
            continue
        headings.append(
            {
                "level": len(match.group(1)),
                "line": line_number,
                "text": match.group(2).strip(),
            }
        )
    return headings


def _compact_text(text: str, *, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 3)].rstrip() + "..."


def _json_item_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in (
            "claims",
            "evidence",
            "tables",
            "figures",
            "items",
            "entries",
            "records",
            "reviews",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                return len(value)
        return len(payload)
    return 1


def _json_sample_records(payload: Any, *, limit: int = 4) -> list[dict[str, Any]]:
    records = _json_record_candidates(payload)
    return [_summarize_json_record(record) for record in records[:limit]]


def _json_record_candidates(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in (
            "claims",
            "evidence",
            "tables",
            "figures",
            "items",
            "entries",
            "records",
            "reviews",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return [
                    {"id": item_key, **item_value}
                    if isinstance(item_value, dict)
                    else {"id": item_key, "value": item_value}
                    for item_key, item_value in value.items()
                ]
        return [
            {"id": item_key, **item_value}
            if isinstance(item_value, dict)
            else {"id": item_key, "value": item_value}
            for item_key, item_value in payload.items()
        ]
    return [payload]


def _summarize_json_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return {"value": _compact_text(str(record), limit=160)}
    summary: dict[str, Any] = {}
    for key in (
        "id",
        "claim_id",
        "evidence_id",
        "table_id",
        "figure_id",
        "title",
        "label",
        "status",
        "verdict",
        "section",
        "source_ref",
        "template_id",
        "pack_id",
        "renderer_family",
        "paper_role",
        "qc_profile",
        "render_receipt_ref",
        "visual_audit_receipt_ref",
        "publication_manifest_ref",
        "display_artifact_manifest_ref",
        "workflow_packet_ref",
        "polish_lifecycle_ref",
    ):
        value = record.get(key)
        if isinstance(value, (str, int, float, bool)):
            summary[key] = value
    for key in (
        "export_paths",
        "rendered_artifact_refs",
        "rendered_artifact_digests",
        "visual_audit",
    ):
        value = _compact_json_summary_value(record.get(key))
        if value is not None:
            summary[key] = value
    if not summary:
        for key, value in record.items():
            if isinstance(value, (str, int, float, bool)):
                summary[str(key)] = value
            if len(summary) >= 4:
                break
    return summary


def _compact_json_summary_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        compact_list = [
            item
            for item in (_compact_json_summary_value(item) for item in value[:12])
            if item is not None
        ]
        return compact_list if compact_list else None
    if isinstance(value, Mapping):
        compact: dict[str, Any] = {}
        for key, item in value.items():
            compact_value = _compact_json_summary_value(item)
            if compact_value is not None:
                compact[str(key)] = compact_value
            if len(compact) >= 24:
                break
        return compact if compact else None
    return None


def _candidate_patch_operations(
    *,
    paper_facing_candidate_delta: Mapping[str, Any],
    markdown_sources: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    repair_scope = _optional_text(paper_facing_candidate_delta.get("repair_scope"))
    target_stage_id = _optional_text(paper_facing_candidate_delta.get("target_stage_id"))
    for source in markdown_sources:
        headings = [
            heading
            for heading in source.get("headings", [])
            if isinstance(heading, Mapping)
        ]
        selected_heading = _select_patch_heading(headings)
        operations.append(
            {
                "operation": "revise_section_candidate",
                "source_ref": source.get("source_ref"),
                "relative_path": source.get("relative_path"),
                "target_heading": selected_heading,
                "candidate_revision_intent": (
                    "Tighten the paper-facing claim/evidence narrative for "
                    f"{repair_scope or target_stage_id or 'the current MAS route-back scope'}."
                ),
                "authority_materialized": False,
            }
        )
    if operations:
        return operations
    return [
        {
            "operation": "source_missing_record",
            "candidate_revision_intent": (
                "No manuscript source was available to materialize a concrete "
                "section patch candidate."
            ),
            "authority_materialized": False,
        }
    ]


def _select_patch_heading(headings: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    preferred_terms = (
        "results",
        "discussion",
        "methods",
        "limitations",
        "conclusion",
    )
    for term in preferred_terms:
        for heading in headings:
            text = _optional_text(heading.get("text"))
            if text is not None and term in text.lower():
                return dict(heading)
    return dict(headings[0]) if headings else None


def _claim_evidence_candidate_rows(
    json_sources: Mapping[str | None, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path in ("paper/claim_evidence_map.json", "paper/evidence_ledger.json"):
        source = json_sources.get(relative_path)
        if not isinstance(source, Mapping):
            continue
        for record in source.get("sample_records", []):
            if not isinstance(record, Mapping):
                continue
            rows.append(
                {
                    "source_ref": source.get("source_ref"),
                    "relative_path": relative_path,
                    "candidate_row": dict(record),
                    "candidate_delta": "review_and_bind_claim_to_available_evidence",
                    "authority_materialized": False,
                }
            )
    return rows


def _display_candidate_rows(
    source: Mapping[str, Any] | None,
    *,
    artifact_type: str,
) -> list[dict[str, Any]]:
    if not isinstance(source, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for record in source.get("sample_records", []):
        if not isinstance(record, Mapping):
            continue
        rows.append(
            {
                "artifact_type": artifact_type,
                "source_ref": source.get("source_ref"),
                "relative_path": source.get("relative_path"),
                "candidate_ref": dict(record),
                **_display_artifact_evidence(record),
                "candidate_delta": "bind_display_caption_to_claim_evidence_refs",
                "authority_materialized": False,
            }
        )
    return rows


def _display_artifact_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    artifact_refs = record.get("rendered_artifact_refs")
    if not isinstance(artifact_refs, list):
        artifact_refs = record.get("export_paths")
    if isinstance(artifact_refs, list):
        refs = [item for item in artifact_refs if isinstance(item, str)]
        if refs:
            evidence["display_artifact_refs"] = refs
    artifact_digests = record.get("rendered_artifact_digests")
    if isinstance(artifact_digests, Mapping):
        digests = {
            str(key): value
            for key, value in artifact_digests.items()
            if isinstance(value, (str, int, float, bool))
        }
        if digests:
            evidence["display_artifact_digests"] = digests
    for key in (
        "render_receipt_ref",
        "visual_audit_receipt_ref",
        "publication_manifest_ref",
        "display_artifact_manifest_ref",
        "workflow_packet_ref",
        "polish_lifecycle_ref",
    ):
        value = record.get(key)
        if isinstance(value, str) and value:
            evidence[key] = value
    visual_audit = record.get("visual_audit")
    if isinstance(visual_audit, Mapping):
        evidence["visual_audit"] = dict(visual_audit)
    return evidence


def _reviewer_response_items(
    *,
    paper_facing_candidate_delta: Mapping[str, Any],
    json_sources: Mapping[str | None, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    review_source = json_sources.get("paper/review/review_ledger.json")
    items: list[dict[str, Any]] = []
    if isinstance(review_source, Mapping):
        for record in review_source.get("sample_records", []):
            if not isinstance(record, Mapping):
                continue
            items.append(
                {
                    "source_ref": review_source.get("source_ref"),
                    "relative_path": review_source.get("relative_path"),
                    "review_item": dict(record),
                    "draft_response": (
                        "Address this reviewer or gate item by linking the "
                        "candidate manuscript and evidence deltas above."
                    ),
                    "authority_materialized": False,
                }
            )
    if items:
        return items
    return [
        {
            "route_back_evidence_ref": paper_facing_candidate_delta.get(
                "route_back_evidence_ref"
            ),
            "draft_response": (
                "MAS route-back remains the review target; no review ledger source "
                "was available in this candidate snapshot."
            ),
            "authority_materialized": False,
        }
    ]


def _paper_facing_candidate_output(
    *,
    kind: str,
    study_id: str,
    route_back_ready: bool,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "status": "candidate_required" if route_back_ready else "context_only",
        "artifact_ref": f"candidate://{study_id}/paper-facing/{kind}",
        "candidate_only": True,
        "authority_materialized": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
