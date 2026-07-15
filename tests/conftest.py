from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

import pytest


ANALYSIS_ROLES = (
    "source_input_digest",
    "data_release",
    "denominator_definitions",
    "analysis_script",
    "analysis_output",
)
MANUSCRIPT_ROLES = ANALYSIS_ROLES + (
    "candidate_admission_receipt",
    "canonical_manuscript",
    "claim_evidence_map",
    "citation_ledger",
    "numeric_trace",
    "reference_library",
    "table_catalog",
    "table_file",
    "figure_catalog",
    "figure_file",
    "render_environment_and_font_manifest",
)
PUBLICATION_ROLES = MANUSCRIPT_ROLES + (
    "docx",
    "pdf",
    "supplementary_output",
    "final_zip_allowlist",
    "final_zip_member",
)
ROLES_BY_SCOPE = {
    "analysis_generation": ANALYSIS_ROLES,
    "manuscript_generation": MANUSCRIPT_ROLES,
    "publication_generation": PUBLICATION_ROLES,
}
LANES_BY_SCOPE = {
    "analysis_generation": ("statistical",),
    "manuscript_generation": ("medical", "statistical", "reference", "display"),
    "publication_generation": (
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    ),
}
AUTHORITY_ROLE_BY_LANE = {
    "medical": "mas_independent_medical_reviewer",
    "statistical": "mas_independent_statistical_reviewer",
    "reference": "mas_independent_reference_reviewer",
    "display": "mas_independent_display_reviewer",
    "publication": "mas_independent_publication_reviewer",
    "exact_byte_package": "mas_independent_exact_byte_package_reviewer",
}


