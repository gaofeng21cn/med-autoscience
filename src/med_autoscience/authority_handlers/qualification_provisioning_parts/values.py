"""Qualification provisioning identities, canonical values and byte fingerprints."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import posixpath
import re
from typing import Any
from .._record_validation import (
    RequestShapeError,
    exact_json_object,
    exact_keys,
    mapping,
    text,
)


REQUEST_KIND = "mas_qualification_work_item_provisioning_authority_request"


RESULT_KIND = "mas_qualification_work_item_provisioning_authority_result"


RECEIPT_KIND = "mas_qualification_work_item_provisioning_receipt"


RECEIPT_CONTENT_KIND = (
    "mas_qualification_work_item_provisioning_receipt_content_binding"
)


SCHEMA_VERSION = 1


ACTION_ID = "qualification_work_item_provisioning_authority_evaluate"


DOMAIN_ID = "medautoscience"


DOMAIN_OWNER = "MedAutoScience"


QUALIFICATION_SCOPE = "standard_agent_full_vm_qualification"


HOST_CAPABILITY_ID = "opl_domain_artifact_cas_materialization.v1"


_SAFE_STUDY_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


_AUTHORITY_BOUNDARY = {
    "owner": DOMAIN_OWNER,
    "handler_role": "authorize_one_qualification_only_work_item_and_exact_cas_bytes",
    "opl_role": "journal_and_materialize_exact_authorized_bytes_all_or_rollback",
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "owns_runtime_or_attempt_lifecycle": False,
    "persists_artifact_or_receipt": False,
    "selects_scientific_stage": False,
    "authorizes_stage_body": False,
    "authorizes_business_action": False,
    "authorizes_publication": False,
    "authorizes_submission": False,
    "provider_completion_is_domain_completion": False,
    "public_action": False,
}


def _raw_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise RequestShapeError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _canonical_workspace_root(value: Any, field: str) -> str:
    root = text(value, field)
    if (
        not root.startswith("/")
        or root == "/"
        or "\\" in root
        or "//" in root
        or posixpath.normpath(root) != root
    ):
        raise RequestShapeError(f"{field} must be a canonical absolute POSIX path")
    return root


def _workspace_relative_path(value: Any, field: str) -> str:
    path = text(value, field)
    if (
        path.startswith("/")
        or "\\" in path
        or "//" in path
        or posixpath.normpath(path) != path
        or path in {".", ".."}
        or path.startswith("../")
    ):
        raise RequestShapeError(f"{field} must stay within the workspace")
    return path


def _timestamp(value: Any, field: str) -> str:
    raw = text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise RequestShapeError(f"{field} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise RequestShapeError(f"{field} must include a timezone")
    return raw


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RequestShapeError(
            "authority JSON contains an unsupported or non-finite value"
        ) from error


def _bytes_sha256(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _fingerprint(value: Any) -> str:
    return _bytes_sha256(_canonical_json_bytes(value))
