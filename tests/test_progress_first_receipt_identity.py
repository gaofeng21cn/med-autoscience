from __future__ import annotations

import importlib


def test_gate_clearing_batch_receipt_consumption_exposes_canonical_work_unit_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_receipt_identity")
    transition = _gate_clearing_transition()
    receipt = module.gate_clearing_batch_receipt_consumption_for_transition(
        transition=transition,
        record={
            "status": "executed",
            "source_eval_id": "publication-eval::003::current",
            "owner_route_currentness_basis": {
                "source_eval_id": "publication-eval::003::current",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
                "truth_epoch": "truth-event-current",
            },
        },
    )

    assert receipt == {
        "consumption_status": "receipt_consumed",
        "receipt_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        "receipt_kind": "gate_clearing_batch",
        "execution_status": "executed",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
        "canonical_work_unit_identity": {
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
            "source_eval_id": "publication-eval::003::current",
            "truth_epoch": "truth-event-current",
        },
    }


def test_gate_clearing_batch_receipt_rejects_different_source_eval() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_receipt_identity")

    assert module.gate_clearing_batch_receipt_consumption_for_transition(
        transition=_gate_clearing_transition(),
        record={
            "status": "executed",
            "source_eval_id": "publication-eval::003::stale",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
        },
    ) is None


def test_gate_clearing_batch_receipt_rejects_different_work_unit_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_first_receipt_identity")

    assert module.gate_clearing_batch_receipt_consumption_for_transition(
        transition=_gate_clearing_transition(),
        record={
            "status": "executed",
            "source_eval_id": "publication-eval::003::current",
            "work_unit_id": "different_gate_replay",
            "work_unit_fingerprint": "truth-snapshot::different",
        },
    ) is None


def _gate_clearing_transition() -> dict[str, object]:
    return {
        "decision_type": "route_back_same_line",
        "route_target": "finalize",
        "owner": "gate_clearing_batch",
        "controller_action": "run_gate_clearing_batch",
        "next_work_unit": {
            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "lane": "publication_gate",
        },
        "source_refs": {
            "owner_route_currentness_basis": {
                "source_eval_id": "publication-eval::003::current",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
            }
        },
    }
