from __future__ import annotations

from typing import Any, Mapping


PROGRAM_ID = "mas_mds_autonomy_operating_system"
SCHEMA_VERSION = 1

QUALITY_AUTHORITY_SURFACES = (
    "study_charter",
    "paper/evidence_ledger.json",
    "paper/review_ledger.json",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
)

RUNTIME_TRUTH_SURFACES = (
    "study_runtime_status",
    "runtime_watch",
    "runtime_escalation_record.json",
    "artifacts/runtime/autonomy_incidents/",
)

PROGRAM_LANES = (
    {
        "lane_id": "P0_baseline_freeze",
        "title": "Baseline freeze and program board",
        "owner": "MedAutoScience",
        "stage": "active",
        "primary_surfaces": (
            "docs/program/mas_mds_autonomy_operating_system_program.md",
            "autonomy_operating_system_program",
        ),
        "acceptance_gate": "main checkout clean, owner boundary frozen, lane board materialized",
    },
    {
        "lane_id": "P1_autonomy_reliability_core",
        "title": "Autonomy reliability core",
        "owner": "MedAutoScience runtime",
        "stage": "active",
        "primary_surfaces": (
            "study_runtime_status",
            "runtime_watch",
            "autonomy_slo",
            "autonomy_state_machine",
        ),
        "acceptance_gate": "study state explains live/stalled/no-live/recovery and owner route",
    },
    {
        "lane_id": "P2_observability_and_profiling",
        "title": "Observability and profiling",
        "owner": "MedAutoScience runtime",
        "stage": "active",
        "primary_surfaces": (
            "cycle_observability",
            "study_cycle_profile",
            "paper_line_delivery_metrics",
        ),
        "acceptance_gate": "paper progress and ETA derive from durable timing and blocker evidence",
    },
    {
        "lane_id": "P3_medical_quality_os",
        "title": "Medical quality operating system",
        "owner": "MedAutoScience eval_hygiene",
        "stage": "active",
        "primary_surfaces": (
            "study_charter.paper_quality_contract",
            "reporting_guideline_checklist.json",
            "quality_gate_ledger_enforcement",
        ),
        "acceptance_gate": "paper quality is guideline-bound before draft and submission handoff",
    },
    {
        "lane_id": "P4_quality_preserving_fast_lane",
        "title": "Quality-preserving fast lane",
        "owner": "MedAutoScience controller",
        "stage": "active",
        "primary_surfaces": (
            "fast_lane_execution_manifest",
            "artifacts/controller/gate_clearing_batch/latest.json",
        ),
        "acceptance_gate": "mechanical acceleration replays gates and never relaxes quality constraints",
    },
    {
        "lane_id": "P5_mas_mds_strangler_program",
        "title": "MAS/MDS strangler program",
        "owner": "MedAutoScience with MedDeepScientist oracle",
        "stage": "active",
        "primary_surfaces": (
            "docs/policies/runtime_protocol.md",
            "docs/policies/mas_mds_transition_contract.md",
            "strangler_registry",
        ),
        "acceptance_gate": "every MDS surface has stage, promotion gate, parity proof, and rollback surface",
    },
    {
        "lane_id": "P6_natural_boundary_refactor",
        "title": "Natural boundary refactor",
        "owner": "MedAutoScience maintainability",
        "stage": "active",
        "primary_surfaces": (
            "boundary_fitness",
            "scripts/line_budget.py",
        ),
        "acceptance_gate": "new logic enters natural modules and does not grow oversized entrypoints",
    },
    {
        "lane_id": "P7_delivery_metrics_and_forecasting",
        "title": "Delivery metrics and forecasting",
        "owner": "MedAutoScience operator truth",
        "stage": "active",
        "primary_surfaces": (
            "paper_line_delivery_metrics",
            "eta_confidence_band",
            "study-progress",
        ),
        "acceptance_gate": "paper-line status includes evidence-based timing, blocker and ETA bands",
    },
    {
        "lane_id": "P8_autonomy_incident_learning_loop",
        "title": "Autonomy incident learning loop",
        "owner": "MedAutoScience reliability",
        "stage": "active",
        "primary_surfaces": (
            "autonomy_incidents",
            "runtime_taxonomy",
            "strangler_rule",
        ),
        "acceptance_gate": "repeat incidents produce prevention actions rather than prose-only notes",
    },
)

