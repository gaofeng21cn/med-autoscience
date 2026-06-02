from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers.study_domain_transition_table_parts import ai_reviewer_transitions
from med_autoscience.controllers.study_domain_transition_table_parts import default_executor_receipts
from med_autoscience.controllers.study_domain_transition_table_parts import family_transition_spec
from med_autoscience.controllers.study_domain_transition_table_parts import publication_gate_lifecycle_transitions
from med_autoscience.controllers.study_domain_transition_table_parts import story_surface_recheck_transition
from med_autoscience.study_delivery_package_contract import delivered_package_handoff_allowed, live_delivered_package_handoff_allowed


SURFACE = "study_domain_transition_table"
SCHEMA_VERSION = 1
PUBLICATION_EVAL_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = story_surface_recheck_transition.REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH
PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH = (
    publication_gate_lifecycle_transitions.PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH
)
_BUNDLE_STAGE_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_FINALIZE_WORK_UNIT_IDS = frozenset(
    {
        "publication_gate_replay",
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)


def project_domain_transition(
    *,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
    macro_state: Mapping[str, Any],
    active_run_id: str | None,
    running_provider_attempt: bool | None = None,
    delivered_package: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    publication_eval, publication_eval_ref = _read_relative_json(root, PUBLICATION_EVAL_RELATIVE_PATH)
    current_ai_reviewer_record = ai_reviewer_publication_eval_records.latest_current_ai_reviewer_publication_eval_record(
        study_root=root,
        current_publication_eval=publication_eval,
    )
    if current_ai_reviewer_record is not None:
        publication_eval, current_record_ref = current_ai_reviewer_record
        publication_eval_ref = ai_reviewer_publication_eval_records.projection_source_ref(
            publication_eval,
            current_record_ref,
        )
    controller_decision, controller_decision_ref = _read_relative_json(root, CONTROLLER_DECISION_RELATIVE_PATH)
    repair_evidence, repair_evidence_ref = _read_relative_json(root, REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    work_unit_lifecycle, work_unit_lifecycle_ref = _read_relative_json(
        root,
        PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH,
    )
    execution_receipt_consumption = study_transition_receipt_consumption.execution_receipt_consumption(status)
    ai_reviewer_receipt_consumption = (
        study_transition_receipt_consumption.ai_reviewer_publication_eval_receipt_consumption(
            publication_eval=publication_eval,
            publication_eval_ref=Path(publication_eval_ref) if publication_eval_ref else PUBLICATION_EVAL_RELATIVE_PATH,
        )
    )
    human_gate_resume_receipt_consumption = (
        study_transition_receipt_consumption.human_gate_resume_receipt_consumption(
            study_root=root,
            controller_decision=controller_decision,
            controller_decision_ref=CONTROLLER_DECISION_RELATIVE_PATH,
        )
    )
    owner_apply_receipt_consumption = study_transition_receipt_consumption.mas_owner_apply_receipt_consumption(
        study_root=root
    )
    memory_writeback_receipt_consumption = (
        study_transition_receipt_consumption.publication_route_memory_writeback_receipt_consumption(
            study_root=root
        )
    )
    source_refs = _present_refs(
        publication_eval_ref,
        controller_decision_ref,
        repair_evidence_ref,
        work_unit_lifecycle_ref,
        _text(execution_receipt_consumption.get("source_ref")),
        _text(human_gate_resume_receipt_consumption.get("receipt_ref")),
        _text(human_gate_resume_receipt_consumption.get("decision_ref")),
        _text(owner_apply_receipt_consumption.get("receipt_ref")),
        _text(owner_apply_receipt_consumption.get("evidence_ref")),
        *_text_list(memory_writeback_receipt_consumption.get("router_receipt_refs")),
        *_text_list(memory_writeback_receipt_consumption.get("writeback_receipt_refs")),
        "progress_projection",
        "study_macro_state",
    )

    projection_error = _mapping(status.get("status_projection_error")) or _mapping(status.get("projection_error"))
    if projection_error:
        return _transition(
            study_id=study_id,
            decision_type="fail_closed",
            route_target="inspect",
            next_work_unit=_work_unit(
                "progress_projection_inspection",
                "controller",
                "Inspect progress projection error before any transition or write.",
            ),
            controller_action="none",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="progress_projection_error",
                blocker_type="projection_contract_error",
                summary=_text(projection_error.get("message"))
                or "Progress projection failed; MAS must fail closed for this study.",
                required_owner_surface="progress_projection",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
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
                required_owner_surface="progress_projection + study_macro_state",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
        )

    if human_gate_resume_receipt_consumption:
        return _transition(
            study_id=study_id,
            decision_type="human_gate_resume_receipt_consumed",
            route_target="runtime",
            next_work_unit=_work_unit(
                "human_gate_resume_receipt",
                "runtime",
                "Resume only after consuming the MAS-owned human gate receipt.",
            ),
            controller_action="resume_runtime_after_human_gate",
            owner="med-autoscience",
            typed_blocker=None,
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
            completion_receipt_consumption=human_gate_resume_receipt_consumption,
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
            completion_receipt_consumption=execution_receipt_consumption,
        )

    if _is_stop_loss(macro_state=macro_state, controller_decision=controller_decision, status=status):
        stop_loss_receipt_consumption = owner_apply_receipt_consumption or execution_receipt_consumption
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
            completion_receipt_consumption=stop_loss_receipt_consumption,
        )

    active_runtime_present = active_run_id is not None and running_provider_attempt is not False
    delivered_package_observed = bool(delivered_package and delivered_package.get("observed") is True)
    if delivered_package_observed and (
        delivered_package_handoff_allowed(publication_eval)
        or (active_runtime_present and live_delivered_package_handoff_allowed(publication_eval))
    ):
        return _delivered_package_handoff_transition(
            study_id=study_id,
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
        )

    stale_reviewer_revision_transition = ai_reviewer_transitions.project_stale_reviewer_revision_transition(
        study_id=study_id,
        study_root=root,
        publication_eval=publication_eval,
        publication_eval_relative_path=PUBLICATION_EVAL_RELATIVE_PATH,
        source_refs=source_refs,
        completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
    )
    if stale_reviewer_revision_transition is not None:
        return stale_reviewer_revision_transition

    review_recheck_transition = story_surface_recheck_transition.project_transition(
        study_root=root,
        study_id=study_id,
        lifecycle=work_unit_lifecycle,
        lifecycle_ref=work_unit_lifecycle_ref,
        publication_eval=publication_eval,
        source_refs=source_refs,
        completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
    )
    if review_recheck_transition is not None:
        consumed_transition = _consumed_default_executor_transition(
            study_id=study_id,
            quest_id=_text(status.get("quest_id")),
            study_root=root,
            status=status,
            publication_eval=publication_eval,
            transition=review_recheck_transition,
            active_run_id=active_run_id,
        )
        return consumed_transition or review_recheck_transition

    ai_reviewer_transition = ai_reviewer_transitions.project_transition(
        study_id=study_id,
        study_root=root,
        publication_eval=publication_eval,
        active_run_id=active_run_id if active_runtime_present else None,
        publication_eval_relative_path=PUBLICATION_EVAL_RELATIVE_PATH,
        source_refs=source_refs,
        completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
    )
    if ai_reviewer_transition is not None:
        consumed_transition = _consumed_default_executor_transition(
            study_id=study_id,
            quest_id=_text(status.get("quest_id")),
            study_root=root,
            status=status,
            publication_eval=publication_eval,
            transition=ai_reviewer_transition,
            active_run_id=active_run_id,
        )
        return consumed_transition or ai_reviewer_transition

    if _publication_gate_blocked(publication_eval, status=status):
        publication_gate_transition = _transition(
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
            completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
        )
        consumed_transition = _consumed_default_executor_transition(
            study_id=study_id,
            quest_id=_text(status.get("quest_id")),
            study_root=root,
            status=status,
            publication_eval=publication_eval,
            transition=publication_gate_transition,
            active_run_id=active_run_id,
        )
        return consumed_transition or publication_gate_transition

    bundle_stage_work_unit = _bundle_stage_finalize_work_unit(
        status=status,
        publication_eval=publication_eval,
        controller_decision=controller_decision,
    )
    if bundle_stage_work_unit is not None:
        bundle_stage_consumption = study_transition_receipt_consumption.bundle_stage_completion_receipt_consumption(
            study_root=root,
            publication_eval=publication_eval,
            work_unit=bundle_stage_work_unit,
            controller_decision=controller_decision,
        )
        if bundle_stage_consumption:
            completion_source_refs = _present_refs(
                publication_eval_ref,
                controller_decision_ref,
                _text(bundle_stage_consumption.get("completion_ref")),
                _text(bundle_stage_consumption.get("artifact_ref")),
                "progress_projection",
                "study_macro_state",
            )
            return _transition(
                study_id=study_id,
                decision_type="completion_receipt_consumed",
                route_target="human_gate",
                next_work_unit=_work_unit(
                    "package_closure_consumed_handoff",
                    "finalize",
                    "Expose the completed package closure receipt without redriving the consumed work unit.",
                ),
                controller_action="none",
                owner="med-autoscience",
                typed_blocker=_typed_blocker(
                    blocker_id="completed_work_unit_consumed",
                    blocker_type="completion_receipt",
                    summary=(
                        "Bundle-stage package closure has already consumed this work unit; automatic redrive is forbidden."
                    ),
                    required_owner_surface=_text(bundle_stage_consumption.get("completion_ref"))
                    or "runtime_turn_closeout",
                ),
                guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
                source_refs=completion_source_refs,
                completion_receipt_consumption=bundle_stage_consumption,
            )
        return _transition(
            study_id=study_id,
            decision_type="bundle_stage_finalize",
            route_target="finalize",
            next_work_unit=bundle_stage_work_unit,
            controller_action="continue_bundle_stage",
            owner="publication_gate",
            typed_blocker=None,
            guard_boundary=_guard_boundary(required_owner_surface=str(PUBLICATION_EVAL_RELATIVE_PATH)),
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
        )

    if owner_apply_receipt_consumption or _meaningful_artifact_delta(repair_evidence):
        return _transition(
            study_id=study_id,
            decision_type="owner_apply_receipt_consumed"
            if owner_apply_receipt_consumption
            else "artifact_delta_live_apply",
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
            completion_receipt_consumption=owner_apply_receipt_consumption or execution_receipt_consumption,
        )

    if active_runtime_present:
        return _transition(
            study_id=study_id,
            decision_type="active_domain_health_diagnostic",
            route_target="diagnostic",
            next_work_unit=_work_unit(
                "domain_health_diagnostic_active_run",
                "diagnostic",
                "Observe the active MAS runtime run through domain health diagnostic refs.",
            ),
            controller_action="domain_health_diagnostic",
            owner="med-autoscience",
            typed_blocker=None,
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=True),
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
        )

    if memory_writeback_receipt_consumption:
        return _transition(
            study_id=study_id,
            decision_type="memory_writeback_receipt_consumed",
            route_target="inspect",
            next_work_unit=_work_unit(
                "publication_route_memory_writeback_receipt_review",
                "inspect",
                "Review MAS-owned publication-route memory writeback receipt refs without reading memory body.",
            ),
            controller_action="none",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="memory_writeback_receipt_observed",
                blocker_type="memory_writeback_receipt",
                summary=(
                    "Publication-route memory writeback receipt was observed; MAS exposes refs only and keeps "
                    "generic runner resume disabled."
                ),
                required_owner_surface="artifacts/stage_knowledge/memory_write_router_receipts",
            ),
            guard_boundary=_guard_boundary(
                required_owner_surface="memory_write_router_receipt",
                opl_generic_runner_may_resume=False,
            ),
            source_refs=source_refs,
            completion_receipt_consumption=memory_writeback_receipt_consumption,
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
            completion_receipt_consumption=execution_receipt_consumption,
        )

    if delivered_package_observed:
        return _delivered_package_handoff_transition(
            study_id=study_id,
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
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
            required_owner_surface="progress_projection + study_macro_state",
        ),
        guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
        source_refs=source_refs,
        completion_receipt_consumption=execution_receipt_consumption,
    )


