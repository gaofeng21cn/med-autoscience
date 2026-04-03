from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.policies import publication_gate as publication_gate_policy
from med_autoscience.runtime_protocol import paper_artifacts, quest_state, user_message
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store


@dataclass
class GateState:
    quest_root: Path
    runtime_state: dict[str, Any]
    anchor_kind: str
    anchor_path: Path
    paper_line_state_path: Path | None
    paper_line_state: dict[str, Any] | None
    main_result_path: Path | None
    main_result: dict[str, Any] | None
    compile_report_path: Path | None
    compile_report: dict[str, Any] | None
    latest_gate_path: Path | None
    latest_gate: dict[str, Any] | None
    active_run_stdout_path: Path | None
    recent_stdout_lines: list[str]
    write_drift_detected: bool
    missing_deliverables: list[str]
    present_deliverables: list[str]
    paper_bundle_manifest_path: Path | None
    paper_bundle_manifest: dict[str, Any] | None
    submission_minimal_manifest_path: Path | None
    submission_minimal_manifest: dict[str, Any] | None
    submission_minimal_docx_present: bool
    submission_minimal_pdf_present: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def find_latest_gate_report(quest_root: Path) -> Path | None:
    return find_latest(list((quest_root / "artifacts" / "reports" / "publishability_gate").glob("*.json")))


def detect_write_drift(lines: list[str]) -> bool:
    merged = "\n".join(lines)
    return any(re.search(pattern, merged, flags=re.IGNORECASE) for pattern in publication_gate_policy.WRITE_DRIFT_PATTERNS)


def classify_deliverables(main_result_path: Path, main_result: dict[str, Any]) -> tuple[list[str], list[str]]:
    required = list(main_result.get("metric_contract", {}).get("required_non_scalar_deliverables") or [])
    manifest_path = paper_artifacts.resolve_artifact_manifest_from_main_result(main_result)
    manifest_payload = load_json(manifest_path, default={}) if manifest_path else {}
    manifest_blob = json.dumps(manifest_payload, ensure_ascii=False).lower()
    present: list[str] = []
    missing: list[str] = []
    for item in required:
        if item.lower() in manifest_blob:
            present.append(item)
        else:
            missing.append(item)
    return present, missing


def gate_allows_write(latest_gate: dict[str, Any] | None, latest_gate_path: Path | None, main_result_path: Path) -> bool:
    if latest_gate is None or latest_gate_path is None:
        return False
    if latest_gate_path.stat().st_mtime < main_result_path.stat().st_mtime:
        return False
    return bool(latest_gate.get("allow_write"))


