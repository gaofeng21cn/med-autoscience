"""Independent review and epistemic currentness fixture builders."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._primitives import PrimitiveAuthorityFixtures
from .surface_constants import AUTHORITY_ROLE_BY_LANE


class ReviewFixtures(PrimitiveAuthorityFixtures):

    @classmethod
    def epistemic_currentness(
        cls,
        manifest: dict[str, Any],
        lane: str,
        *,
        invalidating_changes: list[dict[str, Any]] | None = None,
        ignored_changes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers._generation_manifest import (
            epistemic_review_dependency_refs,
        )

        scope = next(
            item["epistemic_scope"]
            for item in manifest["review_scopes"]
            if item["review_lane"] == lane
        )
        invalidating = deepcopy(invalidating_changes or [])
        ignored = deepcopy(ignored_changes or [])
        return {
            "surface_kind": "opl_epistemic_review_currentness_evaluation",
            "version": "opl-epistemic-review-currentness-evaluation.v2",
            "scope_id": scope["scope_id"],
            "scope_kind": scope["scope_kind"],
            "status": "stale" if invalidating else "current",
            "invalidating_changes": invalidating,
            "ignored_changes": ignored,
            "reviewed_dependency_refs": epistemic_review_dependency_refs(scope),
            "authority_boundary": deepcopy(scope["authority_boundary"]),
        }

    @classmethod
    def independent_review_wrapper(
        cls,
        *,
        lane: str,
        manifest: dict[str, Any],
        manifest_ref: dict[str, Any],
        candidate_receipt_ref: dict[str, Any],
        review_request_ref: dict[str, Any],
        producer_output_ref: dict[str, Any],
        verdict: str = "passed",
        defect_refs: list[dict[str, Any]] | None = None,
        quality_debt_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        scope = next(
            (
                item
                for item in manifest.get("review_scopes", [])
                if item["review_lane"] == lane
            ),
            None,
        )
        core = {
            "receipt_kind": "mas_independent_review_receipt",
            "schema_version": manifest["schema_version"],
            "issuer": "MedAutoScience",
            "authority_role": AUTHORITY_ROLE_BY_LANE[lane],
            "authority_epoch": cls.authority_epoch,
            "review_lane": lane,
            "verdict": verdict,
            "review_request_ref": review_request_ref,
            "producer_output_ref": producer_output_ref,
            "reviewer_attempt_ref": cls.typed_ref(
                "opl_stage_attempt", f"independent-{lane}-reviewer"
            ),
            "rubric_ref": cls.typed_ref("mas_quality_rubric", f"{lane}-rubric"),
            "accepted_candidate_receipt_refs": [candidate_receipt_ref],
            "defect_refs": deepcopy(defect_refs or []),
            "quality_debt_codes": list(quality_debt_codes or []),
        }
        if manifest["schema_version"] == 1:
            core.update(
                {
                    "generation_id": manifest["generation_id"],
                    "generation_manifest_sha256": manifest[
                        "generation_manifest_sha256"
                    ],
                    "reviewed_members": deepcopy(manifest["artifacts"]),
                }
            )
        else:
            if scope is None:
                raise AssertionError(f"missing review scope for {lane}")
            from med_autoscience.authority_handlers._generation_manifest import (
                review_scope_member_projection,
            )

            binding_members = review_scope_member_projection(scope["reviewed_members"])
            owner_refs_by_member_id = {
                item["member_id"]: item["ref"] for item in scope["reviewed_members"]
            }
            authority_issuer = cls.review_snapshot_authority_issuer()
            authority_record = {
                "surface_kind": "mas_review_input_snapshot_authority",
                "schema_version": 2,
                "issuer": authority_issuer,
                "generation_ref": manifest_ref["ref"],
                "review_lane": lane,
                "scope_policy_id": "mas_review_scope_dependency_map",
                "scope_policy_version": 2,
                "review_scope_sha256": scope["review_scope_sha256"],
                "members": [
                    {
                        **item,
                        "owner_ref": owner_refs_by_member_id[item["member_id"]],
                    }
                    for item in binding_members
                ],
            }
            authority_sha256 = cls.fingerprint(authority_record)
            core.update(
                {
                    "issued_generation_id": manifest["generation_id"],
                    "issued_generation_manifest_sha256": manifest[
                        "generation_manifest_sha256"
                    ],
                    "scope_policy_id": scope["scope_policy_id"],
                    "scope_policy_version": scope["scope_policy_version"],
                    "review_scope_sha256": scope["review_scope_sha256"],
                    "reviewed_members": deepcopy(scope["reviewed_members"]),
                    "review_input_snapshot_binding": {
                        "surface_kind": "opl_reviewer_input_snapshot_binding",
                        "schema_version": 3,
                        "snapshot_manifest_ref": cls.exact_ref(
                            "opl_reviewer_input_snapshot_manifest",
                            f"{manifest['generation_id']}-{lane}-review-input-snapshot",
                        ),
                        "owner_authority_ref": {
                            "kind": "mas_review_input_snapshot_authority",
                            "ref": (
                                "mas-review-input-snapshot-authority:"
                                f"{authority_sha256.removeprefix('sha256:')}"
                            ),
                            "size_bytes": len(cls.canonical_bytes(authority_record)),
                            "sha256": authority_sha256,
                        },
                        "producer_attempt_ref": authority_issuer["stage_attempt_ref"],
                        "execution_content_binding_sha256": authority_issuer[
                            "execution_content_binding_sha256"
                        ],
                    },
                }
            )
        receipt_fingerprint = cls.fingerprint(core)
        receipt_ref = {
            "kind": "mas_reviewer_receipt",
            "ref": (
                f"mas-independent-review-receipt:{lane}:"
                f"{receipt_fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": receipt_fingerprint,
        }
        return {"receipt_ref": receipt_ref, "receipt": core}
