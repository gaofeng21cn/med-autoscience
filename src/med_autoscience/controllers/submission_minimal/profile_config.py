from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path

from med_autoscience.publication_profiles import (
    FRONTIERS_FAMILY_HARVARD_PROFILE,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    JACS_PROFILE,
    normalize_publication_profile,
)


STYLES_ROOT = Path(__file__).resolve().parents[2] / "styles"
FRONTIERS_TEMPLATE_RESOURCE_ID = "frontiers_word_manuscript_template"
FRONTIERS_SUPPLEMENTARY_TEMPLATE_RESOURCE_ID = "frontiers_word_supplementary_template"
FRONTIERS_CSL_RESOURCE_ID = "frontiers_harvard_csl"
FRONTIERS_TEMPLATE_ENV = "OPL_MAS_FRONTIERS_TEMPLATE_DOCX"
FRONTIERS_SUPPLEMENTARY_TEMPLATE_ENV = "OPL_MAS_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX"
FRONTIERS_CSL_ENV = "OPL_MAS_FRONTIERS_CSL_PATH"
FRONTIERS_KEYWORDS = [
    "NF-PitNET",
    "pituitary neuroendocrine tumor",
    "residual disease",
    "non-gross-total resection",
    "risk stratification",
    "pituitary surgery",
]
SUBMISSION_FRONT_MATTER_FIELD_ALIASES = {
    "authors": ("authors", "author"),
    "affiliations": ("affiliations",),
    "corresponding_author": ("corresponding_author", "correspondence"),
    "funding": ("funding",),
    "conflict_of_interest": ("conflict_of_interest", "conflicts_of_interest"),
    "ethics": ("ethics", "ethics_statement"),
    "data_availability": ("data_availability", "data_availability_statement"),
    "analytic_data_lock_date": (
        "analytic_data_lock_date",
        "data_lock_date",
        "data_lock",
        "analytic_release_date",
    ),
    "registry_enrollment_period": (
        "registry_enrollment_period",
        "study_enrollment_period",
        "enrollment_period",
        "enrollment_window",
    ),
}


@dataclass(frozen=True)
class PublicationProfileConfig:
    publication_profile: str
    citation_style: str
    csl_path: Path
    output_dir_rel: Path
    reference_doc_path: Path | None = None
    supplementary_reference_doc_path: Path | None = None
    supplementary_docx_name: str | None = None
    journal_name: str | None = None
    journal_family: str | None = None
    reference_style_family: str | None = None


class MissingProvisionedSubmissionResource(FileNotFoundError):
    def __init__(self, *, resource_id: str, env_name: str) -> None:
        self.resolution = {
            "status": "request_only",
            "action_id": "opl_pack_provision_submission_resource",
            "resource_id": resource_id,
            "path_env": env_name,
            "requires_existing_exact_path": True,
            "network_fallback_allowed": False,
        }
        super().__init__(
            f"missing host-provisioned submission resource `{resource_id}`; "
            f"provide an existing exact path through {env_name}"
        )


def submission_resource_requirements() -> dict[str, object]:
    return {
        "surface_kind": "mas_submission_resource_requirements.v1",
        "schema_version": 1,
        "owner": "OPL Pack or the invoking host",
        "purpose": (
            "Declare exact-path submission resources without giving MAS a package "
            "downloader or network provisioning control plane."
        ),
        "resources": {
            FRONTIERS_CSL_RESOURCE_ID: {
                "provisioning": "package_bundled_or_host_exact_path",
                "package_path": "src/med_autoscience/styles/frontiers.csl",
                "path_env": FRONTIERS_CSL_ENV,
            },
            FRONTIERS_TEMPLATE_RESOURCE_ID: {
                "provisioning": "host_exact_path_required",
                "path_env": FRONTIERS_TEMPLATE_ENV,
            },
            FRONTIERS_SUPPLEMENTARY_TEMPLATE_RESOURCE_ID: {
                "provisioning": "host_exact_path_required",
                "path_env": FRONTIERS_SUPPLEMENTARY_TEMPLATE_ENV,
            },
        },
        "missing_resource_output": {
            "status": "request_only",
            "action_id": "opl_pack_provision_submission_resource",
        },
        "authority_boundary": {
            "mas_can_download_resources": False,
            "network_fallback_allowed": False,
            "requires_existing_exact_path": True,
        },
    }


def default_ama_csl_path() -> Path:
    return STYLES_ROOT / "american-medical-association.csl"


def default_frontiers_harvard_csl_path() -> Path:
    return STYLES_ROOT / "frontiers.csl"


def default_acs_csl_path() -> Path:
    return STYLES_ROOT / "american-chemical-society.csl"


