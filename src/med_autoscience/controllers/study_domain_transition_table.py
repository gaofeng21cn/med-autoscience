from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SURFACE = "study_domain_transition_table"
SCHEMA_VERSION = 1
PUBLICATION_EVAL_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")


def project_domain_transition(
    *,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
    macro_state: Mapping[str, Any],
    active_run_id: str | None,
    delivered_package: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    publication_eval, publication_eval_ref = _read_relative_json(root, PUBLICATION_EVAL_RELATIVE_PATH)
    controller_decision, controller_decision_ref = _read_relative_json(root, CONTROLLER_DECISION_RELATIVE_PATH)
    repair_evidence, repair_evidence_ref = _read_relative_json(root, REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    source_refs = _present_refs(
        publication_eval_ref,
        controller_decision_ref,
        repair_evidence_ref,
        "study_runtime_status",
        "study_macro_state",
    )

    if _text(macro_state.get("writer_state")) == "conflict" or _text(macro_state.get("reason")) == "truth_conflict":
        return _transition(
            study_id=study_id,
            decision_type="fail_closed",
            route_target="inspect",
            next_work_unit=_work_unit(
                "truth_conflict_inspection",
                "controller",
                "Inspect conflicting MAS truth surfaces before any transition or write.",
            ),
            controller_action="none",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="truth_conflict",
                blocker_type="truth_conflict",
                summary="Study truth surfaces disagree; MAS must fail closed until owner inspection resolves them.",
                required_owner_surface="study_runtime_status + study_macro_state",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
        )

    if _requires_human_gate(controller_decision):
        return _transition(
            study_id=study_id,
            decision_type="human_gate",
            route_target="human_gate",
            next_work_unit=_work_unit(
                "human_gate_resume",
                "decision",
                "Wait for the explicit human gate response before resuming the study line.",
            ),
            controller_action="wait_for_human_gate",
            owner="human_gate",
            typed_blocker=_typed_blocker(
                blocker_id="human_gate_required",
                blocker_type="human_gate",
                summary="MAS controller decision requires explicit human confirmation.",
                required_owner_surface=str(CONTROLLER_DECISION_RELATIVE_PATH),
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
        )

    if _is_stop_loss(macro_state=macro_state, controller_decision=controller_decision, status=status):
        return _transition(
            study_id=study_id,
            decision_type="stop_loss",
            route_target="stop",
            next_work_unit=_work_unit(
                "stop_loss_handoff",
                "decision",
                "Keep the study stopped unless a new MAS owner plan explicitly reopens it.",
            ),
            controller_action="stop_runtime",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="stop_loss_active",
                blocker_type="stop_loss",
                summary="Study is parked by stop-loss or user stop policy; automatic runner resume is forbidden.",
                required_owner_surface="study_macro_state",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
        )

    if _publication_gate_blocked(publication_eval):
        return _transition(
            study_id=study_id,
            decision_type="publication_gate_blocker",
            route_target="review",
            next_work_unit=_work_unit(
                "publication_gate_replay",
                "review",
                "Replay the MAS publication gate and route blockers to a bounded repair unit.",
            ),
            controller_action="run_gate_clearing_batch",
            owner="publication_gate",
            typed_blocker=_typed_blocker(
                blocker_id="publication_gate_blocked",
                blocker_type="publication_gate",
                summary="Publication gate has unresolved blockers; paper closure and workspace writes remain blocked.",
                required_owner_surface=str(PUBLICATION_EVAL_RELATIVE_PATH),
            ),
            guard_boundary=_guard_boundary(required_owner_surface=str(PUBLICATION_EVAL_RELATIVE_PATH)),
            source_refs=source_refs,
        )

    if _ai_reviewer_re_eval(publication_eval):
        return _transition(
            study_id=study_id,
            decision_type="ai_reviewer_re_eval",
            route_target="review",
            next_work_unit=_work_unit(
                "ai_reviewer_recheck",
                "review",
                "Return the current manuscript and evidence refs to the AI reviewer workflow.",
            ),
            controller_action="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            typed_blocker=None,
            guard_boundary=_guard_boundary(required_owner_surface=str(PUBLICATION_EVAL_RELATIVE_PATH)),
            source_refs=source_refs,
        )

    if _meaningful_artifact_delta(repair_evidence):
        return _transition(
            study_id=study_id,
            decision_type="artifact_delta_live_apply",
            route_target="finalize",
            next_work_unit=_work_unit(
                "provider_hosted_guarded_apply",
                "finalize",
                "Apply artifact delta only through MAS-owned guarded apply receipt.",
            ),
            controller_action="paper_autonomy_guarded_apply",
            owner="med-autoscience",
            typed_blocker=None,
            guard_boundary=_guard_boundary(
                required_owner_surface="mas_owner_apply_receipt",
                mas_owner_apply_receipt_required=True,
            ),
            source_refs=source_refs,
        )

    if active_run_id:
        return _transition(
            study_id=study_id,
            decision_type="active_runtime_watch",
            route_target="runtime",
            next_work_unit=_work_unit("watch_active_run", "runtime", "Watch the active MAS runtime run."),
            controller_action="runtime_watch",
            owner="mas_runtime",
            typed_blocker=None,
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=True),
            source_refs=source_refs,
        )

    if _text(macro_state.get("user_next")) == "submit_info":
        return _transition(
            study_id=study_id,
            decision_type="human_gate",
            route_target="human_gate",
            next_work_unit=_work_unit(
                "submission_metadata_intake",
                "decision",
                "Collect missing submission metadata before any publication-ready claim.",
            ),
            controller_action="wait_for_human_gate",
            owner="human_gate",
            typed_blocker=_typed_blocker(
                blocker_id="submission_metadata_required",
                blocker_type="human_gate",
                summary="Submission metadata is missing and must be supplied by the user.",
                required_owner_surface="submission_metadata",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
        )

    if delivered_package and delivered_package.get("observed") is True:
        return _transition(
            study_id=study_id,
            decision_type="delivered_package_handoff",
            route_target="human_gate",
            next_work_unit=_work_unit(
                "package_review_handoff",
                "finalize",
                "Expose the delivered package as a user-visible milestone without reopening quality authority.",
            ),
            controller_action="wait_for_human_gate",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="package_delivered_not_publication_authority",
                blocker_type="artifact_authority",
                summary="Delivered package is a milestone, not a publication-ready quality verdict.",
                required_owner_surface="artifact_rebuild_proof",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
        )

    return _transition(
        study_id=study_id,
        decision_type="fail_closed",
        route_target="inspect",
        next_work_unit=_work_unit(
            "domain_transition_owner_inspection",
            "controller",
            "Inspect MAS owner surfaces before routing an unclassified state.",
        ),
        controller_action="none",
        owner="med-autoscience",
        typed_blocker=_typed_blocker(
            blocker_id="domain_transition_unclassified",
            blocker_type="fail_closed",
            summary="No MAS-owned transition rule matched this state combination.",
            required_owner_surface="study_runtime_status + study_macro_state",
        ),
        guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
        source_refs=source_refs,
    )


def build_domain_transition_table(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    counts: dict[str, int] = {}
    for row in normalized_rows:
        decision_type = _text(row.get("decision_type")) or "unknown"
        counts[decision_type] = counts.get(decision_type, 0) + 1
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "table_role": "domain_transition_read_model_oracle",
        "authority_boundary": {
            "owner": "MedAutoScience",
            "runner_owner": "OPL Framework",
            "can_write_domain_truth": False,
            "can_execute_generic_state_machine": False,
            "purpose": "MAS-owned domain transition spec/read model; OPL remains responsible for generic runner execution.",
        },
        "counts": counts,
        "rows": normalized_rows,
    }


def _transition(
    *,
    study_id: str,
    decision_type: str,
    route_target: str,
    next_work_unit: Mapping[str, Any],
    controller_action: str,
    owner: str,
    typed_blocker: Mapping[str, Any] | None,
    guard_boundary: Mapping[str, Any],
    source_refs: Iterable[str],
) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "decision_type": decision_type,
        "route_target": route_target,
        "next_work_unit": dict(next_work_unit),
        "controller_action": controller_action,
        "owner": owner,
        "typed_blocker": dict(typed_blocker) if typed_blocker else None,
        "guard_boundary": dict(guard_boundary),
        "source_refs": list(source_refs),
    }


def _work_unit(unit_id: str, lane: str, summary: str) -> dict[str, str]:
    return {"unit_id": unit_id, "lane": lane, "summary": summary}


def _typed_blocker(
    *,
    blocker_id: str,
    blocker_type: str,
    summary: str,
    required_owner_surface: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "blocker_type": blocker_type,
        "summary": summary,
        "required_owner_surface": required_owner_surface,
        "write_permitted": False,
    }


def _guard_boundary(
    *,
    required_owner_surface: str | None = None,
    mas_owner_apply_receipt_required: bool = False,
    opl_generic_runner_may_resume: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runner_boundary": "mas_domain_read_model_only",
        "can_write_domain_truth": False,
        "can_execute_generic_state_machine": False,
        "opl_generic_runner_may_resume": opl_generic_runner_may_resume,
        "mas_owner_apply_receipt_required": mas_owner_apply_receipt_required,
    }
    if required_owner_surface:
        payload["required_owner_surface"] = required_owner_surface
    return payload


def _read_relative_json(study_root: Path, relative_path: Path) -> tuple[dict[str, Any], str | None]:
    path = study_root / relative_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, None
    if not isinstance(payload, Mapping):
        return {}, None
    return dict(payload), str(relative_path)


def _present_refs(*refs: str | None) -> list[str]:
    return [ref for ref in refs if ref]


def _requires_human_gate(controller_decision: Mapping[str, Any]) -> bool:
    return controller_decision.get("requires_human_confirmation") is True or bool(
        controller_decision.get("family_human_gates")
    )


def _is_stop_loss(
    *,
    macro_state: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
    status: Mapping[str, Any],
) -> bool:
    candidates = {
        _text(macro_state.get("reason")),
        _text(controller_decision.get("decision_type")),
        _text(controller_decision.get("route_decision")),
        _text(controller_decision.get("route_target")),
        _text(status.get("reason")),
    }
    return bool({"stop_loss", "user_stop", "publishability_stop_loss_recommended", "stop"} & candidates)


def _publication_gate_blocked(publication_eval: Mapping[str, Any]) -> bool:
    if _text(_mapping(publication_eval.get("assessment_provenance")).get("owner")) == "ai_reviewer":
        return False
    if _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval":
        return False
    return _text(publication_eval.get("status")) == "blocked" or bool(publication_eval.get("blockers"))


def _ai_reviewer_re_eval(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval" or (
        _text(provenance.get("owner")) == "ai_reviewer"
        and _text(provenance.get("source_kind")) == "publication_eval_ai_reviewer"
    )


def _meaningful_artifact_delta(repair_evidence: Mapping[str, Any]) -> bool:
    return _mapping(repair_evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "build_domain_transition_table",
    "project_domain_transition",
]
