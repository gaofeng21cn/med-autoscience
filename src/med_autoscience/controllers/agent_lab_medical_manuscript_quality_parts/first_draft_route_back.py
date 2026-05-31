from __future__ import annotations

from typing import Any

from .quality_boundary import AUTHORITY_BOUNDARY
from .study_quality_targets import study_quality_target_profile


RUNTIME_FORBIDDEN_TERMS = [
    "MAS",
    "AI reviewer",
    "verified outputs",
    "accepted records",
    "source gaps",
    "submission readiness",
    "repair note",
    "blocker",
    "route-back",
]


def first_draft_quality_route_back_checklist(
    *,
    study_id: str,
    evidence_refs: list[str],
    blocker_refs: list[str],
    feedback_ref: str | None,
) -> dict[str, Any]:
    source_refs = _source_refs(
        study_id=study_id,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
        feedback_ref=feedback_ref,
    )
    items = [
        _item(
            blocker="methods_reproducibility_floor_missing",
            route_target="write",
            owner="write",
            next_work_units=["methods_reproducibility_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "Methods identify data source, cohort construction, variables, outcomes, analysis model, "
                "missingness handling, software, and reproducible evidence refs"
            ),
        ),
        _item(
            blocker="results_numeric_uncertainty_floor_missing",
            route_target="analysis-campaign",
            owner="analysis-campaign",
            next_work_units=["results_numeric_uncertainty_evidence_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "Results report denominators, estimates, 95% confidence intervals or supported uncertainty, "
                "and table-linked numeric evidence"
            ),
        ),
        _item(
            blocker="formal_figure_table_quality_floor_missing",
            route_target="figure-polish",
            owner="figure-polish",
            next_work_units=["formal_medical_display_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "main tables and figures are journal-facing medical displays with legends, units, denominators, "
                "claim bindings, and evidence refs"
            ),
        ),
        _item(
            blocker="abstract_hard_metrics_uncertainty_missing",
            route_target="write",
            owner="write",
            next_work_units=["numeric_abstract_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "Abstract reports hard sample sizes, main estimates, uncertainty where supported, "
                "and a conclusion bounded by current evidence"
            ),
        ),
        _item(
            blocker="discussion_result_driven_non_defensive_floor_missing",
            route_target="review",
            owner="review",
            next_work_units=["discussion_result_driven_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "Discussion starts from principal findings, relates them to prior work, interprets clinical meaning, "
                "centralizes limitations, and avoids defensive process narration"
            ),
        ),
        _item(
            blocker="runtime_language_purge_required",
            route_target="write",
            owner="write",
            next_work_units=["runtime_language_purge"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "canonical manuscript body contains no runtime/control-plane or internal QA terminology"
            ),
            forbidden_terms=RUNTIME_FORBIDDEN_TERMS,
        ),
        _item(
            blocker="claim_evidence_alignment_required",
            route_target="write",
            owner="write",
            next_work_units=["claim_evidence_alignment_repair"],
            evidence_refs=source_refs,
            expected_repair_result=(
                "each manuscript claim is linked to current evidence, display, review, and limitation refs"
            ),
        ),
        *_family_items(study_id=study_id, evidence_refs=source_refs),
    ]
    return {
        "surface_kind": "first_draft_quality_route_back_checklist",
        "schema_version": 1,
        "status": "blocked",
        "route_back_required": True,
        "quality_gate_relaxation_allowed": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_write_study_truth": False,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "items": _dedupe_items(items),
    }


def _source_refs(
    *,
    study_id: str,
    evidence_refs: list[str],
    blocker_refs: list[str],
    feedback_ref: str | None,
) -> list[str]:
    refs = [
        *evidence_refs,
        *blocker_refs,
        feedback_ref,
        f"quality-floor-ref:mas/{study_id}/first-draft-medical-manuscript",
    ]
    return _unique([ref for ref in refs if isinstance(ref, str) and ref.strip()])


def _family_items(*, study_id: str, evidence_refs: list[str]) -> list[dict[str, Any]]:
    profile = study_quality_target_profile(study_id=study_id)
    items: list[dict[str, Any]] = []
    for target in profile["targets"]:
        target_id = target["target_id"]
        route_target = target["route_target"]
        items.append(
            _item(
                blocker=f"{target_id}_required",
                route_target=route_target,
                owner=_owner_for_route_target(route_target),
                next_work_units=[target_id],
                evidence_refs=evidence_refs,
                expected_repair_result=target["requirement"],
            )
        )
    return items


def _item(
    *,
    blocker: str,
    route_target: str,
    owner: str,
    next_work_units: list[str],
    evidence_refs: list[str],
    expected_repair_result: str,
    forbidden_terms: list[str] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "blocker": blocker,
        "route_target": route_target,
        "owner": owner,
        "next_work_units": _unique(next_work_units),
        "evidence_refs": _unique(evidence_refs),
        "expected_repair_result": expected_repair_result,
    }
    if forbidden_terms is not None:
        item["forbidden_terms"] = list(forbidden_terms)
    return item


def _owner_for_route_target(route_target: str) -> str:
    if route_target in {"write", "review", "figure-polish", "publication-gate", "controller"}:
        return route_target
    if route_target == "analysis-campaign":
        return "analysis-campaign"
    return route_target


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        blocker = str(item.get("blocker") or "").strip()
        if not blocker or blocker in seen:
            continue
        seen.add(blocker)
        result.append(item)
    return result


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
