from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import progress_portal, runtime_live_console
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_portal_console_soak"
SOAK_REPORT_REF = "artifacts/runtime/portal_console_soak/latest.json"
FORBIDDEN_IDENTITY_TOKENS = (
    "MDS WebUI",
    "DeepScientist",
    "med-deepscientist",
)
FORBIDDEN_TRUTH_REF_TOKENS = (
    "med-deepscientist",
    "/ops/med-deepscientist/",
    "last_launch_report.json/.ds",
)


def run_portal_console_soak(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
    materialize: bool = True,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
    selected_study_root = Path(study_root) if study_root is not None else None
    portal_result = progress_portal.materialize_progress_portal(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
        sync_runtime_summary=False,
    )
    console_result = runtime_live_console.serve_live_console_stream(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
        host="127.0.0.1",
        port=0,
        interval_seconds=30,
    )
    conversation_result = runtime_live_console.materialize_conversation_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=selected_study_root,
        generated_at=generated,
    )
    report = build_portal_console_soak_report(
        profile=profile,
        profile_ref=profile_ref,
        portal_result=portal_result,
        console_result=console_result,
        conversation_result=conversation_result,
        generated_at=generated,
    )
    if materialize:
        report_path = profile.workspace_root / SOAK_REPORT_REF
        _write_json(report_path, report)
        report["report_path"] = str(report_path)
    return report


def build_portal_console_soak_report(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    portal_result: Mapping[str, Any],
    console_result: Mapping[str, Any],
    conversation_result: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
    portal_payload_path = Path(str(portal_result.get("payload_path") or ""))
    portal_html_path = Path(str(portal_result.get("html_path") or ""))
    console_payload_path = Path(str(console_result.get("payload_path") or ""))
    console_html_path = Path(str(console_result.get("html_path") or ""))
    console_ui_payload_path = Path(str(console_result.get("ui_payload_path") or ""))
    conversation_payload_path = Path(
        str(
            _mapping(conversation_result).get("payload_path")
            or profile.workspace_root / "artifacts" / "runtime" / "conversation_read_model" / "latest.json"
        )
    )

    portal_payload = _read_json_object(portal_payload_path)
    console_payload = _read_json_object(console_payload_path)
    console_ui_payload = _read_json_object(console_ui_payload_path)
    conversation_payload = _mapping(_mapping(conversation_result).get("conversation_read_model")) or _read_json_object(
        conversation_payload_path
    )
    portal_html = _read_text(portal_html_path)
    console_html = _read_text(console_html_path)
    console_snapshot = _mapping(console_result.get("session_read_model")) or console_payload

    evidence = {
        "portal_refresh": _portal_refresh_evidence(
            portal_result=portal_result,
            portal_payload=portal_payload,
            portal_html_path=portal_html_path,
        ),
        "per_study_workbench": _per_study_workbench(
            portal_result=portal_result,
            portal_payload=portal_payload,
            portal_html_path=portal_html_path,
        ),
        "route_decision_trail": _route_decision_trail(
            portal_result=portal_result,
            portal_payload=portal_payload,
        ),
        "per_study_deep_link": _per_study_deep_link(
            portal_result=portal_result,
            portal_payload=portal_payload,
        ),
        "conversation_read_model": _conversation_read_model(conversation_payload=conversation_payload),
        "conversation_portal_panel": _conversation_portal_panel(
            portal_result=portal_result,
            portal_payload=portal_payload,
            portal_html_path=portal_html_path,
        ),
        "study_scoped_console": _study_scoped_console(
            console_snapshot=console_snapshot,
            console_ui_payload=console_ui_payload,
        ),
        "action_receipts": _action_receipts(
            console_snapshot=console_snapshot,
            console_ui_payload=console_ui_payload,
        ),
        "authorized_action_apply_receipts": _authorized_action_apply_receipts(
            workspace_root=profile.workspace_root,
            portal_payload=portal_payload,
        ),
        "terminal_attach_gate": _terminal_attach_gate(console_ui_payload=console_ui_payload),
        "latency_slo_source_refs": _latency_slo_source_refs(
            portal_payload=portal_payload,
            console_snapshot=console_snapshot,
            console_ui_payload=console_ui_payload,
        ),
        "live_console_study_run_disambiguation": _live_console_disambiguation(console_snapshot),
        "terminal_log_refs": _terminal_log_refs(console_snapshot),
        "source_ref_cleanliness": _source_ref_cleanliness(
            portal_payload=portal_payload,
            console_payload=console_payload,
            console_ui_payload=console_ui_payload,
        ),
        "product_identity": _product_identity(portal_html=portal_html, console_html=console_html),
        "write_boundary": _write_boundary(
            workspace_root=profile.workspace_root,
            portal_result=portal_result,
            console_result=console_result,
        ),
    }
    status = "passed" if all(item.get("status") == "passed" for item in evidence.values()) else "blocked"
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "owner": "MedAutoScience",
        "generated_at": generated,
        "status": status,
        "read_only": True,
        "authority": {
            "kind": "display_read_model_soak_evidence",
            "writes_authority_surface": False,
            "controller_action_execution_allowed": False,
            "quality_authority_allowed": False,
            "publication_authority_allowed": False,
            "submission_authority_allowed": False,
        },
        "workspace": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        "evidence": evidence,
        "artifact_refs": {
            "progress_portal_payload": str(portal_payload_path),
            "progress_portal_html": str(portal_html_path),
            "live_console_session_read_model": str(console_payload_path),
            "conversation_read_model": str(conversation_payload_path),
            "live_console_ui_payload": str(console_ui_payload_path),
            "live_console_html": str(console_html_path),
            "soak_report": str(profile.workspace_root / SOAK_REPORT_REF),
        },
        "forbidden_authority_writes": [
            "paper/current_package",
            "manuscript/current_package",
            "paper/submission_minimal",
            "manuscript/submission_minimal",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "runtime_lifecycle.sqlite",
            "restore_archive",
        ],
    }


