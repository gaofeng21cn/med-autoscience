"""Verify exact MAS owner receipts for OPL Foundry authority mutations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROCESS_SURFACE = "opl_foundry_owner_gate_process_request"
PROCESS_VERSION = "opl-foundry-owner-gate-process-request.v1"
CONTEXT_SURFACE = "opl_foundry_owner_gate_verification_context"
CONTEXT_VERSION = "opl-foundry-owner-gate-verification-context.v1"
RECEIPT_SURFACE = "opl_foundry_owner_authority_receipt"
RECEIPT_VERSION = "opl-foundry-owner-authority-receipt.v1"
VERIFICATION_SURFACE = "opl_foundry_owner_gate_verification"
VERIFICATION_VERSION = "opl-foundry-owner-gate-verification.v1"
POLICY_SURFACE = "mas_foundry_owner_gate_policy"
POLICY_VERSION = "mas-foundry-owner-gate-policy.v1"
RECEIPT_REF_PREFIX = "opl://foundry/owner-authority-receipts/sha256:"
MAX_INPUT_BYTES = 1024 * 1024

PROCESS_KEYS = {"surface_kind", "version", "context"}
CONTEXT_KEYS = {
    "surface_kind",
    "version",
    "authority_receipt_ref",
    "action",
    "decision",
    "target_agent_id",
    "target_domain_id",
    "run_id",
    "version_digest",
    "expected_revision",
}
RECEIPT_KEYS = {
    "surface_kind",
    "version",
    "receipt_id",
    "authority_ref",
    "action",
    "decision",
    "target_agent_id",
    "target_domain_id",
    "run_id",
    "version_digest",
    "expected_revision",
    "issued_at",
    "receipt_digest",
    "receipt_ref",
}
POLICY_KEYS = {
    "surface_kind",
    "version",
    "policy_ref",
    "owner",
    "target",
    "allowed_authority_refs",
    "allowed_actions",
    "receipt_store",
    "authority_boundary",
}


class OwnerGateError(ValueError):
    """A fail-closed MAS OwnerGate verification failure."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OwnerGateError(f"{label} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise OwnerGateError(f"{label} has unknown or missing fields")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnerGateError(f"{label} must be a non-empty string")
    return value.strip()


def _revision(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OwnerGateError(f"{label} must be a non-negative integer")
    return value


def _digest(value: Any, label: str) -> str:
    text = _text(value, label)
    if (
        len(text) != 71
        or not text.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in text[7:])
    ):
        raise OwnerGateError(f"{label} must be a SHA-256 digest")
    return text


