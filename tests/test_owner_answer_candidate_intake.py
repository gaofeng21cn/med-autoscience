from __future__ import annotations

import json
from pathlib import Path


B002_CANDIDATE = "current_main_03c390_b002_post_0808_owner_answer_candidate_0810.md"
B003_CANDIDATE = "current_main_03c390_b003_post_0736_blocker_disposition_packet_0751.md"


def _write_candidate(path: Path, *, sha_text: str) -> None:
    path.write_text(sha_text, encoding="utf-8")


def test_b002_package_candidate_fails_closed_to_ai_reviewer_owner_surface(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_CANDIDATE
    body = "B002 owner answer candidate body\n"
    _write_candidate(candidate, sha_text=body)

    result = intake_owner_answer_candidate(
        candidate_id="B002-0810",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["surface_kind"] == "mas_owner_answer_candidate_intake_readback"
    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B002-0810"
    assert result["candidate_sha256"]
    assert result["study_id"] == "002-dm-china-us-mortality-attribution"
    assert result["owner_identity"] == {
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        ),
    }
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS publication AI-reviewer governed owner answer"
    )
    assert result["blocked_owner"]["required_governed_answer_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "route_back_evidence_ref",
        "typed_blocker_ref",
        "human_gate_ref",
    ]
    assert result["candidate_is_authority"] is False
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["written_files"] == []
    assert result["write_plan"]["can_write_publication_eval_latest"] is False
    assert result["write_plan"]["can_write_controller_decisions_latest"] is False
    assert result["write_plan"]["can_write_payload_targets"] is False
    assert result["next_legal_surface"]["kind"] == "ai_reviewer_owner_answer_or_route_back"


def test_b003_package_candidate_preserves_stable_owner_gate_blocker_without_redrive(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B003_CANDIDATE
    _write_candidate(candidate, sha_text="B003 blocker disposition packet\n")

    result = intake_owner_answer_candidate(
        candidate_id="B003-0751",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B003-0751"
    assert result["study_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"
    assert result["owner_identity"]["action_type"] == "publication_gate_replay"
    assert result["stable_blocker_policy"] == {
        "preserve_or_explicitly_supersede": "owner-gate-decision:d6d895635654560a85573c04",
        "provider_redrive_allowed": False,
    }
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS paper recovery / publication gate governed owner answer"
    )
    assert result["next_legal_surface"]["kind"] == "publication_gate_owner_answer_or_human_gate"
    assert result["forbidden_authority_writes"]["provider_redrive_hydrate_tick_replay_dhd_apply"] is True


def test_owner_answer_candidate_intake_rejects_sha_mismatch_without_writing(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_CANDIDATE
    _write_candidate(candidate, sha_text="unexpected body\n")

    result = intake_owner_answer_candidate(
        candidate_id="B002-0810",
        candidate_path=candidate,
        expected_sha256="0" * 64,
    )

    assert result["status"] == "candidate_hash_mismatch"
    assert result["candidate_is_authority"] is False
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["written_files"] == []
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS publication AI-reviewer governed owner answer"
    )


def test_owner_answer_candidate_intake_cli_json_readback(tmp_path: Path, capsys) -> None:
    from med_autoscience import cli

    candidate = tmp_path / B003_CANDIDATE
    body = "B003 blocker disposition packet\n"
    _write_candidate(candidate, sha_text=body)

    exit_code = cli.main(
        [
            "owner-answer-candidate-intake",
            "--candidate-id",
            "B003-0751",
            "--candidate-path",
            str(candidate),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    payload = json.loads(captured.out)
    assert payload["status"] == "exact_blocked_owner"
    assert payload["candidate_id"] == "B003-0751"
    assert payload["stable_blocker_policy"]["preserve_or_explicitly_supersede"] == (
        "owner-gate-decision:d6d895635654560a85573c04"
    )
    assert payload["write_plan"]["written_files"] == []
