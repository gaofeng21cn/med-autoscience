from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_transition_receipt_consumption


SURFACE = "study_domain_transition_table"
SCHEMA_VERSION = 1
FAMILY_TRANSITION_SPEC_VERSION = "family-transition-runner.v1"
FAMILY_TRANSITION_TARGET_DOMAIN_ID = "medautoscience"
FAMILY_TRANSITION_OWNER = "med-autoscience"
PUBLICATION_EVAL_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")
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
    delivered_package: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    publication_eval, publication_eval_ref = _read_relative_json(root, PUBLICATION_EVAL_RELATIVE_PATH)
    controller_decision, controller_decision_ref = _read_relative_json(root, CONTROLLER_DECISION_RELATIVE_PATH)
    repair_evidence, repair_evidence_ref = _read_relative_json(root, REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    execution_receipt_consumption = study_transition_receipt_consumption.execution_receipt_consumption(status)
    ai_reviewer_receipt_consumption = (
        study_transition_receipt_consumption.ai_reviewer_publication_eval_receipt_consumption(
            publication_eval=publication_eval,
            publication_eval_ref=PUBLICATION_EVAL_RELATIVE_PATH,
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
    source_refs = _present_refs(
        publication_eval_ref,
        controller_decision_ref,
        repair_evidence_ref,
        _text(execution_receipt_consumption.get("source_ref")),
        _text(human_gate_resume_receipt_consumption.get("receipt_ref")),
        _text(human_gate_resume_receipt_consumption.get("decision_ref")),
        _text(owner_apply_receipt_consumption.get("receipt_ref")),
        _text(owner_apply_receipt_consumption.get("evidence_ref")),
        "study_runtime_status",
        "study_macro_state",
    )

    projection_error = _mapping(status.get("status_projection_error")) or _mapping(status.get("projection_error"))
    if projection_error:
        return _transition(
            study_id=study_id,
            decision_type="fail_closed",
            route_target="inspect",
            next_work_unit=_work_unit(
                "study_status_projection_inspection",
                "controller",
                "Inspect study status projection error before any transition or write.",
            ),
            controller_action="none",
            owner="med-autoscience",
            typed_blocker=_typed_blocker(
                blocker_id="study_status_projection_error",
                blocker_type="projection_contract_error",
                summary=_text(projection_error.get("message"))
                or "Study status projection failed; MAS must fail closed for this study.",
                required_owner_surface="study_runtime_status",
            ),
            guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
            source_refs=source_refs,
            completion_receipt_consumption=owner_apply_receipt_consumption or execution_receipt_consumption,
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
            completion_receipt_consumption=owner_apply_receipt_consumption or execution_receipt_consumption,
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
            completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
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
            completion_receipt_consumption=execution_receipt_consumption or ai_reviewer_receipt_consumption,
        )

    if (
        delivered_package
        and delivered_package.get("observed") is True
        and _publication_eval_clear(publication_eval)
    ):
        return _delivered_package_handoff_transition(
            study_id=study_id,
            source_refs=source_refs,
            completion_receipt_consumption=execution_receipt_consumption,
        )

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
                "study_runtime_status",
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
            completion_receipt_consumption=execution_receipt_consumption,
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

    if delivered_package and delivered_package.get("observed") is True:
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
            required_owner_surface="study_runtime_status + study_macro_state",
        ),
        guard_boundary=_guard_boundary(opl_generic_runner_may_resume=False),
        source_refs=source_refs,
        completion_receipt_consumption=execution_receipt_consumption,
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
    family_transition_spec = build_family_transition_spec(normalized_rows)
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
        "family_transition_spec": family_transition_spec,
        "family_transition_matrix_cases": build_family_transition_matrix_cases(normalized_rows),
    }


def build_family_transition_spec(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in normalized_rows:
        grouped.setdefault(_transition_key(row), []).append(row)
    guards: dict[str, dict[str, Any]] = {}
    transitions: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        representative = group[0]
        guard_id = _guard_id(key)
        source_refs = _unique_texts(ref for row in group for ref in row.get("source_refs") or [])
        guard_boundary = _mapping(representative.get("guard_boundary"))
        guards[guard_id] = {
            "description": f"MAS owner surfaces matched transition `{key}`.",
            "owner": _text(representative.get("owner")) or FAMILY_TRANSITION_OWNER,
            "source_ref": source_refs[0] if source_refs else None,
            "authority_boundary": {
                **dict(guard_boundary),
                "domain_transition_owner": "MedAutoScience",
                "can_write_domain_truth": False,
            },
        }
        transition = {
            "transition_id": f"mas-transition-{key}",
            "current_state": _current_state(key),
            "event": "domain_tick",
            "required_guards": [guard_id],
            "next_state": f"mas_route:{_text(representative.get('route_target')) or 'inspect'}",
            "next_work_unit": _family_work_unit(representative),
            "owner_route": _family_owner_route(representative),
            "receipt": {
                "receipt_refs": [
                    _receipt_ref(row)
                    for row in group
                    if _text(row.get("study_id"))
                ],
                "metadata": {"source_refs": source_refs},
            },
            "projection": {
                "route_node_refs": [
                    f"mas-route-node:{_text(representative.get('route_target')) or 'inspect'}",
                    f"mas-work-unit:{key}",
                ],
                "decision_type": _text(representative.get("decision_type")) or "unknown",
                "source_refs": source_refs,
                "domain_ready_verdict_owner": "med-autoscience",
            },
            "authority_boundary": {
                "domain_transition_owner": "MedAutoScience",
                "can_write_domain_truth": False,
                "can_execute_domain_action": False,
                "opl_interprets_domain_quality": False,
            },
        }
        receipt_consumption = _mapping(representative.get("completion_receipt_consumption"))
        if receipt_consumption:
            transition["receipt"]["completion_receipt_consumption"] = dict(receipt_consumption)
        typed_blocker = _family_typed_blocker(representative)
        if typed_blocker is not None:
            transition["typed_blocker"] = typed_blocker
        human_gate = _family_human_gate(representative)
        if human_gate is not None:
            transition["human_gate"] = human_gate
        transitions.append(transition)
    return {
        "surface_kind": "family_transition_spec",
        "version": FAMILY_TRANSITION_SPEC_VERSION,
        "spec_id": "mas-domain-transition-spec.v1",
        "target_domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
        "owner": FAMILY_TRANSITION_OWNER,
        "authority_boundary": {
            "opl": "transition_runner_transport_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "domain_transition_owner": "MedAutoScience",
            "domain_ready_verdict_owner": "med-autoscience",
            "artifact_authority_owner": "med-autoscience",
            "opl_interprets_domain_quality": False,
            "opl_executes_domain_action": False,
            "opl_writes_domain_truth": False,
        },
        "guards": guards,
        "transitions": transitions,
    }


def build_family_transition_matrix_cases(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        row_payload = dict(row)
        study_id = _text(row_payload.get("study_id"))
        if not study_id:
            continue
        key = _transition_key(row_payload)
        source_ref = _first_source_ref(row_payload)
        context = {"receipt_ref": _receipt_ref(row_payload)}
        if source_ref:
            context = {"source_ref": source_ref, **context}
        receipt_consumption = _mapping(row_payload.get("completion_receipt_consumption"))
        if receipt_consumption:
            context["completion_receipt_consumption"] = dict(receipt_consumption)
        expected = {
            "decision_type": _text(row_payload.get("decision_type")) or "unknown",
            "route_target": _text(row_payload.get("route_target")) or "inspect",
            "next_work_unit_id": _text(_mapping(row_payload.get("next_work_unit")).get("unit_id")),
            "controller_action": _text(row_payload.get("controller_action")) or "none",
            "owner": _text(row_payload.get("owner")) or FAMILY_TRANSITION_OWNER,
        }
        cases.append(
            {
                "case_id": f"{study_id}:{key}",
                "domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
                "current_state": _current_state(key),
                "event": "domain_tick",
                "guards": {_guard_id(key): True},
                "context": context,
                "expected": expected,
            }
        )
    return cases


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
    return {
        "surface_kind": "family_transition_spec_descriptor",
        "target_domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
        "spec_surface_kind": "family_transition_spec",
        "contract_version": FAMILY_TRANSITION_SPEC_VERSION,
        "refresh_policy": "rebuild_study_state_matrix_before_opl_runner",
        "materialized_surfaces": {
            "study_state_matrix": [
                "domain_transition_table.family_transition_spec",
                "domain_transition_table.family_transition_matrix_cases",
            ],
            "sidecar_export": ["family_transition_spec_descriptor"],
            "product_entry_manifest": ["family_transition_spec_descriptor"],
        },
        "authority_boundary": {
            "runner_owner": "OPL Framework",
            "domain_transition_owner": "MedAutoScience",
            "can_write_domain_truth": False,
            "opl_interprets_domain_quality": False,
            "opl_executes_domain_action": False,
        },
        "locator_refs": {
            "study_state_matrix_spec": "/study_state_matrix/domain_transition_table/family_transition_spec",
            "study_state_matrix_cases": "/study_state_matrix/domain_transition_table/family_transition_matrix_cases",
            "sidecar_export_descriptor": "/mas_family_sidecar_export/family_transition_spec_descriptor",
            "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
        },
        "source_refs": {
            "study_state_matrix_domain_transition_table": "/study_state_matrix/domain_transition_table",
            "sidecar_export_descriptor": "/mas_family_sidecar_export/family_transition_spec_descriptor",
            "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
        },
    }


def _transition_key(row: Mapping[str, Any]) -> str:
    unit = _mapping(row.get("next_work_unit"))
    return _slug(_text(unit.get("unit_id")) or _text(row.get("decision_type")) or "unclassified")


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return text or "unclassified"


def _current_state(key: str) -> str:
    return f"mas_domain_transition:{key}"


def _guard_id(key: str) -> str:
    return f"mas_guard_{key}"


def _first_source_ref(row: Mapping[str, Any]) -> str | None:
    for ref in row.get("source_refs") or []:
        text = _text(ref)
        if text:
            return text
    return None


def _receipt_ref(row: Mapping[str, Any]) -> str:
    return f"mas-domain-transition:{_text(row.get('study_id'))}:{_transition_key(row)}"


def _unique_texts(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _family_work_unit(row: Mapping[str, Any]) -> dict[str, Any]:
    unit = _mapping(row.get("next_work_unit"))
    unit_id = _transition_key(row)
    action = _text(row.get("controller_action")) or "none"
    return {
        "work_unit_ref": f"mas-work-unit:{unit_id}",
        "action_refs": [f"mas-controller-action:{action}"],
        "metadata": {
            "unit_id": _text(unit.get("unit_id")) or unit_id,
            "lane": _text(unit.get("lane")),
            "summary": _text(unit.get("summary")),
            "controller_action": action,
            "decision_type": _text(row.get("decision_type")) or "unknown",
        },
    }


def _family_owner_route(row: Mapping[str, Any]) -> dict[str, Any]:
    owner = _text(row.get("owner")) or FAMILY_TRANSITION_OWNER
    route_target = _text(row.get("route_target")) or "inspect"
    controller_action = _text(row.get("controller_action"))
    payload: dict[str, Any] = {
        "owner": owner,
        "route_ref": f"mas-route:{route_target}",
        "metadata": {
            "route_target": route_target,
            "controller_action": controller_action,
        },
    }
    if controller_action:
        payload["action_refs"] = [f"mas-controller-action:{controller_action}"]
    return payload


def _family_typed_blocker(row: Mapping[str, Any]) -> dict[str, Any] | None:
    blocker = _mapping(row.get("typed_blocker"))
    blocker_id = _text(blocker.get("blocker_id"))
    if not blocker_id:
        return None
    refs = []
    if required_surface := _text(blocker.get("required_owner_surface")):
        refs.append(required_surface)
    return {
        "blocker_code": blocker_id,
        "owner": _text(row.get("owner")) or FAMILY_TRANSITION_OWNER,
        "refs": refs,
        "metadata": {
            "blocker_type": _text(blocker.get("blocker_type")),
            "summary": _text(blocker.get("summary")),
            "write_permitted": blocker.get("write_permitted") is True,
        },
    }


def _family_human_gate(row: Mapping[str, Any]) -> dict[str, Any] | None:
    if _text(row.get("decision_type")) != "human_gate":
        return None
    key = _transition_key(row)
    return {
        "gate_ref": f"mas-human-gate:{key}",
        "owner": "human_gate",
        "reason": _text(_mapping(row.get("typed_blocker")).get("summary")) or "mas_human_gate_required",
        "resume_refs": [_receipt_ref(row)],
    }


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
    if _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval":
        return False
    verdict = _mapping(publication_eval.get("verdict"))
    gaps = [item for item in publication_eval.get("gaps") or [] if isinstance(item, Mapping)]
    return (
        _text(publication_eval.get("status")) == "blocked"
        or bool(publication_eval.get("blockers"))
        or _text(verdict.get("overall_verdict")) == "blocked"
        or any(_text(item.get("severity")) in {"must_fix", "blocking", "blocked"} for item in gaps)
    )


def _ai_reviewer_re_eval(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return _text(publication_eval.get("domain_ready_verdict")) == "ai_reviewer_re_eval" or (
        provenance.get("ai_reviewer_required") is True
        and _text(provenance.get("owner")) != "ai_reviewer"
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


__all__ = [
    "build_domain_transition_table",
    "build_family_transition_spec_descriptor",
    "build_family_transition_matrix_cases",
    "build_family_transition_spec",
    "project_domain_transition",
]