def resolve_compile_report_path(
    *,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> Path | None:
    if paper_bundle_manifest_path is None or paper_bundle_manifest is None:
        return None
    candidates = [
        str(paper_bundle_manifest.get("compile_report_path") or "").strip(),
        str((paper_bundle_manifest.get("bundle_inputs") or {}).get("compile_report_path") or "").strip(),
    ]
    worktree_root = paper_bundle_manifest_path.resolve().parent.parent
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if not path.is_absolute():
            path = worktree_root / path
        resolved = path.resolve()
        if resolved.exists():
            return resolved
    return None


def resolve_primary_anchor(
    *,
    quest_root: Path,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> tuple[str, Path, Path | None, dict[str, Any] | None]:
    try:
        main_result_path = quest_state.find_latest_main_result_path(quest_root)
    except FileNotFoundError:
        main_result_path = None
    if main_result_path is not None:
        return "main_result", main_result_path, main_result_path, load_json(main_result_path)
    if paper_bundle_manifest_path is not None and paper_bundle_manifest is not None:
        return "paper_bundle", paper_bundle_manifest_path, None, None
    return "missing", quest_root, None, None


def build_gate_state(quest_root: Path) -> GateState:
    runtime_state = quest_state.load_runtime_state(quest_root)
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
    paper_bundle_manifest = load_json(paper_bundle_manifest_path) if paper_bundle_manifest_path else None
    paper_line_state_path = (
        paper_bundle_manifest_path.parent / "paper_line_state.json"
        if paper_bundle_manifest_path is not None
        else None
    )
    paper_line_state = (
        load_json(paper_line_state_path)
        if paper_line_state_path is not None and paper_line_state_path.exists()
        else None
    )
    anchor_kind, anchor_path, main_result_path, main_result = resolve_primary_anchor(
        quest_root=quest_root,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    compile_report_path = resolve_compile_report_path(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    compile_report = load_json(compile_report_path) if compile_report_path else None
    latest_gate_path = find_latest_gate_report(quest_root)
    latest_gate = load_json(latest_gate_path) if latest_gate_path else None
    stdout_path = quest_state.resolve_active_stdout_path(quest_root=quest_root, runtime_state=runtime_state)
    recent_lines = quest_state.read_recent_stdout_lines(stdout_path)
    if main_result_path is not None and main_result is not None:
        present_deliverables, missing_deliverables = classify_deliverables(main_result_path, main_result)
    else:
        present_deliverables, missing_deliverables = [], []
    submission_minimal_manifest_path = paper_artifacts.resolve_submission_minimal_manifest(paper_bundle_manifest_path)
    submission_minimal_manifest = (
        load_json(submission_minimal_manifest_path) if submission_minimal_manifest_path else None
    )
    submission_minimal_docx_path, submission_minimal_pdf_path = paper_artifacts.resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
    )
    return GateState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        anchor_kind=anchor_kind,
        anchor_path=anchor_path,
        paper_line_state_path=paper_line_state_path if paper_line_state is not None else None,
        paper_line_state=paper_line_state,
        main_result_path=main_result_path,
        main_result=main_result,
        compile_report_path=compile_report_path,
        compile_report=compile_report,
        latest_gate_path=latest_gate_path,
        latest_gate=latest_gate,
        active_run_stdout_path=stdout_path,
        recent_stdout_lines=recent_lines,
        write_drift_detected=detect_write_drift(recent_lines),
        missing_deliverables=missing_deliverables,
        present_deliverables=present_deliverables,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
        submission_minimal_manifest_path=submission_minimal_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
        submission_minimal_docx_present=bool(submission_minimal_docx_path and submission_minimal_docx_path.exists()),
        submission_minimal_pdf_present=bool(submission_minimal_pdf_path and submission_minimal_pdf_path.exists()),
    )


def build_gate_report(state: GateState) -> dict[str, Any]:
    baseline_items = (state.main_result or {}).get("baseline_comparisons", {}).get("items") or []
    primary_delta = None
    for item in baseline_items:
        if item.get("metric_id") == "roc_auc":
            primary_delta = item.get("delta")
            break
    latest_gate_up_to_date = (
        state.latest_gate_path is not None
        and state.latest_gate_path.stat().st_mtime >= state.anchor_path.stat().st_mtime
    )
    blockers: list[str] = []
    if state.anchor_kind == "main_result":
        allow_write = gate_allows_write(state.latest_gate, state.latest_gate_path, state.main_result_path)
        if not latest_gate_up_to_date:
            blockers.append("missing_post_main_publishability_gate")
        if state.missing_deliverables:
            blockers.append("missing_required_non_scalar_deliverables")
        if state.write_drift_detected and not allow_write:
            blockers.append("active_run_drifting_into_write_without_gate_approval")
    elif state.anchor_kind == "paper_bundle":
        allow_write = (
            state.compile_report_path is not None
            and state.submission_minimal_manifest is not None
            and state.submission_minimal_docx_present
            and state.submission_minimal_pdf_present
        )
        if state.compile_report_path is None or state.compile_report is None:
            blockers.append("missing_paper_compile_report")
        if (
            state.submission_minimal_manifest is None
            or not state.submission_minimal_docx_present
            or not state.submission_minimal_pdf_present
        ):
            blockers.append("missing_submission_minimal")
    else:
        allow_write = False
        blockers.append("missing_publication_anchor")

    results_summary = None
    conclusion = None
    if state.main_result is not None:
        results_summary = state.main_result.get("results_summary")
        conclusion = state.main_result.get("conclusion")
    if not results_summary:
        results_summary = (state.compile_report or {}).get("summary") or (state.paper_bundle_manifest or {}).get("summary")
    if not conclusion:
        conclusion = (state.paper_bundle_manifest or {}).get("summary") or (state.compile_report or {}).get("summary")

    return {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": utc_now(),
        "anchor_kind": state.anchor_kind,
        "anchor_path": str(state.anchor_path),
        "quest_id": (state.main_result or {}).get("quest_id") or state.quest_root.name,
        "run_id": (
            (state.main_result or {}).get("run_id")
            or (state.paper_line_state or {}).get("paper_line_id")
            or state.runtime_state.get("active_run_id")
        ),
        "main_result_path": str(state.main_result_path) if state.main_result_path else None,
        "paper_line_state_path": str(state.paper_line_state_path) if state.paper_line_state_path else None,
        "compile_report_path": str(state.compile_report_path) if state.compile_report_path else None,
        "latest_gate_path": str(state.latest_gate_path) if state.latest_gate_path else None,
        "allow_write": allow_write,
        "recommended_action": (
            publication_gate_policy.BLOCKED_RECOMMENDED_ACTION
            if blockers
            else publication_gate_policy.CLEAR_RECOMMENDED_ACTION
        ),
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "write_drift_detected": state.write_drift_detected,
        "required_non_scalar_deliverables": list(
            (state.main_result or {}).get("metric_contract", {}).get("required_non_scalar_deliverables") or []
        ),
        "present_non_scalar_deliverables": state.present_deliverables,
        "missing_non_scalar_deliverables": state.missing_deliverables,
        "paper_bundle_manifest_path": str(state.paper_bundle_manifest_path) if state.paper_bundle_manifest_path else None,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path) if state.submission_minimal_manifest_path else None
        ),
        "submission_minimal_present": state.submission_minimal_manifest is not None,
        "submission_minimal_docx_present": state.submission_minimal_docx_present,
        "submission_minimal_pdf_present": state.submission_minimal_pdf_present,
        "headline_metrics": (state.main_result or {}).get("metrics_summary") or {},
        "primary_metric_delta_vs_baseline": primary_delta,
        "results_summary": results_summary,
        "conclusion": conclusion,
        "controller_note": publication_gate_policy.CONTROLLER_NOTE,
    }


