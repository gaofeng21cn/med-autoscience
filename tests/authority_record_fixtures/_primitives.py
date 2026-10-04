"""Primitive exact-ref, digest, seal, and authority fixture values."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any


class PrimitiveAuthorityFixtures:
    authority_epoch = "mas-authority-epoch-2026-07-15"
    generation_id = "study-generation-003"

    @staticmethod
    def canonical_bytes(payload: dict[str, Any]) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def digest(cls, value: str | bytes) -> str:
        encoded = value.encode("utf-8") if isinstance(value, str) else value
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    @classmethod
    def fingerprint(cls, payload: dict[str, Any]) -> str:
        return cls.digest(cls.canonical_bytes(payload))

    @classmethod
    def review_snapshot_authority_issuer(cls) -> dict[str, Any]:
        return {
            "agent_id": "mas",
            "domain_id": "medautoscience",
            "package_id": "mas",
            "stage_attempt_ref": "opl://stage_attempts/producer-attempt-001",
            "execution_content_binding_sha256": cls.digest(
                "producer-attempt-execution-content-binding"
            ),
            "package_use_boundary_id": "package-use:producer-attempt-001",
            "root_package_content_digest": cls.digest("mas-package-content"),
        }

    @classmethod
    def typed_ref(cls, kind: str, name: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": f"{kind}://{name}",
            "sha256": cls.digest(f"{kind}:{name}:bytes"),
        }

    @classmethod
    def exact_ref(
        cls,
        kind: str,
        name: str,
        *,
        size_bytes: int | None = None,
        sha256: str | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": f"{kind}://{name}",
            "size_bytes": size_bytes if size_bytes is not None else 100 + len(name),
            "sha256": sha256 or cls.digest(f"{kind}:{name}:bytes"),
        }

    @staticmethod
    def no_authority_boundary() -> dict[str, bool]:
        return {"authorizes_publication": False, "authorizes_submission": False}

    @staticmethod
    def artifact_exact_ref(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @staticmethod
    def affected_artifact_binding(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "member_id": artifact["member_id"],
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @classmethod
    def seal(cls, core: dict[str, Any], prefix: str) -> dict[str, Any]:
        receipt_fingerprint = cls.fingerprint(core)
        return {
            **deepcopy(core),
            "receipt_id": f"{prefix}:{receipt_fingerprint.removeprefix('sha256:')}",
            "receipt_size_bytes": len(cls.canonical_bytes(core)),
            "receipt_fingerprint": receipt_fingerprint,
        }

    @classmethod
    def receipt_ref(cls, kind: str, receipt: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": receipt["receipt_id"],
            "size_bytes": receipt["receipt_size_bytes"],
            "sha256": receipt["receipt_fingerprint"],
        }

    @classmethod
    def build_dependency_currentness_authority(
        cls,
        dependency_manifest_ref: dict[str, Any],
        dependency_currentness: str,
        reviewer_response_currentness: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers.build_dependency_currentness import (
            evaluate_build_dependency_currentness_authority,
        )

        request = cls.build_dependency_currentness_authority_request(
            dependency_manifest_ref,
            dependency_currentness,
            reviewer_response_currentness,
        )
        result = evaluate_build_dependency_currentness_authority(request)
        if result["status"] != "owner_authority":
            raise AssertionError(result)
        return {
            "authority_ref": deepcopy(result["authority_ref"]),
            "authority_record": deepcopy(result["authority_record"]),
        }

    @classmethod
    def build_dependency_currentness_authority_request(
        cls,
        dependency_manifest_ref: dict[str, Any],
        dependency_currentness: str,
        reviewer_response_currentness: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reviewer_response_currentness = reviewer_response_currentness or {
            "generation_id": cls.generation_id,
            "candidate_state": "pre_freeze",
            "response_ref": cls.exact_ref(
                "mas_artifact", "reviewer-response-current"
            ),
            "prior_frozen_response_ref": None,
            "post_freeze_disposition": "not_started",
            "external_synthesis_ref": None,
            "new_revision_ref": None,
            "owner_ledger_history_ref": cls.exact_ref(
                "opl_action_output", "build-dependency-currentness-owner-ledger"
            ),
        }
        return {
            "surface_kind": "mas_build_dependency_currentness_authority_request",
            "schema_version": 1,
            "authority_context": {
                "action_id": "build_dependency_currentness_authority_evaluate",
                "authority_epoch": cls.authority_epoch,
                "managed_authority_attempt_ref": cls.typed_ref(
                    "opl_stage_attempt", "build-dependency-currentness-owner"
                ),
                "generation_producer_attempt_ref": cls.typed_ref(
                    "opl_stage_attempt", "paper-producer"
                ),
                "managed_authority_attempt_receipt_ref": cls.exact_ref(
                    "opl_action_output", "build-dependency-currentness-attempt"
                ),
                "owner_ledger_ref": cls.exact_ref(
                    "opl_action_output", "build-dependency-currentness-owner-ledger"
                ),
            },
            "dependency_manifest_ref": deepcopy(dependency_manifest_ref),
            "dependency_currentness": dependency_currentness,
            "reviewer_response_currentness": deepcopy(
                reviewer_response_currentness
            ),
        }

    @staticmethod
    def artifact_binding(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            key: artifact[key]
            for key in ("member_id", "role", "ref", "size_bytes", "sha256")
        }

    @classmethod
    def mas_artifact_ref(cls, artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @classmethod
    def professional_invocation_ref(
        cls,
        invocation_core: dict[str, Any],
    ) -> dict[str, Any]:
        invocation_sha256 = cls.fingerprint(invocation_core)
        return {
            "kind": "mas_professional_skill_invocation",
            "ref": (
                "mas-professional-skill-invocation:"
                f"{invocation_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(invocation_core)),
            "sha256": invocation_sha256,
        }

    @classmethod
    def professional_receipt_ref(
        cls,
        receipt_core: dict[str, Any],
    ) -> dict[str, Any]:
        receipt_sha256 = cls.fingerprint(receipt_core)
        return {
            "kind": "scholarskills_professional_skill_receipt",
            "ref": (
                "scholarskills-professional-skill-receipt:"
                f"{receipt_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(receipt_core)),
            "sha256": receipt_sha256,
        }

    @classmethod
    def candidate_member(cls) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "role": "candidate_artifact",
            "ref": "mas-artifact://bounded-candidate",
            "size_bytes": 431,
            "sha256": cls.digest("bounded-candidate-bytes"),
        }

    @classmethod
    def evidence_member(cls) -> dict[str, Any]:
        return {
            "kind": "mas_evidence",
            "role": "evidence_record",
            "ref": "mas-evidence://bounded-candidate-evidence",
            "size_bytes": 733,
            "sha256": cls.digest("bounded-candidate-evidence-bytes"),
        }
