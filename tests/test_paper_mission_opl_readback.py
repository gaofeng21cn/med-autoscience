from __future__ import annotations
from tests.test_paper_mission_opl_readback_cases.live_probe_cases import *  # noqa: F403,F401
from tests.test_paper_mission_opl_readback_cases.route_back_precedence_cases import *  # noqa: F403,F401
from tests.test_paper_mission_opl_readback_cases.shared import (
    _carrier,
    _opl_route_carrier,
    _opl_runtime_task_payload,
    _opl_transition_receipt,
    _opl_running_task_completed_attempt_payload,
    _opl_running_task_running_attempt_payload,
    _write_closeout,
)

import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from med_autoscience.paper_mission_opl_readback import (
    RUNNING_READBACK_STATUS,
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)


def test_opl_terminal_closeout_readback_observes_record_only_terminal_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(study_root, {})

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_paper_progress"] is False
    assert readback["terminal_closeout"]["domain_ready_claimed"] is False


def test_opl_terminal_closeout_readback_ignores_domain_ready_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_ready_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_ignores_domain_completion_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_completion_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_requires_record_only_boundary(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "authority_boundary": {
                "record_only_surface": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


def test_opl_terminal_closeout_readback_ignores_prior_owner_callable_adapter_closeout_for_next_stage(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "stage_outcome/opl-handoff",
            "blocked_reason": "opl_runtime_lifecycle_readback_required",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_accepts_current_route_target_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_id"] == "publication_gate_replay"


def test_opl_terminal_closeout_readback_accepts_workspace_stage_attempt_closeout_without_fingerprint(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current"
    )
    closeout_root.mkdir(parents=True)
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "study_id": study_id,
                "stage_id": "review",
                "stage_attempt_id": "sat-current",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "route_impact": {
                    "route_target": "review",
                    "recommended_next_owner": "MedAutoScience mission executor",
                    "recommended_next_action": "consume_route_back_evidence_ref",
                    "paper_progress_claim_allowed": False,
                },
                "authority_boundary": {
                    "writes_authority": False,
                    "writes_runtime": False,
                    "writes_yang_authority": False,
                    "writes_current_package": False,
                    "writes_publication_eval": False,
                    "writes_controller_decision": False,
                    "writes_owner_receipt": False,
                    "writes_typed_blocker": False,
                    "writes_human_gate": False,
                    "writes_runtime_queue_or_provider_attempt": False,
                    "can_claim_paper_progress": False,
                    "can_claim_submission_ready": False,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                },
            }
        ),
        encoding="utf-8",
    )
    carrier = {
        "study_id": study_id,
        "command_kind": "resume_stage",
        "route_target": "review",
        "opl_route_command": {"command_kind": "resume_stage", "target": "review"},
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-current"
    assert readback["terminal_closeout"]["closeout_ref"] == (
        "ops/medautoscience/paper_mission_stage_attempts/sat-current/"
        "stage_attempt_closeout_packet.json"
    )


def test_opl_terminal_closeout_readback_rejects_unbound_local_closeout_for_route_identity(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_currentness_mismatch_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [
                carrier["stage_terminal_decision_ref"],
                carrier["opl_route_command_ref"],
                "typed-blocker:stage_attempt_currentness_mismatch",
            ],
            "typed_blocker_ref": "local-closeout#domain_blocker",
            "blocked_reason": "stage_attempt_currentness_mismatch",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_stale_candidate_idempotency(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "closeout_refs": [carrier["paper_mission_transaction_ref"]],
            "idempotency_key": "dm003::candidate-v1",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_no_idempotency_stale_candidate_ref(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    current_candidate_ref = (
        "/workspace/ops/medautoscience/paper_mission_candidate_package/"
        "20260704T1425_dm003_bounded_analysis_sci_upgrade/study/package_manifest.json"
    )
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": (
            "dm003::submission_milestone_candidate::"
            f"{current_candidate_ref}::candidate-ref-missing"
        ),
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "closeout_refs": [
                carrier["paper_mission_transaction_ref"],
                (
                    "/workspace/ops/medautoscience/paper_mission_candidate_package/"
                    "paper_mission_drive/study/package_manifest.json"
                ),
            ],
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_prefers_followthrough_closeout_over_newer_base_closeout(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    base_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    followthrough_ref = f"{base_ref}::followthrough::89b46ab394eb"
    carrier = {
        "study_id": study_id,
        "command_kind": "resume_stage",
        "route_target": "write",
        "opl_route_command": {"command_kind": "resume_stage", "target": "write"},
        "paper_mission_transaction_ref": base_ref,
        "stage_terminal_decision_ref": f"{base_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{base_ref}#opl_route_command",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
        ),
    }

    def write_stage_attempt(
        attempt_id: str,
        *,
        stage_id: str,
        stage_packet_ref: str,
        mtime: float,
    ) -> None:
        attempt_root = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_attempts"
            / attempt_id
        )
        attempt_root.mkdir(parents=True)
        closeout_path = attempt_root / "stage_attempt_closeout_packet.json"
        closeout_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "route_back_evidence_candidate",
                    "study_id": study_id,
                    "stage_id": stage_id,
                    "stage_attempt_id": attempt_id,
                    "work_unit_id": carrier["work_unit_id"],
                    "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                    "stage_packet_ref": stage_packet_ref,
                    "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                    "route_impact": {
                        "owner_answer_kind": "route_back_evidence_ref",
                        "route_back_evidence_ref": (
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            f"{attempt_id}/route_back_evidence_packet.json"
                        ),
                        "paper_facing_delta_ref": (
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            f"{attempt_id}/paper_facing_write_repair_candidate.json"
                        ),
                        "stage_log_summary": {"stage_name": "write"},
                        "user_stage_log": {"outcome": "route_back_evidence_candidate"},
                        "human_stage_log": "Route-back evidence candidate only.",
                    },
                    "closeout_refs": [
                        (
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            f"{attempt_id}/route_back_evidence_packet.json"
                        ),
                        (
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            f"{attempt_id}/candidate_manifest.json"
                        ),
                    ],
                    "authority_boundary": {
                        "record_only_surface": True,
                        "provider_completion_is_domain_completion": False,
                        "artifact_mutation_authorized": False,
                        "publication_eval_latest_write_authorized": False,
                        "controller_decision_write_authorized": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        os.utime(closeout_path, (mtime, mtime))

    write_stage_attempt(
        "sat-followthrough",
        stage_id=carrier["work_unit_id"],
        stage_packet_ref=followthrough_ref,
        mtime=100.0,
    )
    write_stage_attempt(
        "sat-base",
        stage_id="write",
        stage_packet_ref=base_ref,
        mtime=200.0,
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-followthrough"
    assert readback["terminal_closeout"]["stage_id"] == carrier["work_unit_id"]


def test_opl_terminal_closeout_readback_accepts_followthrough_identity_from_route_back_sidecar(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    base_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    followthrough_ref = f"{base_ref}::followthrough::89b46ab394eb"
    carrier = {
        "study_id": study_id,
        "command_kind": "resume_stage",
        "route_target": "write",
        "opl_route_command": {"command_kind": "resume_stage", "target": "write"},
        "paper_mission_transaction_ref": base_ref,
        "stage_terminal_decision_ref": f"{base_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{base_ref}#opl_route_command",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
        ),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    attempt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-followthrough-sidecar"
    )
    attempt_root.mkdir(parents=True)
    (attempt_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "route_back_evidence_candidate",
                "study_id": study_id,
                "stage_id": carrier["work_unit_id"],
                "stage_attempt_id": "sat-followthrough-sidecar",
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "route_impact": {
                    "owner_answer_kind": "route_back_evidence_ref",
                    "route_back_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-followthrough-sidecar/route_back_evidence_packet.json"
                    ),
                    "human_stage_log": "Route-back evidence candidate only.",
                },
                "closeout_refs": [
                    (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-followthrough-sidecar/route_back_evidence_packet.json"
                    )
                ],
                "authority_boundary": {
                    "record_only_surface": True,
                    "provider_completion_is_domain_completion": False,
                    "artifact_mutation_authorized": False,
                    "publication_eval_latest_write_authorized": False,
                    "controller_decision_write_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (attempt_root / "route_back_evidence_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                "study_id": study_id,
                "stage_id": carrier["work_unit_id"],
                "stage_attempt_id": "sat-followthrough-sidecar",
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "stage_packet_ref": followthrough_ref,
                "candidate_manifest_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-followthrough-sidecar/candidate_manifest.json"
                ),
                "paper_facing_delta_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-followthrough-sidecar/paper_facing_write_repair_candidate.json"
                ),
                "source_evidence": {
                    "paper_mission_candidate_package_ref": (
                        "ops/medautoscience/paper_mission_candidate_package/"
                        "20260704T173503Z_dm003_write_repair_sci_delta/"
                        "003-dpcc-primary-care-phenotype-treatment-gap/package_manifest.json"
                    )
                },
                "idempotency_key": "dm003::candidate-v2",
            }
        ),
        encoding="utf-8",
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == (
        "sat-followthrough-sidecar"
    )


