from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from med_autoscience.authority_handlers.foundry_owner_gate import (
    OwnerGateError,
    canonical_json_bytes,
    verify_owner_gate_request,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "contracts" / "foundry_owner_gate_policy.json"
AUTHORITY_REF = "target-agent-owner:med-autoscience"
RUN_ID = "foundry:mas:create:20260724"
VERSION_DIGEST = f"sha256:{'1' * 64}"
FIXED_NOW = "2026-07-24T00:00:00+00:00"


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_bytes())


def _statement(**overrides: object) -> dict[str, object]:
    statement: dict[str, object] = {
        "surface_kind": "opl_foundry_owner_authority_receipt",
        "version": "opl-foundry-owner-authority-receipt.v1",
        "receipt_id": "mas-owner:foundry:approve-active:20260724",
        "authority_ref": AUTHORITY_REF,
        "action": "approve_active",
        "decision": "approve",
        "target_agent_id": "mas",
        "target_domain_id": "medautoscience",
        "run_id": RUN_ID,
        "version_digest": VERSION_DIGEST,
        "expected_revision": 8,
        "issued_at": FIXED_NOW,
    }
    statement.update(overrides)
    return statement


def _receipt(**overrides: object) -> dict[str, object]:
    statement = _statement(**overrides)
    digest = f"sha256:{hashlib.sha256(canonical_json_bytes(statement)).hexdigest()}"
    return {
        **statement,
        "receipt_digest": digest,
        "receipt_ref": f"opl://foundry/owner-authority-receipts/{digest}",
    }


def _context(receipt: dict[str, object], **overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "surface_kind": "opl_foundry_owner_gate_verification_context",
        "version": "opl-foundry-owner-gate-verification-context.v1",
        "authority_receipt_ref": receipt["receipt_ref"],
        "action": receipt["action"],
        "decision": receipt["decision"],
        "target_agent_id": receipt["target_agent_id"],
        "target_domain_id": receipt["target_domain_id"],
        "run_id": receipt["run_id"],
        "version_digest": receipt["version_digest"],
        "expected_revision": receipt["expected_revision"],
    }
    context.update(overrides)
    return context


def _request(context: dict[str, object]) -> dict[str, object]:
    return {
        "surface_kind": "opl_foundry_owner_gate_process_request",
        "version": "opl-foundry-owner-gate-process-request.v1",
        "context": context,
    }


def _write_receipt(receipt_dir: Path, receipt: dict[str, object]) -> Path:
    digest = str(receipt["receipt_digest"]).removeprefix("sha256:")
    path = receipt_dir / f"{digest}.json"
    path.write_bytes(canonical_json_bytes(receipt))
    return path


def test_verifies_exact_physical_canonical_owner_receipt(tmp_path: Path) -> None:
    receipt = _receipt()
    _write_receipt(tmp_path, receipt)

    verification = verify_owner_gate_request(
        _request(_context(receipt)),
        policy=_policy(),
        receipt_dir=tmp_path,
        now=FIXED_NOW,
    )

    assert verification["surface_kind"] == "opl_foundry_owner_gate_verification"
    assert verification["version"] == "opl-foundry-owner-gate-verification.v1"
    assert verification["authority_policy_ref"] == "policy:mas/foundry-owner-gate/v1"
    assert verification["covered_authority_ref"] == AUTHORITY_REF
    assert verification["receipt"] == receipt
    assert str(verification["verification_ref"]).startswith(
        "opl://foundry/owner-gate-verifications/sha256:"
    )


@pytest.mark.parametrize(
    ("label", "context_overrides"),
    [
        ("target agent", {"target_agent_id": "mag"}),
        ("target domain", {"target_domain_id": "medautogrant"}),
        ("action", {"action": "authorize_improve"}),
        ("decision", {"decision": "reject"}),
        ("run", {"run_id": "foundry:other"}),
        ("version", {"version_digest": f"sha256:{'2' * 64}"}),
        ("revision", {"expected_revision": 9}),
    ],
)
def test_rejects_every_mismatched_context_dimension(
    tmp_path: Path,
    label: str,
    context_overrides: dict[str, object],
) -> None:
    receipt = _receipt()
    _write_receipt(tmp_path, receipt)

    with pytest.raises(OwnerGateError, match="not allowed|exact context"):
        verify_owner_gate_request(
            _request(_context(receipt, **context_overrides)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )


def test_rejects_unknown_action_even_with_matching_receipt(tmp_path: Path) -> None:
    receipt = _receipt(action="rollback", decision="rollback")
    _write_receipt(tmp_path, receipt)

    with pytest.raises(OwnerGateError, match="not allowed"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )


def test_rejects_wrong_authority_and_noncanonical_bytes(tmp_path: Path) -> None:
    wrong_authority = _receipt(authority_ref="target-agent-owner:other")
    _write_receipt(tmp_path, wrong_authority)
    with pytest.raises(OwnerGateError, match="authority is not allowed"):
        verify_owner_gate_request(
            _request(_context(wrong_authority)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )

    receipt = _receipt()
    path = _write_receipt(tmp_path, receipt)
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    with pytest.raises(OwnerGateError, match="canonical JSON"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )


def test_rejects_ref_content_substitution_and_unknown_ref(tmp_path: Path) -> None:
    receipt = _receipt()
    path = _write_receipt(tmp_path, receipt)
    substituted = _receipt(receipt_id="mas-owner:substituted")
    path.write_bytes(canonical_json_bytes(substituted))
    with pytest.raises(OwnerGateError, match="digest or ref|filename|exact context"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )

    path.unlink()
    with pytest.raises(OwnerGateError, match="unavailable"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=tmp_path,
            now=FIXED_NOW,
        )


def test_rejects_symlink_receipt_and_symlink_store(tmp_path: Path) -> None:
    receipt = _receipt()
    physical_dir = tmp_path / "physical"
    physical_dir.mkdir()
    physical = _write_receipt(physical_dir, receipt)
    receipt_name = physical.name

    linked_receipt_dir = tmp_path / "linked-receipt"
    linked_receipt_dir.mkdir()
    (linked_receipt_dir / receipt_name).symlink_to(physical)
    with pytest.raises(OwnerGateError, match="not physical"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=linked_receipt_dir,
            now=FIXED_NOW,
        )

    linked_store = tmp_path / "linked-store"
    linked_store.symlink_to(physical_dir, target_is_directory=True)
    with pytest.raises(OwnerGateError, match="physical directory"):
        verify_owner_gate_request(
            _request(_context(receipt)),
            policy=_policy(),
            receipt_dir=linked_store,
            now=FIXED_NOW,
        )


def test_process_entrypoint_is_read_only_and_fails_closed(tmp_path: Path) -> None:
    receipt = _receipt()
    receipt_path = _write_receipt(tmp_path, receipt)
    before = receipt_path.read_bytes()
    command = [
        sys.executable,
        "-m",
        "med_autoscience.authority_handlers.foundry_owner_gate",
        "--policy",
        str(POLICY_PATH),
        "--receipt-dir",
        str(tmp_path),
    ]
    environment = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    completed = subprocess.run(
        command,
        input=canonical_json_bytes(_request(_context(receipt))),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert json.loads(completed.stdout)["receipt"] == receipt
    assert receipt_path.read_bytes() == before

    failed = subprocess.run(
        command,
        input=canonical_json_bytes(
            _request(_context(receipt, expected_revision=999))
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
    )
    assert failed.returncode != 0
    assert failed.stdout == b""
    assert b"exact context" in failed.stderr