def _consumed_default_executor_transition(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    status: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    transition: Mapping[str, Any],
    active_run_id: str | None,
) -> dict[str, Any] | None:
    receipt = default_executor_receipts.consumed_current_transition_receipt(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        status=status,
        publication_eval_payload=publication_eval,
        transition=transition,
        active_run_id=active_run_id,
    )
    if not receipt:
        return None
    return _transition(
        study_id=study_id,
        decision_type="completion_receipt_consumed",
        route_target="inspect",
        next_work_unit=_work_unit(
            "default_executor_owner_receipt_consumed_handoff",
            "controller",
            "Expose the consumed default-executor owner receipt without redriving the current work unit.",
        ),
        controller_action="none",
        owner="med-autoscience",
        typed_blocker=_typed_blocker(
            blocker_id="completed_work_unit_consumed",
            blocker_type="completion_receipt",
            summary="Default-executor owner receipt already consumed this work unit; automatic redrive is forbidden.",
            required_owner_surface=_text(receipt.get("receipt_ref")) or "paper/review",
        ),
        guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
        source_refs=[
            *_text_list(transition.get("source_refs")),
            *([receipt_ref] if (receipt_ref := _text(receipt.get("receipt_ref"))) else []),
        ],
        completion_receipt_consumption=receipt,
    )