def test_opl_terminal_closeout_readback_accepts_transaction_bound_route_back_evidence(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "status": "non_advancing_route_back_evidence_candidate",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-route-back",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "work_unit_id": None,
            "work_unit_fingerprint": None,
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-route-back/study/route_back_evidence_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
            "closeout_refs": [
                {
                    "ref_kind": "route_back_evidence_packet",
                    "workspace_relative_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-route-back/study/route_back_evidence_packet.json"
                    ),
                }
            ],
            "authority_boundary": {
                "candidate_is_authority": False,
                "writes_authority_surface": False,
                "writes_publication_eval": False,
                "writes_controller_decision": False,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "writes_human_gate": False,
                "writes_current_package": False,
                "writes_runtime_queue": False,
                "writes_provider_attempt": False,
                "writes_yang_authority": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-route-back"
    assert readback["terminal_closeout"]["status"] == (
        "non_advancing_route_back_evidence_candidate"
    )
    assert readback["opl_transition_receipt"]["receipt_status"] == (
        "route_back_evidence_closeout_observed"
    )
    assert readback["receipt_evidence"]["route_back_evidence_ref"].endswith(
        "route_back_evidence_packet.json"
    )
    assert readback["mas_receipt_consumption"]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )


def test_opl_terminal_closeout_readback_prefers_route_back_over_typed_closeout_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-route-back/study/route_back_evidence_packet.json"
    )
    _write_closeout(
        study_root,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-route-back",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "opl_transition_receipt": {
                **_opl_transition_receipt(),
                "typed_runtime_blocker_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-route-back/study/stage_attempt_closeout_packet.json"
                ),
                "route_impact": {
                    "recommended_next_action": "consume_route_back_evidence_ref",
                    "user_stage_log": {
                        "evidence_refs": [
                            "ops/medautoscience/paper_mission_stage_attempts/"
                            "sat-route-back/study/attempt_candidate_manifest.json",
                            route_back_ref,
                        ],
                    },
                },
            },
            "typed_runtime_blocker_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-route-back/study/stage_attempt_closeout_packet.json"
            ),
            "closeout_refs": [
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-route-back/study/stage_attempt_closeout_packet.json",
                route_back_ref,
            ],
            "authority_boundary": {
                "record_only_surface": True,
                "provider_completion_is_domain_completion": False,
                "artifact_mutation_authorized": False,
                "publication_eval_latest_write_authorized": False,
                "controller_decision_write_authorized": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["receipt_evidence"]["typed_runtime_blocker_ref"].endswith(
        "stage_attempt_closeout_packet.json"
    )
    assert readback["receipt_evidence"]["route_back_evidence_ref"] == route_back_ref
    assert readback["mas_receipt_consumption"]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )


