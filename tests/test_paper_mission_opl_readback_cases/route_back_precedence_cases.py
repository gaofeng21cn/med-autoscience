from __future__ import annotations

import json
import os
from pathlib import Path

from med_autoscience.paper_mission_opl_readback import (
    TERMINAL_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)
from tests.test_paper_mission_opl_readback_cases.shared import (
    _opl_route_carrier,
    _opl_transition_receipt,
    _write_closeout,
)


def test_opl_terminal_closeout_readback_prefers_latest_alias_bound_route_back_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    mission_ref = f"paper-mission::{study_id}::gate_clearing_claim_evidence_repair"
    expected_transaction_ref = (
        f"paper-mission-transaction::{study_id}::review::{mission_ref}"
    )
    alias_transaction_ref = f"paper-mission-transaction::DM002::review::{mission_ref}"
    carrier = {
        **_opl_route_carrier(),
        "study_id": study_id,
        "paper_mission_transaction_ref": expected_transaction_ref,
        "stage_terminal_decision_ref": (
            f"{expected_transaction_ref}#stage_terminal_decision"
        ),
        "opl_route_command_ref": f"{expected_transaction_ref}#opl_route_command",
        "route_target": "review",
        "opl_route_command": {"command_kind": "resume_stage", "target": "review"},
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "idempotency_key": "dm002::review::fresh",
        "request_idempotency_key": "dm002::review::fresh::request",
        "attempt_idempotency_key": "dm002::review::fresh::attempt",
    }

    def write_workspace_closeout(
        attempt_id: str,
        payload: dict[str, object],
        *,
        mtime: float,
    ) -> tuple[dict[str, object], str]:
        closeout_root = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_attempts"
            / attempt_id
            / study_id
        )
        closeout_root.mkdir(parents=True)
        closeout_path = closeout_root / "stage_attempt_closeout_packet.json"
        closeout_path.write_text(json.dumps(payload), encoding="utf-8")
        os.utime(closeout_path, (mtime, mtime))
        closeout_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            f"{study_id}/stage_attempt_closeout_packet.json"
        )
        return payload, closeout_ref

    old_closeout, old_ref = write_workspace_closeout(
        "sat-old",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "study_id": study_id,
            "stage_id": "review",
            "stage_attempt_id": "sat-old",
            "stage_packet_ref": expected_transaction_ref,
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "work_unit_fingerprint": carrier["work_unit_fingerprint"],
            "authority_boundary": {"writes_authority": False},
        },
        mtime=1000.0,
    )
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/sat-new/"
        f"{study_id}/route_back_evidence_packet.json"
    )
    write_workspace_closeout(
        "sat-new",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "owner_answer_candidate_materialized",
            "study_id": study_id,
            "stage_id": "review",
            "stage_attempt_id": "sat-new",
            "stage_packet_ref": alias_transaction_ref,
            "work_unit_id": None,
            "work_unit_fingerprint": None,
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": route_back_ref,
                "can_claim_paper_progress": False,
            },
            "closeout_refs": [
                {
                    "ref_kind": "route_back_evidence_packet",
                    "workspace_relative_ref": route_back_ref,
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
        mtime=2000.0,
    )
    monkeypatch.setattr(
        readback_module,
        "_matching_opl_runtime_live_probe",
        lambda **_kwargs: ("terminal", old_closeout, old_ref),
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-new"
    assert readback["terminal_closeout"]["stage_packet_ref"] == alias_transaction_ref


def test_opl_terminal_closeout_readback_accepts_candidate_delta_ref_binding(
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
            "status": "",
            "closeout_status": "route_back_evidence_candidate_prepared",
            "stage_id": "publication_gate_replay",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "closeout_refs": [carrier["paper_mission_transaction_ref"]],
            "candidate_delta_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/dm003::candidate-v2/paper_facing_write_repair_candidate.json"
            ),
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["status"] == (
        "route_back_evidence_candidate_prepared"
    )
    assert readback["terminal_closeout"]["closeout_status"] == (
        "route_back_evidence_candidate_prepared"
    )


def test_opl_terminal_closeout_readback_keeps_live_runtime_terminal_over_stale_route_back(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "status": "owner_answer_candidate_materialized",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-old-route-back",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "work_unit_id": None,
            "work_unit_fingerprint": None,
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-old-route-back/study/route_back_evidence_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
            "closeout_refs": [
                {
                    "ref_kind": "route_back_evidence_packet",
                    "workspace_relative_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-old-route-back/study/route_back_evidence_packet.json"
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
    live_closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "completed",
        "study_id": carrier["study_id"],
        "stage_id": "publication_gate_replay",
        "stage_attempt_id": "sat-current-live",
        "work_unit_id": carrier["work_unit_id"],
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "stage_packet_ref": carrier["stage_terminal_decision_ref"],
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        "runtime_readback_source": "opl_family_runtime_queue_inspect",
        "task_id": "frt-current-live",
        "task_status": "blocked",
        "closeout_refs": [
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-current-live/study/stage_attempt_closeout_packet.json"
        ],
        "opl_transition_receipt": _opl_transition_receipt(
            stage_attempt_id="sat-current-live",
            task_id="frt-current-live",
        ),
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
    monkeypatch.setattr(
        readback_module,
        "_matching_opl_runtime_live_probe",
        lambda **_kwargs: (
            "terminal",
            live_closeout,
            "opl://family-runtime/tasks/frt-current-live/terminal-closeout-readback",
        ),
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-current-live"
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_queue_inspect"
    )
    assert readback["terminal_closeout"]["closeout_ref"] == (
        "opl://family-runtime/tasks/frt-current-live/terminal-closeout-readback"
    )


def test_opl_terminal_closeout_readback_enriches_same_attempt_thin_live_terminal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from med_autoscience import paper_mission_opl_readback as readback_module

    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap"
        "::domain-transition::write::dm003-bounded-prose-repair"
    )
    attempt_id = "sat-current-thin-live"
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"{attempt_id}/route_back_evidence_packet.json"
    )
    carrier = {
        **_opl_route_carrier(),
        "study_id": study_id,
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "work_unit_id": "dm003_bounded_prose_repair",
        "work_unit_fingerprint": (
            "domain-transition::write::dm003_bounded_prose_repair::source::current"
        ),
        "route_target": "write",
    }
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / attempt_id
    )
    closeout_root.mkdir(parents=True)
    local_closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "closeout_status": "route_back_evidence_candidate_prepared",
        "study_id": study_id,
        "stage_id": "write",
        "stage_attempt_id": attempt_id,
        "work_unit_id": "dm003_bounded_prose_repair",
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "route_back_evidence_ref": route_back_ref,
        "candidate_delta_ref": (
            "ops/medautoscience/paper_mission_stage_attempts/"
            f"{attempt_id}/paper_facing_write_repair_candidate.json"
        ),
        "candidate_manifest_ref": (
            "ops/medautoscience/paper_mission_stage_attempts/"
            f"{attempt_id}/candidate_manifest.json"
        ),
        "authority_boundary": {
            "record_only_surface": True,
            "writes_authority": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
    }
    closeout_path = closeout_root / "stage_attempt_closeout_packet.json"
    closeout_path.write_text(json.dumps(local_closeout), encoding="utf-8")

    live_closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "completed",
        "study_id": study_id,
        "stage_id": "write",
        "stage_attempt_id": attempt_id,
        "stage_packet_ref": transaction_ref,
        "work_unit_id": "dm003_bounded_prose_repair",
        "work_unit_fingerprint": carrier["work_unit_fingerprint"],
        "runtime_readback_source": "opl_family_runtime_queue_inspect",
        "task_id": "frt-current-thin-live",
        "task_status": "completed",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "opl_transition_receipt": _opl_transition_receipt(
            stage_attempt_id=attempt_id,
            task_id="frt-current-thin-live",
        ),
        "authority_boundary": {"record_only_surface": True},
    }
    monkeypatch.setattr(
        readback_module,
        "_matching_opl_runtime_live_probe",
        lambda **_kwargs: (
            "terminal",
            live_closeout,
            "opl://family-runtime/tasks/frt-current-thin-live/terminal-closeout-readback",
        ),
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=True,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == attempt_id
    assert readback["terminal_closeout"]["closeout_ref"] == (
        f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
        "stage_attempt_closeout_packet.json"
    )
    assert readback["receipt_evidence"]["route_back_evidence_ref"] == route_back_ref
    assert readback["mas_receipt_consumption"]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )


def test_opl_terminal_closeout_readback_prefers_newer_same_route_candidate(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap"
        "::domain-transition::write::medical-prose-write-repair"
    )
    carrier = {
        **_opl_route_carrier(),
        "study_id": study_id,
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::current"
        ),
        "route_target": None,
        "opl_route_command": {
            "command_kind": "resume_stage",
            "target": "medical_prose_write_repair",
        },
    }

    def write_closeout(attempt_id: str, *, mtime: float, rich: bool) -> None:
        closeout_root = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_attempts"
            / attempt_id
            / study_id
        )
        closeout_root.mkdir(parents=True)
        route_back_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            f"{study_id}/route_back_evidence_packet.json"
        )
        candidate_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            f"{study_id}/paper_facing_write_repair_candidate.json"
        )
        closeout = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "owner_answer_candidate_materialized",
            "study_id": study_id,
            "stage_id": "write",
            "stage_attempt_id": attempt_id,
            "stage_packet_ref": transaction_ref,
            "work_unit_id": "medical_prose_write_repair",
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": route_back_ref,
                "paper_facing_delta_ref": candidate_ref if rich else None,
                "can_claim_paper_progress": False,
            },
            "closeout_refs": [
                {
                    "ref_kind": "route_back_evidence_packet",
                    "workspace_relative_ref": route_back_ref,
                },
                *(
                    [
                        {
                            "ref_kind": "candidate_manifest",
                            "workspace_relative_ref": (
                                "ops/medautoscience/paper_mission_stage_attempts/"
                                f"{attempt_id}/{study_id}/candidate_manifest.json"
                            ),
                        },
                        "progress_events.jsonl",
                    ]
                    if rich
                    else []
                ),
            ],
            "authority_boundary": {
                "record_only_surface": True,
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
            },
        }
        route_back = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "study_id": study_id,
            "stage_id": "write",
            "stage_attempt_id": attempt_id,
            "stage_packet_ref": transaction_ref,
            "work_unit_id": "medical_prose_write_repair",
            "owner_answer_kind": "route_back_evidence_ref",
            "route_back_evidence_ref": route_back_ref,
            "candidate_ref": candidate_ref,
            "candidate_is_authority": False,
            "authority_boundary": {"record_only_surface": True},
        }
        closeout_path = closeout_root / "stage_attempt_closeout_packet.json"
        route_back_path = closeout_root / "route_back_evidence_packet.json"
        closeout_path.write_text(json.dumps(closeout), encoding="utf-8")
        route_back_path.write_text(json.dumps(route_back), encoding="utf-8")
        os.utime(closeout_path, (mtime, mtime))
        os.utime(route_back_path, (mtime, mtime))

    write_closeout("sat-old-rich", mtime=1000.0, rich=True)
    write_closeout("sat-new-current", mtime=2000.0, rich=False)

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-new-current"


