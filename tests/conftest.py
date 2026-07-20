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
    "submission_status",
    "publication_evaluation",
    "next_action_envelope",
    "submission_projection_manifest",
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
    def professional_figure_skill_invocations(
        cls,
        artifacts: list[dict[str, Any]],
        *,
        figure_id: str = "F1",
        composition_mode: str = "single_canvas_direct",
    ) -> list[dict[str, Any]]:
        bindings = [
            {
                key: artifact[key]
                for key in ("member_id", "role", "ref", "size_bytes", "sha256")
            }
            for artifact in artifacts
            if artifact["role"] == "figure_file"
        ]
        if not bindings:
            return []
        common = {
            "surface_kind": "mas_professional_figure_skill_invocation_candidate",
            "schema_version": 1,
            "figure_id": figure_id,
            "figure_kind": "evidence_figure",
            "composition_mode": composition_mode,
            "package_id": "mas-scholar-skills",
            "package_version": "test-version",
            "package_source_ref": "git:mas-scholar-skills@test",
            "package_source_sha256": cls.digest("mas-scholar-skills:test-source"),
            "input_contract_ref": f"mas-figure-contract://{figure_id}",
            "input_sha256": cls.digest(f"figure-contract:{figure_id}"),
            "output_artifact_bindings": bindings,
            "status": "completed",
            "refs_only": True,
            "authority": False,
            "publication_ready": False,
        }
        invocations = []
        for skill_id in ("medical-figure-design", "medical-figure-style"):
            invocation = {
                **deepcopy(common),
                "receipt_id": f"mas-professional-figure-skill:{figure_id}:{skill_id}",
                "skill_id": skill_id,
                "skill_source_ref": f"skills/{skill_id}/SKILL.md",
                "skill_source_sha256": cls.digest(f"skill-source:{skill_id}"),
                "invocation_id": f"invocation:{figure_id}:{skill_id}",
                "consumed_rule_refs": [f"{skill_id}#workflow"],
            }
            if skill_id == "medical-figure-design":
                invocation["template_usage"] = {
                    "used": False,
                    "decision_reason": "No reusable template was consumed.",
                }
                invocation["figure_text_policy"] = {
                    "embedded_title": False,
                    "embedded_subtitle": False,
                    "embedded_prose_footer": False,
                    "allowed_text_roles": [
                        "panel_label",
                        "axis_label",
                        "tick_label",
                        "legend",
                        "necessary_statistical_annotation",
                    ],
                }
            invocations.append(invocation)
        if composition_mode == "assembled_panels":
            invocations.append(
                {
                    **deepcopy(common),
                    "receipt_id": (
                        f"mas-professional-figure-skill:{figure_id}:"
                        "medical-figure-composer"
                    ),
                    "skill_id": "medical-figure-composer",
                    "skill_source_ref": "skills/medical-figure-composer/SKILL.md",
                    "skill_source_sha256": cls.digest(
                        "skill-source:medical-figure-composer"
                    ),
                    "invocation_id": (
                        f"invocation:{figure_id}:medical-figure-composer"
                    ),
                    "consumed_rule_refs": ["medical-figure-composer#workflow"],
                }
            )
        return invocations

    @classmethod
    def professional_manuscript_skill_invocations(
        cls,
        artifacts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        role_sets = {
            "medical-manuscript-writing": {"canonical_manuscript"},
            "medical-registry-atlas-story-architect": {
                "canonical_manuscript",
                "claim_evidence_map",
            },
            "medical-statistical-review": {"analysis_output", "numeric_trace"},
            "medical-table-design": {"table_catalog", "table_file"},
            "medical-submission-prep": {
                "canonical_manuscript",
                "docx",
                "pdf",
                "supplementary_output",
                "final_zip_allowlist",
                "final_zip_member",
            },
        }
        invocations = []
        for skill_id, roles in role_sets.items():
            if skill_id == "medical-submission-prep" and not any(
                artifact["role"] in {"docx", "pdf", "supplementary_output"}
                for artifact in artifacts
            ):
                continue
            bindings = [
                {
                    key: artifact[key]
                    for key in ("member_id", "role", "ref", "size_bytes", "sha256")
                }
                for artifact in artifacts
                if artifact["role"] in roles
            ]
            invocations.append(
                {
                    "surface_kind": (
                        "mas_professional_manuscript_skill_invocation_candidate"
                    ),
                    "schema_version": 1,
                    "receipt_id": f"mas-professional-manuscript-skill:{skill_id}",
                    "skill_id": skill_id,
                    "package_id": "mas-scholar-skills",
                    "package_version": "test-version",
                    "package_source_ref": "git:mas-scholar-skills@test",
                    "package_source_sha256": cls.digest(
                        "mas-scholar-skills:test-source"
                    ),
                    "skill_source_ref": f"skills/{skill_id}/SKILL.md",
                    "skill_source_sha256": cls.digest(f"skill-source:{skill_id}"),
                    "invocation_id": f"invocation:first-draft:{skill_id}",
                    "input_contract_ref": "mas-manuscript-contract://first-draft",
                    "input_sha256": cls.digest("manuscript-contract:first-draft"),
                    "consumed_rule_refs": [
                        f"{skill_id}#workflow",
                        *(
                            ["medical-table-design#main-table-information-budget"]
                            if skill_id == "medical-table-design"
                            else []
                        ),
                    ],
                    "output_artifact_bindings": bindings,
                    "template_substitution": False,
                    "status": "completed",
                    "refs_only": True,
                    "authority": False,
                    "publication_ready": False,
                    **(
                        {
                            "table_quality_application": {
                                "schema_version": 1,
                                "policy_ref": "medical-table-design#main-table-information-budget",
                                "template_policy": "reference_floor_not_required",
                                "coverage_status": "all_main_tables_assessed",
                                "main_tables": [
                                    {
                                        "table_id": "T1",
                                        "role": "main_text",
                                        "reader_question": "Who is represented in the cohort?",
                                        "row_count": 7,
                                        "column_count": 8,
                                        "body_word_count": 202,
                                        "max_cell_word_count": 12,
                                        "footnote_word_count": 18,
                                        "supplementary_detail_refs": ["TS27"],
                                        "budget_status": "within_default_budget",
                                        "exception_reason": None,
                                        "final_embedding_status": "passed",
                                        "final_embedding_page_span": 1,
                                        "standalone_notes_heading_present": False,
                                    }
                                ],
                            }
                        }
                        if skill_id == "medical-table-design"
                        else {}
                    ),
                }
            )
        return invocations

    @classmethod
    def generation_manifest(
        cls,
        scope: str,
        *,
        schema_version: int = 1,
        generation_id: str | None = None,
        artifact_sha_overrides: dict[str, str] | None = None,
        artifact_ref_overrides: dict[str, str] | None = None,
        artifact_member_id_overrides: dict[str, str] | None = None,
        extra_artifacts: list[dict[str, Any]] | None = None,
        professional_skill_invocations: list[dict[str, Any]] | None = None,
        include_professional_skill_invocations: bool = True,
        omit_professional_skill_ids: tuple[str, ...] = (),
        professional_figure_composition_mode: str = "single_canvas_direct",
        candidate_receipt: dict[str, Any] | None = None,
        review_receipts: list[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        generation_id = generation_id or cls.generation_id
        artifact_sha_overrides = artifact_sha_overrides or {}
        artifact_ref_overrides = artifact_ref_overrides or {}
        artifact_member_id_overrides = artifact_member_id_overrides or {}
        artifacts: list[dict[str, Any]] = []
        for index, role in enumerate(ROLES_BY_SCOPE[scope]):
            if role == "candidate_admission_receipt" and candidate_receipt is not None:
                artifact = {
                    "role": role,
                    "ref": candidate_receipt["receipt_id"],
                    "size_bytes": candidate_receipt["receipt_size_bytes"],
                    "sha256": candidate_receipt["receipt_fingerprint"],
                }
                if schema_version == 2:
                    artifact["member_id"] = artifact_member_id_overrides.get(
                        role, f"mas-member:{role}:primary"
                    )
                artifacts.append(artifact)
                continue
            role_scope = "analysis_generation" if role in ANALYSIS_ROLES else scope
            artifact = {
                "role": role,
                "ref": artifact_ref_overrides.get(
                    role, f"workspace://study/{role_scope}/{role}"
                ),
                "size_bytes": 1000 + index,
                "sha256": artifact_sha_overrides.get(role)
                or cls.digest(
                    f"{generation_id if schema_version == 1 else 'stable'}:"
                    f"{role_scope}:{role}:bytes"
                ),
            }
            if schema_version == 2:
                artifact["member_id"] = artifact_member_id_overrides.get(
                    role, f"mas-member:{role}:primary"
                )
            artifacts.append(artifact)
        candidate = cls.candidate_member()
        evidence = cls.evidence_member()
        candidate_artifact = {
            name: value for name, value in candidate.items() if name != "kind"
        }
        evidence_artifact = {
            name: value for name, value in evidence.items() if name != "kind"
        }
        if schema_version == 2:
            candidate_artifact["member_id"] = artifact_member_id_overrides.get(
                "candidate_artifact", "mas-member:candidate_artifact:primary"
            )
            evidence_artifact["member_id"] = artifact_member_id_overrides.get(
                "evidence_record", "mas-member:evidence_record:primary"
            )
        artifacts.extend([candidate_artifact, evidence_artifact])
        artifacts.extend(deepcopy(extra_artifacts or []))
        artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
        core = {
            "surface_kind": "mas_evidence_generation_manifest",
            "schema_version": schema_version,
            "generation_id": generation_id,
            "manifest_scope": scope,
            "artifacts": artifacts,
        }
        if schema_version == 2:
            from med_autoscience.authority_handlers._generation_manifest import (
                build_review_scopes,
            )

            core["review_scopes"] = build_review_scopes(artifacts, scope)
            if (
                include_professional_skill_invocations
                and scope != "analysis_generation"
            ):
                generated_invocations = deepcopy(
                    professional_skill_invocations
                    if professional_skill_invocations is not None
                    else [
                        *cls.professional_manuscript_skill_invocations(artifacts),
                        *cls.professional_figure_skill_invocations(
                            artifacts,
                            composition_mode=professional_figure_composition_mode,
                        ),
                    ]
                )
                generated_invocations = [
                    item
                    for item in generated_invocations
                    if item["skill_id"] not in set(omit_professional_skill_ids)
                ]
                generated_invocations.sort(
                    key=lambda item: (
                        item["surface_kind"],
                        item.get("figure_id", ""),
                        item["skill_id"],
                    )
                )
                core["professional_skill_invocations"] = generated_invocations
        manifest_sha256 = cls.fingerprint(core)
        manifest = {
            **core,
            "generation_manifest_sha256": manifest_sha256,
            "independent_review_receipts": deepcopy(review_receipts or []),
        }
        manifest_ref = {
            "kind": "mas_generation_manifest",
            "ref": (
                f"mas-generation-manifest:{generation_id}:{scope}:"
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
        manifest_version: int = 1,
        generation_id: str | None = None,
    ) -> dict[str, Any]:
        generation_id = generation_id or cls.generation_id
        manifest, manifest_ref = cls.generation_manifest(
            "analysis_generation",
            schema_version=manifest_version,
            generation_id=generation_id,
        )
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
            "generation_id": generation_id,
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
            "current_generation_id": generation_id,
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
        manifest_version: int = 2,
        generation_id: str | None = None,
        artifact_sha_overrides: dict[str, str] | None = None,
        artifact_ref_overrides: dict[str, str] | None = None,
        artifact_member_id_overrides: dict[str, str] | None = None,
        extra_artifacts: list[dict[str, Any]] | None = None,
        professional_skill_invocations: list[dict[str, Any]] | None = None,
        include_professional_skill_invocations: bool = True,
        omit_professional_skill_ids: tuple[str, ...] = (),
        professional_figure_composition_mode: str = "single_canvas_direct",
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers.candidate_admission import (
            evaluate_candidate_admission_authority,
        )

        candidate_request = cls.candidate_request(
            verdict=candidate_verdict,
            sensitivity_only=candidate_sensitivity_only,
            manifest_version=manifest_version,
            generation_id=generation_id,
        )
        candidate_result = evaluate_candidate_admission_authority(candidate_request)
        if candidate_result["status"] not in {"accepted", "rejected"}:
            raise AssertionError(candidate_result)
        candidate_receipt = candidate_result["disposition_receipt"]
        candidate_receipt_ref = cls.receipt_ref(
            "mas_candidate_admission_receipt", candidate_receipt
        )
        manifest, manifest_ref = cls.generation_manifest(
            scope,
            schema_version=manifest_version,
            generation_id=generation_id,
            artifact_sha_overrides=artifact_sha_overrides,
            artifact_ref_overrides=artifact_ref_overrides,
            artifact_member_id_overrides=artifact_member_id_overrides,
            extra_artifacts=extra_artifacts,
            candidate_receipt=candidate_receipt,
            professional_skill_invocations=professional_skill_invocations,
            include_professional_skill_invocations=(
                include_professional_skill_invocations
            ),
            omit_professional_skill_ids=omit_professional_skill_ids,
            professional_figure_composition_mode=(professional_figure_composition_mode),
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
        currentness_core: dict[str, Any] = {
            "receipt_kind": "mas_review_currentness_receipt",
            "schema_version": manifest_version,
            "owner": "MedAutoScience",
            "authority_role": "review_currentness_owner",
            "authority_epoch": cls.authority_epoch,
            "current_generation_id": manifest["generation_id"],
            "current_generation_manifest_ref": manifest_ref,
            "current_review_request_ref": current_review_request,
            "current_candidate_admission_receipt_refs": [candidate_receipt_ref],
        }
        if manifest_version == 1:
            currentness_core.update(
                {
                    "current_review_receipt_refs": [
                        deepcopy(wrapper["receipt_ref"]) for wrapper in wrappers
                    ],
                    "superseded_generation_ids": [],
                    "superseded_review_request_refs": superseded_review_requests,
                }
            )
        else:
            currentness_core["lane_currentness"] = [
                {
                    "review_lane": wrapper["receipt"]["review_lane"],
                    "review_authority_epoch": wrapper["receipt"]["authority_epoch"],
                    "currentness_status": "fresh",
                    "current_rubric_ref": deepcopy(wrapper["receipt"]["rubric_ref"]),
                    "review_scope_sha256": wrapper["receipt"]["review_scope_sha256"],
                    "review_receipt_issued_generation_id": wrapper["receipt"][
                        "issued_generation_id"
                    ],
                    "review_receipt_issued_generation_manifest_sha256": wrapper[
                        "receipt"
                    ]["issued_generation_manifest_sha256"],
                    "current_review_request_ref": deepcopy(
                        wrapper["receipt"]["review_request_ref"]
                    ),
                    "current_review_receipt_ref": deepcopy(wrapper["receipt_ref"]),
                    "superseded_review_request_refs": [],
                    "reuse_provenance": None,
                    "epistemic_currentness": cls.epistemic_currentness(
                        manifest,
                        wrapper["receipt"]["review_lane"],
                    ),
                }
                for wrapper in wrappers
            ]
            currentness_core["lane_currentness"].sort(
                key=lambda item: item["review_lane"]
            )
        currentness_receipt = cls.seal(currentness_core, "mas-review-currentness")
        currentness_ref = cls.receipt_ref(
            "mas_review_currentness_receipt", currentness_receipt
        )
        candidate_ref = candidate_receipt["candidate_ref"]
        evidence_ref = candidate_receipt["evidence_refs"][0]
        producer_attempt_ref = cls.typed_ref("opl_stage_attempt", "paper-producer")
        mission_identity = {
            "program_id": "program-dm",
            "study_id": "study-003",
            "mission_id": "paper-mission-study-003",
        }
        revision_core = {
            "receipt_kind": "mas_revision_consumption_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "revision_consumption_owner",
            "mission_identity": mission_identity,
            "generation_id": manifest["generation_id"],
            "producer_attempt_ref": producer_attempt_ref,
            "producer_output_ref": producer_output_ref,
            "applicability": "not_applicable",
            "revision_intake_refs": [],
            "opl_review_receipt_ref": None,
            "opl_finding_lineage": None,
            "finding_closures": [],
            "consumed_revision_refs": [],
            "authority_boundary": {
                "receipt_can_authorize_review_verdict": False,
                "receipt_can_authorize_owner_receipt": False,
                "receipt_can_authorize_publication": False,
                "receipt_can_authorize_submission": False,
                "receipt_can_create_typed_blocker": False,
            },
        }
        revision_receipt = cls.seal(revision_core, "mas-revision-consumption")
        revision_consumption = {
            "surface_kind": "mas_revision_consumption_binding",
            "schema_version": 1,
            "consumption_receipt_ref": cls.receipt_ref(
                "mas_revision_consumption_receipt", revision_receipt
            ),
            "consumption_receipt": revision_receipt,
        }
        return {
            "surface_kind": "mas_paper_mission_authority_request",
            "schema_version": 2,
            "host_context": {
                "action_id": "paper_mission",
                "run_ref": cls.typed_ref("opl_stage_run", "paper-run"),
                "producer_attempt_ref": producer_attempt_ref,
                "output_ref": producer_output_ref,
                "output_state": "consumable",
            },
            "mission": {
                **mission_identity,
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
            "revision_consumption": revision_consumption,
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