def _timestamp(value: Any, label: str) -> str:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise OwnerGateError(f"{label} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None:
        raise OwnerGateError(f"{label} must include a timezone")
    return text


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise OwnerGateError("value is not canonical JSON") from error


def _sha256(bytes_value: bytes) -> str:
    return hashlib.sha256(bytes_value).hexdigest()


def _load_json_file(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise OwnerGateError(f"{label} is unavailable") from error
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise OwnerGateError(f"{label} has an invalid byte length")
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OwnerGateError(f"{label} is not valid JSON") from error
    return _object(value, label), raw


def _validate_policy(raw_policy: Any) -> dict[str, Any]:
    policy = _object(raw_policy, "policy")
    _exact_keys(policy, POLICY_KEYS, "policy")
    if (
        policy.get("surface_kind") != POLICY_SURFACE
        or policy.get("version") != POLICY_VERSION
        or policy.get("owner") != "med-autoscience"
    ):
        raise OwnerGateError("policy identity is invalid")
    _text(policy.get("policy_ref"), "policy_ref")

    target = _object(policy.get("target"), "policy target")
    _exact_keys(target, {"target_agent_id", "target_domain_id"}, "policy target")
    if target != {
        "target_agent_id": "mas",
        "target_domain_id": "medautoscience",
    }:
        raise OwnerGateError("policy target is invalid")

    authority_refs = policy.get("allowed_authority_refs")
    if (
        not isinstance(authority_refs, list)
        or not authority_refs
        or any(not isinstance(entry, str) or not entry.strip() for entry in authority_refs)
        or len(set(authority_refs)) != len(authority_refs)
    ):
        raise OwnerGateError("policy authority refs are invalid")

    allowed_actions = _object(policy.get("allowed_actions"), "policy allowed_actions")
    if allowed_actions != {
        "authorize_improve": "approve",
        "approve_canary": "approve",
        "approve_active": "approve",
    }:
        raise OwnerGateError("policy actions are invalid")

    receipt_store = _object(policy.get("receipt_store"), "policy receipt_store")
    _exact_keys(
        receipt_store,
        {
            "kind",
            "root_source",
            "filename_scheme",
            "physical_non_symlink_required",
            "canonical_json_bytes_required",
        },
        "policy receipt_store",
    )
    if receipt_store != {
        "kind": "owner_issued_content_addressed_files",
        "root_source": "explicit_process_argument",
        "filename_scheme": "sha256_hex_json",
        "physical_non_symlink_required": True,
        "canonical_json_bytes_required": True,
    }:
        raise OwnerGateError("policy receipt store is invalid")

    boundary = _object(policy.get("authority_boundary"), "policy authority_boundary")
    _exact_keys(
        boundary,
        {
            "verifier_can_issue_receipt",
            "verifier_can_auto_approve",
            "verifier_can_write_foundry_state",
            "verifier_can_write_domain_truth",
            "unknown_or_mismatched_receipt",
        },
        "policy authority_boundary",
    )
    if boundary != {
        "verifier_can_issue_receipt": False,
        "verifier_can_auto_approve": False,
        "verifier_can_write_foundry_state": False,
        "verifier_can_write_domain_truth": False,
        "unknown_or_mismatched_receipt": "fail_closed",
    }:
        raise OwnerGateError("policy authority boundary is invalid")
    return policy


def _validate_context(raw_context: Any, policy: dict[str, Any]) -> dict[str, Any]:
    context = _object(raw_context, "context")
    _exact_keys(context, CONTEXT_KEYS, "context")
    if (
        context.get("surface_kind") != CONTEXT_SURFACE
        or context.get("version") != CONTEXT_VERSION
    ):
        raise OwnerGateError("context identity is invalid")
    target = policy["target"]
    if (
        context.get("target_agent_id") != target["target_agent_id"]
        or context.get("target_domain_id") != target["target_domain_id"]
    ):
        raise OwnerGateError("context target is not allowed")
    action = _text(context.get("action"), "context action")
    decision = _text(context.get("decision"), "context decision")
    if policy["allowed_actions"].get(action) != decision:
        raise OwnerGateError("context action or decision is not allowed")
    _text(context.get("run_id"), "context run_id")
    _digest(context.get("version_digest"), "context version_digest")
    _revision(context.get("expected_revision"), "context expected_revision")
    receipt_ref = _text(
        context.get("authority_receipt_ref"),
        "context authority_receipt_ref",
    )
    if (
        len(receipt_ref) != len(RECEIPT_REF_PREFIX) + 64
        or not receipt_ref.startswith(RECEIPT_REF_PREFIX)
        or any(character not in "0123456789abcdef" for character in receipt_ref[-64:])
    ):
        raise OwnerGateError("context authority_receipt_ref is invalid")
    return context


def _read_physical_receipt(receipt_dir: Path, receipt_ref: str) -> tuple[dict[str, Any], bytes]:
    if not receipt_dir.is_absolute():
        raise OwnerGateError("receipt directory must be absolute")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_descriptor = os.open(receipt_dir, directory_flags)
    except OSError as error:
        raise OwnerGateError("receipt directory must be a physical directory") from error
    directory_stat = os.fstat(directory_descriptor)
    if not stat.S_ISDIR(directory_stat.st_mode):
        os.close(directory_descriptor)
        raise OwnerGateError("receipt directory must be a physical directory")

    digest_hex = receipt_ref[-64:]
    receipt_name = f"{digest_hex}.json"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(receipt_name, flags, dir_fd=directory_descriptor)
    except OSError as error:
        os.close(directory_descriptor)
        raise OwnerGateError("owner receipt is unavailable or not physical") from error
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise OwnerGateError("owner receipt must be a physical regular file")
        if file_stat.st_size <= 0 or file_stat.st_size > MAX_INPUT_BYTES:
            raise OwnerGateError("owner receipt has an invalid byte length")
        raw = b""
        while len(raw) < file_stat.st_size:
            chunk = os.read(descriptor, min(65536, file_stat.st_size - len(raw)))
            if not chunk:
                break
            raw += chunk
        if len(raw) != file_stat.st_size:
            raise OwnerGateError("owner receipt changed during read")
    finally:
        os.close(descriptor)
        os.close(directory_descriptor)

    try:
        receipt = _object(json.loads(raw), "owner receipt")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OwnerGateError("owner receipt is not valid JSON") from error
    if raw != canonical_json_bytes(receipt):
        raise OwnerGateError("owner receipt bytes are not canonical JSON")
    return receipt, raw


def _validate_receipt(
    raw_receipt: Any,
    context: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    receipt = _object(raw_receipt, "owner receipt")
    _exact_keys(receipt, RECEIPT_KEYS, "owner receipt")
    if (
        receipt.get("surface_kind") != RECEIPT_SURFACE
        or receipt.get("version") != RECEIPT_VERSION
    ):
        raise OwnerGateError("owner receipt identity is invalid")
    authority_ref = _text(receipt.get("authority_ref"), "owner receipt authority_ref")
    if authority_ref not in policy["allowed_authority_refs"]:
        raise OwnerGateError("owner receipt authority is not allowed")

    statement = {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_digest", "receipt_ref"}
    }
    receipt_digest = f"sha256:{_sha256(canonical_json_bytes(statement))}"
    receipt_ref = f"opl://foundry/owner-authority-receipts/{receipt_digest}"
    if (
        receipt.get("receipt_digest") != receipt_digest
        or receipt.get("receipt_ref") != receipt_ref
    ):
        raise OwnerGateError("owner receipt digest or ref is invalid")

    exact_fields = (
        "action",
        "decision",
        "target_agent_id",
        "target_domain_id",
        "run_id",
        "version_digest",
        "expected_revision",
    )
    if any(receipt.get(field) != context.get(field) for field in exact_fields):
        raise OwnerGateError("owner receipt does not cover the exact context")
    _text(receipt.get("receipt_id"), "owner receipt receipt_id")
    _timestamp(receipt.get("issued_at"), "owner receipt issued_at")
    return receipt


def verify_owner_gate_request(
    raw_request: Any,
    *,
    policy: dict[str, Any],
    receipt_dir: Path,
    now: str,
) -> dict[str, Any]:
    request = _object(raw_request, "process request")
    _exact_keys(request, PROCESS_KEYS, "process request")
    if (
        request.get("surface_kind") != PROCESS_SURFACE
        or request.get("version") != PROCESS_VERSION
    ):
        raise OwnerGateError("process request identity is invalid")
    validated_policy = _validate_policy(policy)
    context = _validate_context(request.get("context"), validated_policy)
    receipt, _raw = _read_physical_receipt(
        receipt_dir,
        context["authority_receipt_ref"],
    )
    validated_receipt = _validate_receipt(receipt, context, validated_policy)
    if validated_receipt["receipt_digest"] != f"sha256:{context['authority_receipt_ref'][-64:]}":
        raise OwnerGateError("owner receipt filename does not match its ref")
    verified_at = _timestamp(now, "verified_at")
    verification_digest = _sha256(
        canonical_json_bytes(
            {
                "authority_policy_ref": validated_policy["policy_ref"],
                "context": context,
                "receipt_digest": validated_receipt["receipt_digest"],
            }
        )
    )
    return {
        "surface_kind": VERIFICATION_SURFACE,
        "version": VERIFICATION_VERSION,
        "verifier_id": "mas-owner-gate:foundry-v1",
        "verification_ref": (
            "opl://foundry/owner-gate-verifications/"
            f"sha256:{verification_digest}"
        ),
        "authority_policy_ref": validated_policy["policy_ref"],
        "verified_at": verified_at,
        "covered_authority_ref": validated_receipt["authority_ref"],
        "receipt": validated_receipt,
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--receipt-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    try:
        raw_input = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not raw_input or len(raw_input) > MAX_INPUT_BYTES:
            raise OwnerGateError("process request has an invalid byte length")
        request = json.loads(raw_input)
        policy, _raw_policy = _load_json_file(arguments.policy, "policy")
        result = verify_owner_gate_request(
            request,
            policy=policy,
            receipt_dir=arguments.receipt_dir,
            now=datetime.now().astimezone().isoformat(),
        )
    except (OwnerGateError, json.JSONDecodeError, UnicodeDecodeError) as error:
        sys.stderr.write(f"mas-foundry-owner-gate: {error}\n")
        raise SystemExit(1) from error
    sys.stdout.buffer.write(canonical_json_bytes(result))


if __name__ == "__main__":
    main()


__all__ = [
    "OwnerGateError",
    "canonical_json_bytes",
    "verify_owner_gate_request",
]