def render_gate_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("blockers") or []
    missing = report.get("missing_non_scalar_deliverables") or []
    metrics = report.get("headline_metrics") or {}
    lines = [
        "# Publishability Gate Control Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_id: `{report['quest_id']}`",
        f"- run_id: `{report['run_id']}`",
        f"- status: `{report['status']}`",
        f"- allow_write: `{str(report['allow_write']).lower()}`",
        f"- recommended_action: `{report['recommended_action']}`",
        "",
        "## Why Blocked" if blockers else "## Status",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- No controller-level blocker detected.")
    lines.extend(
        [
            "",
            "## Headline Metrics",
            "",
            f"- `roc_auc`: `{metrics.get('roc_auc')}`",
            f"- `average_precision`: `{metrics.get('average_precision')}`",
            f"- `brier_score`: `{metrics.get('brier_score')}`",
            f"- `calibration_intercept`: `{metrics.get('calibration_intercept')}`",
            f"- `calibration_slope`: `{metrics.get('calibration_slope')}`",
            "",
            "## Missing Contract Deliverables",
            "",
        ]
    )
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Paper Package Status",
            "",
            f"- `anchor_kind`: `{report.get('anchor_kind')}`",
            f"- `anchor_path`: `{report.get('anchor_path')}`",
            f"- `paper_bundle_manifest_path`: `{report.get('paper_bundle_manifest_path')}`",
            f"- `compile_report_path`: `{report.get('compile_report_path')}`",
            f"- `submission_minimal_manifest_path`: `{report.get('submission_minimal_manifest_path')}`",
            f"- `submission_minimal_present`: `{str(report.get('submission_minimal_present')).lower()}`",
            f"- `submission_minimal_docx_present`: `{str(report.get('submission_minimal_docx_present')).lower()}`",
            f"- `submission_minimal_pdf_present`: `{str(report.get('submission_minimal_pdf_present')).lower()}`",
            "",
            "## Result Context",
            "",
            f"- {report.get('results_summary')}",
            f"- {report.get('conclusion')}",
            "",
            "## Controller Scope",
            "",
            f"- {report.get('controller_note')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_gate_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="publishability_gate",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_gate_markdown(report),
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    source: str = "codex-publication-gate",
) -> dict[str, Any]:
    state = build_gate_state(quest_root)
    report = build_gate_report(state)
    json_path, md_path = write_gate_files(quest_root, report)
    intervention = None
    if apply and report["blockers"]:
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=publication_gate_policy.build_intervention_message(report),
            source=source,
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "allow_write": report["allow_write"],
        "blockers": report["blockers"],
        "missing_non_scalar_deliverables": report["missing_non_scalar_deliverables"],
        "submission_minimal_present": report["submission_minimal_present"],
        "intervention_enqueued": bool(intervention),
        "message_id": intervention.get("message_id") if intervention else None,
        "source": source,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_controller(quest_root=args.quest_root, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