def test_opl_terminal_closeout_readback_uses_newer_route_back_without_closeout_packet(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    transaction_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap"
        "::write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap"
        "::domain-transition::write::medical-prose-write-repair"
    )
    carrier = {
        **_opl_route_carrier(),
        "study_id": study_id,
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::current"
        ),
        "route_target": None,
    }
    old_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-old-rich"
        / study_id
    )
    old_root.mkdir(parents=True)
    old_closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "owner_answer_candidate_materialized",
        "study_id": study_id,
        "stage_id": "write",
        "stage_attempt_id": "sat-old-rich",
        "stage_packet_ref": transaction_ref,
        "work_unit_id": "medical_prose_write_repair",
        "route_impact": {
            "owner_answer_kind": "route_back_evidence_ref",
            "route_back_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-old-rich/{study_id}/route_back_evidence_packet.json"
            ),
            "paper_facing_delta_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-old-rich/{study_id}/paper_facing_write_repair_candidate.json"
            ),
            "stage_log_summary": "older richer candidate",
            "can_claim_paper_progress": False,
        },
        "closeout_refs": [
            (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-old-rich/{study_id}/stage_attempt_closeout_packet.json"
            ),
            (
                "ops/medautoscience/paper_mission_stage_attempts/"
                f"sat-old-rich/{study_id}/candidate_manifest.json"
            ),
            "progress_events.jsonl",
        ],
        "authority_boundary": {
            "record_only_surface": True,
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
        },
    }
    old_closeout_path = old_root / "stage_attempt_closeout_packet.json"
    old_closeout_path.write_text(json.dumps(old_closeout), encoding="utf-8")
    os.utime(old_closeout_path, (1000.0, 1000.0))

    new_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-new-route-back-only"
        / study_id
    )
    new_root.mkdir(parents=True)
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"sat-new-route-back-only/{study_id}/route_back_evidence_packet.json"
    )
    candidate_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"sat-new-route-back-only/{study_id}/paper_facing_write_repair_candidate.json"
    )
    route_back = {
        "surface_kind": "paper_mission_stage_route_back_evidence_packet",
        "study_id": study_id,
        "stage_id": "write",
        "stage_attempt_id": "sat-new-route-back-only",
        "stage_packet_ref": transaction_ref,
        "work_unit_id": "medical_prose_write_repair",
        "owner_answer_kind": "route_back_evidence_ref",
        "route_back_evidence_ref": route_back_ref,
        "candidate_ref": candidate_ref,
        "candidate_is_authority": False,
        "authority_boundary": {"record_only_surface": True},
    }
    route_back_path = new_root / "route_back_evidence_packet.json"
    route_back_path.write_text(json.dumps(route_back), encoding="utf-8")
    os.utime(route_back_path, (2000.0, 2000.0))

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == (
        "sat-new-route-back-only"
    )
    assert readback["receipt_evidence"]["route_back_evidence_ref"] == route_back_ref
