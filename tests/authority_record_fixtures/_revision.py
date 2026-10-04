"""Revision consumption and receipt resealing fixture builders."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._professional_quality import ProfessionalQualityFixtures


class RevisionFixtures(ProfessionalQualityFixtures):

    @classmethod
    def bind_revision_consumption(
        cls,
        request: dict[str, Any],
        *,
        finding_statuses: dict[str, str] | None = None,
        revision_intake_names: tuple[str, ...] = ("revision-intake-current",),
    ) -> None:
        finding_statuses = finding_statuses or {"OPL-REV-001": "closed"}
        revision_intake_refs = [
            cls.exact_ref("opl_revision_intake", name) for name in revision_intake_names
        ]
        revision_intake_refs.sort(
            key=lambda item: (item["ref"], item["size_bytes"], item["sha256"])
        )
        opl_review_receipt_ref = cls.exact_ref(
            "opl_stage_review_receipt", "revision-review-current"
        )
        finding_ids = sorted(finding_statuses)
        finding_lineage = {
            "review_kind": "finding_closure_review",
            "finding_ids": finding_ids,
            "findings_sha256": cls.digest("revision-findings-current"),
            "repair_map_sha256": cls.digest("revision-repair-map-current"),
            "re_review_result_sha256": cls.digest("revision-re-review-current"),
        }
        finding_closures = [
            {
                "finding_id": finding_id,
                "status": status,
                "evidence_refs": [f"mas-revision-evidence://{finding_id}"],
            }
            for finding_id, status in sorted(finding_statuses.items())
        ]
        consumed_revision_refs = [*revision_intake_refs, opl_review_receipt_ref]
        consumed_revision_refs.sort(
            key=lambda item: (
                item["kind"],
                item["ref"],
                item["size_bytes"],
                item["sha256"],
            )
        )
        revision_core = {
            "receipt_kind": "mas_revision_consumption_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "revision_consumption_owner",
            "mission_identity": {
                name: request["mission"][name]
                for name in ("program_id", "study_id", "mission_id")
            },
            "generation_id": request["generation_manifest"]["generation_id"],
            "producer_attempt_ref": deepcopy(
                request["host_context"]["producer_attempt_ref"]
            ),
            "producer_output_ref": deepcopy(request["host_context"]["output_ref"]),
            "applicability": "revision_consumed",
            "revision_intake_refs": revision_intake_refs,
            "opl_review_receipt_ref": opl_review_receipt_ref,
            "opl_finding_lineage": finding_lineage,
            "finding_closures": finding_closures,
            "consumed_revision_refs": consumed_revision_refs,
            "authority_boundary": {
                "receipt_can_authorize_review_verdict": False,
                "receipt_can_authorize_owner_receipt": False,
                "receipt_can_authorize_publication": False,
                "receipt_can_authorize_submission": False,
                "receipt_can_create_typed_blocker": False,
            },
        }
        revision_receipt = cls.seal(revision_core, "mas-revision-consumption")
        request["revision_consumption"] = {
            "surface_kind": "mas_revision_consumption_binding",
            "schema_version": 1,
            "current_accepted_or_active_revision_intake_refs": deepcopy(
                revision_intake_refs
            ),
            "consumption_receipt_ref": cls.receipt_ref(
                "mas_revision_consumption_receipt", revision_receipt
            ),
            "consumption_receipt": revision_receipt,
        }

    @classmethod
    def reseal_revision_consumption(cls, request: dict[str, Any]) -> None:
        receipt = request["revision_consumption"]["consumption_receipt"]
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-revision-consumption")
        request["revision_consumption"]["consumption_receipt"] = sealed
        request["revision_consumption"]["consumption_receipt_ref"] = cls.receipt_ref(
            "mas_revision_consumption_receipt", sealed
        )

    @classmethod
    def reseal_review_currentness(cls, request: dict[str, Any]) -> None:
        receipt = request["review_authority"]["currentness_receipt"]
        if receipt["schema_version"] == 2:
            receipt["lane_currentness"].sort(key=lambda item: item["review_lane"])
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-review-currentness")
        request["review_authority"]["currentness_receipt"] = sealed
        request["review_authority"]["currentness_receipt_ref"] = cls.receipt_ref(
            "mas_review_currentness_receipt", sealed
        )

    @classmethod
    def reseal_selected_build_currentness_receipt(
        cls,
        request: dict[str, Any],
    ) -> None:
        selected_build = request["generation_manifest"]["selected_build_binding"]
        receipt = selected_build["dependency_currentness_receipt"]
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-build-dependency-currentness")
        selected_build["dependency_currentness_receipt"] = sealed
        selected_build["dependency_currentness_receipt_ref"] = cls.receipt_ref(
            "mas_build_dependency_currentness_receipt", sealed
        )

    @classmethod
    def reseal_selected_build_currentness_authority(
        cls,
        request: dict[str, Any],
    ) -> None:
        authority = request["selected_build_currentness_authority"]
        record = authority["authority_record"]
        authority_sha256 = cls.fingerprint(record)
        authority_ref = {
            "kind": "mas_build_dependency_currentness_authority",
            "ref": (
                "mas-build-dependency-currentness-authority:"
                f"{authority_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(record)),
            "sha256": authority_sha256,
        }
        authority["authority_ref"] = authority_ref
        request["review_authority"]["currentness_receipt"][
            "current_build_dependency_authority_refs"
        ] = [deepcopy(authority_ref)]
        request["generation_manifest"]["selected_build_binding"][
            "dependency_currentness_receipt"
        ]["authority_ref"] = deepcopy(authority_ref)
        cls.reseal_selected_build_currentness_receipt(request)
        cls.refresh_paper_manifest_identity(request)

    @classmethod
    def reseal_review_wrapper(cls, wrapper: dict[str, Any]) -> None:
        core = deepcopy(wrapper["receipt"])
        receipt_fingerprint = cls.fingerprint(core)
        lane = core["review_lane"]
        wrapper["receipt_ref"] = {
            "kind": "mas_reviewer_receipt",
            "ref": (
                f"mas-independent-review-receipt:{lane}:"
                f"{receipt_fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": receipt_fingerprint,
        }

    @classmethod
    def refresh_paper_manifest_identity(cls, request: dict[str, Any]) -> None:
        manifest = request["generation_manifest"]
        manifest["artifacts"].sort(
            key=lambda item: (item["role"], item["ref"], item["sha256"])
        )
        for invocation in manifest.get("professional_skill_invocations", []):
            if invocation["schema_version"] == 2:
                invocation_core = {
                    key: deepcopy(value)
                    for key, value in invocation.items()
                    if key != "invocation_ref"
                }
                invocation["invocation_ref"] = cls.professional_invocation_ref(
                    invocation_core
                )
        core = {
            "surface_kind": manifest["surface_kind"],
            "schema_version": manifest["schema_version"],
            "generation_id": manifest["generation_id"],
            "manifest_scope": manifest["manifest_scope"],
            "artifacts": manifest["artifacts"],
        }
        if manifest["schema_version"] == 2:
            from med_autoscience.authority_handlers._generation_manifest import (
                build_review_scopes,
            )

            manifest["review_scopes"] = build_review_scopes(
                manifest["artifacts"], manifest["manifest_scope"]
            )
            core["review_scopes"] = manifest["review_scopes"]
            if "professional_skill_invocations" in manifest:
                core["professional_skill_invocations"] = manifest[
                    "professional_skill_invocations"
                ]
            if "first_draft_quality_application" in manifest:
                core["first_draft_quality_application"] = manifest[
                    "first_draft_quality_application"
                ]
            for field in (
                "clinical_analysis_identity_admission",
                "selected_build_binding",
                "reviewer_response_sync",
            ):
                if field in manifest:
                    core[field] = manifest[field]
        fingerprint = cls.fingerprint(core)
        manifest["generation_manifest_sha256"] = fingerprint
        manifest_ref = {
            "kind": "mas_generation_manifest",
            "ref": (
                f"mas-generation-manifest:{manifest['generation_id']}:"
                f"{manifest['manifest_scope']}:"
                f"{fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": fingerprint,
        }
        request["generation_manifest_ref"] = manifest_ref
        currentness = request["review_authority"]["currentness_receipt"]
        currentness["current_generation_manifest_ref"] = manifest_ref
        cls.reseal_review_currentness(request)