def _delivered_package_handoff_transition(
    *,
    study_id: str,
    source_refs: list[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any]:
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
        completion_receipt_consumption=completion_receipt_consumption,
    )


def build_domain_transition_table(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    counts: dict[str, int] = {}
    for row in normalized_rows:
        decision_type = _text(row.get("decision_type")) or "unknown"
        counts[decision_type] = counts.get(decision_type, 0) + 1
    family_spec = build_family_transition_spec(normalized_rows)
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
        "family_transition_spec": family_spec,
        "family_transition_matrix_cases": build_family_transition_matrix_cases(normalized_rows),
    }


def build_family_transition_spec(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return family_transition_spec.build_family_transition_spec(rows)


def build_family_transition_matrix_cases(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return family_transition_spec.build_family_transition_matrix_cases(rows)


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
    completion_receipt_consumption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
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
    if completion_receipt_consumption:
        payload["completion_receipt_consumption"] = dict(completion_receipt_consumption)
    return payload


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


def build_family_transition_spec_descriptor() -> dict[str, Any]:
    return family_transition_spec.build_family_transition_spec_descriptor()


def _read_relative_json(study_root: Path, relative_path: Path) -> tuple[dict[str, Any], str | None]:
    path = study_root / relative_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, None
    if not isinstance(payload, Mapping):
        return {}, None
    return dict(payload), str(relative_path)


def _present_refs(*refs: object) -> list[str]:
    return [text for ref in refs if (text := _text(ref))]


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


def _publication_gate_blocked(publication_eval: Mapping[str, Any], *, status: Mapping[str, Any]) -> bool:
    if _status_reports_current_publication_gate_continue(status):
        return False
    if _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval":
        return False
    verdict = _mapping(publication_eval.get("verdict"))
    gaps = [item for item in publication_eval.get("gaps") or [] if isinstance(item, Mapping)]
    return (
        _text(publication_eval.get("status")) == "blocked"
        or bool(publication_eval.get("blockers"))
        or _text(verdict.get("overall_verdict")) == "blocked"
        or any(_text(item.get("severity")) in {"must_fix", "blocking", "blocked"} for item in gaps)
        or ai_reviewer_transitions.requires_owner_authorized_publication_gate_recheck_only(publication_eval)
    )


def _status_reports_current_publication_gate_continue(status: Mapping[str, Any]) -> bool:
    supervisor = _mapping(status.get("publication_supervisor_state"))
    return (
        _text(supervisor.get("supervisor_phase")) == "bundle_stage_ready"
        and _text(supervisor.get("current_required_action")) == "continue_bundle_stage"
    )


def _bundle_stage_finalize_work_unit(
    *,
    status: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, str] | None:
    if not _status_reports_bundle_stage(status) and not _publication_eval_reports_bundle_stage(publication_eval):
        return None
    if not _publication_eval_clear(publication_eval):
        return None
    unit = _first_finalize_work_unit(publication_eval.get("recommended_actions"))
    if unit is not None:
        return unit
    unit = _compact_work_unit(controller_decision.get("next_work_unit"))
    if unit is not None and _work_unit_is_finalize(unit):
        return unit
    return _work_unit(
        "submission_authority_sync_closure",
        "controller",
        "Synchronize submission authority and package closure for the bundle-stage.",
    )


def _status_reports_bundle_stage(status: Mapping[str, Any]) -> bool:
    supervisor = _mapping(status.get("publication_supervisor_state"))
    phase = _text(supervisor.get("supervisor_phase"))
    action = _text(supervisor.get("current_required_action"))
    return phase in {"bundle_stage_ready", "bundle_stage_blocked"} and action in _BUNDLE_STAGE_ACTIONS


def _publication_eval_reports_bundle_stage(publication_eval: Mapping[str, Any]) -> bool:
    return _text(publication_eval.get("current_required_action")) in _BUNDLE_STAGE_ACTIONS


def _publication_eval_clear(publication_eval: Mapping[str, Any]) -> bool:
    if _text(publication_eval.get("status")) not in {"clear", ""}:
        return False
    if publication_eval.get("allow_write") is False:
        return False
    blockers = [_text(item) for item in publication_eval.get("blockers") or []]
    return not any(blockers)


def _first_finalize_work_unit(actions: object) -> dict[str, str] | None:
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        route_target = _text(action.get("route_target"))
        unit = _compact_work_unit(action.get("next_work_unit"))
        if route_target == "finalize" and unit is not None and _work_unit_is_finalize(unit):
            return unit
        if unit is not None and _work_unit_is_finalize(unit):
            return unit
    return None


def _compact_work_unit(value: object) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    unit_id = _text(value.get("unit_id"))
    if not unit_id:
        return None
    payload = {"unit_id": unit_id}
    for key in ("lane", "summary"):
        text = _text(value.get(key))
        if text:
            payload[key] = text
    return payload


def _work_unit_is_finalize(unit: Mapping[str, Any]) -> bool:
    return _text(unit.get("lane")) == "finalize" or _text(unit.get("unit_id")) in _FINALIZE_WORK_UNIT_IDS


def _meaningful_artifact_delta(repair_evidence: Mapping[str, Any]) -> bool:
    return _mapping(repair_evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = [
    "build_domain_transition_table",
    "build_family_transition_spec_descriptor",
    "build_family_transition_matrix_cases",
    "build_family_transition_spec",
    "project_domain_transition",
]