def test_opl_terminal_closeout_readback_accepts_matching_candidate_idempotency(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "closeout_refs": [carrier["paper_mission_transaction_ref"]],
            "idempotency_key": "dm003::candidate-v2",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_id"] == "publication_gate_replay"


def test_opl_terminal_closeout_readback_rejects_stale_nested_receipt_idempotency(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "closeout_refs": [carrier["paper_mission_transaction_ref"]],
            "opl_transition_receipt": {
                **_opl_transition_receipt(),
                "attempt_idempotency_key": "dm003::candidate-v1::attempt",
                "request_idempotency_key": "dm003::candidate-v1::request",
            },
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_rejects_retired_stale_opl_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    task = payload["family_runtime_task"]["task"]
    task["last_error"] = (
        "operator_retired_stale_runtime_residue:"
        "mas_paper_mission_current_thread_replaces_stale_stage_route_rows"
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_consumes_matching_opl_runtime_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["dispatch_status"] == "terminal_closeout_observed"
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_provider_running"] is False
    assert readback["can_claim_paper_progress"] is False
    terminal = readback["terminal_closeout"]
    assert terminal["runtime_readback_source"] == "opl_family_runtime_queue_inspect"
    assert terminal["task_id"] == "frt-stage-route"
    assert terminal["task_status"] == "blocked"
    assert terminal["closeout_receipt_status"] == "accepted_typed_closeout"
    assert terminal["stage_id"] == "publication_gate_replay"
    assert terminal["stage_attempt_id"] == "sat-terminal"
    assert terminal["typed_blocker_ref"] == "typed-blocker:opl_runtime_live_readback_required"
    assert terminal["provider_completion_is_domain_ready"] is False
    receipt = readback["opl_transition_receipt"]
    assert receipt["surface_kind"] == "opl_transition_receipt"
    assert receipt["receipt_status"] == "terminal_closeout_observed"
    assert receipt["role"] == "transport_receipt_only"
    assert receipt["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm002"
    )
    assert receipt["opl_route_command_ref"] == (
        "paper-mission-transaction::dm002#opl_route_command"
    )
    assert receipt["stage_attempt_ref"] == "opl://stage-attempts/sat-terminal"
    assert receipt["typed_runtime_blocker_ref"] == (
        "typed-blocker:opl_runtime_live_readback_required"
    )
    assert receipt["can_change_stage_terminal_decision"] is False
    assert receipt["can_select_next_owner"] is False
    assert receipt["can_claim_paper_progress"] is False
    assert terminal["opl_transition_receipt"] == receipt


def test_opl_terminal_closeout_readback_rejects_stale_runtime_receipt_idempotency(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    payload = _opl_runtime_task_payload()
    receipt = payload["family_runtime_task"]["events"][0]["payload"][
        "opl_transition_receipt"
    ]
    receipt["request_idempotency_key"] = "dm003::candidate-v1::request"
    receipt["attempt_idempotency_key"] = "dm003::candidate-v1::attempt"

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_accepts_matching_runtime_receipt_idempotency(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    payload = _opl_runtime_task_payload()
    receipt = payload["family_runtime_task"]["events"][0]["payload"][
        "opl_transition_receipt"
    ]
    receipt["request_idempotency_key"] = carrier["request_idempotency_key"]
    receipt["attempt_idempotency_key"] = carrier["attempt_idempotency_key"]

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["opl_transition_receipt"]["request_idempotency_key"] == (
        carrier["request_idempotency_key"]
    )


def test_opl_terminal_closeout_readback_requires_transition_receipt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    payload["family_runtime_task"]["events"] = []

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback
    assert "opl_transition_receipt" not in readback


def test_opl_terminal_closeout_readback_rejects_unsafe_transition_receipt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    receipt = payload["family_runtime_task"]["events"][0]["payload"][
        "opl_transition_receipt"
    ]
    receipt["authority_boundary"]["writes_owner_receipt"] = True

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback
    assert "opl_transition_receipt" not in readback


def test_opl_terminal_closeout_readback_rejects_cross_transaction_opl_runtime_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "paper_mission_transaction_ref": "paper-mission-transaction::other",
    }

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_consumes_completed_stage_attempt_when_task_still_running(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_completed_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["dispatch_status"] == "terminal_closeout_observed"
    assert readback["can_claim_provider_running"] is False
    terminal = readback["terminal_closeout"]
    assert terminal["task_id"] == "frt-stage-route"
    assert terminal["task_status"] == "running"
    assert terminal["status"] == "completed"
    assert terminal["stage_attempt_id"] == "sat-completed"
    assert terminal["closeout_receipt_status"] == "accepted_typed_closeout"
    assert terminal["closeout_refs"] == [
        "paper-mission-transaction::dm002#opl_route_command",
        "opl://stage-attempts/sat-completed/runtime-blockers/no_typed_domain_handler_closeout_observed",
    ]
    assert terminal["provider_completion_is_domain_ready"] is False


def test_opl_terminal_closeout_readback_accepts_stage_terminal_ref_binding(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-stage-ref",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [
                "paper-mission-transaction::dm002",
                "paper-mission-transaction::dm002#stage_terminal_decision",
            ],
            "opl_transition_receipt": _opl_transition_receipt(
                stage_attempt_id="sat-stage-ref",
            ),
            "closeout_receipt_status": "accepted_typed_closeout",
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-stage-ref",
            },
        },
    ]
    runtime_task["events"] = []

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-stage-ref"
    assert readback["terminal_closeout"]["closeout_refs"] == [
        "paper-mission-transaction::dm002",
        "paper-mission-transaction::dm002#stage_terminal_decision",
    ]


def test_opl_runtime_readback_reports_same_identity_running_attempt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["dispatch_status"] == "provider_attempt_running"
    assert readback["domain_ready_verdict"] == "opl_runtime_attempt_running"
    assert readback["can_claim_provider_running"] is True
    assert readback["can_claim_paper_progress"] is False
    running = readback["running_attempt"]
    assert running["stage_attempt_id"] == "sat-running"
    assert running["provider_status"] == "running"
    assert running["workflow_id"] == "wf-running"
    assert running["provider_completion_is_domain_ready"] is False


def test_opl_runtime_readback_consumes_running_attempt_closeout_without_work_unit(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "status": "route_back_evidence_candidate",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-running",
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "work_unit_id": None,
            "work_unit_fingerprint": None,
            "blocked_reason": None,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-running"
    assert "running_attempt" not in readback
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_readback_prefers_live_running_attempt_over_local_terminal_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "study_id": carrier["study_id"],
            "stage_id": "publication_gate_replay",
            "work_unit_id": carrier["work_unit_id"],
            "work_unit_fingerprint": carrier["work_unit_fingerprint"],
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [carrier["opl_route_command_ref"]],
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert "terminal_closeout" not in readback
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-running"
    assert readback["can_claim_paper_progress"] is False
