from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace



def _base_status_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/workspace/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": "/tmp/workspace/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "noop",
        "reason": "quest_already_running",
    }


def _write_controller_decision_authorization(
    study_root: Path,
    *,
    action_type: str = "ensure_study_runtime",
    next_work_unit: dict[str, object] | None = None,
    blocking_work_units: list[dict[str, object]] | None = None,
    work_unit_fingerprint: str | None = None,
    decision_id: str = "decision-analysis-001",
    emitted_at: str = "2026-04-25T06:20:00+00:00",
) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": emitted_at,
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::001-risk::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::001-risk::quest-001::controller-gap",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::001-risk::quest-001::latest",
                    "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                },
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": action_type, "payload_ref": str(decision_path)}],
                "reason": "Route bounded revision analysis back into the active runtime.",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
                ),
                "route_rationale": "The revision line needs a bounded quality pass under the same manuscript route.",
                **({"work_unit_fingerprint": work_unit_fingerprint} if work_unit_fingerprint else {}),
                **({"next_work_unit": next_work_unit} if next_work_unit else {}),
                **({"blocking_work_units": blocking_work_units} if blocking_work_units else {}),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_authority(
    study_root: Path,
    *,
    evaluated_signature: str = "source::evaluated",
) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::quest-001::latest",
                "emitted_at": "2026-04-25T06:21:00+00:00",
                "gate_fingerprint": "publication-gate::stable",
                "blockers": ["claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "submission_minimal_evaluated_source_signature": evaluated_signature,
                "submission_minimal_authority_source_signature": "source::authority",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_work_unit_authority(study_root: Path) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::quest-001::latest",
                "emitted_at": "2026-04-25T06:21:00+00:00",
                "recommended_actions": [
                    {
                        "action_type": "bounded_analysis",
                        "route_target": "analysis-campaign",
                        "route_key_question": "broad reviewer revision checklist",
                        "route_rationale": "Gate requires controller-owned analysis repair.",
                        "work_unit_fingerprint": "publication-blockers::claim-story-figure",
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                        },
                        "blocking_work_units": [
                            {
                                "unit_id": "analysis_claim_evidence_repair",
                                "lane": "analysis-campaign",
                                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                            },
                            {
                                "unit_id": "submission_minimal_refresh",
                                "lane": "finalize",
                                "summary": "Refresh the stale submission package after gate clearance.",
                            },
                        ],
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "claim_evidence_map",
                                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                                "blocking_reason": "claim_evidence_consistency_failed",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_gate_replay_with_specificity_targets(study_root: Path) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::quest-001::latest",
                "emitted_at": "2026-05-12T01:00:00+00:00",
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "finalize",
                        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                        "route_rationale": "bundle-stage blockers are now on the critical path for this paper line",
                        "work_unit_fingerprint": "publication-blockers::replay-with-targets",
                        "blocking_work_units": [
                            {
                                "unit_id": "publication_gate_replay",
                                "lane": "controller",
                                "summary": "Replay the publication gate against current authority signatures before dispatching new work.",
                            }
                        ],
                        "next_work_unit": {
                            "unit_id": "publication_gate_replay",
                            "lane": "controller",
                            "summary": "Replay the publication gate against current authority signatures before dispatching new work.",
                        },
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "claim_evidence_map",
                                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                                "blocking_reason": "stale_study_delivery_mirror",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                                "blocking_reason": "stale_study_delivery_mirror",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_table_or_manifest",
                                "source_path": str(
                                    study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
                                ),
                                "blocking_reason": "stale_study_delivery_mirror",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
                                "blocking_reason": "stale_study_delivery_mirror",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "publication_gate_source_path",
                                "source_path": "/tmp/runtime/quests/quest-001/artifacts/reports/medical_publication_surface/latest.json",
                                "blocking_reason": "stale_study_delivery_mirror",
                            },
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_runtime_state(quest_root: Path, payload: dict[str, object]) -> None:
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
