from __future__ import annotations

import json
from pathlib import Path


B002_CANDIDATE = "current_main_03c390_b002_post_0808_owner_answer_candidate_0810.md"
B003_CANDIDATE = "current_main_03c390_b003_post_0736_blocker_disposition_packet_0751.md"
B002_0910_CANDIDATE = (
    "current_main_74ee64_b002_0901_payload_metadata_human_gate_"
    "response_candidate_0910.md"
)
B003_0915_CANDIDATE = (
    "current_main_74ee64_b003_0901_preserve_blocker_typed_blocker_"
    "response_candidate_0915.md"
)
B002_1055_CANDIDATE = (
    "current_main_6efcd4_b002_1045_payload_currentness_"
    "governed_answer_target_1055.md"
)
B003_1105_CANDIDATE = (
    "current_main_6efcd4_b003_1045_write_repair_stable_blocker_"
    "governed_answer_target_1105.md"
)


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


def test_b002_0910_response_candidate_fails_closed_without_governed_ref(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_0910_CANDIDATE
    _write_candidate(candidate, sha_text="B002 0910 human gate response candidate\n")

    result = intake_owner_answer_candidate(
        candidate_id="B002-0910",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B002-0910"
    assert result["candidate_packet_kind"] == "b002_0901_payload_metadata_human_gate_response_candidate"
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
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["written_files"] == []
    assert result["write_plan"]["can_write_payload_targets"] is False
    assert result["forbidden_authority_writes"]["non_dry_run_ai_reviewer_materialization"] is True


def test_b003_0915_response_candidate_fails_closed_and_preserves_blocker(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B003_0915_CANDIDATE
    _write_candidate(candidate, sha_text="B003 0915 typed blocker response candidate\n")

    result = intake_owner_answer_candidate(
        candidate_id="B003-0915",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B003-0915"
    assert result["candidate_packet_kind"] == "b003_0901_preserve_blocker_typed_blocker_response_candidate"
    assert result["stable_blocker_policy"] == {
        "preserve_or_explicitly_supersede": "owner-gate-decision:d6d895635654560a85573c04",
        "provider_redrive_allowed": False,
    }
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS paper recovery / publication gate governed owner answer"
    )
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["can_write_runtime_queues_or_provider_attempts"] is False
    assert result["forbidden_authority_writes"]["provider_redrive_hydrate_tick_replay_dhd_apply"] is True


def test_b002_1055_governed_answer_target_fails_closed_without_governed_ref(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_1055_CANDIDATE
    _write_candidate(candidate, sha_text="B002 1055 owner answer target\n")

    result = intake_owner_answer_candidate(
        candidate_id="B002-1055",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B002-1055"
    assert result["candidate_packet_kind"] == "b002_payload_currentness_governed_answer_target"
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS publication AI-reviewer governed owner answer"
    )
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["written_files"] == []
    assert result["write_plan"]["can_write_payload_targets"] is False
    assert result["forbidden_authority_writes"]["non_dry_run_ai_reviewer_materialization"] is True
    assert result["next_legal_surface"]["kind"] == (
        "ai_reviewer_payload_currentness_guard_owner_answer"
    )


def test_b003_1105_governed_answer_target_fails_closed_and_preserves_blocker(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B003_1105_CANDIDATE
    _write_candidate(candidate, sha_text="B003 1105 owner answer target\n")

    result = intake_owner_answer_candidate(
        candidate_id="B003-1105",
        candidate_path=candidate,
        expected_sha256=None,
    )

    assert result["status"] == "exact_blocked_owner"
    assert result["candidate_id"] == "B003-1105"
    assert result["candidate_packet_kind"] == (
        "b003_write_repair_stable_blocker_governed_answer_target"
    )
    assert result["stable_blocker_policy"] == {
        "preserve_or_explicitly_supersede": "owner-gate-decision:d6d895635654560a85573c04",
        "provider_redrive_allowed": False,
    }
    assert result["blocked_owner"]["owner_surface"] == (
        "MAS paper recovery / publication gate governed owner answer"
    )
    assert result["governed_answer_consumed"] is False
    assert result["write_plan"]["can_write_runtime_queues_or_provider_attempts"] is False
    assert result["forbidden_authority_writes"]["provider_redrive_hydrate_tick_replay_dhd_apply"] is True
    assert result["next_legal_surface"]["kind"] == (
        "publication_gate_write_repair_stable_blocker_owner_answer"
    )


def test_governed_response_consumed_only_for_allowed_kind_and_matching_ownership(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_0910_CANDIDATE
    _write_candidate(candidate, sha_text="B002 0910 human gate response candidate\n")

    result = intake_owner_answer_candidate(
        candidate_id="B002-0910",
        candidate_path=candidate,
        expected_sha256=None,
        governed_response_kind="human_gate_ref",
        governed_response_ref="human_gate:owner-answer:b002-0910",
        governed_response_study_id="002-dm-china-us-mortality-attribution",
        governed_response_owner_surface="MAS publication AI-reviewer governed owner answer",
    )

    assert result["status"] == "governed_response_consumed"
    assert result["governed_answer_consumed"] is True
    assert result["governed_response"]["kind"] == "human_gate_ref"
    assert result["governed_response"]["candidate_id"] == "B002-0910"
    assert result["write_plan"]["written_files"] == []
    assert result["write_plan"]["can_write_publication_eval_latest"] is False
    assert result["write_plan"]["can_write_payload_targets"] is False


def test_current_targets_consume_matching_governed_refs_without_writing(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    b002 = tmp_path / B002_1055_CANDIDATE
    b003 = tmp_path / B003_1105_CANDIDATE
    _write_candidate(b002, sha_text="B002 1055 owner answer target\n")
    _write_candidate(b003, sha_text="B003 1105 owner answer target\n")

    b002_result = intake_owner_answer_candidate(
        candidate_id="B002-1055",
        candidate_path=b002,
        expected_sha256=None,
        governed_response_kind="human_gate_ref",
        governed_response_ref="human_gate:owner-answer:b002-1055",
        governed_response_study_id="002-dm-china-us-mortality-attribution",
        governed_response_owner_surface="MAS publication AI-reviewer governed owner answer",
    )
    b003_result = intake_owner_answer_candidate(
        candidate_id="B003-1105",
        candidate_path=b003,
        expected_sha256=None,
        governed_response_kind="typed_blocker_ref",
        governed_response_ref="typed-blocker:b003-1105",
        governed_response_study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        governed_response_owner_surface="MAS paper recovery / publication gate governed owner answer",
    )

    assert b002_result["status"] == "governed_response_consumed"
    assert b002_result["governed_response"]["candidate_id"] == "B002-1055"
    assert b002_result["write_plan"]["written_files"] == []
    assert b002_result["write_plan"]["can_write_payload_targets"] is False
    assert b003_result["status"] == "governed_response_consumed"
    assert b003_result["governed_response"]["candidate_id"] == "B003-1105"
    assert b003_result["write_plan"]["written_files"] == []
    assert b003_result["write_plan"]["can_write_runtime_queues_or_provider_attempts"] is False


def test_governed_response_rejects_unaccepted_kind_without_writing(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B002_0910_CANDIDATE
    _write_candidate(candidate, sha_text="B002 0910 human gate response candidate\n")

    result = intake_owner_answer_candidate(
        candidate_id="B002-0910",
        candidate_path=candidate,
        expected_sha256=None,
        governed_response_kind="owner_gate_decision_ref",
        governed_response_ref="owner-gate-decision:not-an-accepted-shape",
        governed_response_study_id="002-dm-china-us-mortality-attribution",
        governed_response_owner_surface="MAS publication AI-reviewer governed owner answer",
    )

    assert result["status"] == "governed_response_kind_not_accepted"
    assert result["governed_answer_consumed"] is False
    assert result["accepted_response_kinds"] == result["required_governed_answer_shapes"]
    assert result["write_plan"]["written_files"] == []


def test_governed_response_rejects_study_or_owner_surface_mismatch(tmp_path: Path) -> None:
    from med_autoscience.controllers.owner_answer_candidate_intake import (
        intake_owner_answer_candidate,
    )

    candidate = tmp_path / B003_0915_CANDIDATE
    _write_candidate(candidate, sha_text="B003 0915 typed blocker response candidate\n")

    study_result = intake_owner_answer_candidate(
        candidate_id="B003-0915",
        candidate_path=candidate,
        expected_sha256=None,
        governed_response_kind="typed_blocker_ref",
        governed_response_ref="typed-blocker:b003-0915",
        governed_response_study_id="002-dm-china-us-mortality-attribution",
        governed_response_owner_surface="MAS paper recovery / publication gate governed owner answer",
    )
    owner_result = intake_owner_answer_candidate(
        candidate_id="B003-0915",
        candidate_path=candidate,
        expected_sha256=None,
        governed_response_kind="typed_blocker_ref",
        governed_response_ref="typed-blocker:b003-0915",
        governed_response_study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        governed_response_owner_surface="MAS publication AI-reviewer governed owner answer",
    )

    assert study_result["status"] == "governed_response_study_mismatch"
    assert study_result["expected_study_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"
    assert owner_result["status"] == "governed_response_owner_surface_mismatch"
    assert owner_result["expected_owner_surface"] == (
        "MAS paper recovery / publication gate governed owner answer"
    )
    assert study_result["write_plan"]["written_files"] == []
    assert owner_result["write_plan"]["written_files"] == []


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


def test_owner_answer_candidate_intake_cli_consumes_matching_governed_ref(
    tmp_path: Path,
    capsys,
) -> None:
    from med_autoscience import cli

    candidate = tmp_path / B003_0915_CANDIDATE
    _write_candidate(candidate, sha_text="B003 0915 typed blocker response candidate\n")

    exit_code = cli.main(
        [
            "owner-answer-candidate-intake",
            "--candidate-id",
            "B003-0915",
            "--candidate-path",
            str(candidate),
            "--governed-response-kind",
            "typed_blocker_ref",
            "--governed-response-ref",
            "typed-blocker:b003-0915-preserve-owner-gate-decision",
            "--governed-response-study-id",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--governed-response-owner-surface",
            "MAS paper recovery / publication gate governed owner answer",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "governed_response_consumed"
    assert payload["candidate_id"] == "B003-0915"
    assert payload["governed_response"]["kind"] == "typed_blocker_ref"
    assert payload["stable_blocker_policy"]["preserve_or_explicitly_supersede"] == (
        "owner-gate-decision:d6d895635654560a85573c04"
    )
    assert payload["write_plan"]["written_files"] == []