class AuthorityRecordFactory:
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
    def claim_scope(
        cls,
        *,
        sensitivity_only: bool = False,
        supplementary_only: bool = False,
        abstract_headline_allowed: bool = False,
    ) -> dict[str, Any]:
        claim_classes = ["secondary"]
        if sensitivity_only:
            claim_classes.append("sensitivity")
        if supplementary_only:
            claim_classes.append("supplementary_only")
        return {
            "claim_classes": claim_classes,
            "claim_ids": ["bounded_candidate_claim"],
            "permitted_sections": ["supplement" if supplementary_only else "results"],
            "required_disclosures": [
                "report the bounded evidence denominator and uncertainty"
            ],
            "prohibited_claims": ["causal or clinical-quality interpretation"],
            "sensitivity_only": sensitivity_only,
            "supplementary_only": supplementary_only,
            "abstract_headline_allowed": abstract_headline_allowed,
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

    @classmethod
    def generation_manifest(
        cls,
        scope: str,
        *,
        candidate_receipt: dict[str, Any] | None = None,
        review_receipts: list[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        for index, role in enumerate(ROLES_BY_SCOPE[scope]):
            if role == "candidate_admission_receipt" and candidate_receipt is not None:
                artifacts.append(
                    {
                        "role": role,
                        "ref": candidate_receipt["receipt_id"],
                        "size_bytes": candidate_receipt["receipt_size_bytes"],
                        "sha256": candidate_receipt["receipt_fingerprint"],
                    }
                )
                continue
            role_scope = "analysis_generation" if role in ANALYSIS_ROLES else scope
            artifacts.append(
                {
                    "role": role,
                    "ref": f"workspace://study/{role_scope}/{role}",
                    "size_bytes": 1000 + index,
                    "sha256": cls.digest(
                        f"{cls.generation_id}:{role_scope}:{role}:bytes"
                    ),
                }
            )
        candidate = cls.candidate_member()
        evidence = cls.evidence_member()
        artifacts.extend(
            [
                {name: value for name, value in candidate.items() if name != "kind"},
                {name: value for name, value in evidence.items() if name != "kind"},
            ]
        )
        artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
        core = {
            "surface_kind": "mas_evidence_generation_manifest",
            "schema_version": 1,
            "generation_id": cls.generation_id,
            "manifest_scope": scope,
            "artifacts": artifacts,
        }
        manifest_sha256 = cls.fingerprint(core)
        manifest = {
            **core,
            "generation_manifest_sha256": manifest_sha256,
            "independent_review_receipts": deepcopy(review_receipts or []),
        }
        manifest_ref = {
            "kind": "mas_generation_manifest",
            "ref": (
                f"mas-generation-manifest:{cls.generation_id}:{scope}:"
                f"{manifest_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": manifest_sha256,
        }
        return manifest, manifest_ref

    @classmethod
    def candidate_request(
        cls,
        *,
        verdict: str = "accepted",
        request_name: str = "candidate-request-current",
        current_request_name: str | None = None,
        superseded_request_names: tuple[str, ...] = (),
        sensitivity_only: bool = False,
        abstract_headline_allowed: bool = False,
    ) -> dict[str, Any]:
        manifest, manifest_ref = cls.generation_manifest("analysis_generation")
        candidate = {
            "candidate_id": "bounded-candidate",
            "candidate_member": cls.candidate_member(),
            "evidence_members": [cls.evidence_member()],
            "claim_scope": cls.claim_scope(
                sensitivity_only=sensitivity_only,
                abstract_headline_allowed=abstract_headline_allowed,
            ),
        }
        producer_attempt = cls.typed_ref("opl_stage_attempt", "candidate-producer")
        adjudicator_attempt = cls.typed_ref(
            "opl_stage_attempt", "independent-medical-adjudicator"
        )
        candidate_packet = cls.exact_ref("opl_action_output", "candidate-source-packet")
        admission_request = cls.exact_ref("opl_action_output", request_name)
        current_admission_request = cls.exact_ref(
            "opl_action_output", current_request_name or request_name
        )
        superseded_requests = [
            cls.exact_ref("opl_action_output", name)
            for name in superseded_request_names
        ]
        decision_code = {
            "accepted": (
                "accepted_for_bounded_sensitivity_use"
                if sensitivity_only
                else "accepted_for_exact_claim_scope"
            ),
            "rejected": "rejected_unsupported_evidence",
            "route_back": "claim_scope_revision_required",
            "waived": "waived_with_typed_scope",
        }[verdict]
        next_owner = "candidate_evidence_owner" if verdict == "route_back" else None
        resume_condition = (
            "supply a revised exact claim scope" if verdict == "route_back" else None
        )
        waiver = None
        if verdict == "waived":
            waiver = {
                "waiver_kind": "mas_candidate_admission_waiver",
                "waiver_code": "waived_non_material_candidate_gap",
                "scope": "candidate_record_only",
                "evidence_refs": [cls.typed_ref("mas_evidence", "waiver-evidence")],
                "expires_on_generation_change": True,
                "authorizes_manuscript_consumption": False,
            }
        candidate_ref = {
            name: value
            for name, value in candidate["candidate_member"].items()
            if name != "role"
        }
        evidence_refs = [
            {name: value for name, value in item.items() if name != "role"}
            for item in candidate["evidence_members"]
        ]
        adjudicator_core = {
            "receipt_kind": "mas_candidate_adjudicator_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "independent_medical_adjudicator",
            "authority_epoch": cls.authority_epoch,
            "producer_attempt_ref": producer_attempt,
            "adjudicator_attempt_ref": adjudicator_attempt,
            "candidate_packet_ref": candidate_packet,
            "admission_request_ref": admission_request,
            "generation_id": cls.generation_id,
            "generation_manifest_ref": manifest_ref,
            "candidate_id": candidate["candidate_id"],
            "candidate_ref": candidate_ref,
            "evidence_refs": evidence_refs,
            "claim_scope": candidate["claim_scope"],
            "candidate_record_sha256": cls.fingerprint(candidate),
            "verdict": verdict,
            "decision_code": decision_code,
            "next_owner": next_owner,
            "resume_condition": resume_condition,
            "waiver": waiver,
        }
        adjudicator_receipt = cls.seal(adjudicator_core, "mas-candidate-adjudicator")
        adjudicator_ref = cls.receipt_ref(
            "mas_candidate_adjudicator_receipt", adjudicator_receipt
        )
        currentness_core = {
            "receipt_kind": "mas_generation_currentness_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "generation_currentness_owner",
            "authority_epoch": cls.authority_epoch,
            "current_generation_id": cls.generation_id,
            "current_generation_manifest_ref": manifest_ref,
            "current_admission_request_ref": current_admission_request,
            "current_adjudicator_receipt_ref": adjudicator_ref,
            "superseded_generation_ids": [],
            "superseded_request_refs": superseded_requests,
        }
        currentness_receipt = cls.seal(currentness_core, "mas-generation-currentness")
        currentness_ref = cls.receipt_ref(
            "mas_generation_currentness_receipt", currentness_receipt
        )
        return {
            "surface_kind": "mas_candidate_admission_authority_request",
            "schema_version": 2,
            "adjudicator_context": {
                "producer_attempt_ref": producer_attempt,
                "adjudicator_attempt_ref": adjudicator_attempt,
                "candidate_packet_ref": candidate_packet,
                "admission_request_ref": admission_request,
                "adjudicator_receipt_ref": adjudicator_ref,
                "currentness_receipt_ref": currentness_ref,
            },
            "mission": {
                "program_id": "program-dm",
                "study_id": "study-003",
                "mission_id": "paper-mission-study-003",
                "stage_id": "manuscript_authoring",
                "stage_goal_ref": cls.typed_ref(
                    "mas_stage_goal", "manuscript-authoring"
                ),
            },
            "generation_manifest": manifest,
            "generation_manifest_ref": manifest_ref,
            "currentness_receipt": currentness_receipt,
            "candidate": candidate,
            "adjudicator_receipt": adjudicator_receipt,
            "hard_gate": {
                "kind": "none",
                "reason_code": None,
                "evidence_refs": [],
                "next_owner": None,
                "resume_condition": None,
            },
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
        del manifest_ref
        core = {
            "receipt_kind": "mas_independent_review_receipt",
            "schema_version": 1,
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
            "generation_id": manifest["generation_id"],
            "generation_manifest_sha256": manifest["generation_manifest_sha256"],
            "reviewed_members": deepcopy(manifest["artifacts"]),
            "accepted_candidate_receipt_refs": [candidate_receipt_ref],
            "defect_refs": deepcopy(defect_refs or []),
            "quality_debt_codes": list(quality_debt_codes or []),
        }
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

    @classmethod
    def paper_request(
        cls,
        *,
        scope: str = "manuscript_generation",
        stage_id: str = "manuscript_authoring",
        candidate_verdict: str = "accepted",
        candidate_sensitivity_only: bool = False,
        supplied_review_request_name: str = "review-request-current",
        current_review_request_name: str | None = None,
        superseded_review_request_names: tuple[str, ...] = (),
        review_verdicts: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers.candidate_admission import (
            evaluate_candidate_admission_authority,
        )

        candidate_request = cls.candidate_request(
            verdict=candidate_verdict,
            sensitivity_only=candidate_sensitivity_only,
        )
        candidate_result = evaluate_candidate_admission_authority(candidate_request)
        if candidate_result["status"] not in {"accepted", "rejected"}:
            raise AssertionError(candidate_result)
        candidate_receipt = candidate_result["disposition_receipt"]
        candidate_receipt_ref = cls.receipt_ref(
            "mas_candidate_admission_receipt", candidate_receipt
        )
        manifest, manifest_ref = cls.generation_manifest(
            scope, candidate_receipt=candidate_receipt
        )
        producer_output_ref = cls.exact_ref(
            "opl_action_output", f"paper-output-{scope}"
        )
        supplied_review_request = cls.exact_ref(
            "opl_action_output", supplied_review_request_name
        )
        current_review_request = cls.exact_ref(
            "opl_action_output",
            current_review_request_name or supplied_review_request_name,
        )
        wrappers = [
            cls.independent_review_wrapper(
                lane=lane,
                manifest=manifest,
                manifest_ref=manifest_ref,
                candidate_receipt_ref=candidate_receipt_ref,
                review_request_ref=supplied_review_request,
                producer_output_ref=producer_output_ref,
                verdict=(review_verdicts or {}).get(lane, "passed"),
                defect_refs=(
                    [cls.typed_ref("mas_review_defect", f"{lane}-defect")]
                    if (review_verdicts or {}).get(lane) == "revision_required"
                    else []
                ),
            )
            for lane in LANES_BY_SCOPE[scope]
        ]
        manifest["independent_review_receipts"] = wrappers
        superseded_review_requests = [
            cls.exact_ref("opl_action_output", name)
            for name in superseded_review_request_names
        ]
        currentness_core = {
            "receipt_kind": "mas_review_currentness_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "review_currentness_owner",
            "authority_epoch": cls.authority_epoch,
            "current_generation_id": cls.generation_id,
            "current_generation_manifest_ref": manifest_ref,
            "current_review_request_ref": current_review_request,
            "current_candidate_admission_receipt_refs": [candidate_receipt_ref],
            "current_review_receipt_refs": [
                deepcopy(wrapper["receipt_ref"]) for wrapper in wrappers
            ],
            "superseded_generation_ids": [],
            "superseded_review_request_refs": superseded_review_requests,
        }
        currentness_receipt = cls.seal(currentness_core, "mas-review-currentness")
        currentness_ref = cls.receipt_ref(
            "mas_review_currentness_receipt", currentness_receipt
        )
        candidate_ref = candidate_receipt["candidate_ref"]
        evidence_ref = candidate_receipt["evidence_refs"][0]
        return {
            "surface_kind": "mas_paper_mission_authority_request",
            "schema_version": 2,
            "host_context": {
                "action_id": "paper_mission",
                "run_ref": cls.typed_ref("opl_stage_run", "paper-run"),
                "producer_attempt_ref": cls.typed_ref(
                    "opl_stage_attempt", "paper-producer"
                ),
                "output_ref": producer_output_ref,
                "output_state": "consumable",
            },
            "mission": {
                "program_id": "program-dm",
                "study_id": "study-003",
                "mission_id": "paper-mission-study-003",
                "stage_id": stage_id,
                "stage_goal_ref": cls.typed_ref("mas_stage_goal", stage_id),
            },
            "medical_evidence": {
                "source_readiness_status": "ready",
                "source_readiness_receipt_ref": cls.typed_ref(
                    "mas_source_readiness_receipt", "source-ready"
                ),
                "claim_evidence_status": "aligned",
                "claim_boundary_ref": cls.typed_ref(
                    "mas_claim_boundary", "bounded-claims"
                ),
                "candidate_artifact_refs": [
                    {
                        "kind": candidate_ref["kind"],
                        "ref": candidate_ref["ref"],
                        "sha256": candidate_ref["sha256"],
                    }
                ],
                "evidence_refs": [
                    {
                        "kind": evidence_ref["kind"],
                        "ref": evidence_ref["ref"],
                        "sha256": evidence_ref["sha256"],
                    }
                ],
                "negative_result_refs": [],
                "failed_path_refs": [],
                "artifact_lineage_refs": [
                    cls.typed_ref("mas_artifact_lineage", "paper-lineage")
                ],
                "reproducibility_refs": [
                    cls.typed_ref("mas_reproducibility", "paper-reproducibility")
                ],
            },
            "generation_manifest": manifest,
            "generation_manifest_ref": manifest_ref,
            "candidate_admissions": [
                {
                    "receipt_ref": candidate_receipt_ref,
                    "receipt": candidate_receipt,
                }
            ],
            "review_authority": {
                "review_request_ref": supplied_review_request,
                "currentness_receipt_ref": currentness_ref,
                "currentness_receipt": currentness_receipt,
            },
            "repair_state": {
                "status": "not_required",
                "attempts_used": 0,
                "max_attempts": 3,
                "repair_attempt_refs": [],
                "latest_repair_output_ref": None,
            },
            "hard_gate": {
                "kind": "none",
                "reason_code": None,
                "evidence_refs": [],
                "next_owner": None,
                "resume_condition": None,
            },
        }

    @classmethod
    def reseal_review_currentness(cls, request: dict[str, Any]) -> None:
        receipt = request["review_authority"]["currentness_receipt"]
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
        core = {
            "surface_kind": manifest["surface_kind"],
            "schema_version": manifest["schema_version"],
            "generation_id": manifest["generation_id"],
            "manifest_scope": manifest["manifest_scope"],
            "artifacts": manifest["artifacts"],
        }
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


@pytest.fixture
def authority_records() -> AuthorityRecordFactory:
    return AuthorityRecordFactory()