def resolve_provisioned_path(
    *,
    resource_id: str,
    env_name: str,
    provisioned_resources: Mapping[str, str | Path] | None = None,
) -> Path:
    explicit = (provisioned_resources or {}).get(resource_id)
    raw_path = str(explicit or os.getenv(env_name, "")).strip()
    if not raw_path:
        raise MissingProvisionedSubmissionResource(resource_id=resource_id, env_name=env_name)
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"provisioned submission resource is not a file for {resource_id}: {path}")
    return path


def ensure_frontiers_word_templates(
    *,
    provisioned_resources: Mapping[str, str | Path] | None = None,
) -> tuple[Path, Path]:
    return (
        resolve_provisioned_path(
            resource_id=FRONTIERS_TEMPLATE_RESOURCE_ID,
            env_name=FRONTIERS_TEMPLATE_ENV,
            provisioned_resources=provisioned_resources,
        ),
        resolve_provisioned_path(
            resource_id=FRONTIERS_SUPPLEMENTARY_TEMPLATE_RESOURCE_ID,
            env_name=FRONTIERS_SUPPLEMENTARY_TEMPLATE_ENV,
            provisioned_resources=provisioned_resources,
        ),
    )


def ensure_frontiers_harvard_csl_path(
    *,
    provisioned_resources: Mapping[str, str | Path] | None = None,
) -> Path:
    explicit = (provisioned_resources or {}).get(FRONTIERS_CSL_RESOURCE_ID)
    env_path = os.getenv(FRONTIERS_CSL_ENV, "").strip()
    if explicit or env_path:
        return resolve_provisioned_path(
            resource_id=FRONTIERS_CSL_RESOURCE_ID,
            env_name=FRONTIERS_CSL_ENV,
            provisioned_resources=provisioned_resources,
        )
    csl_path = default_frontiers_harvard_csl_path()
    if not csl_path.is_file():
        raise FileNotFoundError(f"missing package-bundled Frontiers Harvard CSL file: {csl_path}")
    return csl_path


def resolve_publication_profile_config(
    *,
    publication_profile: str,
    citation_style: str | None,
    provisioned_resources: Mapping[str, str | Path] | None = None,
) -> PublicationProfileConfig:
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    normalized_citation_style = str(citation_style or "auto").strip()

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        resolved_citation_style = "AMA" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        if resolved_citation_style != "AMA":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        csl_path = default_ama_csl_path()
        if not csl_path.is_file():
            raise FileNotFoundError(f"missing AMA CSL file: {csl_path}")
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=csl_path,
            output_dir_rel=Path("submission_minimal"),
        )

    if normalized_publication_profile == FRONTIERS_FAMILY_HARVARD_PROFILE:
        resolved_citation_style = (
            "FrontiersHarvard" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        )
        if resolved_citation_style != "FrontiersHarvard":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        manuscript_template, supplementary_template = ensure_frontiers_word_templates(
            provisioned_resources=provisioned_resources,
        )
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=ensure_frontiers_harvard_csl_path(provisioned_resources=provisioned_resources),
            output_dir_rel=Path("journal_submissions") / normalized_publication_profile,
            reference_doc_path=manuscript_template,
            supplementary_reference_doc_path=supplementary_template,
            supplementary_docx_name="Supplementary_Material.docx",
            journal_family="Frontiers",
            reference_style_family="FrontiersHarvard",
        )

    if normalized_publication_profile == JACS_PROFILE:
        resolved_citation_style = "ACS" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        if resolved_citation_style != "ACS":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        csl_path = default_acs_csl_path()
        if not csl_path.is_file():
            raise FileNotFoundError(f"missing ACS CSL file: {csl_path}")
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=csl_path,
            output_dir_rel=Path("journal_submissions") / normalized_publication_profile,
            journal_name="Journal of the American Chemical Society",
            journal_family="ACS",
            reference_style_family="ACS",
        )

    raise ValueError(f"unsupported publication profile: {publication_profile}")


__all__ = [
    "FRONTIERS_CSL_ENV",
    "FRONTIERS_CSL_RESOURCE_ID",
    "FRONTIERS_KEYWORDS",
    "FRONTIERS_SUPPLEMENTARY_TEMPLATE_ENV",
    "FRONTIERS_SUPPLEMENTARY_TEMPLATE_RESOURCE_ID",
    "FRONTIERS_TEMPLATE_ENV",
    "FRONTIERS_TEMPLATE_RESOURCE_ID",
    "MissingProvisionedSubmissionResource",
    "PublicationProfileConfig",
    "STYLES_ROOT",
    "SUBMISSION_FRONT_MATTER_FIELD_ALIASES",
    "default_acs_csl_path",
    "default_ama_csl_path",
    "default_frontiers_harvard_csl_path",
    "ensure_frontiers_harvard_csl_path",
    "ensure_frontiers_word_templates",
    "resolve_provisioned_path",
    "resolve_publication_profile_config",
    "submission_resource_requirements",
]