MATURITY_GATES = (
    {
        "gate_id": "single_mas_owner",
        "required": True,
        "summary": "MAS owns research entry, quality contract, publication gate, progress projection, and submission authority.",
    },
    {
        "gate_id": "mds_runtime_oracle_only",
        "required": True,
        "summary": "MDS remains controlled backend, behavior oracle, and upstream intake buffer; it is not a second product owner.",
    },
    {
        "gate_id": "quality_preservation",
        "required": True,
        "summary": "All acceleration preserves evidence, review, and publication gates with gate_relaxation_allowed=false.",
    },
    {
        "gate_id": "observable_long_run",
        "required": True,
        "summary": "Long-running studies expose state, owner, recovery route, blocker, and ETA evidence.",
    },
    {
        "gate_id": "natural_boundary_guard",
        "required": True,
        "summary": "New implementation must not add mechanical splits or grow oversized entrypoint files.",
    },
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _lane_by_id() -> dict[str, dict[str, Any]]:
    return {str(lane["lane_id"]): dict(lane) for lane in PROGRAM_LANES}


def build_program_board(progress_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    progress = _mapping(progress_payload)
    lane_progress = _mapping(progress.get("lane_progress"))
    lanes: list[dict[str, Any]] = []
    for lane_id, lane in _lane_by_id().items():
        override = _mapping(lane_progress.get(lane_id))
        status = _text(override.get("status")) or _text(lane.get("stage")) or "active"
        lanes.append(
            {
                **lane,
                "status": status,
                "commit": _text(override.get("commit")),
                "verification": list(_list(override.get("verification"))),
                "blocks_release": status not in {"completed", "absorbed"},
            }
        )
    completed = [lane for lane in lanes if lane["status"] in {"completed", "absorbed"}]
    blocked = [lane for lane in lanes if lane["status"] == "blocked"]
    return {
        "surface": "mas_mds_autonomy_operating_system_program",
        "schema_version": SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "target_state": {
            "product_owner": "MedAutoScience",
            "runtime_backend": "MedDeepScientist",
            "mds_role": "controlled_backend_behavior_oracle_upstream_intake_buffer",
            "physical_monorepo_absorb": "post_gate_only",
        },
        "quality_authority_surfaces": list(QUALITY_AUTHORITY_SURFACES),
        "runtime_truth_surfaces": list(RUNTIME_TRUTH_SURFACES),
        "maturity_gates": [dict(gate) for gate in MATURITY_GATES],
        "lanes": lanes,
        "status_summary": {
            "lane_count": len(lanes),
            "completed_or_absorbed_count": len(completed),
            "blocked_count": len(blocked),
            "ready_for_program_release": len(completed) == len(lanes) and not blocked,
        },
    }


def validate_program_board(board: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(board.get("surface")) != "mas_mds_autonomy_operating_system_program":
        issues.append({"code": "invalid_surface", "message": "program board surface mismatch"})
    target_state = _mapping(board.get("target_state"))
    if _text(target_state.get("product_owner")) != "MedAutoScience":
        issues.append({"code": "wrong_product_owner", "message": "program board must keep MAS as product owner"})
    if _text(target_state.get("physical_monorepo_absorb")) != "post_gate_only":
        issues.append({"code": "monorepo_absorb_not_post_gate", "message": "physical absorb must stay post-gate"})
    quality_surfaces = set(str(item) for item in _list(board.get("quality_authority_surfaces")))
    missing_quality = [surface for surface in QUALITY_AUTHORITY_SURFACES if surface not in quality_surfaces]
    if missing_quality:
        issues.append(
            {
                "code": "missing_quality_authority_surface",
                "message": "program board dropped required quality authority surfaces",
                "missing": missing_quality,
            }
        )
    for lane in _list(board.get("lanes")):
        if not isinstance(lane, Mapping):
            issues.append({"code": "invalid_lane", "message": "lane must be an object"})
            continue
        lane_id = _text(lane.get("lane_id")) or "<unknown>"
        if not _text(lane.get("owner")):
            issues.append({"code": "lane_missing_owner", "lane_id": lane_id})
        if not _list(lane.get("primary_surfaces")):
            issues.append({"code": "lane_missing_primary_surfaces", "lane_id": lane_id})
        if not _text(lane.get("acceptance_gate")):
            issues.append({"code": "lane_missing_acceptance_gate", "lane_id": lane_id})
    return {
        "surface": "mas_mds_autonomy_operating_system_program_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
