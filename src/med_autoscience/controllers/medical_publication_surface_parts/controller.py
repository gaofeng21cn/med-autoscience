from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.medical_journal_style_corpus import (
    ensure_current_medical_journal_style_corpus,
    stable_medical_journal_style_corpus_path,
)
from med_autoscience.medical_prose_review_request import (
    materialize_medical_prose_review_request,
    stable_medical_prose_review_request_path,
)
from med_autoscience.controllers.opl_pending_user_message_handoff import build_pending_user_message_handoff
from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store

from .shared import (
    _controller_override,
    build_surface_state,
    resolve_runtime_root_from_quest_root,
)
from .reporting import (
    _append_materialization_error,
    _materialization_error_hit,
    build_surface_report,
    render_surface_markdown,
)

def write_surface_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    report_store = _controller_override("runtime_protocol_report_store", runtime_protocol_report_store)
    return report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="medical_publication_surface",
        timestamp=report["generated_at"],
        report=report,
        markdown=render_surface_markdown(report),
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    daemon_url: str | None = None,
    source: str = "codex-medical-publication-surface",
) -> dict[str, Any]:
    state = build_surface_state(quest_root)
    style_corpus_path = None
    prose_review_request_path = None
    materialization_error_hit = None
    if apply and state.study_root is not None:
        ensure_current_medical_journal_style_corpus(study_root=state.study_root)
        style_corpus_path = stable_medical_journal_style_corpus_path(study_root=state.study_root)
        prose_review_request_path = stable_medical_prose_review_request_path(study_root=state.study_root)
        try:
            materialize_medical_prose_review_request(
                study_root=state.study_root,
                paper_root=state.paper_root,
                manuscript_path=state.draft_path,
            )
        except (OSError, TypeError, ValueError) as exc:
            materialization_error_hit = _materialization_error_hit(
                state=state,
                artifact_path=prose_review_request_path,
                error=exc,
            )
    report = build_surface_report(state)
    if materialization_error_hit is not None:
        report = _append_materialization_error(report, materialization_error_hit)
    json_path, md_path = write_surface_files(quest_root, report)
    stop_result = None
    intervention = None
    if apply and report["blockers"]:
        current_status = str(state.runtime_state.get("status") or "").strip().lower()
        if current_status in {"running", "active"} and daemon_url:
            stop_result = {
                "status": "owner_route_required",
                "reason": "opl_current_control_state_stop_required",
                "queue_owner": "one-person-lab",
                "runtime_state_mutated": False,
                "quest_id": report["quest_id"],
                "source": source,
            }
        intervention = build_pending_user_message_handoff(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=medical_surface_policy.build_intervention_message(report),
            source=source,
            evidence_refs=[str(json_path)],
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "blockers": report["blockers"],
        "top_hits": report["top_hits"],
        "medical_manuscript_blueprint_path": report.get("medical_manuscript_blueprint_path"),
        "medical_prose_review_path": report.get("medical_prose_review_path"),
        "style_corpus_path": str(style_corpus_path) if style_corpus_path is not None else None,
        "medical_prose_review_request_path": (
            str(prose_review_request_path) if prose_review_request_path is not None else None
        ),
        "medical_journal_prose_ai_verdict": report.get("medical_journal_prose_ai_verdict"),
        "medical_journal_prose_mechanical_flag_count": report.get("medical_journal_prose_mechanical_flag_count"),
        "stop_result": stop_result,
        "intervention_enqueued": False,
        "intervention_handoff": intervention,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--daemon-url", default="http://127.0.0.1:20999")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_controller(
        quest_root=args.quest_root,
        apply=args.apply,
        daemon_url=args.daemon_url,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


__all__ = [name for name in globals() if not name.startswith("__")]