def _portal_refresh_evidence(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
    portal_html_path: Path,
) -> dict[str, Any]:
    portal_view = _mapping(portal_payload.get("portal_view"))
    status = "passed" if portal_result.get("status") == "materialized" and portal_html_path.is_file() else "blocked"
    return {
        "status": status,
        "payload_generated_at": _text(portal_payload.get("generated_at")),
        "html_path": str(portal_html_path),
        "refresh_mode": portal_view.get("refresh_mode"),
    }


def _live_console_disambiguation(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    studies = [dict(item) for item in snapshot.get("studies") or [] if isinstance(item, Mapping)]
    study_ids = [_text(item.get("study_id")) for item in studies]
    run_ids = [
        _text(run.get("run_id"))
        for item in studies
        for run in item.get("runs") or []
        if isinstance(run, Mapping)
    ]
    if not run_ids:
        run_ids = [_text(item.get("active_run_id")) for item in studies]
    distinct_studies = sorted({item for item in study_ids if item})
    distinct_runs = sorted({item for item in run_ids if item})
    return {
        "status": "passed" if len(distinct_studies) >= 2 and len(distinct_runs) >= 1 else "blocked",
        "study_ids": distinct_studies,
        "run_ids": distinct_runs,
        "selected_study_id": _text(snapshot.get("selected_study_id")),
    }


def _per_study_workbench(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
    portal_html_path: Path,
) -> dict[str, Any]:
    workspace = _mapping(portal_payload.get("workspace"))
    studies = [dict(item) for item in workspace.get("studies") or [] if isinstance(item, Mapping)]
    workbench = _mapping(portal_payload.get("study_workbench"))
    tabs = _mapping_list(workbench.get("tabs"))
    tab_ids = {_text(item.get("id")) for item in tabs if _text(item.get("id"))}
    expected_tabs = {"overview", "route_decision_trail", "path_stage", "runtime", "artifacts", "source_refs"}
    materialized_pages = _materialized_study_page_refs(
        portal_result=portal_result,
        portal_html_path=portal_html_path,
        studies=studies,
    )
    has_rows = bool({_text(item.get("study_id")) for item in studies if _text(item.get("study_id"))})
    has_workbench_surface = workbench.get("surface_kind") == "mas_progress_portal_study_workbench"
    has_tabs = expected_tabs.issubset(tab_ids)
    has_materialized_pages = len(materialized_pages) >= len(studies) > 0
    return {
        "status": "passed" if has_rows and ((has_workbench_surface and has_tabs) or has_materialized_pages) else "blocked",
        "study_count": len(studies),
        "workbench_surface_kind": _text(workbench.get("surface_kind")),
        "expected_tabs": sorted(expected_tabs),
        "observed_tabs": sorted(tab for tab in tab_ids if tab),
        "materialized_page_refs": materialized_pages,
        "blockers": _blockers(
            ("missing_workspace_study_rows", not has_rows),
            ("missing_per_study_sections_or_pages", not ((has_workbench_surface and has_tabs) or has_materialized_pages)),
        ),
    }


def _route_decision_trail(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> dict[str, Any]:
    trails = _portal_route_trails(portal_result=portal_result, portal_payload=portal_payload)
    explicit = [trail for trail in trails if trail.get("surface_kind") == "mas_progress_portal_route_decision_trail"]
    available = [trail for trail in explicit if trail.get("status") == "available"]
    missing = [trail for trail in explicit if trail.get("status") != "available"]
    all_conditions = [
        condition
        for trail in explicit
        for condition in _string_refs(_mapping(trail.get("conditions")).get("missing"))
    ]
    has_nodes = any(_mapping_list(trail.get("nodes")) for trail in available)
    has_active_path = any(_text(trail.get("active_path")) for trail in available)
    has_winning_path = any(_text(trail.get("winning_path")) for trail in available)
    has_source_refs = any(_string_refs(trail.get("source_refs")) for trail in available)
    return {
        "status": "passed" if explicit and available and has_nodes and has_active_path and has_winning_path and has_source_refs else "blocked",
        "trail_count": len(explicit),
        "available_count": len(available),
        "missing_count": len(missing),
        "active_paths": _dedupe_text(trail.get("active_path") for trail in available),
        "winning_paths": _dedupe_text(trail.get("winning_path") for trail in available),
        "source_ref_count": sum(len(_string_refs(trail.get("source_refs"))) for trail in available),
        "blockers": _blockers(
            ("missing_route_decision_trail_surface", not explicit),
            ("missing_route_nodes", not has_nodes),
            ("missing_active_path", explicit and not has_active_path),
            ("missing_winning_path", explicit and not has_winning_path),
            ("missing_route_decision_trail_source_refs", bool(available) and not has_source_refs),
        )
        + [f"route_decision_trail:{condition}" for condition in _dedupe_text(all_conditions)],
    }


def _per_study_deep_link(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> dict[str, Any]:
    handoff = _mapping(portal_payload.get("opl_handoff"))
    live_console = _mapping(portal_payload.get("live_console"))
    hosted_package = _mapping(portal_result.get("hosted_package"))
    package_study_pages = _mapping(_mapping(hosted_package.get("package_refs")).get("study_pages"))
    refs = [
        _text(handoff.get("deep_link")),
        _text(live_console.get("html_ref")),
        *_string_refs(portal_payload.get("per_study_deep_links")),
    ]
    refs.extend(str(item) for item in package_study_pages.values() if item)
    workspace = _mapping(portal_payload.get("workspace"))
    for item in workspace.get("studies") or []:
        if not isinstance(item, Mapping):
            continue
        refs.extend(
            [
                _text(item.get("href")),
                _text(item.get("portal_href")),
                _text(item.get("deep_link")),
                _text(item.get("portal_deep_link")),
                _text(item.get("live_console_href")),
                _text(item.get("live_console_deep_link")),
            ]
        )
    for page in _mapping(portal_result.get("study_pages")).values():
        if isinstance(page, Mapping):
            refs.extend([_text(page.get("html_path")), _text(page.get("html_ref"))])
    clean_refs = [ref for ref in refs if ref]
    study_scoped_refs = [
        ref
        for ref in clean_refs
        if "study_id=" in ref or "/studies/" in ref or "selected_study_id=" in ref
    ]
    return {
        "status": "passed" if study_scoped_refs else "blocked",
        "checked_refs": clean_refs,
        "study_scoped_refs": study_scoped_refs,
        "blockers": [] if study_scoped_refs else ["missing_study_scoped_portal_or_console_deep_link"],
    }


def _conversation_read_model(*, conversation_payload: Mapping[str, Any]) -> dict[str, Any]:
    timeline = _mapping_list(conversation_payload.get("timeline"))
    studies = _mapping_list(conversation_payload.get("studies"))
    source_refs = _conversation_source_refs(conversation_payload)
    selected_study_id = _text(conversation_payload.get("selected_study_id"))
    scoped = bool(selected_study_id or any(_text(item.get("study_id")) for item in studies + timeline))
    has_conversation_items = bool(
        timeline
        or studies
        or conversation_payload.get("surface_kind") == "mas_runtime_conversation_read_model"
    )
    return {
        "status": "passed" if has_conversation_items and scoped and source_refs else "blocked",
        "surface_kind": _text(conversation_payload.get("surface_kind")),
        "selected_study_id": selected_study_id,
        "timeline_item_count": len(timeline),
        "study_count": len(studies),
        "source_refs": source_refs,
        "blockers": _blockers(
            ("missing_conversation_read_model", not has_conversation_items),
            ("missing_study_scope", not scoped),
            ("missing_conversation_source_refs", not source_refs),
        ),
    }


def _conversation_portal_panel(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
    portal_html_path: Path,
) -> dict[str, Any]:
    panels = _portal_conversation_panels(portal_result=portal_result, portal_payload=portal_payload)
    visible_html_refs = _conversation_panel_html_refs(
        portal_result=portal_result,
        portal_html_path=portal_html_path,
    )
    available = [
        panel
        for panel in panels
        if panel.get("surface_kind") == "mas_progress_portal_conversation_panel"
        and panel.get("status") == "available"
    ]
    source_refs = [
        ref
        for panel in panels
        for ref in _string_refs(panel.get("source_refs"))
    ]
    return {
        "status": "passed" if available and visible_html_refs and source_refs else "blocked",
        "panel_count": len(panels),
        "available_panel_count": len(available),
        "html_refs": visible_html_refs,
        "source_refs": _dedupe_text(source_refs),
        "blockers": _blockers(
            ("missing_conversation_portal_panel", not panels),
            ("missing_available_conversation_portal_panel", not available),
            ("missing_visible_conversation_html", not visible_html_refs),
            ("missing_conversation_panel_source_refs", not source_refs),
        ),
    }


def _study_scoped_console(
    *,
    console_snapshot: Mapping[str, Any],
    console_ui_payload: Mapping[str, Any],
) -> dict[str, Any]:
    selected = _text(console_snapshot.get("selected_study_id")) or _text(console_ui_payload.get("selected_study_id"))
    studies = [dict(item) for item in console_snapshot.get("studies") or [] if isinstance(item, Mapping)]
    selected_rows = [item for item in studies if item.get("selected") is True or _text(item.get("study_id")) == selected]
    stream_sources = [
        dict(item)
        for item in console_snapshot.get("stream_sources") or []
        if isinstance(item, Mapping)
    ]
    scoped_sources = [
        item
        for item in stream_sources
        if selected and _text(item.get("study_id")) == selected
    ]
    return {
        "status": "passed" if selected and (selected_rows or scoped_sources) else "blocked",
        "selected_study_id": selected,
        "selected_row_count": len(selected_rows),
        "scoped_stream_source_count": len(scoped_sources),
        "blockers": _blockers(
            ("missing_selected_study_id", not selected),
            ("missing_selected_study_row_or_stream_sources", not (selected_rows or scoped_sources)),
        ),
    }


def _action_receipts(
    *,
    console_snapshot: Mapping[str, Any],
    console_ui_payload: Mapping[str, Any],
) -> dict[str, Any]:
    intents = _mapping_list(console_snapshot.get("controller_action_intents"))
    intents.extend(_mapping_list(console_ui_payload.get("controller_action_intents")))
    receipts: list[dict[str, Any]] = []
    for item in intents:
        if _text(item.get("receipt_ref")) or _text(item.get("audit_ref")) or _text(item.get("command")):
            receipts.append(item)
    direct_exec = [
        item
        for item in intents
        if item.get("executes_directly") is True or item.get("direct_execution_allowed") is True
    ]
    return {
        "status": "passed" if intents and receipts and not direct_exec else "blocked",
        "intent_count": len(intents),
        "receipt_or_command_count": len(receipts),
        "direct_execution_intents": [_text(item.get("intent")) for item in direct_exec],
        "blockers": _blockers(
            ("missing_controller_action_intents", not intents),
            ("missing_action_receipt_or_command_refs", not receipts),
            ("ui_direct_execution_detected", bool(direct_exec)),
        ),
    }


def _authorized_action_apply_receipts(
    *,
    workspace_root: Path,
    portal_payload: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_root = workspace_root / "artifacts" / "runtime" / "progress_portal" / "action_receipts"
    receipts = [_read_json_object(path) for path in sorted(receipt_root.glob("*.json"))] if receipt_root.is_dir() else []
    for item in _mapping_list(_mapping(portal_payload.get("progress_portal_actions")).get("receipts")):
        receipts.append(item)
    apply_receipts = [item for item in receipts if item.get("apply") is True]
    applied = [item for item in apply_receipts if item.get("apply_status") == "applied"]
    forbidden_writes_ok = all(
        "controller_decisions/latest.json" in _string_refs(item.get("forbidden_writes"))
        and "runtime_sqlite_authority" in _string_refs(item.get("forbidden_writes"))
        for item in apply_receipts
    )
    actions = sorted({_text(item.get("action")) for item in applied if _text(item.get("action"))})
    return {
        "status": "passed" if applied and forbidden_writes_ok else "blocked",
        "receipt_count": len(receipts),
        "apply_receipt_count": len(apply_receipts),
        "applied_action_count": len(applied),
        "applied_actions": actions,
        "blockers": _blockers(
            ("missing_apply_action_receipts", not apply_receipts),
            ("missing_applied_action_receipts", not applied),
            ("apply_receipt_forbidden_writes_missing", apply_receipts and not forbidden_writes_ok),
        ),
    }


def _terminal_attach_gate(*, console_ui_payload: Mapping[str, Any]) -> dict[str, Any]:
    gate = _mapping(console_ui_payload.get("terminal_attach_gate"))
    contract = _mapping(gate.get("required_owner_contract"))
    required = {"token", "lease", "idempotency", "audit", "input", "resize", "detach"}
    observed = {key for key in required if _text(contract.get(key))}
    missing_contract = sorted(required - observed)
    blocked_status = gate.get("status") == "blocked_by_missing_terminal_input_owner"
    forbidden_owner_ok = gate.get("forbidden_owner") == "legacy_mds_daemon_websocket"
    read_only = gate.get("read_only_default") is True
    attach_started = gate.get("attach_started") is True
    return {
        "status": "passed" if gate and blocked_status and forbidden_owner_ok and read_only and not attach_started and not missing_contract else "blocked",
        "surface_kind": _text(gate.get("surface_kind")),
        "gate_status": _text(gate.get("status")),
        "forbidden_owner": _text(gate.get("forbidden_owner")),
        "read_only_default": gate.get("read_only_default"),
        "attach_started": bool(gate.get("attach_started")),
        "study_id": _text(gate.get("study_id")),
        "missing_owner_contract": missing_contract,
        "blockers": _blockers(
            ("missing_terminal_attach_gate", not gate),
            ("terminal_attach_gate_not_blocked", bool(gate) and not blocked_status),
            ("legacy_owner_not_forbidden", bool(gate) and not forbidden_owner_ok),
            ("terminal_attach_gate_not_read_only", bool(gate) and not read_only),
            ("terminal_attach_started", attach_started),
        )
        + [f"missing_owner_contract:{item}" for item in missing_contract],
    }


def _latency_slo_source_refs(
    *,
    portal_payload: Mapping[str, Any],
    console_snapshot: Mapping[str, Any],
    console_ui_payload: Mapping[str, Any],
) -> dict[str, Any]:
    study = _mapping(portal_payload.get("study"))
    freshness = _mapping(portal_payload.get("freshness"))
    slo = _mapping(study.get("outer_supervision_slo")) or _mapping(portal_payload.get("outer_supervision_slo"))
    events = _mapping_list(console_snapshot.get("events"))
    sources = [
        *_string_refs(portal_payload.get("source_refs")),
        *_source_ref_objects(console_snapshot.get("source_refs")),
        *_string_refs(console_ui_payload.get("source_refs")),
    ]
    has_latency = bool(
        _text(freshness.get("status"))
        or _text(freshness.get("latest_event_at"))
        or _text(slo.get("state"))
        or any(_text(item.get("observed_at")) for item in events)
    )
    has_slo = bool(_text(slo.get("state")) or _text(slo.get("surface_kind")) == "outer_supervision_slo")
    has_source_refs = bool(sources)
    return {
        "status": "passed" if has_latency and has_slo and has_source_refs else "blocked",
        "freshness_status": _text(freshness.get("status")),
        "outer_supervision_slo_state": _text(slo.get("state")),
        "event_count": len(events),
        "source_ref_count": len(sources),
        "blockers": _blockers(
            ("missing_latency_or_freshness_evidence", not has_latency),
            ("missing_outer_supervision_slo", not has_slo),
            ("missing_source_refs", not has_source_refs),
        ),
    }


def _terminal_log_refs(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sources = [
        dict(item)
        for item in snapshot.get("stream_sources") or []
        if isinstance(item, Mapping) and item.get("topic") in {"terminal.tail", "log.tail"}
    ]
    if not sources:
        for study in snapshot.get("studies") or []:
            if not isinstance(study, Mapping):
                continue
            for key, topic in (("terminal_sources", "terminal.tail"), ("log_sources", "log.tail")):
                for source in study.get(key) or []:
                    if isinstance(source, Mapping):
                        item = dict(source)
                        item["topic"] = topic
                        item["study_id"] = study.get("study_id")
                        sources.append(item)
    readable = [
        source
        for source in sources
        if _text(source.get("source_ref")) and source.get("status", source.get("source_status")) == "available"
    ]
    return {
        "status": "passed" if readable and len(readable) == len(sources) else "blocked",
        "refs": [
            {
                "topic": _text(source.get("topic")),
                "study_id": _text(source.get("study_id")),
                "source_ref": _text(source.get("source_ref")),
                "status": _text(source.get("status")) or _text(source.get("source_status")),
            }
            for source in sources
        ],
    }


def _source_ref_cleanliness(
    *,
    portal_payload: Mapping[str, Any],
    console_payload: Mapping[str, Any],
    console_ui_payload: Mapping[str, Any],
) -> dict[str, Any]:
    refs = [
        *_string_refs(portal_payload.get("source_refs")),
        *_source_ref_objects(console_payload.get("source_refs")),
        *_string_refs(console_ui_payload.get("source_refs")),
    ]
    forbidden = [
        ref
        for ref in refs
        if any(token in ref for token in FORBIDDEN_TRUTH_REF_TOKENS)
    ]
    return {
        "status": "passed" if not forbidden else "blocked",
        "checked_ref_count": len(refs),
        "forbidden_refs": forbidden,
    }


def _product_identity(*, portal_html: str, console_html: str) -> dict[str, Any]:
    combined = f"{portal_html}\n{console_html}"
    forbidden = [token for token in FORBIDDEN_IDENTITY_TOKENS if token in combined]
    return {
        "status": "passed" if "Med Auto Science" in combined and not forbidden else "blocked",
        "brand": "Med Auto Science",
        "forbidden_identity_tokens": forbidden,
    }


def _write_boundary(
    *,
    workspace_root: Path,
    portal_result: Mapping[str, Any],
    console_result: Mapping[str, Any],
) -> dict[str, Any]:
    allowed = {
        str(Path(str(portal_result.get("payload_path"))).resolve()),
        str(Path(str(portal_result.get("html_path"))).resolve()),
        str(Path(str(portal_result.get("hosted_package_path"))).resolve()),
        str(Path(str(console_result.get("payload_path"))).resolve()),
        str(Path(str(console_result.get("history_path"))).resolve()),
        str(Path(str(console_result.get("ui_payload_path"))).resolve()),
        str(Path(str(console_result.get("html_path"))).resolve()),
        str((workspace_root / SOAK_REPORT_REF).resolve()),
    }
    forbidden_paths = [
        workspace_root / "publication_eval" / "latest.json",
        workspace_root / "controller_decisions" / "latest.json",
        workspace_root / "runtime_lifecycle.sqlite",
    ]
    return {
        "status": "passed" if not any(path.exists() for path in forbidden_paths) else "blocked",
        "allowed_written_refs": sorted(allowed),
        "forbidden_existing_refs": [str(path) for path in forbidden_paths if path.exists()],
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _blockers(*items: tuple[str, bool]) -> list[str]:
    return [name for name, blocked in items if blocked]


def _materialized_study_page_refs(
    *,
    portal_result: Mapping[str, Any],
    portal_html_path: Path,
    studies: list[dict[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for page in _mapping(portal_result.get("study_pages")).values():
        if isinstance(page, Mapping):
            refs.extend([_text(page.get("html_path")), _text(page.get("html_ref"))])
    base = portal_html_path.parent
    for item in studies:
        study_id = _text(item.get("study_id"))
        if not study_id:
            continue
        candidate = base / "studies" / study_id / "index.html"
        if candidate.is_file():
            refs.append(str(candidate))
    return [ref for ref in _dedupe_text(refs) if ref]


def _portal_route_trails(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    trails: list[dict[str, Any]] = []
    workbench = _mapping(portal_payload.get("study_workbench"))
    trail = _mapping(workbench.get("route_decision_trail"))
    if trail:
        trails.append(trail)
    for page in _mapping(portal_result.get("study_pages")).values():
        if not isinstance(page, Mapping):
            continue
        payload_path = Path(str(page.get("payload_path") or ""))
        page_payload = _read_json_object(payload_path)
        page_trail = _mapping(_mapping(page_payload.get("study_workbench")).get("route_decision_trail"))
        if page_trail:
            trails.append(page_trail)
    return trails


def _portal_conversation_panels(
    *,
    portal_result: Mapping[str, Any],
    portal_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    panels: list[dict[str, Any]] = []
    panel = _mapping(_mapping(portal_payload.get("study_workbench")).get("conversation"))
    if panel:
        panels.append(panel)
    for page in _mapping(portal_result.get("study_pages")).values():
        if not isinstance(page, Mapping):
            continue
        payload_path = Path(str(page.get("payload_path") or ""))
        page_payload = _read_json_object(payload_path)
        page_panel = _mapping(_mapping(page_payload.get("study_workbench")).get("conversation"))
        if page_panel:
            panels.append(page_panel)
    return panels


def _conversation_panel_html_refs(
    *,
    portal_result: Mapping[str, Any],
    portal_html_path: Path,
) -> list[str]:
    refs: list[str] = []
    for path in [portal_html_path, *[
        Path(str(page.get("html_path") or ""))
        for page in _mapping(portal_result.get("study_pages")).values()
        if isinstance(page, Mapping)
    ]]:
        html = _read_text(path)
        if "Conversation" in html and "Conversation Source Refs" in html:
            refs.append(str(path))
    return refs


def _conversation_source_refs(payload: Mapping[str, Any]) -> list[str]:
    refs = _source_ref_objects(payload.get("source_refs"))
    for item in _mapping_list(payload.get("timeline")):
        refs.extend(
            [
                _text(item.get("source_ref")),
                _text(item.get("receipt_ref")),
                _text(item.get("payload_ref")),
            ]
        )
    return _dedupe_text(refs)


def _source_ref_objects(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            ref = _text(item.get("source_ref"))
            if ref:
                refs.append(ref)
    return refs


def _string_refs(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [str(item) for item in value if _text(item)]


def _dedupe_text(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "SOAK_REPORT_REF",
    "SURFACE_KIND",
    "build_portal_console_soak_report",
    "run_portal_console_soak",
]
